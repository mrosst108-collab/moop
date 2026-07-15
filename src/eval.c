#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "eval.h"
#include "logic.h"

/* Loop lengths for interpreter-made protos: coprime, so an epoch
 * covers every alignment. */
#define LEN_A 4
#define LEN_B 5
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
    env_bind("world", 5, (MoopValue){ .kind = MOOP_VAL_PROTO,
                                      .proto = &world });
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
    case MOOP_NODE_BIJECT:
        /* deliberately before evaluating operands: the whole form is
         * unimplemented, and honesty beats a partial answer */
        snprintf(err, errlen, "bijection is not implemented yet");
        return false;
    case MOOP_NODE_IS: {
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
