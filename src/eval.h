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
 *   "code"          a quote mentions code instead of using it: the
 *                   value is the code itself (user code is homoiconic)
 *   x -> "m"        x's code for m, found up the lineage like a send
 *   x -> "m" is c   teach m from the code value c (evaluated now)
 *   code -> first   the first part of code; `rest` is the code after
 *                   it — every part is code (blocks, definitions,
 *                   chains, steps, births, quotes all come apart)
 *
 * At startup the world is generated as the model prescribes: a
 * system-facing actor generates the system root, which generates the
 * user-facing root proto bound to the name `world`. */

typedef enum {
    MOOP_VAL_NUMBER,
    MOOP_VAL_BOOL,
    MOOP_VAL_PROTO,
    MOOP_VAL_CODE,
} MoopValueKind;

/* User code as a value: one line (a chain or a statement) or the lines
 * of a block. Immutable once made; teaching copies it. */
typedef struct {
    MoopAst **lines;  /* owned; each line's root is its statement */
    size_t n;
} MoopCode;

typedef struct {
    MoopValueKind kind;
    long number;
    bool truth;
    MoopProto *proto;
    const MoopCode *code;
} MoopValue;

/* Print code the way it is written: one line in quotes, or a block. */
void moop_code_write(FILE *out, const MoopCode *code);

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
