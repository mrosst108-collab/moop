#include "slot.h"

#include <assert.h>

typedef struct {
    Rme7Kind     kind;
    Rme7Equation admits;
    Rme7Operand  operand;
    Rme7Algebra  algebra;
    uint8_t      tier;
    const char  *name;
    const char  *office;
    const char  *witness;
} SlotFacts;

/* Indexed by Rme7Slot. The office and witness columns are the grammar's,
 * not a realization's -- no geometry, no manifold, no coordinates. */
static const SlotFacts FACTS[RME7_SLOT_COUNT] = {
    [RME7_J_SHARP] = {
        RME7_KIND_OPERATOR, RME7_EQ_DRIFT_X, RME7_OPERAND_DH, RME7_ALGEBRA_ANTISYMMETRIC, 0, "J#",
        "circulates without converging",
        "Hdot = 0: conservative structure loses its office" },
    [RME7_G_SHARP] = {
        RME7_KIND_OPERATOR, RME7_EQ_DRIFT_X, RME7_OPERAND_DH, RME7_ALGEBRA_POSITIVE_SEMIDEFINITE, 0, "G#",
        "converges; the only slot whose office is convergence",
        "Hdot < 0: no dedicated convergent office; descent untypeable" },
    [RME7_G_TILDE_SHARP] = {
        RME7_KIND_OPERATOR, RME7_EQ_DRIFT_X, RME7_OPERAND_DPHI, RME7_ALGEBRA_ANTISYMMETRIC, 0, "G~#",
        "confines without converging; never a gradient descent",
        "Phidot = 0: confinement collapses into descent" },
    [RME7_SIGMA] = {
        RME7_KIND_OPERATOR, RME7_EQ_DIFFUSION_X, RME7_OPERAND_DW, RME7_ALGEBRA_NONE, 1, "Sigma",
        "stochastic exploration, and the one route between objects",
        "Sigma_ij = 0: novelty and the ecological channel die together" },
    [RME7_F] = {
        RME7_KIND_OPERATOR, RME7_EQ_DRIFT_THETA, RME7_OPERAND_NONE, RME7_ALGEBRA_NONE, 2, "F",
        "evolves the generator; never a term in the state equation",
        "dtheta = 0: RME-4 at the generator level" },
    [RME7_KAPPA] = {
        RME7_KIND_ADMISSIBILITY, RME7_EQ_NONE, RME7_OPERAND_NONE, RME7_ALGEBRA_NONE, 3, "kappa",
        "admits or refuses a proposed generator change; a verdict, never a score",
        "im F not contained in K_adm: ungoverned self-modification" },
    [RME7_GAMMA] = {
        RME7_KIND_INVARIANT, RME7_EQ_NONE, RME7_OPERAND_NONE, RME7_ALGEBRA_NONE, 4, "gamma",
        "path dependence, measured from trajectories and never applied",
        "[G#, G~#] = 0: order-sensitive dynamics loses its dedicated invariant" },
};

/* The count is 5 + 1 + 1, checked here rather than asserted in prose. */
static_assert(5 + 1 + 1 == RME7_SLOT_COUNT,
              "5 operators + 1 admissibility structure + 1 invariant = 7");
static_assert(RME7_GAMMA + 1 == RME7_SLOT_COUNT,
              "gamma is the last slot; nothing may be appended after it");

Rme7Kind rme7_slot_kind(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].kind;
}

Rme7Equation rme7_slot_admits(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].admits;
}

/* Kind and equation-admission are not two independent facts: a slot is an
 * operator exactly when it may stand as an additive term somewhere. */
bool rme7_slot_is_dynamical(Rme7Slot slot) {
    bool additive = rme7_slot_admits(slot) != RME7_EQ_NONE;
    assert(additive == (rme7_slot_kind(slot) == RME7_KIND_OPERATOR));
    return additive;
}

uint8_t rme7_slot_tier(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].tier;
}

const char *rme7_slot_name(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].name;
}

const char *rme7_slot_office(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].office;
}

Rme7Algebra rme7_slot_algebra(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].algebra;
}

const char *rme7_algebra_name(Rme7Algebra algebra) {
    switch (algebra) {
    case RME7_ALGEBRA_NONE:                 return "none declared";
    case RME7_ALGEBRA_ANTISYMMETRIC:        return "antisymmetric";
    case RME7_ALGEBRA_POSITIVE_SEMIDEFINITE:return "positive semidefinite";
    }
    return "unknown";
}

Rme7Operand rme7_slot_operand(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].operand;
}

int rme7_format_edges(Rme7Edge *out, int max) {
    int n = 0;
    /* symmetric: operators sharing a one-form, recorded once per pair */
    for (int a = 0; a < RME7_SLOT_COUNT; a++)
        for (int b = a + 1; b < RME7_SLOT_COUNT; b++) {
            Rme7Slot x = (Rme7Slot)a, y = (Rme7Slot)b;
            if (rme7_slot_operand(x) == RME7_OPERAND_NONE) continue;
            if (rme7_slot_operand(x) != rme7_slot_operand(y)) continue;
            if (out != nullptr && n < max)
                out[n] = (Rme7Edge){ RME7_EDGE_SHARES_OPERAND, x, y };
            n++;
        }
    /* directional: what each slot is computed from */
    for (int a = 0; a < RME7_SLOT_COUNT; a++) {
        Rme7Slot x = (Rme7Slot)a, dep[RME7_SLOT_COUNT];
        int k = rme7_slot_derives_from(x, dep, RME7_SLOT_COUNT);
        for (int i = 0; i < k; i++) {
            if (out != nullptr && n < max)
                out[n] = (Rme7Edge){ RME7_EDGE_DERIVES, x, dep[i] };
            n++;
        }
    }
    return n;
}

int rme7_isolated_slots(Rme7Slot *out, int max) {
    Rme7Edge e[RME7_SLOT_COUNT * RME7_SLOT_COUNT];
    int m = rme7_format_edges(e, RME7_SLOT_COUNT * RME7_SLOT_COUNT);
    int n = 0;
    for (int a = 0; a < RME7_SLOT_COUNT; a++) {
        Rme7Slot x = (Rme7Slot)a;
        bool touched = false;
        for (int i = 0; i < m; i++)
            if (e[i].from == x || e[i].to == x) { touched = true; break; }
        if (touched) continue;
        if (out != nullptr && n < max) out[n] = x;
        n++;
    }
    return n;
}

const char *rme7_operand_name(Rme7Operand operand) {
    switch (operand) {
    case RME7_OPERAND_NONE: return "none";
    case RME7_OPERAND_DH:   return "dH";
    case RME7_OPERAND_DPHI: return "dPhi";
    case RME7_OPERAND_DW:   return "dW";
    }
    return "unknown";
}

const char *rme7_slot_witness(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].witness;
}

int rme7_slot_derives_from(Rme7Slot slot, Rme7Slot *out, int max) {
    assert(slot < RME7_SLOT_COUNT);
    if (slot != RME7_GAMMA) return 0;
    if (out != nullptr && max >= 2) {
        out[0] = RME7_G_SHARP;
        out[1] = RME7_G_TILDE_SHARP;
    }
    return 2;
}

bool rme7_slot_is_primitive(Rme7Slot slot) {
    return rme7_slot_derives_from(slot, nullptr, 0) == 0;
}

int rme7_slot_coupled_with(Rme7Slot slot, Rme7Slot *out, int max) {
    assert(slot < RME7_SLOT_COUNT);
    (void)out; (void)max;
    return 0;   /* nothing in the record establishes a co-occurrence coupling */
}

int rme7_unsupported_groupings(Rme7Slot *out, int max) {
    int found = 0;
    for (uint8_t rank = 0; rank < RME7_TIER_COUNT; rank++) {
        int members = 0; Rme7Slot first = RME7_J_SHARP;
        for (int s = 0; s < RME7_SLOT_COUNT; s++) {
            Rme7Slot sl = (Rme7Slot)s;
            if (rme7_slot_tier(sl) != rank) continue;
            if (members == 0) first = sl;
            members++;
        }
        if (members < 2) continue;              /* a singleton fuses nothing */
        if (rme7_slot_coupled_with(first, nullptr, 0) >= members - 1) continue;
        if (out != nullptr && found < max) out[found] = first;
        found++;
    }
    return found;
}

bool rme7_slot_order_grounded(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    uint8_t rank = rme7_slot_tier(slot);
    if (rank == 0) return true;            /* the base needs no predecessor */

    Rme7Slot dep[RME7_SLOT_COUNT];
    int n = rme7_slot_derives_from(slot, dep, RME7_SLOT_COUNT);
    for (int i = 0; i < n; i++)
        if (rme7_slot_tier(dep[i]) == rank - 1) return true;
    return false;
}

int rme7_ungrounded_order(Rme7Slot *out, int max) {
    int found = 0;
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        Rme7Slot sl = (Rme7Slot)s;
        if (rme7_slot_order_grounded(sl)) continue;
        if (out != nullptr && found < max) out[found] = sl;
        found++;
    }
    return found;
}

Rme7Basis rme7_structure_basis(Rme7Structure structure) {
    switch (structure) {
    case RME7_STRUCT_KIND_PARTITION:         return RME7_BASIS_RECORDED;
    case RME7_STRUCT_EQUATION_ADMISSION:     return RME7_BASIS_RECORDED;
    case RME7_STRUCT_GAMMA_DERIVATION:       return RME7_BASIS_RECORDED;
    case RME7_STRUCT_OPERAND:                return RME7_BASIS_RECORDED;
    /* Entailed by the removal witnesses, not stated by the format. */
    case RME7_STRUCT_ALGEBRA:                return RME7_BASIS_DERIVED;
    /* operator iff additive is not an independent fact: it follows from the
     * kind and the equation, and is asserted where the two are read. */
    case RME7_STRUCT_OPERATOR_BICONDITIONAL: return RME7_BASIS_DERIVED;
    case RME7_STRUCT_RANK0_GROUPING:         return RME7_BASIS_STIPULATED;
    case RME7_STRUCT_RANK_ORDER:             return RME7_BASIS_STIPULATED;
    case RME7_STRUCT_BIT_POSITION:           return RME7_BASIS_LAYOUT;
    case RME7_STRUCT_COUPLING:               return RME7_BASIS_ABSENT;
    }
    return RME7_BASIS_ABSENT;
}

/* Well-formedness recomputed under a supplied rank assignment: the prefix
 * condition, plus the tier-0 rule as a parameter. Bit position is not an
 * argument here, and that is the point -- it enumerates over SLOT SETS, so no
 * assignment of bits to slots can reach the answer. */
int rme7_wellformed_under(const uint8_t ranks[RME7_SLOT_COUNT],
                          bool tier0_all_or_none) {
    int count = 0;
    uint8_t maxrank = 0;
    for (int s = 0; s < RME7_SLOT_COUNT; s++)
        if (ranks[s] > maxrank) maxrank = ranks[s];

    for (unsigned b = 1; b < (1u << RME7_SLOT_COUNT); b++) {
        bool ok = true;
        for (int s = 0; s < RME7_SLOT_COUNT && ok; s++) {
            if (!(b & (1u << s))) continue;
            /* every rank strictly below this slot's must be complete */
            for (uint8_t r = 0; r < ranks[s] && ok; r++)
                for (int t = 0; t < RME7_SLOT_COUNT; t++)
                    if (ranks[t] == r && !(b & (1u << t))) { ok = false; break; }
        }
        if (ok && tier0_all_or_none) {
            int have = 0, total = 0;
            for (int s = 0; s < RME7_SLOT_COUNT; s++)
                if (ranks[s] == 0) { total++; if (b & (1u << s)) have++; }
            if (have != 0 && have != total) ok = false;
        }
        if (ok) count++;
    }
    (void)maxrank;
    return count;
}

/* Order-sensitive hash of the ACCEPTED SET, under a fixed slot labelling.
 * Ranks vary, labelling does not, so any change is attributable to ranks. */
uint64_t rme7_wellformed_signature(const uint8_t ranks[RME7_SLOT_COUNT],
                                   bool tier0_all_or_none) {
    uint64_t h = 1469598103934665603u;
    for (unsigned b = 1; b < (1u << RME7_SLOT_COUNT); b++) {
        bool ok = true;
        for (int s = 0; s < RME7_SLOT_COUNT && ok; s++) {
            if (!(b & (1u << s))) continue;
            for (uint8_t r = 0; r < ranks[s] && ok; r++)
                for (int t = 0; t < RME7_SLOT_COUNT; t++)
                    if (ranks[t] == r && !(b & (1u << t))) { ok = false; break; }
        }
        if (ok && tier0_all_or_none) {
            int have = 0, total = 0;
            for (int s = 0; s < RME7_SLOT_COUNT; s++)
                if (ranks[s] == 0) { total++; if (b & (1u << s)) have++; }
            if (have != 0 && have != total) ok = false;
        }
        if (ok) h = (h ^ (uint64_t)b) * 1099511628211u;
    }
    return h;
}

static void real_ranks(uint8_t out[RME7_SLOT_COUNT]) {
    for (int s = 0; s < RME7_SLOT_COUNT; s++) out[s] = rme7_slot_tier((Rme7Slot)s);
}

Rme7Warrant rme7_structure_warrant(Rme7Structure structure) {
    uint8_t ranks[RME7_SLOT_COUNT];
    real_ranks(ranks);
    uint64_t baseline = rme7_wellformed_signature(ranks, true);

    switch (structure) {
    case RME7_STRUCT_RANK0_GROUPING: {
        /* relax the tier-0 rule and see whether the legal SET changes */
        uint64_t relaxed = rme7_wellformed_signature(ranks, false);
        return relaxed != baseline ? RME7_WARRANT_DEMONSTRATED
                                   : RME7_WARRANT_REFUTED_STRUCTURALLY;
    }
    case RME7_STRUCT_RANK_ORDER: {
        /* Swap two ranks. The COUNT is invariant under any permutation --
         * the chain is relabelled, not reshaped -- so only the set answers. */
        uint8_t permuted[RME7_SLOT_COUNT];
        real_ranks(permuted);
        uint8_t a = permuted[RME7_SIGMA];
        permuted[RME7_SIGMA] = permuted[RME7_F];
        permuted[RME7_F] = a;
        uint64_t swapped = rme7_wellformed_signature(permuted, true);
        return swapped != baseline ? RME7_WARRANT_DEMONSTRATED
                                   : RME7_WARRANT_REFUTED_STRUCTURALLY;
    }
    case RME7_STRUCT_BIT_POSITION:
        /* Structural: rme7_wellformed_under enumerates over slot sets and
         * takes no bit assignment, so relabelling bits is unreachable in
         * principle rather than merely unused. */
        return RME7_WARRANT_REFUTED_STRUCTURALLY;

    /* Contingent. Traced through the sources: rme7_slot_kind is read by one
     * assertion inside rme7_slot_is_dynamical and nowhere else;
     * rme7_slot_admits only by that same function; rme7_slot_derives_from only
     * by rme7_slot_is_primitive and rme7_slot_order_grounded, which are audit
     * machinery. Nothing that classifies a profile, types a claim or crosses a
     * channel branches on any of them. That is this layer being thin, and says
     * nothing whatever about the format. */
    case RME7_STRUCT_EQUATION_ADMISSION: {
        /* Now consumed: claim typing refuses a slot placed in an equation it
         * does not admit. The table is consequential iff it distinguishes
         * slots for that test -- F does not admit the state equation and J#
         * does, so two otherwise identical claims type differently. The
         * companion half, that the typing predicate actually branches on it,
         * is asserted in the test suite where channel.h is in scope. */
        bool f_state  = (rme7_slot_admits(RME7_F) & RME7_EQ_STATE) != 0;
        bool j_state  = (rme7_slot_admits(RME7_J_SHARP) & RME7_EQ_STATE) != 0;
        return f_state != j_state ? RME7_WARRANT_DEMONSTRATED
                                  : RME7_WARRANT_REFUTED_STRUCTURALLY;
    }

    /* Still contingent -- but for a known reason now, and it is not thinness.
     * kind and admits are biconditional (rme7_slot_is_dynamical asserts it),
     * so consuming both would be redundant: enforcing equation admission
     * already enforces the partition. Non-use by REDUNDANCY, which licenses
     * nothing about the format either. */
    case RME7_STRUCT_KIND_PARTITION:
    case RME7_STRUCT_OPERATOR_BICONDITIONAL:
    case RME7_STRUCT_GAMMA_DERIVATION:
    case RME7_STRUCT_OPERAND:
    case RME7_STRUCT_ALGEBRA:
        return RME7_WARRANT_REFUTED_CONTINGENTLY;

    case RME7_STRUCT_COUPLING:
        /* An empty relation has nothing to perturb. */
        return RME7_WARRANT_ASSERTED;
    }
    return RME7_WARRANT_ASSERTED;
}

const char *rme7_warrant_name(Rme7Warrant warrant) {
    switch (warrant) {
    case RME7_WARRANT_DEMONSTRATED:
        return "demonstrated by perturbation";
    case RME7_WARRANT_REFUTED_STRUCTURALLY:
        return "refuted structurally: no operation could read it";
    case RME7_WARRANT_REFUTED_CONTINGENTLY:
        return "refuted contingently: nothing here reads it yet";
    case RME7_WARRANT_ASSERTED:
        return "asserted: nothing to perturb";
    }
    return "unknown";
}

bool rme7_structure_consequential(Rme7Structure structure) {
    /* Derived from the warrant, not declared -- and ONLY a structural
     * refutation may make a structure non-consequential. A contingent one is
     * a fact about this layer, so it is treated as consequential, which keeps
     * a thin implementation from arguing its way into a smaller format. */
    if (rme7_structure_warrant(structure) == RME7_WARRANT_REFUTED_STRUCTURALLY)
        return false;
    switch (structure) {
    /* Alter the kind and a slot's admissible role changes: substitution and
     * interpretation both move. */
    case RME7_STRUCT_KIND_PARTITION:         return true;
    /* Alter which equation admits a slot and legal composition changes. */
    case RME7_STRUCT_EQUATION_ADMISSION:     return true;
    case RME7_STRUCT_OPERATOR_BICONDITIONAL: return true;
    /* gamma without both operands is not computable: composition changes. */
    case RME7_STRUCT_GAMMA_DERIVATION:       return true;
    /* Both decide which profiles are legal. */
    case RME7_STRUCT_RANK0_GROUPING:         return true;
    case RME7_STRUCT_RANK_ORDER:             return true;
    case RME7_STRUCT_COUPLING:               return true;
    case RME7_STRUCT_OPERAND:                return true;
    case RME7_STRUCT_ALGEBRA:                return true;
    case RME7_STRUCT_BIT_POSITION:           return false;  /* unreachable */
    }
    return true;
}

bool rme7_structure_recoverable(Rme7Structure structure) {
    switch (rme7_structure_basis(structure)) {
    case RME7_BASIS_RECORDED:
    case RME7_BASIS_DERIVED:
        return true;
    /* An explicitly empty relation IS carried: the format states that no
     * coupling is recorded, rather than leaving a reader to infer one. */
    case RME7_BASIS_ABSENT:
        return true;
    case RME7_BASIS_STIPULATED:
    case RME7_BASIS_LAYOUT:
        return false;
    }
    return false;
}

bool rme7_structure_defective(Rme7Structure structure) {
    return rme7_structure_consequential(structure) &&
           !rme7_structure_recoverable(structure);
}

int rme7_defects(Rme7Structure *out, int max) {
    int found = 0;
    for (int i = 0; i < RME7_STRUCTURE_COUNT; i++) {
        Rme7Structure st = (Rme7Structure)i;
        if (!rme7_structure_defective(st)) continue;
        if (out != nullptr && found < max) out[found] = st;
        found++;
    }
    return found;
}

int rme7_over_recorded(Rme7Structure *out, int max) {
    int found = 0;
    for (int i = 0; i < RME7_STRUCTURE_COUNT; i++) {
        Rme7Structure st = (Rme7Structure)i;
        if (rme7_structure_consequential(st)) continue;
        if (rme7_structure_basis(st) != RME7_BASIS_RECORDED) continue;
        if (out != nullptr && found < max) out[found] = st;
        found++;
    }
    return found;
}

const char *rme7_structure_name(Rme7Structure structure) {
    switch (structure) {
    case RME7_STRUCT_KIND_PARTITION:         return "the 5 + 1 + 1 partition";
    case RME7_STRUCT_EQUATION_ADMISSION:     return "which equation admits a slot";
    case RME7_STRUCT_OPERATOR_BICONDITIONAL: return "operator iff additive";
    case RME7_STRUCT_GAMMA_DERIVATION:       return "gamma from G# and G~#";
    case RME7_STRUCT_RANK0_GROUPING:         return "rank 0 groups three slots";
    case RME7_STRUCT_RANK_ORDER:             return "the ranks occur in this sequence";
    case RME7_STRUCT_COUPLING:               return "slots that must co-occur";
    case RME7_STRUCT_BIT_POSITION:           return "which bit a slot occupies";
    case RME7_STRUCT_OPERAND:                return "what the operator is applied to";
    case RME7_STRUCT_ALGEBRA:                return "the algebraic form the witness entails";
    }
    return "unknown";
}

const char *rme7_basis_name(Rme7Basis basis) {
    switch (basis) {
    case RME7_BASIS_RECORDED:   return "recorded";
    case RME7_BASIS_DERIVED:    return "derived from recorded structure";
    case RME7_BASIS_STIPULATED: return "stipulated -- nothing carries it";
    case RME7_BASIS_LAYOUT:     return "layout -- not a claim about the object";
    case RME7_BASIS_ABSENT:     return "absent";
    }
    return "unknown";
}

bool rme7_custody_may_legislate(Rme7Custody custody) {
    (void)custody;
    return false;
}

const char *rme7_custody_name(Rme7Custody custody) {
    switch (custody) {
    case RME7_CUSTODY_NONE:          return "grammar";
    case RME7_CUSTODY_ANCHORED:      return "anchored";
    case RME7_CUSTODY_DERIVED:       return "derived";
    case RME7_CUSTODY_INTERPRETIVE:  return "interpretive";
    case RME7_CUSTODY_UNADJUDICATED: return "unadjudicated";
    }
    return "unknown";
}
