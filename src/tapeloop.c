#include <assert.h>
#include "gates.h"
#include "tapeloop.h"

void moop_core_init(MoopCore *core,
                    bool *cells_a, size_t len_a,
                    bool *cells_b, size_t len_b)
{
    /* With len_a < 2 the target would alias a control, and a cell that
     * controls its own flip is not self-inverse — reversibility breaks. */
    assert(len_a >= 2 && len_b >= 1);
    core->a = (MoopLoop){ .cells = cells_a, .len = len_a, .head = 0 };
    core->b = (MoopLoop){ .cells = cells_b, .len = len_b, .head = 0 };
}

/* Fire the gate for the current alignment: controls are the cells under
 * both heads, target is the cell about to rotate under the gate on A.
 * Controls are never written and CCNOT is self-inverse, so firing twice
 * at the same alignment is the identity — which is what makes
 * step/step_back exact inverses. */
static void fire(MoopCore *core)
{
    bool c1 = core->a.cells[core->a.head];
    bool c2 = core->b.cells[core->b.head];
    bool *target = &core->a.cells[(core->a.head + 1) % core->a.len];
    moop_ccnot(c1, c2, target);
}

void moop_core_step(MoopCore *core)
{
    fire(core);
    core->a.head = (core->a.head + 1) % core->a.len;
    core->b.head = (core->b.head + core->b.len - 1) % core->b.len;
}

void moop_core_step_back(MoopCore *core)
{
    core->a.head = (core->a.head + core->a.len - 1) % core->a.len;
    core->b.head = (core->b.head + 1) % core->b.len;
    fire(core);
}
