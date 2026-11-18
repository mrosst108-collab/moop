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

check "--version prints version" "moop 0.7.0" "$("$BIN" --version)"
check "core unit tests pass" "0" "$(build/test_core > /dev/null; echo $?)"
check "quit exits the repl cleanly" "0" "$(printf 'quit\n' | "$BIN" >/dev/null 2>&1; echo $?)"
check "repl reports lex errors" "error: unexpected character '@'" "$(printf 'a @ b\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# evaluation: is binds, bare expressions print
check "is binds and names evaluate" "1" "$(printf 'x is 42\nx\nquit\n' | "$BIN" 2>/dev/null | grep -c 42)"
check "the article births protos" "1" "$(printf 'a world\nquit\n' | "$BIN" 2>/dev/null | grep -c 'a proto')"
check "an births too" "1" "$(printf 'an world\nquit\n' | "$BIN" 2>/dev/null | grep -c 'a proto')"
check "is without an article aliases" "1" "$(printf 'd is a world\nalias is d\nalias inherits d\nquit\n' | "$BIN" 2>/dev/null | grep -c false)"
check "is with the article introduces" "1" "$(printf 'd is a world\nr is a d\nr inherits d\nquit\n' | "$BIN" 2>/dev/null | grep -c true)"
check "births come from protos only" "error: births come from protos" "$(printf 'a 5\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "generate is no longer a special word" "error: nothing in the lineage hosts \"generate\"" "$(printf 'world ask generate\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "inheritance is a lineage predicate" "1" "$(printf 'c is a world\nc <- world\nquit\n' | "$BIN" 2>/dev/null | grep -c true)"
check "grandchildren do not lie about lineage" "1" "$(printf 'c is a world\ng is a c\ng <- world\nquit\n' | "$BIN" 2>/dev/null | grep -c false)"

# maybe: unpredictable-looking but replayable
run1=$(printf 'coin is a world\ncoin -> maybe\ncoin -> maybe\ncoin -> maybe\nquit\n' | "$BIN" 2>&1)
run2=$(printf 'coin is a world\ncoin -> maybe\ncoin -> maybe\ncoin -> maybe\nquit\n' | "$BIN" 2>&1)
check "maybe is replayable across runs" "$run1" "$run2"

# teaching: user-defined messages are stored chains
check "taught messages answer and delegate" "1" "$(printf 'dog is a world\ndog -> answer is 42\nrex is a dog\nrex -> answer\nquit\n' | "$BIN" 2>/dev/null | grep -c 42)"
check "the receiver is the one asked, even delegated" "1" "$(printf 'dog is a world\ndog ask who is inherits dog\nrex is a dog\nrex ask who\nquit\n' | "$BIN" 2>/dev/null | grep -c true)"
check "headless chains address the world at top level" "1" "$(printf 'ask maybe\nquit\n' | "$BIN" 2>/dev/null | grep -cE 'true|false')"
check "self is no longer a special word" "error: unknown name 'self'" "$(printf 'self\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "re-teaching replaces the chain" "1" "$(printf 'dog is a world\ndog -> answer is 1\ndog -> answer is 2\ndog -> answer\nquit\n' | "$BIN" 2>/dev/null | grep -c ' 2$')"
check "innate messages cannot be redefined" "error: value is innate" "$(printf 'world -> value is 1\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "runaway recursion is caught" "error: message recursion too deep" "$(printf 'dog is a world\ndog ask loop is ask loop\ndog ask loop\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# vocabulary: words and arrows are the same operators
check "word vocabulary evaluates" "1" "$(printf 'c is a world\nc inherits world\nquit\n' | "$BIN" 2>/dev/null | grep -c true)"

# pythonic whitespace: trailing is opens an indented block
check "block teaching delegates" "1" "$(printf 'dog is a world\ndog ask mood is\n    ask maybe\n\nrex is a dog\nrex ask mood\nquit\n' | "$BIN" 2>/dev/null | grep -cE 'true|false')"
check "name blocks answer with the last value" "1" "$(printf 'treasure is\n    a world\n    42\n\ntreasure\nquit\n' | "$BIN" 2>/dev/null | grep -c ' 42$')"
check "unindented block lines are refused" "error: expected an indented line or a blank line" "$(printf 'dog is a world\ndog ask mood is\nself ask maybe\nquit\n' | "$BIN" 2>&1 >/dev/null | head -1)"
check "empty bodies are refused" "error: the definition body is empty" "$(printf 'dog is a world\ndog ask mood is\n\nquit\n' | "$BIN" 2>&1 >/dev/null | head -1)"
check "nested definitions are refused" "error: definitions cannot nest (yet)" "$(printf 'dog is a world\ndog ask mood is\n    x is 1\nquit\n' | "$BIN" 2>&1 >/dev/null | head -1)"

# bijection: every <-> is an involution — twice is identity
vals=$(printf 'c is a world\nc -> value\n5 <-> c\nc -> value\n5 <-> c\nc -> value\nquit\n' | "$BIN" 2>/dev/null | grep -oE '[0-9]+$' | tail -3)
v1=$(echo "$vals" | sed -n 1p); v2=$(echo "$vals" | sed -n 2p); v3=$(echo "$vals" | sed -n 3p)
check "value <-> body applied twice is identity" "$v1" "$v3"
check "value <-> body actually transforms" "yes" "$([ "$v1" != "$v2" ] && echo yes)"

# mirrors 0 is the identity idiom: a body answers with its receiver, and
# the body is left as it was (retained 2026-11-18)
check "mirrors 0 answers with the receiver, even when delegated" "true" "$(printf 'box is a world\nbox ask me is mirrors 0\nkid is a box\nkid ask me inherits box\nquit\n' | "$BIN" 2>/dev/null | grep -oE 'true|false')"
idv=$(printf 'box is a world\nbox ask me is mirrors 0\nbox ask value\nbox ask me ask value\nbox ask value\nquit\n' | "$BIN" 2>/dev/null | sed '1,2d' | grep -oE '[0-9]+$' | tr '\n' ' ')
check "mirrors 0 leaves the body's value as it was" "yes" "$(echo $idv | awk '{print ($1==$2 && $2==$3 && NF==3) ? "yes" : "no"}')"

ex=$(printf 'box is a world\noth is a world\nbox -> value\noth -> value\nbox <-> oth\nbox -> value\noth -> value\nquit\n' | "$BIN" 2>/dev/null | grep -oE '[0-9]+$' | tail -4)
x1=$(echo "$ex" | sed -n 1p); y1=$(echo "$ex" | sed -n 2p)
x2=$(echo "$ex" | sed -n 3p); y2=$(echo "$ex" | sed -n 4p)
check "body <-> body exchanges one way" "$x2" "$y1"
check "body <-> body exchanges the other way" "$y2" "$x1"

# honesty: what is not implemented says so
check "oversized values are refused, not truncated" "error: an 8-cell loop carries at most 255" "$(printf 'c is a world\n256 <-> c\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "number-number bijection is honestly absent" "error: a bijection relates a value and a body, or two bodies" "$(printf '1 <-> 2\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "unknown names are reported" "error: unknown name 'ghost'" "$(printf 'ghost\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "unhosted messages are reported" "error: nothing in the lineage hosts \"dance\"" "$(printf 'world -> dance\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# running files: a file is a session without the banner and the prompts
P=tests/programs
check "a file prints the value of each statement that is not a definition" "$(cat $P/lineage.out)" "$("$BIN" $P/lineage.moop 2>&1)"
check "a file that runs exits 0" "0" "$("$BIN" $P/lineage.moop >/dev/null 2>&1; echo $?)"
repl=$({ cat $P/pets.moop; echo quit; } | "$BIN" 2>&1 | sed -e '1,2d' -e 's/moop> //g' -e 's/\.\.\.\.> //g' -e '/^$/d')
check "the same lines give the same values in a file and in the repl" "$repl" "$("$BIN" $P/pets.moop 2>&1)"
check "a file run twice gives the same values" "$("$BIN" $P/pets.moop 2>&1)" "$("$BIN" $P/pets.moop 2>&1)"
check "a file prints no banner and no prompt" "0" "$("$BIN" $P/pets.moop 2>&1 | grep -c -e 'moop' -e '> ')"

# a file stops at its first error, names the line, and exits 1
check "an error names the file and the line" "$P/stops.moop:3: error: unknown name 'ghost'" "$("$BIN" $P/stops.moop 2>&1 >/dev/null)"
check "nothing runs after the first error" "1" "$("$BIN" $P/stops.moop 2>/dev/null)"
check "what was printed before an error comes before it" "1
$P/stops.moop:3: error: unknown name 'ghost'" "$("$BIN" $P/stops.moop 2>&1)"
check "a file with an error exits 1" "1" "$("$BIN" $P/stops.moop >/dev/null 2>&1 && echo 0 || echo $?)"
check "an error inside a block names the body line" "$P/block_error.moop:4: error: unknown name 'ghost'" "$("$BIN" $P/block_error.moop 2>&1)"
check "an indented line under no open block is refused" "$P/gap.moop:5: error: an indented line belongs to a block, and none is open" "$("$BIN" $P/gap.moop 2>&1)"
check "the repl refuses it too" "error: an indented line belongs to a block, and none is open" "$(printf '  world\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# files made here, for bytes a text file should not be asked to hold
T=build/files
rm -rf $T && mkdir -p $T
printf '' > $T/empty.moop
check "an empty file runs and prints nothing" "0:" "$("$BIN" $T/empty.moop 2>&1; echo "$?:")"
printf 'treasure is\n    a world\n    7' > $T/open.moop
printf 'treasure is\n    a world\n    7\n\ntreasure' > $T/noeol.moop
check "the end of the file closes a block" "0" "$("$BIN" $T/open.moop >/dev/null 2>&1; echo $?)"
check "a last line needs no newline" "7" "$("$BIN" $T/noeol.moop 2>&1)"
printf 'x is 5\r\nx\r\n' > $T/crlf.moop
check "CRLF line endings are line endings" "5" "$("$BIN" $T/crlf.moop 2>&1)"
printf 'x is 5\nx\rx\n' > $T/cr.moop
check "a carriage return inside a line is not" "$T/cr.moop:2: error: unexpected byte 0x0D" "$("$BIN" $T/cr.moop 2>&1)"
printf 'x is 5\nx\000ghost\nx\n' > $T/nul.moop
check "a line holding a NUL byte is refused whole" "$T/nul.moop:2: error: a NUL byte in the line" "$("$BIN" $T/nul.moop 2>&1)"
printf 'x is 5\nx%01100d\nx\n' 0 > $T/long.moop
check "a line too long is refused, never split" "$T/long.moop:2: error: line too long" "$("$BIN" $T/long.moop 2>&1)"
check "the repl refuses it too, and goes on" "5" "$({ cat $T/long.moop; echo quit; } | "$BIN" 2>/dev/null | sed -e '1,2d' -e 's/moop> //g' -e '/^$/d')"
printf 'quit\n' > $T/quit.moop
check "quit is the repl's command, not a word of the language" "$T/quit.moop:1: error: unknown name 'quit'" "$("$BIN" $T/quit.moop 2>&1)"
check "a missing file is reported" "1" "$("$BIN" $T/none.moop 2>&1 | grep -c "^error: cannot open $T/none.moop: ")"
check "a missing file exits 1" "1" "$("$BIN" $T/none.moop >/dev/null 2>&1 && echo 0 || echo $?)"
check "a directory is not run as an empty file" "1" "$("$BIN" $T 2>&1 | grep -c "^error: cannot read $T: ")"
check "a directory exits 1" "1" "$("$BIN" $T >/dev/null 2>&1 && echo 0 || echo $?)"
check "moop runs one file" "error: moop runs one file" "$("$BIN" $P/lineage.moop $P/lineage.moop 2>&1)"
check "an unknown option is reported" "error: unknown option --help" "$("$BIN" --help 2>&1)"
check "bytes that do not print are named by code" "error: unexpected byte 0xC3" "$(printf 'x \303\251\nquit\n' | "$BIN" 2>&1 >/dev/null)"

exit $fail
