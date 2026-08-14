"""The passage audit: was a closure promoted into authority over the next opening?

The passage constraint says Cᵢ satisfied is a precondition for entering layer
i+1, never a warrant for Oᵢ₊₁. Two tests for that were considered and rejected
before this one.

*Citation* -- does the justification for Oᵢ₊₁ cite Cᵢ as its warrant. Rejected:
silent promotion is the characteristic form, so an audit firing on citation
catches the honest violations and misses the ones the firewall exists for.

*Content dependence* -- substitute a different Cᵢ and see whether Oᵢ₊₁ shifts.
Rejected: Cᵢ can legitimately inform what is declared next, since it is the same
inquiry, and the constraint is about authority rather than relevance. A
divergence test cannot tell those apart and over-fires.

What is retained is a **provenance query**. The passage constraint is not a
semantic property of the resulting opening; it is a property of the opening's
custody, and custody is an ordering fact the hash chain already records. So this
is not a classifier and not a new measurement channel -- it is a typed read over
records that already exist.

Two questions are kept apart, because the first draft of the state table mixed
them: *was the opening held before the closure* is about the run, and *does the
record establish when custody began* is about the ledger. They get separate
reports.
"""

from __future__ import annotations

from collections import Counter

from .ontology import LAYER_IDS

PROTECTED = "protected"
STANDING_PROTECTED = "standing_protected"
STANDING_UNSUPPORTED = "standing_claimed_unsupported"
UNPROTECTED = "unprotected_by_record"
UNRESOLVED = "unresolved"

STATES = (PROTECTED, STANDING_PROTECTED, STANDING_UNSUPPORTED, UNPROTECTED, UNRESOLVED)

#: A ``standing_since`` value beginning with this marks custody whose origin is
#: outside this ledger. It is the only route to UNRESOLVED, which is the point:
#: unresolved should mean "the provenance was not preserved", not "a standing
#: opening was declared".
EXTERNAL_ORIGIN = "external"

#: Which states are positive forensic findings, and at which layer they sit.
FINDING_TYPE = {
    PROTECTED: None,
    STANDING_PROTECTED: None,
    UNRESOLVED: None,
    UNPROTECTED: "L1",
    STANDING_UNSUPPORTED: "L2",
}

MEANING = {
    PROTECTED: "the record establishes that the opening was held before the closure",
    STANDING_PROTECTED: (
        "the opening was established as standing under an earlier commitment "
        "that predates the closure, and that commitment does contain it"
    ),
    STANDING_UNSUPPORTED: (
        "the opening claims to have been standing since a commitment that does "
        "not contain it. The record contains a claim of earlier custody that "
        "the record itself contradicts"
    ),
    UNPROTECTED: "the first recorded custody of the opening occurs after the closure",
    UNRESOLVED: (
        "custody is claimed from an origin outside this record, so the record "
        "cannot place it relative to the closure"
    ),
}

NOT_VIOLATED = (
    "NOT_VIOLATED means the record does not establish a violation. It does not "
    "mean the record establishes compliance. "
    "No state here is a finding of promotion: 'unprotected by the record' means "
    "the record does not protect the opening, not that the opening was promoted "
    "-- it may have been held all along and written down late. 'Unresolved' is "
    "weaker still. Turning missing provenance into a finding of promotion is "
    "interpolating what the record does not establish, which is the one thing "
    "the forensic layer prohibits."
)

# -- audit states -----------------------------------------------------------

CLEAN = "CLEAN"
FINDINGS = "FINDINGS"
UNEXAMINED = "UNEXAMINED"

FULL_COVERAGE = "FULL"
PARTIAL_COVERAGE = "PARTIAL"
NO_COVERAGE = "UNEXAMINED"

AUDIT_STATE_MEANING = {
    CLEAN: (
        "Every passage relation the record raises was examined, and no positive "
        "finding was recorded. This is the only state that may be read as 'the "
        "examined record contains no finding'."
    ),
    FINDINGS: (
        "One or more positive findings. If coverage is not full, the findings "
        "stand and the unexamined boundaries are not thereby clean."
    ),
    UNEXAMINED: (
        "The record does not contain enough layer-addressable commitments and "
        "closures to establish that the relations it raises were examined. This "
        "says nothing about passage discipline, in either direction."
    ),
}

COVERAGE_RULE = (
    "A forensic audit cannot certify the absence of a finding in a region it "
    "did not examine. An empty findings block from an impoverished record and "
    "an empty findings block from a disciplined one are not the same result, "
    "and the difference is carried in the audit state rather than left to be "
    "inferred from a count."
)

REQUIRED_SET_NOTE = (
    "The required set is induced by the record, not by a norm. A boundary "
    "(C_i, O_i+1) is *raised* when the record itself contains a closure at i or "
    "an opening at i+1 -- the record's own assertion that the layer was in play "
    "is what makes the passage question live there. Deriving the required set "
    "from what a properly conducted run *should* have contained would be a "
    "normative judgement about what the user ought to have declared, which this "
    "audit is not authorised to make."
)

FORENSIC_ONLY = (
    "This audit reports the record and never grades it. A rate is a Layer 1 "
    "statement; a score would supply a warrant standard, which is Layer 5, and "
    "hand custody of the closure criterion to the instrument."
)


def next_layer(layer: str) -> str | None:
    idx = LAYER_IDS.index(layer)
    return LAYER_IDS[idx + 1] if idx + 1 < len(LAYER_IDS) else None


def _anchor_contains(ledger, anchor_hash: str, opening_id: str):
    """Resolve a standing anchor by CONTENT, not by pointer.

    ``standing_since`` is a field whose entire function is to claim earlier
    custody. Accepting the assertion and checking only its timestamp would make
    it a backdating primitive: any opening could name any earlier commitment and
    inherit its protection. The audit therefore reads the referenced
    commitment's payload and confirms the opening is actually in it.
    """
    for rec in ledger.records:
        if rec["hash"] != anchor_hash:
            continue
        if rec["type"] != "commitment":
            return None, "anchor is not a commitment"
        ids = {o.get("opening_id") for o in rec["payload"].get("openings") or []}
        return (rec, None) if opening_id in ids else (rec, "anchor does not contain this opening")
    return None, "anchor not present in this chain"


def classify(ledger, entry: dict, closure_rec: dict) -> dict:
    opening = entry["opening"]
    seal_seq = entry["seq"]
    closure_seq = closure_rec["seq"]
    reopened = bool(opening.get("triggered_reopen"))
    mode = opening["custody_mode"]

    base = {
        "opening_id": opening["opening_id"],
        "layer": opening["layer"],
        "custody_mode": mode,
        "triggered_reopen": reopened,
        "closure_layer": closure_rec["payload"]["layer"],
        "closure_seq": closure_seq,
        "seal_seq": seal_seq,
    }

    # A reopened opening is a fresh declaration. Standing protection acquired
    # before the trigger does not carry across it, or "standing" would license
    # every later re-declaration.
    if mode == "run_specific" or reopened:
        state = PROTECTED if seal_seq < closure_seq else UNPROTECTED
        detail = ("reopened on trigger, so judged on its own seal time"
                  if reopened else "run-specific opening, judged on its seal time")
        return {**base, "state": state, "detail": detail}

    anchor = opening.get("standing_since")
    if anchor is None:
        # First recorded declaration of a standing opening: this record *is* the
        # origin. Requiring it to name an earlier one would leave every standing
        # opening permanently unresolved, which is over-strict -- the record does
        # establish when custody began. Judge it on its own seal time.
        state = PROTECTED if seal_seq < closure_seq else UNPROTECTED
        return {**base, "state": state,
                "detail": "standing custody first recorded here; judged on its own seal time"}

    if isinstance(anchor, str) and anchor.startswith(EXTERNAL_ORIGIN):
        return {**base, "state": UNRESOLVED, "anchor": anchor,
                "detail": "custody claimed from an origin outside this record"}

    record, problem = _anchor_contains(ledger, anchor, opening["opening_id"])
    if problem is not None:
        return {**base, "state": STANDING_UNSUPPORTED, "anchor": anchor, "detail": problem}
    if record["seq"] >= closure_seq:
        return {**base, "state": UNPROTECTED, "anchor": anchor,
                "detail": "the standing anchor itself postdates the closure"}
    return {**base, "state": STANDING_PROTECTED, "anchor": anchor,
            "detail": f"standing since commitment at seq {record['seq']}"}


def coverage(ledger) -> dict:
    """Which passage boundaries the record raises, and which of them it can answer.

    Boundary granularity, deliberately distinct from the pair count in the
    findings block: several closures at layer i and several openings at i+1
    produce many comparisons across one boundary, and coverage is a question
    about boundaries.
    """
    closure_layers = {r["payload"]["layer"] for r in ledger.records if r["type"] == "closure"}
    opening_layers = {e["opening"]["layer"] for e in ledger.openings()}

    raised, examined, unexamined = [], [], []
    for lower, upper in zip(LAYER_IDS, LAYER_IDS[1:]):
        has_closure, has_opening = lower in closure_layers, upper in opening_layers
        if not (has_closure or has_opening):
            continue
        raised.append((lower, upper))
        if has_closure and has_opening:
            examined.append((lower, upper))
        else:
            unexamined.append({
                "boundary": (lower, upper),
                "missing": "opening at " + upper if has_closure else "closure at " + lower,
            })

    if not examined:
        status = NO_COVERAGE
    elif len(examined) == len(raised):
        status = FULL_COVERAGE
    else:
        status = PARTIAL_COVERAGE

    return {
        "required_boundaries": len(raised),
        "examined_boundaries": len(examined),
        "raised": raised,
        "examined": examined,
        "unexamined": unexamined,
        "coverage_status": status,
        "required_set_note": REQUIRED_SET_NOTE,
    }


def audit(ledger) -> dict:
    """Findings about the run, provenance quality about the ledger, coverage about both."""
    closures = [r for r in ledger.records if r["type"] == "closure"]
    openings = ledger.openings()

    findings = []
    for closure_rec in closures:
        successor = next_layer(closure_rec["payload"]["layer"])
        if successor is None:
            continue
        for entry in openings:
            if entry["opening"]["layer"] == successor:
                findings.append(classify(ledger, entry, closure_rec))

    counts = Counter(f["state"] for f in findings)
    examined_ids = {f["opening_id"] for f in findings}
    unpaired = [e["opening"]["opening_id"] for e in openings
                if e["opening"]["opening_id"] not in examined_ids]

    positive = [f for f in findings if FINDING_TYPE[f["state"]] is not None]
    cover = coverage(ledger)

    if positive:
        state = FINDINGS
    elif cover["coverage_status"] == FULL_COVERAGE:
        state = CLEAN
    else:
        # Partial coverage cannot support a clean conclusion: some boundary the
        # record itself raised went unexamined, and absence of a finding there
        # is absence of a look.
        state = UNEXAMINED

    return {
        "state": state,
        "state_meaning": AUDIT_STATE_MEANING[state],
        "coverage": cover,
        "coverage_rule": COVERAGE_RULE,
        "findings_stand_despite_partial_coverage": (
            state == FINDINGS and cover["coverage_status"] != FULL_COVERAGE
        ),
        "pairs_examined": len(findings),
        "findings": findings,
        "counts": {s: counts.get(s, 0) for s in STATES},
        "positive_findings": positive,
        "openings_with_no_preceding_closure": sorted(set(unpaired)),
        "provenance_quality": {
            "unresolved": counts.get(UNRESOLVED, 0),
            "unsupported_standing_claims": counts.get(STANDING_UNSUPPORTED, 0),
            "note": (
                "This is a fact about the ledger's bookkeeping, not about the "
                "run. An unresolved rate says the provenance needed to "
                "distinguish legitimate standing custody from a retrospective "
                "claim was not preserved. Reporting it in the same column as "
                "the run findings invites the first to be read as the second."
            ),
        },
        "meanings": dict(MEANING),
        "not_violated": NOT_VIOLATED,
        "forensic_only": FORENSIC_ONLY,
    }


def render(result: dict) -> str:
    cover = result["coverage"]
    lines = [
        f"Passage audit: {result['state']}  (forensic; the record, never a grade)",
        f"  {result['state_meaning']}",
        "",
        f"  coverage: {cover['examined_boundaries']}/{cover['required_boundaries']} "
        f"boundaries raised by the record were examined -- {cover['coverage_status']}",
    ]
    for gap in cover["unexamined"]:
        lo, hi = gap["boundary"]
        lines.append(f"    not examined: {lo} -> {hi} (no {gap['missing']})")
    if result["findings_stand_despite_partial_coverage"]:
        lines.append("    findings below stand; the unexamined boundaries are not thereby clean")
    lines.append("")

    lines.append(f"  pairs examined: {result['pairs_examined']}")
    for state in STATES:
        lines.append(f"    {state:30s} {result['counts'][state]}")
    lines.append("")
    for finding in result["positive_findings"]:
        layer = FINDING_TYPE[finding["state"]]
        lines.append(f"  ! {finding['opening_id']} @ {finding['layer']} after "
                     f"{finding['closure_layer']}: {finding['state']} [{layer}] -- {finding['detail']}")
    if result["positive_findings"]:
        lines.append("")
    quality = result["provenance_quality"]
    lines.append(f"  provenance quality: unresolved={quality['unresolved']}, "
                 f"unsupported standing claims={quality['unsupported_standing_claims']}")
    lines.append(f"  {result['not_violated']}")
    return "\n".join(lines)
