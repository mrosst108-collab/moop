"""The session ledger: an append-only hash chain.

Two invariants of the instrument are enforced here rather than promised.

**Commit before run.** A response record is refused unless the commitment it
references is already sealed earlier in the chain. Retrofitting declared poles
to whatever came back is not caught by inspecting a transcript -- a retrofitted
transcript and a genuine one look the same -- so the ordering is made
structural. This is the Layer 1-2 audit imported as a rule: did the opening
exist prior to the work it is said to have constrained.

**Responder is not classifier.** A classification record must name a
responder id and a classifier id, and they must differ. Otherwise the
measurement is self-report, and the planted-error mechanic becomes a system
marking its own work.

Editing an earlier record breaks every hash after it, which ``verify`` reports.
The chain does not prevent tampering; it makes tampering visible, which is what
a forensic record is for.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone

RECORD_TYPES = (
    "commitment",      # sealed declarations, before any generation
    "response",        # a generated response, referencing a commitment
    "classification",  # a classifier output over a response
    "plant",           # ground truth for a planted misclassification
    "adjudication",    # the student's verdict on a classification
    "outcome",         # externally sourced, later
    "validation",      # classifier validation against an external anchor
    "note",
)


class LedgerError(ValueError):
    pass


def canonical(payload) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(payload) -> str:
    return hashlib.sha256(canonical(payload).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, path: str) -> None:
        self.path = path
        self.records: list = []
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as handle:
                for line in handle:
                    line = line.strip()
                    if line:
                        self.records.append(json.loads(line))

    # -- internals ---------------------------------------------------------

    @property
    def head(self) -> str:
        return self.records[-1]["hash"] if self.records else "0" * 64

    def _find(self, record_hash: str):
        for rec in self.records:
            if rec["hash"] == record_hash:
                return rec
        return None

    def _append(self, kind: str, payload: dict, refs: dict | None = None) -> str:
        if kind not in RECORD_TYPES:
            raise LedgerError(f"unknown record type {kind!r}")
        body = {
            "seq": len(self.records),
            "type": kind,
            "at": _now(),
            "prev": self.head,
            "refs": refs or {},
            "payload": payload,
            "payload_sha256": digest(payload),
        }
        record = dict(body, hash=digest(body))
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
        self.records.append(record)
        return record["hash"]

    # -- typed appends -----------------------------------------------------

    def commit(self, declarations: dict) -> str:
        """Seal the student's declarations. Nothing may be added to them later."""
        return self._append("commitment", declarations)

    def response(self, commitment_hash: str, payload: dict) -> str:
        target = self._find(commitment_hash)
        if target is None:
            raise LedgerError(
                "commit-before-run: no sealed commitment with that hash exists "
                "earlier in this chain. A response cannot reference declarations "
                "that were not sealed before it."
            )
        if target["type"] != "commitment":
            raise LedgerError(f"reference is a {target['type']}, not a commitment")
        return self._append("response", payload, {"commitment": commitment_hash})

    def classification(self, response_hash: str, payload: dict, *, responder: str,
                       classifier: str) -> str:
        if responder == classifier:
            raise LedgerError(
                "responder != classifier: the instance producing the response "
                "may not be the instance typing it, or the measurement is "
                "self-report."
            )
        target = self._find(response_hash)
        if target is None or target["type"] != "response":
            raise LedgerError("classification must reference a sealed response")
        return self._append(
            "classification", payload,
            {"response": response_hash, "responder": responder, "classifier": classifier},
        )

    def plant(self, classification_hash: str, truth: dict) -> str:
        target = self._find(classification_hash)
        if target is None or target["type"] != "classification":
            raise LedgerError("plant must reference a sealed classification")
        return self._append("plant", truth, {"classification": classification_hash})

    def adjudication(self, classification_hash: str, payload: dict) -> str:
        target = self._find(classification_hash)
        if target is None or target["type"] != "classification":
            raise LedgerError("adjudication must reference a sealed classification")
        return self._append("adjudication", payload, {"classification": classification_hash})

    def outcome(self, refs: dict, payload: dict) -> str:
        """Externally sourced. Self-supplied outcomes are internal recurrence."""
        if not payload.get("source") or payload.get("source") == "self":
            raise LedgerError(
                "an outcome must name an external source. If the student "
                "decides which retained bridges failed, the loop calibrates a "
                "judgement against later judgements by the same party, which "
                "yields coherence and not evidence."
            )
        return self._append("outcome", payload, refs)

    def validation(self, payload: dict) -> str:
        """A classifier-validation record against an anchor external to the architecture."""
        for key in ("anchor", "method", "agreement"):
            if key not in payload:
                raise LedgerError(f"validation record requires {key!r}")
        return self._append("validation", payload)

    # -- reading -----------------------------------------------------------

    def of_type(self, kind: str) -> list:
        return [r for r in self.records if r["type"] == kind]

    def has_validation(self) -> bool:
        return bool(self.of_type("validation"))

    def verify(self) -> dict:
        problems = []
        prev = "0" * 64
        for idx, rec in enumerate(self.records):
            if rec["seq"] != idx:
                problems.append(f"record {idx}: seq is {rec['seq']}")
            if rec["prev"] != prev:
                problems.append(f"record {idx}: prev link broken")
            body = {k: v for k, v in rec.items() if k != "hash"}
            if digest(body) != rec["hash"]:
                problems.append(f"record {idx}: content hash mismatch -- edited after sealing")
            if digest(rec["payload"]) != rec["payload_sha256"]:
                problems.append(f"record {idx}: payload hash mismatch")
            prev = rec["hash"]
        return {"records": len(self.records), "intact": not problems, "problems": problems}
