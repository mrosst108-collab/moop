#include <stdint.h>

#include "classify.h"

const char *rme_classification_name(RmeClassification c)
{
    switch (c) {
    case RME_CLASS_RME4:  return "RME-4";
    case RME_CLASS_RME5:  return "RME-5";
    case RME_CLASS_RME6:  return "RME-6";
    case RME_CLASS_RME6B: return "RME-6B";
    case RME_CLASS_RME7:  return "RME-7";
    default:              return "<invalid-classification>";
    }
}

bool rme_classify(const RmeSystem *s, RmeClassification *out)
{
    static RmeEdge edges[RME_MAX_EDGES];

    if (s == nullptr || out == nullptr) {
        return false;
    }
    if (s->slot_count > RME_MAX_SLOTS) {
        return false;   /* unrepresentable; refuse rather than truncate */
    }
    if (s->slot_count == 0) {
        *out = RME_CLASS_RME4;
        return true;
    }

    /* The decisive projection: governed slots and state->state edges only.
     * A cycle here — and only here — promotes to RME-7. */
    size_t m_gs = rme_project(s, true, edges, RME_MAX_EDGES);
    if (m_gs == SIZE_MAX) {
        return false;   /* projection did not fit; no verdict is available */
    }
    if (rme_graph_has_cycle(s->slot_count, edges, m_gs)) {
        *out = RME_CLASS_RME7;
        return true;
    }
    size_t governed_edges = m_gs;

    /* Not RME-7.  A cycle that needs an environmental node to close is
     * RME-6B — a causal feedback loop, but not internal governed-state
     * reciprocity.  This is the verdict that requires looking beyond G_GS,
     * which is why G_GS is decisive for PROMOTION and not for every
     * verdict. */
    size_t m_all = rme_project(s, false, edges, RME_MAX_EDGES);
    if (m_all == SIZE_MAX) {
        return false;
    }
    if (rme_graph_has_cycle(s->slot_count, edges, m_all)) {
        *out = RME_CLASS_RME6B;
        return true;
    }

    if (governed_edges > 0) {
        *out = RME_CLASS_RME6;   /* one-way governed composition */
    } else if (s->adapts_parameters) {
        *out = RME_CLASS_RME5;
    } else {
        *out = RME_CLASS_RME4;
    }
    return true;
}
