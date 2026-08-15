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

#include "rme/classify.h"
#include "rme/compose.h"
#include "rme/schedule.h"

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
     * garbage index returned a confident classification computed from a
     * truncated projection -- the third instance of the silent-wrong-answer
     * shape, after rme_classify (capacity) and rme_graph_has_cycle
     * (allocation). */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t bad_read[] = { 99 };              /* no such slot */
        static const RmeTransitionDecl tr[] = { { "T_Y", 1, bad_read, 1 } };
        RmeSystem s = { slots, 2, tr, 1, false };

        RmeClassification c;
        bool refused = !rme_classify(&s, &c);

        static const RmeTransitionDecl tr2[] = { { "T", 42, nullptr, 0 } };  /* no such target */
        RmeSystem s2 = { slots, 2, tr2, 1, false };
        bool refused2 = !rme_classify(&s2, &c);

        rme_check(refused && refused2,
                  "D4", "a system naming an out-of-range slot is refused, not silently truncated");
    }

    /* ---- D5: the graph primitives take n and the edge array as
     * INDEPENDENT arguments, so nothing but an explicit check makes them
     * consistent.  An out-of-range endpoint indexed the CSR arrays out of
     * bounds; it is now refused. */
    {
        const RmeEdge e[] = { { 0, 7 } };     /* 7 >= n */
        bool cyclic = true;
        bool refused = !rme_graph_has_cycle(2, e, 1, &cyclic);

        size_t comp[2], ncomp = 0;
        bool refused_scc = !rme_graph_scc(2, e, 1, comp, &ncomp);

        rme_check(refused && refused_scc,
                  "D5", "edge endpoints outside [0,n) are refused, not written out of bounds");
    }

    /* ---- D6: a malformed system is refused by the SCHEDULER too, on the
     * same terms.  Two entry points consuming RmeSystem must not disagree
     * about what a valid system is. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        static const size_t bad_read[] = { 5 };
        static const RmeTransitionDecl tr[] = { { "T", 0, bad_read, 1 } };
        RmeSystem s = { slots, 1, tr, 1, false };

        RmeSchedule sch;
        bool refused = !rme_schedule_build(&s, &sch);
        if (!refused) {
            rme_schedule_release(&sch);
        }
        rme_check(refused,
                  "D6", "the scheduler refuses the same malformed system the classifier does");
    }
}
