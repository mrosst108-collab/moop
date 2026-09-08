#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "rme7.h"

/* A reddit at the terminal. Commands, one per line:
 *   sub NAME USER               a user founds a subreddit (and moderates it)
 *   post SUB USER TITLE...      Σ: a post arrives
 *   comment SUB USER PARENT TEXT...
 *                               Σ: a comment arrives under node PARENT
 *   vote SUB ID DELTA           Σ: a vote arrives
 *   tick SECONDS                time passes; every track decays (G♯)
 *   show SUB                    sort (J♯) and print the tree
 *   cross FROM ID TO USER       Σ_ij: crosspost through the port
 *   lock SUB USER ID            F under κ: no more comments under ID
 *   rules TRACK USER MAXTITLE MINHOT HALFLIFE ALLOWCROSS EXPORT
 *                               F under κ: a moderator changes θ; a user
 *                               moderates their own profile track uN
 *   ban ADMIN USER              F under κ on every subreddit's θ, by the
 *                               site (user 0): nothing of USER's is
 *                               admitted anywhere
 *   profile USER K              the user's track uN, rebuilt from every
 *                               subreddit's nodes by USER (top K each)
 *                               through the port, then ranked by itself;
 *                               karma is summed inside it
 *   all K                       r/all: rebuilt from every subreddit's top K
 *                               through the port, then ranked by itself
 *   sweep SUB                   drop what the rules no longer admit
 *   gamma SUB                   how path-dependent the rules are now
 *   follow USER TARGET          F under κ on uUSER's θ: USER delegates
 *                               their rank to TARGET (transitively)
 *   unfollow USER TARGET        the reverse
 *   pagerank ADMIN ALPHA TOL ROUNDS
 *                               F under κ on the site's θ: the delegation
 *                               parameters
 *   cast SUB USER ID DELTA      Σ: an attributed vote — counts in V and
 *                               records a ballot; changes no rank
 *   weigh SUB                   rebuild every node's W from the voters'
 *                               current ranks, through the port
 *   blend ADMIN SUB LAMBDA      F under κ by the site: S = λ·hot + (1−λ)·heat
 *   rank                        run the delegation rounds: every user track
 *                               exports its share through the port, sums
 *                               what arrived, damps; stops at tolerance or
 *                               the round limit; ranks are stale until then
 *   help                        list the commands
 *   save FILE                   from now on, append every application
 *                               command to FILE before running it
 *   quit
 * The clock is virtual and starts at 0, so runs replay exactly: the
 * command stream on stdin is the session's transcript. `reddit FILE`
 * replays FILE silently, then reads stdin — a restart. Session control
 * (save, help, quit) is not part of the application history and is
 * never recorded. */

/* The command inventory, the source of `help`. The shell tests hold it
 * equal to what the dispatcher below actually accepts, so the language
 * cannot drift from its own description. */
static const struct { const char *name, *usage, *what; } commands[] = {
    { "sub",     "sub NAME USER",                       "a user founds a subreddit and moderates it" },
    { "post",    "post SUB USER TITLE...",              "a post arrives, if the rules admit it" },
    { "comment", "comment SUB USER PARENT TEXT...",     "a comment arrives under node PARENT" },
    { "vote",    "vote SUB ID DELTA",                   "a vote arrives on node ID" },
    { "tick",    "tick SECONDS",                        "time passes; hot decays everywhere" },
    { "show",    "show TRACK",                          "the rules in force, then the tree ranked by hot" },
    { "cross",   "cross FROM ID TO USER",               "crosspost node ID through the port" },
    { "lock",    "lock SUB USER ID",                    "a moderator closes node ID to new comments" },
    { "rules",   "rules TRACK USER MAXTITLE MINHOT HALFLIFE ALLOWCROSS EXPORT",
                                                        "a moderator changes the rules and ranking" },
    { "ban",     "ban ADMIN USER",                      "the site (user 0) bans USER from every subreddit" },
    { "profile", "profile USER K",                      "rebuild uUSER from every subreddit's top K by them" },
    { "all",     "all K",                               "rebuild r/all from every subreddit's top K" },
    { "sweep",   "sweep SUB",                           "drop what the rules no longer admit" },
    { "gamma",   "gamma SUB",                           "how many nodes' fate depends on decay running first" },
    { "cast",    "cast SUB USER ID DELTA",              "an attributed vote: counts in V, records a ballot, changes no rank" },
    { "weigh",   "weigh SUB",                           "rebuild W on every node from the voters' current ranks, via the port" },
    { "blend",   "blend ADMIN SUB LAMBDA",              "the site sets SUB's ordering: S = lambda*hot + (1-lambda)*heat" },
    { "follow",  "follow USER TARGET",                  "USER delegates their rank to TARGET (their own theta, via f)" },
    { "unfollow","unfollow USER TARGET",                "USER withdraws that delegation" },
    { "pagerank","pagerank ADMIN ALPHA TOL ROUNDS",     "the site sets the delegation parameters" },
    { "rank",    "rank",                                "run the delegation rounds through the port; ranks are stale until run" },
    { "help",    "help",                                "this list" },
    { "save",    "save FILE",                           "record every application command to FILE from now on" },
    { "quit",    "quit",                                "leave" },
};

static FILE *transcript;   /* where application commands are recorded */
static bool replaying;     /* a file is being replayed: effects, no output */

constexpr size_t TRACKS = 16;
static Track tracks[TRACKS];
static size_t ntracks;
static time_t now;
static Track all; /* r/all: founded by the site (user 0), fed by ports */
static Track users[TRACKS]; /* profiles: uN, founded by N, fed by ports */
static size_t nusers;

static Track *find(const char *name)
{
    for (size_t i = 0; i < ntracks; i++)
        if (strcmp(tracks[i].name, name) == 0)
            return &tracks[i];
    for (size_t i = 0; i < nusers; i++)
        if (strcmp(users[i].name, name) == 0)
            return &users[i];
    return nullptr;
}

/* A subreddit only: posts and comments arrive in subreddits, never in
 * a profile — a user originates nothing into their own track. */
static Track *find_sub(const char *name)
{
    for (size_t i = 0; i < ntracks; i++)
        if (strcmp(tracks[i].name, name) == 0)
            return &tracks[i];
    return nullptr;
}

static Track *profile_of(unsigned user)
{
    char name[REDDIT_NAME];
    snprintf(name, sizeof name, "u%u", user);
    Track *t = find(name);
    if (t == nullptr && nusers < TRACKS) {
        t = &users[nusers++];
        reddit_track_init(t, name, user); /* the user moderates it */
        t->rules.export_to_all = false;   /* a profile feeds nothing */
    }
    return t;
}

/* The tree walk lives here, in the driver: the array is already in hot
 * order at every depth (one sort), so children print in rank order. */
static void show_under(const Track *t, int parent, int depth)
{
    for (size_t i = 0; i < t->nposts; i++) {
        const Post *p = &t->posts[i];
        if (p->parent != parent)
            continue;
        printf("  %*s#%u [%+d, hot %.2f", depth * 4, "", p->id, p->votes, p->hot);
        if (p->nballots)
            printf(", W %.2f heat %.2f", p->weight, p->heat);
        if (t->ranking.lambda != 1.0)
            printf(", S %.2f", t->ranking.lambda * p->hot + (1.0 - t->ranking.lambda) * p->heat);
        printf("] %s  (u%u)%s\n", p->title, p->author,
               (int)p->id == t->rules.locked ? " [locked]" : "");
        show_under(t, (int)p->id, depth + 1);
    }
}

/* θ as it is, not an explanation of it: every field of the rules and
 * the ranking, read from the struct that governs the tree printed below. */
static void show_rules(const Track *t)
{
    printf("  rules: max_title=%zu min_hot=%.2f half_life=%.0f crosspost=%s "
           "export=%s locked=%d banned=%d mods=",
           t->rules.max_title, t->rules.min_hot, t->ranking.half_life,
           t->rules.allow_crosspost ? "yes" : "no",
           t->rules.export_to_all ? "yes" : "no",
           t->rules.locked, t->rules.banned);
    for (size_t i = 0; i < t->nmods; i++)
        printf("%su%u", i ? "," : "", t->mods[i]);
    if (t->rules.nsubs) {
        printf(" subs=");
        for (size_t i = 0; i < t->rules.nsubs; i++)
            printf("%su%u", i ? "," : "", t->rules.subs[i]);
    }
    if (t == &all)
        printf(" alpha=%.2f tolerance=%g rounds=%zu", t->ranking.alpha,
               t->ranking.tolerance, t->ranking.rounds);
    if (t->ranking.lambda != 1.0)
        printf(" lambda=%.2f", t->ranking.lambda);
    putchar('\n');
    if (t->name[0] == 'u')
        printf("  rank %.6f\n", t->rank);
}

static void show(Track *t)
{
    t->gsharp(t, now);
    t->jsharp(t);
    if (replaying)
        return; /* the effects above happened; the observation is not repeated */
    printf("r/%s (%zu nodes, %zu mods)\n", t->name, t->nposts, t->nmods);
    show_rules(t);
    show_under(t, -1, 0);
}

static void refuse(const char *what)
{
    if (!replaying)
        fprintf(stderr, "refused: %s\n", what);
}

/* Run one stream of commands. Returns false on quit. */
static bool run(FILE *in)
{
    char line[256];
    while (fgets(line, sizeof line, in)) {
        line[strcspn(line, "\n")] = '\0';
        char cmd[16] = "", a[REDDIT_NAME] = "", b[REDDIT_NAME] = "";
        int consumed = 0;
        if (sscanf(line, "%15s%n", cmd, &consumed) != 1)
            continue;
        const char *rest = line + consumed;

        /* session control is not application history */
        if (strcmp(cmd, "quit") == 0)
            return false;
        if (strcmp(cmd, "save") == 0) {
            char path[200];
            if (sscanf(rest, "%199s", path) != 1) { refuse("save FILE"); continue; }
            if (transcript) fclose(transcript);
            transcript = fopen(path, "a");
            if (!transcript) refuse("cannot open that file");
            continue;
        }
        if (strcmp(cmd, "help") != 0 && transcript && !replaying) {
            fputs(line, transcript);
            fputc('\n', transcript);
            fflush(transcript);
        }

        if (strcmp(cmd, "help") == 0) {
            if (replaying) continue;
            for (size_t i = 0; i < sizeof commands / sizeof commands[0]; i++)
                printf("%-8s %-58s %s\n", commands[i].name, commands[i].usage, commands[i].what);
        } else if (strcmp(cmd, "sub") == 0) {
            unsigned user;
            if (sscanf(rest, "%23s %u", a, &user) != 2) { refuse("sub NAME USER"); continue; }
            if (find(a)) { refuse("that name is taken"); continue; }
            if (ntracks == TRACKS) { fprintf(stderr, "refused: capacity is %zu subreddits\n", TRACKS); continue; }
            reddit_track_init(&tracks[ntracks++], a, user);
        } else if (strcmp(cmd, "post") == 0) {
            unsigned user; int n;
            if (sscanf(rest, "%23s %u%n", a, &user, &n) != 2) { refuse("post SUB USER TITLE"); continue; }
            Track *t = find_sub(a);
            const char *title = rest + n + strspn(rest + n, " ");
            if (!t) { refuse("no such subreddit"); continue; }
            if (t->nposts == REDDIT_POSTS) { fprintf(stderr, "refused: capacity is %zu nodes in a track\n", REDDIT_POSTS); continue; }
            if (!t->sigma(t, user, -1, title, now)) refuse("the rules do not admit that post");
        } else if (strcmp(cmd, "comment") == 0) {
            unsigned user; int parent, n;
            if (sscanf(rest, "%23s %u %d%n", a, &user, &parent, &n) != 3) { refuse("comment SUB USER PARENT TEXT"); continue; }
            Track *t = find_sub(a);
            const char *text = rest + n + strspn(rest + n, " ");
            if (!t) { refuse("no such subreddit"); continue; }
            if (t->nposts == REDDIT_POSTS) { fprintf(stderr, "refused: capacity is %zu nodes in a track\n", REDDIT_POSTS); continue; }
            if (!t->sigma(t, user, parent, text, now)) refuse("the rules do not admit that comment");
        } else if (strcmp(cmd, "vote") == 0) {
            int id, d;
            if (sscanf(rest, "%23s %d %d", a, &id, &d) != 3) { refuse("vote SUB ID DELTA"); continue; }
            Track *t = find(a);
            if (!t || !reddit_vote(t, id, d)) refuse("no such node");
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
            int id; unsigned user;
            if (sscanf(rest, "%23s %d %23s %u", a, &id, b, &user) != 4) { refuse("cross FROM ID TO USER"); continue; }
            Track *from = find(a), *to = find(b);
            if (!from || !to) { refuse("no such subreddit"); continue; }
            if (!reddit_port(from, id, to, user, now, REDDIT_FRESH)) refuse("the port did not admit it");
        } else if (strcmp(cmd, "lock") == 0) {
            unsigned user; int id;
            if (sscanf(rest, "%23s %u %d", a, &user, &id) != 3) { refuse("lock SUB USER ID"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            Rules r = t->rules;
            r.locked = id;
            if (!t->f(t, user, r, t->ranking)) refuse("not a moderator");
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
            r.locked = t->rules.locked;
            r.banned = t->rules.banned;
            r.nsubs = t->rules.nsubs;
            memcpy(r.subs, t->rules.subs, sizeof r.subs);
            k.alpha = t->ranking.alpha; k.tolerance = t->ranking.tolerance; k.rounds = t->ranking.rounds;
            k.lambda = t->ranking.lambda;
            if (!t->f(t, user, r, k)) refuse("not a moderator, or rules out of range");
        } else if (strcmp(cmd, "ban") == 0) {
            unsigned admin, user;
            if (sscanf(rest, "%u %u", &admin, &user) != 2) { refuse("ban ADMIN USER"); continue; }
            size_t done = 0;
            for (size_t i = 0; i < ntracks; i++) {
                Rules r = tracks[i].rules;
                r.banned = (int)user;
                done += tracks[i].f(&tracks[i], admin, r, tracks[i].ranking);
            }
            if (done < ntracks) refuse("not the site");
        } else if (strcmp(cmd, "profile") == 0) {
            unsigned user; size_t k;
            if (sscanf(rest, "%u %zu", &user, &k) != 2) { refuse("profile USER K"); continue; }
            Track *u = profile_of(user);
            if (!u) { fprintf(stderr, "refused: capacity is %zu profiles\n", TRACKS); continue; }
            /* rebuilt from ports, like r/all; the loop is the driver's */
            u->nposts = 0;
            for (size_t s = 0; s < ntracks; s++) {
                Track *t = &tracks[s];
                t->gsharp(t, now);
                t->jsharp(t);
                size_t sent = 0;
                for (size_t i = 0; i < t->nposts && sent < k; i++)
                    if (t->posts[i].author == user)
                        sent += reddit_port(t, (int)t->posts[i].id, u, user,
                                            now, REDDIT_CARRY);
            }
            show(u);
            if (!replaying) printf("  karma %d\n", reddit_karma(u));
        } else if (strcmp(cmd, "cast") == 0) {
            unsigned user; int id, d;
            if (sscanf(rest, "%23s %u %d %d", a, &user, &id, &d) != 4) { refuse("cast SUB USER ID DELTA"); continue; }
            Track *t = find_sub(a);
            if (!t) { refuse("no such subreddit"); continue; }
            if (!reddit_cast(t, user, id, d)) refuse("no such node, already cast, or the ballots are full");
        } else if (strcmp(cmd, "weigh") == 0) {
            if (sscanf(rest, "%23s", a) != 1) { refuse("weigh SUB"); continue; }
            Track *t = find_sub(a);
            if (!t) { refuse("no such subreddit"); continue; }
            /* the receiver forgets its W, then each voter's track exports
             * its authority in vote units (rank x N) through the port,
             * once per ballot; a voter with no track contributes nothing */
            for (size_t i = 0; i < t->nposts; i++) t->posts[i].weight = 0.0;
            for (size_t i = 0; i < t->nposts; i++)
                for (size_t b = 0; b < t->posts[i].nballots; b++) {
                    char name[REDDIT_NAME];
                    snprintf(name, sizeof name, "u%u", t->posts[i].ballots[b].voter);
                    Track *v = find(name);
                    if (!v) continue;
                    v->share = v->rank * (double)nusers;
                    reddit_port(v, (int)t->posts[i].id, t, t->posts[i].ballots[b].voter, now, REDDIT_WEIGHT);
                }
            t->gsharp(t, now);
        } else if (strcmp(cmd, "blend") == 0) {
            unsigned admin; double lam;
            if (sscanf(rest, "%u %23s %lf", &admin, a, &lam) != 3) { refuse("blend ADMIN SUB LAMBDA"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such track"); continue; }
            if (admin != REDDIT_SITE) { refuse("only the site sets lambda"); continue; }
            Ranking k = t->ranking; k.lambda = lam;
            if (!t->f(t, admin, t->rules, k)) refuse("lambda out of range");
        } else if (strcmp(cmd, "follow") == 0 || strcmp(cmd, "unfollow") == 0) {
            unsigned user, target;
            if (sscanf(rest, "%u %u", &user, &target) != 2) { refuse("follow USER TARGET"); continue; }
            Track *u = profile_of(user), *v = profile_of(target);
            if (!u || !v) { fprintf(stderr, "refused: capacity is %zu profiles\n", TRACKS); continue; }
            Rules r = u->rules;
            size_t k = 0;
            while (k < r.nsubs && r.subs[k] != target) k++;
            if (cmd[0] == 'f') {
                if (k < r.nsubs) { refuse("already following"); continue; }
                if (r.nsubs == REDDIT_SUBS) { fprintf(stderr, "refused: capacity is %zu subscriptions\n", REDDIT_SUBS); continue; }
                r.subs[r.nsubs++] = target;
            } else {
                if (k == r.nsubs) { refuse("not following"); continue; }
                for (; k + 1 < r.nsubs; k++) r.subs[k] = r.subs[k + 1];
                r.nsubs--;
            }
            if (!u->f(u, user, r, u->ranking)) refuse("not a moderator");
        } else if (strcmp(cmd, "pagerank") == 0) {
            unsigned admin; Ranking k = all.ranking;
            if (sscanf(rest, "%u %lf %lf %zu", &admin, &k.alpha, &k.tolerance, &k.rounds) != 4) { refuse("pagerank ADMIN ALPHA TOL ROUNDS"); continue; }
            if (!all.f(&all, admin, all.rules, k)) refuse("not the site, or parameters out of range");
        } else if (strcmp(cmd, "rank") == 0) {
            /* power iteration as message passing. The loop is the driver's,
             * like `all K`: one track at a time sets its share and ports it;
             * each track then settles from its own incoming alone. */
            size_t n = nusers;
            if (n == 0) { refuse("nobody to rank"); continue; }
            for (size_t i = 0; i < n; i++) users[i].rank = 1.0 / (double)n;
            size_t round = 0; double change = 1.0;
            while (round < all.ranking.rounds && change > all.ranking.tolerance) {
                round++;
                for (size_t i = 0; i < n; i++) users[i].incoming = 0.0;
                for (size_t i = 0; i < n; i++) {
                    Track *u = &users[i];
                    if (u->rules.nsubs == 0) {        /* dangling: spread uniformly */
                        u->share = u->rank / (double)n;
                        for (size_t j = 0; j < n; j++) reddit_port(u, -1, &users[j], 0, now, REDDIT_RANK);
                    } else {
                        u->share = u->rank / (double)u->rules.nsubs;
                        for (size_t k = 0; k < u->rules.nsubs; k++) {
                            Track *v = profile_of(u->rules.subs[k]);
                            if (v) reddit_port(u, -1, v, 0, now, REDDIT_RANK);
                        }
                    }
                }
                change = 0.0;
                for (size_t i = 0; i < n; i++) {   /* each track settles from its own incoming */
                    double next = all.ranking.alpha * users[i].incoming + (1.0 - all.ranking.alpha) / (double)n;
                    change += next > users[i].rank ? next - users[i].rank : users[i].rank - next;
                    users[i].rank = next;
                }
            }
            if (!replaying) printf("rank: %zu rounds, change %g, %s\n", round, change,
                                   change <= all.ranking.tolerance ? "converged" : "round limit");
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
                size_t sent = 0;
                for (size_t i = 0; i < t->nposts && sent < k; i++)
                    if (t->posts[i].parent < 0)
                        sent += reddit_port(t, (int)t->posts[i].id, &all, 0,
                                            now, REDDIT_CARRY);
            }
            show(&all);
        } else if (strcmp(cmd, "sweep") == 0) {
            if (sscanf(rest, "%23s", a) != 1) { refuse("sweep SUB"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            t->gsharp(t, now);
            size_t dropped = reddit_sweep(t);
            if (!replaying) printf("dropped %zu\n", dropped);
        } else if (strcmp(cmd, "gamma") == 0) {
            if (sscanf(rest, "%23s", a) != 1) { refuse("gamma SUB"); continue; }
            Track *t = find(a);
            if (!t) { refuse("no such subreddit"); continue; }
            if (!replaying) printf("gamma %zu\n", reddit_gamma(t, now));
        } else {
            refuse("unknown command");
        }
    }
    return true;
}

int main(int argc, char **argv)
{
    reddit_track_init(&all, "all", 0);
    all.rules.export_to_all = false; /* it does not feed itself */
    if (argc == 2) {
        FILE *f = fopen(argv[1], "r");
        if (!f) { perror(argv[1]); return 1; }
        replaying = true;
        run(f);            /* the history, re-executed: effects only */
        replaying = false;
        fclose(f);
    }
    run(stdin);
    if (transcript) fclose(transcript);
    return 0;
}
