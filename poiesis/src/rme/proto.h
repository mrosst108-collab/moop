#ifndef RME_PROTO_H
#define RME_PROTO_H

#include "port.h"

/* poiesis — the prototype record.
 *
 * A prototype is a SCHEMA-COMPLETE TYPED ENVELOPE whose declared ports may
 * be individually realized as ACTIVE or VESTIGIAL: sparse *substantive*
 * realization, never sparse schema.  Every port below is always present as
 * a field; what varies per instance is each port's status and realization.
 */

/* Identity and schema identity are SEPARATE (spec §Schema identity).
 * "P claims RME-7" is underspecified without the latter, and a bare enum
 * must not become the whole versioning mechanism. */
typedef struct {
    const char *name;
} RmeProtoId;

typedef struct {
    const char *name;   /* which schema this prototype claims to satisfy */
    unsigned    major;
    unsigned    minor;
} RmeSchemaId;

/* The schema this build implements. */
#define RME_SCHEMA_NAME  "rme7-poiesis"
#define RME_SCHEMA_MAJOR 0u
#define RME_SCHEMA_MINOR 1u

typedef struct RmePrototype {
    RmeProtoId  identity;
    RmeSchemaId schema;

    /* Every schema port, always present.  Sparse realization, never sparse
     * schema — a field left out of a designated initializer zero-fills to
     * RME_UNDEFINED and is rejected by rme7_conforms(). */
    RmeStatePort            state;
    RmeObservationPort      observation;
    RmeTransitionPort       transition;
    RmeParameterizationPort parameterization;
    RmeCouplingPort         coupling;
    RmeAdaptationPort       adaptation;
    RmeGovernancePort       governance;
    RmeNestedPort           nested;
} RmePrototype;

/* Uniform access to a port's header, preserving each port's own type in
 * the struct.  Valid ISO C: the header is the first member of every port
 * struct, and a pointer to a struct suitably converted points to its
 * initial member.  A compile-time check in proto.c asserts that. */
RmePortHeader       *rme_port_at(RmePrototype *p, RmePortId id);
const RmePortHeader *rme_port_at_const(const RmePrototype *p, RmePortId id);

/* Non-null iff the port's api pointer is set.  Used by TypeSafe: a port of
 * either status must point at a valid object of its declared interface
 * type, so a null api is a type-discipline failure and NOT a way to spell
 * "vestigial". */
const void *rme_port_api(const RmePrototype *p, RmePortId id);

/* Set every port to `status` with the supplied api objects.  Convenience
 * for tests; production prototypes use designated initializers so that
 * omission is caught rather than defaulted. */
void rme_proto_set_status(RmePrototype *p, RmePortId id, RmePortStatus s);

#endif /* RME_PROTO_H */
