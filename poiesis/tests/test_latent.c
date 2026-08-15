/* poiesis — the remaining conformance-suite entries: C11b and C18a/b/c.
 *
 * C18 is the substrate's actual thesis, tested rather than asserted:
 *
 *   Latent(P,Q,R) <=> exists p in P, q in Q :
 *                     Declared(p) ^ Declared(q) ^ Compatible(p,q,R)
 *
 * "R may be introduced without redesign of either object's declared
 * ontology or port interface IFF every endpoint and every boundary-relevant
 * distinction R's compatibility contract requires is declared, retained and
 * reachable through the existing declared interface."
 *
 * Note what is NOT claimed: not that any two conformant objects will
 * eventually interoperate.  Preservation does not create compatibility
 * (C18b); it keeps compatibility an open question rather than a foreclosed
 * one (C18a).  A relation needing a port that was never declared is not
 * admissible at any price short of boundary redesign (C18c).
 */
#include <stddef.h>

#include "rme/schedule.h"
#include "rme/validate.h"

extern void rme_check(bool cond, const char *id, const char *what);

static RmeOutcome l_state(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome l_obs(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome l_step(void *self, const void *args) { (void)self; (void)args; return RME_OK; }
static RmeOutcome l_get(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome l_couple(void *self, void *peer) { (void)self; (void)peer; return RME_OK; }
static RmeOutcome l_adapt(void *self) { (void)self; return RME_OK; }
static RmeOutcome l_govern(void *self) { (void)self; return RME_OK; }
static RmeOutcome l_resolve(const void *self, size_t i, const void **out)
{ (void)self; (void)i; if (out) *out = nullptr; return RME_OK; }

static const RmeStateApi            a_state  = { l_state,   "active" };
static const RmeObservationApi      a_obs    = { l_obs,     "active" };
static const RmeTransitionApi       a_trans  = { l_step,    "active" };
static const RmeParameterizationApi a_param  = { l_get,     "active" };
static const RmeCouplingApi         a_coup   = { l_couple,  "active" };
static const RmeAdaptationApi       a_adapt  = { l_adapt,   "active" };
static const RmeGovernanceApi       a_gov    = { l_govern,  "active" };
static const RmeNestedApi           a_nested = { l_resolve, "active" };

static RmePrototype active(const char *name)
{
    RmePrototype p = {
        .identity = { name },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_ACTIVE, RME_PORT_state },            &a_state  },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &a_obs    },
        .transition       = { { RME_ACTIVE, RME_PORT_transition },       &a_trans  },
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &a_param  },
        .coupling         = { { RME_ACTIVE, RME_PORT_coupling },         &a_coup   },
        .adaptation       = { { RME_ACTIVE, RME_PORT_adaptation },       &a_adapt  },
        .governance       = { { RME_ACTIVE, RME_PORT_governance },       &a_gov    },
        .nested           = { { RME_ACTIVE, RME_PORT_nested },           &a_nested },
    };
    return p;
}

/* A byte-level snapshot, so "the boundary did not change" is verified
 * rather than asserted. */
static bool boundary_unchanged(const RmePrototype *before, const RmePrototype *after)
{
    if (before->schema.name  != after->schema.name
        || before->schema.major != after->schema.major
        || before->schema.minor != after->schema.minor) {
        return false;
    }
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        const RmePortHeader *hb = rme_port_at_const(before, (RmePortId)i);
        const RmePortHeader *ha = rme_port_at_const(after,  (RmePortId)i);
        if (hb->status != ha->status || hb->id != ha->id) {
            return false;
        }
        if (rme_port_api(before, (RmePortId)i) != rme_port_api(after, (RmePortId)i)) {
            return false;
        }
    }
    return true;
}

void rme_test_latent(void);

void rme_test_latent(void)
{
    /* ---- C11b: a status outside {ACTIVE, VESTIGIAL} is rejected AT THE
     * VALIDATION BOUNDARY.  This is a claim about the boundary, not about
     * the C type system: ISO C does not stop an arbitrary integer reaching
     * an enum object, so what is asserted is that no such representation
     * enters the validated-prototype state. */
    {
        rme_validation_reset();
        RmePrototype p = active("P");
        p.governance.hdr.status = (RmePortStatus)91;   /* out of domain */
        RmeValidation err;
        const RmeValidated *v = rme_validate(&p, &err);
        rme_check(v == nullptr && !err.ok && err.port == RME_PORT_governance
                      && rme_validation_count() == 0,
                  "C11b", "status outside {ACTIVE,VESTIGIAL} rejected at the validation boundary");
    }

    /* ---- C18a: retained compatible endpoints, then a LATER-SPECIFIED
     * relation.  Admissible(R_new,P,Q) holds while R_new is undeclared; the
     * relation may then be declared, and NEITHER BOUNDARY CHANGES.
     *
     * This is the whole substrate thesis in one test, and it is why
     * admissibility had to be separable from declaration: with the two
     * collapsed, "admissible but not yet declared" is not a state the API
     * can represent. */
    {
        RmePrototype p = active("P");
        RmePrototype q = active("Q");
        RmePrototype p_before = p, q_before = q;

        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };

        /* R_new does not exist yet: Declared(R_new) = false. */
        RmeRelation R_new = { e, 1, false };
        RmeComposition adm    = rme_admissible(&p, &q, &R_new);
        RmeComposition not_yet = rme_compose_valid(&p, &q, &R_new);

        /* Someone now declares it.  Nothing about P or Q is touched. */
        RmeRelation R_declared = { e, 1, true };
        RmeComposition after = rme_compose_valid(&p, &q, &R_declared);

        rme_check(adm.ok && !not_yet.ok && after.ok
                      && boundary_unchanged(&p_before, &p)
                      && boundary_unchanged(&q_before, &q),
                  "C18a", "admissible while undeclared; declaring it redesigns neither boundary");
    }

    /* ---- C18b: the endpoints exist and are ACTIVE, but their contracts are
     * incompatible.  Rejected, and NO SILENT REDESIGN: both prototypes are
     * untouched and both remain conformant.  Preservation does not create
     * compatibility (N6). */
    {
        RmePrototype p = active("P");
        RmePrototype q = active("Q");
        RmePrototype p_before = p, q_before = q;

        const RmeConnection e[] = { { RME_PORT_state, RME_PORT_governance } };
        RmeRelation R = { e, 1, false };
        RmeComposition adm = rme_admissible(&p, &q, &R);

        RmeConformance kp = rme7_conforms(&p);
        RmeConformance kq = rme7_conforms(&q);

        rme_check(!adm.ok && adm.edge == 0
                      && kp.ok && kq.ok
                      && boundary_unchanged(&p_before, &p)
                      && boundary_unchanged(&q_before, &q),
                  "C18b", "incompatible contracts: refused, both prototypes intact and conformant");
    }

    /* ---- C18c: R_new requires a port the schema never declared.  It cannot
     * be admitted at all — not because it is incompatible, but because
     * there is no endpoint for it to name.  Admitting it would require
     * changing the declared boundary, which is precisely what §9 says is
     * outside the guarantee. */
    {
        RmePrototype p = active("P");
        RmePrototype q = active("Q");

        /* A port id beyond the schema: the shape a future capability with
         * no declared endpoint would take. */
        const RmeConnection e[] = { { RME_PORT_state, (RmePortId)RME_PORT_COUNT } };
        RmeRelation R = { e, 1, false };
        RmeComposition adm = rme_admissible(&p, &q, &R);

        rme_check(!adm.ok && adm.edge == 0,
                  "C18c", "a relation naming an undeclared port cannot be admitted");
    }

    /* ---- The distinction C18a rests on, isolated.  A VESTIGIAL endpoint is
     * retained (it is in the envelope, declared and typed) yet is NOT
     * admissible, because Participates(p,R_C) => Status(p) = ACTIVE is
     * unconditional.  Retention keeps the future open; it does not wire
     * anything (N5, N6). */
    {
        RmePrototype p = active("P");
        RmePrototype q = active("Q");
        q.coupling = (RmeCouplingPort){ { RME_VESTIGIAL, RME_PORT_coupling },
                                        &rme_vestigial_coupling };

        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, false };
        RmeComposition adm = rme_admissible(&p, &q, &R);

        /* Retained: still declared, still typed, still in the envelope. */
        RmePortSet env = rme_envelope(&q);
        bool retained = rme_portset_has(&env, RME_PORT_coupling)
                     && rme_port_api(&q, RME_PORT_coupling) != nullptr;

        rme_check(!adm.ok && retained,
                  "C18d", "a vestigial endpoint is retained yet not admissible: "
                          "retention is not wiring");
    }

    /* ---- Admissible =/=> Declared, stated directly.  A relation can be
     * admissible indefinitely without ever being declared, and evaluating
     * admissibility declares nothing. */
    {
        RmePrototype p = active("P");
        RmePrototype q = active("Q");
        const RmeConnection e[] = { { RME_PORT_observation, RME_PORT_state } };
        RmeRelation R = { e, 1, false };

        RmeComposition a1 = rme_admissible(&p, &q, &R);
        RmeComposition a2 = rme_admissible(&p, &q, &R);   /* idempotent */
        RmeComposition c  = rme_compose_valid(&p, &q, &R);

        rme_check(a1.ok && a2.ok && !c.ok && R.declared == false,
                  "C18e", "evaluating admissibility neither declares the relation nor mutates it");
    }
}
