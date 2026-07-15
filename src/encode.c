#include <assert.h>
#include <limits.h>
#include "encode.h"
#include "gates.h"

#define VALUE_BITS (CHAR_BIT * sizeof(unsigned long))

void moop_encode_xor(MoopCore *core, unsigned long value)
{
    assert(value <= moop_encode_max(core));
    for (size_t i = 0; i < core->a.len && i < VALUE_BITS; i++) {
        if (value >> i & 1) {
            moop_not(&core->a.cells[i]);
            core->a.marks[i] = true;
        }
    }
}

unsigned long moop_decode(const MoopCore *core)
{
    unsigned long value = 0;
    for (size_t i = 0; i < core->a.len && i < VALUE_BITS; i++)
        value |= (unsigned long)core->a.cells[i] << i;
    return value;
}

void moop_exchange(MoopCore *x, MoopCore *y)
{
    assert(x->a.len == y->a.len);
    for (size_t i = 0; i < x->a.len; i++) {
        moop_swap(&x->a.cells[i], &y->a.cells[i]);
        moop_swap(&x->a.marks[i], &y->a.marks[i]);
    }
}

unsigned long moop_encode_max(const MoopCore *core)
{
    if (core->a.len >= VALUE_BITS)
        return ULONG_MAX;
    return (1UL << core->a.len) - 1;
}
