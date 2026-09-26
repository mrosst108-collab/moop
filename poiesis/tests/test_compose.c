/* poiesis — AXIS B suite: composition and nesting.
 *
 * Mandatory convention: every composition test states its relation R
 * explicitly.  N3/F5 turn on compatibility belonging to the relation
 * rather than to the mere coexistence of ports, so a test that leaves R
 * implicit would silently retest the old "corresponding ports" reading.
 */
#include <stdio.h>

#include "rme/compose.h"
#include "rme/nest.h"

extern int  rme_test_passed;
extern int  rme_test_failed;
extern void rme_check(bool cond, const char *id, const char *what);

/* A spy: counts invocations so we can prove ComposeValid executes nothing. */
static int spy_calls;
static RmeOutcome spy_step(void *self, const void *args)
{ (void)self; (void)args; spy_calls++; return RME_OK; }
static RmeOutcome spy_couple(void *self, void *peer)
{ (void)self; (void)peer; spy_calls++; return RME_OK; }

static RmeOutcome q_state(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome q_obs(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome q_get(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome q_adapt(void *self) { (void)self; return RME_OK; }
static RmeOutcome q_govern(void *self) { (void)self; return RME_OK; }

static const RmeStateApi            s_state = { q_state, "active" };
static const RmeObservationApi      s_obs   = { q_obs,   "active" };
static const RmeTransitionApi       s_trans = { spy_step, "active-spy" };
static const RmeParameterizationApi s_param = { q_get,   "active" };
static const RmeCouplingApi         s_coup  = { spy_couple, "active-spy" };
static const RmeAdaptationApi       s_adapt = { q_adapt, "active" };
static const RmeGovernanceApi       s_gov   = { q_govern, "active" };

/* Nested realization backed by a HANDLE TABLE, not an owned array — the
 * point of C13: representation does not determine the relation. */
static const RmePrototype *handle_table[4];
static size_t              handle_count;

static RmeOutcome handle_resolve(const void *self, size_t i, const void **out)
{
    (void)self;
    if (i >= handle_count) {
        return RME_NOT_REALIZED;
    }
    if (out) *out = handle_table[i];
    return RME_OK;
}
static const RmeNestedApi s_nested_handles = { handle_resolve, "active:handle-table" };

/* Build a prototype whose ports take the given statuses.  Vestigial ports
 * point at their declared vestigial realizations. */
static RmePrototype mk(const char *name, RmePortStatus trans, RmePortStatus coup,
                       const RmeNestedApi *nested_api, RmePortStatus nested_status)
{
    RmePrototype p = {
        .identity = { name },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_ACTIVE, RME_PORT_state },            &s_state },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &s_obs   },
        .transition       = { { trans, RME_PORT_transition },
                              trans == RME_ACTIVE ? &s_trans : &rme_vestigial_transition },
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &s_param },
        .coupling         = { { coup, RME_PORT_coupling },
                              coup == RME_ACTIVE ? &s_coup : &rme_vestigial_coupling },
        .adaptation       = { { RME_ACTIVE, RME_PORT_adaptation },       &s_adapt },
        .governance       = { { RME_ACTIVE, RME_PORT_governance },       &s_gov   },
        .nested           = { { nested_status, RME_PORT_nested },
                              nested_status == RME_ACTIVE ? nested_api : &rme_vestigial_nested },
    };
    return p;
}

void rme_test_axis_b(void);

void rme_test_axis_b(void)
{
    /* ---- C2: compatible active ports, R = {} .  Compatibility is true
     * for the pair, but it creates NO composition and NO obligation. */
    {
        RmePrototype p = mk("P", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        RmePrototype q = mk("Q", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        const char *why = nullptr;
        bool pair_compatible =
            rme_compatible(&p, RME_PORT_transition, &q, RME_PORT_coupling, &why);

        RmeRelation R = { nullptr, 0, true };            /* R = {} */
        RmeComposition c = rme_compose_valid(&p, &q, &R);

        rme_check(pair_compatible && c.ok && c.obligations == 0,
                  "C2", "R={}: compatible pair exists yet incurs zero obligations (N3)");
    }

    /* ---- C4: R = {(P.state, Q.governance)} — a declared but incompatible
     * endpoint pair. */
    {
        RmePrototype p = mk("P", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        RmePrototype q = mk("Q", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        const RmeConnection e[] = { { RME_PORT_state, RME_PORT_governance } };
        RmeRelation R = { e, 1, true };
        RmeComposition c = rme_compose_valid(&p, &q, &R);
        rme_check(!c.ok && c.edge == 0,
                  "C4", "R={(state,governance)}: incompatible declared pair rejected");
    }

    /* ---- C5: R = {(P.transition, Q.coupling)} with Q.coupling VESTIGIAL.
     * A vestigial port may sit in the envelope but cannot be wired. */
    {
        RmePrototype p = mk("P", RME_ACTIVE, RME_ACTIVE,   nullptr, RME_VESTIGIAL);
        RmePrototype q = mk("Q", RME_ACTIVE, RME_VESTIGIAL, nullptr, RME_VESTIGIAL);
        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, true };
        RmeComposition c = rme_compose_valid(&p, &q, &R);
        rme_check(!c.ok, "C5", "R={(transition,coupling)}: VESTIGIAL endpoint cannot participate");
    }

    /* ---- C6: ports OUTSIDE R are mutually incompatible; irrelevant.
     * R = {(P.transition, Q.coupling)} only. */
    {
        RmePrototype p = mk("P", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        RmePrototype q = mk("Q", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        const char *why = nullptr;
        bool outside_incompatible =
            !rme_compatible(&p, RME_PORT_state, &q, RME_PORT_governance, &why);

        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, true };
        RmeComposition c = rme_compose_valid(&p, &q, &R);

        rme_check(outside_incompatible && c.ok && c.obligations == 1,
                  "C6", "R={(transition,coupling)}: an incompatible pair outside R is irrelevant (F5)");
    }

    /* ---- C7: R is a relation, not an event.  Validation must invoke no
     * realization at all. */
    {
        RmePrototype p = mk("P", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        RmePrototype q = mk("Q", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, true };
        spy_calls = 0;
        RmeComposition c = rme_compose_valid(&p, &q, &R);
        rme_check(c.ok && spy_calls == 0,
                  "C7", "R={(transition,coupling)}: validated with zero realization calls");
    }

    /* ---- An UNDECLARED relation is not a composition, however compatible
     * its endpoints are. */
    {
        RmePrototype p = mk("P", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        RmePrototype q = mk("Q", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, false };                 /* Declared(R) = false */
        RmeComposition c = rme_compose_valid(&p, &q, &R);
        rme_check(!c.ok, "B1", "undeclared relation is not a composition");
    }

    /* ---- C8: complementary vestigiality.  P1 has transition ACTIVE /
     * coupling VESTIGIAL; P2 has transition VESTIGIAL / coupling ACTIVE.
     * R = {(P1.transition, P2.coupling)} — the vestigial ports are present
     * in both envelopes but deliberately absent from R. */
    {
        RmePrototype p1 = mk("P1", RME_ACTIVE,    RME_VESTIGIAL, nullptr, RME_VESTIGIAL);
        RmePrototype p2 = mk("P2", RME_VESTIGIAL, RME_ACTIVE,    nullptr, RME_VESTIGIAL);
        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, true };
        RmeComposition c = rme_compose_valid(&p1, &p2, &R);

        RmeConformance c1 = rme7_conforms(&p1);
        RmeConformance c2 = rme7_conforms(&p2);

        rme_check(c.ok && c1.ok && c2.ok,
                  "C8", "R={(P1.transition,P2.coupling)}: composes; vestigial ports outside R (local)");
    }

    /* ---- C13: nesting realized by a HANDLE TABLE rather than an owned
     * contiguous array.  Representation does not determine the relation. */
    {
        static RmePrototype child;
        child = mk("K", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        handle_table[0] = &child;
        handle_count = 1;

        RmePrototype parent = mk("P", RME_ACTIVE, RME_ACTIVE, &s_nested_handles, RME_ACTIVE);
        RmeNesting n = rme_nested_valid(&parent, &child);
        rme_check(n.ok, "C13", "nesting via handle table is valid (representation-independent)");
    }

    /* ---- C14: the child activates a STRICT SUBSET of the parent's ports.
     * Valid; semantics are not inherited. */
    {
        static RmePrototype child;
        child = mk("K", RME_VESTIGIAL, RME_VESTIGIAL, nullptr, RME_VESTIGIAL);
        handle_table[0] = &child;
        handle_count = 1;

        RmePrototype parent = mk("P", RME_ACTIVE, RME_ACTIVE, &s_nested_handles, RME_ACTIVE);
        RmeNesting n = rme_nested_valid(&parent, &child);

        bool child_is_sparser =
            child.transition.hdr.status == RME_VESTIGIAL &&
            parent.transition.hdr.status == RME_ACTIVE;

        rme_check(n.ok && child_is_sparser,
                  "C14", "child activating a strict subset is valid; semantics not inherited");
    }

    /* ---- A parent that does not declare the relation does not contain
     * the child, whatever storage happens to hold. */
    {
        static RmePrototype child;
        child = mk("K", RME_ACTIVE, RME_ACTIVE, nullptr, RME_VESTIGIAL);
        handle_table[0] = &child;
        handle_count = 1;

        RmePrototype parent = mk("P", RME_ACTIVE, RME_ACTIVE, &s_nested_handles, RME_VESTIGIAL);
        RmeNesting n = rme_nested_valid(&parent, &child);
        rme_check(!n.ok, "B2", "undeclared containment is not nesting");
    }
}
