# Selvage

A minimal language in which every rule reads both ways, every loss is said aloud, and every undecided question is asked aloud.

- **One definition per rule.** A rule is a set of clauses. The checker classes it as a bijection, a partial bijection or lossy, and the arrow states which: `shape <-> shape` on a certified rule, `shape => shape` on a lossy one. The wrong arrow is refused either way.
- **Inverses are code, and so is the inverter.** Inversion is defined by `mirror`, a rule of the prelude on code that the checker certifies and that is its own inverse. `invert` runs that rule and has no table of its own; the same checker checks the inverse and the same forward engine runs it, in the interpreter and in C23. `selvage invert` prints it.
- **Two tiers, one set of gates.** What the system does is conservative: the prelude has no lossy clause. What a program may do is dissipative, through an explicit loss. An ordinary gate is a reversible gate followed by `discard` (`examples/gates.selv`).
- **Losses are declared.** A lossy rule writes `=>`. Each loss is a `keep` message to Root, the system-facing root, whose rule is a bijection on the journal; the system rewinds by taking those messages back. An entry names the code that kept it by that code's identity, and code takes back only what its mirror kept. Code is identified by what it is and what it refers to: a variable by its binding, and a rule, a request or an answer by its identity. Renaming any of them changes no identity, and holding an identity grants no authority.
- **One binding per name.** A name is bound once where it can be seen: binding it again is refused, and `set` overwrites. Nothing hides anything.
- **Loss is counted exactly where it can be.** A clause choice is kept only where the output leaves one; a dropped value is charged the bits that tell apart what it could have been; a value that can still be computed is dropped for nothing. Both backends charge alike.
- **One-to-one is not onto.** `<->` certifies that a rule is one-to-one. `selvage check` reports apart whether it is a permutation, an embedding or partial, and only as far as that is established.
- **Functions and procedures.** An expression rule with an empty `uses` row is a function. With a row it is a procedure: it keeps the replies the world gives it, and lists `System` when it reaches `keep`.
- **CCNOT is the base rule.** Gates, the ripple-carry adder that realizes word addition, exchange and fan-out are built from it in Selvage itself. `selvage lineage --verify` shows how every rule, answer and prototype rests on it, each link with its certificate, and runs the gate-level realizations.
- **Code is data, and so are declarations.** Expressions, steps, clauses and the journal are ordinary data that rules pattern-match; a rule, an answer, a type, a request group and the whole program are forms too, of types the prelude declares, and `selvage census` shows that nothing escapes. Holding a form grants nothing: running constructed code (`evaluate`) needs the checker's admission.
- **Prototypes by delegation.** An answer delegates a request it has no rule for to the one component of its state that answers it, and the certificate stays with the rule that answers. `Object`, the user-facing root, holds a `Root` and delegates everything to it.
- **Refusal is a request.** A division by zero, an index out of range or any other refusal goes to the nearest installed answer for `Refusal`; with none, Root ends the run with status 70.
- **Retention is sealed, disclosure is mediated.** `keep` is sealed to Root (`request System for Root`): a program can neither send nor answer it, nor make a Root. `history` is asked through `Witness`, and a host installs its own answer to decide what the code inside it reads. A host may give its copy back, but not while keeping what it read, and not through an answer that kept a record of it.
- **A stated proof.** The soundness theorem is proved for a model of the language (SPEC.md XI.3); the model is also written out as a second evaluator and compared with the interpreter on generated rules.
- **Defined depth.** A run that nests deeper than its bound (10,000 rule calls unless set with `--depth`) is refused with status 70, identically in the interpreter and in compiled code. A self tail call is a loop.
- **The CCNOT tape.** The prelude rules `draw` and `birth` give deterministic draws and certified births from moop's CCNOT tape, pinned to a trace of moop's implementation in both backends. A draw is an observation, not a random bit; a program makes its own tape and passes it along (SPEC.md VI.6).
- **MAYBE.** `Trit` (`true | false | maybe`) carries Kleene logic; `decide` sends only the undecided cases to whoever answers `Decide` (a rule book, an LLM through `--decide command:…`, a person), and every decision is kept and replayable.
- **Live.** `selvage repl` checks each line before it runs.
- **Reversible profile, in part.** `selvage circuit` lays out a certified rule over bits as X, CNOT and CCNOT gates, its words fixed at layout, and checks the circuit against the interpreter by simulation. Nothing runs on reversible or quantum hardware (SPEC.md IX.4).
- **Measurement, declared and unanswered.** The prelude declares the request `measure`, and nothing answers it: `ask measure()` is refused with status 70 until a quantum profile installs an answer. There are no quantum types (SPEC.md VII.4).
- **Two backends.** Programs run in a reversible interpreter, or compile to C23 with no undefined behaviour. On seven benchmarks the C23 output runs within 12% of handwritten C23 and 6% of Rust in the geometric mean (`bench/results.md`), and about 580× faster than Io.

The language description is [SPEC.md](SPEC.md), specification 0.4. This toolchain is 0.5.0 and reads its notation. Part XII of the description lists what is ratified and not yet built.

## Quick start

```sh
python3 -m selvage check examples/orbit.selv     # certify and classify every rule
python3 -m selvage run   examples/orbit.selv     # interpret
python3 -m selvage build examples/orbit.selv     # compile to C23 with clang
./examples/orbit
python3 -m selvage call examples/orbit.selv damped_orbit "Phase(1000, 5)" --params "10, 50" --rewind
python3 -m selvage invert examples/orbit.selv damped_orbit   # the derived inverse, as Selvage
python3 -m selvage lineage examples/prototypes.selv Resettable --verify   # the chain to ccnot, each link certified
python3 -m selvage census examples/declarations.selv                      # which constructs are forms a rule takes apart
python3 -m selvage circuit examples/gates.selv ripple_add "(array(Bit, 4), array(Bit, 4), Bit(0))" --gates   # a certified rule as gates
python3 -m selvage run examples/triage.selv --decide "command:python3 examples/decider.py" --record decisions.json
python3 -m selvage run examples/triage.selv --decide replay:decisions.json
python3 -m selvage repl
python3 -m unittest discover -s tests            # conformance suite
python3 tests/roundtrip_gen.py 2000              # generated rules: undo is the inverse, no two inputs share an output
python3 tests/generated_04.py 500                # generated programs with oracles: arrows, delegation, rows, operators, Any, refusal,
                                                 #   seal, witness, depth, structures, decisions, journal, names, accounting, extent, forms, and the model of the proof
python3 tests/reference_model.py 600             # the interpreter and invert against the model of SPEC.md XI.3
python3 tools/mutation_check.py                  # break the toolchain 153 ways; the generated tests must notice each
python3 tools/check_description.py               # every code block of SPEC.md, checked with the toolchain
python3 bench/run.py                             # Selvage vs C23 vs Rust
```

```selvage
rule leapfrog(k: I64) takes (I64, I64) returns (I64, I64)
    (q, p) <-> (q, p) where
        subtract k * q / 2 from p
        add p to q
        subtract k * q / 2 from p

rule main uses Output
    s is leapfrog(3)((100, 0))
    output s                          # (-50, -75)
    output undo leapfrog(3)(s)        # (100, 0): the inverse was derived, not written
```

## Layout

| Path | Contents |
|---|---|
| `selvage/lexer.py`, `parser.py`, `printer.py` | Pythonic-indentation syntax; canonical printer |
| `selvage/forms.py` | Forms, words, identity hashes, loss weights |
| `selvage/checker.py` | Types, R2 certification, R3 linearity, R4 updates, R5 seals, R6 rows; elaboration; checks every derived inverse |
| `selvage/codeid.py` | The identity of code: variables by their binding; rules, requests and answers by identity; cycles identified as a whole |
| `selvage/account.py`, `extent.py` | What a kept entry is charged; how far a certified rule reaches (permutation, embedding, partial) |
| `selvage/declared.py`, `census.py` | Declarations and programs as values a rule takes apart; the form census |
| `selvage/invert.py` | `invert`: reads the clauses of the prelude's `mirror` and runs them; blocks as sequences |
| `selvage/lineage.py` | What each rule's reversibility rests on, down to `ccnot` |
| `selvage/circuit.py` | The reversible profile, in part: certified rules over bits laid out as X, CNOT and CCNOT, checked by simulation |
| `selvage/interp.py` | One forward engine for rules and inverses; `undo`, rewind, decisions; the journal as Root's state |
| `selvage/deciders.py`, `repl.py` | World deciders for `decide`; the interactive prompt |
| `selvage/cgen.py`, `runtime/selvage_rt.h` | C23 backend and runtime |
| `selvage/prelude.selv` | `mirror`, the definition of inversion; `ccnot`; `cnot`, `toggle`, `ripple_add`, `exchange`, `fanout`; the Kleene circuits; `Journal`, `System` (sealed to Root), `Witness`, `Refusal`, `Root`, `Object`; the CCNOT tape (`CcnotTape`, `tape_tick`, `draw`, `birth`); `Measure`, answered by nothing |
| `examples/` | adder, gates (two tiers), orbit, arrays, shapes, messages, derivative, triage (MAYBE), prototypes, witness (hosts and history), inversion (the inverter as a certified rule), declarations (declarations and the program as data) |
| `tests/` | conformance suite; `roundtrip_gen.py` generates random certified rules and checks each for a round trip; `generated_04.py` generates programs with an oracle for each 0.4 change; `reference_model.py` is the model of the soundness proof, as an evaluator |
| `tools/` | `check_description.py`: the description check; `mutation_check.py`: the mutation check |
| `bench/` | benchmarks in Selvage, C23 and Rust (`results.md`); against Io in `bench/io` |

Requires Python 3 (tested with 3.13) and clang 18 or later; Rust only for the benchmarks.
