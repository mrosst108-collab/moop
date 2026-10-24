/* Experiments behind docs/paper/: the reversibility x homoiconicity
 * analysis of the moop core. Exhaustive results are exact; sampled ones
 * use a fixed-seed generator, so every number reproduces.
 *
 *   cc -std=c2x -O2 -Wall -Wextra -Wpedantic -Isrc \
 *      docs/paper/experiments.c src/tapeloop.c src/gates.c src/logic.c \
 *      src/encode.c -o build/experiments && ./build/experiments [DIR]
 *
 * With DIR, the figure data (orbits.dat, pruning.dat) is written there.
 *
 * E1  closed form: the core is two coupled nonlinear shift registers
 * E2  orbit census of the epoch map, moop's wiring vs. the original
 *     one-target ("Harvard") wiring, every state enumerated; then every
 *     loop pair with a + b <= 22: does each non-trivial orbit rewrite
 *     both loops?
 * E3  how much of program-space the longest 8/13 orbit tours
 * E4  pruning yield vs. tape density
 * E5  rewind lemma: pruning never changes the past of unpruned cells
 * E6  causal marks are derivable by replay
 * E7  MAYBE balance
 * E8  the crossing rule: with the user layer in the loop, the initial
 *     tapes are recoverable from the final tapes plus the transcript of
 *     observations; closed-loop deposits are not injective on the tapes
 *     alone
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "encode.h"
#include "gates.h"
#include "logic.h"
#include "tapeloop.h"

#define MAX_LEN 20

static uint64_t rng_state = UINT64_C(0x9E3779B97F4A7C15);

static uint64_t rng(void) /* xorshift64 */
{
    rng_state ^= rng_state << 13;
    rng_state ^= rng_state >> 7;
    rng_state ^= rng_state << 17;
    return rng_state;
}

typedef struct {
    bool a[MAX_LEN], ma[MAX_LEN], b[MAX_LEN], mb[MAX_LEN];
    MoopCore core;
} Body;

static void body_init(Body *x, size_t la, size_t lb)
{
    moop_core_init(&x->core, x->a, x->ma, la, x->b, x->mb, lb);
}

/* Each cell is set with probability percent/100. Returns the set count. */
static size_t body_fill(Body *x, unsigned percent)
{
    size_t set = 0;
    for (size_t i = 0; i < x->core.a.len; i++)
        set += x->a[i] = rng() % 100 < percent;
    for (size_t i = 0; i < x->core.b.len; i++)
        set += x->b[i] = rng() % 100 < percent;
    return set;
}

/* Tape states as integers: bit i is A cell i, bit la + j is B cell j. */
static uint32_t pack(const MoopCore *c)
{
    uint32_t s = 0;
    for (size_t i = 0; i < c->a.len; i++)
        s |= (uint32_t)c->a.cells[i] << i;
    for (size_t i = 0; i < c->b.len; i++)
        s |= (uint32_t)c->b.cells[i] << (c->a.len + i);
    return s;
}

static void unpack(MoopCore *c, uint32_t s)
{
    for (size_t i = 0; i < c->a.len; i++)
        c->a.cells[i] = s >> i & 1;
    for (size_t i = 0; i < c->b.len; i++)
        c->b.cells[i] = s >> (c->a.len + i) & 1;
}

/* The original wiring (commit 2231ab2): one CCNOT, targeting A only, so
 * loop B is a read-only program tape — the Harvard control. Returns
 * whether the gate fired. */
static bool harvard_step(MoopCore *c)
{
    bool c1 = c->a.cells[c->a.head];
    bool c2 = c->b.cells[c->b.head];
    moop_ccnot(c1, c2, &c->a.cells[(c->a.head + 1) % c->a.len]);
    c->a.head = (c->a.head + 1) % c->a.len;
    c->b.head = (c->b.head + c->b.len - 1) % c->b.len;
    return c1 && c2;
}

/* One epoch from heads (0, 0); the heads return there, so this is a
 * bijection on tape states. *fired reports whether the gate ever fired. */
static uint32_t epoch_map(uint32_t s, size_t la, size_t lb, bool harvard,
                          bool *fired)
{
    Body x;
    body_init(&x, la, lb);
    unpack(&x.core, s);
    size_t epoch = moop_core_epoch(&x.core);
    *fired = false;
    for (size_t t = 0; t < epoch; t++) {
        if (harvard)
            *fired |= harvard_step(&x.core);
        else
            moop_core_step(&x.core);
    }
    for (size_t i = 0; !harvard && i < la; i++)
        *fired |= x.ma[i];
    return pack(&x.core);
}

/* --- E1 ---------------------------------------------------------------
 * x_t, y_t are the cells under A's and B's heads at tick t. Claim:
 *   x_{t+1} = x_{t+1-la} ^ (x_t & y_t)
 *   y_{t+1} = y_{t+1-lb} ^ (x_t & y_t)                                  */
static void closed_form(void)
{
    enum { LA = 8, LB = 13, T = 20000, TRIALS = 50 };
    static bool x[T + 1], y[T + 1];
    long checked = 0, violations = 0;
    for (int trial = 0; trial < TRIALS; trial++) {
        Body body;
        body_init(&body, LA, LB);
        body_fill(&body, 50);
        for (int t = 0; t <= T; t++) {
            x[t] = body.core.a.cells[body.core.a.head];
            y[t] = body.core.b.cells[body.core.b.head];
            if (t < T)
                moop_core_step(&body.core);
        }
        for (int t = LB - 1; t < T; t++) {
            bool g = x[t] && y[t];
            violations += x[t + 1] != (x[t + 1 - LA] ^ g);
            violations += y[t + 1] != (y[t + 1 - LB] ^ g);
            checked++;
        }
    }
    printf("E1 closed form (8/13): %ld ticks checked, %ld violations\n",
           checked, violations);
}

/* --- E2, E3 ------------------------------------------------------------ */
static void tour(uint32_t start, size_t la, size_t lb)
{
    static bool seen_a[1 << MAX_LEN], seen_b[1 << MAX_LEN];
    size_t na = 0, nb = 0;
    uint32_t x = start;
    bool fired;
    do {
        uint32_t a = x & ((UINT32_C(1) << la) - 1), b = x >> la;
        na += !seen_a[a];
        nb += !seen_b[b];
        seen_a[a] = seen_b[b] = true;
        x = epoch_map(x, la, lb, false, &fired);
    } while (x != start);
    printf("E3 the longest %zu/%zu orbit visits %zu of %u B-values and "
           "%zu of %u A-values\n",
           la, lb, nb, 1u << lb, na, 1u << la);
}

typedef struct {
    uint32_t orbits, fixed, rewrite_a, rewrite_b, silent, longest, longest_at;
    uint64_t on_rewriting; /* states on orbits along which B changes */
} Census;

/* Every tape state, grouped into orbits of the epoch map. If lengths is
 * non-NULL, lengths[l] counts the orbits of length l. */
static Census census(size_t la, size_t lb, bool harvard, uint32_t *lengths)
{
    uint32_t n = UINT32_C(1) << (la + lb);
    uint32_t mask_a = (UINT32_C(1) << la) - 1;
    uint8_t *seen = calloc(n, 1);
    if (seen == NULL) {
        perror("calloc");
        exit(1);
    }
    Census c = { 0 };
    bool fired;
    for (uint32_t s = 0; s < n; s++) {
        if (seen[s])
            continue;
        uint32_t x = s, len = 0;
        bool changes_a = false, changes_b = false;
        do {
            seen[x] = 1;
            uint32_t y = epoch_map(x, la, lb, harvard, &fired);
            c.silent += !fired;
            changes_a |= (y & mask_a) != (x & mask_a);
            changes_b |= (y >> la) != (x >> la);
            x = y;
            len++;
        } while (x != s);
        c.orbits++;
        c.fixed += len == 1;
        c.rewrite_a += changes_a;
        c.rewrite_b += changes_b;
        if (changes_b)
            c.on_rewriting += len;
        if (len > c.longest) {
            c.longest = len;
            c.longest_at = s;
        }
        if (lengths != NULL)
            lengths[len]++;
    }
    free(seen);
    return c;
}

static void census_row(size_t la, size_t lb, bool harvard, uint32_t *lengths,
                       Census *out)
{
    Census c = census(la, lb, harvard, lengths);
    uint32_t n = UINT32_C(1) << (la + lb);
    printf("   %2zu/%-2zu %-9s %8u %7u %7u %7u %7u %7u %7u %8u %6.1f%%\n",
           la, lb, harvard ? "harvard" : "moop", n, c.orbits, c.fixed,
           c.orbits - c.fixed, c.rewrite_a, c.rewrite_b, c.silent, c.longest,
           100.0 * (double)c.on_rewriting / n);
    if (out != NULL)
        *out = c;
}

/* Observation 1, widened: every pair 2 <= a <= b with a + b <= 22. */
static void sweep(void)
{
    size_t pairs = 0, coprime = 0, exceptions = 0;
    uint64_t states = 0, nontrivial = 0;
    for (size_t sum = 4; sum <= 22; sum++) {
        for (size_t la = 2; la <= sum / 2; la++) {
            size_t lb = sum - la;
            Census c = census(la, lb, false, NULL);
            size_t x = la, y = lb;
            while (y != 0) {
                size_t t = x % y;
                x = y;
                y = t;
            }
            pairs++;
            coprime += x == 1;
            states += UINT64_C(1) << sum;
            nontrivial += c.orbits - c.fixed;
            if (c.rewrite_a != c.orbits - c.fixed ||
                c.rewrite_b != c.orbits - c.fixed) {
                exceptions++;
                printf("   exception at %zu/%zu: %u non-trivial orbits, "
                       "%u rewrite A, %u rewrite B\n",
                       la, lb, c.orbits - c.fixed, c.rewrite_a, c.rewrite_b);
            }
        }
    }
    printf("E2 sweep: %zu loop pairs (%zu coprime), %llu states, %llu "
           "non-trivial orbits; pairs where some non-trivial orbit leaves a "
           "loop unrewritten: %zu\n",
           pairs, coprime, (unsigned long long)states,
           (unsigned long long)nontrivial, exceptions);
}

/* Fraction of states on orbits no longer than each length, for Fig. 2. */
static void write_lengths(FILE *f, const char *wiring, const uint32_t *lengths,
                          uint32_t n)
{
    uint64_t states = 0;
    for (uint32_t l = 1; l <= n; l++) {
        if (lengths[l] == 0)
            continue;
        states += (uint64_t)lengths[l] * l;
        fprintf(f, "%s\t%u\t%u\t%.6f\n", wiring, l, lengths[l],
                (double)states / n);
    }
}

/* --- E4 ---------------------------------------------------------------- */
static void density(FILE *data)
{
    static const unsigned percents[] = { 2, 4, 6, 8, 10, 20, 30, 40, 50 };
    enum { TRIALS = 4000 };
    printf("E4 first-epoch pruning (8/13, %d trials per density)\n", TRIALS);
    for (size_t p = 0; p < sizeof percents / sizeof percents[0]; p++) {
        size_t set = 0, discarded = 0, runs_pruning = 0;
        for (int t = 0; t < TRIALS; t++) {
            Body body;
            body_init(&body, 8, 13);
            set += body_fill(&body, percents[p]);
            size_t d = moop_core_run(&body.core, moop_core_epoch(&body.core));
            discarded += d;
            runs_pruning += d > 0;
        }
        double inert = set ? 100.0 * (double)discarded / (double)set : 0;
        double hit = 100.0 * (double)runs_pruning / TRIALS;
        printf("   density %2u%%: %5.1f%% of set bits were inert; "
               "prune discarded something in %5.1f%% of runs\n",
               percents[p], inert, hit);
        if (data != NULL)
            fprintf(data, "%u\t%.2f\t%.2f\n", percents[p], inert, hit);
    }
}

/* --- E5 ----------------------------------------------------------------
 * Run k ticks, prune, run k ticks back: every unpruned cell must be at
 * its initial value. */
static void rewind_lemma(void)
{
    static const unsigned percents[] = { 20, 25, 33, 50 };
    enum { TRIALS = 100000 };
    long pruned_runs = 0, mismatches = 0;
    for (int t = 0; t < TRIALS; t++) {
        Body body;
        body_init(&body, 8, 13);
        body_fill(&body, percents[rng() % 4]);
        Body initial = body;
        size_t k = 1 + rng() % moop_core_epoch(&body.core);
        for (size_t i = 0; i < k; i++)
            moop_core_step(&body.core);
        bool pruned_a[MAX_LEN], pruned_b[MAX_LEN];
        for (size_t i = 0; i < 8; i++)
            pruned_a[i] = !body.ma[i] && body.a[i];
        for (size_t i = 0; i < 13; i++)
            pruned_b[i] = !body.mb[i] && body.b[i];
        pruned_runs += moop_core_prune(&body.core) > 0;
        for (size_t i = 0; i < k; i++)
            moop_core_step_back(&body.core);
        for (size_t i = 0; i < 8; i++)
            mismatches += !pruned_a[i] && body.a[i] != initial.a[i];
        for (size_t i = 0; i < 13; i++)
            mismatches += !pruned_b[i] && body.b[i] != initial.b[i];
    }
    printf("E5 rewind lemma: %d trials, %ld pruned something, "
           "%ld unpruned cells differed after rewinding\n",
           TRIALS, pruned_runs, mismatches);
}

/* --- E6 ----------------------------------------------------------------
 * Stepping back within an epoch adds no marks, and rewinding to the epoch
 * start then replaying with fresh marks reproduces them exactly. */
static void marks_by_replay(void)
{
    enum { TRIALS = 20000 };
    long back_changed = 0, replay_differed = 0;
    for (int t = 0; t < TRIALS; t++) {
        Body body;
        body_init(&body, 8, 13);
        body_fill(&body, 25);
        size_t k = 1 + rng() % (moop_core_epoch(&body.core) - 1);
        for (size_t i = 0; i < k; i++)
            moop_core_step(&body.core);
        Body forward = body;
        size_t j = rng() % (k + 1);
        for (size_t i = 0; i < j; i++)
            moop_core_step_back(&body.core);
        back_changed += memcmp(body.ma, forward.ma, 8) != 0;
        back_changed += memcmp(body.mb, forward.mb, 13) != 0;
        for (size_t i = 0; i < k - j; i++)
            moop_core_step_back(&body.core);
        memset(body.ma, 0, sizeof body.ma);
        memset(body.mb, 0, sizeof body.mb);
        for (size_t i = 0; i < k; i++)
            moop_core_step(&body.core);
        replay_differed += memcmp(body.ma, forward.ma, 8) != 0;
        replay_differed += memcmp(body.mb, forward.mb, 13) != 0;
    }
    printf("E6 marks: %d trials; back-steps changed marks in %ld loops, "
           "replay differed in %ld loops\n",
           TRIALS, back_changed, replay_differed);
}

/* --- E7 ---------------------------------------------------------------- */
static void maybe_balance(void)
{
    enum { BODIES = 100, DRAWS = 10000 };
    long ones = 0;
    for (int t = 0; t < BODIES; t++) {
        Body body;
        body_init(&body, 8, 13);
        body_fill(&body, 50);
        for (int i = 0; i < DRAWS; i++)
            ones += moop_maybe(&body.core);
    }
    printf("E7 MAYBE: %d draws, %.4f ones\n", BODIES * DRAWS,
           (double)ones / (BODIES * DRAWS));
}

/* --- E8 ----------------------------------------------------------------
 * A user layer in the loop: one RAM byte r, and a random program over
 *   STEP     reversible core step
 *   MAYBE    observe (steps the core); r = r << 1 | bit
 *   VALUE    observe loop A (pure); r = that value
 *   DEPOSIT  XOR r onto loop A through gates (closed loop: r depends on
 *            what was observed)
 *   FORGET   r &= mask (irreversible user logic)
 * Claim: the initial tapes are a function of the final tapes, the initial
 * r, the program, and the transcript of observations. */
enum { OP_STEP, OP_MAYBE, OP_VALUE, OP_DEPOSIT, OP_FORGET, OP_COUNT };

typedef struct {
    int op;
    uint8_t mask;
} Instr;

static uint8_t user_step(Instr in, uint8_t r, const unsigned *obs,
                         size_t *k)
{
    switch (in.op) {
    case OP_MAYBE:
        return (uint8_t)(r << 1 | obs[(*k)++]);
    case OP_VALUE:
        return (uint8_t)obs[(*k)++];
    case OP_FORGET:
        return r & in.mask;
    default:
        return r;
    }
}

static void crossing_rule(void)
{
    enum { TRIALS = 100000, LEN = 64 };
    long failures = 0, observations = 0;
    for (int t = 0; t < TRIALS; t++) {
        Instr prog[LEN];
        for (size_t i = 0; i < LEN; i++)
            prog[i] = (Instr){ .op = (int)(rng() % OP_COUNT),
                               .mask = (uint8_t)rng() };
        Body body;
        body_init(&body, 8, 13);
        body_fill(&body, 50);
        Body initial = body;
        uint8_t r0 = (uint8_t)rng(), r = r0;
        unsigned transcript[LEN];
        size_t k = 0;

        /* run: the system half acts, the user half consumes the transcript */
        for (size_t i = 0; i < LEN; i++) {
            size_t before = k;
            switch (prog[i].op) {
            case OP_STEP:
                moop_core_step(&body.core);
                break;
            case OP_MAYBE:
                transcript[k++] = moop_maybe(&body.core);
                break;
            case OP_VALUE:
                transcript[k++] = (unsigned)moop_decode(&body.core);
                break;
            case OP_DEPOSIT:
                moop_encode_xor(&body.core, r);
                break;
            }
            k = before;
            r = user_step(prog[i], r, transcript, &k);
        }
        observations += (long)k;

        /* recover: replay the user layer from r0 and the transcript to learn
         * each deposit, then undo the system half in reverse */
        uint8_t deposits[LEN];
        r = r0;
        k = 0;
        for (size_t i = 0; i < LEN; i++) {
            deposits[i] = r;
            r = user_step(prog[i], r, transcript, &k);
        }
        for (size_t i = LEN; i-- > 0;) {
            if (prog[i].op == OP_STEP || prog[i].op == OP_MAYBE)
                moop_core_step_back(&body.core);
            else if (prog[i].op == OP_DEPOSIT)
                moop_encode_xor(&body.core, deposits[i]);
        }
        failures += memcmp(body.a, initial.a, 8) != 0 ||
                    memcmp(body.b, initial.b, 13) != 0;
    }

    /* closed loop on the tapes alone: VALUE then DEPOSIT resets loop A */
    uint32_t n = UINT32_C(1) << 21;
    uint8_t *hit = calloc(n, 1);
    if (hit == NULL) {
        perror("calloc");
        exit(1);
    }
    uint32_t image = 0;
    for (uint32_t s = 0; s < n; s++) {
        Body body;
        body_init(&body, 8, 13);
        unpack(&body.core, s);
        moop_encode_xor(&body.core, moop_decode(&body.core));
        uint32_t y = pack(&body.core);
        image += !hit[y];
        hit[y] = 1;
    }
    free(hit);
    printf("E8 crossing rule: %d random programs of %d instructions "
           "(%ld observations); tapes not recovered from transcript in %ld\n"
           "   closed loop (observe value, deposit it): %u of %u tape states "
           "remain distinct\n",
           TRIALS, LEN, observations, failures, image, n);
}

int main(int argc, char **argv)
{
    static const size_t sizes[][2] = {
        { 2, 3 }, { 3, 4 }, { 3, 5 }, { 4, 5 }, { 5, 7 },
        { 5, 8 }, { 7, 8 }, { 8, 9 }, { 8, 13 },
    };
    FILE *orbits_dat = NULL, *pruning_dat = NULL;
    if (argc > 1) {
        char path[4096];
        snprintf(path, sizeof path, "%s/orbits.dat", argv[1]);
        orbits_dat = fopen(path, "w");
        snprintf(path, sizeof path, "%s/pruning.dat", argv[1]);
        pruning_dat = fopen(path, "w");
        if (orbits_dat == NULL || pruning_dat == NULL) {
            perror(path);
            return 1;
        }
    }

    closed_form();
    printf("E2 orbit census of the epoch map (every tape state)\n"
           "   loops wiring     states  orbits   fixed nontriv "
           "rewr. A rewr. B  silent  longest on-rewriting\n");
    uint32_t n = UINT32_C(1) << 21;
    uint32_t *moop_lengths = calloc(n + 1, sizeof *moop_lengths);
    uint32_t *harvard_lengths = calloc(n + 1, sizeof *harvard_lengths);
    if (moop_lengths == NULL || harvard_lengths == NULL) {
        perror("calloc");
        return 1;
    }
    Census big = { 0 };
    for (size_t i = 0; i < sizeof sizes / sizeof sizes[0]; i++) {
        bool last = i + 1 == sizeof sizes / sizeof sizes[0];
        census_row(sizes[i][0], sizes[i][1], false,
                   last ? moop_lengths : NULL, last ? &big : NULL);
        census_row(sizes[i][0], sizes[i][1], true,
                   last ? harvard_lengths : NULL, NULL);
    }
    if (orbits_dat != NULL) {
        fprintf(orbits_dat, "wiring\tlength\torbits\tcumulative\n");
        write_lengths(orbits_dat, "moop", moop_lengths, n);
        write_lengths(orbits_dat, "harvard", harvard_lengths, n);
        fclose(orbits_dat);
    }
    free(moop_lengths);
    free(harvard_lengths);
    tour(big.longest_at, 8, 13);
    sweep();
    if (pruning_dat != NULL)
        fprintf(pruning_dat, "density\tinert\tpruned_runs\n");
    density(pruning_dat);
    if (pruning_dat != NULL)
        fclose(pruning_dat);
    rewind_lemma();
    marks_by_replay();
    maybe_balance();
    crossing_rule();
    return 0;
}
