#include <stdio.h>
#include <string.h>
#include "gates.h"
#include "logic.h"
#include "ram.h"
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

static void test_reversible_gates(void)
{
    bool x = true, y = false;

    moop_not(&x);
    check(x == false, "not flips");
    moop_not(&x);
    check(x == true, "not is self-inverse");

    moop_cnot(true, &y);
    check(y == true, "cnot flips target when control set");
    moop_cnot(false, &y);
    check(y == true, "cnot leaves target when control clear");
    moop_cnot(true, &y);
    check(y == false, "cnot is self-inverse");

    x = true; y = false;
    moop_swap(&x, &y);
    check(x == false && y == true, "swap exchanges");
    moop_swap(&x, &y);
    check(x == true && y == false, "swap is self-inverse");
}

static void test_irreversible_logic(void)
{
    check(moop_and(1, 1) && !moop_and(1, 0), "and");
    check(moop_or(0, 1) && !moop_or(0, 0), "or");
    check(moop_nand(1, 0) && !moop_nand(1, 1), "nand");
    check(moop_nor(0, 0) && !moop_nor(0, 1), "nor");
    check(moop_xor(1, 0) && !moop_xor(1, 1), "xor");
}

static void test_maybe(void)
{
    bool a[5] = {1, 0, 1, 1, 0}, b[7] = {0, 1, 1, 0, 1, 0, 1};
    bool a2[5], b2[7];
    memcpy(a2, a, sizeof a);
    memcpy(b2, b, sizeof b);

    enum { DRAWS = 12 };
    bool first[DRAWS], second[DRAWS];
    MoopCore core, core2;

    moop_core_init(&core, a, 5, b, 7);
    for (int i = 0; i < DRAWS; i++)
        first[i] = moop_maybe(&core);

    moop_core_init(&core2, a2, 5, b2, 7);
    for (int i = 0; i < DRAWS; i++)
        second[i] = moop_maybe(&core2);
    check(memcmp(first, second, sizeof first) == 0,
          "maybe is deterministic for identical tapes");

    for (int i = 0; i < DRAWS; i++)
        moop_core_step_back(&core);
    check(a[0] == 1 && a[1] == 0 && a[2] == 1 && a[3] == 1 && a[4] == 0 &&
          core.a.head == 0 && core.b.head == 0,
          "maybe's effect on system memory is fully reversible");
}

static void test_ram(void)
{
    uint8_t bytes[16] = {0};
    MoopRam ram;
    moop_ram_init(&ram, bytes, sizeof bytes);
    moop_ram_write(&ram, 3, 0xAB);
    check(moop_ram_read(&ram, 3) == 0xAB, "ram write/read round-trip");
    moop_ram_write(&ram, 3, 0xCD);
    check(moop_ram_read(&ram, 3) == 0xCD, "ram overwrites (forgets) freely");
}

int main(void)
{
    test_ccnot_truth_table();
    test_reversible_gates();
    test_counter_rotation();
    test_gate_computes();
    test_reversibility();
    test_irreversible_logic();
    test_maybe();
    test_ram();
    return failures;
}
