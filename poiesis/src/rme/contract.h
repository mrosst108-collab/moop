#ifndef RME_CONTRACT_H
#define RME_CONTRACT_H

#include "proto.h"

/* poiesis — per-port contracts.
 *
 * Status SELECTS the applicable realization contract:
 *
 *     RealizationValid(p) = ActiveContract(p)     if Status(p) = ACTIVE
 *                           VestigialContract(p)  if Status(p) = VESTIGIAL
 *
 * There is NO universal null implementation.  "Non-substantive" is fixed
 * by each port's own vestigial contract: an inert endpoint, an empty
 * capability, a default-valued state and an operation returning a defined
 * "not realized" result are not equivalent shapes, and a blanket
 * `return 0;` is prohibited.  A port's permitted vestigial realization is
 * DECLARED; a hand-rolled stub that merely returns zero is not that
 * declared object and is rejected.
 *
 * OPEN (spec §Disposition): the substantive content of these contracts is
 * the next specification task.  Every contract below carries `provisional`
 * so the gap is mechanically visible — rme_contract_report() prints it and
 * the build surfaces it.  Provisional contracts must not harden into
 * accidental normative commitments.
 */

typedef struct {
    RmePortId   id;
    bool        provisional;

    /* The declared permitted vestigial realization for this port.  A
     * VESTIGIAL port must point at exactly this object. */
    const void *vestigial_realization;

    /* Optimization invariant, NOT an RME-7 semantic rule:
     *     Elidable(p) <=> Status(p)=VESTIGIAL && allows_elision
     * VESTIGIAL alone never implies elidable. */
    bool        vestigial_allows_elision;

    const char *note;
} RmePortContract;

const RmePortContract *rme_contract(RmePortId id);

/* Status-selected validation for one port.  On failure sets *why. */
bool rme_realization_valid(const RmePrototype *p, RmePortId id, const char **why);

/* Optimization permission — never a semantic status. */
bool rme_port_elidable(const RmePrototype *p, RmePortId id);

/* Declared compatibility relation over an endpoint PAIR.  This is a
 * property of the pair alone: it says nothing about whether the two
 * prototypes compose, and its negation says nothing about either
 * prototype's conformance. */
bool rme_compatible(const RmePrototype *P, RmePortId pi,
                    const RmePrototype *Q, RmePortId qi,
                    const char **why);

/* Mechanically visible provisional status: how many contracts are still
 * provisional, and a printable report. */
size_t rme_contract_provisional_count(void);
void   rme_contract_report(void);

/* The declared vestigial realizations, exposed so instances can point at
 * them.  Each is port-appropriate, not a shared no-op. */
extern const RmeStateApi            rme_vestigial_state;
extern const RmeObservationApi      rme_vestigial_observation;
extern const RmeTransitionApi       rme_vestigial_transition;
extern const RmeParameterizationApi rme_vestigial_parameterization;
extern const RmeCouplingApi         rme_vestigial_coupling;
extern const RmeAdaptationApi       rme_vestigial_adaptation;
extern const RmeGovernanceApi       rme_vestigial_governance;
extern const RmeNestedApi           rme_vestigial_nested;

#endif /* RME_CONTRACT_H */
