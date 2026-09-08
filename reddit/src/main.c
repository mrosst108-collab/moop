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
        printf("  %*s#%u [%+d, hot %.2f] %s  (u%u)%s\n", depth * 4, "",
               p->id, p->votes, p->hot, p->title, p->author,
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
    putchar('\n');
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
