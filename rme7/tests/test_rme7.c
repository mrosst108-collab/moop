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

static bool t_ok(const void *claim, void *into, void *ctx) {
    (void)ctx; *(int *)into = *(const int *)claim; return true;
}
static bool t_fail(const void *claim, void *into, void *ctx) {
    (void)claim; (void)into; (void)ctx; return false;
}
static Rme7Verdict k_gate(const void *translated, void *ctx) {
    Ctx *c = ctx; c->admitted++;
    return (c->admit_everything || *(const int *)translated > 0)
           ? RME7_ADMITTED : RME7_REFUSED;
}
static bool a_take(const void *translated, void *ctx) {
    (void)translated; ((Ctx *)ctx)->assimilated++; return true;
}

static void test_channel(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j;
    (void)rme7_proto_generate(&l.userroot, &i, "i");
    (void)rme7_proto_generate(&l.userroot, &j, "j");

    Ctx ctx = { 0, 0, false };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &j, .to = &i };
    check(rme7_channel_contracted(&ch), "three stages and two endpoints is a contract");

    int claim = 1, into = 0;
    Rme7Crossing r = rme7_channel_cross(&ch, &claim, &into);
    check(r.reached == RME7_STAGE_COMPLETE && r.verdict == RME7_ADMITTED,
          "translate, admit, assimilate -- in that order");
    check(ctx.admitted == 1 && ctx.assimilated == 1, "each stage ran once");

    claim = -1;
    r = rme7_channel_cross(&ch, &claim, &into);
    check(r.reached == RME7_STAGE_ADMIT && r.verdict == RME7_REFUSED,
          "a refused claim stops at the gate and is not assimilated");
    check(ctx.assimilated == 1, "nothing crossed that the gate refused");

    Rme7Channel untranslatable = ch; untranslatable.translate = t_fail;
    r = rme7_channel_cross(&untranslatable, &claim, &into);
    check(r.reached == RME7_STAGE_TRANSLATE, "what cannot be translated never reaches the gate");

    Rme7Channel uncontracted = ch; uncontracted.admit = nullptr;
    check(!rme7_channel_contracted(&uncontracted), "a route missing a stage is not a channel");
    r = rme7_channel_cross(&uncontracted, &claim, &into);
    check(r.verdict == RME7_REFUSED, "an untyped route is refused, not run");

    Rme7Channel selfch = ch; selfch.to = selfch.from;
    check(!rme7_channel_contracted(&selfch), "a channel needs two objects");

    check(!rme7_composed(&uncontracted, 1) && rme7_composed(&ch, 1),
          "composition is exactly one contracted channel, not more autonomy");
}

/* A channel is not delegation, and delegation is not a channel. */
static void test_channel_is_not_delegation(void) {
    Ladder l; build_ladder(&l);
    Rme7Proto i, j;
    (void)rme7_proto_generate(&l.userroot, &i, "i");
    (void)rme7_proto_generate(&l.userroot, &j, "j");
    i.payload.purpose = "i's purpose";
    j.payload.purpose = "j's purpose";

    Ctx ctx = { 0, 0, true };
    Rme7Channel ch = { .translate = t_ok, .admit = k_gate, .assimilate = a_take,
                       .ctx = &ctx, .from = &j, .to = &i };
    int claim = 5, into = 0;
    (void)rme7_channel_cross(&ch, &claim, &into);

    check(!rme7_proto_delegates_to(&i, &j) && !rme7_proto_delegates_to(&j, &i),
          "peers that exchange influence do not thereby delegate to each other");
    check(strcmp(rme7_proto_payload(&i)->purpose,
                 rme7_proto_payload(&j)->purpose) != 0,
          "coupling is not identification: the purposes stay distinct");
}

int main(void) {
    test_slots();
    test_ladder();
    test_definition_is_not_exhibition();
    test_exhibiting_the_undefined();
    test_staircase();
    test_refusals_and_delta();
    test_delta_on_a_proto();
    test_purpose_is_never_shared();
    test_channel();
    test_channel_is_not_delegation();
    printf(failures ? "\n%d failing\n" : "\nall passing\n", failures);
    return failures ? 1 : 0;
}
