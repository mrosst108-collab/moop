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

/* A claim, typed enough for a receiver to check it without knowing what it
 * means. The content stays opaque -- the operator semantics are not ours to
 * invent -- but everything a receiver needs in order to refuse it structurally
 * is declared: which distinction it concerns, at what rung it was made, how
 * grounded it is at the sender, and whether it purports to legislate. */
typedef struct {
    bool        concerns_slot;  /* false: a payload-only claim */
    Rme7Slot    slot;           /* meaningful iff concerns_slot */
    Rme7Rung    rung;           /* the rung at which the sender made it */
    Rme7Equation equation;      /* which equation it places the slot in;
                                 * RME7_EQ_NONE = the claim does not say */
    Rme7Custody custody;        /* how grounded at the sender */
    bool        legislates;     /* claims grammar-level force; always refused */
    const void *content;        /* opaque: the semantics are not the port's */
    size_t      size;
} Rme7Claim;

/* Why a translated claim is or is not well typed FOR THIS RECEIVER. These are
 * structural facts, checkable with no operator semantics whatever. */
typedef enum : uint8_t {
    RME7_TYPING_OK,
    RME7_TYPING_UNDEFINED_SLOT,      /* the receiver's chain does not define it */
    RME7_TYPING_RUNG_ABOVE_RECEIVER, /* it cites distinctions the receiver lacks */
    RME7_TYPING_UNEXHIBITED_SLOT,    /* defined, understood, and not instantiated */
    RME7_TYPING_WRONG_EQUATION,      /* places the slot in an equation it does not admit */
    RME7_TYPING_LEGISLATES           /* no custody grade licenses this */
} Rme7Typing;

/* WHAT A PORT CERTIFIES -- the open architectural question, made runnable
 * rather than argued.
 *
 *   COMPREHENSION: the receiver possesses the definitional machinery to
 *   understand the distinction. Checked as `defines(slot) AND the claim was
 *   not made above the receiver's rung`. Permits being told about a
 *   distinction one understands but does not currently instantiate.
 *
 *   EXHIBITION: the receiver actually instantiates the distinction. Checked
 *   as `exhibits(slot)`, per slot rather than per level, so it needs no rung
 *   comparison at all -- a well-formed profile cannot exhibit a slot without
 *   standing at or above its tier.
 *
 * The two are NOT equivalent, and RME-4-zero is where they come apart: it
 * defines Sigma by delegation and does not exhibit it, so a Sigma-claim at
 * rung 4 is well typed under COMPREHENSION and refused under EXHIBITION.
 * Comprehension is the default because it is the behaviour that was already
 * shipped; the default is not an endorsement. */
typedef enum : uint8_t {
    RME7_TYPING_COMPREHENSION = 0,
    RME7_TYPING_EXHIBITION    = 1,
    RME7_TYPING_BOTH          = 2
} Rme7TypingMode;

/* The two are INCOMPARABLE, which is the reason BOTH exists. Enumerated over
 * every (receiver rung, slot, claim rung) triple: 114 of 175 agree, 24 are
 * accepted only by comprehension, and 37 only by exhibition. Neither implies
 * the other, so exhibition is not a strengthening of comprehension and
 * choosing between them forfeits something either way. They guard different
 * failures:
 *
 *   comprehension is RELATIONAL -- it compares sender and receiver, and is
 *   what refuses level inflation: being addressed in terms of a stratum you
 *   have not reached.
 *
 *   exhibition is UNARY -- it reads the receiver alone, per slot, and is what
 *   refuses vacuous reference: being addressed about a distinction you do not
 *   instantiate. The sender's rung does not appear in it at all.
 *
 * Consequence worth knowing before choosing: exhibition alone DESTROYS the
 * directionality result, because a predicate that never reads the sender's
 * rung cannot order senders against receivers. BOTH is the conjunction and
 * is the only mode that refuses both failures. */

/* Well-typedness is the POSTCONDITION OF TRANSLATION, not a fourth stage.
 * The factorization has three factors and this does not add one: a
 * translation that yields something ill typed for the receiver has not put
 * the claim in the receiver's terms, which was its whole job. Enforcing T's
 * contract is not the same as inserting a stage between T and kappa. */
[[nodiscard]] Rme7Typing rme7_claim_typing_in(const Rme7Claim *claim,
                                              const Rme7Proto *receiver,
                                              Rme7TypingMode mode);

/* Shorthand for the comprehension mode. */
[[nodiscard]] Rme7Typing rme7_claim_typing(const Rme7Claim *claim,
                                           const Rme7Proto *receiver);
[[nodiscard]] const char *rme7_typing_name(Rme7Typing typing);

typedef enum : uint8_t {
    RME7_STAGE_TRANSLATE,
    RME7_STAGE_ADMIT,
    RME7_STAGE_ASSIMILATE,
    RME7_STAGE_COMPLETE
} Rme7Stage;

typedef struct {
    /* T_ij: re-express the claim in the receiver's terms. False =
     * untranslatable. Its output is then held to rme7_claim_typing. */
    bool (*translate)(const Rme7Claim *foreign, Rme7Claim *local, void *ctx);
    /* kappa_i: admit or refuse a well-typed claim. Policy, not typing. */
    Rme7Verdict (*admit)(const Rme7Claim *local, void *ctx);
    /* A_i: take it up locally. False = assimilation failed. */
    bool (*assimilate)(const Rme7Claim *local, void *ctx);
    void *ctx;

    const Rme7Proto *from;
    const Rme7Proto *to;

    /* Which question this port asks. Zero-initialises to COMPREHENSION. */
    Rme7TypingMode mode;
} Rme7Channel;

/* Why a crossing ended where it did. The stage says where; this says what,
 * and separates three failures that a single "refused" would conflate: a
 * claim that means nothing in the receiver's terms, one that means something
 * and was not admitted, and one that was admitted and could not be taken up. */
typedef enum : uint8_t {
    RME7_CROSS_OK,
    RME7_CROSS_UNCONTRACTED,
    RME7_CROSS_UNTRANSLATABLE,
    RME7_CROSS_ILL_TYPED,
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
    Rme7Typing       typing;   /* why translation failed, when it did */
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
                                              const Rme7Claim *claim,
                                              Rme7Claim *local);

[[nodiscard]] const char *rme7_stage_name(Rme7Stage stage);
[[nodiscard]] const char *rme7_cross_outcome_name(Rme7CrossOutcome outcome);

/* Composition is not "more autonomy": it is exactly the event that some
 * ordered pair has a contracted channel. */
[[nodiscard]] bool rme7_composed(const Rme7Channel *channels, size_t count);

#endif /* RME7_CHANNEL_H */
