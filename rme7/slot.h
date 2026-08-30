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

/* Inter-slot relations the format RECORDS.
 *
 * Minimality permits omitting a distinction only when it is reconstructible
 * from the retained typed structure without ambiguity. An unrecorded coupling
 * fails that test in the way that matters: it leaves undecidable whether
 * operators must travel together, may be independently substituted, may be
 * removed singly, may have their positions occupied by another operator, or
 * constitute an indivisible module. Those are exactly the questions a modular
 * format exists to settle mechanically.
 *
 * Only one relation is recorded, and it is transcribed rather than invented:
 * gamma is the commutator [G#, G~#], which this repository's retrieved
 * ontology carries as `commutator_of`. (That ontology withholds the field
 * from a classifier prompt, for reasons local to that experiment; the
 * withholding is prompt-scoped and says nothing about the format.)
 *
 * Fills `out` with the slots this slot is computed from and returns their
 * count; returns 0 for a primitive slot. */
[[nodiscard]] int rme7_slot_derives_from(Rme7Slot slot, Rme7Slot *out, int max);
[[nodiscard]] bool rme7_slot_is_primitive(Rme7Slot slot);

/* A COUPLING: slots that must be exhibited TOGETHER. This is what a fusion
 * claim requires, and it is NOT what derives_from records.
 *
 * The two are different relations and conflating them is easy. `derives_from`
 * is directional: gamma is computed from G# and G~#, which says gamma implies
 * both, and says nothing whatever about whether G# implies G~#. A coupling is
 * symmetric co-occurrence. Only the second can ground a fusion.
 *
 * NO COUPLING IS RECORDED. This returns 0 for every slot, and exists so the
 * absence is callable rather than remembered -- and so that a coupling, once
 * established, has somewhere to be written instead of being stipulated inside
 * a predicate where nothing can point at it. */
[[nodiscard]] int rme7_slot_coupled_with(Rme7Slot slot, Rme7Slot *out, int max);

/* Grouping claims the staircase makes that no recorded coupling supports.
 *
 * A rank carrying one slot makes no grouping claim -- there is nothing to
 * fuse. A rank carrying several claims they belong together, and under the
 * recoverability criterion that claim must be reconstructible from a recorded
 * relation. Fills `out` with one representative slot per unsupported grouping
 * and returns the count. */
[[nodiscard]] int rme7_unsupported_groupings(Rme7Slot *out, int max);

/* Is this slot's POSITION IN THE ORDER grounded in a recorded relation?
 *
 * The audit above asks whether a grouping is recoverable. This asks the same
 * question of the sequence, and it is a different question. A typed difference
 * establishes that two slots are DISTINGUISHABLE; it does not establish which
 * comes FIRST. Distinguishability is a classification fact and sequence is a
 * relation, so a boundary being recoverable says nothing about the direction
 * across it.
 *
 * Grounded means: this slot is at the base, or a slot it is recorded as
 * depending on sits at the rank immediately below. Nothing else counts --
 * an office saying kappa gates F's proposals is prose, and prose is what this
 * predicate exists to stop standing in for a relation.
 *
 * Every slot above the base returns false today. */
[[nodiscard]] bool rme7_slot_order_grounded(Rme7Slot slot);
[[nodiscard]] int  rme7_ungrounded_order(Rme7Slot *out, int max);

/* THE PROVENANCE LEDGER.
 *
 * Which structure is part of the object, and which is an artifact of how the
 * representation was laid out? Every structural claim this format makes, with
 * what carries it -- so the question is answered by calling rather than by
 * reading nine documents.
 *
 * The distinction that makes it necessary: a format contains claims about its
 * object AND choices about its own encoding, and the two are not
 * distinguishable by inspection. Bit position and rank are both orders over
 * the same seven slots, they agree monotonically, and they govern entirely
 * different things -- which bit a profile sets, versus which prefix is well
 * formed. Nothing requires the agreement. Two coincident orders, one a claim
 * and one an artifact, is exactly the condition under which each gets read as
 * the other. */
typedef enum : uint8_t {
    RME7_BASIS_RECORDED,    /* a typed field or relation carries it           */
    RME7_BASIS_DERIVED,     /* follows from recorded structure                */
    RME7_BASIS_STIPULATED,  /* asserted, and nothing in the format carries it */
    RME7_BASIS_LAYOUT,      /* encoding choice; not a claim about the object  */
    RME7_BASIS_ABSENT       /* the format has no such structure at all        */
} Rme7Basis;

typedef enum : uint8_t {
    RME7_STRUCT_KIND_PARTITION,
    RME7_STRUCT_EQUATION_ADMISSION,
    RME7_STRUCT_OPERATOR_BICONDITIONAL,
    RME7_STRUCT_GAMMA_DERIVATION,
    RME7_STRUCT_RANK0_GROUPING,
    RME7_STRUCT_RANK_ORDER,
    RME7_STRUCT_COUPLING,
    RME7_STRUCT_BIT_POSITION
} Rme7Structure;
#define RME7_STRUCTURE_COUNT 8

/* THE ARCHITECTURAL TEST, mechanized.
 *
 *   Every distinction whose alteration could change the legal composition,
 *   substitution, ordering, coupling, or interpretation of a component must be
 *   recoverable from the representation.
 *
 * Two legitimate outcomes when one is not: encode it, or remove the claim that
 * depends on it. Never a third -- inferring it from layout, sort, proximity,
 * convention or prose is what the preceding audits kept catching.
 *
 * The test needs BOTH halves. Recoverability alone over-reports: it flags an
 * encoding choice that was never a claim. Consequentiality alone under-reports:
 * it says nothing about whether the claim is carried. A defect is the
 * conjunction -- consequential AND not recoverable.
 *
 * CUSTODY NOTE. Recoverability is checked; consequentiality is a JUDGEMENT
 * encoded here, not derived from anything. It is exposed as its own predicate
 * precisely so it can be disputed per structure rather than buried inside a
 * verdict. */
[[nodiscard]] bool rme7_structure_consequential(Rme7Structure structure);
[[nodiscard]] bool rme7_structure_recoverable(Rme7Structure structure);
[[nodiscard]] bool rme7_structure_defective(Rme7Structure structure);

/* Consequential claims the representation does not carry. */
[[nodiscard]] int rme7_defects(Rme7Structure *out, int max);

/* The other side of the constraint against overengineering: structure the
 * format records that no composition depends on. Adding capacity merely to
 * look complete shows up here. */
[[nodiscard]] int rme7_over_recorded(Rme7Structure *out, int max);

[[nodiscard]] Rme7Basis   rme7_structure_basis(Rme7Structure structure);
[[nodiscard]] const char *rme7_structure_name(Rme7Structure structure);
[[nodiscard]] const char *rme7_basis_name(Rme7Basis basis);

/* Always false, for every tag. No custody grade licenses a grammar-level
 * claim; this exists so the refusal is callable rather than remembered. */
[[nodiscard]] bool rme7_custody_may_legislate(Rme7Custody custody);
[[nodiscard]] const char *rme7_custody_name(Rme7Custody custody);

#endif /* RME7_SLOT_H */
