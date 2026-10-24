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
    bool fragments; /* quoted code: may end waiting for its last piece */
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
    Parser inner = { .ast = p->ast, .err = p->err, .errlen = p->errlen,
                     .fragments = true };
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
        if (inner == MOOP_TOK_END && p->fragments) /* waiting for a term */
            return add_node(p, (MoopNode){
                .kind = MOOP_NODE_BIRTH, .left = -1, .right = -1,
            });
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
        /* a fragment may end on its operator, waiting for a term */
        int right = peek(p).kind == MOOP_TOK_END && p->fragments
                        ? -1 : parse_term(p);
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
    /* the joint on its own: the piece between a designator and a body */
    if (p->fragments && peek(p).kind == MOOP_TOK_IS &&
        p->toks[p->pos + 1].kind == MOOP_TOK_END) {
        advance(p);
        return add_node(p, (MoopNode){
            .kind = MOOP_NODE_IS, .left = -1, .right = -1,
        });
    }
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
    /* `is` at the end: a block opener at top level; in quoted code, a
     * definition still waiting for its body */
    int body = -1;
    if (peek(p).kind != MOOP_TOK_END)
        body = parse_chain(p);
    (void)quoted;
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

bool moop_parse_code(const char *src, size_t len, MoopAst *ast,
                     char *err, size_t errlen)
{
    Parser p = { .ast = ast, .err = err, .errlen = errlen,
                 .fragments = true };
    ast->count = 0;
    ast->root = -1;

    MoopLexer lx;
    moop_lexer_init_n(&lx, src, len);
    if (!tokenize(&p, &lx))
        return false;
    if (peek(&p).kind == MOOP_TOK_END) {
        fail(&p, "there is no code here");
        return false;
    }
    p.ast->root = parse_statement(&p, true);
    if (!p.failed && peek(&p).kind != MOOP_TOK_END)
        fail(&p, "expected an operator between expressions");
    return !p.failed;
}

bool moop_ast_whole(const MoopAst *ast, int idx)
{
    const MoopNode *n = &ast->nodes[idx];
    switch (n->kind) {
    case MOOP_NODE_QUOTE: /* mentioned code is data, whole or not */
    case MOOP_NODE_WORD:
    case MOOP_NODE_NUMBER:
    case MOOP_NODE_RECEIVER:
        return true;
    case MOOP_NODE_BIRTH:
        return n->left >= 0 && moop_ast_whole(ast, n->left);
    case MOOP_NODE_IS:
        return n->left >= 0 && n->right >= 0 &&
               moop_ast_whole(ast, n->left) && moop_ast_whole(ast, n->right);
    case MOOP_NODE_SEND:
    case MOOP_NODE_INHERIT:
    case MOOP_NODE_BIJECT:
        return n->right >= 0 && moop_ast_whole(ast, n->left) &&
               moop_ast_whole(ast, n->right);
    }
    return false;
}

/* --- writing code back out ------------------------------------------ */

static const char *op_word(MoopNodeKind kind)
{
    switch (kind) {
    case MOOP_NODE_SEND:    return "->";
    case MOOP_NODE_INHERIT: return "<-";
    case MOOP_NODE_BIJECT:  return "<->";
    default:                return "?";
    }
}

/* The writer appends to a file or to a buffer (snprintf-style). */
typedef struct {
    FILE *out;
    char *buf;
    size_t cap, len;
} Sink;

static void put(Sink *s, const char *text, size_t n)
{
    if (s->out != NULL) {
        fwrite(text, 1, n, s->out);
    } else if (s->len < s->cap) {
        size_t room = s->cap - s->len;
        memcpy(s->buf + s->len, text, n < room ? n : room);
    }
    s->len += n;
}

static void puts_sink(Sink *s, const char *text)
{
    put(s, text, strlen(text));
}

static void write_node(Sink *s, const MoopAst *ast, int idx, int depth)
{
    const MoopNode *n = &ast->nodes[idx];
    switch (n->kind) {
    case MOOP_NODE_WORD:
    case MOOP_NODE_NUMBER:
        put(s, n->start, n->len);
        return;
    case MOOP_NODE_RECEIVER:
        return; /* headless: the chain starts with its operator */
    case MOOP_NODE_BIRTH: {
        if (n->left < 0) {
            puts_sink(s, "a"); /* waiting for a term */
            return;
        }
        const MoopNode *t = &ast->nodes[n->left];
        bool vowel = t->kind == MOOP_NODE_WORD &&
                     strchr("aeiouAEIOU", t->start[0]) != NULL;
        puts_sink(s, vowel ? "an " : "a ");
        write_node(s, ast, n->left, depth);
        return;
    }
    case MOOP_NODE_SEND:
    case MOOP_NODE_INHERIT:
    case MOOP_NODE_BIJECT:
        write_node(s, ast, n->left, depth);
        if (ast->nodes[n->left].kind != MOOP_NODE_RECEIVER)
            puts_sink(s, " ");
        puts_sink(s, op_word(n->kind));
        if (n->right >= 0) { /* else waiting for a term */
            puts_sink(s, " ");
            write_node(s, ast, n->right, depth);
        }
        return;
    case MOOP_NODE_IS:
        if (n->left >= 0) {
            write_node(s, ast, n->left, depth);
            puts_sink(s, " ");
        }
        puts_sink(s, "is");
        if (n->right >= 0) {
            puts_sink(s, " ");
            write_node(s, ast, n->right, depth);
        }
        return;
    case MOOP_NODE_QUOTE: {
        const char *mark = depth % 2 == 0 ? "\"" : "'";
        puts_sink(s, mark);
        write_node(s, ast, n->left, depth + 1);
        puts_sink(s, mark);
        return;
    }
    }
}

void moop_ast_write(FILE *out, const MoopAst *ast, int idx, int depth)
{
    Sink s = { .out = out };
    write_node(&s, ast, idx, depth);
}

size_t moop_ast_format(char *buf, size_t cap, const MoopAst *ast, int idx,
                       int depth)
{
    Sink s = { .buf = buf, .cap = cap };
    write_node(&s, ast, idx, depth);
    if (cap > 0)
        buf[s.len < cap ? s.len : cap - 1] = '\0';
    return s.len;
}
