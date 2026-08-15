# Differential run — diagnostic, first pass

```
AGREE 14   DISAGREE 0   UNDECIDABLE 1 executed (+5 declared)   ORACLE-DEFECT 0
```

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

## Limitations — stated because they bound what 14 AGREE means

1. **One author.** Both substrates, the oracle, and this harness were written by me from one reading
   of S1–S11. Agreement is evidence of **convergence under independent decomposition**, not of
   correctness: a shared misreading of an S-statement produces agreement just as readily. This is
   the ceiling on the experiment as constructed, and no amount of additional cells raises it.
2. **Five of six slack cells are declared, not executed.** K-1, K-2, K-3, K-5 and K-6 name
   structural differences with no runtime observable to compare. They are printed as
   `DECLARED-SLACK` rather than as `n/a` vs `n/a` cells, because a cell comparing nothing with
   nothing classifies UNDECIDABLE whatever the substrates do — the vacuity this project keeps
   finding elsewhere.
3. **The cells were chosen by me.** Zero DISAGREE partly reflects which comparisons exist. The cells
   cover every S-statement that has an executable consequence, but coverage of *an S-statement* is
   not coverage of *its consequences*.
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
