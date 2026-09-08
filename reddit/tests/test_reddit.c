#include <stdio.h>
#include <string.h>
#include "rme7.h"

static int failures;

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
    check(a.sigma(&a, 1, "first", 0) && a.sigma(&a, 3, "second", 10) &&
          a.sigma(&a, 4, "third", 20) && a.nposts == 3,
          "sigma: posts arrive");
    check(reddit_vote(&a, 0, 5) && reddit_vote(&a, 2, 2) && !reddit_vote(&a, 9, 1),
          "sigma: votes arrive; out of range is refused");

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
    Rules strict = { .max_title = 4, .min_hot = 0.0, .allow_crosspost = true };
    check(a.f(&a, 1, strict, a.ranking), "f: a moderator changes the rules");
    Track snap = a;
    check(!a.sigma(&a, 5, "far too long", 200) && same_posts(&a, &snap),
          "gtildesharp: refuses without altering X");
    check(a.sigma(&a, 5, "ok", 200), "gtildesharp: admits what fits");

    /* kappa: not a moderator, nothing changes — including the refusal */
    Rules loose = a.rules; loose.max_title = 50;
    snap = a;
    check(!a.f(&a, 99, loose, a.ranking) && a.rules.max_title == 4 &&
          same_posts(&a, &snap),
          "kappa: a non-moderator's f is refused and theta is unchanged");
    check(!a.f(&a, 1, loose, (Ranking){ .half_life = 0 }) && a.rules.max_title == 4,
          "f: out-of-range theta is refused as a whole");

    /* the port: translate, gate, adapt; refused leaves the target unchanged */
    check(reddit_port(&b, 0, &a, 1, 300) == false && a.nposts == 4,
          "port: nothing to crosspost from an empty track");
    check(b.sigma(&b, 2, "woof", 300), "a post on the other track");
    snap = a;
    check(!reddit_port(&b, 0, &a, 1, 300) && same_posts(&a, &snap),
          "port: the target's gate (max_title 4) refuses, target untouched");
    check(a.f(&a, 1, (Rules){ .max_title = 40, .min_hot = 0, .allow_crosspost = true },
              a.ranking) &&
          reddit_port(&b, 0, &a, 1, 300) &&
          strcmp(a.posts[a.nposts - 1].title, "x/dogs: woof") == 0 &&
          a.posts[a.nposts - 1].author == 1,
          "port: translated with its origin, admitted, adapted as the poster's");
    a.rules.allow_crosspost = false;
    snap = a;
    check(!reddit_port(&b, 0, &a, 1, 301) && same_posts(&a, &snap),
          "port: allow_crosspost is kappa at the port");

    /* no capture: nothing on b changes a's ranking, only the port can */
    Track a0 = a;
    a0.gsharp(&a0, 5000); a0.jsharp(&a0);
    for (int i = 0; i < 20; i++) reddit_vote(&b, 0, 7);
    b.gsharp(&b, 5000); b.jsharp(&b);
    b.f(&b, 2, (Rules){ .max_title = 10, .min_hot = 1, .allow_crosspost = false },
        (Ranking){ .half_life = 1 });
    reddit_sweep(&b);
    a.gsharp(&a, 5000); a.jsharp(&a);
    check(same_posts(&a, &a0),
          "no capture: every act on b leaves a's ranking identical");

    /* gamma: measured, from a copy, changing nothing */
    Track c;
    reddit_track_init(&c, "news", 1);
    c.sigma(&c, 1, "old", 0);
    c.sigma(&c, 1, "new", 7000);
    c.f(&c, 1, (Rules){ .max_title = 40, .min_hot = 0.5, .allow_crosspost = true },
        (Ranking){ .half_life = 3600 });
    snap = c;
    size_t g = reddit_gamma(&c, 7200);
    check(g == 1 && same_posts(&c, &snap),
          "gamma: one post's fate depends on whether decay ran first; nothing changed");
    c.gsharp(&c, 7200);
    check(reddit_sweep(&c) == 1 && c.nposts == 1 &&
          strcmp(c.posts[0].title, "new") == 0,
          "sweep: the rules, applied after decay, drop exactly that post");

    return failures;
}
