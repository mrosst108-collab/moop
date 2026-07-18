#ifndef MOOP_TAPELOOP_H
#define MOOP_TAPELOOP_H

#include <stdbool.h>
#include <stddef.h>

/* The central primitive of moop: one CCNOT (Toffoli) gate connected to two
 * counter-rotating circular Turing tapes ("loops").
 *
 * Each tick:
 *   1. the gate fires symmetrically: controls are the cells under each
 *      loop's head; the shared controls drive two CCNOTs, one targeting
 *      the next cell (in rotation order) of EACH loop.
 *   2. the loops rotate one cell in opposite directions
 *      (A forward, B backward).
 *
 * The two CCNOTs share controls and have distinct targets, so they
 * commute and the pair is self-inverse; rotation is a permutation — every
 * tick is reversible and moop_core_step_back() exactly undoes
 * moop_core_step().
 *
 * The symmetric wiring is what makes the loops HOMOICONIC: there is no
 * designated program tape. Every cell is simultaneously potential
 * instruction (control) and potential data (target); code rewrites code,
 * and because each rewrite is reversible, running any state backward
 * recovers the program that produced it. The system is causally closed —
 * nothing outside the loops is needed to go forward or back. This wiring
 * is still expected to iterate — keep it confined here.
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
 *
 * Admissibility (asserted in moop_core_init): each loop has >= 2 cells
 * (else a target aliases a control and self-inverseness breaks), and the
 * lengths are coprime (else shared factors partition the (A, B) pairings
 * into alignment classes that never meet, and "one epoch = every pairing
 * consulted once" — which pruning relies on — no longer holds).
 * moop_core_step_back() asserts ticks > 0: stepping back past the epoch
 * start would cross a prune boundary, where the guarantee ends.
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
