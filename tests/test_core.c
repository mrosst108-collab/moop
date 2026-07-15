#include <stdio.h>
#include <string.h>
#include "tapeloop.h"

static int failures;

static void check(bool ok, const char *desc)
{
    printf("%s - %s\n", ok ? "ok  " : "FAIL", desc);
    if (!ok)
        failures = 1;
}

static void test_ccnot_truth_table(void)
{
    /* target flips iff both controls are set */
    for (int c1 = 0; c1 <= 1; c1++)
        for (int c2 = 0; c2 <= 1; c2++)
            for (int t = 0; t <= 1; t++) {
                bool target = t;
                moop_ccnot(c1, c2, &target);
                bool expected = t ^ (c1 && c2);
                check(target == expected, "ccnot truth table entry");
            }
}

static void test_counter_rotation(void)
{
    bool a[5] = {0}, b[3] = {0};
    MoopCore core;
    moop_core_init(&core, a, 5, b, 3);
    moop_core_step(&core);
    check(core.a.head == 1, "loop A rotates forward");
    check(core.b.head == 2, "loop B rotates backward");
}

static void test_gate_computes(void)
{
    /* both heads on 1-cells: the gate must flip A's next cell */
    bool a[4] = {1, 0, 1, 0}, b[3] = {1, 1, 0};
    MoopCore core;
    moop_core_init(&core, a, 4, b, 3);
    moop_core_step(&core);
    check(a[1] == 1, "ccnot flips target when both controls set");
}

static void test_reversibility(void)
{
    /* coprime lengths so every cell alignment occurs before repeating */
    bool a[5]  = {1, 0, 1, 1, 0};
    bool b[7]  = {0, 1, 1, 0, 1, 0, 1};
    bool a0[5], b0[7];
    memcpy(a0, a, sizeof a);
    memcpy(b0, b, sizeof b);

    MoopCore core;
    moop_core_init(&core, a, 5, b, 7);

    enum { TICKS = 35 }; /* one full lcm(5,7) alignment cycle */
    for (int i = 0; i < TICKS; i++)
        moop_core_step(&core);
    bool changed = memcmp(a0, a, sizeof a) != 0;
    check(changed, "stepping actually transforms the tape");

    for (int i = 0; i < TICKS; i++)
        moop_core_step_back(&core);
    check(memcmp(a0, a, sizeof a) == 0 &&
          memcmp(b0, b, sizeof b) == 0 &&
          core.a.head == 0 && core.b.head == 0,
          "step_back exactly inverts step over a full cycle");
}

int main(void)
{
    test_ccnot_truth_table();
    test_counter_rotation();
    test_gate_computes();
    test_reversibility();
    return failures;
}
