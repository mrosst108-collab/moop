"""A strict, dependency-free reader for the subset of YAML this tree uses.

The point is not to be YAML. The point is that the ontology files parse the
same way on every machine, for ever, with nothing installed -- an instrument
whose inputs depend on a floating third-party parser version is not
reproducible.

Supported: block mappings, block lists (including the ``- key: value`` inline
form), flow sequences of scalars, literal block scalars (``|``), ``#``
comments, and the scalar types string / int / float / bool / null.

Everything else is a hard error with a line number. Nothing is guessed at.
"""

from __future__ import annotations

import re

__all__ = ["YamlishError", "load", "load_file"]


class YamlishError(ValueError):
    """Raised for any construct outside the supported subset."""


_KEY_RE = re.compile(r"^([A-Za-z0-9_][A-Za-z0-9_.\-/]*):(?:\s+(.*))?$")
_INT_RE = re.compile(r"^-?\d+$")
_FLOAT_RE = re.compile(r"^-?\d+\.\d+$")


class _Reader:
    def __init__(self, text: str, source: str) -> None:
        self.raw = text.split("\n")
        self.source = source
        self.i = 0

    # -- errors ------------------------------------------------------------

    def err(self, msg: str, lineno: int | None = None):
        ln = (self.i if lineno is None else lineno) + 1
        raise YamlishError(f"{self.source}:{ln}: {msg}")

    # -- lexical helpers ---------------------------------------------------

    def _strip_comment(self, line: str, lineno: int) -> str:
        out: list[str] = []
        quote: str | None = None
        for ch in line:
            if quote is not None:
                if ch == "\\":
                    self.err("backslash escapes are not supported in scalars", lineno)
                out.append(ch)
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
                out.append(ch)
            elif ch == "#" and (not out or out[-1] in " \t"):
                break
            else:
                out.append(ch)
        if quote is not None:
            self.err("unterminated quoted scalar", lineno)
        return "".join(out).rstrip()

    def peek(self):
        """Advance to the next significant line; return (indent, text, lineno)."""
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            line = self._strip_comment(raw, self.i)
            if line.strip() == "":
                self.i += 1
                continue
            indent = len(line) - len(line.lstrip(" "))
            if "\t" in raw[: indent + 1]:
                self.err("tabs are not permitted for indentation", self.i)
            return (indent, line.strip(), self.i)
        return None

    # -- scalars -----------------------------------------------------------

    def _scalar(self, text: str, lineno: int):
        if text == "":
            return None
        if text[0] in "\"'":
            quote = text[0]
            if len(text) < 2 or text[-1] != quote:
                self.err("unterminated quoted scalar", lineno)
            return text[1:-1]
        if text[0] == "[":
            return self._flow_sequence(text, lineno)
        if text[0] == "{":
            self.err("flow mappings are not supported; use a block mapping", lineno)
        if text[0] in "&*":
            self.err("anchors and aliases are not supported", lineno)
        if text in ("true", "false"):
            return text == "true"
        if text in ("null", "~"):
            return None
        if _INT_RE.match(text):
            return int(text)
        if _FLOAT_RE.match(text):
            return float(text)
        return text

    def _flow_sequence(self, text: str, lineno: int) -> list:
        if not text.endswith("]"):
            self.err("unterminated flow sequence", lineno)
        body = text[1:-1].strip()
        if body == "":
            return []
        items: list[str] = []
        cur: list[str] = []
        quote: str | None = None
        for ch in body:
            if quote is not None:
                cur.append(ch)
                if ch == quote:
                    quote = None
            elif ch in "\"'":
                quote = ch
                cur.append(ch)
            elif ch in "[{":
                self.err("nested flow collections are not supported", lineno)
            elif ch == ",":
                items.append("".join(cur).strip())
                cur = []
            else:
                cur.append(ch)
        items.append("".join(cur).strip())
        return [self._scalar(item, lineno) for item in items]

    def _block_scalar(self, parent_indent: int) -> str:
        lines: list[str] = []
        base: int | None = None
        while self.i < len(self.raw):
            raw = self.raw[self.i]
            if raw.strip() == "":
                lines.append("")
                self.i += 1
                continue
            indent = len(raw) - len(raw.lstrip(" "))
            if indent <= parent_indent:
                break
            if base is None:
                base = indent
            if indent < base:
                self.err("block scalar line is less indented than its block", self.i)
            lines.append(raw[base:])
            self.i += 1
        while lines and lines[-1] == "":
            lines.pop()
        return "\n".join(lines) + ("\n" if lines else "")

    # -- structure ---------------------------------------------------------

    def parse_block(self, indent: int):
        p = self.peek()
        if p is None:
            self.err("expected a block, found end of input")
        if p[0] != indent:
            self.err(f"expected a block at indent {indent}, found indent {p[0]}", p[2])
        if p[1] == "-" or p[1].startswith("- "):
            return self.parse_list(indent)
        return self.parse_map(indent)

    def parse_map(self, indent: int) -> dict:
        out: dict = {}
        while True:
            p = self.peek()
            if p is None or p[0] < indent:
                break
            ind, content, lineno = p
            if ind > indent:
                self.err("unexpected indentation", lineno)
            if content == "-" or content.startswith("- "):
                self.err("a list item cannot appear at the indent of a mapping key", lineno)
            m = _KEY_RE.match(content)
            if not m:
                self.err(f"expected 'key: value', found {content!r}", lineno)
            key, rest = m.group(1), m.group(2)
            if key in out:
                self.err(f"duplicate key {key!r}", lineno)
            self.i = lineno + 1
            if rest is None or rest == "":
                nxt = self.peek()
                out[key] = self.parse_block(nxt[0]) if nxt is not None and nxt[0] > indent else None
            elif rest == "|":
                out[key] = self._block_scalar(indent)
            elif rest == ">":
                self.err("folded block scalars ('>') are not supported; use '|'", lineno)
            else:
                out[key] = self._scalar(rest, lineno)
        return out

    def parse_list(self, indent: int) -> list:
        out: list = []
        while True:
            p = self.peek()
            if p is None or p[0] < indent:
                break
            ind, content, lineno = p
            if ind > indent:
                self.err("unexpected indentation", lineno)
            if not (content == "-" or content.startswith("- ")):
                break
            item = content[2:].strip() if content.startswith("- ") else ""
            if item == "":
                self.i = lineno + 1
                nxt = self.peek()
                out.append(self.parse_block(nxt[0]) if nxt is not None and nxt[0] > indent else None)
            elif _KEY_RE.match(item):
                child = indent + 2
                self.raw[lineno] = " " * child + item
                self.i = lineno
                out.append(self.parse_map(child))
            else:
                self.i = lineno + 1
                out.append(self._scalar(item, lineno))
        return out


def load(text: str, source: str = "<string>"):
    reader = _Reader(text, source)
    first = reader.peek()
    if first is None:
        return None
    if first[0] != 0:
        reader.err("the document must start at indent 0", first[2])
    value = reader.parse_block(0)
    trailing = reader.peek()
    if trailing is not None:
        reader.err(f"unparsed trailing content: {trailing[1]!r}", trailing[2])
    return value


def load_file(path):
    with open(path, "r", encoding="utf-8") as handle:
        return load(handle.read(), source=str(path))
