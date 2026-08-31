"""The Reddit causal mechanism, extracted from the archive.

SOURCE: reddit-archive/reddit @ 753b17407e9a9dca09558526805922de24133d53.
Every structure here cites the file and line it was read from. Nothing is
invented to complete a picture, and nothing is shaped to fit RME-7 -- the
compatibility question is asked separately, in ``compat``.

THIS IS NOT CALLED AN ASDG FORMULATION. ``prompts/asdg-rme7.md`` section 4 --
the grammar, its primitives, its well-formedness conditions, and the relation
by which RME-7 is a format within it -- is [unpopulated]. Naming this output
"ASDG" would claim conformance to a grammar this repository does not hold. It
is a structural formulation; whether it is an ASDG one cannot be checked here.

THE ARCHITECTURAL RULING carried into this formulation: temporal evolution
belongs in the STATE, not only in the observation. The archive puts it in the
observation -- ``hot`` divides absolute epoch seconds by 45000 and stored
state never changes with time (r2/r2/lib/db/_sorts.pyx:46-56). The
reconstruction deliberately departs from the archive here, so ``Attention``
below is marked CONSTRUCTED rather than EXTRACTED.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Basis(Enum):
    """Where a structure in this formulation came from."""

    EXTRACTED = "read from the archive; cites file and line"
    CONSTRUCTED = "added by the architectural ruling; not in the archive"


@dataclass(frozen=True)
class Structure:
    name: str
    basis: Basis
    source: str
    note: str = ""


# --------------------------------------------------------------------------
# 1. STATE
# --------------------------------------------------------------------------

STATE = (
    Structure("thing.ups / thing.downs", Basis.EXTRACTED,
              "r2/r2/models/vote.py:117-119, 147-155",
              "two counters per votable thing; incremented by delta"),
    Structure("account.karma[subreddit, kind]", Basis.EXTRACTED,
              "r2/r2/models/account.py:224-240",
              "NOT a scalar: sparse vector over (subreddit x kind), stored as "
              "dynamic attributes named '{sr}_{kind}_karma'"),
    Structure("subreddit.subscribers", Basis.EXTRACTED,
              "r2/r2/models/subreddit.py:1349-1366",
              "sr._incr('_ups', +/-1) on subscribe/unsubscribe"),
    Structure("aggregate.cached_rankings", Basis.EXTRACTED,
              "r2/r2/lib/voting.py:182-184, 219-231",
              "materialized hot/top/controversial per author, subreddit, "
              "domain -- the observation layer has state of its own"),
    Structure("thing.attention", Basis.CONSTRUCTED,
              "architectural ruling; absent from the archive",
              "a temporal state variable that evolves between events. This is "
              "the ruling's whole content: the archive has dX/dt = 0."),
)


# --------------------------------------------------------------------------
# 2. THE IDENTIFIED EVENT
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Event:
    """An identified, typed input. Identity is causally consumed, not metadata.

    The archive's mechanism reads every one of these fields:
      actor + target -> previous_vote lookup   (vote.py:70-76)
      actor == target.author -> is_self_vote   (vote.py:128-133)
      previous_vote absent -> automatic vote   (vote.py:135-138)
      target.author -> karma destination       (vote.py:163-167)
      target.subreddit + kind -> karma index   (account.py:224-240)

    Anonymising this event is therefore not a simplification; it removes the
    inputs the gates and the routing run on.
    """

    actor: str
    target: str
    kind: str
    direction: int
    at: float
    prior: "Event | None" = None

    def is_self_directed(self, author_of_target: str) -> bool:
        return self.actor == author_of_target

    def is_automatic_initial(self, author_of_target: str) -> bool:
        return self.is_self_directed(author_of_target) and self.prior is None


# --------------------------------------------------------------------------
# 3. TWO GATES, KEPT APART
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Verdict:
    """A boolean verdict with reasons. Never a scalar, never a score.

    r2/r2/models/vote.py:220-233 -- the archive attaches note codes
    (AUTOMATIC_INITIAL_VOTE, KARMALESS_THING, COMMENT_STICKIED) to refusals.
    """

    allowed: bool
    notes: tuple[str, ...] = ()

    def __bool__(self) -> bool:
        return self.allowed


class Gate:
    """Base for the two admissibility structures. They are NOT one gate."""

    NAME = "gate"
    JURISDICTION = ""
    SOURCE = ""
    INPUTS: tuple[str, ...] = ()


class StateChangeGate(Gate):
    """May this event alter state at all?

    r2/r2/models/vote.py:190-300 (VoteEffects). Path-dependent: the verdict
    consults the STORED verdict of the prior event --
    'if not vote.previous_vote.effects.affects_score: return False'
    (vote.py:244-247, 259-262). History is carried in the gate, not recomputed.
    """

    NAME = "kappa_change"
    JURISDICTION = "local state of the target and its author"
    SOURCE = "r2/r2/models/vote.py:190-300"
    INPUTS = ("event", "prior verdict", "target kind", "sticky/distinguished")


class PropagationGate(Gate):
    """May an admitted alteration enter the aggregate states?

    r2/r2/lib/voting.py:168-175:
        vote_valid = is_automatic_initial_vote or effects.affects_score
        link_valid = not (link._spam or link._deleted)

    Different inputs and a different jurisdiction from the first gate: it
    consults _spam and _deleted, which the first gate never sees. Merging the
    two would erase a causal distinction the archive uses.
    """

    NAME = "kappa_propagate"
    JURISDICTION = "aggregate states keyed by author, subreddit, domain"
    SOURCE = "r2/r2/lib/voting.py:168-175"
    INPUTS = ("first verdict", "target.spam", "target.deleted")


GATES = (StateChangeGate, PropagationGate)


# --------------------------------------------------------------------------
# 4. THE CHANNEL FAMILY
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Route:
    """One destination of one event. Typed by what keys it."""

    destination: str
    keyed_by: tuple[str, ...]
    source: str


#: One admitted event fans out to THREE destinations through ONE gate
#: (r2/r2/lib/voting.py:171-174). This is a family, not an occurrence: the
#: same payload, three keyings, sharded independently.
CHANNEL_FAMILY = (
    Route("author.karma", ("author", "subreddit", "kind"),
          "r2/r2/models/vote.py:163-167"),
    Route("author.submitted_rankings", ("author_id % 10",),
          "r2/r2/lib/voting.py:186-192"),
    Route("subreddit.rankings", ("sr_id % 10",),
          "r2/r2/lib/voting.py:234-240"),
    Route("domain.rankings", ("domain",),
          "r2/r2/lib/voting.py:171-174"),
)


# --------------------------------------------------------------------------
# 5. OBSERVATIONS -- functions of state, never terms in its evolution
# --------------------------------------------------------------------------

OBSERVATIONS = (
    Structure("score = ups - downs", Basis.EXTRACTED,
              "r2/r2/lib/db/_sorts.pyx:40-41", ""),
    Structure("hot = sign*log10(max(|s|,1)) + (t - 1134028003)/45000",
              Basis.EXTRACTED, "r2/r2/lib/db/_sorts.pyx:46-56",
              "the archive's ONLY time dependence, and it is here rather "
              "than in the state -- which is what the ruling reverses"),
    Structure("controversy = (ups+downs) ** balance", Basis.EXTRACTED,
              "r2/r2/lib/db/_sorts.pyx:58-66", ""),
    Structure("confidence = Wilson lower bound, z at 80%", Basis.EXTRACTED,
              "r2/r2/lib/db/_sorts.pyx:68-84", ""),
    Structure("qa = confidence + log10(length)/5", Basis.EXTRACTED,
              "r2/r2/lib/db/_sorts.pyx:98-129", ""),
)


# --------------------------------------------------------------------------
# 6. THE TRANSITION
# --------------------------------------------------------------------------

@dataclass
class Transition:
    """X(t+) = T(X(t-), e). Gates sit inside it, in order, not around it."""

    gate_change: type[Gate] = StateChangeGate
    gate_propagate: type[Gate] = PropagationGate
    routes: tuple[Route, ...] = field(default=CHANNEL_FAMILY)

    def stages(self) -> tuple[str, ...]:
        return ("event",
                self.gate_change.NAME,
                "local state update",
                self.gate_propagate.NAME,
                "aggregate updates")


#: What the archive does NOT contain, recorded so it is not later assumed.
ABSENT_FROM_ARCHIVE = (
    "autonomous evolution: state is exactly constant between events "
    "(no _incr site fires without an external action)",
    "intrinsic stochasticity: no sampling in the model; the only "
    "nondeterminism is scheduling (async queues, grace period, lock "
    "contention, '% 10' sharding), which is infrastructure",
    "anonymous driving process: every input carries an actor identity that "
    "the gates and routing consume",
)
