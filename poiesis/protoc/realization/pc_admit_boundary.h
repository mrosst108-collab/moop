#ifndef PC_ADMIT_BOUNDARY_H
#define PC_ADMIT_BOUNDARY_H

#include "../identity/pc_identity.h"

/* ProtoC — realization/   Derived from S2, S8, S9, S10.
 *
 * The boundary at which a surface becomes CHECKED.  Both halves of S2's
 * closure are enforced here, independently, and the result of passing is
 * an IDENTITY -- not a flag, not a wrapper, not a field.
 *
 * S9/S10 fall out of that choice rather than being defended by it: there
 * is no transferable "validated" value anywhere in ProtoC, so
 * `child = parent` cannot transmit checked status, because checked status
 * is not a thing either object holds.  What exists is a registry entry and
 * a value that names it.
 *
 * NOTE the symmetric-distinction rule.  This module does NOT reproduce a
 * separate "conformance" predicate alongside a "validation" one merely
 * because AWV has both.  S1-S11 name one boundary and one set of
 * requirements on it; ProtoC implements one.  If AWV's two predicates
 * disagree about a record while ProtoC's one does not, that is a
 * consequence to compare, not a structure to imitate. */

typedef struct {
    PcIdentity identity;    /* dead identity if the surface was refused */
    PcVerdict  verdict;     /* why, when refused */
} PcAdmission;

/* The sole producer of a checked identity.  Takes ONLY the surface: no
 * actor, no capability, no parent, no provenance -- S9/S10 make all of
 * those irrelevant to the answer, so there is no parameter through which
 * to offer them. */
PcAdmission pc_admit_surface(PcRegistry *r, PcSurface *s);

#endif /* PC_ADMIT_BOUNDARY_H */
