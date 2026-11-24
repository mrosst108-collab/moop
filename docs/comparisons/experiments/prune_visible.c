/* Would pruning a body be visible to a moop program?
 *
 * No body is pruned during a session: the interpreter advances a body
 * one moop_core_step at a time and never calls moop_core_prune or
 * moop_core_run (docs/model.md, "What the core is, and what a program
 * reaches").  This program shows what a prune would do if it happened.
 * It rebuilds the interpreter's world exactly as moop_eval_init does,
 * births two children of the world, and prunes each body by hand.
 *
 * From the repository root:
 *   cc -std=c2x -Wall -Wextra -Isrc \
 *      docs/comparisons/experiments/prune_visible.c \
 *      src/tapeloop.c src/gates.c src/logic.c src/ram.c src/actor.c \
 *      src/proto.c src/encode.c -o build/prune_visible
 *   build/prune_visible
 *
 * It prints (0.10.0, wiring 1):
 *   first child at birth:                 181
 *   after 300 draws:                      196
 *   then pruned (0 set bits discarded):   196
 *   second child at birth:                52
 *   pruned at once (9 set bits discarded): 0
 *
 * 181 and 52 are the values `box ask value` prints for the world's
 * first and second child, so the rebuilt world is the interpreter's.
 * A birth marks none of the child's cells, so a body pruned before it
 * has fired loses everything it was born with. */
#include <stdbool.h>
#include <stdio.h>
#include "actor.h"
#include "encode.h"
#include "logic.h"
#include "proto.h"
#include "tapeloop.h"

#define LEN_A 8      /* the interpreter's body: src/eval.c */
#define LEN_B 13
#define TABLE_CAP 4

int main(void)
{
    /* the actor's tapes, as src/eval.c seeds them */
    static bool actor_a[5] = {1, 0, 1, 1, 0}, actor_ma[5];
    static bool actor_b[7] = {0, 1, 1, 0, 1, 0, 1}, actor_mb[7];
    static bool sys_a[LEN_A], sys_ma[LEN_A], sys_b[LEN_B], sys_mb[LEN_B];
    static bool world_a[LEN_A], world_ma[LEN_A], world_b[LEN_B], world_mb[LEN_B];
    static bool one_a[LEN_A], one_ma[LEN_A], one_b[LEN_B], one_mb[LEN_B];
    static bool two_a[LEN_A], two_ma[LEN_A], two_b[LEN_B], two_mb[LEN_B];
    static MoopMessage actor_table[2];
    static MoopProtoMessage sys_table[TABLE_CAP], world_table[TABLE_CAP];
    static MoopProtoMessage one_table[TABLE_CAP], two_table[TABLE_CAP];
    MoopActor actor;
    MoopProto sysroot, world, one, two;

    moop_actor_init(&actor, actor_a, actor_ma, 5, actor_b, actor_mb, 7,
                    actor_table, 2);
    moop_actor_generate_root(&actor, &sysroot, sys_a, sys_ma, LEN_A,
                             sys_b, sys_mb, LEN_B, sys_table, TABLE_CAP);
    moop_proto_generate(&sysroot, &world, world_a, world_ma, LEN_A,
                        world_b, world_mb, LEN_B, world_table, TABLE_CAP);

    moop_proto_generate(&world, &one, one_a, one_ma, LEN_A,
                        one_b, one_mb, LEN_B, one_table, TABLE_CAP);
    printf("first child at birth:                 %lu\n",
           (unsigned long)moop_decode(&one.core));
    for (int i = 0; i < 300; i++)
        moop_maybe(&one.core);
    printf("after 300 draws:                      %lu\n",
           (unsigned long)moop_decode(&one.core));
    size_t gone = moop_core_prune(&one.core);
    printf("then pruned (%zu set bits discarded):   %lu\n", gone,
           (unsigned long)moop_decode(&one.core));

    moop_proto_generate(&world, &two, two_a, two_ma, LEN_A,
                        two_b, two_mb, LEN_B, two_table, TABLE_CAP);
    printf("second child at birth:                %lu\n",
           (unsigned long)moop_decode(&two.core));
    gone = moop_core_prune(&two.core);
    printf("pruned at once (%zu set bits discarded): %lu\n", gone,
           (unsigned long)moop_decode(&two.core));
    return 0;
}
