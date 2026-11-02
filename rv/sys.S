/* moop-rv — the operating-system boundary: Linux user mode, RV64.
 *
 * Everything that knows about Linux lives in this file: the process
 * entry point, the raw system calls, and stdin buffering. The rest of
 * moop-rv uses only the interface below, so a bare-metal backend
 * replaces this one file (docs/riscv.md). The interface is frozen with
 * the P1 infrastructure.
 *
 * Interface (standard RISC-V calling convention):
 *   moop_main(a0 = argc, a1 = argv) -> a0 = exit status
 *       provided by main.S; called once from _start
 *   sys_write_all(a0 = fd, a1 = buf, a2 = len)
 *       writes every byte, retrying partial and interrupted writes;
 *       other write errors are ignored, as the C reference's stdio
 *       output ignores them
 *   sys_getc() -> a0 = the next stdin byte (0..255), or -1 at end of
 *       input; end of input is sticky (as in C stdio), and a read error
 *       also ends input
 *
 * Linux system calls preserve every register except a0, which the
 * routines below rely on. */

#define SYS_READ   63
#define SYS_WRITE  64
#define SYS_EXIT   93
#define EINTR      4
#define INBUF_CAP  4096

    .text
    .globl _start
_start:
    ld   a0, 0(sp)              // argc
    addi a1, sp, 8              // argv
    andi sp, sp, -16            // the psABI's 16-byte stack alignment
    call moop_main
    li   a7, SYS_EXIT           // exit(status): the status is in a0
    ecall

    .globl sys_write_all
sys_write_all:
    mv   t0, a0                 // keep the fd: a0 carries each result
1:  beqz a2, 3f
    mv   a0, t0
    li   a7, SYS_WRITE
    ecall
    bltz a0, 2f
    add  a1, a1, a0             // a partial write: continue after it
    sub  a2, a2, a0
    j    1b
2:  li   t1, -EINTR
    beq  a0, t1, 1b             // interrupted: retry
3:  ret

    .globl sys_getc
sys_getc:
    la   t0, instate
    ld   t1, 0(t0)              // pos: next unread byte in inbuf
    ld   t2, 8(t0)              // len: bytes held in inbuf
    bltu t1, t2, 2f
    ld   t3, 16(t0)             // input already ended?
    bnez t3, 4f
1:  li   a0, 0                  // refill: read(0, inbuf, INBUF_CAP)
    la   a1, inbuf
    li   a2, INBUF_CAP
    li   a7, SYS_READ
    ecall
    li   t3, -EINTR
    beq  a0, t3, 1b
    blez a0, 3f                 // 0: end of input; negative: an error
    sd   a0, 8(t0)
    li   t1, 0
2:  la   t3, inbuf
    add  t3, t3, t1
    lbu  a0, 0(t3)
    addi t1, t1, 1
    sd   t1, 0(t0)
    ret
3:  li   t3, 1                  // remember the end: it is sticky
    sd   t3, 16(t0)
4:  li   a0, -1
    ret

    .bss
    .balign 8
instate:
    .skip 24                    // pos, len, ended
inbuf:
    .skip INBUF_CAP
