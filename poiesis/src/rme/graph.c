#include <stdint.h>

#include "graph.h"

size_t rme_project(const RmeSystem *s, bool governed_only,
                   RmeEdge *out, size_t cap)
{
    size_t n = 0;

    for (size_t t = 0; t < s->transition_count; t++) {
        const RmeTransitionDecl *d = &s->transitions[t];
        if (d->target >= s->slot_count) {
            continue;
        }
        /* The target must be a state slot of the projection.  In G_GS that
         * means governed; an environmental target contributes no edge. */
        if (governed_only && !s->slots[d->target].governed) {
            continue;
        }
        for (size_t r = 0; r < d->read_count; r++) {
            size_t src = d->reads[r];
            if (src >= s->slot_count) {
                continue;
            }
            if (governed_only && !s->slots[src].governed) {
                continue;
            }
            if (n >= cap) {
                return SIZE_MAX;
            }
            /* Y -> X iff T_X reads Y. */
            out[n].from = src;
            out[n].to   = d->target;
            n++;
        }
    }
    return n;
}
