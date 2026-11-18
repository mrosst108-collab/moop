"""A stand-in for a language model as the world's decider.

Selvage runs it with the question as JSON on stdin: the undecided expression,
the values it read, its identity hash and the text of the rules it calls.  It
prints true, false or maybe.  Replace the body with a call to any model.

    python3 -m selvage run examples/triage.selv --decide "command:python3 examples/decider.py"
"""
import json
import sys

q = json.load(sys.stdin)
note = q['context'].get('note', '').lower()
if any(w in note for w in ('down', 'failing', 'outage', 'error rate')):
    print('true')
elif any(w in note for w in ('typo', 'cosmetic', 'slow')):
    print('false')
else:
    print('maybe')
