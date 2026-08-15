#ifndef RME_COMPOSE_H
#define RME_COMPOSE_H

#include "conform.h"

/* poiesis — AXIS B: composition.
 *
 *   ComposeValid(P,Q,R) <=> Declared(R) ^ EndpointsValid(R)
 *                           ^ forall (p,q) in R : Active(p) ^ Active(q) ^ Compatible(p,q)
 *
 * RELATIONAL, and kept strictly apart from conformance (F4).  R is a
 * RELATION, NOT AN EVENT: the same predicate serves statically declared
 * composition, runtime negotiation, pre-execution validation, nested
 * composition and purely hypothetical checking.  Evaluating it never
 * invokes a port realization.
 *
 * F5: only explicitly declared connection endpoints incur compatibility
 * obligations.  Ports outside R are irrelevant to that composition, and
 * `obligations` reports exactly |R| so the caller can see that mere
 * coexistence of compatible ports creates nothing.
 *
 * Prohibited, and not implementable through this interface:
 *   Compatible(p,q)  => Compose(P,Q)     -- compatibility is a pair property
 *   !Compatible(p,q) => !RME7(P)         -- conformance is unaffected
 */

typedef struct {
    RmePortId p;   /* endpoint in P */
    RmePortId q;   /* endpoint in Q */
} RmeConnection;

typedef struct {
    const RmeConnection *edges;
    size_t               count;
    bool                 declared;  /* Declared(R): an undeclared relation is not a composition */
} RmeRelation;

typedef struct {
    bool        ok;
    size_t      edge;         /* index of the offending connection, or count */
    size_t      obligations;  /* == |R|; never the number of compatible pairs */
    const char *why;
} RmeComposition;

RmeComposition rme_compose_valid(const RmePrototype *P,
                                 const RmePrototype *Q,
                                 const RmeRelation  *R);

#endif /* RME_COMPOSE_H */
