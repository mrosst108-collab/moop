#ifndef AWV_AWV_H
#define AWV_AWV_H

#include "rme/classify.h"
#include "rme/schedule.h"
#include "rme/validate.h"

/* AWV as a CLIENT of poiesis.
 *
 * The dependency runs AWV -> poiesis and NEVER the reverse.  Nothing under
 * src/rme/ knows the words delta, Sigma_U, A-hat, Route 7C, Fork G or any
 * other AWV term, and `make layering` checks that mechanically rather than
 * by convention.  Everything below is expressed in poiesis' vocabulary:
 * slots, a governed marking, declared read-sets, ports and statuses.
 *
 * WHAT IS DECLARED HERE IS AWV'S, NOT POIESIS'.  The classification that
 * follows is not asserted by this file — the slots and read-sets are, and
 * rme_classify() observes what follows from them.  Every marking below is
 * traceable to an explicit statement in AWV's own change log:
 *
 *   v0.18  delta retyped as a DERIVED OPERATOR rather than a state object,
 *          "making 6B mechanical -- the cycle through behaviour and delta
 *          passes through no governed state".  delta is therefore NOT a
 *          slot here: it is an operator applied within a transition, and
 *          an operator is not a state object.
 *
 *   v0.16  "the environmental loop through behaviour is 6B because
 *          BEHAVIOUR IS NOT A GOVERNED STATE OBJECT".  That single bit on
 *          one slot is the whole difference between 6B and 7.
 *
 *   v0.12  the A-weighted supermajority rows are A -> theta -> A, "the loop
 *          15.1 reserves"; they are "contingent on Fork G RATHER THAN
 *          OPERATIVE".  The operative system therefore declares no read of
 *          A by the transition on theta.
 *
 *   v0.14  Fork N closed to UNIFORM fallback, so the epoch solve reads no
 *          previous-epoch authority; "AWV reverts to 6B".
 */

/* AWV's declared state objects.  Ordering is this file's; the governed
 * marking is AWV's. */
enum {
    AWV_SIGMA_U = 0,   /* governed     -- the subscription/endorsement graph */
    AWV_A,             /* governed     -- the authority vector              */
    AWV_THETA,         /* governed     -- governance parameters             */
    AWV_BEHAVIOUR,     /* ENVIRONMENTAL -- v0.16, and decisive              */
    AWV_SLOT_COUNT
};

/* The operative system: what AWV is as deployed.  K8 expects RME-6B. */
const RmeSystem *awv_system_operative(void);

/* Route 7C (v0.13, withdrawn by v0.14, retained in 15.0 as a documented
 * near-miss).  The median-band fallback reads the PREVIOUS EPOCH'S median
 * authority, which is a governed read of A by the transition on A: a
 * governed self-dependency, and therefore a directed cycle inside G_GS.
 *
 * AWV's own methodological finding was that "a numerical convention can
 * cross the RME-7 boundary without announcing it".  This system exists so
 * that claim is checked by the classifier instead of argued: it is exactly
 * the shape K10 pins, arrived at from a numerical convention rather than
 * from governance. */
const RmeSystem *awv_system_route_7c(void);

/* Fork G (v0.12): were the A-weighted supermajority rows made operative,
 * theta would read A while A already reads theta -- a governed 2-cycle.
 * The reserved loop, declared here so that its consequence is mechanical
 * rather than remembered. */
const RmeSystem *awv_system_fork_g(void);

/* AWV's declared prototypes.  Each is assessed against its own schema:
 * nothing here inherits validity from AWV's structure or from any other
 * prototype (F7). */
RmePrototype awv_authority_prototype(void);
RmePrototype awv_presentation_prototype(void);

/* v0.9: "open admission frozen as the default condition of a topical
 * community; no admission authority and no moderator exist UNLESS A
 * COMMUNITY OPTS IN" -- "optional architecture, not a requirement".
 *
 * The two forms share ONE schema and differ only in port status.  That is
 * vestigiality doing the work it exists for: in the default form the
 * admission and governance capabilities are structurally present and
 * contractually typed but non-substantive, so opting in changes statuses
 * and declares a relation WITHOUT redesigning either boundary. */
RmePrototype awv_community_prototype_open(void);
RmePrototype awv_community_prototype_curated(void);

/* AWV'S OWN CONSTITUTIONAL PREDICATE.
 *
 * This lives in the client and nowhere else.  poiesis answers whether an
 * endpoint pair is STRUCTURALLY ADMISSIBLE; it has no access to AWV's
 * constitution and must not acquire one.  A substrate that refused the
 * relation below would be smuggling AWV's constitution into src/rme/.
 *
 * v0.12: extra eigenproblems are constitutionally free "only while output
 * remains presentation state, which excludes 13.2's use of community-local
 * PageRank to assign admission authority".  Presentation may be READ from;
 * it may not WRITE INTO constitutional state. */
bool awv_constitutionally_permitted(const RmePrototype *from, RmePortId fp,
                                    const RmePrototype *to,   RmePortId tp);

#endif /* AWV_AWV_H */
