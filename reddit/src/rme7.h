#ifndef REDDIT_RME7_H
#define REDDIT_RME7_H

#include <stdbool.h>
#include <stddef.h>
#include <time.h>

/* A reddit, shaped by RME-7 at role-plus-constraint level.
 *
 * A subreddit is a TRACK: state X (posts) and generator θ (rules,
 * ranking, moderators) in the same struct but never confused. The
 * seven primitives are SLOTS — function pointers with defaults — so an
 * office is invariant and its occupant is swappable. Nothing here
 * claims an equation; each slot's job is a constraint the tests run:
 *
 *   jsharp       conservative circulation: sorts — a permutation only
 *   gsharp       dissipative, converges: decay — the ONLY writer of hot
 *   gtildesharp  confinement: rules — accept or refuse, never edit
 *   sigma        driving: posts and votes arrive (intra-track);
 *                reddit_port is the cross-track Σ_ij,
 *                adapter ∘ gate ∘ translation, the ONLY two-track act
 *   f            generator self-modification: changes θ
 *   kappa        integrity gate: who may call f
 *   gamma        derived, [gsharp, gtildesharp]: not a slot — measured
 *                from a trajectory by reddit_gamma
 *
 * Capture (G♯_ij ≠ 0) is the failure condition: no slot may read a
 * second track. The tests hold that throughout, not only at the end. */

constexpr size_t REDDIT_POSTS = 64;
constexpr size_t REDDIT_TEXT  = 96;
constexpr size_t REDDIT_NAME  = 24;
constexpr size_t REDDIT_MODS  = 4;

typedef struct {
    char title[REDDIT_TEXT];
    unsigned author;
    int votes;
    time_t born;
    double hot;            /* written by gsharp only */
} Post;

typedef struct {
    size_t max_title;      /* confinement: titles this long or shorter */
    double min_hot;        /* confinement: posts stay while hot >= this */
    bool allow_crosspost;  /* the port's gate on this track (receiver side) */
    bool export_to_all;    /* the port's translation from this track: a
                              sender may decline to translate (opt-out) */
} Rules;

typedef struct {
    double half_life;      /* seconds for hot to halve */
} Ranking;

typedef struct Track Track;
struct Track {
    char name[REDDIT_NAME];

    /* X — state */
    Post posts[REDDIT_POSTS];
    size_t nposts;

    /* θ — generator */
    Rules rules;
    Ranking ranking;
    unsigned mods[REDDIT_MODS];
    size_t nmods;

    /* the slots */
    void (*jsharp)(Track *t);
    void (*gsharp)(Track *t, time_t now);
    bool (*gtildesharp)(const Track *t, const Post *p);
    bool (*sigma)(Track *t, unsigned user, const char *title, time_t now);
    bool (*f)(Track *t, unsigned user, Rules rules, Ranking ranking);
    bool (*kappa)(const Track *t, unsigned user);
};

/* A track is born with default occupants in every slot, `founder` as
 * its first moderator, and permissive rules. */
void reddit_track_init(Track *t, const char *name, unsigned founder);

/* Σ_ii, the other half: a vote on post i. Refused if i is out of range. */
bool reddit_vote(Track *t, size_t i, int delta);

/* Σ_ij — the port: translation, then gate, then adapter. The ONLY
 * function that takes two tracks. Two translations (realization data,
 * not a second port):
 *   REDDIT_FRESH  a crosspost by `user`: the title carries its origin,
 *                 the post starts over with one vote at `now`
 *   REDDIT_CARRY  aggregation: votes and birth time travel with the
 *                 post, so the receiver ranks it by its own decay; the
 *                 sender's export_to_all must be on, or T declines
 * The gate is the receiver's rules (allow_crosspost, then the rules
 * themselves); the adapter enters it as a post of `to`. Refused,
 * touching nothing, if any step refuses. */
typedef enum { REDDIT_FRESH, REDDIT_CARRY } Translation;

bool reddit_port(const Track *from, size_t i, Track *to, unsigned user,
                 time_t now, Translation how);

/* Sweep: posts the rules no longer admit are dropped. Applies
 * gtildesharp to the current state; returns how many left. */
size_t reddit_sweep(Track *t);

/* γ — measured, not applied: how many posts' fate under the rules
 * depends on whether decay ran first. Works on copies; changes nothing. */
size_t reddit_gamma(const Track *t, time_t now);

#endif
