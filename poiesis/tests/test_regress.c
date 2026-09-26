/* poiesis — regressions for defects found by the §13 conformance audit.
 *
 * Each of these was CONFIRMED before being fixed: D1 and D2 by mutation
 * (deleting the guard left 84/84 passing), D3 by execution (segfault), D4
 * and D5 by reading the code against the silent-wrong-answer pattern that
 * had already been removed twice elsewhere.
 *
 * They live together because their common shape is the lesson: a guard
 * with no test is indistinguishable from a guard that is not there, and a
 * malformed input silently dropped is worse than one loudly refused.
 */
#include <stddef.h>
#include <stdint.h>

#include "rme/graph.h"
#include "rme/compose.h"
#include "rme/schedule.h"
#include "rme/validate.h"

extern void rme_check(bool cond, const char *id, const char *what);

static RmeOutcome r_state(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome r_obs(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome r_step(void *self, const void *args) { (void)self; (void)args; return RME_OK; }
static RmeOutcome r_get(void *self, void *out) { (void)self; (void)out; return RME_OK; }
static RmeOutcome r_couple(void *self, void *peer) { (void)self; (void)peer; return RME_OK; }
static RmeOutcome r_adapt(void *self) { (void)self; return RME_OK; }
static RmeOutcome r_govern(void *self) { (void)self; return RME_OK; }
static RmeOutcome r_resolve(const void *self, size_t i, const void **out)
{ (void)self; (void)i; if (out) *out = nullptr; return RME_OK; }

static const RmeStateApi            x_state  = { r_state,   "active" };
static const RmeObservationApi      x_obs    = { r_obs,     "active" };
static const RmeTransitionApi       x_trans  = { r_step,    "active" };
static const RmeParameterizationApi x_param  = { r_get,     "active" };
static const RmeCouplingApi         x_coup   = { r_couple,  "active" };
static const RmeAdaptationApi       x_adapt  = { r_adapt,   "active" };
static const RmeGovernanceApi       x_gov    = { r_govern,  "active" };
static const RmeNestedApi           x_nested = { r_resolve, "active" };

static RmePrototype mk(const char *name)
{
    RmePrototype p = {
        .identity = { name },
        .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
        .state            = { { RME_ACTIVE, RME_PORT_state },            &x_state  },
        .observation      = { { RME_ACTIVE, RME_PORT_observation },      &x_obs    },
        .transition       = { { RME_ACTIVE, RME_PORT_transition },       &x_trans  },
        .parameterization = { { RME_ACTIVE, RME_PORT_parameterization }, &x_param  },
        .coupling         = { { RME_ACTIVE, RME_PORT_coupling },         &x_coup   },
        .adaptation       = { { RME_ACTIVE, RME_PORT_adaptation },       &x_adapt  },
        .governance       = { { RME_ACTIVE, RME_PORT_governance },       &x_gov    },
        .nested           = { { RME_ACTIVE, RME_PORT_nested },           &x_nested },
    };
    return p;
}

void rme_test_regress(void);

void rme_test_regress(void)
{
    /* ---- D1: the P-SIDE ACTIVE guard.  Every existing test put the
     * vestigial endpoint on Q, so deleting the P-side check left 84/84
     * passing -- the guard was indistinguishable from its own absence.
     * Participates(p,R_C) => Status(p) = ACTIVE binds BOTH sides. */
    {
        RmePrototype p = mk("P");
        RmePrototype q = mk("Q");
        p.transition = (RmeTransitionPort){ { RME_VESTIGIAL, RME_PORT_transition },
                                            &rme_vestigial_transition };

        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, true };
        RmeComposition c = rme_compose_valid(&p, &q, &R);
        RmeComposition a = rme_admissible(&p, &q, &R);

        rme_check(!c.ok && !a.ok && c.edge == 0,
                  "D1", "a VESTIGIAL endpoint on the P side is refused, not only on Q");
    }

    /* ---- D2: symmetry, stated so neither side can be dropped silently
     * again.  The same relation with the vestigial port on Q. */
    {
        RmePrototype p = mk("P");
        RmePrototype q = mk("Q");
        q.coupling = (RmeCouplingPort){ { RME_VESTIGIAL, RME_PORT_coupling },
                                        &rme_vestigial_coupling };
        const RmeConnection e[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { e, 1, true };
        rme_check(!rme_admissible(&p, &q, &R).ok,
                  "D2", "a VESTIGIAL endpoint on the Q side is refused (the guard is symmetric)");
    }

    /* ---- D3: a relation claiming connections it does not carry is
     * MALFORMED, not empty.  This segfaulted: endpoints_valid read
     * R->edges[0] on the strength of R->count alone. */
    {
        RmePrototype p = mk("P");
        RmeRelation R = { nullptr, 1, true };
        RmeComposition c = rme_admissible(&p, &p, &R);
        rme_check(!c.ok && c.why != nullptr,
                  "D3", "relation with count>0 and no edge array is refused, not dereferenced");
    }

    /* ---- D4: a transition naming a slot outside the declared table is a
     * malformed SYSTEM.  It used to be silently skipped, so a system with a
     * garbage index returned a confident answer computed from a truncated
     * projection -- the third instance of the silent-wrong-answer shape,
     * after the old classifier (capacity) and the old edge-list cycle
     * predicate (allocation).  Refused under BOTH selections. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t bad_read[] = { 99 };              /* no such slot */
        static const RmeTransitionDecl tr[] = { { "T_Y", 1, bad_read, 1 } };
        RmeSystem s = { slots, 2, tr, 1 };

        bool got = false;
        bool refused = !rme_has_cycle(&s, true, &got) && !rme_has_cycle(&s, false, &got);

        static const RmeTransitionDecl tr2[] = { { "T", 42, nullptr, 0 } };  /* no such target */
        RmeSystem s2 = { slots, 2, tr2, 1 };
        bool refused2 = !rme_has_cycle(&s2, true, &got) && !rme_has_cycle(&s2, false, &got);

        rme_check(refused && refused2,
                  "D4", "a system naming an out-of-range slot is refused, not silently truncated");
    }

    /* ---- D4b: the WHOLE declaration is validated before either selection
     * is computed.  The old classifier projected the governed slots first,
     * so an out-of-range read behind an environmental target was never
     * examined once a governed cycle had been found: it answered RME-7 for
     * a malformed system.  And a system with no slots answered RME-4
     * whatever its transitions named.  Both are confident answers computed
     * around a malformed declaration (S8); both are now refused. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true }, { "E", false } };
        static const size_t rx[] = { 1 };
        static const size_t ry[] = { 0 };
        static const size_t bad[] = { 7 };                    /* no such slot */
        static const RmeTransitionDecl tr[] = {
            { "T_X", 0, rx, 1 }, { "T_Y", 1, ry, 1 },   /* a governed 2-cycle */
            { "T_E", 2, bad, 1 },                        /* environmental target */
        };
        RmeSystem s = { slots, 3, tr, 3 };
        bool got = false;
        bool refused_gov = !rme_has_cycle(&s, true, &got);
        bool refused_all = !rme_has_cycle(&s, false, &got);

        static const RmeTransitionDecl tr0[] = { { "T", 0, nullptr, 0 } };
        RmeSystem empty = { slots, 0, tr0, 1 };              /* targets a slot that cannot exist */
        bool refused_empty = !rme_has_cycle(&empty, true, &got);

        rme_check(refused_gov && refused_all && refused_empty,
                  "D4b", "a malformed declaration is refused under either selection, never answered around");
    }

    /* ---- D5: a graph primitive that takes n and the edge array as
     * INDEPENDENT arguments needs an explicit check to make them
     * consistent.  An out-of-range endpoint indexed the CSR arrays out of
     * bounds; it is now refused.  (The cycle check no longer takes n and
     * edges separately: it reads the declared system, whose indices D4 and
     * D4b cover.) */
    {
        const RmeEdge e[] = { { 0, 7 } };     /* 7 >= n */
        size_t comp[2], ncomp = 0;
        bool refused_scc = !rme_graph_scc(2, e, 1, comp, &ncomp);

        rme_check(refused_scc,
                  "D5", "edge endpoints outside [0,n) are refused, not written out of bounds");
    }

    /* ---- V4: SPEC §6's status closure is a VALIDATION-BOUNDARY claim, and
     * §15.1 step 5(c) names this exact record: an ACTIVE port aimed at the
     * declared vestigial realization.  rme_validate() omitted the
     * RealizationValid conjunct, so this reached validated state while
     * rme7_conforms() called it non-conformant -- the boundary and the
     * conformance predicate disagreed about the same record. */
    {
        rme_validation_reset();
        RmePrototype p = mk("P");
        p.adaptation.api = &rme_vestigial_adaptation;   /* status still ACTIVE */
        RmeValidation err;
        const RmeValidated *v = rme_validate(&p, &err);
        rme_check(v == nullptr && !err.ok && err.port == RME_PORT_adaptation
                      && !rme7_conforms(&p).ok,
                  "V4", "ACTIVE port aimed at the vestigial realization is refused AT the boundary");
    }

    /* ---- V5: a VESTIGIAL port pointing somewhere other than its declared
     * vestigial realization is refused by the boundary too, so V4 is not
     * passing on one direction of the closure alone. */
    {
        rme_validation_reset();
        static const RmeCouplingApi impostor = { r_couple, "not the declared object" };
        RmePrototype p = mk("P");
        p.coupling = (RmeCouplingPort){ { RME_VESTIGIAL, RME_PORT_coupling }, &impostor };
        RmeValidation err;
        rme_check(rme_validate(&p, &err) == nullptr && err.port == RME_PORT_coupling,
                  "V5", "VESTIGIAL port not pointing at its declared realization is refused too");
    }

    /* ---- V6: a handle from before a reset is INERT, not stale.  Arena
     * slots are recycled, so without a generation check the old handle
     * silently began denoting a different prototype -- laundering arriving
     * by lifetime rather than by inheritance.
     *
     * The invariant, stated at full strength:
     *
     *     A RELEASED IDENTITY MUST NEVER BECOME A VALID IDENTITY FOR A
     *     LATER OBJECT.
     *
     * The first attempt at this fix FAILED THIS TEST: stamping a generation
     * into the slot does nothing while slots are recycled, because the
     * reused slot receives the CURRENT generation and the old handle shares
     * its address -- (slot address, current generation) does not identify an
     * object across reuse.  Allocation had to become monotonic.  This test
     * is kept permanently, in the form that caught it, because it documents
     * WHY non-reuse was chosen rather than merely that it is done: the
     * tempting "just add a generation field" repair does not work. */
    {
        rme_validation_reset();
        RmePrototype first = mk("FIRST");
        const RmeValidated *old = rme_validate(&first, nullptr);
        bool named_first = rme_validated_name(old) != nullptr;

        rme_validation_reset();
        RmePrototype second = mk("SECOND");
        const RmeValidated *fresh = rme_validate(&second, nullptr);

        rme_check(named_first && old != fresh          /* the slot is NOT reused */
                      && !rme_validated_live(old)      /* the old handle is dead */
                      && rme_validated_name(old) == nullptr
                      && rme_validated_proto(old) == nullptr
                      && !rme_validated_conforms(old).ok,
                  "V6", "a handle from a released generation is inert, never re-designated");
    }

    /* ---- V7: OWNERSHIP, both halves.  The substrate owns the RECORD --
     * mutating the caller's prototype cannot reach the validated copy.  It
     * does NOT own what the record points at: a realization object is the
     * client's dispatch table, aliased by the copy.  Deep-copying a vtable
     * would defeat its purpose, so the claim is bounded here rather than
     * the code changed, and this test is what stops the bound widening
     * again by accident. */
    {
        rme_validation_reset();
        RmePrototype p = mk("P");
        const RmeValidated *v = rme_validate(&p, nullptr);
        const RmePrototype *inside = rme_validated_proto(v);

        /* Owned: the record. */
        p.coupling.hdr.status = RME_UNDEFINED;
        bool record_owned = inside->coupling.hdr.status == RME_ACTIVE
                         && rme_validated_conforms(v).ok;

        /* Not owned, by design: the realization object itself. */
        bool realization_aliased = inside->coupling.api == &x_coup;

        rme_check(record_owned && realization_aliased,
                  "V7", "the record is substrate-owned; the realization it names is not (bounded claim)");
    }

    /* ---- D6: a malformed system is refused by the SCHEDULER too, on the
     * same terms.  Two entry points consuming RmeSystem must not disagree
     * about what a valid system is. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        static const size_t bad_read[] = { 5 };
        static const RmeTransitionDecl tr[] = { { "T", 0, bad_read, 1 } };
        RmeSystem s = { slots, 1, tr, 1 };

        RmeSchedule sch;
        bool refused = !rme_schedule_build(&s, &sch);
        if (!refused) {
            rme_schedule_release(&sch);
        }
        bool got = false;
        bool check_refused = !rme_has_cycle(&s, true, &got) && !rme_has_cycle(&s, false, &got);
        rme_check(refused && check_refused,
                  "D6", "the scheduler refuses the same malformed system the cycle check does");
    }
}
