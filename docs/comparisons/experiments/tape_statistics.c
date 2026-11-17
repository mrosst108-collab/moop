/* Wiring 1 on the interpreter's 8/13-cell bodies: the cycle structure of
 * the tape and the statistics of its draws (MAYBE).
 *
 * One epoch, lcm(8, 13) = 104 ticks, returns both heads to cell 0, so the
 * epoch map is a permutation of the 2^21 tape contents; every state's full
 * period is 104 times the length of its cycle under that map.
 *
 * From the repository root:
 *   cc -std=c2x -O2 -Isrc docs/comparisons/experiments/tape_statistics.c \
 *      src/tapeloop.c src/gates.c src/logic.c -o build/tape_statistics
 *   build/tape_statistics          (about 6 seconds) */
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

static void cycles(void)
{
    uint8_t *seen = calloc(N, 1);
    uint64_t hist[23] = {0}, count = 0, fixed = 0, longest = 0, short_ = 0;
    for (uint32_t s0 = 0; s0 < N; s0++) {
        if (seen[s0])
            continue;
        uint64_t len = 0;
        uint32_t s = s0;
        do {
            seen[s] = 1;
            s = epoch(s);
            len++;
        } while (s != s0);
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
    return 0;
}
