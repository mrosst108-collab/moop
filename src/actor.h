#ifndef MOOP_ACTOR_H
#define MOOP_ACTOR_H

#include <stdbool.h>
#include <stddef.h>
#include "tapeloop.h"

/* Actors are moop's bridging construct between the layers.
 *
 * An actor's body IS a reversible core: it inherits reversibility and
 * homoiconicity constitutionally — from the substrate, not from other
 * actors. Actors are non-hereditary: message lookup is strictly local,
 * and a miss never delegates, because there is no parent to delegate to.
 * The `<-` operator has no meaning for actors.
 *
 * What an actor hosts is the irreversible, user-facing surface: named
 * messages. Sending is a user-layer act — replies are plain values,
 * consumed into the forgetful world. Handlers may act on the body only
 * through reversible operations (gates, steps) and observation; hosting
 * and un-hosting are themselves irreversible, user-layer acts. This
 * generalizes the MAYBE bridge: reversible effect inside, irreversible
 * observation outside. */

typedef struct MoopActor MoopActor;

typedef bool (*MoopHandler)(MoopActor *self);

typedef struct {
    const char *name;
    MoopHandler fn;
} MoopMessage;

struct MoopActor {
    MoopCore core;          /* the body: reversible, homoiconic */
    MoopMessage *messages;  /* caller-owned; the hosted surface */
    size_t hosted;
    size_t capacity;
};

void moop_actor_init(MoopActor *actor,
                     bool *cells_a, bool *marks_a, size_t len_a,
                     bool *cells_b, bool *marks_b, size_t len_b,
                     MoopMessage *table, size_t capacity);

/* Host a message. Returns false if the table is full. */
bool moop_actor_host(MoopActor *actor, const char *name, MoopHandler fn);

/* Send a message. Strictly local lookup (non-hereditary): returns false
 * if the actor does not host `name`; otherwise calls the handler and
 * stores its reply in *reply. */
bool moop_actor_send(MoopActor *actor, const char *name, bool *reply);

#endif
