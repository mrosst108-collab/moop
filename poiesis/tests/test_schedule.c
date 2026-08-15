/* poiesis — GATE 2 suite: flattening, elision, and fixed-point groups.
 *
 * The invariant under test:
 *
 *     E_dispatch subset-of E_envelope      and never   VESTIGIAL => EnvelopeAbsent
 *
 * Every test states which ports it expects in which set.  A test that only
 * compared COUNTS would pass while dispatch contained a port the envelope
 * did not, so containment is checked as a set relation.
 */
#include <stddef.h>

#include "rme/schedule.h"

extern void rme_check(bool cond, const char *id, const char *what);

static RmeOutcome s_state(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome s_obs(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome s_step(void *self, const void *args) { (void)self; (void)args; return RME_OK; }
static RmeOutcome s_get(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome s_couple(void *self, void *peer) { (void)self; (void)peer; return RME_OK; }
static RmeOutcome s_adapt(void *self) { (void)self; return RME_OK; }
static RmeOutcome s_govern(void *self) { (void)self; return RME_OK; }
static RmeOutcome s_resolve(const void *self, size_t i, const void **out)
{ (void)self; (void)i; if (out) *out = nullptr; return RME_OK; }

static const RmeStateApi            act_state  = { s_state,   "active" };
static const RmeObservationApi      act_obs    = { s_obs,     "active" };
static const RmeTransitionApi       act_trans  = { s_step,    "active" };
static const RmeParameterizationApi act_param  = { s_get,     "active" };
static const RmeCouplingApi         act_coup   = { s_couple,  "active" };
static const RmeAdaptationApi       act_adapt  = { s_adapt,   "active" };
static const RmeGovernanceApi       act_gov    = { s_govern,  "active" };
static const RmeNestedApi           act_nested = { s_resolve, "active" };

static RmePrototype all_active(void)
{
    RmePrototype p = {
        .identity = { "A" },
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

static RmePrototype all_vestigial(void)
{
    RmePrototype p = {
        .identity = { "V" },
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

void rme_test_schedule(void);

void rme_test_schedule(void)
{
    /* ---- S1: the envelope is the whole schema regardless of status.  With
     * every port VESTIGIAL, all eight are still present.  This is the
     * refutation of VESTIGIAL => EnvelopeAbsent. */
    {
        RmePrototype v = all_vestigial();
        RmePortSet env = rme_envelope(&v);
        bool all_present = env.count == (size_t)RME_PORT_COUNT;
        for (int i = 0; i < RME_PORT_COUNT; i++) {
            all_present = all_present && rme_portset_has(&env, (RmePortId)i);
        }
        rme_check(all_present,
                  "S1", "all-vestigial prototype: every port still in the envelope");
    }

    /* ---- S2: the envelope is IDENTICAL for an all-active and an
     * all-vestigial prototype.  Status changes dispatch, never the
     * boundary. */
    {
        RmePrototype a = all_active();
        RmePrototype v = all_vestigial();
        RmePortSet ea = rme_envelope(&a);
        RmePortSet ev = rme_envelope(&v);
        rme_check(ea.mask == ev.mask && ea.count == ev.count,
                  "S2", "envelope is identical for all-active and all-vestigial prototypes");
    }

    /* ---- S3: E_dispatch subset-of E_envelope, as a SET relation. */
    {
        RmePrototype a = all_active();
        RmePrototype v = all_vestigial();
        RmePortSet da = rme_dispatch(&a), ea = rme_envelope(&a);
        RmePortSet dv = rme_dispatch(&v), ev = rme_envelope(&v);
        rme_check(rme_portset_subset(&da, &ea) && rme_portset_subset(&dv, &ev)
                      && rme_dispatch_within_envelope(&a)
                      && rme_dispatch_within_envelope(&v),
                  "S3", "E_dispatch is a subset of E_envelope for both prototypes");
    }

    /* ---- S4: no ACTIVE port is ever elided — dispatch equals the envelope
     * when every port is active. */
    {
        RmePrototype a = all_active();
        RmePortSet d = rme_dispatch(&a), e = rme_envelope(&a);
        rme_check(d.mask == e.mask && d.count == (size_t)RME_PORT_COUNT,
                  "S4", "all-active prototype: dispatch equals envelope, nothing elided");
    }

    /* ---- S5: VESTIGIAL does not imply elidable.  Elision follows each
     * port's own contract, so the four ports whose vestigial contracts
     * forbid it stay in dispatch even when vestigial: state (the default
     * must still be produced), coupling and governance (their REFUSAL must
     * remain observable — eliding governance would read as permission
     * granted), and nested. */
    {
        RmePrototype v = all_vestigial();
        RmePortSet d = rme_dispatch(&v);
        bool kept = rme_portset_has(&d, RME_PORT_state)
                 && rme_portset_has(&d, RME_PORT_coupling)
                 && rme_portset_has(&d, RME_PORT_governance)
                 && rme_portset_has(&d, RME_PORT_nested);
        bool dropped = !rme_portset_has(&d, RME_PORT_observation)
                    && !rme_portset_has(&d, RME_PORT_transition)
                    && !rme_portset_has(&d, RME_PORT_parameterization)
                    && !rme_portset_has(&d, RME_PORT_adaptation);
        rme_check(kept && dropped && d.count == 4,
                  "S5", "elision is per-port contract: refusing ports stay in dispatch");
    }

    /* ---- S6: the ports dropped from dispatch are still in the envelope.
     * This is the whole invariant in one assertion — an elided port is
     * still declared, typed, and available as a future endpoint. */
    {
        RmePrototype v = all_vestigial();
        RmePortSet d = rme_dispatch(&v), e = rme_envelope(&v);
        RmePortId elided[] = { RME_PORT_observation, RME_PORT_transition,
                               RME_PORT_parameterization, RME_PORT_adaptation };
        bool all_kept_in_envelope = true;
        for (size_t i = 0; i < sizeof elided / sizeof *elided; i++) {
            all_kept_in_envelope = all_kept_in_envelope
                                && !rme_portset_has(&d, elided[i])
                                &&  rme_portset_has(&e, elided[i]);
        }
        rme_check(all_kept_in_envelope,
                  "S6", "elided ports leave the dispatch array and remain in the envelope");
    }

    /* ---- S7: topological order over a chain.  Edge Y -> X means T_X reads
     * Y, so Y must be evaluated first. */
    {
        static const RmeSlot slots[] = { { "A", true }, { "B", true }, { "C", true } };
        static const size_t rb[] = { 0 };   /* T_B reads A */
        static const size_t rc[] = { 1 };   /* T_C reads B */
        static const RmeTransitionDecl tr[] = { { "T_B", 1, rb, 1 }, { "T_C", 2, rc, 1 } };
        RmeSystem s = { slots, 3, tr, 2, false };

        RmeSchedule sch;
        bool built = rme_schedule_build(&s, &sch);
        bool ordered = built && sch.order_count == 3
                    && sch.order[0] == 0 && sch.order[1] == 1 && sch.order[2] == 2
                    && sch.group_count == 3;
        bool none_iterate = built;
        for (size_t i = 0; built && i < sch.group_count; i++) {
            none_iterate = none_iterate && !sch.groups[i].iterate;
        }
        rme_schedule_release(&sch);
        rme_check(ordered && none_iterate,
                  "S7", "acyclic chain flattens to dependency order with no iteration groups");
    }

    /* ---- S8: a mutual pair becomes ONE group marked for fixed-point
     * iteration.  Note this is a scheduling fact, not a classification:
     * `iterate` is not RME-7. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t rx[] = { 1 };
        static const size_t ry[] = { 0 };
        static const RmeTransitionDecl tr[] = { { "T_X", 0, rx, 1 }, { "T_Y", 1, ry, 1 } };
        RmeSystem s = { slots, 2, tr, 2, false };

        RmeSchedule sch;
        bool built = rme_schedule_build(&s, &sch);
        bool one_group = built && sch.group_count == 1
                      && sch.groups[0].count == 2 && sch.groups[0].iterate
                      && sch.order_count == 2;
        rme_schedule_release(&sch);
        rme_check(one_group, "S8", "mutually dependent slots form one fixed-point group");
    }

    /* ---- S9: a self-dependency is marked for iteration even though its
     * SCC has a single member — the case cardinality alone would miss, and
     * the scheduling counterpart of the frozen self-loop rule. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        static const size_t rx[] = { 0 };
        static const RmeTransitionDecl tr[] = { { "T_X", 0, rx, 1 } };
        RmeSystem s = { slots, 1, tr, 1, false };

        RmeSchedule sch;
        bool built = rme_schedule_build(&s, &sch);
        bool marked = built && sch.group_count == 1
                   && sch.groups[0].count == 1 && sch.groups[0].iterate;
        rme_schedule_release(&sch);
        rme_check(marked, "S9", "single-member SCC with a self-edge is marked for iteration");
    }

    /* ---- S10: the schedule respects ENVIRONMENTAL dependencies too.  It
     * uses the full projection, not G_GS: restricting it to governed slots
     * would leak a classification concept into execution order. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "E", false } };
        static const size_t re[] = { 0 };   /* T_E reads X */
        static const size_t rx[] = { 1 };   /* T_X reads E  -> a cycle through E */
        static const RmeTransitionDecl tr[] = { { "T_E", 1, re, 1 }, { "T_X", 0, rx, 1 } };
        RmeSystem s = { slots, 2, tr, 2, false };

        RmeSchedule sch;
        bool built = rme_schedule_build(&s, &sch);
        bool grouped = built && sch.group_count == 1 && sch.groups[0].iterate;

        /* The same system classifies RME-6B, not RME-7: iterate != RME-7. */
        RmeClassification c;
        bool classified = rme_classify(&s, &c) && c == RME_CLASS_RME6B;

        rme_schedule_release(&sch);
        rme_check(grouped && classified,
                  "S10", "schedule groups an environmental cycle; the same system is RME-6B");
    }

    /* ---- S11: a system too large to schedule is refused, not truncated. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        RmeSystem s = { slots, (size_t)RME_MAX_SLOTS + 1, nullptr, 0, false };
        RmeSchedule sch;
        bool built = rme_schedule_build(&s, &sch);
        rme_check(!built, "S11", "unschedulable system is refused, never partially flattened");
    }
}
