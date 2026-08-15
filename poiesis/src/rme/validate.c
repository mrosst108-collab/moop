#include "validate.h"

/* The definition is confined to this translation unit.  Everywhere else
 * RmeValidated is incomplete, which is what makes forging or copying one a
 * compile error rather than a convention violation. */
struct RmeValidated {
    RmePrototype proto;   /* a COPY of the RECORD -- see the ownership note
                           * in validate.h for what that does and does not
                           * cover. */
    unsigned     epoch;   /* the arena generation this handle belongs to */
};

#define RME_VALIDATED_CAP 512u

static struct RmeValidated arena[RME_VALIDATED_CAP];
static size_t              arena_used;   /* monotonic high-water mark */
static size_t              gen_count;    /* validations in this generation */
static unsigned            arena_epoch = 1u;

/* Recycling arena storage would otherwise leave outstanding handles
 * silently DENOTING A DIFFERENT PROTOTYPE -- a validated handle that no
 * longer designates what it validated is exactly the laundering F7/F8
 * forbid, arriving by lifetime rather than by inheritance.  Bumping the
 * epoch makes every prior handle inert instead. */
/* THE INVARIANT: a released identity must never become a valid identity for
 * a later object.
 *
 * Allocation is MONOTONIC across resets, and that is load-bearing rather
 * than lazy.  A handle is a pointer INTO a slot, so if reset rewound the
 * cursor the next validation would overwrite that slot -- stamping it with
 * the CURRENT epoch and bringing the old handle back to life denoting a
 * different prototype.  A generation counter cannot separate them while the
 * address is shared.  Never reusing a slot is what makes a released handle
 * permanently dead.  Exhaustion is refused honestly (see rme_validate). */
void rme_validation_reset(void)
{
    arena_epoch++;
    gen_count = 0;
}

static bool live(const RmeValidated *v)
{
    return v != nullptr && v->epoch == arena_epoch;
}

size_t rme_validation_count(void)
{
    return gen_count;   /* this generation, not the high-water mark */
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
    /* SPEC §6 states the status closure as a VALIDATION-BOUNDARY claim:
     *     Status(p)=ACTIVE    => ActiveRealization(p)
     *     Status(p)=VESTIGIAL => VestigialRealization(p)
     * and §15.1 step 5(c) requires the boundary to refuse an ACTIVE port
     * aimed at the declared vestigial realization.  Omitting this conjunct
     * let exactly that record reach validated state. */
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        if (!rme_realization_valid(raw, (RmePortId)i, &e->why)) {
            e->port = (RmePortId)i;
            return nullptr;
        }
    }

    if (arena_used >= RME_VALIDATED_CAP) {
        e->why = "validated-prototype storage exhausted";
        return nullptr;
    }

    /* Copy into substrate-owned storage.  After this point the caller can
     * mutate its own object freely without affecting what was validated. */
    struct RmeValidated *v = &arena[arena_used++];
    gen_count++;
    v->proto = *raw;
    v->epoch = arena_epoch;

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
    return live(v) ? &v->proto : nullptr;
}

const char *rme_validated_name(const RmeValidated *v)
{
    return (live(v) && v->proto.identity.name) ? v->proto.identity.name : nullptr;
}

bool rme_validated_live(const RmeValidated *v)
{
    return live(v);
}

RmeConformance rme_validated_conforms(const RmeValidated *v)
{
    if (!live(v)) {
        RmeConformance r = { false, RME_PORT_COUNT,
                             "handle is null or belongs to a released arena generation" };
        return r;
    }
    return rme7_conforms(&v->proto);
}

RmeComposition rme_compose_valid_v(const RmeValidated *P, const RmeValidated *Q,
                                   const RmeRelation *R)
{
    if (!live(P) || !live(Q)) {
        RmeComposition c = { false, 0, 0,
                             "composition requires live validated prototypes" };
        return c;
    }
    return rme_compose_valid(&P->proto, &Q->proto, R);
}
