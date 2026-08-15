#ifndef RME_GRAPH_H
#define RME_GRAPH_H

#include <stdbool.h>
#include <stddef.h>

/* poiesis — AXIS C input: the declarations a system makes about its own
 * dynamics, and the projection the classifier is allowed to see.
 *
 * These are the classification declarations, kept separate from the port
 * schema:
 *
 *     STATE · INPUTS · PARAMETERS · TRANSITION · OUTPUTS · GOVERNED STATE
 *
 * `governed` is a MARKING ON STATE SLOTS, not a port.  That single bit is
 * what separates RME-7 from RME-6B.
 */

typedef struct {
    const char *name;
    bool        governed;   /* false => environmental */
} RmeSlot;

/* One transition operator: which slot it updates, and which slots it
 * reads.  A read is exactly the claim d T_target / d read != 0. */
typedef struct {
    const char   *name;
    size_t        target;       /* index into RmeSystem.slots */
    const size_t *reads;        /* indices into RmeSystem.slots */
    size_t        read_count;
} RmeTransitionDecl;

typedef struct {
    const RmeSlot           *slots;
    size_t                   slot_count;
    const RmeTransitionDecl *transitions;
    size_t                   transition_count;
    /* RME-5: a transition adapts a parameter rather than composing state. */
    bool                     adapts_parameters;
} RmeSystem;

/* Edge set of the decisive projection.
 *
 *     G_GS = (V_G, E_SS)     V_G  = governed state objects
 *                            E_SS = state->state dependency edges,
 *                                   Y -> X iff T_X reads Y
 *
 * `governed_only` selects the projection: true builds G_GS; false builds
 * the same construction over ALL slots, which is used only to tell RME-6B
 * (a cycle that needs an environmental node) from RME-6 (no cycle at all).
 * Nothing else in the classifier may look at the full execution graph.
 */
typedef struct {
    size_t from;
    size_t to;
} RmeEdge;

/* Writes at most `cap` edges into `out`; returns the number written.
 * Returns SIZE_MAX if `cap` was insufficient. */
size_t rme_project(const RmeSystem *s, bool governed_only,
                   RmeEdge *out, size_t cap);

/* Strongly connected components.  `comp` must have room for n entries and
 * receives comp[v] = the component id of vertex v.
 *
 * Components are numbered in EMISSION order, which Tarjan guarantees to be
 * REVERSE TOPOLOGICAL over the condensation: if component A has an edge
 * into component B, B receives the LOWER id.  Since an edge Y -> X means
 * "T_X reads Y", evaluation order is therefore DESCENDING component id.
 *
 * Returns false only when working storage could not be obtained — never as
 * a way of saying "no components".  A caller must not read *component_count
 * after a false return. */
bool rme_graph_scc(size_t n, const RmeEdge *e, size_t m,
                   size_t *comp, size_t *component_count);

/* Directed-cycle predicate, exposed so acyclicity can be asserted directly
 * rather than inferred from a classification (K1).
 *
 * FROZEN self-loop rule: a self-edge X -> X counts as a directed cycle.
 * Tarjan reports it as a single-member SCC, so cardinality alone would miss
 * it; the check is explicit.  See classify.h for why the rule is semantic
 * rather than algorithmic.
 *
 * Returns false if no verdict could be computed, so an allocation failure
 * can never be silently reported as "acyclic" — which would downgrade an
 * RME-7 system to RME-6. */
bool rme_graph_has_cycle(size_t n, const RmeEdge *e, size_t m, bool *out);

#endif /* RME_GRAPH_H */
