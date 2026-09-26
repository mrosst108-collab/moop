#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <string.h>
#include "rme7.h"

/* A vote counter saturates rather than overflowing: signed overflow is
 * undefined, and a counter that cannot go higher simply stays. The wide
 * accumulator holds any int + int and any sum of int votes. */
static int sat_i(long long v)
{
    if (v > INT_MAX) return INT_MAX;
    if (v < INT_MIN) return INT_MIN;
    return (int)v;
}

/* --- default occupants ------------------------------------------------ */

/* jsharp: order by S = lambda*hot + (1-lambda)*heat, descending — with
 * lambda = 1 that is by hot. A permutation of X: nothing is created,
 * dropped, or rewritten. */
static double score(const Track *t, const Post *p)
{
    return t->ranking.lambda * p->hot + (1.0 - t->ranking.lambda) * p->heat;
}

static void sort_by_hot(Track *t)
{
    for (size_t i = 1; i < t->nposts; i++) {
        Post key = t->posts[i];
        size_t j = i;
        while (j > 0 && score(t, &t->posts[j - 1]) < score(t, &key)) {
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
        p->heat = p->weight * exp2(-age / t->ranking.half_life);
    }
}

/* gtildesharp: the rules. A verdict on one node; the node is const.
 * The same verdict for a post and a comment — a comment additionally
 * needs its parent present and not locked. */
static bool admits(const Track *t, const Post *p)
{
    if (strlen(p->title) > t->rules.max_title || p->hot < t->rules.min_hot)
        return false;
    if (reddit_is_banned(t, p->author))
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

/* kappa: who may modify the generator, given which authority holds the
 * field. The site may change anything; a moderator may change only what
 * the track holds. A site-held field (the ban set, the site ranking
 * parameters) is the site's alone. */
static bool is_mod(const Track *t, unsigned user, Held held)
{
    if (user == REDDIT_SITE)
        return true;
    if (held == REDDIT_HELD_SITE)
        return false;
    for (size_t i = 0; i < t->nmods; i++)
        if (t->mods[i] == user)
            return true;
    return false;
}

/* Which authority a proposed θ needs: site-held if it moves the ban set
 * or a site ranking parameter, else track-held. F knows the generator's
 * structure and reads off the site from what changed; kappa decides
 * admission from that. */
static Held held_of_change(const Track *t, const Rules *r, const Ranking *k)
{
    if (r->nbanned != t->rules.nbanned ||
        memcmp(r->banned, t->rules.banned, r->nbanned * sizeof r->banned[0]) != 0)
        return REDDIT_HELD_SITE;
    if (k->alpha != t->ranking.alpha || k->tolerance != t->ranking.tolerance ||
        k->rounds != t->ranking.rounds || k->lambda != t->ranking.lambda ||
        k->interval != t->ranking.interval)
        return REDDIT_HELD_SITE;
    return REDDIT_HELD_TRACK;
}

/* f: change θ. Passes through kappa first — gated by the field's holder,
 * not only by the actor — so a refused change is no change. Never
 * touches X. */
static bool adapt(Track *t, unsigned user, Rules rules, Ranking ranking)
{
    if (!t->kappa(t, user, held_of_change(t, &rules, &ranking)))
        return false;
    /* Range, written to reject NaN and infinity as well as out-of-band:
     * a NaN compares false to every bound, so `x >= lo && x <= hi` is the
     * form that refuses it. alpha < 1 strictly — G♯ is the only office
     * that converges, and at alpha = 1 (no teleport) the rank iteration
     * need not. */
    if (!(ranking.half_life > 0) || rules.max_title >= REDDIT_TEXT ||
        !isfinite(rules.min_hot) ||
        !(ranking.alpha >= 0 && ranking.alpha < 1) ||
        !(ranking.tolerance >= 0 && isfinite(ranking.tolerance)) ||
        ranking.rounds == 0 || rules.nsubs > REDDIT_SUBS ||
        !(ranking.lambda >= 0 && ranking.lambda <= 1) ||
        ranking.interval == 0 || rules.nbanned > REDDIT_BANS)
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
                        .locked = -1, .nbanned = 0 };
    t->ranking = (Ranking){ .half_life = 3600.0, .alpha = 0.85,
                            .tolerance = 1e-6, .rounds = 100, .lambda = 1.0,
                            .interval = 60 };
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

bool reddit_is_banned(const Track *t, unsigned user)
{
    for (size_t i = 0; i < t->rules.nbanned; i++)
        if (t->rules.banned[i] == user)
            return true;
    return false;
}

bool reddit_set_ban(Rules *r, unsigned user, bool add)
{
    size_t i = 0;
    while (i < r->nbanned && r->banned[i] != user)
        i++;
    bool present = i < r->nbanned;
    if (add) {
        if (present || r->nbanned == REDDIT_BANS)
            return false;              /* already barred, or the set is full */
        r->banned[r->nbanned++] = user;
        return true;
    }
    if (!present)
        return false;                  /* not barred: nothing to lift */
    for (; i + 1 < r->nbanned; i++)
        r->banned[i] = r->banned[i + 1];
    r->nbanned--;
    return true;
}

bool reddit_vote(Track *t, int id, int delta)
{
    Post *p = (Post *)reddit_find(t, id);
    if (p == nullptr)
        return false;
    p->votes = sat_i((long long)p->votes + delta);
    return true;
}

bool reddit_cast(Track *t, unsigned voter, int id, int delta)
{
    if (delta != 1 && delta != -1)
        return false;                 /* a ballot is +1 or -1: no other lever */
    if (reddit_is_banned(t, voter))
        return false;                 /* kappa_Sigma gates a ballot as a post */
    Post *p = (Post *)reddit_find(t, id);
    if (p == nullptr || p->nballots == REDDIT_BALLOTS)
        return false;
    for (size_t i = 0; i < p->nballots; i++)
        if (p->ballots[i].voter == voter)
            return false;
    p->ballots[p->nballots++] = (Ballot){ .voter = voter, .delta = delta };
    p->votes = sat_i((long long)p->votes + delta);
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
    if (how == REDDIT_RANK) {
        /* translation: the sender's share; gate: none; adapter: summed */
        to->incoming += from->share;
        return true;
    }
    if (how == REDDIT_WEIGHT) {
        /* translation: the voter's authority (share); gate: the receiver
         * holds this voter's ballot on this node, and the voter is not
         * barred here; adapter: signed sum */
        if (reddit_is_banned(to, user))
            return false;              /* a banned voter's standing does not weigh */
        Post *p = (Post *)reddit_find(to, id);
        if (p == nullptr)
            return false;
        for (size_t i = 0; i < p->nballots; i++)
            if (p->ballots[i].voter == user) {
                p->weight += from->share * p->ballots[i].delta;
                return true;
            }
        return false;
    }
    const Post *src = reddit_find(from, id);
    if (src == nullptr)
        return false;
    if (src->parent >= 0 && how == REDDIT_FRESH)
        return false; /* a crossposted comment would have no parent */

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
        /* it starts over: nobody has cast here and nothing was weighed
         * here, so the sender's ballots and W stay behind */
        memset(p.ballots, 0, sizeof p.ballots);
        p.nballots = 0;
        p.weight = 0.0;
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

int reddit_karma(const Track *t)
{
    long long karma = 0;
    for (size_t i = 0; i < t->nposts; i++)
        karma += t->posts[i].votes;   /* wide: any sum of int votes fits */
    return sat_i(karma);
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
