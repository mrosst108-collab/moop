#include "gates.h"

void moop_not(bool *a)
{
    *a = !*a;
}

void moop_cnot(bool c, bool *target)
{
    *target ^= c;
}

void moop_ccnot(bool c1, bool c2, bool *target)
{
    *target ^= (c1 && c2);
}

void moop_swap(bool *a, bool *b)
{
    bool tmp = *a;
    *a = *b;
    *b = tmp;
}
