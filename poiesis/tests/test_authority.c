/* poiesis — the AUTHORITY/VALIDITY suite (F7-F11).
 *
 *     Authority may be inherited; validity must be earned.
 *
 * The decisive test is not "does validation reject bad children?" but:
 *
 *     Can an unvalidated representation obtain the type accepted by
 *     downstream semantic operations without crossing rme_validate()?
 *
 * Every test below hands the authority machine MAXIMAL, LEGITIMATE input —
 * an authorized actor, an unattenuated capability, a legally derived
 * context, a successfully validated parent, genuine provenance — and then
 * asks whether any of it can substitute for the child's own validation.
 */
#include <stddef.h>

#include "rme/classify.h"
#include "rme/validate.h"

extern void rme_check(bool cond, const char *id, const char *what);

/* A well-formed representation: every port VESTIGIAL, pointing at its own
 * declared vestigial realization. */
static RmePrototype well_formed(const char *name)
{
    RmePrototype p = {
        .identity = { name },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_VESTIGIAL, RME_PORT_state },            &rme_vestigial_state            },
        .observation      = { { RME_VESTIGIAL, RME_PORT_observation },      &rme_vestigial_observation      },
        .transition       = { { RME_VESTIGIAL, RME_PORT_transition },       &rme_vestigial_transition       },
        .parameterization = { { RME_VESTIGIAL, RME_PORT_parameterization }, &rme_vestigial_parameterization },
        .coupling         = { { RME_VESTIGIAL, RME_PORT_coupling },         &rme_vestigial_coupling         },
        .adaptation       = { { RME_VESTIGIAL, RME_PORT_adaptation },       &rme_vestigial_adaptation       },
        .governance       = { { RME_VESTIGIAL, RME_PORT_governance },       &rme_vestigial_governance       },
        .nested           = { { RME_VESTIGIAL, RME_PORT_nested },           &rme_vestigial_nested           },
    };
    return p;
}

/* Three ways to be malformed, so the tests do not all turn on one check. */
static RmePrototype malformed_omitted_port(const char *name)
{
    RmePrototype p = well_formed(name);
    p.coupling.hdr.status = RME_UNDEFINED;          /* as a zero-fill leaves it */
    return p;
}
static RmePrototype malformed_out_of_domain(const char *name)
{
    RmePrototype p = well_formed(name);
    p.governance.hdr.status = (RmePortStatus)47;    /* outside {ACTIVE, VESTIGIAL} */
    return p;
}
static RmePrototype malformed_null_realization(const char *name)
{
    RmePrototype p = well_formed(name);
    p.state.api = nullptr;                          /* null is not a way to spell VESTIGIAL */
    return p;
}

/* The maximally trusted authority path, built fresh for each test. */
typedef struct {
    RmeActor               actor;
    RmeConstructionContext sys_root;
    RmeConstructionContext user_root;
    RmeConstructionContext proto_ctx;
    bool                   built;
} Trusted;

static Trusted make_trusted(void)
{
    Trusted t = { 0 };
    t.actor = (RmeActor){
        .identity        = "A0",
        .capability      = { "omnipotent", RME_ACT_ALL },
        .provenance      = "substrate origin",
        .authority_scope = "everything",
    };
    RmeCapability all = { "omnipotent", RME_ACT_ALL };
    t.built = rme_context_root(&t.actor, all, "system-root", &t.sys_root)
           && rme_context_derive(&t.sys_root, all, "user-root", &t.user_root)
           && rme_context_derive(&t.user_root, all, "prototype", &t.proto_ctx);
    return t;
}

void rme_test_authority(void);

void rme_test_authority(void)
{
    /* ---- CAP1 (capability_constructs): the POSITIVE path, end to end.
     * Without this, every negative test below could pass for the
     * uninteresting reason that the path never worked at all. */
    {
        rme_validation_reset();
        Trusted t = make_trusted();
        RmePrototype raw = well_formed("P_good");
        RmeConstructed c = rme_construct(&t.proto_ctx, RME_ACT_CONSTRUCT_PROTOTYPE, &raw);
        RmeValidation err;
        const RmeValidated *v = rme_validate_constructed(&c, &err);
        RmeConformance k = rme_validated_conforms(v);

        rme_check(t.built && c.authorized && v != nullptr && err.ok && k.ok,
                  "CAP1", "actor -> capability -> context -> construct -> validate -> conform succeeds");
    }

    /* ---- F8d: THE DECISIVE TEST.  Every authority-side input is maximal
     * and legitimate; the only defect is in the child's own representation.
     * Construction is authorized and validation still fails. */
    {
        rme_validation_reset();
        Trusted t = make_trusted();

        /* A parent that genuinely crossed its own boundary. */
        RmePrototype parent_raw = well_formed("Parent");
        const RmeValidated *parent = rme_validate(&parent_raw, nullptr);

        RmePrototype child_raw = malformed_omitted_port("Child");
        RmeConstructed c = rme_construct(&t.proto_ctx, RME_ACT_CONSTRUCT_PROTOTYPE, &child_raw);
        RmeValidation err;
        const RmeValidated *child = rme_validate_constructed(&c, &err);

        rme_check(t.built && parent != nullptr && c.authorized
                      && child == nullptr && !err.ok && err.port == RME_PORT_coupling,
                  "F8d", "maximal authority + validated parent + malformed child: "
                         "construction authorized, validation refuses");
    }

    /* ---- F8d': the same with an out-of-domain status, so the result does
     * not rest on the UNDEFINED sentinel alone (C11b). */
    {
        rme_validation_reset();
        Trusted t = make_trusted();
        RmePrototype raw = malformed_out_of_domain("Child");
        RmeConstructed c = rme_construct(&t.proto_ctx, RME_ACT_CONSTRUCT_PROTOTYPE, &raw);
        const RmeValidated *v = rme_validate_constructed(&c, nullptr);

        RmePrototype raw2 = malformed_null_realization("Child2");
        RmeConstructed c2 = rme_construct(&t.proto_ctx, RME_ACT_CONSTRUCT_PROTOTYPE, &raw2);
        const RmeValidated *v2 = rme_validate_constructed(&c2, nullptr);

        rme_check(c.authorized && v == nullptr && c2.authorized && v2 == nullptr,
                  "F8d'", "out-of-domain status and null realization also refuse under full authority");
    }

    /* ---- F8a: TrustedActor(A) ^ Produced(A,P) => RME7Conforms(P) is FALSE. */
    {
        rme_validation_reset();
        Trusted t = make_trusted();
        RmePrototype raw = malformed_omitted_port("P");
        RmeConstructed c = rme_construct(&t.proto_ctx, RME_ACT_CONSTRUCT_PROTOTYPE, &raw);
        RmeConformance k = rme7_conforms(c.raw);
        rme_check(c.authorized && !k.ok,
                  "F8a", "production by a trusted actor does not confer conformance");
    }

    /* ---- F8b: Capability(A,c) ^ Produces(A,X) => Validated(X) is FALSE. */
    {
        rme_validation_reset();
        Trusted t = make_trusted();
        RmePrototype raw = malformed_omitted_port("X");
        RmeConstructed c = rme_construct(&t.proto_ctx, RME_ACT_CONSTRUCT_PROTOTYPE, &raw);
        rme_check(c.authorized && rme_validate(c.raw, nullptr) == nullptr
                      && rme_validation_count() == 0,
                  "F8b", "capability to produce does not confer validation");
    }

    /* ---- F8c: Validated(X) ^ ChildOf(Y,X) => Validated(Y) is FALSE.
     * The parent's handle exists and is valid; the child's does not. */
    {
        rme_validation_reset();
        RmePrototype parent_raw = well_formed("X");
        const RmeValidated *x = rme_validate(&parent_raw, nullptr);
        RmePrototype child_raw = malformed_omitted_port("Y");
        const RmeValidated *y = rme_validate(&child_raw, nullptr);
        rme_check(x != nullptr && y == nullptr && rme_validation_count() == 1,
                  "F8c", "a validated parent does not validate its child");
    }

    /* ---- F7a: Conforms(parent) ^ ChildOf(child,parent) => Conforms(child)
     * is FALSE.  Assessed against the child's OWN declared schema. */
    {
        rme_validation_reset();
        RmePrototype parent_raw = well_formed("Parent");
        RmePrototype child_raw  = malformed_omitted_port("Child");
        RmeConformance kp = rme7_conforms(&parent_raw);
        RmeConformance kc = rme7_conforms(&child_raw);
        rme_check(kp.ok && !kc.ok,
                  "F7a", "conformance is nonhereditary: conformant parent, non-conformant child");
    }

    /* ---- F7b: classification does not descend either.  Same capability
     * context; the parent's system is RME-7 and the child's is RME-6, and
     * each verdict follows from its own declared governed edges. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t rx[] = { 1 };
        static const size_t ry[] = { 0 };
        static const RmeTransitionDecl parent_tr[] = { { "T_X", 0, rx, 1 }, { "T_Y", 1, ry, 1 } };
        static const RmeTransitionDecl child_tr[]  = { { "T_Y", 1, ry, 1 } };
        RmeSystem parent_sys = { slots, 2, parent_tr, 2, false };
        RmeSystem child_sys  = { slots, 2, child_tr,  1, false };

        RmeClassification pc, cc;
        bool ok = rme_classify(&parent_sys, &pc) && rme_classify(&child_sys, &cc);
        rme_check(ok && pc == RME_CLASS_RME7 && cc == RME_CLASS_RME6,
                  "F7b", "classification is nonhereditary: RME-7 parent, RME-6 child");
    }

    /* ---- Grant is monotone toward attenuation: widening is refused. */
    {
        Trusted t = make_trusted();
        RmeCapability narrow = { "narrow", RME_ACT_CONSTRUCT_PROTOTYPE };
        RmeConstructionContext attenuated;
        bool narrowed = rme_context_derive(&t.proto_ctx, narrow, "narrow", &attenuated);

        RmeCapability wider = { "wider", RME_ACT_ALL };
        RmeConstructionContext widened;
        bool widening_refused = !rme_context_derive(&attenuated, wider, "wider", &widened);

        rme_check(narrowed && widening_refused && rme_context_depth(&attenuated) == 4,
                  "G1", "Grant attenuates: Auth(C') subset-of Auth(C), never the reverse");
    }

    /* ---- An attenuated context cannot perform what it gave up, however
     * powerful its ancestors remain. */
    {
        Trusted t = make_trusted();
        RmeCapability narrow = { "no-nesting", RME_ACT_CONSTRUCT_PROTOTYPE };
        RmeConstructionContext attenuated;
        bool ok = rme_context_derive(&t.proto_ctx, narrow, "narrow", &attenuated);
        RmePrototype raw = well_formed("P");
        RmeConstructed c = rme_construct(&attenuated, RME_ACT_NEST, &raw);
        rme_check(ok && !c.authorized && c.raw == nullptr,
                  "G2", "an attenuated context cannot exercise an action it does not hold");
    }

    /* ---- F9, the reverse direction: validation grants no authority.  A
     * successfully validated prototype exists, yet a context lacking the
     * action still refuses to construct.  Nothing about holding a validated
     * handle widens capability. */
    {
        rme_validation_reset();
        Trusted t = make_trusted();
        RmePrototype raw = well_formed("P");
        const RmeValidated *v = rme_validate(&raw, nullptr);

        RmeCapability none = { "inert", 0u };
        RmeConstructionContext powerless;
        bool derived = rme_context_derive(&t.proto_ctx, none, "powerless", &powerless);
        RmeConstructed c = rme_construct(&powerless, RME_ACT_CONSTRUCT_PROTOTYPE, &raw);

        rme_check(v != nullptr && derived && !c.authorized,
                  "F9", "validation establishes validity and confers no construction authority");
    }

    /* ---- ProtoC's third possibility: a prototype may CARRY a capability
     * reference without acquiring authority or validity from it. */
    {
        rme_validation_reset();
        static const RmeCapability omnipotent = { "omnipotent", RME_ACT_ALL };
        RmePrototype raw = malformed_omitted_port("P");
        RmeCapabilityRef ref = { &raw, &omnipotent };   /* association, not a field */
        const RmeValidated *v = rme_validate(ref.subject, nullptr);
        rme_check(ref.capability->actions == RME_ACT_ALL && v == nullptr,
                  "CAPREF", "a carried capability reference confers neither authority nor validity");
    }

    /* ---- The validated prototype is substrate-owned: mutating the raw
     * object afterwards does not reach through the handle. */
    {
        rme_validation_reset();
        RmePrototype raw = well_formed("P");
        const RmeValidated *v = rme_validate(&raw, nullptr);
        raw.coupling.hdr.status = RME_UNDEFINED;        /* corrupt the caller's copy */
        RmeConformance k = rme_validated_conforms(v);
        rme_check(v != nullptr && k.ok
                      && rme_validated_proto(v) != &raw,
                  "V1", "validation copies: post-validation mutation of the raw object cannot reach it");
    }

    /* ---- Downstream semantic operations accept only the validated type. */
    {
        rme_validation_reset();
        RmePrototype p_raw = well_formed("P");
        RmePrototype q_raw = well_formed("Q");
        const RmeValidated *p = rme_validate(&p_raw, nullptr);
        const RmeValidated *q = rme_validate(&q_raw, nullptr);
        RmeRelation R = { nullptr, 0, true };
        RmeComposition c  = rme_compose_valid_v(p, q, &R);
        RmeComposition c2 = rme_compose_valid_v(nullptr, q, &R);
        rme_check(c.ok && !c2.ok,
                  "V2", "composition over validated handles; an unvalidated operand has no handle to pass");
    }
}
