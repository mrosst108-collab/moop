#include <string.h>
#include "actor.h"

void moop_actor_init(MoopActor *actor,
                     bool *cells_a, bool *marks_a, size_t len_a,
                     bool *cells_b, bool *marks_b, size_t len_b,
                     MoopMessage *table, size_t capacity)
{
    moop_core_init(&actor->core, cells_a, marks_a, len_a,
                   cells_b, marks_b, len_b);
    actor->messages = table;
    actor->hosted = 0;
    actor->capacity = capacity;
}

bool moop_actor_host(MoopActor *actor, const char *name, MoopHandler fn)
{
    if (actor->hosted == actor->capacity)
        return false;
    actor->messages[actor->hosted++] = (MoopMessage){ .name = name, .fn = fn };
    return true;
}

bool moop_actor_send(MoopActor *actor, const char *name, bool *reply)
{
    /* Local lookup only: a miss is a miss. No parent chain exists. */
    for (size_t i = 0; i < actor->hosted; i++) {
        if (strcmp(actor->messages[i].name, name) == 0) {
            *reply = actor->messages[i].fn(actor);
            return true;
        }
    }
    return false;
}
