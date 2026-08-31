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
/* Position in the canonical form. Read off the equation as carried:
 *
 *   dX_t = J#(dH) - G#(dH) - G~#(dPhi) + Sigma.dW_t
 *   dtheta = ... F(X, theta, Phi) dt
 *
 * The state equation has TWO positions, not one. The metriplectic triple sits
 * under dt; Sigma sits under dW. Drift and diffusion are the structure of an
 * SDE, and a typing that calls both "the state equation" is coarser than the
 * form it transcribes -- which is why the tier-0/tier-1 boundary looked
 * ungrounded when it is written down in the equation itself.
 *
 * STATE and GENERATOR remain as unions, so a claim may name a coarser
 * position than the format distinguishes. That is under-specification, not
 * error: a claim is refused only when it names a position the slot does not
 * admit at all. */
typedef enum : uint8_t {
    RME7_EQ_NONE         = 0u,
    RME7_EQ_DRIFT_X      = 1u << 0,  /* the dt term of dX      */
    RME7_EQ_DIFFUSION_X  = 1u << 1,  /* the dW term of dX      */
    RME7_EQ_DRIFT_THETA  = 1u << 2,  /* the dt term of dtheta  */

    RME7_EQ_STATE     = RME7_EQ_DRIFT_X | RME7_EQ_DIFFUSION_X,
    RME7_EQ_GENERATOR = RME7_EQ_DRIFT_THETA
} Rme7Equation;

/* What the operator is applied to in the canonical form. J#(dH) and G#(dH)
 * share an operand; G~#(dPhi) does not. That is a relation among the tier-0
 * members written into the equation, and it is NOT the gamma commutator --
 * gamma couples G# with G~#, argument-sharing couples J# with G#. Two
 * relations over three slots, overlapping on G#, neither covering all three. */
typedef enum : uint8_t {
    RME7_OPERAND_NONE,
    RME7_OPERAND_DH,     /* the energy one-form  */
    RME7_OPERAND_DPHI,   /* the purpose one-form */
    RME7_OPERAND_DW      /* a Wiener increment   */
} Rme7Operand;

[[nodiscard]] Rme7Operand rme7_slot_operand(Rme7Slot slot);

/* The algebraic form, and it is DERIVED rather than recorded.
 *
 * Found by a second implementation, not by this one. Grouping the seven slots
 * by every property this layer records leaves J# and G# identical: both
 * operators, both in the drift of X, both consuming dH. They differ by enum
 * constant, office prose and witness prose, and by nothing typed. The enum
 * made them distinct by construction, so nothing here ever asked what
 * separates them -- a sort standing in for a structure, one level up from
 * where that error was found before.
 *
 * What separates them follows from the removal witnesses already in this file:
 * <v, Mv> = 0 for all v iff M is antisymmetric, and >= 0 iff M is positive
 * semidefinite. So Hdot = 0 gives J# its form and Hdot < 0 gives G# its own.
 * The witness is recorded; the algebra is entailed. The two are kept apart
 * because collapsing them would let a derivation pass as a record. */
typedef enum : uint8_t {
    RME7_ALGEBRA_NONE,
    RME7_ALGEBRA_ANTISYMMETRIC,        /* M^T = -M; conserves its operand   */
    RME7_ALGEBRA_POSITIVE_SEMIDEFINITE /* x^T M x >= 0; dissipates its operand */
} Rme7Algebra;

[[nodiscard]] Rme7Algebra rme7_slot_algebra(Rme7Slot slot);
[[nodiscard]] const char *rme7_algebra_name(Rme7Algebra algebra);

/* THE RECORDED RELATION GRAPH, over slots, at FORMAT level.
 *
 * Two edge kinds and they are not interchangeable: sharing an operand is
 * symmetric and says two operators consume the same one-form; derivation is
 * directional and says one is computed from another. A structure with
 * heterogeneous edges cannot be collapsed into a single nesting without
 * choosing one kind to be the hierarchy and demoting the other.
 *
 * Deliberately a separate type from the object-level Rme7RelationKind in
 * proto.h. Those are relations a particular realization declares about
 * itself; these are relations the canonical form records about the format.
 * Conflating the two scopes is the error this audit keeps finding, so the
 * types do not conflate them either. */
typedef enum : uint8_t {
    RME7_EDGE_SHARES_OPERAND,  /* symmetric: both consume the same one-form */
    RME7_EDGE_DERIVES          /* directional: from is computed from to     */
} Rme7EdgeKind;

typedef struct {
    Rme7EdgeKind kind;
    Rme7Slot     from;
    Rme7Slot     to;
} Rme7Edge;

/* Every edge the format records. Fills `out`, returns the count. */
[[nodiscard]] int rme7_format_edges(Rme7Edge *out, int max);

/* Slots participating in no recorded edge at all. A nesting over all seven
 * must invent an edge for each of these, and inventing edges is exactly how a
 * realization ordering becomes grammar. */
[[nodiscard]] int rme7_isolated_slots(Rme7Slot *out, int max);
[[nodiscard]] const char *rme7_operand_name(Rme7Operand operand);

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
    RME7_STRUCT_BIT_POSITION,
    RME7_STRUCT_OPERAND,                 /* what the operator is applied to */
    RME7_STRUCT_ALGEBRA                  /* the form entailed by the witness */
} Rme7Structure;
#define RME7_STRUCTURE_COUNT 10

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
 * WARRANT, not assertion. Consequentiality is no longer a hand-written column.
 * Where a structure can be perturbed in process, the format PERTURBS IT AND
 * LOOKS: alter the structure, recompute which profiles are well formed, and
 * see whether a licensed operation changed. A structure whose alteration
 * changes nothing is refuted, not merely unlisted.
 *
 * That matters beyond tidiness. A format that declares which distinctions
 * about itself are consequential is certifying its own criteria of failure.
 * Demonstration removes the declaration from the load-bearing path: the two
 * defects below are DEMONSTRATED, so the verdict does not rest on anyone's
 * judgement, and the structures that remain merely asserted are all
 * recoverable and therefore cannot be defects whatever their warrant. */
/* THE SCOPE LIMIT, which is not optional to state.
 *
 * A perturbation measures consequentiality RELATIVE TO THE OPERATIONS THIS
 * IMPLEMENTATION PROVIDES. An incomplete implementation refutes a structure
 * merely by not consuming it yet, and reading that as a fact about the format
 * would be the failure this whole audit exists to prevent -- deleting a real
 * distinction because a partial realization happens to ignore it.
 *
 * So refutation splits, and the split is load-bearing:
 *
 *   STRUCTURALLY refuted -- no operation COULD read it. Well-formedness
 *   enumerates over slot sets, so no assignment of bits to slots is reachable
 *   even in principle. This licenses a conclusion about the format.
 *
 *   CONTINGENTLY refuted -- no operation HERE reads it. The kind partition and
 *   equation admission are consumed by one assertion and by the audit itself;
 *   nothing that classifies a profile, types a claim, or crosses a channel
 *   branches on either. This licenses NOTHING about the format. It is a fact
 *   about this layer's incompleteness.
 *
 * Only a structural refutation may make a structure non-consequential.
 * Contingent refutation is treated as consequential-until-shown-otherwise,
 * deliberately, so that a thin implementation cannot argue its way into a
 * smaller format. */
typedef enum : uint8_t {
    RME7_WARRANT_DEMONSTRATED,           /* perturbed; a licensed operation changed */
    RME7_WARRANT_REFUTED_STRUCTURALLY,   /* no operation could read it              */
    RME7_WARRANT_REFUTED_CONTINGENTLY,   /* no operation here reads it yet          */
    RME7_WARRANT_ASSERTED                /* nothing to perturb                      */
} Rme7Warrant;

[[nodiscard]] Rme7Warrant rme7_structure_warrant(Rme7Structure structure);
[[nodiscard]] const char *rme7_warrant_name(Rme7Warrant warrant);

/* The perturbation instrument, exposed so the demonstrations can be re-run
 * rather than believed. `rme7_wellformed_under` counts the well-formed
 * non-empty profiles under a supplied rank assignment and tier-0 rule.
 *
 * COUNT IS THE WRONG COMPARISON and the signature exists because of it. A
 * permutation of the ranks relabels which slot sits at which position while
 * preserving the chain, so it leaves the COUNT identical and changes WHICH
 * profiles are legal. Comparing cardinalities reports such a permutation as
 * having changed nothing, which is false. Compare the signature. */
[[nodiscard]] int rme7_wellformed_under(const uint8_t ranks[RME7_SLOT_COUNT],
                                        bool tier0_all_or_none);
[[nodiscard]] uint64_t rme7_wellformed_signature(const uint8_t ranks[RME7_SLOT_COUNT],
                                                 bool tier0_all_or_none);

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
