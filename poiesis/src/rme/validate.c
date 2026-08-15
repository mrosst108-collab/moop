#include "validate.h"

/* The definition is confined to this translation unit.  Everywhere else
 * RmeValidated is incomplete, which is what makes forging or copying one a
 * compile error rather than a convention violation. */
struct RmeValidated {
    RmePrototype proto;   /* a COPY: not the caller's storage */
};

#define RME_VALIDATED_CAP 64u

static struct RmeValidated arena[RME_VALIDATED_CAP];
static size_t              arena_used;

void rme_validation_reset(void)
{
    arena_used = 0;
}

size_t rme_validation_count(void)
{
    return arena_used;
}

const RmeValidated *rme_validate(const RmePrototype *raw, RmeValidation *err)
{
    RmeValidation local = { false, RME_PORT_COUNT, "unevaluated" };
    RmeValidation *e = err ? err : &local;

    e->ok = false;
    e->port = RME_PORT_COUNT;

    if (raw == nullptr) {
        e->why = "null representation";
        return nullptr;
    }

    /* The REPRESENTATION invariant: schema identity, the status closure
     * {ACTIVE, VESTIGIAL} (so the UNDEFINED construction sentinel and any
     * out-of-domain integer are refused here, C11/C11b), and type validity
     * of every declared realization. */
    if (!rme_schema_valid(raw, &e->why)) {
        return nullptr;
    }
    if (!rme_port_complete(raw, &e->port, &e->why)) {
        return nullptr;
    }
    if (!rme_type_safe(raw, &e->port, &e->why)) {
        return nullptr;
    }

    if (arena_used >= RME_VALIDATED_CAP) {
        e->why = "validated-prototype storage exhausted";
        return nullptr;
    }

    /* Copy into substrate-owned storage.  After this point the caller can
     * mutate its own object freely without affecting what was validated. */
    struct RmeValidated *v = &arena[arena_used++];
    v->proto = *raw;

    e->ok = true;
    e->why = "validated";
    return v;
}

const RmeValidated *rme_validate_constructed(const RmeConstructed *c, RmeValidation *err)
{
    RmeValidation local = { false, RME_PORT_COUNT, "unevaluated" };
    RmeValidation *e = err ? err : &local;

    if (c == nullptr) {
        e->ok = false;
        e->port = RME_PORT_COUNT;
        e->why = "null construction";
        return nullptr;
    }
    /* c->authorized and c->provenance are deliberately NOT consulted.  A
     * maximally authorized construction under a fully capable context with
     * a validated parent yields exactly the same verdict as the bare
     * representation would (F8). */
    return rme_validate(c->raw, err);
}

const RmePrototype *rme_validated_proto(const RmeValidated *v)
{
    return v ? &v->proto : nullptr;
}

const char *rme_validated_name(const RmeValidated *v)
{
    return (v && v->proto.identity.name) ? v->proto.identity.name : nullptr;
}

RmeConformance rme_validated_conforms(const RmeValidated *v)
{
    if (v == nullptr) {
        RmeConformance r = { false, RME_PORT_COUNT, "null validated prototype" };
        return r;
    }
    return rme7_conforms(&v->proto);
}

RmeComposition rme_compose_valid_v(const RmeValidated *P, const RmeValidated *Q,
                                   const RmeRelation *R)
{
    if (P == nullptr || Q == nullptr) {
        RmeComposition c = { false, 0, 0, "composition requires validated prototypes" };
        return c;
    }
    return rme_compose_valid(&P->proto, &Q->proto, R);
}
