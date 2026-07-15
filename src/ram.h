#ifndef MOOP_RAM_H
#define MOOP_RAM_H

#include <stddef.h>
#include <stdint.h>

/* Conventional user-facing memory: byte-addressable, overwritable,
 * forgetful — the counterpart to the gate-based system memory in
 * src/tapeloop.h. Reversible operators must never touch this. */

typedef struct {
    uint8_t *bytes;  /* caller-owned storage */
    size_t len;
} MoopRam;

void moop_ram_init(MoopRam *ram, uint8_t *bytes, size_t len);
uint8_t moop_ram_read(const MoopRam *ram, size_t addr);
void moop_ram_write(MoopRam *ram, size_t addr, uint8_t value);

#endif
