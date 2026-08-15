#include "nest.h"

bool rme_parent_child_relation_valid(const RmePrototype *P,
                                     const RmePrototype *K,
                                     const char **why)
{
    if (P == nullptr || K == nullptr) {
        if (why) *why = "nesting needs a parent and a child";
        return false;
    }

    /* Containment is declared through the parent's nested port.  A parent
     * that does not declare the relation does not contain the child,
     * whatever its storage happens to hold. */
    if (P->nested.hdr.status != RME_ACTIVE) {
        if (why) *why = "parent does not declare a child relation (nested port is not ACTIVE)";
        return false;
    }
    if (P->nested.api == nullptr || P->nested.api->resolve == nullptr) {
        if (why) *why = "parent's nested realization cannot resolve children";
        return false;
    }

    /* Resolution is representation-independent: we ask the parent to
     * resolve by index and compare identity of the result.  Whether the
     * realization is backed by an array, a handle table or an index map is
     * not our business here. */
    for (size_t i = 0; i < RME_NEST_MAX; i++) {
        const void *child = nullptr;
        RmeOutcome o = P->nested.api->resolve(P, i, &child);
        if (o != RME_OK) {
            break;
        }
        if (child == (const void *)K) {
            return true;
        }
    }

    if (why) *why = "parent's child relation does not resolve to this child";
    return false;
}

RmeNesting rme_nested_valid(const RmePrototype *P, const RmePrototype *K)
{
    RmeNesting r = { false, "unevaluated" };

    /* Both are INDEPENDENTLY conformant objects — conformance is unary and
     * is evaluated separately for each. */
    RmeConformance rp = rme7_conforms(P);
    if (!rp.ok) {
        r.why = rp.why;
        return r;
    }
    RmeConformance rk = rme7_conforms(K);
    if (!rk.ok) {
        r.why = rk.why;
        return r;
    }
    if (!rme_parent_child_relation_valid(P, K, &r.why)) {
        return r;
    }

    r.ok = true;
    r.why = "nesting valid";
    return r;
}
