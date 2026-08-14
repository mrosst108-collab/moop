"""Structural validation of classifier output, plus the evidence-span check.

The schemas in ``schemas/`` are the single source of truth; this is a small
reader for the subset of JSON Schema they use, so the shape is never specified
in two places that can drift apart.

Two checks do real work here. The first is the ontology-version check: a
classification carries the version it was produced under, and that field is a
*declaration about history*, not history. It cannot make an earlier
classification belong to the current ontology. The engine cannot verify the
classifier's internal process from a version string, but it can establish
whether the record is admissible to *this* scoring run, and a mismatch means it
is not -- which is a fact about admissibility, not evidence that the classifier
was wrong. The stored record keeps whatever version it claimed; an artifact is
reclassified or excluded, never silently relabelled.

The second is the evidence check. A classification whose
quoted evidence does not occur in the source it claims to be quoting is
downgraded to ``uncertain`` and the downgrade is recorded. This is cheap and it
catches the failure mode a rubric cannot: an instrument that produces
confident, well-formed classifications of text that is not there.
"""

from __future__ import annotations

import json
import os
import re

from .ontology import ROOT

_TYPES = {
    "object": dict,
    "array": list,
    "string": str,
    "boolean": bool,
    "number": (int, float),
    "integer": int,
    "null": type(None),
}


class ValidationError(ValueError):
    pass


def _resolve(root: dict, ref: str) -> dict:
    if not ref.startswith("#/"):
        raise ValidationError(f"unsupported $ref {ref!r}")
    node = root
    for part in ref[2:].split("/"):
        node = node[part]
    return node


def _type_ok(value, spec) -> bool:
    names = spec if isinstance(spec, list) else [spec]
    for name in names:
        expected = _TYPES[name]
        if name == "boolean":
            if isinstance(value, bool):
                return True
            continue
        if name in ("number", "integer") and isinstance(value, bool):
            continue
        if isinstance(value, expected):
            return True
    return False


def check(instance, schema: dict, root: dict | None = None, path: str = "$") -> list:
    root = root if root is not None else schema
    errors: list = []

    if "$ref" in schema:
        return check(instance, _resolve(root, schema["$ref"]), root, path)
    if "const" in schema and instance != schema["const"]:
        errors.append(f"{path}: expected {schema['const']!r}, got {instance!r}")
    if "enum" in schema and instance not in schema["enum"]:
        errors.append(f"{path}: {instance!r} is not one of {schema['enum']}")
    if "type" in schema and not _type_ok(instance, schema["type"]):
        errors.append(f"{path}: expected type {schema['type']}, got {type(instance).__name__}")
        return errors

    if isinstance(instance, dict):
        for key in schema.get("required", []):
            if key not in instance:
                errors.append(f"{path}: missing required field {key!r}")
        props = schema.get("properties", {})
        if schema.get("additionalProperties") is False:
            for key in instance:
                if key not in props:
                    errors.append(f"{path}: unexpected field {key!r}")
        for key, sub in props.items():
            if key in instance:
                errors.extend(check(instance[key], sub, root, f"{path}.{key}"))

    if isinstance(instance, list):
        if "minItems" in schema and len(instance) < schema["minItems"]:
            errors.append(f"{path}: expected at least {schema['minItems']} items")
        if "items" in schema:
            for idx, item in enumerate(instance):
                errors.extend(check(item, schema["items"], root, f"{path}[{idx}]"))

    if isinstance(instance, str):
        if "minLength" in schema and len(instance) < schema["minLength"]:
            errors.append(f"{path}: shorter than minLength {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], instance):
            errors.append(f"{path}: does not match {schema['pattern']!r}")

    return errors


def check_ontology_version(instance: dict, ontology_version: str) -> list:
    """Hard refusal on mismatch or absence. Not a warning, and not a rescore."""
    claimed = instance.get("ontology_version")
    if not claimed:
        return ["$.ontology_version: absent -- an artifact that does not say "
                "which ontology it was produced under cannot be placed in a corpus"]
    if claimed != ontology_version:
        return [
            f"$.ontology_version: produced under {claimed!r}, engine holds "
            f"{ontology_version!r}. Refused: a version string cannot make an "
            "earlier classification belong to the current ontology. Reclassify "
            "the artifact or exclude it; do not relabel it."
        ]
    return []


def load_schema(name: str, root: str = ROOT) -> dict:
    with open(os.path.join(root, "schemas", name), "r", encoding="utf-8") as handle:
        return json.load(handle)


# -- evidence ---------------------------------------------------------------

_WS = re.compile(r"\s+")


def _norm(text: str) -> str:
    return _WS.sub(" ", text).strip().lower()


def _walk_supported(node, path="$"):
    """Yield every (path, dict) carrying both `support` and `evidence`."""
    if isinstance(node, dict):
        if "support" in node:
            yield path, node
        for key, value in node.items():
            yield from _walk_supported(value, f"{path}.{key}")
    elif isinstance(node, list):
        for idx, item in enumerate(node):
            yield from _walk_supported(item, f"{path}[{idx}]")


def check_evidence(instance: dict, source_text: str) -> list:
    """Downgrade unsupported claims in place; return the list of downgrades."""
    haystack = _norm(source_text)
    downgrades = []
    for path, node in _walk_supported(instance):
        spans = node.get("evidence") or []
        missing = [s for s in spans if _norm(s) and _norm(s) not in haystack]
        if not spans:
            if node.get("support") != "uncertain":
                downgrades.append({"path": path, "reason": "no evidence span", "was": node["support"]})
                node["support"] = "uncertain"
        elif missing:
            if node.get("support") != "uncertain":
                downgrades.append({
                    "path": path,
                    "reason": "evidence span not found in source",
                    "was": node["support"],
                    "spans": missing,
                })
                node["support"] = "uncertain"
    return downgrades


def validate(instance: dict, mode: str, source_text: str, root: str = ROOT, *,
             ontology_version: str) -> dict:
    """``ontology_version`` is keyword-only and required: an artifact cannot be
    admitted without its provenance being checked, and an optional argument is
    one a caller can forget."""
    schema_name = {
        "pole_typing": "pole_classification.json",
        "bridge_typing": "bridge_classification.json",
    }[mode]
    schema = load_schema(schema_name, root)
    errors = check(instance, schema) + check_ontology_version(instance, ontology_version)
    downgrades = check_evidence(instance, source_text) if not errors else []
    return {"mode": mode, "schema": schema_name, "errors": errors, "downgrades": downgrades}
