#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "encode.h"
#include "eval.h"
#include "logic.h"

/* Loop lengths for interpreter-made protos: coprime, so an epoch
 * covers every alignment. 8 cells on loop A = values 0..255. */
#define LEN_A 8
#define LEN_B 13
#define TABLE_CAP 4

/* --- the world ------------------------------------------------------- */

static MoopActor the_actor;
static bool actor_a[5] = {1, 0, 1, 1, 0};
static bool actor_b[7] = {0, 1, 1, 0, 1, 0, 1};
static bool actor_ma[5], actor_mb[7];
static MoopMessage actor_table[2];

static MoopProto sysroot;
static bool sys_a[LEN_A], sys_ma[LEN_A], sys_b[LEN_B], sys_mb[LEN_B];
static MoopProtoMessage sys_table[TABLE_CAP];

static MoopProto world;
static bool world_a[LEN_A], world_ma[LEN_A], world_b[LEN_B], world_mb[LEN_B];
static MoopProtoMessage world_table[TABLE_CAP];

/* --- the environment: names are the mutable user-layer handle -------- */

typedef struct {
    char *name;
    MoopValue value;
} Binding;

#define ENV_MAX 64
static Binding env[ENV_MAX];
static size_t env_n;

static Binding *env_find(const char *name, size_t len)
{
    for (size_t i = 0; i < env_n; i++)
        if (strlen(env[i].name) == len && memcmp(env[i].name, name, len) == 0)
            return &env[i];
    return NULL;
}

static bool env_bind(const char *name, size_t len, MoopValue value)
{
    Binding *b = env_find(name, len);
    if (b == NULL) {
        if (env_n == ENV_MAX)
            return false;
        char *copy = malloc(len + 1);
        if (copy == NULL)
            return false;
        memcpy(copy, name, len);
        copy[len] = '\0';
        b = &env[env_n++];
        b->name = copy;
    }
    b->value = value;
    return true;
}

/* --- teachings: user-defined messages, stored as chains --------------
 * The user layer is homoiconic in its own medium: a message body is the
 * same data the parser produced, kept in RAM, evaluated at each send.
 * A body is a sequence of chains (one per indented line, or a single
 * inline chain); the last chain's value answers. Nothing user-facing
 * lives on the tapes. */

#define BODY_MAX 16

typedef struct {
    MoopProto *owner;
    char *name;
    MoopAst *bodies[BODY_MAX];  /* owned deep copies */
    size_t nbodies;
} Teaching;

#define TEACHINGS_MAX 128
static Teaching teachings[TEACHINGS_MAX];
static size_t teachings_n;

static void free_bodies(MoopAst **bodies, size_t n)
{
    for (size_t i = 0; i < n; i++)
        moop_ast_free(bodies[i]);
}

static Teaching *find_teaching(const MoopProto *owner,
                               const char *name, size_t len)
{
    for (size_t i = 0; i < teachings_n; i++)
        if (teachings[i].owner == owner &&
            strlen(teachings[i].name) == len &&
            memcmp(teachings[i].name, name, len) == 0)
            return &teachings[i];
    return NULL;
}

/* Whoever a headless chain addresses. Taught bodies set it to the
 * object that was asked; between sends it is the world — the top level
 * is a body whose receiver is the world. */
static MoopValue current_receiver;

void moop_eval_init(void)
{
    static bool done = false;
    if (done)
        return;
    done = true;
    moop_actor_init(&the_actor, actor_a, actor_ma, 5, actor_b, actor_mb, 7,
                    actor_table, 2);
    moop_actor_generate_root(&the_actor, &sysroot,
                             sys_a, sys_ma, LEN_A, sys_b, sys_mb, LEN_B,
                             sys_table, TABLE_CAP);
    moop_proto_generate(&sysroot, &world,
                        world_a, world_ma, LEN_A, world_b, world_mb, LEN_B,
                        world_table, TABLE_CAP);
    MoopValue w = { .kind = MOOP_VAL_PROTO, .proto = &world };
    env_bind("world", 5, w);
    current_receiver = w;
}

/* --- evaluation ------------------------------------------------------ */

static MoopProto *birth_proto(MoopProto *generator)
{
    MoopProto *p = malloc(sizeof *p);
    bool *ca = malloc(LEN_A * sizeof *ca);
    bool *ma = malloc(LEN_A * sizeof *ma);
    bool *cb = malloc(LEN_B * sizeof *cb);
    bool *mb = malloc(LEN_B * sizeof *mb);
    MoopProtoMessage *table = malloc(TABLE_CAP * sizeof *table);
    if (!p || !ca || !ma || !cb || !mb || !table) {
        free(p); free(ca); free(ma); free(cb); free(mb); free(table);
        return NULL;
    }
    moop_proto_generate(generator, p, ca, ma, LEN_A, cb, mb, LEN_B,
                        table, TABLE_CAP);
    return p;
}

static bool eval_node(const MoopAst *ast, int idx, MoopValue *out,
                      char *err, size_t errlen);

static bool is_innate(const MoopNode *msg)
{
    return (msg->len == 8 && memcmp(msg->start, "generate", 8) == 0) ||
           (msg->len == 5 && memcmp(msg->start, "maybe", 5) == 0) ||
           (msg->len == 5 && memcmp(msg->start, "value", 5) == 0);
}

/* Run a taught body addressed to the receiver: headless chains inside
 * it resolve to the object that was asked, then the outer receiver is
 * restored. */
static int send_depth;

static bool eval_teaching(const Teaching *t, MoopValue receiver,
                          MoopValue *out, char *err, size_t errlen)
{
    if (send_depth == 32) {
        snprintf(err, errlen, "message recursion too deep");
        return false;
    }

    MoopValue saved = current_receiver;
    current_receiver = receiver;
    send_depth++;
    bool ok = true;
    for (size_t i = 0; ok && i < t->nbodies; i++)
        ok = eval_node(t->bodies[i], t->bodies[i]->root, out, err, errlen);
    send_depth--;
    current_receiver = saved;
    return ok;
}

static bool eval_send(const MoopAst *ast, const MoopNode *node,
                      MoopValue *out, char *err, size_t errlen)
{
    MoopValue recv;
    if (!eval_node(ast, node->left, &recv, err, errlen))
        return false;

    const MoopNode *msg = &ast->nodes[node->right];
    if (msg->kind != MOOP_NODE_WORD) {
        snprintf(err, errlen, "a message must be a name");
        return false;
    }
    if (recv.kind != MOOP_VAL_PROTO) {
        snprintf(err, errlen, "only protos host messages (yet)");
        return false;
    }

    /* dispatch: innate, then taught (delegating), then C-hosted */
    if (msg->len == 8 && memcmp(msg->start, "generate", 8) == 0) {
        MoopProto *child = birth_proto(recv.proto);
        if (child == NULL) {
            snprintf(err, errlen, "out of memory");
            return false;
        }
        *out = (MoopValue){ .kind = MOOP_VAL_PROTO, .proto = child };
        return true;
    }
    if (msg->len == 5 && memcmp(msg->start, "maybe", 5) == 0) {
        *out = (MoopValue){ .kind = MOOP_VAL_BOOL,
                            .truth = moop_maybe(&recv.proto->core) };
        return true;
    }
    if (msg->len == 5 && memcmp(msg->start, "value", 5) == 0) {
        *out = (MoopValue){ .kind = MOOP_VAL_NUMBER,
                            .number = (long)moop_decode(&recv.proto->core) };
        return true;
    }

    for (MoopProto *p = recv.proto; p != NULL; p = p->parent) {
        const Teaching *t = find_teaching(p, msg->start, msg->len);
        if (t != NULL)
            return eval_teaching(t, recv, out, err, errlen);
    }

    char name[64];
    if (msg->len >= sizeof name) {
        snprintf(err, errlen, "message name too long");
        return false;
    }
    memcpy(name, msg->start, msg->len);
    name[msg->len] = '\0';
    bool reply;
    if (moop_proto_send(recv.proto, name, &reply)) {
        *out = (MoopValue){ .kind = MOOP_VAL_BOOL, .truth = reply };
        return true;
    }
    snprintf(err, errlen, "nothing in the lineage hosts \"%s\"", name);
    return false;
}

/* Store a teaching, taking ownership of the bodies (freed on failure). */
static bool teach_store(MoopProto *owner, const MoopNode *msg,
                        MoopAst **bodies, size_t nbodies,
                        char *err, size_t errlen)
{
    if (is_innate(msg)) {
        free_bodies(bodies, nbodies);
        snprintf(err, errlen, "%.*s is innate", (int)msg->len, msg->start);
        return false;
    }

    Teaching *t = find_teaching(owner, msg->start, msg->len);
    if (t != NULL) {
        free_bodies(t->bodies, t->nbodies); /* re-teaching replaces */
    } else {
        char *name = malloc(msg->len + 1);
        if (teachings_n == TEACHINGS_MAX || name == NULL) {
            free(name);
            free_bodies(bodies, nbodies);
            snprintf(err, errlen, "too many teachings");
            return false;
        }
        memcpy(name, msg->start, msg->len);
        name[msg->len] = '\0';
        t = &teachings[teachings_n++];
        t->owner = owner;
        t->name = name;
    }
    memcpy(t->bodies, bodies, nbodies * sizeof *bodies);
    t->nbodies = nbodies;
    return true;
}

static bool eval_teach(const MoopAst *ast, const MoopNode *designator,
                       int bodyidx, MoopValue *out, char *err, size_t errlen)
{
    MoopValue recv;
    if (!eval_node(ast, designator->left, &recv, err, errlen))
        return false;
    if (recv.kind != MOOP_VAL_PROTO) {
        snprintf(err, errlen, "only protos host messages");
        return false;
    }

    MoopAst *body = moop_ast_clone(ast);
    if (body == NULL) {
        snprintf(err, errlen, "out of memory");
        return false;
    }
    body->root = bodyidx; /* the stored chain, not the whole definition */

    if (!teach_store(recv.proto, &ast->nodes[designator->right],
                     &body, 1, err, errlen))
        return false;
    *out = (MoopValue){ .kind = MOOP_VAL_BOOL, .truth = true };
    return true;
}

static bool eval_node(const MoopAst *ast, int idx, MoopValue *out,
                      char *err, size_t errlen)
{
    const MoopNode *node = &ast->nodes[idx];
    switch (node->kind) {
    case MOOP_NODE_WORD: {
        Binding *b = env_find(node->start, node->len);
        if (b == NULL) {
            snprintf(err, errlen, "unknown name '%.*s'",
                     (int)node->len, node->start);
            return false;
        }
        *out = b->value;
        return true;
    }
    case MOOP_NODE_RECEIVER:
        *out = current_receiver;
        return true;
    case MOOP_NODE_NUMBER: {
        char buf[32];
        size_t n = node->len < sizeof buf - 1 ? node->len : sizeof buf - 1;
        memcpy(buf, node->start, n);
        buf[n] = '\0';
        *out = (MoopValue){ .kind = MOOP_VAL_NUMBER,
                            .number = strtol(buf, NULL, 10) };
        return true;
    }
    case MOOP_NODE_SEND:
        return eval_send(ast, node, out, err, errlen);
    case MOOP_NODE_INHERIT: {
        MoopValue child, parent;
        if (!eval_node(ast, node->left, &child, err, errlen) ||
            !eval_node(ast, node->right, &parent, err, errlen))
            return false;
        if (child.kind != MOOP_VAL_PROTO || parent.kind != MOOP_VAL_PROTO) {
            snprintf(err, errlen, "inheritance relates protos");
            return false;
        }
        *out = (MoopValue){ .kind = MOOP_VAL_BOOL,
                            .truth = child.proto->parent == parent.proto };
        return true;
    }
    case MOOP_NODE_BIJECT: {
        MoopValue l, r;
        if (!eval_node(ast, node->left, &l, err, errlen) ||
            !eval_node(ast, node->right, &r, err, errlen))
            return false;
        if (l.kind == MOOP_VAL_PROTO && r.kind == MOOP_VAL_PROTO) {
            moop_exchange(&l.proto->core, &r.proto->core);
            *out = l; /* the left body, so pipelines continue */
            return true;
        }
        MoopValue *num = NULL, *body = NULL;
        if (l.kind == MOOP_VAL_NUMBER && r.kind == MOOP_VAL_PROTO) {
            num = &l; body = &r;
        } else if (l.kind == MOOP_VAL_PROTO && r.kind == MOOP_VAL_NUMBER) {
            num = &r; body = &l;
        }
        if (num != NULL) {
            unsigned long max = moop_encode_max(&body->proto->core);
            if (num->number < 0 || (unsigned long)num->number > max) {
                snprintf(err, errlen,
                         "an %zu-cell loop carries at most %lu",
                         body->proto->core.a.len, max);
                return false;
            }
            moop_encode_xor(&body->proto->core,
                            (unsigned long)num->number);
            *out = *body;
            return true;
        }
        snprintf(err, errlen,
                 "a bijection relates a value and a body, or two bodies");
        return false;
    }
    case MOOP_NODE_IS: {
        if (node->right == -1) {
            /* the reader hands blocks to moop_eval_block; reaching this
             * inline means the body never arrived */
            snprintf(err, errlen, "the definition body is missing");
            return false;
        }
        const MoopNode *lhs = &ast->nodes[node->left];
        if (lhs->kind == MOOP_NODE_SEND)
            return eval_teach(ast, lhs, node->right, out, err, errlen);
        MoopValue value;
        if (!eval_node(ast, node->right, &value, err, errlen))
            return false;
        if (!env_bind(node->start, node->len, value)) {
            snprintf(err, errlen, "too many names");
            return false;
        }
        *out = value;
        return true;
    }
    }
    snprintf(err, errlen, "unreachable");
    return false;
}

bool moop_eval(const MoopAst *ast, MoopValue *out, bool *quiet,
               char *err, size_t errlen)
{
    *quiet = ast->nodes[ast->root].kind == MOOP_NODE_IS;
    return eval_node(ast, ast->root, out, err, errlen);
}

bool moop_eval_block(const MoopAst *head, MoopAst **bodies, size_t nbodies,
                     char *err, size_t errlen)
{
    const MoopNode *root = &head->nodes[head->root];
    const MoopNode *lhs = &head->nodes[root->left];

    if (lhs->kind == MOOP_NODE_SEND) {
        MoopValue recv;
        if (!eval_node(head, lhs->left, &recv, err, errlen)) {
            free_bodies(bodies, nbodies);
            return false;
        }
        if (recv.kind != MOOP_VAL_PROTO) {
            free_bodies(bodies, nbodies);
            snprintf(err, errlen, "only protos host messages");
            return false;
        }
        return teach_store(recv.proto, &head->nodes[lhs->right],
                           bodies, nbodies, err, errlen);
    }

    /* name block: evaluate the sequence now, the last value gets the name */
    MoopValue value = { .kind = MOOP_VAL_BOOL, .truth = false };
    for (size_t i = 0; i < nbodies; i++) {
        if (!eval_node(bodies[i], bodies[i]->root, &value, err, errlen)) {
            free_bodies(bodies, nbodies);
            return false;
        }
    }
    free_bodies(bodies, nbodies);
    if (!env_bind(root->start, root->len, value)) {
        snprintf(err, errlen, "too many names");
        return false;
    }
    return true;
}
