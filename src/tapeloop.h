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
 */

typedef struct {
    bool *cells;  /* caller-owned storage */
    size_t len;
    size_t head;  /* index of the cell currently under the gate */
} MoopLoop;

typedef struct {
    MoopLoop a;   /* rotates forward  (+1 per tick) */
    MoopLoop b;   /* rotates backward (-1 per tick) */
} MoopCore;

void moop_core_init(MoopCore *core,
                    bool *cells_a, size_t len_a,
                    bool *cells_b, size_t len_b);

void moop_core_step(MoopCore *core);
void moop_core_step_back(MoopCore *core);

#endif
