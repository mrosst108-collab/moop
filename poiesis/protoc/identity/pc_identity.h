#ifndef PC_IDENTITY_H
#define PC_IDENTITY_H

#include <stdint.h>

#include "../types/pc_surface.h"

/* ProtoC — identity/   Derived from S5 and S6.
 *
 * S5:  A RELEASED IDENTITY MUST NEVER BECOME A VALID IDENTITY FOR A LATER
 *      OBJECT.
 *
 * That is an INVARIANT, not a mechanism.  ProtoC reaches it a different way
 * than a substrate whose handle is a pointer into a slot must:
 *
 *      IDENTITY IS A VALUE, NOT A REFERENCE.
 *
 * A PcIdentity is a (slot, serial) pair held BY VALUE.  The serial comes
 * from a strictly increasing counter and is stamped into the slot.  A
 * released identity keeps its old serial; the slot's serial has moved on;
 * they never compare equal again.  Because the comparison is between two
 * VALUES rather than through a shared address, SLOTS MAY BE RECYCLED
 * FREELY and S5 still holds.
 *
 * A substrate that hands out pointers cannot do this: the released handle
 * and the reused slot ARE THE SAME ADDRESS, so any generation stamped into
 * the slot is read through the stale handle as the current one.  Such a
 * substrate must forbid reuse instead.  Both satisfy S5; neither mechanism
 * is required by it.
 *
 * S6: the registry holds surfaces the CLIENT owns.  It stores the address
 * and never copies, frees or dereferences the realization machinery those
 * surfaces name.
 */

typedef struct {
    size_t   slot;
    uint64_t serial;   /* 0 is never issued, so a zero-filled identity is dead */
} PcIdentity;

typedef struct {
    PcSurface **surface;   /* client-owned, held not copied (S6) */
    uint64_t   *serial;
    size_t      capacity;
    size_t      in_use;
    uint64_t    next_serial;
} PcRegistry;

void pc_registry_init(PcRegistry *r, PcSurface **surface_store,
                      uint64_t *serial_store, size_t capacity);

/* Admits a surface and mints its identity.  Returns a dead identity when
 * there is no room -- S8: refused, never a plausible-looking answer. */
PcIdentity pc_identity_mint(PcRegistry *r, PcSurface *s);

/* Releases an identity.  The slot becomes reusable immediately; the
 * identity does not. */
bool pc_identity_release(PcRegistry *r, PcIdentity id);

bool       pc_identity_live(const PcRegistry *r, PcIdentity id);
PcSurface *pc_identity_surface(const PcRegistry *r, PcIdentity id);

/* A dead identity, for callers that need one. */
PcIdentity pc_identity_none(void);

#endif /* PC_IDENTITY_H */
