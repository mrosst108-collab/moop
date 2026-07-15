#ifndef MOOP_ENCODE_H
#define MOOP_ENCODE_H

#include "tapeloop.h"

/* The value encoding: how user-visible numbers live on tape states.
 * Bit i of a value is cell i of loop A.
 *
 * Everything here is built from involutions, so `<->` is bijective as
 * a fact, not a figure of speech:
 *
 * - moop_encode_xor deposits a value with gate-layer NOTs (XOR).
 *   Self-inverse: encoding the same value twice erases it. Writing and
 *   unwriting are the same reversible act. Deposited cells are marked
 *   causal — a deliberate deposit must survive pruning.
 * - moop_exchange swaps two bodies' A-tapes with gate-layer SWAPs.
 *   Self-inverse and symmetric; marks travel with their cells, so a
 *   bit's causal history rides along.
 * - moop_decode is pure observation (reads, changes nothing).
 *
 * Values wider than loop A do not fit; callers must refuse them rather
 * than truncate — silent truncation would make `<->` lossy, which is
 * the one thing it must never be. */

void moop_encode_xor(MoopCore *core, unsigned long value);
unsigned long moop_decode(const MoopCore *core);
void moop_exchange(MoopCore *x, MoopCore *y);

/* Largest value loop A can carry. */
unsigned long moop_encode_max(const MoopCore *core);

#endif
