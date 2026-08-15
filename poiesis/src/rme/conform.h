#ifndef RME_CONFORM_H
#define RME_CONFORM_H

#include "contract.h"

/* poiesis — AXIS A: conformance.
 *
 *   RME7(P) <=> SchemaValid(P) ^ PortComplete(P) ^ TypeSafe(P) ^ RealizationValid(P)
 *
 * UNARY, by construction: the signature admits exactly one prototype, so
 * conformance cannot come to depend on a second one.  Deliberately absent:
 * UsesEveryOperator(P), and any composition clause — composition validity
 * is relational and lives in compose.h.
 *
 * Note the name.  rme7_conforms() is NOT rme_classify(): a prototype whose
 * observed dynamics classify as RME-6 is normally RME-7-conformant, and an
 * asserted classification can never make a prototype conformant.
 */

typedef struct {
    bool        ok;
    RmePortId   port;    /* which port failed; RME_PORT_COUNT if not port-specific */
    const char *why;     /* never null when ok == false */
} RmeConformance;

RmeConformance rme7_conforms(const RmePrototype *p);

/* The four conjuncts, separately testable. */
bool rme_schema_valid(const RmePrototype *p, const char **why);
bool rme_port_complete(const RmePrototype *p, RmePortId *bad, const char **why);
bool rme_type_safe(const RmePrototype *p, RmePortId *bad, const char **why);

#endif /* RME_CONFORM_H */
