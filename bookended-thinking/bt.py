#!/usr/bin/env python3
"""bt -- the command line for the bookended-thinking instrument.

This program never calls a language model. It renders prompts for one to
answer, and it ingests, validates, seals and measures what comes back. Keeping
generation outside the program is what makes the responder-is-not-classifier
separation structural instead of procedural: two separate artifacts are
ingested, and the ledger refuses them if they claim the same author.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from engine import passage, scoring, validate, yamlish         # noqa: E402
from engine.ledger import Ledger, LedgerError                  # noqa: E402
from engine.ontology import Ontology, TypingRules              # noqa: E402
from engine.typing_rules import predicted_blocks               # noqa: E402

PROMPTS = {"pole": "pole_classifier.md", "bridge": "bridge_classifier.md"}
MODES = {"pole": "pole_typing", "bridge": "bridge_typing"}


def _load():
    return Ontology.load(HERE), TypingRules.load(HERE)


def cmd_check(args) -> int:
    ont, rules = _load()
    print(f"ontology      {ont.version}  ({len(ont.layers)} layers, {len(ont.dynamics)} objects)")
    print(f"typing rules  {rules.version}  (withheld from classifier)")
    print()
    blocks = predicted_blocks(ont, rules)
    for name in ("operator_block", "indicator_row", "invariant_row"):
        b = blocks[name]
        print(f"  {name:16s} {b['cells']:>3} cells  {b['relation']:<17s} [{b['status']}]  {', '.join(b['members'])}")
    print(f"  total            refused -- {blocks['total_refused_because']}")
    print()
    for key, name in PROMPTS.items():
        ont.render_prompt(os.path.join(HERE, "prompts", name), HERE)
        print(f"  prompt {key:7s} renders clean (no prediction leak)")
    for drill in sorted(os.listdir(os.path.join(HERE, "drills"))):
        if drill.endswith(".yaml"):
            yamlish.load_file(os.path.join(HERE, "drills", drill))
            print(f"  drill  {drill[:-5]:7s} parses")
    return 0


def cmd_render(args) -> int:
    ont, _ = _load()
    sys.stdout.write(ont.render_prompt(os.path.join(HERE, "prompts", PROMPTS[args.mode]), HERE))
    return 0


def cmd_drill(args) -> int:
    path = os.path.join(HERE, "drills", f"{args.name}.yaml")
    if not os.path.exists(path):
        print(f"no such drill: {args.name}", file=sys.stderr)
        return 2
    data = yamlish.load_file(path)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("\n-- seal the pre-registration before running:  bt.py seal <ledger> <file>",
          file=sys.stderr)
    return 0


def cmd_seal(args) -> int:
    ledger = Ledger(args.ledger)
    with open(args.file, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    digest = ledger.commit(payload)
    print(digest)
    return 0


def cmd_ingest(args) -> int:
    ont, _ = _load()
    ledger = Ledger(args.ledger)
    with open(args.response, "r", encoding="utf-8") as handle:
        response_text = handle.read()
    with open(args.classification, "r", encoding="utf-8") as handle:
        classification = json.load(handle)

    result = validate.validate(classification, MODES[args.mode], response_text, HERE)
    if result["errors"]:
        for err in result["errors"]:
            print(f"schema: {err}", file=sys.stderr)
        return 1
    for down in result["downgrades"]:
        print(f"downgraded {down['path']}: {down['reason']} (was {down['was']})", file=sys.stderr)

    try:
        response_hash = ledger.response(args.commitment, {"text": response_text})
        digest = ledger.classification(
            response_hash, classification,
            responder=args.responder, classifier=args.classifier,
        )
    except LedgerError as exc:
        print(f"ledger: {exc}", file=sys.stderr)
        return 1
    print(digest)
    return 0


def cmd_verify(args) -> int:
    ledger = Ledger(args.ledger)
    result = ledger.verify()
    print(json.dumps(result, indent=2))
    if not ledger.has_validation():
        print("\nno validation record: reports from this ledger are coherence, not corroboration",
              file=sys.stderr)
    return 0 if result["intact"] else 1


def cmd_passage(args) -> int:
    result = passage.audit(Ledger(args.ledger))
    print(json.dumps(result, indent=2) if args.json else passage.render(result))
    return 0


def cmd_report(args) -> int:
    ont, rules = _load()
    with open(args.runs, "r", encoding="utf-8") as handle:
        runs = json.load(handle)
    ledger = Ledger(args.ledger) if args.ledger else None
    rep = scoring.report(
        ontology=ont,
        rules=rules,
        ledger=ledger,
        input_cells=[tuple(c) for c in runs.get("input_cells", [])],
        output_samples=[[tuple(c) for c in s] for s in runs.get("output_samples", [])],
        null_samples=[[tuple(c) for c in s] for s in runs.get("null_samples", [])],
        declared_objects=runs.get("declared_objects", []),
        interaction_arms=runs.get("interaction_arms"),
        ablation_arms=runs.get("ablation_arms"),
        planted_rounds=runs.get("planted_rounds"),
        trajectory_arms=runs.get("trajectory_arms"),
    )
    print(scoring.render(rep) if not args.json else json.dumps(rep, indent=2, default=str))
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="bt", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("check", help="load the ontology and prove the prompts leak nothing").set_defaults(func=cmd_check)

    p = sub.add_parser("render", help="print a classifier prompt with the ontology interpolated")
    p.add_argument("mode", choices=sorted(PROMPTS))
    p.set_defaults(func=cmd_render)

    p = sub.add_parser("drill", help="print a drill specification")
    p.add_argument("name")
    p.set_defaults(func=cmd_drill)

    p = sub.add_parser("seal", help="seal declarations into the ledger (commit before run)")
    p.add_argument("ledger")
    p.add_argument("file")
    p.set_defaults(func=cmd_seal)

    p = sub.add_parser("ingest", help="validate and seal a response plus its classification")
    p.add_argument("ledger")
    p.add_argument("--mode", choices=sorted(MODES), required=True)
    p.add_argument("--commitment", required=True, help="hash of the sealed commitment")
    p.add_argument("--response", required=True)
    p.add_argument("--classification", required=True)
    p.add_argument("--responder", required=True)
    p.add_argument("--classifier", required=True)
    p.set_defaults(func=cmd_ingest)

    p = sub.add_parser("verify", help="walk the hash chain")
    p.add_argument("ledger")
    p.set_defaults(func=cmd_verify)

    p = sub.add_parser("passage", help="provenance query: was a closure promoted into authority?")
    p.add_argument("ledger")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_passage)

    p = sub.add_parser("report", help="compute what is currently well-founded")
    p.add_argument("runs")
    p.add_argument("--ledger")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_report)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
