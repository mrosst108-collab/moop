#include <assert.h>
#include <stdio.h>

#include "contract.h"

/* ---------------------------------------------------------------------
 * Declared vestigial realizations.
 *
 * These are deliberately NOT the same shape as one another.  A blanket
 * `return 0;` would be semantically wrong for at least two of these ports:
 * a vestigial COUPLING must refuse a peer rather than silently accept one,
 * and a vestigial GOVERNANCE must refuse rather than silently permit.
 * Returning "success" from either would be a substantive behaviour change
 * disguised as a null realization.
 * --------------------------------------------------------------------- */

/* state: a DEFAULT-VALUED state.  Answers, and answers definedly. */
static RmeOutcome v_state_read(void *self, void *out)
{
    (void)self; (void)out;
    return RME_OK;
}

/* observation: nothing is observed — a defined "not realized". */
static RmeOutcome v_observation_observe(void *self, void *out)
{
    (void)self; (void)out;
    return RME_NOT_REALIZED;
}

/* transition: identity on state. */
static RmeOutcome v_transition_step(void *self, const void *args)
{
    (void)self; (void)args;
    return RME_NOT_REALIZED;
}

static RmeOutcome v_parameterization_get(void *self, void *out)
{
    (void)self; (void)out;
    return RME_NOT_REALIZED;
}

/* coupling: REFUSES.  Not a no-op — silently accepting a peer would be a
 * substantive coupling behaviour. */
static RmeOutcome v_coupling_couple(void *self, void *peer)
{
    (void)self; (void)peer;
    return RME_REFUSED;
}

static RmeOutcome v_adaptation_adapt(void *self)
{
    (void)self;
    return RME_NOT_REALIZED;
}

/* governance: REFUSES.  A vestigial governance port must never read as
 * permission granted. */
static RmeOutcome v_governance_govern(void *self)
{
    (void)self;
    return RME_REFUSED;
}

/* nested: resolves no children, and says so. */
static RmeOutcome v_nested_resolve(const void *self, size_t i, const void **out)
{
    (void)self; (void)i;
    if (out != nullptr) {
        *out = nullptr;
    }
    return RME_NOT_REALIZED;
}

const RmeStateApi            rme_vestigial_state            = { v_state_read,            "vestigial:default-valued" };
const RmeObservationApi      rme_vestigial_observation      = { v_observation_observe,   "vestigial:inert" };
const RmeTransitionApi       rme_vestigial_transition       = { v_transition_step,       "vestigial:identity" };
const RmeParameterizationApi rme_vestigial_parameterization = { v_parameterization_get,  "vestigial:empty" };
const RmeCouplingApi         rme_vestigial_coupling         = { v_coupling_couple,       "vestigial:refusing" };
const RmeAdaptationApi       rme_vestigial_adaptation       = { v_adaptation_adapt,      "vestigial:inert" };
const RmeGovernanceApi       rme_vestigial_governance       = { v_governance_govern,     "vestigial:refusing" };
const RmeNestedApi           rme_vestigial_nested           = { v_nested_resolve,        "vestigial:childless" };

/* ---------------------------------------------------------------------
 * Contract table.  Every entry is PROVISIONAL — the per-port contracts are
 * an OPEN specification item and must not harden by being implemented.
 * --------------------------------------------------------------------- */
static const RmePortContract rme_contracts[RME_PORT_COUNT] = {
    [RME_PORT_state] = {
        RME_PORT_state, true, &rme_vestigial_state, false,
        "default-valued; not elidable — the default must still be produced"
    },
    [RME_PORT_observation] = {
        RME_PORT_observation, true, &rme_vestigial_observation, true,
        "inert endpoint; elidable — nothing observes"
    },
    [RME_PORT_transition] = {
        RME_PORT_transition, true, &rme_vestigial_transition, true,
        "identity on state; elidable"
    },
    [RME_PORT_parameterization] = {
        RME_PORT_parameterization, true, &rme_vestigial_parameterization, true,
        "empty capability; elidable"
    },
    [RME_PORT_coupling] = {
        RME_PORT_coupling, true, &rme_vestigial_coupling, false,
        "REFUSES a peer; not elidable — the refusal must remain observable"
    },
    [RME_PORT_adaptation] = {
        RME_PORT_adaptation, true, &rme_vestigial_adaptation, true,
        "inert; elidable"
    },
    [RME_PORT_governance] = {
        RME_PORT_governance, true, &rme_vestigial_governance, false,
        "REFUSES; not elidable — must never read as permission granted"
    },
    [RME_PORT_nested] = {
        RME_PORT_nested, true, &rme_vestigial_nested, false,
        "childless; not elidable"
    },
};

const RmePortContract *rme_contract(RmePortId id)
{
    assert(id >= 0 && id < RME_PORT_COUNT);
    return &rme_contracts[id];
}

bool rme_realization_valid(const RmePrototype *p, RmePortId id, const char **why)
{
    const RmePortHeader *h = rme_port_at_const(p, id);
    const void *api = rme_port_api(p, id);
    const RmePortContract *c = rme_contract(id);

    /* Either status requires a valid object of the declared interface
     * type.  A null api is a type-discipline failure, never a way to
     * spell "vestigial". */
    if (api == nullptr) {
        if (why) *why = "port api is null; a realization object is required for either status";
        return false;
    }

    switch (h->status) {
    case RME_ACTIVE:
        /* ActiveContract: must be a substantive realization, i.e. NOT the
         * declared vestigial object. */
        if (api == c->vestigial_realization) {
            if (why) *why = "ACTIVE port points at the declared vestigial realization";
            return false;
        }
        return true;

    case RME_VESTIGIAL:
        /* VestigialContract: must be exactly the port's DECLARED vestigial
         * realization.  A hand-rolled stub — including a blanket
         * `return 0;` — is not that object and is rejected here. */
        if (api != c->vestigial_realization) {
            if (why) *why = "VESTIGIAL port does not point at this port's declared vestigial realization";
            return false;
        }
        return true;

    case RME_UNDEFINED:
    default:
        if (why) *why = "port status is UNDEFINED; it must never survive validation";
        return false;
    }
}

bool rme_port_elidable(const RmePrototype *p, RmePortId id)
{
    const RmePortHeader *h = rme_port_at_const(p, id);
    /* VESTIGIAL alone is never sufficient. */
    return h->status == RME_VESTIGIAL && rme_contract(id)->vestigial_allows_elision;
}

/* ---------------------------------------------------------------------
 * Declared compatibility relation over endpoint PAIRS.  PROVISIONAL.
 *
 * Compatibility is a property of the pair.  It does not imply that the two
 * prototypes compose (that needs a declared connection relation R), and
 * its negation does not make either prototype non-conformant.
 * --------------------------------------------------------------------- */
typedef struct { RmePortId a, b; } RmePortPair;

static const RmePortPair rme_declared_compatible[] = {
    /* like-to-like */
    { RME_PORT_state,            RME_PORT_state },
    { RME_PORT_observation,      RME_PORT_observation },
    { RME_PORT_transition,       RME_PORT_transition },
    { RME_PORT_parameterization, RME_PORT_parameterization },
    { RME_PORT_coupling,         RME_PORT_coupling },
    { RME_PORT_adaptation,       RME_PORT_adaptation },
    { RME_PORT_governance,       RME_PORT_governance },
    { RME_PORT_nested,           RME_PORT_nested },
    /* declared cross-pairs */
    { RME_PORT_transition,       RME_PORT_coupling },
    { RME_PORT_observation,      RME_PORT_state },
};

bool rme_compatible(const RmePrototype *P, RmePortId pi,
                    const RmePrototype *Q, RmePortId qi,
                    const char **why)
{
    (void)P; (void)Q;
    const size_t n = sizeof rme_declared_compatible / sizeof rme_declared_compatible[0];
    for (size_t i = 0; i < n; i++) {
        RmePortPair pr = rme_declared_compatible[i];
        if ((pr.a == pi && pr.b == qi) || (pr.a == qi && pr.b == pi)) {
            return true;
        }
    }
    if (why) *why = "endpoint pair is not in the declared compatibility relation";
    return false;
}

size_t rme_contract_provisional_count(void)
{
    size_t n = 0;
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        if (rme_contracts[i].provisional) {
            n++;
        }
    }
    return n;
}

void rme_contract_report(void)
{
    printf("port contracts: %zu of %d PROVISIONAL (OPEN specification item)\n",
           rme_contract_provisional_count(), RME_PORT_COUNT);
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        const RmePortContract *c = &rme_contracts[i];
        printf("  %-18s %-12s elide=%-5s %s\n",
               rme_port_name(c->id),
               c->provisional ? "PROVISIONAL" : "settled",
               c->vestigial_allows_elision ? "yes" : "no",
               c->note);
    }
}
