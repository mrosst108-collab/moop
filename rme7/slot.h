#ifndef RME7_SLOT_H
#define RME7_SLOT_H

#include <stdbool.h>
#include <stdint.h>

/* The seven typed format-level slots.
 *
 * Three things are absent from this enum on purpose, and their absence IS
 * the enforcement -- a type error you cannot spell is better than one you
 * catch:
 *
 *   Psi    is an argument of F, never a slot. Adding it here would be the
 *          slot inflation that breaks 5 + 1 + 1 = 7.
 *   Sigma_ii / Sigma_ij are typed INSTANCES of one slot, not two slots.
 *          Splitting Sigma corrupts the count, so the instance typing lives
 *          in channel.h and cannot reach this enum.
 *   gamma  carries no value anywhere in this framework. It is computed from
 *          trajectories; a declaration may say only that it is observable.
 */
typedef enum : uint8_t {
    RME7_J_SHARP,        /* conservative circulation */
    RME7_G_SHARP,        /* dissipation              */
    RME7_G_TILDE_SHARP,  /* confinement              */
    RME7_SIGMA,          /* stochastic and channel   */
    RME7_F,              /* generator evolution      */
    RME7_KAPPA,          /* admissibility structure  */
    RME7_GAMMA           /* structural invariant     */
} Rme7Slot;

#define RME7_SLOT_COUNT 7

/* 5 operators + 1 admissibility structure + 1 invariant. Not seven
 * instances of one kind, and not seven independent algebraic generators. */
typedef enum : uint8_t {
    RME7_KIND_OPERATOR,       /* an additive term; produces tangent vectors */
    RME7_KIND_ADMISSIBILITY,  /* a gate, not a term                         */
    RME7_KIND_INVARIANT       /* in no equation; measured from trajectories */
} Rme7Kind;

/* Which equation a slot may appear in AS AN ADDITIVE TERM.
 *
 * F is GENERATOR only: putting F in dX turns generator change into state
 * forcing, which is a category error and the most frequently reintroduced
 * one. kappa and gamma are NONE: a gate is not a term, and an invariant
 * computed over trajectories is not a term either. */
typedef enum : uint8_t {
    RME7_EQ_NONE      = 0u,
    RME7_EQ_STATE     = 1u << 0,  /* dX      */
    RME7_EQ_GENERATOR = 1u << 1   /* dtheta  */
} Rme7Equation;

/* Custody. Exhibits may exhibit; they may not legislate. */
typedef enum : uint8_t {
    RME7_CUSTODY_NONE,          /* grammar level -- not an exhibit at all */
    RME7_CUSTODY_ANCHORED,
    RME7_CUSTODY_DERIVED,
    RME7_CUSTODY_INTERPRETIVE,
    RME7_CUSTODY_UNADJUDICATED
} Rme7Custody;

/* A slot DEFINITION at one rung of the ladder: what this slot is, here.
 *
 * `defined == false` means not defined at this rung -- defer to the parent.
 * It never means the slot is absent from the world.
 *
 * Definitions are the only thing delegation carries. Whether a particular
 * object EXHIBITS a slot is separate, local, and lives in its activation
 * profile: what a slot means is inherited, what an object shows is not.
 * Collapsing the two would make every descendant of a root that defines all
 * seven exhibit all seven, and the restriction staircase would vanish. */
typedef struct {
    bool        defined;
    Rme7Custody custody;
    const char *office;   /* what this slot does here; may be nullptr */
} Rme7SlotDecl;

[[nodiscard]] Rme7Kind     rme7_slot_kind(Rme7Slot slot);
[[nodiscard]] Rme7Equation rme7_slot_admits(Rme7Slot slot);
[[nodiscard]] bool         rme7_slot_is_dynamical(Rme7Slot slot);

/* Position on the restriction staircase: 0 for the metriplectic triple,
 * then Sigma, F, kappa, gamma. A well-formed profile is a prefix. */
[[nodiscard]] uint8_t rme7_slot_tier(Rme7Slot slot);
#define RME7_TIER_COUNT 5

[[nodiscard]] const char *rme7_slot_name(Rme7Slot slot);
[[nodiscard]] const char *rme7_slot_office(Rme7Slot slot);

/* What is lost when this slot is removed -- the removal witness. */
[[nodiscard]] const char *rme7_slot_witness(Rme7Slot slot);

/* Always false, for every tag. No custody grade licenses a grammar-level
 * claim; this exists so the refusal is callable rather than remembered. */
[[nodiscard]] bool rme7_custody_may_legislate(Rme7Custody custody);
[[nodiscard]] const char *rme7_custody_name(Rme7Custody custody);

#endif /* RME7_SLOT_H */
