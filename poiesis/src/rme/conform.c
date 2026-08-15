#include <string.h>

#include "conform.h"

bool rme_schema_valid(const RmePrototype *p, const char **why)
{
    if (p == nullptr) {
        if (why) *why = "null prototype";
        return false;
    }
    /* Schema identity is required.  "P claims RME-7" is underspecified
     * without it, and it is kept distinct from prototype identity. */
    if (p->schema.name == nullptr) {
        if (why) *why = "no schema identity: prototype does not declare which schema it satisfies";
        return false;
    }
    if (strcmp(p->schema.name, RME_SCHEMA_NAME) != 0) {
        if (why) *why = "schema identity names a different schema than this build implements";
        return false;
    }
    if (p->schema.major != RME_SCHEMA_MAJOR) {
        if (why) *why = "schema major version mismatch";
        return false;
    }
    return true;
}

bool rme_port_complete(const RmePrototype *p, RmePortId *bad, const char **why)
{
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        const RmePortHeader *h = rme_port_at_const(p, (RmePortId)i);

        /* F2: {ACTIVE, VESTIGIAL} is the entire legal semantic domain.
         * A port omitted from a designated initializer zero-fills to
         * UNDEFINED and is caught right here — the sentinel never reaches
         * the public API. */
        if (!rme_status_is_legal(h->status)) {
            if (bad) *bad = (RmePortId)i;
            if (why) *why = (h->status == RME_UNDEFINED)
                ? "port omitted: status is the UNDEFINED construction sentinel"
                : "port status is outside {ACTIVE, VESTIGIAL}";
            return false;
        }

        /* The header must know which port it is, or diagnostics and
         * uniform access silently disagree with the schema. */
        if (h->id != (RmePortId)i) {
            if (bad) *bad = (RmePortId)i;
            if (why) *why = "port header id does not match its schema slot";
            return false;
        }
    }
    return true;
}

bool rme_type_safe(const RmePrototype *p, RmePortId *bad, const char **why)
{
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        /* Both statuses require a valid object of the port's declared
         * interface type.  Null is a type failure, not a spelling of
         * "vestigial". */
        if (rme_port_api(p, (RmePortId)i) == nullptr) {
            if (bad) *bad = (RmePortId)i;
            if (why) *why = "port realization is null; declared interface type is not inhabited";
            return false;
        }
    }
    return true;
}

RmeConformance rme7_conforms(const RmePrototype *p)
{
    RmeConformance r = { false, RME_PORT_COUNT, "unevaluated" };

    if (!rme_schema_valid(p, &r.why)) {
        return r;
    }
    if (!rme_port_complete(p, &r.port, &r.why)) {
        return r;
    }
    if (!rme_type_safe(p, &r.port, &r.why)) {
        return r;
    }
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        /* Status SELECTS the contract; there is no universal null rule. */
        if (!rme_realization_valid(p, (RmePortId)i, &r.why)) {
            r.port = (RmePortId)i;
            return r;
        }
    }

    r.ok = true;
    r.port = RME_PORT_COUNT;
    r.why = "conformant";
    return r;
}
