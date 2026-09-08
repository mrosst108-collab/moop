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
check "theta has no comment-ranking parameter (field names)" "0" "$(sed -n '/} Post;/,/} Ranking;/p' src/rme7.h | grep -cE '^ +(int|bool|double|size_t) [a-z_]*comment')"
# the command language cannot drift from its own description
check "help lists exactly the commands the dispatcher accepts" "$(grep -oE 'strcmp\(cmd, "[a-z]+"\)' src/main.c | grep -oE '"[a-z]+"' | tr -d '"' | sort | tr '\n' ' ')" "$(grep -oE '^    \{ "[a-z]+"' src/main.c | grep -oE '[a-z]+' | sort | tr '\n' ' ')"
check "help runs and names every command" "16" "$(printf 'help\nquit\n' | "$BIN" 2>/dev/null | grep -cE '^[a-z]+ ')"
check "show prints theta as it is" "1" "$(printf 'sub cats 1\nrules cats 1 40 2.5 1800 0 1\nlock cats 1 7\nshow cats\nquit\n' | "$BIN" 2>/dev/null | grep -c '^  rules: max_title=40 min_hot=2.50 half_life=1800 crosspost=no export=yes locked=7 banned=-1 mods=u1$')"
check "capacity is stated, not hidden" "1" "$(for i in $(seq 1 17); do echo "sub s$i 1"; done | { cat; echo quit; } | "$BIN" 2>&1 >/dev/null | grep -c 'refused: capacity is 16 subreddits')"
check "the slot set did not change: six slots, gamma measured" "6" "$(grep -cE '^    (void|bool) \(\*[a-z]+\)\(' src/rme7.h)"

session='sub cats 1
post cats 1 a cat
post cats 3 another cat
vote cats 1 4
comment cats 4 1 nice cat
comment cats 5 1 meh
vote cats 2 3
comment cats 6 2 agreed
comment cats 6 9 orphan
show cats
tick 3600
show cats
sub dogs 2
cross cats 1 dogs 2
cross cats 2 dogs 2
show dogs
rules dogs 2 3 0 3600 1 1
post dogs 2 long title
rules dogs 9 50 0 3600 1 1
lock cats 1 1
comment cats 7 1 too late
lock cats 9 1
gamma cats
sub birds 4
post birds 4 tweet
vote birds 0 40
all 1
rules birds 4 50 0 3600 1 0
all 1
post birds 3 by user three
comment cats 3 0 also user three
profile 3 5
rules u3 3 50 5 3600 1 0
profile 3 5
rules u3 9 50 0 3600 1 0
post u3 3 straight into my profile
ban 5 3
ban 0 3
post cats 3 after the ban
quit'
out=$(printf '%s\n' "$session" | "$BIN" 2>&1)
check "votes rank: the voted post is first" "1" "$(printf '%s\n' "$out" | grep -c '^  #1 \[+5, hot 5.00\] another cat  (u3)$')"
check "comments nest under their parent, ranked among siblings" "1" "$(printf '%s\n' "$out" | grep -c '^      #2 \[+4, hot 4.00\] nice cat  (u4)$')"
check "and recursively" "1" "$(printf '%s\n' "$out" | grep -c '^          #4 \[+1, hot 1.00\] agreed  (u6)$')"
check "an orphan comment, and one under a locked post, are refused" "2" "$(printf '%s\n' "$out" | grep -c 'refused: the rules do not admit that comment')"
check "one half-life halves hot, comments included" "1" "$(printf '%s\n' "$out" | grep -c '^      #2 \[+4, hot 2.00\] nice cat  (u4)$')"
check "the port translates and adapts a post" "1" "$(printf '%s\n' "$out" | grep -c 'x/cats: another cat  (u2)')"
check "the port refuses a comment" "1" "$(printf '%s\n' "$out" | grep -c 'refused: the port did not admit it')"
check "rules refuse without altering: one too long, one banned" "2" "$(printf '%s\n' "$out" | grep -c 'refused: the rules do not admit that post')"
check "kappa refuses a non-moderator: rules, lock, another's profile" "3" "$(printf '%s\n' "$out" | grep -c 'refused: not a moderator')"
check "gamma is measured" "1" "$(printf '%s\n' "$out" | grep -c '^gamma [0-9]')"
check "r/all: fed through the port, ranked by itself" "1" "$(printf '%s\n' "$out" | grep -c '^  #2 \[+41, hot 41.00\] x/birds: tweet  (u0)$')"
check "r/all: carries the feeder's votes, not a fresh post (both builds)" "2" "$(printf '%s\n' "$out" | grep -c 'hot 2.50\] x/cats: another cat  (u0)')"
check "r/all: an opted-out subreddit vanishes from it" "1" "$(printf '%s\n' "$out" | grep -c '^r/all (2 nodes')"
check "profile: fed through the port, karma summed inside it" "1" "$(printf '%s\n' "$out" | grep -c '^  karma 6$')"
check "profile: a comment arrives flattened, marked with its origin" "1" "$(printf '%s\n' "$out" | grep -c '^  #1 \[+1, hot 1.00\] x/cats: also user three  (u3)$')"
check "profile: an opted-out subreddit is absent from it too" "0" "$(printf '%s\n' "$out" | grep -c 'x/birds: by user three')"
check "theta_u has a consumer: the profile's min_hot hides cold nodes" "1" "$(printf '%s\n' "$out" | grep -c '^  karma 0$')"
check "a user originates nothing into their own track" "1" "$(printf '%s\n' "$out" | grep -c 'refused: no such subreddit')"
check "ban: only the site" "1" "$(printf '%s\n' "$out" | grep -c 'refused: not the site')"
check "runs replay exactly" "$out" "$(printf '%s\n' "$session" | "$BIN" 2>&1)"
exit $fail
