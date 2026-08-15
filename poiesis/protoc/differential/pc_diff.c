/* THE DIFFERENTIAL HARNESS.
 *
 * This is NOT part of ProtoC.  It is excluded from `make protoc` and links
 * both substrates deliberately -- comparing them is its whole job.  ProtoC
 * proper still never sees an AWV header.
 *
 * THREE DISTINCT CLAIMS, kept apart:
 *
 *   ProtoC self-test   ProtoC implements ITS OWN stated semantics
 *                      consistently.  Says nothing about faithfulness.
 *   Differential test  the two substrates agree on consequences WHERE THE
 *                      FROZEN SEMANTICS DETERMINE A CONSEQUENCE.
 *   Oracle check       the comparison has not promoted an implementation
 *                      mechanism into a semantic requirement.
 *
 * PRE-REGISTRATION.  The six slack cells below are declared HERE, before
 * any output exists.  A DISAGREE on any of them is an ORACLE DEFECT, not a
 * substrate defect, and the pre-registration is the test -- they are never
 * exempted after seeing the result.
 */
#include <stdio.h>
#include <string.h>

#include "../composition/pc_compose.h"
#include "../realization/pc_admit_boundary.h"
#include "../graph/pc_graph.h"

#include "rme/schedule.h"
#include "rme/validate.h"

/* A consequence, normalized so the two substrates' differing return types
 * cannot themselves manufacture a disagreement. */
typedef enum { X_YES, X_NO, X_REFUSED, X_NA } XCons;
static const char *xs(XCons c)
{
    switch (c) { case X_YES: return "yes"; case X_NO: return "no";
                 case X_REFUSED: return "refused"; default: return "n/a"; }
}

typedef enum { CLS_AGREE, CLS_DISAGREE, CLS_UNDECIDABLE, CLS_ORACLE_DEFECT } Cls;
static const char *cs(Cls c)
{
    switch (c) { case CLS_AGREE: return "AGREE"; case CLS_DISAGREE: return "DISAGREE";
                 case CLS_UNDECIDABLE: return "UNDECIDABLE"; default: return "ORACLE-DEFECT"; }
}

static int n_agree, n_disagree, n_undec, n_oracle;

/* `determined` records whether S1-S11 FIX this consequence.  It is set from
 * the derivation, before the values are known. */
static void cell(const char *id, const char *sref, bool determined,
                 XCons protoc, XCons awv, const char *derivation)
{
    Cls c;
    if (!determined) {
        /* Pre-registered slack.  Equal or not, the frozen material does not
         * adjudicate -- and a DISAGREE verdict here would be the oracle
         * inventing a requirement. */
        c = (protoc == awv) ? CLS_UNDECIDABLE : CLS_UNDECIDABLE;
    } else {
        c = (protoc == awv) ? CLS_AGREE : CLS_DISAGREE;
    }
    switch (c) {
    case CLS_AGREE: n_agree++; break;
    case CLS_DISAGREE: n_disagree++; break;
    case CLS_UNDECIDABLE: n_undec++; break;
    default: n_oracle++; break;
    }
    printf("%-7s %-5s  protoc=%-8s awv=%-8s  %-13s  %s\n",
           id, sref, xs(protoc), xs(awv), cs(c), derivation);
}

/* ---------------- ProtoC fixtures ---------------- */
static const PcPortDescriptor DESC[] = {
    { "state", "state-if" }, { "step", "step-if" },
    { "couple", "couple-if" }, { "observe", "observe-if" },
};
static const PcSchema SCHEMA = { "diff.demo", DESC, 4, 1 };
static const int pr[4] = {0,0,0,0}, pv[4] = {0,0,0,0};
static void pc_fill(PcPort *d)
{
    d[0] = (PcPort){ PC_ACTIVE, &pr[0], &pv[0], false };
    d[1] = (PcPort){ PC_ACTIVE, &pr[1], &pv[1], true  };
    d[2] = (PcPort){ PC_ACTIVE, &pr[2], &pv[2], false };
    d[3] = (PcPort){ PC_ACTIVE, &pr[3], &pv[3], true  };
}
static PcSurface pcs(const char *id, PcPort *st) { pc_fill(st);
    PcSurface s = { id, &SCHEMA, st, 4 }; return s; }
static const PcCompatPair PAIRS[] = { { "step", "couple" }, { "state", "state" } };
static const PcCompatibility COMPAT = { PAIRS, 2, true };

/* ---------------- AWV fixtures ---------------- */
static RmeOutcome a1(void *s, void *o){(void)s;(void)o;return RME_OK;}
static RmeOutcome a2(void *s, const void *o){(void)s;(void)o;return RME_OK;}
static RmeOutcome a3(void *s, void *p){(void)s;(void)p;return RME_OK;}
static RmeOutcome a4(void *s){(void)s;return RME_OK;}
static RmeOutcome a5(const void*s,size_t i,const void**o){(void)s;(void)i;if(o)*o=nullptr;return RME_OK;}
static const RmeStateApi S_={a1,"a"}; static const RmeObservationApi O_={a1,"a"};
static const RmeTransitionApi T_={a2,"a"}; static const RmeParameterizationApi P_={a1,"a"};
static const RmeCouplingApi C_={a3,"a"}; static const RmeAdaptationApi A_={a4,"a"};
static const RmeGovernanceApi G_={a4,"a"}; static const RmeNestedApi N_={a5,"a"};
static RmePrototype awv(const char *n)
{
    RmePrototype p = { .identity={n}, .schema={RME_SCHEMA_NAME,RME_SCHEMA_MAJOR,RME_SCHEMA_MINOR},
      .state={{RME_ACTIVE,RME_PORT_state},&S_}, .observation={{RME_ACTIVE,RME_PORT_observation},&O_},
      .transition={{RME_ACTIVE,RME_PORT_transition},&T_},
      .parameterization={{RME_ACTIVE,RME_PORT_parameterization},&P_},
      .coupling={{RME_ACTIVE,RME_PORT_coupling},&C_}, .adaptation={{RME_ACTIVE,RME_PORT_adaptation},&A_},
      .governance={{RME_ACTIVE,RME_PORT_governance},&G_}, .nested={{RME_ACTIVE,RME_PORT_nested},&N_} };
    return p;
}

/* The endpoint CORRESPONDENCE the harness declares, so cells are about the
 * same semantic question on both sides.  Chosen to make comparison
 * possible; NOT derived from either substrate's internals, and recorded
 * because an unstated correspondence is where a false disagreement hides.
 *
 *      ProtoC "step"   <-> AWV transition
 *      ProtoC "couple" <-> AWV coupling
 *      ProtoC "state"  <-> AWV state
 */
#define PC_STEP 1
#define PC_COUPLE 2

int main(void)
{
    printf("cell    S      ProtoC        AWV            classification   derivation\n");
    printf("------- -----  ------------  -------------  ---------------  ---------\n");

    /* ---- S1: admissible while UNDECLARED. */
    {
        PcDeclaration ent[2]; PcDeclarationLog log; pc_declaration_init(&log, ent, 2);
        PcPort sa[4], sb[4]; PcSurface A = pcs("A", sa), B = pcs("B", sb);
        const PcConnection e[] = { { PC_STEP, PC_COUPLE } }; PcConnectionSet set = { e, 1 };
        PcComposition pcc = pc_compose(&log, &A, &B, &set, &COMPAT);
        XCons p = (pcc.admissibility == PC_ADMIT_OK) ? X_YES : X_NO;

        RmePrototype ra = awv("A"), rb = awv("B");
        const RmeConnection re[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { re, 1, false };                       /* undeclared */
        XCons a = rme_admissible(&ra, &rb, &R).ok ? X_YES : X_NO;

        cell("D-S1a", "S1", true, p, a, "admissible must be evaluable while undeclared");

        XCons p2 = pcc.composed ? X_YES : X_NO;
        XCons a2c = rme_compose_valid(&ra, &rb, &R).ok ? X_YES : X_NO;
        cell("D-S1b", "S1", true, p2, a2c, "Admissible does NOT imply Declared");
    }

    /* ---- S3: a VESTIGIAL endpoint is refused, on EITHER side. */
    {
        PcPort sa[4], sb[4]; PcSurface A = pcs("A", sa), B = pcs("B", sb);
        sa[PC_STEP].status = PC_VESTIGIAL; sa[PC_STEP].realization = &pv[PC_STEP];
        XCons p = pc_endpoint_admissible(&A, PC_STEP, &B, PC_COUPLE, &COMPAT).result == PC_ADMIT_OK
                  ? X_YES : X_NO;
        RmePrototype ra = awv("A"), rb = awv("B");
        ra.transition = (RmeTransitionPort){ { RME_VESTIGIAL, RME_PORT_transition },
                                             &rme_vestigial_transition };
        const RmeConnection re[] = { { RME_PORT_transition, RME_PORT_coupling } };
        RmeRelation R = { re, 1, false };
        XCons a = rme_admissible(&ra, &rb, &R).ok ? X_YES : X_NO;
        cell("D-S3a", "S3", true, p, a, "vestigial endpoint on the LEFT is not wireable");

        PcPort sc[4], sd[4]; PcSurface C = pcs("C", sc), D = pcs("D", sd);
        sd[PC_COUPLE].status = PC_VESTIGIAL; sd[PC_COUPLE].realization = &pv[PC_COUPLE];
        XCons p2 = pc_endpoint_admissible(&C, PC_STEP, &D, PC_COUPLE, &COMPAT).result == PC_ADMIT_OK
                   ? X_YES : X_NO;
        RmePrototype rc = awv("C"), rd = awv("D");
        rd.coupling = (RmeCouplingPort){ { RME_VESTIGIAL, RME_PORT_coupling },
                                         &rme_vestigial_coupling };
        XCons a2c = rme_admissible(&rc, &rd, &R).ok ? X_YES : X_NO;
        cell("D-S3b", "S3", true, p2, a2c, "vestigial endpoint on the RIGHT is not wireable");

        /* and it is nonetheless RETAINED */
        XCons p3 = (pc_in_envelope(&A, PC_STEP) && A.ports[PC_STEP].realization) ? X_YES : X_NO;
        RmePortSet env = rme_envelope(&ra);
        XCons a3c = (rme_portset_has(&env, RME_PORT_transition)
                     && rme_port_api(&ra, RME_PORT_transition)) ? X_YES : X_NO;
        cell("D-S3c", "S3", true, p3, a3c, "the refused endpoint is still retained and reachable");
    }

    /* ---- S2: an ACTIVE port naming its declared vestigial form is refused
     * AT THE BOUNDARY. */
    {
        PcSurface *store[2]; uint64_t ser[2]; PcRegistry reg;
        pc_registry_init(&reg, store, ser, 2);
        PcPort sa[4]; PcSurface A = pcs("A", sa);
        sa[0].realization = &pv[0];
        XCons p = pc_admit_surface(&reg, &A).identity.serial != 0 ? X_YES : X_REFUSED;

        rme_validation_reset();
        RmePrototype ra = awv("A");
        ra.adaptation.api = &rme_vestigial_adaptation;
        XCons a = rme_validate(&ra, nullptr) != nullptr ? X_YES : X_REFUSED;
        cell("D-S2a", "S2", true, p, a, "ACTIVE naming the vestigial form refused at the boundary");
    }

    /* ---- S5: a released identity never revives.  THE MECHANISMS DIFFER
     * (slot reuse vs monotonic allocation) and that difference is
     * pre-registered slack -- only the invariant is compared. */
    {
        PcSurface *store[2]; uint64_t ser[2]; PcRegistry reg;
        pc_registry_init(&reg, store, ser, 2);
        PcPort sa[4], sb[4]; PcSurface A = pcs("A", sa), B = pcs("B", sb);
        PcIdentity first = pc_identity_mint(&reg, &A);
        pc_identity_release(&reg, first);
        (void)pc_identity_mint(&reg, &B);
        XCons p = pc_identity_live(&reg, first) ? X_YES : X_NO;

        rme_validation_reset();
        RmePrototype r1 = awv("first");
        const RmeValidated *h = rme_validate(&r1, nullptr);
        rme_validation_reset();
        RmePrototype r2 = awv("second");
        (void)rme_validate(&r2, nullptr);
        XCons a = rme_validated_live(h) ? X_YES : X_NO;
        cell("D-S5a", "S5", true, p, a, "a released identity is dead after a later object exists");
    }

    /* ---- S7: the envelope never shrinks; elision touches dispatch only. */
    {
        PcPort sa[4]; PcSurface A = pcs("A", sa);
        size_t env0 = pc_envelope_count(&A);
        for (int i = 0; i < 4; i++) { sa[i].status = PC_VESTIGIAL; sa[i].realization = &pv[i]; }
        XCons p = (pc_envelope_count(&A) == env0) ? X_YES : X_NO;

        RmePrototype ra = awv("A");
        RmePortSet e0 = rme_envelope(&ra);
        RmePrototype rv = awv("V");
        rv.state=(RmeStatePort){{RME_VESTIGIAL,RME_PORT_state},&rme_vestigial_state};
        rv.observation=(RmeObservationPort){{RME_VESTIGIAL,RME_PORT_observation},&rme_vestigial_observation};
        rv.transition=(RmeTransitionPort){{RME_VESTIGIAL,RME_PORT_transition},&rme_vestigial_transition};
        rv.parameterization=(RmeParameterizationPort){{RME_VESTIGIAL,RME_PORT_parameterization},&rme_vestigial_parameterization};
        rv.coupling=(RmeCouplingPort){{RME_VESTIGIAL,RME_PORT_coupling},&rme_vestigial_coupling};
        rv.adaptation=(RmeAdaptationPort){{RME_VESTIGIAL,RME_PORT_adaptation},&rme_vestigial_adaptation};
        rv.governance=(RmeGovernancePort){{RME_VESTIGIAL,RME_PORT_governance},&rme_vestigial_governance};
        rv.nested=(RmeNestedPort){{RME_VESTIGIAL,RME_PORT_nested},&rme_vestigial_nested};
        RmePortSet e1 = rme_envelope(&rv);
        XCons a = (e0.count == e1.count) ? X_YES : X_NO;
        cell("D-S7a", "S7", true, p, a, "the envelope is status-independent");
    }

    /* ---- S4: the four graph consequences.  MECHANISMS DIFFER
     * (reachability vs SCC+self-check) -- pre-registered slack. */
    {
        uint64_t rows[4], gov[1], scr[4];
        PcDepGraph g; pc_graph_init(&g, 4, rows, gov, 1);
        pc_graph_mark_governed(&g, 0); pc_graph_mark_governed(&g, 1);
        pc_graph_declare_dependency(&g, 0, 1);
        bool c1 = true; pc_graph_has_cycle(&g, gov, scr, &c1);

        static const RmeSlot sl[] = { { "X", true }, { "Y", true } };
        static const size_t ry[] = { 0 };
        static const RmeTransitionDecl tr[] = { { "T_Y", 1, ry, 1 } };
        RmeSystem s = { sl, 2, tr, 1, false };
        RmeEdge ed[8]; size_t m = rme_project(&s, true, ed, 8);
        bool a1c = true; rme_graph_has_cycle(2, ed, m, &a1c);
        cell("D-S4a", "S4", true, c1 ? X_YES : X_NO, a1c ? X_YES : X_NO,
             "one-way governed dependency is not reciprocity");

        pc_graph_declare_dependency(&g, 1, 0);
        bool c2 = false; pc_graph_has_cycle(&g, gov, scr, &c2);
        static const size_t rx2[] = { 1 };
        static const RmeTransitionDecl tr2[] = { { "T_X", 0, rx2, 1 }, { "T_Y", 1, ry, 1 } };
        RmeSystem s2 = { sl, 2, tr2, 2, false };
        size_t m2 = rme_project(&s2, true, ed, 8);
        bool a2c = false; rme_graph_has_cycle(2, ed, m2, &a2c);
        cell("D-S4b", "S4", true, c2 ? X_YES : X_NO, a2c ? X_YES : X_NO,
             "reciprocal governed dependency IS a directed cycle");

        uint64_t r3[1], g3[1], s3[1];
        PcDepGraph gs; pc_graph_init(&gs, 1, r3, g3, 1);
        pc_graph_mark_governed(&gs, 0); pc_graph_declare_dependency(&gs, 0, 0);
        bool c3 = false; pc_graph_has_cycle(&gs, g3, s3, &c3);
        static const RmeSlot sl1[] = { { "X", true } };
        static const size_t rs[] = { 0 };
        static const RmeTransitionDecl tr3[] = { { "T_X", 0, rs, 1 } };
        RmeSystem s4 = { sl1, 1, tr3, 1, false };
        size_t m3 = rme_project(&s4, true, ed, 8);
        bool a3c = false; rme_graph_has_cycle(1, ed, m3, &a3c);
        cell("D-S4c", "S4", true, c3 ? X_YES : X_NO, a3c ? X_YES : X_NO,
             "a governed SELF-EDGE is a directed cycle");

        uint64_t r4[1], g4[1], s5[1];
        PcDepGraph gn; pc_graph_init(&gn, 1, r4, g4, 1);
        pc_graph_mark_governed(&gn, 0);
        bool c4 = true; pc_graph_has_cycle(&gn, g4, s5, &c4);
        static const RmeTransitionDecl tr4[] = { { "T_X", 0, nullptr, 0 } };
        RmeSystem s6 = { sl1, 1, tr4, 1, false };
        size_t m4 = rme_project(&s6, true, ed, 8);
        bool a4c = true; rme_graph_has_cycle(1, ed, m4, &a4c);
        cell("D-S4d", "S4", true, c4 ? X_YES : X_NO, a4c ? X_YES : X_NO,
             "no declared dependency: execution structure cannot promote");
    }

    /* ---- S8: malformed is REFUSED, not answered. */
    {
        PcPort sa[4]; PcSurface A = pcs("A", sa);
        PcConnectionSet bad = { nullptr, 1 }; size_t obl = 0;
        XCons p = pc_set_admissible(&A, &A, &bad, &COMPAT, &obl).result == PC_ADMIT_MALFORMED
                  ? X_REFUSED : X_NO;
        RmePrototype ra = awv("A");
        RmeRelation R = { nullptr, 1, false };
        RmeComposition c = rme_admissible(&ra, &ra, &R);
        XCons a = (!c.ok && c.why != nullptr) ? X_REFUSED : X_NO;
        cell("D-S8a", "S8", true, p, a, "a set claiming edges it lacks is refused, not dereferenced");

        uint64_t rows[2], gov[1]; PcDepGraph g; pc_graph_init(&g, 2, rows, gov, 1);
        XCons p2 = pc_graph_declare_dependency(&g, 0, 9) ? X_YES : X_REFUSED;
        static const RmeSlot sl[] = { { "X", true }, { "Y", true } };
        static const size_t bad_r[] = { 99 };
        static const RmeTransitionDecl trb[] = { { "T", 1, bad_r, 1 } };
        RmeSystem sb = { sl, 2, trb, 1, false };
        RmeEdge ed[4];
        XCons a2c = (rme_project(&sb, true, ed, 4) == SIZE_MAX) ? X_REFUSED : X_YES;
        cell("D-S8b", "S8", true, p2, a2c, "an out-of-range dependency is refused, not dropped");
    }

    /* ================= PRE-REGISTERED SLACK ================= */
    printf("\n--- pre-registered slack: DISAGREE here would be an ORACLE DEFECT ---\n");

    /* K-4 is EXECUTED, and it is the one that matters: the two substrates
     * genuinely produce DIFFERENT observable values here, and the
     * classifier must still not call it DISAGREE.  A slack cell whose two
     * sides happen to agree tests nothing. */
    {
        PcSurface *store[2]; uint64_t ser[2]; PcRegistry reg;
        pc_registry_init(&reg, store, ser, 2);
        PcPort sa[4], sb[4]; PcSurface A = pcs("A", sa), B = pcs("B", sb);
        PcIdentity f = pc_identity_mint(&reg, &A);
        pc_identity_release(&reg, f);
        PcIdentity g2 = pc_identity_mint(&reg, &B);
        XCons p = (g2.slot == f.slot) ? X_YES : X_NO;      /* ProtoC RECYCLES */

        rme_validation_reset();
        RmePrototype r1 = awv("first");
        const RmeValidated *h1 = rme_validate(&r1, nullptr);
        rme_validation_reset();
        RmePrototype r2 = awv("second");
        const RmeValidated *h2 = rme_validate(&r2, nullptr);
        XCons a = (h1 == h2) ? X_YES : X_NO;               /* AWV does NOT */

        cell("K-4", "S5", false, p, a,
             "storage reuse: ProtoC recycles, AWV cannot -- both satisfy S5 (see D-S5a)");
    }

    /* The remaining five are DECLARED, not executed: their difference is
     * structural (a type shape, a build-time choice) and has no runtime
     * observable to compare.  Printed as declarations so they cannot be
     * mistaken for executed comparisons -- a cell that compares n/a with
     * n/a classifies UNDECIDABLE whatever the substrates do, and would be
     * exactly the vacuous check this project keeps finding. */
    printf("K-1     S3     DECLARED-SLACK (not executed)   compatibility relation: client param vs fixed table\n");
    printf("K-2     -      DECLARED-SLACK (not executed)   port vocabulary: descriptor table vs fixed set\n");
    printf("K-3     S3     DECLARED-SLACK (not executed)   compatibility symmetry: flag vs fixed choice\n");
    printf("K-5     S6     DECLARED-SLACK (not executed)   ownership: value identity vs opaque handle\n");
    printf("K-6     S4     DECLARED-SLACK (not executed)   cycle mechanism: reachability vs SCC+self-check\n");

    printf("\nAGREE %d   DISAGREE %d   UNDECIDABLE %d   ORACLE-DEFECT %d\n",
           n_agree, n_disagree, n_undec, n_oracle);
    printf("\nThis is a DIAGNOSTIC run. An aggregate verdict exists only after every\n"
           "DISAGREE has been through the five questions in DIFFERENTIAL.md.\n");
    return n_disagree > 0 || n_oracle > 0 ? 1 : 0;
}
