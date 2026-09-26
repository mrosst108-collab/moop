#ifndef RME_PORT_H
#define RME_PORT_H

#include <stdbool.h>
#include <stddef.h>

/* poiesis — the RME-7 port schema.
 *
 * Portability: every construct here is ISO C23 required (enum, struct,
 * offsetof, static_assert, designated initializers).  No compiler
 * extensions.  See the Makefile for the -std probe.
 *
 * FROZEN (spec §Ports): ports are concrete typed structures.  There is no
 * universal `struct rme_port` carrying a void* payload — compile-time
 * distinguishability is worth more here than genericity.  Shared fields
 * live in a header that is the FIRST member of every port struct, so
 * `(RmePortHeader *)&proto->state` is a valid ISO C conversion (a pointer
 * to a struct, suitably converted, points to its initial member).  That is
 * what lets validation walk ports uniformly without erasing their types.
 */

/* ---------------------------------------------------------------- schema
 * SINGLE SOURCE OF TRUTH for the port vocabulary.  The id enum, the name
 * table, the offset table and the completeness check all expand from this
 * macro, so adding or renaming a port cannot leave a stale check behind.
 *
 * PROVISIONAL (spec §Schema): the exact vocabulary is not settled — five
 * variants appeared during specification.  Changing it is a one-line edit
 * here, by design.
 */
#define RME_PORTS(X)    \
    X(state)            \
    X(observation)      \
    X(transition)       \
    X(parameterization) \
    X(coupling)         \
    X(adaptation)       \
    X(governance)       \
    X(nested)

typedef enum {
#define RME_PORT_ENUM(n) RME_PORT_##n,
    RME_PORTS(RME_PORT_ENUM)
#undef RME_PORT_ENUM
    RME_PORT_COUNT
} RmePortId;

/* ---------------------------------------------------------------- status
 * F2: {ACTIVE, VESTIGIAL} is the ENTIRE legal semantic domain.
 *
 * RME_UNDEFINED = 0 is an internal CONSTRUCTION SENTINEL, never a public
 * semantic status and never a legal third state.  A designated-initializer
 * table zero-fills any port the author forgot, so an omitted port reads
 * back as UNDEFINED and is rejected by rme7_conforms().  If it were ever
 * allowed to survive validation, ACTIVE / VESTIGIAL / ABSENT would return
 * through the API — which is exactly what the schema-completeness rule
 * exists to prevent.
 *
 * Deliberately absent: any `Realized(p)` predicate.  A third quasi-status
 * invites `Realized(p) == false`, reopening ABSENT as a semantic state.
 */
typedef enum {
    RME_UNDEFINED = 0,
    RME_ACTIVE,
    RME_VESTIGIAL
} RmePortStatus;

/* True only for the two legal semantic statuses. */
static inline bool rme_status_is_legal(RmePortStatus s)
{
    return s == RME_ACTIVE || s == RME_VESTIGIAL;
}

const char *rme_port_name(RmePortId id);
const char *rme_status_name(RmePortStatus s);

/* ---------------------------------------------------------------- header
 * First member of every port struct.  `id` lets uniform validation report
 * which port failed without the caller re-deriving it.
 */
typedef struct {
    RmePortStatus status;
    RmePortId     id;
} RmePortHeader;

/* ------------------------------------------------------------------ APIs
 * One distinct interface type per port.  These are NOT interchangeable and
 * are not reducible to a common function-pointer bag: distinctness is the
 * type discipline the spec asks for.
 *
 * A VESTIGIAL port still points at a valid object of its declared
 * interface type — never a bare null.  What makes it vestigial is that its
 * realization is marked non-substantive for that port's capability, per
 * that port's OWN vestigial contract.  There is deliberately no global
 * "null implementation": an inert endpoint, an empty capability, a
 * default-valued state and an operation returning a defined "not realized"
 * result are not equivalent, and a blanket `return 0;` is prohibited.
 *
 * OPEN (spec §Disposition): the substantive content of these interfaces is
 * the next specification task.  Every contract below is marked provisional
 * so the gap stays mechanically visible.
 */

/* Result of invoking a port operation.  RME_NOT_REALIZED is a *defined*
 * outcome, distinct from failure — it is what a vestigial realization may
 * legitimately answer where its contract permits that shape. */
typedef enum {
    RME_OK = 0,
    RME_NOT_REALIZED,
    RME_REFUSED
} RmeOutcome;

typedef struct { RmeOutcome (*read)(void *self, void *out); const char *kind; } RmeStateApi;
typedef struct { RmeOutcome (*observe)(void *self, void *out); const char *kind; } RmeObservationApi;
typedef struct { RmeOutcome (*step)(void *self, const void *args); const char *kind; } RmeTransitionApi;
typedef struct { RmeOutcome (*get)(void *self, void *out); const char *kind; } RmeParameterizationApi;
typedef struct { RmeOutcome (*couple)(void *self, void *peer); const char *kind; } RmeCouplingApi;
typedef struct { RmeOutcome (*adapt)(void *self); const char *kind; } RmeAdaptationApi;
typedef struct { RmeOutcome (*govern)(void *self); const char *kind; } RmeGovernanceApi;
/* resolve() is a QUERY: const self, so representation-independent child
 * resolution never has to cast away const. */
typedef struct { RmeOutcome (*resolve)(const void *self, size_t i, const void **out); const char *kind; } RmeNestedApi;

/* ----------------------------------------------------------------- ports
 * Header first in every one of these — the uniform-access rule above
 * depends on it, and rme_port_at() asserts the offsets are all zero.
 */
typedef struct { RmePortHeader hdr; const RmeStateApi           *api; } RmeStatePort;
typedef struct { RmePortHeader hdr; const RmeObservationApi     *api; } RmeObservationPort;
typedef struct { RmePortHeader hdr; const RmeTransitionApi      *api; } RmeTransitionPort;
typedef struct { RmePortHeader hdr; const RmeParameterizationApi *api; } RmeParameterizationPort;
typedef struct { RmePortHeader hdr; const RmeCouplingApi        *api; } RmeCouplingPort;
typedef struct { RmePortHeader hdr; const RmeAdaptationApi      *api; } RmeAdaptationPort;
typedef struct { RmePortHeader hdr; const RmeGovernanceApi      *api; } RmeGovernancePort;
typedef struct { RmePortHeader hdr; const RmeNestedApi          *api; } RmeNestedPort;

#endif /* RME_PORT_H */
