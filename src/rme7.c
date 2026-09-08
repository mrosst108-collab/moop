#include <assert.h>
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

const char *moop_rme7_name(MoopRme7Primitive p)
{
    return names[p];
}

bool moop_rme7_generate(MoopProto *root, MoopRme7 *fw,
                        size_t len_a, size_t len_b)
{
    if (root->facing != MOOP_FACING_USER)
        return false;
    assert(len_a <= MOOP_RME7_MAX_CELLS && len_b <= MOOP_RME7_MAX_CELLS);

    moop_proto_generate(root, &fw->port,
                        fw->cells_a[0], fw->marks_a[0], len_a,
                        fw->cells_b[0], fw->marks_b[0], len_b,
                        NULL, 0);
    for (size_t i = 0; i < MOOP_RME7_PRIMITIVES; i++)
        moop_proto_generate(&fw->port, &fw->slots[i],
                            fw->cells_a[1 + i], fw->marks_a[1 + i], len_a,
                            fw->cells_b[1 + i], fw->marks_b[1 + i], len_b,
                            NULL, 0);
    return true;
}
