#include <stdio.h>
#include <stdbool.h>
#include "tapeloop.h"
#include "logic.h"
static void show(const MoopCore *c) {
    printf("CcnotTape from Tapes([");
    for (size_t k = 0; k < c->a.len; k++) printf("%s%d", k ? ", " : "", c->a.cells[k]);
    printf("], [");
    for (size_t k = 0; k < c->b.len; k++) printf("%s%d", k ? ", " : "", c->b.cells[k]);
    printf("], %zu, %zu)\n", c->a.head, c->b.head);
}
int main(void) {
    bool a[8], ma[8], b[13], mb[13], ca[8], cma[8], cb[13], cmb[13];
    for (int k = 0; k < 8; k++) a[k] = (k * k + 1) % 2;
    for (int k = 0; k < 13; k++) b[k] = ((k * 5) / 3 + 1) % 2;
    MoopCore p, c;
    moop_core_init(&p, a, ma, 8, b, mb, 13);
    show(&p);
    for (int k = 0; k < 40; k++) printf("%d\n", moop_maybe(&p));
    show(&p);
    MoopCore before = p; bool sa[8], sb[13];
    for (int k = 0; k < 8; k++) sa[k] = a[k];
    for (int k = 0; k < 13; k++) sb[k] = b[k];
    /* birth, exactly as seed() in src/proto.c */
    moop_core_init(&c, ca, cma, 8, cb, cmb, 13);
    for (size_t k = 0; k < c.a.len; k++) c.a.cells[k] = moop_maybe(&p);
    for (size_t k = 0; k < c.b.len; k++) c.b.cells[k] = moop_maybe(&p);
    show(&p); show(&c);
    for (int k = 0; k < 20; k++) printf("%d\n", moop_maybe(&c));
    show(&c);
    /* undo the birth: step the parent back len_a + len_b ticks */
    for (int k = 0; k < 21; k++) moop_core_step_back(&p);
    show(&p);
    bool same = p.a.head == before.a.head && p.b.head == before.b.head;
    for (int k = 0; k < 8; k++) same = same && a[k] == sa[k];
    for (int k = 0; k < 13; k++) same = same && b[k] == sb[k];
    fprintf(stderr, "moop step_back restored parent: %s\n", same ? "yes" : "NO");
    return 0;
}
