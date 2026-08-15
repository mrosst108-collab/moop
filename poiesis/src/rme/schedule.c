#include <stdint.h>
#include <stdlib.h>

#include "schedule.h"

static void portset_add(RmePortSet *s, RmePortId id)
{
    s->ports[s->count++] = id;
    s->mask |= 1u << (unsigned)id;
}

RmePortSet rme_envelope(const RmePrototype *p)
{
    RmePortSet s = { { 0 }, 0, 0u };
    (void)p;
    /* Unconditional.  The envelope is the declared schema, and status has
     * no vote: a VESTIGIAL port is present, not absent. */
    for (int i = 0; i < RME_PORT_COUNT; i++) {
        portset_add(&s, (RmePortId)i);
    }
    return s;
}

RmePortSet rme_dispatch(const RmePrototype *p)
{
    RmePortSet s = { { 0 }, 0, 0u };

    for (int i = 0; i < RME_PORT_COUNT; i++) {
        /* rme_port_elidable() is the single authority: it consults the
         * port's own vestigial contract and returns false for every ACTIVE
         * port.  Nothing here re-derives elision from status, which is what
         * would smuggle in VESTIGIAL(p) => Elidable(p). */
        if (rme_port_elidable(p, (RmePortId)i)) {
            continue;
        }
        portset_add(&s, (RmePortId)i);
    }
    return s;
}

bool rme_portset_has(const RmePortSet *s, RmePortId id)
{
    if (s == nullptr || id < 0 || id >= RME_PORT_COUNT) {
        return false;
    }
    return (s->mask & (1u << (unsigned)id)) != 0u;
}

bool rme_portset_subset(const RmePortSet *lo, const RmePortSet *hi)
{
    if (lo == nullptr || hi == nullptr) {
        return false;
    }
    return (lo->mask & ~hi->mask) == 0u;
}

bool rme_dispatch_within_envelope(const RmePrototype *p)
{
    RmePortSet env = rme_envelope(p);
    RmePortSet dis = rme_dispatch(p);

    if (!rme_portset_subset(&dis, &env)) {
        return false;
    }
    /* The envelope must be the whole schema.  Checked explicitly rather
     * than trusted, because a future edit that let a status omit a port
     * from the envelope would satisfy the subset relation while destroying
     * the distinction the invariant exists to protect. */
    return env.count == (size_t)RME_PORT_COUNT;
}

void rme_schedule_release(RmeSchedule *s)
{
    if (s == nullptr) {
        return;
    }
    free(s->order);
    free(s->groups);
    s->order = nullptr;
    s->groups = nullptr;
    s->order_count = 0;
    s->group_count = 0;
}

bool rme_schedule_build(const RmeSystem *s, RmeSchedule *out)
{
    if (s == nullptr || out == nullptr) {
        return false;
    }
    *out = (RmeSchedule){ nullptr, 0, nullptr, 0 };

    size_t n = s->slot_count;
    if (n == 0) {
        return true;   /* an empty schedule, honestly empty */
    }
    if (n > RME_MAX_SLOTS) {
        return false;
    }

    size_t total_reads = 0;
    for (size_t t = 0; t < s->transition_count; t++) {
        total_reads += s->transitions[t].read_count;
    }

    RmeEdge *edges  = calloc(total_reads ? total_reads : 1, sizeof *edges);
    size_t  *comp   = calloc(n, sizeof *comp);
    size_t  *csize  = calloc(n, sizeof *csize);
    bool    *cself  = calloc(n, sizeof *cself);
    if (!edges || !comp || !csize || !cself) {
        goto fail;
    }

    /* The FULL projection: execution order must respect every declared
     * read.  Restricting to G_GS here would produce a schedule that ignores
     * environmental dependencies — a classification concept leaking into an
     * execution concern. */
    size_t m = rme_project(s, false, edges, total_reads ? total_reads : 1);
    if (m == SIZE_MAX) {
        goto fail;
    }

    size_t ncomp = 0;
    if (!rme_graph_scc(n, edges, m, comp, &ncomp)) {
        goto fail;
    }

    for (size_t v = 0; v < n; v++) {
        csize[comp[v]]++;
    }
    /* A self-dependency needs fixed-point iteration even though its SCC has
     * one member — the same case cardinality alone would miss. */
    for (size_t i = 0; i < m; i++) {
        if (edges[i].from == edges[i].to) {
            cself[comp[edges[i].from]] = true;
        }
    }

    size_t *order = calloc(n, sizeof *order);
    RmeScheduleGroup *groups = calloc(ncomp ? ncomp : 1, sizeof *groups);
    if (!order || !groups) {
        free(order); free(groups);
        goto fail;
    }

    /* Tarjan numbers components in reverse topological order, so counting
     * DOWN from the highest id yields dependencies before dependents. */
    size_t w = 0;
    size_t g = 0;
    for (size_t back = ncomp; back-- > 0; ) {
        groups[g].first = w;
        groups[g].count = csize[back];
        groups[g].iterate = (csize[back] > 1) || cself[back];
        for (size_t v = 0; v < n; v++) {
            if (comp[v] == back) {
                order[w++] = v;
            }
        }
        g++;
    }

    free(edges); free(comp); free(csize); free(cself);
    out->order = order;
    out->order_count = w;
    out->groups = groups;
    out->group_count = g;
    return true;

fail:
    free(edges); free(comp); free(csize); free(cself);
    return false;
}
