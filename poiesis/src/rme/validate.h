#ifndef RME_VALIDATE_H
#define RME_VALIDATE_H

#include "actor.h"
#include "compose.h"

/* poiesis — THE VALIDATION BOUNDARY (spec §8.3, F7-F11).
 *
 *     untrusted / external representation --> validation --> validated prototype
 *
 * The audit question this file exists to answer "no" to:
 *
 *     Can an unvalidated representation obtain the representation/type
 *     accepted by downstream RME operations WITHOUT passing through
 *     validation?
 *
 * Three mechanisms, all structural rather than conventional:
 *
 *  1. RmeValidated is an OPAQUE INCOMPLETE TYPE.  Its definition lives only
 *     in validate.c, so a client cannot declare one, cannot initialize one
 *     field-wise, and cannot copy one.  rme_validate() is its sole
 *     producer.  Copying the POINTER merely aliases the same validated
 *     prototype — which is correct: you cannot obtain a handle to a child
 *     by copying its parent's handle.  This is what makes F7/F8 a
 *     type-level barrier instead of a convention.
 *
 *  2. rme_validate() stores a COPY in substrate-owned storage.  The
 *     validated prototype is therefore not the caller's object, closing the
 *     mutate-after-validate window a pointer-only handle would leave open.
 *
 *  3. There is NO validity field anywhere in actor.h to launder.  The
 *     forbidden line `child->validated = parent->validated;` does not
 *     compile, because no such member exists on any type.
 *
 * F9 is bidirectional, and this header is one half of the evidence: no
 * function here returns, derives or widens a capability.  Validation
 * establishes semantic validity; it grants no construction authority.
 *
 * Two stages kept apart, per §8.1's four-concept table:
 *
 *     validation   does the REPRESENTATION satisfy the schema and the
 *                  representation invariant?      -> rme_validate()
 *     conformance  does the validated prototype satisfy the RME-7
 *                  REALIZATION contract?          -> rme_validated_conforms()
 */

typedef struct RmeValidated RmeValidated;   /* OPAQUE — defined in validate.c */

typedef struct {
    bool        ok;
    RmePortId   port;   /* offending port, or RME_PORT_COUNT */
    const char *why;    /* never null when ok == false */
} RmeValidation;

/* The SOLE producer of a validated prototype.  Returns nullptr — writing
 * the reason to *err when given — if the representation fails validation.
 *
 * Note the parameter: a RAW prototype.  Nothing about an actor, capability,
 * context, parent or provenance is accepted, because none of them bears on
 * the answer (F8).  A trusted construction path cannot be presented here in
 * lieu of a valid representation, since there is no parameter through which
 * to present it. */
const RmeValidated *rme_validate(const RmePrototype *raw, RmeValidation *err);

/* Validation of a construction's product.  Provided for symmetry with the
 * authority machine, and deliberately equivalent to validating the raw
 * representation: the RmeConstructed wrapper contributes NOTHING to the
 * verdict.  Its authorization and provenance fields are not consulted. */
const RmeValidated *rme_validate_constructed(const RmeConstructed *c, RmeValidation *err);

const RmePrototype *rme_validated_proto(const RmeValidated *v);
const char         *rme_validated_name(const RmeValidated *v);

/* The realization-contract predicate, applied to something that has already
 * crossed the representation boundary. */
RmeConformance rme_validated_conforms(const RmeValidated *v);

/* A downstream semantic operation that accepts ONLY the validated type.
 * The raw-prototype entry point in compose.h remains for Axis B's own
 * tests; this is the form that demonstrates the boundary. */
RmeComposition rme_compose_valid_v(const RmeValidated *P, const RmeValidated *Q,
                                   const RmeRelation *R);

/* Substrate storage management (test support). */
void   rme_validation_reset(void);
size_t rme_validation_count(void);

#endif /* RME_VALIDATE_H */
