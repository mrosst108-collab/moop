"""What a kept entry is charged for (VII.5).

A run keeps an entry for each thing it lets go of.  The charge for an entry is the number of
bits that tell apart what the run could have let go of there, given what remains:

  a clause choice    nothing where the output shows which clause ran; otherwise the bits that
                     tell apart the clauses whose right side the output matches
  a dropped value    by its declared type: a word its width, a value of a type with several
                     constructors the bits that tell apart the constructors it may still have,
                     plus its fields; nothing where it can still be computed from what remains
  a decision         its bit, and which of the answers installed for `Decide` (or the world)
                     settled it

Both backends charge by this definition (cgen.py emits the same arithmetic), and
tests/generated_04.py computes it a third time, from its own model of each program.
"""
from .forms import Form, Arr, Inst, INT_TYPES, MAYBE, weight


def clog2(n):
    """The bits that tell n things apart: 0 for one thing, else the ceiling of log2 n."""
    return 0 if n <= 1 else (n - 1).bit_length()


def dropped_bits(m, v, t, top=None):
    """The charge for a dropped value `v` of declared type `t`.  `top` is how many constructors
    the value itself may still have, where the checker has shown fewer than its type declares."""
    if t == 'Lit':
        t = 'I64'
    if t == 'Trit':
        return 2                                  # three values: two bits, whichever it holds
    if t == 'Bool':
        return 1
    if t == 'F64':
        return 64
    if isinstance(t, str) and t in INT_TYPES:
        return INT_TYPES[t][0]                    # a word: its declared width
    if t == 'Text' and isinstance(v, str):
        return 64 + 8 * len(v.encode())           # an array of bytes: its length, and its bytes
    if isinstance(t, tuple):
        if t[0] == 'Tuple' and isinstance(v, tuple) and len(v) == len(t[1]):
            return sum(dropped_bits(m, x, tx) for x, tx in zip(v, t[1]))
        if t[0] == 'Array' and isinstance(v, Arr):
            return 64 + sum(dropped_bits(m, x, t[1]) for x in v.data)
        if t[0] == 'Data' and t[1] != 'Code' and t[1] in m.types and isinstance(v, Form) \
                and v.tag in m.types[t[1]].ctors:
            ctors = m.types[t[1]].ctors
            fields = ctors[v.tag]
            if len(fields) == len(v.kids):
                return clog2(len(ctors) if top is None else top) + \
                    sum(dropped_bits(m, x, ft) for x, (_, ft) in zip(v.kids, fields))
        if t[0] == 'Inst' and isinstance(v, Inst) and t[1] in m.answers and v.answer == t[1]:
            a = m.answers[t[1]]
            ps = v.params if isinstance(v.params, tuple) else (v.params,)
            if len(ps) == len(a.params):
                return sum(dropped_bits(m, x, pt) for x, (_, pt) in zip(ps, a.params)) + \
                    dropped_bits(m, v.state, a.takes)
    # whatever the declaration leaves open (`Any`, code): the value says what it is, and a
    # form or an instance is charged 16 bits for that
    return weight(v)


def decision_bits(installed):
    """The charge for a decision: its bit, and which of the `installed` answers for `Decide`,
    or the world, settled it."""
    return 1 + clog2(installed + 1)


def entry_bits(e, dropped=None):
    """The charge for one entry.  `dropped` is the charge the run worked out when it kept a
    dropped value; without it the value is charged as its declaration left it open."""
    if e.tag == 'Dropped':
        return weight(e.kids[2]) if dropped is None else dropped
    if e.tag == 'Chose':
        return clog2(e.kids[2].v)
    # Decided, where the run's own charge is not at hand: by the answers the entry says were asked
    return decision_bits(e.kids[2].v)
