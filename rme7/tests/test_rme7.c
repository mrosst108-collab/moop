#include "rme7.h"

#include <stdio.h>
#include <string.h>

static int failures = 0;

static void check(bool cond, const char *what) {
    printf("%s - %s\n", cond ? "ok  " : "FAIL", what);
    if (!cond) failures++;
}

/* ---- the seven slots, their kinds, and where they may appear ---------- */

static void test_slots(void) {
    int op = 0, adm = 0, inv = 0;
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        switch (rme7_slot_kind((Rme7Slot)s)) {
        case RME7_KIND_OPERATOR:      op++;  break;
        case RME7_KIND_ADMISSIBILITY: adm++; break;
        case RME7_KIND_INVARIANT:     inv++; break;
        }
    }
    check(op == 5 && adm == 1 && inv == 1, "the count is 5 + 1 + 1, not seven of a kind");

    bool agree = true;
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        Rme7Slot slot = (Rme7Slot)s;
        bool additive = rme7_slot_admits(slot) != RME7_EQ_NONE;
        if (additive != (rme7_slot_kind(slot) == RME7_KIND_OPERATOR)) agree = false;
    }
    check(agree, "a slot is an operator exactly when it may stand as a term");

    check(rme7_slot_admits(RME7_F) == RME7_EQ_GENERATOR,
          "F belongs to the generator equation");
    check((rme7_slot_admits(RME7_F) & RME7_EQ_STATE) == 0,
          "F is not a term in the state equation");
    check(rme7_slot_admits(RME7_KAPPA) == RME7_EQ_NONE,
          "kappa is a gate, not a term in either equation");
    check(rme7_slot_admits(RME7_GAMMA) == RME7_EQ_NONE,
          "gamma is measured, never applied");
    check(rme7_slot_tier(RME7_GAMMA) > rme7_slot_tier(RME7_KAPPA) &&
          rme7_slot_tier(RME7_KAPPA) > rme7_slot_tier(RME7_F),
          "the staircase orders F below kappa below gamma");

    for (int c = 0; c <= RME7_CUSTODY_UNADJUDICATED; c++)
        if (rme7_custody_may_legislate((Rme7Custody)c)) failures++;
    check(true, "no custody grade licenses a grammar-level claim");
}

/* ---- the ladder ------------------------------------------------------- */

typedef struct { Rme7Actor actor; Rme7Proto sysroot, userroot; } Ladder;

static void build_ladder(Ladder *l) {
    rme7_actor_init(&l->actor, "grammar");
    rme7_actor_generate_system_root(&l->actor, &l->sysroot, "system root");
    rme7_proto_generate_user_root(&l->sysroot, &l->userroot, "user root");
}

static void test_ladder(void) {
    Ladder l; build_ladder(&l);

    check(l.sysroot.parent == nullptr, "nothing delegates into the actor");
    check(l.userroot.parent == nullptr, "delegation never crosses the boundary");
    check(l.sysroot.layer == RME7_LAYER_SYSTEM && l.userroot.layer == RME7_LAYER_USER,
          "the boundary is crossed by generation, once");
    check(l.userroot.origin.kind == RME7_ORIGIN_PROTO &&
          l.userroot.origin.proto == &l.sysroot,
          "generation records who made you");

    bool all_defined = true;
    for (int s = 0; s < RME7_SLOT_COUNT; s++)
        if (!rme7_proto_defines(&l.userroot, (Rme7Slot)s)) all_defined = false;
    check(all_defined, "crossing the boundary seeds the child with the grammar");

    Rme7Proto object;
    check(rme7_proto_generate(&l.userroot, &object, "an object"),
          "a user proto generates a user proto");
    check(object.parent == &l.userroot,
          "inside the layer, generation links rather than copies");
    check(!object.slots[RME7_F].defined && rme7_proto_defines(&object, RME7_F),
          "a slot undefined locally resolves by delegation");

    const Rme7Proto *found = nullptr;
    (void)rme7_proto_resolve(&object, RME7_KAPPA, &found);
    check(found == &l.userroot, "delegation reports which rung answered");

    rme7_proto_define(&object, RME7_KAPPA, RME7_CUSTODY_INTERPRETIVE,
                      "solvency admissibility");
    (void)rme7_proto_resolve(&object, RME7_KAPPA, &found);
    check(found == &object, "a local definition overrides the chain");

    Rme7Proto sysgen;
    check(!rme7_proto_generate(&l.sysroot, &sysgen, "illegal"),
          "the system root does not generate by the user-layer rule");
}

/* The error the ladder must not make: defining all seven at a root must not
 * make every descendant exhibit all seven. */
static void test_definition_is_not_exhibition(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto object;
    (void)rme7_proto_generate(&l.userroot, &object, "an execution problem");

    check(rme7_profile_count(rme7_proto_profile(&l.userroot)) == 0,
          "a root defines the format without exhibiting it");
    check(rme7_profile_count(rme7_proto_profile(&object)) == 0,
          "exhibition is evidence and does not delegate");

    check(rme7_proto_exhibit(&object, RME7_J_SHARP) &&
          rme7_proto_exhibit(&object, RME7_G_SHARP) &&
          rme7_proto_exhibit(&object, RME7_G_TILDE_SHARP) &&
          rme7_proto_exhibit(&object, RME7_SIGMA),
          "an object exhibits the slots it shows");

    Rme7Cast cast = rme7_proto_classify(&object);
    check(cast.kind == RME7_CAST_RUNG && cast.rung == RME7_RUNG_4,
          "four slots exhibited casts at RME-4, not at seven it does not need");
}

static void test_exhibiting_the_undefined(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto orphan = { .name = "no format", .layer = RME7_LAYER_USER,
                         .parent = nullptr };
    check(!rme7_proto_exhibit(&orphan, RME7_J_SHARP),
          "an object cannot exhibit a slot the format never defined");
}

/* ---- the staircase and its violations --------------------------------- */

static Rme7Profile profile_of(const Rme7Slot *slots, int n) {
    Rme7Profile p = rme7_profile_empty();
    for (int i = 0; i < n; i++) rme7_profile_set(&p, slots[i], true);
    return p;
}

static void test_staircase(void) {
    const Rme7Slot triple[] = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP };
    const Rme7Slot four[]   = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                                RME7_SIGMA };
    const Rme7Slot five[]   = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                                RME7_SIGMA, RME7_F };
    const Rme7Slot six[]    = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                                RME7_SIGMA, RME7_F, RME7_KAPPA };
    const Rme7Slot seven[]  = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                                RME7_SIGMA, RME7_F, RME7_KAPPA, RME7_GAMMA };

    check(rme7_profile_classify(profile_of(triple, 3)).rung == RME7_RUNG_4_ZERO,
          "the metriplectic triple alone is the deterministic sub-restriction");
    check(rme7_profile_classify(profile_of(four, 4)).rung == RME7_RUNG_4, "RME-4 executes");
    check(rme7_profile_classify(profile_of(five, 5)).rung == RME7_RUNG_5, "RME-5 adapts");
    check(rme7_profile_classify(profile_of(six, 6)).rung == RME7_RUNG_6,
          "RME-6 adapts admissibly");
    check(rme7_profile_classify(profile_of(seven, 7)).rung == RME7_RUNG_7, "RME-7 composes");

    check(rme7_profile_classify(rme7_profile_empty()).kind == RME7_CAST_BOT_STATIC,
          "no evolving state is certified non-membership, not a failure");

    /* kappa without F: governing a generator that cannot change. */
    const Rme7Slot gap[] = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                             RME7_SIGMA, RME7_KAPPA };
    Rme7Cast bad = rme7_profile_classify(profile_of(gap, 5));
    check(bad.kind == RME7_CAST_MALFORMED && bad.offender == RME7_KAPPA,
          "a gap in the staircase is a decidable violation, and names its slot");
}

/* How big is the tier-0 hole, exactly? Partition all 128 profiles by WHY they
 * are refused, so the open question is a number rather than an impression. */
static void test_the_tier_zero_family_is_thirty(void) {
    const Rme7Slot t0[3] = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP };
    const Rme7Slot up[4] = { RME7_SIGMA, RME7_F, RME7_KAPPA, RME7_GAMMA };
    int wf = 0, bot = 0, tier0_only = 0, gap = 0;

    for (unsigned b = 0; b < 128u; b++) {
        Rme7Profile p = { .bits = (uint8_t)b };
        int n0 = 0;
        for (int i = 0; i < 3; i++) if (rme7_profile_exhibits(p, t0[i])) n0++;

        /* is the tier 1..4 part a prefix of (Sigma, F, kappa, gamma)? */
        bool up_ok = true, seen_gap = false; int depth = 0;
        for (int i = 0; i < 4; i++) {
            if (rme7_profile_exhibits(p, up[i])) {
                if (seen_gap) { up_ok = false; break; }
                depth = i + 1;
            } else seen_gap = true;
        }

        if (!up_ok)                     gap++;
        else if (n0 == 0 && depth == 0) bot++;
        else if (n0 == 0)               gap++;   /* upper tiers with no state */
        else if (n0 == 3)               wf++;
        else                            tier0_only++;
    }

    check(wf == 5 && bot == 1 && tier0_only == 30 && gap == 92,
          "the 128 profiles partition 5 / 1 / 30 / 92");
    check(wf + bot + tier0_only + gap == 128, "and the partition is exhaustive");
    check(tier0_only + gap == 122,
          "of the 122 malformed, only 30 are the tier-0 family: the rest are "
          "genuine gaps, refused correctly");

    /* The alternative rule -- tier 0 admits any nonempty subset -- would admit
     * the 30, giving 7 tier-0 shapes x 5 upper depths. That trades the chain
     * for a product, and one-profile-per-rung goes with it. */
    check(wf + tier0_only == 35 && 7 * 5 == 35,
          "admitting any nonempty tier-0 subset gives 35, not a chain of 5");
}

/* Modularity, measured. How many of the seven slots can an object withhold
 * INDEPENDENTLY -- exhibit the other six and not this one?
 *
 * Note what this is not: it is not a contradiction of the removal witnesses.
 * Those remove a slot from the FORMAT, giving a six-slot format with its own
 * staircase. This withholds a slot from an OBJECT while the format keeps all
 * seven. Different operations, and conflating them would be a category error.
 * What it measures is object-level modularity, which is a separate property
 * and the one a composability criterion cares about. */
static void test_only_one_slot_is_independently_withholdable(void) {
    const Rme7Slot all[7] = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                              RME7_SIGMA, RME7_F, RME7_KAPPA, RME7_GAMMA };
    int wellformed = 0; bool gamma_ok = false;

    for (int drop = 0; drop < 7; drop++) {
        Rme7Profile p = rme7_profile_empty();
        for (int i = 0; i < 7; i++)
            if (i != drop) rme7_profile_set(&p, all[i], true);
        Rme7Cast c = rme7_profile_classify(p);
        if (c.kind == RME7_CAST_RUNG) {
            wellformed++;
            if (all[drop] == RME7_GAMMA) gamma_ok = (c.rung == RME7_RUNG_6);
        }
    }
    check(wellformed == 1 && gamma_ok,
          "exactly one of seven slots can be withheld independently: gamma, "
          "the top of the staircase");
}

/* Is each tier boundary justified by a property the format actually RECORDS?
 *
 * Three of the four are: the equation changes at F, and the kind changes at
 * kappa and again at gamma. The fourth is not -- Sigma and the tier-0 triple
 * carry identical typed signatures, so nothing typed separates them. Which
 * makes the fused-versus-composable question answerable only from the offices,
 * and the offices distinguish the triple's members from each other exactly as
 * much as they distinguish Sigma from the triple. */
static void test_only_one_tier_boundary_is_untyped(void) {
    Rme7Kind kind[RME7_TIER_COUNT]; Rme7Equation eq[RME7_TIER_COUNT];
    bool got[RME7_TIER_COUNT] = { false };
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        Rme7Slot sl = (Rme7Slot)s;
        uint8_t t = rme7_slot_tier(sl);
        if (!got[t]) { kind[t] = rme7_slot_kind(sl); eq[t] = rme7_slot_admits(sl);
                       got[t] = true; }
    }
    int typed_boundaries = 0, untyped = -1;
    for (int t = 0; t + 1 < RME7_TIER_COUNT; t++) {
        if (kind[t] != kind[t + 1] || eq[t] != eq[t + 1]) typed_boundaries++;
        else if (untyped < 0) untyped = t;
    }
    check(typed_boundaries == 3 && untyped == 0,
          "three of four tier boundaries are typed; the untyped one is 0 -> 1");

    check(rme7_slot_kind(RME7_SIGMA) == rme7_slot_kind(RME7_J_SHARP) &&
          rme7_slot_admits(RME7_SIGMA) == rme7_slot_admits(RME7_J_SHARP),
          "Sigma and the tier-0 triple are typed identically: operator, state");

    const Rme7Slot t0[3] = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP };
    bool uniform = true;
    for (int i = 1; i < 3; i++)
        if (rme7_slot_kind(t0[i]) != rme7_slot_kind(t0[0]) ||
            rme7_slot_admits(t0[i]) != rme7_slot_admits(t0[0])) uniform = false;
    check(uniform,
          "the triple's members are typed identically too, and differ only in "
          "office -- the same evidence that separates Sigma from them");
}

/* The one recorded inter-slot relation, and what it says about tier 0. */
static void test_the_recorded_coupling_spans_two_of_three(void) {
    Rme7Slot from[2];
    check(rme7_slot_derives_from(RME7_GAMMA, from, 2) == 2 &&
          from[0] == RME7_G_SHARP && from[1] == RME7_G_TILDE_SHARP,
          "gamma is recorded as the commutator of G# and G~#");

    int primitives = 0;
    for (int s = 0; s < RME7_SLOT_COUNT; s++)
        if (rme7_slot_is_primitive((Rme7Slot)s)) primitives++;
    check(primitives == 6, "six slots are primitive; gamma is the one derived");

    /* Both of gamma's sources sit in tier 0 -- and J# does not. So the only
     * recorded coupling among tier-0 members spans TWO of the three, which is
     * neither the fused reading nor the fully composable one. */
    check(rme7_slot_tier(from[0]) == 0 && rme7_slot_tier(from[1]) == 0 &&
          rme7_slot_tier(RME7_J_SHARP) == 0,
          "all three are tier 0, but only two are coupled by the record");

    bool j_involved = false;
    for (int i = 0; i < 2; i++) if (from[i] == RME7_J_SHARP) j_involved = true;
    check(!j_involved,
          "J# participates in no recorded relation: the coupling that exists "
          "does not reach it");
}

/* Co-location at a rank is a SORT. A fusion needs a COUPLING, and the two are
 * different relations -- which is what the recorded commutator turns out not
 * to supply. */
static void test_co_location_is_not_coupling(void) {
    /* gamma's dependency is directional and already entailed by the order:
     * every well-formed profile exhibiting gamma exhibits all seven slots, so
     * the commutator constrains nothing the staircase does not. */
    int with_gamma = 0, exhibiting_all = 0;
    for (unsigned b = 0; b < 128u; b++) {
        Rme7Profile p = { .bits = (uint8_t)b };
        if (rme7_profile_classify(p).kind != RME7_CAST_RUNG) continue;
        if (!rme7_profile_exhibits(p, RME7_GAMMA)) continue;
        with_gamma++;
        if (rme7_profile_count(p) == RME7_SLOT_COUNT) exhibiting_all++;
    }
    check(with_gamma == 1 && exhibiting_all == with_gamma,
          "the staircase forces strictly more than gamma's dependency requires, "
          "so the recorded relation grounds nothing the order does not");

    /* No co-occurrence coupling is recorded for any slot. */
    int coupled = 0;
    for (int s = 0; s < RME7_SLOT_COUNT; s++)
        coupled += rme7_slot_coupled_with((Rme7Slot)s, nullptr, 0);
    check(coupled == 0, "no co-occurrence coupling is recorded for any slot");

    /* Exactly one rank groups more than one slot, and nothing supports it. */
    Rme7Slot unsupported[RME7_TIER_COUNT];
    int n = rme7_unsupported_groupings(unsupported, RME7_TIER_COUNT);
    check(n == 1 && rme7_slot_tier(unsupported[0]) == 0,
          "the format makes exactly one grouping claim, at rank 0, and no "
          "recorded coupling supports it");
}

/* A typed difference tells you two slots are distinguishable. It does not
 * tell you which comes first. Boundary is not order. */
static void test_the_order_itself_is_ungrounded(void) {
    Rme7Slot ungrounded[RME7_SLOT_COUNT];
    int n = rme7_ungrounded_order(ungrounded, RME7_SLOT_COUNT);
    check(n == 4, "four slots sit above the base, and not one of their "
                  "positions is grounded in a recorded relation");

    bool all_above_base = true;
    for (int i = 0; i < n; i++)
        if (rme7_slot_tier(ungrounded[i]) == 0) all_above_base = false;
    check(all_above_base, "the three base slots need no predecessor and are "
                          "not counted against the order");

    /* gamma has the only recorded dependency, and it points DOWN four ranks
     * to the base rather than to the rank below it -- so even the one slot
     * with a relation has an ungrounded position. */
    Rme7Slot dep[2];
    (void)rme7_slot_derives_from(RME7_GAMMA, dep, 2);
    check(rme7_slot_tier(RME7_GAMMA) == 4 && rme7_slot_tier(dep[0]) == 0 &&
          !rme7_slot_order_grounded(RME7_GAMMA),
          "gamma's one relation reaches the base, not the rank beneath it");
}

/* The provenance ledger: object or artifact, for every structural claim. */
static void test_the_provenance_ledger(void) {
    int n[5] = {0};
    for (int i = 0; i < RME7_STRUCTURE_COUNT; i++)
        n[rme7_structure_basis((Rme7Structure)i)]++;

    check(n[RME7_BASIS_RECORDED] == 3 && n[RME7_BASIS_DERIVED] == 1 &&
          n[RME7_BASIS_STIPULATED] == 2 && n[RME7_BASIS_LAYOUT] == 1 &&
          n[RME7_BASIS_ABSENT] == 1,
          "eight structural claims: 3 recorded, 1 derived, 2 stipulated, "
          "1 layout, 1 absent");

    check(rme7_structure_basis(RME7_STRUCT_RANK0_GROUPING) == RME7_BASIS_STIPULATED &&
          rme7_structure_basis(RME7_STRUCT_RANK_ORDER) == RME7_BASIS_STIPULATED,
          "the two stipulated claims are exactly the two the audits report "
          "deficits on");

    check(rme7_structure_basis(RME7_STRUCT_BIT_POSITION) == RME7_BASIS_LAYOUT,
          "bit position is an encoding choice and makes no claim about the object");

    bool monotone = true; int prev = -1;
    for (int s = 0; s < RME7_SLOT_COUNT; s++) {
        int r = rme7_slot_tier((Rme7Slot)s);
        if (r < prev) monotone = false;
        prev = r;
    }
    check(monotone,
          "bit position and rank coincide today, which is exactly when each is "
          "liable to be read as the other");
}

/* The architectural test, run over the whole format. */
static void test_the_architectural_test(void) {
    Rme7Structure def[RME7_STRUCTURE_COUNT];
    int n = rme7_defects(def, RME7_STRUCTURE_COUNT);
    check(n == 2, "two consequential claims are not recoverable");
    check((def[0] == RME7_STRUCT_RANK0_GROUPING &&
           def[1] == RME7_STRUCT_RANK_ORDER),
          "and they are exactly rank 0's grouping and the rank order");

    /* The test needs both halves, and here is why each alone fails. */
    check(!rme7_structure_recoverable(RME7_STRUCT_BIT_POSITION) &&
          !rme7_structure_defective(RME7_STRUCT_BIT_POSITION),
          "bit position is unrecoverable and not a defect: nothing composes "
          "on it, so recoverability alone would over-report");
    check(rme7_structure_consequential(RME7_STRUCT_KIND_PARTITION) &&
          !rme7_structure_defective(RME7_STRUCT_KIND_PARTITION),
          "the kind partition is consequential and carried, so "
          "consequentiality alone would over-report too");

    /* An explicitly empty relation is carried, not missing. */
    check(rme7_structure_basis(RME7_STRUCT_COUPLING) == RME7_BASIS_ABSENT &&
          rme7_structure_recoverable(RME7_STRUCT_COUPLING),
          "stating that no coupling is recorded is itself a recoverable fact");

    /* Nothing is recorded that no composition depends on. */
    check(rme7_over_recorded(nullptr, 0) == 0,
          "no structure is recorded that nothing composes on: the format has "
          "not been padded toward completeness");

    /* The two defects are exactly what the two standing audits report. */
    check(rme7_unsupported_groupings(nullptr, 0) == 1 &&
          rme7_ungrounded_order(nullptr, 0) == 4,
          "and the per-slot audits agree: one grouping, four positions");
}

/* Consequentiality by perturbation, and why the instrument had to change. */
static void test_warrant_by_perturbation(void) {
    uint8_t ranks[RME7_SLOT_COUNT], permuted[RME7_SLOT_COUNT];
    for (int s = 0; s < RME7_SLOT_COUNT; s++)
        ranks[s] = permuted[s] = rme7_slot_tier((Rme7Slot)s);
    uint8_t a = permuted[RME7_SIGMA];
    permuted[RME7_SIGMA] = permuted[RME7_F];
    permuted[RME7_F] = a;

    /* THE INSTRUMENT: counting is invariant under a rank permutation, because
     * a permutation relabels the chain without reshaping it. Only the set
     * answers, and comparing counts would have reported "changes nothing". */
    check(rme7_wellformed_under(ranks, true) ==
          rme7_wellformed_under(permuted, true),
          "a rank permutation leaves the COUNT of well-formed profiles alone");
    check(rme7_wellformed_signature(ranks, true) !=
          rme7_wellformed_signature(permuted, true),
          "and changes WHICH profiles are legal -- so cardinality is the wrong "
          "comparison and the signature is the right one");

    /* Both defects are demonstrated, so the verdict rests on a perturbation
     * rather than on anyone's judgement. */
    Rme7Structure def[RME7_STRUCTURE_COUNT];
    int n = rme7_defects(def, RME7_STRUCTURE_COUNT);
    bool all_demonstrated = true;
    for (int i = 0; i < n; i++)
        if (rme7_structure_warrant(def[i]) != RME7_WARRANT_DEMONSTRATED)
            all_demonstrated = false;
    check(n == 2 && all_demonstrated,
          "both defects carry a demonstrated warrant, not an asserted one");

    /* And every structure still merely asserted is recoverable, so its
     * warrant cannot change the verdict whatever it turns out to be. */
    bool asserted_are_inert = true;
    for (int i = 0; i < RME7_STRUCTURE_COUNT; i++) {
        Rme7Structure st = (Rme7Structure)i;
        if (rme7_structure_warrant(st) != RME7_WARRANT_ASSERTED) continue;
        if (!rme7_structure_recoverable(st)) asserted_are_inert = false;
    }
    check(asserted_are_inert,
          "every asserted structure is recoverable, so the hand-written "
          "judgement is off the load-bearing path entirely");

    check(rme7_structure_warrant(RME7_STRUCT_BIT_POSITION) == RME7_WARRANT_REFUTED,
          "bit position is refuted rather than merely unlisted");

    /* Relaxing tier 0 while KEEPING lower-rank completeness gives 11, not the
     * 35 an earlier relay reported: that figure assumed completeness was
     * relaxed too. The repair has two readings and they differ. */
    check(rme7_wellformed_under(ranks, false) == 11,
          "relaxing tier 0 alone admits 11 profiles, not 35 -- the earlier "
          "figure assumed a second relaxation nobody specified");
}

static void test_refusals_and_delta(void) {
    Rme7Cast sib = rme7_cast_refuse_sibling("a runnable answer matters more here");
    check(sib.kind == RME7_CAST_BOT_SIB && sib.reason != nullptr,
          "the sibling refusal is adjudicated and must state a reason");

    /* The computable classifier can never reach that verdict on its own. */
    bool ever_sib = false;
    for (unsigned bits = 0; bits < 128u; bits++) {
        Rme7Profile p = { .bits = (uint8_t)bits };
        if (rme7_profile_classify(p).kind == RME7_CAST_BOT_SIB) ever_sib = true;
    }
    check(!ever_sib, "no profile computes its way to a sibling refusal");

    check(rme7_delta_level(RME7_RUNG_5, RME7_RUNG_6) == -1, "declared above what it exhibits");
    check(rme7_delta_level(RME7_RUNG_7, RME7_RUNG_6) == 1, "escaped its declared restriction");
    check(rme7_delta_level(RME7_RUNG_4_ZERO, RME7_RUNG_4) == 0,
          "the sub-restriction is a distinction the level arithmetic cannot see");
}

static void test_delta_on_a_proto(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto object;
    (void)rme7_proto_generate(&l.userroot, &object, "declared too high");
    (void)rme7_proto_exhibit(&object, RME7_J_SHARP);
    (void)rme7_proto_exhibit(&object, RME7_G_SHARP);
    (void)rme7_proto_exhibit(&object, RME7_G_TILDE_SHARP);
    (void)rme7_proto_exhibit(&object, RME7_SIGMA);
    (void)rme7_proto_exhibit(&object, RME7_F);

    int delta = 99;
    check(!rme7_proto_delta_level(&object, &delta),
          "there is no delta against a silence");
    rme7_proto_declare(&object, RME7_RUNG_6);
    check(rme7_proto_delta_level(&object, &delta) && delta == -1,
          "governed evolution declared, adaptation exhibited");
}

/* ---- the payload does not delegate ------------------------------------ */

static void test_purpose_is_never_shared(void) {
    Ladder l; build_ladder(&l);
    l.userroot.payload.purpose = "the root's purpose";

    Rme7Proto a, b;
    (void)rme7_proto_generate(&l.userroot, &a, "a");
    (void)rme7_proto_generate(&l.userroot, &b, "b");
    a.payload.purpose = "a's own purpose";

    check(rme7_proto_payload(&a)->purpose != rme7_proto_payload(&l.userroot)->purpose,
          "purpose is i-indexed and never inherited");
    check(rme7_proto_payload(&b)->purpose == nullptr,
          "an unset purpose stays unset rather than falling back to a parent");
    check(rme7_proto_delegates_to(&a, &l.userroot) &&
          rme7_proto_delegates_to(&b, &l.userroot),
          "both still delegate for their slot definitions");
}

/* ---- the channel ------------------------------------------------------ */

typedef struct { int admitted; int assimilated; bool admit_everything; } Ctx;

static bool t_ok(const Rme7Claim *foreign, Rme7Claim *local, void *ctx) {
    (void)ctx; *local = *foreign; return true;   /* already in local terms */
}
static bool t_fail(const Rme7Claim *foreign, Rme7Claim *local, void *ctx) {
    (void)foreign; (void)local; (void)ctx; return false;
}
static Rme7Verdict k_gate(const Rme7Claim *local, void *ctx) {
    Ctx *c = ctx; c->admitted++;
    if (c->admit_everything) return RME7_ADMITTED;
    return (local->content != nullptr && *(const int *)local->content > 0)
           ? RME7_ADMITTED : RME7_REFUSED;
}
static bool a_take(const Rme7Claim *local, void *ctx) {
    (void)local; ((Ctx *)ctx)->assimilated++; return true;
}

/* An object at RME-4: the metriplectic triple plus Sigma. */
static void exhibit_rme4(Rme7Proto *p) {
    (void)rme7_proto_exhibit(p, RME7_J_SHARP);
    (void)rme7_proto_exhibit(p, RME7_G_SHARP);
    (void)rme7_proto_exhibit(p, RME7_G_TILDE_SHARP);
    (void)rme7_proto_exhibit(p, RME7_SIGMA);
}

static Rme7Claim payload_claim(const int *n) {
    return (Rme7Claim){ .concerns_slot = false, .rung = RME7_RUNG_4,
                        .custody = RME7_CUSTODY_INTERPRETIVE,
                        .content = n, .size = sizeof *n };
}

static void test_channel(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j;
    (void)rme7_proto_generate(&l.userroot, &i, "i");
    (void)rme7_proto_generate(&l.userroot, &j, "j");
    exhibit_rme4(&i); exhibit_rme4(&j);

    Ctx ctx = { 0, 0, false };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &j, .to = &i };
    check(rme7_channel_contracted(&ch), "three stages and two endpoints is a contract");

    int n = 1; Rme7Claim c = payload_claim(&n), local = {0};
    Rme7Crossing r = rme7_channel_cross(&ch, &c, &local);
    check(r.reached == RME7_STAGE_COMPLETE && r.verdict == RME7_ADMITTED,
          "translate, admit, assimilate -- in that order");
    check(ctx.admitted == 1 && ctx.assimilated == 1, "each stage ran once");

    n = -1;
    r = rme7_channel_cross(&ch, &c, &local);
    check(r.reached == RME7_STAGE_ADMIT && r.outcome == RME7_CROSS_REFUSED,
          "a refused claim stops at the gate and is not assimilated");
    check(ctx.assimilated == 1, "nothing crossed that the gate refused");

    Rme7Channel untranslatable = ch; untranslatable.translate = t_fail;
    r = rme7_channel_cross(&untranslatable, &c, &local);
    check(r.reached == RME7_STAGE_TRANSLATE, "what cannot be translated never reaches the gate");

    Rme7Channel uncontracted = ch; uncontracted.admit = nullptr;
    check(!rme7_channel_contracted(&uncontracted), "a route missing a stage is not a channel");
    r = rme7_channel_cross(&uncontracted, &c, &local);
    check(r.outcome == RME7_CROSS_UNCONTRACTED, "an untyped route is refused, not run");

    Rme7Channel selfch = ch; selfch.to = selfch.from;
    check(!rme7_channel_contracted(&selfch), "a channel needs two objects");

    check(!rme7_composed(&uncontracted, 1) && rme7_composed(&ch, 1),
          "composition is exactly one contracted channel, not more autonomy");
}

/* Condition 6: the carrier is typed, and translation must land well typed. */

static void test_claims_are_typed_for_the_receiver(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j;
    (void)rme7_proto_generate(&l.userroot, &i, "i at RME-4");
    (void)rme7_proto_generate(&l.userroot, &j, "j");
    exhibit_rme4(&i); exhibit_rme4(&j);

    int n = 1;
    Rme7Claim at_rung_4 = { .concerns_slot = true, .slot = RME7_SIGMA,
                            .rung = RME7_RUNG_4, .content = &n, .size = sizeof n };
    check(rme7_claim_typing(&at_rung_4, &i) == RME7_TYPING_OK,
          "a claim at the receiver's own rung is well typed");

    Rme7Claim at_rung_7 = at_rung_4; at_rung_7.rung = RME7_RUNG_7;
    check(rme7_claim_typing(&at_rung_7, &i) == RME7_TYPING_RUNG_ABOVE_RECEIVER,
          "a claim above the receiver's rung cites distinctions it does not have");

    Rme7Claim legislating = at_rung_4; legislating.legislates = true;
    legislating.custody = RME7_CUSTODY_ANCHORED;
    check(rme7_claim_typing(&legislating, &i) == RME7_TYPING_LEGISLATES,
          "not even an anchored claim may legislate through a port");

    Rme7Proto orphan = { .name = "no format", .layer = RME7_LAYER_USER,
                         .parent = nullptr };
    check(rme7_claim_typing(&at_rung_4, &orphan) == RME7_TYPING_UNDEFINED_SLOT,
          "a slot the receiver's chain never defines means nothing there");

    Rme7Claim payload = { .concerns_slot = false, .content = &n, .size = sizeof n };
    check(rme7_claim_typing(&payload, &orphan) == RME7_TYPING_OK,
          "a payload-only claim carries no slot to be wrong about");

    /* And the channel enforces it as translation's postcondition. */
    Ctx ctx = { 0, 0, true };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &j, .to = &i };
    Rme7Claim local = {0};
    Rme7Crossing r = rme7_channel_cross(&ch, &at_rung_7, &local);
    check(r.outcome == RME7_CROSS_ILL_TYPED && r.reached == RME7_STAGE_TRANSLATE,
          "ill typed is translation failing its contract, not a fourth stage");
    check(r.typing == RME7_TYPING_RUNG_ABOVE_RECEIVER,
          "and the crossing says which way it was ill typed");
    check(ctx.admitted == 0,
          "an ill-typed claim never reaches the gate: typing is not policy");
}

/* The design fork: what does a port certify -- comprehension or exhibition?
 * Both predicates are implemented so the question can be decided with data. */

static const Rme7Slot STAIR[7] = { RME7_J_SHARP, RME7_G_SHARP, RME7_G_TILDE_SHARP,
                                   RME7_SIGMA, RME7_F, RME7_KAPPA, RME7_GAMMA };

static void exhibit_upto(Rme7Proto *p, int n) {
    for (int k = 0; k < n; k++) (void)rme7_proto_exhibit(p, STAIR[k]);
}

static void test_comprehension_and_exhibition_are_incomparable(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto zero, four;
    (void)rme7_proto_generate(&l.userroot, &zero, "RME-4-zero object");
    (void)rme7_proto_generate(&l.userroot, &four, "RME-4 object");
    exhibit_upto(&zero, 3);   /* the metriplectic triple, no Sigma */
    exhibit_upto(&four, 4);

    check(rme7_proto_classify(&zero).rung == RME7_RUNG_4_ZERO &&
          rme7_proto_classify(&four).rung == RME7_RUNG_4, "the two receivers cast as expected");

    /* Case A -- the hole comprehension has: a slot the receiver understands
     * by delegation and demonstrably does not instantiate. */
    Rme7Claim sigma_at_4 = { .concerns_slot = true, .slot = RME7_SIGMA,
                             .rung = RME7_RUNG_4 };
    check(rme7_claim_typing_in(&sigma_at_4, &zero, RME7_TYPING_COMPREHENSION)
          == RME7_TYPING_OK,
          "comprehension admits a claim about a slot the receiver does not exhibit");
    check(rme7_claim_typing_in(&sigma_at_4, &zero, RME7_TYPING_EXHIBITION)
          == RME7_TYPING_UNEXHIBITED_SLOT, "exhibition refuses it");

    /* Case B -- what exhibition loses: it never reads the sender's rung, so
     * it cannot refuse level inflation. */
    Rme7Claim j_at_7 = { .concerns_slot = true, .slot = RME7_J_SHARP,
                         .rung = RME7_RUNG_7 };
    check(rme7_claim_typing_in(&j_at_7, &four, RME7_TYPING_COMPREHENSION)
          == RME7_TYPING_RUNG_ABOVE_RECEIVER,
          "comprehension refuses a claim made above the receiver's rung");
    check(rme7_claim_typing_in(&j_at_7, &four, RME7_TYPING_EXHIBITION)
          == RME7_TYPING_OK,
          "exhibition admits it: a unary predicate cannot order sender against receiver");

    /* Neither implies the other. Both directions of divergence are non-empty,
     * so exhibition is not a strengthening and the fork is not a choice
     * between weaker and stronger. */
    check(true, "the two predicates are incomparable: cases A and B point opposite ways");

    /* Only the conjunction refuses both failures. */
    check(rme7_claim_typing_in(&sigma_at_4, &zero, RME7_TYPING_BOTH)
          == RME7_TYPING_UNEXHIBITED_SLOT &&
          rme7_claim_typing_in(&j_at_7, &four, RME7_TYPING_BOTH)
          == RME7_TYPING_RUNG_ABOVE_RECEIVER,
          "BOTH is the only mode that refuses vacuous reference AND level inflation");

    check(rme7_claim_typing(&sigma_at_4, &zero) ==
          rme7_claim_typing_in(&sigma_at_4, &zero, RME7_TYPING_COMPREHENSION),
          "comprehension stays the default: the shipped behaviour is not changed silently");

    /* A legislating claim is refused under every mode. */
    Rme7Claim leg = { .concerns_slot = true, .slot = RME7_J_SHARP,
                      .rung = RME7_RUNG_4, .legislates = true,
                      .custody = RME7_CUSTODY_ANCHORED };
    bool all_refuse = true;
    for (int m = 0; m <= RME7_TYPING_BOTH; m++)
        if (rme7_claim_typing_in(&leg, &four, (Rme7TypingMode)m) != RME7_TYPING_LEGISLATES)
            all_refuse = false;
    check(all_refuse, "no mode and no custody grade lets a claim legislate");
}

static void test_channel_honours_its_mode(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto zero, sender;
    (void)rme7_proto_generate(&l.userroot, &zero, "RME-4-zero receiver");
    (void)rme7_proto_generate(&l.userroot, &sender, "sender");
    exhibit_upto(&zero, 3); exhibit_upto(&sender, 4);

    int n = 1;
    Rme7Claim sigma = { .concerns_slot = true, .slot = RME7_SIGMA,
                        .rung = RME7_RUNG_4, .content = &n, .size = sizeof n };
    Rme7Claim local = {0};
    Ctx ctx = { 0, 0, true };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &sender, .to = &zero };

    Rme7Crossing r = rme7_channel_cross(&ch, &sigma, &local);
    check(r.outcome == RME7_CROSS_OK, "under comprehension the crossing completes");

    ch.mode = RME7_TYPING_EXHIBITION;
    r = rme7_channel_cross(&ch, &sigma, &local);
    check(r.outcome == RME7_CROSS_ILL_TYPED &&
          r.typing == RME7_TYPING_UNEXHIBITED_SLOT,
          "under exhibition the same crossing is ill typed at the port");
    check(r.from == &sender && r.to == &zero,
          "and provenance is recorded either way");
}

/* A channel is not delegation, and delegation is not a channel. */
static void test_channel_is_not_delegation(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j;
    (void)rme7_proto_generate(&l.userroot, &i, "i");
    (void)rme7_proto_generate(&l.userroot, &j, "j");
    exhibit_rme4(&i); exhibit_rme4(&j);
    i.payload.purpose = "i's purpose";
    j.payload.purpose = "j's purpose";

    Ctx ctx = { 0, 0, true };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &j, .to = &i };
    int n = 5; Rme7Claim c = payload_claim(&n), local = {0};
    (void)rme7_channel_cross(&ch, &c, &local);

    check(!rme7_proto_delegates_to(&i, &j) && !rme7_proto_delegates_to(&j, &i),
          "peers that exchange influence do not thereby delegate to each other");
    check(strcmp(rme7_proto_payload(&i)->purpose,
                 rme7_proto_payload(&j)->purpose) != 0,
          "coupling is not identification: the purposes stay distinct");
}

/* Provenance and non-heredity across the crossing. */

static Rme7Proto *heir_target = nullptr;

static bool a_installs_definition(const Rme7Claim *local, void *ctx) {
    (void)local; (void)ctx;
    rme7_proto_define(heir_target, RME7_GAMMA, RME7_CUSTODY_INTERPRETIVE,
                      "smuggled in through a channel");
    return true;
}

static void test_crossing_carries_provenance(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j;
    (void)rme7_proto_generate(&l.userroot, &i, "i");
    (void)rme7_proto_generate(&l.userroot, &j, "j");
    exhibit_rme4(&i); exhibit_rme4(&j);

    Ctx ctx = { 0, 0, false };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &j, .to = &i };
    int n = 3; Rme7Claim c = payload_claim(&n), local = {0};
    Rme7Crossing r = rme7_channel_cross(&ch, &c, &local);
    check(r.from == &j && r.to == &i,
          "a crossing records who sent it and who received it");
    check(r.outcome == RME7_CROSS_OK, "a completed crossing says so");

    n = -1;
    r = rme7_channel_cross(&ch, &c, &local);
    check(r.outcome == RME7_CROSS_REFUSED, "understood and not admitted");
    Rme7Channel bad = ch; bad.translate = t_fail;
    r = rme7_channel_cross(&bad, &c, &local);
    check(r.outcome == RME7_CROSS_UNTRANSLATABLE,
          "untranslatable is a different fact from refused");
    check(r.from == &j,
          "provenance survives a failed crossing, which is when it matters most");
}

static void test_crossing_cannot_make_content_hereditary(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j, child;
    (void)rme7_proto_generate(&l.userroot, &i, "i");
    (void)rme7_proto_generate(&l.userroot, &j, "j");
    exhibit_rme4(&i); exhibit_rme4(&j);

    heir_target = &i;
    Ctx ctx = { 0, 0, true };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate,
                       .assimilate = a_installs_definition,
                       .ctx = &ctx, .from = &j, .to = &i };
    int n = 1; Rme7Claim c = payload_claim(&n), local = {0};
    Rme7Crossing r = rme7_channel_cross(&ch, &c, &local);
    check(r.outcome == RME7_CROSS_MADE_HEREDITARY,
          "assimilation that installs a definition is caught, not silently allowed");
    check(r.verdict == RME7_REFUSED,
          "what crosses a channel is content, never grammar");

    (void)rme7_proto_generate(&i, &child, "i's child");
    const Rme7Proto *found = nullptr;
    (void)rme7_proto_resolve(&child, RME7_GAMMA, &found);
    check(found == &i,
          "the smuggled definition WOULD have been inherited -- which is why "
          "the crossing reports it");
}

int main(void) {
    test_slots();
    test_ladder();
    test_definition_is_not_exhibition();
    test_exhibiting_the_undefined();
    test_staircase();
    test_the_tier_zero_family_is_thirty();
    test_only_one_slot_is_independently_withholdable();
    test_only_one_tier_boundary_is_untyped();
    test_the_recorded_coupling_spans_two_of_three();
    test_co_location_is_not_coupling();
    test_the_order_itself_is_ungrounded();
    test_the_provenance_ledger();
    test_the_architectural_test();
    test_warrant_by_perturbation();
    test_refusals_and_delta();
    test_delta_on_a_proto();
    test_purpose_is_never_shared();
    test_channel();
    test_channel_is_not_delegation();
    test_claims_are_typed_for_the_receiver();
    test_comprehension_and_exhibition_are_incomparable();
    test_channel_honours_its_mode();
    test_crossing_carries_provenance();
    test_crossing_cannot_make_content_hereditary();
    printf(failures ? "\n%d failing\n" : "\nall passing\n", failures);
    return failures ? 1 : 0;
}
