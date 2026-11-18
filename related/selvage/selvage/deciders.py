"""World deciders: how the host answers `settle` when no answer in the program decides.

A decider takes a question record and returns True, False or MAYBE.  The record is
built from the program's own forms (homoiconicity): the undecided expression as
canonical text, the values it read, the identity hash of the request, a replay
key shared with the C23 backend, and the text of the rules the expression calls, so a model or a person sees exactly what
the program saw.

  refuse              nobody outside decides (the default): `decide` is refused
  true | false        a fixed policy
  ask                 a person answers on the terminal
  command:CMD         run CMD with the question as JSON on stdin; it prints
                      true, false or maybe (any LLM client fits here)
  replay:FILE         answer from a record made with --record
"""
import json
import subprocess
import sys

from .forms import MAYBE, Fault


def parse_reply(text):
    w = (text or '').strip().split()
    w = w[0].lower().strip('".,') if w else ''
    return {'true': True, 'false': False}.get(w, MAYBE)


def refuse(record):
    return MAYBE


def fixed(value):
    return lambda record: value


def ask_human(record):
    sys.stderr.write(f"\nundecided: {record['question']}\n")
    for k, v in record['context'].items():
        sys.stderr.write(f'  {k} = {v}\n')
    sys.stderr.write('decide (true / false / maybe): ')
    sys.stderr.flush()
    return parse_reply(sys.stdin.readline())


def command(cmd):
    def run(record):
        r = subprocess.run(cmd, shell=True, input=json.dumps(record), capture_output=True, text=True)
        return parse_reply(r.stdout)
    return run


def replay(path):
    """Answer from a record, in order.  The next recorded decision is the answer when its
    question and its context are the question and context now asked, compared as text; it
    is then used up, and the one after it is next.  Nothing is searched for: a question the
    next record does not answer is refused, and so is one asked when the record has ended."""
    if isinstance(path, str):
        with open(path) as f:
            book = list(json.load(f))
    else:
        book = list(path)          # the records themselves
    at = [0]

    def decide(record):
        if at[0] >= len(book):
            raise Fault(f"replay: the record has no decision left for `{record['question']}`")
        r = book[at[0]]
        if r['question'] != record['question'] or r['context'] != record['context']:
            raise Fault(f"replay: the next recorded decision is for `{r['question']}`, not for "
                        f"`{record['question']}` as it is asked now")
        at[0] += 1
        return parse_reply(r['reply'])
    return decide


def from_spec(spec):
    if spec is None or spec == 'refuse':
        return refuse
    if spec in ('true', 'false'):
        return fixed(spec == 'true')
    if spec == 'ask':
        return ask_human
    if spec.startswith('command:'):
        return command(spec[len('command:'):])
    if spec.startswith('replay:'):
        return replay(spec[len('replay:'):])
    raise ValueError(f'unknown decider {spec!r}')
