#ifndef PC_ADMIT_H
#define PC_ADMIT_H

#include "../types/pc_surface.h"

/* ProtoC — admissibility/
 *
 * Derived from S1 and S3 only.  See ../DERIVATION.md.
 *
 * THE DELIBERATE STRUCTURAL DIVERGENCE.  The ENDPOINT-PAIR PREDICATE IS
 * PRIMARY and a relation is a FOLD over it.  The obvious factoring is the
 * other way round -- iterate a relation object, check its endpoints -- and
 * that factoring is what makes S1 easy to violate, because the relation
 * object carries a declared flag that sits right next to the endpoint
 * checks and invites being consulted by them.
 *
 * Here the primary entry point CANNOT consult declaration status, because
 * it never receives a relation.  S1 is satisfied by the SHAPE OF THE API
 * rather than by remembering not to read a field:
 *
 *     Admissible  =/=>  Declared
 *
 * Declaration lives in declaration/ and is not visible from this header.
 *
 * WHAT S1-S11 DO NOT DETERMINE, stated rather than resolved by looking:
 * the frozen semantics fix that admissibility requires compatible endpoints
 * (S3) but NOWHERE fix WHICH endpoint pairs are compatible.  ProtoC
 * therefore takes the compatibility relation as a CLIENT-SUPPLIED
 * PARAMETER.  If AWV hardcodes a particular table, that is a difference the
 * frozen material does not adjudicate, and the differential oracle should
 * record it as UNDECIDABLE rather than as either implementation's defect.
 */

/* A declared compatibility relation over port descriptors, supplied by
 * whoever declares the schemas.  Compared by declared port NAME, because a
 * descriptor is the only thing the frozen semantics give us to compare. */
typedef struct {
    const char *a;
    const char *b;
} PcCompatPair;

typedef struct {
    const PcCompatPair *pairs;
    size_t              count;
    bool                symmetric;   /* whether (a,b) also licenses (b,a) */
} PcCompatibility;

typedef enum {
    PC_ADMIT_OK = 0,
    PC_ADMIT_MALFORMED,          /* refusal, not a negative answer (S8) */
    PC_ADMIT_PORT_OUT_OF_RANGE,
    PC_ADMIT_ENDPOINT_NOT_ACTIVE,
    PC_ADMIT_INCOMPATIBLE,
} PcAdmitResult;

typedef struct {
    PcAdmitResult result;
    size_t        edge;    /* offending connection index, or count */
} PcAdmitVerdict;

const char *pc_admit_text(PcAdmitResult r);

/* THE PRIMARY PREDICATE.  One endpoint pair, no relation, no declaration.
 *
 * S3, unconditionally and on BOTH endpoints: a vestigial port is retained,
 * typed and reachable -- and not wireable.  The two endpoints are checked
 * symmetrically because the requirement is symmetric; an asymmetric
 * implementation is untestable by any single-sided fixture. */
PcAdmitVerdict pc_endpoint_admissible(const PcSurface *A, size_t pa,
                                      const PcSurface *B, size_t pb,
                                      const PcCompatibility *compat);

/* A proposed connection set.  Deliberately NOT called a relation and
 * deliberately carrying no declared flag: this type exists only to be
 * folded over. */
typedef struct {
    size_t a;
    size_t b;
} PcConnection;

typedef struct {
    const PcConnection *edges;
    size_t              count;
} PcConnectionSet;

/* The fold.  Obligations are exactly |set|, never the number of compatible
 * pairs found: S1 makes admissibility a property of the DECLARED endpoints,
 * so a pair that happens to be compatible outside the set contributes
 * nothing. */
PcAdmitVerdict pc_set_admissible(const PcSurface *A, const PcSurface *B,
                                 const PcConnectionSet *set,
                                 const PcCompatibility *compat,
                                 size_t *obligations);

#endif /* PC_ADMIT_H */
