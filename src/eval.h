#ifndef MOOP_EVAL_H
#define MOOP_EVAL_H

#include <stdbool.h>
#include <stddef.h>
#include "parser.h"
#include "proto.h"

/* The evaluator: the user-facing layer of the interpreter.
 *
 * Each construct has one job (orthogonality):
 *   name is thing   binds a name (names are the mutable, user-layer
 *                   handle; lineage is fixed at generation)
 *   a thing         birth — the indefinite article: a NEW proto
 *                   generated from thing; `rex is a dog` introduces,
 *                   `rex is dog` aliases. There is no creation message.
 *   x -> message    sends: `maybe` observes x's reversible body,
 *                   `value` decodes it, anything else is looked up in
 *                   x's taught and hosted tables (delegating)
 *   child <- parent lineage predicate: true iff parent is child's
 *                   birth-fixed delegation parent
 *   x <-> y         gate-backed involutions: value deposit / body
 *                   exchange; applying the same one twice is identity
 *
 * At startup the world is generated as the model prescribes: a
 * system-facing actor generates the system root, which generates the
 * user-facing root proto bound to the name `world`. */

typedef enum {
    MOOP_VAL_NUMBER,
    MOOP_VAL_BOOL,
    MOOP_VAL_PROTO,
} MoopValueKind;

typedef struct {
    MoopValueKind kind;
    long number;
    bool truth;
    MoopProto *proto;
} MoopValue;

void moop_eval_init(void);

/* Evaluate one parsed line. On success returns true; *quiet is set for
 * definitions (which print nothing). On failure returns false with a
 * message (no "error: " prefix) in err. */
bool moop_eval(const MoopAst *ast, MoopValue *out, bool *quiet,
               char *err, size_t errlen);

/* Evaluate a block definition: `head` is a statement whose `is` had no
 * inline body (root IS node with right == -1); `bodies` are the block's
 * lines, one parsed chain each. Takes ownership of `bodies` in every
 * outcome. Teaching designators store the sequence; name designators
 * evaluate it now and bind the last value. Definitions are quiet. */
bool moop_eval_block(const MoopAst *head, MoopAst **bodies, size_t nbodies,
                     char *err, size_t errlen);

#endif
