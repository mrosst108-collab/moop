/* Test probe for `make test-rv`: prints /proc/cpuinfo as the emulator
 * presents it. QEMU's user mode synthesizes that file from the emulated
 * CPU, so its "isa" line shows exactly which extensions the tests run
 * with; tests/rv_tests.sh requires it to equal the declared RV_MARCH. */

#define AT_FDCWD  -100
#define SYS_OPENAT 56
#define SYS_READ   63
#define SYS_WRITE  64
#define SYS_EXIT   93

    .text
    .globl _start
_start:
    li   a0, AT_FDCWD
    la   a1, path
    li   a2, 0                  // O_RDONLY
    li   a7, SYS_OPENAT
    ecall
    bltz a0, 2f
    mv   s0, a0
1:  mv   a0, s0                 // copy the file to stdout
    la   a1, buf
    li   a2, 4096
    li   a7, SYS_READ
    ecall
    blez a0, 3f
    mv   a2, a0
    li   a0, 1
    la   a1, buf
    li   a7, SYS_WRITE
    ecall
    j    1b
2:  li   a0, 1                  // could not open: fail loudly
    li   a7, SYS_EXIT
    ecall
3:  li   a0, 0
    li   a7, SYS_EXIT
    ecall

    .section .rodata
path:
    .asciz "/proc/cpuinfo"

    .bss
buf:
    .skip 4096
