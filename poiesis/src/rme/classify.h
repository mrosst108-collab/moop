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
 * G_GS is decisive for RME-7 PROMOTION.  It is not the sole input to every
 * verdict: RME-6B is precisely the case where a cycle requires a
 * non-governed node, so that verdict is reached by projecting over ALL
 * slots and finding a cycle there after finding none in G_GS.  (The earlier
 * wording of this comment said classification simply *is* cyclicity in
 * G_GS, which overstated it and disagreed with the code below.)
 *
 * SELF-LOOP RULE — FROZEN, directed-cycle semantics.  A governed self-edge
 * X -> X (T_X declares a read of X) IS a directed cycle and satisfies the
 * RME-7 criterion; a singleton vertex without a self-edge does not.  The
 * decision is semantic, not algorithmic: mutual governed dependency is the
 * criterion and self-dependency (dT_X/dX != 0) is its degenerate case.
 * Tarjan alone would report a self-edge as a single-member SCC, so
 * cyclicity is tested by the presence of a self-edge as well as by SCC
 * cardinality.  K7 and K10 pin the distinction that follows:
 *
 *     governed self-dependency  !=  execution self-recursion
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
    RME_CLASS_RME4 = 0,
    RME_CLASS_RME5,
    RME_CLASS_RME6,
    RME_CLASS_RME6B,
    RME_CLASS_RME7
} RmeClassification;

const char *rme_classification_name(RmeClassification c);

#define RME_MAX_SLOTS 2048u
#define RME_MAX_EDGES 8192u

/* Returns false — writing nothing to *out — when the system exceeds what
 * this build can project, so a truncated projection can never be reported
 * as a classification.  Silently downgrading an unrepresentable system to
 * RME-4 would be exactly the kind of quiet failure the audit forbids. */
bool rme_classify(const RmeSystem *s, RmeClassification *out);

#endif /* RME_CLASSIFY_H */
