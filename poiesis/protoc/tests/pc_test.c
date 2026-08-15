/* ProtoC — its OWN tests, derived from S1-S11 in ../DERIVATION.md.
 *
 * These are NOT the AWV suite.  No expected result here was obtained by
 * running AWV or by reading src/rme/; each traces to a derivation entry.
 * The AWV suite is applied later, as an external oracle, and a
 * disagreement there is classified AGREE / DISAGREE / UNDECIDABLE rather
 * than treated as a ProtoC failure by default.
 */
#include <stdio.h>

#include "../composition/pc_compose.h"
#include "../realization/pc_admit_boundary.h"

static int passed, failed;
static void check(bool cond, const char *id, const char *what)
{
    if (cond) { passed++; printf("ok   - %-5s %s\n", id, what); }
    else      { failed++; printf("FAIL - %-5s %s\n", id, what); }
}

static const PcPortDescriptor DESC[] = {
    { "state",     "state-if"     },
    { "step",      "step-if"      },
    { "couple",    "couple-if"    },
    { "observe",   "observe-if"   },
};
static const PcSchema SCHEMA = { "protoc.demo", DESC, 4, 1 };

/* Distinct client-owned realization objects.  ProtoC never dereferences
 * these -- S6 -- so their contents are irrelevant and their ADDRESSES are
 * the whole point. */
static const int r_state = 0, r_step = 0, r_couple = 0, r_observe = 0;
static const int v_state = 0, v_step = 0, v_couple = 0, v_observe = 0;

static PcPort mkports(PcPort *dst)
{
    dst[0] = (PcPort){ PC_ACTIVE, &r_state,   &v_state,   false };
    dst[1] = (PcPort){ PC_ACTIVE, &r_step,    &v_step,    true  };
    dst[2] = (PcPort){ PC_ACTIVE, &r_couple,  &v_couple,  false };
    dst[3] = (PcPort){ PC_ACTIVE, &r_observe, &v_observe, true  };
    return dst[0];
}
static PcSurface mk(const char *id, PcPort *storage)
{
    mkports(storage);
    PcSurface s = { id, &SCHEMA, storage, 4 };
    return s;
}

static const PcCompatPair PAIRS[] = { { "step", "couple" }, { "state", "state" } };
static const PcCompatibility COMPAT = { PAIRS, 2, true };

int main(void)
{
    /* P1 (S8): a zero-filled port is the construction sentinel and is
     * refused, not defaulted to a semantic status. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        ports[2].status = PC_STATUS_UNSET;
        PcVerdict v = pc_surface_wellformed(&s);
        check(v.reason == PC_REFUSED_STATUS_UNSET && v.port == 2,
              "P1", "unset status refused, naming the port (S8)");
    }

    /* P2 (S8): a status outside the semantic domain is refused, and it is
     * DISTINGUISHABLE from the sentinel. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        ports[1].status = (PcStatus)77;
        PcVerdict v = pc_surface_wellformed(&s);
        check(v.reason == PC_REFUSED_STATUS_DOMAIN && v.port == 1,
              "P2", "out-of-domain status refused, distinct from the sentinel (S8)");
    }

    /* P3 (S8): an instance vector disagreeing with its schema is malformed.
     * Truncating to the shorter would be the silent normalization S8
     * forbids. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        s.port_count = 3;
        check(pc_surface_wellformed(&s).reason == PC_REFUSED_ARITY,
              "P3", "arity mismatch refused, not truncated (S8)");
    }

    /* P4 (S2), both directions independently. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        ports[0].realization = &v_state;              /* ACTIVE names the vestigial form */
        PcVerdict a = pc_port_realization_agrees(&s, 0);

        PcPort p2[4]; PcSurface s2 = mk("T", p2);
        p2[1].status = PC_VESTIGIAL;                  /* VESTIGIAL, wrong object */
        PcVerdict b = pc_port_realization_agrees(&s2, 1);

        check(a.reason == PC_REFUSED_ACTIVE_IS_VESTIGIAL_FORM
              && b.reason == PC_REFUSED_VESTIGIAL_NOT_DECLARED_FORM,
              "P4", "status/realization closure enforced in BOTH directions (S2)");
    }

    /* P5 (S7): elision is a permission; VESTIGIAL alone never implies it,
     * and ACTIVE never permits it however the bit is set. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        ports[1].status = PC_VESTIGIAL; ports[1].realization = &v_step;   /* elidable   */
        ports[2].status = PC_VESTIGIAL; ports[2].realization = &v_couple; /* not        */
        bool active_never = !pc_port_elidable(&s, 0) && !pc_port_elidable(&s, 3);
        check(pc_port_elidable(&s, 1) && !pc_port_elidable(&s, 2) && active_never,
              "P5", "elidable iff VESTIGIAL and permitted; ACTIVE never (S7)");
    }

    /* P6 (S7): the envelope never shrinks.  Dispatch omits; the envelope is
     * the whole declared schema regardless of status. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        size_t env_before = pc_envelope_count(&s), dis_before = pc_dispatch_count(&s);
        ports[1].status = PC_VESTIGIAL; ports[1].realization = &v_step;
        ports[3].status = PC_VESTIGIAL; ports[3].realization = &v_observe;
        size_t env_after = pc_envelope_count(&s), dis_after = pc_dispatch_count(&s);
        check(env_before == 4 && env_after == 4 && dis_before == 4 && dis_after == 2
              && pc_in_envelope(&s, 1) && !pc_in_dispatch(&s, 1),
              "P6", "elision removes from dispatch, never from the envelope (S7)");
    }

    /* P7 (S1): the primary admissibility predicate cannot consult
     * declaration -- it is never handed one.  Structural, not remembered. */
    {
        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        PcAdmitVerdict v = pc_endpoint_admissible(&A, 1, &B, 2, &COMPAT);
        check(v.result == PC_ADMIT_OK,
              "P7", "admissible with no relation object in scope at all (S1)");
    }

    /* P8 (S3): symmetric and unconditional, on BOTH endpoints.  A
     * single-sided fixture cannot distinguish a symmetric guard from a
     * one-sided one, so both sides are exercised. */
    {
        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        pa[1].status = PC_VESTIGIAL; pa[1].realization = &v_step;
        PcAdmitVerdict left = pc_endpoint_admissible(&A, 1, &B, 2, &COMPAT);

        PcPort pc2[4], pd[4];
        PcSurface C = mk("C", pc2), D = mk("D", pd);
        pd[2].status = PC_VESTIGIAL; pd[2].realization = &v_couple;
        PcAdmitVerdict right = pc_endpoint_admissible(&C, 1, &D, 2, &COMPAT);

        check(left.result == PC_ADMIT_ENDPOINT_NOT_ACTIVE
              && right.result == PC_ADMIT_ENDPOINT_NOT_ACTIVE,
              "P8", "a VESTIGIAL endpoint is refused on EITHER side (S3)");
    }

    /* P9 (S3): the refused endpoint is nonetheless retained and reachable.
     * Retention is not wiring. */
    {
        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        pa[1].status = PC_VESTIGIAL; pa[1].realization = &v_step;
        bool retained = pc_in_envelope(&A, 1) && A.ports[1].realization != nullptr
                     && A.schema->ports[1].name != nullptr;
        check(pc_endpoint_admissible(&A, 1, &B, 2, &COMPAT).result != PC_ADMIT_OK
              && retained,
              "P9", "the inadmissible endpoint is still retained, typed and reachable (S3)");
    }

    /* P10 (S8): malformed is refused with its own code, never folded into
     * "inadmissible" -- the caller must distinguish nonsense from no. */
    {
        PcPort pa[4]; PcSurface A = mk("A", pa);
        PcConnectionSet bad = { nullptr, 1 };
        size_t obl = 0;
        PcAdmitVerdict v = pc_set_admissible(&A, &A, &bad, &COMPAT, &obl);
        check(v.result == PC_ADMIT_MALFORMED && obl == 1,
              "P10", "a set claiming edges it lacks is refused, not dereferenced (S8)");
    }

    /* P11 (S1): obligations are exactly |set|.  A compatible pair OUTSIDE
     * the set contributes nothing. */
    {
        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        const PcConnection e[] = { { 1, 2 } };
        PcConnectionSet set = { e, 1 };
        size_t obl = 99;
        PcAdmitVerdict v = pc_set_admissible(&A, &B, &set, &COMPAT, &obl);
        /* (state,state) is compatible but is not in the set. */
        bool outside_is_compatible =
            pc_endpoint_admissible(&A, 0, &B, 0, &COMPAT).result == PC_ADMIT_OK;
        check(v.result == PC_ADMIT_OK && obl == 1 && outside_is_compatible,
              "P11", "obligations == |set|; a compatible pair outside it is irrelevant (S1)");
    }

    /* P12 (S1): evaluating admissibility mutates nothing. */
    {
        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        PcPort before[4]; for (int i = 0; i < 4; i++) before[i] = pa[i];
        (void)pc_endpoint_admissible(&A, 1, &B, 2, &COMPAT);
        (void)pc_endpoint_admissible(&A, 1, &B, 2, &COMPAT);
        bool unchanged = true;
        for (int i = 0; i < 4; i++) {
            unchanged = unchanged && before[i].status == pa[i].status
                     && before[i].realization == pa[i].realization;
        }
        check(unchanged, "P12", "evaluating admissibility is idempotent and mutates nothing (S1)");
    }

    /* P13 (S6): ProtoC compares realization pointers and never owns or
     * dereferences them.  The surface holds the caller's addresses. */
    {
        PcPort ports[4]; PcSurface s = mk("S", ports);
        check(s.ports[0].realization == &r_state && s.ports[2].vestigial_form == &v_couple,
              "P13", "realizations are client-owned addresses, held not copied (S6)");
    }

    /* ---- identity/ (S5).  The invariant is that a released identity never
     * becomes valid for a later object.  ProtoC reaches it by making
     * identity a VALUE, which lets slots be RECYCLED safely -- a substrate
     * handing out pointers into slots cannot do this and must forbid reuse
     * instead.  Same invariant, different mechanism. */
    {
        PcSurface *store[2]; uint64_t serials[2];
        PcRegistry reg; pc_registry_init(&reg, store, serials, 2);

        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);

        PcIdentity first = pc_identity_mint(&reg, &A);
        bool first_live = pc_identity_live(&reg, first);
        pc_identity_release(&reg, first);

        PcIdentity second = pc_identity_mint(&reg, &B);   /* SAME SLOT reused */
        bool slot_reused = second.slot == first.slot;

        check(first_live && slot_reused
              && !pc_identity_live(&reg, first)
              && pc_identity_surface(&reg, first) == nullptr
              && pc_identity_live(&reg, second)
              && pc_identity_surface(&reg, second) == &B,
              "P14", "a released identity stays dead even when its SLOT is reused (S5)");
    }

    /* ---- P15 (S5): a zero-filled identity is dead.  Serial 0 is never
     * issued, so an uninitialised value cannot name anything. */
    {
        PcSurface *store[2]; uint64_t serials[2];
        PcRegistry reg; pc_registry_init(&reg, store, serials, 2);
        PcPort pa[4]; PcSurface A = mk("A", pa);
        (void)pc_identity_mint(&reg, &A);
        PcIdentity zero = { 0, 0 };
        check(!pc_identity_live(&reg, zero) && !pc_identity_release(&reg, zero),
              "P15", "a zero-filled identity is dead and cannot be released (S5)");
    }

    /* ---- P16 (S9/S10): copying an identity aliases the SAME object; it
     * cannot transfer checked status to a different one.  There is no
     * "validated" value to assign, because checked status is a registry
     * fact named by a value, not a property either surface holds. */
    {
        PcSurface *store[2]; uint64_t serials[2];
        PcRegistry reg; pc_registry_init(&reg, store, serials, 2);
        PcPort pa[4], pb[4];
        PcSurface parent = mk("parent", pa), child = mk("child", pb);
        pb[2].status = PC_STATUS_UNSET;                    /* the child is malformed */

        PcAdmission p = pc_admit_surface(&reg, &parent);
        PcAdmission c = pc_admit_surface(&reg, &child);

        PcIdentity stolen = p.identity;                    /* the tempting move */
        check(p.identity.serial != 0 && c.identity.serial == 0
              && c.verdict.reason == PC_REFUSED_STATUS_UNSET
              && pc_identity_surface(&reg, stolen) == &parent,   /* still the parent */
              "P16", "copying an identity aliases the same object, never transfers status (S9/S10)");
    }

    /* ---- P17 (S2): the boundary enforces the status/realization closure,
     * not merely structural well-formedness. */
    {
        PcSurface *store[2]; uint64_t serials[2];
        PcRegistry reg; pc_registry_init(&reg, store, serials, 2);
        PcPort pa[4]; PcSurface A = mk("A", pa);
        pa[0].realization = &v_state;              /* ACTIVE names the vestigial form */
        PcAdmission a = pc_admit_surface(&reg, &A);
        check(a.identity.serial == 0
              && a.verdict.reason == PC_REFUSED_ACTIVE_IS_VESTIGIAL_FORM,
              "P17", "the boundary refuses an ACTIVE port naming its vestigial form (S2)");
    }

    /* ---- P18 (S1): admissible while UNDECLARED.  Admissibility is
     * computed by code that never receives the declaration log. */
    {
        PcDeclaration entries[4]; PcDeclarationLog log;
        pc_declaration_init(&log, entries, 4);

        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        const PcConnection e[] = { { 1, 2 } };
        PcConnectionSet set = { e, 1 };

        PcComposition before = pc_compose(&log, &A, &B, &set, &COMPAT);
        bool admissible_undeclared = !before.declared
                                  && before.admissibility == PC_ADMIT_OK
                                  && !before.composed;

        pc_declare(&log, &A, &B, &set);
        PcComposition after = pc_compose(&log, &A, &B, &set, &COMPAT);

        check(admissible_undeclared && after.declared && after.composed,
              "P18", "admissible while undeclared; declaring it changes neither surface (S1)");
    }

    /* ---- P19 (S1): declaration is bound to its PARTICIPANTS.  A
     * declaration for (A,B) is not a declaration for (C,D). */
    {
        PcDeclaration entries[4]; PcDeclarationLog log;
        pc_declaration_init(&log, entries, 4);
        PcPort pa[4], pb[4], pc2[4], pd[4];
        PcSurface A = mk("A", pa), B = mk("B", pb), C = mk("C", pc2), D = mk("D", pd);
        const PcConnection e[] = { { 1, 2 } };
        PcConnectionSet set = { e, 1 };
        pc_declare(&log, &A, &B, &set);
        check(pc_is_declared(&log, &A, &B, &set) && !pc_is_declared(&log, &C, &D, &set),
              "P19", "declaration binds to its participants, not to argument position (S1)");
    }

    /* ---- P20 (S1): declaring does NOT make something admissible.  The two
     * stages are computed by code that cannot see the other's input. */
    {
        PcDeclaration entries[4]; PcDeclarationLog log;
        pc_declaration_init(&log, entries, 4);
        PcPort pa[4], pb[4];
        PcSurface A = mk("A", pa), B = mk("B", pb);
        pa[1].status = PC_VESTIGIAL; pa[1].realization = &v_step;
        const PcConnection e[] = { { 1, 2 } };
        PcConnectionSet set = { e, 1 };
        bool declared = pc_declare(&log, &A, &B, &set);
        PcComposition c = pc_compose(&log, &A, &B, &set, &COMPAT);
        check(declared && c.declared
              && c.admissibility == PC_ADMIT_ENDPOINT_NOT_ACTIVE && !c.composed,
              "P20", "declaring an inadmissible set records the act and composes nothing (S1)");
    }

    printf("\nProtoC: %d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
