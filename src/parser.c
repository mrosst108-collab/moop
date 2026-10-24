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

static bool tokenize(Parser *p, MoopLexer *lx);
static int parse_statement(Parser *p, bool quoted);

/* A quote's inner text is parsed in place, into the same tree: the
 * lexemes keep pointing into the source line. */
static int parse_quote(Parser *p, MoopToken t)
{
    Parser inner = { .ast = p->ast, .err = p->err, .errlen = p->errlen };
    MoopLexer lx;
    moop_lexer_init_n(&lx, t.start, t.len);
    int root = -1;
    if (tokenize(&inner, &lx)) {
        if (peek(&inner).kind == MOOP_TOK_END)
            fail(&inner, "a quote must hold code");
        else
            root = parse_statement(&inner, true);
    }
    if (!inner.failed && peek(&inner).kind != MOOP_TOK_END)
        fail(&inner, "expected an operator between expressions");
    if (inner.failed || p->failed) {
        p->failed = true; /* the message is already written */
        return -1;
    }
    return add_node(p, (MoopNode){
        .kind = MOOP_NODE_QUOTE, .left = root, .right = -1,
    });
}

static int parse_term(Parser *p)
{
    MoopToken t = peek(p);
    if (t.kind == MOOP_TOK_QUOTE) {
        advance(p);
        return parse_quote(p, t);
    }
    if (t.kind == MOOP_TOK_ARTICLE) {
        advance(p);
        MoopTokKind inner = peek(p).kind;
        if (inner != MOOP_TOK_WORD && inner != MOOP_TOK_NUMBER) {
            fail(p, "'a' introduces a new thing: a name must follow");
            return -1;
        }
        int core = parse_term(p);
        return add_node(p, (MoopNode){
            .kind = MOOP_NODE_BIRTH, .left = core, .right = -1,
        });
    }
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

static bool tokenize(Parser *p, MoopLexer *lx)
{
    for (;;) {
        MoopToken t = moop_lexer_next(lx);
        if (t.kind == MOOP_TOK_ERROR) {
            if (!p->failed)
                snprintf(p->err, p->errlen, "unexpected character '%.*s'",
                         (int)t.len, t.start);
            p->failed = true;
            return false;
        }
        if (t.kind == MOOP_TOK_UNCLOSED) {
            fail(p, "a quote is never closed");
            return false;
        }
        if (p->n == MAX_TOKENS) {
            fail(p, "line too long");
            return false;
        }
        p->toks[p->n++] = t;
        if (t.kind == MOOP_TOK_END)
            return true;
    }
}

bool moop_quoted_name(const MoopAst *ast, int idx)
{
    const MoopNode *n = &ast->nodes[idx];
    return n->kind == MOOP_NODE_QUOTE && n->left >= 0 &&
           ast->nodes[n->left].kind == MOOP_NODE_WORD;
}

static int parse_statement(Parser *p, bool quoted)
{
    int first = parse_chain(p);
    if (p->failed || peek(p).kind != MOOP_TOK_IS)
        return first;

    const MoopNode *lhs = &p->ast->nodes[first];
    bool name_def = lhs->kind == MOOP_NODE_WORD;
    bool msg_def = lhs->kind == MOOP_NODE_SEND &&
                   (p->ast->nodes[lhs->right].kind == MOOP_NODE_WORD ||
                    moop_quoted_name(p->ast, lhs->right));
    if (!name_def && !msg_def) {
        fail(p, "only names and messages can be defined");
        return -1;
    }
    advance(p); /* is */
    int body = -1;
    if (peek(p).kind != MOOP_TOK_END)
        body = parse_chain(p);
    else if (quoted)
        fail(p, "quoted code must be whole: the definition body is missing");
    int root = add_node(p, (MoopNode){
        .kind = MOOP_NODE_IS,
        .start = name_def ? lhs->start : NULL,
        .len = name_def ? lhs->len : 0,
        .left = first, .right = body,
    });
    if (!p->failed && peek(p).kind == MOOP_TOK_IS)
        fail(p, "'is' names things: name is thing");
    return root;
}

bool moop_parse(const char *src, MoopAst *ast, char *err, size_t errlen)
{
    Parser p = { .ast = ast, .err = err, .errlen = errlen };
    ast->count = 0;
    ast->root = -1;

    MoopLexer lx;
    moop_lexer_init(&lx, src);
    if (!tokenize(&p, &lx))
        return false;

    p.ast->root = parse_statement(&p, false);
    if (!p.failed && peek(&p).kind != MOOP_TOK_END)
        fail(&p, "expected an operator between expressions");
    return !p.failed;
}

/* --- writing code back out ------------------------------------------ */

static const char *op_word(MoopNodeKind kind)
{
    switch (kind) {
    case MOOP_NODE_SEND:    return "ask";
    case MOOP_NODE_INHERIT: return "inherits";
    case MOOP_NODE_BIJECT:  return "mirrors";
    default:                return "?";
    }
}

void moop_ast_write(FILE *out, const MoopAst *ast, int idx, int depth)
{
    const MoopNode *n = &ast->nodes[idx];
    switch (n->kind) {
    case MOOP_NODE_WORD:
    case MOOP_NODE_NUMBER:
        fprintf(out, "%.*s", (int)n->len, n->start);
        return;
    case MOOP_NODE_RECEIVER:
        return; /* headless: the chain starts with its operator */
    case MOOP_NODE_BIRTH: {
        const MoopNode *t = &ast->nodes[n->left];
        bool vowel = t->kind == MOOP_NODE_WORD &&
                     strchr("aeiouAEIOU", t->start[0]) != NULL;
        fputs(vowel ? "an " : "a ", out);
        moop_ast_write(out, ast, n->left, depth);
        return;
    }
    case MOOP_NODE_SEND:
    case MOOP_NODE_INHERIT:
    case MOOP_NODE_BIJECT:
        moop_ast_write(out, ast, n->left, depth);
        if (ast->nodes[n->left].kind != MOOP_NODE_RECEIVER)
            fputc(' ', out);
        fprintf(out, "%s ", op_word(n->kind));
        moop_ast_write(out, ast, n->right, depth);
        return;
    case MOOP_NODE_IS:
        moop_ast_write(out, ast, n->left, depth);
        fputs(" is", out);
        if (n->right >= 0) {
            fputc(' ', out);
            moop_ast_write(out, ast, n->right, depth);
        }
        return;
    case MOOP_NODE_QUOTE: {
        char mark = depth % 2 == 0 ? '"' : '\'';
        fputc(mark, out);
        moop_ast_write(out, ast, n->left, depth + 1);
        fputc(mark, out);
        return;
    }
    }
}
