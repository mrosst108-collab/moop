#include <string.h>

#include "bind.h"

static bool streq(const char *a, const char *b)
{
    return a != nullptr && b != nullptr && strcmp(a, b) == 0;
}

bool rme_represents(const RmeField *f, const RmeRead *r)
{
    if (f == nullptr || r == nullptr) {
        return false;
    }
    /* Semantic identity.  The field must EXPLICITLY designate this
     * dependency.  A null `represents` designates nothing, and matching on
     * f->name instead would let a coincidence of spelling stand in for a
     * declaration — which is exactly what "explicitly designated component"
     * rules out. */
    if (!streq(f->represents, r->dep)) {
        return false;
    }
    /* Declared type.  The dependency's contract constrains what may
     * represent it; right designation with the wrong type is not
     * representation. */
    if (!streq(f->type, r->type)) {
        return false;
    }
    return true;
}

RmeBindResult rme_bind_valid(const RmeTransitionBind *t)
{
    RmeBindResult res = { false, 0, "unevaluated" };

    if (t == nullptr) {
        res.why = "null transition bind";
        return res;
    }
    if (t->read_count > 0 && t->reads == nullptr) {
        res.why = "read_count > 0 but Reads(T) is null";
        return res;
    }
    if (t->read_count > 0 && t->arg == nullptr) {
        res.why = "transition declares reads but no ArgType: nothing can represent them";
        return res;
    }

    for (size_t i = 0; i < t->read_count; i++) {
        const RmeRead *r = &t->reads[i];
        bool found = false;

        /* Fields(ArgType(T)) is consulted only here, and only to ask whether
         * something in it represents a read that was declared elsewhere.
         * Nothing in this loop can add to, or infer, Reads(T). */
        size_t nf = (t->arg->fields == nullptr) ? 0 : t->arg->field_count;
        for (size_t j = 0; j < nf && !found; j++) {
            found = rme_represents(&t->arg->fields[j], r);
        }

        if (!found) {
            res.read = i;
            res.why = "declared read has no representing field in ArgType(T): "
                      "dependency expanded without the matching interface change";
            return res;
        }
    }

    res.ok   = true;
    res.read = t->read_count;
    res.why  = "every declared read is represented";
    return res;
}
