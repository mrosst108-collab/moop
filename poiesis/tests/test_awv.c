/* poiesis — GATE 4: AWV as a client.
 *
 * K8 is the only AWV entry in the conformance suite.  Everything else here
 * exists to stop K8 passing for an uninteresting reason: a system with no
 * declared cycle at all would also fail to be RME-7, so the counterfactuals
 * show that this system sits ONE DECLARATION away from 7 in two different
 * directions and is 6B because of a specific marking, not by accident.
 */
#include <stddef.h>
#include <stdint.h>

#include "awv/awv.h"

extern void rme_check(bool cond, const char *id, const char *what);

static bool classifies(const RmeSystem *s, RmeClassification want)
{
    RmeClassification got;
    return rme_classify(s, &got) && got == want;
}

void rme_test_awv(void);

void rme_test_awv(void)
{
    /* ---- K8: AWV's declared prototypes and read-sets classify RME-6B.
     * Observed from the declarations, not asserted by them. */
    {
        rme_check(classifies(awv_system_operative(), RME_CLASS_RME6B),
                  "K8", "AWV as declared classifies RME-6B");
    }

    /* ---- The decisive bit.  The loop A -> behaviour -> Sigma_U -> A is a
     * genuine directed cycle; it is 6B and not 7 solely because behaviour
     * is not a governed state object (v0.16).  Checked by projecting both
     * ways: cyclic over all slots, acyclic within G_GS. */
    {
        static RmeEdge edges[16];
        const RmeSystem *s = awv_system_operative();

        size_t m_gs = rme_project(s, true, edges, 16);
        bool gs_cyclic = true;
        bool gs_ok = (m_gs != SIZE_MAX)
                  && rme_graph_has_cycle(AWV_SLOT_COUNT, edges, m_gs, &gs_cyclic);

        size_t m_all = rme_project(s, false, edges, 16);
        bool all_cyclic = false;
        bool all_ok = (m_all != SIZE_MAX)
                   && rme_graph_has_cycle(AWV_SLOT_COUNT, edges, m_all, &all_cyclic);

        rme_check(gs_ok && !gs_cyclic && all_ok && all_cyclic,
                  "K8a", "the loop is real: cyclic over all slots, acyclic within G_GS");
    }

    /* ---- One bit is load-bearing.  Marking behaviour governed — changing
     * nothing else — promotes the same read-sets to RME-7.  This is the
     * mechanical form of "behaviour is not a governed state object". */
    {
        const RmeSystem *op = awv_system_operative();
        RmeSlot flipped[AWV_SLOT_COUNT];
        for (size_t i = 0; i < AWV_SLOT_COUNT; i++) {
            flipped[i] = op->slots[i];
        }
        flipped[AWV_BEHAVIOUR].governed = true;
        RmeSystem s = { flipped, AWV_SLOT_COUNT, op->transitions, op->transition_count, false };

        rme_check(classifies(&s, RME_CLASS_RME7),
                  "K8b", "governing behaviour would promote AWV to RME-7: the marking is decisive");
    }

    /* ---- Route 7C (v0.13, withdrawn v0.14, retained as a near-miss).  The
     * median-band fallback reads the previous epoch's median of A, adding
     * one entry to one read-set.  AWV's finding was that "a numerical
     * convention can cross the RME-7 boundary without announcing it";
     * here the classifier announces it.  Note the shape: a governed
     * self-dependency, which is exactly K10 reached from a numerical
     * convention rather than from governance. */
    {
        rme_check(classifies(awv_system_route_7c(), RME_CLASS_RME7),
                  "K8c", "Route 7C: a numerical convention crosses into RME-7");
    }

    /* ---- Fork G (v0.12): the reserved A -> theta -> A loop, were the
     * A-weighted supermajority rows made operative. */
    {
        rme_check(classifies(awv_system_fork_g(), RME_CLASS_RME7),
                  "K8d", "Fork G: A-weighted governance would close a governed 2-cycle");
    }

    /* ---- The two near-misses are DIFFERENT cycles.  7C is a self-edge on
     * A; Fork G is a 2-cycle through theta.  If both were the same edge the
     * pair would demonstrate less than it appears to. */
    {
        static RmeEdge e7c[16], eg[16];
        size_t m7c = rme_project(awv_system_route_7c(), true, e7c, 16);
        size_t mg  = rme_project(awv_system_fork_g(),   true, eg,  16);

        bool self_edge_in_7c = false;
        for (size_t i = 0; i < m7c && m7c != SIZE_MAX; i++) {
            self_edge_in_7c = self_edge_in_7c || (e7c[i].from == e7c[i].to);
        }
        bool self_edge_in_g = false;
        for (size_t i = 0; i < mg && mg != SIZE_MAX; i++) {
            self_edge_in_g = self_edge_in_g || (eg[i].from == eg[i].to);
        }
        rme_check(self_edge_in_7c && !self_edge_in_g,
                  "K8e", "7C is a governed self-edge; Fork G is a 2-cycle — distinct near-misses");
    }

    /* ---- Each AWV prototype crosses its own validation boundary and is
     * assessed against its own schema (F7).  Validity is not inherited from
     * AWV's structure, from the authority prototype, or from the system's
     * classification. */
    {
        rme_validation_reset();
        RmePrototype a = awv_authority_prototype();
        RmePrototype p = awv_presentation_prototype();
        RmePrototype c = awv_community_prototype_open();
        RmePrototype k = awv_community_prototype_curated();

        const RmeValidated *va = rme_validate(&a, nullptr);
        const RmeValidated *vp = rme_validate(&p, nullptr);
        const RmeValidated *vc = rme_validate(&c, nullptr);
        const RmeValidated *vk = rme_validate(&k, nullptr);

        bool all_conform = rme_validated_conforms(va).ok
                        && rme_validated_conforms(vp).ok
                        && rme_validated_conforms(vc).ok
                        && rme_validated_conforms(vk).ok;

        rme_check(va && vp && vc && vk && all_conform && rme_validation_count() == 4,
                  "K8f", "each AWV prototype crosses its own boundary: four validations, four handles");
    }

    /* ---- v0.9's "optional architecture, not a requirement", mechanically.
     * The open and curated communities share ONE schema and differ only in
     * two port statuses.  Because the default form keeps admission and
     * governance PRESENT AND TYPED rather than absent, opting in is a
     * status change — no port added, no type changed, no boundary
     * redesigned.  This is C18a in the client. */
    {
        RmePrototype open    = awv_community_prototype_open();
        RmePrototype curated = awv_community_prototype_curated();

        RmePortSet e_open = rme_envelope(&open), e_cur = rme_envelope(&curated);
        bool same_boundary = e_open.mask == e_cur.mask;

        bool only_two_differ = true;
        for (int i = 0; i < RME_PORT_COUNT; i++) {
            const RmePortHeader *ho = rme_port_at_const(&open,    (RmePortId)i);
            const RmePortHeader *hc = rme_port_at_const(&curated, (RmePortId)i);
            bool expected_to_differ = (i == RME_PORT_coupling) || (i == RME_PORT_governance);
            only_two_differ = only_two_differ
                           && ((ho->status == hc->status) != expected_to_differ);
        }

        /* Admission becomes wireable exactly when it becomes ACTIVE:
         * Participates(p, R_C) => Status(p) = ACTIVE. */
        const RmeConnection wire[] = { { RME_PORT_coupling, RME_PORT_coupling } };
        RmeRelation R = { wire, 1, true };
        RmeComposition before = rme_compose_valid(&open,    &open,    &R);
        RmeComposition after  = rme_compose_valid(&curated, &curated, &R);

        rme_check(same_boundary && only_two_differ && !before.ok && after.ok,
                  "K8g", "opting in to curated admission is a status change, not a boundary redesign");
    }

    /* ---- The firewall, stated as a DIFFERENCE IN VERDICTS from two
     * predicates that answer different questions.
     *
     * R_C = {(presentation.state, authority.state)} — a like-to-like pair
     * in poiesis' declared compatibility relation, both endpoints ACTIVE.
     * poiesis therefore finds it admissible, CORRECTLY: structural
     * admissibility is all it is asked about.  AWV's own constitution
     * forbids exactly this wiring (v0.12), and that verdict comes from a
     * predicate living in src/awv/ which src/rme/ cannot see.
     *
     * A substrate that refused here would have AWV's constitution compiled
     * into it, and the dependency AWV -> poiesis would run both ways. */
    {
        RmePrototype pres = awv_presentation_prototype();
        RmePrototype auth = awv_authority_prototype();
        const RmeConnection wire[] = { { RME_PORT_state, RME_PORT_state } };
        RmeRelation R = { wire, 1, true };

        RmeComposition structural = rme_compose_valid(&pres, &auth, &R);
        bool constitutional = awv_constitutionally_permitted(
            &pres, RME_PORT_state, &auth, RME_PORT_state);

        /* And the control: the same predicate permits a relation AWV does
         * not forbid, so it is not simply refusing everything. */
        RmePrototype open = awv_community_prototype_open();
        bool permitted_elsewhere = awv_constitutionally_permitted(
            &pres, RME_PORT_observation, &open, RME_PORT_state);

        rme_check(structural.ok && !constitutional && permitted_elsewhere,
                  "K8h", "structurally admissible yet constitutionally forbidden: "
                         "poiesis does not adjudicate AWV's constitution");
    }
}
