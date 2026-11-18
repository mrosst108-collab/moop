"""Forms: the one representation for code, data, patterns and journal entries.

A form is an atom (Word, float, bool, str) or a tagged node with ordered children.
Runtime tuples are Python tuples; arrays are owned buffers (Arr); answer
instances are Inst.  Identity is the hash of the canonical encoding.
"""
import hashlib
import math

INT_TYPES = {
    'I8': (8, True), 'I16': (16, True), 'I32': (32, True), 'I64': (64, True),
    'U8': (8, False), 'U16': (16, False), 'U32': (32, False), 'U64': (64, False),
    'Bit': (1, False),
}
SCALAR_TYPES = set(INT_TYPES) | {'F64', 'Bool', 'Text'}


class Fault(Exception):
    """A defined runtime refusal (R8): the operation is refused, never undefined."""


class _Maybe:
    """The third truth value: not yet decided."""
    __slots__ = ()
    _inst = None

    def __new__(cls):
        if cls._inst is None:
            cls._inst = super().__new__(cls)
        return cls._inst

    def __repr__(self):
        return 'maybe'

    def __reduce__(self):
        return (_Maybe, ())


MAYBE = _Maybe()


class Word:
    """A fixed-width integer with defined wrap-around semantics.

    A literal is flexible: it adopts the type of the word it meets.
    """
    __slots__ = ('v', 'ty', 'flex')

    def __init__(self, v, ty='I64', flex=False):
        bits, signed = INT_TYPES[ty]
        v &= (1 << bits) - 1
        if signed and v >= 1 << (bits - 1):
            v -= 1 << bits
        self.v, self.ty, self.flex = v, ty, flex

    def to(self, ty):
        return Word(self.v, ty)

    def __eq__(self, other):
        if not isinstance(other, Word):
            return False
        if self.flex and not other.flex:
            return Word(self.v, other.ty).v == other.v
        if other.flex and not self.flex:
            return Word(other.v, self.ty).v == self.v
        return self.v == other.v and (self.ty == other.ty or self.flex or other.flex)

    def __hash__(self):
        return hash(self.v)

    def __repr__(self):
        return f'Word({self.v},{self.ty})'


class Form:
    """A tagged node. `line` is source position metadata, not part of identity."""
    __slots__ = ('tag', 'kids', 'line')

    def __init__(self, tag, kids=(), line=None):
        self.tag, self.kids, self.line = tag, tuple(kids), line

    def __eq__(self, other):
        return isinstance(other, Form) and self.tag == other.tag and self.kids == other.kids

    def __hash__(self):
        return hash((self.tag, self.kids))

    def __repr__(self):
        return f'{self.tag}{self.kids!r}' if self.kids else self.tag


class Arr:
    """An owned array.  Linear use makes in-place update unobservable."""
    __slots__ = ('ty', 'data')

    def __init__(self, ty, data):
        self.ty, self.data = ty, data

    def __eq__(self, other):
        return isinstance(other, Arr) and self.ty == other.ty and self.data == other.data

    def __hash__(self):
        return hash((self.ty, len(self.data)))

    def __repr__(self):
        return f'Arr({self.ty},{self.data!r})'


class Inst:
    """An answer instance: an answer with its parameters and current state."""
    __slots__ = ('answer', 'params', 'state')

    def __init__(self, answer, params, state):
        self.answer, self.params, self.state = answer, tuple(params), state

    def __eq__(self, other):
        return (isinstance(other, Inst) and self.answer == other.answer
                and self.params == other.params and self.state == other.state)

    def __hash__(self):
        return hash((self.answer, self.params))

    def __repr__(self):
        return f'Inst({self.answer},{self.params!r},{self.state!r})'


def encode(v):
    """Canonical encoding used for identity (hash) and for weighing losses."""
    if isinstance(v, Word):
        return f'{v.ty}:{v.v}'
    if isinstance(v, bool):
        return 'Bool:' + ('true' if v else 'false')
    if v is MAYBE:
        return 'Trit:maybe'
    if isinstance(v, float):
        return 'F64:' + v.hex()
    if isinstance(v, str):
        return 'Text:' + repr(v)
    if isinstance(v, tuple):
        return '(' + ','.join(encode(x) for x in v) + ')'
    if isinstance(v, Form):
        return v.tag + '(' + ','.join(encode(x) for x in v.kids) + ')'
    if isinstance(v, Arr):
        return f'Array[{v.ty}](' + ','.join(encode(x) for x in v.data) + ')'
    if isinstance(v, Inst):
        return f'Inst:{v.answer}({encode(v.params)};{encode(v.state)})'
    if v is None:
        return 'None'
    raise TypeError(f'cannot encode {v!r}')


def equal(a, b, same):
    """Structural equality.  With `same`, floats compare on their canonical form, as `was`,
    patterns and take-backs need: every NaN is the one NaN, and -0.0 differs from 0.0.
    Without it they compare as IEEE 754 says, as the `=` operator does."""
    if isinstance(a, float) and isinstance(b, float):
        if same:
            return (a != a and b != b) or (a == b and math.copysign(1.0, a) == math.copysign(1.0, b))
        return a == b
    if isinstance(a, tuple) and isinstance(b, tuple):
        return len(a) == len(b) and all(equal(x, y, same) for x, y in zip(a, b))
    if isinstance(a, Form) and isinstance(b, Form):
        return a.tag == b.tag and equal(a.kids, b.kids, same)
    if isinstance(a, Arr) and isinstance(b, Arr):
        return a.ty == b.ty and equal(tuple(a.data), tuple(b.data), same)
    if isinstance(a, Inst) and isinstance(b, Inst):
        return a.answer == b.answer and equal(a.params, b.params, same) and equal(a.state, b.state, same)
    if isinstance(a, bool) != isinstance(b, bool):
        return False
    return a == b


def identity(v):
    """A form's identity: the hash of its canonical encoding (16 hex digits)."""
    return hashlib.sha256(encode(v).encode()).hexdigest()[:16]


def weight(v):
    """Bits a value occupies when it is lost (used for epsilon)."""
    if isinstance(v, Word):
        return INT_TYPES[v.ty][0]
    if isinstance(v, bool):
        return 1
    if v is MAYBE:
        return 2
    if isinstance(v, float):
        return 64
    if isinstance(v, str):
        return 8 * len(v.encode())
    if isinstance(v, tuple):
        return sum(weight(x) for x in v)
    if isinstance(v, Form):
        return 16 + sum(weight(x) for x in v.kids)
    if isinstance(v, Arr):
        return 64 + sum(weight(x) for x in v.data)
    if isinstance(v, Inst):
        return 16 + weight(v.params) + weight(v.state)
    return 0


def show(v):
    """Render a runtime value in Selvage's own literal syntax."""
    if v is MAYBE:
        return 'maybe'
    if isinstance(v, Word):
        return str(v.v)
    if isinstance(v, bool):
        return 'true' if v else 'false'
    if isinstance(v, float):
        r = repr(v)
        return r
    if isinstance(v, str):
        return v
    if isinstance(v, tuple):
        if len(v) == 1:
            return '(' + show(v[0]) + ',)'
        return '(' + ', '.join(show_inner(x) for x in v) + ')'
    if isinstance(v, Form):
        from .printer import is_code_form, code_text, STEP_TAGS, program_text
        from .declared import is_declared, undeclared
        if is_declared(v):
            try:
                d = undeclared(v)
                return program_text(d).rstrip('\n') if d.tag == 'Program' else code_text(d)
            except Exception:
                pass                      # not put together as a declaration: shown as the form it is
        if is_code_form(v) or v.tag in STEP_TAGS or v.tag in ('Block', 'Clause', 'LossyClause', 'RuleDecl', 'AnswerDecl'):
            return code_text(v)
        if not v.kids:
            return v.tag
        return v.tag + '(' + ', '.join(show_inner(x) for x in v.kids) + ')'
    if isinstance(v, Arr):
        return '[' + ', '.join(show_inner(x) for x in v.data) + ']'
    if isinstance(v, Inst):
        p = '(' + ', '.join(show_inner(x) for x in v.params) + ')' if v.params else ''
        return f'{v.answer}{p} from {show_inner(v.state)}'
    if v is None:
        return '()'
    return repr(v)


def show_inner(v):
    if isinstance(v, str):
        return repr(v).replace("'", '"') if '"' not in v else repr(v)
    return show(v)
