#include <ctype.h>
#include <string.h>
#include "lexer.h"

void moop_lexer_init(MoopLexer *lx, const char *src)
{
    moop_lexer_init_n(lx, src, strlen(src));
}

void moop_lexer_init_n(MoopLexer *lx, const char *src, size_t len)
{
    lx->src = src;
    lx->len = len;
    lx->pos = 0;
}

static MoopToken make(MoopTokKind kind, const char *start, size_t len)
{
    return (MoopToken){ .kind = kind, .start = start, .len = len };
}

static char at(const MoopLexer *lx, size_t i)
{
    return i < lx->len ? lx->src[i] : '\0';
}

/* A quote opened at p: nesting alternates the marks, so inside a quote
 * the same mark closes and the other mark opens one level deeper. */
static MoopToken quote(MoopLexer *lx, size_t p)
{
    char closer = lx->src[p];
    size_t depth = 1;
    for (size_t q = p + 1; at(lx, q) != '\0'; q++) {
        char c = at(lx, q);
        if (c == closer) {
            depth--;
            closer = closer == '"' ? '\'' : '"';
        } else if (c == '"' || c == '\'') {
            depth++;
            closer = c;
        }
        if (depth == 0) {
            lx->pos = q + 1;
            return make(MOOP_TOK_QUOTE, lx->src + p + 1, q - p - 1);
        }
    }
    lx->pos = lx->len;
    return make(MOOP_TOK_UNCLOSED, lx->src + p, 1);
}

MoopToken moop_lexer_next(MoopLexer *lx)
{
    const char *s = lx->src;

    while (at(lx, lx->pos) == ' ' || at(lx, lx->pos) == '\t')
        lx->pos++;

    size_t p = lx->pos;
    char c = at(lx, p);

    if (c == '\0')
        return make(MOOP_TOK_END, s + p, 0);

    if (c == '"' || c == '\'')
        return quote(lx, p);

    if (c == '-' && at(lx, p + 1) == '>') {
        lx->pos = p + 2;
        return make(MOOP_TOK_SEND, s + p, 2);
    }
    if (c == '<' && at(lx, p + 1) == '-') {
        if (at(lx, p + 2) == '>') {
            lx->pos = p + 3;
            return make(MOOP_TOK_BIJECT, s + p, 3);
        }
        lx->pos = p + 2;
        return make(MOOP_TOK_INHERIT, s + p, 2);
    }

    if (isalpha((unsigned char)c) || c == '_') {
        size_t n = p;
        while (isalpha((unsigned char)at(lx, n)) ||
               isdigit((unsigned char)at(lx, n)) || at(lx, n) == '_')
            n++;
        lx->pos = n;
        size_t len = n - p;
        if (len == 1 && s[p] == 'a')
            return make(MOOP_TOK_ARTICLE, s + p, len);
        if (len == 2 && strncmp(s + p, "an", 2) == 0)
            return make(MOOP_TOK_ARTICLE, s + p, len);
        if (len == 2 && strncmp(s + p, "is", 2) == 0)
            return make(MOOP_TOK_IS, s + p, len);
        if (len == 3 && strncmp(s + p, "ask", 3) == 0)
            return make(MOOP_TOK_SEND, s + p, len);
        if (len == 8 && strncmp(s + p, "inherits", 8) == 0)
            return make(MOOP_TOK_INHERIT, s + p, len);
        if (len == 7 && strncmp(s + p, "mirrors", 7) == 0)
            return make(MOOP_TOK_BIJECT, s + p, len);
        return make(MOOP_TOK_WORD, s + p, len);
    }

    if (isdigit((unsigned char)c)) {
        size_t n = p;
        while (isdigit((unsigned char)at(lx, n)))
            n++;
        lx->pos = n;
        return make(MOOP_TOK_NUMBER, s + p, n - p);
    }

    lx->pos = p + 1;
    return make(MOOP_TOK_ERROR, s + p, 1);
}
