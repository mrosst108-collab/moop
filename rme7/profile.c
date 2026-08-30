#include "profile.h"

#include <assert.h>
#include <stddef.h>

Rme7Profile rme7_profile_empty(void) { return (Rme7Profile){ .bits = 0u }; }

bool rme7_profile_exhibits(Rme7Profile p, Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return (p.bits & (uint8_t)(1u << slot)) != 0u;
}

void rme7_profile_set(Rme7Profile *p, Rme7Slot slot, bool exhibited) {
    assert(p != nullptr && slot < RME7_SLOT_COUNT);
    uint8_t mask = (uint8_t)(1u << slot);
    p->bits = exhibited ? (uint8_t)(p->bits | mask)
                        : (uint8_t)(p->bits & (uint8_t)~mask);
}

int rme7_profile_count(Rme7Profile p) {
    int n = 0;
    for (int s = 0; s < RME7_SLOT_COUNT; s++)
        if (rme7_profile_exhibits(p, (Rme7Slot)s)) n++;
    return n;
}

const char *rme7_rung_name(Rme7Rung rung) {
    switch (rung) {
    case RME7_RUNG_4_ZERO: return "RME-4-zero";
    case RME7_RUNG_4:      return "RME-4";
    case RME7_RUNG_5:      return "RME-5";
    case RME7_RUNG_6:      return "RME-6";
    case RME7_RUNG_7:      return "RME-7";
    }
    return "unknown";
}

const char *rme7_rung_question(Rme7Rung rung) {
    switch (rung) {
    case RME7_RUNG_4_ZERO: return "Can it execute without noise?";
    case RME7_RUNG_4:      return "Can it execute?";
    case RME7_RUNG_5:      return "Can it change itself?";
    case RME7_RUNG_6:      return "Can it change itself admissibly?";
    case RME7_RUNG_7:      return "Can several changing systems compose "
                                  "without losing their identities?";
    }
    return "unknown";
}

int rme7_rung_level(Rme7Rung rung) {
    switch (rung) {
    case RME7_RUNG_4_ZERO: return 4;
    case RME7_RUNG_4:      return 4;
    case RME7_RUNG_5:      return 5;
    case RME7_RUNG_6:      return 6;
    case RME7_RUNG_7:      return 7;
    }
    return 0;
}

/* Highest tier with every slot at that tier exhibited, walking up from 0
 * and stopping at the first incomplete tier. */
static bool tier_complete(Rme7Profile p, uint8_t tier) {
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        Rme7Slot slot = (Rme7Slot)s;
        if (rme7_slot_tier(slot) == tier && !rme7_profile_exhibits(p, slot))
            return false;
    }
    return true;
}

static bool tier_empty(Rme7Profile p, uint8_t tier) {
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        Rme7Slot slot = (Rme7Slot)s;
        if (rme7_slot_tier(slot) == tier && rme7_profile_exhibits(p, slot))
            return false;
    }
    return true;
}

bool rme7_profile_wellformed(Rme7Profile p, Rme7Slot *offender) {
    /* Every exhibited slot must have every lower tier complete beneath it. */
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        Rme7Slot slot = (Rme7Slot)s;
        if (!rme7_profile_exhibits(p, slot)) continue;
        for (uint8_t t = 0; t < rme7_slot_tier(slot); t++) {
            if (!tier_complete(p, t)) {
                if (offender != nullptr) *offender = slot;
                return false;
            }
        }
    }
    /* Tier 0 is the metriplectic triple: all three or none. */
    if (!tier_complete(p, 0) && !tier_empty(p, 0)) {
        if (offender != nullptr) {
            for (int s = 0; s < RME7_SLOT_COUNT; s++) {
                Rme7Slot slot = (Rme7Slot)s;
                if (rme7_slot_tier(slot) == 0 &&
                    !rme7_profile_exhibits(p, slot)) { *offender = slot; break; }
            }
        }
        return false;
    }
    return true;
}

Rme7Cast rme7_profile_classify(Rme7Profile p) {
    Rme7Slot offender = RME7_J_SHARP;
    if (!rme7_profile_wellformed(p, &offender))
        return (Rme7Cast){ .kind = RME7_CAST_MALFORMED, .offender = offender };

    /* No slot of the state equation exhibited: nothing evolves. */
    if (tier_empty(p, 0))
        return (Rme7Cast){ .kind = RME7_CAST_BOT_STATIC };

    Rme7Rung rung = RME7_RUNG_4_ZERO;
    if (rme7_profile_exhibits(p, RME7_SIGMA)) rung = RME7_RUNG_4;
    if (rme7_profile_exhibits(p, RME7_F))     rung = RME7_RUNG_5;
    if (rme7_profile_exhibits(p, RME7_KAPPA)) rung = RME7_RUNG_6;
    if (rme7_profile_exhibits(p, RME7_GAMMA)) rung = RME7_RUNG_7;
    return (Rme7Cast){ .kind = RME7_CAST_RUNG, .rung = rung };
}

Rme7Cast rme7_cast_refuse_sibling(const char *reason) {
    assert(reason != nullptr &&
           "a sibling refusal is an adjudication and must state its reason");
    return (Rme7Cast){ .kind = RME7_CAST_BOT_SIB, .reason = reason };
}

int rme7_delta_level(Rme7Rung observed, Rme7Rung declared) {
    return rme7_rung_level(observed) - rme7_rung_level(declared);
}
