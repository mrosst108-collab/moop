#ifndef RME7_PROTO_H
#define RME7_PROTO_H

#include "profile.h"
#include "slot.h"

/* The ladder.
 *
 *   actor  -->  system root proto  -->  user root proto  -->  protos...
 *
 * Two relations, kept strictly apart, exactly as they are kept apart in the
 * object model this shape is borrowed from:
 *
 *   GENERATION (who made you) is the only downward path, and the only way
 *   anything crosses the layer boundary. It is recorded immutably at birth
 *   and can never be rewired.
 *
 *   DELEGATION (whom you defer to for a slot you did not establish) walks
 *   parent links, never crosses the layer boundary, and never reaches the
 *   actor -- the actor is not a proto and has no delegable surface.
 *
 * The correspondence that makes this worth doing: the ladder carries TYPE
 * and each object carries its own VALUE. Three things live at three levels,
 * and only the first is inherited:
 *
 *   slot DEFINITIONS  delegate  -- what a slot is, and what office it holds
 *   the CONTRACT                -- local: what this object offers to compose on
 *   the activation PROFILE      -- local: what THIS object exhibits
 *   the PAYLOAD                 -- local: purpose, energy, state
 *
 * Contract and profile are separate for the reason a whole relay was spent
 * establishing one level up: NOT CURRENTLY USED IS NOT UNAVAILABLE. An object
 * may contract to compose on a slot it does not presently exhibit, and
 * collapsing the two would let a momentarily thin object be read as
 * structurally incapable -- the object-level form of the same error.
 *
 * That split is load-bearing twice over. Because exhibition does not
 * delegate, a proto generated from a root that defines all seven slots does
 * not thereby exhibit all seven, and the restriction staircase survives.
 * Because the payload does not delegate, the forbidden collapse
 * Phi_i = Phi_j cannot arise from the hierarchy at all: there is no
 * function in this header that walks a parent chain looking for a purpose.
 */

typedef struct Rme7Actor Rme7Actor;
typedef struct Rme7Proto Rme7Proto;

typedef enum : uint8_t {
    RME7_LAYER_SYSTEM,
    RME7_LAYER_USER
} Rme7Layer;

typedef enum : uint8_t {
    RME7_ORIGIN_ACTOR,
    RME7_ORIGIN_PROTO
} Rme7OriginKind;

typedef struct {
    Rme7OriginKind   kind;
    const Rme7Actor *actor;  /* set iff kind == RME7_ORIGIN_ACTOR */
    const Rme7Proto *proto;  /* set iff kind == RME7_ORIGIN_PROTO */
} Rme7Origin;

/* Per-object payload. NEVER delegated -- there is deliberately no resolve
 * function for it. Purpose is i-indexed and never shared by default; two
 * objects that agreed a purpose by inheritance would be one object. */
typedef struct {
    const char *purpose;  /* Phi_i */
    const char *energy;   /* H_i   */
    void       *state;    /* X_i, theta_i; opaque to the type layer */
} Rme7Payload;

/* The system-facing actor: NON-HEREDITARY BY CONSTRUCTION.
 *
 * It has no parent field and no delegation entry point, so nothing can
 * delegate into it and it can defer to nothing. That is what protects the
 * grammar: a realization can never reach up the ladder and redefine the
 * format it is a realization of. Implementation order is not grammar
 * order, and this struct is where the difference is enforced rather than
 * asserted. */
struct Rme7Actor {
    const char  *name;
    Rme7SlotDecl slots[RME7_SLOT_COUNT];
};

struct Rme7Proto {
    const char      *name;
    Rme7Layer        layer;
    const Rme7Proto *parent;  /* delegation; nullptr at either root */
    Rme7Origin       origin;  /* generation; immutable after birth  */
    Rme7SlotDecl     slots[RME7_SLOT_COUNT];  /* definitions; delegable   */
    Rme7Profile      contracts;                /* offered; local only      */
    Rme7Profile      exhibits;                 /* evidence; local only     */
    Rme7Payload      payload;                  /* value; local only        */
    Rme7Rung         declared;
    bool             declared_set;
};

/* Seeds the actor with the grammar: all seven slots established, each with
 * the office the grammar gives it, custody NONE because the grammar is not
 * an exhibit. */
void rme7_actor_init(Rme7Actor *actor, const char *name);

/* Generation across the layer boundary SEEDS: the child receives a copy of
 * the generator's slot declarations, because it cannot delegate back across
 * the boundary to find them. This is the one sanctioned crossing shape. */
void rme7_actor_generate_system_root(const Rme7Actor *actor,
                                     Rme7Proto *out, const char *name);
void rme7_proto_generate_user_root(const Rme7Proto *system_root,
                                   Rme7Proto *out, const char *name);

/* Generation within the user layer LINKS: the child establishes nothing and
 * delegates upward for everything it has not overridden. Returns false and
 * leaves `out` untouched if the generator is not user-facing. */
[[nodiscard]] bool rme7_proto_generate(const Rme7Proto *generator,
                                       Rme7Proto *out, const char *name);

/* Define a slot locally, overriding whatever the chain would resolve. */
void rme7_proto_define(Rme7Proto *proto, Rme7Slot slot,
                       Rme7Custody custody, const char *office);

/* Record that this object EXHIBITS a slot. Local, never inherited, and
 * refused for a slot no rung of the chain defines: an object cannot exhibit
 * a distinction the format has not given it. Returns false on refusal. */
[[nodiscard]] bool rme7_proto_exhibit(Rme7Proto *proto, Rme7Slot slot);
void rme7_proto_unexhibit(Rme7Proto *proto, Rme7Slot slot);

/* Offer to compose on a slot without exhibiting it. Refused, like exhibition,
 * for a slot no rung of the chain defines: an object cannot contract on a
 * distinction the format never gave it. Exhibiting implies contracting. */
[[nodiscard]] bool rme7_proto_contract(Rme7Proto *proto, Rme7Slot slot);
[[nodiscard]] Rme7Profile rme7_proto_contracts(const Rme7Proto *proto);

/* Two objects are structurally compatible when their contracts agree. Note
 * what this does NOT consult: lineage. Interoperability does not require
 * common ancestry, and this is the predicate that says so. */
[[nodiscard]] bool rme7_proto_compatible(const Rme7Proto *a, const Rme7Proto *b);

/* Resolve a slot DEFINITION by delegation. Returns nullptr when no rung of
 * the chain defines it -- which means not defined, never "absent from the
 * world". When `found_in` is non-null it receives the proto that answered. */
[[nodiscard]] const Rme7SlotDecl *rme7_proto_resolve(const Rme7Proto *proto,
                                                     Rme7Slot slot,
                                                     const Rme7Proto **found_in);

[[nodiscard]] bool rme7_proto_defines(const Rme7Proto *proto, Rme7Slot slot);

/* This object's own activation profile. Local by construction -- which is
 * what makes a clear bit mean "not established HERE" rather than "the
 * format lacks it". */
[[nodiscard]] Rme7Profile rme7_proto_profile(const Rme7Proto *proto);
[[nodiscard]] Rme7Cast    rme7_proto_classify(const Rme7Proto *proto);

/* Local only. Never walks the parent chain -- see the payload note above. */
[[nodiscard]] const Rme7Payload *rme7_proto_payload(const Rme7Proto *proto);

void rme7_proto_declare(Rme7Proto *proto, Rme7Rung rung);

/* Observed minus declared, for a proto that declared a rung. Returns false
 * when nothing was declared: there is no delta against a silence. */
[[nodiscard]] bool rme7_proto_delta_level(const Rme7Proto *proto, int *out);

/* Is `ancestor` on this proto's delegation chain? */
[[nodiscard]] bool rme7_proto_delegates_to(const Rme7Proto *proto,
                                           const Rme7Proto *ancestor);

/* Was this proto generated, directly or transitively, by `origin`? */
[[nodiscard]] bool rme7_proto_descends_from(const Rme7Proto *proto,
                                            const Rme7Proto *origin);

#endif /* RME7_PROTO_H */
