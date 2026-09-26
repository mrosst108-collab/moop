#ifndef PC_SURFACE_H
#define PC_SURFACE_H

#include <stdbool.h>
#include <stddef.h>

/* ProtoC — types/
 *
 * Derived from SEMANTICS.md S1-S11 ONLY.  Every structural decision below is
 * recorded in ../DERIVATION.md with the S-statement that forces it.  Nothing
 * here was decided by reading ../../src/rme/, and where the frozen semantics
 * do not determine a decision, that is said so explicitly rather than
 * resolved by looking.
 *
 * THE DELIBERATE STRUCTURAL DIVERGENCE.  Ports are DATA, not named struct
 * members: a shared immutable descriptor table plus a parallel instance
 * array.  A surface is therefore describable at runtime and its port count
 * is not baked into the type.  Nothing in the frozen semantics mentions a
 * fixed port vocabulary -- S3 constrains what a status MEANS, not how many
 * ports exist -- so treating the vocabulary as data is faithful, and it is
 * about as far from a fixed record of named members as one can get while
 * still expressing S1-S11.
 */

/* S2 forces status and realization validity to be INDEPENDENTLY enforced,
 * so they are separate fields validated separately, and neither is
 * inferable from the other.
 *
 * PC_STATUS_UNSET exists because S8 requires a malformed input to be
 * REFUSED rather than normalized: a zero-filled port must be detectably
 * unset rather than silently defaulting to a semantic status.  It is a
 * construction sentinel and never a semantic answer. */
typedef enum {
    PC_STATUS_UNSET = 0,
    PC_ACTIVE,
    PC_VESTIGIAL,
} PcStatus;

/* The two semantic statuses, and nothing else, are answers. */
bool pc_status_is_semantic(PcStatus s);

/* The declared, immutable description of one port.  Shared across every
 * surface of a schema: a description is not per-instance state. */
typedef struct {
    const char *name;   /* declared port identity */
    const char *type;   /* declared interface type */
} PcPortDescriptor;

typedef struct {
    const char             *name;
    const PcPortDescriptor *ports;
    size_t                  port_count;
    unsigned                revision;
} PcSchema;

/* One port instance.
 *
 * S6 stops substrate ownership at the record boundary, so `realization` and
 * `vestigial_form` are POINTERS THE SURFACE DOES NOT OWN.  The type says so
 * by being const and by the surface never freeing, copying or dereferencing
 * them -- ProtoC compares them, and comparison is the only operation S2
 * needs.
 *
 * S7 makes elision a per-port PERMISSION rather than a consequence of
 * status, so the permission is a field on the port and is meaningless
 * unless the status is vestigial. */
typedef struct {
    PcStatus    status;
    const void *realization;
    const void *vestigial_form;
    bool        elidable_when_vestigial;
} PcPort;

/* A surface: a schema plus the instance vector.  Note there is no validity
 * field.  S9/S10 make validity nonhereditary and non-transferable, and a
 * field would be the obvious way to violate both, so the representation
 * simply has nowhere to record it. */
typedef struct {
    const char     *identity;
    const PcSchema *schema;
    PcPort         *ports;
    size_t          port_count;
} PcSurface;

/* Refusal reasons.  S8 requires that a malformed input be refused rather
 * than normalized, which means the refusal must be DISTINGUISHABLE from a
 * negative answer -- hence a reason code rather than a bare false. */
typedef enum {
    PC_OK = 0,
    PC_REFUSED_NO_SURFACE,
    PC_REFUSED_NO_SCHEMA,
    PC_REFUSED_ARITY,          /* instance vector disagrees with the schema */
    PC_REFUSED_STATUS_UNSET,
    PC_REFUSED_STATUS_DOMAIN,  /* outside {ACTIVE, VESTIGIAL} */
    PC_REFUSED_NO_REALIZATION,
    PC_REFUSED_ACTIVE_IS_VESTIGIAL_FORM,
    PC_REFUSED_VESTIGIAL_NOT_DECLARED_FORM,
} PcRefusal;

typedef struct {
    PcRefusal reason;
    size_t    port;    /* offending port index, or port_count */
} PcVerdict;

const char *pc_refusal_text(PcRefusal r);

/* Structural well-formedness: does the instance vector match its schema?
 * Separate from the status/realization questions because S2 requires the
 * two to be independently enforced -- fusing them would make it impossible
 * to say which one failed. */
PcVerdict pc_surface_wellformed(const PcSurface *s);

/* Per-port status/realization agreement (S2).  Both directions:
 *   ACTIVE    must NOT name the declared vestigial form
 *   VESTIGIAL must name exactly the declared vestigial form
 * Neither direction is inferable from the other, so both are checked. */
PcVerdict pc_port_realization_agrees(const PcSurface *s, size_t port);

/* S7: elision is a permission, never implied by status. */
bool pc_port_elidable(const PcSurface *s, size_t port);

/* The envelope is every declared port unconditionally; the dispatch set
 * omits only what the permission allows.  S7 makes the containment a
 * property of CONSTRUCTION -- pc_dispatch_count can only ever be <=
 * pc_envelope_count because omission is the only operation available -- so
 * no runtime subset predicate is offered.  Offering one would suggest the
 * relation might fail. */
size_t pc_envelope_count(const PcSurface *s);
size_t pc_dispatch_count(const PcSurface *s);
bool   pc_in_envelope(const PcSurface *s, size_t port);
bool   pc_in_dispatch(const PcSurface *s, size_t port);

#endif /* PC_SURFACE_H */
