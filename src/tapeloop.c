#include <assert.h>
#include "gates.h"
#include "tapeloop.h"

void moop_core_init(MoopCore *core,
                    bool *cells_a, bool *marks_a, size_t len_a,
                    bool *cells_b, bool *marks_b, size_t len_b)
{
    /* With a loop shorter than 2 cells its target would alias a control,
     * and a cell that controls its own flip is not self-inverse —
     * reversibility breaks. */
    assert(len_a >= 2 && len_b >= 2);
    core->a = (MoopLoop){ .cells = cells_a, .marks = marks_a, .len = len_a };
    core->b = (MoopLoop){ .cells = cells_b, .marks = marks_b, .len = len_b };
    core->ticks = 0;
    for (size_t i = 0; i < len_a; i++)
        marks_a[i] = false;
    for (size_t i = 0; i < len_b; i++)
        marks_b[i] = false;
}

/* Fire the gate for the current alignment: controls are the cells under
 * both heads; the shared controls drive two CCNOTs, targeting the cell
 * about to rotate under the gate on each loop (A's next is +1, B rotates
 * the other way so its next is -1). Controls are never written, the two
 * targets are distinct, and CCNOT is self-inverse — so the pair commutes
 * and firing twice at the same alignment is the identity, which is what
 * makes step/step_back exact inverses. Symmetric targets mean neither
 * loop is a fixed program: code rewrites code (homoiconicity).
 *
 * A firing that changes state (both controls set) pulls all four cells
 * into the causal web. Marks only ever grow within an epoch; firing in
 * reverse marks too, a conservative over-approximation. */
static void fire(MoopCore *core)
{
    size_t ta = (core->a.head + 1) % core->a.len;
    size_t tb = (core->b.head + core->b.len - 1) % core->b.len;
    bool c1 = core->a.cells[core->a.head];
    bool c2 = core->b.cells[core->b.head];
    if (c1 && c2) {
        core->a.marks[core->a.head] = true;
        core->b.marks[core->b.head] = true;
        core->a.marks[ta] = true;
        core->b.marks[tb] = true;
    }
    moop_ccnot(c1, c2, &core->a.cells[ta]);
    moop_ccnot(c1, c2, &core->b.cells[tb]);
}

void moop_core_step(MoopCore *core)
{
    fire(core);
    core->a.head = (core->a.head + 1) % core->a.len;
    core->b.head = (core->b.head + core->b.len - 1) % core->b.len;
    core->ticks++;
}

void moop_core_step_back(MoopCore *core)
{
    core->a.head = (core->a.head + core->a.len - 1) % core->a.len;
    core->b.head = (core->b.head + 1) % core->b.len;
    fire(core);
    core->ticks--; /* meaningful within the current epoch only */
}

static size_t gcd(size_t x, size_t y)
{
    while (y != 0) {
        size_t t = x % y;
        x = y;
        y = t;
    }
    return x;
}

size_t moop_core_epoch(const MoopCore *core)
{
    return core->a.len / gcd(core->a.len, core->b.len) * core->b.len;
}

static size_t prune_loop(MoopLoop *loop)
{
    size_t discarded = 0;
    for (size_t i = 0; i < loop->len; i++) {
        if (!loop->marks[i]) {
            discarded += loop->cells[i];
            loop->cells[i] = false;
        }
        loop->marks[i] = false;
    }
    return discarded;
}

size_t moop_core_prune(MoopCore *core)
{
    size_t discarded = prune_loop(&core->a) + prune_loop(&core->b);
    core->ticks = 0;
    return discarded;
}

size_t moop_core_run(MoopCore *core, size_t ticks)
{
    size_t epoch = moop_core_epoch(core);
    size_t discarded = 0;
    while (ticks-- > 0) {
        moop_core_step(core);
        if (core->ticks == epoch)
            discarded += moop_core_prune(core);
    }
    return discarded;
}
