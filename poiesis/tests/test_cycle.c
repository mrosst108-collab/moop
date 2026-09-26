/* poiesis — GATE 3 suite: Axis C, OBSERVED not asserted.
 *
 * Axis C asks a declared system ONE question: does a directed cycle lie
 * among the selected slots (rme_has_cycle).  The substrate names no RME
 * level.  Each test states the answer it expects, and the conformance
 * suite's verdict names read off those answers:
 *
 *     RME-7    a cycle among the governed slots
 *     6B       a cycle over all slots, and none among the governed ones
 *     not 7    no cycle among the governed slots
 *
 * Every test declares its slots and its transition read-sets explicitly.
 * The check's only input is RmeSystem: it cannot see call graphs,
 * containment or recursion, so nesting/recursion/execution loops cannot
 * promote a system to RME-7 by construction rather than by argument.
 */
#include <stddef.h>
#include <stdint.h>

#include "rme/graph.h"
#include "rme/conform.h"

extern void rme_check(bool cond, const char *id, const char *what);

/* An answer, compared in one step.  A refusal is never read as an answer:
 * "no cycle" requires the check to have ANSWERED no. */
static bool cycle_is(const RmeSystem *s, bool governed_only, bool want)
{
    bool got;
    return rme_has_cycle(s, governed_only, &got) && got == want;
}

/* The two readings the suite names. */
static bool governed_cycle(const RmeSystem *s)
{
    return cycle_is(s, true, true);
}

static bool environmental_return(const RmeSystem *s)
{
    return cycle_is(s, true, false) && cycle_is(s, false, true);
}

/* ---- K1: a thousand-deep one-way governed chain, with nesting declared as
 * a SEPARATE relation.  Asserts depth, acyclicity, and that the chain is
 * really declared — depth alone would leave open whether acyclicity was
 * reached by having no edges at all. */
#define K1_N 1000
static RmeSlot           k1_slots[K1_N];
static RmeTransitionDecl k1_trans[K1_N - 1];
static size_t            k1_reads[K1_N - 1];
static size_t            k1_nesting_parent[K1_N];   /* R_N, not E_GS */
static RmeEdge           k1_edges[K1_N];

static size_t k1_nesting_depth(void)
{
    size_t deepest = 0;
    for (size_t i = 0; i < K1_N; i++) {
        size_t d = 0;
        for (size_t v = i; v != 0; v = k1_nesting_parent[v]) {
            d++;
        }
        if (d > deepest) {
            deepest = d;
        }
    }
    return deepest + 1;   /* count the root itself */
}

void rme_test_cycle(void);

void rme_test_cycle(void)
{
    /* ---- K2: mutual governed reads.  The direct criterion, satisfied as a
     * CONJUNCTION: dT_X/dY != 0 AND dT_Y/dX != 0. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t rx[] = { 1 };   /* T_X reads Y */
        static const size_t ry[] = { 0 };   /* T_Y reads X */
        static const RmeTransitionDecl tr[] = {
            { "T_X", 0, rx, 1 },
            { "T_Y", 1, ry, 1 },
        };
        RmeSystem s = { slots, 2, tr, 2 };
        rme_check(governed_cycle(&s),
                  "K2", "mutual governed reads are a governed cycle: RME-7");
    }

    /* ---- K4: one direction only.  A pipeline is not reciprocity — this is
     * the case the disjunctive criterion would wrongly promote.  Not a
     * governed cycle, and no cycle at all. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t ry[] = { 0 };   /* T_Y reads X; nothing reads Y */
        static const RmeTransitionDecl tr[] = { { "T_Y", 1, ry, 1 } };
        RmeSystem s = { slots, 2, tr, 1 };
        rme_check(cycle_is(&s, true, false) && cycle_is(&s, false, false),
                  "K4", "one-way governed dependency is no cycle: not RME-7");
    }

    /* ---- K5: mediated criterion, X1 -> X2 -> X3 -> X1, every node
     * governed. */
    {
        static const RmeSlot slots[] = { { "X1", true }, { "X2", true }, { "X3", true } };
        static const size_t r1[] = { 2 };   /* T_X1 reads X3 */
        static const size_t r2[] = { 0 };   /* T_X2 reads X1 */
        static const size_t r3[] = { 1 };   /* T_X3 reads X2 */
        static const RmeTransitionDecl tr[] = {
            { "T_X1", 0, r1, 1 }, { "T_X2", 1, r2, 1 }, { "T_X3", 2, r3, 1 },
        };
        RmeSystem s = { slots, 3, tr, 3 };
        rme_check(governed_cycle(&s),
                  "K5", "governed 3-cycle is a governed cycle: RME-7 (mediated criterion)");
    }

    /* ---- K6: the SAME cycle with one node environmental.  The cycle no
     * longer lies entirely within the governed slots, so it is 6B, not 7.
     * One bit on one slot is the whole difference. */
    {
        static const RmeSlot slots[] = { { "X1", true }, { "E", false }, { "X3", true } };
        static const size_t r1[] = { 2 };
        static const size_t r2[] = { 0 };
        static const size_t r3[] = { 1 };
        static const RmeTransitionDecl tr[] = {
            { "T_X1", 0, r1, 1 }, { "T_E", 1, r2, 1 }, { "T_X3", 2, r3, 1 },
        };
        RmeSystem s = { slots, 3, tr, 3 };
        rme_check(environmental_return(&s),
                  "K6", "same cycle with one environmental node returns through it: 6B, not 7");
    }

    /* ---- K3: return through environmental state, X -> environment -> X. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "E", false } };
        static const size_t re[] = { 0 };   /* T_E reads X */
        static const size_t rx[] = { 1 };   /* T_X reads E */
        static const RmeTransitionDecl tr[] = {
            { "T_E", 1, re, 1 }, { "T_X", 0, rx, 1 },
        };
        RmeSystem s = { slots, 2, tr, 2 };
        rme_check(environmental_return(&s),
                  "K3", "return through environmental state: 6B");
    }

    /* ---- K7: execution self-recursion and an execution loop, with NO
     * declared governed reads.  The check cannot see bodies, and must not
     * promote.  Pairs with K10 to pin:
     *     governed self-dependency != execution self-recursion            */
    {
        static const RmeSlot slots[] = { { "X", true } };
        /* T_X's body recurses and loops; it declares no governed read. */
        static const RmeTransitionDecl tr[] = { { "T_X", 0, nullptr, 0 } };
        RmeSystem s = { slots, 1, tr, 1 };
        rme_check(cycle_is(&s, true, false),
                  "K7", "execution self-recursion with no governed read does not promote");
    }

    /* ---- K10: a single governed state with an explicit governed
     * self-dependency X -> X, and NO execution recursion.  FROZEN rule: a
     * governed self-edge is a directed cycle, therefore RME-7.  Under
     * reachability it needs no special case: it is a path of length 1. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        static const size_t rx[] = { 0 };   /* T_X declares a read of X */
        static const RmeTransitionDecl tr[] = { { "T_X", 0, rx, 1 } };
        RmeSystem s = { slots, 1, tr, 1 };
        rme_check(governed_cycle(&s),
                  "K10", "governed self-dependency X->X is a directed cycle: RME-7");
    }

    /* ---- K1: depth 1000, one-way governed, nesting declared separately.
     * Asserts depth AND acyclicity directly, and that all 999 governed
     * dependencies are declared. */
    {
        for (size_t i = 0; i < K1_N; i++) {
            k1_slots[i].name = "P";
            k1_slots[i].governed = true;
            k1_nesting_parent[i] = (i == 0) ? 0 : i - 1;   /* R_N: a 1000-deep chain */
        }
        for (size_t i = 0; i + 1 < K1_N; i++) {
            k1_reads[i] = i;                       /* T_{i+1} reads P_i */
            k1_trans[i].name = "T";
            k1_trans[i].target = i + 1;
            k1_trans[i].reads = &k1_reads[i];
            k1_trans[i].read_count = 1;
        }
        RmeSystem s = { k1_slots, K1_N, k1_trans, K1_N - 1 };

        size_t m = rme_project(&s, true, k1_edges, K1_N);
        bool declared = (m == K1_N - 1);
        bool acyclic  = cycle_is(&s, true, false) && cycle_is(&s, false, false);
        bool deep     = (k1_nesting_depth() == K1_N);

        rme_check(declared && acyclic && deep,
                  "K1", "1000-deep one-way governed chain: 999 governed edges, no cycle; "
                        "nesting depth 1000 promotes nothing");
    }

    /* ---- K9: a conformant prototype whose system has no governed cycle.
     * Both hold simultaneously — that is the normal case, not a tension
     * (F6). */
    {
        RmePrototype p = {
            .identity = { "P" },
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
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t ry[] = { 0 };
        static const RmeTransitionDecl tr[] = { { "T_Y", 1, ry, 1 } };
        RmeSystem s = { slots, 2, tr, 1 };

        RmeConformance c = rme7_conforms(&p);
        rme_check(c.ok && cycle_is(&s, true, false),
                  "K9", "RME-7-conformant prototype whose system has no governed cycle: both hold");
    }

    /* ---- C17: a system with a governed cycle alongside a NON-conformant
     * prototype.  The check has no authority over conformance (F6, and the
     * prohibited inference "governed cycle => RME7Conforms(P)"). */
    {
        RmePrototype p = {
            .identity = { "P" },
            .schema   = { RME_SCHEMA_NAME, RME_SCHEMA_MAJOR, RME_SCHEMA_MINOR },
            .state            = { { RME_VESTIGIAL, RME_PORT_state },            &rme_vestigial_state            },
            .observation      = { { RME_VESTIGIAL, RME_PORT_observation },      &rme_vestigial_observation      },
            .transition       = { { RME_VESTIGIAL, RME_PORT_transition },       &rme_vestigial_transition       },
            .parameterization = { { RME_VESTIGIAL, RME_PORT_parameterization }, &rme_vestigial_parameterization },
            .coupling         = { { RME_UNDEFINED, RME_PORT_coupling },         &rme_vestigial_coupling         },
            .adaptation       = { { RME_VESTIGIAL, RME_PORT_adaptation },       &rme_vestigial_adaptation       },
            .governance       = { { RME_VESTIGIAL, RME_PORT_governance },       &rme_vestigial_governance       },
            .nested           = { { RME_VESTIGIAL, RME_PORT_nested },           &rme_vestigial_nested           },
        };
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t rx[] = { 1 };
        static const size_t ry[] = { 0 };
        static const RmeTransitionDecl tr[] = { { "T_X", 0, rx, 1 }, { "T_Y", 1, ry, 1 } };
        RmeSystem s = { slots, 2, tr, 2 };

        /* Order matters: conformance is sampled AFTER the check has run, or
         * the test shows only that conformance was already false and says
         * nothing about the check's inability to change it. */
        RmeConformance before = rme7_conforms(&p);
        bool seven = governed_cycle(&s);
        RmeConformance after = rme7_conforms(&p);
        rme_check(seven && !before.ok && !after.ok
                      && before.port == after.port,
                  "C17", "observing a governed cycle leaves the prototype non-conformant, verdict unchanged");
    }

    /* ---- K11: a refusal is not an answer.  A system too large to represent
     * is refused under BOTH selections rather than reported acyclic. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        RmeSystem s = { slots, (size_t)RME_MAX_SLOTS + 1, nullptr, 0 };
        bool got = false;
        rme_check(!rme_has_cycle(&s, true, &got) && !rme_has_cycle(&s, false, &got),
                  "K11", "system exceeding representable capacity is refused, not downgraded");
    }
}
