#include "pc_identity.h"

PcIdentity pc_identity_none(void)
{
    PcIdentity id = { 0, 0 };
    return id;
}

void pc_registry_init(PcRegistry *r, PcSurface **surface_store,
                      uint64_t *serial_store, size_t capacity)
{
    if (r == nullptr) {
        return;
    }
    r->surface = surface_store;
    r->serial = serial_store;
    r->capacity = capacity;
    r->in_use = 0;
    r->next_serial = 1;   /* 0 is never issued */
    for (size_t i = 0; i < capacity; i++) {
        r->surface[i] = nullptr;
        r->serial[i] = 0;
    }
}

PcIdentity pc_identity_mint(PcRegistry *r, PcSurface *s)
{
    if (r == nullptr || r->surface == nullptr || s == nullptr) {
        return pc_identity_none();
    }
    /* Slot reuse is SAFE here, and that is the point: identity is compared
     * by value, so a recycled slot cannot resurrect a released identity. */
    for (size_t i = 0; i < r->capacity; i++) {
        if (r->surface[i] == nullptr) {
            r->surface[i] = s;
            r->serial[i] = r->next_serial++;
            r->in_use++;
            PcIdentity id = { i, r->serial[i] };
            return id;
        }
    }
    return pc_identity_none();   /* refused, not a plausible identity (S8) */
}

bool pc_identity_live(const PcRegistry *r, PcIdentity id)
{
    if (r == nullptr || r->serial == nullptr || id.serial == 0) {
        return false;
    }
    if (id.slot >= r->capacity) {
        return false;
    }
    return r->serial[id.slot] == id.serial && r->surface[id.slot] != nullptr;
}

bool pc_identity_release(PcRegistry *r, PcIdentity id)
{
    if (!pc_identity_live(r, id)) {
        return false;
    }
    r->surface[id.slot] = nullptr;
    r->serial[id.slot] = 0;    /* the released serial is never reissued */
    r->in_use--;
    return true;
}

PcSurface *pc_identity_surface(const PcRegistry *r, PcIdentity id)
{
    return pc_identity_live(r, id) ? r->surface[id.slot] : nullptr;
}
