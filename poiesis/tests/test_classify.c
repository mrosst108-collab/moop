/* poiesis — GATE 3 suite: classification (Axis C), OBSERVED not asserted.
 *
 * Every test declares its slots and its transition read-sets explicitly.
 * The classifier's only input is RmeSystem: it cannot see call graphs,
 * containment or recursion, so nesting/recursion/execution loops cannot
 * promote a system to RME-7 by construction rather than by argument.
 */
#include <stddef.h>
#include <stdint.h>

#include "rme/classify.h"
#include "rme/conform.h"

extern void rme_check(bool cond, const char *id, const char *what);

/* Classify and compare in one step.  A refused verdict (capacity exceeded)
 * is never silently treated as a classification. */
static bool classifies(const RmeSystem *s, RmeClassification want)
{
    RmeClassification got;
    return rme_classify(s, &got) && got == want;
}

static bool classifies_not(const RmeSystem *s, RmeClassification unwanted)
{
    RmeClassification got;
    return rme_classify(s, &got) && got != unwanted;
}

/* ---- K1: a thousand-deep one-way governed chain, with nesting declared as
 * a SEPARATE relation.  Asserts both the depth and the acyclicity of G_GS —
 * depth alone would leave open whether RME-6 was reached by accident. */
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

void rme_test_classify(void);

void rme_test_classify(void)
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
        RmeSystem s = { slots, 2, tr, 2, false };
        rme_check(classifies(&s, RME_CLASS_RME7),
                  "K2", "mutual governed reads classify RME-7");
    }

    /* ---- K4: one direction only.  A pipeline is not reciprocity — this is
     * the case the disjunctive criterion would wrongly promote. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "Y", true } };
        static const size_t ry[] = { 0 };   /* T_Y reads X; nothing reads Y */
        static const RmeTransitionDecl tr[] = { { "T_Y", 1, ry, 1 } };
        RmeSystem s = { slots, 2, tr, 1, false };
        rme_check(classifies_not(&s, RME_CLASS_RME7) && classifies(&s, RME_CLASS_RME6),
                  "K4", "one-way governed dependency is RME-6, not RME-7");
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
        RmeSystem s = { slots, 3, tr, 3, false };
        rme_check(classifies(&s, RME_CLASS_RME7),
                  "K5", "governed 3-cycle classifies RME-7 (mediated criterion)");
    }

    /* ---- K6: the SAME cycle with one node environmental.  The cycle no
     * longer lies entirely within G_GS, so it is 6B, not 7.  One bit on one
     * slot is the whole difference. */
    {
        static const RmeSlot slots[] = { { "X1", true }, { "E", false }, { "X3", true } };
        static const size_t r1[] = { 2 };
        static const size_t r2[] = { 0 };
        static const size_t r3[] = { 1 };
        static const RmeTransitionDecl tr[] = {
            { "T_X1", 0, r1, 1 }, { "T_E", 1, r2, 1 }, { "T_X3", 2, r3, 1 },
        };
        RmeSystem s = { slots, 3, tr, 3, false };
        rme_check(classifies(&s, RME_CLASS_RME6B),
                  "K6", "same cycle with one environmental node is RME-6B, not RME-7");
    }

    /* ---- K3: return through environmental state, X -> environment -> X. */
    {
        static const RmeSlot slots[] = { { "X", true }, { "E", false } };
        static const size_t re[] = { 0 };   /* T_E reads X */
        static const size_t rx[] = { 1 };   /* T_X reads E */
        static const RmeTransitionDecl tr[] = {
            { "T_E", 1, re, 1 }, { "T_X", 0, rx, 1 },
        };
        RmeSystem s = { slots, 2, tr, 2, false };
        rme_check(classifies(&s, RME_CLASS_RME6B),
                  "K3", "return through environmental state is RME-6B");
    }

    /* ---- K7: execution self-recursion and an execution loop, with NO
     * declared governed reads.  The classifier cannot see bodies, and must
     * not promote.  Pairs with K10 to pin:
     *     governed self-dependency != execution self-recursion            */
    {
        static const RmeSlot slots[] = { { "X", true } };
        /* T_X's body recurses and loops; it declares no governed read. */
        static const RmeTransitionDecl tr[] = { { "T_X", 0, nullptr, 0 } };
        RmeSystem s = { slots, 1, tr, 1, false };
        rme_check(classifies_not(&s, RME_CLASS_RME7),
                  "K7", "execution self-recursion with no governed read does not promote");
    }

    /* ---- K10: a single governed state with an explicit governed
     * self-dependency X -> X, and NO execution recursion.  FROZEN rule: a
     * governed self-edge is a directed cycle, therefore RME-7. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        static const size_t rx[] = { 0 };   /* T_X declares a read of X */
        static const RmeTransitionDecl tr[] = { { "T_X", 0, rx, 1 } };
        RmeSystem s = { slots, 1, tr, 1, false };
        rme_check(classifies(&s, RME_CLASS_RME7),
                  "K10", "governed self-dependency X->X is a directed cycle: RME-7");
    }

    /* ---- K1: depth 1000, one-way governed, nesting declared separately.
     * Asserts depth AND acyclicity of G_GS directly. */
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
        RmeSystem s = { k1_slots, K1_N, k1_trans, K1_N - 1, false };

        size_t m = rme_project(&s, true, k1_edges, K1_N);
        bool cyclic = true;
        bool gs_acyclic = (m != SIZE_MAX)
                       && rme_graph_has_cycle(K1_N, k1_edges, m, &cyclic)
                       && !cyclic;
        bool deep = (k1_nesting_depth() == K1_N);

        rme_check(classifies(&s, RME_CLASS_RME6) && gs_acyclic && deep && m == K1_N - 1,
                  "K1", "1000-deep one-way governed chain is RME-6 with G_GS acyclic; "
                        "nesting depth 1000 promotes nothing");
    }

    /* ---- K9: a conformant prototype whose system classifies RME-6.  Both
     * hold simultaneously — that is the normal case, not a tension (F6). */
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
        RmeSystem s = { slots, 2, tr, 1, false };

        RmeConformance c = rme7_conforms(&p);
        rme_check(c.ok && classifies(&s, RME_CLASS_RME6),
                  "K9", "RME-7-conformant prototype whose system classifies RME-6: both hold");
    }

    /* ---- C17: a system classifying RME-7 alongside a NON-conformant
     * prototype.  Classification has no authority over conformance
     * (F6, and the prohibited inference Classify(S)=RME7 => RME7Conforms(P)). */
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
        RmeSystem s = { slots, 2, tr, 2, false };

        /* Order matters: conformance is sampled AFTER the classifier has
         * run, or the test shows only that conformance was already false
         * and says nothing about classification's inability to change it. */
        RmeConformance before = rme7_conforms(&p);
        bool seven = classifies(&s, RME_CLASS_RME7);
        RmeConformance after = rme7_conforms(&p);
        rme_check(seven && !before.ok && !after.ok
                      && before.port == after.port,
                  "C17", "classifying RME-7 leaves the prototype non-conformant, verdict unchanged");
    }

    /* ---- A refused verdict is not a classification: a system too large to
     * project reports failure rather than defaulting to RME-4. */
    {
        static const RmeSlot slots[] = { { "X", true } };
        RmeSystem s = { slots, (size_t)RME_MAX_SLOTS + 1, nullptr, 0, false };
        RmeClassification got;
        rme_check(!rme_classify(&s, &got),
                  "K11", "system exceeding representable capacity is refused, not downgraded");
    }
}
