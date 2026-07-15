#ifndef MOOP_TAPELOOP_H
#define MOOP_TAPELOOP_H

#include <stdbool.h>
#include <stddef.h>

/* The central primitive of moop: one CCNOT (Toffoli) gate connected to two
 * counter-rotating circular Turing tapes ("loops").
 *
 * Each tick:
 *   1. gate fires: controls are the cells under each loop's head;
 *      target is the next cell (in rotation order) on loop A.
 *   2. the loops rotate one cell in opposite directions
 *      (A forward, B backward).
 *
 * CCNOT is reversible and rotation is a permutation, so every tick is
 * reversible; moop_core_step_back() exactly undoes moop_core_step().
 * This wiring (which cells are controls, where the target sits) is the
 * initial design and is expected to iterate — keep it confined here.
 *
 * Causal pruning. Each loop carries causal marks: a cell is marked the
 * first time it participates in a firing (both controls set, so state
 * actually changes). Cells still unmarked when moop_core_prune() runs are
 * causally unrelated to the rest of the current state — zeroing them loses
 * only their own value, nothing about any other cell. Pruning is the one
 * sanctioned act of forgetting in the system layer: it is irreversible, it
 * starts a fresh causal epoch (marks and tick count reset), and the
 * step/step_back round-trip guarantee holds BETWEEN prunes, not across
 * them. moop_core_run() auto-prunes at every epoch boundary (one full
 * alignment cycle, lcm(len_a, len_b) ticks). Marks and ticks are heuristic
 * metadata, not part of the reversible state.
 */

typedef struct {
    bool *cells;  /* caller-owned storage */
    bool *marks;  /* caller-owned; true once the cell joins the causal web */
    size_t len;
    size_t head;  /* index of the cell currently under the gate */
} MoopLoop;

typedef struct {
    MoopLoop a;    /* rotates forward  (+1 per tick) */
    MoopLoop b;    /* rotates backward (-1 per tick) */
    size_t ticks;  /* ticks since epoch start (init or last prune) */
} MoopCore;

void moop_core_init(MoopCore *core,
                    bool *cells_a, bool *marks_a, size_t len_a,
                    bool *cells_b, bool *marks_b, size_t len_b);

void moop_core_step(MoopCore *core);
void moop_core_step_back(MoopCore *core);

/* Ticks in one full alignment cycle: lcm(len_a, len_b). */
size_t moop_core_epoch(const MoopCore *core);

/* Zero every causally inert (unmarked) cell, reset marks and ticks.
 * Returns how many set bits were discarded. */
size_t moop_core_prune(MoopCore *core);

/* Step `ticks` times, auto-pruning at each epoch boundary.
 * Returns total set bits discarded by pruning. */
size_t moop_core_run(MoopCore *core, size_t ticks);

#endif
