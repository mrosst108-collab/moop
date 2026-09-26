#ifndef PC_GRAPH_H
#define PC_GRAPH_H

#include <stdint.h>

#include "../types/pc_surface.h"

/* ProtoC — graph/   Derived from S4 and S8.
 *
 * S4:  reciprocal governed coupling is a DIRECTED CYCLE entirely within the
 *      governed sub-relation.  A governed self-edge is such a cycle.
 *      Execution self-recursion is not.
 *
 * THERE IS NO CLASSIFIER HERE, and there will not be.  SEMANTICS.md places
 * classification outside ProtoC: ProtoC realizes the semantic object, an
 * external observer classifies it.  A classifier here would make the two
 * substrates validate one another circularly.  This module answers only
 * "does the governed sub-relation contain a directed cycle" -- a graph
 * question -- and says nothing about RME levels.
 *
 * WHAT S4 CONSTRAINS AND WHAT IT LEAVES SLACK.  It constrains that there
 * IS a governed/non-governed distinction, that the criterion is a directed
 * cycle, that the cycle must lie entirely among governed nodes, and that a
 * self-edge qualifies.  It says nothing about representation or algorithm,
 * so both are ProtoC's own:
 *
 *   - dependencies are BITSET ROWS, not an edge list;
 *   - the governed restriction is a MASK APPLIED DURING THE COMPUTATION,
 *     never a materialized projection into a second structure;
 *   - cycles are found by TRANSITIVE-CLOSURE REACHABILITY, not by strongly
 *     connected components.
 *
 * A CONSEQUENCE WORTH RECORDING.  Under reachability, "x reaches x" is
 * true exactly when a path of length >= 1 returns to x -- which INCLUDES a
 * self-edge with no special case whatsoever.  A substrate testing cycles by
 * SCC cardinality must add an explicit self-edge check, because a self-loop
 * is a one-member component.  S4's self-edge rule is therefore free here
 * and requires machinery there.  Same invariant, different mechanism; the
 * same shape as the S5 identity result.
 *
 * EDGE DIRECTION is a convention, not a semantic commitment: the existence
 * of a directed cycle is invariant under reversing every edge, so nothing
 * in S4 depends on which way the arrow is read.
 */

typedef struct {
    size_t    n;
    uint64_t *rows;       /* n rows of `words` words; bit j of row i: i -> j */
    uint64_t *governed;   /* `words` words; bit i set iff node i is governed */
    size_t    words;
} PcDepGraph;

size_t pc_graph_words(size_t n);

/* `rows` needs n*pc_graph_words(n) words; `governed` needs
 * pc_graph_words(n). Both are caller-owned (S6). */
bool pc_graph_init(PcDepGraph *g, size_t n, uint64_t *rows, uint64_t *governed,
                   size_t words);

/* A declared dependency between two nodes.  Refused, not ignored, when
 * either endpoint is out of range (S8) -- a dependency naming a node that
 * does not exist is a malformed declaration, and dropping it would yield a
 * confident answer computed from an incomplete relation. */
bool pc_graph_declare_dependency(PcDepGraph *g, size_t from, size_t to);

bool pc_graph_mark_governed(PcDepGraph *g, size_t node);
bool pc_graph_is_governed(const PcDepGraph *g, size_t node);

/* Does a directed cycle exist among the nodes selected by `mask`?
 *
 * `mask == nullptr` selects every node; passing `g->governed` answers S4's
 * question. The restriction is applied DURING the closure, so no projected
 * graph is ever built and none can be truncated.
 *
 * Returns false, writing nothing to *out, when no answer could be computed
 * (S8): a refusal is never reported as "acyclic". */
bool pc_graph_has_cycle(const PcDepGraph *g, const uint64_t *mask,
                        uint64_t *scratch, bool *out);

#endif /* PC_GRAPH_H */
