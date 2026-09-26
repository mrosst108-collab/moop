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
 *   kappa        integrity gate: who may call f, given which authority
 *                holds the field being changed (track-held vs site-held)
 *   gamma        derived, [gsharp, gtildesharp]: not a slot — measured
 *                from a trajectory by reddit_gamma
 *
 * Capture (G♯_ij ≠ 0) is the failure condition: no slot may read a
 * second track. The tests hold that throughout, not only at the end. */

constexpr size_t REDDIT_POSTS = 64;
constexpr size_t REDDIT_TITLE = 95;  /* a human's text: the most max_title
                                        allows, in bytes */
constexpr size_t REDDIT_AI_CHARS = 300; /* an AI answer: at most this many
                                        characters (UTF-8 code points) */
constexpr size_t REDDIT_TEXT  = 4 * REDDIT_AI_CHARS + 1; /* room for either */
constexpr size_t REDDIT_NAME  = 24;
constexpr size_t REDDIT_MODS  = 4;
constexpr size_t REDDIT_SUBS  = 8;   /* subscriptions a user may hold */
constexpr size_t REDDIT_BALLOTS = 8; /* attributed votes a node may hold */
constexpr size_t REDDIT_BANS  = 16;  /* users a track's theta may bar */
constexpr unsigned REDDIT_SITE = 0;  /* the site's own identity: admin */
constexpr unsigned REDDIT_AI = ~0u;  /* the AI's identity: an author that
                                        holds nothing — no track, rank,
                                        ballot, moderation or principal
                                        (README, prediction 7) */

/* Which authority holds a generator field, so kappa can gate a change by
 * the field it touches and not only by the actor. A track-held field
 * (max_title, min_hot, half_life, allow_crosspost, export_to_all,
 * allow_ai, locked, subs) is a moderator's; a site-held field (the ban
 * set, and the site
 * ranking parameters alpha/tolerance/rounds/lambda/interval) is the
 * site's alone. Level before sector: this is not a new slot, it is the
 * argument kappa already needed to tell its two sites apart. */
typedef enum { REDDIT_HELD_TRACK, REDDIT_HELD_SITE } Held;

/* A node of X. Posts and comments are the same kind of node: a comment
 * is a node with a parent. Ids are stable under jsharp's permutations,
 * so the tree is carried by ids, never by array positions. */
typedef struct { unsigned voter; int delta; } Ballot;

/* Has the AI been asked to answer this node? A request makes it pending;
 * the answer resolves it, to answered (terminal) or back to none. */
typedef enum { REDDIT_AI_NONE, REDDIT_AI_PENDING, REDDIT_AI_ANSWERED } AiState;

typedef struct {
    char title[REDDIT_TEXT];
    unsigned id;
    int parent;            /* id of the parent node; -1 for a post */
    unsigned author;       /* REDDIT_AI: entered through reddit_answer only */
    AiState ai;            /* on a human's node: asked, answered, or neither */
    unsigned asked_by;     /* who asked the AI: on the node asked, and on
                              the answer */
    int votes;             /* V: the popular vote, anonymous and attributed */
    Ballot ballots[REDDIT_BALLOTS]; /* the attributed votes, one per voter */
    size_t nballots;
    double weight;         /* W: sum over ballots of voter authority x delta,
                              in vote units; produced only by the port
                              (weigh), stale until the next weigh */
    time_t born;
    double hot;            /* decayed V — written by gsharp only */
    double heat;           /* decayed W — written by gsharp only */
} Post;

typedef struct {
    size_t max_title;      /* confinement: titles this long or shorter */
    double min_hot;        /* confinement: posts stay while hot >= this */
    bool allow_crosspost;  /* the port's gate on this track (receiver side) */
    bool export_to_all;    /* the port's translation from this track: a
                              sender may decline to translate (opt-out) */
    bool allow_ai;         /* AI answers may be requested and admitted
                              here. Track-held; changed by f. */
    int locked;            /* a rule about one post: no comments arrive
                              under it; -1 for none. Changed by f. */
    unsigned banned[REDDIT_BANS]; /* users barred here: nothing of theirs
                              is admitted, and their standing ballots stop
                              weighing. A set, so a second ban does not
                              erase the first. Site-held; changed by f. */
    size_t nbanned;
    unsigned subs[REDDIT_SUBS]; /* on a user's track: whom this user
                              authorizes to carry their rank (delegation);
                              a subscription is the user's act on their own
                              theta, through f under kappa */
    size_t nsubs;
} Rules;

typedef struct {
    double half_life;      /* seconds for hot to halve */
    double alpha;          /* delegation: damping; on the site track */
    double tolerance;      /* delegation: stop when total change is below */
    size_t rounds;         /* delegation: round limit */
    double lambda;         /* ordering: S = lambda*hot + (1-lambda)*heat.
                              The site's policy, held per track, set only
                              by the site (README, prediction 5) */
    size_t interval;       /* live service: seconds of wall time per
                              generated `tick`; on the site track */
} Ranking;

typedef struct Track Track;
struct Track {
    char name[REDDIT_NAME];

    /* X — state: a tree, stored flat, linked by ids */
    Post posts[REDDIT_POSTS];
    size_t nposts;
    unsigned next_id;
    /* X on a user's track — rank, produced only by the port: what arrived
     * this round (incoming), what the driver set as this track's export
     * per edge (share), and the settled value (rank) */
    double rank, incoming, share;

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
    bool (*kappa)(const Track *t, unsigned user, Held held);
};

/* A track is born with default occupants in every slot, `founder` as
 * its first moderator, and permissive rules. */
void reddit_track_init(Track *t, const char *name, unsigned founder);

/* The node with this id, or nullptr. */
const Post *reddit_find(const Track *t, int id);

/* Is this user in the track's ban set? Read by gtildesharp (admission),
 * by the attributed vote (kappa_Sigma), and by the weight port. */
bool reddit_is_banned(const Track *t, unsigned user);

/* Add or drop a user in a Rules ban set, in place; returns whether the
 * set changed. The caller passes the result to f, so kappa still gates
 * the change (site-held). A full set refuses a new ban. */
bool reddit_set_ban(Rules *r, unsigned user, bool add);

/* Σ_ii, the other half: an anonymous vote on a node. Refused if there is none. */
bool reddit_vote(Track *t, int id, int delta);

/* Σ_ii: an attributed vote, delta +1 or -1. Counts in V like any vote,
 * and records the ballot. Refused if delta is anything else, the voter is
 * barred here, the node is missing, the voter already cast here, or the
 * node's ballots are full. Changes no rank anywhere. */
bool reddit_cast(Track *t, unsigned voter, int id, int delta);

/* Σ_ii: a request for the AI's answer to node `id`, attributed like a
 * ballot. The node becomes pending, with the requester recorded. Refused
 * if the requester is the AI or barred here, the node is missing or not
 * unrequested, the track is full, or the answer asked for would not be
 * admitted now — gtildesharp run on a probe answer, so a request has no
 * rules of its own. */
bool reddit_request(Track *t, unsigned requester, int id);

/* Σ_ii: the AI's answer to pending node `id` — the ONLY path by which an
 * AI-authored node enters X. It resolves the request either way: if the
 * text is admitted (gtildesharp; at most REDDIT_AI_CHARS characters) the
 * answer enters under the node and the node is answered, which is
 * terminal; if the text is empty or refused, the node is unrequested
 * again. Returns whether an answer entered. */
bool reddit_answer(Track *t, int id, const char *text, time_t now);

/* Σ_ij — the port: translation, then gate, then adapter. The ONLY
 * function that takes two tracks. Two translations (realization data,
 * not a second port):
 *   REDDIT_FRESH  a crosspost by `user`: the title carries its origin,
 *                 the post starts over with one vote at `now`, no
 *                 ballots and no W — nobody cast there and nothing was
 *                 weighed there. Refuses comments: a comment has no
 *                 parent elsewhere.
 *   REDDIT_CARRY  aggregation: votes and birth time travel with the
 *                 node, so the receiver ranks it by its own decay; the
 *                 sender's export_to_all must be on, or T declines. A
 *                 comment is carried FLATTENED — it arrives as a
 *                 top-level node marked with its origin — because an
 *                 aggregate (r/all, a profile) shows what was said, not
 *                 where it hung.
 *   REDDIT_RANK   delegation: the sender's `share` of rank crosses and
 *                 is summed into the receiver's `incoming`. `id` and
 *                 `user` are unused. No receiver-side gate: a delegate
 *                 cannot refuse (README, prediction 4).
 *   REDDIT_WEIGHT weighing: the sender is a voter's track and `share` is
 *                 their authority in vote units; it is added, signed by
 *                 the ballot that `user` cast on node `id` in `to`, to
 *                 that node's weight. Refused if `user` is barred in `to`
 *                 or there is no such ballot. Uses `id` and `user`
 *                 (README, predictions 5 and 6).
 * The gate is the receiver's rules (allow_crosspost, then the rules
 * themselves); the adapter enters it as a post of `to`, unrequested.
 * Nothing the AI wrote crosses: an AI node is refused under every
 * translation. Refused, touching nothing, if any step refuses. */
typedef enum { REDDIT_FRESH, REDDIT_CARRY, REDDIT_RANK, REDDIT_WEIGHT } Translation;

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
