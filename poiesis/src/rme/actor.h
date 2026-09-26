#ifndef RME_ACTOR_H
#define RME_ACTOR_H

#include "proto.h"

/* poiesis — the AUTHORITY relation class (spec §8.2, §15.0.1-2, F7-F11).
 *
 * Nothing in this header is a prototype, and nothing in it participates in
 * conformance, port schemas, port status, composition, classification,
 * RmePrototype or RmeSystem.  It is a DIFFERENT TYPED RELATION CLASS whose
 * only legal effect on the semantic side is to authorize a construction
 * ATTEMPT.
 *
 *     Actor -- Capability --Grant--> Capability' -- Context --> construction
 *
 * F9, bidirectional: a capability authorizes an attempted construction and
 * does NOT establish semantic validity; validation establishes semantic
 * validity and does NOT grant construction authority.  Accordingly there is
 * no function here that takes an RmeValidated, and none in validate.h that
 * returns a capability.
 *
 * F10: authority, provenance and semantic predicates are distinct typed
 * relations.  A single construction both authorizes (authority) and records
 * origin (provenance); those are two different edges, and neither is
 * semantic inheritance.
 *
 * DELIBERATELY ABSENT from every type below: any validation, conformance,
 * classification or port-status field.  There is nothing here to launder.
 * `child->validated = parent->validated` is not merely forbidden by rule —
 * no such member exists to write.
 */

/* Auth(C): the set of actions a capability permits. */
typedef enum {
    RME_ACT_CONSTRUCT_SYSTEM_ROOT = 1u << 0,
    RME_ACT_CONSTRUCT_USER_ROOT   = 1u << 1,
    RME_ACT_CONSTRUCT_PROTOTYPE   = 1u << 2,
    RME_ACT_NEST                  = 1u << 3,
} RmeAction;

#define RME_ACT_ALL (RME_ACT_CONSTRUCT_SYSTEM_ROOT | RME_ACT_CONSTRUCT_USER_ROOT | \
                     RME_ACT_CONSTRUCT_PROTOTYPE   | RME_ACT_NEST)

/* Capability is its OWN TYPE, not an untyped bitfield on the actor.  That
 * is what makes "hereditary" unambiguous (F11): the type names what is
 * inherited. */
typedef struct {
    const char *label;
    unsigned    actions;   /* Auth(C) */
} RmeCapability;

/* C' <= C  iff  Auth(C') subset-of Auth(C). */
bool rme_auth_subset(const RmeCapability *lo, const RmeCapability *hi);

/* The actor: a provenance/source type, never a prototype (§8.2). */
typedef struct {
    const char   *identity;
    RmeCapability capability;
    const char   *provenance;
    const char   *authority_scope;
} RmeActor;

/* The capability chain.  `parent` is capability inheritance; `origin` is
 * provenance.  Two different edges, deliberately two different fields. */
typedef struct RmeConstructionContext {
    const char                          *label;
    const RmeActor                      *origin;   /* provenance */
    const struct RmeConstructionContext *parent;   /* capability inheritance */
    RmeCapability                        capability;
} RmeConstructionContext;

/* Root context: capability must be within the actor's own. */
bool rme_context_root(const RmeActor *a, RmeCapability want,
                      const char *label, RmeConstructionContext *out);

/* Grant.  Monotone toward attenuation:
 *
 *     Auth(C') subset-of Auth(C)      always
 *     Auth(C') superset-of Auth(C)    never
 *
 * Returns false if `want` exceeds the parent's capability.  There is no
 * widening entry point in this header. */
bool rme_context_derive(const RmeConstructionContext *parent, RmeCapability want,
                        const char *label, RmeConstructionContext *out);

bool   rme_context_permits(const RmeConstructionContext *c, unsigned actions);
size_t rme_context_depth(const RmeConstructionContext *c);

/* The product of an authorized construction ATTEMPT.
 *
 * `raw` is NOT a validated prototype and has no route to becoming one
 * except rme_validate().  This struct carries provenance and authorization
 * and no semantic predicate whatsoever. */
typedef struct {
    const RmePrototype           *raw;
    const RmeConstructionContext *provenance;
    bool                          authorized;
} RmeConstructed;

/* Asserts only: "raw was produced under ctx, which was authorized to
 * attempt it."  It asserts nothing of the form RME7Conforms(raw),
 * Validated(raw), or Classification(raw). */
RmeConstructed rme_construct(const RmeConstructionContext *ctx,
                             unsigned needed_actions,
                             const RmePrototype *raw);

/* ProtoC's third possibility (§15.0.1): a prototype may CARRY OR REFERENCE
 * a capability without becoming an actor or acquiring its authority.  Held
 * ALONGSIDE the prototype as an association — deliberately not a field
 * inside RmePrototype, where it would read as "the prototype possesses
 * authority" and then as "its authority explains its validity".
 *
 *     RmePrototype -- association -- RmeCapability    neither becomes the other
 */
typedef struct {
    const RmePrototype *subject;
    const RmeCapability *capability;
} RmeCapabilityRef;

#endif /* RME_ACTOR_H */
