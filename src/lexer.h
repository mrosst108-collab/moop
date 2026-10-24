#ifndef MOOP_LEXER_H
#define MOOP_LEXER_H

#include <stddef.h>

/* Surface syntax operators. Each has a word form (canonical — Quorum's
 * evidence: words read better than symbols) and an arrow alias (compact
 * notation, same token):
 *   ask       ->   message passing      (asymmetric: left flows right)
 *   inherits  <-   lineage predicate    (asymmetric)
 *   mirrors   <->  bijection            (symmetric: an involution —
 *                                        mirroring twice restores)
 *   is             asymmetric identity  (the name becomes the thing)
 *   a / an         birth                (the indefinite article: `a dog`
 *                                        is a NEW proto generated from
 *                                        dog, exactly as in English)
 *
 * The words are reserved; they cannot name values or messages. The
 * arrows wear their information behavior: one-way arrows forget a
 * direction (user layer); the two-way arrow is reversible and compiles
 * to the gate layer. Semantics notes live in docs/syntax.md.
 *
 * Quotation marks mention code instead of using it, exactly as in
 * English: "ask maybe" is that code itself, as a value. Quotes nest the
 * way English prose nests them, alternating the marks — inside a quote
 * the same mark closes and the other mark opens a deeper quote:
 *   "rex ask mood is 'ask maybe'"
 * A QUOTE token carries the text between its marks.
 */

typedef enum {
    MOOP_TOK_WORD,     /* identifier: letters and underscores */
    MOOP_TOK_NUMBER,   /* decimal digits */
    MOOP_TOK_SEND,     /* ->  */
    MOOP_TOK_INHERIT,  /* <-  */
    MOOP_TOK_BIJECT,   /* <-> */
    MOOP_TOK_IS,       /* is  */
    MOOP_TOK_ARTICLE,  /* a, an */
    MOOP_TOK_QUOTE,    /* "..." or '...': start/len is the inner text */
    MOOP_TOK_END,      /* end of input */
    MOOP_TOK_ERROR,    /* unexpected character (in start/len) */
    MOOP_TOK_UNCLOSED, /* a quote whose closing mark never comes */
} MoopTokKind;

typedef struct {
    MoopTokKind kind;
    const char *start;  /* points into the source text */
    size_t len;
} MoopToken;

typedef struct {
    const char *src;
    size_t len;  /* the text ends here (quotes are lexed in place) */
    size_t pos;
} MoopLexer;

void moop_lexer_init(MoopLexer *lx, const char *src);
void moop_lexer_init_n(MoopLexer *lx, const char *src, size_t len);
MoopToken moop_lexer_next(MoopLexer *lx);

#endif
