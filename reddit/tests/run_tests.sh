#!/bin/sh
# Smoke tests for the reddit. Run via `make test` in reddit/.
BIN=${BIN:-build/reddit}
fail=0
check() {
    desc=$1; expected=$2; actual=$3
    if [ "$actual" = "$expected" ]; then echo "ok   - $desc"; else echo "FAIL - $desc (expected '$expected', got '$actual')"; fail=1; fi
}
check "unit tests pass" "0" "$(build/test_reddit > /dev/null; echo $?)"
# the discipline, statically: exactly one function signature in the
# library names two tracks, and it is the port
check "only the port takes two tracks" "1" "$(grep -cE '^[a-z_ ]*\(.*Track \*[a-z]+.*Track \*[a-z]+' src/reddit.c)"
check "and that function is reddit_port" "1" "$(grep -cE '^bool reddit_port\(.*Track \*from.*Track \*to' src/reddit.c)"
check "the slot set did not change: six slots, gamma measured" "6" "$(grep -cE '^    (void|bool) \(\*[a-z]+\)\(' src/rme7.h)"

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
rules dogs 2 3 0 3600 1 1
post dogs 2 long title
rules dogs 9 50 0 3600 1 1
gamma cats
sub birds 4
post birds 4 tweet
vote birds 0 40
all 1
rules birds 4 50 0 3600 1 0
all 1
quit'
out=$(printf '%s\n' "$session" | "$BIN" 2>&1)
check "votes rank: the voted post is first" "1" "$(printf '%s\n' "$out" | grep -c '0\. \[+5, hot 5.00\] another cat')"
check "one half-life halves hot" "1" "$(printf '%s\n' "$out" | grep -c '\[+5, hot 2.50\] another cat  (u3)')"
check "the port translates and adapts" "1" "$(printf '%s\n' "$out" | grep -c 'x/cats: a cat  (u2)')"
check "rules refuse without altering" "1" "$(printf '%s\n' "$out" | grep -c 'refused: the rules do not admit that post')"
check "kappa refuses a non-moderator" "1" "$(printf '%s\n' "$out" | grep -c 'refused: not a moderator')"
check "gamma is measured" "1" "$(printf '%s\n' "$out" | grep -c '^gamma [0-9]')"
check "r/all: fed through the port, ranked by itself" "1" "$(printf '%s\n' "$out" | grep -c '^  0\. \[+41, hot 41.00\] x/birds: tweet  (u0)')"
check "r/all: carries the feeder's votes, not a fresh post (both builds)" "2" "$(printf '%s\n' "$out" | grep -c 'hot 2.50\] x/cats: another cat  (u0)')"
check "r/all: an opted-out subreddit vanishes from it" "1" "$(printf '%s\n' "$out" | grep -c '^r/all (2 posts')"
check "runs replay exactly" "$out" "$(printf '%s\n' "$session" | "$BIN" 2>&1)"
exit $fail
