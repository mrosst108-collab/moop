/* moop-rv — entry and REPL (P1: infrastructure only).
 *
 * For everything P1 covers, observable behavior is the C reference's
 * (src/main.c), byte for byte: --version, refusing file arguments, the
 * banner and prompts, the reader (lines of at most 1023 characters;
 * longer lines and NUL bytes refused whole — docs/syntax.md), blank
 * lines, `quit`, and end of input.
 *
 * Evaluation is not ported yet. Any other line is refused with an
 * honest error rather than skipped or faked: a REPL that silently
 * ignored statements would look functional while doing nothing. */

#include "moop.h"

#define STDOUT         1
#define STDERR         2
#define LINE_CAP       1024     /* at most LINE_CAP - 1 characters */
#define LINE_OK        0
#define LINE_EOF       1
#define LINE_TOO_LONG  2
#define LINE_NUL       3
#define NEWLINE        10
#define TAB            9
#define SPACE          32

    .text
    .globl moop_main
moop_main:                      // a0 = argc, a1 = argv -> a0 = status
    addi sp, sp, -16
    sd   ra, 8(sp)
    li   t0, 2
    blt  a0, t0, .Lrepl         // no arguments: the REPL
    ld   a0, 8(a1)              // only argv[1] is examined
    la   a1, s_version_flag
    call str_eq
    beqz a0, .Lfile
    li   a0, STDOUT
    la   a1, s_version
    call write_str
    li   a0, 0
    j    .Lreturn
.Lfile:
    li   a0, STDERR
    la   a1, s_no_files
    call write_str
    li   a0, 1
    j    .Lreturn
.Lrepl:
    call repl
    li   a0, 0
.Lreturn:
    ld   ra, 8(sp)
    addi sp, sp, 16
    ret

repl:
    addi sp, sp, -16
    sd   ra, 8(sp)
    li   a0, STDOUT
    la   a1, s_version          // the banner: "moop <version>" ...
    call write_str
    li   a0, STDOUT
    la   a1, s_quit_hint        // ... then how to leave
    call write_str
.Lprompt:
    li   a0, STDOUT
    la   a1, s_prompt
    call write_str
    call read_line
    li   t0, LINE_EOF
    beq  a0, t0, .Lleave
    li   t0, LINE_TOO_LONG
    beq  a0, t0, .Ltoo_long
    li   t0, LINE_NUL
    beq  a0, t0, .Lnul
    la   a0, line
    la   a1, s_quit
    call str_eq
    bnez a0, .Lleave
    la   a0, line
    call is_blank
    bnez a0, .Lprompt           // blank lines are skipped silently
    la   a1, s_no_eval          // not ported yet: refuse honestly
    j    .Lcomplain
.Ltoo_long:
    la   a1, s_too_long
    j    .Lcomplain
.Lnul:
    la   a1, s_nul
.Lcomplain:
    li   a0, STDERR
    call write_str
    j    .Lprompt
.Lleave:
    ld   ra, 8(sp)
    addi sp, sp, 16
    ret

/* read_line() -> a0 = LINE_OK, LINE_EOF, LINE_TOO_LONG, or LINE_NUL.
 * A line is taken whole or not at all: an over-long line is consumed
 * to its end and refused, never split; a NUL byte refuses the line. On
 * LINE_OK, `line` holds the text without its newline, NUL-terminated.
 * A final line without a newline is an ordinary line. */
read_line:
    addi sp, sp, -32
    sd   ra, 24(sp)
    sd   s0, 16(sp)             // s0: characters seen on this line
    sd   s1, 8(sp)              // s1: 1 once a NUL byte is seen
    li   s0, 0
    li   s1, 0
1:  call sys_getc
    bltz a0, 3f                 // end of input
    li   t0, NEWLINE
    beq  a0, t0, 4f
    seqz t0, a0
    or   s1, s1, t0
    li   t0, LINE_CAP - 1
    bgeu s0, t0, 2f             // past capacity: count, don't store
    la   t1, line
    add  t1, t1, s0
    sb   a0, 0(t1)
2:  addi s0, s0, 1
    j    1b
3:  li   a0, LINE_EOF
    beqz s0, 5f                 // nothing read: input has ended
4:  li   t0, LINE_CAP - 1
    li   a0, LINE_TOO_LONG
    bgtu s0, t0, 5f
    li   a0, LINE_NUL
    bnez s1, 5f
    la   t1, line
    add  t1, t1, s0
    sb   zero, 0(t1)
    li   a0, LINE_OK
5:  ld   ra, 24(sp)
    ld   s0, 16(sp)
    ld   s1, 8(sp)
    addi sp, sp, 32
    ret

/* str_eq(a0, a1) -> a0 = 1 if the two NUL-terminated strings are equal */
str_eq:
1:  lbu  t0, 0(a0)
    lbu  t1, 0(a1)
    bne  t0, t1, 2f
    beqz t0, 3f
    addi a0, a0, 1
    addi a1, a1, 1
    j    1b
2:  li   a0, 0
    ret
3:  li   a0, 1
    ret

/* is_blank(a0) -> a0 = 1 if the string holds only spaces and tabs */
is_blank:
1:  lbu  t0, 0(a0)
    beqz t0, 3f
    li   t1, SPACE
    beq  t0, t1, 2f
    li   t1, TAB
    bne  t0, t1, 4f
2:  addi a0, a0, 1
    j    1b
3:  li   a0, 1
    ret
4:  li   a0, 0
    ret

/* write_str(a0 = fd, a1 = NUL-terminated string) */
write_str:
    mv   t0, a1
1:  lbu  t1, 0(t0)
    beqz t1, 2f
    addi t0, t0, 1
    j    1b
2:  sub  a2, t0, a1
    tail sys_write_all

    .section .rodata
s_version_flag:
    .asciz "--version"
s_version:                      /* the one version string: src/moop.h */
    .ascii "moop ", MOOP_VERSION, "\n"
    .byte 0
s_quit_hint:
    .asciz "type \"quit\" to leave\n"
s_prompt:
    .asciz "moop> "
s_quit:
    .asciz "quit"
s_no_files:
    .asciz "error: running files is not implemented yet\n"
s_too_long:                     /* 1023 = LINE_CAP - 1 */
    .asciz "error: line too long (lines hold at most 1023 characters)\n"
s_nul:
    .asciz "error: unexpected character (a NUL byte)\n"
s_no_eval:
    .asciz "error: evaluation is not ported to moop-rv yet\n"

    .bss
line:
    .skip LINE_CAP
