#ifndef RME_GRAPH_H
#define RME_GRAPH_H

#include <stdbool.h>
#include <stddef.h>

/* poiesis — AXIS C input: the declarations a system makes about its own
 * dynamics, the one question Axis C asks of them, and the projection the
 * scheduler builds from them.
 *
 * These are the declarations, kept separate from the port schema:
 *
 *     STATE · INPUTS · PARAMETERS · TRANSITION · OUTPUTS · GOVERNED STATE
 *
 * `governed` is a MARKING ON STATE SLOTS, not a port.  That single bit is
 * what separates a governed cycle from a cycle that closes only through
 * environmental state.
 *
 * THERE IS NO CLASSIFIER HERE.  Axis C is observational (SPEC §11): the
 * substrate answers one graph question — does a directed cycle lie among
 * the selected slots — and names no RME level.  An observer reads the
 * answer: a cycle among governed slots is the RME-7 criterion; a cycle
 * over all slots with none among the governed ones returns through
 * environmental state.  The earlier five-level classifier answered more
 * than the invariant requires, and was reduced to this check.
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
} RmeSystem;

/* The largest system this build represents.  A larger one is refused by
 * the cycle check and by the scheduler, never truncated or downgraded. */
#define RME_MAX_SLOTS 2048u

/* Edge set of a projection, materialized for the scheduler.
 *
 *     G_GS = (V_G, E_SS)     V_G  = governed state objects
 *                            E_SS = state->state dependency edges,
 *                                   Y -> X iff T_X reads Y
 *
 * `governed_only` selects the projection: true builds G_GS; false builds
 * the same construction over ALL slots, which is what the scheduler orders.
 * The cycle check below does NOT use this: it reads the declarations
 * directly and applies the governed restriction during its computation, so
 * no capped edge list stands between a system and its answer.
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

/* THE Axis C check: does a directed cycle lie among the selected slots?
 *
 * `governed_only` selects the slots — true asks the RME-7 question (SPEC
 * §11: a directed cycle entirely among governed state objects); false asks
 * whether any cycle exists over all slots.  An edge Y -> X exists iff T_X
 * declares a read of Y and both X and Y are selected.
 *
 * MECHANISM: transitive-closure reachability over bitset rows, with the
 * selection applied while the rows are built — no projected edge list is
 * materialized, so nothing can be truncated between the declarations and
 * the answer.  A cycle exists iff some selected slot reaches itself by a
 * path of length >= 1.
 *
 * FROZEN self-loop rule (SPEC §11): a governed self-read X -> X is a
 * directed cycle.  Under reachability that needs NO SPECIAL CASE — a
 * self-edge is already a path of length 1 from X to X.  (A check by SCC
 * cardinality must add one, since a self-loop is a one-member component.)
 * Execution self-recursion is not declared as a read, so it cannot count.
 *
 * REFUSAL (never a guess): returns false, writing nothing to *out, when
 * `s` or `out` is null, the system exceeds RME_MAX_SLOTS, any declaration
 * is malformed — a target or read outside the slot table, a transition
 * that claims reads but supplies none, a non-empty table that is null —
 * or working storage cannot be obtained.  The WHOLE declaration is
 * validated before either selection is computed, so a malformed read is
 * refused even where the governed selection would not have looked at it.
 *
 * OBSERVATIONAL: reads `s` only.  It has no access to any prototype and
 * cannot establish or mutate conformance. */
bool rme_has_cycle(const RmeSystem *s, bool governed_only, bool *out);

#endif /* RME_GRAPH_H */
