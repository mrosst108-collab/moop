# Experiments

Programs behind `../merge.md` and `../merge-plan.md`. The `.selv` files
were written for Selvage 0.4.9, and the tables below describe them as
they were then. Selvage 0.5.0, the integrated toolchain, is now in this
repository at `related/selvage`. Under it (checked 2026-11-18):

- **Still run:** `conform.selv` still prints `tests/tape_vectors.txt`
  byte for byte, and `tape.selv`, `feistel.selv`, `tick_timing.selv` and
  `instance_copy_defect.selv` still pass the checker.
- **Refused:** `ccnot_tape.selv` and `birth.selv`, because the names
  they declare (`CcnotTape`, `tape_tick`, `draw`, `birth`) now belong to
  Selvage's prelude (*is defined twice*). They are kept as records of
  what was admitted. The live text is in `related/selvage/selvage/prelude.selv`.

## Current — the merge candidate

| File | What it is |
|---|---|
| `ccnot_tape.selv` | The prelude text as admitted (patch 0003, ruling G7): the record `CcnotTape` and the rules `tape_tick`, `draw`, `birth`, with bounded heads as in `src/tapeloop.c`. The earlier answer version (`CcnotTape for Draw`) is in git history |
| `conform.selv` | The conformance scenario in Selvage, with rule calls: 40 draws, a birth, 20 draws from the child, and a birth taken back. Prints `tests/tape_vectors.txt` byte for byte, in the interpreter and compiled |
| `instance_copy_defect.selv` | Selvage defect found on the way: a copy of an answer instance shares its array with the original |
| `tape_statistics.c` | moop's tape (wiring 1, 8/13 cells), exhaustively: the cycle structure of all 2²¹ states and the bias and correlation of draws. Build and run instructions are in its header; results are in `docs/model.md` |

The trace both implementations must reproduce, byte for byte, is
`tests/tape_vectors.txt`. moop checks it in `make test`
(`test_wiring_1_trace` in `tests/test_core.c`). The Selvage side, from
the repository root with the 0.4.9 toolchain:

```sh
selvage run docs/comparisons/experiments/conform.selv | diff - tests/tape_vectors.txt
```

## Earlier — superseded by the files above

These used one `U64` tick counter in place of bounded heads, which is
not moop's machine at lengths that do not divide 2⁶⁴.

| File | What it showed |
|---|---|
| `tape.selv` | Tick and draw certify; `undo` refuses a draw that was not produced |
| `birth.selv` | A birth certifies as an embedding and `undo` restores the parent |
| `tick_timing.selv` | Literal tape lengths do not make the tick faster |
| `feistel.selv` | A three-line certified permutation, the competitor for hot randomness |
