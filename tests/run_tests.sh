#!/bin/sh
# Smoke tests for the moop interpreter. Run via `make test`.
set -e
BIN=${BIN:-build/moop}
fail=0

check() {
    desc=$1; expected=$2; actual=$3
    if [ "$actual" = "$expected" ]; then
        echo "ok   - $desc"
    else
        echo "FAIL - $desc (expected '$expected', got '$actual')"
        fail=1
    fi
}

check "--version prints version" "moop 0.3.0" "$("$BIN" --version)"
check "core unit tests pass" "0" "$(build/test_core > /dev/null; echo $?)"
check "quit exits the repl cleanly" "0" "$(printf 'quit\n' | "$BIN" >/dev/null 2>&1; echo $?)"
check "repl reports lex errors" "error: unexpected character '@'" "$(printf 'a @ b\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# evaluation: is binds, bare expressions print
check "is binds and names evaluate" "1" "$(printf 'x is 42\nx\nquit\n' | "$BIN" 2>/dev/null | grep -c 42)"
check "generation births protos" "1" "$(printf 'world -> generate\nquit\n' | "$BIN" 2>/dev/null | grep -c 'a proto')"
check "inheritance is a lineage predicate" "1" "$(printf 'c is world -> generate\nc <- world\nquit\n' | "$BIN" 2>/dev/null | grep -c true)"
check "grandchildren do not lie about lineage" "1" "$(printf 'c is world -> generate\ng is c -> generate\ng <- world\nquit\n' | "$BIN" 2>/dev/null | grep -c false)"

# maybe: unpredictable-looking but replayable
run1=$(printf 'coin is world -> generate\ncoin -> maybe\ncoin -> maybe\ncoin -> maybe\nquit\n' | "$BIN" 2>&1)
run2=$(printf 'coin is world -> generate\ncoin -> maybe\ncoin -> maybe\ncoin -> maybe\nquit\n' | "$BIN" 2>&1)
check "maybe is replayable across runs" "$run1" "$run2"

# teaching: user-defined messages are stored chains
check "taught messages answer and delegate" "1" "$(printf 'dog is world -> generate\ndog -> answer is 42\nrex is dog -> generate\nrex -> answer\nquit\n' | "$BIN" 2>/dev/null | grep -c 42)"
check "self is the receiver, even when delegated" "1" "$(printf 'dog is world -> generate\ndog -> who is self <- dog\nrex is dog -> generate\nrex -> who\nquit\n' | "$BIN" 2>/dev/null | grep -c true)"
check "re-teaching replaces the chain" "1" "$(printf 'dog is world -> generate\ndog -> answer is 1\ndog -> answer is 2\ndog -> answer\nquit\n' | "$BIN" 2>/dev/null | grep -c ' 2$')"
check "innate messages cannot be redefined" "error: generate is innate" "$(printf 'world -> generate is 1\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "runaway recursion is caught" "error: message recursion too deep" "$(printf 'dog is world -> generate\ndog -> loop is self -> loop\ndog -> loop\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# bijection: every <-> is an involution — twice is identity
vals=$(printf 'c is world -> generate\nc -> value\n5 <-> c\nc -> value\n5 <-> c\nc -> value\nquit\n' | "$BIN" 2>/dev/null | grep -oE '[0-9]+$' | tail -3)
v1=$(echo "$vals" | sed -n 1p); v2=$(echo "$vals" | sed -n 2p); v3=$(echo "$vals" | sed -n 3p)
check "value <-> body applied twice is identity" "$v1" "$v3"
check "value <-> body actually transforms" "yes" "$([ "$v1" != "$v2" ] && echo yes)"

ex=$(printf 'a is world -> generate\nb is world -> generate\na -> value\nb -> value\na <-> b\na -> value\nb -> value\nquit\n' | "$BIN" 2>/dev/null | grep -oE '[0-9]+$' | tail -4)
a1=$(echo "$ex" | sed -n 1p); b1=$(echo "$ex" | sed -n 2p)
a2=$(echo "$ex" | sed -n 3p); b2=$(echo "$ex" | sed -n 4p)
check "body <-> body exchanges one way" "$a2" "$b1"
check "body <-> body exchanges the other way" "$b2" "$a1"

# honesty: what is not implemented says so
check "oversized values are refused, not truncated" "error: an 8-cell loop carries at most 255" "$(printf 'c is world -> generate\n256 <-> c\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "number-number bijection is honestly absent" "error: a bijection relates a value and a body, or two bodies" "$(printf '1 <-> 2\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "unknown names are reported" "error: unknown name 'ghost'" "$(printf 'ghost\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "unhosted messages are reported" "error: nothing in the lineage hosts \"dance\"" "$(printf 'world -> dance\nquit\n' | "$BIN" 2>&1 >/dev/null)"

exit $fail
