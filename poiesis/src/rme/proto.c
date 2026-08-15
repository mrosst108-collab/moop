#include <assert.h>

#include "proto.h"

/* Offset of each port field within RmePrototype, and offset of the api
 * pointer within each port struct.  Both tables expand from RME_PORTS, so
 * the single-source-of-truth rule holds. */

#define RME_PORT_OFFSET(n) [RME_PORT_##n] = offsetof(RmePrototype, n),
static const size_t rme_port_offset[RME_PORT_COUNT] = {
    RME_PORTS(RME_PORT_OFFSET)
};
#undef RME_PORT_OFFSET

#define RME_API_OFFSET(n) [RME_PORT_##n] = offsetof(RmePrototype, n.api),
static const size_t rme_api_offset[RME_PORT_COUNT] = {
    RME_PORTS(RME_API_OFFSET)
};
#undef RME_API_OFFSET

#define RME_PORT_NAME(n) [RME_PORT_##n] = #n,
static const char *const rme_port_names[RME_PORT_COUNT] = {
    RME_PORTS(RME_PORT_NAME)
};
#undef RME_PORT_NAME

/* The uniform-access rule: the header must be the first member of every
 * port struct, or (RmePortHeader *)&proto->state is not the header.
 * Checked at compile time, once per port, from the same macro. */
#define RME_HDR_FIRST(n) \
    static_assert(offsetof(RmePrototype, n.hdr) == offsetof(RmePrototype, n), \
                  "port header must be the first member of port " #n);
RME_PORTS(RME_HDR_FIRST)
#undef RME_HDR_FIRST

/* The name table and the enum cannot drift apart. */
static_assert(sizeof rme_port_names / sizeof rme_port_names[0] == RME_PORT_COUNT,
              "port name table out of step with RmePortId");
static_assert(sizeof rme_port_offset / sizeof rme_port_offset[0] == RME_PORT_COUNT,
              "port offset table out of step with RmePortId");

const char *rme_port_name(RmePortId id)
{
    if (id < 0 || id >= RME_PORT_COUNT) {
        return "<invalid-port>";
    }
    return rme_port_names[id];
}

const char *rme_status_name(RmePortStatus s)
{
    switch (s) {
    case RME_ACTIVE:    return "ACTIVE";
    case RME_VESTIGIAL: return "VESTIGIAL";
    case RME_UNDEFINED: return "UNDEFINED";
    default:            return "<invalid-status>";
    }
}

RmePortHeader *rme_port_at(RmePrototype *p, RmePortId id)
{
    assert(p != nullptr);
    assert(id >= 0 && id < RME_PORT_COUNT);
    return (RmePortHeader *)((unsigned char *)p + rme_port_offset[id]);
}

const RmePortHeader *rme_port_at_const(const RmePrototype *p, RmePortId id)
{
    assert(p != nullptr);
    assert(id >= 0 && id < RME_PORT_COUNT);
    return (const RmePortHeader *)((const unsigned char *)p + rme_port_offset[id]);
}

const void *rme_port_api(const RmePrototype *p, RmePortId id)
{
    assert(p != nullptr);
    assert(id >= 0 && id < RME_PORT_COUNT);
    const void *const *slot =
        (const void *const *)((const unsigned char *)p + rme_api_offset[id]);
    return *slot;
}

void rme_proto_set_status(RmePrototype *p, RmePortId id, RmePortStatus s)
{
    RmePortHeader *h = rme_port_at(p, id);
    h->status = s;
    h->id = id;
}
