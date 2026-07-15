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
        if (n - p == 2 && strncmp(s + p, "is", 2) == 0)
            return make(MOOP_TOK_IS, s + p, 2);
        return make(MOOP_TOK_WORD, s + p, n - p);
    }

    if (isdigit((unsigned char)c)) {
        size_t n = p;
        while (isdigit((unsigned char)s[n]))
            n++;
        lx->pos = n;
        return make(MOOP_TOK_NUMBER, s + p, n - p);
    }

    lx->pos = p + 1;
    return make(MOOP_TOK_ERROR, s + p, 1);
}
