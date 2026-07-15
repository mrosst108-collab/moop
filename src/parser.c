#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "lexer.h"
#include "parser.h"

MoopAst *moop_ast_clone(const MoopAst *src)
{
    MoopAst *copy = malloc(sizeof *copy);
    if (copy == NULL)
        return NULL;
    *copy = *src;
    for (size_t i = 0; i < copy->count; i++) {
        if (src->nodes[i].start != NULL) {
            char *s = malloc(src->nodes[i].len);
            if (s == NULL) {
                copy->count = i; /* free only what we duplicated */
                moop_ast_free(copy);
                return NULL;
            }
            memcpy(s, src->nodes[i].start, src->nodes[i].len);
            copy->nodes[i].start = s;
        }
    }
    return copy;
}

void moop_ast_free(MoopAst *ast)
{
    if (ast == NULL)
        return;
    for (size_t i = 0; i < ast->count; i++)
        free((char *)ast->nodes[i].start);
    free(ast);
}

#define MAX_TOKENS 128

typedef struct {
    MoopToken toks[MAX_TOKENS];
    size_t n;
    size_t pos;
    MoopAst *ast;
    char *err;
    size_t errlen;
    bool failed;
} Parser;

static void fail(Parser *p, const char *msg)
{
    if (!p->failed) {
        snprintf(p->err, p->errlen, "%s", msg);
        p->failed = true;
    }
}

static MoopToken peek(Parser *p)
{
    return p->toks[p->pos];
}

static void advance(Parser *p)
{
    if (p->toks[p->pos].kind != MOOP_TOK_END)
        p->pos++;
}

static int add_node(Parser *p, MoopNode node)
{
    if (p->ast->count == MOOP_AST_MAX) {
        fail(p, "expression too long");
        return -1;
    }
    p->ast->nodes[p->ast->count] = node;
    return (int)p->ast->count++;
}

static int parse_term(Parser *p)
{
    MoopToken t = peek(p);
    if (t.kind == MOOP_TOK_WORD || t.kind == MOOP_TOK_NUMBER) {
        advance(p);
        return add_node(p, (MoopNode){
            .kind = t.kind == MOOP_TOK_WORD ? MOOP_NODE_WORD
                                            : MOOP_NODE_NUMBER,
            .start = t.start, .len = t.len, .left = -1, .right = -1,
        });
    }
    fail(p, "expected a name or number");
    return -1;
}

static bool is_op(MoopTokKind kind)
{
    return kind == MOOP_TOK_SEND || kind == MOOP_TOK_INHERIT ||
           kind == MOOP_TOK_BIJECT;
}

static int parse_chain(Parser *p)
{
    int left;
    if (is_op(peek(p).kind))
        left = add_node(p, (MoopNode){
            .kind = MOOP_NODE_RECEIVER, .left = -1, .right = -1,
        });
    else
        left = parse_term(p);
    while (!p->failed) {
        MoopNodeKind kind;
        switch (peek(p).kind) {
        case MOOP_TOK_SEND:    kind = MOOP_NODE_SEND;    break;
        case MOOP_TOK_INHERIT: kind = MOOP_NODE_INHERIT; break;
        case MOOP_TOK_BIJECT:  kind = MOOP_NODE_BIJECT;  break;
        default:
            return left;
        }
        advance(p);
        int right = parse_term(p);
        left = add_node(p, (MoopNode){
            .kind = kind, .start = NULL, .len = 0,
            .left = left, .right = right,
        });
    }
    return left;
}

bool moop_parse(const char *src, MoopAst *ast, char *err, size_t errlen)
{
    Parser p = { .ast = ast, .err = err, .errlen = errlen };
    ast->count = 0;
    ast->root = -1;

    MoopLexer lx;
    moop_lexer_init(&lx, src);
    for (;;) {
        MoopToken t = moop_lexer_next(&lx);
        if (t.kind == MOOP_TOK_ERROR) {
            snprintf(err, errlen, "unexpected character '%.*s'",
                     (int)t.len, t.start);
            return false;
        }
        if (p.n == MAX_TOKENS) {
            snprintf(err, errlen, "line too long");
            return false;
        }
        p.toks[p.n++] = t;
        if (t.kind == MOOP_TOK_END)
            break;
    }

    int first = parse_chain(&p);
    p.ast->root = first;

    if (!p.failed && peek(&p).kind == MOOP_TOK_IS) {
        const MoopNode *lhs = &p.ast->nodes[first];
        bool name_def = lhs->kind == MOOP_NODE_WORD;
        bool msg_def = lhs->kind == MOOP_NODE_SEND &&
                       p.ast->nodes[lhs->right].kind == MOOP_NODE_WORD;
        if (!name_def && !msg_def) {
            fail(&p, "only names and messages can be defined");
        } else {
            advance(&p); /* is */
            int body = peek(&p).kind == MOOP_TOK_END ? -1 : parse_chain(&p);
            p.ast->root = add_node(&p, (MoopNode){
                .kind = MOOP_NODE_IS,
                .start = name_def ? lhs->start : NULL,
                .len = name_def ? lhs->len : 0,
                .left = first, .right = body,
            });
        }
    }

    if (!p.failed && peek(&p).kind == MOOP_TOK_IS)
        fail(&p, "'is' names things: name is thing");
    if (!p.failed && peek(&p).kind != MOOP_TOK_END)
        fail(&p, "expected an operator between expressions");
    return !p.failed;
}
