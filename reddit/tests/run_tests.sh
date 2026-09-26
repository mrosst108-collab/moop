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
check "help lists exactly the commands the dispatcher accepts" "$(sed -n '/^static bool execute/,/^static bool run/p' src/main.c | grep -oE 'strcmp\(cmd, "[a-z]+"\)' | grep -oE '"[a-z]+"' | tr -d '"' | sort -u | tr '\n' ' ')" "$(grep -oE '^    \{ "[a-z]+"' src/main.c | grep -oE '[a-z]+' | sort | tr '\n' ' ')"
check "help runs and names every command" "26" "$(printf 'help\nquit\n' | "$BIN" 2>/dev/null | grep -cE '^[a-z]+ ')"
check "show prints theta as it is" "1" "$(printf 'sub cats 1\nrules cats 1 40 2.5 1800 0 1\nlock cats 1 7\nshow cats\nquit\n' | "$BIN" 2>/dev/null | grep -c '^  rules: max_title=40 min_hot=2.50 half_life=1800 crosspost=no export=yes locked=7 banned=none mods=u1$')"
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
# each user owns exactly one personal track: its name cannot be squatted
check "a subreddit cannot take a personal track's name" "1" "$(printf 'sub u7 2\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: uN names belong to users')"
check "a profile is its user's, moderated by them alone" "1" "$(printf 'sub u7 2\nprofile 7 5\nquit\n' | "$BIN" 2>/dev/null | grep -c 'mods=u7$')"
check "a subreddit named like a word starting with u is fine" "0" "$(printf 'sub unix 2\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c refused)"

# anti-puppet (prediction 6): a generator-side actor cannot write the
# site's admission data or evaluation configuration
check "'all' is reserved: a user cannot found r/all" "1" "$(printf 'sub all 5\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: that name is taken')"
check "a subreddit name longer than the field is refused whole" "1" "$(printf 'sub aaaaaaaaaaaaaaaaaaaaaaaaaaaa5 1\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: that name is too long')"
check "ban is site-held: a moderator cannot ban on their own track" "1" "$(printf 'sub cats 1\nban 1 3\nshow cats\nquit\n' | "$BIN" 2>&1 | grep -c 'banned=none')"
check "a moderator's ban is refused, saying not the site" "1" "$(printf 'sub cats 1\nban 1 3\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: not the site')"
check "a moderator's refused ban does not lift the site's ban (channel 1 re-run)" "1" "$(printf 'sub cats 1\nban 0 99\nban 1 99\nshow cats\nquit\n' | "$BIN" 2>/dev/null | grep -c 'banned=u99 ')"
check "a second site ban keeps the first: the set holds both" "1" "$(printf 'sub cats 1\nban 0 3\nban 0 4\nshow cats\nquit\n' | "$BIN" 2>/dev/null | grep -c 'banned=u3,u4 ')"
check "a re-banned user cannot post; the earlier ban still bars its user" "1" "$(printf 'sub cats 1\nban 0 3\nban 0 4\npost cats 3 after two bans\nshow cats\nquit\n' | "$BIN" 2>&1 | grep -c 'refused: the rules do not admit that post')"
check "unban is site-held: a moderator cannot lift a ban" "1" "$(printf 'sub cats 1\nban 0 3\nunban 1 3\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: not the site')"
check "the site lifts one ban and the other stays" "1" "$(printf 'sub cats 1\nban 0 3\nban 0 4\nunban 0 3\nshow cats\nquit\n' | "$BIN" 2>/dev/null | grep -c 'banned=u4 ')"
check "a subreddit founded after a ban is founded under it" "1" "$(printf 'sub cats 1\nban 0 3\nsub dogs 1\npost dogs 3 banned here too\nshow dogs\nquit\n' | "$BIN" 2>&1 | grep -c 'refused: the rules do not admit that post')"
check "kappa_Sigma: a banned user's attributed vote is refused" "1" "$(printf 'sub cats 1\npost cats 1 a post\nban 0 3\ncast cats 3 0 1\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: delta not')"
check "a ballot is +/-1: a large delta is refused" "1" "$(printf 'sub cats 1\npost cats 1 a post\ncast cats 2 0 1000000\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: delta not')"
check "a user does not certify their own authority: self-follow refused" "1" "$(printf 'follow 3 3\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: a user does not certify their own authority')"
check "a non-site actor changes no rank in r/all's theta (blend)" "1" "$(printf 'sub cats 1\npost cats 1 a\npost cats 1 b\nblend 1 cats 0.5\nshow cats\nquit\n' | "$BIN" 2>&1 | grep -c 'refused: only the site sets lambda')"
# the C field-holder battery names every field of theta, no more, no fewer
check "the field-holder battery covers every field of Rules and Ranking" \
    "$(sed -n '/} Post;/,/} Ranking;/p' src/rme7.h | grep -oE '^    (size_t|double|bool|int|unsigned) [a-z_]+' | awk '{print $2}' | grep -vE '^n(banned|subs)$' | sort | tr '\n' ' ')" \
    "$(sed -n '/^static const char \*change_field/,/^}/p' tests/test_reddit.c | grep -oE 'return "[a-z_]+"' | grep -oE '"[a-z_]+"' | tr -d '"' | sort | tr '\n' ' ')"
# every command in the language, issued by non-site actors (a moderator on
# their own track, strangers, a banned user), leaves the site's
# configuration, every existing track's admission data, and every rank
# byte-identical; no evaluation (rank, weigh) runs in between
T=$(mktemp -d)
setup='sub cats 1
sub dogs 2
post cats 1 one
post dogs 2 two
comment cats 4 0 four here
profile 2 3
profile 4 3
ban 0 3
pagerank 0 0.8 0.0001 50
clock 0 30
blend 0 cats 0.5
follow 1 2
follow 2 4
follow 4 1
rank
cast cats 4 0 1
weigh cats'
battery='sub newsub 5
post cats 5 hello
post cats 3 barred
comment cats 5 0 hi
vote cats 0 1
cast cats 5 0 1
cross cats 0 dogs 5
cross cats 0 u2 5
vote u2 0 50
lock cats 1 0
lock cats 5 0
rules cats 1 50 0 1800 0 0
rules cats 5 10 9 60 0 0
rules u1 2 10 9 60 0 0
ban 1 5
ban 3 3
unban 1 3
unban 3 3
profile 5 3
profile 1 3
follow 5 1
follow 3 2
unfollow 1 2
pagerank 1 0.5 0.1 3
pagerank 3 0.5 0.1 3
clock 1 5
clock 5 5
blend 1 cats 1
blend 2 dogs 0
sweep cats
gamma cats'
views='show cats
show dogs
show u1
show u2
show u4
all 5'
# T_E as printed: the site's parameters and bans on every track, every
# rank, W in every subreddit, and the X of the profiles the battery does
# not rebuild. r/all's X is left out: `all K` is itself a declared
# evaluation, and a moderator's opt-out (track-held) legitimately moves it
site_view() { awk '/^r\// { t = $1; print t; next }
    { for (i = 1; i <= NF; i++) if ($i ~ /^(banned|lambda|alpha|tolerance|rounds|interval)=/) print t, $i
      if ($1 == "rank") print t, $0
      if (t != "r/all" && match($0, /W -?[0-9.]+/)) print t, substr($0, RSTART, RLENGTH)
      if ((t == "r/u2" || t == "r/u4") && $1 ~ /^#/) print t, $0 }'; }
printf '%s\n' "$setup" > "$T/setup.txt"
printf '%s\n%s\n' "$setup" "$battery" > "$T/battery.txt"
sv_before=$(printf '%s\nquit\n' "$views" | "$BIN" "$T/setup.txt" 2>/dev/null | site_view)
sv_after=$(printf '%s\nquit\n' "$views" | "$BIN" "$T/battery.txt" 2>/dev/null | site_view)
check "the battery's baseline holds bans, lambda, alpha, interval, ranks, W, profile X" "yes" "$([ "$(printf '%s\n' "$sv_before" | grep -c ' banned=u3$')" = 2 ] && printf '%s\n' "$sv_before" | grep -q '^r/cats lambda=0.50$' && printf '%s\n' "$sv_before" | grep -q '^r/all alpha=0.80$' && printf '%s\n' "$sv_before" | grep -q '^r/all interval=30$' && [ "$(printf '%s\n' "$sv_before" | grep -c ' rank ')" = 3 ] && printf '%s\n' "$sv_before" | grep -q '^r/cats W [1-9]' && printf '%s\n' "$sv_before" | grep -q '^r/u2 .*x/dogs: two' && printf '%s\n' "$sv_before" | grep -q '^r/u4 .*x/cats: four here' && echo yes)"
check "no non-site command writes the site's configuration, admission data, or a rank" "$sv_before" "$sv_after"
rm -rf "$T"
# the forcing failures of channels 4, 5 and 6, re-run
check "a voter with no track contributes nothing and stops nothing" "1" "$(printf 'sub news 1\npost news 1 first\npost news 1 second\nfollow 2 3\nfollow 3 2\nrank\ncast news 9 0 1\ncast news 2 1 1\nweigh news\nshow news\nquit\n' | "$BIN" 2>/dev/null | grep -c '#1 \[+2, hot 2.00, W 1.00 heat 1.00\] second')"
check "weigh scales by the N of the last rank: a new profile moves no W" "1" "$(printf 'follow 1 2\nfollow 2 3\nrank\nsub news 0\npost news 0 x\ncast news 3 0 1\nweigh news\nshow news\nprofile 7 1\nweigh news\nshow news\nquit\n' | "$BIN" 2>/dev/null | grep -oE 'W [0-9.]+' | sort -u | wc -l)"
check "nobody crossposts or votes into a profile" "2" "$(printf 'sub cats 1\npost cats 9 from nine\npost cats 3 by three\nprofile 3 5\ncross cats 0 u3 9\nvote u3 0 50\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: no such subreddit')"
check "and the profile is as its rebuild left it" "r/u3 (1 nodes, 1 mods)" "$(printf 'sub cats 1\npost cats 9 from nine\npost cats 3 by three\nprofile 3 5\ncross cats 0 u3 9\nvote u3 0 50\nshow u3\nquit\n' | "$BIN" 2>/dev/null | grep '^r/u3' | tail -1)"
check "a crosspost starts over: the sender's ballots and W stay behind" "1" "$(printf 'follow 1 2\nfollow 2 1\nrank\nsub cats 1\nsub dogs 2\npost cats 1 one\ncast cats 2 0 1\nweigh cats\ncross cats 0 dogs 5\nweigh dogs\nshow dogs\nquit\n' | "$BIN" 2>/dev/null | grep -c '^  #0 \[+1, hot 1.00\] x/cats: one  (u5)$')"

# persistence: the transcript is the input history, replayed exactly
T=$(mktemp -d)
hist='sub science 1
post science 1 Water on Mars
comment science 2 0 Source?
vote science 0 4
tick 3600
rules science 1 50 0.5 3600 1 1
lock science 1 0
sub cats 3
cross science 0 cats 3
all 2
profile 1 5'
direct=$(printf '%s\nshow science\nshow cats\nquit\n' "$hist" | "$BIN" 2>/dev/null | sed -n '/^r\/science/,$p')
printf '%s\n' "$hist" > "$T/hist.txt"
fromfile=$(printf 'show science\nshow cats\nquit\n' | "$BIN" "$T/hist.txt" 2>/dev/null)
check "a file replays to the same state as stdin" "$direct" "$fromfile"
printf 'save %s\n%s\nhelp\nquit\n' "$T/saved.txt" "$hist" | "$BIN" >/dev/null 2>&1
check "save records application commands only: no save, help, quit" "0" "$(grep -cE '^(save|help|quit)' "$T/saved.txt")"
check "save records every application command" "$(printf '%s\n' "$hist" | wc -l)" "$(wc -l < "$T/saved.txt")"
roundtrip=$(printf 'show science\nshow cats\nquit\n' | "$BIN" "$T/saved.txt" 2>/dev/null)
check "restart from a saved transcript reproduces the session" "$direct" "$roundtrip"
check "replay is silent" "0" "$(printf 'quit\n' | "$BIN" "$T/hist.txt" 2>&1 | wc -c)"
check "a missing transcript file is an error" "1" "$(printf 'quit\n' | "$BIN" "$T/none.txt" >/dev/null 2>&1; echo $?)"
rm -rf "$T"

# delegation: distributed power iteration equals an independent PageRank reference
# graph: 1->2, 2->3, 1->4; 3 and 4 dangling; alpha 0.85, uniform teleport
graph='follow 1 2
follow 2 3
follow 1 4
rank
show u1
show u2
show u3
show u4'
ours=$(printf '%s\nquit\n' "$graph" | "$BIN" 2>/dev/null | grep -oE '^  rank [0-9.]+' | awk '{printf "%.4f ", $2}')
ref=$(awk 'BEGIN{ n=4; a=0.85
  # adjacency: out[u]=list; dangling spread uniform; 100 rounds
  out[1]="2 4"; out[2]="3"; out[3]=""; out[4]=""
  for(i=1;i<=n;i++) r[i]=1/n
  for(t=0;t<100;t++){ for(i=1;i<=n;i++) in_[i]=0
    for(u=1;u<=n;u++){ m=split(out[u],d," "); if(m==0){ for(j=1;j<=n;j++) in_[j]+=r[u]/n } else { for(j=1;j<=m;j++) in_[d[j]]+=r[u]/m } }
    for(i=1;i<=n;i++) r[i]=a*in_[i]+(1-a)/n }
  for(i=1;i<=n;i++) printf "%.4f ", r[i] }')
check "rank equals an independent PageRank reference to four decimals" "$ref" "$ours"
check "rank reports convergence" "1" "$(printf '%s\nquit\n' "$graph" | "$BIN" 2>/dev/null | grep -c '^rank: [0-9]* rounds, change [0-9.e-]*, converged$')"
check "ranks sum to one" "1.0000" "$(printf '%s\nquit\n' "$graph" | "$BIN" 2>/dev/null | grep -oE '^  rank [0-9.]+' | awk '{s+=$2} END{printf "%.4f", s}')"
# stale until the next run; propagation one hop per round
stale=$(printf '%s\nfollow 3 1\nshow u1\nrank\nshow u1\nquit\n' "$graph" | "$BIN" 2>/dev/null | grep -oE '^  rank [0-9.]+' | awk '{print $2}' | tail -2)
check "a subscription change does not move rank until the next run" "yes" "$([ "$(echo "$stale" | sed -n 1p)" != "$(echo "$stale" | sed -n 2p)" ] && [ "$(echo "$stale" | sed -n 1p)" = "$(printf '%s\nquit\n' "$graph" | "$BIN" 2>/dev/null | grep -oE '^  rank [0-9.]+' | awk 'NR==1{print $2}')" ] && echo yes)"
onehop=$(printf 'pagerank 0 0.85 0 1\nfollow 1 2\nfollow 2 3\nrank\nshow u3\nquit\n' | "$BIN" 2>/dev/null | grep -oE '^  rank [0-9.]+' | awk '{print $2}')
twohop=$(printf 'pagerank 0 0.85 0 2\nfollow 1 2\nfollow 2 3\nrank\nshow u3\nquit\n' | "$BIN" 2>/dev/null | grep -oE '^  rank [0-9.]+' | awk '{print $2}')
check "with one round, influence travels one hop; with two, further" "yes" "$([ "$onehop" != "$twohop" ] && echo yes)"
check "pagerank parameters are the site's theta, shown on r/all" "1" "$(printf 'pagerank 0 0.5 0.001 7\nall 1\nquit\n' | "$BIN" 2>/dev/null | grep -c 'alpha=0.50 tolerance=0.001 rounds=7')"
check "only the site may set them" "1" "$(printf 'pagerank 5 0.5 0.001 7\nquit\n' | "$BIN" 2>&1 >/dev/null | grep -c 'refused: not the site')"
check "only the user may change whom they follow" "1" "$(printf 'follow 1 2\nshow u1\nquit\n' | "$BIN" 2>/dev/null | grep -c 'subs=u2')"

# rank-weighted ranking: authority arrives through the port; one-way dependency
wr='follow 1 2
follow 2 3
follow 1 4
rank
sub news 0
post news 0 many anonymous votes
post news 0 one authority
vote news 0 99
cast news 3 1 1
weigh news
show news
show u3
blend 0 news 0
show news
blend 5 news 0.5
cast news 3 0 1
show u3
follow 4 3
weigh news
show news
rank
weigh news
show news'
out=$(printf '%s\nquit\n' "$wr" | "$BIN" 2>&1)
r3=$(printf '%s\n' "$out" | grep -oE '^  rank [0-9.]+' | awk 'NR==1{print $2}')
expectW=$(awk -v r=$r3 'BEGIN{printf "%.2f", r*4}')
check "weigh: W on the endorsed node is the voter's rank x N, via the port" "1" "$(printf '%s\n' "$out" | grep -c "#1 \[+2, hot 2.00, W $expectW heat $expectW\] one authority")"
check "lambda 1: the popular node is first" "1" "$(printf '%s\n' "$out" | sed -n '/^r\/news/,/^r\/u3/p' | grep -c '^  #0 \[+100, hot 100.00\] many anonymous')"
check "lambda 0: the endorsed node is first, S shown" "1" "$(printf '%s\n' "$out" | awk '/lambda=0.00/{f=1} f&&/^  #1 /{print; exit}' | grep -c 'S '"$expectW"'\] one authority')"
check "only the site sets lambda" "1" "$(printf '%s\n' "$out" | grep -c 'refused: only the site sets lambda')"
check "casting changes no rank" "1" "$(printf '%s\n' "$out" | grep -oE '^  rank [0-9.]+' | awk 'NR==1{a=$2} NR==2{b=$2} END{print (a==b)?1:0}')"
before=$(printf '%s\n' "$out" | grep -oE 'W [0-9.]+' | sed -n '2p'); after=$(printf '%s\n' "$out" | grep -oE 'W [0-9.]+' | tail -1)
check "a weigh after a subscription change uses the old ranks until rank runs" "yes" "$([ -n "$before" ] && [ "$before" = "$(printf '%s\n' "$out" | grep -oE 'W [0-9.]+' | sed -n '1p')" ] && [ "$before" != "$after" ] && echo yes)"
check "the port's id and user are used by weighing (static)" "1" "$(grep -c 'REDDIT_WEIGHT) {' src/reddit.c)"

# equivalence: the binary reproduces the committed Phase 3 corner observations
# byte for byte (attribution/h3-*/). Provider-independent: any host that
# passes this has the same reference realization.
eq=0; for d in ../attribution/h3-E13 ../attribution/h3-E19; do
  [ -d "$d" ] || continue; read -r N M < "$d/NM"
  tracks=$(sed -n "$((N+1)),${M}p" "$d/source.txt" | awk '{print $2}' | grep -vE '^[0-9]+$' | sort -u)
  for h in H00 H01 H10 H11; do
    { for t in $tracks; do echo "show $t"; done; echo quit; } | "$BIN" "$d/$h.txt" 2>&1 | diff -q - "$d/$h.obs" >/dev/null && eq=$((eq+1))
  done; done
check "the binary reproduces the eight committed corner observations" "8" "$eq"

# the live ingress: identity bound at the socket, one serialized order,
# wall time as recorded ticks, downtime is not time
T=$(mktemp -d); S="$T/sock"; printf 'tk-site-8f3 0\ntk-alice-2c1 1\ntk-bob-77e 2\n' > "$T/principals"
"$BIN" serve "$S" "$T/principals" "$T/transcript" & srv=$!
i=0; while [ ! -S "$S" ] && [ $i -lt 50 ]; do sleep 0.1; i=$((i+1)); done
printf 'sub cats 9\npost cats 7 hello from alice\nshow cats\n' | "$BIN" connect "$S" tk-alice-2c1 > "$T/alice.out"
check "identity is bound at ingress: the transcript records the bound number" "2" "$(grep -cE '^(sub cats 1|post cats 1 hello from alice)$' "$T/transcript")"
check "a claimed number is discarded, not recorded" "0" "$(grep -cE 'cats (9|7) ' "$T/transcript")"
check "the client sees the executor's output" "1" "$(grep -c '^r/cats' "$T/alice.out")"
# a tab must not let a client smuggle a claimed actor past the binder
printf 'post cats\t0 7 tabbed\n' | "$BIN" connect "$S" tk-bob-77e > /dev/null
check "a tab cannot smuggle a claimed actor: u0 is not recorded" "0" "$(grep -cE '^post cats 0 ' "$T/transcript")"
check "the tabbed line binds the real actor (u2)" "1" "$(grep -cE '^post cats 2 7 tabbed$' "$T/transcript")"
# an over-long line is refused whole, never split into a second command
pad=$(printf 'x%.0s' $(seq 1 520)); printf 'post cats 1 %ssub sneaky 7\n' "$pad" > "$T/long.txt"
check "an over-long line replays refused, not split into 'sub sneaky'" "0" "$(printf 'show sneaky\nquit\n' | "$BIN" "$T/long.txt" 2>/dev/null | grep -c '^r/sneaky')"
printf 'ban 0 1\n' | "$BIN" connect "$S" tk-bob-77e > "$T/bob.out"
check "a refused attempt is admitted to the order and recorded" "1" "$(grep -c '^ban 2 1$' "$T/transcript")"
check "and refused by kappa under the bound identity" "1" "$(grep -c 'refused: not the site' "$T/bob.out")"
printf 'tick 5\nsave x\nquit\n' | "$BIN" connect "$S" tk-bob-77e > "$T/bob2.out"
check "tick, save, quit from a client are refused at ingress, not recorded" "0" "$(grep -cE '^(tick|save|quit)' "$T/transcript")"
printf 'show cats\n' | "$BIN" connect "$S" tk-nobody-000 > "$T/nobody.out"
check "an unknown principal is refused before any command" "1" "$(grep -c 'refused: unknown principal' "$T/nobody.out")"
check "tokens never enter the transcript" "0" "$(grep -c 'tk-' "$T/transcript")"
printf 'clock 0 1\n' | "$BIN" connect "$S" tk-site-8f3 > /dev/null
sleep 2.6
ticks1=$(grep -c '^tick 1$' "$T/transcript")
check "wall time generates ordinary tick lines at the site's interval" "yes" "$([ "$ticks1" -ge 2 ] && echo yes)"
kill $srv; wait $srv 2>/dev/null; sleep 2
"$BIN" serve "$S" "$T/principals" "$T/transcript" & srv=$!
i=0; while [ ! -S "$S" ] && [ $i -lt 50 ]; do sleep 0.1; i=$((i+1)); done
ticks2=$(grep -c '^tick 1$' "$T/transcript")
check "downtime is not time: a restart synthesizes no ticks" "$ticks1" "$ticks2"
printf 'show cats\n' | "$BIN" connect "$S" tk-alice-2c1 > "$T/alice2.out"
check "a restart replays the transcript: the state is back" "1" "$(grep -c 'hello from alice' "$T/alice2.out")"
sleep 1.6
check "and ticking resumes from the restart" "yes" "$([ "$(grep -c '^tick 1$' "$T/transcript")" -gt "$ticks2" ] && echo yes)"
kill $srv; wait $srv 2>/dev/null; rm -rf "$T"

exit $fail
