/* Selvage runtime for the C23 backend.
 *
 * Every operation is defined (R8): integer arithmetic wraps through C23's
 * <stdckdint.h>, division by zero and out-of-range indices are refused with a
 * message, float-to-integer conversion saturates, and shifts mask their count.
 * The journal keeps the complements of declared losses until a commit.
 */
#ifndef SELVAGE_RT_H
#define SELVAGE_RT_H

/* POSIX is used only by the host decider (temp file, popen, memory streams). */
#ifndef _POSIX_C_SOURCE
#define _POSIX_C_SOURCE 200809L
#endif

#include <inttypes.h>
#include <math.h>
#include <pthread.h>
#include <stdbool.h>
#include <stdckdint.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

[[noreturn]] static void sv_fault(const char *msg) {
    fflush(stdout);
    fprintf(stderr, "selvage: refused: %s\n", msg);
    exit(70);
}

/* ---- depth (R8) --------------------------------------------------------
 * A run nests rule calls to a bound, the same bound and the same count as in the
 * interpreter: one for each rule invocation in progress; a self tail call is a loop
 * and adds none.  Each rule function is passed the depth of its invocation and checks
 * it on entry.  The bound is fixed when the program is built (-DSV_DEPTH=N), so a
 * check on a depth the compiler knows costs nothing.  Beyond the bound the run is
 * refused, never crashed: the program runs on a stack reserved for the bound
 * (SV_FRAME bytes a call), and the build refuses any function whose frame is larger
 * than half of that. */
#ifndef SV_DEPTH
#define SV_DEPTH 10000
#endif
#define SV_FRAME 32768

[[noreturn]] static void sv_fault_depth(void) {
    fflush(stdout);
    fprintf(stderr, "selvage: refused: the run nests deeper than %lld rule calls\n", (long long)SV_DEPTH);
    exit(70);
}

static void (*sv_entry)(void);
static void *sv_run(void *unused) { (void)unused; sv_entry(); return NULL; }

static void sv_start(void (*entry)(void)) {
    pthread_attr_t attr;
    pthread_t thread;
    size_t stack = (size_t)SV_DEPTH * SV_FRAME + (1u << 20);
    sv_entry = entry;
    if (pthread_attr_init(&attr) || pthread_attr_setstacksize(&attr, stack) ||
        pthread_create(&thread, &attr, sv_run, NULL)) {
        fflush(stdout);
        fprintf(stderr, "selvage: refused: cannot reserve a stack for a depth of %lld rule calls\n",
                (long long)SV_DEPTH);
        exit(70);
    }
    pthread_join(thread, NULL);
}

[[noreturn]] static void sv_fault_index(uint64_t i, int64_t len) {
    fflush(stdout);
    fprintf(stderr, "selvage: refused: index %" PRId64 " is outside 0 to %" PRId64 "\n",
            (int64_t)i, len - 1);
    exit(70);
}

/* ---- the journal ------------------------------------------------------ */
typedef struct {
    unsigned char *buf;
    size_t len, cap;
    uint64_t pending_bits; /* bits held: hidden loss, recoverable by rewind */
    uint64_t epsilon;      /* bits pruned at commits */
} sv_journal_t;

static sv_journal_t sv_j;

/* The bits that tell n things apart: 0 for one thing, else the ceiling of log2 n (VII.5). */
static inline uint64_t sv_clog2(uint64_t n) { uint64_t b = 0; while (b < 63 && (UINT64_C(1) << b) < n) b++; return b; }

static void sv_jpush(const void *p, size_t n, uint64_t bits) {
    if (sv_j.len + n > sv_j.cap) {
        size_t cap = sv_j.cap ? sv_j.cap : 4096;
        while (cap < sv_j.len + n) cap *= 2;
        unsigned char *nb = realloc(sv_j.buf, cap);
        if (!nb) sv_fault("out of memory for the journal");
        sv_j.buf = nb;
        sv_j.cap = cap;
    }
    if (n) memcpy(sv_j.buf + sv_j.len, p, n);
    sv_j.len += n;
    sv_j.pending_bits += bits;
}

static void sv_commit(void) {
    sv_j.epsilon += sv_j.pending_bits;
    sv_j.pending_bits = 0;
    sv_j.len = 0;
}

static void sv_report(void) {
    if (getenv("SELVAGE_STATS"))
        fprintf(stderr, "epsilon=%" PRIu64 " journal_bits=%" PRIu64 "\n", sv_j.epsilon, sv_j.pending_bits);
}

/* ---- wrapping integer arithmetic ------------------------------------- */
#define SV_SIGNED(T, N, UT, MIN, MAX, BITS)                                                       \
    static inline T sv_add_##N(T a, T b) { T r; (void)ckd_add(&r, a, b); return r; }              \
    static inline T sv_sub_##N(T a, T b) { T r; (void)ckd_sub(&r, a, b); return r; }              \
    static inline T sv_mul_##N(T a, T b) { T r; (void)ckd_mul(&r, a, b); return r; }              \
    static inline T sv_neg_##N(T a) { T r; (void)ckd_sub(&r, (T)0, a); return r; }               \
    static inline T sv_div_##N(T a, T b) {                                                        \
        if (b == 0) sv_fault("division by zero");                                                 \
        if (a == MIN && b == -1) return MIN;                                                      \
        return (T)(a / b);                                                                        \
    }                                                                                             \
    static inline T sv_mod_##N(T a, T b) {                                                        \
        if (b == 0) sv_fault("division by zero");                                                 \
        if (a == MIN && b == -1) return 0;                                                        \
        return (T)(a % b);                                                                        \
    }                                                                                             \
    static inline T sv_to_##N(uint64_t u) {                                                       \
        UT b = (UT)u;                                                                             \
        return b <= (UT)MAX ? (T)b : (T)(-(T)(UT)(~b) - 1);                                       \
    }                                                                                             \
    static inline T sv_shl_##N(T a, uint64_t n) { return sv_to_##N((uint64_t)((UT)a << (n & (BITS - 1)))); } \
    static inline T sv_shr_##N(T a, uint64_t n) {                                                 \
        unsigned s = (unsigned)(n & (BITS - 1));                                                  \
        return a < 0 ? (T)~(T)((T)~a >> s) : (T)(a >> s);                                         \
    }                                                                                             \
    static inline T sv_f64_to_##N(double x) {                                                     \
        if (isnan(x)) return 0;                                                                   \
        if (x <= (double)MIN) return MIN;                                                         \
        if (x >= (double)MAX) return MAX;                                                         \
        return (T)x;                                                                              \
    }

#define SV_UNSIGNED(T, N, MAX, BITS)                                                              \
    static inline T sv_add_##N(T a, T b) { T r; (void)ckd_add(&r, a, b); return r; }              \
    static inline T sv_sub_##N(T a, T b) { T r; (void)ckd_sub(&r, a, b); return r; }              \
    static inline T sv_mul_##N(T a, T b) { T r; (void)ckd_mul(&r, a, b); return r; }              \
    static inline T sv_neg_##N(T a) { T r; (void)ckd_sub(&r, (T)0, a); return r; }               \
    static inline T sv_div_##N(T a, T b) { if (b == 0) sv_fault("division by zero"); return (T)(a / b); } \
    static inline T sv_mod_##N(T a, T b) { if (b == 0) sv_fault("division by zero"); return (T)(a % b); } \
    static inline T sv_to_##N(uint64_t u) { return (T)u; }                                       \
    static inline T sv_shl_##N(T a, uint64_t n) { return (T)(a << (n & (BITS - 1))); }            \
    static inline T sv_shr_##N(T a, uint64_t n) { return (T)(a >> (n & (BITS - 1))); }            \
    static inline T sv_f64_to_##N(double x) {                                                     \
        if (isnan(x) || x <= 0.0) return 0;                                                       \
        if (x >= (double)MAX) return MAX;                                                         \
        return (T)x;                                                                              \
    }

SV_SIGNED(int8_t, i8, uint8_t, INT8_MIN, INT8_MAX, 8)
SV_SIGNED(int16_t, i16, uint16_t, INT16_MIN, INT16_MAX, 16)
SV_SIGNED(int32_t, i32, uint32_t, INT32_MIN, INT32_MAX, 32)
SV_SIGNED(int64_t, i64, uint64_t, INT64_MIN, INT64_MAX, 64)
SV_UNSIGNED(uint8_t, u8, UINT8_MAX, 8)
SV_UNSIGNED(uint16_t, u16, UINT16_MAX, 16)
SV_UNSIGNED(uint32_t, u32, UINT32_MAX, 32)
SV_UNSIGNED(uint64_t, u64, UINT64_MAX, 64)

/* Bit is arithmetic modulo 2: add is XOR and multiply is AND, so
 * `add a * b to c` on bits is exactly ccnot. */
static inline uint8_t sv_add_bit(uint8_t a, uint8_t b) { return (uint8_t)((a ^ b) & 1u); }
static inline uint8_t sv_sub_bit(uint8_t a, uint8_t b) { return (uint8_t)((a ^ b) & 1u); }
static inline uint8_t sv_mul_bit(uint8_t a, uint8_t b) { return (uint8_t)(a & b & 1u); }
static inline uint8_t sv_neg_bit(uint8_t a) { return (uint8_t)(a & 1u); }
static inline uint8_t sv_div_bit(uint8_t a, uint8_t b) { if (!b) sv_fault("division by zero"); return a; }
static inline uint8_t sv_mod_bit(uint8_t a, uint8_t b) { if (!b) sv_fault("division by zero"); (void)a; return 0; }
static inline uint8_t sv_to_bit(uint64_t u) { return (uint8_t)(u & 1u); }
static inline uint8_t sv_shl_bit(uint8_t a, uint64_t n) { (void)n; return a; }
static inline uint8_t sv_shr_bit(uint8_t a, uint64_t n) { (void)n; return a; }
static inline uint8_t sv_f64_to_bit(double x) { return (isnan(x) || x <= 0.0) ? 0 : 1; }

/* ---- sameness: equality on the canonical form ---------------------------
   `was`, patterns and take-backs compare on the canonical form: every NaN is
   the one NaN, and -0.0 differs from 0.0.  The `=` operator stays IEEE 754. */
static inline bool sv_same_f64(double a, double b) {
    if (a != a || b != b) return a != a && b != b;
    return memcmp(&a, &b, sizeof a) == 0;
}
#define SV_SAME(x, y) _Generic((x), double: sv_same_f64((double)(x), (double)(y)), default: ((x) == (y)))

/* ---- arrays: owned buffers, bounds-checked ----------------------------- */
#define SV_ARR(T, N)                                                                               \
    typedef struct { T *data; int64_t len; } sv_a_##N;                                             \
    static inline sv_a_##N sv_arr_new_##N(int64_t n) {                                             \
        if (n < 0) sv_fault("an array length must be non-negative");                               \
        sv_a_##N a = { n ? (T *)calloc((size_t)n, sizeof(T)) : NULL, n };                          \
        if (n && !a.data) sv_fault("out of memory");                                               \
        return a;                                                                                  \
    }                                                                                              \
    static inline T *sv_at_##N(sv_a_##N a, uint64_t i) {                                           \
        if (i >= (uint64_t)a.len) sv_fault_index(i, a.len);                                        \
        return &a.data[i];                                                                         \
    }                                                                                              \
    static inline sv_a_##N sv_arr_copy_##N(sv_a_##N a) {                                           \
        sv_a_##N b = sv_arr_new_##N(a.len);                                                        \
        if (a.len) memcpy(b.data, a.data, sizeof(T) * (size_t)a.len);                              \
        return b;                                                                                  \
    }                                                                                              \
    static inline bool sv_eq_a_##N(sv_a_##N a, sv_a_##N b) {                                       \
        if (a.len != b.len) return false;                                                          \
        for (int64_t i = 0; i < a.len; i++) if (!(a.data[i] == b.data[i])) return false;           \
        return true;                                                                               \
    }                                                                                              \
    static inline bool sv_same_a_##N(sv_a_##N a, sv_a_##N b) {                                     \
        if (a.len != b.len) return false;                                                          \
        for (int64_t i = 0; i < a.len; i++) if (!SV_SAME(a.data[i], b.data[i])) return false;      \
        return true;                                                                               \
    }                                                                                              \
    static inline void sv_free_a_##N(sv_a_##N a) { free(a.data); }

/* ---- printing that matches the interpreter ------------------------------ */
static inline void sv_putc(FILE *o, char c) { fputc(c, o); }
static void sv_print_f64(FILE *o, double x) {
    if (isnan(x)) { fputs("nan", o); return; }
    if (isinf(x)) { fputs(x > 0 ? "inf" : "-inf", o); return; }
    char buf[64];
    for (int p = 1; p <= 17; p++) {
        snprintf(buf, sizeof buf, "%.*e", p - 1, x);
        if (strtod(buf, NULL) == x) break;
    }
    char digits[32];
    int nd = 0;
    int neg = buf[0] == '-';
    const char *s = buf + neg;
    for (; *s && *s != 'e'; s++)
        if (*s >= '0' && *s <= '9') digits[nd++] = *s;
    int ex = atoi(s + 1);
    while (nd > 1 && digits[nd - 1] == '0') nd--;
    if (neg) sv_putc(o, '-');
    if (ex >= -4 && ex < 16) {
        if (ex >= 0) {
            for (int i = 0; i <= ex; i++) sv_putc(o, i < nd ? digits[i] : '0');
            sv_putc(o, '.');
            if (nd > ex + 1) for (int i = ex + 1; i < nd; i++) sv_putc(o, digits[i]);
            else sv_putc(o, '0');
        } else {
            fputs("0.", o);
            for (int i = 0; i < -ex - 1; i++) sv_putc(o, '0');
            for (int i = 0; i < nd; i++) sv_putc(o, digits[i]);
        }
    } else {
        sv_putc(o, digits[0]);
        if (nd > 1) { sv_putc(o, '.'); for (int i = 1; i < nd; i++) sv_putc(o, digits[i]); }
        fprintf(o, "e%+03d", ex);
    }
}

static inline void sv_print_i8(FILE *o, int8_t x) { fprintf(o, "%" PRId8, x); }
static inline void sv_print_i16(FILE *o, int16_t x) { fprintf(o, "%" PRId16, x); }
static inline void sv_print_i32(FILE *o, int32_t x) { fprintf(o, "%" PRId32, x); }
static inline void sv_print_i64(FILE *o, int64_t x) { fprintf(o, "%" PRId64, x); }
static inline void sv_print_u8(FILE *o, uint8_t x) { fprintf(o, "%" PRIu8, x); }
static inline void sv_print_u16(FILE *o, uint16_t x) { fprintf(o, "%" PRIu16, x); }
static inline void sv_print_u32(FILE *o, uint32_t x) { fprintf(o, "%" PRIu32, x); }
static inline void sv_print_u64(FILE *o, uint64_t x) { fprintf(o, "%" PRIu64, x); }
static inline void sv_print_bit(FILE *o, uint8_t x) { fputc(x ? '1' : '0', o); }
static inline void sv_print_bool(FILE *o, bool x) { fputs(x ? "true" : "false", o); }
static inline void sv_print_text(FILE *o, const char *x) { fputs(x, o); }

/* ---- Trit: the third truth value ----------------------------------------
 * Two bits, (known, value): false = 10, true = 11, maybe = 00.  Deciding
 * writes the known bit.  Kleene's strong logic is a few bit operations, the
 * same circuit ccnot builds with ancillas. */
enum { SV_MAYBE = 0, SV_FALSE = 2, SV_TRUE = 3 };
static inline uint8_t sv_trit_of_bool(bool b) { return b ? SV_TRUE : SV_FALSE; }
static inline uint8_t sv_k3_and(uint8_t a, uint8_t b) {
    unsigned k1 = a >> 1, v1 = a & 1u, k2 = b >> 1, v2 = b & 1u;
    unsigned known = (k1 & k2) | (k1 & !v1) | (k2 & !v2), value = v1 & v2;
    return (uint8_t)((known << 1) | value);
}
static inline uint8_t sv_k3_or(uint8_t a, uint8_t b) {
    unsigned k1 = a >> 1, v1 = a & 1u, k2 = b >> 1, v2 = b & 1u;
    unsigned known = (k1 & k2) | (k1 & v1) | (k2 & v2), value = v1 | v2;
    return (uint8_t)((known << 1) | value);
}
static inline uint8_t sv_k3_not(uint8_t a) {
    unsigned k = a >> 1, v = a & 1u;
    return (uint8_t)((k << 1) | (k & !v));
}
static inline void sv_print_trit(FILE *o, uint8_t x) {
    fputs(x == SV_TRUE ? "true" : (x == SV_FALSE ? "false" : "maybe"), o);
}

/* ---- decisions: the world's answer to settle ----------------------------- */
static void sv_json_text(FILE *o, const char *s) {
    fputc('"', o);
    for (; *s; s++) {
        unsigned char c = (unsigned char)*s;
        if (c == '"' || c == '\\') { fputc('\\', o); fputc(c, o); }
        else if (c == '\n') fputs("\\n", o);
        else if (c < 0x20) fprintf(o, "\\u%04x", c);
        else fputc(c, o);
    }
    fputc('"', o);
}

static uint64_t sv_fnv1a(const char *s) {
    uint64_t h = UINT64_C(14695981039346656037);
    for (; *s; s++) { h ^= (unsigned char)*s; h *= UINT64_C(1099511628211); }
    return h;
}

/* Settle one undecided question.  SELVAGE_DECIDE chooses the decider:
 * refuse (default), true, false, or command:CMD, where CMD reads the question
 * as JSON on stdin and prints true, false or maybe. */
static bool sv_decide_world(const char *question, const char *context_json, const char *key_text,
                            const char *definitions_json, int line) {
    const char *spec = getenv("SELVAGE_DECIDE");
    int reply = -1;
    if (spec && strcmp(spec, "true") == 0) reply = 1;
    else if (spec && strcmp(spec, "false") == 0) reply = 0;
    else if (spec && strncmp(spec, "command:", 8) == 0) {
        char path[] = "/tmp/selvage-question-XXXXXX";
        int fd = mkstemp(path);
        if (fd < 0) sv_fault("cannot write the question for the decider");
        FILE *q = fdopen(fd, "w");
        fputs("{\"question\": ", q); sv_json_text(q, question);
        fprintf(q, ", \"context\": %s, \"key\": \"%016" PRIx64 "\", \"definitions\": %s}",
                context_json, sv_fnv1a(key_text), definitions_json);
        fclose(q);
        size_t n = strlen(spec + 8) + strlen(path) + 8;
        char *cmd = malloc(n);
        snprintf(cmd, n, "%s < %s", spec + 8, path);
        FILE *p = popen(cmd, "r");
        char word[32] = {0};
        if (p && fscanf(p, "%31s", word) == 1) {
            if (strcmp(word, "true") == 0) reply = 1;
            else if (strcmp(word, "false") == 0) reply = 0;
        }
        if (p) pclose(p);
        free(cmd);
        remove(path);
    }
    if (reply < 0) {
        fflush(stdout);
        fprintf(stderr, "selvage: refused: line %d: nobody decided `%s`; it is still maybe\n", line, question);
        exit(70);
    }
    return reply == 1;
}

#endif
