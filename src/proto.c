#include <string.h>
#include "logic.h"
#include "proto.h"

/* Generation seeds the child's tapes by observing the generator's
 * reversible dynamics through the MAYBE bridge — one draw per cell.
 * Deterministic given the generator's state, and reversible for the
 * generator: stepping it back len_a + len_b ticks returns it to the
 * moment before the birth. */
static void seed(MoopCore *generator, MoopCore *child)
{
    for (size_t i = 0; i < child->a.len; i++)
        child->a.cells[i] = moop_maybe(generator);
    for (size_t i = 0; i < child->b.len; i++)
        child->b.cells[i] = moop_maybe(generator);
}

static void proto_init(MoopProto *proto,
                       bool *cells_a, bool *marks_a, size_t len_a,
                       bool *cells_b, bool *marks_b, size_t len_b,
                       MoopProtoMessage *table, size_t capacity)
{
    moop_core_init(&proto->core, cells_a, marks_a, len_a,
                   cells_b, marks_b, len_b);
    proto->messages = table;
    proto->hosted = 0;
    proto->capacity = capacity;
}

void moop_actor_generate_root(MoopActor *actor, MoopProto *root,
                              bool *cells_a, bool *marks_a, size_t len_a,
                              bool *cells_b, bool *marks_b, size_t len_b,
                              MoopProtoMessage *table, size_t capacity)
{
    proto_init(root, cells_a, marks_a, len_a, cells_b, marks_b, len_b,
               table, capacity);
    seed(&actor->core, &root->core);
    root->parent = NULL; /* nothing delegates into an actor */
    root->facing = MOOP_FACING_SYSTEM;
}

void moop_proto_generate(MoopProto *generator, MoopProto *child,
                         bool *cells_a, bool *marks_a, size_t len_a,
                         bool *cells_b, bool *marks_b, size_t len_b,
                         MoopProtoMessage *table, size_t capacity)
{
    proto_init(child, cells_a, marks_a, len_a, cells_b, marks_b, len_b,
               table, capacity);
    seed(&generator->core, &child->core);
    if (generator->facing == MOOP_FACING_SYSTEM) {
        /* the system root generates user-facing roots: delegation
         * must not cross the layer boundary */
        child->parent = NULL;
        child->facing = MOOP_FACING_USER;
    } else {
        child->parent = generator;
        child->facing = MOOP_FACING_USER;
    }
}

bool moop_proto_host(MoopProto *proto, const char *name, MoopProtoHandler fn)
{
    if (proto->hosted == proto->capacity)
        return false;
    proto->messages[proto->hosted++] =
        (MoopProtoMessage){ .name = name, .fn = fn };
    return true;
}

bool moop_proto_send(MoopProto *proto, const char *name, bool *reply)
{
    for (MoopProto *p = proto; p != NULL; p = p->parent) {
        for (size_t i = 0; i < p->hosted; i++) {
            if (strcmp(p->messages[i].name, name) == 0) {
                *reply = p->messages[i].fn(proto); /* self = receiver */
                return true;
            }
        }
    }
    return false;
}
