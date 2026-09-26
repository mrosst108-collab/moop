# Differential run — diagnostic, first pass

```
AGREE 15   DISAGREE 0   UNDECIDABLE 2 executed (+5 declared)   ORACLE-DEFECT 0
```

**One DISAGREE occurred and was dissolved by the five questions.** See "The first DISAGREE" below —
it is the most informative result in this file.

**No aggregate verdict is claimed.** This is a diagnostic pass. An aggregate exists only after every
DISAGREE has been through the five questions below, and there are none to put through them yet.

## The three claims, kept apart

```
ProtoC self-test   ProtoC implements ITS OWN stated semantics consistently  (26 tests)
Differential test  the two agree on consequences the frozen semantics DETERMINE  (14 cells)
Oracle check       the comparison has not promoted a mechanism into a requirement  (K cells)
```

The first says nothing about faithfulness. P14 established that ProtoC satisfies *its reading* of
S5; it could not establish that the reading is right. That is the gap this run addresses — and only
partially, see the limitations.

## Executed cells

| cell | S | consequence compared | result |
|---|---|---|---|
| D-S1a | S1 | admissible while undeclared | AGREE |
| D-S1b | S1 | `Admissible ⇏ Declared` | AGREE |
| D-S2a | S2 | ACTIVE naming its vestigial form refused **at the boundary** | AGREE |
| D-S3a/b | S3 | vestigial endpoint unwireable on **either** side | AGREE |
| D-S3c | S3 | the refused endpoint is still retained and reachable | AGREE |
| D-S4a–d | S4 | one-way ≠ cycle · reciprocal = cycle · self-edge = cycle · no declared dependency ⇒ no cycle | AGREE |
| D-S5a | S5 | a released identity is dead once a later object exists | AGREE |
| D-S7a | S7 | the envelope is status-independent | AGREE |
| D-S8a/b | S8 | malformed refused, not dereferenced or dropped | AGREE |
| D-S9a | S9/S10 | a malformed child cannot obtain checked status from a valid parent | AGREE |
| D-S6a | S6 | record-copy vs record-reference | **UNDECIDABLE** (was DISAGREE; see above) |
| D-S11 | S11 | — | **not comparable by design**: ProtoC has no classifier |

## The slack cell that matters

**K-4 is the only executed one, and it is the point of the whole pre-registration:**

```
ProtoC:  storage reuse = yes    (identity is a value; slots recycle safely)
AWV:     storage reuse = no     (identity is a pointer; reuse would resurrect handles)
verdict: UNDECIDABLE            -- NOT DisAGREE
```

The two substrates produce **genuinely different observable values** here, and the classifier still
declines to call it a disagreement, because S5 fixes the invariant and not the mechanism — and
D-S5a already showed both satisfy the invariant. A slack cell whose two sides happen to agree would
test nothing; this one differs and is still correctly classified.

## The first DISAGREE — and why it was an oracle defect

Adding cells for the four S-statements that had none (S6, S9, S10, S11) produced the run's first
disagreement:

```
D-S6a   protoc = yes    awv = no        <- mutating the caller's record reaches inside?
```

ProtoC's registry holds the client's surface; AWV's boundary stores a copy. Two substrates, two
answers, on a cell marked *determined*. Before reporting a ProtoC defect, the five questions:

**1. Is the consequence actually fixed by S1–S11?** No. S6 reads *"ownership stops at the record
boundary; client realization objects remain client-owned; the substrate must not claim otherwise."*
That is a **ceiling on what the substrate may own, not a floor requiring it to own the record.** The
operative clause is *must not claim otherwise* — and it came from AWV's R3, which was an
**overclaim** defect, not a missing-copy defect. S6 forbids saying more than you do; it does not
mandate copying.

**2. Is the comparison invariant to known slack?** **No — and this is decisive.** K-5 pre-registered
*"ownership architecture: value identity vs opaque handle"* as slack **before this cell existed**.
D-S6a tests exactly that difference under a different label. Routing around a pre-registration is
worse than contradicting one, because it looks like a new finding.

**3. Reproducible?** Yes, both sides deterministically.

**4. Does either side rely on an implementation artifact?** Yes — both answers follow directly from
the ownership architecture K-5 declared slack.

**5. Does the derivation entail the expected result?** No. `DERIVATION.md`'s S6 entry and
`SEMANTICS.md`'s invariants-not-mechanisms section both state that S6 requires no particular
ownership architecture.

**Verdict: ORACLE DEFECT.** The cell's *classification* was wrong — not the frozen semantics, and
not either substrate. Reclassified as undetermined; **S6 is unchanged.** An oracle edited to match
the code would be the failure mode; an oracle whose cell-marking is corrected against its own
derivation record is the mechanism working.

**What this cost, had the pre-registration not existed:** a reported ProtoC defect, a "fix" making
ProtoC copy records it has no reason to copy, and a false convergence — two substrates agreeing
because one was bent toward the other.

**A residue worth recording:** S6 may have **no executable determined consequence at all.** Its
content is a prohibition on *claims*, and a claim is a documentation property. R3 was found by
reading a comment against behaviour, not by running anything. That is a limit on what differential
testing can reach, and it is not fixable by adding cells.

## Limitations — stated because they bound what 15 AGREE means

1. **One author.** Both substrates, the oracle, and this harness were written by me from one reading
   of S1–S11. Agreement is evidence of **convergence under independent decomposition**, not of
   correctness: a shared misreading of an S-statement produces agreement just as readily. This is
   the ceiling on the experiment as constructed, and no amount of additional cells raises it.
2. **Five of six slack cells are declared, not executed.** K-1, K-2, K-3, K-5 and K-6 name
   structural differences with no runtime observable to compare. They are printed as
   `DECLARED-SLACK` rather than as `n/a` vs `n/a` cells, because a cell comparing nothing with
   nothing classifies UNDECIDABLE whatever the substrates do — the vacuity this project keeps
   finding elsewhere.
3. **The cells were chosen by me.** Zero surviving DISAGREE partly reflects which comparisons
   exist. Every S-statement now has at least one cell except **S11**, which is not comparable by
   design, and **S6**, whose only cell turned out undetermined. Coverage of *an S-statement* is
   still not coverage of *its consequences*.
4. **An endpoint correspondence is asserted**, not derived: ProtoC `step`/`couple`/`state` ↔ AWV
   `transition`/`coupling`/`state`. It is recorded in the harness because an unstated correspondence
   is exactly where a false disagreement would hide.

## The five questions — for any future DISAGREE

Before an aggregate verdict, each DISAGREE must answer:

1. Is the consequence actually fixed by S1–S11?
2. Is the comparison invariant to the known implementation slack?
3. Can each side's result be independently reproduced?
4. Does either side rely on an implementation artifact?
5. Does the oracle's derivation actually entail the expected result?

And the pre-registration is the test: a K-cell reported as DISAGREE is an **oracle defect**, and it
is not exempted after the fact.

## What the most interesting future result would be

Not a ProtoC bug. It would be a DISAGREE that survives reproduction and turns out to show
**S1–S11 do not determine the disputed consequence** — a specification discovery, correctly
recorded as UNDECIDABLE. The converse, where the derivation genuinely entails one side and the
other violates it, is the valuable DISAGREE.
