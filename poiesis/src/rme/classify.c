#include <stdint.h>
#include <stdlib.h>
#include <string.h>

#include "classify.h"

const char *rme_level_name(RmeLevel l)
{
    switch (l) {
    case RME_LEVEL_4:  return "RME-4";
    case RME_LEVEL_5:  return "RME-5";
    case RME_LEVEL_6:  return "RME-6";
    case RME_LEVEL_6B: return "RME-6B";
    case RME_LEVEL_7:  return "RME-7";
    default:           return "<invalid-level>";
    }
}

/* Tarjan's SCC, iterative so that a long chain (K1 uses a thousand nodes)
 * cannot exhaust the stack.  We need only the verdict: does any SCC have
 * more than one member, or is there a self-loop?  Either is a directed
 * cycle in the projection handed to us. */
typedef struct {
    size_t *off;      /* CSR offsets, n+1 */
    size_t *adj;      /* CSR targets, m   */
    size_t *index;
    size_t *low;
    bool   *onstack;
    size_t *stk;      /* Tarjan stack     */
    size_t *frame_v;  /* DFS frame: vertex */
    size_t *frame_e;  /* DFS frame: next adjacency slot */
} Tarjan;

static bool tarjan_has_cycle(size_t n, const RmeEdge *e, size_t m)
{
    if (n == 0) {
        return false;
    }
    /* A self-loop is a one-member SCC that still constitutes a cycle, and
     * Tarjan alone would not report it as size > 1. */
    for (size_t i = 0; i < m; i++) {
        if (e[i].from == e[i].to) {
            return true;
        }
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

    bool found = false;
    if (!t.off || !t.adj || !t.index || !t.low || !t.onstack ||
        !t.stk || !t.frame_v || !t.frame_e) {
        goto done;
    }

    /* CSR build: counting sort of edges by source. */
    for (size_t i = 0; i < m; i++) {
        t.off[e[i].from + 1]++;
    }
    for (size_t v = 0; v < n; v++) {
        t.off[v + 1] += t.off[v];
    }
    {
        size_t *cursor = calloc(n, sizeof *cursor);
        if (!cursor) {
            goto done;
        }
        for (size_t i = 0; i < m; i++) {
            size_t f = e[i].from;
            t.adj[t.off[f] + cursor[f]] = e[i].to;
            cursor[f]++;
        }
        free(cursor);
    }

    /* index[] is 1-based so 0 means "unvisited". */
    size_t next_index = 1;
    size_t sp = 0;    /* Tarjan stack pointer */

    for (size_t root = 0; root < n && !found; root++) {
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

            /* v is finished. */
            if (t.low[v] == t.index[v]) {
                size_t members = 0;
                size_t w;
                do {
                    w = t.stk[--sp];
                    t.onstack[w] = false;
                    members++;
                } while (w != v);
                if (members > 1) {
                    found = true;
                    break;
                }
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

done:
    free(t.off); free(t.adj); free(t.index); free(t.low);
    free(t.onstack); free(t.stk); free(t.frame_v); free(t.frame_e);
    return found;
}

RmeLevel rme_classify(const RmeSystem *s)
{
    static RmeEdge edges[RME_MAX_EDGES];

    if (s == nullptr || s->slot_count == 0) {
        return RME_LEVEL_4;
    }

    /* The decisive projection: governed slots and state->state edges only.
     * A cycle here — and only here — is RME-7. */
    size_t m_gs = rme_project(s, true, edges, RME_MAX_EDGES);
    if (m_gs != SIZE_MAX && tarjan_has_cycle(s->slot_count, edges, m_gs)) {
        return RME_LEVEL_7;
    }
    size_t governed_edges = (m_gs == SIZE_MAX) ? 0 : m_gs;

    /* Not RME-7.  A cycle that needs an environmental node to close is
     * RME-6B — a causal feedback loop, but not internal governed-state
     * reciprocity. */
    size_t m_all = rme_project(s, false, edges, RME_MAX_EDGES);
    if (m_all != SIZE_MAX && tarjan_has_cycle(s->slot_count, edges, m_all)) {
        return RME_LEVEL_6B;
    }

    if (governed_edges > 0) {
        return RME_LEVEL_6;   /* one-way governed composition */
    }
    if (s->adapts_parameters) {
        return RME_LEVEL_5;
    }
    return RME_LEVEL_4;
}
