#include "pc_compose.h"

PcComposition pc_compose(const PcDeclarationLog *log,
                         const PcSurface *a, const PcSurface *b,
                         const PcConnectionSet *set,
                         const PcCompatibility *compat)
{
    PcComposition c = { false, false, PC_ADMIT_MALFORMED, 0, 0 };

    /* Computed independently and BOTH reported, so "not declared" and "not
     * admissible" are never conflated into a single false. */
    c.declared = pc_is_declared(log, a, b, set);

    size_t obl = 0;
    PcAdmitVerdict v = pc_set_admissible(a, b, set, compat, &obl);
    c.admissibility = v.result;
    c.edge = v.edge;
    c.obligations = obl;

    c.composed = c.declared && (v.result == PC_ADMIT_OK);
    return c;
}
