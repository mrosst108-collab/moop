"""Selvage: a minimal language in which every rule reads both ways and every loss is said aloud."""
import os

from .parser import parse
from .checker import build_model, CheckError
from .forms import Fault

__version__ = '0.5.0'
PRELUDE_PATH = os.path.join(os.path.dirname(__file__), 'prelude.selv')


def load(src, name='<program>'):
    """Parse and check a program together with the prelude. Returns (model, checker, program form)."""
    with open(PRELUDE_PATH) as f:
        prelude = parse(f.read())
    prog = parse(src)
    m, ch = build_model(prelude, prog)
    m.prelude_names = {d.kids[0] for d in prelude.kids}
    if m.errors:
        raise CheckError(f'{name}:\n  ' + '\n  '.join(m.errors))
    return m, ch, prog
