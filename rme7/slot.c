#include "slot.h"

#include <assert.h>

typedef struct {
    Rme7Kind     kind;
    Rme7Equation admits;
    uint8_t      tier;
    const char  *name;
    const char  *office;
    const char  *witness;
} SlotFacts;

/* Indexed by Rme7Slot. The office and witness columns are the grammar's,
 * not a realization's -- no geometry, no manifold, no coordinates. */
static const SlotFacts FACTS[RME7_SLOT_COUNT] = {
    [RME7_J_SHARP] = {
        RME7_KIND_OPERATOR, RME7_EQ_STATE, 0, "J#",
        "circulates without converging",
        "Hdot = 0: conservative structure loses its office" },
    [RME7_G_SHARP] = {
        RME7_KIND_OPERATOR, RME7_EQ_STATE, 0, "G#",
        "converges; the only slot whose office is convergence",
        "Hdot < 0: no dedicated convergent office; descent untypeable" },
    [RME7_G_TILDE_SHARP] = {
        RME7_KIND_OPERATOR, RME7_EQ_STATE, 0, "G~#",
        "confines without converging; never a gradient descent",
        "Phidot = 0: confinement collapses into descent" },
    [RME7_SIGMA] = {
        RME7_KIND_OPERATOR, RME7_EQ_STATE, 1, "Sigma",
        "stochastic exploration, and the one route between objects",
        "Sigma_ij = 0: novelty and the ecological channel die together" },
    [RME7_F] = {
        RME7_KIND_OPERATOR, RME7_EQ_GENERATOR, 2, "F",
        "evolves the generator; never a term in the state equation",
        "dtheta = 0: RME-4 at the generator level" },
    [RME7_KAPPA] = {
        RME7_KIND_ADMISSIBILITY, RME7_EQ_NONE, 3, "kappa",
        "admits or refuses a proposed generator change; a verdict, never a score",
        "im F not contained in K_adm: ungoverned self-modification" },
    [RME7_GAMMA] = {
        RME7_KIND_INVARIANT, RME7_EQ_NONE, 4, "gamma",
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

const char *rme7_slot_witness(Rme7Slot slot) {
    assert(slot < RME7_SLOT_COUNT);
    return FACTS[slot].witness;
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
