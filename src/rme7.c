#include <assert.h>
#include <stddef.h>
#include "rme7.h"

static const char *const names[MOOP_RME7_PRIMITIVES] = {
    [MOOP_RME7_JSHARP]      = "jsharp",
    [MOOP_RME7_GSHARP]      = "gsharp",
    [MOOP_RME7_GTILDESHARP] = "gtildesharp",
    [MOOP_RME7_SIGMA]       = "sigma",
    [MOOP_RME7_F]           = "f",
    [MOOP_RME7_KAPPA]       = "kappa",
    [MOOP_RME7_GAMMA]       = "gamma",
};

/* Derived by the deletion test against the multi-track card: a port of
 * each primitive either is the port, is its failure condition, is
 * covered by a port that already exists, or awaits a ruling. */
static const MoopPortVerdict verdicts[MOOP_RME7_PRIMITIVES] = {
    [MOOP_RME7_JSHARP]      = MOOP_PORT_ABSENT,   /* would merge the tracks */
    [MOOP_RME7_GSHARP]      = MOOP_PORT_REFUSED,  /* capture */
    [MOOP_RME7_GTILDESHARP] = MOOP_PORT_OPEN,
    [MOOP_RME7_SIGMA]       = MOOP_PORT_ADMITTED, /* the port */
    [MOOP_RME7_F]           = MOOP_PORT_ABSENT,   /* Σ_ij then F_i covers it */
    [MOOP_RME7_KAPPA]       = MOOP_PORT_ADMITTED, /* the gate factor */
    [MOOP_RME7_GAMMA]       = MOOP_PORT_ABSENT,   /* derived, not an operator */
};

const char *moop_rme7_name(MoopRme7Primitive p)
{
    return names[p];
}

MoopPortVerdict moop_rme7_verdict(MoopRme7Primitive p)
{
    return verdicts[p];
}

bool moop_rme7_verdict_of(const MoopRme7 *fw, const MoopProto *p,
                          MoopPortVerdict *out)
{
    /* nearest typed ancestor wins: a port born from sigma is a sigma
     * port; one born from port alone has no primitive */
    for (const MoopProto *q = p; q != NULL; q = q->parent) {
        for (size_t i = 0; i < MOOP_RME7_PRIMITIVES; i++) {
            if (q == &fw->ports[i]) {
                *out = verdicts[i];
                return true;
            }
        }
        if (q == &fw->port) {
            *out = MOOP_PORT_OPEN;
            return true;
        }
    }
    return false;
}

/* --- the hosted verdict vocabulary --------------------------------------
 * Hosted once, on `port`. A handler receives only the receiver, so it
 * recovers its framework from lineage: the ancestor hosting this very
 * vocabulary is `port`, which lives at a known offset in MoopRme7. The
 * handlers read parent links and nothing else — no body is touched. */

static bool answer(MoopProto *self, MoopPortVerdict asked);

static bool msg_admitted(MoopProto *s) { return answer(s, MOOP_PORT_ADMITTED); }
static bool msg_refused(MoopProto *s)  { return answer(s, MOOP_PORT_REFUSED); }
static bool msg_absent(MoopProto *s)   { return answer(s, MOOP_PORT_ABSENT); }
static bool msg_open(MoopProto *s)     { return answer(s, MOOP_PORT_OPEN); }

static const MoopProtoMessage vocabulary[MOOP_PORT_VERDICTS] = {
    [MOOP_PORT_ADMITTED] = { "admitted", msg_admitted },
    [MOOP_PORT_REFUSED]  = { "refused",  msg_refused },
    [MOOP_PORT_ABSENT]   = { "absent",   msg_absent },
    [MOOP_PORT_OPEN]     = { "open",     msg_open },
};

static const MoopRme7 *framework_of(const MoopProto *self)
{
    for (const MoopProto *q = self; q != NULL; q = q->parent) {
        for (size_t i = 0; i < q->hosted; i++) {
            if (q->messages[i].fn == msg_admitted) {
                const char *base = (const char *)q - offsetof(MoopRme7, port);
                return (const MoopRme7 *)base;
            }
        }
    }
    return NULL;
}

static bool answer(MoopProto *self, MoopPortVerdict asked)
{
    const MoopRme7 *fw = framework_of(self);
    MoopPortVerdict v;
    /* dispatch only reaches here through `port`, so both hold */
    assert(fw != NULL);
    if (fw == NULL || !moop_rme7_verdict_of(fw, self, &v))
        return false;
    return v == asked;
}

/* --- generation ------------------------------------------------------- */

bool moop_rme7_generate(MoopProto *root, MoopRme7 *fw,
                        size_t len_a, size_t len_b)
{
    if (root->facing != MOOP_FACING_USER)
        return false;
    assert(len_a <= MOOP_RME7_MAX_CELLS && len_b <= MOOP_RME7_MAX_CELLS);

    moop_proto_generate(root, &fw->port,
                        fw->cells_a[0], fw->marks_a[0], len_a,
                        fw->cells_b[0], fw->marks_b[0], len_b,
                        fw->port_table, MOOP_PORT_VERDICTS);
    for (size_t v = 0; v < MOOP_PORT_VERDICTS; v++)
        moop_proto_host(&fw->port, vocabulary[v].name, vocabulary[v].fn);

    for (size_t i = 0; i < MOOP_RME7_PRIMITIVES; i++)
        moop_proto_generate(&fw->port, &fw->ports[i],
                            fw->cells_a[1 + i], fw->marks_a[1 + i], len_a,
                            fw->cells_b[1 + i], fw->marks_b[1 + i], len_b,
                            NULL, 0); /* nothing hosted: they delegate */
    return true;
}
