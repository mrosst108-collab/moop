#include <ctype.h>
#include <string.h>
#include "lexer.h"

void moop_lexer_init(MoopLexer *lx, const char *src)
{
    lx->src = src;
    lx->pos = 0;
}

static MoopToken make(MoopTokKind kind, const char *start, size_t len)
{
    return (MoopToken){ .kind = kind, .start = start, .len = len };
}

MoopToken moop_lexer_next(MoopLexer *lx)
{
    const char *s = lx->src;

    while (s[lx->pos] == ' ' || s[lx->pos] == '\t')
        lx->pos++;

    size_t p = lx->pos;
    char c = s[p];

    if (c == '\0')
        return make(MOOP_TOK_END, s + p, 0);

    if (c == '-' && s[p + 1] == '>') {
        lx->pos = p + 2;
        return make(MOOP_TOK_SEND, s + p, 2);
    }
    /* a number literal (U1): an optional '-', digits, then optionally
     * '/' and digits, with no spaces. '-' before a digit cannot be the
     * start of '->'. Whether its value can be represented is decided
     * when it is read (src/number.c), not here. */
    if (isdigit((unsigned char)c) ||
        (c == '-' && isdigit((unsigned char)s[p + 1]))) {
        size_t n = c == '-' ? p + 1 : p;
        while (isdigit((unsigned char)s[n]))
            n++;
        if (s[n] == '/' && isdigit((unsigned char)s[n + 1])) {
            n++;
            while (isdigit((unsigned char)s[n]))
                n++;
        }
        lx->pos = n;
        return make(MOOP_TOK_NUMBER, s + p, n - p);
    }
    if (c == '<' && s[p + 1] == '-') {
        if (s[p + 2] == '>') {
            lx->pos = p + 3;
            return make(MOOP_TOK_BIJECT, s + p, 3);
        }
        lx->pos = p + 2;
        return make(MOOP_TOK_INHERIT, s + p, 2);
    }

    if (isalpha((unsigned char)c) || c == '_') {
        size_t n = p;
        while (isalpha((unsigned char)s[n]) || isdigit((unsigned char)s[n]) ||
               s[n] == '_')
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
        if ((len == 4 && strncmp(s + p, "true", 4) == 0) ||
            (len == 5 && strncmp(s + p, "false", 5) == 0))
            return make(MOOP_TOK_TRUTH, s + p, len);
        return make(MOOP_TOK_WORD, s + p, len);
    }

    lx->pos = p + 1;
    return make(MOOP_TOK_ERROR, s + p, 1);
}
