#define _POSIX_C_SOURCE 200809L /* dprintf, poll, unix sockets */
#include <errno.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <time.h>
#include <unistd.h>
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
 *   clock ADMIN SECONDS         F under κ on the site's θ: the live tick
 *                               interval
 * The clock is virtual and starts at 0, so runs replay exactly: the
 * command stream on stdin is the session's transcript. `reddit FILE`
 * replays FILE silently, then reads stdin — a restart. Session control
 * (save, help, quit) is not part of the application history and is
 * never recorded.
 *
 * Live service (README, "Frozen decisions for a live service"):
 *   reddit serve SOCKET PRINCIPALS TRANSCRIPT
 *       replays TRANSCRIPT if it exists, then accepts connections on the
 *       Unix socket. A connection's first line must be `auth TOKEN`; the
 *       token is looked up in PRINCIPALS (lines `TOKEN USER`) and binds
 *       the connection to that user number — identity is established
 *       here and nowhere else. Every later line from the connection has
 *       its actor field REPLACED by the bound number, is appended to
 *       TRANSCRIPT, and executes, in one serialized order with every
 *       other connection's lines and the generated ticks. Refusals by the
 *       rules are recorded like any attempt. `tick`, `save`, `quit`, and
 *       `auth` from a client are refused at the ingress and not recorded.
 *       Every `interval` seconds of wall time (site θ, `clock`) the
 *       server appends an ordinary `tick INTERVAL`. Downtime is not
 *       time: a restart replays and resumes ticking from then.
 *   reddit connect SOCKET TOKEN
 *       stdin lines to the server, its output to stdout, until EOF. */

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
    { "clock",   "clock ADMIN SECONDS",                 "the site sets the live tick interval (theta of r/all)" },
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

/* Personal-track names are reserved: `u` followed by digits belongs to
 * exactly one user, who is its only moderator. A subreddit may not take
 * such a name, and a profile is only ever looked up among profiles. */
static bool reserved_name(const char *name)
{
    if (name[0] != 'u' || name[1] == '\0') return false;
    for (const char *p = name + 1; *p; p++) if (*p < '0' || *p > '9') return false;
    return true;
}

static Track *profile_of(unsigned user)
{
    char name[REDDIT_NAME];
    snprintf(name, sizeof name, "u%u", user);
    Track *t = nullptr;
    for (size_t i = 0; i < nusers && !t; i++)
        if (strcmp(users[i].name, name) == 0) t = &users[i];
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
        printf(" alpha=%.2f tolerance=%g rounds=%zu interval=%zu", t->ranking.alpha,
               t->ranking.tolerance, t->ranking.rounds, t->ranking.interval);
    if (t->ranking.lambda != 1.0)
        printf(" lambda=%.2f", t->ranking.lambda);
    putchar('\n');
    if (t >= users && t < users + TRACKS)
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
/* Execute one command line. Returns false on quit. Every consumer of the
 * reference executor — stdin, a replayed file, the live ingress — goes
 * through here, so there is one order of execution and one semantics. */
static bool execute(char *line)
{
    char cmd[16] = "", a[REDDIT_NAME] = "", b[REDDIT_NAME] = "";
    int consumed = 0;
    if (sscanf(line, "%15s%n", cmd, &consumed) != 1)
        return true;
    const char *rest = line + consumed;

    /* session control is not application history */
    if (strcmp(cmd, "quit") == 0)
        return false;
    if (strcmp(cmd, "save") == 0) {
        char path[200];
        if (sscanf(rest, "%199s", path) != 1) { refuse("save FILE"); return true; }
        if (transcript) fclose(transcript);
        transcript = fopen(path, "a");
        if (!transcript) refuse("cannot open that file");
        return true;
    }
    if (strcmp(cmd, "help") != 0 && transcript && !replaying) {
        fputs(line, transcript);
        fputc('\n', transcript);
        fflush(transcript);
    }

    if (strcmp(cmd, "help") == 0) {
        if (replaying) return true;
        for (size_t i = 0; i < sizeof commands / sizeof commands[0]; i++)
            printf("%-8s %-58s %s\n", commands[i].name, commands[i].usage, commands[i].what);
    } else if (strcmp(cmd, "sub") == 0) {
        unsigned user;
        if (sscanf(rest, "%23s %u", a, &user) != 2) { refuse("sub NAME USER"); return true; }
        if (find(a)) { refuse("that name is taken"); return true; }
        if (reserved_name(a)) { refuse("uN names belong to users"); return true; }
        if (ntracks == TRACKS) { fprintf(stderr, "refused: capacity is %zu subreddits\n", TRACKS); return true; }
        reddit_track_init(&tracks[ntracks++], a, user);
    } else if (strcmp(cmd, "post") == 0) {
        unsigned user; int n;
        if (sscanf(rest, "%23s %u%n", a, &user, &n) != 2) { refuse("post SUB USER TITLE"); return true; }
        Track *t = find_sub(a);
        const char *title = rest + n + strspn(rest + n, " ");
        if (!t) { refuse("no such subreddit"); return true; }
        if (t->nposts == REDDIT_POSTS) { fprintf(stderr, "refused: capacity is %zu nodes in a track\n", REDDIT_POSTS); return true; }
        if (!t->sigma(t, user, -1, title, now)) refuse("the rules do not admit that post");
    } else if (strcmp(cmd, "comment") == 0) {
        unsigned user; int parent, n;
        if (sscanf(rest, "%23s %u %d%n", a, &user, &parent, &n) != 3) { refuse("comment SUB USER PARENT TEXT"); return true; }
        Track *t = find_sub(a);
        const char *text = rest + n + strspn(rest + n, " ");
        if (!t) { refuse("no such subreddit"); return true; }
        if (t->nposts == REDDIT_POSTS) { fprintf(stderr, "refused: capacity is %zu nodes in a track\n", REDDIT_POSTS); return true; }
        if (!t->sigma(t, user, parent, text, now)) refuse("the rules do not admit that comment");
    } else if (strcmp(cmd, "vote") == 0) {
        int id, d;
        if (sscanf(rest, "%23s %d %d", a, &id, &d) != 3) { refuse("vote SUB ID DELTA"); return true; }
        Track *t = find(a);
        if (!t || !reddit_vote(t, id, d)) refuse("no such node");
    } else if (strcmp(cmd, "tick") == 0) {
        long s;
        if (sscanf(rest, "%ld", &s) != 1 || s < 0) { refuse("tick SECONDS"); return true; }
        now += s;
        for (size_t i = 0; i < ntracks; i++)
            tracks[i].gsharp(&tracks[i], now);
    } else if (strcmp(cmd, "show") == 0) {
        if (sscanf(rest, "%23s", a) != 1) { refuse("show SUB"); return true; }
        Track *t = find(a);
        if (!t) { refuse("no such subreddit"); return true; }
        show(t);
    } else if (strcmp(cmd, "cross") == 0) {
        int id; unsigned user;
        if (sscanf(rest, "%23s %d %23s %u", a, &id, b, &user) != 4) { refuse("cross FROM ID TO USER"); return true; }
        Track *from = find(a), *to = find(b);
        if (!from || !to) { refuse("no such subreddit"); return true; }
        if (!reddit_port(from, id, to, user, now, REDDIT_FRESH)) refuse("the port did not admit it");
    } else if (strcmp(cmd, "lock") == 0) {
        unsigned user; int id;
        if (sscanf(rest, "%23s %u %d", a, &user, &id) != 3) { refuse("lock SUB USER ID"); return true; }
        Track *t = find(a);
        if (!t) { refuse("no such subreddit"); return true; }
        Rules r = t->rules;
        r.locked = id;
        if (!t->f(t, user, r, t->ranking)) refuse("not a moderator");
    } else if (strcmp(cmd, "rules") == 0) {
        unsigned user; Rules r; Ranking k; int allow, export;
        if (sscanf(rest, "%23s %u %zu %lf %lf %d %d", a, &user, &r.max_title,
                   &r.min_hot, &k.half_life, &allow, &export) != 7) {
            refuse("rules SUB USER MAXTITLE MINHOT HALFLIFE ALLOWCROSS EXPORT"); return true;
        }
        r.allow_crosspost = allow != 0;
        r.export_to_all = export != 0;
        Track *t = find(a);
        if (!t) { refuse("no such subreddit"); return true; }
        r.locked = t->rules.locked;
        r.banned = t->rules.banned;
        r.nsubs = t->rules.nsubs;
        memcpy(r.subs, t->rules.subs, sizeof r.subs);
        k.alpha = t->ranking.alpha; k.tolerance = t->ranking.tolerance; k.rounds = t->ranking.rounds;
        k.lambda = t->ranking.lambda; k.interval = t->ranking.interval;
        if (!t->f(t, user, r, k)) refuse("not a moderator, or rules out of range");
    } else if (strcmp(cmd, "ban") == 0) {
        unsigned admin, user;
        if (sscanf(rest, "%u %u", &admin, &user) != 2) { refuse("ban ADMIN USER"); return true; }
        size_t done = 0;
        for (size_t i = 0; i < ntracks; i++) {
            Rules r = tracks[i].rules;
            r.banned = (int)user;
            done += tracks[i].f(&tracks[i], admin, r, tracks[i].ranking);
        }
        if (done < ntracks) refuse("not the site");
    } else if (strcmp(cmd, "profile") == 0) {
        unsigned user; size_t k;
        if (sscanf(rest, "%u %zu", &user, &k) != 2) { refuse("profile USER K"); return true; }
        Track *u = profile_of(user);
        if (!u) { fprintf(stderr, "refused: capacity is %zu profiles\n", TRACKS); return true; }
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
        if (sscanf(rest, "%23s %u %d %d", a, &user, &id, &d) != 4) { refuse("cast SUB USER ID DELTA"); return true; }
        Track *t = find_sub(a);
        if (!t) { refuse("no such subreddit"); return true; }
        if (!reddit_cast(t, user, id, d)) refuse("no such node, already cast, or the ballots are full");
    } else if (strcmp(cmd, "weigh") == 0) {
        if (sscanf(rest, "%23s", a) != 1) { refuse("weigh SUB"); return true; }
        Track *t = find_sub(a);
        if (!t) { refuse("no such subreddit"); return true; }
        /* the receiver forgets its W, then each voter's track exports
         * its authority in vote units (rank x N) through the port,
         * once per ballot; a voter with no track contributes nothing */
        for (size_t i = 0; i < t->nposts; i++) t->posts[i].weight = 0.0;
        for (size_t i = 0; i < t->nposts; i++)
            for (size_t b = 0; b < t->posts[i].nballots; b++) {
                char name[REDDIT_NAME];
                snprintf(name, sizeof name, "u%u", t->posts[i].ballots[b].voter);
                Track *v = find(name);
                if (!v) return true;
                v->share = v->rank * (double)nusers;
                reddit_port(v, (int)t->posts[i].id, t, t->posts[i].ballots[b].voter, now, REDDIT_WEIGHT);
            }
        t->gsharp(t, now);
    } else if (strcmp(cmd, "clock") == 0) {
        unsigned admin; Ranking k = all.ranking;
        if (sscanf(rest, "%u %zu", &admin, &k.interval) != 2) { refuse("clock ADMIN SECONDS"); return true; }
        if (!all.f(&all, admin, all.rules, k)) refuse("not the site, or interval out of range");
    } else if (strcmp(cmd, "blend") == 0) {
        unsigned admin; double lam;
        if (sscanf(rest, "%u %23s %lf", &admin, a, &lam) != 3) { refuse("blend ADMIN SUB LAMBDA"); return true; }
        Track *t = find(a);
        if (!t) { refuse("no such track"); return true; }
        if (admin != REDDIT_SITE) { refuse("only the site sets lambda"); return true; }
        Ranking k = t->ranking; k.lambda = lam;
        if (!t->f(t, admin, t->rules, k)) refuse("lambda out of range");
    } else if (strcmp(cmd, "follow") == 0 || strcmp(cmd, "unfollow") == 0) {
        unsigned user, target;
        if (sscanf(rest, "%u %u", &user, &target) != 2) { refuse("follow USER TARGET"); return true; }
        Track *u = profile_of(user), *v = profile_of(target);
        if (!u || !v) { fprintf(stderr, "refused: capacity is %zu profiles\n", TRACKS); return true; }
        Rules r = u->rules;
        size_t k = 0;
        while (k < r.nsubs && r.subs[k] != target) k++;
        if (cmd[0] == 'f') {
            if (k < r.nsubs) { refuse("already following"); return true; }
            if (r.nsubs == REDDIT_SUBS) { fprintf(stderr, "refused: capacity is %zu subscriptions\n", REDDIT_SUBS); return true; }
            r.subs[r.nsubs++] = target;
        } else {
            if (k == r.nsubs) { refuse("not following"); return true; }
            for (; k + 1 < r.nsubs; k++) r.subs[k] = r.subs[k + 1];
            r.nsubs--;
        }
        if (!u->f(u, user, r, u->ranking)) refuse("not a moderator");
    } else if (strcmp(cmd, "pagerank") == 0) {
        unsigned admin; Ranking k = all.ranking;
        if (sscanf(rest, "%u %lf %lf %zu", &admin, &k.alpha, &k.tolerance, &k.rounds) != 4) { refuse("pagerank ADMIN ALPHA TOL ROUNDS"); return true; }
        if (!all.f(&all, admin, all.rules, k)) refuse("not the site, or parameters out of range");
    } else if (strcmp(cmd, "rank") == 0) {
        /* power iteration as message passing. The loop is the driver's,
         * like `all K`: one track at a time sets its share and ports it;
         * each track then settles from its own incoming alone. */
        size_t n = nusers;
        if (n == 0) { refuse("nobody to rank"); return true; }
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
        if (sscanf(rest, "%zu", &k) != 1) { refuse("all K"); return true; }
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
        if (sscanf(rest, "%23s", a) != 1) { refuse("sweep SUB"); return true; }
        Track *t = find(a);
        if (!t) { refuse("no such subreddit"); return true; }
        t->gsharp(t, now);
        size_t dropped = reddit_sweep(t);
        if (!replaying) printf("dropped %zu\n", dropped);
    } else if (strcmp(cmd, "gamma") == 0) {
        if (sscanf(rest, "%23s", a) != 1) { refuse("gamma SUB"); return true; }
        Track *t = find(a);
        if (!t) { refuse("no such subreddit"); return true; }
        if (!replaying) printf("gamma %zu\n", reddit_gamma(t, now));
    } else {
        refuse("unknown command");
    }
    return true;
}

/* Run one stream of commands. Returns false on quit. */
static bool run(FILE *in)
{
    char line[256];
    while (fgets(line, sizeof line, in)) {
        line[strcspn(line, "\n")] = '\0';
        if (!execute(line))
            return false;
    }
    return true;
}

/* --- the live ingress ------------------------------------------------
 * One process, one poll loop: the total order of the transcript is the
 * order complete lines are taken here. The reference executor above is
 * untouched; the ingress only decides who is speaking and rewrites the
 * actor field before handing the line on. */

constexpr size_t CLIENTS = 16;
constexpr size_t PRINCIPALS = 64;
static struct { char token[64]; unsigned user; } principals[PRINCIPALS];
static size_t nprincipals;
static struct { int fd; int user; char buf[512]; size_t len; } clients[CLIENTS];

/* Which argument carries the actor, per command (0: none). */
static int actor_field(const char *cmd)
{
    static const struct { const char *name; int field; } table[] = {
        { "sub", 2 }, { "post", 2 }, { "comment", 2 }, { "cast", 2 },
        { "cross", 4 }, { "lock", 2 }, { "rules", 2 }, { "ban", 1 },
        { "profile", 1 }, { "follow", 1 }, { "unfollow", 1 },
        { "pagerank", 1 }, { "blend", 1 }, { "clock", 1 },
    };
    for (size_t i = 0; i < sizeof table / sizeof table[0]; i++)
        if (strcmp(table[i].name, cmd) == 0) return table[i].field;
    return 0;
}

/* Rewrite the actor field of `line` to `user`, in place of whatever the
 * client claimed. Returns false if the line has no such field yet. */
static bool bind_actor(const char *line, unsigned user, char *out, size_t outlen)
{
    char cmd[16] = "";
    int consumed = 0;
    if (sscanf(line, "%15s%n", cmd, &consumed) != 1) return false;
    int field = actor_field(cmd);
    if (field == 0) { snprintf(out, outlen, "%s", line); return true; }
    /* walk the words; replace the field-th argument */
    const char *p = line + consumed;
    size_t n = 0;
    n += (size_t)snprintf(out + n, outlen - n, "%s", cmd);
    for (int i = 1; ; i++) {
        p += strspn(p, " ");
        if (*p == '\0') return i > field;
        const char *e = p + strcspn(p, " ");
        if (i == field) n += (size_t)snprintf(out + n, outlen - n, " %u", user);
        else n += (size_t)snprintf(out + n, outlen - n, " %.*s", (int)(e - p), p);
        p = e;
        if (n >= outlen - 1) return false;
    }
}

static void serve_line(size_t c, char *raw)
{
    char cmd[16] = "";
    sscanf(raw, "%15s", cmd);
    int fd = clients[c].fd;
    if (clients[c].user < 0) {                      /* identity, once */
        char token[64];
        if (strcmp(cmd, "auth") != 0 || sscanf(raw + 4, "%63s", token) != 1) {
            dprintf(fd, "refused: authenticate first\n"); close(fd); clients[c].fd = -1; return;
        }
        for (size_t i = 0; i < nprincipals; i++)
            if (strcmp(principals[i].token, token) == 0) {
                clients[c].user = (int)principals[i].user;
                dprintf(fd, "bound: u%u\n", principals[i].user); return;
            }
        dprintf(fd, "refused: unknown principal\n"); close(fd); clients[c].fd = -1; return;
    }
    if (strcmp(cmd, "tick") == 0 || strcmp(cmd, "save") == 0 ||
        strcmp(cmd, "quit") == 0 || strcmp(cmd, "auth") == 0) {
        dprintf(fd, "refused: %s is the server's, not a client's\n", cmd); return;
    }
    char line[512];
    if (!bind_actor(raw, (unsigned)clients[c].user, line, sizeof line)) {
        dprintf(fd, "refused: %s needs its actor\n", cmd); return;
    }
    /* the executor's output goes to this client for the duration */
    fflush(stdout); fflush(stderr);
    int so = dup(STDOUT_FILENO), se = dup(STDERR_FILENO);
    dup2(fd, STDOUT_FILENO); dup2(fd, STDERR_FILENO);
    execute(line);                                  /* records, then runs */
    fflush(stdout); fflush(stderr);
    dup2(so, STDOUT_FILENO); dup2(se, STDERR_FILENO); close(so); close(se);
}

static int serve(const char *sock, const char *principals_path, const char *transcript_path)
{
    FILE *pf = fopen(principals_path, "r");
    if (!pf) { perror(principals_path); return 1; }
    while (nprincipals < PRINCIPALS &&
           fscanf(pf, "%63s %u", principals[nprincipals].token, &principals[nprincipals].user) == 2)
        nprincipals++;
    fclose(pf);

    FILE *f = fopen(transcript_path, "r");          /* the history, if any */
    if (f) { replaying = true; run(f); replaying = false; fclose(f); }
    transcript = fopen(transcript_path, "a");
    if (!transcript) { perror(transcript_path); return 1; }

    int ls = socket(AF_UNIX, SOCK_STREAM, 0);
    struct sockaddr_un addr = { .sun_family = AF_UNIX };
    snprintf(addr.sun_path, sizeof addr.sun_path, "%s", sock);
    unlink(sock);
    if (bind(ls, (struct sockaddr *)&addr, sizeof addr) < 0 || listen(ls, 8) < 0) { perror(sock); return 1; }
    for (size_t i = 0; i < CLIENTS; i++) clients[i].fd = -1;

    time_t last_tick = time(nullptr);               /* downtime is not time */
    for (;;) {
        struct pollfd pfd[CLIENTS + 1];
        pfd[0] = (struct pollfd){ .fd = ls, .events = POLLIN };
        for (size_t i = 0; i < CLIENTS; i++)
            pfd[i + 1] = (struct pollfd){ .fd = clients[i].fd, .events = POLLIN };
        time_t due = last_tick + (time_t)all.ranking.interval;
        time_t now_wall = time(nullptr);
        int timeout = due > now_wall ? (int)(due - now_wall) * 1000 : 0;
        int r = poll(pfd, CLIENTS + 1, timeout);
        if (r < 0 && errno != EINTR) { perror("poll"); return 1; }
        now_wall = time(nullptr);
        while (now_wall - last_tick >= (time_t)all.ranking.interval) {
            char t[32];
            snprintf(t, sizeof t, "tick %zu", all.ranking.interval);
            execute(t);                             /* an ordinary line, recorded */
            last_tick += (time_t)all.ranking.interval;
        }
        if (pfd[0].revents & POLLIN) {
            int fd = accept(ls, nullptr, nullptr);
            size_t i = 0; while (i < CLIENTS && clients[i].fd >= 0) i++;
            if (i == CLIENTS) { dprintf(fd, "refused: capacity is %zu connections\n", CLIENTS); close(fd); }
            else clients[i] = (typeof(clients[0])){ .fd = fd, .user = -1, .len = 0 };
        }
        for (size_t i = 0; i < CLIENTS; i++) {
            if (clients[i].fd < 0 || !(pfd[i + 1].revents & (POLLIN | POLLHUP))) continue;
            ssize_t n = read(clients[i].fd, clients[i].buf + clients[i].len, sizeof clients[i].buf - clients[i].len - 1);
            if (n <= 0) { close(clients[i].fd); clients[i].fd = -1; continue; }
            clients[i].len += (size_t)n; clients[i].buf[clients[i].len] = '\0';
            char *nl;
            while (clients[i].fd >= 0 && (nl = strchr(clients[i].buf, '\n'))) {
                *nl = '\0';
                serve_line(i, clients[i].buf);
                size_t rest = clients[i].len - (size_t)(nl + 1 - clients[i].buf);
                memmove(clients[i].buf, nl + 1, rest + 1); clients[i].len = rest;
            }
            if (clients[i].fd >= 0 && clients[i].len >= sizeof clients[i].buf - 1) { close(clients[i].fd); clients[i].fd = -1; }
        }
    }
}

static int connect_to(const char *sock, const char *token)
{
    int fd = socket(AF_UNIX, SOCK_STREAM, 0);
    struct sockaddr_un addr = { .sun_family = AF_UNIX };
    snprintf(addr.sun_path, sizeof addr.sun_path, "%s", sock);
    if (connect(fd, (struct sockaddr *)&addr, sizeof addr) < 0) { perror(sock); return 1; }
    dprintf(fd, "auth %s\n", token);
    char line[512];
    /* send everything, then half-close, then drain the replies: the
     * server answers in order, so the drain reads every response */
    while (fgets(line, sizeof line, stdin)) write(fd, line, strlen(line));
    shutdown(fd, SHUT_WR);
    /* the server keeps the connection until we close; give it a moment
     * per line, then read what is there */
    struct pollfd p = { .fd = fd, .events = POLLIN };
    for (;;) {
        int r = poll(&p, 1, 300);
        if (r <= 0) break;
        ssize_t n = read(fd, line, sizeof line - 1);
        if (n <= 0) break;
        fwrite(line, 1, (size_t)n, stdout);
    }
    close(fd);
    return 0;
}

int main(int argc, char **argv)
{
    reddit_track_init(&all, "all", 0);
    all.rules.export_to_all = false; /* it does not feed itself */
    if (argc == 5 && strcmp(argv[1], "serve") == 0)
        return serve(argv[2], argv[3], argv[4]);
    if (argc == 4 && strcmp(argv[1], "connect") == 0)
        return connect_to(argv[2], argv[3]);
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
