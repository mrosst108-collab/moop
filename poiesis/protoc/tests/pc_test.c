/* ProtoC — its OWN tests, derived from S1-S11 in ../DERIVATION.md.
 *
 * These are NOT the AWV suite.  No expected result here was obtained by
 * running AWV or by reading src/rme/; each traces to a derivation entry.
 * The AWV suite is applied later, as an external oracle, and a
 * disagreement there is classified AGREE / DISAGREE / UNDECIDABLE rather
 * than treated as a ProtoC failure by default.
 */
#include <stdio.h>

#include "../admissibility/pc_admit.h"

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

    printf("\nProtoC: %d passed, %d failed\n", passed, failed);
    return failed ? 1 : 0;
}
