#ifndef MOOP_LOGIC_H
#define MOOP_LOGIC_H

#include <stdbool.h>
#include "tapeloop.h"

/* The irreversible operator layer, for user-facing values. These are pure
 * value functions (inputs are consumed into one output — information is
 * discarded, which is exactly what the reversible layer must never do).
 * Segregation rule: nothing in this layer may write system memory.
 *
 * moop_maybe is the primitive bridge between the layers (actors in
 * actor.h generalize the same shape — reversible effect inside,
 * irreversible observation outside): it advances
 * the reversible core one tick and observes the cell under loop A's head.
 * Deterministic and reproducible (same tapes, same answers), and its only
 * effect on system memory is a reversible step — no information is lost.
 * Initial design; see docs/model.md. */

bool moop_and(bool a, bool b);
bool moop_or(bool a, bool b);
bool moop_nand(bool a, bool b);
bool moop_nor(bool a, bool b);
bool moop_xor(bool a, bool b);
bool moop_maybe(MoopCore *oracle);

#endif
