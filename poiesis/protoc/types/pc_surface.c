#include "pc_surface.h"

bool pc_status_is_semantic(PcStatus s)
{
    return s == PC_ACTIVE || s == PC_VESTIGIAL;
}

const char *pc_refusal_text(PcRefusal r)
{
    switch (r) {
    case PC_OK:                                  return "ok";
    case PC_REFUSED_NO_SURFACE:                  return "no surface";
    case PC_REFUSED_NO_SCHEMA:                   return "surface declares no schema";
    case PC_REFUSED_ARITY:                       return "instance vector disagrees with the schema";
    case PC_REFUSED_STATUS_UNSET:                return "port status is the construction sentinel";
    case PC_REFUSED_STATUS_DOMAIN:               return "port status outside {ACTIVE, VESTIGIAL}";
    case PC_REFUSED_NO_REALIZATION:              return "port names no realization";
    case PC_REFUSED_ACTIVE_IS_VESTIGIAL_FORM:    return "ACTIVE port names the declared vestigial form";
    case PC_REFUSED_VESTIGIAL_NOT_DECLARED_FORM: return "VESTIGIAL port does not name its declared form";
    }
    return "<unknown refusal>";
}

static PcVerdict verdict(PcRefusal r, size_t port)
{
    PcVerdict v = { r, port };
    return v;
}

PcVerdict pc_surface_wellformed(const PcSurface *s)
{
    if (s == nullptr || s->ports == nullptr) {
        return verdict(PC_REFUSED_NO_SURFACE, 0);
    }
    if (s->schema == nullptr || s->schema->ports == nullptr) {
        return verdict(PC_REFUSED_NO_SCHEMA, 0);
    }
    /* S8: an instance vector that disagrees with its schema is malformed.
     * Truncating to the shorter of the two would be exactly the silent
     * normalization S8 forbids. */
    if (s->port_count != s->schema->port_count) {
        return verdict(PC_REFUSED_ARITY, 0);
    }
    for (size_t i = 0; i < s->port_count; i++) {
        const PcPort *p = &s->ports[i];
        if (p->status == PC_STATUS_UNSET) {
            return verdict(PC_REFUSED_STATUS_UNSET, i);
        }
        if (!pc_status_is_semantic(p->status)) {
            return verdict(PC_REFUSED_STATUS_DOMAIN, i);
        }
        /* A port with no realization is not "vestigial by omission" -- S3
         * says vestigial is RETAINED AND TYPED, so absence is malformed. */
        if (p->realization == nullptr) {
            return verdict(PC_REFUSED_NO_REALIZATION, i);
        }
    }
    return verdict(PC_OK, s->port_count);
}

PcVerdict pc_port_realization_agrees(const PcSurface *s, size_t port)
{
    if (s == nullptr || s->ports == nullptr) {
        return verdict(PC_REFUSED_NO_SURFACE, 0);
    }
    if (port >= s->port_count) {
        return verdict(PC_REFUSED_ARITY, port);
    }
    const PcPort *p = &s->ports[port];
    if (!pc_status_is_semantic(p->status)) {
        return verdict(p->status == PC_STATUS_UNSET ? PC_REFUSED_STATUS_UNSET
                                                    : PC_REFUSED_STATUS_DOMAIN, port);
    }
    if (p->realization == nullptr) {
        return verdict(PC_REFUSED_NO_REALIZATION, port);
    }
    /* Both directions of S2's closure, checked independently.  A port with
     * no declared vestigial form cannot violate either direction, so the
     * comparison is skipped rather than assumed. */
    if (p->vestigial_form != nullptr) {
        if (p->status == PC_ACTIVE && p->realization == p->vestigial_form) {
            return verdict(PC_REFUSED_ACTIVE_IS_VESTIGIAL_FORM, port);
        }
        if (p->status == PC_VESTIGIAL && p->realization != p->vestigial_form) {
            return verdict(PC_REFUSED_VESTIGIAL_NOT_DECLARED_FORM, port);
        }
    }
    return verdict(PC_OK, port);
}

bool pc_port_elidable(const PcSurface *s, size_t port)
{
    if (s == nullptr || s->ports == nullptr || port >= s->port_count) {
        return false;
    }
    const PcPort *p = &s->ports[port];
    /* S7: permission AND vestigial status.  An ACTIVE port is never
     * elidable however the permission bit happens to be set, so the status
     * test is not redundant with the permission test. */
    return p->status == PC_VESTIGIAL && p->elidable_when_vestigial;
}

size_t pc_envelope_count(const PcSurface *s)
{
    return (s == nullptr) ? 0 : s->port_count;
}

bool pc_in_envelope(const PcSurface *s, size_t port)
{
    return s != nullptr && port < s->port_count;
}

bool pc_in_dispatch(const PcSurface *s, size_t port)
{
    return pc_in_envelope(s, port) && !pc_port_elidable(s, port);
}

size_t pc_dispatch_count(const PcSurface *s)
{
    size_t n = 0;
    for (size_t i = 0; i < pc_envelope_count(s); i++) {
        if (pc_in_dispatch(s, i)) {
            n++;
        }
    }
    return n;
}
