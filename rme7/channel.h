#ifndef RME7_CHANNEL_H
#define RME7_CHANNEL_H

#include <stddef.h>

#include "proto.h"

/* Sigma_ij = A_i . kappa_i . T_ij -- translation, admission, assimilation.
 *
 * This is the horizontal relation, and it is NOT delegation. Delegation is
 * vertical, transitive, and shares definitions; a channel is peer-to-peer,
 * gated, and translates into the receiver's own terms without sharing
 * anything. Spelling either as the other would produce the collapse the
 * format forbids -- an object that got its purpose by deferring to a peer
 * would not be a second object.
 *
 * The three stages run in order and short-circuit. A route missing any
 * stage is not a weak channel; it is structurally unclassified, and this
 * header refuses to run it. */

typedef enum : uint8_t {
    RME7_REFUSED  = 0,
    RME7_ADMITTED = 1
} Rme7Verdict;

/* Two values, no arithmetic, no scalar constructor anywhere. Admissibility
 * is a verdict; a channel that could report 0.87 would be the wrong type. */
static_assert(RME7_ADMITTED == 1 && RME7_REFUSED == 0);

typedef enum : uint8_t {
    RME7_STAGE_TRANSLATE,
    RME7_STAGE_ADMIT,
    RME7_STAGE_ASSIMILATE,
    RME7_STAGE_COMPLETE
} Rme7Stage;

typedef struct {
    /* T_ij: put the claim in the receiver's terms. False = untranslatable. */
    bool (*translate)(const void *claim, void *into, void *ctx);
    /* kappa_i: admit or refuse the translated claim. */
    Rme7Verdict (*admit)(const void *translated, void *ctx);
    /* A_i: take it up locally. False = assimilation failed. */
    bool (*assimilate)(const void *translated, void *ctx);
    void *ctx;

    const Rme7Proto *from;
    const Rme7Proto *to;
} Rme7Channel;

/* Why a crossing ended where it did. The stage says where; this says what,
 * and separates three failures that a single "refused" would conflate: a
 * claim that means nothing in the receiver's terms, one that means something
 * and was not admitted, and one that was admitted and could not be taken up. */
typedef enum : uint8_t {
    RME7_CROSS_OK,
    RME7_CROSS_UNCONTRACTED,
    RME7_CROSS_UNTRANSLATABLE,
    RME7_CROSS_REFUSED,
    RME7_CROSS_UNASSIMILABLE,
    RME7_CROSS_MADE_HEREDITARY
} Rme7CrossOutcome;

/* A crossing carries its provenance. Which object sent it and which received
 * it is explicit in the result rather than implicit in the call site: across
 * a boundary there is no shared past to run backwards, so provenance has to
 * be recorded where the crossing happens or it is not recorded at all. */
typedef struct {
    Rme7Stage        reached;
    Rme7Verdict      verdict;
    Rme7CrossOutcome outcome;
    const Rme7Proto *from;
    const Rme7Proto *to;
} Rme7Crossing;

/* A channel is contracted when both endpoints are named, distinct, and all
 * three stages are present. Anything else is an untyped route. */
[[nodiscard]] bool rme7_channel_contracted(const Rme7Channel *ch);

/* Runs T, then kappa, then A, stopping at the first stage that fails.
 * Refuses (without running anything) when the channel is not contracted.
 *
 * NON-HEREDITY IS ENFORCED, not hoped for. What crosses a channel is content,
 * never grammar: assimilation may change the receiver's state, but it may not
 * install a slot definition, because a definition is delegable and the
 * receiver's own children would then inherit foreign content as if the
 * receiver had established it. The receiver's definitions are fingerprinted
 * before and after assimilation, and a crossing that changed them reports
 * RME7_CROSS_MADE_HEREDITARY. This is the actor rule -- a miss never
 * delegates -- holding one level up, at the boundary between objects. */
[[nodiscard]] Rme7Crossing rme7_channel_cross(const Rme7Channel *ch,
                                              const void *claim, void *into);

[[nodiscard]] const char *rme7_stage_name(Rme7Stage stage);
[[nodiscard]] const char *rme7_cross_outcome_name(Rme7CrossOutcome outcome);

/* Composition is not "more autonomy": it is exactly the event that some
 * ordered pair has a contracted channel. */
[[nodiscard]] bool rme7_composed(const Rme7Channel *channels, size_t count);

#endif /* RME7_CHANNEL_H */
