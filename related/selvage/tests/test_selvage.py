"""Conformance suite for the Selvage build.  Run: python3 -m unittest discover -s tests"""
import io
import itertools
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

import selvage  # noqa: E402
from selvage import load, CheckError  # noqa: E402
from selvage.forms import Word, Arr, Inst, Form, Fault, MAYBE, identity  # noqa: E402
from selvage.deciders import fixed, refuse  # noqa: E402
from selvage.interp import Interp  # noqa: E402
from selvage.checker import definition_of  # noqa: E402
from selvage.invert import invert  # noqa: E402
from selvage.codeid import code_identity, identities, rule_identities  # noqa: E402
from selvage.extent import extent  # noqa: E402
from selvage.parser import parse  # noqa: E402
from selvage.printer import program_text  # noqa: E402

EX = os.path.join(ROOT, 'examples')
PROGS = os.path.join(ROOT, 'tests', 'programs')
HAVE_CLANG = shutil.which('clang') is not None


def src(name, d=EX):
    with open(os.path.join(d, name)) as f:
        return f.read()


def by_name(text):
    """A printed journal with each entry's code identity left out, so a test can name entries by
    where they came from.  The identities themselves are tested in TestJournalIdentity."""
    import re
    return re.sub(r'\b(Dropped|Chose|Decided)\("[0-9a-f]{16}", ', r'\1(', text)


def run_interp(text):
    import io
    m, _, _ = load(text)
    out = io.StringIO()
    it = Interp(m, out)
    it.run_main()
    return out.getvalue(), it


def run_refused(text):
    """Run a program that is expected to be refused in the run; the refusal's text."""
    m = load(text)[0]
    it = Interp(m, io.StringIO())
    try:
        it.run_main()
    except Fault as e:
        return str(e)
    return ''


def cli(*args, env=None):
    e = dict(os.environ, PYTHONPATH=ROOT)
    if env:
        e.update(env)
    return subprocess.run([sys.executable, '-m', 'selvage', *args], capture_output=True, text=True, env=e)


def build_and_run(path, tmp):
    exe = os.path.join(tmp, os.path.basename(path).replace('.selv', ''))
    r = cli('build', path, '-o', exe)
    if r.returncode != 0:
        raise AssertionError(r.stderr)
    res = subprocess.run([exe], capture_output=True, text=True, env=dict(os.environ, SELVAGE_STATS='1'))
    return res


W = lambda v, t='I64': Word(v, t)  # noqa: E731
F_ = Form


class TestSurface(unittest.TestCase):
    """The printer is canonical: parse(print(f)) = f and print is idempotent."""

    def test_round_trip_examples(self):
        files = [os.path.join(EX, f) for f in os.listdir(EX) if f.endswith('.selv')]
        files.append(selvage.PRELUDE_PATH)
        files += [os.path.join(PROGS, f) for f in os.listdir(PROGS) if f.endswith('.selv')]
        for path in files:
            with open(path) as f:
                p = parse(f.read())
            text = program_text(p)
            self.assertEqual(parse(text), p, path)
            self.assertEqual(program_text(parse(text)), text, path)

    def test_layout_is_not_part_of_identity(self):
        a = parse('rule f takes I64 returns I64\n    x <-> x\n')
        b = parse('rule f   takes I64   returns I64\n        x   <->   x    # comment\n')
        self.assertEqual(identity(a), identity(b))

    def test_quoted_code_is_data(self):
        out, _ = run_interp(src('derivative.selv'))
        self.assertEqual(out.splitlines(), ['x * x + 3 * x', '1 * x + x * 1 + (0 * x + 3 * 1)',
                                            '10', '7', 'true', '0 * y + x * 1 + (0 * x + 3 * 0)'])


class TestCCNOT(unittest.TestCase):
    """ccnot is the base rule; the other gates and the update words are built on it."""

    def setUp(self):
        self.m, _, _ = load('rule by_update takes (Bit, Bit, Bit) returns (Bit, Bit, Bit)\n'
                            '    (a, b, c) <-> (a, b, c) where\n'
                            '        add a * b to c\n'
                            'rule by_xor takes (Bit, Bit) returns (Bit, Bit)\n'
                            '    (a, c) <-> (a, c) where\n'
                            '        add a to c\n')
        self.it = Interp(self.m)

    def test_prelude_gates_are_bijections(self):
        for g in ('ccnot', 'cnot', 'toggle', 'ripple_add', 'exchange', 'fanout'):
            self.assertEqual(self.m.rules[g].cls, 'bijection', g)

    def test_ccnot_truth_table_and_self_inverse(self):
        r = self.m.rules['ccnot']
        for a, b, c in itertools.product((0, 1), repeat=3):
            x = (W(a, 'Bit'), W(b, 'Bit'), W(c, 'Bit'))
            y = self.it.forward(r, (), x)
            self.assertEqual(tuple(v.v for v in y), (a, b, c ^ (a & b)))
            self.assertEqual(self.it.forward(r, (), y), x)
            self.assertEqual(self.it.backward(r, (), y, 'undo'), x)

    def test_update_word_on_bits_is_ccnot(self):
        u, g = self.m.rules['by_update'], self.m.rules['ccnot']
        self.assertEqual(u.cls, 'bijection')
        for bits in itertools.product((0, 1), repeat=3):
            x = tuple(W(v, 'Bit') for v in bits)
            self.assertEqual(self.it.forward(u, (), x), self.it.forward(g, (), x))

    def test_update_on_bits_is_cnot(self):
        u, g = self.m.rules['by_xor'], self.m.rules['cnot']
        for bits in itertools.product((0, 1), repeat=2):
            x = tuple(W(v, 'Bit') for v in bits)
            self.assertEqual(self.it.forward(u, (), x), self.it.forward(g, (), x))

    def test_cnot_and_toggle(self):
        cn, inv = self.m.rules['cnot'], self.m.rules['toggle']
        for a, c in itertools.product((0, 1), repeat=2):
            y = self.it.forward(cn, (), (W(a, 'Bit'), W(c, 'Bit')))
            self.assertEqual((y[0].v, y[1].v), (a, a ^ c))
        self.assertEqual(self.it.forward(inv, (), W(0, 'Bit')).v, 1)

    def test_ripple_adder_agrees_with_machine_addition(self):
        m, _, _ = load(src('adder.selv'))
        it = Interp(m)
        self.assertEqual(it.call_expr_rule(m.rules['mismatches'], (W(15),)).v, 0)
        r = m.rules['ripple_add']
        rng = random.Random(7)
        for _ in range(40):
            n = rng.choice([4, 8, 16])
            x, y = rng.getrandbits(n), rng.getrandbits(n)
            a = Arr('Bit', [W((x >> i) & 1, 'Bit') for i in range(n)])
            b = Arr('Bit', [W((y >> i) & 1, 'Bit') for i in range(n)])
            a2, s, c = it.forward(r, (), (a, b, W(0, 'Bit')))
            total = sum(bit.v << i for i, bit in enumerate(s.data))
            self.assertEqual(total, (x + y) % (1 << n))
            a3, b3, c3 = it.backward(r, (), (a2, s, c), 'undo')
            self.assertEqual(sum(bit.v << i for i, bit in enumerate(b3.data)), y)


class TestChecker(unittest.TestCase):
    """R2–R4, R6 and R8 refusals."""

    REFUSED = {
        'rule f takes (I64, I64) returns I64\n    (a, b) <-> a\n': 'is lost',
        'rule f takes I64 returns I64\n    x <-> x where\n        add x to x\n': 'R4',
        ('rule f takes (I64, I64) returns I64\n    (a, b) => a where\n        discard b\n'
         'rule main uses System\n    x is undo f(3)\n'): 'needs a certified rule',
        ('rule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n        k is a * 2\n'
         '        add 1 to a\n        add k to b\n'): 'cannot be uncomputed',
        'rule f(k: I64) takes I64 returns I64\n    x <-> x where\n        add 1 to k\n': 'parameter',
        'rule main\n    output 3\n': 'uses Output',
        ('rule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n        if a > 0\n'
         '            add b to a\n'): 'condition',
        'rule f(i: I64) takes Array(U64) returns Array(U64)\n    a <-> a where\n        add a[i] to a[i]\n': 'R4',
        'rule f(a: U8, b: I64) returns U8\n    a + b\n': 'type mismatch',
        ('rule f takes I64 returns I64\n    x <-> x where\n        repeat while x > 0\n'
         '            subtract 1 from x\n'): 'exit assertion',
        'rule f takes (I64, I64) returns (I64, I64, I64)\n    (a, b) <-> (a, b, a)\n': 'twice',
        'rule length(x: I64) returns I64\n    x\n': 'built-in',
        ('rule f takes Array(I64) returns Array(I64)\n    a <-> a where\n        repeat with i from 0 to length(a) - 1\n'
         '            discard a\n'): 'same names live',
    }

    def test_refusals(self):
        for text, needle in self.REFUSED.items():
            with self.assertRaises(CheckError, msg=text) as cm:
                load(text)
            self.assertIn(needle, str(cm.exception), text)

    LOSSY = 'rule f takes (I64, I64) returns I64\n    (a, b) {} a where\n        discard b\n'
    COUNTER = ('request Counter\n    bump(n: I64) returns I64\n    reset() returns ()\n'
               'answer Count for Counter takes I64\n    (bump(n), c) <-> (n, c) where\n        add n to c\n')

    def refused(self, text, needle):
        with self.assertRaises(CheckError, msg=text) as cm:
            load(text)
        self.assertIn(needle, str(cm.exception), text)

    def test_the_arrow_states_the_certificate(self):
        self.assertEqual(load(self.LOSSY.format('=>'))[0].rules['f'].cls, 'lossy')
        self.refused(self.LOSSY.format('<->'), 'a lossy rule writes `=>`')
        self.refused('rule g takes I64 returns I64\n    x => x where\n        add 1 to x\n',
                     'a certified rule writes `<->`')
        self.refused('rule g takes Bool returns Bool\n    true <-> false\n    false => true\n', 'same arrow')
        self.refused('rule f takes (I64, I64) returns I64 uses Discard\n    (a, b) => a where\n        discard b\n',
                     'Discard is not a request group')
        # the class propagates through calls, and with it the arrow a caller needs
        self.refused(self.LOSSY.format('=>') + 'rule g takes (I64, I64) returns I64\n'
                     '    p <-> r where\n        r is f(p)\n', 'a lossy rule writes `=>`')
        # in an answer each request's rule carries its own arrow
        m = load(self.COUNTER.replace('answer Count', 'answer Both') +
                 '    (reset(), c) => ((), c) where\n        set c to 0\n')[0]
        self.assertEqual({op: r.cls for op, r in m.answers['Both'].ops.items()},
                         {'bump': 'bijection', 'reset': 'lossy'})
        self.refused(self.COUNTER + '    (reset(), c) <-> ((), c) where\n        set c to 0\n',
                     'Count.reset is lossy')

    def test_inversion_preserves_the_arrow(self):
        from selvage.checker import definition_of
        from selvage.invert import invert
        from selvage.printer import code_text
        m = load(self.LOSSY.format('=>') + 'rule g takes I64 returns I64\n    x <-> x where\n        add 1 to x\n')[0]
        for name, arrow, other in (('f', '=>', '<->'), ('g', '<->', '=>')):
            code = definition_of(m, m.rules[name])
            for c in (code, invert(code), invert(invert(code))):
                text = code_text(c)
                self.assertIn(f' {arrow} ', text)
                self.assertNotIn(f' {other} ', text)
            self.assertEqual(invert(invert(code)), code)
        self.assertEqual(m.rules['f'].inverse.cls, 'lossy')

    def test_functions_and_procedures_are_told_apart_by_the_row(self):
        m = load(self.LOSSY.format('=>') + 'rule double(x: I64) returns I64\n    x * 2\n'
                 'rule drop uses System\n    f((1, 2))\n')[0]
        self.assertEqual((m.rules['double'].cls, m.rules['drop'].cls), ('function', 'procedure'))
        # reaching keep: a lossy rule, a lossy request rule (sent or installed), a world reply
        self.refused(self.LOSSY.format('=>') + 'rule drop\n    f((1, 2))\n', 'declare `uses System`')
        both = self.COUNTER.replace('answer Count', 'answer Both') + \
            '    (reset(), c) => ((), c) where\n        set c to 0\n'
        self.refused(both + 'rule z\n    b is Both from 3\n    b -> reset()\n', 'declare `uses System`')
        self.refused(both + 'rule w uses Counter\n    ask bump(1)\nrule z\n    w() with Both from 3\n',
                     'declare `uses System`')
        self.refused('rule t(x: Trit) returns Bool uses Decide\n    decide x\n', 'declare `uses System`')
        # not by the word `decide`: a crisp condition never leaves the program
        m = load('rule t(x: I64) returns Bool\n    decide x > 3\n')[0]
        self.assertEqual(m.rules['t'].cls, 'function')
        # a certified message, and an answer whose rules are all certified, reach nothing
        m = load(self.COUNTER + 'rule z returns I64\n    c is Count from 3\n    c -> bump(2)\n')[0]
        self.assertEqual(m.rules['z'].cls, 'function')
        # a step calls functions only: a procedure's result is not recomputable from its parameters
        self.refused('rule p(x: I64) returns I64 uses Output\n    output x\n    x\n'
                     'rule g takes I64 returns I64\n    a <-> a where\n        add p(1) to a\n', 'is a procedure')

    def test_derivation_is_for_records_and_delegation_for_answers(self):
        from selvage.lexer import SyntaxFault
        with self.assertRaises(SyntaxFault) as cm:
            load(self.COUNTER + 'answer More <- Count\n    (reset(), c) => ((), c) where\n        set c to 0\n')
        self.assertIn('`<-` derives record types', str(cm.exception))
        load('type Point(x: I64, y: I64)\ntype Pixel(color: U8) <- Point\n')
        # exactly one answering component delegates; several are refused; none answers nothing
        m = load(self.COUNTER + 'answer One for Counter takes (I64, Count)\n')[0]
        self.assertEqual(m.answers['One'].delegates, {'bump': ((1,), 'Count')})
        self.assertFalse(m.answers_op('One', 'reset'))
        self.refused(self.COUNTER + 'answer Two for Counter takes (Count, Count)\n', 'Two must take bump itself')
        load(self.COUNTER + 'answer Two for Counter takes (Count, Count)\n'
             '    (bump(n), s) <-> (n, s)\n')
        send = 'rule r takes One returns ((), One)\n    s <-> (v, s) where\n        v is s -> reset()\n'
        self.refused(self.COUNTER + 'answer One for Counter takes (I64, Count)\n' + send, 'One does not answer reset')
        self.refused('request G\n    g() returns ()\nanswer Loop for G takes Loop\n', 'holds an instance of itself')
        self.refused(self.COUNTER + 'answer Odd for Counter takes I64\n    (history(), c) <-> ((), c)\n',
                     'with a request of Counter')     # a clause answers a request of a declared group

    def test_r6_rows_contain_what_a_rule_reaches(self):
        self.refused('rule main\n    output 3\n', 'declare `uses Output`')
        self.refused('rule a uses Output\n    output 1\nrule b\n    a()\n', 'b calls a, which uses Output')
        self.refused(self.COUNTER + 'rule a returns I64\n    ask bump(1)\n', 'declare `uses Counter`')
        self.refused('rule g takes Trit returns (Trit, Bool)\n    t => (t, d) where\n        d is decide t\n',
                     'declare `uses Decide`')
        self.refused('rule f returns I64 uses Nothing\n    1\n', 'unknown request group Nothing')
        # an installed answer takes the requests it answers; one it does not answer continues
        # outward, so its group stays in the row
        asks = self.COUNTER + 'rule b returns {} {}\n    (v, c) is (ask {}) with Count from 0\n    v\n'
        self.assertEqual(load(asks.format('I64', '', 'bump(1)'))[0].rules['b'].cls, 'function')
        self.refused(asks.format('()', '', 'reset()'), 'declare `uses Counter`')
        load(asks.format('()', 'uses Counter', 'reset()'))
        # a called rule's group is taken only when every request of the group is answered
        call = self.COUNTER + ('rule a returns I64 uses Counter\n    ask bump(1)\n'
                               'rule b returns I64 {}\n    (v, c) is a() with Count from 0\n    v\n')
        self.refused(call.format(''), 'b calls a, which uses Counter')
        load(call.format('uses Counter'))
        one = ('request One\n    one() returns I64\nanswer Uno for One takes I64\n'
               '    (one(), c) <-> (r, c) where\n        r is c\n'
               'rule a returns I64 uses One\n    ask one()\n'
               'rule b returns I64\n    (v, u) is a() with Uno from 4\n    v\n')
        m = load(one)[0]
        self.assertEqual((m.rules['a'].cls, m.rules['b'].cls), ('procedure', 'function'))
        self.assertEqual(Interp(m).call_expr_rule(m.rules['b'], ()), W(4))

    def test_any_is_confined_to_the_prelude(self):
        for text in ('type Box\n    Box(inside: Any)\n', 'rule f(x: Any) returns I64\n    1\n',
                     'request G\n    put(x: Any) returns ()\n', 'rule f takes Any returns Any\n    x <-> x\n',
                     'request G\n    get() returns I64\nanswer A for G takes Any\n    (get(), s) <-> (1, s)\n',
                     'rule f returns Array(Any)\n    array(Any, 3)\n'):
            self.refused(text, '`Any` belongs to the prelude')
        m = load('')[0]   # the prelude writes it for the journal's entries, and Code holds forms
        self.assertEqual(m.types['Journal'].ctors['Kept'][0], ('entry', 'Any'))
        self.assertEqual(dict(m.types['Code'].ctors['Literal'])['value'], 'Any')

    def test_classification(self):
        expect = {
            'shapes.selv': {'flip': 'bijection', 'split': 'bijection', 'small': 'partial', 'magnitude': 'lossy'},
            'orbit.selv': {'orbit': 'bijection', 'damped_orbit': 'lossy'},
            'arrays.selv': {'prefix_sum': 'bijection', 'reverse': 'bijection', 'count_above': 'bijection'},
            'messages.selv': {'pay': 'bijection', 'walk': 'lossy'},
            'derivative.selv': {'derivative': 'lossy'},
            'adder.selv': {'half_adder': 'bijection', 'ripple_add': 'bijection'},
        }
        for f, rules in expect.items():
            m, _, _ = load(src(f))
            for name, cls in rules.items():
                self.assertEqual(m.rules[name].cls, cls, f'{f}:{name}')
        m, _, _ = load(src('messages.selv'))
        # one rule per request: Ledger is total over its requests and states
        self.assertEqual(m.answers['Ledger'].cls, 'bijection')
        self.assertEqual(m.answers['Replay'].cls, 'lossy')

    def test_runtime_alias_check(self):
        m, _, _ = load('rule f(i: I64, j: I64) takes Array(I64) returns Array(I64)\n'
                       '    a <-> a where\n        add a[j] to a[i]\n')
        it = Interp(m)
        a = Arr('I64', [W(1), W(2)])
        self.assertEqual(it.forward(m.rules['f'], (W(0), W(1)), a).data[0].v, 3)
        with self.assertRaises(Fault):
            it.forward(m.rules['f'], (W(1), W(1)), Arr('I64', [W(1), W(2)]))


class TestReversibility(unittest.TestCase):
    """undo for certified rules; rewind for every rule, through the journal."""

    def test_undo_round_trips(self):
        m, _, _ = load(src('orbit.selv'))
        it = Interp(m)
        r = m.rules['orbit']
        rng = random.Random(1)
        for _ in range(20):
            k, n = W(rng.randint(1, 40)), W(rng.randint(0, 200))
            x = Form('Phase', (W(rng.randint(-10**6, 10**6)), W(rng.randint(-10**4, 10**4))))
            y = it.forward(r, (k, n), x)
            self.assertEqual(it.backward(r, (k, n), y, 'undo'), x)
        self.assertEqual(it.journal, [])

    def test_undo_refuses_values_outside_the_image(self):
        m, _, _ = load(src('shapes.selv'))
        it = Interp(m)
        with self.assertRaises(Fault):
            it.backward(m.rules['small'], (), W(99), 'undo')

    def check_rewind(self, it, rule, params, value):
        before = identity(value)
        n0 = len(it.journal)
        out = it.forward(rule, params, value)
        held = it.journal_bits()
        back = it.backward(rule, params, out, 'rewind')
        self.assertEqual(identity(back), before)
        self.assertEqual(len(it.journal), n0)
        return held

    def test_rewind_lossy_rules(self):
        m, _, _ = load(src('orbit.selv'))
        it = Interp(m)
        held = self.check_rewind(it, m.rules['damped_orbit'], (W(10), W(50)), Form('Phase', (W(12345), W(-77))))
        self.assertEqual(held, 50 * 64)
        m, _, _ = load(src('shapes.selv'))
        it = Interp(m)
        for v in (Form('Positive', (W(3),)), Form('Negative', (W(3),)), Form('Zero', ())):
            self.check_rewind(it, m.rules['magnitude'], (), v)
        m, _, _ = load(src('derivative.selv'))
        it = Interp(m)
        code = parse('rule main\n    x * x * x + 2 * x + 7\n').kids[0].kids[5].kids[0].kids[0]
        self.check_rewind(it, m.rules['derivative'], ('x',), code)
        self.check_rewind(it, m.rules['derivative'], ('q',), code)

    def test_rewind_through_requests_restores_the_answer(self):
        m, _, _ = load(src('messages.selv'))
        it = Interp(m)
        path = Arr('F64', [0.5, -1.25, 2.0, 3.5])
        cell = [Inst('Replay', (path,), W(0))]
        it.handlers.append(cell)
        self.check_rewind(it, m.rules['walk'], (W(4),), 0.125)
        self.assertEqual(cell[0].state, W(0))

    def test_undo_a_message(self):
        out, _ = run_interp(src('messages.selv'))
        lines = out.splitlines()
        self.assertEqual(lines[:5], ['Deposited(50)', 'Ledger from 150', 'Withdrew(30)',
                                     'Ledger from 120', 'Ledger from 150'])

    def test_epsilon_counts_pruned_bits(self):
        m, _, _ = load(src('orbit.selv'))
        it = Interp(m)
        it.forward(m.rules['damped_orbit'], (W(10), W(30)), Form('Phase', (W(1000), W(5))))
        self.assertEqual(it.journal_bits(), 30 * 64)
        it.commit()
        self.assertEqual((it.epsilon, it.journal), (30 * 64, []))
        with self.assertRaises(Fault):   # nothing left to rewind past a commit
            it.rewind(m.rules['damped_orbit'], (W(10), W(30)), Form('Phase', (W(1000), W(5))))


class TestPrograms(unittest.TestCase):
    EXPECTED = {
        'gates.selv': ['(1, 1, 1)', '(1, 1)', '(0, 1, 1)', '(1, 1, 0)', '(0, 0, 1, 0, 0)', '(0, 1, 1, 0, 0)',
                       '(0, 1, 1, 0, 0)', '(1, 1, 0, 1, 1)'],
        'shapes.selv': ['Negative(5)', 'Positive(5)', 'Pixel(3, 4, 200)', 'Point(3, 4)', 'Pixel(3, 4, 200)',
                        '11', '0', '7'],
        'orbit.selv': ['Phase(72388, -6879)', 'Phase(100000, 0)', 'true', 'Phase(-41076, 2337)'],
        'arrays.selv': ['[1, 3, 6, 10, 15, 21, 28, 36]', '[1, 2, 3, 4, 5, 6, 7, 8]',
                        '[-10, -9, -6, -1, 6, 15, 26]', '[26, 15, 6, -1, -6, -9, -10]', '3',
                        '([-10, -9, -6, -1, 6, 15, 26], 0)'],
    }

    def test_interpreter_outputs(self):
        for f, lines in self.EXPECTED.items():
            out, _ = run_interp(src(f))
            self.assertEqual(out.splitlines(), lines, f)

    def test_the_interpreter_reaches_the_default_depth_bound_in_every_shape(self):
        # a clause rule calling itself, a call inside a tuple, and a rule reached through an
        # answer each nest 9,999 calls below main; one more is refused, by the bound and not
        # by a limit of the interpreter's own
        text = depth_shapes() + ('rule main uses Output\n    output relay(4998)(0)\n    output climb(9998)(0)\n'
                                 '    output nest(9998)\n    output {}\n')
        with tempfile.TemporaryDirectory() as tmp:
            for last in ('relay(4999)(0)', 'climb(9999)(0)', 'nest(9999)'):
                path = os.path.join(tmp, 'deep.selv')
                with open(path, 'w') as f:
                    f.write(text.format(last))
                r = cli('run', path)
                self.assertEqual((r.returncode, r.stdout.splitlines()), (70, ['4999', '49985001', '9998']), last)
                self.assertEqual(r.stderr, 'selvage: refused: the run nests deeper than 10000 rule calls\n')

    def test_refusals_are_defined(self):
        for p in ('divzero.selv', 'bounds.selv'):
            r = cli('run', os.path.join(PROGS, p))
            self.assertEqual(r.returncode, 70)       # Root's answer to a refusal: the run ends
            self.assertIn('refused', r.stderr)
            self.assertEqual(r.stdout.strip(), '0')


def depth_shapes():
    sys.path.insert(0, os.path.join(ROOT, 'tests'))
    import generated_04
    return generated_04.DEPTH_HEAD


TRITS_EXPECTED = ['(true, maybe, false)', '(maybe, maybe, false)', '(false, false, false)',
                  '(true, true, true)', '(true, maybe, maybe)', '(true, maybe, false)',
                  '(false, maybe, true)', '(maybe, false)', 'true', 'page', 'queue', 'queue', 'page']
DECIDER = f'command:{sys.executable} {os.path.join(EX, "decider.py")}'


class TestMaybe(unittest.TestCase):
    """Three-valued logic, decide, and the answers that settle maybe."""

    def run_with(self, text, decider):
        import io
        m, _, _ = load(text)
        out = io.StringIO()
        it = Interp(m, out, decider)
        it.run_main()
        return out.getvalue().splitlines(), it

    def test_kleene_tables_and_decisions(self):
        from selvage.deciders import command
        lines, it = self.run_with(src('trits.selv', PROGS), command(DECIDER[len('command:'):]))
        self.assertEqual(lines, TRITS_EXPECTED)
        self.assertEqual(len(it.decisions), 2)        # only the two undecided cases left the program

    def test_not_is_a_certified_bijection_on_trit(self):
        m, _, _ = load(src('trits.selv', PROGS))
        self.assertEqual(m.rules['flip'].cls, 'bijection')

    def test_undecided_conditions_are_refused(self):
        for text, needle in {
            'rule f(t: Trit) returns I64\n    if t\n        1\n    otherwise\n        0\n': 'say `decide`',
            'rule f(t: Trit) returns Bool\n    decide t\n': 'uses Decide',
            'rule f(x: I64) returns Bool uses Decide\n    decide x\n': 'settles true, false or maybe',
            'rule f takes Trit returns Trit\n    true <-> true\n    false <-> false\n': None,
        }.items():
            if needle is None:
                m, _, _ = load(text)
                self.assertEqual(m.rules['f'].cls, 'partial')   # maybe is not covered
                continue
            with self.assertRaises(CheckError) as cm:
                load(text)
            self.assertIn(needle, str(cm.exception))

    def test_nobody_decides_is_a_refusal(self):
        with self.assertRaises(Fault):
            self.run_with(src('trits.selv', PROGS), refuse)

    def test_escalation_through_answers(self):
        lines, it = self.run_with(src('triage.selv'), fixed(False))
        self.assertEqual(lines, ['page the on-call engineer', 'queue for the morning', 'page the on-call engineer',
                                 'queue for the morning', 'queue for the morning', 'Tally from 2'])
        self.assertEqual(len(it.decisions), 2)

    def test_replay_needs_no_decider(self):
        import json
        from selvage.deciders import command, replay
        lines1, it = self.run_with(src('triage.selv'), command(DECIDER[len('command:'):]))
        with tempfile.NamedTemporaryFile('w', suffix='.json', delete=False) as f:
            json.dump(it.decisions, f)
        lines2, _ = self.run_with(src('triage.selv'), replay(f.name))
        self.assertEqual(lines1, lines2)

    def test_rewind_across_a_decision_restores_the_answers(self):
        text = src('triage.selv') + (
            '\nrule gate takes (I64, Trit) returns (I64, Trit, Bool) uses Decide\n'
            '    (severity, outage) => (severity, outage, d) where\n'
            '        d is decide by_severity(severity) or outage\n')
        m, _, _ = load(text)
        self.assertEqual(m.rules['gate'].cls, 'lossy')
        it = Interp(m, None, fixed(True))
        cell = [Inst('Tally', (), W(0))]
        it.handlers.append(cell)
        for v in ((W(3), MAYBE), (W(5), MAYBE), (W(2), False)):
            out = it.forward(m.rules['gate'], (), v)
            back = it.backward(m.rules['gate'], (), out, 'rewind')
            self.assertEqual(back, v)
            self.assertEqual((cell[0].state, it.journal), (W(0), []))

    def test_repl(self):
        session = '\n'.join([
            'x is 40', 'x + 2', 'rule twice takes I64 returns (I64, I64)', '    a <-> (a, b) where',
            '        b is a', '', 'undo twice((21, 21))', 'add x to x', 'maybe or true',
            'decide maybe', '']) + '\n'
        r = subprocess.run([sys.executable, '-m', 'selvage', 'repl', '--decide', 'false'], input=session,
                           capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=ROOT))
        self.assertEqual(r.stdout.splitlines(), ['42', 'twice: bijection', '21', 'true', 'false'])
        self.assertIn('R4', r.stderr)


ALL_EXAMPLES = ('orbit.selv', 'shapes.selv', 'messages.selv', 'arrays.selv', 'derivative.selv',
                'triage.selv', 'adder.selv', 'prototypes.selv', 'witness.selv', 'inversion.selv', 'gates.selv',
                'declarations.selv')


def clause_rules(m):
    """Every clause rule and every answer's own request rule, prelude included."""
    out = [r for r in m.rules.values() if r.kind == 'clauses']
    return out + [o for a in m.answers.values() for o in a.ops.values() if o.owner == a.name]


def bits(x, n=8):
    return Arr('Bit', [W((x >> i) & 1, 'Bit') for i in range(n)])


class TestInversion(unittest.TestCase):
    """`invert` is an involution on code; an inverse is ordinary code; one engine runs both."""

    @classmethod
    def setUpClass(cls):
        cls.models = {f: load(src(f))[0] for f in ALL_EXAMPLES}

    def decls(self):
        from selvage.checker import definition_of
        for f, m in self.models.items():
            for r in [r for r in m.rules.values() if r.kind == 'clauses'] + list(m.answers.values()):
                yield f, m, r, definition_of(m, r)

    def test_invert_is_an_involution(self):
        from selvage.invert import invert
        n = 0
        for f, m, r, d in self.decls():
            self.assertEqual(invert(invert(d)), d, f'{f}: {r.name}')
            n += 1
        self.assertGreater(n, 60)

    def test_inverse_prints_parses_and_hashes_like_any_code(self):
        from selvage.invert import invert
        from selvage.printer import code_text
        for f, m, r, d in self.decls():
            inv = invert(d)
            again = parse(code_text(inv) + '\n').kids[0]
            self.assertEqual(again, inv, f'{f}: {r.name}')
            self.assertEqual(identity(again), identity(inv))

    def test_the_inverse_that_runs_is_the_inverse_invert_prints(self):
        from selvage.invert import invert
        for f, m in self.models.items():
            for r in clause_rules(m):
                self.assertEqual(tuple(r.inverse.clauses), tuple(invert(c) for c in r.clauses), r.name)
                self.assertIs(r.inverse.inverse, r)
                self.assertEqual(r.inverse.cls == 'lossy', r.cls == 'lossy', r.name)

    def test_inverse_passes_the_ordinary_checker_as_source(self):
        """The printed inverse of every clause rule, renamed and appended to its program
        as plain source, checks with nothing special about it."""
        from selvage.checker import definition_of
        from selvage.invert import invert
        from selvage.printer import code_text
        for f in ALL_EXAMPLES:
            m = self.models[f]
            extra = []
            for name in m.decl_order:
                r = m.rules[name]
                if r.kind == 'clauses' and name not in m.prelude_names:
                    extra.append(code_text(invert(definition_of(m, r))).replace(
                        f'rule undo {name}', f'rule {name}_back', 1))
            if not extra:
                continue
            m2, _, _ = load(src(f) + '\n' + '\n\n'.join(extra) + '\n')
            for name in m.decl_order:
                r = m.rules[name]
                if r.kind == 'clauses' and name not in m.prelude_names:
                    self.assertEqual(m2.rules[name + '_back'].cls, r.inverse.cls, f'{f}: {name}')

    def test_elaborated_code_leaves_nothing_implicit(self):
        """Every temporary is uncomputed by a `was` step in the code itself; `set` and
        rounding updates are spelled as an exchange plus a discard."""
        from selvage.checker import Checker
        for f, m in self.models.items():
            for r in clause_rules(m):
                for b in Checker(m).blocks_of(r):
                    self.assertFalse(m.auto.get(id(b)), f'{f}: {r.name}')
                    self.assertFalse([s for s in b.kids if s.tag == 'Set'], f'{f}: {r.name}')
        from selvage.checker import definition_of
        from selvage.printer import code_text
        text = code_text(definition_of(self.models['orbit.selv'], self.models['orbit.selv'].rules['damped_orbit']))
        self.assertIn('discard old_p', text)
        text = code_text(definition_of(self.models['derivative.selv'], self.models['derivative.selv'].rules['derivative']))
        self.assertNotIn('copy', text)

    def round_trip(self, it, r, params, value, undo=False):
        """execute(invert(r), execute(r, S, J)) = (S, J)."""
        before = (identity(value), [identity(e) for e in it.journal],
                  [identity(c[0]) for c in it.handlers])
        out = it.forward(r, params, deep(value))
        back = it.undo(r, params, out) if undo else it.rewind(r, params, out)
        after = (identity(back), [identity(e) for e in it.journal], [identity(c[0]) for c in it.handlers])
        self.assertEqual(after, before, r.name)

    def test_semantic_round_trips(self):
        rng = random.Random(7)
        m = self.models['orbit.selv']
        it = Interp(m)
        for g in ('ccnot',):
            for x in itertools.product((0, 1), repeat=3):
                self.round_trip(it, m.rules[g], (), tuple(W(v, 'Bit') for v in x), undo=True)
        for x in itertools.product((0, 1), repeat=2):
            self.round_trip(it, m.rules['cnot'], (), tuple(W(v, 'Bit') for v in x), undo=True)
        for _ in range(30):
            a, b = rng.randrange(256), rng.randrange(256)
            self.round_trip(it, m.rules['ripple_add'], (), (bits(a), bits(b), W(0, 'Bit')), undo=True)
            self.round_trip(it, m.rules['exchange'], (), (bits(a), bits(b)), undo=True)
            self.round_trip(it, m.rules['fanout'], (), (bits(a), bits(0)), undo=True)
            ph = Form('Phase', (W(rng.randint(-10**6, 10**6)), W(rng.randint(-10**4, 10**4))))
            self.round_trip(it, m.rules['orbit'], (W(rng.randint(1, 40)), W(rng.randint(0, 50))), ph, undo=True)
            self.round_trip(it, m.rules['damped_orbit'], (W(10), W(rng.randint(0, 40))), ph)
        m = self.models['shapes.selv']
        it = Interp(m)
        for v in (Form('Positive', (W(3),)), Form('Negative', (W(3),)), Form('Zero', ())):
            self.round_trip(it, m.rules['magnitude'], (), v)
        m = self.models['derivative.selv']
        it = Interp(m)
        code = parse('rule main\n    x * x * x + 2 * x + 7\n').kids[0].kids[5].kids[0].kids[0]
        self.round_trip(it, m.rules['derivative'], ('x',), code)
        m = self.models['messages.selv']
        it = Interp(m)
        it.handlers.append([Inst('Replay', (Arr('F64', [0.5, -1.25, 2.0, 3.5]),), W(0))])
        self.round_trip(it, m.rules['walk'], (W(4),), 0.125)
        self.round_trip(it, m.rules['pay'], (W(30),), Inst('Ledger', (), W(100)), undo=True)
        m = self.models['prototypes.selv']
        it = Interp(m)
        self.round_trip(it, m.rules['bump_twice'], (W(7),),
                        Inst('Resettable', (), (Inst('Count', (), W(5)), W(0))), undo=True)

    def test_a_loss_is_a_message_to_the_root(self):
        m = self.models['orbit.selv']
        it = Interp(m)
        it.forward(m.rules['damped_orbit'], (W(10), W(3)), Form('Phase', (W(1000), W(5))))
        self.assertEqual([e.tag for e in it.journal], ['Dropped'] * 3)
        obj = it.root[0]            # an Object holding a Root, whose state is the journal
        self.assertEqual((obj.answer, obj.state.answer, obj.state.state.tag), ('Object', 'Root', 'Kept'))
        self.assertEqual(m.answers['Object'].ops, {})
        self.assertEqual(m.answers['Object'].delegates['keep'], ((), 'Root'))
        self.assertIs(m.op_rule('Object', 'keep'), m.answers['Root'].ops['keep'])
        self.assertEqual(m.answers['Root'].ops['keep'].cls, 'bijection')

    def test_authority_stays_outside_the_code(self):
        m = self.models['orbit.selv']
        it = Interp(m)
        out = it.forward(m.rules['damped_orbit'], (W(10), W(3)), Form('Phase', (W(1000), W(5))))
        with self.assertRaises(Fault):          # user-facing undo: certified rules only
            it.undo(m.rules['damped_orbit'], (W(10), W(3)), out)
        with self.assertRaises(Fault):          # the inverse is code anyone may hold; running it
            it.run_rule(m.rules['damped_orbit'].inverse, (W(10), W(3)), out)   # takes the system
        out2, _ = run_interp('rule main uses Output\n    output evaluate(quote x * 2 + 1, quote x, 20)\n')
        self.assertEqual(out2, '41\n')
        with self.assertRaises(Fault):          # admission: a request in constructed code is refused
            run_interp('rule main uses Output\n    output evaluate(quote ask history(), quote x, 1)\n')

    def test_delegation_keeps_each_certificate_where_it_is_answered(self):
        m = self.models['prototypes.selv']
        res, cnt = m.answers['Resettable'], m.answers['Count']
        self.assertEqual((list(res.ops), res.delegates), (['reset'], {'bump': ((0,), 'Count')}))
        self.assertIs(m.op_rule('Resettable', 'bump'), cnt.ops['bump'])     # the parent's own rule
        self.assertEqual((cnt.ops['bump'].cls, res.ops['reset'].cls, res.cls), ('bijection', 'lossy', 'lossy'))
        self.assertEqual(m.rules['bump_twice'].cls, 'bijection')
        out, _ = run_interp(src('prototypes.selv'))
        self.assertEqual(by_name(out).splitlines(), [
            'Resettable from (Count from 25, 0)', 'Resettable from (Count from 5, 0)',
            'Resettable from (Count from 0, 1)', 'Kept(Dropped("Resettable.reset", 25), Empty)'])

    def test_lineage_reaches_ccnot_from_every_rule(self):
        from selvage.lineage import links
        for f, m in self.models.items():
            nodes = [r.name for r in clause_rules(m)] + list(m.answers)
            for n in nodes:
                seen, queue = set(), [n]
                while queue:
                    x = queue.pop()
                    if x not in seen:
                        seen.add(x)
                        ls = links(m, x)
                        self.assertTrue(all(kind in ('checked', 'delegated', 'realized', 'theorem')
                                            for _, _, kind, _ in ls), x)
                        queue += [t for _, t, _, _ in ls]
                self.assertIn('ccnot', seen, f'{f}: {n}')
        from selvage.lineage import keys_of, verify, reachable
        keys = set()
        for f, m in self.models.items():
            for key in keys_of(m, reachable(m, [r.name for r in clause_rules(m)] + list(m.answers))):
                if key not in keys:
                    keys.add(key)
                    cases, bad, _ = verify(m, key, samples=16)
                    self.assertEqual(bad, 0, key)
                    self.assertGreater(cases, 0)
        self.assertTrue({('bit-xor',), ('bit-and-xor',), ('move',), ('add', 'I64')} <= keys)
        self.assertIn(('bump (to its Count)', 'Count.bump', 'delegated', None),
                      links(self.models['prototypes.selv'], 'Resettable'))
        r = cli('lineage', os.path.join(EX, 'prototypes.selv'), 'Resettable')
        layers = [line.split()[1] for line in r.stdout.splitlines()]
        for want in ('prototype', 'actor', 'user', 'system', 'logic', 'base'):
            self.assertIn(want, layers)


class TestMirror(unittest.TestCase):
    """Inversion is the prelude's rule `mirror`: certified, its own inverse, and the only table
    `invert` has.  Three readings of it are compared: the rule run by the interpreter like any
    rule, the host's `invert` running its clauses, and an independent table (reference_model)."""

    def agree(self, text, lossy=True):
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        from reference_model import model_invert
        from selvage.invert import as_sequence, as_block
        m = load(text)[0]
        it, mirror, n = Interp(m), m.rules['mirror'], 0
        rules = list(m.rules.values()) + [o for a in m.answers.values() for o in a.ops.values()]
        for r in rules:
            if getattr(r, 'kind', None) != 'clauses' or getattr(r, 'native', False) or (r.cls == 'lossy' and not lossy):
                continue
            for c in r.clauses:                                          # the code that runs, elaborated
                want = model_invert(c)                                   # the independent table
                self.assertEqual(invert(c), want, r.name)                # the host, running mirror's clauses
                self.assertEqual(as_block(it.forward(mirror, (), as_sequence(c))), want, r.name)    # the rule itself
                self.assertEqual(as_block(it.undo(mirror, (), as_sequence(c))), want, r.name)       # and its inverse
                n += 1
        return n

    def test_the_inverter_is_a_certified_rule_of_the_prelude(self):
        m = load('')[0]
        self.assertEqual(m.rules['mirror'].cls, 'partial')
        self.assertEqual({c.tag for c in m.rules['mirror'].clauses}, {'Clause'})        # `<->` throughout
        out, _ = run_interp(src('inversion.selv'))
        lines = out.splitlines()
        self.assertEqual(lines[:5], ['swap p and q', 'subtract k from p', 'true', 'true', 'x was discarded'])
        self.assertEqual(lines[-2:], ['true', 'true'])

    def test_invert_has_no_table_but_the_rule(self):
        # change a clause of `mirror` in the prelude's text and the host's `invert` changes with it
        from selvage import invert as host
        table = host.mirror_clauses()
        self.assertEqual(len(table), len(load('')[0].rules['mirror'].clauses))
        step = Form('AddTo', (Form('Name', ('k',)), Form('Name', ('p',))))
        self.assertEqual(invert(step).tag, 'SubtractFrom')
        saved = table['AddTo']
        try:
            table['AddTo'] = (saved[0], 'Swap', saved[2], saved[3])
            self.assertEqual(invert(step).tag, 'Swap')
        finally:
            table['AddTo'] = saved
        self.assertFalse(hasattr(host, 'invert_step'))

    def test_mirror_is_its_own_inverse_clause_for_clause(self):
        # the premise of the involution proof (VIII.2): the derived inverse of `mirror` has, for
        # each clause of `mirror`, the clause with the same two sides, and steps that differ
        # only in reading `y was mirror(x)` where `mirror` reads `x is mirror(y)`
        m = load('')[0]
        r = m.rules['mirror']

        def key(c, backward):
            names, out = {}, []

            def shape(p):
                if p.tag == 'Name':
                    return p.kids[0] if p.kids[0][0].isupper() else names.setdefault(p.kids[0], len(names))
                return (p.kids[0].kids[0],) + tuple(shape(a) for a in p.kids[1].kids)
            sides = (shape(c.kids[0]), shape(c.kids[1]))
            for st in c.kids[2].kids:
                bound, read = st.kids[0].kids[0], st.kids[1].kids[1].kids[0].kids[0]
                self.assertEqual((st.tag, st.kids[1].kids[0].kids[0]), ('Was' if backward else 'Let', 'mirror'))
                out.append((names[read], names[bound]) if backward else (names[bound], names[read]))
            return sides + (frozenset(out),)
        mine = sorted(map(repr, (key(c, False) for c in definition_of(m, r).kids[-1].kids)))
        derived = sorted(map(repr, (key(c, True) for c in invert(definition_of(m, r)).kids[-1].kids)))
        self.assertEqual(mine, derived)

    def test_it_inverts_every_clause_certified_or_lossy_as_the_independent_table_does(self):
        n = sum(self.agree(src(f)) for f in ALL_EXAMPLES)
        self.assertGreaterEqual(n, 150)
        self.assertGreaterEqual(self.agree(''), 15)                   # the prelude's, mirror's own among them
        import generated_04
        import roundtrip_gen
        rng, n, lossy = random.Random(4), 0, 0
        for i in range(90):
            if i % 3 == 0:
                text = generated_04.decision_program(rng)[0]('=>')    # lossy or not: mirrored either way
            else:
                text = roundtrip_gen.Gen(rng).program() if i % 3 == 1 else generated_04.Structures(rng).program()
            try:
                k = self.agree(text)
            except CheckError:
                continue
            n += k
            lossy += 'discard' in text or 'set ' in text
        self.assertGreaterEqual(n, 300)
        self.assertGreaterEqual(lossy, 5)

    def test_a_sequence_reads_from_either_end(self):
        from selvage.invert import as_sequence, as_block
        m = load(src('inversion.selv'))[0]
        body = definition_of(m, m.rules['leapfrog']).kids[-1].kids[0].kids[2]
        self.assertEqual(as_block(as_sequence(body)), body)
        a, b, c = body.kids
        done = Form('Done', ())
        mixed = Form('Then', (a, Form('After', (Form('After', (done, b)), c))))       # first, then ... last
        self.assertEqual(as_block(mixed), body)


class TestJournalContract(unittest.TestCase):
    """keep appends one whole entry; the journal is ordered; only the system's rewind takes
    entries back, newest first; nothing else writes it; rewind restores it exactly."""

    PROG = ('rule drop_a takes (I64, I64) returns I64\n    (a, b) => a where\n        discard b\n'
            'rule drop_b takes (I64, I64) returns I64\n    (a, b) => a where\n        discard b\n')

    def test_keep_appends_and_rewind_restores_the_exact_journal(self):
        m = load(src('orbit.selv'))[0]
        it = Interp(m)
        r = m.rules['damped_orbit']
        out1 = it.forward(r, (W(10), W(3)), Form('Phase', (W(1000), W(5))))
        first, j1 = list(it.journal), identity(it.root[0].state)   # the Root the Object holds
        out2 = it.forward(r, (W(10), W(2)), Form('Phase', (W(77), W(-4))))
        self.assertEqual(len(it.journal), 5)
        self.assertEqual(it.journal[:3], first)              # earlier entries untouched
        self.assertEqual(it.rewind(r, (W(10), W(2)), out2), Form('Phase', (W(77), W(-4))))
        self.assertEqual(identity(it.root[0].state), j1)     # exact identity, not just length
        self.assertEqual(it.rewind(r, (W(10), W(3)), out1), Form('Phase', (W(1000), W(5))))
        self.assertEqual(it.root[0], Inst('Object', (), Inst('Root', (), Form('Empty', ()))))

    def test_a_rewind_out_of_step_is_refused(self):
        m = load(self.PROG)[0]
        it = Interp(m)
        it.forward(m.rules['drop_a'], (), (W(1), W(2)))
        it.forward(m.rules['drop_b'], (), (W(3), W(4)))
        with self.assertRaises(Fault):
            it.rewind(m.rules['drop_a'], (), W(1))           # drop_b's entry is newest

    def test_only_the_system_writes_or_takes_back(self):
        answers = 'System is sealed to Root: Mine cannot answer it'
        for text, needle in (
                ('answer Mine for System takes Journal\n    (keep(e), j) <-> ((), Kept(e, j))\n', answers),
                ('answer Mine for System takes Root\n', answers),                  # by delegation either
                ('answer Mine for System takes (Root, I64)\n', answers),
                ('rule main uses System\n    x is ask keep(5)\n', 'keep is a request of System, which is sealed'),
                ('rule f takes Object returns ((), Object)\n    o <-> (u, o) where\n        u is o -> keep(5)\n',
                 'keep is a request of System, which is sealed'),
                ('rule main uses Output\n    (v, r) is 1 with Root from Empty\n    output v\n', 'Root is sealed'),
                ('rule main uses Output\n    (v, r) is 1 with Object from (Root from Empty)\n    output v\n',
                 'Root is sealed'),
                ('rule main uses Output\n    (v, r) is 1 with Object from Empty\n    output v\n',
                 'Object holds a Root, which is sealed'),
                ('rule f takes Object returns Root\n    o <-> r where\n        o was Object from r\n',
                 'Object holds a Root, which is sealed'),
                ('rule f takes Journal returns Root\n    j <-> r where\n        r is Root from j\n', 'Root is sealed'),
                ('rule f takes Root returns Journal\n    r <-> j where\n        r was Root from j\n', 'Root is sealed')):
            with self.assertRaises(CheckError) as cm:
                load(text)
            self.assertIn(needle, str(cm.exception), text)
        out, it = run_interp(self.PROG + 'rule main uses Output, System, Witness\n'
                             '    v is drop_a((1, 2))\n    output ask history()\n')
        self.assertEqual(by_name(out), 'Kept(Dropped("drop_a", 2), Empty)\n')
        with self.assertRaises(Fault):
            it.take_back()                                    # user authority

    def test_a_decision_entry_counts_the_answers_it_asked(self):
        from selvage.forms import Form as F_
        it = Interp(load(src('orbit.selv'))[0])
        self.assertEqual(it.entry_bits(F_('Decided', ('c0de', 'r', W(0), True))), 1)
        self.assertEqual(it.entry_bits(F_('Decided', ('c0de', 'r', W(1), False))), 2)
        self.assertEqual(it.entry_bits(F_('Decided', ('c0de', 'r', W(3), True))), 3)

    def test_control_flow_inverts_only_when_it_can_be_reconstructed(self):
        for body in ('if a > 0\n            add 1 to a', 'repeat with i from 0 to a\n            add 1 to a'):
            with self.assertRaises(CheckError):
                load(f'rule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n        {body}\n')
        m = load('rule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n'
                 '        if b > 0\n            add b to a\n')[0]
        self.assertEqual(m.rules['f'].cls, 'bijection')


class TestJournalIdentity(unittest.TestCase):
    """R13: a journal entry names the code that kept it by that code's identity (III.3), and code
    takes back what its mirror kept.  Who it was kept by is recorded beside it and decides nothing.
    Code is identified by what it is and what it references: a call holds the identity of the
    rule called, not its name."""

    PROG = ('type T\n    A(n: I64)\n    B(n: I64)\n'
            'rule {0} takes T returns I64\n{1}'
            'rule settle_it(t: Trit) returns Bool uses Decide, System\n    decide t\n'
            'rule gate takes (Trit, I64) returns (Trit, Bool, I64) uses Decide\n    (t, x) => (t, d, x) where\n        d is decide t\n')
    A = '    A(n) => n where\n        x is n * 2\n        discard x\n'
    B = '    B(n) => n where\n        add 1 to n\n'
    CALL = ('rule {0} takes (I64, I64) returns I64\n    (kept, dropped) => kept where\n{1}        discard dropped\n'
            'rule f takes (I64, I64) returns I64\n    (a, b) => c where\n        c is {0}((a, b))\n')
    LOOP = ('rule {0} takes (I64, I64) returns I64\n    (0, acc) => acc\n    (n, acc) => out where\n'
            '        add {2} to acc\n        subtract 1 from n\n        out is {1}((n, acc))\n')

    def kept(self, name='f', clauses=None, value=None):
        m = load(self.PROG.format(name, ''.join(clauses or (self.A, self.B))))[0]
        it = Interp(m, None, fixed(True))
        out = it.forward(m.rules[name], (), value or Form('A', (W(5),)))
        return m, it, out

    def test_an_entry_names_the_code_that_kept_it(self):
        m, it, out = self.kept()
        f = m.rules['f']
        a, b = code_identity(m, f.clauses[0]), code_identity(m, f.clauses[1])
        self.assertEqual([(e.tag,) + e.kids for e in it.journal],
                         [('Dropped', a, 'f', W(10)), ('Chose', a, 'f', W(2))])
        self.assertEqual(it.rewind(f, (), out), Form('A', (W(5),)))
        it.forward(f, (), Form('B', (W(5),)))
        self.assertEqual([(e.tag, e.kids[0]) for e in it.journal], [('Chose', b)])
        # a decision: in a clause rule, the clause; in a procedure, the procedure's own body,
        # and not the declaration it stands in
        it = Interp(m, None, fixed(True))
        it.forward(m.rules['gate'], (), (MAYBE, W(1)))
        it.call_expr_rule(m.rules['settle_it'], (MAYBE,))
        self.assertEqual([(e.tag, e.kids[0], e.kids[1]) for e in it.journal],
                         [('Decided', code_identity(m, m.rules['gate'].clauses[0]), 'gate'),
                          ('Decided', code_identity(m, m.rules['settle_it'].block, m.rules['settle_it']), 'settle_it')])
        self.assertNotEqual(code_identity(m, m.rules['settle_it'].block, m.rules['settle_it']),
                            rule_identities(m)['settle_it'])                  # the body, not the rule it is the body of

    def test_renaming_a_rule_or_reordering_its_clauses_changes_no_identity(self):
        _, first, _ = self.kept()
        m, it, out = self.kept('renamed', (self.B, self.A))
        self.assertEqual([e.kids[0] for e in it.journal], [e.kids[0] for e in first.journal])     # the same code
        self.assertEqual([e.kids[1] for e in it.journal], ['renamed', 'renamed'])                 # kept by another name
        self.assertEqual(it.rewind(m.rules['renamed'], (), out), Form('A', (W(5),)))              # the second clause now

    def test_a_call_holds_the_identity_of_the_rule_called_and_not_its_name(self):
        ids = lambda text, rule='f': (rule_identities(load(text)[0])[rule],                        # noqa: E731
                                      code_identity(load(text)[0], load(text)[0].rules[rule].clauses[0]))
        base = ids(self.CALL.format('helper', ''))
        self.assertEqual(ids(self.CALL.format('other', '')), base)             # the rule called, under another name
        declared = self.CALL.format('helper', '').split('rule f')
        self.assertEqual(ids('rule f' + declared[1] + declared[0]), base)       # and declared after its caller
        # the rule called, changed: it is another rule, and its caller is other code
        self.assertNotEqual(ids(self.CALL.format('helper', '        add 1 to kept\n')), base)
        # and the caller's entries say so, while the rule called keeps its own name for the reader
        m = load(self.CALL.format('other', ''))[0]
        it = Interp(m)
        it.forward(m.rules['f'], (), (W(1), W(2)))
        helper = code_identity(load(self.CALL.format('helper', ''))[0], load(self.CALL.format('helper', ''))[0].rules['helper'].clauses[0])
        self.assertEqual([(e.kids[0], e.kids[1]) for e in it.journal], [(helper, 'other')])

    def test_rules_that_call_themselves_or_each_other_have_stable_identities(self):
        def program(a='ping', b='pong', x=1, y=2, own='sink', first=True):
            decls = [self.LOOP.format(a, b, x), self.LOOP.format(b, a, y), self.LOOP.format(own, own, 3)]
            return ''.join(decls if first else reversed(decls))
        m = load(program())[0]
        base = rule_identities(m)
        self.assertEqual(len({base['ping'], base['pong'], base['sink']}), 3)
        for a, b, own, first in (('tick', 'tock', 'fall', True), ('ping', 'pong', 'sink', False), ('b', 'a', 'c', False)):
            ids = rule_identities(load(program(a, b, own=own, first=first))[0])
            self.assertEqual((ids[a], ids[b], ids[own]), (base['ping'], base['pong'], base['sink']), (a, b, own, first))
        # one member changed: the cycle is another cycle, and both members are other rules
        other = rule_identities(load(program(y=5))[0])
        self.assertTrue(other['ping'] != base['ping'] and other['pong'] != base['pong'] and other['sink'] == base['sink'])
        # members that nothing separates are the same code, and have one identity
        twins = rule_identities(load(program(x=4, y=4))[0])
        self.assertEqual(twins['ping'], twins['pong'])
        # a run keeps and takes back under those identities, level by level
        it = Interp(m)
        out = it.forward(m.rules['ping'], (), (W(3), W(0)))
        clause = lambda r, i: code_identity(m, m.rules[r].clauses[i])                              # noqa: E731
        self.assertEqual([(e.kids[0], e.kids[1]) for e in it.journal],
                         [(clause('pong', 0), 'pong'), (clause('ping', 1), 'ping'), (clause('pong', 1), 'pong'),
                          (clause('ping', 1), 'ping')])
        self.assertEqual((out, it.rewind(m.rules['ping'], (), out), it.journal), (W(4), (W(3), W(0)), []))

    def test_code_takes_back_only_what_its_mirror_kept(self):
        def forged(change):
            m, it, out = self.kept()
            j = it.journal_of(it.root[0])
            it.root[0] = it.with_journal(it.root[0], Form('Kept', (change(j.kids[0]), j.kids[1])))
            return it.rewind(m.rules['f'], (), out)
        # who kept an entry decides nothing: the code does
        self.assertEqual(forged(lambda e: Form('Chose', (e.kids[0], 'another rule', e.kids[2]))), Form('A', (W(5),)))
        for code in ('0' * 16, identity(Form('Done', ()))):
            with self.assertRaises(Fault) as c:
                forged(lambda e: Form('Chose', (code,) + e.kids[1:]))
            self.assertIn('journal out of step', str(c.exception))
        # forward keeping and backward taking back agree on the code: the mirror of the clause
        # running backward is the clause that ran
        m, it, _ = self.kept()
        f = m.rules['f']
        self.assertEqual([it.mirrors(c, f.inverse) for c in f.inverse.clauses], [code_identity(m, c) for c in f.clauses])

    def test_identities_are_compared_as_the_forms_they_name(self):
        from unittest import mock
        import selvage.codeid
        import selvage.interp
        one = lambda v, refs=None: 'one-name'                                                      # noqa: E731
        m = load(self.PROG.format('f', self.A + self.B))[0]
        with mock.patch.object(selvage.interp, 'identity', one):
            it = Interp(m)
            it.forward(m.rules['f'], (), Form('A', (W(5),)))
            with self.assertRaises(Fault) as c:
                it.forward(m.rules['f'], (), Form('B', (W(5),)))
        self.assertIn('two different pieces of code share the identity', str(c.exception))
        # and rules: a caller holds the identity of what it calls, so two rules may not share one
        m = load(self.PROG.format('f', self.A + self.B))[0]
        with mock.patch.object(selvage.codeid, 'identity', one):
            with self.assertRaises(Fault) as c:
                Interp(m).forward(m.rules['f'], (), Form('A', (W(5),)))
        self.assertIn('two different declarations share the identity', str(c.exception))


class TestCodeIdentity(unittest.TestCase):
    """Code is identified by what it is and what it refers to (III.3).  Names are for readers;
    identities are for execution; canonical forms establish equality; authority is none of these."""

    LOOP = ('rule {0} takes (I64, I64) returns I64\n    (0, acc) => acc\n    (n, acc) => out where\n'
            '        add {2} to acc\n        subtract 1 from n\n        out is {1}((n, acc))\n')

    def setUp(self):
        sys.path.insert(0, os.path.join(ROOT, 'tests'))

    def ids(self, text, rule='f'):
        m = load(text)[0]
        r = m.rules[rule]
        return (rule_identities(m)[rule],
                tuple(code_identity(m, c, r) for c in r.clauses) if r.kind == 'clauses' else code_identity(m, r.block, r))

    def test_variables_are_identified_by_their_binding_and_not_their_name(self):
        import generated_04
        rng = random.Random(3)
        for _ in range(5):
            for what, code, same, different in generated_04.scope_cases(rng):
                want = self.ids(code)
                for other in same:
                    self.assertEqual(self.ids(other), want, what + '\n' + other)
                for other in different:
                    self.assertNotEqual(self.ids(other), want, what + '\n' + other)

    def test_the_description_s_example_is_one_rule_under_two_names(self):
        text = open(os.path.join(ROOT, 'SPEC.md')).read()
        block = text[text.index('rule tally takes'):]
        ids = rule_identities(load(block[:block.index('```')])[0])
        self.assertEqual(ids['tally'], ids['sum'])
        self.assertNotEqual(ids['cross'], ids['sum'])

    def test_no_name_is_bound_where_it_is_already_bound(self):
        import generated_04
        for what, code in generated_04.shadowed(random.Random(3)):
            with self.assertRaises(CheckError, msg=what) as c:
                load(code)
            self.assertRegex(str(c.exception), 'already bound|never rebound', what)
        # what stays allowed: a name bound again after it was given back, and in another block
        load('rule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n        t is b\n        add t to a\n'
             '        t was b\n        t is a\n        add t to b\n        t was a\n'
             '        repeat with i from 0 to 2\n            add i to a\n        repeat with i from 0 to 3\n            add i to b\n')

    def test_requests_and_answers_are_referred_to_by_identity(self):
        import generated_04
        base = dict(G='G', put='put', take='take', Cell='Cell', Twin='Twin', made='Cell', sent='put', asked='put')
        new = dict(G='Store', put='stash', take='fetch', Cell='Box', Twin='Other', made='Box', sent='stash', asked='stash')
        a, b = generated_04.NAMED.format(**base), generated_04.NAMED.format(**new)
        for rule in ('via', 'asker', 'holder'):
            self.assertEqual(self.ids(a, rule), self.ids(b, rule), rule)        # every name changed, no identity
        ia, ib = identities(load(a)[0]), identities(load(b)[0])
        self.assertEqual((ia.groups['G'], ia.requests['put'], ia.answers['Cell']),
                         (ib.groups['Store'], ib.requests['stash'], ib.answers['Box']))
        # declarations are not interchangeable code: the same signature is another request,
        # and the same code is another answer
        self.assertNotEqual(ia.requests['put'], ia.requests['take'])
        self.assertNotEqual(ia.answers['Cell'], ia.answers['Twin'])
        self.assertNotEqual(self.ids(generated_04.NAMED.format(**dict(base, sent='take')), 'via'), self.ids(a, 'via'))
        self.assertNotEqual(self.ids(generated_04.NAMED.format(**dict(base, made='Twin')), 'via'), self.ids(a, 'via'))
        # a quoted name is data: a rule that quotes one request is not a rule that quotes another
        quoting = 'rule says returns Code\n    quote {}(1)\n'
        self.assertNotEqual(self.ids(a + quoting.format('put'), 'says'), self.ids(b + quoting.format('stash'), 'says'))
        self.assertEqual(self.ids(a + quoting.format('put'), 'says'), self.ids(a.replace('via', 'through') + quoting.format('put'), 'says'))
        # a run keeps under the same identities, and shows the names of its own program
        kept = []
        for text in (a, b):
            m = load(text)[0]
            it = Interp(m)
            out = it.forward(m.rules['via'], (), (W(3), W(10)))
            kept.append(([e.kids[0] for e in it.journal], [e.kids[1] for e in it.journal]))
            self.assertEqual(it.rewind(m.rules['via'], (), out), (W(3), W(10)))
        self.assertEqual(kept[0][0], kept[1][0])
        self.assertEqual((kept[0][1], kept[1][1]), (['Cell.put', 'via'], ['Box.stash', 'via']))

    def test_exclusive_clauses_are_a_set_and_first_match_clauses_a_sequence(self):
        head = 'type T\n    A(n: I64)\n    B(n: I64)\nrule f takes T returns I64\n'
        a, b = '    A(n) => n where\n        add 1 to n\n', '    B(n) => n where\n        add 2 to n\n'
        self.assertEqual(self.ids(head + a + b)[0], self.ids(head + b + a)[0])
        self.assertEqual(sorted(self.ids(head + a + b)[1]), sorted(self.ids(head + b + a)[1]))
        # where the first match decides, the order is what the rule does
        first, second = '    0 => 10\n', '    n => n\n'
        one, other = ('rule f takes I64 returns I64\n' + x for x in (first + second, second + first))
        self.assertNotEqual(self.ids(one)[0], self.ids(other)[0])
        run = lambda text: Interp(load(text)[0]).forward(load(text)[0].rules['f'], (), W(0))       # noqa: E731
        self.assertEqual((run(one), run(other)), (W(10), W(0)))
        self.assertEqual(sorted(self.ids(one)[1]), sorted(self.ids(other)[1]))      # the clauses themselves are the same code

    def test_a_cycle_is_identified_as_a_whole_and_its_members_by_what_they_refer_to(self):
        def ring(steps, names=('a', 'b', 'c'), order=(0, 1, 2)):
            decls = [self.LOOP.format(names[i], names[(i + 1) % 3], steps[i]) for i in range(3)]
            return ''.join(decls[i] for i in order)
        m = rule_identities(load(ring((1, 1, 2)))[0])
        # a and b have the same code but call different members: three rules
        self.assertEqual(len({m['a'], m['b'], m['c']}), 3)
        for names, order in ((('x', 'y', 'z'), (0, 1, 2)), (('a', 'b', 'c'), (2, 0, 1)), (('c', 'a', 'b'), (1, 2, 0))):
            other = rule_identities(load(ring((1, 1, 2), names, order))[0])
            self.assertEqual([other[n] for n in names], [m['a'], m['b'], m['c']], (names, order))
        # a ring whose members repeat is identified by refinement alone, and is the ring of its
        # period: an alternating ring of four under any names, order and rotation, and the ring of two
        def any_ring(names, steps, order):
            k = len(names)
            decls = [self.LOOP.format(names[i], names[(i + 1) % k], steps[i]) for i in range(k)]
            return ''.join(decls[i] for i in order)
        four = rule_identities(load(any_ring('abcd', (1, 2, 1, 2), (0, 1, 2, 3)))[0])
        self.assertEqual((four['a'] == four['c'], four['b'] == four['d'], four['a'] == four['b']), (True, True, False))
        turned = rule_identities(load(any_ring('wxyz', (2, 1, 2, 1), (3, 1, 0, 2)))[0])
        self.assertEqual(({turned['w'], turned['y']}, {turned['x'], turned['z']}), ({four['b']}, {four['a']}))
        two = rule_identities(load(any_ring('pq', (1, 2), (1, 0)))[0])
        self.assertEqual((two['p'], two['q']), (four['a'], four['b']))
        # one member changed: every member is another rule
        changed = rule_identities(load(ring((1, 1, 3)))[0])
        self.assertTrue(all(changed[n] != m[n] for n in 'abc'))
        # where nothing separates the members they are one rule, called by three names
        same = rule_identities(load(ring((4, 4, 4)))[0])
        self.assertEqual(len({same['a'], same['b'], same['c']}), 1)
        # and that one rule is the rule that calls itself: a ring of members nothing separates
        # is the same code unrolled, and no run can tell the two apart
        alone = rule_identities(load(self.LOOP.format('a', 'a', 4))[0])
        self.assertEqual(alone['a'], same['a'])
        seen = []
        for text in (self.LOOP.format('a', 'a', 4), ring((4, 4, 4))):
            mod = load(text)[0]
            it = Interp(mod)
            out = it.forward(mod.rules['a'], (), (W(5), W(1)))
            seen.append((out, [e.kids[0] for e in it.journal]))
            self.assertEqual(it.rewind(mod.rules['a'], (), out), (W(5), W(1)))
        self.assertEqual(seen[0], seen[1])
        # a ring whose members differ is no rule that calls itself
        two = rule_identities(load(self.LOOP.format('a', 'b', 4) + self.LOOP.format('b', 'a', 5))[0])
        self.assertNotIn(alone['a'], (two['a'], two['b']))

    def test_declaration_order_only_breaks_ties(self):
        one = 'request One\n    first(v: I64) returns ()\n    peek() returns I64\n'
        two = 'request Two\n    second(t: Text) returns ()\n'
        a, b = identities(load(one + two)[0]), identities(load(two + one)[0])
        # a group with a signature of its own is the same group wherever it is declared
        self.assertEqual((a.groups['One'], a.requests['first'], a.requests['peek'], a.groups['Two']),
                         (b.groups['One'], b.requests['first'], b.requests['peek'], b.groups['Two']))
        # and under any name
        c = identities(load(two + one.replace('One', 'Uno').replace('first', 'primo').replace('peek', 'guarda'))[0])
        self.assertEqual((a.groups['One'], a.requests['first'], a.requests['peek']),
                         (c.groups['Uno'], c.requests['primo'], c.requests['guarda']))
        # its requests are a sequence: in another order it is another group, of other requests
        d = identities(load('request One\n    peek() returns I64\n    first(v: I64) returns ()\n' + two)[0])
        self.assertNotEqual(a.groups['One'], d.groups['One'])
        self.assertNotEqual(a.requests['first'], d.requests['first'])
        self.assertNotEqual(a.requests['peek'], d.requests['peek'])
        self.assertEqual(a.groups['Two'], d.groups['Two'])
        # two groups with the same signatures are told apart by which is declared first, and by
        # nothing else: declared the other way round, each has what the other had
        twin = 'request {}\n    {}(v: I64) returns ()\n    {}() returns I64\n'
        left, right = twin.format('Left', 'lput', 'lsee'), twin.format('Right', 'rput', 'rsee')
        e, f = identities(load(left + right)[0]), identities(load(right + left)[0])
        self.assertNotEqual(e.groups['Left'], e.groups['Right'])
        self.assertEqual((e.groups['Left'], e.groups['Right']), (f.groups['Right'], f.groups['Left']))
        self.assertEqual((e.requests['lput'], e.requests['rsee']), (f.requests['rput'], f.requests['lsee']))
        self.assertEqual(e.groups['Left'], a.groups['One'])            # the first of its signature, whatever it is called
        # answers: the same rule.  Different code keeps its identity wherever it is declared;
        # the same code is told apart by which is declared first
        look = 'request Look\n    look() returns I64\n'
        ans = 'answer {} for Look takes I64\n    (look(), s) <-> (v, s) where\n        v is s{}\n'
        x, y, z = ans.format('Plain', ''), ans.format('Same', ''), ans.format('Other', ' + 1')
        g, h = identities(load(look + x + z)[0]), identities(load(look + z + x)[0])
        self.assertEqual((g.answers['Plain'], g.answers['Other']), (h.answers['Plain'], h.answers['Other']))
        i, j = identities(load(look + x + y + z)[0]), identities(load(look + z + y + x)[0])
        self.assertNotEqual(i.answers['Plain'], i.answers['Same'])
        self.assertEqual((i.answers['Plain'], i.answers['Same'], i.answers['Other']),
                         (j.answers['Same'], j.answers['Plain'], j.answers['Other']))

    def test_quoted_code_is_identified_as_written(self):
        rule = 'rule {} takes I64 returns I64\n    n <-> n where\n        add 1 to n\n'
        main = ('rule main uses Output\n    output identity(quote f(1))\n    output identity(quote g(1))\n'
                '    output identity(quote x + 1)\n    output identity(quote y + 1)\n')
        with_f, _ = run_interp(rule.format('f') + main)
        with_g, _ = run_interp(rule.format('g') + main)
        f1, g1, x1, y1 = with_f.split()
        # a quoted call names what it names, and a quoted variable is its spelling: no call is
        # resolved in it and no name numbered
        self.assertEqual(len({f1, g1, x1, y1}), 4)
        # and what it is does not depend on the program around it: `f(1)` quoted where f is a
        # rule and where no rule has that name is the same form
        self.assertEqual(with_f, with_g)

    def test_a_ring_shares_an_identity_and_stays_a_ring(self):
        ring = ''.join(self.LOOP.format(n, c, 4) for n, c in (('a', 'b'), ('b', 'c'), ('c', 'a')))
        alone = self.LOOP.format('a', 'a', 4)
        ids = rule_identities(load(ring)[0])
        self.assertEqual({ids['a'], ids['b'], ids['c']}, {rule_identities(load(alone)[0])['a']})
        seen = {}
        for name, text in (('ring', ring), ('alone', alone)):
            m = load(text)[0]
            it = Interp(m)
            out = it.forward(m.rules['a'], (), (W(5), W(0)))
            seen[name] = (out, [e.kids[0] for e in it.journal], [e.kids[1] for e in it.journal])
            # the run nests as deep as its calls are: find the bound it just fits
            fits = None
            for limit in range(1, 12):
                it = Interp(m)
                it.depth_limit = limit
                try:
                    it.forward(m.rules['a'], (), (W(5), W(0)))
                    fits = limit
                    break
                except Fault as e:
                    self.assertIn(f'nests deeper than {limit} rule calls', str(e))
            seen[name] += (fits,)
        self.assertEqual(seen['ring'][3], seen['alone'][3])
        self.assertGreaterEqual(seen['ring'][3], 6)                    # six calls, one inside the other
        # the same results under the same identities; the names say which member ran, in the
        # order the ring was gone round: it was not rewritten into the rule that calls itself
        self.assertEqual(seen['ring'][:2], seen['alone'][:2])
        self.assertEqual(set(seen['alone'][2]), {'a'})
        self.assertEqual(set(seen['ring'][2]), {'a', 'b', 'c'})
        # whatever tells one member apart keeps the ring from being one rule: its code,
        # which member it calls, a parameter
        for other in (
                ''.join(self.LOOP.format(n, c, k) for n, c, k in (('a', 'b', 4), ('b', 'c', 4), ('c', 'a', 5))),
                ''.join(self.LOOP.format(n, c, 4) for n, c in (('a', 'b'), ('b', 'b'), ('c', 'a'))),
                self.LOOP.format('a', 'b(4)', 4) + self.LOOP.format('b(k: I64)', 'c', 'k') + self.LOOP.format('c', 'a', 4)):
            got = rule_identities(load(other)[0])
            self.assertGreater(len({got['a'], got['b'], got['c']}), 1, other)
            self.assertNotEqual(got['a'], ids['a'], other)

    def test_rules_that_share_an_identity_are_interchangeable(self):
        twins = self.LOOP.format('ping', 'pong', 4) + self.LOOP.format('pong', 'ping', 4)
        top = 'rule top takes (I64, I64) returns I64\n    (n, acc) => out where\n        out is {}((n, acc))\n'
        shown = []
        for called in ('ping', 'pong'):
            m = load(twins + top.format(called))[0]
            self.assertEqual(rule_identities(m)['ping'], rule_identities(m)['pong'])
            for n in range(4):
                it = Interp(m)
                out = it.forward(m.rules['top'], (), (W(n), W(0)))
                shown.append((called, n, rule_identities(m)['top'], out, tuple(e.kids[0] for e in it.journal)))
                self.assertEqual(it.rewind(m.rules['top'], (), out), (W(n), W(0)))
        # calling one for the other changes nothing but the names a reader sees
        self.assertEqual([s[2:] for s in shown if s[0] == 'ping'], [s[2:] for s in shown if s[0] == 'pong'])
        # the same holds for two rules with the same code that call nothing
        two = 'rule one takes I64 returns I64\n    n <-> n where\n        add 3 to n\nrule two takes I64 returns I64\n    x <-> x where\n        add 3 to x\n'
        ids = rule_identities(load(two)[0])
        self.assertEqual(ids['one'], ids['two'])

    def test_an_identity_grants_no_authority(self):
        ids = identities(load('')[0])
        self.assertTrue(ids.requests['keep'] and ids.answers['Root'] and ids.groups['System'])     # they have identities
        for text, why in (
                ('rule f returns () uses System\n    ask keep(1)\n', 'sealed'),
                ('rule f returns Root\n    Root from Empty\n', 'sealed'),
                # the same code as Root's own clause for `keep` answers nothing: the seal decides, not the code
                ('answer Mine for System takes Journal\n    (keep(e), j) <-> ((), Kept(e, j))\n', 'sealed')):
            with self.assertRaises(CheckError) as c:
                load(text)
            self.assertIn(why, str(c.exception), text)
        # two groups with the same signature are two groups: an answer declared for one answers
        # nothing of the other, however alike the requests are
        head = ('request One\n    first() returns I64\nrequest Two\n    second() returns I64\n'
                'answer Only for One takes ()\n    (first(), s) <-> (7, s)\n')
        ids = identities(load(head)[0])
        self.assertNotEqual(ids.groups['One'], ids.groups['Two'])
        self.assertNotEqual(ids.requests['first'], ids.requests['second'])
        asking = 'rule f returns I64{}\n    (r, o) is ask {}() with Only from ()\n    r\n'
        for text, why in ((asking.format('', 'second'), 'declare `uses Two`'),
                          ('answer Wrong for One takes ()\n    (second(), s) <-> (7, s)\n', 'with a request of One')):
            with self.assertRaises(CheckError) as c:
                load(head + text)
            self.assertIn(why, str(c.exception), text)
        m = load(head + asking.format('', 'first'))[0]
        self.assertEqual(Interp(m).run_main('f'), W(7))
        m = load(head + asking.format(' uses Two', 'second'))[0]
        with self.assertRaises(Fault) as c:
            Interp(m).run_main('f')
        self.assertIn('no answer for request second', str(c.exception))
        # an answer with the same code as another is declared for its own groups, and is its own answer
        closed = 'answer {} for Witness takes ()\n    (history(), s) <-> (Empty, s)\n'
        m = load(closed.format('Closed') + closed.format('Shut'))[0]
        self.assertNotEqual(identities(m).answers['Closed'], identities(m).answers['Shut'])


class TestTwoTiers(unittest.TestCase):
    """What the system does is conservative; what a program may do is dissipative, through an
    explicit loss (II.5).  A dissipative gate is a reversible gate and a `discard`."""

    def test_the_prelude_has_no_lossy_clause(self):
        m = load('')[0]
        arrows = [c.tag for r in m.rules.values() if r.kind == 'clauses' and not r.backward for c in r.clauses]
        arrows += [c.tag for a in m.answers.values() for r in a.ops.values() for c in r.clauses]
        self.assertGreater(len(arrows), 25)
        self.assertEqual(set(arrows), {'Clause'})
        self.assertFalse([n for n, r in m.rules.items() if r.cls == 'lossy'])
        self.assertNotIn('=>', src('prelude.selv', os.path.join(ROOT, 'selvage')).replace('`=>`', ''))

    def test_a_dissipative_gate_is_a_reversible_gate_and_a_discard(self):
        from selvage.lineage import links
        m = load(src('gates.selv'))[0]
        B = lambda x: Word(x, 'Bit')     # noqa: E731
        truth = {'and': lambda a, b: a & b, 'or': lambda a, b: a | b, 'nand': lambda a, b: 1 - (a & b)}
        for name, f in truth.items():
            into, gate = m.rules[name + '_into'], m.rules[name + '_gate']
            self.assertEqual((into.cls, gate.cls, gate.reasons), ('bijection', 'lossy', ['it discards a', 'it discards b']))
            for a, b in itertools.product((0, 1), repeat=2):
                it = Interp(m)
                # the reversible gate keeps its inputs beside the result, and keeps nothing else
                self.assertEqual(it.forward(into, (), (B(a), B(b))), (B(a), B(b), B(f(a, b))))
                self.assertEqual(it.journal, [])
                self.assertEqual(it.undo(into, (), (B(a), B(b), B(f(a, b)))), (B(a), B(b)))
                # the ordinary gate gives the result alone; what it let go of is in the journal
                self.assertEqual(it.forward(gate, (), (B(a), B(b))), B(f(a, b)))
                self.assertEqual([(e.tag, e.kids[2]) for e in it.journal], [('Dropped', B(a)), ('Dropped', B(b))])
                self.assertEqual(it.rewind(gate, (), B(f(a, b))), (B(a), B(b)))
                self.assertEqual(it.journal, [])
            # the gate rests on the reversible one, and its loss on Root's `keep`, down to ccnot
            self.assertIn(('calls', name + '_into', 'checked'), [x[:3] for x in links(m, name + '_gate')])
            self.assertIn(('keeps', 'Object', 'delegated'), [x[:3] for x in links(m, name + '_gate')])
        text = cli('lineage', os.path.join(EX, 'gates.selv'), 'and_gate').stdout
        for node in ('and_into', 'Object', 'Root.keep', 'exchange', 'cnot', 'ccnot'):
            self.assertRegex(text, rf'(?m)^{re.escape(node)} ', node)

    def test_certified_code_cannot_rest_on_a_dissipative_gate(self):
        gates = src('gates.selv').split('rule main')[0]
        with self.assertRaises(CheckError) as c:
            load(gates + 'rule through takes (Bit, Bit) returns Bit\n    (a, b) <-> c where\n        c is and_gate((a, b))\n')
        self.assertIn('through is lossy (it consumes through and_gate, which is lossy)', str(c.exception))
        # a dissipative rule may rest on either tier
        load(gates + 'rule both takes (Bit, Bit) returns Bit\n    (a, b) => c where\n        (a, b) is cnot((a, b))\n'
                     '        c is and_gate((a, b))\n')

    def test_boolean_logic_runs_on_the_kleene_circuits(self):
        from selvage.lineage import links, verify
        m = load('rule mark takes (Bool, Bool, I64) returns (Bool, Bool, I64)\n    (p, q, n) <-> (p, q, n) where\n'
                 '        if p and (q or not p)\n            add 1 to n\n')[0]
        self.assertIn(('Boolean logic', 'trit_and', 'realized', ('boolean',)), links(m, 'mark'))
        cases, bad, how = verify(m, ('boolean',))
        self.assertEqual((cases, bad), (10, 0))
        self.assertIn('exhaustive over Bool', how)


class TestAccounting(unittest.TestCase):
    """What a run is charged for what it lets go of (VII.5): the bits that tell apart what it
    could have let go of there, given what remains."""

    TYPES = ('type Shape\n    Circle(r: I64)\n    Square(side: I64)\n    Tri(a: I64, b: I64)\n\n'
             'type Hue\n    Red\n    Green\n    Blue\n\ntype Only\n    Only(n: I64, flag: Bool)\n\n'
             'type Opt\n    None\n    Some(n: I64)\n\n')

    def kept(self, text, value, rule='f'):
        m = load(self.TYPES + text)[0]
        it = Interp(m)
        out = it.forward(m.rules[rule], (), value)
        got = ([e.tag for e in it.journal], it.journal_bits())
        self.assertEqual(deep(it.rewind(m.rules[rule], (), out)), deep(value))
        self.assertEqual(it.journal, [])
        return got

    def test_a_clause_choice_is_kept_only_where_the_output_leaves_one(self):
        table = 'rule f takes (Bit, Bit) returns Bit\n    (0, 0) => 0\n    (0, 1) => 0\n    (1, 0) => 0\n    (1, 1) => 1\n'
        B = lambda x: Word(x, 'Bit')     # noqa: E731
        for a, b in ((0, 0), (0, 1), (1, 0)):
            self.assertEqual(self.kept(table, (B(a), B(b))), (['Chose'], 2))        # one of three
        self.assertEqual(self.kept(table, (B(1), B(1))), ([], 0))                   # the output 1 shows its clause
        m = load(table)[0]
        it = Interp(m)
        it.forward(m.rules['f'], (), (B(0), B(1)))
        self.assertEqual(it.journal[0].kids[2], W(3))                               # among the three that give 0
        # the first match decides, and each output still shows its clause: nothing is kept
        first = 'rule f takes I64 returns Opt\n    0 => None\n    n => Some(n)\n'
        self.assertEqual(self.kept(first, W(0)), ([], 0))
        self.assertEqual(self.kept(first, W(7)), ([], 0))
        # a right side that takes any output shares every output
        wide = 'rule f takes (Bit, I64) returns I64\n    (0, n) => n\n    (1, n) => 0 where\n        discard n\n'
        self.assertEqual(self.kept(wide, (B(0), W(5))), ([], 0))                    # 5 is not the second clause's 0
        self.assertEqual(self.kept(wide, (B(0), W(0))), (['Chose'], 1))
        self.assertEqual(self.kept(wide, (B(1), W(9))), (['Dropped', 'Chose'], 65))

    def test_a_dropped_value_is_charged_by_its_type(self):
        drop = 'rule f takes ({}, I64) returns I64\n    (x, n) => n where\n        discard x\n'
        for t, value, bits in (('Bit', Word(1, 'Bit'), 1), ('U8', Word(200, 'U8'), 8), ('Bool', True, 1),
                               ('Trit', True, 2), ('Trit', MAYBE, 2),                 # three values, whichever it holds
                               ('Hue', F_('Green', ()), 2),                           # one of three
                               ('Opt', F_('None', ()), 1), ('Opt', F_('Some', (W(4),)), 65),
                               ('Only', F_('Only', (W(4), True)), 65),                # one constructor: its fields
                               ('Shape', F_('Tri', (W(1), W(2))), 130),
                               ('(Bit, Hue)', (Word(0, 'Bit'), F_('Red', ())), 3)):
            self.assertEqual(self.kept(drop.format(t), (value, W(0))), (['Dropped'], bits), t)

    def test_only_the_constructors_still_possible_are_counted(self):
        # an earlier clause takes every Circle: what the second clause drops is one of two
        area = 'rule f takes Shape returns I64\n    Circle(r) => r\n    other => 0 where\n        discard other\n'
        self.assertEqual(self.kept(area, F_('Square', (W(4),))), (['Dropped', 'Chose'], 1 + 64 + 1))
        self.assertEqual(self.kept(area, F_('Tri', (W(1), W(2)))), (['Dropped', 'Chose'], 1 + 128 + 1))
        # the earlier clause takes only some Circles: a Circle is still possible, one of three
        some = 'rule f takes Shape returns I64\n    Circle(0) => 0\n    other => 1 where\n        discard other\n'
        self.assertEqual(self.kept(some, F_('Square', (W(4),))), (['Dropped'], 2 + 64))
        # a value made here by a constructor is that constructor
        made = ('rule f takes I64 returns I64\n    n => n where\n        w is Some(n)\n        add 1 to n\n'
                '        discard w\n')
        self.assertEqual(self.kept(made, W(7)), (['Dropped'], 64))

    def test_a_value_that_can_still_be_computed_is_dropped_for_nothing(self):
        again = 'rule f takes (I64, I64) returns I64\n    (a, b) => a where\n        t is a + 1\n        discard t\n        discard b\n'
        self.assertEqual(self.kept(again, (W(5), W(6))), (['Dropped', 'Dropped'], 64))
        # once what it was computed from has changed, the checker no longer shows that
        changed = again.replace('        discard t\n', '        add 1 to a\n        discard t\n')
        self.assertEqual(self.kept(changed, (W(5), W(6))), (['Dropped', 'Dropped'], 128))

    def test_the_charges_tell_the_inputs_apart(self):
        # for each output of a gate, the charges of the inputs that give it are the lengths of
        # a code for those inputs: none is charged less than the gate lost
        m = load(src('gates.selv'))[0]
        B = lambda x: Word(x, 'Bit')     # noqa: E731
        for name in ('and_gate', 'or_gate', 'nand_gate', 'and_table', 'and_least'):
            by_output = {}
            for a, b in itertools.product((0, 1), repeat=2):
                it = Interp(m)
                out = it.forward(m.rules[name], (), (B(a), B(b)))
                by_output.setdefault(out.v, []).append(it.journal_bits())
            for out, charges in by_output.items():
                self.assertLessEqual(sum(2.0 ** -c for c in charges), 1.0, (name, out))
        # the table and the least form keep nothing where the output is 1, and two bits otherwise
        for name in ('and_table', 'and_least'):
            it = Interp(m)
            it.forward(m.rules[name], (), (B(1), B(1)))
            self.assertEqual(it.journal_bits(), 0)
            it.forward(m.rules[name], (), (B(0), B(1)))
            self.assertEqual(it.journal_bits(), 2)

    def test_a_dropped_text_is_charged_its_length_and_its_bytes(self):
        # T1.  A Text is an array of bytes: 64 bits for its length and 8 a byte.  Charged 8 a
        # byte alone, "" dropped beside "a" and "b" was charged nothing, and the three charges
        # were not the lengths of a code.
        drop = 'rule f takes (Text, I64) returns I64\n    (t, n) => n where\n        discard t\n'
        charges = []
        for text, bits in (('', 64), ('a', 72), ('b', 72), ('hello', 104), ('é', 80)):
            self.assertEqual(self.kept(drop, (text, W(0))), (['Dropped'], bits), text)
            charges.append(bits)
        self.assertLessEqual(sum(2.0 ** -c for c in charges), 1.0)
        self.assertGreater(sum(2.0 ** -c for c in (0, 8, 8)), 1.0)      # what 8 a byte alone gave
        # inside a value of a declared type as well
        inside = ('type Tag\n    Tag(name: Text, on: Bit)\n\nrule f takes (Tag, I64) returns I64\n'
                  '    (t, n) => n where\n        discard t\n')
        self.assertEqual(self.kept(inside, (F_('Tag', ('ab', Word(1, 'Bit'))), W(0))), (['Dropped'], 64 + 16 + 1))

    def test_a_word_is_charged_by_its_declared_width_however_it_was_written(self):
        # 0.4.0 to 0.4.8.  A literal given where a narrower word is declared is that word: the interpreter
        # held it at a literal's width and charged 64 bits where the type says 8.
        m = load('rule k takes (U8, I64) returns I64\n    (n, m) => m where\n        discard n\n\n'
                 'rule p(w: U8) takes I64 returns I64\n    n => n where\n        t is w\n        add 1 to t\n'
                 '        discard t\n')[0]
        for value in ((Word(7, 'I64', True), W(1)), (Word(7, 'U8'), W(1))):      # a literal; a U8
            it = Interp(m)
            it.forward(m.rules['k'], (), value)
            self.assertEqual((it.journal_bits(), it.journal[0].kids[2].ty), (8, 'U8'), value)
        it = Interp(m)                                                           # a parameter too
        it.forward(m.rules['p'], (Word(200, 'I64', True),), W(0))
        self.assertEqual((it.journal_bits(), it.journal[0].kids[2].v, it.journal[0].kids[2].ty), (8, 201, 'U8'))

    def test_a_decision_is_charged_by_the_answers_installed(self):
        # Q13.  A decision can be settled by each answer installed for Decide, or by the world.
        # Charged by the answers that were asked, those N + 1 charges stop being the lengths
        # of a code at fifteen answers: the sums are 1, 33/32 and 33/32 for 14, 15 and 16.
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import generated_04
        m = load(generated_04.DECIDE_HEAD + 'rule gate takes Trit returns (Trit, Bool) uses Decide\n'
                 '    t => (t, d) where\n        d is decide t\n')[0]
        for n, bits in ((1, 2), (3, 3), (14, 5), (15, 5), (16, 6)):
            charges = []
            for way in range(n + 1):                 # the answer that settles it; n: the world
                it = Interp(m, io.StringIO(), fixed(True))
                stack = ['Yes' if i == way else 'Defer' for i in range(n)]          # innermost first
                it.handlers += [[Inst(a, (), W(0))] for a in reversed(stack)]
                it.forward(m.rules['gate'], (), MAYBE)
                (charge, entry), = [(c, e) for c, e in zip(it.charges, it.journal) if e.tag == 'Decided']
                self.assertEqual(entry.kids[2].v, min(way + 1, n))                    # how many were asked
                charges.append(charge)
            self.assertEqual(set(charges), {bits}, n)                                # the same whoever settled it
            self.assertLessEqual(sum(2.0 ** -c for c in charges), 1.0, n)
            old = sum(2.0 ** -(1 + ((min(w + 1, n) + 1) - 1).bit_length()) for w in range(n + 1))
            self.assertEqual(old > 1.0, n >= 15, n)                                   # by the answers asked

    def test_epsilon_is_the_sum_of_the_charges(self):
        out, it = run_interp(src('accounting.selv', PROGS))
        self.assertEqual(out.split(), ['3', '0', '0', '0', '0', '7', '5', '9'])
        # 0; 66 = one of two Shapes + 64 + a choice of two; 130; 3 = a Trit + a choice; 3; 0; 64;
        # 104 = a Text of five bytes: 64 for its length and 8 a byte
        self.assertEqual(it.epsilon, 0 + 66 + 130 + 3 + 3 + 0 + 64 + 104)


class TestDeclaredTypes(unittest.TestCase):
    """A value is given only where its type is declared (R1).  `Bool` is a sub-shape of `Trit`:
    a Bool is given where a Trit is declared, and a Trit is never given where a Bool is.
    Toolchains 0.3.4 to 0.4.8 accepted the second, so a name declared Bool could hold `maybe`."""

    WHY = 'a Trit may be maybe and a Bool may not'
    @staticmethod
    def refusal(text):
        try:
            load(text)
        except CheckError as e:
            return str(e)
        return None

    def test_a_trit_is_refused_where_a_bool_is_declared(self):
        # Site by site: the sixteen places a value is given where a type is declared; 0.4.8
        # accepted a Trit at fifteen of them, all but an instance's state.  With a Trit there the program is refused, with its reason, with nothing else wrong, and
        # with no failure of the toolchain.  The same program with a Bool there is accepted.
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import generated_04
        names = dict(f='f', g='g', t='t', b='b', put='put', get='get', Cell='Cell', Store='Store', Flag='Flag', P='I64')
        self.assertEqual(len(generated_04.DECL_SITES), 16)
        for site, template in generated_04.DECL_SITES:
            why = self.refusal(template.format(X='Trit', **names))
            self.assertIsNotNone(why, site)
            if site == 'the state an instance is made from':
                self.assertIn('takes a state of type Bool, found Trit', why)
            else:
                self.assertIn(self.WHY, why, site)
            self.assertNotIn('internal', why, site)
            self.assertEqual(len(why.splitlines()), 2, why)
            self.assertIsNone(self.refusal(template.format(X='Bool', **names)), site)

    def test_a_bool_is_given_where_a_trit_is_declared(self):
        # the other direction stands: a Bool is a Trit that happens to be decided
        m = load('rule lift takes Bool returns Trit\n    true <-> true\n    false <-> false\n\n'
                 'rule widen takes (Bool, Trit) returns (Bool, Trit)\n    (b, t) => (b, t) where\n'
                 '        set t to b\n\n'
                 'rule both(a: Bool, b: Trit) returns Trit\n    a and Trit(b)\n\n'
                 'rule known takes Trit returns Trit\n    t <-> t\n\n'
                 'rule main uses Output\n    output known(true)\n    output both(true, maybe)\n')[0]
        it = Interp(m)
        for b in (True, False):
            self.assertIs(it.forward(m.rules['lift'], (), b), b)
            self.assertIs(it.undo(m.rules['lift'], (), b), b)
        # read backward, the embedding refuses what is no Bool: `maybe` is outside its image
        self.assertRaises(Fault, it.undo, m.rules['lift'], (), MAYBE)
        self.assertEqual(run_interp('rule lift takes Bool returns Trit\n    true <-> true\n    false <-> false\n\n'
                                    'rule main uses Output\n    output lift(true)\n')[0].split(), ['true'])
        # `Trit(...)` takes a Bool or a Trit and nothing else
        self.assertIn('Trit(...) takes a Bool or a Trit',
                      self.refusal('rule f(n: I64) returns Trit\n    Trit(n)\n'))

    def test_no_certified_rule_decides_a_trit(self):
        # The rule 0.3.4 to 0.4.8 certified.  Given (maybe, true) it asked, kept a `Decided`
        # entry inside a rule written `<->`, and `undo` refused its output (XI.3, Part 2).
        was = ('rule f takes (Trit, Bool) returns (Trit, Bool, Bool)\n    (t, b) <-> (t, b, d) where\n'
               '        swap t and b\n        d is decide b\n')
        why = self.refusal(was)
        self.assertIsNotNone(why)
        self.assertIn('type mismatch in swap: Trit and Bool', why)
        self.assertIn(self.WHY, why)
        # with a Bool that is one, the certificate holds: nothing asked, nothing kept, undone
        m = load(was.replace('(Trit, Bool)', '(Bool, Bool)').replace('(Trit, Bool, Bool)', '(Bool, Bool, Bool)'))[0]
        r = m.rules['f']
        self.assertEqual(r.cls, 'bijection')
        for a, b in itertools.product((True, False), repeat=2):
            it = Interp(m, io.StringIO(), refuse)
            out = it.forward(r, (), (a, b))
            self.assertEqual((out, it.journal), ((b, a, a), []))
            self.assertEqual(it.undo(r, (), out), (a, b))

    def test_set_writes_its_value_in_the_cells_type(self):
        # `set n to 0` on a U8 ended the check with an internal failure, 0.4.0 to 0.4.8:
        # the value was held as a literal's I64 and then exchanged with the cell.  And the
        # value `set` replaced in a Trit was charged as a Bool, 1 bit or 2 by what it held.
        rule = 'rule g takes {0} returns {0}\n    n => n where\n        set n to {1}\n'
        for t, new, values, bits in (('U8', '0', [Word(7, 'U8')], 8), ('Bit', '1', [Word(0, 'Bit')], 1),
                                     ('I64', '0', [W(7)], 64), ('F64', '0', [2.5], 64),
                                     ('Bool', 'true', [True, False], 1),
                                     ('Trit', 'true', [True, False, MAYBE], 2)):
            m = load(rule.format(t, new))[0]
            charges = []
            for v in values:
                it = Interp(m)
                out = it.forward(m.rules['g'], (), v)
                if isinstance(out, Word):
                    self.assertEqual((out.v, out.ty), (int(new), t))
                charges.append(it.journal_bits())
                self.assertEqual(deep(it.rewind(m.rules['g'], (), out)), deep(v), t)
            self.assertEqual(set(charges), {bits}, t)
            self.assertLessEqual(sum(2.0 ** -c for c in charges), 1.0, t)
        # where the value cannot be written in the cell's type, a refusal with its reason
        why = self.refusal('rule g takes (U8, Trit) returns (U8, Trit)\n    p => p where\n        set p to (0, true)\n')
        self.assertIn("write the value in the cell's type", why)
        self.assertNotIn('internal', why)

    def test_a_request_is_given_arguments_of_its_declared_types(self):
        # 0.3.4 to 0.4.8 compared neither a request's arguments nor an answer's reply and state
        # with what the request and the answer declare: each program below was accepted
        self.assertIn('type mismatch in argument n of put: I64 and Text',
                      self.refusal('request Cell\n    put(n: I64) returns ()\n\nrule f(t: Text) uses Cell\n    ask put(t)\n'))
        self.assertIn('type mismatch in the reply of Store.get: I64 and Text',
                      self.refusal('request Cell\n    get() returns I64\n\nanswer Store for Cell takes Text\n'
                                   '    (get(), s) <-> (r, s) where\n        r is s\n'))
        self.assertIn('type mismatch in the state of Store.put: I64 and Text',
                      self.refusal('request Cell\n    put(n: Text) returns ()\n\nanswer Store for Cell takes I64\n'
                                   '    (put(f), s) => ((), f) where\n        discard s\n'))


class TestExtent(unittest.TestCase):
    """`<->` certifies one-to-one.  Whether a rule takes every input, and whether it gives
    every output, are reported apart, and only as far as they are established (V.2)."""

    def test_a_gate_is_a_permutation_and_an_ancilla_makes_an_embedding(self):
        m = load(src('gates.selv'))[0]
        for name in ('ccnot', 'cnot', 'toggle', 'trit_and', 'trit_or', 'trit_not', 'and_told'):
            self.assertEqual(extent(m, m.rules[name])[0], 'permutation', name)
            self.assertEqual(extent(m, m.rules[name].inverse)[0], 'permutation', name)
        for name in ('and_into', 'or_into', 'nand_into'):
            r = m.rules[name]
            self.assertEqual(r.cls, 'bijection')                 # the certificate: one-to-one on every input
            self.assertEqual(extent(m, r), ('embedding', 'run on all 4 inputs: defined on every one; it gives 4 of 8 outputs'))
            self.assertEqual(extent(m, r.inverse)[0], 'partial inverse')
            # its inverse is defined on its image and nowhere else
            taken = 0
            for y in itertools.product((0, 1), repeat=3):
                try:
                    Interp(m).undo(r, (), tuple(Word(b, 'Bit') for b in y))
                    taken += 1
                except Fault:
                    pass
            self.assertEqual(taken, 4)
        report = cli('check', os.path.join(EX, 'gates.selv')).stdout
        self.assertRegex(report, r'and_into\s+embedding\s')
        self.assertRegex(report, r'and_told\s+permutation\s')
        self.assertNotRegex(report, r'and_into\s+bijection')

    def test_a_rule_over_words_is_settled_by_its_steps_or_by_counting(self):
        head = 'rule f takes (I64, I64) returns {}\n    (a, b) <-> {} where\n'
        for returns, right, steps, kind, said in (
                ('(I64, I64)', '(a, b)', ['add a / 2 to b', 'swap a and b'], 'permutation', 'no step of its inverse can refuse'),
                ('(I64, I64, I64)', '(a, b, c)', ['c is 5', 'add a to c'], 'embedding', 'fewer inputs than outputs'),
                ('I64', 'a', ['b was 5'], 'partial inverse', 'fewer outputs than inputs'),
                ('(I64, I64)', '(a, b)', ['add 7 / a to b'], 'one-to-one', 'not established')):
            m = load(head.format(returns, right) + ''.join(f'        {s}\n' for s in steps))[0]
            got = extent(m, m.rules['f'])
            self.assertEqual(got[0], kind, steps)
            self.assertIn(said, got[1], steps)
        # a rule that calls a permutation, and gives back what one gave, is one
        calls = ('rule g(k: I64) takes I64 returns I64\n    n <-> n where\n        add k to n\n'
                 'rule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n        a is g(3)(a)\n'
                 '        b is undo g(2)(b)\n')
        m = load(calls)[0]
        self.assertEqual(extent(m, m.rules['f'])[0], 'permutation')

    def test_nothing_is_claimed_that_is_not_established(self):
        # a rule over arrays can be refused for an index; a clause that does not take every
        # value is partial; neither is called a permutation
        m = load(src('arrays.selv'))[0]
        for name in ('prefix_sum', 'reverse'):
            self.assertEqual(extent(m, m.rules[name]), ('one-to-one', 'defined on every input: not established; onto: not established'))
        m = load(src('shapes.selv'))[0]
        self.assertEqual(extent(m, m.rules['small'])[0], 'partial')
        self.assertEqual(extent(m, m.rules['magnitude']), (None, None))             # lossy: no extent to report
        # every rule the toolchain calls a permutation by its steps takes every input tried
        # and gives every output tried
        m = load(src('orbit.selv'))[0]
        r = m.rules['orbit']
        self.assertEqual(extent(m, r)[0], 'permutation')
        rng = random.Random(4)
        for _ in range(50):
            y = F_('Phase', (W(rng.randrange(-2 ** 63, 2 ** 63)), W(rng.choice([0, 1, -1, rng.randrange(-2 ** 63, 2 ** 63)]))))
            x = Interp(m).undo(r, (W(3), W(2)), y)
            self.assertEqual(Interp(m).forward(r, (W(3), W(2)), x), y)

    def test_an_answer_s_rules_report_their_extent(self):
        # an answer's rule for one request takes the request's fields with the state and gives
        # the reply with the state; its extent is settled as any rule's is, and reported with
        # the answer, so that an embedding is never shown as a bare "bijection"
        m = load(src('prototypes.selv'))[0]
        self.assertEqual(extent(m, m.answers['Count'].ops['bump']),
                         ('permutation', 'defined on every input (no step of it can refuse); '
                                         'onto (no step of its inverse can refuse)'))
        m = load(src('messages.selv'))[0]
        # a deposit always replies Deposited: a Receipt it never gives, so more outputs than inputs
        self.assertEqual(extent(m, m.answers['Ledger'].ops['deposit']),
                         ('embedding', 'defined on every input (no step of it can refuse); '
                                       'not onto (fewer inputs than outputs)'))
        text = ('request Peek\n    peek() returns Bit\n'
                'answer Lamp for Peek takes Bit\n    (peek(), b) <-> (c, b) where\n        c is b\n'
                'request Poke\n    poke() returns ()\n'
                'answer Cell for Poke takes Array(I64)\n    (poke(), a) <-> ((), a) where\n        add 1 to a[0]\n')
        m = load(text)[0]
        r = m.answers['Lamp'].ops['peek']
        self.assertEqual(extent(m, r), ('embedding', 'run on all 2 inputs: defined on every one; it gives 2 of 4 outputs'))
        self.assertEqual(extent(m, r.inverse)[0], 'partial inverse')
        # an index can refuse, and an array's values are not counted: nothing is claimed
        self.assertEqual(extent(m, m.answers['Cell'].ops['poke']),
                         ('one-to-one', 'defined on every input: not established; onto: not established'))
        path = os.path.join(tempfile.mkdtemp(), 'lamp.selv')
        with open(path, 'w') as f:
            f.write(text)
        lines = cli('check', path).stdout.splitlines()
        self.assertIn('  Lamp                 bijection       (answer for Peek) certified', lines)
        self.assertIn('    peek               embedding       run on all 2 inputs: defined on every one; '
                      'it gives 2 of 4 outputs', lines)


class TestDeclarations(unittest.TestCase):
    """A declaration and a program are forms a rule takes apart (VIII.1).  A declaration is
    not Code, and holding one grants nothing."""

    def test_the_form_types_are_the_prelude_s_own_text(self):
        m = load('')[0]
        text = src('prelude.selv', os.path.join(ROOT, 'selvage'))
        for t in ('Parts', 'Code', 'TypeExpr', 'Param', 'Slot', 'Ctor', 'Op', 'Declaration', 'Program'):
            self.assertIn(t, m.types)
            self.assertRegex(text, rf'(?m)^type {t}\b')
            self.assertIn(t, m.decls)                    # so a program can ask for its definition
        self.assertEqual(sorted(m.types['Declaration'].ctors), ['AnswerDecl', 'RequestDecl', 'RuleDecl', 'TypeDecl'])
        # a declaration is not Code: no constructor of Code is one, and `mirror` does not take one
        self.assertFalse(set(m.types['Declaration'].ctors) & set(m.types['Code'].ctors))
        with self.assertRaises(CheckError) as c:
            load('rule f returns Code\n    mirror(definition(quote mirror))\n')
        self.assertIn('Code and Declaration', str(c.exception))

    def test_the_example_takes_declarations_and_the_program_apart(self):
        out, _ = run_interp(src('declarations.selv'))
        lines = out.splitlines()
        self.assertEqual(lines[:4], ['rule tick(k: I64) takes (I64, I64) returns (I64, I64)', '    (n, m) <-> (n, m) where',
                                     '        add k to n', '        swap n and m'])
        self.assertEqual(lines[4:7], ['("answer", "Cell")', '("type", "Light")', '("request", "Store")'])
        # the inverse written in the language is the one the toolchain derives, but for its name
        m = load(src('declarations.selv'))[0]
        derived = cli('invert', os.path.join(EX, 'declarations.selv'), 'tick').stdout.splitlines()
        self.assertEqual(lines[7:11], [derived[0].replace('rule undo tick', 'rule tick')] + derived[1:])
        self.assertEqual(lines[11:13], ['true', '10'])
        self.assertEqual(lines[13], 'Part("Light", Part("Store", Part("Cell", Part("tick", Part("count", Part("kind", '
                                    'Part("each_mirrored", Part("turned", Part("names", Part("main", NoParts))))))))))')
        self.assertEqual((m.rules['turned'].cls, m.rules['each_mirrored'].cls), ('partial', 'bijection'))

    def test_every_declaration_is_held_as_a_value_and_written_back(self):
        from selvage.declared import declared, undeclared, is_declared
        from selvage.forms import encode, show
        n = 0
        for text in [src('prelude.selv', os.path.join(ROOT, 'selvage'))] + [src(f) for f in ALL_EXAMPLES] + \
                [src('every_form.selv', PROGS)]:
            prog = parse(text)
            for d in prog.kids:
                v = declared(d)
                n += 1
                self.assertTrue(is_declared(v) and not is_declared(d), d.kids[0])
                self.assertEqual(encode(undeclared(v)), encode(d), d.kids[0])
                self.assertEqual(show(v), '\n'.join(program_text(Form('Program', (d,))).rstrip('\n').split('\n')), d.kids[0])
            self.assertEqual(show(declared(prog)) + '\n', program_text(prog))
        self.assertGreater(n, 100)
        # a value that is not put together as a declaration is refused, not printed as one
        for bad in (Form('RuleDecl', ('f', Form('NoParts', ()), 3, 4, 5, 6)), Form('Program', (Form('Part', (1, 2)),))):
            with self.assertRaises(Fault):
                undeclared(bad)

    def test_definition_gives_rules_answers_types_and_requests(self):
        head = src('declarations.selv').split('rule main')[0]
        show_all = 'rule main uses Output\n' + ''.join(f'    output definition(quote {n})\n'
                                                      for n in ('Light', 'Store', 'Cell', 'Root', 'Journal', 'Code'))
        out, _ = run_interp(head + show_all)
        self.assertIn('type Light\n    Red\n    Green\n', out)
        self.assertIn('request Store\n    put(v: I64) returns ()\n', out)
        self.assertIn('answer Cell for Store takes I64\n    (put(v), s) => ((), v) where\n        discard s\n', out)
        self.assertIn('answer Root for System, Witness, Refusal takes Journal\n', out)
        self.assertIn('type Journal\n    Empty\n    Kept(entry: Any, rest: Journal)\n', out)
        self.assertIn('type Code\n    Literal(value: Any)\n', out)
        r = run_refused(head + 'rule main uses Output\n    output definition(quote nothing_here)\n')
        self.assertIn('nothing is declared under the name nothing_here', r)

    def test_the_program_is_a_form(self):
        text = src('declarations.selv')
        out, _ = run_interp(text.split('rule main')[0] + 'rule main uses Output\n    output program()\n')
        self.assertEqual(out, program_text(parse(text.split('rule main')[0] + 'rule main uses Output\n    output program()\n')))
        with self.assertRaises(CheckError) as c:
            load('rule main uses Output\n    output program(1)\n')
        self.assertIn('takes nothing', str(c.exception))

    def test_all_of_the_code_is_written_to_be_taken_apart(self):
        # `sequence` writes blocks as sequences and tuples as lists of parts; `block` writes
        # them back; quoted code and literals are data and are left as they are
        probe = ('rule members takes Code returns I64\n    Tupled(NoParts) => 0\n'
                 '    Tupled(Part(a, rest)) => n where\n        n is members(Tupled(rest))\n        add 1 to n\n        discard a\n'
                 'rule main uses Output, System\n'
                 '    c is quote (p, q + 1, (r, s))\n'
                 '    output members(sequence(c))\n'
                 '    output block(sequence(c)) = c\n'
                 '    output sequence(quote f(quote (a, b))) = quote f(quote (a, b))\n')
        out, _ = run_interp(probe)
        self.assertEqual(out.split(), ['3', 'true', 'false'])
        m = load(src('every_form.selv', PROGS))[0]
        from selvage.invert import as_sequence, as_block
        from selvage.forms import encode
        for name, r in m.rules.items():
            if r.kind == 'clauses' and not r.backward:
                for c in r.clauses:
                    whole = as_sequence(c, whole=True)
                    self.assertNotIn('Tuple(', encode(whole).replace('TupleType(', ''))
                    self.assertNotIn('Block(', encode(whole))
                    self.assertEqual(encode(as_block(whole, whole=True)), encode(c), name)

    def test_holding_a_declaration_grants_nothing(self):
        # Root's declaration can be read and printed; no Root can be made from it, and a
        # declaration a program builds declares nothing and runs nothing
        head = 'rule main uses Output\n'
        out, _ = run_interp(head + '    d is definition(quote Root)\n    output identity(d) = identity(definition(quote Root))\n')
        self.assertEqual(out.split(), ['true'])
        for text, why in (
                (head + '    d is definition(quote Root)\n    output Root from Empty\n', 'sealed'),
                (head + '    d is RuleDecl("sneak", NoParts, TypeName(""), TypeName(""), NoParts, NoParts)\n    output sneak()\n',
                 'unknown rule sneak'),
                ('rule main uses Output, System\n    ask keep(definition(quote Root))\n', 'sealed')):
            with self.assertRaises(CheckError) as c:
                load(text)
            self.assertIn(why, str(c.exception), text)
        with self.assertRaises(CheckError) as c:
            load(head + '    output evaluate(definition(quote mirror))\n')
        self.assertIn('holding it runs nothing', str(c.exception))
        # and a step handed to `evaluate` as a value is refused in the run, not run
        r = run_refused(head + '    output evaluate(Discard("x"))\n')
        self.assertIn('evaluate runs an expression, and Discard is not one', r)

    def test_a_name_is_not_given_back_against_an_expression_that_reads_it(self):
        with self.assertRaises(CheckError) as c:
            load('rule f takes I64 returns I64\n    n <-> m where\n        m is 5\n        n was 0 + n\n')
        self.assertIn('gives n back against an expression that reads it', str(c.exception))
        self.assertNotIn('internal', str(c.exception))


class TestCensus(unittest.TestCase):
    """Nothing in a program's structure escapes being a form, and the census establishes each
    of its columns by doing it (VIII.1)."""

    def test_every_form_the_parser_writes_is_taken_apart_and_put_together(self):
        from selvage.census import census, parser_tags, REWRITTEN
        m = load(src('every_form.selv', PROGS))[0]
        rows, escaped, unmet, round_trips = census(m)
        self.assertEqual((escaped, unmet, round_trips), ({}, [], []))
        self.assertTrue(all(apart and together for _, _, _, apart, together in rows))
        met = {tag for _, tag, _, _, _ in rows}
        # every tag the parser can write is met as a constructor, or is one of the lists a
        # value writes as parts
        for tag in parser_tags():
            self.assertTrue(tag in met or tag in REWRITTEN or tag in ('Field', 'Program'), tag)
        self.assertGreaterEqual(len([1 for t, *_ in rows if t == 'Code']), 48)
        self.assertEqual({t for t, *_ in rows} >= {'Code', 'Parts', 'TypeExpr', 'Param', 'Slot', 'Ctor', 'Op',
                                                   'Declaration', 'Program'}, True)

    def test_nothing_escapes_in_any_example(self):
        from selvage.census import census
        for f in ALL_EXAMPLES:
            rows, escaped, _, round_trips = census(load(src(f))[0])
            self.assertEqual((escaped, round_trips), ({}, []), f)
            self.assertTrue(all(apart and together for _, _, _, apart, together in rows), f)

    def test_the_census_reports_what_it_finds(self):
        r = cli('census', os.path.join(PROGS, 'every_form.selv'))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertRegex(r.stdout, r'Code\s+48 of 49\s+\d+\s+yes\s+yes')
        self.assertIn('escapes (a tag that is no constructor of a form type): none', r.stdout)
        self.assertIn("the parser's tags this program does not use: none", r.stdout)
        self.assertIn('not forms: the answers installed around a run', r.stdout)
        # a tag with no constructor is reported, not passed over
        from selvage import census as cs
        m = load(src('every_form.selv', PROGS))[0]
        del m.ctors['Index']
        self.assertIn('Index', cs.census(m)[1])


class TestSemanticContracts(unittest.TestCase):
    """The five places the description's guarantees meet the implementation."""

    DECIDERS = ('answer Maybe for Decide takes I64\n    (settle(q, c), n) => (maybe, n) where\n'
                '        add 1 to n\n        discard q\n        discard c\n'
                'answer Yes for Decide takes I64\n    (settle(q, c), n) => (true, n) where\n'
                '        add 1 to n\n        discard q\n        discard c\n'
                'rule gate takes Trit returns (Trit, Bool) uses Decide\n'
                '    t => (t, d) where\n        d is decide t\n'
                'rule crisp takes Bool returns (Bool, Bool) uses Decide\n'
                '    b <-> (b, d) where\n        d is decide b\n')

    def test_history_is_a_copy_into_an_empty_name_and_its_inverse_uncopies(self):
        from selvage.checker import definition_of
        from selvage.invert import invert
        from selvage.printer import code_text
        m = load('')[0]
        root = m.answers['Root']
        self.assertEqual(root.ops['history'].cls, 'bijection')
        self.assertIs(m.op_rule('Object', 'history'), root.ops['history'])
        self.assertIn('h is j', code_text(definition_of(m, root)))
        self.assertIn('h was j', code_text(invert(definition_of(m, root))))
        out, it = run_interp(TestJournalContract.PROG + 'rule main uses Output, System, Witness\n'
                             '    v is drop_a((1, 2))\n    h is ask history()\n    output h = h\n')
        self.assertEqual(out, 'true\n')

    def test_the_escalation_path_is_reconstructed_from_entry_code_and_answers(self):
        m = load(self.DECIDERS)[0]
        it = Interp(m)
        outer, inner = [Inst('Yes', (), W(0))], [Inst('Maybe', (), W(0))]
        it.handlers += [outer, inner]
        out = it.forward(m.rules['gate'], (), MAYBE)
        self.assertEqual(out, (MAYBE, True))
        e = it.journal[-1]
        self.assertEqual((e.tag, e.kids[2].v, e.kids[3]), ('Decided', 2, False))   # two asked; an answer settled it
        self.assertEqual(it.rewind(m.rules['gate'], (), out), MAYBE)
        self.assertEqual((outer[0].state, inner[0].state, it.journal), (W(0), W(0), []))

    def test_a_statically_crisp_decide_is_not_world_input(self):
        m = load(self.DECIDERS)[0]
        self.assertEqual((m.rules['crisp'].cls, m.rules['gate'].cls), ('bijection', 'lossy'))
        it = Interp(m)
        self.assertEqual(it.undo(m.rules['crisp'], (), it.forward(m.rules['crisp'], (), True)), True)

    def test_a_clause_choice_is_kept_after_the_entries_of_its_clause(self):
        m = load(TestJournalContract.PROG +
                 'rule pick takes (Bool, I64, I64) returns I64\n'
                 '    (true, a, b) => r where\n        r is drop_a((a, b))\n'
                 '    (false, a, b) => r where\n        r is drop_b((b, a))\n')[0]
        it = Interp(m)
        for v in ((True, W(1), W(2)), (False, W(3), W(4))):
            out = it.forward(m.rules['pick'], (), v)
            self.assertEqual([(e.tag, e.kids[1]) for e in it.journal],
                             [('Dropped', 'drop_a' if v[0] else 'drop_b'), ('Chose', 'pick')])
            self.assertEqual(it.rewind(m.rules['pick'], (), out), v)
            self.assertEqual(it.journal, [])

    def test_a_rewind_is_bound_to_the_newest_run_and_its_exact_output(self):
        m = load(src('orbit.selv'))[0]
        it = Interp(m)
        r = m.rules['damped_orbit']
        out1 = it.forward(r, (W(10), W(3)), Form('Phase', (W(1000), W(5))))
        out2 = it.forward(r, (W(10), W(3)), Form('Phase', (W(2000), W(9))))
        with self.assertRaises(Fault):            # same rule, older run
            it.rewind(r, (W(10), W(3)), out1)
        self.assertEqual(len(it.journal), 6)      # refused before anything was taken back
        with self.assertRaises(Fault):            # newest run, wrong output
            it.rewind(r, (W(10), W(3)), Form('Phase', (W(0), W(0))))
        self.assertEqual(it.rewind(r, (W(10), W(3)), out2), Form('Phase', (W(2000), W(9))))
        self.assertEqual(it.rewind(r, (W(10), W(3)), out1), Form('Phase', (W(1000), W(5))))

    def test_a_rewind_is_bound_by_the_canonical_form_and_not_by_a_hash(self):
        from unittest import mock
        import selvage.interp
        m = load(src('orbit.selv') + 'rule keep_first takes (F64, F64) returns F64\n'
                 '    (a, b) => a where\n        discard b\n')[0]
        it = Interp(m)
        r, start = m.rules['damped_orbit'], Form('Phase', (W(1000), W(5)))
        out = it.forward(r, (W(10), W(3)), start)
        # were every identity the same, a rewind naming another output would still be refused
        with mock.patch.object(selvage.interp, 'identity', lambda v, refs=None: 'one-hash'):
            with self.assertRaises(Fault):
                it.rewind(r, (W(10), W(3)), Form('Phase', (W(0), W(0))))
            self.assertEqual(len(it.journal), 3)
        self.assertEqual(it.rewind(r, (W(10), W(3)), out), start)
        # the form compared is the canonical one: every NaN is the one NaN, and -0.0 is not 0.0
        f = m.rules['keep_first']
        nan = it.forward(f, (), (float('nan'), 1.0))
        self.assertTrue(it.rewind(f, (), float('nan'))[1] == 1.0)
        zero = it.forward(f, (), (0.0, 2.0))
        with self.assertRaises(Fault):
            it.rewind(f, (), -0.0)
        self.assertEqual(it.rewind(f, (), zero), (0.0, 2.0))

    def test_replay_matches_the_question_and_its_context_and_not_the_key(self):
        import json
        from selvage.deciders import replay
        prog = ('rule ask_twice(t: Trit, u: Trit) returns (Bool, Bool, Bool) uses Decide, System\n'
                '    a is decide t\n    b is decide t\n    c is decide u or t\n    (a, b, c)\n')
        m = load(prog)[0]
        replies = iter([True, False, True])
        it = Interp(m, None, lambda record: next(replies))
        first = it.call_expr_rule(m.rules['ask_twice'], (MAYBE, MAYBE))
        self.assertEqual(first, (True, False, True))
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'record.json')
            with open(path, 'w') as f:
                json.dump(it.decisions, f)
            # the same question asked twice was answered differently: replay gives each reply once, in order
            again = Interp(m, None, replay(path)).call_expr_rule(m.rules['ask_twice'], (MAYBE, MAYBE))
            self.assertEqual(again, first)
            run = lambda: Interp(m, None, replay(path)).call_expr_rule(m.rules['ask_twice'], (MAYBE, MAYBE))  # noqa: E731

            def refused(records, why):
                with open(path, 'w') as f:
                    json.dump(records, f)
                with self.assertRaises(Fault) as cm:
                    run()
                self.assertIn(why, str(cm.exception))
            # a record with the right key and another question is not the question asked
            refused([dict(d, question='u') for d in it.decisions[:1]] + it.decisions[1:], 'the next recorded decision is for `u`')
            # nor is one with another context
            refused([dict(d, context={'t': 'true'}) for d in it.decisions], 'the next recorded decision is for')
            # in order, and nothing is searched for: the right records in another order are refused
            refused([it.decisions[2], it.decisions[0], it.decisions[1]], 'the next recorded decision is for `u or t`')
            # each record is used once: one record cannot answer the same question twice
            refused(it.decisions[:1], 'the record has no decision left')
            refused(it.decisions[:1] * 3, 'the next recorded decision is for `t`')      # the third asks `u or t`

    def test_kleene_logic_is_a_verified_gate_circuit(self):
        from selvage.lineage import verify
        m = load('')[0]
        for n in ('trit_and', 'trit_or', 'trit_not'):
            self.assertEqual(m.rules[n].cls, 'bijection')
        self.assertEqual(verify(m, ('kleene',))[:2], (21, 0))

    def test_repeat_while_is_refused_in_clause_rules(self):
        with self.assertRaises(CheckError):
            load('rule f takes I64 returns I64\n    a <-> a where\n        repeat while a > 0\n'
                 '            subtract 1 from a\n')

    def test_repeat_n_times_is_a_count(self):
        from selvage.lexer import SyntaxFault
        # A2: `repeat n times` is `repeat with i from 1 to n`, and is not the language's.  It is
        # refused where it was written, in a clause rule and in an expression rule, with what replaces it
        for loop in ('repeat a times', 'repeat 3 times'):
            for text in ('rule f takes I64 returns I64\n    a <-> a where\n        ' + loop +
                         '\n            subtract 1 from a\n',
                         'rule f(a: I64) returns I64\n    n is a\n    ' + loop + '\n        set n to n - 1\n    n\n'):
                with self.assertRaises(SyntaxFault) as e:      # refused as it is read, before any check
                    load(text)
                self.assertIn('count from 1 to n', str(e.exception), loop)
        out, _ = run_interp('rule main uses Output\n    s is 0\n    repeat with i from 1 to 4\n        add i to s\n'
                            '    repeat with i from 1 to 0\n        add 100 to s\n    output s\n')
        self.assertEqual(out.strip(), '10')                 # from 1 to 0 runs no times, as `repeat 0 times` did
        self.assertNotIn('times', selvage.parser.KEYWORDS)
        self.assertEqual(len(selvage.parser.KEYWORDS), 38)


class TestSoundness(unittest.TestCase):
    """R4 for the cells a step changes and the parameters of what it consumes; sameness on
    the canonical form; and generated rules, each checked for a round trip."""

    HEAD = ('rule f takes (Array(I64), Array(I64), I64) returns (Array(I64), Array(I64), I64)\n'
            '    (a, b, x) <-> (a, b, x) where\n        ')

    def test_r4_an_index_may_not_read_what_its_step_changes(self):
        for body in ('swap a[a[0]] and a[1]', 'add 1 to a[a[0]]', 'swap a[b[0]] and b[0]',
                     'swap x and a[x]', 'subtract 2 from a[x + a[1]]', 'set a[a[0]] to 5'):
            with self.assertRaises(CheckError) as c:
                load(self.HEAD + body + '\n')
            self.assertIn('R4', str(c.exception), body)
        for body in ('swap a[length(a) - 1] and a[0]', 'add x to a[length(a) - 1]',
                     'swap a[b[0]] and a[b[1]]', 'swap a and b', 'add a[1] to b[x]'):
            self.assertEqual(load(self.HEAD + body + '\n')[0].rules['f'].cls, 'bijection', body)
        self.assertEqual(load('')[0].rules['ripple_add'].cls, 'bijection')

    def test_an_uncompute_is_proved_only_in_the_pattern_that_bound_it(self):
        # obligation O5 (XI.3): proved means the same pattern, the same expression, nothing changed
        rule = ('rule f takes (I64, I64, I64) returns (I64, I64, I64)\n    (x, y, z) <-> (x, y, z) where\n'
                '        (a, b) is (x, y)\n        add a to z\n        {} was (x, y)\n')
        same, other = load(rule.format('(a, b)'))[0], load(rule.format('(b, a)'))[0]
        self.assertEqual(len(same.proved) - len(other.proved), 2)    # in the rule and in its inverse
        v = (W(1), W(2), W(0))
        y = Interp(same).forward(same.rules['f'], (), v)
        self.assertEqual(Interp(same).undo(same.rules['f'], (), y), v)
        # given back in another pattern, the uncompute is checked when it runs, and is false here
        with self.assertRaises(Fault) as c:
            Interp(other).forward(other.rules['f'], (), v)
        self.assertIn('is not what it was computed from', str(c.exception))
        w = (W(2), W(2), W(0))       # where it is true, the run and its inverse agree
        self.assertEqual(Interp(other).undo(other.rules['f'], (), Interp(other).forward(other.rules['f'], (), w)), w)

    def test_r4_holds_under_either_arrow(self):
        lossy = self.HEAD.replace('<->', '=>')
        for body in ('set a[a[0]] to 5', 'swap a[a[0]] and a[1]\n        set x to 0',
                     'add 1 to a[a[0]]\n        set x to 0', 'set x to 0\n        swap x and a[x]'):
            with self.assertRaises(CheckError) as c:
                load(lossy + body + '\n')
            self.assertIn('R4', str(c.exception), body)
        for body in ('set a[b[0]] to x', 'set x to a[1]\n        add x to b[0]'):
            self.assertEqual(load(lossy + body + '\n')[0].rules['f'].cls, 'lossy', body)

    def test_r4_a_parameter_may_not_read_what_its_call_consumes(self):
        with self.assertRaises(CheckError) as c:
            load('rule g(k: I64) takes I64 returns I64\n    x <-> x where\n        add k to x\n'
                 'rule f takes I64 returns I64\n    a <-> y where\n        y is g(a)(a)\n')
        self.assertIn('R4', str(c.exception))
        self.assertNotIn('internal', str(c.exception))

    def test_sameness_is_equality_on_the_canonical_form(self):
        out, _ = run_interp(src('sameness.selv', PROGS))
        self.assertEqual(out.splitlines(), ['(0.0, nan)', '0.0', '2.5', 'false', 'true', 'Reading(nan, -0.0)'])
        with self.assertRaises(Fault):
            run_interp(src('sameness_refused.selv', PROGS))

    def test_unpacking_an_instance_checks_its_image(self):
        m = load('request R\n    get() returns I64\nanswer A(k: I64) for R takes I64\n'
                 '    (get(), s) <-> (v, s) where\n        v is s + k\n'
                 'rule pack(k: I64) takes I64 returns A\n    s <-> i where\n        i is A(k) from s\n'
                 'rule zero(k: I64) takes A returns A\n    c => c where\n'
                 '        c was A(k) from n\n        set n to 0\n        c is A(k) from n\n')[0]
        it = Interp(m)
        self.assertEqual((m.rules['pack'].cls, m.rules['zero'].cls), ('bijection', 'lossy'))
        i = it.forward(m.rules['pack'], (W(7),), W(5))
        self.assertEqual(it.undo(m.rules['pack'], (W(7),), i), W(5))
        with self.assertRaises(Fault):
            it.undo(m.rules['pack'], (W(7),), Inst('A', (W(99),), W(5)))
        z = it.forward(m.rules['zero'], (W(7),), Inst('A', (W(7),), W(42)))
        self.assertEqual(z, Inst('A', (W(7),), W(0)))
        self.assertEqual(it.rewind(m.rules['zero'], (W(7),), z), Inst('A', (W(7),), W(42)))

    def test_the_description_s_code_blocks_check(self):
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import check_description
        results = check_description.check(os.path.join(ROOT, 'SPEC.md'))
        self.assertEqual([r for r in results if r[2] == 'FAILS'], [])
        self.assertGreaterEqual(sum(1 for r in results if r[2] in ('checks', 'prelude', 'inverse')), 12)
        self.assertIn('refused', {r[2] for r in results})          # a refused example is refused, for its reason

    def test_a_refused_example_is_checked_for_its_reason(self):
        # F7: a block may show a refused program; it must be refused, and for the reason it gives
        sys.path.insert(0, os.path.join(ROOT, 'tools'))
        import check_description
        block = '```selvage\n# refused: {}\nrule f takes (I64, I64) returns (I64, I64)\n    (a, b) <-> (a, b) where\n        {}\n```\n'
        doc = (block.format('the update reads its own target', 'add a to a')
               + block.format('the update reads its own target', 'add b to a')        # accepted: not refused at all
               + block.format('a lossy rule writes', 'add a to a'))                    # refused, for another reason
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'doc.md')
            with open(path, 'w') as f:
                f.write(doc)
            verdicts = [r[2] for r in check_description.check(path)]
        self.assertEqual(verdicts, ['refused', 'FAILS', 'FAILS'])

    def test_a_generator_first_requires_its_prelude_to_be_accepted(self):
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        from unittest import mock
        import generated_04
        with mock.patch.object(generated_04, 'refusal', lambda text: 'the prelude is broken' if text == '' else None):
            for name, part in generated_04.PARTS:
                stats, findings = part(5, 1)
                self.assertEqual([f[0] for f in findings], ['the toolchain refuses its own prelude'], name)

    def test_generated_rules_round_trip(self):
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import roundtrip_gen
        certified, refused, findings = roundtrip_gen.run(programs=200, seed=7)
        self.assertEqual(findings, [])
        self.assertGreater(certified, 40)
        self.assertGreater(refused, 40)


class TestBuiltValues(unittest.TestCase):
    def test_a_literal_in_a_constructor_takes_the_field_s_type(self):
        # a side that is built gives each literal the type its place declares, inside a
        # constructor as elsewhere: what `undo` gives back is the same value, not one that prints alike
        text = ('type Hue\n    Red\n    Green\ntype Lamp\n    Lamp(on: Bit, hue: Hue)\n'
                'rule strike takes (Bit, Lamp) returns Bit\n    (b, Lamp(1, Red)) <-> b\n'
                'rule light takes Bit returns (Bit, Lamp)\n    b <-> (b, Lamp(1, Red))\n')
        m = load(text)[0]
        lamp = Form('Lamp', (Word(1, 'Bit'), Form('Red', ())))
        x = (Word(0, 'Bit'), lamp)
        it = Interp(m)
        back = it.undo(m.rules['strike'], (), it.forward(m.rules['strike'], (), x))
        self.assertEqual(identity(back), identity(x))
        self.assertEqual(identity(it.forward(m.rules['light'], (), Word(0, 'Bit'))), identity(x))

    def test_a_copied_instance_shares_nothing(self):
        # values are owned and copied, never shared (III.2): an instance whose state holds an
        # array is copied with its state, directly, inside a record and inside a tuple, so a
        # message to one copy leaves every other copy as it was
        text = ('request Poke\n    poke() returns ()\n'
                'answer Cell for Poke takes Array(I64)\n'
                '    (poke(), a) <-> ((), a) where\n        add 1 to a[0]\n'
                'type Box(c: Cell, k: I64)\n'
                'rule main uses Output\n'
                '    x is Cell from array(I64, 2)\n'
                '    y is x\n'
                '    r1 is x -> poke()\n'
                '    output (x, y)\n'
                '    bx is Box(Cell from array(I64, 2), 0)\n'
                '    by is bx\n'
                '    c is bx.c\n'
                '    r2 is c -> poke()\n'
                '    output (c, by)\n'
                '    t is (Cell from array(I64, 2), 0)\n'
                '    u is t\n'
                '    (d, k) is t\n'
                '    r3 is d -> poke()\n'
                '    output (d, u)\n')
        out, _ = run_interp(text)
        self.assertEqual(out.splitlines(), [
            '(Cell from [1, 0], Cell from [0, 0])',
            '(Cell from [1, 0], Box(Cell from [0, 0], 0))',
            '(Cell from [1, 0], (Cell from [0, 0], 0))'])


class TestCcnotTape(unittest.TestCase):
    """The CCNOT tape in the prelude (VI.6): wiring 1 of moop's tape, pinned to a trace of moop's
    own implementation; `draw` and `birth` prelude rules over the tape, so nothing else is the
    tape's draw; a draw a deterministic observation; a birth certified and taken back."""
    TAPE = ('rule two_draws takes CcnotTape returns (Bit, Bit, CcnotTape)\n    t <-> (x, y, t) where\n'
            '        (x, t) is draw(t)\n        (y, t) is draw(t)\n'
            'rule born takes CcnotTape returns (CcnotTape, CcnotTape)\n    t <-> (child, t) where\n'
            '        (child, t) is birth(t)\n')

    @staticmethod
    def make(la, lb, ones=True):
        return (f'    a is array(Bit, {la})\n    b is array(Bit, {lb})\n'
                + (f'    repeat with k from 0 to {la} - 1\n        set a[k] to 1\n'
                   f'    repeat with k from 0 to {lb} - 1\n        set b[k] to 1\n' if ones else '')
                + '    tape is CcnotTape(a, b, 0, 0)\n')

    def test_the_trace_is_moop_s(self):
        # moop's C implementation printed ccnot_tape.trace; the interpreter must print it byte for byte
        out, _ = run_interp(src('ccnot_tape.selv', PROGS))
        with open(os.path.join(PROGS, 'ccnot_tape.trace')) as f:
            self.assertEqual(out, f.read())

    @unittest.skipUnless(HAVE_CLANG, 'clang not available')
    def test_compiled_code_prints_moop_s_trace(self):
        # draws and births are rules, so they compile; the build prints the same trace
        tmp = tempfile.mkdtemp()
        r = build_and_run(os.path.join(PROGS, 'ccnot_tape.selv'), tmp)
        self.assertEqual(r.returncode, 0, r.stderr)
        with open(os.path.join(PROGS, 'ccnot_tape.trace')) as f:
            self.assertEqual(r.stdout, f.read())

    def test_draws_and_births_are_taken_back(self):
        out, _ = run_interp(self.TAPE + 'rule main uses Output\n' + self.make(8, 13) +
                            '    start is tape\n    (x, y, t) is two_draws(tape)\n'
                            '    (child, p) is born(t)\n    t2 is undo born((child, p))\n'
                            '    back is undo two_draws((x, y, t2))\n    output back = start\n')
        self.assertEqual(out.strip(), 'true')
        # a draw that the tape did not give is not taken back: a draw is an embedding
        why = run_refused(self.TAPE + 'rule main uses Output\n' + self.make(8, 13) +
                          '    (x, y, t) is two_draws(tape)\n    output undo two_draws((Bit(1) - x, y, t))\n')
        self.assertIn('is not what it was computed from', why)

    def test_a_tape_needs_two_cells(self):
        # R4 guards the tick when it runs: an empty tape divides by zero, and a one-cell tape
        # would make a target of a control
        for la, lb, needle in ((0, 13, 'division by zero'), (1, 13, 'R4'), (8, 1, 'R4')):
            why = run_refused('rule main uses Output\n' + self.make(la, lb, ones=False) +
                              '    (d, t) is draw(tape)\n    output d\n')
            self.assertIn(needle, why, (la, lb))
        out, _ = run_interp('rule main uses Output\n' + self.make(2, 2) + '    (d, t) is draw(tape)\n    output d\n')
        self.assertEqual(out.strip(), '0')

    def test_on_its_domain_the_tick_is_a_permutation(self):
        # every tape of the domain D with 2 or 3 cells on each side, every head position: the tick
        # maps D onto D one to one; a draw and a birth are one to one, and not onto (VI.6)
        from selvage.interp import deep_copy
        m = load('')[0]
        tick, draw, birth = m.rules['tape_tick'], m.rules['draw'], m.rules['birth']
        it = Interp(m)
        states = 0
        for la, lb in itertools.product((2, 3), repeat=2):
            domain = set()
            ticked, drawn, born = set(), set(), set()
            for bits in range(2 ** (la + lb)):
                for i, j in itertools.product(range(la), range(lb)):
                    a = Arr('Bit', [W((bits >> k) & 1, 'Bit') for k in range(la)])
                    b = Arr('Bit', [W((bits >> (la + k)) & 1, 'Bit') for k in range(lb)])
                    x = F_('CcnotTape', (a, b, W(i), W(j)))
                    domain.add(identity(x))
                    # a rule consumes its input and updates arrays in place: each run gets a copy
                    ticked.add(identity(it.forward(tick, (), deep_copy(x))))
                    bit, y = it.forward(draw, (), deep_copy(x))
                    self.assertEqual(bit, y.kids[0].data[y.kids[2].v])      # the bit is the cell under i
                    drawn.add(identity((bit, y)))
                    child, parent = it.forward(birth, (), deep_copy(x))
                    self.assertEqual((child.kids[2].v, child.kids[3].v), (0, 0))
                    born.add(identity((child, parent)))
            states += len(domain)
            self.assertEqual(ticked, domain, (la, lb))                    # into D, and onto it
            self.assertEqual(len(drawn), len(domain), (la, lb))           # one to one
            self.assertEqual(len(born), len(domain), (la, lb))
        self.assertEqual(states, 64 + 192 + 192 + 576)

    def test_outside_its_domain_every_input_is_refused(self):
        # a tape of fewer than two cells, or a head outside its tape, negative or not: refused
        # when it runs, with status 70, in both backends; never wrapped round
        tmp = tempfile.mkdtemp()
        for la, lb, i, j, needle in ((0, 13, 0, 0, 'division by zero'), (1, 13, 0, 0, 'R4'),
                                     (8, 1, 0, 0, 'R4'), (8, 13, 8, 0, 'index 8 is outside 0 to 7'),
                                     (8, 13, 0, 13, 'index 13 is outside 0 to 12'),
                                     (8, 13, -1, 0, 'index -1 is outside 0 to 7'),
                                     (8, 13, 0, -1, 'index -1 is outside 0 to 12')):
            path = os.path.join(tmp, 'outside.selv')
            with open(path, 'w') as f:
                f.write(f'rule main uses Output\n    a is array(Bit, {la})\n    b is array(Bit, {lb})\n'
                        f'    (d, t) is draw(CcnotTape(a, b, {i}, {j}))\n    output d\n')
            r = cli('run', path)
            self.assertEqual(r.returncode, 70, (la, lb, i, j))
            self.assertIn(needle, r.stderr, (la, lb, i, j))
            if HAVE_CLANG:
                c = build_and_run(path, tmp)
                self.assertEqual(c.returncode, 70, (la, lb, i, j))
                self.assertIn(needle, c.stderr, (la, lb, i, j))

    def test_draw_is_the_tape_s(self):
        # `draw`, `birth` and `tape_tick` are prelude rules: a program cannot declare its own (C5)
        for name in ('draw', 'birth', 'tape_tick'):
            with self.assertRaises(CheckError, msg=name) as e:
                load(f'rule {name} takes Bit returns Bit\n    b <-> b\n')
            self.assertIn(f'{name} is defined twice', str(e.exception))
        # there is no request group to answer, and no ambient tape to ask (C3)
        with self.assertRaises(CheckError) as e:
            load('rule main uses Draw, Output\n    d is ask draw()\n    output d\n')
        self.assertIn('unknown request', str(e.exception))
        # what the reservation does not cover, as ruled: a request a program declares in a group
        # of its own may be called draw.  `m -> draw()` is that program's message, not the rule
        out, _ = run_interp('request Mine\n    draw() returns Bit\n'
                            'answer M for Mine takes Bit\n    (draw(), b) <-> (c, b) where\n        c is b\n'
                            'rule main uses Output\n    m is M from Bit(1)\n    output m -> draw()\n')
        self.assertEqual(out.strip(), '1')

    def test_the_tick_rests_on_ccnot_and_nothing_more_is_claimed(self):
        m = load('')[0]
        for n in ('tape_tick', 'draw', 'birth'):
            self.assertEqual(m.rules[n].cls, 'bijection', n)
        # an index can refuse and an array's values are not counted, so whether the tick and a
        # draw take every input and reach every output is not established, and is not claimed
        unknown = ('one-to-one', 'defined on every input: not established; onto: not established')
        self.assertEqual(extent(m, m.rules['tape_tick']), unknown)
        self.assertEqual(extent(m, m.rules['draw']), unknown)
        # a child starts with both heads at 0, so a birth does not reach every pair of tapes:
        # one-to-one and not onto, which is all a birth promises (a valid reversible initialization)
        self.assertEqual(extent(m, m.rules['birth']),
                         ('one-to-one', 'defined on every input: not established; not onto (a value no right side matches)'))
        path = os.path.join(tempfile.mkdtemp(), 'min.selv')
        with open(path, 'w') as f:
            f.write('rule main uses Output\n    output 1\n')
        r = cli('lineage', path, 'tape_tick', '--verify')
        self.assertIn('add a * b on Bit -> ccnot [realized]', r.stdout)
        self.assertIn('add a * b on Bit = ccnot', r.stdout)


class TestReversibleProfile(unittest.TestCase):
    """The reversible profile (IX.4), in part: certified rules over bits, their words laid out,
    lowered to X, CNOT and CCNOT and checked by simulation against the interpreter.  The CCNOT tape
    is the first program it is tried on, not its definition."""
    from selvage import circuit as C

    @staticmethod
    def tape(la, lb, i, j, rng):
        bits = lambda n: Arr('Bit', [W(rng.randint(0, 1), 'Bit') for _ in range(n)])   # noqa: E731
        return F_('CcnotTape', (bits(la), bits(lb), W(i), W(j)))

    def agree(self, m, r, inputs):
        from selvage.interp import deep_copy
        c = self.C.lower(m, r, (), inputs[0])
        for x in inputs:
            got = self.C.simulate(c, x)
            self.assertEqual(got, Interp(m).forward(r, (), deep_copy(x)), r.name)
            self.assertEqual(self.C.simulate_back(c, got), x, r.name)
            self.assertEqual(self.C.simulate(self.C.lower(m, r.inverse, (), got), got), x, r.name)
        return c

    def test_the_tape_s_rules_lower_to_their_gates(self):
        m, rng = load('')[0], random.Random(3)
        for name, counts, ancillas in (('tape_tick', {'CCNOT': 2, 'CNOT': 0, 'X': 0}, 0),
                                       ('draw', {'CCNOT': 2, 'CNOT': 1, 'X': 0}, 1),
                                       ('birth', {'CCNOT': 42, 'CNOT': 21, 'X': 0}, 21)):
            c = self.agree(m, m.rules[name], [self.tape(8, 13, 3, 7, rng) for _ in range(40)])
            self.assertEqual(c.counts(), counts, name)
            self.assertEqual(len(c.ancillas), ancillas, name)
            # every ancilla becomes an output: a draw's bit, a child's cells; none is left over
            self.assertEqual(set(c.ancillas) <= set(c.output_wires()), True, name)

    def test_an_epoch_lowers_to_208_ccnots(self):
        # the 104 ticks of one alignment of tapes of 8 and 13 cells, from heads 0 and 0
        m = load('rule epoch takes CcnotTape returns CcnotTape\n    s <-> s where\n'
                 '        repeat with k from 1 to 104\n            s is tape_tick(s)\n')[0]
        x = self.tape(8, 13, 0, 0, random.Random(4))
        c = self.agree(m, m.rules['epoch'], [x])
        self.assertEqual(c.counts(), {'CCNOT': 208, 'CNOT': 0, 'X': 0})
        it, y = Interp(m), x
        from selvage.interp import deep_copy
        y = deep_copy(x)
        for _ in range(104):
            y = it.forward(m.rules['tape_tick'], (), y)
        self.assertEqual(self.C.simulate(c, x), y)
        self.assertEqual((y.kids[2].v, y.kids[3].v), (0, 0))

    def test_ancillas_come_back_clean_and_an_embedding_refuses_what_it_does_not_give(self):
        m = load('rule borrow takes (Bit, Bit) returns (Bit, Bit)\n    (a, b) <-> (a, b) where\n'
                 '        t is a\n        add t to b\n        t was a\n')[0]
        ins = [(W(a, 'Bit'), W(b, 'Bit')) for a in (0, 1) for b in (0, 1)]
        c = self.agree(m, m.rules['borrow'], ins)
        self.assertEqual((c.counts(), len(c.ancillas), len(c.released)), ({'CCNOT': 0, 'CNOT': 3, 'X': 0}, 1, 1))
        m = load('')[0]
        x = self.tape(8, 13, 0, 0, random.Random(5))
        c = self.C.lower(m, m.rules['draw'], (), x)
        bit, t = self.C.simulate(c, x)
        with self.assertRaises(self.C.Dirty):
            self.C.simulate_back(c, (W(1 - bit.v, 'Bit'), t))

    def test_the_profile_is_not_the_tape(self):
        m = load(src('gates.selv').split('rule main')[0])[0]
        bit = lambda v: W(v, 'Bit')                                   # noqa: E731
        ins = [tuple(bit((v >> k) & 1) for k in range(4)) for v in range(16)]
        adds = [(Arr('Bit', list(x)), Arr('Bit', list(y)), bit(cin)) for x in ins for y in ins for cin in (0, 1)]
        c = self.agree(m, m.rules['ripple_add'], adds)                 # all 512 inputs at width 4
        self.assertEqual(c.counts(), {'CCNOT': 8, 'CNOT': 16, 'X': 0})
        pairs = [(bit(a), bit(b)) for a in (0, 1) for b in (0, 1)]
        for name, counts in (('and_into', {'CCNOT': 1, 'CNOT': 0, 'X': 0}), ('or_into', {'CCNOT': 1, 'CNOT': 0, 'X': 5}),
                             ('nand_into', {'CCNOT': 1, 'CNOT': 0, 'X': 1})):
            self.assertEqual(self.agree(m, m.rules[name], pairs).counts(), counts, name)
        m = load('rule h takes (Bit, Bit) returns (Bit, Bit)\n    (a, b) <-> (b, a) where\n        swap a and b\n')[0]
        c = self.agree(m, m.rules['h'], pairs)
        self.assertEqual((len(c.gates), c.relabels), (0, 1))          # a swap relabels wires

    def test_what_the_profile_refuses(self):
        bit = lambda v: W(v, 'Bit')                                   # noqa: E731
        for text, rule, sample, params, reason in (
                (src('orbit.selv'), 'orbit', F_('Phase', (W(1000), W(5))), (W(10), W(50)), 'no bit on a wire'),
                (src('orbit.selv'), 'damped_orbit', F_('Phase', (W(1000), W(5))), (W(10), W(50)), 'not certified'),
                (src('arrays.selv'), 'prefix_sum', Arr('U64', [W(1, 'U64')] * 4), (), 'no bit on a wire'),
                ('rule f takes (Bit, Bit) returns (Bit, Bit)\n    (a, b) <-> (a, b) where\n        if a = 1\n            add 1 to b\n',
                 'f', (bit(0), bit(0)), (), 'a condition reads a bit'),
                ('rule g takes (Bit, I64) returns (Bit, I64)\n    (a, n) <-> (a, n) where\n        add I64(a) to n\n',
                 'g', (bit(0), W(3)), (), 'compute a word from a bit'),
                ('rule k takes (Bit, Bit) returns (Bit, Bit)\n    (0, b) <-> (0, b)\n    (1, b) <-> (1, b) where\n        add 1 to b\n',
                 'k', (bit(0), bit(0)), (), 'a clause is chosen by a bit')):
            m = load(text)[0]
            with self.assertRaises(self.C.NotLowerable, msg=rule) as e:
                self.C.lower(m, m.rules[rule], params, sample)
            self.assertIn(reason, str(e.exception), rule)

    def test_the_circuit_command(self):
        path = os.path.join(tempfile.mkdtemp(), 'min.selv')
        with open(path, 'w') as f:
            f.write('rule main uses Output\n    output 1\n')
        r = cli('circuit', path, 'draw', 'CcnotTape(array(Bit, 8), array(Bit, 13), 0, 0)')
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('gates    2 CCNOT, 1 CNOT, 0 X', r.stdout)
        self.assertIn('checked  the circuit gives what the interpreter gives; run backward, it gives the input back', r.stdout)
        r = cli('circuit', os.path.join(EX, 'orbit.selv'), 'orbit', 'Phase(1000, 5)', '--params', '10, 50')
        self.assertEqual(r.returncode, 1)
        self.assertIn('not lowered: orbit has no bit on a wire', r.stdout)


class TestMeasure(unittest.TestCase):
    """The quantum interface as far as it goes (VII.4): the request group `Measure`, declared in the
    prelude and answered by nothing.  An `ask measure()` is refused at Root, status 70, until a
    quantum profile installs the answer.  No quantum type exists."""
    ASK = 'rule probe returns Bit uses Measure\n    ask measure()\n'
    STAND = ('answer Stand for Measure takes I64\n    (measure(), n) <-> (b, n) where\n'
             '        b is Bit(n mod 2)\n        add 1 to n\n')

    @staticmethod
    def refusal(text):
        try:
            load(text)
            return None
        except CheckError as e:
            return str(e)

    def test_the_prelude_declares_measure_and_nothing_answers_it(self):
        m = load('')[0]
        self.assertEqual(list(m.requests['Measure']), ['measure'])
        self.assertEqual([n for n, a in m.answers.items() if 'Measure' in a.groups], [])
        self.assertNotIn('measure', m.answers['Root'].native)
        # both names are the prelude's; a program's own rule may still be called measure, as for draw
        self.assertIn('request group Measure is declared twice', self.refusal('request Measure\n    look() returns Bit\n'))
        self.assertIn('request measure is declared twice',
                      self.refusal('request Gauge\n    measure(x: I64) returns I64\n'))
        out, _ = run_interp('rule measure(x: I64) returns I64\n    x + 1\nrule main uses Output\n    output measure(2)\n')
        self.assertEqual(out.strip(), '3')

    def test_an_ask_of_measure_is_refused_at_root_with_status_70(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'measure.selv')
            with open(path, 'w') as f:
                f.write(self.ASK + 'rule main uses Output, Measure\n    output 1\n    output probe()\n    output 2\n')
            self.assertEqual(cli('check', path).returncode, 0)    # the program is valid; it is refused when it runs
            r = cli('run', path)
            self.assertEqual(r.returncode, 70, r.stderr)
            self.assertEqual(r.stdout, '1\n')
            self.assertIn('no answer for request measure', r.stderr)
            # compiled code has no `ask` (IX.2): the program is not built, so nothing runs
            r = cli('emit-c', path)
            self.assertEqual(r.returncode, 1)
            self.assertIn('stays in the interpreter', r.stderr)

    def test_a_rule_that_measures_is_lossy_and_a_rule_that_draws_is_not(self):
        # a rule's class is fixed statically: an ask's reply is world input, a draw is a certified rule
        asks = 'rule look takes I64 returns (I64, Bit) uses Measure\n    x {} (x, b) where\n        b is ask measure()\n'
        self.assertIn('it asks outside itself, so its reply is world input', self.refusal(asks.format('<->')))
        self.assertIsNone(self.refusal(asks.format('=>')))
        self.assertEqual(load(asks.format('=>'))[0].rules['look'].cls, 'lossy')
        draws = 'rule look takes CcnotTape returns (Bit, CcnotTape)\n    t {} (b, t) where\n        (b, t) is draw(t)\n'
        self.assertIsNone(self.refusal(draws.format('<->')))
        self.assertIn('a certified rule writes `<->`', self.refusal(draws.format('=>')))
        # the row says where a rule reaches measure
        self.assertIn('declare `uses Measure`', self.refusal('rule probe returns Bit\n    ask measure()\n'))

    def test_a_stand_in_takes_the_request_inside_its_with_only(self):
        # an answer a program installs is its own stand-in, not a measurement; outside it, Root refuses
        prog = (self.STAND + self.ASK + 'rule main uses Output, Measure\n'
                '    (b, s) is probe() with Stand from 3\n    output b\n    output s\n    output probe()\n')
        m = load(prog)[0]
        out = io.StringIO()
        with self.assertRaises(Fault) as e:
            Interp(m, out).run_main()
        self.assertEqual(out.getvalue(), '1\nStand from 4\n')
        self.assertIn('no answer for request measure', str(e.exception))


class TestSealAndWitness(unittest.TestCase):
    """P3: retention is sealed to Root, disclosure goes through Witness, and a host mediates."""

    DROP = 'rule drop takes (I64, I64) returns I64\n    (a, b) => a where\n        discard b\n'
    VAULT = ('request Vault for Keeper\n    put(n: I64) returns I64\n'
             'answer Keeper for Vault takes I64\n    (put(n), c) <-> (n, c) where\n        add n to c\n')

    def refused(self, text, needle):
        with self.assertRaises(CheckError, msg=text) as cm:
            load(text)
        self.assertIn(needle, str(cm.exception), text)

    def test_the_seal_is_a_rule_about_places_and_names_no_declaration(self):
        m = load('')[0]
        self.assertEqual((m.sealed, m.sealed_answers), ({'System': 'Root'}, {'Root': 'System'}))
        self.assertEqual(sorted(m.requests['System']), ['keep'])
        # the same rule for a seal a program declares: the program is one place, and holds it
        m = load(self.VAULT + 'rule fill takes Keeper returns (I64, Keeper)\n    k <-> (u, k) where\n'
                 '        u is k -> put(3)\nrule make returns Keeper\n    Keeper from 0\n')[0]
        self.assertEqual(m.sealed['Vault'], 'Keeper')
        it = Interp(m)
        self.assertEqual(it.forward(m.rules['fill'], (), it.call_expr_rule(m.rules['make'], ())),
                         (W(3), Inst('Keeper', (), W(3))))
        self.refused('request Vault for Nobody\n    put(n: I64) returns I64\n', 'which is not an answer')
        self.refused('request Vault for Keeper\n    put(n: I64) returns I64\nrequest Other\n    o() returns ()\n'
                     'answer Keeper for Other takes I64\n', 'Keeper is not an answer for Vault')
        self.refused('request Mine for Root\n    peek() returns Journal\n', 'declared in another place')
        self.refused('request System\n    peek() returns Journal\n', 'request group System is declared twice')
        self.refused('type Journal\n    Forged\n', 'type Journal is defined twice')
        self.refused('request G\n    g() returns ()\nanswer Root for G takes I64\n', 'answer Root is defined twice')

    def test_history_is_asked_through_witness(self):
        m = load('')[0]
        self.assertEqual({op: m.ops[op] for op in ('keep', 'history', 'refuse')},
                         {'keep': 'System', 'history': 'Witness', 'refuse': 'Refusal'})
        read = self.DROP + 'rule main uses Output, System{}\n    v is drop((1, 2))\n    output ask history()\n'
        self.refused(read.format(''), 'main asks history; declare `uses Witness`')    # retention is not disclosure
        self.assertEqual(by_name(run_interp(read.format(', Witness'))[0]), 'Kept(Dropped("drop", 2), Empty)\n')
        # the row follows the request through calls
        self.refused('rule peek returns Journal uses Witness\n    ask history()\n'
                     'rule main uses Output\n    output peek()\n', 'main calls peek, which uses Witness')

    def test_root_keeps_retention_disclosure_and_termination_apart(self):
        m = load('')[0]
        root = m.answers['Root']
        self.assertEqual(root.group_order, ['System', 'Witness', 'Refusal'])
        self.assertEqual((sorted(root.ops), root.native), (['history', 'keep'], {'refuse'}))
        self.assertEqual({op: root.ops[op].cls for op in root.ops}, {'keep': 'bijection', 'history': 'bijection'})
        it = Interp(m)
        r0 = it.root[0]
        reply, r1 = it.send(r0, 'keep', (W(5),))                 # retention: one entry more, nothing disclosed
        self.assertEqual((reply, it.journal_of(r1)), ((), Form('Kept', (W(5), Form('Empty', ())))))
        reply, r2 = it.send(r1, 'history', ())                   # disclosure: a copy, and the journal as it was
        self.assertEqual((reply, r2), (it.journal_of(r1), r1))
        req, r3 = it.unsend_any(r2, 'history', reply)            # giving the copy back changes nothing either
        self.assertEqual((req.tag, r3), ('history', r1))
        with self.assertRaises(Fault):                           # termination: the run ends; nothing is kept or shown
            run_interp(self.DROP + 'rule main uses Output, System\n    v is drop((1, 2))\n    w is 1 / (v - v)\n')

    def test_a_host_mediates_what_inner_code_reads(self):
        out, it = run_interp(src('witness.selv'))
        full = 'Kept(Dropped("spend", 7777), Kept(Dropped("spend", 4242), Empty))'
        shown = 'Kept(Dropped("spend", ()), Kept(Dropped("spend", ()), Empty))'
        self.assertEqual(by_name(out).splitlines(), [full, shown, 'Empty', shown, 'Counting from 1', 'true'])
        m = load(src('witness.selv'))[0]
        self.assertEqual({a: m.answers[a].cls for a in ('Closed', 'Counting', 'Redacting')},
                         {'Closed': 'bijection', 'Counting': 'lossy', 'Redacting': 'lossy'})
        self.assertEqual(m.rules['redact'].cls, 'bijection')
        self.assertEqual(m.reach('Redacting', 'history'), (frozenset({'history'}), frozenset()))

    def test_an_inquiry_leaves_the_journal_as_it_was(self):
        m = load(src('witness.selv'))[0]
        it = Interp(m)
        it.forward(m.rules['spend'], (), (W(1), W(4242)))
        it.forward(m.rules['spend'], (), (W(2), W(7777)))
        before, kept = identity(it.root[0]), it.kept
        for host in (None, Inst('Closed', (), ()), Inst('Counting', (), W(0)), Inst('Redacting', (), ())):
            cells = [[host]] if host else []
            it.handlers += cells
            seen = it.call_expr_rule(m.rules['inquire'], ())
            del it.handlers[1:]
            self.assertEqual((identity(it.root[0]), it.kept), (before, kept), host)
            self.assertEqual('4242' in str(seen), host is None or host.answer == 'Counting', host)

    RECORDING_HOSTS = (
        # holds a copy of what it disclosed in its own state, for as long as the inquiry stands
        'answer Logging for Witness takes Journal\n    (history(), log) => (h, Kept(c, log)) where\n'
        '        h is ask history()\n        c is h\n'
        # keeps a record of the value it disclosed: the record is in the journal
        'answer Audit for Witness takes ()\n    (history(), s) => (h, s) where\n'
        '        h is ask history()\n        record is h\n        discard record\n'
        # keeps a mark of the disclosure, without the value
        'answer Marking for Witness takes ()\n    (history(), s) => (h, s) where\n'
        '        h is ask history()\n        mark is 1\n        discard mark\n'
        'type Log\n    Clean\n    Noted(reason: Text, earlier: Log)\n'
        'answer Recorder for Refusal takes Log\n    (refuse(reason), log) <-> ((), Noted(reason, log))\n')

    def inquiry(self, body, declared=''):
        """Run a main that has kept one value and then does `body`; what it showed, or its refusal."""
        import io
        program = (src('witness.selv').split('rule main')[0] + self.RECORDING_HOSTS + declared
                   + 'rule main uses Output, System, Witness\n    a is spend((1, 4242))\n' + body)
        out = io.StringIO()
        try:
            Interp(load(program)[0], out).run_main()
        except Fault as e:
            return str(e)
        return by_name(out.getvalue()).splitlines()

    def test_a_withdrawn_inquiry_takes_back_what_the_hosts_counted_and_held(self):
        redacted = 'Kept(Dropped("spend", ()), Empty)'
        # a count and a held copy are in the host's own state: giving the copy back takes them back
        self.assertEqual(self.inquiry('    ((seen, r), c) is (inquire() with Redacting from ()) with Counting from 0\n'
                                      '    output c\n    output seen\n'), ['Counting from 0', redacted])
        self.assertEqual(self.inquiry('    ((seen, r), c) is (inquire() with Redacting from ()) with Logging from Empty\n'
                                      '    output c\n    output seen\n'), ['Logging from Empty', redacted])
        # through two hosts, each as it was; and the journal as it was
        self.assertEqual(self.inquiry(
            '    before is inquire()\n'
            '    (((seen, r), c), d) is ((inquire() with Redacting from ()) with Logging from Empty) with Counting from 0\n'
            '    after is inquire()\n    output c\n    output d\n    output after = before\n'),
            ['Logging from Empty', 'Counting from 0', 'true'])
        # an inquiry that stands is counted and held
        self.assertEqual(self.inquiry('    ((seen, c), d) is (inquire() with Logging from Empty) with Counting from 0\n'
                                      '    output c\n    output d\n'),
                         ['Logging from Kept(Kept(Dropped("spend", 4242), Empty), Empty)', 'Counting from 1'])

    def test_a_kept_record_of_a_disclosure_cannot_be_withdrawn(self):
        needle = 'only the system takes back what was kept'
        inner = '(inquire() with Redacting from ())'
        for chain in (f'{inner} with Audit from ()', f'{inner} with Marking from ()',
                      f'({inner} with Counting from 0) with Audit from ()',
                      f'({inner} with Logging from Empty) with Marking from ()'):
            self.assertIn(needle, self.inquiry(f'    got is {chain}\n    output got\n'), chain)
        # the record alone is no refusal: an inquiry that is not given back stands, and so does its record
        shown = self.inquiry('    (seen, host) is inquire() with Audit from ()\n    after is inquire()\n'
                             '    output seen\n    output after\n')
        self.assertEqual(shown[0], 'Kept(Dropped("spend", 4242), Empty)')
        self.assertEqual(shown[1], f'Kept(Dropped("Audit.history", {shown[0]}), {shown[0]})')
        # nothing took the refusal: status 70
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'audit.selv')
            with open(path, 'w') as f:
                f.write(src('witness.selv').split('rule main')[0] + self.RECORDING_HOSTS
                        + 'rule main uses Output, System, Witness\n    a is spend((1, 4242))\n'
                          '    ((seen, r), c) is (inquire() with Redacting from ()) with Audit from ()\n    output seen\n')
            r = cli('run', path)
            self.assertEqual((r.returncode, r.stdout), (70, ''), r.stderr[-300:])
            self.assertIn(needle, r.stderr)

    def test_a_refused_withdrawal_leaves_the_answers_further_out_as_they_stood(self):
        # Redacting gives its copy back through Audit, which kept a record: refused.  The refusal is
        # taken inside Counting, which the inquiry had already reached: its count stands at one,
        # and the journal holds Audit's record once
        shown = self.inquiry(
            '    ((u, k), c) is (probe() with Recorder from Clean) with Counting from 0\n'
            '    after is inquire()\n    output k\n    output c\n    output after\n',
            'rule probe uses Witness, System\n'
            '    ((seen, r), a) is (inquire() with Redacting from ()) with Audit from ()\n')
        self.assertIn('only the system takes back what was kept', shown[0])
        self.assertTrue(shown[0].startswith('Recorder from Noted('), shown[0])
        self.assertEqual(shown[1], 'Counting from 1')
        spent = 'Kept(Dropped("spend", 4242), Empty)'
        self.assertEqual(shown[2], f'Kept(Dropped("Audit.history", {spent}), {spent})')

    def test_a_host_that_gives_its_copy_back_keeps_nothing_of_it(self):
        hosts = src('witness.selv').split('rule main')[0]
        hoard = ('answer Hoard for Witness takes Journal\n    (history(), mine) => (out, {}) where\n'
                 '        all is ask history()\n        c is all\n        out is Empty\n{}        all was ask history()\n')
        # it would restore the answers further out while holding what they disclosed: refused
        self.refused(hosts + hoard.format('Kept(c, mine)', ''), 'Hoard gives back the copy history disclosed, and '
                     'keeps what it read in its state; a host that gives its copy back keeps nothing of it')
        self.refused(hosts + hoard.format('mine', '        discard c\n'), 'keeps what it read (`discard c`)')
        # a bit of it is enough: a state changed under a condition on what it read
        self.refused(hosts + 'answer Peek for Witness takes I64\n    (history(), n) => (out, n) where\n'
                     '        all is ask history()\n        out is Empty\n        if all = Empty\n'
                     '            add 1 to n\n        all was ask history()\n', 'keeps what it read in its state')
        # a host that keeps nothing of it passes, whatever it discloses inward
        load(hosts + 'answer Through for Witness takes I64\n    (history(), n) => (out, n) where\n'
                     '        all is ask history()\n        out is all\n        add 1 to n\n        all was ask history()\n')
        self.assertEqual(load(src('witness.selv'))[0].rules['main'].cls, 'procedure')     # Redacting passes

    def test_installing_a_host_that_asks_outward_is_in_the_row(self):
        hosts = src('witness.selv').split('rule main')[0]
        use = hosts + 'rule look returns Journal{}\n    (seen, h) is inquire() with {}\n    seen\n'
        self.assertEqual(load(use.format('', 'Closed from ()'))[0].rules['look'].cls, 'function')
        for host in ('Counting from 0', 'Redacting from ()'):
            self.refused(use.format('', host), 'whose rule for history asks history; declare `uses Witness`')
            self.refused(use.format(' uses Witness', host), 'declare `uses System`')   # its rule is lossy: it asks
            load(use.format(' uses Witness, System', host))
        # a host that stops the request stops the row too, whatever is installed inside it
        load(hosts + 'rule look returns Journal uses System\n'
             '    ((seen, a), b) is (inquire() with Counting from 0) with Closed from ()\n    seen\n')
        # messaging an instance directly carries what its rule asks as well
        self.refused(hosts + 'rule look returns Journal\n    c is Redacting from ()\n    c -> history()\n',
                     'declare `uses Witness`')

    def test_an_answer_passes_outward_only_where_a_sealed_answer_ends_the_path(self):
        g = ('request G\n    op(n: I64) returns I64\nanswer Mid for G takes I64\n'
             '    (op(n), c) => (r, c) where\n        r is ask op(n)\n        discard n\n')
        self.refused(g, 'Mid asks op while it is answering op')
        m = load('')[0]
        self.assertEqual((m.passes_outward('history'), m.passes_outward('settle')), (True, False))
        # reached indirectly, the request is not passed outward either: the run is refused, not crashed
        loop = ('request G\n    op(n: I64) returns I64\n'
                'rule again takes I64 returns I64 uses G\n    n => r where\n        r is ask op(n)\n        discard n\n'
                'answer Mid for G takes I64\n    (op(n), c) => (r, c) where\n        r is again(n)\n'
                'rule main uses Output, G, System\n    (v, m) is (ask op(1)) with Mid from 0\n    output v\n')
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, 'loop.selv')
            with open(path, 'w') as f:
                f.write(loop)
            r = cli('run', path)
            self.assertEqual(r.returncode, 70, r.stderr[-300:])
            self.assertEqual(r.stderr, 'selvage: refused: the run nests deeper than 10000 rule calls\n')

    def test_an_instance_holds_a_state_of_the_type_its_answer_takes(self):
        a = ('request G\n    op(n: I64) returns I64\nanswer A(k: I64) for G takes (I64, Bool)\n'
             '    (op(n), s) <-> (n, s)\nrule make returns A\n    {}\n')
        load(a.format('A(2) from (1, true)'))
        self.refused(a.format('A(2) from true'), 'A takes a state of type (I64, Bool), found Bool')
        self.refused(a.format('A(2) from (1, 2)'), 'A takes a state of type (I64, Bool)')
        self.refused(a.format('A(true) from (1, true)'), 'parameter k of A')
        self.refused(a.format('A from (1, true)'), 'A takes 1 parameter(s), given 0')

    def test_a_commit_point_is_in_the_row(self):
        self.refused('rule f returns I64\n    commit\n    1\n', 'f commits, which dissipates what the journal holds')
        m = load('rule f returns I64 uses System\n    commit\n    1\n')[0]
        self.assertEqual(m.rules['f'].cls, 'procedure')
        self.refused('rule f returns I64 uses System\n    commit\n    1\nrule g returns I64\n    f()\n',
                     'g calls f, which uses System')

    def test_layout_is_the_only_lineage_exemption(self):
        from selvage.lineage import links
        m = load('rule pick takes (Array(Bit), Array(Bit)) returns (Array(Bit), Array(Bit))\n'
                 '    (a, sel) <-> (a, sel) where\n        add 1 to a[sel[0] + sel[1]]\n'
                 'rule fixed(k: I64) takes Array(Bit) returns Array(Bit)\n    a <-> a where\n'
                 '        repeat with i from 0 to length(a) - 2\n            add a[i + 1] to a[i]\n'
                 '        add 1 to a[k * 2]\n')[0]
        what = lambda n: {w for w, _, _, _ in links(m, n)}  # noqa: E731
        self.assertEqual(what('fixed'), {'add on Bit'})                 # indices and counts: layout only
        self.assertEqual(what('pick'), {'add on Bit', 'sum on Bit'})    # an index that reads data is labelled


class TestGenerated04(unittest.TestCase):
    """Generated programs, each with an oracle that predicts what the checker and the run must
    do: one generator for each change of the 0.4 implementation group (tests/generated_04.py).
    tools/mutation_check.py breaks the toolchain one way at a time to see that they notice."""

    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import generated_04
        cls.parts = dict(generated_04.PARTS)
        cls.gen = generated_04

    def part(self, name, programs, **at_least):
        stats, findings = self.parts[name](programs, 7)
        self.assertEqual([(kind, detail) for kind, _, detail in findings[:3]], [])
        for what, n in at_least.items():
            self.assertGreaterEqual(stats[what.replace('_', ' ')], n, stats)

    def test_a_run_is_charged_for_what_it_lets_go_of(self):
        self.part('accounting', 120, rules=110, lossy=95, runs=900, entries=2000, choices_kept=400, choices_not_needed=200,
                  constructors_ruled_out=8, dropped_for_nothing=60, outputs_weighed=150, compiled=10 if HAVE_CLANG else 0,
                  copies_dropped_after_a_change=20)

    def test_a_value_is_given_only_where_its_type_is_declared(self):
        self.part('declared', 120, narrowings_refused=120, same_programs_accepted=120, sites=16, literals_set=110,
                  undecided_values_set=110, literals_given_as_words=200, rewinds=400)

    def test_declarations_and_programs_are_read_by_rules_as_the_text_says(self):
        self.part('forms', 120, accepted=80, declarations=250, read_alike_by_a_rule_and_from_the_text=80, clauses_mirrored=150,
                  constructors_taken_apart=400, uncomputes_that_read_themselves_refused=80)

    def test_certified_rules_laid_out_as_gates_agree_with_the_interpreter(self):
        self.part('circuits', 150, gate_rules=150, array_rules=150, tape_rules=150, runs=2500,
                  inverses_laid_out=2000, refused_alike=50)

    def test_the_ccnot_tape_agrees_with_a_model_of_wiring_1(self):
        self.part('tape', 150, tapes=150, draws=2000, births=50, taken_back=2000, ticks_undone=150)

    def test_an_ask_of_measure_is_taken_by_a_stand_in_or_refused_at_root(self):
        self.part('measure', 150, programs_run=150, asks_taken=60, refused_at_the_root=60, completed=20,
                  wrong_arrows_refused=60, missing_rows_refused=100)

    def test_how_far_a_certified_rule_reaches(self):
        self.part('extent', 150, gate_rules=90, permutations=15, embeddings=15, partial_inverses=4, partial=6,
                  word_rules=40, claims_tried=250, answers=130)

    def test_arrows_state_the_certificate_and_lossy_runs_rewind(self):
        self.part('arrows', 240, lossy=20, certified=20, rewinds=200)

    def test_delegation_to_the_single_component_that_answers(self):
        self.part('delegation', 120, valid=50, ambiguous=20, delegated=40, unanswered=60, messages=100, asks=50)

    def test_rows_tell_functions_from_procedures_and_show_reaching_keep(self):
        self.part('rows', 80, functions=30, procedures=100, rows_cut=200, runs=200, kept=100)

    def test_a_kept_reply_stands_between_runs(self):
        self.part('between runs', 120, rewound=40, refused=15)

    def test_every_operator_class_carries_a_link(self):
        self.part('operators', 200, rules=200, links=400)

    def test_any_is_refused_in_every_declaration_position(self):
        self.part('any', 150, accepted=150, refused=150)

    def test_a_refusal_goes_to_the_nearest_answer_or_ends_the_run(self):
        self.part('refusal', 200, completed=50, ended_by_Root=50, taken=40)

    def test_every_route_to_what_is_sealed_is_refused(self):
        self.part('seal', 250, refused_by_the_checker=180, refused_in_the_run=10, routes=23)

    def test_inner_code_reads_what_its_hosts_pass_on(self):
        self.part('witness', 200, disclosed=60, redacted=20, closed=30, rows_cut=200,
                  withdrawals_refused=4, records_kept=40, effects_rewound=5, retaining_hosts_refused=300)

    def test_a_run_nests_to_the_bound_and_no_deeper(self):
        self.part('depth', 80, runs=250, refused=80, completed=80, at_the_bound=60)

    def test_the_theorem_holds_on_rules_that_call_message_and_open(self):
        self.part('structures', 200, certified=80, refused=60, round_trips=600, inverse_refused=200, inverse_accepted=600)

    def test_decisions_inside_clause_rules_are_kept_and_rewound(self):
        self.part('decisions', 100, rules=100, runs=600, settled_by_an_answer=100, settled_by_the_world=100, rewinds=600,
                  replays=60, replays_refused=150)

    def test_code_is_identified_by_what_it_is_and_not_by_its_names(self):
        self.part('names', 80, rules=25, renamed_alike=25, nested_bindings_renamed=10, uses_changed=10, scope_cases=200,
                  shadowing_refused=150, requests_and_answers_renamed=40, twins_kept_apart=40, runs=80)

    def test_an_entry_names_its_code_under_renaming_and_reordering(self):
        self.part('journal', 120, runs=400, entries=1000, renamed=100, variables_renamed=40, reordered=60, declared_elsewhere=100,
                  recursive_runs=200, callees_changed=120, rewinds=400, forged_entries_refused=900,
                  shared_identities_refused=20)

    def test_the_interpreter_and_invert_are_the_model_of_the_proof(self):
        self.part('model', 240, rules=80, forward_runs=800, inverse_runs=800, proved_uncomputes_reached=100)

    def test_an_untaken_refusal_ends_the_run_with_status_70(self):
        rng, seen = random.Random(11), set()
        with tempfile.TemporaryDirectory() as tmp:
            while len(seen) < 2:
                p = self.gen.Refusals(rng)
                want, ended = [], False
                try:
                    p.run(len(p.rules) - 1, 1, [[0]], want)
                except self.gen.Stop:
                    ended = True
                if ended in seen or any(isinstance(w, tuple) for w in want):
                    continue
                seen.add(ended)
                path = os.path.join(tmp, f'p{len(seen)}.selv')
                with open(path, 'w') as f:
                    f.write(p.text())
                r = cli('run', path)
                self.assertEqual(r.returncode, 70 if ended else 0, r.stderr)
                self.assertEqual(r.stdout.splitlines()[:len(want)], want)
                self.assertEqual('refused' in r.stderr, ended)


def deep(v):
    from selvage.interp import deep_copy
    return deep_copy(v)


@unittest.skipUnless(HAVE_CLANG, 'clang not available')
class TestC23Backend(unittest.TestCase):
    """The C23 backend prints what the interpreter prints, and counts the same epsilon."""

    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp()

    def compare(self, path):
        r = cli('run', path, env={'SELVAGE_STATS': '1'})
        self.assertEqual(r.returncode, 0, r.stderr)
        c = build_and_run(path, self.tmp)
        self.assertEqual(c.returncode, 0, c.stderr)
        self.assertEqual(c.stdout, r.stdout, path)
        self.assertEqual(c.stderr.strip().splitlines()[-1], r.stderr.strip().splitlines()[-1], path)

    def test_examples_agree(self):
        for f in ('shapes.selv', 'orbit.selv', 'arrays.selv', 'gates.selv'):
            self.compare(os.path.join(EX, f))

    def test_the_backends_charge_alike(self):
        # clause choices kept only where the output leaves one, variants by the constructors
        # still possible, a Trit two bits whichever value it holds, a recomputable value nothing
        self.compare(os.path.join(PROGS, 'accounting.selv'))
        r = cli('run', os.path.join(PROGS, 'accounting.selv'), env={'SELVAGE_STATS': '1'})
        self.assertEqual(r.stderr.strip().splitlines()[-1], 'epsilon=370 journal_bits=0')
        r = cli('run', os.path.join(EX, 'gates.selv'), env={'SELVAGE_STATS': '1'})
        self.assertEqual(r.stderr.strip().splitlines()[-1], 'epsilon=36 journal_bits=0')

    def test_the_corrected_charges_are_the_same_in_both_backends(self):
        # the corrected charges and T1: each program against one expected ε, in the interpreter and compiled
        main = '\nrule main uses Output, System\n'
        for what, text, eps in (
                ('a literal given as a U8',
                 'rule k takes (U8, I64) returns I64\n    (n, m) => m where\n        discard n\n' + main +
                 '    output k((7, 1))\n    x is U8(7)\n    output k((x, 1))\n', 8 + 8),
                ('set to a literal',
                 'rule g takes U8 returns U8\n    n => n where\n        set n to 0\n' + main + '    output g(7)\n', 8),
                ('set on a Trit',
                 'rule g takes Trit returns Trit\n    t => t where\n        set t to true\n' + main +
                 '    output g(maybe)\n    output g(false)\n', 2 + 2),
                ('a dropped Text',
                 'rule f takes (Text, I64) returns I64\n    (t, n) => n where\n        discard t\n' + main +
                 '    output f(("hello", 9))\n    output f(("", 9))\n', 104 + 64),
                # 0.4.0 to 0.4.8 could not compile these: the derived inverse gave a value it
                # takes back no type, over the type of an expression the two directions share
                ('an input changed, then dropped',
                 'rule f takes (Bit, Bit) returns Bit\n    (v, w) => w where\n        add 1 to v\n        discard v\n' +
                 main + '    output f((Bit(0), Bit(1)))\n', 1),
                ('an input copied and changed, then both dropped',
                 'rule f takes (Bit, Bit) returns Bit\n    (v, w) => w where\n        t is v\n        add 1 to v\n'
                 '        discard t\n        discard v\n' + main + '    output f((Bit(0), Bit(1)))\n', 2),
                ('an input copied, then both dropped',
                 'rule f takes (U8, Bit) returns Bit\n    (v, w) => w where\n        t is v\n        discard t\n'
                 '        discard v\n' + main + '    output f((7, Bit(1)))\n', 8)):
            path = os.path.join(self.tmp, 'corrected.selv')
            with open(path, 'w') as f:
                f.write(text)
            self.compare(path)
            r = cli('run', path, env={'SELVAGE_STATS': '1'})
            self.assertEqual(r.stderr.strip().splitlines()[-1], f'epsilon={eps} journal_bits=0', what)

    def test_text_is_the_same_bytes_in_both_backends(self):
        # compiled code holds Text as a C string, so a NUL byte would end it early: 0.4.9
        # printed "\0a" in the interpreter and an empty line compiled.  A NUL is refused in a
        # text, alike by check, run and build; every other byte prints and is charged alike
        for what, body in (('a NUL byte', b'\x00a'), ('a NUL byte after a backslash', b'\\\x00a')):
            path = os.path.join(self.tmp, 'nul.selv')
            with open(path, 'wb') as f:
                f.write(b'rule main uses Output\n    output "' + body + b'"\n')
            for cmd in ('check', 'run', 'build'):
                r = cli(cmd, path, '-o', os.path.join(self.tmp, 'nul')) if cmd == 'build' else cli(cmd, path)
                self.assertEqual(r.returncode, 1, (what, cmd))
                self.assertIn('text cannot hold a NUL byte', r.stderr, (what, cmd))
        path = os.path.join(self.tmp, 'bytes.selv')
        with open(path, 'wb') as f:
            f.write(b'rule f takes (Text, I64) returns I64\n    (t, n) => n where\n        discard t\n'
                    b'rule main uses Output, System\n'
                    b'    output "tab\there"\n    output "caf\xc3\xa9 \xe2\x9c\x93"\n    output "q\\"b\\\\s"\n'
                    b'    output f(("tab\there", 1))\n    output f(("caf\xc3\xa9 \xe2\x9c\x93", 2))\n'
                    b'    output f(("q\\"b\\\\s", 3))\n')
        self.compare(path)
        r = cli('run', path, env={'SELVAGE_STATS': '1'})
        # 64 for each length, and 8 for each byte: 8, 9 and 5 bytes
        self.assertEqual(r.stderr.strip().splitlines()[-1], f'epsilon={3 * 64 + 8 * (8 + 9 + 5)} journal_bits=0')

    def test_a_name_bound_twice_is_refused_alike(self):
        # the checker refuses it, so neither backend meets one: the run and the build end
        # with the same refusal
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import generated_04
        for what, code in generated_04.shadowed(random.Random(5)):
            path = os.path.join(self.tmp, 'twice.selv')
            with open(path, 'w') as f:
                f.write(code)
            ran, built = cli('run', path), cli('build', path, '-o', os.path.join(self.tmp, 'twice'))
            self.assertNotEqual((ran.returncode, built.returncode), (0, 0), what)
            self.assertRegex(ran.stderr, 'already bound|never rebound', what)
            self.assertEqual(ran.stderr, built.stderr, what)

    def test_defined_behaviour_agrees(self):
        self.compare(os.path.join(PROGS, 'defined.selv'))

    def test_sameness_agrees_in_c(self):
        self.compare(os.path.join(PROGS, 'sameness.selv'))
        c = build_and_run(os.path.join(PROGS, 'sameness_refused.selv'), self.tmp)
        self.assertEqual(c.returncode, 70)
        self.assertIn('refused', c.stderr)

    def test_derived_inverses_compile_and_agree(self):
        # forward code with checker-written uncomputes; the inverse is invert's code compiled forward
        self.compare(os.path.join(PROGS, 'uncompute.selv'))
        c = cli('emit-c', os.path.join(PROGS, 'uncompute.selv')).stdout
        self.assertIn('sv_mix_inv', c)
        self.assertNotIn('not what it was computed from', c.split('sv_mix_inv(int64_t v_k, sv_d_Pair in) {')[0]
                         .split('static sv_d_Pair sv_mix(int64_t v_k, sv_d_Pair in) {')[-1])

    def test_trits_and_decisions_agree(self):
        exe = os.path.join(self.tmp, 'trits')
        self.assertEqual(cli('build', os.path.join(PROGS, 'trits.selv'), '-o', exe).returncode, 0)
        r = subprocess.run([exe], capture_output=True, text=True, env=dict(os.environ, SELVAGE_DECIDE=DECIDER))
        self.assertEqual(r.stdout.splitlines(), TRITS_EXPECTED)
        r = subprocess.run([exe], capture_output=True, text=True, env=dict(os.environ, SELVAGE_DECIDE='refuse'))
        self.assertEqual(r.returncode, 70)
        self.assertIn('still maybe', r.stderr)

    def test_procedures_keep_world_replies_in_c(self):
        # generated procedures: the same output, and the same epsilon for kept replies and losses
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import generated_04
        rng, done, commits = random.Random(5), 0, 0
        env = {'SELVAGE_STATS': '1', 'SELVAGE_DECIDE': 'true'}
        while done < 5 or not commits:
            text = generated_04.c_program(rng)
            path = os.path.join(self.tmp, 'proc.selv')
            with open(path, 'w') as f:
                f.write(text)
            r = cli('run', path, env=env)
            self.assertEqual(r.returncode, 0, r.stderr)
            if 'decide t' not in text or r.stderr.strip().splitlines()[-1] == 'epsilon=0 journal_bits=0':
                continue        # this one keeps nothing: it would compare nothing
            done += 1
            commits += '    commit\n' in text
            exe = os.path.join(self.tmp, f'proc{done}')
            self.assertEqual(cli('build', path, '-o', exe).returncode, 0)
            c = subprocess.run([exe], capture_output=True, text=True, env=dict(os.environ, **env))
            self.assertEqual((c.returncode, c.stdout), (0, r.stdout), text)
            self.assertEqual(c.stderr.strip().splitlines()[-1], r.stderr.strip().splitlines()[-1], text)

    def test_the_depth_bound_agrees_in_c(self):
        # generated programs, each built and run at the bound it just fits and at one less:
        # the same output, the same refusal, the same status, and never a crash
        sys.path.insert(0, os.path.join(ROOT, 'tests'))
        import generated_04
        rng = random.Random(9)
        for n in range(3):
            text, calls = generated_04.depth_program(rng, compilable=True)
            deepest = 1 + max(levels for _, levels, _ in calls)
            path = os.path.join(self.tmp, f'depth{n}.selv')
            with open(path, 'w') as f:
                f.write(text)
            for bound in (deepest - 1, deepest):
                want, refused = generated_04.depth_oracle(calls, bound)
                r = cli('run', path, '--depth', str(bound))
                exe = os.path.join(self.tmp, f'depth{n}_{bound}')
                self.assertEqual(cli('build', path, '-o', exe, '--depth', str(bound)).returncode, 0)
                c = subprocess.run([exe], capture_output=True, text=True)
                self.assertEqual((r.returncode, r.stdout.splitlines()), (70 if refused else 0, want), text)
                self.assertEqual((c.returncode, c.stdout, c.stderr), (r.returncode, r.stdout, r.stderr), text)
                if refused:
                    self.assertEqual(r.stderr, f'selvage: refused: the run nests deeper than {bound} rule calls\n')

    def test_the_default_depth_bound_is_reached_in_both_backends(self):
        deep = ('rule ping(n: I64) returns I64\n    if n = 0\n        0\n    otherwise\n        1 + pong(n - 1)\n'
                'rule pong(n: I64) returns I64\n    if n = 0\n        0\n    otherwise\n        2 + ping(n - 1)\n'
                'rule spin(n: I64, acc: I64) returns I64\n    if n = 0\n        acc\n    otherwise\n'
                '        spin(n - 1, acc + 1)\n'
                'rule main uses Output\n    output spin(200000, 0)\n    output ping(9998)\n    output ping(9999)\n')
        path = os.path.join(self.tmp, 'deep.selv')
        with open(path, 'w') as f:
            f.write(deep)
        exe = os.path.join(self.tmp, 'deep')
        self.assertEqual(cli('build', path, '-o', exe).returncode, 0)
        r, c = cli('run', path), subprocess.run([exe], capture_output=True, text=True)
        # a tail call two hundred thousand deep is a loop; 9,999 calls below main fit; 10,000 do not
        self.assertEqual((r.returncode, r.stdout.splitlines()), (70, ['200000', '14997']))
        self.assertEqual(r.stderr, 'selvage: refused: the run nests deeper than 10000 rule calls\n')
        self.assertEqual((c.returncode, c.stdout, c.stderr), (r.returncode, r.stdout, r.stderr))

    def test_the_depth_argument_is_the_backend_s_own(self):
        # F3: compiled code passes the depth of the run to every rule; nothing of it is in the language
        text = 'rule twice(n: I64) returns I64\n    n + n\nrule main uses Output\n    output twice(4)\n'
        path = os.path.join(self.tmp, 'own.selv')
        with open(path, 'w') as f:
            f.write(text)
        c = cli('emit-c', path).stdout
        self.assertRegex(c, r'sv_twice\(int64_t v_n, int64_t sv_d\)')
        self.assertIn('if (sv_d > SV_DEPTH) sv_fault_depth();', c)
        m = load(text)[0]
        self.assertEqual(m.rules['twice'].params, [('n', 'I64')])                # one parameter, as written
        self.assertNotIn('sv_d', program_text(parse(text)))
        with self.assertRaises(CheckError):
            load(text.replace('twice(4)', 'twice(4, 1)'))                         # and no way to pass another
        self.assertEqual(cli('emit-c', path, '--depth', '50').stdout.count('#define SV_DEPTH 50'), 1)

    def test_adder_exhaustive_in_c(self):
        c = build_and_run(os.path.join(EX, 'adder.selv'), self.tmp)
        self.assertEqual(c.stdout.splitlines(), ['(1, 0, 1)', '(1, 1, 0)', '44', '0'])

    def test_refusals_exit_70(self):
        for p in ('divzero.selv', 'bounds.selv'):
            c = build_and_run(os.path.join(PROGS, p), self.tmp)
            self.assertEqual(c.returncode, 70)
            self.assertIn('refused', c.stderr)

    def test_inverse_functions_are_emitted(self):
        r = cli('emit-c', os.path.join(EX, 'arrays.selv'))
        for fn in ('sv_prefix_sum_inv', 'sv_reverse_inv', 'sv_count_above_inv'):
            self.assertIn(fn, r.stdout)

    def test_interpreter_only_features_are_refused_cleanly(self):
        for f in ('messages.selv', 'derivative.selv'):
            r = cli('emit-c', os.path.join(EX, f))
            self.assertEqual(r.returncode, 1)
            self.assertIn('stays in the interpreter', r.stderr)


if __name__ == '__main__':
    unittest.main()
