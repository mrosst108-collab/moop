/* NEGATIVE TEST — this file MUST FAIL to compile.
 *
 * Spec §8.2: the actor is a provenance/source type, NOT a prototype.  Were
 * it one, the ladder would read Actor -> Prototype -> Prototype and invite
 * precisely the semantic inheritance F7/F8 forbid.
 *
 *     Actor != Prototype != Root != Owner != Conformance authority
 *
 * Two attempts: treating an actor as a prototype, and submitting one to a
 * semantic predicate.
 */
#include "rme/validate.h"

const RmePrototype *actor_is_a_prototype(const RmeActor *a);
RmeConformance actor_conformance(const RmeActor *a);

const RmePrototype *actor_is_a_prototype(const RmeActor *a)
{
    const RmePrototype *p = a;   /* incompatible pointer types */
    return p;
}

RmeConformance actor_conformance(const RmeActor *a)
{
    return rme7_conforms(a);     /* actors are not subjects of conformance */
}
