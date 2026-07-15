#ifndef MOOP_GATES_H
#define MOOP_GATES_H

#include <stdbool.h>

/* The reversible operator layer. These act in place on cells of the
 * gate-based system memory (tape loops) and each is its own inverse.
 * Segregation rule: nothing in this layer may touch user-facing RAM. */

void moop_not(bool *a);                            /* a ^= 1            */
void moop_cnot(bool c, bool *target);              /* target ^= c       */
void moop_ccnot(bool c1, bool c2, bool *target);   /* target ^= c1 & c2 */
void moop_swap(bool *a, bool *b);

#endif
