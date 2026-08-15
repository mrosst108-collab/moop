#ifndef RME_SCHEDULE_H
#define RME_SCHEDULE_H

#include "classify.h"
#include "contract.h"

/* poiesis — GATE 2: flattening, elision, and fixed-point groups (§7, §12).
 *
 * TWO SETS, AND THE INVARIANT BETWEEN THEM:
 *
 *     E_envelope   every schema-declared port, unconditionally
 *     E_dispatch   the ports that must actually be invoked
 *
 *     E_dispatch  subset-of  E_envelope
 *
 * Elision is an OPTIMIZATION PERMISSION, never a semantic rule:
 *
 *     Elidable(p)  <=>  Status(p) = VESTIGIAL
 *                       && VestigialContract(p).allows_elision
 *
 * and it licenses neither of the prohibited inferences:
 *
 *     VESTIGIAL(p)  =>  Elidable(p)         X   permission is per-port
 *     VESTIGIAL(p)  =>  EnvelopeAbsent(p)   X   vestigial is PRESENT
 *
 * An elidable port leaves the DISPATCH ARRAY.  Nothing ever leaves the
 * ENVELOPE.  That is the substrate invariant restated for the optimizer:
 * realization compression is not boundary compression.  Caches, temporaries
 * and optimized-away computation may vanish freely; a boundary-relevant
 * distinction may not, because its absence would force a redesign before a
 * future relation could be declared against it.
 *
 * ABSENT is deliberately not reachable from here.  A port dropped from
 * dispatch is still declared, still typed, still contractually specified,
 * and still an endpoint a future R_C could name — at which point it must
 * be ACTIVE to participate (Participates(p,R_C) => Status(p) = ACTIVE), a
 * transition that costs nothing precisely because the envelope kept it.
 *
 * The transition schedule flattens to a topological order over the
 * condensation of the dependency graph, with multi-member SCCs and
 * self-dependent slots marked for fixed-point iteration.  It uses the FULL
 * projection, not G_GS: evaluation must respect every declared read,
 * governed or environmental.  A schedule is not a classification, and
 * `iterate` is not RME-7 — the governed/environmental distinction that
 * separates RME-7 from RME-6B plays no part in execution order.
 */

typedef struct {
    RmePortId ports[RME_PORT_COUNT];
    size_t    count;
    unsigned  mask;    /* bit i set iff port i is a member */
} RmePortSet;

/* Every declared port, whatever its status.  The result is always the full
 * schema: this function has no way to omit one. */
RmePortSet rme_envelope(const RmePrototype *p);

/* The ports that must be invoked: the envelope minus those whose own
 * vestigial contract permits elision. */
RmePortSet rme_dispatch(const RmePrototype *p);

bool rme_portset_has(const RmePortSet *s, RmePortId id);
bool rme_portset_subset(const RmePortSet *lo, const RmePortSet *hi);

/* The Gate 2 invariant, checkable directly on any prototype. */
bool rme_dispatch_within_envelope(const RmePrototype *p);

/* One scheduling group: a strongly connected component of the dependency
 * graph, in evaluation order. */
typedef struct {
    size_t first;     /* index into RmeSchedule.order */
    size_t count;     /* members in this group */
    bool   iterate;   /* fixed-point iteration required: |SCC| > 1, or a
                       * self-dependency, which a one-member SCC would
                       * otherwise hide (the same rule classify.h freezes) */
} RmeScheduleGroup;

typedef struct {
    size_t           *order;         /* slot indices, evaluation order */
    size_t            order_count;
    RmeScheduleGroup *groups;
    size_t            group_count;
} RmeSchedule;

/* Returns false — allocating nothing — if the schedule could not be built.
 * A partial or truncated schedule is never returned as if complete. */
bool rme_schedule_build(const RmeSystem *s, RmeSchedule *out);
void rme_schedule_release(RmeSchedule *s);

#endif /* RME_SCHEDULE_H */
