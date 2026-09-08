#include <stdio.h>
#include <string.h>
#include "rme7.h"

static int failures;

/* a Ranking with the delegation parameters at their defaults: f refuses
 * a Ranking with rounds == 0 or alpha outside [0, 1] */
#define RANKING(h) ((Ranking){ .half_life = (h), .alpha = 0.85, .tolerance = 1e-6, .rounds = 100, .lambda = 1.0 })

static void check(bool ok, const char *desc)
{
    printf("%s - %s\n", ok ? "ok  " : "FAIL", desc);
    if (!ok)
        failures = 1;
}

static bool same_posts(const Track *x, const Track *y)
{
    return x->nposts == y->nposts &&
           memcmp(x->posts, y->posts, x->nposts * sizeof(Post)) == 0;
}

/* Multiset equality of titles, ignoring order. */
static bool same_titles(const Track *x, const Track *y)
{
    if (x->nposts != y->nposts)
        return false;
    bool used[REDDIT_POSTS] = {};
    for (size_t i = 0; i < x->nposts; i++) {
        bool found = false;
        for (size_t j = 0; j < y->nposts && !found; j++)
            if (!used[j] && strcmp(x->posts[i].title, y->posts[j].title) == 0)
                used[j] = found = true;
        if (!found)
            return false;
    }
    return true;
}

int main(void)
{
    Track a, b;
    reddit_track_init(&a, "cats", 1);
    reddit_track_init(&b, "dogs", 2);
    check(a.sigma(&a, 1, -1, "first", 0) && a.sigma(&a, 3, -1, "second", 10) &&
          a.sigma(&a, 4, -1, "third", 20) && a.nposts == 3,
          "sigma: posts arrive");
    check(reddit_vote(&a, 0, 5) && reddit_vote(&a, 2, 2) && !reddit_vote(&a, 9, 1),
          "sigma: votes arrive by id; a missing node is refused");

    /* J-sharp: a permutation and nothing else */
    Track before = a;
    a.gsharp(&a, 30);
    a.jsharp(&a);
    check(same_titles(&a, &before) && a.posts[0].hot >= a.posts[1].hot &&
          a.posts[1].hot >= a.posts[2].hot,
          "jsharp: sorting permutes X and orders by hot");

    /* G-sharp: converges to zero, monotonically, and nowhere else is hot written */
    double h0 = a.posts[0].hot;
    a.gsharp(&a, 3630);
    double h1 = a.posts[0].hot;
    a.gsharp(&a, 100000);
    check(h1 < h0 && a.posts[0].hot < h1 && a.posts[0].hot < 0.001,
          "gsharp: hot decays toward zero and only toward zero");
    check(h1 * 2 > h0 * 0.99 && h1 * 2 < h0 * 1.01,
          "gsharp: one half-life halves");

    /* G-tilde-sharp: a verdict, never an edit; a refused post enters nothing */
    Rules strict = { .max_title = 4, .min_hot = 0.0, .allow_crosspost = true, .locked = -1, .banned = -1 };
    check(a.f(&a, 1, strict, a.ranking), "f: a moderator changes the rules");
    Track snap = a;
    check(!a.sigma(&a, 5, -1, "far too long", 200) && same_posts(&a, &snap),
          "gtildesharp: refuses without altering X");
    check(a.sigma(&a, 5, -1, "ok", 200), "gtildesharp: admits what fits");

    /* kappa: not a moderator, nothing changes — including the refusal */
    Rules loose = a.rules; loose.max_title = 50;
    snap = a;
    check(!a.f(&a, 99, loose, a.ranking) && a.rules.max_title == 4 &&
          same_posts(&a, &snap),
          "kappa: a non-moderator's f is refused and theta is unchanged");
    check(!a.f(&a, 1, loose, RANKING(0)) && a.rules.max_title == 4,
          "f: out-of-range theta is refused as a whole");

    /* the port: translate, gate, adapt; refused leaves the target unchanged */
    check(reddit_port(&b, 0, &a, 1, 300, REDDIT_FRESH) == false && a.nposts == 4,
          "port: nothing to crosspost from an empty track");
    check(b.sigma(&b, 2, -1, "woof", 300), "a post on the other track");
    snap = a;
    check(!reddit_port(&b, 0, &a, 1, 300, REDDIT_FRESH) && same_posts(&a, &snap),
          "port: the target's gate (max_title 4) refuses, target untouched");
    check(a.f(&a, 1, (Rules){ .max_title = 40, .min_hot = 0, .allow_crosspost = true, .locked = -1, .banned = -1 },
              a.ranking) &&
          reddit_port(&b, 0, &a, 1, 300, REDDIT_FRESH) &&
          strcmp(a.posts[a.nposts - 1].title, "x/dogs: woof") == 0 &&
          a.posts[a.nposts - 1].author == 1,
          "port: translated with its origin, admitted, adapted as the poster's");
    a.rules.allow_crosspost = false;
    snap = a;
    check(!reddit_port(&b, 0, &a, 1, 301, REDDIT_FRESH) && same_posts(&a, &snap),
          "port: allow_crosspost is kappa at the port");

    /* no capture: nothing on b changes a's ranking, only the port can */
    Track a0 = a;
    a0.gsharp(&a0, 5000); a0.jsharp(&a0);
    for (int i = 0; i < 20; i++) reddit_vote(&b, 0, 7);
    b.gsharp(&b, 5000); b.jsharp(&b);
    b.f(&b, 2, (Rules){ .max_title = 10, .min_hot = 1, .allow_crosspost = false, .locked = -1, .banned = -1 },
        RANKING(1));
    reddit_sweep(&b);
    a.gsharp(&a, 5000); a.jsharp(&a);
    check(same_posts(&a, &a0),
          "no capture: every act on b leaves a's ranking identical");

    /* gamma: measured, from a copy, changing nothing */
    Track c;
    reddit_track_init(&c, "news", 1);
    c.sigma(&c, 1, -1, "old", 0);
    c.sigma(&c, 1, -1, "new", 7000);
    c.f(&c, 1, (Rules){ .max_title = 40, .min_hot = 0.5, .allow_crosspost = true, .locked = -1, .banned = -1 },
        RANKING(3600));
    snap = c;
    size_t g = reddit_gamma(&c, 7200);
    check(g == 1 && same_posts(&c, &snap),
          "gamma: one post's fate depends on whether decay ran first; nothing changed");
    c.gsharp(&c, 7200);
    check(reddit_sweep(&c) == 1 && c.nposts == 1 &&
          strcmp(c.posts[0].title, "new") == 0,
          "sweep: the rules, applied after decay, drop exactly that post");

    /* r/all — the frozen prediction: an aggregate track fed only by ports */
    Track r1, r2, all;
    reddit_track_init(&r1, "one", 1);
    reddit_track_init(&r2, "two", 2);
    reddit_track_init(&all, "all", 0);
    r1.sigma(&r1, 1, -1, "small", 0);  reddit_vote(&r1, 0, 2);   /* 3 votes  */
    r1.sigma(&r1, 1, -1, "big", 0);    reddit_vote(&r1, 1, 20);  /* 21 votes */
    r2.sigma(&r2, 2, -1, "medium", 0); reddit_vote(&r2, 0, 9);   /* 10 votes */
    r2.sigma(&r2, 2, -1, "tiny", 0);                             /* 1 vote   */
    Track *subs[] = { &r1, &r2 };
    size_t fed = 0;
    for (size_t s = 0; s < 2; s++) {
        subs[s]->gsharp(subs[s], 100);
        subs[s]->jsharp(subs[s]);
        for (size_t i = 0; i < 1 && i < subs[s]->nposts; i++)
            fed += reddit_port(subs[s], (int)subs[s]->posts[i].id, &all, 0, 100, REDDIT_CARRY);
    }
    all.gsharp(&all, 100);
    all.jsharp(&all);
    check(fed == 2 && all.nposts == 2 &&
          strcmp(all.posts[0].title, "x/one: big") == 0 &&
          strcmp(all.posts[1].title, "x/two: medium") == 0 &&
          all.posts[0].votes == 21,
          "r/all: fed top-1 of each track through the port, ranked by itself");
    check(all.posts[0].hot > all.posts[1].hot && all.posts[0].hot <= 21.0,
          "r/all: hot is the receiver's decay of carried votes");

    /* no live cross-track read: changing a feeder changes nothing in all */
    Track all0 = all;
    reddit_vote(&r2, 0, 1000);
    r2.gsharp(&r2, 100); r2.jsharp(&r2);
    all.gsharp(&all, 100); all.jsharp(&all);
    check(same_posts(&all, &all0),
          "r/all: a feeder's change reaches it only through the next port");

    /* the sender's opt-out lives in the translation */
    r2.f(&r2, 2, (Rules){ .max_title = 40, .min_hot = 0, .allow_crosspost = true,
                          .export_to_all = false, .locked = -1, .banned = -1 }, r2.ranking);
    Track allx = all;
    check(!reddit_port(&r2, 0, &all, 0, 100, REDDIT_CARRY) && same_posts(&all, &allx),
          "r/all: an opted-out track declines to translate; all untouched");
    check(reddit_port(&r2, 0, &r1, 5, 100, REDDIT_FRESH),
          "opt-out is about aggregation: a user may still crosspost");

    /* the receiver's gate: r/all's own rules decide admission */
    all.f(&all, 0, (Rules){ .max_title = 40, .min_hot = 5.0, .allow_crosspost = true,
                            .export_to_all = false, .locked = -1, .banned = -1 }, all.ranking);
    all.nposts = 0;
    fed = 0;
    for (size_t s = 0; s < 2; s++) {
        subs[s]->rules.export_to_all = true;
        for (size_t i = 0; i < subs[s]->nposts; i++)
            fed += reddit_port(subs[s], (int)subs[s]->posts[i].id, &all, 0, 100, REDDIT_CARRY);
    }
    check(fed == 2 && all.nposts == 2,
          "r/all: its min_hot gate refuses the cold posts (tiny, small, the crosspost)");
    check(!reddit_port(&all, 0, &all, 0, 100, REDDIT_CARRY),
          "r/all: does not feed itself");

    /* comments — the frozen prediction: recursive state, six slots unchanged */
    Track c2;
    reddit_track_init(&c2, "tree", 1);
    check(c2.sigma(&c2, 1, -1, "post", 0) &&              /* id 0 */
          c2.sigma(&c2, 2, 0, "reply", 0) &&               /* id 1 */
          c2.sigma(&c2, 3, 0, "other reply", 0) &&         /* id 2 */
          c2.sigma(&c2, 4, 1, "reply to reply", 0) &&      /* id 3 */
          c2.nposts == 4,
          "sigma: comments arrive under a parent, as nodes of X");
    check(!c2.sigma(&c2, 5, 42, "orphan", 0) && c2.nposts == 4,
          "gtildesharp: a comment without a parent is refused");

    /* votes: post 4, reply 1, other reply 7, reply-to-reply 6 */
    reddit_vote(&c2, 0, 3);
    reddit_vote(&c2, 2, 6);
    reddit_vote(&c2, 3, 5);
    c2.gsharp(&c2, 0);
    c2.jsharp(&c2);

    /* one sort, every depth: the flat order restricted to any sibling
     * set is hot-descending; the tree walk is the driver's */
    size_t at[5] = {};
    for (size_t i = 0; i < c2.nposts; i++)
        at[c2.posts[i].id] = i;
    check(at[2] < at[1] && at[2] < at[0],
          "jsharp: one permutation orders siblings at every depth");
    check(reddit_find(&c2, 3)->parent == 1 && reddit_find(&c2, 1)->parent == 0,
          "the tree is carried by ids and survives the permutation");

    /* one decay: comments halve under the track's one half-life */
    c2.gsharp(&c2, 3600);
    check(reddit_find(&c2, 2)->hot > 3.49 && reddit_find(&c2, 2)->hot < 3.51 &&
          reddit_find(&c2, 0)->hot > 1.99 && reddit_find(&c2, 0)->hot < 2.01,
          "gsharp: comments decay under the same half-life as posts");

    /* one min_hot for posts and comments: the behavioral prediction */
    c2.f(&c2, 1, (Rules){ .max_title = 40, .min_hot = 0.75, .allow_crosspost = true,
                          .export_to_all = true, .locked = -1, .banned = -1 }, c2.ranking);
    check(c2.sigma(&c2, 6, 2, "fresh reply", 3600) && c2.nposts == 5,
          "a fresh comment (hot 1.0) clears min_hot like a fresh post");
    /* sweep: reply (0.5) fails the verdict; reply-to-reply (3.0) passes
     * it but its parent is gone, so it falls on the next pass */
    check(reddit_sweep(&c2) == 2 && c2.nposts == 3 &&
          reddit_find(&c2, 1) == nullptr && reddit_find(&c2, 3) == nullptr &&
          reddit_find(&c2, 0) && reddit_find(&c2, 2) && reddit_find(&c2, 4),
          "sweep: a verdict per node, the cascade only its repetition");

    /* lock: F under kappa, a rule about one post; not a thread generator */
    Rules locked = c2.rules; locked.locked = 2;
    check(!c2.f(&c2, 99, locked, c2.ranking) && c2.rules.locked == -1,
          "kappa: a non-moderator cannot lock");
    check(c2.f(&c2, 1, locked, c2.ranking) &&
          !c2.sigma(&c2, 7, 2, "too late", 3600) &&
          c2.sigma(&c2, 7, 0, "still open", 3600) &&
          reddit_find(&c2, 4) != nullptr,
          "a lock refuses new comments under one node; others and existing stay");

    /* comments do not cross tracks */
    Track d2;
    reddit_track_init(&d2, "elsewhere", 9);
    check(!reddit_port(&c2, 4, &d2, 9, 3600, REDDIT_FRESH) &&
          reddit_port(&c2, 0, &d2, 9, 3600, REDDIT_FRESH) && d2.nposts == 1,
          "port: refuses a comment, carries a post");

    /* gamma counts over the tree with no new mechanism: at 7200 the
     * fresh reply (1.0 at 3600) has halved to 0.5 < 0.75 */
    check(reddit_gamma(&c2, 7200) == 1,
          "gamma: measured over the tree; one node's fate flips with decay");

    /* users — the frozen prediction: a second track kind, fed only by ports */
    Track s1, s2, u;
    reddit_track_init(&s1, "one", 1);
    reddit_track_init(&s2, "two", 2);
    reddit_track_init(&u, "u7", 7);          /* the user moderates their profile */
    u.rules.export_to_all = false;
    s1.sigma(&s1, 7, -1, "mine in one", 0);  reddit_vote(&s1, 0, 9);   /* 10 */
    s1.sigma(&s1, 8, -1, "not mine", 0);
    s1.sigma(&s1, 7, 0, "my comment", 0);                              /* 1  */
    s2.sigma(&s2, 7, -1, "mine in two", 0);  reddit_vote(&s2, 0, 2);   /* 3  */
    Track *subs2[] = { &s1, &s2 };
    size_t fed_u = 0;
    for (size_t k = 0; k < 2; k++)
        for (size_t i = 0; i < subs2[k]->nposts; i++)
            if (subs2[k]->posts[i].author == 7)
                fed_u += reddit_port(subs2[k], (int)subs2[k]->posts[i].id, &u, 7, 0,
                                   REDDIT_CARRY);
    u.gsharp(&u, 0);
    u.jsharp(&u);
    check(fed_u == 3 && u.nposts == 3 && u.mods[0] == 7,
          "profile: a track fed only through the port, moderated by its user");
    check(reddit_karma(&u) == 14,
          "karma: summed inside X_u after the ports, never across subreddits");
    check(strcmp(u.posts[2].title, "x/one: my comment") == 0 && u.posts[2].parent == -1,
          "the aggregation translation carries a comment, flattened and marked");
    check(!reddit_port(&s1, 2, &s2, 9, 0, REDDIT_FRESH),
          "the crosspost translation still refuses a comment");

    /* theta_u has a consumer: the profile's own min_hot gates the port */
    Rules mine = u.rules; mine.min_hot = 5.0;
    check(!u.f(&u, 8, mine, u.ranking) && u.rules.min_hot == 0.0,
          "kappa: another user cannot change my profile's theta");
    check(u.f(&u, 7, mine, u.ranking) && u.rules.min_hot == 5.0,
          "f: the user changes their own theta");
    u.nposts = 0;
    fed_u = 0;
    for (size_t k = 0; k < 2; k++)
        for (size_t i = 0; i < subs2[k]->nposts; i++)
            if (subs2[k]->posts[i].author == 7)
                fed_u += reddit_port(subs2[k], (int)subs2[k]->posts[i].id, &u, 7, 0,
                                   REDDIT_CARRY);
    check(fed_u == 1 && u.nposts == 1 && reddit_karma(&u) == 10,
          "theta_u is consumed: the profile's min_hot admits one node of three");

    /* stale until rebuilt: a vote in a subreddit does not reach the profile */
    Track u0 = u;
    reddit_vote(&s1, 0, 100);
    s1.gsharp(&s1, 0);
    u.gsharp(&u, 0); u.jsharp(&u);
    check(same_posts(&u, &u0) && reddit_karma(&u) == 10,
          "profile: stale until the next build; no live cross-track read");

    /* a ban is f on each subreddit's theta by the site, not a read of theta_u */
    Rules b1 = s1.rules; b1.banned = 7;
    check(!s1.f(&s1, 8, b1, s1.ranking) && s1.rules.banned == -1,
          "kappa: a non-site, non-moderator cannot ban");
    check(s1.f(&s1, REDDIT_SITE, b1, s1.ranking) && s1.rules.banned == 7,
          "kappa admits the site everywhere: the ban lands in theta");
    check(!s1.sigma(&s1, 7, -1, "after the ban", 1) && s1.sigma(&s1, 8, -1, "others may", 1),
          "gtildesharp: nothing of the banned user's is admitted there");
    check(same_posts(&u, &u0),
          "the ban touches no profile content until subreddits re-export");
    check(reddit_sweep(&s1) == 2 && reddit_find(&s1, 0) == nullptr,
          "sweep applies the ban to what they already wrote there, cascading");
    /* delegation — the frozen prediction 4: rank crosses only through the port */
    Track ua, ub;
    reddit_track_init(&ua, "u1", 1);
    reddit_track_init(&ub, "u2", 2);
    Rules sub = ua.rules; sub.subs[0] = 2; sub.nsubs = 1;
    check(!ua.f(&ua, 2, sub, ua.ranking) && ua.rules.nsubs == 0,
          "kappa: only the user may change whom they delegate to");
    check(ua.f(&ua, 1, sub, ua.ranking) && ua.rules.nsubs == 1 && ua.rules.subs[0] == 2,
          "f: a subscription is the user's own theta");
    Rules self = ua.rules; self.subs[1] = 1; self.nsubs = 2;
    check(ua.f(&ua, 1, self, ua.ranking) && ua.rules.nsubs == 2,
          "self-subscription is an ordinary edge");
    ua.rank = 0.5; ua.share = 0.25; ub.incoming = 0.0;
    check(reddit_port(&ua, -1, &ub, 0, 0, REDDIT_RANK) && ub.incoming == 0.25 &&
          reddit_port(&ua, -1, &ub, 0, 0, REDDIT_RANK) && ub.incoming == 0.5,
          "port: the rank translation sums the sender's share into the receiver");
    Ranking bad = ua.ranking; bad.alpha = 1.5;
    check(!ua.f(&ua, 1, ua.rules, bad) && ua.ranking.alpha == 0.85,
          "f: alpha outside [0,1] is refused");

    /* rank-weighted ranking — the frozen prediction 5 */
    Track sr, v1, v2;
    reddit_track_init(&sr, "r", 1); reddit_track_init(&v1, "u1", 1); reddit_track_init(&v2, "u2", 2);
    sr.sigma(&sr, 1, -1, "many anonymous", 0);      /* node 0 */
    sr.sigma(&sr, 2, -1, "one authority", 0);       /* node 1 */
    reddit_vote(&sr, 0, 99);
    check(reddit_cast(&sr, 2, 1, 1) && sr.posts[1].votes == 2 && sr.posts[1].nballots == 1,
          "cast: counts in V and records a ballot");
    check(!reddit_cast(&sr, 2, 1, 1) && sr.posts[1].nballots == 1,
          "cast: one ballot per voter per node");
    v1.rank = 0.1; v2.rank = 0.9;                    /* two users: N = 2 */
    double rk1 = v1.rank, rk2 = v2.rank;
    v2.share = v2.rank * 2.0;
    check(!reddit_port(&v2, 0, &sr, 2, 0, REDDIT_WEIGHT),
          "port: weighing is refused where the voter cast no ballot");
    check(reddit_port(&v2, 1, &sr, 2, 0, REDDIT_WEIGHT) && sr.posts[1].weight == 1.8,
          "port: the voter's authority in vote units lands on the node they cast on");
    check(v1.rank == rk1 && v2.rank == rk2,
          "casting and weighing change no rank");
    sr.gsharp(&sr, 0); sr.jsharp(&sr);
    check(sr.posts[0].votes == 100 && sr.posts[0].hot == 100.0,
          "lambda 1: the popular vote orders, as before");
    Ranking lam = sr.ranking; lam.lambda = 0.0;
    check(sr.f(&sr, REDDIT_SITE, sr.rules, lam) && sr.ranking.lambda == 0.0,
          "the site sets lambda through f");
    sr.jsharp(&sr);
    check(sr.posts[0].id == 1 && sr.posts[0].heat == 1.8 && sr.posts[1].heat == 0.0,
          "lambda 0: one high-authority ballot outranks 99 anonymous votes");
    lam.lambda = 1.5;
    check(!sr.f(&sr, REDDIT_SITE, sr.rules, lam) && sr.ranking.lambda == 0.0,
          "f: lambda outside [0,1] is refused");

    return failures;
}
