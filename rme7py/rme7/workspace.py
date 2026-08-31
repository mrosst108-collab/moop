"""The workspace: ports emitted as blanks, and read back.

``placement`` says where a term may go. This module is the interface a model
actually sees -- the six ports rendered as labelled, constrained blanks, and
the filled text parsed back into a ``Realization``.

The interface changes the kind of guarantee on offer. In ``placement`` a
misplacement is REFUSED: hand it a term declaring itself an operator in the
drift of X consuming dW, and it raises. Here a misplacement is
UNREPRESENTABLE: a blank belongs to a port, so filling one cannot express a
signature at all. A model choosing blanks cannot put F in the drift of X
because no blank there will take it. Refusal needs the mistake to be made
first; unrepresentability does not.

The cost from entry 30 survives the round trip unchanged and is not papered
over: a capacity-2 blank recovers its occupants as a set, so a workspace
filled in either order parses to the same realization.
"""

from __future__ import annotations

from .placement import Grammar, Port, Realization, Refused, Term

BLANK = "____"
_SEP = ":"


def _spec(port: Port) -> str:
    return (f"kind={port.kind.name.lower()} "
            f"position={port.position.name.lower()} "
            f"consumes={port.operand.name.lower()} "
            f"capacity={port.capacity}")


def emit(realization: Realization | None = None) -> str:
    """Render the workspace. Every port appears, filled or blank.

    An unfilled port shows its blanks rather than disappearing, which is the
    entry-31 rule at the interface: inactive is a state, not an omission.
    """
    r = realization if realization is not None else Realization()
    lines = []
    for port in r.grammar.ports:
        held = sorted(t.label for t in port.held)
        slots = held + [BLANK] * (port.capacity - len(held))
        lines.append(f"{port.path} [{_spec(port)}] {_SEP} " + " , ".join(slots))
    return "\n".join(lines)


def parse(text: str, name: str = "parsed") -> Realization:
    """Read a filled workspace back.

    A filled blank contributes only a LABEL. The term's signature is taken
    from the port it was written in -- the model does not get to declare one,
    which is exactly why a misplacement cannot be expressed here.
    """
    r = Realization(name)
    by_path = {p.path: p for p in r.grammar.ports}
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if _SEP not in line:
            raise Refused(f"no {_SEP!r} in line: {line!r}")
        head, tail = line.split(_SEP, 1)
        path = head.split("[")[0].strip()
        if path not in by_path:
            raise Refused(f"unknown port: {path!r}. The workspace is fixed; "
                          "a port cannot be introduced by writing one down.")
        if path in seen:
            raise Refused(f"port written twice: {path!r}")
        seen.add(path)
        port = by_path[path]
        for cell in (c.strip() for c in tail.split(",")):
            if not cell or cell == BLANK:
                continue
            r.occupy(Term(cell, port.kind, port.position, port.operand))
    missing = set(by_path) - seen
    if missing:
        raise Refused(f"workspace incomplete, ports dropped: {sorted(missing)}")
    return r


def round_trip(realization: Realization) -> Realization:
    """emit then parse. Equal reports, up to the known collisions."""
    return parse(emit(realization), realization.name)
