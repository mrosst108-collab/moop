#ifndef MOOP_PARSER_H
#define MOOP_PARSER_H

#include <stdbool.h>
#include <stddef.h>

/* One grammar rule, by design (orthogonality: the operators differ in
 * meaning, never in shape):
 *
 *   statement := chain ["is" [chain]]
 *   chain     := [term] ((-> | <- | <->) term)*   ; associates left
 *   term      := WORD | NUMBER
 *
 * `a -> b -> c` is ((a -> b) -> c): a pipeline, reading left to right.
 * The operators also have word spellings (ask, inherits, mirrors) —
 * same tokens, handled entirely by the lexer.
 *
 * A chain may begin with an operator: the missing head is the RECEIVER
 * — an English imperative, instructions addressed to whoever is being
 * spoken to. In a taught body that is the object that was asked; at the
 * top level it is the world. There is no receiver keyword.
 *
 * The left side of `is` must be a designator: a bare WORD (naming a
 * value; the right side evaluates now) or `term -> WORD` (teaching a
 * message; the right side is stored as a chain — code as user-layer
 * data — and evaluates at each send addressed to the receiver).
 *
 * `is` with nothing after it (right == -1) announces an indented block:
 * the definition body follows, one chain per line, ended by a blank
 * line. The reader (REPL) collects the block; the parser stays
 * line-shaped. */

typedef enum {
    MOOP_NODE_WORD,
    MOOP_NODE_NUMBER,
    MOOP_NODE_RECEIVER, /* implicit head of a chain that starts with an op */
    MOOP_NODE_SEND,     /* ->  */
    MOOP_NODE_INHERIT,  /* <-  */
    MOOP_NODE_BIJECT,   /* <-> */
    MOOP_NODE_IS,       /* left = designator, right = chain (-1: block) */
} MoopNodeKind;

typedef struct {
    MoopNodeKind kind;
    const char *start;  /* lexeme for WORD/NUMBER; points into the source */
    size_t len;
    int left, right;    /* node indices; -1 if none */
} MoopNode;

#define MOOP_AST_MAX 64

typedef struct {
    MoopNode nodes[MOOP_AST_MAX];
    size_t count;
    int root;
} MoopAst;

/* Parse one line. Returns true and fills ast, or false and writes a
 * message (without the "error: " prefix) into err. */
bool moop_parse(const char *src, MoopAst *ast, char *err, size_t errlen);

/* Heap copy with owned lexemes (an ast's lexemes otherwise point into
 * the source line, which the reader reuses). NULL on exhaustion. */
MoopAst *moop_ast_clone(const MoopAst *src);
void moop_ast_free(MoopAst *ast);

#endif
