#include <math.h>
#include <stdio.h>
#include <string.h>
#include "rme7.h"

/* --- default occupants ------------------------------------------------ */

/* jsharp: order by hot, descending. A permutation of X: nothing is
 * created, dropped, or rewritten. */
static void sort_by_hot(Track *t)
{
    for (size_t i = 1; i < t->nposts; i++) {
        Post key = t->posts[i];
        size_t j = i;
        while (j > 0 && t->posts[j - 1].hot < key.hot) {
            t->posts[j] = t->posts[j - 1];
            j--;
        }
        t->posts[j] = key;
    }
}

/* gsharp: exponential decay toward zero. The one place `hot` is
 * written, and it only ever moves toward the fixed point. */
static void decay(Track *t, time_t now)
{
    for (size_t i = 0; i < t->nposts; i++) {
        Post *p = &t->posts[i];
        double age = difftime(now, p->born);
        if (age < 0)
            age = 0;
        p->hot = p->votes * exp2(-age / t->ranking.half_life);
    }
}

/* gtildesharp: the rules. A verdict on one node; the node is const.
 * The same verdict for a post and a comment — a comment additionally
 * needs its parent present and not locked. */
static bool admits(const Track *t, const Post *p)
{
    if (strlen(p->title) > t->rules.max_title || p->hot < t->rules.min_hot)
        return false;
    if (p->parent < 0)
        return true;
    return reddit_find(t, p->parent) != nullptr && p->parent != t->rules.locked;
}

/* sigma: a node arrives — a post (parent -1) or a comment under a
 * parent. It enters only if the rules admit it. */
static bool arrive(Track *t, unsigned user, int parent, const char *text,
                   time_t now)
{
    if (t->nposts == REDDIT_POSTS)
        return false;
    Post p = { .id = t->next_id, .parent = parent, .author = user,
               .votes = 1, .born = now, .hot = 1.0 };
    if (strlen(text) >= sizeof p.title)
        return false; /* refused, not truncated */
    strcpy(p.title, text);
    if (!t->gtildesharp(t, &p))
        return false;
    t->posts[t->nposts++] = p;
    t->next_id++;
    return true;
}

/* kappa: who may modify the generator — the moderators. */
static bool is_mod(const Track *t, unsigned user)
{
    for (size_t i = 0; i < t->nmods; i++)
        if (t->mods[i] == user)
            return true;
    return false;
}

/* f: change θ. Passes through kappa first; a refused change is no
 * change. Never touches X. */
static bool adapt(Track *t, unsigned user, Rules rules, Ranking ranking)
{
    if (!t->kappa(t, user))
        return false;
    if (ranking.half_life <= 0 || rules.max_title >= REDDIT_TEXT)
        return false;
    t->rules = rules;
    t->ranking = ranking;
    return true;
}

/* --- the track ----------------------------------------------------- */

void reddit_track_init(Track *t, const char *name, unsigned founder)
{
    memset(t, 0, sizeof *t);
    snprintf(t->name, sizeof t->name, "%s", name);
    t->rules = (Rules){ .max_title = REDDIT_TEXT - 1, .min_hot = 0.0,
                        .allow_crosspost = true, .export_to_all = true,
                        .locked = -1 };
    t->ranking = (Ranking){ .half_life = 3600.0 };
    t->mods[0] = founder;
    t->nmods = 1;
    t->jsharp = sort_by_hot;
    t->gsharp = decay;
    t->gtildesharp = admits;
    t->sigma = arrive;
    t->f = adapt;
    t->kappa = is_mod;
}

const Post *reddit_find(const Track *t, int id)
{
    if (id < 0)
        return nullptr;
    for (size_t i = 0; i < t->nposts; i++)
        if (t->posts[i].id == (unsigned)id)
            return &t->posts[i];
    return nullptr;
}

bool reddit_vote(Track *t, int id, int delta)
{
    Post *p = (Post *)reddit_find(t, id);
    if (p == nullptr)
        return false;
    p->votes += delta;
    return true;
}

size_t reddit_sweep(Track *t)
{
    size_t dropped = 0, pass;
    do {
        size_t kept = 0;
        pass = 0;
        for (size_t i = 0; i < t->nposts; i++) {
            if (t->gtildesharp(t, &t->posts[i]))
                t->posts[kept++] = t->posts[i];
            else
                pass++;
        }
        t->nposts = kept;
        dropped += pass;
    } while (pass > 0); /* orphans fail the verdict on the next pass */
    return dropped;
}

/* --- the port ------------------------------------------------------- */

bool reddit_port(const Track *from, int id, Track *to, unsigned user,
                 time_t now, Translation how)
{
    const Post *src = reddit_find(from, id);
    if (src == nullptr || src->parent >= 0)
        return false; /* comments do not cross tracks */

    /* translation: the sender's side. It may decline. */
    if (how == REDDIT_CARRY && !from->rules.export_to_all)
        return false;
    Post p = *src;
    p.id = to->next_id;
    p.parent = -1;
    char title[REDDIT_TEXT];
    int n = snprintf(title, sizeof title, "x/%s: %s", from->name, p.title);
    if (n < 0 || (size_t)n >= sizeof title)
        return false; /* would not fit: refused, not truncated */
    strcpy(p.title, title);
    p.author = user;
    if (how == REDDIT_FRESH) {
        p.votes = 1;
        p.born = now;
    }
    p.hot = 0.0; /* the receiver's gsharp writes hot, nobody else */

    /* gate: the receiver's side */
    if (!to->rules.allow_crosspost || to->nposts == REDDIT_POSTS)
        return false;
    Track judge = *to; /* hot under the receiver's own decay, on a copy */
    judge.posts[judge.nposts++] = p;
    judge.gsharp(&judge, now);
    if (!to->gtildesharp(to, &judge.posts[judge.nposts - 1]))
        return false;

    /* adapter: it is the receiver's post now */
    to->posts[to->nposts++] = judge.posts[judge.nposts - 1];
    to->next_id++;
    return true;
}

/* --- gamma ---------------------------------------------------------- */

size_t reddit_gamma(const Track *t, time_t now)
{
    Track after = *t;      /* decay, then judge */
    after.gsharp(&after, now);
    size_t differ = 0;
    for (size_t i = 0; i < t->nposts; i++)
        differ += t->gtildesharp(t, &t->posts[i]) !=
                  after.gtildesharp(&after, &after.posts[i]);
    return differ;
}
