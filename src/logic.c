#include "logic.h"

bool moop_and(bool a, bool b)  { return a && b; }
bool moop_or(bool a, bool b)   { return a || b; }
bool moop_nand(bool a, bool b) { return !(a && b); }
bool moop_nor(bool a, bool b)  { return !(a || b); }
bool moop_xor(bool a, bool b)  { return a != b; }

bool moop_maybe(MoopCore *oracle)
{
    moop_core_step(oracle);
    return oracle->a.cells[oracle->a.head];
}
