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

Rme7Typing rme7_claim_typing_in(const Rme7Claim *claim, const Rme7Proto *receiver,
                                Rme7TypingMode mode) {
    if (claim == nullptr || receiver == nullptr) return RME7_TYPING_UNDEFINED_SLOT;

    /* No custody grade licenses a grammar-level claim, so the flag settles it
     * without consulting the grade at all. Common to both modes. */
    if (claim->legislates && !rme7_custody_may_legislate(claim->custody))
        return RME7_TYPING_LEGISLATES;

    if (!claim->concerns_slot) return RME7_TYPING_OK;   /* payload-only */

    /* The format's most-emphasized rule, finally enforced where claims cross:
     * a slot may be placed only in an equation that admits it. F in the state
     * equation turns generator change into state forcing; kappa or gamma in
     * either turns a gate or an invariant into a term. Recorded as a typed
     * property since the first commit and, until now, read by nothing. */
    if (claim->equation != RME7_EQ_NONE &&
        (rme7_slot_admits(claim->slot) & claim->equation) != claim->equation)
        return RME7_TYPING_WRONG_EQUATION;

    /* A distinction the receiver's chain never defines means nothing here,
     * under either reading of what a port certifies. */
    if (!rme7_proto_defines(receiver, claim->slot))
        return RME7_TYPING_UNDEFINED_SLOT;

    if (mode == RME7_TYPING_EXHIBITION || mode == RME7_TYPING_BOTH) {
        /* Per slot, not per level -- so no rung comparison is needed here, and
         * the RME-4-zero blind spot in the level map cannot reach this test. */
        if (!rme7_profile_exhibits(rme7_proto_profile(receiver), claim->slot))
            return RME7_TYPING_UNEXHIBITED_SLOT;
        if (mode == RME7_TYPING_EXHIBITION) return RME7_TYPING_OK;
        /* BOTH falls through to the relational test as well. */
    }

    /* Rung-matched, never rung-inflated: a claim made above the receiver's
     * rung cites distinctions the receiver has not reached. */
    Rme7Cast cast = rme7_proto_classify(receiver);
    if (cast.kind != RME7_CAST_RUNG) return RME7_TYPING_RUNG_ABOVE_RECEIVER;
    if (rme7_rung_level(claim->rung) > rme7_rung_level(cast.rung))
        return RME7_TYPING_RUNG_ABOVE_RECEIVER;

    return RME7_TYPING_OK;
}

Rme7Typing rme7_claim_typing(const Rme7Claim *claim, const Rme7Proto *receiver) {
    return rme7_claim_typing_in(claim, receiver, RME7_TYPING_COMPREHENSION);
}

const char *rme7_typing_name(Rme7Typing typing) {
    switch (typing) {
    case RME7_TYPING_OK:                   return "well typed";
    case RME7_TYPING_UNDEFINED_SLOT:       return "concerns a slot the receiver does not define";
    case RME7_TYPING_RUNG_ABOVE_RECEIVER:  return "made above the receiver's rung";
    case RME7_TYPING_UNEXHIBITED_SLOT:     return "understood but not instantiated by the receiver";
    case RME7_TYPING_WRONG_EQUATION:       return "places the slot in an equation it does not admit";
    case RME7_TYPING_LEGISLATES:           return "purports to legislate";
    }
    return "unknown";
}

Rme7Crossing rme7_channel_cross(const Rme7Channel *ch,
                                const Rme7Claim *claim, Rme7Claim *local) {
    if (!rme7_channel_contracted(ch))
        return (Rme7Crossing){ .reached  = RME7_STAGE_TRANSLATE,
                               .verdict  = RME7_REFUSED,
                               .outcome  = RME7_CROSS_UNCONTRACTED,
                               .from = ch != nullptr ? ch->from : nullptr,
                               .to   = ch != nullptr ? ch->to   : nullptr };

    Rme7Crossing r = { .from = ch->from, .to = ch->to };

    if (!ch->translate(claim, local, ch->ctx)) {
        r.reached = RME7_STAGE_TRANSLATE;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_UNTRANSLATABLE;
        return r;
    }

    /* T's postcondition, not a fourth stage: a translation that yields
     * something ill typed for the receiver has not done its job. */
    r.typing = rme7_claim_typing_in(local, ch->to, ch->mode);
    if (r.typing != RME7_TYPING_OK) {
        r.reached = RME7_STAGE_TRANSLATE;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_ILL_TYPED;
        return r;
    }

    if (ch->admit(local, ch->ctx) != RME7_ADMITTED) {
        r.reached = RME7_STAGE_ADMIT;
        r.verdict = RME7_REFUSED;
        r.outcome = RME7_CROSS_REFUSED;
        return r;
    }

    uint64_t before = definition_fingerprint(ch->to);
    bool took = ch->assimilate(local, ch->ctx);
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
    case RME7_CROSS_ILL_TYPED:       return "translated, and ill typed for the receiver";
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
