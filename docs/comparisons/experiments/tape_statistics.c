/* Wiring 1 on the interpreter's 8/13-cell bodies: the cycle structure of
 * the tape, the statistics of its draws (MAYBE), and how they change if a
 * draw observed a different point of the same dynamics.
 *
 * One epoch, lcm(8, 13) = 104 ticks, returns both heads to cell 0, so the
 * epoch map is a permutation of the 2^21 tape contents; every state's full
 * period is 104 times the length of its cycle under that map.
 *
 * From the repository root:
 *   cc -std=c2x -O2 -Isrc docs/comparisons/experiments/tape_statistics.c \
 *      src/tapeloop.c src/gates.c src/logic.c -lm -o build/tape_statistics
 *   build/tape_statistics          (about a minute and a half) */
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include "logic.h"
#include "tapeloop.h"

enum { LA = 8, LB = 13, N = 1 << (LA + LB), EPOCH = 104 };
static bool a[LA], b[LB], ma[LA], mb[LB];
static MoopCore core;

static void load(uint32_t s)
{
    moop_core_init(&core, a, ma, LA, b, mb, LB);
    for (int k = 0; k < LA; k++)
        a[k] = (s >> k) & 1;
    for (int k = 0; k < LB; k++)
        b[k] = (s >> (LA + k)) & 1;
}

static uint32_t pack(void)
{
    uint32_t s = 0;
    for (int k = 0; k < LA; k++)
        s |= (uint32_t)a[k] << k;
    for (int k = 0; k < LB; k++)
        s |= (uint32_t)b[k] << (LA + k);
    return s;
}

static uint32_t epoch(uint32_t s)
{
    load(s);
    for (int t = 0; t < EPOCH; t++)
        moop_maybe(&core);
    return pack();
}

static uint32_t *period_of; /* cycle length under the epoch map, per state */

static void cycles(void)
{
    uint8_t *seen = calloc(N, 1);
    uint32_t *cycle = malloc(sizeof *cycle * N);
    period_of = malloc(sizeof *period_of * N);
    uint64_t hist[23] = {0}, count = 0, fixed = 0, longest = 0, short_ = 0;
    for (uint32_t s0 = 0; s0 < N; s0++) {
        if (seen[s0])
            continue;
        uint64_t len = 0;
        uint32_t s = s0;
        do {
            seen[s] = 1;
            cycle[len++] = s;
            s = epoch(s);
        } while (s != s0);
        for (uint64_t i = 0; i < len; i++)
            period_of[cycle[i]] = (uint32_t)len;
        count++;
        fixed += len == 1;
        short_ += len <= 4 ? len : 0;
        if (len > longest)
            longest = len;
        int lg = 0;
        while ((1ull << (lg + 1)) <= len)
            lg++;
        hist[lg] += len;
    }
    free(seen);
    free(cycle);
    printf("cycles of the epoch map over %d states: %llu\n", N,
           (unsigned long long)count);
    printf("  states with period <= 104 draws: %llu; <= 416 draws: %llu (%.2f%%)\n",
           (unsigned long long)fixed, (unsigned long long)short_,
           100.0 * short_ / N);
    printf("  longest period: %llu draws (of %llu states with heads)\n",
           (unsigned long long)(longest * EPOCH),
           (unsigned long long)N * EPOCH);
    for (int i = 0; i < 23; i++)
        if (hist[i])
            printf("  period %9llu to %9llu draws: %6.2f%% of states\n",
                   (unsigned long long)(EPOCH << i),
                   (unsigned long long)(EPOCH << (i + 1)) - 1,
                   100.0 * hist[i] / N);
}

/* along one full cycle: bias, adjacent pairs, and agreement with the draw
 * k places back (0.5 means no correlation at that lag) */
static void draws(const char *name, uint32_t s0)
{
    load(s0);
    uint64_t n = 0, ones = 0, pair[4] = {0}, agree[3] = {0};
    const int lag[3] = {LA, LB, EPOCH};
    static uint8_t ring[EPOCH];
    int prev = -1;
    for (;;) {
        bool d = moop_maybe(&core);
        if (n >= EPOCH)
            for (int i = 0; i < 3; i++)
                agree[i] += d == ring[(n - lag[i]) % EPOCH];
        ring[n % EPOCH] = d;
        if (prev >= 0)
            pair[prev * 2 + d]++;
        prev = d;
        ones += d;
        n++;
        if (n % EPOCH == 0 && pack() == s0)
            break;
    }
    double m = (double)(n - EPOCH), p = (double)(n - 1);
    printf("%s: period %llu draws\n", name, (unsigned long long)n);
    printf("  ones %.4f; pairs 00 %.4f 01 %.4f 10 %.4f 11 %.4f\n",
           (double)ones / n, pair[0] / p, pair[1] / p, pair[2] / p,
           pair[3] / p);
    printf("  agreement with the draw %d back %.4f, %d back %.4f, %d back %.4f\n",
           lag[0], agree[0] / m, lag[1], agree[1] / m, lag[2], agree[2] / m);
}

/* The same dynamics observed four ways: does moving the observation point
 * remove the lag correlation, or only move it? */
typedef bool (*Observe)(const MoopCore *);
static bool obs_a(const MoopCore *c) { return c->a.cells[c->a.head]; }
static bool obs_b(const MoopCore *c) { return c->b.cells[c->b.head]; }
static bool obs_a_xor_b(const MoopCore *c)
{
    return c->a.cells[c->a.head] ^ c->b.cells[c->b.head];
}
static bool obs_a_parity(const MoopCore *c)
{
    bool p = false;
    for (size_t k = 0; k < c->a.len; k++)
        p ^= c->a.cells[k];
    return p;
}

static void observation(const char *name, Observe obs, uint32_t s0)
{
    enum { NL = 6 };
    const int lag[NL] = {1, 2, LA, LB, LA + LB, EPOCH};
    static uint8_t ring[EPOCH];
    uint64_t n = 0, agree[NL] = {0};
    load(s0);
    for (;;) {
        moop_core_step(&core);
        bool d = obs(&core);
        if (n >= EPOCH)
            for (int i = 0; i < NL; i++)
                agree[i] += d == ring[(n - lag[i]) % EPOCH];
        ring[n % EPOCH] = d;
        n++;
        if (n % EPOCH == 0 && pack() == s0)
            break;
    }
    printf("  %-32s", name);
    for (int i = 0; i < NL; i++)
        printf(" %3d:%.3f", lag[i], agree[i] / (double)(n - EPOCH));
    printf("\n");
}

/* Every lag 1..104 along one cycle: the worst agreement, and the sampling
 * noise it should be compared with (about 0.5 / sqrt(draws)). */
static void lag_scan(const char *name, Observe obs, uint32_t s0)
{
    static uint8_t ring[EPOCH + 1];
    uint64_t agree[EPOCH + 1] = {0}, n = 0;
    load(s0);
    for (;;) {
        moop_core_step(&core);
        bool d = obs(&core);
        if (n >= EPOCH)
            for (int l = 1; l <= EPOCH; l++)
                agree[l] += d == ring[(n - l) % (EPOCH + 1)];
        ring[n % (EPOCH + 1)] = d;
        n++;
        if (n % EPOCH == 0 && pack() == s0)
            break;
    }
    double m = (double)(n - EPOCH), worst = 0.5;
    int at = 1;
    for (int l = 1; l <= EPOCH; l++) {
        double v = agree[l] / m;
        if (fabs(v - 0.5) > fabs(worst - 0.5)) {
            worst = v;
            at = l;
        }
    }
    printf("  %-28s %9llu draws: worst lag %3d at %.4f (noise ~%.4f)\n", name,
           (unsigned long long)n, at, worst, 0.5 / sqrt(m));
}

/* Births over every parent state, seeded in src/proto.c's order (A's cells,
 * then B's), each cell one draw through the given observation. */
static void births(const char *name, Observe obs)
{
    uint64_t ba = 0, bb = 0, ap = 0;
    for (uint32_t s = 0; s < N; s++) {
        bool ca[LA], cb[LB];
        load(s);
        for (int k = 0; k < LA; k++) {
            moop_core_step(&core);
            ca[k] = obs(&core);
        }
        for (int k = 0; k < LB; k++) {
            moop_core_step(&core);
            cb[k] = obs(&core);
        }
        for (int k = 0; k < LA; k++) {
            ba += cb[k] == ca[k];
            ap += ca[k] == ((s >> k) & 1);
        }
        for (int k = 0; k < LB - LA; k++)
            bb += cb[k + LA] == cb[k];
    }
    printf("  %-28s child B[k]=A[k] %.4f; B[k+8]=B[k] %.4f; "
           "child A[k]=parent's A[k] %.4f\n", name,
           (double)ba / ((double)N * LA), (double)bb / ((double)N * (LB - LA)),
           (double)ap / ((double)N * LA));
}

/* What births can produce, over every parent: agreement for all 210 pairs
 * of child cells, how many distinct children exist, and how the child's
 * period compares with all states. Child bit i is cell i of A for i < 8,
 * cell i - 8 of B after (src/proto.c's seeding order). */
static int period_bucket(uint32_t epochs)
{
    return epochs <= 4 ? 0 : epochs <= 1024 ? 1 : epochs <= 32768 ? 2
         : epochs <= 131072 ? 3 : 4;
}

static void children(const char *name, Observe obs)
{
    enum { C = LA + LB };
    static const char *bucket[5] = {"<=416", "<=106K", "<=3.4M", "<=13.6M",
                                    "<=54.5M"};
    static uint64_t same[C][C];
    uint64_t born_in[5] = {0}, all_in[5] = {0}, distinct = 0;
    uint8_t *born = calloc(N, 1);
    for (int i = 0; i < C; i++)
        for (int j = 0; j < C; j++)
            same[i][j] = 0;
    for (uint32_t parent = 0; parent < N; parent++) {
        uint32_t child = 0;
        load(parent);
        for (int i = 0; i < C; i++) {
            moop_core_step(&core);
            child |= (uint32_t)obs(&core) << i;
        }
        distinct += !born[child];
        born[child] = 1;
        born_in[period_bucket(period_of[child])]++;
        all_in[period_bucket(period_of[parent])]++;
        for (int i = 0; i < C; i++)
            for (int j = i + 1; j < C; j++)
                same[i][j] += ((child >> i) & 1) == ((child >> j) & 1);
    }
    free(born);
    double worst = 0.5;
    int off = 0;
    for (int i = 0; i < C; i++)
        for (int j = i + 1; j < C; j++) {
            double v = (double)same[i][j] / N;
            off += fabs(v - 0.5) > 0.05;
            if (fabs(v - 0.5) > fabs(worst - 0.5))
                worst = v;
        }
    printf("  %-10s cell pairs outside 45-55%%: %3d of 210 (worst %.4f); "
           "distinct children %7llu (%.2f%%)\n", name, off, worst,
           (unsigned long long)distinct, 100.0 * distinct / N);
    printf("  %-10s child's period in draws:", "");
    for (int k = 0; k < 5; k++)
        printf(" %s %.2f%% (all %.2f%%)", bucket[k], 100.0 * born_in[k] / N,
               100.0 * all_in[k] / N);
    printf("\n");
}

/* Behavioural diversity: how many distinct draw sequences children produce
 * over their first 21 and 64 draws, each under its wiring's own
 * observation (bounded above by the number of distinct bodies). */
static uint64_t first_draws(uint32_t state, Observe obs, int n)
{
    uint64_t d = 0;
    load(state);
    for (int i = 0; i < n; i++) {
        moop_core_step(&core);
        d |= (uint64_t)obs(&core) << i;
    }
    return d;
}

static int by_value(const void *x, const void *y)
{
    uint64_t p = *(const uint64_t *)x, q = *(const uint64_t *)y;
    return (p > q) - (p < q);
}

static uint64_t count_distinct(uint64_t *v)
{
    qsort(v, N, sizeof *v, by_value);
    uint64_t d = 1;
    for (size_t i = 1; i < N; i++)
        d += v[i] != v[i - 1];
    return d;
}

static void behaviour(const char *name, Observe obs)
{
    uint64_t *p21 = malloc(sizeof *p21 * N), *p64 = malloc(sizeof *p64 * N);
    uint64_t *all = malloc(sizeof *all * N);
    for (uint32_t parent = 0; parent < N; parent++) {
        uint32_t child = (uint32_t)first_draws(parent, obs, LA + LB);
        p21[parent] = first_draws(child, obs, 21);
        p64[parent] = first_draws(child, obs, 64);
        all[parent] = first_draws(parent, obs, 64);
    }
    printf("  %-10s distinct children's first 21 draws %7llu, first 64 %7llu "
           "(all states, first 64: %7llu)\n", name,
           (unsigned long long)count_distinct(p21),
           (unsigned long long)count_distinct(p64),
           (unsigned long long)count_distinct(all));
    free(p21);
    free(p64);
    free(all);
}

int main(void)
{
    cycles();
    uint32_t seed = 0; /* the seed of tests/tape_vectors.txt */
    for (int k = 0; k < LA; k++)
        seed |= (uint32_t)((k * k + 1) % 2) << k;
    for (int k = 0; k < LB; k++)
        seed |= (uint32_t)(((k * 5) / 3 + 1) % 2) << (LA + k);
    draws("the trace's seed", seed);
    draws("one set cell on each tape (the longest cycle)", 1u | 1u << LA);
    printf("the trace's seed, agreement by lag for four observation points:\n");
    observation("A under its head (wiring 1)", obs_a, seed);
    observation("B under its head", obs_b, seed);
    observation("A xor B under the heads", obs_a_xor_b, seed);
    observation("parity of all of A", obs_a_parity, seed);
    printf("every lag 1..104, wiring 1 against the wiring-2 candidate:\n");
    lag_scan("wiring 1, trace seed", obs_a, seed);
    lag_scan("A xor B, trace seed", obs_a_xor_b, seed);
    lag_scan("wiring 1, longest cycle", obs_a, 1u | 1u << LA);
    lag_scan("A xor B, longest cycle", obs_a_xor_b, 1u | 1u << LA);
    printf("births over all %d parents:\n", N);
    births("wiring 1", obs_a);
    births("A xor B", obs_a_xor_b);
    printf("what births can produce, over all %d parents:\n", N);
    children("wiring 1", obs_a);
    children("A xor B", obs_a_xor_b);
    printf("how children behave, over all %d parents:\n", N);
    behaviour("wiring 1", obs_a);
    behaviour("A xor B", obs_a_xor_b);
    return 0;
}
