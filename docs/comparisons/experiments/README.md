# Experiments

Programs behind `../merge.md` and `../merge-plan.md`. The `.selv` files
are Selvage 0.4.9 programs; they need that toolchain (not in this
repository) and Clang 18 to build.

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
