#include <string.h>

#include "pc_admit.h"

const char *pc_admit_text(PcAdmitResult r)
{
    switch (r) {
    case PC_ADMIT_OK:                   return "admissible";
    case PC_ADMIT_MALFORMED:            return "malformed input: refused, not answered";
    case PC_ADMIT_PORT_OUT_OF_RANGE:    return "connection names a port outside the schema";
    case PC_ADMIT_ENDPOINT_NOT_ACTIVE:  return "endpoint is not ACTIVE and cannot participate";
    case PC_ADMIT_INCOMPATIBLE:         return "endpoint pair is not in the declared compatibility relation";
    }
    return "<unknown>";
}

static PcAdmitVerdict av(PcAdmitResult r, size_t edge)
{
    PcAdmitVerdict v = { r, edge };
    return v;
}

static bool same(const char *x, const char *y)
{
    return x != nullptr && y != nullptr && strcmp(x, y) == 0;
}

static bool compatible(const PcCompatibility *c, const char *na, const char *nb)
{
    if (c == nullptr || c->pairs == nullptr) {
        return false;
    }
    for (size_t i = 0; i < c->count; i++) {
        if (same(c->pairs[i].a, na) && same(c->pairs[i].b, nb)) {
            return true;
        }
        if (c->symmetric && same(c->pairs[i].a, nb) && same(c->pairs[i].b, na)) {
            return true;
        }
    }
    return false;
}

PcAdmitVerdict pc_endpoint_admissible(const PcSurface *A, size_t pa,
                                      const PcSurface *B, size_t pb,
                                      const PcCompatibility *compat)
{
    /* S8: malformed is REFUSED with its own code, never folded into
     * "inadmissible".  A caller must be able to tell "these do not connect"
     * from "you handed me nonsense". */
    if (A == nullptr || B == nullptr || compat == nullptr) {
        return av(PC_ADMIT_MALFORMED, 0);
    }
    if (pc_surface_wellformed(A).reason != PC_OK ||
        pc_surface_wellformed(B).reason != PC_OK) {
        return av(PC_ADMIT_MALFORMED, 0);
    }
    if (!pc_in_envelope(A, pa) || !pc_in_envelope(B, pb)) {
        return av(PC_ADMIT_PORT_OUT_OF_RANGE, 0);
    }

    /* S3, symmetric and unconditional.  Note this reads only status: a
     * vestigial endpoint is IN the envelope and reachable, and is still not
     * wireable.  Retention is not wiring. */
    if (A->ports[pa].status != PC_ACTIVE || B->ports[pb].status != PC_ACTIVE) {
        return av(PC_ADMIT_ENDPOINT_NOT_ACTIVE, 0);
    }

    if (!compatible(compat, A->schema->ports[pa].name, B->schema->ports[pb].name)) {
        return av(PC_ADMIT_INCOMPATIBLE, 0);
    }
    return av(PC_ADMIT_OK, 0);
}

PcAdmitVerdict pc_set_admissible(const PcSurface *A, const PcSurface *B,
                                 const PcConnectionSet *set,
                                 const PcCompatibility *compat,
                                 size_t *obligations)
{
    if (set == nullptr) {
        if (obligations) *obligations = 0;
        return av(PC_ADMIT_MALFORMED, 0);
    }
    /* S8: a set claiming edges it does not carry is malformed, not empty. */
    if (set->count > 0 && set->edges == nullptr) {
        if (obligations) *obligations = set->count;
        return av(PC_ADMIT_MALFORMED, 0);
    }
    if (obligations) *obligations = set->count;

    for (size_t i = 0; i < set->count; i++) {
        PcAdmitVerdict v = pc_endpoint_admissible(A, set->edges[i].a,
                                                  B, set->edges[i].b, compat);
        if (v.result != PC_ADMIT_OK) {
            v.edge = i;
            return v;
        }
    }
    return av(PC_ADMIT_OK, set->count);
}
