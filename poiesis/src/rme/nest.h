#ifndef RME_NEST_H
#define RME_NEST_H

#include "conform.h"

/* poiesis — nesting.
 *
 *   NestedValid(P,K) <=> RME7(P) ^ RME7(K) ^ ParentChildRelationValid(P,K)
 *
 * The nested-prototype relation is ABSTRACT.  It may be realized with
 * arrays, pointers, indices, handles, or any other type-safe
 * representation: the parent's nested port resolves a child by index and
 * hands back a pointer, so representation does not determine the semantic
 * relation.  Containment, reference, composition, identity and
 * ownership/lifetime stay separate — a prototype may contain another
 * without owning its storage.
 *
 * A child does NOT inherit the parent's semantics.  Deliberately absent:
 * any requirement that K activate the ports P activates, or that K
 * instantiate any operator.
 */

typedef struct {
    bool        ok;
    const char *why;
} RmeNesting;

RmeNesting rme_nested_valid(const RmePrototype *P, const RmePrototype *K);

bool rme_parent_child_relation_valid(const RmePrototype *P,
                                     const RmePrototype *K,
                                     const char **why);

/* Upper bound on children consulted while resolving the relation. */
#define RME_NEST_MAX 4096u

#endif /* RME_NEST_H */
