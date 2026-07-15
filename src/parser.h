#ifndef MOOP_PARSER_H
#define MOOP_PARSER_H

#include <stdbool.h>
#include <stddef.h>

/* One grammar rule, by design (orthogonality: the operators differ in
 * meaning, never in shape):
 *
 *   statement := WORD "is" chain | chain
 *   chain     := term ((-> | <- | <->) term)*   ; associates left
 *   term      := WORD | NUMBER
 *
 * `a -> b -> c` is ((a -> b) -> c): a pipeline, reading left to right.
 */

typedef enum {
    MOOP_NODE_WORD,
    MOOP_NODE_NUMBER,
    MOOP_NODE_SEND,     /* ->  */
    MOOP_NODE_INHERIT,  /* <-  */
    MOOP_NODE_BIJECT,   /* <-> */
    MOOP_NODE_IS,       /* left = name word, right = chain */
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

#endif
