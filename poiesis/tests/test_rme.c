/* poiesis conformance suite.
 *
 * Test ids match the specification's verification tables.  Each test names
 * the invariant it pins, so a failure says which frozen distinction broke.
 */
#include <stdio.h>
#include <string.h>

#include "rme/conform.h"

void rme_test_axis_b(void);
void rme_test_bind(void);
void rme_test_classify(void);
void rme_test_authority(void);
void rme_test_schedule(void);

int rme_test_passed;
int rme_test_failed;

void rme_check(bool cond, const char *id, const char *what)
{
    if (cond) {
        rme_test_passed++;
        printf("ok   - %-4s %s\n", id, what);
    } else {
        rme_test_failed++;
        printf("FAIL - %-4s %s\n", id, what);
    }
}

/* ---- substantive (ACTIVE) realizations, distinct from the vestigial ones */
static RmeOutcome a_state_read(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome a_obs(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome a_step(void *self, const void *args) { (void)self; (void)args; return RME_OK; }
static RmeOutcome a_get(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome a_couple(void *self, void *peer) { (void)self; (void)peer; return RME_OK; }
static RmeOutcome a_adapt(void *self) { (void)self; return RME_OK; }
static RmeOutcome a_govern(void *self) { (void)self; return RME_OK; }
static RmeOutcome a_resolve(const void *self, size_t i, const void **out)
{ (void)self; (void)i; if (out) *out = nullptr; return RME_OK; }

static const RmeStateApi            act_state  = { a_state_read, "active" };
static const RmeObservationApi      act_obs    = { a_obs,        "active" };
static const RmeTransitionApi       act_trans  = { a_step,       "active" };
static const RmeParameterizationApi act_param  = { a_get,        "active" };
static const RmeCouplingApi         act_coup   = { a_couple,     "active" };
static const RmeAdaptationApi       act_adapt  = { a_adapt,      "active" };
static const RmeGovernanceApi       act_gov    = { a_govern,     "active" };
static const RmeNestedApi           act_nested = { a_resolve,    "active" };

/* A fully ACTIVE, conformant prototype. */
static RmePrototype make_active(const char *name)
{
    RmePrototype p = {
        .identity = { name },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_ACTIVE, RME_PORT_state },            &act_state  },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &act_obs    },
        .transition       = { { RME_ACTIVE, RME_PORT_transition },       &act_trans  },
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &act_param  },
        .coupling         = { { RME_ACTIVE, RME_PORT_coupling },         &act_coup   },
        .adaptation       = { { RME_ACTIVE, RME_PORT_adaptation },       &act_adapt  },
        .governance       = { { RME_ACTIVE, RME_PORT_governance },       &act_gov    },
        .nested           = { { RME_ACTIVE, RME_PORT_nested },           &act_nested },
    };
    return p;
}

/* Every port VESTIGIAL, pointing at each port's DECLARED vestigial object. */
static RmePrototype make_all_vestigial(const char *name)
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

int main(void)
{
    /* ---- C1: conformance is unary (F4). Evaluated with no other
     * prototype in scope; the signature admits only one. */
    {
        RmePrototype p = make_active("P");
        RmeConformance r = rme7_conforms(&p);
        rme_check(r.ok, "C1", "conformance is unary and succeeds with no other prototype in scope");
    }

    /* ---- C5(partial)/N1: every operator-associated port VESTIGIAL is
     * still conformant. Fullness of realization is never required. */
    {
        RmePrototype p = make_all_vestigial("V");
        RmeConformance r = rme7_conforms(&p);
        rme_check(r.ok, "N1", "all-vestigial prototype is conformant (fullness never required)");
    }

    /* ---- C11: a port omitted from the initializer is rejected as the
     * UNDEFINED sentinel; it never reaches the public API. */
    {
        RmePrototype p = make_active("P");
        p.coupling.hdr.status = RME_UNDEFINED;   /* as a zero-fill would leave it */
        RmeConformance r = rme7_conforms(&p);
        rme_check(!r.ok && r.port == RME_PORT_coupling,
              "C11", "omitted port rejected as UNDEFINED, reported by name");
    }

    /* ---- C12: no schema identity -> rejected. */
    {
        RmePrototype p = make_active("P");
        p.schema.name = nullptr;
        RmeConformance r = rme7_conforms(&p);
        rme_check(!r.ok, "C12", "prototype without schema identity is rejected");
    }

    /* ---- C9: a hand-rolled `return 0;` stub is NOT the port's declared
     * vestigial realization, and its VestigialContract rejects it. */
    {
        static const RmeCouplingApi bogus_noop = { a_couple, "return-0 stub" };
        RmePrototype p = make_all_vestigial("V");
        p.coupling.api = &bogus_noop;            /* status still VESTIGIAL */
        RmeConformance r = rme7_conforms(&p);
        rme_check(!r.ok && r.port == RME_PORT_coupling,
              "C9", "blanket no-op rejected by the port's own vestigial contract");
    }

    /* ---- C10: a vestigial port invoked through its API is type-valid and
     * contract-conformant — never a null dereference, and NOT a uniform
     * `return 0`. Coupling must REFUSE; governance must REFUSE. */
    {
        RmePrototype p = make_all_vestigial("V");
        RmeOutcome c = p.coupling.api->couple(&p, &p);
        RmeOutcome g = p.governance.api->govern(&p);
        RmeOutcome o = p.observation.api->observe(&p, nullptr);
        rme_check(c == RME_REFUSED && g == RME_REFUSED && o == RME_NOT_REALIZED,
              "C10", "vestigial realizations differ by port: coupling/governance refuse, observation inert");
    }

    /* ---- ACTIVE must not point at the declared vestigial object. */
    {
        RmePrototype p = make_active("P");
        p.adaptation.api = &rme_vestigial_adaptation;   /* status still ACTIVE */
        RmeConformance r = rme7_conforms(&p);
        rme_check(!r.ok && r.port == RME_PORT_adaptation,
              "A1", "ACTIVE port pointing at the vestigial realization is rejected");
    }

    /* ---- Type discipline: a null api is a type failure, not a spelling
     * of "vestigial". */
    {
        RmePrototype p = make_all_vestigial("V");
        p.state.api = nullptr;
        RmeConformance r = rme7_conforms(&p);
        rme_check(!r.ok && r.port == RME_PORT_state,
              "A2", "null realization rejected (null is not a way to spell VESTIGIAL)");
    }

    /* ---- Elision is an optimization permission, never implied by status.
     * VESTIGIAL(p) => Elidable(p) is prohibited. */
    {
        RmePrototype p = make_all_vestigial("V");
        bool coupling_elidable   = rme_port_elidable(&p, RME_PORT_coupling);
        bool governance_elidable = rme_port_elidable(&p, RME_PORT_governance);
        bool observation_elidable = rme_port_elidable(&p, RME_PORT_observation);
        rme_check(!coupling_elidable && !governance_elidable && observation_elidable,
              "A3", "VESTIGIAL does not imply elidable; permission is per-port contract");
    }

    /* ---- ACTIVE is never elidable regardless of contract. */
    {
        RmePrototype p = make_active("P");
        bool any = false;
        for (int i = 0; i < RME_PORT_COUNT; i++) {
            any = any || rme_port_elidable(&p, (RmePortId)i);
        }
        rme_check(!any, "A4", "no ACTIVE port is elidable");
    }

    /* ---- Compatibility is a property of an endpoint PAIR. Its truth does
     * not compose prototypes, and its falsity does not unmake conformance
     * (N2/N3 — the composition half is exercised in the Axis B suite). */
    {
        RmePrototype p = make_active("P");
        RmePrototype q = make_active("Q");
        const char *why = nullptr;
        bool compat = rme_compatible(&p, RME_PORT_transition, &q, RME_PORT_coupling, &why);
        bool incompat = rme_compatible(&p, RME_PORT_state, &q, RME_PORT_governance, &why);
        RmeConformance rp = rme7_conforms(&p);
        RmeConformance rq = rme7_conforms(&q);
        rme_check(compat && !incompat && rp.ok && rq.ok,
              "C3", "an incompatible endpoint pair leaves both prototypes conformant (N2)");
    }

    /* ---- Provisional contracts must be mechanically visible. */
    {
        rme_check(rme_contract_provisional_count() == RME_PORT_COUNT,
              "P1", "all per-port contracts report PROVISIONAL (OPEN spec item)");
    }

    rme_test_axis_b();
    rme_test_bind();
    rme_test_classify();
    rme_test_authority();
    rme_test_schedule();

    printf("\n%d passed, %d failed\n", rme_test_passed, rme_test_failed);
    if (rme_test_failed == 0) {
        printf("\n");
        rme_contract_report();
    }
    return rme_test_failed == 0 ? 0 : 1;
}
