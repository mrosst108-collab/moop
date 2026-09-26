#ifndef RME_BIND_H
#define RME_BIND_H

#include <stdbool.h>
#include <stddef.h>

/* poiesis — transition read-sets (spec §10).
 *
 *   Reads(T)          declared dependency set of T
 *   ArgType(T)        declared argument-interface type of T
 *   Fields(ArgType)   declared semantic fields of that interface
 *   Represents(f, r)  f EXPLICITLY represents dependency r
 *
 *   BindValid(T)  iff  forall r in Reads(T),
 *                      exists f in Fields(ArgType(T)) : Represents(f, r)
 *
 * TWO INDEPENDENTLY DECLARED SURFACES.  Reads(T) is NOT inferred from
 * Fields(ArgType(T)), and Fields(ArgType(T)) is NOT inferred from Reads(T).
 *
 * In particular bind must not introspect a C struct to derive the read set.
 * If it did, an undeclared read expansion would silently redefine the very
 * interface it is supposed to violate: every read would be represented by
 * construction, C15 would become inexpressible, and the predicate would be
 * a tautology wearing the costume of a check.  Both surfaces are therefore
 * supplied by the declarer, and this module only compares them.
 *
 * A compile-time-fixed argument struct is a VALID realization (C16).  What
 * is rejected is dependency expansion without the matching interface change
 * (C15).  Changing the interface correspondingly restores validity (C15b).
 * The prohibited inference HardWiredArgs(T) => !RME7Conforms(T) is not
 * implementable through this interface: nothing here inspects storage
 * strategy, only declarations.
 *
 * NOT CLAIMED (spec §10, "outside the theorem"):
 *
 *     Bind(T)  =/=>  Body(T) reads only Reads(T)
 *
 * Bind establishes declaration/interface correspondence.  It cannot prove
 * that an arbitrary C body obeys its declared dependency set; that needs
 * static analysis or instrumentation, and is outside the substrate.
 */

typedef struct {
    const char *name;   /* member name within ArgType */
    const char *type;   /* declared type of that member */

    /* Which dependency this field EXPLICITLY represents.  nullptr means the
     * field represents no declared dependency.  Semantic identity is
     * DECLARED, never guessed from spelling: a field that merely looks
     * related does not qualify, which is what the specification's
     * "explicitly designated component" requires. */
    const char *represents;
} RmeField;

typedef struct {
    const char     *name;
    const RmeField *fields;
    size_t          field_count;
} RmeArgType;

/* One element of Reads(T): the dependency's own name, and the type its
 * contract requires of whatever represents it. */
typedef struct {
    const char *dep;
    const char *type;
} RmeRead;

typedef struct {
    const char       *name;
    const RmeArgType *arg;        /* ArgType(T) */
    const RmeRead    *reads;      /* Reads(T)   */
    size_t            read_count;
} RmeTransitionBind;

typedef struct {
    bool        ok;
    size_t      read;   /* index of the unrepresented read, or read_count */
    const char *why;    /* never null when ok == false */
} RmeBindResult;

/* Represents(f, r): declared semantic identity AND declared type.  Both are
 * required.  Either alone admits a coincidence — a field spelled like the
 * dependency but designating something else, or one of the right type that
 * represents a different dependency entirely. */
bool rme_represents(const RmeField *f, const RmeRead *r);

RmeBindResult rme_bind_valid(const RmeTransitionBind *t);

#endif /* RME_BIND_H */
