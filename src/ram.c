#include <assert.h>
#include "ram.h"

void moop_ram_init(MoopRam *ram, uint8_t *bytes, size_t len)
{
    ram->bytes = bytes;
    ram->len = len;
}

uint8_t moop_ram_read(const MoopRam *ram, size_t addr)
{
    assert(addr < ram->len);
    return ram->bytes[addr];
}

void moop_ram_write(MoopRam *ram, size_t addr, uint8_t value)
{
    assert(addr < ram->len);
    ram->bytes[addr] = value;
}
