#ifndef RME_CLASSIFY_H
#define RME_CLASSIFY_H

#include "graph.h"

/* poiesis — AXIS C: classification, OBSERVED not asserted.
 *
 *   RME-4   fixed relation
 *   RME-5   parameter adaptation
 *   RME-6   one-way governed composition
 *   RME-6B  composition + return through ENVIRONMENTAL state
 *   RME-7   a directed cycle ENTIRELY among governed state objects
 *
 * Direct criterion is a CONJUNCTION — dT_X/dY != 0 AND dT_Y/dX != 0.  The
 * disjunctive form classifies every pipeline as RME-7.  Mediated criterion:
 * X1 -> ... -> Xn -> X1 with every node governed.
 *
 * HARD INVARIANT: promote only when the cycle is internal to G_GS.  Never
 * from syntactic nesting, recursion, component count, or an execution
 * loop.  The classifier's only input is RmeSystem — it cannot see call
 * graphs, containment, or recursion, so those cannot promote by
 * construction.
 *
 * This function is NOT rme7_conforms().  Classification is an observation
 * of governed transition structure; conformance is a property of a
 * prototype's interface.  An RME-6 instance that is RME-7-conformant is
 * the normal case, and asserting a classification can never make anything
 * conformant.
 */

typedef enum {
    RME_LEVEL_4 = 0,
    RME_LEVEL_5,
    RME_LEVEL_6,
    RME_LEVEL_6B,
    RME_LEVEL_7
} RmeLevel;

const char *rme_level_name(RmeLevel l);

RmeLevel rme_classify(const RmeSystem *s);

#define RME_MAX_SLOTS 2048u
#define RME_MAX_EDGES 8192u

#endif /* RME_CLASSIFY_H */
