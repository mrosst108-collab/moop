#include <inttypes.h>
#include <stdio.h>
#include "number.h"

/* --- 128-bit unsigned magnitudes -------------------------------------
 * One small set of operations, implemented twice. Every operand is at
 * most 2^127 - 1, which keeps the portable long division within 128
 * bits. Algorithms above this section use only these operations, so the
 * two implementations cannot differ in anything but speed. */

#if defined(__SIZEOF_INT128__) && !defined(MOOP_PORTABLE_WIDE)

__extension__ typedef unsigned __int128 Wide;
#define WIDE_IMPL "native"

static Wide w_make(uint64_t hi, uint64_t lo) { return (Wide)hi << 64 | lo; }
static Wide w_add(Wide a, Wide b) { return a + b; }
static Wide w_shl1(Wide a) { return a << 1; }
static int w_cmp(Wide a, Wide b) { return a < b ? -1 : a > b; }
static bool w_zero(Wide a) { return a == 0; }
static uint64_t w_lo(Wide a) { return (uint64_t)a; }

static void w_divmod(Wide a, Wide b, Wide *quo, Wide *rem)
{
    *quo = a / b;
    *rem = a % b;
}

#else

typedef struct {
    uint64_t hi, lo;
} Wide;
#define WIDE_IMPL "portable"

static Wide w_make(uint64_t hi, uint64_t lo) { return (Wide){ hi, lo }; }
static uint64_t w_lo(Wide a) { return a.lo; }
static bool w_zero(Wide a) { return a.hi == 0 && a.lo == 0; }

static Wide w_add(Wide a, Wide b)
{
    Wide r = { a.hi + b.hi, a.lo + b.lo };
    if (r.lo < a.lo)
        r.hi++;
    return r;
}

static Wide w_sub(Wide a, Wide b)
{
    Wide r = { a.hi - b.hi, a.lo - b.lo };
    if (a.lo < b.lo)
        r.hi--;
    return r;
}

static Wide w_shl1(Wide a)
{
    return (Wide){ a.hi << 1 | a.lo >> 63, a.lo << 1 };
}

static int w_cmp(Wide a, Wide b)
{
    if (a.hi != b.hi)
        return a.hi < b.hi ? -1 : 1;
    if (a.lo != b.lo)
        return a.lo < b.lo ? -1 : 1;
    return 0;
}

/* Binary long division, one bit at a time from the top. With both
 * operands at most 2^127 - 1 the remainder never needs a 129th bit. */
static void w_divmod(Wide a, Wide b, Wide *quo, Wide *rem)
{
    Wide q = { 0, 0 }, r = { 0, 0 };
    for (int i = 127; i >= 0; i--) {
        r = w_shl1(r);
        r.lo |= i >= 64 ? a.hi >> (i - 64) & 1 : a.lo >> i & 1;
        q = w_shl1(q);
        if (w_cmp(r, b) >= 0) {
            r = w_sub(r, b);
            q.lo |= 1;
        }
    }
    *quo = q;
    *rem = r;
}

#endif

const char *moop_number_wide(void)
{
    return WIDE_IMPL;
}

/* 2^127 - 1: the largest written part of a literal (U1) */
static Wide part_limit(void)
{
    return w_make(INT64_MAX, UINT64_MAX);
}

static Wide w_from(uint64_t v)
{
    return w_make(0, v);
}

static Wide w_gcd(Wide a, Wide b)
{
    while (!w_zero(b)) {
        Wide q, r;
        w_divmod(a, b, &q, &r);
        a = b;
        b = r;
    }
    return a;
}

/* --- numbers ----------------------------------------------------------- */

/* A literal in a message, shortened if long, so that no message is cut
 * short by its buffer. */
static int shown(size_t len)
{
    return len > 40 ? 40 : (int)len;
}

static const char *ellipsis(size_t len)
{
    return len > 40 ? "..." : "";
}

bool moop_number_read(const char *s, size_t len, MoopNumber *out,
                      char *err, size_t errlen)
{
    Wide limit = part_limit(), lim10, last;
    w_divmod(limit, w_from(10), &lim10, &last);

    bool neg = len > 0 && s[0] == '-';
    Wide part[2] = { w_from(0), w_from(0) };
    size_t digits[2] = { 0, 0 };
    int k = 0;
    for (size_t i = neg ? 1 : 0; i < len; i++) {
        if (s[i] == '/' && k == 0) {
            k = 1;
            continue;
        }
        if (s[i] < '0' || s[i] > '9')
            goto malformed;
        uint64_t d = (uint64_t)(s[i] - '0');
        int c = w_cmp(part[k], lim10);
        if (c > 0 || (c == 0 && d > w_lo(last))) {
            snprintf(err, errlen,
                     "%.*s%s has a part too large to read: each part of a "
                     "literal is at most 170141183460469231731687303715884105727",
                     shown(len), s, ellipsis(len));
            return false;
        }
        /* part * 10 + d, exact: part is at most (2^127 - 1) / 10 here */
        Wide twice = w_shl1(part[k]);
        part[k] = w_add(w_add(twice, w_shl1(w_shl1(twice))), w_from(d));
        digits[k]++;
    }
    if (digits[0] == 0 || (k == 1 && digits[1] == 0))
        goto malformed;

    Wide num = part[0], den = k == 1 ? part[1] : w_from(1);
    if (w_zero(den)) {
        snprintf(err, errlen, "%.*s%s has a denominator of 0",
                 shown(len), s, ellipsis(len));
        return false;
    }
    if (w_zero(num)) {
        *out = (MoopNumber){ 0, 1 };  /* -0 and 0/5 are 0 */
        return true;
    }
    Wide g = w_gcd(num, den), rem;
    w_divmod(num, g, &num, &rem);
    w_divmod(den, g, &den, &rem);
    Wide bound = w_from(MOOP_NUMBER_BOUND);
    if (w_cmp(num, bound) > 0 || w_cmp(den, bound) > 0) {
        snprintf(err, errlen,
                 "%.*s%s cannot be represented: reduced, its numerator and "
                 "denominator must be at most 9223372036854775807",
                 shown(len), s, ellipsis(len));
        return false;
    }
    int64_t p = (int64_t)w_lo(num);
    *out = (MoopNumber){ neg ? -p : p, (int64_t)w_lo(den) };
    return true;

malformed:
    snprintf(err, errlen, "%.*s%s is not a number", shown(len), s,
             ellipsis(len));
    return false;
}

MoopNumber moop_number_whole(int64_t n)
{
    return (MoopNumber){ n, 1 };
}

bool moop_number_is_whole(MoopNumber n)
{
    return n.q == 1;
}

bool moop_number_equal(MoopNumber a, MoopNumber b)
{
    return a.p == b.p && a.q == b.q;
}

size_t moop_number_text(MoopNumber n, char *buf, size_t cap)
{
    int w = n.q == 1 ? snprintf(buf, cap, "%" PRId64, n.p)
                     : snprintf(buf, cap, "%" PRId64 "/%" PRId64, n.p, n.q);
    return w < 0 ? 0 : (size_t)w;
}
