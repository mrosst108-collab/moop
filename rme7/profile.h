#ifndef RME7_PROFILE_H
#define RME7_PROFILE_H

#include "slot.h"

/* An activation profile: one bit per slot.
 *
 * A set bit means EXHIBITED. A clear bit means NOT ESTABLISHED -- not
 * "absent". The profile is a translation artifact and records the result of
 * an explicit cast; equal profiles never imply the underlying systems are
 * the same, and a native formalism is not presumed to contain seven native
 * components waiting to be recognised. */
typedef struct { uint8_t bits; } Rme7Profile;

[[nodiscard]] Rme7Profile rme7_profile_empty(void);
[[nodiscard]] bool  rme7_profile_exhibits(Rme7Profile p, Rme7Slot slot);
void rme7_profile_set(Rme7Profile *p, Rme7Slot slot, bool exhibited);
[[nodiscard]] int   rme7_profile_count(Rme7Profile p);

/* The restriction staircase. There is no RME-1, RME-2 or RME-3.
 * RME-4 zero is the deterministic sub-restriction: the metriplectic triple
 * with no stochastic slot at all. */
typedef enum : uint8_t {
    RME7_RUNG_4_ZERO,
    RME7_RUNG_4,
    RME7_RUNG_5,
    RME7_RUNG_6,
    RME7_RUNG_7
} Rme7Rung;

[[nodiscard]] const char *rme7_rung_name(Rme7Rung rung);
[[nodiscard]] const char *rme7_rung_question(Rme7Rung rung);

/* The numeric level, for level arithmetic. RME-4 zero and RME-4 share
 * level 4: the sub-restriction is a distinction the arithmetic cannot see,
 * which is stated here rather than discovered later. */
[[nodiscard]] int rme7_rung_level(Rme7Rung rung);

/* What a cast can produce. Two refusals, and they are deliverables.
 *
 * BOT_STATIC is computable: no slot of the state equation is exhibited, so
 * there is no evolving state, and non-membership is certified.
 *
 * BOT_SIB is NOT computable from the problem alone -- whether a sibling
 * formalism serves better depends on what the practitioner needs, not on
 * the cast. It therefore has its own constructor and requires a stated
 * reason; the classifier below can never return it. */
typedef enum : uint8_t {
    RME7_CAST_RUNG,
    RME7_CAST_BOT_STATIC,
    RME7_CAST_BOT_SIB,
    RME7_CAST_MALFORMED
} Rme7CastKind;

typedef struct {
    Rme7CastKind kind;
    Rme7Rung     rung;      /* meaningful iff kind == RME7_CAST_RUNG      */
    Rme7Slot     offender;  /* meaningful iff kind == RME7_CAST_MALFORMED */
    const char  *reason;    /* set for BOT_SIB; may be nullptr otherwise  */
} Rme7Cast;

/* A profile is well formed when it is a prefix of the staircase: no slot
 * may be exhibited while a slot below its tier is not. A gap is a decidable
 * level violation, not a matter of judgement. */
[[nodiscard]] bool rme7_profile_wellformed(Rme7Profile p, Rme7Slot *offender);

/* Computable classification only. Never returns BOT_SIB. */
[[nodiscard]] Rme7Cast rme7_profile_classify(Rme7Profile p);

/* The adjudicated refusal. Requires a reason; refuses to be constructed
 * without one. */
[[nodiscard]] Rme7Cast rme7_cast_refuse_sibling(const char *reason);

/* Observed level minus declared level. Positive: the system escaped the
 * restriction it declared. Negative: it was declared above what it
 * exhibits. Both directions are faults, and both are decidable. */
[[nodiscard]] int rme7_delta_level(Rme7Rung observed, Rme7Rung declared);

#endif /* RME7_PROFILE_H */
