#!/bin/sh
# moop-rv tests (docs/riscv.md). Run via `make test-rv`, which passes the
# declared ISA and the emulator configuration from the Makefile.
#
# Parity: moop-rv must be observably identical to the C reference —
# stdout, stderr, the merged stream (pinning error ordering), and exit
# status, compared byte for byte. The reference's output is the
# expectation, but the specification (docs/) outranks both: a difference
# is resolved against the docs, never by declaring either side right.
# moop-rv earns equivalence; it does not define it.
#
# P1 scope: --version, argument handling, the banner and prompts, the
# reader, blank lines, quit, and end of input. Evaluation is not ported,
# so no parity case evaluates a statement.
set -u
REF=${REF:-build/moop}
RV_BIN=${RV_BIN:-build/moop-rv}
: "${RV_RUN:?} ${RV_MARCH:?} ${RV_MATTR:?} ${RV_OBJDUMP:?} ${RV_PROBE:?}"
tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT
fail=0

ok()  { echo "ok   - $1"; }
bad() { echo "FAIL - $1"; fail=1; }

# --- the declared target ISA -------------------------------------------

# RV_MATTR must name exactly RV_MARCH's extensions (canonical order).
std=""; z=""
for e in $(echo "$RV_MATTR" | tr ',' ' ' | tr -d '+'); do
    case $e in
    [zsx]*) z="${z}_$e" ;;
    *)      std="$std$e" ;;
    esac
done
if [ "rv64i$std$z" = "$RV_MARCH" ]; then
    ok "the audit's extension set is the declared ISA ($RV_MARCH)"
else
    bad "RV_MATTR ($RV_MATTR) does not match RV_MARCH ($RV_MARCH)"
fi

# The emulated CPU must run exactly the declared ISA.
isa=$($RV_RUN "$RV_PROBE" | sed -n 's/^isa[[:space:]]*:[[:space:]]*//p' | head -1)
if [ "$isa" = "$RV_MARCH" ]; then
    ok "the emulated CPU is the declared ISA"
else
    bad "the emulated CPU runs '$isa', not the declared '$RV_MARCH'"
fi

# Every instruction in the binary must decode under the declared ISA
# alone: raw encodings (.insn, .word) and `.option arch` regions that
# escape the assembler's -march check show up here as <unknown>.
$RV_OBJDUMP -d --no-show-raw-insn --triple=riscv64 --mattr="$RV_MATTR" \
    "$RV_BIN" > "$tmp/disasm" 2>&1
if ! grep -qE '^ +[0-9a-f]+:' "$tmp/disasm"; then
    bad "the binary audit disassembled nothing"
elif grep -q 'unknown' "$tmp/disasm"; then
    bad "instructions outside the declared ISA: $(grep -c unknown "$tmp/disasm")"
else
    ok "every instruction belongs to the declared ISA"
fi

# The ELF entry point must be _start (the Linux process entry).
entry=$($RV_OBJDUMP -f "$RV_BIN" | sed -n 's/^start address: 0x0*//p')
start=$($RV_OBJDUMP -t "$RV_BIN" | sed -n 's/^0*\([0-9a-f]*\) .* _start$/\1/p')
if [ -n "$start" ] && [ "$entry" = "$start" ]; then
    ok "the entry point is _start"
else
    bad "the entry point (0x$entry) is not _start (0x$start)"
fi

# --- parity with the C reference ---------------------------------------

# parity DESCRIPTION INPUT-FILE [ARG...]
parity() {
    desc=$1; input=$2; shift 2
    "$REF" "$@" < "$input" > "$tmp/ref.stdout" 2> "$tmp/ref.stderr"
    echo $? > "$tmp/ref.status"
    "$REF" "$@" < "$input" > "$tmp/ref.merged" 2>&1
    $RV_RUN "$RV_BIN" "$@" < "$input" > "$tmp/rv.stdout" 2> "$tmp/rv.stderr"
    echo $? > "$tmp/rv.status"
    $RV_RUN "$RV_BIN" "$@" < "$input" > "$tmp/rv.merged" 2>&1
    for stream in stdout stderr merged status; do
        if ! cmp -s "$tmp/ref.$stream" "$tmp/rv.$stream"; then
            bad "$desc ($stream differs)"
            return
        fi
    done
    ok "$desc"
}

in=$tmp/in
: > "$in.none"
parity "--version" "$in.none" --version
parity "--version ignores later arguments" "$in.none" --version extra
parity "file arguments are refused" "$in.none" program.moop
parity "an empty argument is refused like a file" "$in.none" ""

printf 'quit\n' > "$in.quit"
parity "quit leaves the repl" "$in.quit"
parity "end of input leaves the repl" "$in.none"
printf 'quit' > "$in.quit_eof"
parity "quit without a final newline" "$in.quit_eof"
printf 'quit\nnever read\n' > "$in.after"
parity "nothing after quit is read" "$in.after"
printf '\n   \n\t \t\nquit\n' > "$in.blank"
parity "blank lines are skipped" "$in.blank"
printf '\n\n' > "$in.blank_eof"
parity "blank lines then end of input" "$in.blank_eof"
awk 'BEGIN { for (i = 0; i < 5000; i++) print "   "; print "quit" }' > "$in.many"
parity "input spanning many buffer refills" "$in.many"

printf '%1023s\nquit\n' '' > "$in.fits"
parity "a 1023-character line fits" "$in.fits"
printf '%1024s\nquit\n' '' > "$in.long"
parity "a 1024-character line is refused" "$in.long"
printf '%5000s\nquit\n' x > "$in.huge"
parity "a line longer than the input buffer is refused whole" "$in.huge"
printf '%1100s\n' quit > "$in.split"
parity "an over-long line ending in quit does not quit" "$in.split"
printf '%1100s' x > "$in.long_eof"
parity "an over-long final line without a newline is refused" "$in.long_eof"
{ printf 'qu'; printf '\000'; printf 'it\nquit\n'; } > "$in.nul"
parity "a NUL byte refuses the line" "$in.nul"

# --- honesty: what moop-rv cannot do yet, it says ----------------------

printf 'x is 1\nquit\n' > "$in.stmt"
got=$($RV_RUN "$RV_BIN" < "$in.stmt" 2>&1 >/dev/null)
if [ "$got" = "error: evaluation is not ported to moop-rv yet" ]; then
    ok "statements are refused honestly, not silently skipped"
else
    bad "statements must be refused honestly (got '$got')"
fi

exit $fail
