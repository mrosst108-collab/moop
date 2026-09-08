#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rme7.h"

/* A reddit at the terminal. Commands, one per line:
 *   sub NAME USER               a user founds a subreddit (and moderates it)
 *   post SUB USER TITLE...      Σ: a post arrives
 *   vote SUB INDEX DELTA        Σ: a vote arrives
 *   tick SECONDS                time passes; every track decays (G♯)
 *   show SUB                    sort (J♯) and print
 *   cross FROM INDEX TO USER    Σ_ij: crosspost through the port
 *   rules SUB USER MAXTITLE MINHOT HALFLIFE ALLOWCROSS EXPORT
 *                               F under κ: a moderator changes θ
 *   all K                       r/all: rebuilt from every subreddit's top K
 *                               through the port, then ranked by itself
 *   sweep SUB                   drop what the rules no longer admit
 *   gamma SUB                   how path-dependent the rules are now
 *   quit
 * The clock is virtual and starts at 0, so runs replay exactly. */

constexpr size_t TRACKS = 16;
static Track tracks[TRACKS];
static size_t ntracks;
static time_t now;
static Track all; /* r/all: founded by the site (user 0), fed by ports */

static Track *find(const char *name)
{
    for (size_t i = 0; i < ntracks; i++)
        if (strcmp(tracks[i].name, name) == 0)
            return &tracks[i];
    return nullptr;
}

static void show(Track *t)
{
    t->gsharp(t, now);
    t->jsharp(t);
    printf("r/%s (%zu posts, %zu mods)\n", t->name, t->nposts, t->nmods);
    for (size_t i = 0; i < t->nposts; i++)
        printf("  %zu. [%+d, hot %.2f] %s  (u%u)\n", i, t->posts[i].votes,
               t->posts[i].hot, t->posts[i].title, t->posts[i].author);
}

static void refuse(const char *what)
{
    fprintf(stderr, "refused: %s\n", what);
}

int main(void)
{
    char line[256];
    reddit_track_init(&all, "all", 0);
    all.rules.export_to_all = false; /* it does not feed itself */
    while (fgets(line, sizeof line, stdin)) {
        line[strcspn(line, "\n")] = '\0';
        char cmd[16] = "", a[REDDIT_NAME] = "", b[REDDIT_NAME] = "";
        int consumed = 0;
        if (sscanf(line, "%15s%n", cmd, &consumed) != 1)
            continue;
        const char *rest = line + consumed;

        if (strcmp(cmd, "quit") == 0) {
            break;
        } else if (strcmp(cmd, "sub") == 0) {
            unsigned user;
            if (sscanf(rest, "%23s %u", a, &user) != 2) { refuse("sub NAME USER"); continue; }
            if (ntracks == TRACKS || find(a)) { refuse("no room, or that name is taken"); continue; }
            reddit_track_init(&tracks[ntracks++], a, user);
        } else if (strcmp(cmd, "post") == 0) {
            unsigned user; int n;
            if (sscanf(rest, "%23s %u%n", a, &user, &n) != 2) { refuse("post SUB USER TITLE"); continue; }
            Track *t = find(a);
            const char *title = rest + n + strspn(rest + n, " ");
            if (!t) { refuse("no such subreddit"); continue; }
            if (!t->sigma(t, user, title, now)) refuse("the rules do not admit that post");
        } else if (strcmp(cmd, "vote") == 0) {
            size_t i; int d;
            if (sscanf(rest, "%23s %zu %d", a, &i, &d) != 3) { refuse("vote SUB INDEX DELTA"); continue; }
            Track *t = find(a);
            if (!t || !reddit_vote(t, i, d)) refuse("no such post");
        } else if (strcmp(cmd, "tick") == 0) {
            long s;
            if (sscanf(rest, "%ld", &s) != 1 || s < 0) { refuse("tick SECONDS"); continue; }
            now += s;
            for (size_t i = 0; i < ntracks; i++)
                tracks[i].gsharp(&tracks[i], now);
        } else if (strcmp(cmd, "show") == 0) {
            if (sscanf(rest, "%23s", a) != 1) { refuse("show SUB"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            show(t);
        } else if (strcmp(cmd, "cross") == 0) {
            size_t i; unsigned user;
            if (sscanf(rest, "%23s %zu %23s %u", a, &i, b, &user) != 4) { refuse("cross FROM INDEX TO USER"); continue; }
            Track *from = find(a), *to = find(b);
            if (!from || !to) { refuse("no such subreddit"); continue; }
            if (!reddit_port(from, i, to, user, now, REDDIT_FRESH)) refuse("the port did not admit it");
        } else if (strcmp(cmd, "rules") == 0) {
            unsigned user; Rules r; Ranking k; int allow, export;
            if (sscanf(rest, "%23s %u %zu %lf %lf %d %d", a, &user, &r.max_title,
                       &r.min_hot, &k.half_life, &allow, &export) != 7) {
                refuse("rules SUB USER MAXTITLE MINHOT HALFLIFE ALLOWCROSS EXPORT"); continue;
            }
            r.allow_crosspost = allow != 0;
            r.export_to_all = export != 0;
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            if (!t->f(t, user, r, k)) refuse("not a moderator, or rules out of range");
        } else if (strcmp(cmd, "all") == 0) {
            size_t k;
            if (sscanf(rest, "%zu", &k) != 1) { refuse("all K"); continue; }
            /* r/all is a track of its own, rebuilt from ports; the loop
             * lives here, in the driver, never in the library */
            all.nposts = 0;
            for (size_t s = 0; s < ntracks; s++) {
                Track *t = &tracks[s];
                t->gsharp(t, now);
                t->jsharp(t);
                for (size_t i = 0; i < k && i < t->nposts; i++)
                    reddit_port(t, i, &all, 0, now, REDDIT_CARRY);
            }
            show(&all);
        } else if (strcmp(cmd, "sweep") == 0) {
            if (sscanf(rest, "%23s", a) != 1) { refuse("sweep SUB"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            t->gsharp(t, now);
            printf("dropped %zu\n", reddit_sweep(t));
        } else if (strcmp(cmd, "gamma") == 0) {
            if (sscanf(rest, "%23s", a) != 1) { refuse("gamma SUB"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            printf("gamma %zu\n", reddit_gamma(t, now));
        } else {
            refuse("unknown command");
        }
    }
    return 0;
}
