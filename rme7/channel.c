#include "channel.h"

#include <stddef.h>
#include <stdint.h>

/* Cheap order-sensitive fingerprint of a proto's LOCAL definitions. Only
 * locality matters: a crossing cannot reach an ancestor, so an unchanged
 * local set is enough to establish that nothing was installed. */
static uint64_t definition_fingerprint(const Rme7Proto *p) {
    uint64_t h = 1469598103934665603u;
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        uintptr_t office = (uintptr_t)p->slots[s].office;
        uint64_t field = (uint64_t)p->slots[s].defined
                       | ((uint64_t)p->slots[s].custody << 1)
                       | ((uint64_t)office << 8);
        h = (h ^ field) * 1099511628211u;
    }
    return h;
}

bool rme7_channel_contracted(const Rme7Channel *ch) {
    if (ch == nullptr) return false;
    if (ch->translate == nullptr || ch->admit == nullptr ||
        ch->assimilate == nullptr) return false;
    if (ch->from == nullptr || ch->to == nullptr) return false;
    return ch->from != ch->to;   /* i != j */
}

Rme7Crossing rme7_channel_cross(const Rme7Channel *ch,
                                const void *claim, void *into) {
    if (!rme7_channel_contracted(ch))
        return (Rme7Crossing){ .reached  = RME7_STAGE_TRANSLATE,
                               .verdict  = RME7_REFUSED,
                               .outcome  = RME7_CROSS_UNCONTRACTED,
                               .from = ch != nullptr ? ch->from : nullptr,
                               .to   = ch != nullptr ? ch->to   : nullptr };

    Rme7Crossing r = { .from = ch->from, .to = ch->to };

    if (!ch->translate(claim, into, ch->ctx)) {
        r.reached = RME7_STAGE_TRANSLATE;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_UNTRANSLATABLE;
        return r;
    }

    if (ch->admit(into, ch->ctx) != RME7_ADMITTED) {
        r.reached = RME7_STAGE_ADMIT;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_REFUSED;
        return r;
    }

    uint64_t before = definition_fingerprint(ch->to);
    bool took = ch->assimilate(into, ch->ctx);
    uint64_t after = definition_fingerprint(ch->to);

    if (before != after) {
        /* Content crossed and became grammar. The receiver's children would
         * inherit it as though the receiver had established it. */
        r.reached = RME7_STAGE_ASSIMILATE;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_MADE_HEREDITARY;
        return r;
    }

    if (!took) {
        r.reached = RME7_STAGE_ASSIMILATE;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_UNASSIMILABLE;
        return r;
    }

    r.reached = RME7_STAGE_COMPLETE;
    r.verdict = RME7_ADMITTED;
    r.outcome = RME7_CROSS_OK;
    return r;
}

const char *rme7_stage_name(Rme7Stage stage) {
    switch (stage) {
    case RME7_STAGE_TRANSLATE:  return "translate";
    case RME7_STAGE_ADMIT:      return "admit";
    case RME7_STAGE_ASSIMILATE: return "assimilate";
    case RME7_STAGE_COMPLETE:   return "complete";
    }
    return "unknown";
}

const char *rme7_cross_outcome_name(Rme7CrossOutcome outcome) {
    switch (outcome) {
    case RME7_CROSS_OK:              return "crossed";
    case RME7_CROSS_UNCONTRACTED:    return "uncontracted route";
    case RME7_CROSS_UNTRANSLATABLE:  return "means nothing in the receiver's terms";
    case RME7_CROSS_REFUSED:         return "understood and not admitted";
    case RME7_CROSS_UNASSIMILABLE:   return "admitted and could not be taken up";
    case RME7_CROSS_MADE_HEREDITARY: return "assimilation installed a definition";
    }
    return "unknown";
}

bool rme7_composed(const Rme7Channel *channels, size_t count) {
    for (size_t i = 0; i < count; i++)
        if (rme7_channel_contracted(&channels[i])) return true;
    return false;
}
