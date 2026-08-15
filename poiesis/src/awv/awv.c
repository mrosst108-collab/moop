#include "awv.h"

/* ---- slots -------------------------------------------------------------
 *
 * Exactly one bit is doing the constitutional work: AWV_BEHAVIOUR is NOT
 * governed.  Flip it and the same read-sets classify RME-7. */
static const RmeSlot awv_slots[AWV_SLOT_COUNT] = {
    [AWV_SIGMA_U]   = { "Sigma_U",   true  },
    [AWV_A]         = { "A",         true  },
    [AWV_THETA]     = { "theta",     true  },
    [AWV_BEHAVIOUR] = { "behaviour", false },          /* environmental */
};

/* ---- operative read-sets ----------------------------------------------- */

/* The epoch solve reads the graph and the governance parameters.  It does
 * NOT read A: Fork N closed to uniform fallback (v0.14), so no
 * previous-epoch authority enters the solve. */
static const size_t r_A[]         = { AWV_SIGMA_U, AWV_THETA };

/* Users see ranked output and act.  This is where authority leaves the
 * governed region. */
static const size_t r_behaviour[] = { AWV_A };

/* Subscriptions and endorsements are created by behaviour.  delta applies
 * here as a DERIVED OPERATOR (v0.18); it is not a state object and so
 * contributes no slot and no edge of its own. */
static const size_t r_sigma[]     = { AWV_BEHAVIOUR };

static const RmeTransitionDecl awv_operative_tr[] = {
    { "T_A",         AWV_A,         r_A,         2 },
    { "T_behaviour", AWV_BEHAVIOUR, r_behaviour, 1 },
    { "T_Sigma_U",   AWV_SIGMA_U,   r_sigma,     1 },
    /* T_theta declares no read of A: the A-weighted rows are contingent on
     * Fork G, not operative (v0.12). */
    { "T_theta",     AWV_THETA,     nullptr,     0 },
};

static const RmeSystem awv_operative = {
    awv_slots, AWV_SLOT_COUNT, awv_operative_tr, 4, false
};

const RmeSystem *awv_system_operative(void)
{
    return &awv_operative;
}

/* ---- Route 7C ----------------------------------------------------------
 *
 * The median-band fallback centres on the previous epoch's median of A, so
 * the transition on A reads A.  One extra entry in one read-set. */
static const size_t r_A_7c[] = { AWV_SIGMA_U, AWV_THETA, AWV_A };

static const RmeTransitionDecl awv_7c_tr[] = {
    { "T_A",         AWV_A,         r_A_7c,      3 },
    { "T_behaviour", AWV_BEHAVIOUR, r_behaviour, 1 },
    { "T_Sigma_U",   AWV_SIGMA_U,   r_sigma,     1 },
    { "T_theta",     AWV_THETA,     nullptr,     0 },
};

static const RmeSystem awv_7c = {
    awv_slots, AWV_SLOT_COUNT, awv_7c_tr, 4, false
};

const RmeSystem *awv_system_route_7c(void)
{
    return &awv_7c;
}

/* ---- Fork G ------------------------------------------------------------
 *
 * theta reads A, while A already reads theta: A -> theta -> A, entirely
 * among governed slots. */
static const size_t r_theta_g[] = { AWV_A };

static const RmeTransitionDecl awv_fork_g_tr[] = {
    { "T_A",         AWV_A,         r_A,         2 },
    { "T_behaviour", AWV_BEHAVIOUR, r_behaviour, 1 },
    { "T_Sigma_U",   AWV_SIGMA_U,   r_sigma,     1 },
    { "T_theta",     AWV_THETA,     r_theta_g,   1 },
};

static const RmeSystem awv_fork_g = {
    awv_slots, AWV_SLOT_COUNT, awv_fork_g_tr, 4, false
};

const RmeSystem *awv_system_fork_g(void)
{
    return &awv_fork_g;
}

/* ---- prototypes --------------------------------------------------------
 *
 * Substantive realizations are stubs at this layer: Gate 4 is about the
 * DECLARED structure -- which ports AWV activates and which it keeps
 * present but non-substantive -- not about running AWV. */
static RmeOutcome a_state(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome a_obs(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome a_step(void *self, const void *args) { (void)self; (void)args; return RME_OK; }
static RmeOutcome a_get(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome a_couple(void *self, void *peer) { (void)self; (void)peer; return RME_OK; }
static RmeOutcome a_govern(void *self) { (void)self; return RME_OK; }
static RmeOutcome a_resolve(const void *self, size_t i, const void **out)
{ (void)self; (void)i; if (out) *out = nullptr; return RME_OK; }

static const RmeStateApi            act_state  = { a_state,   "awv:state" };
static const RmeObservationApi      act_obs    = { a_obs,     "awv:observation" };
static const RmeTransitionApi       act_trans  = { a_step,    "awv:transition" };
static const RmeParameterizationApi act_param  = { a_get,     "awv:parameterization" };
static const RmeCouplingApi         act_coup   = { a_couple,  "awv:coupling" };
static const RmeGovernanceApi       act_gov    = { a_govern,  "awv:governance" };
static const RmeNestedApi           act_nested = { a_resolve, "awv:nested" };

RmePrototype awv_authority_prototype(void)
{
    RmePrototype p = {
        .identity = { "awv.authority" },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        /* A is state; the epoch solve is its transition; alpha, beta,
         * lambda_V and mu are its declared parameters (v0.6, v0.10). */
        .state            = { { RME_ACTIVE, RME_PORT_state },            &act_state },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &act_obs   },
        .transition       = { { RME_ACTIVE, RME_PORT_transition },       &act_trans },
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &act_param },
        /* v0.4: "One PageRank on Sigma_U" -- authority couples to no peer
         * authority computation. */
        .coupling         = { { RME_VESTIGIAL, RME_PORT_coupling },      &rme_vestigial_coupling   },
        /* v0.15: behaviour at t alters authority first solved at t+1.  No
         * within-epoch adaptation. */
        .adaptation       = { { RME_VESTIGIAL, RME_PORT_adaptation },    &rme_vestigial_adaptation },
        /* Fork G is not operative: authority does not govern itself. */
        .governance       = { { RME_VESTIGIAL, RME_PORT_governance },    &rme_vestigial_governance },
        .nested           = { { RME_VESTIGIAL, RME_PORT_nested },        &rme_vestigial_nested     },
    };
    return p;
}

RmePrototype awv_presentation_prototype(void)
{
    RmePrototype p = {
        .identity = { "awv.presentation" },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_ACTIVE, RME_PORT_state },            &act_state },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &act_obs   },
        .transition       = { { RME_ACTIVE, RME_PORT_transition },       &act_trans },
        /* v0.5: three modes, viewer-selected windows, plurality free. */
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &act_param },
        /* v0.12: extra eigenproblems are free ONLY while output remains
         * presentation state.  Presentation couples to nothing
         * constitutional, and that is what keeps the freedom bounded. */
        .coupling         = { { RME_VESTIGIAL, RME_PORT_coupling },      &rme_vestigial_coupling   },
        .adaptation       = { { RME_VESTIGIAL, RME_PORT_adaptation },    &rme_vestigial_adaptation },
        .governance       = { { RME_VESTIGIAL, RME_PORT_governance },    &rme_vestigial_governance },
        .nested           = { { RME_VESTIGIAL, RME_PORT_nested },        &rme_vestigial_nested     },
    };
    return p;
}

/* The two community forms share one schema and differ ONLY in the status of
 * coupling (admission) and governance (moderation). */
RmePrototype awv_community_prototype_open(void)
{
    RmePrototype p = {
        .identity = { "awv.community.open" },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_ACTIVE, RME_PORT_state },            &act_state  },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &act_obs    },
        .transition       = { { RME_ACTIVE, RME_PORT_transition },       &act_trans  },
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &act_param  },
        /* v0.9: no admission authority and no moderator exist by default.
         * PRESENT AND TYPED, NOT ABSENT -- which is what makes opting in a
         * status change rather than a boundary redesign. */
        .coupling         = { { RME_VESTIGIAL, RME_PORT_coupling },      &rme_vestigial_coupling   },
        .governance       = { { RME_VESTIGIAL, RME_PORT_governance },    &rme_vestigial_governance },
        .adaptation       = { { RME_VESTIGIAL, RME_PORT_adaptation },    &rme_vestigial_adaptation },
        /* v0.4: communities demoted to routing -- they contain content. */
        .nested           = { { RME_ACTIVE, RME_PORT_nested },           &act_nested },
    };
    return p;
}

RmePrototype awv_community_prototype_curated(void)
{
    RmePrototype p = awv_community_prototype_open();
    p.identity.name = "awv.community.curated";
    /* The community opted in.  Same schema, same ports, two statuses
     * changed and substantive realizations supplied. */
    p.coupling   = (RmeCouplingPort){   { RME_ACTIVE, RME_PORT_coupling },   &act_coup };
    p.governance = (RmeGovernancePort){ { RME_ACTIVE, RME_PORT_governance }, &act_gov  };
    return p;
}

/* ---- AWV's constitution ------------------------------------------------ */

static bool named(const RmePrototype *p, const char *name)
{
    if (p == nullptr || p->identity.name == nullptr) {
        return false;
    }
    for (size_t i = 0; ; i++) {
        if (p->identity.name[i] != name[i]) {
            return false;
        }
        if (name[i] == '\0') {
            return true;
        }
    }
}

bool awv_constitutionally_permitted(const RmePrototype *from, RmePortId fp,
                                    const RmePrototype *to,   RmePortId tp)
{
    (void)fp;
    /* The three-layer separation: presentation output may not become
     * constitutional input.  Reading authority state is what the feed IS;
     * writing into it is the violation. */
    if (named(from, "awv.presentation") && named(to, "awv.authority")
        && tp == RME_PORT_state) {
        return false;
    }
    return true;
}
