#ifndef PC_DECLARE_H
#define PC_DECLARE_H

#include "../admissibility/pc_admit.h"

/* ProtoC — declaration/   Derived from S1.
 *
 *      Admissible  !=  Declared  !=  Executed
 *      Admissible  =/=>  Declared
 *
 * THE DELIBERATE DIVERGENCE.  Declaration is NOT a flag on the connection
 * set.  It is an ACT recorded in a separate registry, and Declared(set) is
 * a QUERY against that registry.
 *
 * A flag on the set would sit inside the very object admissibility
 * receives, one dereference from every endpoint check.  Here the connection
 * set has no such field to read, and admissibility/ does not include this
 * header, so `Admissible =/=> Declared` is enforced by what is reachable
 * rather than by discipline.
 *
 * EXECUTION IS ABSENT.  S1 places Executed outside the substrate, so this
 * header offers no way to perform a declared connection.  `Executed =>
 * Declared` therefore holds vacuously here, and cannot be violated by an
 * operation that does not exist.
 */

typedef struct {
    const PcConnectionSet *set;
    const PcSurface       *a;
    const PcSurface       *b;
} PcDeclaration;

typedef struct {
    PcDeclaration *entries;
    size_t         capacity;
    size_t         count;
} PcDeclarationLog;

void pc_declaration_init(PcDeclarationLog *log, PcDeclaration *store, size_t capacity);

/* Records the act.  Deliberately does NOT evaluate admissibility: S1 makes
 * them different stages, and checking here would make Declared imply
 * Admissible, which is a claim S1 does not license in either direction. */
bool pc_declare(PcDeclarationLog *log, const PcSurface *a, const PcSurface *b,
                const PcConnectionSet *set);

/* Declaration is bound to its PARTICIPANTS, not to argument position: a
 * declaration made for (A,B) is not a declaration for (C,D). */
bool pc_is_declared(const PcDeclarationLog *log, const PcSurface *a,
                    const PcSurface *b, const PcConnectionSet *set);

#endif /* PC_DECLARE_H */
