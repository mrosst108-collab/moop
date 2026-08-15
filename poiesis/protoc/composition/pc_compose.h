#ifndef PC_COMPOSE_H
#define PC_COMPOSE_H

#include "../declaration/pc_declare.h"

/* ProtoC — composition/   Derived from S1.
 *
 * Composition is the CONJUNCTION of two independently computed stages:
 *
 *      Compose(A,B,set)  <=>  Declared(A,B,set)  AND  Admissible(A,B,set)
 *
 * Both operands are computed by code that cannot see the other's input:
 * pc_set_admissible() never receives the log, pc_is_declared() never
 * receives the compatibility relation.  Neither can shortcut the other. */

typedef struct {
    bool          composed;
    bool          declared;      /* reported separately, so a caller can see WHICH failed */
    PcAdmitResult admissibility;
    size_t        edge;
    size_t        obligations;
} PcComposition;

PcComposition pc_compose(const PcDeclarationLog *log,
                         const PcSurface *a, const PcSurface *b,
                         const PcConnectionSet *set,
                         const PcCompatibility *compat);

#endif /* PC_COMPOSE_H */
