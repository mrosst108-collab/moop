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
 *   sigma        driving: posts, comments and votes arrive (intra-track);
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
constexpr unsigned REDDIT_SITE = 0;  /* the site's own identity: admin */

/* A node of X. Posts and comments are the same kind of node: a comment
 * is a node with a parent. Ids are stable under jsharp's permutations,
 * so the tree is carried by ids, never by array positions. */
typedef struct {
    char title[REDDIT_TEXT];
    unsigned id;
    int parent;            /* id of the parent node; -1 for a post */
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
    int locked;            /* a rule about one post: no comments arrive
                              under it; -1 for none. Changed by f. */
    int banned;            /* a rule about one user: nothing of theirs is
                              admitted here; -1 for none. Changed by f. */
} Rules;

typedef struct {
    double half_life;      /* seconds for hot to halve */
} Ranking;

typedef struct Track Track;
struct Track {
    char name[REDDIT_NAME];

    /* X — state: a tree, stored flat, linked by ids */
    Post posts[REDDIT_POSTS];
    size_t nposts;
    unsigned next_id;

    /* θ — generator */
    Rules rules;
    Ranking ranking;
    unsigned mods[REDDIT_MODS];
    size_t nmods;

    /* the slots */
    void (*jsharp)(Track *t);
    void (*gsharp)(Track *t, time_t now);
    bool (*gtildesharp)(const Track *t, const Post *p);
    bool (*sigma)(Track *t, unsigned user, int parent, const char *text,
                  time_t now);           /* parent -1: a post; else a comment */
    bool (*f)(Track *t, unsigned user, Rules rules, Ranking ranking);
    bool (*kappa)(const Track *t, unsigned user);
};

/* A track is born with default occupants in every slot, `founder` as
 * its first moderator, and permissive rules. */
void reddit_track_init(Track *t, const char *name, unsigned founder);

/* The node with this id, or nullptr. */
const Post *reddit_find(const Track *t, int id);

/* Σ_ii, the other half: a vote on a node. Refused if there is none. */
bool reddit_vote(Track *t, int id, int delta);

/* Σ_ij — the port: translation, then gate, then adapter. The ONLY
 * function that takes two tracks. Two translations (realization data,
 * not a second port):
 *   REDDIT_FRESH  a crosspost by `user`: the title carries its origin,
 *                 the post starts over with one vote at `now`. Refuses
 *                 comments: a comment has no parent elsewhere.
 *   REDDIT_CARRY  aggregation: votes and birth time travel with the
 *                 node, so the receiver ranks it by its own decay; the
 *                 sender's export_to_all must be on, or T declines. A
 *                 comment is carried FLATTENED — it arrives as a
 *                 top-level node marked with its origin — because an
 *                 aggregate (r/all, a profile) shows what was said, not
 *                 where it hung.
 * The gate is the receiver's rules (allow_crosspost, then the rules
 * themselves); the adapter enters it as a post of `to`. Refused,
 * touching nothing, if any step refuses. */
typedef enum { REDDIT_FRESH, REDDIT_CARRY } Translation;

bool reddit_port(const Track *from, int id, Track *to, unsigned user,
                 time_t now, Translation how);

/* Sweep: nodes the rules no longer admit are dropped, and so, on the
 * next pass, are nodes whose parent is gone — the verdict is per node
 * and the cascade is only its repetition. Returns how many left. */
size_t reddit_sweep(Track *t);

/* Karma: a sum inside one track's X. On a user's profile track — fed
 * only through the port — it is the user's karma, computed after the
 * ports and never by a read across subreddits. */
int reddit_karma(const Track *t);

/* γ — measured, not applied: how many posts' fate under the rules
 * depends on whether decay ran first. Works on copies; changes nothing. */
size_t reddit_gamma(const Track *t, time_t now);

#endif
