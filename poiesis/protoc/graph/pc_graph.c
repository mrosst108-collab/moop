#include <string.h>

#include "pc_graph.h"

size_t pc_graph_words(size_t n)
{
    return (n + 63u) / 64u;
}

static bool bit(const uint64_t *w, size_t i)
{
    return (w[i / 64u] >> (i % 64u)) & 1u;
}
static void set_bit(uint64_t *w, size_t i)
{
    w[i / 64u] |= (uint64_t)1u << (i % 64u);
}

bool pc_graph_init(PcDepGraph *g, size_t n, uint64_t *rows, uint64_t *governed,
                   size_t words)
{
    if (g == nullptr || words < pc_graph_words(n)) {
        return false;
    }
    if (n > 0 && (rows == nullptr || governed == nullptr)) {
        return false;
    }
    g->n = n;
    g->rows = rows;
    g->governed = governed;
    g->words = words;
    if (n > 0) {
        memset(rows, 0, n * words * sizeof *rows);
        memset(governed, 0, words * sizeof *governed);
    }
    return true;
}

bool pc_graph_declare_dependency(PcDepGraph *g, size_t from, size_t to)
{
    if (g == nullptr || from >= g->n || to >= g->n) {
        return false;   /* malformed: refused, not dropped (S8) */
    }
    set_bit(&g->rows[from * g->words], to);
    return true;
}

bool pc_graph_mark_governed(PcDepGraph *g, size_t node)
{
    if (g == nullptr || node >= g->n) {
        return false;
    }
    set_bit(g->governed, node);
    return true;
}

bool pc_graph_is_governed(const PcDepGraph *g, size_t node)
{
    return g != nullptr && node < g->n && bit(g->governed, node);
}

bool pc_graph_has_cycle(const PcDepGraph *g, const uint64_t *mask,
                        uint64_t *scratch, bool *out)
{
    if (g == nullptr || out == nullptr) {
        return false;
    }
    if (g->n == 0) {
        *out = false;
        return true;
    }
    if (scratch == nullptr || g->rows == nullptr) {
        return false;   /* no answer available; never guess "acyclic" (S8) */
    }

    const size_t n = g->n, w = g->words;
    const bool selected_all = (mask == nullptr);

    /* Copy the selected sub-relation into scratch.  A node outside the mask
     * contributes no row and appears in no row: the restriction happens
     * HERE, during the computation, so there is no projected structure that
     * could be truncated or fall out of step with the original. */
    for (size_t i = 0; i < n; i++) {
        uint64_t *dst = &scratch[i * w];
        if (!selected_all && !bit(mask, i)) {
            memset(dst, 0, w * sizeof *dst);
            continue;
        }
        const uint64_t *src = &g->rows[i * w];
        for (size_t k = 0; k < w; k++) {
            dst[k] = selected_all ? src[k] : (src[k] & mask[k]);
        }
    }

    /* Transitive closure.  scratch[i] ends as the set of nodes reachable
     * from i by a path of length >= 1. */
    for (size_t k = 0; k < n; k++) {
        for (size_t i = 0; i < n; i++) {
            if (!bit(&scratch[i * w], k)) {
                continue;
            }
            uint64_t *ri = &scratch[i * w];
            const uint64_t *rk = &scratch[k * w];
            for (size_t q = 0; q < w; q++) {
                ri[q] |= rk[q];
            }
        }
    }

    /* A cycle exists iff some selected node reaches itself.  A SELF-EDGE
     * NEEDS NO SPECIAL CASE: it is already a path of length 1 from x to x. */
    for (size_t i = 0; i < n; i++) {
        if (!selected_all && !bit(mask, i)) {
            continue;
        }
        if (bit(&scratch[i * w], i)) {
            *out = true;
            return true;
        }
    }
    *out = false;
    return true;
}
