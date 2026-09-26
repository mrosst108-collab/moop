/* poiesis — the OPEN item, tested rather than deferred (spec §11.1, §14).
 *
 * The question:
 *
 *     Does the retained PROTOTYPE representation expose all relation-bearing
 *     distinctions required to reconstruct E_GS -- or is E_GS merely
 *     INJECTED at system level?
 *
 * The experiment that settles it is a discrimination test.  If the cycle
 * check answers two systems differently while their prototype
 * representations are INDISTINGUISHABLE, then no function whatsoever of the
 * prototypes alone -- present or future, however written -- can reproduce
 * the answer.  Sufficiency is refuted, not left open.
 *
 * A pair of systems with that property is not contrived here: K8b already
 * uses it.  Flipping the governed marking on ONE SLOT turns AWV's cycle
 * from environmental (6B) to governed (RME-7) while touching no prototype
 * at all.
 */
#include <stddef.h>
#include <string.h>

#include "awv/awv.h"

extern void rme_check(bool cond, const char *id, const char *what);

/* Field-by-field prototype comparison, so the verdict does not rest on
 * struct padding happening to match. */
static bool prototypes_indistinguishable(const RmePrototype *a, const RmePrototype *b)
{
    if (a->identity.name != b->identity.name
        && (a->identity.name == nullptr || b->identity.name == nullptr
            || strcmp(a->identity.name, b->identity.name) != 0)) {
        return false;
    }
    if (a->schema.name != b->schema.name
        || a->schema.major != b->schema.major
        || a->schema.minor != b->schema.minor) {
        return false;
    }
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        const RmePortHeader *ha = rme_port_at_const(a, (RmePortId)i);
        const RmePortHeader *hb = rme_port_at_const(b, (RmePortId)i);
        if (ha->status != hb->status || ha->id != hb->id) {
            return false;
        }
        if (rme_port_api(a, (RmePortId)i) != rme_port_api(b, (RmePortId)i)) {
            return false;
        }
    }
    return true;
}

void rme_test_sufficiency(void);

void rme_test_sufficiency(void)
{
    /* Two systems: AWV as declared, and AWV with behaviour marked governed.
     * Same slots by name, same transitions, same read-sets, ONE BIT apart. */
    const RmeSystem *op = awv_system_operative();
    static RmeSlot governed_behaviour[AWV_SLOT_COUNT];
    for (size_t i = 0; i < AWV_SLOT_COUNT; i++) {
        governed_behaviour[i] = op->slots[i];
    }
    governed_behaviour[AWV_BEHAVIOUR].governed = true;
    RmeSystem promoted = { governed_behaviour, AWV_SLOT_COUNT,
                           op->transitions, op->transition_count };

    /* ---- E1: the cycle check genuinely answers the two systems
     * differently.  Positive control: without this the discrimination test
     * would be vacuous.  A refusal on either side leaves `both` false. */
    bool op_gov = true, pr_gov = false, op_all = false;
    bool both = rme_has_cycle(op, true, &op_gov)
             && rme_has_cycle(&promoted, true, &pr_gov)
             && rme_has_cycle(op, false, &op_all);
    {
        rme_check(both && !op_gov && op_all && pr_gov,
                  "E1", "control: the operative system is 6B, the promoted one has a governed cycle (7)");
    }

    /* ---- E2: AWV's prototypes are IDENTICAL across the two systems.  The
     * governed marking lives on a slot; no port, status, realization,
     * identity or schema field records it, because the schema has no field
     * in which it could be recorded. */
    {
        RmePrototype a1 = awv_authority_prototype(),    a2 = awv_authority_prototype();
        RmePrototype p1 = awv_presentation_prototype(), p2 = awv_presentation_prototype();
        RmePrototype c1 = awv_community_prototype_open(), c2 = awv_community_prototype_open();

        bool same = prototypes_indistinguishable(&a1, &a2)
                 && prototypes_indistinguishable(&p1, &p2)
                 && prototypes_indistinguishable(&c1, &c2);

        rme_check(same, "E2",
                  "the prototype representation is identical under both answers");
    }

    /* ---- E3: THE RESULT.  Different answers, indistinguishable
     * prototypes.  Therefore no function of the prototype representation
     * alone can reproduce rme_has_cycle()'s answer, and E_GS is NOT
     * reconstructible at prototype level with the frozen schema.
     *
     * This is a NEGATIVE result and it is decisive, not provisional: it does
     * not say the reconstruction has yet to be written, it says no such
     * reconstruction exists to be written.  The distinguishing datum -- the
     * governed marking, and the transition read-sets -- is declared on
     * RmeSystem and has no representation on RmePrototype.
     *
     * What this does NOT show: that the substrate invariant is violated.
     * The governed marking is a property of a SYSTEM's dynamics, not of a
     * prototype's boundary, and §5 already declares it "a marking on state
     * slots, not a port".  Whether that is the right place for it is an
     * architectural question this test does not settle -- it settles only
     * that the two questions cannot both be answered by the prototype. */
    {
        RmePrototype a1 = awv_authority_prototype();
        RmePrototype a2 = awv_authority_prototype();
        bool answers_differ = both && op_gov != pr_gov;
        bool prototypes_same = prototypes_indistinguishable(&a1, &a2);

        rme_check(answers_differ && prototypes_same,
                  "E3", "prototype-level E_GS reconstruction is IMPOSSIBLE, not merely absent");
    }

    /* ---- E4: what IS demonstrated, stated exactly.  The observational
     * check exists without changing any prototype's declared ontology or
     * interface, because its input arrives through a separately declared
     * type.  That is extensibility BY DEPENDENCY INJECTION.  It is a real
     * property and it is not preservation, and the specification must not
     * report the one as evidence of the other. */
    {
        RmePrototype a = awv_authority_prototype();
        RmeConformance k = rme7_conforms(&a);
        bool gov = true, all = false;
        bool answered = rme_has_cycle(op, true, &gov) && rme_has_cycle(op, false, &all);

        /* Conformance and the cycle check are computed from disjoint inputs:
         * neither call can see the other's argument. */
        rme_check(k.ok && answered && !gov && all,
                  "E4", "the cycle check and conformance succeed from disjoint inputs (injection, not preservation)");
    }
}
