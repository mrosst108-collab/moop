# Experiments

Programs behind `../merge.md` and `../merge-plan.md`. The `.selv` files
are Selvage 0.4.9 programs; they need that toolchain (not in this
repository) and Clang 18 to build.

## Current — the merge candidate

| File | What it is |
|---|---|
| `ccnot_tape.selv` | Candidate prelude text: `Tapes`, `tape_tick`, the `Draw` requests and the `CcnotTape` answer, with bounded heads as in `src/tapeloop.c` |
| `conform.selv` | The conformance scenario in Selvage: 40 draws, a birth, 20 draws from the child, and the birth undone |
| `moop_trace.c` | The same scenario against moop's C tape (`src/tapeloop.c`, `src/gates.c`, `src/logic.c`), printed in Selvage's output format |
| `tape_vectors.txt` | The 66-line trace both produce, byte for byte |
| `instance_copy_defect.selv` | Selvage defect found on the way: a copy of an answer instance shares its array with the original |

To regenerate the moop side from the repository root:

```sh
gcc -std=c2x -Isrc docs/comparisons/experiments/moop_trace.c \
    src/tapeloop.c src/gates.c src/logic.c -o /tmp/moop_trace
/tmp/moop_trace | diff - docs/comparisons/experiments/tape_vectors.txt
```

The Selvage side is `selvage run conform.selv`, compared with the same
file.

## Earlier — superseded by the files above

These used one `U64` tick counter in place of bounded heads, which is
not moop's machine at lengths that do not divide 2⁶⁴.

| File | What it showed |
|---|---|
| `tape.selv` | Tick and draw certify; `undo` refuses a draw that was not produced |
| `birth.selv` | A birth certifies as an embedding and `undo` restores the parent |
| `tick_timing.selv` | Literal tape lengths do not make the tick faster |
| `feistel.selv` | A three-line certified permutation, the competitor for hot randomness |
