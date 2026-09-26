#include <stdint.h>
#include <stdlib.h>

#include "graph.h"

size_t rme_project(const RmeSystem *s, bool governed_only,
                   RmeEdge *out, size_t cap)
{
    size_t n = 0;

    for (size_t t = 0; t < s->transition_count; t++) {
        const RmeTransitionDecl *d = &s->transitions[t];
        /* An index outside the declared slot table is a MALFORMED system,
         * not an edge to skip.  Dropping it silently would hand back a
         * truncated projection that answers confidently and wrongly -- the
         * same silent-wrong-answer shape once removed from the old
         * classifier (capacity) and edge-list cycle predicate (allocation),
         * both since replaced by rme_has_cycle, which builds no projection. */
        if (d->target >= s->slot_count) {
            return SIZE_MAX;
        }
        if (d->read_count > 0 && d->reads == nullptr) {
            return SIZE_MAX;
        }
        /* The target must be a state slot of the projection.  In G_GS that
         * means governed; an environmental target contributes no edge. */
        if (governed_only && !s->slots[d->target].governed) {
            continue;
        }
        for (size_t r = 0; r < d->read_count; r++) {
            size_t src = d->reads[r];
            if (src >= s->slot_count) {
                return SIZE_MAX;
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

/* Tarjan's SCC, iterative so that a long chain (K1 uses a thousand nodes)
 * cannot exhaust the stack. */
typedef struct {
    size_t *off;      /* CSR offsets, n+1 */
    size_t *adj;      /* CSR targets, m   */
    size_t *index;
    size_t *low;
    bool   *onstack;
    size_t *stk;      /* Tarjan stack     */
    size_t *frame_v;  /* DFS frame: vertex */
    size_t *frame_e;  /* DFS frame: next adjacency slot */
    size_t *cursor;   /* CSR fill cursor  */
} Tarjan;

static void tarjan_release(Tarjan *t)
{
    free(t->off); free(t->adj); free(t->index); free(t->low);
    free(t->onstack); free(t->stk); free(t->frame_v); free(t->frame_e);
    free(t->cursor);
}

bool rme_graph_scc(size_t n, const RmeEdge *e, size_t m,
                   size_t *comp, size_t *component_count)
{
    if (comp == nullptr || component_count == nullptr) {
        return false;
    }
    if (m > 0 && e == nullptr) {
        return false;
    }
    /* Endpoints outside [0,n) would index the CSR arrays out of bounds.
     * Refuse rather than corrupt the heap: the caller supplies n and e
     * independently, so nothing else makes them consistent. */
    for (size_t i = 0; i < m; i++) {
        if (e[i].from >= n || e[i].to >= n) {
            return false;
        }
    }
    if (n == 0) {
        *component_count = 0;
        return true;
    }

    Tarjan t = { 0 };
    t.off     = calloc(n + 1, sizeof *t.off);
    t.adj     = calloc(m ? m : 1, sizeof *t.adj);
    t.index   = calloc(n, sizeof *t.index);
    t.low     = calloc(n, sizeof *t.low);
    t.onstack = calloc(n, sizeof *t.onstack);
    t.stk     = calloc(n, sizeof *t.stk);
    t.frame_v = calloc(n + 1, sizeof *t.frame_v);
    t.frame_e = calloc(n + 1, sizeof *t.frame_e);
    t.cursor  = calloc(n, sizeof *t.cursor);

    if (!t.off || !t.adj || !t.index || !t.low || !t.onstack ||
        !t.stk || !t.frame_v || !t.frame_e || !t.cursor) {
        tarjan_release(&t);
        return false;
    }

    /* CSR build: counting sort of edges by source. */
    for (size_t i = 0; i < m; i++) {
        t.off[e[i].from + 1]++;
    }
    for (size_t v = 0; v < n; v++) {
        t.off[v + 1] += t.off[v];
    }
    for (size_t i = 0; i < m; i++) {
        size_t f = e[i].from;
        t.adj[t.off[f] + t.cursor[f]] = e[i].to;
        t.cursor[f]++;
    }

    /* index[] is 1-based so 0 means "unvisited". */
    size_t next_index = 1;
    size_t sp = 0;      /* Tarjan stack pointer */
    size_t ncomp = 0;

    for (size_t root = 0; root < n; root++) {
        if (t.index[root] != 0) {
            continue;
        }
        size_t fp = 0;                 /* DFS frame pointer */
        t.frame_v[fp] = root;
        t.frame_e[fp] = t.off[root];
        t.index[root] = t.low[root] = next_index++;
        t.stk[sp++] = root;
        t.onstack[root] = true;

        while (true) {
            size_t v = t.frame_v[fp];
            if (t.frame_e[fp] < t.off[v + 1]) {
                size_t w = t.adj[t.frame_e[fp]];
                t.frame_e[fp]++;
                if (t.index[w] == 0) {
                    t.index[w] = t.low[w] = next_index++;
                    t.stk[sp++] = w;
                    t.onstack[w] = true;
                    fp++;
                    t.frame_v[fp] = w;
                    t.frame_e[fp] = t.off[w];
                } else if (t.onstack[w]) {
                    if (t.index[w] < t.low[v]) {
                        t.low[v] = t.index[w];
                    }
                }
                continue;
            }

            /* v is finished; if it roots an SCC, emit that component. */
            if (t.low[v] == t.index[v]) {
                size_t w;
                do {
                    w = t.stk[--sp];
                    t.onstack[w] = false;
                    comp[w] = ncomp;
                } while (w != v);
                ncomp++;
            }
            if (fp == 0) {
                break;
            }
            fp--;
            size_t parent = t.frame_v[fp];
            if (t.low[v] < t.low[parent]) {
                t.low[parent] = t.low[v];
            }
        }
    }

    tarjan_release(&t);
    *component_count = ncomp;
    return true;
}

/* The WHOLE declaration, validated before either selection is computed: a
 * malformed read is refused even where the governed selection would skip
 * the transition holding it.  Answering around a malformed declaration is
 * a confident answer computed from an incomplete relation. */
static bool declaration_ok(const RmeSystem *s)
{
    if (s->slot_count > 0 && s->slots == nullptr) {
        return false;
    }
    if (s->transition_count > 0 && s->transitions == nullptr) {
        return false;
    }
    for (size_t t = 0; t < s->transition_count; t++) {
        const RmeTransitionDecl *d = &s->transitions[t];
        if (d->target >= s->slot_count) {
            return false;
        }
        if (d->read_count > 0 && d->reads == nullptr) {
            return false;
        }
        for (size_t r = 0; r < d->read_count; r++) {
            if (d->reads[r] >= s->slot_count) {
                return false;
            }
        }
    }
    return true;
}

bool rme_has_cycle(const RmeSystem *s, bool governed_only, bool *out)
{
    if (s == nullptr || out == nullptr) {
        return false;
    }
    if (s->slot_count > RME_MAX_SLOTS) {
        return false;   /* unrepresentable: refuse, never downgrade */
    }
    if (!declaration_ok(s)) {
        return false;   /* malformed: refuse, never answer around it */
    }
    const size_t n = s->slot_count;
    if (n == 0) {
        *out = false;
        return true;
    }

    const size_t w = (n + 63) / 64;
    uint64_t *row = calloc(n * w, sizeof *row);
    if (row == nullptr) {
        return false;   /* no answer — never silently "acyclic" */
    }

    /* row[X] holds bit Y iff T_X declares a read of Y and both slots are
     * selected.  The selection is applied HERE, while the rows are built,
     * so no projected structure exists to be truncated.  (This reads the
     * arrow as X -> Y where the projection writes Y -> X; cycle existence
     * is invariant under reversing every edge, so nothing depends on it.) */
    for (size_t t = 0; t < s->transition_count; t++) {
        const RmeTransitionDecl *d = &s->transitions[t];
        if (governed_only && !s->slots[d->target].governed) {
            continue;
        }
        uint64_t *rx = &row[d->target * w];
        for (size_t r = 0; r < d->read_count; r++) {
            const size_t y = d->reads[r];
            if (governed_only && !s->slots[y].governed) {
                continue;
            }
            rx[y / 64] |= (uint64_t)1 << (y % 64);
        }
    }

    /* Transitive closure: row[i] ends as the set of slots i reaches by a
     * path of length >= 1. */
    for (size_t k = 0; k < n; k++) {
        const uint64_t *rk = &row[k * w];
        for (size_t i = 0; i < n; i++) {
            uint64_t *ri = &row[i * w];
            if (ri[k / 64] & ((uint64_t)1 << (k % 64))) {
                for (size_t q = 0; q < w; q++) {
                    ri[q] |= rk[q];
                }
            }
        }
    }

    /* A cycle exists iff some slot reaches itself.  A self-read needs NO
     * special case: it is already a path of length 1.  An unselected slot
     * has an empty row and appears in none, so it can never qualify. */
    bool found = false;
    for (size_t i = 0; i < n && !found; i++) {
        found = ((row[i * w + i / 64] >> (i % 64)) & 1u) != 0;
    }
    free(row);
    *out = found;
    return true;
}
