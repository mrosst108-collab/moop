#ifndef MOOP_PROTO_H
#define MOOP_PROTO_H

#include <stdbool.h>
#include <stddef.h>
#include "actor.h"
#include "tapeloop.h"

/* Protos: the generative object hierarchy.
 *
 * A system-facing actor generates the system-facing root proto; the
 * system-facing root generates user-facing root protos; user-facing
 * protos generate protos, which generate protos... All of them inherit
 * reversibility and homoiconicity by CONSTRUCTION: every generated
 * body is a reversible core on the substrate. That inheritance flows
 * down the generative chain, not the delegation chain.
 *
 * Generation and inheritance are distinct relations:
 *   - GENERATION is an act (who made you). It is the only downward
 *     path from the system layer to the user layer, and it has the
 *     sanctioned bridge shape: the child's initial tapes are seeded by
 *     observing the generator's reversible dynamics (MAYBE draws), so
 *     generating costs the generator nothing irreversible — step it
 *     back and it returns to the moment before the birth. Provenance
 *     needs no pointer: the substrate can always run backward.
 *   - INHERITANCE (`<-`) is a pointer (whom you defer to). Message
 *     lookup delegates up parent links among user-facing protos only.
 *     Delegation NEVER crosses the layer boundary: a user-facing root
 *     has no parent, and nothing delegates into the system-facing
 *     root or the actor.
 */

typedef enum {
    MOOP_FACING_SYSTEM,
    MOOP_FACING_USER,
} MoopFacing;

typedef struct MoopProto MoopProto;

typedef bool (*MoopProtoHandler)(MoopProto *self);

typedef struct {
    const char *name;
    MoopProtoHandler fn;
} MoopProtoMessage;

struct MoopProto {
    MoopCore core;              /* the body: reversible, homoiconic */
    MoopProtoMessage *messages; /* caller-owned; the hosted surface */
    size_t hosted;
    size_t capacity;
    MoopProto *parent;          /* delegation; NULL at either root */
    MoopFacing facing;
};

/* The system-facing actor generates the system-facing root proto. */
void moop_actor_generate_root(MoopActor *actor, MoopProto *root,
                              bool *cells_a, bool *marks_a, size_t len_a,
                              bool *cells_b, bool *marks_b, size_t len_b,
                              MoopProtoMessage *table, size_t capacity);

/* A proto generates a proto. A system-facing generator yields a
 * user-facing ROOT (parent NULL — delegation cannot cross the layer
 * boundary); a user-facing generator yields a hereditary child
 * (parent = generator). */
void moop_proto_generate(MoopProto *generator, MoopProto *child,
                         bool *cells_a, bool *marks_a, size_t len_a,
                         bool *cells_b, bool *marks_b, size_t len_b,
                         MoopProtoMessage *table, size_t capacity);

/* Host a message. Returns false if the table is full. */
bool moop_proto_host(MoopProto *proto, const char *name, MoopProtoHandler fn);

/* Send a message. Lookup delegates up the parent chain (hereditary),
 * but the handler always runs with the original receiver as self.
 * Returns false if no proto in the chain hosts `name`. */
bool moop_proto_send(MoopProto *proto, const char *name, bool *reply);

#endif
