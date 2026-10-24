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

# R 'lines' [n]: run lines in a fresh REPL, print the last n output lines
R() {
    printf "$1\nquit\n" | "$BIN" 2>&1 |
        sed -e ':a' -e 's/^moop> //' -e 'ta' -e 's/^\.\.\.\.> //' -e 'ta' -e '/^$/d' |
        tail -n "${2:-1}"
}

check "--version prints version" "moop 0.10.0" "$("$BIN" --version)"
check "core unit tests pass" "0" "$(build/test_core > /dev/null; echo $?)"
check "quit exits the repl cleanly" "0" "$(printf 'quit\n' | "$BIN" >/dev/null 2>&1; echo $?)"
check "repl reports lex errors" "error: unexpected character '@'" "$(printf 'a @ b\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# evaluation: is binds, bare expressions print
check "is binds and names evaluate" "1" "$(printf 'x is 42\nx\nquit\n' | "$BIN" 2>/dev/null | grep -c 42)"
check "the article births protos" "1" "$(printf 'a world\nquit\n' | "$BIN" 2>/dev/null | grep -c 'a proto')"
check "an births too" "1" "$(printf 'an world\nquit\n' | "$BIN" 2>/dev/null | grep -c 'a proto')"
check "is without an article aliases" "2" "$(R 'd is a world\nalias is d\nalias -> m is 2\nd -> m')"
check "is with the article introduces" "1" "$(R 'd is a world\nd -> m is 1\nr is a d\nr -> m is 2\nd -> m')"
check "births come from protos only" "error: births come from protos" "$(printf 'a 5\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "generate is no longer a special word" "error: nothing in the lineage hosts \"generate\"" "$(printf 'world ask generate\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# inheritance: <- declares whom a proto defers to
D='dog is a world\ndog -> bark is 7\ncat is a world'
check "<- declares inheritance" "7" "$(R "$D\ncat <- dog\ncat -> bark")"
check "<- answers the child, so pipelines continue" "7" "$(R "$D\ncat <- dog -> bark")"
check "grandchildren delegate through a declared parent" "7" "$(R "$D\nkit is a cat\ncat <- dog\nkit -> bark")"
check "re-declaring replaces the parent" "error: nothing in the lineage hosts \"bark\"" "$(R "$D\ncat <- dog\nfish is a world\ncat <- fish\ncat -> bark")"
check "inheritance cannot loop" "error: inheritance cannot loop: the parent already inherits from the child" "$(R 'dog is a world\nkit is a dog\ndog <- kit')"
check "a proto cannot inherit from itself" "error: a proto cannot inherit from itself" "$(R 'dog is a world\ndog <- dog')"
check "inheritance relates protos" "error: inheritance relates protos" "$(R 'dog is a world\ndog <- 5')"

# maybe: unpredictable-looking but replayable
run1=$(printf 'coin is a world\ncoin -> maybe\ncoin -> maybe\ncoin -> maybe\nquit\n' | "$BIN" 2>&1)
run2=$(printf 'coin is a world\ncoin -> maybe\ncoin -> maybe\ncoin -> maybe\nquit\n' | "$BIN" 2>&1)
check "maybe is replayable across runs" "$run1" "$run2"

# teaching: user-defined messages are stored chains
check "taught messages answer and delegate" "1" "$(printf 'dog is a world\ndog -> answer is 42\nrex is a dog\nrex -> answer\nquit\n' | "$BIN" 2>/dev/null | grep -c 42)"
check "the receiver is the one asked, even delegated" "$(R 'dog is a world\nrex is a dog\nrex -> value')" "$(R 'dog is a world\ndog -> who is -> value\nrex is a dog\nrex -> who')"
check "headless chains address the world at top level" "1" "$(printf 'ask maybe\nquit\n' | "$BIN" 2>/dev/null | grep -cE 'true|false')"
check "self is no longer a special word" "error: unknown name 'self'" "$(printf 'self\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "re-teaching replaces the chain" "1" "$(printf 'dog is a world\ndog -> answer is 1\ndog -> answer is 2\ndog -> answer\nquit\n' | "$BIN" 2>/dev/null | grep -c ' 2$')"
check "innate messages cannot be redefined" "error: value is innate" "$(printf 'world -> value is 1\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "runaway recursion is caught" "error: message recursion too deep" "$(printf 'dog is a world\ndog ask loop is ask loop\ndog ask loop\nquit\n' | "$BIN" 2>&1 >/dev/null)"

# vocabulary: the arrows are canonical; the words are the same operators
check "word aliases are the same operators" "7" "$(R 'dog is a world\ndog ask bark is 7\ncat is a world\ncat inherits dog\ncat ask bark')"

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

ex=$(printf 'box is a world\noth is a world\nbox -> value\noth -> value\nbox <-> oth\nbox -> value\noth -> value\nquit\n' | "$BIN" 2>/dev/null | grep -oE '[0-9]+$' | tail -4)
x1=$(echo "$ex" | sed -n 1p); y1=$(echo "$ex" | sed -n 2p)
x2=$(echo "$ex" | sed -n 3p); y2=$(echo "$ex" | sed -n 4p)
check "body <-> body exchanges one way" "$x2" "$y1"
check "body <-> body exchanges the other way" "$y2" "$x1"

# export: observing a value and depositing it back cancels it on the
# tapes; the value lives on in the user layer and restores them
exp=$(printf 'box is a world\nbox -> value\nn is box -> value\nn <-> box\nbox -> value\nn <-> box\nbox -> value\nquit\n' | "$BIN" 2>/dev/null | grep -oE '[0-9]+$' | tail -3)
e1=$(echo "$exp" | sed -n 1p); e2=$(echo "$exp" | sed -n 2p); e3=$(echo "$exp" | sed -n 3p)
check "depositing an observed value exports it" "0" "$e2"
check "the held value restores the body" "$e1" "$e3"

# reflection: quotes mention code, so user code is a value
check "a quote is code, not its result" '"-> maybe"' "$(R 'plan is "-> maybe"\nplan')"
check "code is written with canonical arrows" '"dog -> mood <-> an animal <- world"' "$(R 'x is "dog ask mood mirrors a animal inherits world"\nx')"
check "a quoted message reads the taught code" '"-> maybe"' "$(R 'dog is a world\ndog -> mood is -> maybe\ndog -> "mood"')"
check "reading follows the lineage like a send" '"-> maybe"' "$(R 'dog is a world\ndog -> mood is -> maybe\nrex is a dog\nrex -> "mood"')"
check "teaching from code installs it" "9" "$(R 'dog is a world\ndog -> "mood" is "9"\ndog -> mood')"
check "the quote moves across is" "$(R 'd is a world\nd -> m is -> maybe\nd -> "m"')" "$(R 'd is a world\nd -> "m" is "-> maybe"\nd -> "m"')"
check "behaviors copy as code" "42" "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    42\n\ncat is a world\ncat -> "both" is dog -> "both"\ncat -> both')"
check "block code reads back as a block" "a block:" "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    42\n\ndog -> "both"' 3 | head -n 1)"
check "code values do not alias teachings" '"1"' "$(R 'dog is a world\ndog -> m is 1\nold is dog -> "m"\ndog -> m is 2\nold')"
check "nested quotes alternate the marks" "\"rex -> mood is '-> maybe'\"" "$(R "meta is \"rex -> mood is '-> maybe'\"\nmeta")"
check "code that answers code reads back nested" "\"'-> maybe'\"" "$(R 'dog is a world\ndog -> tpl is "-> maybe"\ndog -> "tpl"')"
check "running code is teaching it, then asking" "a proto" "$(R 'world -> "go" is "a world"\n-> go')"
check "innate messages have no code" "error: maybe is innate: it has no code" "$(R 'world -> "maybe"')"
check "only code is taught to a quoted message" "error: only code can be taught to a quoted message" "$(R 'dog is a world\ndog -> "mood" is 5')"
check "quoted definitions cannot be installed (yet)" "error: definitions cannot nest (yet)" "$(R 'dog is a world\ndog -> "m" is "x is 1"')"
check "a quoted message is a single name" "error: a quoted message is a single name" "$(R 'world -> "-> maybe"')"
check "an unclosed quote is reported" "error: a quote is never closed" "$(R 'x is "-> maybe')"

# taking code apart: every code value answers first and rest
P='plan is "dog -> mood <-> 5"'
check "a chain's first part is its head" '"dog"' "$(R "$P\nplan -> first")"
check "a chain's rest is a headless chain" '"-> mood <-> 5"' "$(R "$P\nplan -> rest")"
check "a headless chain's first part is a step" '"-> mood"' "$(R "$P\nplan -> rest -> first")"
check "a step's rest is its operand" '"5"' "$(R "$P\nplan -> rest -> rest -> rest")"
check "an operator is a fragment" '"<->"' "$(R "$P\nplan -> rest -> rest -> first")"
check "a single number has no parts" "error: a single number has no parts" "$(R "$P\nplan -> rest -> rest -> rest -> first")"
check "a definition's first part is its head" '"rex -> mood is"' "$(R 'd is "rex -> mood is -> maybe"\nd -> first')"
check "a head comes apart into designator and joint" '"rex -> mood" "is"' "$(R 'd is "rex -> mood is -> maybe"\nd -> first -> first\nd -> first -> rest' 2 | tr '\n' ' ' | sed 's/ $//')"
check "a definition's rest is what it is" '"-> maybe"' "$(R 'd is "rex -> mood is -> maybe"\nd -> rest')"
check "a block's first part is its first line" '"-> maybe"' "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    42\n\ndog -> "both" -> first')"
check "a block's rest is the rest of the block" 'a block:     42' "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    42\n\ndog -> "both" -> rest' 2 | tr '\n' ' ' | sed 's/ $//')"
check "a birth's rest is what it births from" '"dog"' "$(R '"a dog" -> rest')"
check "a birth's first part is its article" '"a"' "$(R '"a dog" -> first')"
check "a single operator has no parts" "error: a single operator has no parts" "$(R '"->" -> first')"
check "a quote's first part is its inside" '"-> maybe"' "$(R "q is \"'-> maybe'\"\nq -> first")"
check "parts can be taught" "5" "$(R "dog is a world\n$P\ndog -> \"m\" is plan -> rest -> rest -> rest\ndog -> m")"
check "code answers only first and rest" "error: code answers only first and rest" "$(R "$P\nplan -> value")"

# building code: <- joins code, the right following the left, so that
# (c -> first) <- (c -> rest) gives c back for every shape
law() { R "c is \"$1\"\nf is c -> first\nr is c -> rest\nf <- r"; }
check "joining restores a chain" '"dog -> mood <-> 5"' "$(law 'dog -> mood <-> 5')"
check "joining restores a headless chain" '"-> mood <-> 5"' "$(law '-> mood <-> 5')"
check "joining restores a step" '"<-> 5"' "$(law '<-> 5')"
check "joining restores a definition" '"rex -> mood is -> maybe"' "$(law 'rex -> mood is -> maybe')"
check "joining restores a head" '"rex -> mood is"' "$(law 'rex -> mood is')"
check "joining restores a birth" '"an animal"' "$(law 'an animal')"
check "joining restores a block" 'a block:     -> maybe     42' "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    42\n\nc is dog -> "both"\nf is c -> first\nr is c -> rest\nf <- r' 3 | tr '\n' ' ' | sed 's/ $//')"
check "code builds left to right" '"dog -> mood"' "$(R '"dog" <- "->" <- "mood"')"
check "a definition builds from its pieces" '"rex is 42"' "$(R '"rex" <- "is" <- "42"')"
check "fragments print and re-enter" '"dog ->"' "$(R 'x is "dog ->"\nx')"
check "pieces that do not read as code do not join" "error: these do not join: expected an operator between expressions" "$(R '"dog" <- "cat"')"
check "a line joins onto a block" 'a block:     42     -> value' "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    -> value\n\none is dog -> "both" -> rest\n"42" <- one' 3 | tr '\n' ' ' | sed 's/ $//')"
check "a fragment is never a line" "error: a line of a block must be whole code, not a fragment" "$(R 'dog is a world\ndog -> both is\n    -> maybe\n    -> value\n\none is dog -> "both" -> rest\none <- "dog ->"')"
check "fragments are never taught" "error: a fragment is not whole code: it still waits for its last piece" "$(R 'dog is a world\ndog -> "m" is "dog ->"')"
check "assembled code is taught and runs" "7" "$(R 'dog is a world\ndog -> seven is 7\ndog -> "m" is "->" <- "seven"\ndog -> m')"
check "<- does not mix code and protos" "error: <- joins code to code, or makes a proto inherit from a proto" "$(R 'world <- "x"')"

# honesty: what is not implemented says so
check "oversized values are refused, not truncated" "error: an 8-cell loop carries at most 255" "$(printf 'c is a world\n256 <-> c\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "number-number bijection is honestly absent" "error: a bijection relates a value and a body, or two bodies" "$(printf '1 <-> 2\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "unknown names are reported" "error: unknown name 'ghost'" "$(printf 'ghost\nquit\n' | "$BIN" 2>&1 >/dev/null)"
check "unhosted messages are reported" "error: nothing in the lineage hosts \"dance\"" "$(printf 'world -> dance\nquit\n' | "$BIN" 2>&1 >/dev/null)"

exit $fail
