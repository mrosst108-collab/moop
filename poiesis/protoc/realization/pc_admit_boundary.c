#include "pc_admit_boundary.h"

PcAdmission pc_admit_surface(PcRegistry *r, PcSurface *s)
{
    PcAdmission a = { pc_identity_none(), { PC_OK, 0 } };

    a.verdict = pc_surface_wellformed(s);
    if (a.verdict.reason != PC_OK) {
        return a;
    }
    /* S2: the status/realization closure is enforced AT THE BOUNDARY, both
     * directions, every port.  A surface that passes structural
     * well-formedness but names the wrong realization has not been
     * checked. */
    for (size_t i = 0; i < s->port_count; i++) {
        PcVerdict v = pc_port_realization_agrees(s, i);
        if (v.reason != PC_OK) {
            a.verdict = v;
            return a;
        }
    }
    a.identity = pc_identity_mint(r, s);
    if (a.identity.serial == 0) {
        a.verdict = (PcVerdict){ PC_REFUSED_NO_SURFACE, s->port_count };
    }
    return a;
}
