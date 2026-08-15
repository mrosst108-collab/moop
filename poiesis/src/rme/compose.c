#include "compose.h"

/* EndpointsValid(R): every endpoint names a real schema port on the right
 * prototype, and the two prototypes are supplied.  This is a check on the
 * relation's well-formedness, before any status or compatibility question
 * arises. */
static bool endpoints_valid(const RmePrototype *P, const RmePrototype *Q,
                            const RmeRelation *R, size_t *bad, const char **why)
{
    if (P == nullptr || Q == nullptr) {
        if (why) *why = "composition needs two prototypes";
        return false;
    }
    for (size_t i = 0; i < R->count; i++) {
        RmeConnection e = R->edges[i];
        if (e.p < 0 || e.p >= RME_PORT_COUNT || e.q < 0 || e.q >= RME_PORT_COUNT) {
            if (bad) *bad = i;
            if (why) *why = "connection names a port outside the schema";
            return false;
        }
    }
    return true;
}

RmeComposition rme_admissible(const RmePrototype *P,
                              const RmePrototype *Q,
                              const RmeRelation  *R)
{
    RmeComposition r = { false, 0, 0, "unevaluated" };

    if (R == nullptr) {
        r.why = "no connection relation supplied";
        return r;
    }
    r.obligations = R->count;   /* exactly |R| — never the count of compatible pairs */
    r.edge = R->count;

    /* R->declared is DELIBERATELY NOT READ here.  Admissibility is a
     * compatibility predicate over endpoints; declaration is a relational
     * configuration.  A proposed future relation is admissible or not on
     * exactly the same terms as an existing one. */
    if (!endpoints_valid(P, Q, R, &r.edge, &r.why)) {
        return r;
    }

    for (size_t i = 0; i < R->count; i++) {
        RmeConnection e = R->edges[i];
        const RmePortHeader *hp = rme_port_at_const(P, e.p);
        const RmePortHeader *hq = rme_port_at_const(Q, e.q);

        /* Only PARTICIPATING endpoints incur obligations, and a
         * participating endpoint must be ACTIVE.  A vestigial port may sit
         * in the envelope untouched, but it cannot be wired. */
        if (hp->status != RME_ACTIVE) {
            r.edge = i;
            r.why = "connection endpoint in P is not ACTIVE";
            return r;
        }
        if (hq->status != RME_ACTIVE) {
            r.edge = i;
            r.why = "connection endpoint in Q is not ACTIVE";
            return r;
        }
        if (!rme_compatible(P, e.p, Q, e.q, &r.why)) {
            r.edge = i;
            return r;
        }
    }

    /* Note what did NOT happen: no port realization was invoked.  R is a
     * relation, not an event. */
    r.ok = true;
    r.edge = R->count;
    r.why = "admissible";
    return r;
}

RmeComposition rme_compose_valid(const RmePrototype *P,
                                 const RmePrototype *Q,
                                 const RmeRelation  *R)
{
    RmeComposition r = { false, 0, 0, "unevaluated" };

    if (R == nullptr) {
        r.why = "no connection relation supplied";
        return r;
    }
    r.obligations = R->count;
    r.edge = R->count;

    /* Declared(R).  An undeclared relation is not a composition, however
     * compatible the participants' ports happen to be -- and however
     * ADMISSIBLE it is.  Admissible =/=> Declared. */
    if (!R->declared) {
        r.why = "connection relation is not declared";
        return r;
    }

    r = rme_admissible(P, Q, R);
    if (r.ok) {
        r.why = "composition valid";
    }
    return r;
}
