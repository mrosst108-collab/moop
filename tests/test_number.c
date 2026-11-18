/* Unit tests for src/number.c (docs/foundations.md, F4, F5, F8, U1).
 *
 * `make test` builds this file twice: once with the compiler's native
 * 128-bit integers where it has them, and once with MOOP_PORTABLE_WIDE,
 * which forces the portable implementation. Both must pass the same
 * checks, so the two implementations agree on every case below. */
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include "number.h"

static int failures;

static void check(bool ok, const char *desc)
{
    printf("%s - %s\n", ok ? "ok  " : "FAIL", desc);
    if (!ok)
        failures = 1;
}

/* the literal reads as p/q exactly */
static bool reads(const char *text, int64_t p, int64_t q)
{
    MoopNumber n;
    char err[256];
    return moop_number_read(text, strlen(text), &n, err, sizeof err) &&
           n.p == p && n.q == q;
}

/* the literal is refused, and the reason contains `why` */
static bool refused(const char *text, const char *why)
{
    MoopNumber n;
    char err[256] = "";
    return !moop_number_read(text, strlen(text), &n, err, sizeof err) &&
           strstr(err, why) != NULL;
}

static bool prints(const char *text, const char *expected)
{
    MoopNumber n;
    char err[256], out[MOOP_NUMBER_TEXT_MAX];
    if (!moop_number_read(text, strlen(text), &n, err, sizeof err))
        return false;
    moop_number_text(n, out, sizeof out);
    return strcmp(out, expected) == 0;
}

static int64_t gcd64(int64_t a, int64_t b)
{
    if (a < 0)
        a = -a;
    while (b != 0) {
        int64_t t = a % b;
        a = b;
        b = t;
    }
    return a;
}

#define M INT64_MAX
#define L "170141183460469231731687303715884105727"       /* 2^127 - 1 */
#define L1 "170141183460469231731687303715884105728"      /* 2^127 */
#define TWO128 "340282366920938463463374607431768211456"  /* 2^128 */

int main(void)
{
#if defined(__SIZEOF_INT128__) && !defined(MOOP_PORTABLE_WIDE)
    const char *expected = "native";
#else
    const char *expected = "portable";
#endif
    printf("wide: %s\n", moop_number_wide());
    check(strcmp(moop_number_wide(), expected) == 0,
          "the build uses the implementation it was asked for");

    /* canonical form: integers, negatives, zero, fractions */
    check(reads("0", 0, 1) && reads("-0", 0, 1) && reads("0/5", 0, 1) &&
              reads("-0/7", 0, 1),
          "zero is 0/1, whatever its spelling, with no negative zero");
    check(reads("7", 7, 1) && reads("-7", -7, 1), "integers have denominator 1");
    check(reads("10/4", 5, 2) && reads("-10/4", -5, 2) && reads("9/5", 9, 5),
          "fractions are reduced on reading, the sign on the numerator");
    check(reads("000012/0004", 3, 1), "leading zeros are digits like any other");
    check(reads("4/2", 2, 1), "a fraction that reduces to a whole number is one");

    /* the runtime bounds: |p| <= 2^63 - 1, q <= 2^63 - 1 */
    check(reads("9223372036854775807", M, 1) &&
              reads("-9223372036854775807", -M, 1),
          "the largest and smallest numerators are read");
    check(reads("1/9223372036854775807", 1, M), "the largest denominator is read");
    check(refused("9223372036854775808", "cannot be represented") &&
              refused("-9223372036854775808", "cannot be represented"),
          "one past either numerator bound is refused (no signed minimum)");
    check(refused("1/9223372036854775808", "cannot be represented"),
          "one past the denominator bound is refused");

    /* parts beyond 64 bits are read exactly, then reduced */
    check(reads("18446744073709551614/2", M, 1) &&
              reads("-18446744073709551614/2", -M, 1),
          "a reducible literal with a part beyond 64 bits reads");
    check(reads("85070591730234615865843651857942052864/18446744073709551616",
                4611686018427387904, 1),
          "2^126 / 2^64 reads as 2^62: both parts beyond 64 bits");
    check(refused("18446744073709551616/2", "cannot be represented"),
          "a reduction that does not fit is refused (2^64 / 2 = 2^63)");

    /* the bound on reading a part: 2^127 - 1, the same for both signs */
    check(reads(L "/" L, 1, 1) && reads("-" L "/" L, -1, 1),
          "a part of exactly 2^127 - 1 is read, with either sign");
    check(refused(L, "cannot be represented"),
          "2^127 - 1 is read, and refused only because it does not fit");
    check(refused(L1 "/2", "too large to read") &&
              refused("-" L1 "/2", "too large to read") &&
              refused("2/" L1, "too large to read"),
          "a part of 2^127 is refused as too large to read, either sign or place");
    check(refused(TWO128 "/" TWO128, "too large to read"),
          "a part beyond the bound is refused even where it would reduce to 1");
    check(reads("00000000000000000000000000000000000000000000000005", 5, 1),
          "many leading zeros do not make a part large");

    /* malformed and undefined */
    check(refused("5/0", "denominator of 0") && refused("0/0", "denominator of 0") &&
              refused("-3/000", "denominator of 0"),
          "a denominator of 0 is refused");
    check(refused("", "is not a number") && refused("-", "is not a number") &&
              refused("5/", "is not a number") && refused("/5", "is not a number") &&
              refused("5/-3", "is not a number") && refused("1/2/3", "is not a number"),
          "text that is not a literal is refused");

    /* printing: canonical, and it reads back as an equal number */
    check(prints("0", "0") && prints("-0", "0") && prints("7", "7") &&
              prints("-7", "-7") && prints("10/4", "5/2") && prints("-9/5", "-9/5") &&
              prints("18446744073709551614/2", "9223372036854775807") &&
              prints("1/9223372036854775807", "1/9223372036854775807"),
          "an integer prints without /1, a fraction reduced, the sign in front");

    /* equality is exact */
    MoopNumber a, b;
    char err[256];
    moop_number_read("2/3", 3, &a, err, sizeof err);
    moop_number_read("4/6", 3, &b, err, sizeof err);
    bool eq = moop_number_equal(a, b);
    moop_number_read("1/3", 3, &b, err, sizeof err);
    check(eq && !moop_number_equal(a, b), "2/3 equals 4/6, and not 1/3");

    /* many literals from a fixed generator: canonical, and printing
     * reads back as an equal number */
    uint64_t state = 0x6d6f6f70;  /* fixed: the run is reproducible */
    int canonical = 0, round_trips = 0, cases = 20000;
    for (int i = 0; i < cases; i++) {
        state = state * 6364136223846793005u + 1442695040888963407u;
        int64_t p = (int64_t)(state >> 1) >> (state % 63);
        state = state * 6364136223846793005u + 1442695040888963407u;
        uint64_t uq = (state >> 1) >> (state % 63);
        int64_t q = uq == 0 ? 1 : (int64_t)uq;
        if (i % 2)
            p = -p;
        char lit[64], out[MOOP_NUMBER_TEXT_MAX];
        snprintf(lit, sizeof lit, "%" PRId64 "/%" PRId64, p, q);
        MoopNumber n, back;
        if (!moop_number_read(lit, strlen(lit), &n, err, sizeof err))
            continue;
        if (n.q > 0 && gcd64(n.p, n.q) == (n.p == 0 ? n.q : 1) &&
            (n.p != 0 || n.q == 1))
            canonical++;
        moop_number_text(n, out, sizeof out);
        if (moop_number_read(out, strlen(out), &back, err, sizeof err) &&
            moop_number_equal(n, back))
            round_trips++;
    }
    printf("generated literals: %d, canonical %d, read back equal %d\n",
           cases, canonical, round_trips);
    check(canonical == cases && round_trips == cases,
          "20000 generated literals are canonical and read back equal");

    return failures;
}
