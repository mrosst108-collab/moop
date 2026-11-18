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

/* A chain that begins with one of these has no head: it addresses the
 * receiver. A WORD in operator position is not one of them — a chain
 * that begins with a word is headed by that name. */
static bool is_op(MoopTokKind kind)
{
    return kind == MOOP_TOK_SEND || kind == MOOP_TOK_INHERIT ||
           kind == MOOP_TOK_BIJECT;
}

static bool starts_term(MoopTokKind kind)
{
    return kind == MOOP_TOK_WORD || kind == MOOP_TOK_NUMBER ||
           kind == MOOP_TOK_ARTICLE;
}

/* `tok` (a term the grammar cannot place) follows the step `left`.
 * Say why, by what the step was; false if this case has no message of
 * its own. Two cases are about arguments:
 *   box add 5 6      add takes one argument, and 6 would be a second
 *   box ask add 5    ask gives nothing (prototype B's form is refused) */
static bool refuse_after(Parser *p, int left, MoopToken tok)
{
    const MoopNode *l = &p->ast->nodes[left];
    char msg[MOOP_ERR_MAX];
    if (l->kind == MOOP_NODE_TELL) {
        snprintf(msg, sizeof msg,
                 "%.*s takes one argument, and '%.*s' would be a second",
                 (int)l->len, l->start, (int)tok.len, tok.start);
        fail(p, msg);
        return true;
    }
    if (l->kind == MOOP_NODE_SEND &&
        p->ast->nodes[l->right].kind == MOOP_NODE_WORD) {
        const MoopNode *m = &p->ast->nodes[l->right];
        bool headless = p->ast->nodes[l->left].kind == MOOP_NODE_RECEIVER;
        if (headless)
            snprintf(msg, sizeof msg,
                     "ask sends a message that takes nothing, and a body "
                     "cannot give its own receiver something");
        else if (tok.kind == MOOP_TOK_WORD)
            snprintf(msg, sizeof msg,
                     "ask sends a message that takes nothing, so '%.*s' "
                     "cannot be given to %.*s, and as a message it needs "
                     "an argument",
                     (int)tok.len, tok.start, (int)m->len, m->start);
        else
            snprintf(msg, sizeof msg,
                     "ask sends a message that takes nothing: to give %.*s "
                     "something, write it without ask",
                     (int)m->len, m->start);
        fail(p, msg);
        return true;
    }
    return false;
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
        MoopToken op = peek(p);
        MoopNodeKind kind;
        switch (op.kind) {
        case MOOP_TOK_SEND:    kind = MOOP_NODE_SEND;    break;
        case MOOP_TOK_INHERIT: kind = MOOP_NODE_INHERIT; break;
        case MOOP_TOK_BIJECT:  kind = MOOP_NODE_BIJECT;  break;
        case MOOP_TOK_WORD:    kind = MOOP_NODE_TELL;    break;
        default:
            /* a number or a birth where an operator belongs */
            if (starts_term(op.kind))
                refuse_after(p, left, op);
            return left;
        }
        advance(p);
        if (kind == MOOP_NODE_TELL && !starts_term(peek(p).kind)) {
            /* a word in operator position, and no argument after it */
            if (refuse_after(p, left, op))
                return -1;
            char msg[MOOP_ERR_MAX];
            if (peek(p).kind == MOOP_TOK_IS)
                snprintf(msg, sizeof msg,
                         "'%.*s' takes something here, and nothing names it: "
                         "write 'ask %.*s' to teach a message that takes "
                         "nothing",
                         (int)op.len, op.start, (int)op.len, op.start);
            else
                snprintf(msg, sizeof msg,
                         "'%.*s' stands where a message stands, and nothing "
                         "follows it: it needs an argument",
                         (int)op.len, op.start);
            fail(p, msg);
            return -1;
        }
        int right = parse_term(p);
        bool tell = kind == MOOP_NODE_TELL;
        left = add_node(p, (MoopNode){
            .kind = kind,
            .start = tell ? op.start : NULL, .len = tell ? op.len : 0,
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
            /* a byte that does not print is named by its code, so the
             * message itself stays readable */
            unsigned char c = (unsigned char)t.start[0];
            if (c >= 0x20 && c < 0x7f)
                snprintf(err, errlen, "unexpected character '%c'", c);
            else
                snprintf(err, errlen, "unexpected byte 0x%02X", c);
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
        bool msg_def = (lhs->kind == MOOP_NODE_SEND ||
                        lhs->kind == MOOP_NODE_TELL) &&
                       p.ast->nodes[lhs->right].kind == MOOP_NODE_WORD;
        if (lhs->kind == MOOP_NODE_TELL && !msg_def) {
            char msg[MOOP_ERR_MAX];
            snprintf(msg, sizeof msg,
                     "the word after %.*s names what it takes: write a name "
                     "there, not a value",
                     (int)lhs->len, lhs->start);
            fail(&p, msg);
        } else if (!name_def && !msg_def) {
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
