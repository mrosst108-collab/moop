# Related projects

## Selvage 0.5.0 (`selvage/`)

Selvage is moop's sibling language: a minimal language in which every
rule reads both ways and every loss is stated, with a Python toolchain
and a C23 backend. Its own README and its language description
(`selvage/SPEC.md`) say what it is.

**How the two are related.** The merge between them is complete
(`../docs/comparisons/merge-plan.md`):
- Selvage took one mechanism from moop: the CCNOT tape, as the prelude
  record `CcnotTape` and the rules `tape_tick`, `draw` and `birth`;
- moop stays a separate language, and is the reference model for that
  tape (ruling G1);
- wiring 1 is frozen, and both languages reproduce
  `../tests/tape_vectors.txt` byte for byte (G2).

**Where this tree comes from.** It is the Selvage 0.4.9 release archive
(sha256 `ef8b7e705be5a4d57a3b79c99b58d259ff626c65669843f3eaa23d3b890aa2e2`)
with eight patches applied, in this order:

```
0001 → 0003 → 0004 → 0005 → 0006 → 0007 → 0008 → 0009
```

The patches are in `../docs/comparisons/selvage-patches/`, with the
handoff report that records each one's changes and validation. Patch
0002 is excluded: ruling A1 keeps `repeat while`. Applying the patches
to a fresh copy of the archive reproduces this tree byte for byte.

**What 0.5.0 adds to 0.4.9:**
- two defects corrected;
- the extent of each answer rule reported;
- the audit rulings A2 and A3;
- the CCNOT tape and its domain;
- the reversible profile, in part (`selvage circuit`);
- the request group `Measure`, answered by nothing;
- the rulings C1 to C5 and N1 to N3, ratified.

The full list is in `selvage/SPEC.md`, XII.3 and XII.4.

**Running it.** Selvage needs Python 3, and Clang with C23 for its
compiled backend. From `related/selvage`:

```sh
python3 -m selvage --version                 # selvage 0.5.0
python3 -m unittest tests.test_selvage       # the suite: 199 tests
python3 tools/mutation_check.py              # 153 mutations, about 40 minutes
python3 tools/check_description.py           # every code block of SPEC.md
(cd bench && python3 run.py 5)               # benchmarks against C and Rust
```

**Its place in this repository.**
- **moop's build ignores it.** The Makefile compiles only `src/*.c`, and
  `make test` does not run Selvage's suite.
- **The trace: three claims, three pieces of evidence.**

  | Evidence | What it establishes |
  |---|---|
  | moop's `make test`, through `test_wiring_1_trace`, runs moop's tape through the scenario and compares the result with `../tests/tape_vectors.txt` | moop's runtime reproduces the trace |
  | Selvage's own suite, through `TestCcnotTape.test_the_trace_is_moop_s` and `test_compiled_code_prints_moop_s_trace`, runs the scenario in Selvage's interpreter and its compiled code, and compares the output with `selvage/tests/programs/ccnot_tape.trace` | Selvage's runtime reproduces its copy of the trace. moop's `make test` does not run this |
  | moop's `make test` compares the two stored files byte for byte | The two copies of the trace are the same file. It runs neither language |

  Only together do they show that the two languages correspond. The
  third check exists so that a change to either copy is noticed in this
  repository. It does not stand in for running Selvage's suite.
- **Changing Selvage.** Changes are made against this tree and recorded
  as Selvage changes, not mixed into moop's. The archive contains no
  licence file.
