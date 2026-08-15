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

/* Admissible(R, P, Q): every endpoint required by R exists in the declared
 * schemas, has the required identity and type, has Status = ACTIVE, and
 * satisfies the applicable endpoint compatibility contracts.
 *
 * THREE STAGES, NEVER CONFLATED (spec §4):
 *
 *     Admissible(R,P,Q)  !=  Declared(R)  !=  Executed(R)
 *
 *     Admissible  =/=>  Declared
 *     Declared    =/=>  Executed
 *     Executed     =>   Declared
 *
 * Admissibility is therefore evaluated WITHOUT consulting R->declared: a
 * relation that does not yet exist can be assessed for admissibility, which
 * is exactly what §9's future-relation question asks (C18a).  Collapsing
 * this into rme_compose_valid() would make "R may subsequently be declared
 * without redesigning either boundary" unaskable.
 *
 * The ACTIVE requirement is unconditional.  A relation able to connect a
 * vestigial endpoint would have to be a different, explicitly declared
 * relation class -- never an exception embedded here. */
RmeComposition rme_admissible(const RmePrototype *P,
                              const RmePrototype *Q,
                              const RmeRelation  *R);

/* ComposeValid(P,Q,R) = Declared(R) AND Admissible(R,P,Q). */
RmeComposition rme_compose_valid(const RmePrototype *P,
                                 const RmePrototype *Q,
                                 const RmeRelation  *R);

#endif /* RME_COMPOSE_H */
