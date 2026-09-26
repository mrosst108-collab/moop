#include "actor.h"

bool rme_auth_subset(const RmeCapability *lo, const RmeCapability *hi)
{
    if (lo == nullptr || hi == nullptr) {
        return false;
    }
    return (lo->actions & ~hi->actions) == 0u;
}

bool rme_context_root(const RmeActor *a, RmeCapability want,
                      const char *label, RmeConstructionContext *out)
{
    if (a == nullptr || out == nullptr) {
        return false;
    }
    /* An actor cannot originate a context more powerful than itself. */
    if (!rme_auth_subset(&want, &a->capability)) {
        return false;
    }
    out->label      = label;
    out->origin     = a;
    out->parent     = nullptr;
    out->capability = want;
    return true;
}

bool rme_context_derive(const RmeConstructionContext *parent, RmeCapability want,
                        const char *label, RmeConstructionContext *out)
{
    if (parent == nullptr || out == nullptr) {
        return false;
    }
    /* Grant is monotone toward attenuation.  Widening is not expressible
     * through this entry point, so a descendant context cannot acquire an
     * action its ancestor lacked. */
    if (!rme_auth_subset(&want, &parent->capability)) {
        return false;
    }
    out->label      = label;
    out->origin     = parent->origin;   /* provenance travels */
    out->parent     = parent;           /* capability chain */
    out->capability = want;
    return true;
}

bool rme_context_permits(const RmeConstructionContext *c, unsigned actions)
{
    if (c == nullptr) {
        return false;
    }
    return (actions & ~c->capability.actions) == 0u;
}

size_t rme_context_depth(const RmeConstructionContext *c)
{
    size_t d = 0;
    for (; c != nullptr; c = c->parent) {
        d++;
    }
    return d;
}

RmeConstructed rme_construct(const RmeConstructionContext *ctx,
                             unsigned needed_actions,
                             const RmePrototype *raw)
{
    RmeConstructed r = { nullptr, ctx, false };

    if (!rme_context_permits(ctx, needed_actions)) {
        return r;   /* not authorized to attempt */
    }
    /* Authorized.  Note what is NOT inspected here: the prototype's ports,
     * statuses, schema, contracts or conformance.  Construction authority
     * is a capability relation, not a prototype property (F9), so this
     * function must not be tempted into pre-judging the representation. */
    r.raw = raw;
    r.authorized = true;
    return r;
}
