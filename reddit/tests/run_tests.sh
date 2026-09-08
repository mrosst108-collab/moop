#!/bin/sh
# Smoke tests for the reddit. Run via `make test` in reddit/.
BIN=${BIN:-build/reddit}
fail=0
check() {
    desc=$1; expected=$2; actual=$3
    if [ "$actual" = "$expected" ]; then echo "ok   - $desc"; else echo "FAIL - $desc (expected '$expected', got '$actual')"; fail=1; fi
}
check "unit tests pass" "0" "$(build/test_reddit > /dev/null; echo $?)"

session='sub cats 1
post cats 1 a cat
post cats 3 another cat
vote cats 1 4
show cats
tick 3600
show cats
sub dogs 2
cross cats 1 dogs 2
show dogs
rules dogs 2 3 0 3600 1
post dogs 2 long title
rules dogs 9 50 0 3600 1
gamma cats
quit'
out=$(printf '%s\n' "$session" | "$BIN" 2>&1)
check "votes rank: the voted post is first" "1" "$(printf '%s\n' "$out" | grep -c '0\. \[+5, hot 5.00\] another cat')"
check "one half-life halves hot" "1" "$(printf '%s\n' "$out" | grep -c '\[+5, hot 2.50\]')"
check "the port translates and adapts" "1" "$(printf '%s\n' "$out" | grep -c 'x/cats: a cat  (u2)')"
check "rules refuse without altering" "1" "$(printf '%s\n' "$out" | grep -c 'refused: the rules do not admit that post')"
check "kappa refuses a non-moderator" "1" "$(printf '%s\n' "$out" | grep -c 'refused: not a moderator')"
check "gamma is measured" "1" "$(printf '%s\n' "$out" | grep -c '^gamma [0-9]')"
check "runs replay exactly" "$out" "$(printf '%s\n' "$session" | "$BIN" 2>&1)"
exit $fail
