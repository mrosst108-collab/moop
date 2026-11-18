# Selvage — Language Description

**A minimal systems language in which transformations are explicit, reversible rules are certified, information loss is declared and accounted for, and undecided questions are routed through requests.**

*Specification 0.4 · toolchain 0.5.0 · working name*

Selvage has three semantic mechanisms:
- **Form** represents values, structures, code and state.
- **Rule** transforms forms through explicit, checkable clauses.
- **Request** connects a transformation to an answer, its state and its environment.

A program is a form. Running it applies rules to states: each step denotes a partial function on states, undefined where the step refuses (XI.3). Interaction goes through requests.

`ccnot` (controlled-controlled-NOT) is not a fourth mechanism. It is the primitive at the base of Selvage's reversible-realization lineage. Everything else is derived from the three mechanisms, or introduced as a library, a notation or a realization. The interpreter and the C23 backend do not run programs as gate circuits; they use native operations. Gate lineage says how the language's reversible operations can be realized, not how an ordinary run is executed.

Code as data and reversibility support each other without being one property:
- code as data makes a rule, and its inverse, values that a rule can take apart and build;
- a certified rule is a bijection between its domain and its codomain, and its inverse is derived by transforming its code;
- the checker checks the derived inverse by the same certification rules as any rule;
- information accounting covers what is not reversible.

That certificate is a property of the transformation; it does not by itself certify a machine-code sequence or a gate circuit. A realization is supported separately, by a checked gate-level rule, a comparison run on demand, or a cited theorem, and the lineage report says which (VII.6).

Information loss is explicit. Destructive steps, external decisions and commit points are declared and accounted for. Where recovery needs retained information, the system records it in a journal under Root's authority. A rewind can reconstruct a lossy run only while that run is still eligible: it is the newest that kept anything, and no later retained entry or commit point stands in the way (VII.1). Recoverability does not make the transformation bijective, and it gives user code no authority over the journal.

The central proposition: **a program is a form; execution is a rule; interaction is a request; reversibility is certified; information loss is accounted for; and restoration remains subject to authority.**

Selvage draws on Quorum-like readable syntax, Io's live object model and metaprogramming, Rust's ownership discipline, C23's computational control and the mathematical influence of RME-7. These are design influences and objectives, not claims of equivalence or of feature parity.

---

## I. Design Constitution

### I.0 Reading this description

This description states design rules, reports what toolchain 0.5.0 implements, and records the evidence for each claim. The three are kept apart throughout.
- Parts II to VIII describe the language: its mechanisms, types, transformations, interactions, reversibility and code representation.
- Parts IX and X describe backends, realization profiles and the RME-7 library direction.
- Part XI reports tests, measurements and the stated soundness proof. Tests are evidence about the cases run; they are not proofs.
- Part XII records binding rulings, deprecated forms, implementation work and open questions.

The Python interpreter is the reference implementation and covers the most of the language; some ratified items remain specified or deferred (XII.4). The C23 backend is partial: answers and messages (`ask`, `->`, `with`), quoted code, recursive data, rewind and `history` stay in the interpreter (IX.2). The reversible realization profile is built in part, for certified rules over bits whose words are layout; the quantum profile is absent, apart from the request group `Measure`, which nothing answers (VII.4, IX.4). The suite has 199 tests.

What is proved, what is an open obligation, and what rests on tests:

| Claim | Standing |
|---|---|
| For the model of XI.3: a certified rule is one-to-one, its derived inverse returns its input and refuses what it does not produce, and a lossy run rewinds with its journal | Proved: a written proof, not machine-checked (XI.3) |
| The checker establishes the model's obligations, O1 to O6, for every rule it certifies | Not proved. Generated tests and the mutation check (XI.2) |
| The interpreter runs the model | Not proved. Compared with a second evaluator on generated rules (XI.2) |
| The C23 backend agrees with the interpreter | Tests only (XI.4) |
| A gate-level realization is faithful | Lineage, `--verify`, and the gate tests (VII.6) |
| Over closed types, the charges of the runs that share a result are a code for them | An open proof obligation; tested on small types (VII.5) |
| Over open types, ε bounds what was lost | Not claimed: a convention of accounting (VII.5) |

A proof about the model is not a proof about the toolchain. A defect in the checker leaves the proof standing and falsifies the claim that the checker meets the model's obligations.

### I.1 Status model

Every status entry in this description carries three independent fields.

| Field | Values |
|---|---|
| **Implementation** | **Built**: in the toolchain · **Partial**: built for a subset · **Specified**: defined here, not built · **Deferred**: deliberately left for later by a ruling · **Absent**: neither designed in detail nor built |
| **Design** | **Ratified**: a binding ruling (the register in XII.1, and the hard constraints) · **Proposed**: defined, awaiting ratification · **Open**: needs a ruling · **Deprecated**: superseded by a ruling, and listed in XII.2 only |
| **Evidence** | Named tests · generated tests · static check · runtime observation · proof (stated in this description) · theorem (cited) · benchmark · none |

The fields answer five separate questions, and no answer implies another:

| Question | Where it is answered |
|---|---|
| Normative: is this required behaviour? | Design is Ratified |
| Implemented: does the toolchain do it? | Implementation is Built or Partial |
| Tested: which tests cover it? | Evidence names them (the suite is listed in XI.4) |
| Proven: is there a stated proof? | Evidence says "proof". One theorem is proved: soundness, for the model of XI.3 |
| Deferred: deliberately not yet implemented? | Implementation is Deferred |

The toolchain is at 0.5.0 and reads the notation of this description. Its suite has 199 tests (XI.4). An entry is marked Built only where the toolchain does what the entry says, and its evidence cell says what shows it. A ratified entry that is not built stays Specified, and XII.4 lists those in the order they are to be built.

### I.2 Hard constraints

| # | Constraint | How Selvage meets it | Implementation | Design | Evidence |
|---|---|---|---|---|---|
| H1 | Foundation-first synergy: derive higher-level capabilities from the smallest sufficient foundations; prefer composition to specialized mechanisms | Every capability is admitted at the lowest tier that can build it (I.4). Inversion is a code transformation run by the one forward engine and checked by the one checker; every reversible realization traces to `ccnot` (VII.6) | Built | Ratified | TestInversion: the inversion laws, and lineage reaching `ccnot` |
| H2 | Minimalism: minimize independent mechanisms, semantic rules, special cases, compiler machinery and runtime infrastructure | Three mechanisms, one realization primitive, eight checking rules, 38 keywords. There is no backward interpreter or reverse emitter: the prelude rule `mirror` derives inverse code from the backward reading of each step (V.6, VIII.2) | Built | Ratified | TestInversion: one engine runs rules and their inverses; TestC23Backend: the same inverse, compiled |

### I.3 Soft constraints

| # | Constraint | How Selvage meets it | Implementation | Design | Evidence |
|---|---|---|---|---|---|
| 1 | Quorum-like naturalism | Programs read as sentences: `add p to q`, `swap a[i] and a[j]`, `repeat with i from 1 to n`, `t was a * k`, `if … otherwise`, `=` and `not=`. Loss is a word or an arrow (`discard`, `set`, `commit`, `=>`); so is deferral (`decide`) | Built | Proposed | TestSurface; TestPrograms |
| 2 | System-facing reversibility | What the system does is conservative, and what a program may do is dissipative through an explicit loss (II.5). Every retained loss is a `keep` message to Root. The system rewinds the newest eligible run exactly, by running the rule's derived inverse; user code can `undo` only certified rules (VII) | Built | Ratified | TestTwoTiers; TestReversibility; TestInversion.test_semantic_round_trips |
| 3 | Homoiconicity | Nothing in the language's semantic structure escapes representation as a form. Code, data, patterns, steps, clauses, requests, decisions and journal entries are forms that rules inspect and transform, and inverses are code. Declarations and the program are forms of types of their own, distinct from `Code`. The form census finds nothing that escapes. Typed encodings and the live run are specified and not built (VIII.1) | Partial | Ratified | TestDeclarations; TestCensus; TestInversion; TestSurface.test_quoted_code_is_data |
| 4 | RME-7 influence | RME-7 as a library and conformance layer, not a source of kernel features. The conservative/dissipative split is the language's own invariant (II.5); symbolic differentiation is a library rule over forms (X) | Partial | Ratified | TestPrograms.test_interpreter_outputs (orbit, derivative) |
| 5 | Message passing `->` | `account -> withdraw(30)` sends a request to a named answer instance; a message is taken back by the derived inverse of the rule that answered it (VI.2) | Built | Proposed | TestReversibility.test_undo_a_message; TestInversion.test_semantic_round_trips |
| 6 | Inheritance `<-` | Field-only structural derivation of record types. Prototype behaviour is delegation through Request (VI.3) | Built | Ratified | TestPrograms.test_interpreter_outputs (shapes: `split`); TestInversion.test_delegation_keeps_each_certificate_where_it_is_answered |
| 7 | Bijective `<->` | `<->` marks the clauses of rules the checker certifies; lossy rules write `=>` (II.4, V.2) | Built | Ratified | TestChecker.test_the_arrow_states_the_certificate; generated rules (XI.2) |
| 8 | Pythonic whitespace | Indentation opens and closes blocks; there is no `end` (IV) | Built | Proposed | TestSurface |
| 9 | CCNOT primitive (reversible realization) | `ccnot` is the four-clause prelude rule at the base of the reversible-realization lineage, with the derived gate rules (`cnot`, `toggle`, `ripple_add`, `exchange`, `fanout` and the Kleene circuits). It is not on the ordinary execution path, and native execution does not need it. The clause test certifies a transformation; `ccnot` grounds its reversible realization (II.3, VII.6) | Built | Ratified | TestCCNOT; `lineage --verify` |
| 10 | MAYBE | `Trit` with Kleene's strong logic, and a general decision protocol: only the undecided cases leave the program, to a rule book, a person, a model or any other answer (VI.4) | Built | Ratified | TestMaybe; TestSemanticContracts.test_kleene_logic_is_a_verified_gate_circuit |
| 11 | C23, Rust and Io competitiveness (systems programming) | Competitive generated code, measured; layout, ABI/FFI, atomics, freestanding operation and static request lowering are objectives with their own status (IX.3) | Partial | Ratified | Benchmarks (IX.5) |

**Realization objective: quantum readiness.** Certified finite transformations may be realized on reversible and quantum hardware through separate realization profiles (IX.4). Ordinary implementations carry no quantum hardware, simulation or runtime machinery, and quantum readiness authorizes no quantum claim about ordinary Selvage execution: the language stays classical unless a quantum realization is explicitly selected.

| Objective | Implementation | Design | Evidence |
|---|---|---|---|
| Quantum readiness, as realization profiles outside the kernel | Partial (reversible profile); Absent (quantum profile), apart from the `Measure` group, which nothing answers | Ratified | TestReversibleProfile; the circuits generator (XI.2); TestMeasure |

### I.4 Admission

**The derivation ladder.** Tiers give dependency order, not run-time order.

| Tier | Contents |
|---|---|
| 0 | Form, Rule, Request; checking rules R1–R8 |
| 1 | `Bit`, `ccnot`, reversible bit rules (`cnot`, `toggle`, `exchange`, `fanout`, `ripple_add`) |
| 2 | Words and exact arithmetic, tuples, records, variants, arrays, `Trit` and Kleene circuits |
| 3 | `Code`, clause rules, elaboration, inversion |
| 4 | Answers, instances, delegation, messages, decisions, the journal and the roots |
| 5 | Libraries and notation: RME-7 prelude, scheduler, certified notation |

**The admission test.** A candidate capability passes four steps, in order:
1. **Foundation:** name the mechanisms it is built from, and the lowest tier that can build it.
2. **Synergy:** it strengthens at least two admitted elements, or makes at least two unnecessary.
3. **Interference:** it weakens none.
4. **Uniformity:** it carries no internal special case.

Two admissions show the test at work:
- **MAYBE** passes at Tiers 2 and 4. Its value is a two-bit shape realized from `ccnot`, and its decision is a request. It strengthens Request, which gains a decision protocol, and Form, since questions are code. It makes unnecessary a separate oracle interface, a probabilistic-logic subsystem and a tool-calling layer.
- **`invert`** passes at Tier 3. It is built from Form (steps are data) and Rule (an inverse is a clause rule). It strengthens Rule, whose inverse becomes printable, hashable and checkable code, and Request, since a message is taken back by an ordinary inverse rule. It makes unnecessary a backward interpreter, a reverse emitter and a hidden uncompute table.

---

## II. Semantic Kernel

### II.1 Three mechanisms

| Mechanism | What it is | What it makes unnecessary |
|---|---|---|
| **Form** | The one representation: an atom (word, float, `true`, `false`, `maybe`, text) or a tagged node with ordered children | A syntax tree separate from data; a reflection interface; a serialization format |
| **Rule** | A set of clauses, each a single template matched on one side and built on the other. A rule runs forward only; its inverse is another rule, the sides swapped and each step read backward (V.6) | Separate functions, constructors, pattern matching and hand-written inverses; a backward interpreter |
| **Request** | `ask op(args)` goes to the nearest installed instance that answers `op`; `instance -> op(args)` goes to a named one; `decide` sends an undecided condition outward. An answer has one rule per request, from `(request, state)` to `(reply, state)` | Mutable state, objects, effect handlers and oracle interfaces as separate mechanisms |

| Mechanism | Implementation | Design | Evidence |
|---|---|---|---|
| Form, Rule, Request as the only semantic mechanisms | Built | Ratified | TestSurface; TestPrograms; TestInversion |

### II.2 Three notions kept apart

| Notion | Property of | Meaning |
|---|---|---|
| **Reversibility** | A transformation | A bijection between its declared domain and codomain: every output identifies exactly one input. This is what `<->` states |
| **Recoverability** | The information a run retains | A transformation may lose information from its own state while the run keeps what is needed to reconstruct it elsewhere: (x, y) → (x, 0) is not reversible, but (x, y) → ((x, 0), y) is. The journal is a structured realization of the second arrangement |
| **Authority** | Who may retrieve that information | An inverse program existing does not let user code take back what the system holds. Only the system writes entries and takes them back (the Root seal, VII.3). Reading is an inquiry through `Witness`, which a host can answer itself to limit what inner code retrieves (VII.2) |

A representation can be reversible without its computation being reversible; a computation can be recoverable without being reversible; and neither establishes authority to recover. The inverse of code is itself code that anyone may compute (VIII.2), which says nothing about whether running it returns the input, or about who may run it.

| Notion | Implementation | Design | Evidence |
|---|---|---|---|
| The three kept distinct | Built | Ratified | TestInversion.test_authority_stays_outside_the_code; TestJournalContract; TestMirror; TestJournalIdentity |

### II.3 The realization primitive

```selvage
rule ccnot takes (Bit, Bit, Bit) returns (Bit, Bit, Bit)
    (0, b, c) <-> (0, b, c)
    (1, 0, c) <-> (1, 0, c)
    (1, 1, 0) <-> (1, 1, 1)
    (1, 1, 1) <-> (1, 1, 0)
```

The left sides are exclusive and exhaustive and the right sides exclusive, so the clause test certifies `ccnot` with nothing else assumed. `ccnot` is a computational primitive, not a semantic mechanism. A text value is a representation, a request is an interaction and a prototype is a composition of answers; none is a gate. What `ccnot` grounds is the reversible realization of operations, link by link (VII.6). It is not on the ordinary execution path: the interpreter and the C23 backend compute with native operations.

**Certification and lineage are distinct.** The clause test (R2) certifies a transformation. `ccnot` grounds the lineage of its reversible realization. A certificate's correctness does not depend on its gate ancestry, and `<->` certifies a transformation, not the circuit that realizes it.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| `ccnot` as the realization primitive | Built | Ratified | TestCCNOT.test_ccnot_truth_table_and_self_inverse |

### II.4 Eight checking rules

| # | Rule | Statement | Implementation | Design | Evidence |
|---|---|---|---|---|---|
| R1 | Shapes are types | A type is a set of shapes. `Bool` (`true \| false`) is a sub-shape of `Trit` (`true \| false \| maybe`): a `Bool` is given where a `Trit` is declared, and a `Trit` never where a `Bool` is | Built | Proposed | TestChecker.test_refusals (type mismatch); TestMaybe.test_undecided_conditions_are_refused; TestDeclaredTypes; the declared-types generator (XI.2) |
| R2 | Certification | A clause rule is a **bijection** if its left sides are exclusive and exhaustive and its right sides exclusive, and every step is certified. It is a **partial bijection** if both sides are exclusive. Otherwise it is **lossy**. The arrow must match: `<->` for a certified rule, `=>` for a lossy one; a mismatch either way is refused. An answer is certified one request at a time | Built | Ratified | TestChecker.test_classification, test_the_arrow_states_the_certificate; generated rules (XI.2) |
| R3 | Linearity | Every name bound on the left is consumed exactly once: by the right side, by `discard`, by a move into a consuming rule, or by `was`. Reading does not consume. Values are owned and copied, never shared | Built | Proposed | TestChecker.test_refusals; TestInversion.test_elaborated_code_leaves_nothing_implicit |
| R4 | Exact updates | A step may not read what it changes, as a gate's controls differ from its target. `add`, `subtract` and `swap` may read anything except their own target. The index that selects a changed cell may not read anything the step changes; reading an array's length is allowed when only its elements change. The parameters of a consuming call may not read what the call consumes. Elements are checked by index arithmetic, at run time where that cannot settle it | Built | Proposed | TestChecker.test_runtime_alias_check; TestSoundness; generated rules (XI.2) |
| R5 | Roles by seal | A sealed declaration can be used only by code that holds its seal: only that code makes or opens an instance of a sealed answer, or sends or answers a request of a sealed group. `request G for A` seals the group `G` to the answer `A`, and the place that declares them holds the seal. The Root seal is the first (VII.3); seals for roles and units remain proposed | Built | Ratified | TestSealAndWitness.test_the_seal_is_a_rule_about_places_and_names_no_declaration; TestGenerated04.test_every_route_to_what_is_sealed_is_refused |
| R6 | Rows contain | A rule's `uses` row lists every request group it can reach, including `Decide`, and those of the rules it calls. Reaching `keep` is shown uniformly: by the `=>` arrow on a clause rule, and by `System` in the row of an expression rule, which has no arrow (V.3). A request an installed answer takes is not in the row; one it does not take continues outward and stays in it. An answer has no row: what its rules ask is in the row of whoever messages or installs it. A commit point is in `System` (V.3, VI.2) | Built | Ratified | TestChecker.test_r6_rows_contain_what_a_rule_reaches, test_functions_and_procedures_are_told_apart_by_the_row; TestGenerated04.test_rows_tell_functions_from_procedures_and_show_reaching_keep |
| R7 | Two stores | The prelude is fixed for the run. Constructed code runs only through `evaluate`, which the checker admits call by call; `install` governed by κ is specified | Partial | Proposed | TestInversion.test_authority_stays_outside_the_code |
| R8 | No undefined behaviour | Every operation is defined or refused. An undecided condition is refused, never guessed. A refusal is a request (VI.5). A run that nests deeper than the depth bound is refused, alike in both backends (III.5) | Built | Proposed | TestPrograms.test_refusals_are_defined; TestC23Backend.test_defined_behaviour_agrees, test_refusals_exit_70, test_the_depth_bound_agrees_in_c; TestSealAndWitness.test_an_answer_passes_outward_only_where_a_sealed_answer_ends_the_path |

### II.5 Two tiers

Every dissipative operation a program performs is realized through conservative computation and an explicit loss boundary. The information needed to restore what was lost is retained through `keep`, which only the system sends.

| System-facing | User-facing |
|---|---|
| Reversible gate realization | Ordinary logical operations |
| Conservative transformations | Transformations that may dissipate |
| Certified inverse relationships | Explicit loss through `discard`, `=>` and `set` |
| Authorized retention of what was let go | The result, and what the program is seen to do |

- **The system's own code is conservative.** The prelude holds no `=>` clause: every rule and every answer rule in it is certified. Loss enters only in a program.
- **There is one set of gates.** `ccnot` and what the prelude builds from it are reversible. An ordinary gate, which gives one bit for two, is not a second kind of primitive: it is a reversible gate followed by `discard`.
- **The coupling runs one way.** A dissipative rule may rest on certified rules. A certified rule cannot rest on a dissipative one: it would be lossy, and its `<->` would be refused (R2).
- **`keep` is not a program's operation.** It stays in `System`, sealed to Root (VII.3). The system retains what restoration needs and nothing else: what a function overwrites is recomputable and is not kept (V.3).
- **A program is not written at the gate level.** It writes `a and b`; where it also lets go of `a` and `b`, that is its `discard`.

```selvage
rule and_into takes (Bit, Bit) returns (Bit, Bit, Bit)
    (a, b) <-> (a, b, c) where
        c is Bit(0)
        (a, b, c) is ccnot((a, b, c))

rule and_gate takes (Bit, Bit) returns Bit
    (a, b) => c where
        (a, b, c) is and_into((a, b))
        discard a
        discard b
```

`and_into` keeps its inputs beside the result and is certified. `and_gate` is the ordinary gate: its two discards are its loss, each a `keep` to Root, whose own rule is certified and realized by `exchange`. `selvage lineage` shows both chains ending in `ccnot` (VII.6).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| No lossy clause in the prelude; no irreversible gate primitive | Built | Ratified | TestTwoTiers.test_the_prelude_has_no_lossy_clause |
| Ordinary gates as a reversible gate and a `discard`, resting on `ccnot` and on Root's `keep` | Built | Ratified | TestTwoTiers.test_a_dissipative_gate_is_a_reversible_gate_and_a_discard; `examples/gates.selv`; TestC23Backend.test_examples_agree |
| Certified code cannot rest on a dissipative rule | Built | Ratified | TestTwoTiers.test_certified_code_cannot_rest_on_a_dissipative_gate; TestChecker.test_the_arrow_states_the_certificate |

---

## III. Types and Values

### III.1 Types

| Type | Values | Notes |
|---|---|---|
| `I8` … `I64`, `U8` … `U64` | Fixed-width integers | Operations over the modular domain ℤ/2ⁿ; signed types read the same bits in two's complement. Division truncates toward zero |
| `Bit` | 0, 1 | The 1-bit unsigned word, ℤ/2: `add` is XOR, `*` is AND |
| `Bool` | `true`, `false` | A sub-shape of `Trit`: a `Bool` is accepted where a `Trit` is declared. A `Trit` is accepted where a `Bool` is declared nowhere: not as an input, a parameter, a result, a field, a request's argument, an answer's reply or state, the value `set` gives, or the other side of a `swap`. It becomes a `Bool` only by `decide` (VI.4) |
| `Trit` | `true`, `false`, `maybe` | Kleene's strong logic (VI.4). Realized as two bits *(known, value)*: `false` 10, `true` 11, `maybe` 00. The pair 01 is not a `Trit` |
| `F64` | IEEE 754 binary64 | IEEE 754 operations, rounding to nearest, ties to even |
| `Text` | Text | Output; joining with `+`. A text holds no NUL byte: a literal with one is refused (IV) |
| `(T, U, …)` | Tuples | `()` is unit |
| Records and variants | `type Point(x: I64, y: I64)`; a block of constructors | A record is a variant with one constructor. Types are nominal: two types with the same fields are different types |
| `Array(T)` | Owned, bounds-checked arrays | `array(T, n)` is filled with zeros |
| Answer names | Answer instances | `Ledger from 100`. The state is of the type the answer takes, and the parameters of the types it declares |
| `Code` | Code as data | Expressions, steps and clauses (VIII.1) |
| `Declaration`, `Program` | Declarations and the program as data | A rule, an answer, a type or a request group; the declarations of a program in order. With them `TypeExpr`, `Param`, `Slot`, `Ctor`, `Op` (VIII.1) |
| `Parts` | A list of parts | `NoParts`, `Part(first, rest)`: the parameters of a rule, the members of a tuple, the declarations of a program |
| `Journal`, `Entry` | The journal | `Empty`, `Kept(entry, rest)`; entries `Dropped(code, by, value)`, `Chose(code, by, among)`, `Decided(code, by, asked, world)` (prelude) |
| `Any` | Any value | Unchecked. Confined to the prelude's journal entries, which hold values of every type, and to `Code`. A program's own declarations may not use it, and there are no type parameters yet |

An integer literal adopts the type of the value it meets, and defaults to `I64` when bound to a name. `U8(x)`, `F64(x)` and the other type names convert between types (III.5). `Trit(b)` gives a `Bool` as a `Trit`, unchanged; no conversion goes the other way.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| `Any` confined to the prelude and `Code` | Built | Ratified | TestChecker.test_any_is_confined_to_the_prelude; TestGenerated04.test_any_is_refused_in_every_declaration_position |
| An instance's state and parameters typed | Built | Proposed | TestSealAndWitness.test_an_instance_holds_a_state_of_the_type_its_answer_takes |

### III.2 Ownership and arrays

- **Owned values.** Every value has one owner. `b is a` makes a copy; no two names refer to one mutable value, so there are no aliases.
- **Moves and borrows.** A clause rule's input is moved in and its parameters are borrowed. This is the borrow/move distinction of Rust, obtained from linearity, with no separate borrow checker.
- **Arrays.** An array is a length and a contiguous run of elements, checked on every index. An array handed to a consuming rule is copied, never aliased. Writing any element counts as writing the array.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Ownership and value semantics | Built | Proposed | TestPrograms.test_interpreter_outputs (arrays); TestC23Backend.test_examples_agree |
| Array layout, lifetime and scope-end freeing in C23 | Partial | Proposed | — |

### III.3 Identity and equality

- **Equality** of two forms is structural: same tag, same children, compared on their canonical form.
- **Identity** is a name for a form: `identity(x)` = H(CanonicalEncode(x)), the first 64 bits of SHA-256 over the canonical encoding.
- **Identity does not establish equality.** Two forms with equal identities are presumed equal only where nothing rests on it, as an index. Where it matters (binding a rewind to its run, naming the code that kept a journal entry, certificates, replay, admission), equality is checked on the canonical form.

**Four responsibilities, kept apart.**

| | Is for | What it does | What it never does |
|---|---|---|---|
| A name | Readers | Says how a thing is written, called and reported: diagnostics, printed code, and `by`, the provenance of a journal entry (VII.3) | Decide which code runs or what an entry refers to |
| An identity | Execution | Says which rule a call reaches, which request a message carries, which answer an instance is of, which code kept an entry | Prove two things equal; grant permission |
| A canonical form | Structural equality | Is what an identity names; where two identities are compared, the forms are | Depend on a name a reader chose |
| Authority | What execution may do | Seals, rows and installed answers decide what may be sent, answered, made or opened (R5, R6, VI.2) | Follow from an identity |

Identity resolution is never authority resolution. A program that holds or can compute the identity of a request or an answer gains no permission to send it, answer it, intercept it or replace it. A request's identity does not let anything answer it; an answer's identity does not widen the groups it is declared for; a seal constrains regardless of either.

**The canonical form of code.** Code is identified by what it is and what it refers to, not by the names it is given. Before code is encoded:

| In the code | Becomes | So that |
|---|---|---|
| A variable | The number of its binding, counted in the order bindings occur; a parameter, its place | Renaming a variable everywhere it is bound and used changes nothing. This is alpha-equivalence |
| A call | The identity of the rule called | Renaming a rule changes no caller; changing a rule changes every caller |
| A request, in a message, in `ask`, or in the clause that answers it | The identity of the request | Renaming a request or its group changes nothing that uses it |
| An answer, in `A from s`, in `with`, or in a type | The identity of the answer | Renaming an answer changes nothing that makes, installs or holds one |
| A group, in a `uses` row | The identity of the group | Renaming a group changes no rule that lists it |
| A type or a constructor | Its name | Values carry these names |
| A name nothing binds | Itself | Two different free names stay different |
| Quoted code | Itself, untouched | A quoted name is data, whatever it would refer to if run |

```selvage
rule tally takes (I64, I64) returns (I64, I64)
    (count, step) <-> (count, step) where
        t is step
        add t to count
        t was step

rule sum takes (I64, I64) returns (I64, I64)
    (a, b) <-> (a, b) where
        kept is b
        add kept to a
        kept was b

rule cross takes (I64, I64) returns (I64, I64)
    (a, b) <-> (a, b) where
        kept is a
        add kept to b
        kept was a
```

`tally` and `sum` are one rule under two names, with one identity: a caller of either is a caller of the other, and a journal entry kept by one names the code of both. `cross` has the names of `sum` and another identity, because its temporary is bound to the other variable.

- **Only naming is normalized.** What is preserved, and so changes the identity when it changes: which binding a use refers to; the order in which names are bound; the shape of every pattern, including a name used in two places; where each binding is made and where it is given back; and every free name.
- **Nothing hides anything.** A name is bound once where it can be seen (IV), so no binding shadows another and none can be captured. Each use has exactly one binding to be numbered by.
- **A rule's identity** is the identity of its code: its parameters, its types, its row, and its clauses or body in canonical form. Its own name is no part of it, nor is where it is declared. Clauses whose left sides are exclusive are a set, and their order is no part of it either; where the first match decides, the order is what the rule does, and is part of it.
- **Rules that call one another in a cycle** are identified as a whole, since none can be resolved before the others. The members are told apart by refinement, which reads nothing but code:
    1. Every member starts in one class.
    2. Each member is written in canonical form, with a call to a member of the cycle written as that member's class.
    3. The distinct forms are sorted by their canonical encoding, and each member's class becomes the place of its form in that order.
    4. Steps 2 and 3 are repeated until a round separates no more members. A class only ever splits, so the refinement ends.
- **The canonical form of a cycle** is its distinct members in the final order, each calling the others by their class; a member's identity is that of the cycle together with its class. No tie is left to break: members that end in one class are indistinguishable, and have one identity. Names and the order of declaration enter nowhere, so any program with the same code gives the same identities, under any implementation of these four steps and the same canonical encoding.
- **Members nothing separates have one identity,** and only those. Two members whose code is alike but who call different members are different rules. Members that share an identity are interchangeable: calling one for the other changes no result, no refusal and no journal entry beyond the name a reader sees in `by`. A ring of such members has the identity of the one rule that calls itself, and a ring whose members repeat with a shorter period has the identity of the ring of that period. That is a statement about identity and rewrites nothing: the ring runs as a ring, and how deep a run nests, in what order, and where its entries stand in the journal are those of the calls it makes.
- **Requests and answers are declarations, not interchangeable code.** Two requests with the same signature are two requests, and two answers with the same clauses are two answers, as two types with the same fields are two types.
    - A group is identified by the signatures of its requests, in their order. Groups with the same signatures are told apart by which is declared first.
    - A request is identified by its group and its place in it. In another order the requests of a group are another group, of other requests.
    - An answer is identified by its code — its state, its groups and its clauses in canonical form. Answers with the same code are told apart by which is declared first.
    - The order of declaration only breaks ties. A group with a signature of its own, or an answer with code of its own, is the same wherever it is declared.
    - They are resolved in turn: groups and requests, then answers, then rules. In a request's signature an answer type is a kind of type, not a reference to one answer, so no request's identity depends on an answer's.
    - None of these depends on a name. The prelude is declared before any program, so no program changes the identities of what the prelude declares.
- **An identity is checked against its form.** A run holds the canonical form behind every identity it uses, of rules, requests, answers and the code that keeps entries, and refuses if two different declarations or pieces of code share one. A hash finds; it does not prove equal.
- **`identity(v)` is of the value as given.** Applied to quoted code it is the identity of that form as written, names included, since a quoted name is data. The identity under which code runs and keeps entries is computed by the toolchain from the checked program; no built-in yields it, and none is to be added without a semantics of its own (XII.1).
- **Two comparisons on `F64`.**
    - The `=` operator is IEEE 754, field by field in aggregates: NaN is not equal to itself, and `0.0 = -0.0`.
    - **Sameness** is equality of canonical forms: every NaN is the one NaN, and `-0.0` differs from `0.0`. It is what `was`, patterns and take-backs compare, so a value a rule produced is always accepted back, and a value it could not have produced is refused.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Structural equality; identity as hash of canonical encoding | Built | Ratified | TestSurface.test_layout_is_not_part_of_identity; TestInversion.test_inverse_prints_parses_and_hashes_like_any_code |
| Sameness for `was`, patterns and take-backs; `=` stays IEEE | Built | Proposed | TestSoundness.test_sameness_is_equality_on_the_canonical_form; TestC23Backend.test_sameness_agrees_in_c |
| Rewind binding checked on the canonical form rather than its hash | Built | Ratified | TestSemanticContracts.test_a_rewind_is_bound_by_the_canonical_form_and_not_by_a_hash |
| Variables identified by their binding: consistent renaming preserves identity; a change of binding structure changes it | Built | Ratified | TestCodeIdentity.test_variables_are_identified_by_their_binding_and_not_their_name; TestGenerated04.test_code_is_identified_by_what_it_is_and_not_by_its_names |
| Calls resolved to the identity of the rule called | Built | Ratified | TestJournalIdentity.test_a_call_holds_the_identity_of_the_rule_called_and_not_its_name; TestGenerated04.test_an_entry_names_its_code_under_renaming_and_reordering |
| Requests in messages and in `ask`, and answers through `from`, resolved to identities; quoted names stay data; names kept for diagnostics and `by` | Built | Ratified | TestCodeIdentity.test_requests_and_answers_are_referred_to_by_identity; the names generator (XI.2) |
| An identity grants no authority: seals and declared groups decide as before | Built | Ratified | TestCodeIdentity.test_an_identity_grants_no_authority; TestGenerated04.test_every_route_to_what_is_sealed_is_refused |
| Exclusive clauses a set; first-match clauses a sequence | Built | Ratified | TestCodeIdentity.test_exclusive_clauses_are_a_set_and_first_match_clauses_a_sequence |
| Cycles identified as a whole by refinement; members by their code and by which members they call; stable under renaming, reordering and rotation | Built | Ratified | TestCodeIdentity.test_a_cycle_is_identified_as_a_whole_and_its_members_by_what_they_refer_to; TestJournalIdentity.test_rules_that_call_themselves_or_each_other_have_stable_identities |
| Members that share an identity are interchangeable | Built | Ratified | TestCodeIdentity.test_rules_that_share_an_identity_are_interchangeable |
| The order of declaration as a tie-breaker only, among groups with the same signatures and answers with the same code | Built | Ratified | TestCodeIdentity.test_declaration_order_only_breaks_ties, test_requests_and_answers_are_referred_to_by_identity; the names generator ("twins kept apart") |
| Quoted code identified as written: no call resolved in it, no name numbered | Built | Ratified | TestCodeIdentity.test_quoted_code_is_identified_as_written; the names generator |
| A ring of members nothing separates sharing the identity of the rule that calls itself, and still running as a ring | Built | Ratified | TestCodeIdentity.test_a_ring_shares_an_identity_and_stays_a_ring |
| An identity checked against the canonical form it names | Built | Ratified | TestJournalIdentity.test_identities_are_compared_as_the_forms_they_name; the journal generator (XI.2) |
| Replay matched on question and context rather than on the key alone | Built | Ratified | TestSemanticContracts.test_replay_matches_the_question_and_its_context_and_not_the_key |

### III.4 Floating point

An `F64` update rounds, so the checker treats it as an exchange plus a discard: the old bit pattern is retained, and the new one is computed by IEEE rules. Retaining the whole 64-bit word is a storage convention. It is not a claim about the exact information a given operation loses, which depends on the operation and its domain.

### III.5 Defined behaviour (R8)

| Case | Result |
|---|---|
| Integer overflow | Wraps (C23 `ckd_add`, `ckd_sub`, `ckd_mul`) |
| `MIN / -1` | `MIN`; `MIN mod -1` is 0 |
| Integer division or `mod` by zero | Refused (fault; status 70 in compiled code) |
| Index out of range | Refused, with the valid range |
| Shift by n | n is masked to the width |
| Narrowing conversion | Wraps (`U8(300)` is 44) |
| F64 to integer | Saturates; NaN gives 0 |
| F64 division by zero | IEEE infinity or NaN |
| Aliased element update | Refused at check time when provable, otherwise at run time |
| Undecided condition | Refused at check time (`if maybe`); at run time, `decide` that nobody settles is refused |
| A run nested deeper than the depth bound | Refused, at the same bound and with the same reason in both backends |

A refusal at run time is the request `refuse` (VI.5). Unless an installed answer takes it, the run ends with status 70.

**The depth bound.** The depth of a run is the number of rule invocations in progress: a call of a rule, or the rule an answer runs for a message or a request. A self tail call is a loop (V.3) and adds nothing.
- The bound is 10,000 by default. The interpreter takes another with `--depth N` or `SELVAGE_DEPTH`; compiled code takes it when it is built.
- A run that would go deeper is refused: `the run nests deeper than N rule calls`, status 70.
- The bound belongs to the run, not to the machine. Compiled code runs on a stack reserved for the bound, and the build refuses a rule whose stack frame is larger than that stack allows for one call, so the bound is reached before the stack ends.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Defined behaviour | Built | Proposed | TestC23Backend.test_defined_behaviour_agrees, test_trits_and_decisions_agree |
| A run nested too deep, refused alike in both backends | Built | Ratified | TestC23Backend.test_the_depth_bound_agrees_in_c, test_the_default_depth_bound_is_reached_in_both_backends; TestPrograms.test_the_interpreter_reaches_the_default_depth_bound_in_every_shape; the depth generator (XI.2) |
| What the bound counts, and its default | Built | Ratified | The same tests; TestC23Backend.test_the_depth_argument_is_the_backend_s_own |

---

## IV. Grammar

**Lexical rules:**
- Indentation opens and closes blocks; tabs in indentation are refused.
- A loop counts: `repeat with i from a to b`, or `from b down to a`. To repeat n times, count from 1 to n.
- `#` starts a comment.
- Line breaks inside `( )` and `[ ]` are ignored.
- Literals: integers (`42`, `0xFF`, `1_000_000`), floats (`2.5`, `1e-7`), text (`"…"`), `true`, `false`, `maybe`. A text that holds a NUL byte is refused: it is invisible in the source, and compiled code holds a text as a C string, which a NUL would end.
- `=` tests equality and `not=` inequality. Names are bound with `is`, released with `was`, and changed only with update words.

**Keywords (38):** `add and answer ask commit decide discard discarded down false for from if is maybe mod not or otherwise output quote repeat request returns rule set subtract swap takes to true type undo uses was where while with`

**The four arrows:**

| Arrow | Mechanism | Meaning | Implementation | Design |
|---|---|---|---|---|
| `<->` | Rule | A clause of a rule the checker certifies (bijection or partial bijection) | Built | Ratified |
| `=>` | Rule | A clause of a lossy rule: the declaration of loss | Built | Ratified |
| `->` | Request | A message to a named answer instance | Built | Proposed |
| `<-` | Form | Field-only derivation of one record type from another. On an answer it is refused | Built | Ratified |

**Grammar:**

```
program     = { declaration }
declaration = type | rule | request | answer
type        = "type" Name [ fields ] [ "<-" Name ] NEWLINE [ INDENT { Name [ fields ] NEWLINE } DEDENT ]
rule        = "rule" [ "undo" ] Name [ params ] [ "takes" type ] [ "returns" type ] [ "uses" Name { "," Name } ]
              NEWLINE INDENT ( clause { clause } | statement { statement } ) DEDENT
clause      = pattern ( "<->" | "=>" ) pattern [ "where" NEWLINE block ] NEWLINE
request     = "request" Name [ "for" Name ] NEWLINE INDENT { Name [ params ] [ "returns" type ] NEWLINE } DEDENT
answer      = "answer" [ "undo" ] Name [ params ] "for" Name { "," Name } [ "takes" type ]
              NEWLINE [ INDENT clause { clause } DEDENT ]
statement   = pattern "is" expr | pattern "was" expr | Name "was" "discarded"
            | "add" expr "to" target | "subtract" expr "from" target
            | "set" target "to" expr | "swap" target "and" target | "discard" Name | "output" expr | "commit"
            | "if" expr NEWLINE block { "otherwise" "if" expr NEWLINE block } [ "otherwise" NEWLINE block ]
            | "repeat" "with" Name "from" expr [ "down" ] "to" expr NEWLINE block
            | "repeat" "while" expr NEWLINE block | expr
expr        = or_expr [ "from" or_expr ] [ "with" expr ]
or_expr     = and_expr { "or" and_expr }        and_expr = not_expr { "and" not_expr }
not_expr    = "not" not_expr | cmp              cmp = sum [ ( "=" | "not=" | "<" | ">" | "<=" | ">=" ) sum ]
sum         = term { ( "+" | "-" ) term }       term = unary { ( "*" | "/" | "mod" ) unary }
unary       = "-" unary | postfix
postfix     = primary { "(" args ")" | "." Name | "[" expr "]" | "->" Name [ "(" args ")" ] }
primary     = literal | Name | "(" [ expr { "," expr } ] ")" | "ask" Name [ "(" args ")" ]
            | "undo" postfix | "quote" or_expr | "decide" or_expr
pattern     = Name | literal | "(" pattern { "," pattern } ")" | Constructor "(" pattern { "," pattern } ")"
```

- An answer may answer several groups. It delegates each request it has no clause for to the component of its state that answers it (VI.3).
- `request G for A` seals the group `G` to the answer `A` (R5, VII.3). It adds no keyword: `for` reads both ways, an answer for a group and a group for an answer.
- `rule undo f` and `answer undo A` are how `invert` prints a derived inverse. The parser reads them, so an inverse round-trips through text, but a program does not declare them: an inverse is derived, never written.
- **A name is bound once where it can be seen.** `p is e` binds names that are not bound. Binding one that is — a parameter, an earlier binding still held, the counter of an enclosing loop — is refused: `set` overwrites, and another value takes another name. A name is free again once it has been given back or consumed, and at the end of the block that bound it. So one temporary may follow another under the same name, and each branch and each loop may use the same names. No binding hides another, and every use of a name has one binding (III.3).
- **The canonical printer** fixes all layout, so layout is never part of a program. Deriving the printer as the parser run backward is specified.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Grammar, with `=>` clauses, answers for several groups, clause-free answers and sealed groups | Built | Proposed | TestSurface.test_round_trip_examples; TestSoundness.test_the_description_s_code_blocks_check |
| `parse(print(f)) = f`, printing idempotent | Built | Proposed | TestSurface.test_round_trip_examples |
| A name bound once where it can be seen, in clause rules, expression rules and loop counters. The checker refuses the rest, so the run and the build end with the same refusal | Built | Ratified | TestCodeIdentity.test_no_name_is_bound_where_it_is_already_bound; TestC23Backend.test_a_name_bound_twice_is_refused_alike; the names generator (XI.2) |

---

## V. Transformation Semantics

### V.1 Clause rules

A clause rule consumes an input:
- Parameters are read and never consumed. The input is owned and moved.
- Calls: `leapfrog(3)((100, 0))`. A rule without parameters is called on its input directly.
- Inverses: `undo leapfrog(3)(s)` runs the derived inverse; `undo` of a lossy rule is refused.
- `p is e` binds; `p was e` is its backward reading and releases `p`.
- A clause rule contains no commit point. `output` and `commit` end what can be rewound, so they stand in expression rules, between rule calls; whatever a rule does can be rewound.

```selvage
rule leapfrog(k: I64) takes (I64, I64) returns (I64, I64)
    (q, p) <-> (q, p) where
        add k * q / 2 to p
        subtract p from q
        add k * q / 2 to p
```

### V.2 Classes and arrows

| Class | Condition | Arrow | `undo` | Journal |
|---|---|---|---|---|
| bijection | Left exclusive and exhaustive, right exclusive, every step certified | `<->` | Allowed | Nothing kept |
| partial bijection | Both sides exclusive, every step certified | `<->` | Allowed; refused outside the image | Nothing kept |
| lossy | Anything else | `=>` | Refused | Every loss kept by Root |

The two certified classes are read off the clauses: `bijection` says the left sides take every shape of the input type, `partial bijection` that they do not. Both certify the same thing, that the rule is one-to-one, with an inverse defined exactly on its image (XI.3).

**How far a certified rule reaches.** Whether a rule takes every input, and whether it gives every output, are two further questions. The checker settles each on its own and reports only what it has established:

| Extent | Defined on every input | Onto its output type | |
|---|---|---|---|
| permutation | Yes | Yes | `ccnot`; `orbit` |
| embedding | Yes | No | `and_into` (II.5): 4 inputs, 4 of 8 outputs |
| partial inverse | No | Yes | The inverse of an embedding: defined on the image, not on the whole type |
| partial | No | No | |
| one-to-one | One or both not established | | A rule over arrays, where an index may be refused |

| Established | How |
|---|---|
| By running it | The input type has at most 4,096 values, and the rule is run on every one |
| By its steps | No step of the rule can refuse, so it takes every input, apart from the depth bound: a run already at its bound refuses any call, and the theorem this rests on excludes such runs (XI.3). No step of its inverse can refuse, so its inverse is defined everywhere and its image is everything (XI.3, Part 3). The test is cautious: a division by anything but a literal other than zero, an index, a `was` that is not proved, a pattern a value might not match, and a call into a cycle all count as able to refuse |
| By counting | A one-to-one rule from fewer values into more does not give them all; one from more into fewer does not take them all. A value that matches no left side is not taken, and one that matches no right side is not given |

The test by steps is a sufficient one. A step outside it is not thereby able to refuse; the rule is then reported as not established, never as refusing. A call into a cycle of rules counts as able to refuse.

`selvage check` prints the extent of each certified rule in place of its class, with how it was established. An answer is listed with its class, and under it the extent of its rule for each request: that rule takes the request's fields with the state and gives the reply with the state, and its extent is settled the same three ways. An embedding is never reported as a permutation, and a rule whose reach is not established is reported as one-to-one and nothing more.

The checker names each loss, for example:
- *it discards items*;
- *an update on F64 rounds*;
- *right sides of clauses 1 and 2 overlap, so the clause choice is lost*;
- *it decides, and a decision about maybe is world input*.

The arrow states the certificate. A rule whose checker class is lossy must write `=>`, and a certified rule must write `<->`. The certificate belongs to the rule, so every clause of a rule carries the same arrow. Classification propagates through calls and messages, so changing a rule's class changes the arrow its callers need, as a type change would.

```selvage
rule damped_orbit(k: I64, steps: I64) takes Phase returns Phase
    Phase(q, p) => Phase(q, p) where
        repeat with i from 1 to steps
            add k * q / 2000 to p
            subtract p from q
            add k * q / 2000 to p
            set p to p - p / 64
```

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| The three classes | Built | Proposed | TestChecker.test_classification |
| The extent of a certified rule reported apart from its class: permutation, embedding, partial inverse, partial; nothing claimed that is not established | Built | Ratified | TestExtent.test_a_gate_is_a_permutation_and_an_ancilla_makes_an_embedding, test_a_rule_over_words_is_settled_by_its_steps_or_by_counting, test_nothing_is_claimed_that_is_not_established; TestGenerated04.test_how_far_a_certified_rule_reaches |
| The extent of an answer's rule for each request, listed under the answer | Built | Proposed | TestExtent.test_an_answer_s_rules_report_their_extent; TestGenerated04.test_how_far_a_certified_rule_reaches (every generated rule hosted by an answer as well) |
| The arrow matches the class, and a mismatch either way is refused | Built | Ratified | TestChecker.test_the_arrow_states_the_certificate; TestGenerated04.test_arrows_state_the_certificate_and_lossy_runs_rewind |
| R4 under either arrow | Built | Proposed | TestSoundness.test_r4_holds_under_either_arrow |

### V.3 Expression rules: functions and procedures

An expression rule takes only parameters and computes a value. Systems code lives here.
- The last statement is the value.
- A self tail call is a loop, in both backends: it adds nothing to the depth of the run (III.5).
- `repeat while` is available here, and only here.

Its `uses` row says which of two things it is:

| | Function | Procedure |
|---|---|---|
| `uses` row | Empty | Not empty |
| Its result | Recomputable from its parameters (Bennett) | Recomputable from its parameters together with the world replies it kept |
| What it keeps | Nothing. Its internal overwrites are not losses | Every reply it receives from the world, such as a decision the world settles. Its overwrites are still not kept |
| ε | Nothing to count | Counts the kept replies at the next commit point |

**Reaching `keep`.** A procedure reaches `keep` when it calls a lossy rule, messages or installs an answer with a lossy request rule, or can receive a reply from the world. It then lists `System` in its row. This is R6 applied uniformly: a clause rule shows the same thing by its `=>` arrow, and an expression rule, having no arrow, shows it in its row. `route` in VI.4 is a procedure with the row `uses Decide, System`.

**A reply from the world.** The test is the type of what is decided, not the word `decide`. A condition of type `Trit` may be `maybe`, and `maybe` may reach the world, so deciding it needs `Decide` and `System`. A condition of type `Bool` never leaves the program: `decide n > 2` needs neither, and a rule that only decides crisp conditions is a function.

**What is kept.** When the world settles a decision, the procedure keeps `Decided(code, by, asked, world)`, naming its own code. When an installed answer settles it, the procedure keeps nothing: the reply did not come from the world, and the answer's own rule accounts for whatever that rule loses.

**Steps call functions.** Inside a clause's step, an expression may call a function and may not call a procedure, since the step must be recomputable to be read backward.

**Commit points.** An empty row cannot conceal a world interaction or a retained effect. `output` is a request of `Output`. `commit` dissipates what Root retains, so it is accounted to the group that owns retention: a rule that commits lists `System`, and is a procedure. No group exists for `commit` alone.

**Between runs.** A reply a procedure kept stands between the runs around it: a run that ended before it can no longer be rewound (VII.1).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Functions and procedures told apart by the row | Built | Ratified | TestChecker.test_functions_and_procedures_are_told_apart_by_the_row; TestGenerated04.test_rows_tell_functions_from_procedures_and_show_reaching_keep |
| A procedure keeps and accounts for world replies, in both backends | Built | Ratified | TestGenerated04.test_rows_tell_functions_from_procedures_and_show_reaching_keep; TestC23Backend.test_procedures_keep_world_replies_in_c |
| A procedure that reaches `keep` lists `System` | Built | Ratified | The same tests; a row without it is refused in every generated case |
| A kept reply stands between the runs around it | Built | Ratified | TestGenerated04.test_a_kept_reply_stands_between_runs |
| A commit point in the row | Built | Ratified | TestSealAndWitness.test_a_commit_point_is_in_the_row; the rows generator (XI.2) |
| A self tail call is a loop, in both backends | Built | Ratified | TestC23Backend.test_the_default_depth_bound_is_reached_in_both_backends (a tail call 200,000 deep); the depth generator (XI.2) |

### V.4 Four uses of a value

| Use | Written | Contract | Realized by |
|---|---|---|---|
| Borrow | Any expression that reads `x` | `x` is neither consumed nor changed; parameters are only borrowed | Wires; no gate |
| Copy into an empty name | `y is x` … `y was x` | `y` does not exist before, so its cells are empty: (x, ∅) ↔ (x, x). `y was x` checks y = x and empties `y` | `fanout` |
| Compute and uncompute a temporary | `t is e` … `t was e` | Bennett: `t` is computed into empty cells, used, and uncomputed after its last use; the checker proves that nothing `e` reads has changed, and writes the `was` | Gates for each operation of `e`; `fanout`; Bennett's construction in general |
| Keep in the journal | `discard x` | `x` moves into a `Dropped` entry; only the system takes it back | `Root.keep` |

### V.5 Elaboration

After checking, the checker writes into the rule what it proved, so nothing about inversion stays implicit:
- each temporary's uncompute, as a `was` step after its last use;
- `set t to e`, as `old_t is e`, `swap t and old_t`, `discard old_t`;
- a rounding update, the same way.

The elaborated code checks again with nothing left to add.

**Proved uncomputes.** An uncompute `p was e` is proved when it follows, in the same block, the `is` that bound `p`, with the same pattern and the same expression, and no step between them changes a name of `p` or a name `e` reads. A proved uncompute costs nothing at run time. Any other is checked when it runs, and refused if it does not hold (XI.3, O5).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Elaboration, checked as a fixpoint | Built | Proposed | TestInversion.test_elaborated_code_leaves_nothing_implicit |
| An uncompute proved only in the pattern that bound it | Built | Proposed | TestSoundness.test_an_uncompute_is_proved_only_in_the_pattern_that_bound_it; the structures and model generators (XI.2) |

### V.6 Inversion

`invert` maps a rule's code to its inverse's code. It reverses each block and replaces each step by its backward reading. It never runs anything and needs no model.

Inversion is defined in the language. The table below is the prelude's rule `mirror`, a certified rule on code (VIII.2); `invert` runs that rule and holds no table of its own.

| Step | Its backward reading | What the checker requires, so the backward reading can be reconstructed |
|---|---|---|
| `p is e` | `p was e` | — |
| `p is g(k)(x)` | `p was g(k)(x)` | The parameter `k` does not read `x`, which the call consumes (R4) |
| `add e to t` | `subtract e from t` | `e` does not read `t`, and no index of `t` reads what the step changes (R4) |
| `swap a and b` | `swap a and b` | No index of `a` or `b` reads what the swap changes (R4) |
| `discard x` | `x was discarded` | — |
| `if c` A `otherwise` B | `if c` A′ `otherwise` B′ | Neither branch changes anything `c` reads, so `c` chooses the same branch backward |
| `repeat with i from a to b` A | `repeat with i from b down to a` A′ | The body does not change anything `a` or `b` reads |
| `repeat while c` A | None | Refused in clause rules: without an exit assertion, the iteration count cannot be reconstructed |
| `L <-> R where S` | `R <-> L where S′` | — |
| `L => R where S` | `R => L where S′` | Where the output matches the right side of more than one clause, the clause choice is kept, and the inverse takes it back to choose. Where it matches one, that clause ran, and nothing is kept |
| `rule f … takes T returns U` | `rule undo f … takes U returns T` | — |

`invert` keeps the arrow. It never turns a declaration of loss into a claim of reversibility.

**What a condition reads** is exactly its free names, and the checker can know it:
- values are owned and never shared, so there are no aliases;
- a condition may not contain a request, a decision or a consuming call, which are bound on their own line first;
- an expression rule called in a condition is a function of its arguments;
- writing any element of an array counts as writing the array.

**`was` is uniform:** it consumes what `is` bound and gives back what `is` consumed.

| `p was …` | Read forward |
|---|---|
| `p was e` (pure) | Check that `p` is the same as `e` (sameness, III.3), skipped when the checker proved it, then release `p` |
| `p was g(x)` | `p` goes back through `g`'s derived inverse, and `x` returns |
| `r was t -> op(…)` | The message is taken back: the derived inverse of the rule that answered `op` runs |
| `r was ask op(…)` | The same, on the nearest instance that answers `op` |
| `i was A(k) from s` | The instance is unpacked: it must be an `A` with parameters `k`, and its state returns as `s` |
| `d was decide e` | The decision comes back from the journal, and each consulted answer's rule runs backward (VI.4) |
| `x was discarded` | `x` comes back from the journal, under the system's authority only |

`selvage invert` prints the derived inverse:

```selvage
rule undo leapfrog(k: I64) takes (I64, I64) returns (I64, I64)
    (q, p) <-> (q, p) where
        subtract k * q / 2 from p
        add p to q
        subtract k * q / 2 from p

rule undo damped_orbit(k: I64, steps: I64) takes Phase returns Phase
    Phase(q, p) => Phase(q, p) where
        repeat with i from steps down to 1
            old_p was discarded
            swap p and old_p
            old_p was p - p / 64
            subtract k * q / 2000 from p
            add p to q
            subtract k * q / 2000 from p
```

**The guarantee.** `invert` derives an inverse program for every clause rule. The checker certifies that the inverse is defined on the forward rule's image, and that everything it needs to reconstruct a run is either recomputable or kept. A value outside the image is refused at run time (R8).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| `invert`, an involution on elaborated code | Built | Proposed | TestInversion (XI.2) |
| `invert(L => R) = R => L` | Built | Ratified | TestChecker.test_inversion_preserves_the_arrow; TestGenerated04.test_arrows_state_the_certificate_and_lossy_runs_rewind |
| Control-flow and R4 obligations | Built | Proposed | TestJournalContract.test_control_flow_inverts_only_when_it_can_be_reconstructed; TestSoundness; generated rules (XI.2) |

---

## VI. Interaction Semantics

### VI.1 Requests and answers

```selvage
answer Ledger for Account takes I64
    (deposit(n), balance) <-> (Deposited(n), balance) where
        add n to balance
    (withdraw(n), balance) <-> (Withdrew(n), balance) where
        subtract n from balance

rule pay(n: I64) takes Ledger returns (Receipt, Ledger)
    account <-> (receipt, account) where
        receipt is account -> withdraw(n)
```

- **One rule per request.** An answer's clauses for `deposit` form one rule and those for `withdraw` another, each certified on its own, each with its own arrow.
- **Instances.** `Ledger from 100` makes an instance, an ordinary value.
- **Messages taken back.** `receipt was account -> withdraw(n)` runs the derived inverse of `Ledger`'s `withdraw` rule. Because that rule is certified, `pay` is too, and `undo pay(30)((Withdrew(30), Ledger from 120))` returns `Ledger from 150`.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Answers, instances, per-request certification, messages taken back | Built | Proposed | TestReversibility.test_undo_a_message; TestInversion.test_semantic_round_trips |

### VI.2 Resolution and `with`

- `instance -> op(args)` is resolved statically: the instance's answer is known from its type.
- `ask op(args)` goes to the nearest installed instance that answers `op`, by a rule of its own or by delegation (VI.3), innermost first. An installed instance that does not answer `op` is passed over, and the request continues outward. Passing over is not a refusal.
- `e with A from s` runs `e` with that instance installed. It returns the pair (value, final instance), so nothing is dropped.
- Every run starts inside an `Object`, the user-facing root (VII.2). A request that reaches it and that it does not answer is refused there (VI.5).
- **Rows follow the same path.** An `ask` inside `e with A from s` is out of the enclosing rule's row when `A` answers that request; otherwise its group stays in the row. A rule called inside it keeps its groups in the row unless the installed answers answer every request of the group: a group does not leave a row because one of its requests was answered.
- **An answer has no row.** What its rules ask is carried to the row of whoever messages or installs it, and is taken out only by an answer installed around it.
- **One request is passed outward.** An answer that is answering a request may ask that same request again where a sealed answer gives the final reply; the ask then goes to the next answer out. Today that is `history`: a host's answer for `Witness` asks the next one, in the end Root (VII.2). Anywhere else, an answer that asks the request it is answering is refused by the checker.
- **Requests in general are not restricted.** Whether every request made inside an answer should resolve outward from it is Proposed, and not built: other requests an answer makes resolve as they do anywhere, from the innermost installed answer.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| `->`, `ask` and `with` | Built | Proposed | TestReversibility.test_undo_a_message, test_rewind_through_requests_restores_the_answer; TestMaybe.test_escalation_through_answers |
| An `ask` that an installed answer does not take continues outward, in the run and in the row | Built | Ratified | TestGenerated04.test_delegation_to_the_single_component_that_answers; TestChecker.test_r6_rows_contain_what_a_rule_reaches |
| What an installed or messaged answer asks, in the row | Built | Ratified | TestSealAndWitness.test_installing_a_host_that_asks_outward_is_in_the_row; TestGenerated04.test_inner_code_reads_what_its_hosts_pass_on |
| The request an answer is answering, passed outward where a sealed answer ends the path | Built | Ratified | TestSealAndWitness.test_an_answer_passes_outward_only_where_a_sealed_answer_ends_the_path; the same generated test |
| Every request from inside an answer resolving outward from it | Absent | Proposed | — |

### VI.3 Prototypes by delegation

An answer delegates a request it does not answer itself to a component of its state: an instance, held in that state, of an answer that does answer the request. The parent's rule runs on the parent's own state and keeps its certificate; the child's rules run on the child's state. A child never changes the certificate of a rule it delegates to, and never acts on a parent's state except by sending it messages or by unpacking an instance it owns.

- **Components.** The components of a state are the state itself when it is an instance, the members of a tuple, and the fields of a record. An instance nested deeper is reached through the answer that holds it: delegation chains, one answer at a time.
- **Groups.** An answer delegates only requests of the groups it is declared for. A component may answer more; the answer that holds it does not, unless it declares that group too.
- **Certificates.** A message's class is the class of the rule that finally answers it, so a rule that sends only certified requests to a delegating answer is certified, and its arrow is `<->`.

| Components of the state that answer the request | Result |
|---|---|
| Exactly one | The request is delegated to it |
| None | There is nothing to delegate to: the answer does not answer that request, and a message naming it is refused by the checker |
| Several | Refused by the checker; the answer must take the request itself |

```selvage
answer Count for Counter takes I64
    (bump(n), c) <-> (n, c) where
        add n to c

answer Resettable for Counter takes (Count, I64)
    (reset(), (c, resets)) => ((), (c, resets)) where
        c was Count from k
        set k to 0
        c is Count from k
        add 1 to resets
```

A `Resettable` holds a `Count` and a tally of its own. It answers `reset` itself, lossily, and delegates `bump` to the `Count`, certified. A rule that sends only `bump` to a `Resettable` is certified, and `undo` takes its messages back. In lineage the link is `delegated` (VII.6).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Delegation to the one state component that answers; several refused; none means the request is not answered | Built | Ratified | TestInversion.test_delegation_keeps_each_certificate_where_it_is_answered; TestGenerated04.test_delegation_to_the_single_component_that_answers |
| A message naming a request the answer does not answer is refused by the checker | Built | Ratified | The same generated test |
| `<-` on an answer refused | Built | Ratified | TestChecker.test_derivation_is_for_records_and_delegation_for_answers |
| Packing and unpacking an instance inside a clause | Built | Proposed | TestSoundness.test_unpacking_an_instance_checks_its_image |

### VI.4 MAYBE: a general decision protocol

**Values.** `Trit` has three values. `maybe` means *not yet decided*; it is neither a probability nor noise.

| `a and b` | true | maybe | false |
|---|---|---|---|
| **true** | true | maybe | false |
| **maybe** | maybe | maybe | false |
| **false** | false | false | false |

| `a or b` | true | maybe | false |
|---|---|---|---|
| **true** | true | true | true |
| **maybe** | true | maybe | maybe |
| **false** | true | maybe | false |

`not` swaps `true` and `false` and keeps `maybe`. On two-valued operands these are ordinary Boolean logic. A rule over `Trit` shapes is certified like any other:

```selvage
rule flip takes Trit returns Trit
    true <-> false
    false <-> true
    maybe <-> maybe
```

**Realization.** A `Trit` is two bits *(known, value)*: `false` is 10, `true` is 11, and `maybe` is 00. The pair 01 is not a `Trit` value; compiled code holds a `Trit` as a byte of the same bits, and no boundary of the language today admits a raw pair (VIII.1). The prelude writes Kleene logic as gate circuits. Each keeps its inputs and adds its result into a target pair, so an empty target (0, 0) receives the answer, the same contract as `fanout`:

```selvage
rule trit_and takes (Bit, Bit, Bit, Bit, Bit, Bit) returns (Bit, Bit, Bit, Bit, Bit, Bit)
    (k1, v1, k2, v2, k, v) <-> (k1, v1, k2, v2, k, v) where
        add v1 * v2 to v
        t1 is k1 * k2
        t2 is k1 * (v1 + 1)
        t3 is k2 * (v2 + 1)
        u is t1 + t2 + t1 * t2
        add u + t3 + u * t3 to k
```

Every product is a `ccnot` into an empty cell and every sum a `cnot`; the checker uncomputes the cells. `trit_and`, `trit_or` and `trit_not` are certified bijections, checked against the language's own `and`, `or` and `not` on all 21 cases. The backends compute the same function directly, as a few bit operations.

**The protocol.** The decision layer is separate from the logic:

| Part | Role |
|---|---|
| `maybe` | An undecided proposition (a logic value) |
| `decide e` | A request to resolve `e` |
| `Decide` | The request group: `settle(question, context)` |
| An answer for `Decide` | A decision policy, returning true, false or **defer** |
| The world | The last resolver: a person, a model, a sensor, a consensus, any program |
| The journal | Where a decision entering the computation is kept |

`defer` is the protocol outcome written as `maybe` in a reply: the answer passes the question on. It is not a fourth truth value.

- `if` and `repeat while` need a decided condition. A condition that can be `maybe` is refused at check time: *`if` needs a decided condition, and this one can be maybe; say `decide` to settle it*.
- `decide e` on `true` or `false` passes straight through and never calls out. On `maybe`, `settle` goes to the nearest answer for `Decide`. An answer that defers passes it to the next answer out, so the stack of answers is the escalation chain. The world decides last; if the world also defers, `decide` is refused.
- A rule that decides declares `uses Decide`, so every place a program defers a judgment is visible in its signature. A procedure that decides also lists `System`, since the world's reply is kept (V.3).

```selvage
answer Tally for Decide takes I64
    (settle(question, context), n) => (maybe, n) where
        add 1 to n
        discard question
        discard context
```

**The question is the program's own code.** The request carries the undecided expression as a `Code` form and the values it read as bindings. The world receives this record:

```json
{
  "question": "urgent(severity, outage, note)",
  "context": {"note": "some users report slow logins", "outage": "maybe", "severity": "3"},
  "key": "7e177af2229de30e",
  "identity": "fb53c11332148939",
  "definitions": ["rule urgent(severity: I64, outage: Trit, note: Text) returns Trit\n    by_severity(severity) or outage"]
}
```

A resolver sees the rule that could not decide, printed canonically, with the values it read. Homoiconicity builds the prompt.

| Record field | Identifies |
|---|---|
| `question` | The code: the canonical text of the undecided expression |
| `context` | The bindings it read |
| `key` | Code with context, the replay key (FNV-1a), the same in both backends |
| `identity` | The `settle` request as a form |
| `definitions` | The rules the question calls |

**World deciders** (CLI `--decide`, or `SELVAGE_DECIDE` for both backends):

| Decider | Who answers |
|---|---|
| `refuse` | Nobody; `decide` on `maybe` is refused (the default) |
| `true`, `false` | A fixed policy |
| `ask` | A person at the terminal (interpreter) |
| `command:CMD` | Any program that reads the record as JSON and prints `true`, `false` or `maybe` |
| `replay:FILE` | A record made with `--record` (interpreter) |

**Decisions as world input.**
- **Three cases.** A `decide` whose operand is a `Bool` is statically crisp: no request can occur, and it costs the rule nothing. One whose operand is a `Trit` may leave the program, so the rule is lossy. A decision the world settles is a run-time event, kept by Root whether a clause rule or a procedure asked (V.3).
- **Rewound exactly.** The entry `Decided(code, by, asked, world)` records how many answers were asked and whether the world settled it. The rest of the path is reconstructed without being stored:
    - the question and its bindings are recomputed from the code and the unchanged values it read;
    - the answers asked are the first `asked` answers for `Decide`, innermost first, and a clause rule cannot change which answers are installed;
    - every answer asked deferred except the last, which replied the decision, unless the world settled it.

    Each answer's derived inverse runs on its reply, and taking a message back checks that the request it recovers is the one sent.

- **Recorded and replayed.** `--record` keeps what the world was asked and how it replied; `replay` reruns a run exactly without the resolver. Replay is ordered and consumes its record: the next recorded decision answers the question now asked when its text and its context are the same as recorded, not merely its key; it is then used up, and the one after it is next. Nothing is searched for or used twice. A question the next record does not answer is refused, and so is one asked when the record has ended. Replay establishes that a recorded decision is reproduced, not that it was right.
- **Counted.** ε counts 1 + ⌈log₂(n + 1)⌉ bits for a decision made with n answers installed for `Decide`, however many of them were asked (VII.5). The replay record is the world's, kept outside the journal, and ε does not count it.

**Example.**

```selvage
rule by_severity(severity: I64) returns Trit
    if severity >= 4
        true
    otherwise if severity <= 1
        false
    otherwise
        maybe

rule urgent(severity: I64, outage: Trit, note: Text) returns Trit
    by_severity(severity) or outage

rule route(severity: I64, outage: Trit, note: Text) returns Text uses Decide, System
    if decide urgent(severity, outage, note)
        "page the on-call engineer"
    otherwise
        "queue for the morning"
```

| Ticket | Value | Settled by |
|---|---|---|
| Severity 5 | `true` | Crisp |
| Severity 1 | `false` | Crisp |
| Severity 3 with outage `true` | `maybe or true = true` | Crisp |
| Severity 3, "slow logins" | `maybe` | Decider: `false` |
| Severity 2, "error rate doubled" | `maybe` | Decider: `true` |

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Kleene logic and its gate circuits | Built | Proposed | TestMaybe.test_kleene_tables_and_decisions; TestSemanticContracts.test_kleene_logic_is_a_verified_gate_circuit |
| `decide`, escalation, world deciders, record and replay | Built | Ratified | TestMaybe |
| Replay ordered and consuming, matched on question and context, a mismatch refused | Built | Ratified | TestSemanticContracts.test_replay_matches_the_question_and_its_context_and_not_the_key; the decisions generator (XI.2) |
| Decisions inside clause rules, kept and rewound | Built | Ratified | TestGenerated04.test_decisions_inside_clause_rules_are_kept_and_rewound |
| Statically crisp `decide` certified | Built | Proposed | TestSemanticContracts.test_a_statically_crisp_decide_is_not_world_input |
| Answers for `Decide`, record and replay in C23 | Absent | Proposed | — |

### VI.5 Refusal

A refusal (R8) is a request: `refuse(reason)`, in the group `Refusal`.

1. An operation meets a refusal condition: a division by zero, an index out of range, a value outside a rule's image, an undecided condition nobody settles, a request nobody answers, a rewind out of order. A program raises one itself with `ask refuse("…")`, and then lists `Refusal` in its row.
2. The nearest installed answer for `Refusal` takes the request. The computation inside that answer's `with` is aborted, the answer's `refuse` rule runs with the reason, and execution resumes after the `with`.
3. If no installed answer takes it, Root answers by ending the run, with status 70.

The condition and its disposition are separate. An operation refuses; an answer, in the end Root, decides what becomes of the refusal.

A handled refusal and a terminal refusal stay distinguishable. An installed answer intercepts the request, and the run goes on. Root supplies the terminal fallback: its answer has no clause and ends the run. Status 70 always means a refusal nothing took; status 1 means the checker did not accept the program, and nothing ran.

```selvage
type Log
    Clean
    Noted(reason: Text, earlier: Log)

answer Recorder for Refusal takes Log
    (refuse(reason), log) <-> ((), Noted(reason, log))
```

`risky() with Recorder from Clean` runs `risky()`. If nothing refuses, it yields `((), Recorder from Clean)`. If something does, it yields `((), Recorder from Noted(reason, Clean))`, and the statements after it run.

- **What may run inside.** What runs inside an answer for `Refusal` may stop short, so it must compute `()`: there is then no value the refusal could leave missing. Substituting a result for a refused operation is not defined (XII.5).
- **What was kept.** Entries kept before the refusal stay in the journal. They belong to no finished run, so they stand between earlier runs and their rewinds until the next commit point (VII.1).
- **Other answers.** An installed answer that is not for `Refusal` is passed over, like any request it does not answer.
- **Compiled code.** `with` stays in the interpreter (IX.2), so compiled code has only Root's answer: status 70.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Refusal conditions, each ending the run with status 70 when nothing takes them | Built | Ratified | TestPrograms.test_refusals_are_defined; TestC23Backend.test_refusals_exit_70; TestGenerated04.test_an_untaken_refusal_ends_the_run_with_status_70 |
| Refusal as a request the nearest installed answer takes before Root | Built | Ratified | TestGenerated04.test_a_refusal_goes_to_the_nearest_answer_or_ends_the_run |
| What runs inside an answer for `Refusal` computes `()` | Built | Ratified | The same generated test; the checker refuses any other type |
| Substituting a result for a refused operation | Absent | Open | — |

### VI.6 The CCNOT tape

The prelude holds one stateful source of values: a CCNOT tape. It is wiring 1 of moop's tape, a mechanism of another language, admitted as a record and three certified rules. It is not a new mechanism and not on the execution path.

```selvage
type CcnotTape(a: Array(Bit), b: Array(Bit), i: I64, j: I64)

rule tape_tick takes CcnotTape returns CcnotTape
    CcnotTape(a, b, i, j) <-> CcnotTape(a, b, ni, nj) where
        add a[i] * b[j] to a[(i + 1) mod length(a)]
        add a[i] * b[j] to b[(j + length(b) - 1) mod length(b)]
        ni is (i + 1) mod length(a)
        i was (ni + length(a) - 1) mod length(a)
        nj is (j + length(b) - 1) mod length(b)
        j was (nj + 1) mod length(b)

rule draw takes CcnotTape returns (Bit, CcnotTape)
    s <-> (seen, s) where
        s is tape_tick(s)
        seen is s.a[s.i]

rule birth takes CcnotTape returns (CcnotTape, CcnotTape)
    s <-> (CcnotTape(ca, cb, 0, 0), s) where
        ca is array(Bit, length(s.a))
        cb is array(Bit, length(s.b))
        repeat with k from 0 to length(ca) - 1
            s is tape_tick(s)
            add s.a[s.i] to ca[k]
        repeat with k from 0 to length(cb) - 1
            s is tape_tick(s)
            add s.a[s.i] to cb[k]
```

- **The tape.** Two circular tapes of bits, `a` and `b`, under heads `i` and `j`. One tick (`tape_tick`) fires two CCNOTs that share their controls, the cells under both heads, and target the next cell of each tape; then `i` moves forward and `j` backward. Each update is `add a[i] * b[j] to …`, which is `ccnot` (VII.6), so the tick's bit updates are realized gate for gate.
- **A draw is a deterministic observation** (C1). `draw` ticks the tape and copies the cell then under `i`, giving the bit and the tape. The copy goes into an empty name, so the rule is an embedding: nothing is kept, and `undo` refuses a draw the tape did not give. A draw is not a random bit, and nothing here claims statistical independence: on tapes of 8 and 13 cells a draw agrees with the draw 8 places back 74.8% of the time. A program that needs random numbers does not use `draw`. Another generator, such as a certified rule over words, is a rule of its own, never another implementation of the tape.
- **`draw` is the tape's** (C5). `draw`, `birth` and `tape_tick` are prelude rules, and a prelude name cannot be declared again, so no program can define its own `draw` rule or stand in for the tape's. There is no request group for the tape and so nothing to answer. The reservation is of the prelude rule names, not of the words in every namespace: a request a program declares in a group of its own may be called `draw`, and `m -> draw()` is then that program's message, a different form from the rule call `draw(t)`.
- **A birth** draws one cell for each cell of a child tape, `a`'s cells first, and gives the child, with both heads at 0, together with the parent. It is certified: the parent advances by ticks and the child is copies, so taking a birth back gives the parent back. A birth promises a valid reversible initialization and no more. It is one-to-one and not onto, since a child always starts with its heads at 0, and how many different children a tape can bear is not part of it (on tapes of 8 and 13 cells, 2.80% of possible children).
- **A program makes its tape and passes it** (C3). `CcnotTape(a, b, 0, 0)` makes one from tapes the program fills; each `draw` and `birth` takes the tape and gives it back, so the program holds its tape as it holds any value. No tape is ambient, and `ask draw()` is refused at check time: there is no request to ask. The tapes a program starts from are an explicit initialization, not a source of entropy, and seeding does not make the tape random.
- **Domain.** The tapes the rules are for are the domain D: every `CcnotTape(a, b, i, j)` with `length(a) ≥ 2`, `length(b) ≥ 2`, `0 ≤ i < length(a)` and `0 ≤ j < length(b)`, the cells being any bits. The two lengths need not be equal. D belongs to the model these claims are made in: it is not a type, and nothing checks it statically, so a program can build a tape outside it, which is then refused when it runs (below). On D, for any lengths:

  | Rule | On D | Not onto, because |
  |---|---|---|
  | `tape_tick` | A permutation of D that keeps both lengths | — |
  | `draw` | An embedding of D into `Bit` × D | The bit given is always the cell under head `i` of the tape given |
  | `birth` | An embedding of D into D × D | A child's heads are always 0 |

  *Proof.* Fix the lengths. A tick first applies two CCNOTs whose controls are `a[i]` and `b[j]` and whose targets are `a[(i + 1) mod length(a)]` and `b[(j - 1) mod length(b)]`. With two cells or more on each tape, neither target is its tape's control, and the targets are on different tapes; so the controls are not written, and applying the pair twice is the identity. It then moves the heads by (+1, −1), a bijection of the head positions. A composition of bijections of the finite set D is a permutation of it: total on D, with an inverse that also maps D onto D. A draw gives the tick's result whole, beside a copy of one of its cells, so the draw is one-to-one; and a pair whose bit differs from the cell under `i` is not given. A birth gives the parent after `length(a) + length(b)` ticks, so it is one-to-one; and a child with a head not at 0 is not given. ∎ The proof covers every length. The run of every state of D with 2 or 3 cells on each tape (below) is a finite exhaustive check, evidence for those sizes only.

  Outside D, every input is refused when it runs, in both backends, with status 70; none is wrapped round:

  | Input | Refused by |
  |---|---|
  | A tape of no cells | Division by zero |
  | A tape of one cell | R4: the update reads its own target |
  | A head outside its tape, negative or past the end | The index check: *index n is outside 0 to m* |

  The claims above are about the model. `selvage check` reports less, since no type states D: the tick and the draw as one-to-one with nothing more established, the birth as one-to-one and not onto (V.2). Stating D in types would be a language feature with its own admission case, and the tape does not justify it alone.
- **Both backends.** The three are clause rules, so compiled code runs them, `undo` included (IX.2).
- **Gates.** The reversible profile lays the three out (IX.4). The heads are words, so a circuit is laid out for given heads: a tick is 2 CCNOTs, a draw 2 CCNOTs and a CNOT onto a fresh wire, a birth 2(m + n) CCNOTs and m + n CNOTs for tapes of m and n cells. The tape is the first program the profile was tried on, not its definition.
- **Moop's trace.** The tape is pinned to moop's own implementation: `tests/programs/ccnot_tape.selv` prints `tests/programs/ccnot_tape.trace` byte for byte, in the interpreter and compiled, and moop's C implementation prints the same file. A change of wiring is a new wiring with a new trace, never an edit.
- **Admission** (I.4). *Foundation:* a record (Tier 2) and three clause rules over bit updates (Tier 1). *Synergy:* it gives Selvage generation, a certified birth that is taken back, and it gives the realization lineage rules whose defining step is `ccnot` itself, a first program for the reversible profile (IX.4). It needs no request and so no compiled answers. Of the four steps this is still the weakest: it makes no existing construct unnecessary. *Interference:* four names are reserved; no example, test program or benchmark changes. *Uniformity:* only existing constructs, with the domain guarded by the existing checks. The decisions taken in admitting it are C1 to C5 (XII.6).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| `CcnotTape`, `tape_tick`, `draw` and `birth` in the prelude, certified | Built | Ratified (C4, C5) | TestCcnotTape.test_the_tick_rests_on_ccnot_and_nothing_more_is_claimed |
| Wiring 1, pinned to moop's trace, in the interpreter and compiled | Built | Proposed | TestCcnotTape.test_the_trace_is_moop_s, test_compiled_code_prints_moop_s_trace |
| Draws and births against a model of wiring 1, and taken back | Built | Proposed | The tape generator (XI.2); TestCcnotTape.test_draws_and_births_are_taken_back |
| `draw`, `birth` and `tape_tick` cannot be declared again; no request for the tape; a program's own request may share the word | Built | Ratified (C5) | TestCcnotTape.test_draw_is_the_tape_s |
| The domain D stated, and each rule's extent on it: the tick a permutation, a draw and a birth embeddings | Built | Proposed | Proof (VI.6); TestCcnotTape.test_on_its_domain_the_tick_is_a_permutation, every state of D with 2 or 3 cells on each tape (1,024) |
| Every input outside D refused when it runs, in both backends; no head wrapped round | Built | Proposed | TestCcnotTape.test_a_tape_needs_two_cells, test_outside_its_domain_every_input_is_refused |
| D established by the checker, not guarded at run time | Absent | Open | — (a length invariant in types; not justified by the tape alone) |

---

## VII. Reversibility and Information Accounting

### VII.1 One engine

| Operation | Who | What runs | What it may take back |
|---|---|---|---|
| forward | Anyone | The rule | — |
| `undo` | User code | The certified rule's derived inverse, forward | Nothing kept: a certified inverse never needs the journal |
| rewind | The system (runtime API, `selvage call --rewind`) | Any rule's derived inverse, forward | Exactly the entries its run kept |
| `_inv` in C | Compiled code | The derived inverse, compiled forward by the same emitter | — |

The inverse is code anyone may hold, print or transform. Holding it grants nothing: `x was discarded` runs only under the system's authority.

**A rewind belongs to one run.** The system remembers every run that kept anything, with its output. A rewind must name the newest such run and that output, and may take back exactly the entries that run kept, no more and no fewer. Rewinding happens in the context the run ran in, with the same answers installed.

**What was kept afterwards stands in the way.** If anything was kept after a run ended, such as a reply a procedure kept (V.3) or the entries of a run a refusal cut short (VI.5), that run can no longer be rewound, and the refusal says how many entries stand between the run and its rewind.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| One forward engine for rules and inverses, in both backends | Built | Proposed | TestInversion; TestC23Backend.test_derived_inverses_compile_and_agree |
| Rewind bound to its run | Built | Proposed | TestSemanticContracts.test_a_rewind_is_bound_to_the_newest_run_and_its_exact_output |
| A run with entries kept after it is not rewound | Built | Ratified | TestGenerated04.test_a_kept_reply_stands_between_runs |

### VII.2 The roots

```selvage
type Journal
    Empty
    Kept(entry: Any, rest: Journal)

type Entry
    Dropped(code: Text, by: Text, value: Any)
    Chose(code: Text, by: Text, among: I64)
    Decided(code: Text, by: Text, asked: I64, world: Bool)

request System for Root
    keep(entry: Any) returns ()

request Witness
    history() returns Journal

request Refusal
    refuse(reason: Text) returns ()

answer Root for System, Witness, Refusal takes Journal
    (keep(e), j) <-> ((), Kept(e, j))
    (history(), j) <-> (h, j) where
        h is j

answer Object for System, Witness, Refusal takes Root
```

Three things are kept apart:

| | What it is |
|---|---|
| **Journal** | Retained historical state: what the run kept, newest first |
| **Witness** | Controlled historical inquiry: `history`, asked by a rule that lists `Witness` and answered by the nearest answer for it |
| **Root** | Authority over system-level operations: it alone holds the journal, answers `keep`, and gives the final answer to `refuse` |

- **Root, the system-facing root**, owns the journal. `keep` writes it and `history` gives a copy. Root's answer to `refuse` is the end of the run (VI.5); that answer has no clause, since it has no reply.
- **Object, the user-facing root**, takes a `Root` instance and delegates every request to it. Every run starts inside an `Object`, so a request that no installed answer takes reaches it, and its reversibility is Root's, by delegation.
- **One answer, three groups.** Root answers `System`, `Witness` and `Refusal`, and the three stay distinct in meaning: `keep` controls retention, `history` controls historical disclosure, and `refuse` controls termination. Retaining a value discloses nothing, and reading history retains nothing.
- **`System` is sealed to Root** (`request System for Root`, VII.3): a program lists `System` in a row when it reaches `keep`, and can neither send `keep` nor answer it.

**Disclosure goes through a host.**

| Who | What it does |
|---|---|
| Inner code | Asks `history`, and lists `Witness` to do so |
| The host's answer for `Witness` | Decides what inner code receives. It may ask `history` of the next answer out |
| Root | Answers `history` under its seal, with a copy of the journal |

```selvage
answer Closed for Witness takes ()
    (history(), s) <-> (Empty, s)

rule redact takes Journal returns (Journal, Journal)
    Empty <-> (Empty, Empty)
    Kept(Dropped(code, by, value), rest) <-> (Kept(Dropped(code, by, ()), shown), Kept(value, hidden)) where
        (shown, hidden) is redact(rest)
    Kept(Chose(code, by, among), rest) <-> (Kept(Chose(code, by, among), shown), hidden) where
        (shown, hidden) is redact(rest)
    Kept(Decided(code, by, asked, world), rest) <-> (Kept(Decided(code, by, asked, world), shown), hidden) where
        (shown, hidden) is redact(rest)

answer Redacting for Witness takes ()
    (history(), s) => (out, s) where
        all is ask history()
        (shown, hidden) is redact(all)
        out is shown
        (shown, hidden) was redact(all)
        all was ask history()
```

`Closed` discloses nothing. `Redacting` discloses which rules dropped something and not what they dropped: it asks Root's `history`, splits the copy with a certified rule, copies out the part that may be shown, puts the copy back together and gives it back.

- **Inner code cannot go around its host.** Its `ask` goes to the nearest answer for `Witness`. An answer it installs itself can only ask the host: under a `Redacting` host, inner code that installs its own pass-through answer still reads the redacted journal.
- **The path outward is this one path.** A host's answer that is answering `history` may ask `history`, and that ask goes to the next answer out, in the end Root (VI.2). It is a capability boundary for disclosure, not a rule about requests in general.
- **An inquiry leaves the journal as it was.** Root's rule copies, and keeps nothing.

**Giving the copy back.** A host that passes `history` on may give its copy back, as `Redacting` does with `all was ask history()`. That takes its ask back from the answers further out.
- **What was transactional is rewound.** What an answer further out did in its own state when it was asked, such as counting the inquiry or holding a copy, is taken back with the ask. The answers further out are then as they were before the host asked.
- **A kept record refuses the withdrawal.** An answer further out that kept a record of the disclosure in the journal, whether the value it disclosed or a mark that it disclosed, cannot be passed back through: the giving back is refused, as a take-back only the system may make. Unless an answer for `Refusal` takes the refusal, the run ends with status 70; if one does, what the inquiry reached stands as it was when it was refused.
- **A host that gives its copy back keeps nothing of it.** In a clause that takes back its own ask, what the ask returned, and whatever is computed from it or decided by it, may reach the reply and nothing else: not the answer's state, a message, another request, a decision that may reach the world, or the journal. The checker refuses the clause otherwise. A host cannot claim to pass the copy back while keeping what it read.

So a disclosure is never withdrawn once an intermediary has kept what was disclosed (G11).

```selvage
# refused: a host that gives its copy back keeps nothing of it
answer Hoard for Witness takes Journal
    (history(), mine) => (out, Kept(c, mine)) where
        all is ask history()
        c is all
        out is Empty
        all was ask history()
```

`Hoard` is refused: it would restore the answers further out while keeping, in its state, what they disclosed.

- **The row shows it.** Installing a host whose rule asks `history` outward puts `Witness` in the installing rule's row, unless an answer installed around it takes the request. A rule that reads history, or lets code inside it read history, says so.
- **A component stays within its groups.** An installed answer declared for another group does not answer `history`, even when its state holds an answer for `Witness` (VI.3).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Root's `keep` and the journal as a form | Built | Proposed | TestJournalContract; TestInversion.test_a_loss_is_a_message_to_the_root |
| `Object` taking a `Root` instance and delegating to it | Built | Ratified | TestInversion.test_a_loss_is_a_message_to_the_root; TestJournalContract.test_keep_appends_and_rewind_restores_the_exact_journal |
| `Refusal`, with Root's clause-free answer to `refuse` | Built | Ratified | TestGenerated04.test_a_refusal_goes_to_the_nearest_answer_or_ends_the_run |
| An answer for several groups, each with its own meaning | Built | Ratified | TestSealAndWitness.test_root_keeps_retention_disclosure_and_termination_apart; TestGenerated04.test_delegation_to_the_single_component_that_answers |
| `keep` alone in `System`; `history` asked through `Witness` | Built | Ratified | TestSealAndWitness.test_history_is_asked_through_witness |
| A host's answer for `Witness` deciding what inner code reads | Built | Ratified | TestSealAndWitness.test_a_host_mediates_what_inner_code_reads; TestGenerated04.test_inner_code_reads_what_its_hosts_pass_on |
| An inquiry leaving the journal as it was | Built | Ratified | TestSealAndWitness.test_an_inquiry_leaves_the_journal_as_it_was; the same generated test |
| Installing a host that asks outward, in the row | Built | Ratified | TestSealAndWitness.test_installing_a_host_that_asks_outward_is_in_the_row |
| Giving the copy back rewinds what was transactional further out | Built | Ratified | TestSealAndWitness.test_a_withdrawn_inquiry_takes_back_what_the_hosts_counted_and_held; TestGenerated04.test_inner_code_reads_what_its_hosts_pass_on |
| A kept record of the disclosure refuses the giving back | Built | Ratified | TestSealAndWitness.test_a_kept_record_of_a_disclosure_cannot_be_withdrawn, test_a_refused_withdrawal_leaves_the_answers_further_out_as_they_stood; the same generated test |
| A host that gives its copy back keeps nothing of it | Built | Ratified | TestSealAndWitness.test_a_host_that_gives_its_copy_back_keeps_nothing_of_it; the same generated test, with hosts that try every route to keeping |
| What counts as keeping: the reply alone may depend on what was read, by value or by condition | Built | Ratified | The same tests |

### VII.3 `keep`: certificate, authority, storage, accounting

These are four separate specifications.

**The certificate.** `keep` is a bijection with exact domain and codomain:

K : Entry × Journal → NonEmptyJournal,   K(e, j) = Kept(e, j),   K⁻¹(Kept(e, j)) = (e, j)

The clause test certifies this, and nothing more. It does not claim a bijection from all journals to all journals.

**The authority policy.** The checker and the runtime enforce the rest:

| Invariant | How it is enforced |
|---|---|
| `keep` adds exactly one whole entry, newest first, and changes nothing below it | K |
| Only the system takes an entry back, and only the newest | The take-back runs only under rewind authority; the inverse asks for entries in exactly the reverse order the rule kept them |
| An entry is taken back only by the mirror of the code that kept it, in the run that kept it | Every entry names its code by identity, and the clause running backward is `mirror` of the clause that ran; a rewind names its run; any other is refused |
| No program writes a journal any other way | `System` is sealed to `Root` (R5): only the system makes a Root instance, sends `keep` or answers it |
| Reading is an inquiry, and does not change the journal | `history` is asked through `Witness` and returns a copy; the nearest answer for `Witness` decides what the reader sees, and may give its copy back, which is refused where a record of the disclosure was kept (VII.2) |
| A commit point dissipates every entry at once | `output` and `commit`, which stand between rule calls |
| Rewind restores the exact prior journal | Checked with earlier entries present |

**Entries.**

| Entry | Kept for |
|---|---|
| `Dropped(code, by, v)` | A discard, including the old value replaced by `set` or by a rounded update |
| `Chose(code, by, n)` | A lossy rule's clause choice, kept where the output matches the right sides of n clauses, n being more than one. `code` names the clause chosen; the entry is kept after every entry the clause's own steps kept, including those of the rules it called, so the inverse takes it back first |
| `Decided(code, by, asked, world)` | A decision (VI.4) |

**An entry names the code that kept it.** The name is the identity of that code in its canonical form (III.3), the identity under which every rule, request and answer is referred to; the journal has no naming scheme of its own.

| What an entry says | How |
|---|---|
| The code that kept it | `code`: the identity of the clause that kept it, as it runs. For a reply a procedure kept, the identity of the procedure's own code |
| The event | The entry's place in the journal, newest first, within the run a rewind is bound to (VII.1). No identifier is added for it |
| What was kept | The value, the number of clauses that share the output, or how a decision was settled |
| Where it came from | `by`: the rule, or the answer and request, the code belonged to when it ran |

- **Code takes back what its mirror kept.** A rewind runs the mirror of each clause that ran (VIII.2), and a clause running backward takes an entry only if the entry names the clause it is the mirror of. To choose a clause backward, the inverse takes the `Chose` entry and runs the clause whose mirror it names.
- **`by` decides nothing.** It is for whoever reads the journal. No take-back and no choice of clause goes by it.
- **Names and order do not matter.** A clause's identity holds neither its rule's name, nor its place among the clauses, nor the names of its variables. Where it calls a rule, sends a request or makes an answer, it holds that identity and not a name (III.3). Renaming any rule, variable, request, group or answer, reordering clauses or moving a declaration changes no entry's `code`.
- **What the code does matters.** Changing a step, the shape of a pattern, or which binding a use refers to changes the identity of that code. Changing a rule that is called changes the identity of the code that calls it.
- **Forward and backward agree.** The identity under which a clause keeps an entry and the identity its mirror looks for are the same, computed the same way.
- **Identity is a name, compared as the form it names.** A run holds the canonical form behind every identity it uses, and refuses if two different pieces of code share one. So where two identities are compared, the forms are compared (III.3).
- **Integrity is at the level of the program.** No program can make or change a journal entry: the journal is sealed. A host that tampers with the journal directly can write an entry that names another clause of the same rule, and it will pass. The guarantee is not cryptographic, and does not hold against a hostile or compromised host.
- **Position orders events within a run.** An entry's place is its order among the entries of its run. It is not an identifier across runs.
- **Identity of code only.** It is the identity of the code as a form: not of a compiled artifact, of a specialization, or of a rule together with the values it runs on.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Entries naming their code by identity; take-backs and the choice of clause going by it | Built | Ratified | TestJournalIdentity.test_an_entry_names_the_code_that_kept_it, test_code_takes_back_only_what_its_mirror_kept; TestGenerated04.test_an_entry_names_its_code_under_renaming_and_reordering |
| No identity changed by renaming a rule or reordering its clauses | Built | Ratified | TestJournalIdentity.test_renaming_a_rule_or_reordering_its_clauses_changes_no_identity; the same generated test |
| No entry's `code` changed by renaming a variable, a request, a group or an answer; an entry's `by` showing the program's own names | Built | Ratified | TestCodeIdentity.test_requests_and_answers_are_referred_to_by_identity; the same generated test ("variables renamed"); the names generator (XI.2) |
| `by` kept beside the identity, as provenance and never as authority | Built | Ratified | TestJournalIdentity.test_code_takes_back_only_what_its_mirror_kept; the same generated test |
| Identities compared as the forms they name | Built | Ratified | TestJournalIdentity.test_identities_are_compared_as_the_forms_they_name; the same generated test |
| Entries naming their code in compiled code | Deferred | Ratified | Compiled code keeps values and their bit counts, and neither rewinds nor answers `history` (IX.2). When it implements these entries they carry the same identities as the interpreter's: there is no second, weaker model |

**The Root seal.** The seal is an authority boundary, not a naming convention.

- **How it is written.** `request G for A` seals the group `G` to the answer `A`. The prelude writes `request System for Root`.
- **One general rule (R5).** A seal is held by the place that declares it. Only code in that place sends a request of the sealed group, declares an answer for it, or makes or opens an instance of the sealed answer. Nothing in the rule mentions `Root` or `keep`.
- **Where, not who.** A seal says where a request is answerable. It does not by itself grant authority to every answer in that place.
- **Holding a sealed instance.** An answer whose state holds a sealed instance is sealed with it, since making or opening the holder would hand that instance over. `Object` is sealed this way.
- **Places.** There are two: the prelude, which is fixed for the run (R7), and the program. A program is not in the prelude, so it cannot acquire the Root seal. A seal a program declares is held by the program itself and binds nothing inside it; it will bind other places when modules exist (XII.5).
- **The system holds the other half.** It makes the one Root instance when a run starts, is the only sender of `keep`, takes entries back only under rewind authority (VII.1), and itself answers a request the sealed answer declares and has no clause for, which is how Root answers `refuse`.
- **It is tested from outside.** Its evidence is programs that try each route and are refused: sending `keep` from a procedure, a clause rule, an answer or a message; making a Root or an Object, alone, around a forged journal or to install around other code; packing or opening one in a clause; answering `System`, by a clause or by holding a root; sealing another group to Root; declaring a prelude name again; reading history without `Witness`; taking an entry back without authority; asking through constructed code.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Only the system writes the journal or takes entries back | Built | Ratified | TestJournalContract.test_only_the_system_writes_or_takes_back, test_a_rewind_out_of_step_is_refused |
| That boundary enforced by the Root seal under R5 | Built | Ratified | TestSealAndWitness.test_the_seal_is_a_rule_about_places_and_names_no_declaration; TestGenerated04.test_every_route_to_what_is_sealed_is_refused |
| Seals other than Root's binding other places | Absent | Open | Needs modules (XII.5) |

**Storage.** How a backend holds the entries: forms in the interpreter, a byte stack in C23.

**Accounting.** ε (VII.5).

### VII.4 Commit points, measurement and reset

`output` and `commit` dissipate the journal: nothing before them can be rewound. They stand between rule calls, so rewinding a rule never meets one. Output reaches the world, so it commits.

**Measurement** (quantum profile, IX.4) is a Request to the quantum world, not a new kernel primitive:
- the quantum backend receives a measurement request;
- the observed outcome is world input, recorded in the journal;
- the measuring transition is lossy and written `=>`;
- measurement is a commit point. Replay reproduces the recorded outcome. It does not repeat the physical measurement or restore the amplitudes before it: the journal keeps the history of the observation, not the quantum state that preceded it.

**Reset** is irreversible state preparation: a lossy transition, written `=>`, that discards the prior quantum state and prepares the specified initial state. An implementation may discard internally, but the semantics is the reset, not an alias for measurement or for `discard`.

**What is built: the request, answered by nothing.** The prelude declares the group (N1):

```selvage
request Measure
    measure() returns Bit
```

No answer for it exists, in the prelude or in the toolchain, and Root does not answer it. An `ask measure()` that no installed answer takes reaches Root unanswered and is refused (VI.5): the run ends with status 70, after whatever it output before. A quantum profile would install the answer. No quantum type exists (IX.4).
- **An environmental request** (N1). The prelude declares the request and does not answer it, and claims no implementation of quantum measurement. An answer comes from the world a program runs in, or from an answer the program installs explicitly. A request can be declared before its physical realization exists: the declaration does not establish the realization.
- **What Q3 asks of the asker already holds,** by rules that were there before: a rule that asks `measure` lists `Measure` in its row (R6), and a clause rule that asks it is lossy and writes `=>`, because its reply is world input. Nothing is special to `measure`: the refusal is the one every request nobody answers meets, with the same reason.
- **Not `draw`.** A draw is a certified rule over a tape the program holds, the same in every backend (VI.6). A rule that draws is certified, and one that asks `measure` is lossy whatever is installed: a rule's class is fixed statically, so the two cannot stand in for each other.
- **Environmental measurement and stand-ins** (N2). `Measure` is not sealed, so a program may install an answer of its own for it, as it may for `Refusal` or `Witness`. Two cases are kept apart:
    - *Environmental measurement*: an answer supplied by the environment the program runs in, through a quantum profile. None exists.
    - *A stand-in*: an answer the program installs, a modelled reply for a test, a simulation or a controlled experiment. Inside its `with`, `measure` is answered as the stand-in says. A stand-in implements the request's contract: it does not establish that a physical measurement occurred, and what it replies is not quantum measurement. One that replies with the tape's `draw` does not make a draw random (C1). Outside every stand-in the request reaches Root and is refused.
- **What is measured is not said** (N3). `measure` takes nothing: a qubit, and how one is named, are the quantum interface's to define (XII.5). When qubit types or registers exist, the signature is to be revisited together with what a measurement does to the state, how its outcome is represented, and its irreversibility.
- **Compiled code** has no `ask` (IX.2), so a program that asks `measure` is not built: it is refused, with status 1, before anything runs. The two backends refuse at different points, not with different meanings: the interpreter when the request is asked, compiled code when the program is built, and neither runs past a `measure` that nothing answers. The build refusal is the broader of the two: compiled code refuses every `ask`, a stand-in's included, until requests are lowered statically (XII.4, item 5).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| The group `Measure` in the prelude, answered by nothing; `ask measure()` refused at Root with status 70 in the interpreter, and a program that asks it not built in compiled code (status 1) | Built | Ratified (N1) | TestMeasure.test_the_prelude_declares_measure_and_nothing_answers_it, test_an_ask_of_measure_is_refused_at_root_with_status_70; the measure generator (XI.2) |
| A rule that asks `measure`: `Measure` in its row, and lossy if it is a clause rule | Built | Ratified | TestMeasure.test_a_rule_that_measures_is_lossy_and_a_rule_that_draws_is_not; the same generator |
| A program's own answer for `Measure`, a stand-in taking the request inside its `with` only | Built | Ratified (N2) | TestMeasure.test_a_stand_in_takes_the_request_inside_its_with_only; the same generator |
| Measurement answered by a quantum backend: the outcome kept, a commit point | Absent | Ratified | — |
| Reset as lossy state preparation | Absent | Ratified | — |

### VII.5 Three quantities

| Quantity | What it is | Where it is reported |
|---|---|---|
| Information a step loses | What is needed to tell its inputs apart, given its output | The checker names each loss; the entry carries it |
| Journal storage | How a backend represents the entries it holds | Implementation-defined |
| ε | Under the accounting convention below, the bits of the entries a commit point dissipates | `SELVAGE_STATS`, identical in both backends |

ε counts what a run made unrecoverable: what its lossy rules dropped, and the world replies its rules and procedures kept. For values of closed types it is meant to bound that loss from above, which is an open proof obligation (below); for values of open types it is a convention. It is neither memory use nor heat.

**What an entry is charged.** The bits that tell apart what the run could have let go of there, given what remains.

| Entry | Charge |
|---|---|
| A clause choice | Nothing where the output matches the right side of one clause: the output shows which clause ran, and no entry is kept. Otherwise ⌈log₂ n⌉, n being the clauses whose right side the output matches |
| A dropped word | Its width. `Bool` 1; `Trit` 2, whichever value it holds |
| A dropped value of a type with constructors | ⌈log₂ k⌉ for which constructor it is, k being the constructors it may still have, plus its fields, each by its declared type. A type with one constructor is charged its fields alone |
| A dropped tuple | Its parts |
| A dropped value that can still be computed | Nothing. The entry is kept, since the inverse takes it back, but dropping it lost nothing |
| A decision, with n answers installed for `Decide` | 1 + ⌈log₂(n + 1)⌉: its bit, and which of the n answers or the world settled it, however many were asked |

- **Constructors still possible.** A value made in the clause by a constructor has that one. A name bound by the left side cannot have a constructor where one earlier clause takes every input of this clause that has it there. Otherwise every constructor of its type is possible.
- **Still computable.** The test is the one for a proved uncompute (V.5): the name was bound in this block from an expression, and nothing that expression read, nor the name, has changed since. What it was computed from is charged when that is dropped.
- **Exact where the checker decides, a bound elsewhere.** A value the checker cannot show to be computable, and a constructor it cannot rule out, are charged in full.
- **Conventions that remain.** A dropped `F64` is 64 (III.4). A dropped array is 64 for its length, plus its elements. A dropped `Text` is charged as an array of bytes: 64 for its length and 8 for each byte. A value whose type the declaration leaves open, `Any` or code, is charged 16 for each form in it, plus the parts.
- **The charges as a code, for values of closed types.** Where a rule drops only values whose type says what they can be — words, `Bool`, `Trit`, `F64`, `Text`, constructors, tuples, arrays, instances — and keeps clause choices, the charges of the inputs that give one output are meant to be the lengths of a code that tells those inputs apart. On every rule the generated tests go through, input by input, they are (XI.2). That they are for every such rule is the proof obligation below.
- **Open types are outside the code.** A dropped value of an open type is charged for its content and not for what kind of value it is, so there an input can be charged less than the rule lost. That charge is a convention of accounting, and ε is not a bound on the loss for a rule that drops such a value.
- **One definition.** The interpreter and compiled code charge alike, and the tests compute each charge a third time from a model of their own.
- **A value is charged by the type it is declared.** A literal given where a `U8` is declared is a `U8`, and is charged 8 bits.

**The lower bound: an open proof obligation.** Take a clause rule whose runs decide no `Trit` and drop only values of closed types. Fix its parameters, which answers are installed and in what order, and the journal it starts from. A run takes an input, and the states of those answers, to an output and their states afterwards; it is charged c, the sum of the charges of the entries it kept. The obligation is Kraft's inequality: for every result, the charges of the runs that end in it satisfy

Σ 2<sup>−c</sup> ≤ 1.

The charges are then the lengths of a code that tells those runs apart, and three bounds follow for a result that N inputs share:
- whatever the odds of the inputs, the expected charge is at least the entropy of which input it was;
- taken evenly over the N inputs, the charge is at least log₂ N;
- the largest charge is at least ⌈log₂ N⌉.

It is not required that every input be charged ⌈log₂ N⌉, and it is not so. A rule that takes `None`, `Some(0)` and `Some(1)` to one output charges them 1, 2 and 2 bits, where ⌈log₂ 3⌉ is 2. Those charges are a code, and no code for three things is shorter.

A proof must establish three things: that the inverse run, given the entries, recovers the input; that the sum of the entries' charges is enough for the whole run, without taking the entries to be independent; and what is held fixed. Until a proof is accepted, the bound rests on generated tests.

Decisions are outside the obligation, as are the replies a procedure keeps (XI.3, scope). Charged by the answers installed, the ways one decision can be settled are charged the lengths of a code; the obligation does not yet take in the world's reply.

```selvage
rule and_table takes (Bit, Bit) returns Bit
    (0, 0) => 0
    (0, 1) => 0
    (1, 0) => 0
    (1, 1) => 1
```

Three clauses give 0: there the choice among three is kept, 2 bits. The output 1 shows its clause, and nothing is kept. `and_gate` (II.5) keeps both inputs, 2 bits on every run. The least any form of the gate can keep is nothing for (1, 1) and log₂ 3 bits otherwise.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| A clause choice kept only where the output leaves one, among the clauses that share it | Built | Ratified | TestAccounting.test_a_clause_choice_is_kept_only_where_the_output_leaves_one; TestGenerated04.test_a_run_is_charged_for_what_it_lets_go_of |
| A dropped value charged by its declared type, and by the constructors still possible | Built | Ratified | TestAccounting.test_a_dropped_value_is_charged_by_its_type, test_only_the_constructors_still_possible_are_counted; the same generated test |
| A value that can still be computed dropped for nothing | Built | Ratified | TestAccounting.test_a_value_that_can_still_be_computed_is_dropped_for_nothing; the same generated test |
| The charges of the inputs that give one output being the lengths of a code, on generated rules over small closed types | Built | Ratified | TestAccounting.test_the_charges_tell_the_inputs_apart; TestGenerated04.test_a_run_is_charged_for_what_it_lets_go_of ("outputs weighed") |
| A dropped `Text` charged 64 for its length and 8 for each byte | Built | Ratified | TestAccounting.test_a_dropped_text_is_charged_its_length_and_its_bytes; TestC23Backend.test_the_corrected_charges_are_the_same_in_both_backends; the accounting generator, with `Text` among its types |
| A decision charged by the answers installed for `Decide` | Built | Proposed (Q13, XII.6) | TestAccounting.test_a_decision_is_charged_by_the_answers_installed, at 14, 15 and 16 answers; the decisions generator |
| A word charged by its declared width, however it was written | Built | Ratified | TestAccounting.test_a_word_is_charged_by_its_declared_width_however_it_was_written; the declared-types generator |
| The lower bound for every rule over closed types | Specified: a proof obligation | The obligation Ratified (T3). Its statement as Kraft's inequality Proposed (T5, XII.6) | No proof. A proof must show the entries of the runs that share a result to be uniquely decodable |
| The same charges in both backends, and ε their sum | Built | Ratified | TestAccounting.test_epsilon_is_the_sum_of_the_charges; TestC23Backend.test_the_backends_charge_alike, test_the_corrected_charges_are_the_same_in_both_backends; the same generated test ("compiled") |
| What "still possible" and "still computable" are taken to mean; the conventions that remain | Built | Ratified | TestAccounting; the accounting generator (XI.2) |

### VII.6 The chain to `ccnot`

Each reversible thing rests on the layer below it. `selvage lineage` reads the links from the code that runs.

| Layer | What is reversible | Rests on |
|---|---|---|
| prototype | An answer that delegates: its own request rules, and those of the component it delegates to | Its rules; the component's rules, by delegation; finally Object |
| user root | `Object` | Root, by delegation |
| system root | `Root`: `keep` and `history` | Clauses that move values: `exchange`, `fanout` |
| actor | An answer instance: state plus one rule per request; a message is taken back by the rule's derived inverse. Scheduling and concurrency are not part of it | Clause rules |
| function | A clause rule over words and data. An expression rule is listed as a function or a procedure (V.3) | Its steps: word `add` and `subtract` are `ripple_add`; `swap` and moves are `exchange`; copies are `fanout`; losses are `keep`. Each operator class in its expressions has its own link |
| logic | `ripple_add` (Cuccaro), `exchange`, `fanout`, `cnot`, `toggle`, Kleene circuits: rules over bits | Bit updates: `add x to z` is `cnot`, `add x * y to z` is `ccnot` |
| base | `ccnot` | Its four clauses, by the clause test alone |

Every link carries its own certificate:

| Certificate | What establishes it |
|---|---|
| checked | The checker certified this rule using the target's certificate |
| delegated | At run time the request goes to the target, whose certificate holds there |
| realized | A step is realized by a gate-level rule; `--verify` runs both and compares them |
| theorem | Bennett's construction over Toffoli-universal gates; cited, not run |

```
$ selvage lineage examples/orbit.selv orbit --verify
orbit       function          bijection  subtract on I64 -> ripple_add [realized]; division and remainder -> ripple_add [theorem]; multiplication -> ripple_add [theorem]; add on I64 -> ripple_add [realized]
ripple_add  logic             bijection  add on Bit -> cnot [realized]; add a * b on Bit -> ccnot [realized]
cnot        logic             bijection  calls -> ccnot [checked]
ccnot       base              bijection  its four clauses [the clause test alone]

realizations, run now:
  add on I64 = ripple_add                       537 cases, 0 mismatches  (every pair at 4 bits, and 281 pairs at 64 bits (edges and random))
  add a * b on Bit = ccnot                        8 cases, 0 mismatches  (exhaustive over Bit)
  add on Bit = cnot                               4 cases, 0 mismatches  (exhaustive over Bit)
```

What is run and what is cited:
- **Run.** The Bit updates agree with `ccnot` and `cnot` on every input. `ripple_add` agrees with machine addition on every pair at 4 bits, on all 65,536 pairs at 8 bits (compiled), and on edge and random pairs at each width a program uses; its derived inverse subtracts. `exchange` and `fanout` agree with swap and copy the same way. `Bool` is a sub-shape of `Trit` (R1), so on known values the Kleene circuits are Boolean logic: they agree with `and`, `or` and `not` on all ten cases. On `Bit`, a temporary is realized directly, a `ccnot` per product and a `cnot` per sum.
- **Cited.** That a temporary computed from an arbitrary word expression, or a copy of a whole data structure, reduces to these gates is Bennett's construction over Toffoli's universal gate. These links are labelled `theorem`.
- **Machine.** Compiled code uses the machine's own addition; the realization checks tie it to the gate-level rules.
- **Operators inside expressions.** Every operator class a step's expression uses carries its own link, so nothing a rule rests on is unlabelled. In `add k * q / 2 to p` the `add` is linked to `ripple_add`, and the multiply and the divide each carry a `theorem` link. A gate-level multiply, verified like `ripple_add`, is deferred.

| Operator class | Link | Certificate |
|---|---|---|
| Word addition and subtraction | `ripple_add` | realized, run by `--verify` |
| Multiplication | `ripple_add` | theorem |
| Division and remainder | `ripple_add` | theorem |
| Comparison | `ripple_add` | theorem |
| Bitwise operations and shifts | `ccnot` | theorem |
| Conversions | `fanout` | theorem |
| `F64` arithmetic | `ripple_add` | theorem |
| Boolean logic on `Bool` | `trit_and`, `trit_or`, `trit_not` | realized, run by `--verify` |
| Kleene logic on `Trit` | `trit_and` | realized |
| Products and sums on `Bit` | `ccnot`, `cnot` | realized |

- **A function called in an expression** is linked as `computes with`, so its own operators are reached. A function is recomputed whole from its parameters (Bennett); a procedure, from its parameters and the replies it kept.
- **Circuit layout.** In a rule over bits, an index or count expression built only from literals, parameters, loop counters and array lengths lays out the circuit. It is fixed when the rule is unrolled at a width, and it is not a gate, so it carries no link. The exemption is for layout alone: an index or count that reads the rule's data is an operation on that data, and carries its link like any other.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Lineage with a certificate per link, for steps | Built | Proposed | TestInversion.test_lineage_reaches_ccnot_from_every_rule |
| A link for each operator class inside expressions | Built | Ratified | TestGenerated04.test_every_operator_class_carries_a_link |
| Layout as the only exemption | Built | Ratified | TestSealAndWitness.test_layout_is_the_only_lineage_exemption |
| Boolean logic realized by the Kleene circuits, with no new prelude code | Built | Ratified | TestTwoTiers.test_boolean_logic_runs_on_the_kleene_circuits; TestGenerated04.test_every_operator_class_carries_a_link |
| A gate-level multiply, verified | Deferred | Ratified | — |
| Realization links run on demand | Built | Proposed | `--verify`: 0 mismatches |
| Delegated links for prototypes under VI.3 | Built | Ratified | TestInversion.test_lineage_reaches_ccnot_from_every_rule (prototypes) |

### VII.7 Guarantees

| ID | Guarantee | Implementation | Design | Evidence |
|---|---|---|---|---|
| G1 | `invert` derives an inverse program for every clause rule; the checker certifies it is defined on the forward rule's image and that what it needs is recomputable or kept | Built | Proposed | Proof, for the model of XI.3; TestInversion; TestSoundness.test_generated_rules_round_trip; TestGenerated04.test_the_theorem_holds_on_rules_that_call_message_and_open, test_the_interpreter_and_invert_are_the_model_of_the_proof |
| G2 | Between commit points, the newest run that kept anything can be rewound exactly, including losses, messages and decisions | Built | Proposed | TestInversion.test_semantic_round_trips; TestSemanticContracts |
| G3 | Every bit a run loses, and every reply it takes from the world, is a `keep` message under the authority policy, so ε is complete under its convention, for clause rules and for procedures (V.3) | Built | Ratified | TestJournalContract; TestReversibility.test_epsilon_counts_pruned_bits; TestGenerated04.test_rows_tell_functions_from_procedures_and_show_reaching_keep; ε identical in both backends (TestC23Backend) |
| G4 | The prelude cannot change during a run | Built | Proposed | By construction |
| G5 | A certificate applies only to the form whose canonical encoding it names | Specified | Proposed | — |
| G6 | No operation has undefined behaviour; no undecided condition is guessed; a run nested too deep is refused alike in both backends (III.5) | Built | Proposed | TestPrograms.test_refusals_are_defined; TestC23Backend.test_defined_behaviour_agrees, test_the_depth_bound_agrees_in_c, test_the_default_depth_bound_is_reached_in_both_backends |
| G7 | Representing code grants nothing: the inverse of a lossy rule takes back only under the system's authority, and constructed code runs only after admission | Built | Ratified | TestInversion.test_authority_stays_outside_the_code |
| G8 | Every reversible realization traces to `ccnot`, each link with its own certificate, the operator classes inside expressions included; lineage grounds realization, not certification (VII.6) | Built | Ratified | TestInversion.test_lineage_reaches_ccnot_from_every_rule; TestGenerated04.test_every_operator_class_carries_a_link; `lineage --verify`; theorem links cited |
| G9 | The arrow of every clause states its rule's certificate | Built | Ratified | TestChecker.test_the_arrow_states_the_certificate, test_inversion_preserves_the_arrow; TestGenerated04.test_arrows_state_the_certificate_and_lossy_runs_rewind |
| G10 | Only the system writes the journal or takes entries back, and reading it is an inquiry the nearest `Witness` answer controls (VII.2, VII.3) | Built | Ratified | TestJournalContract.test_only_the_system_writes_or_takes_back; TestSealAndWitness; TestGenerated04.test_every_route_to_what_is_sealed_is_refused, test_inner_code_reads_what_its_hosts_pass_on |
| G11 | A disclosure is not withdrawn once an intermediary has kept what was disclosed: a record kept further out refuses the withdrawal, and a host that gives its copy back keeps nothing of it (VII.2) | Built | Ratified | TestSealAndWitness.test_a_kept_record_of_a_disclosure_cannot_be_withdrawn, test_a_host_that_gives_its_copy_back_keeps_nothing_of_it; TestGenerated04.test_inner_code_reads_what_its_hosts_pass_on |

---

## VIII. Homoiconicity and Metaprogramming

### VIII.1 How far code is data

| Level | What is a form | Implementation | Design | Evidence |
|---|---|---|---|---|
| Expression | Every expression: each form the parser writes for one is a constructor of `Code` | Built | Ratified | TestCensus.test_every_form_the_parser_writes_is_taken_apart_and_put_together; TestSurface.test_quoted_code_is_data |
| Step and clause | Every step of a clause rule and of an expression rule, clauses, and every derived inverse. `sequence` writes a block as a sequence and a tuple as a list of parts, so that a clause can take all of the code apart; `block` writes them back. Quoted code and literals are data, and are left as they are | Built | Ratified | TestInversion; TestDeclarations.test_all_of_the_code_is_written_to_be_taken_apart |
| Run | Answer instances are values; the journal is readable as data through `history`, asked of `Witness` | Built | Proposed | TestJournalContract; TestSemanticContracts.test_history_is_a_copy_into_an_empty_name_and_its_inverse_uncopies |
| Live run | Installing admitted code into a running program; scheduled actors and their continuations | Specified | Proposed | — |
| Declaration | Rule, answer, type and request declarations as forms of the type `Declaration`, distinct from `Code`: a declaration's header names and types it and is not `Code`; the clauses in its body are. `definition(quote n)` gives the declaration under any name, the prelude's included | Built | Ratified | TestDeclarations.test_definition_gives_rules_answers_types_and_requests, test_every_declaration_is_held_as_a_value_and_written_back; TestGenerated04.test_declarations_and_programs_are_read_by_rules_as_the_text_says |
| Program | The whole program as a form of the type `Program`: its declarations in the order written. `program()` gives it, and it prints as the program's canonical text | Built | Ratified | TestDeclarations.test_the_program_is_a_form; the same generated test |
| The form census | `selvage census FILE`: which constructs have a form, which a rule takes apart and which it puts back together, each established by doing it. A declaration that prints but cannot be taken apart does not count | Built | Ratified | TestCensus |
| Encoding | For each form type T that can be serialized, a certified pair encode<sub>T</sub> : T ↔ ValidBits<sub>T</sub>, the bit arrays that encode a value of T. An invalid encoding is refused: for a `Trit`, the pair 01 is one. A copy is an embedding into initialized cells, not a permutation. It follows the declaration forms, so that the bit format does not fix today's gap | Specified | Ratified | — |

**The form types are the prelude's own text.** `Code`, `Parts`, `TypeExpr`, `Param`, `Slot`, `Ctor`, `Op`, `Declaration` and `Program` are declared in the prelude like any type, and the parser's forms are their values. The toolchain holds no table of constructors beside them.

| Type | Constructors |
|---|---|
| `Declaration` | `RuleDecl(name, params, domain, codomain, row, body)`, `AnswerDecl(name, params, groups, state, clauses)`, `TypeDecl(name, shapes, parent)`, `RequestDecl(name, requests, sealed)` |
| `Program` | `Program(declarations)` |
| `TypeExpr` | `TypeName(name)`, `TypeApp(name, arguments)`, `TupleType(members)`; an unstated type is `TypeName("")` |
| `Param`, `Slot`, `Ctor`, `Op` | `Param(name, kind)`; `Slot(name, kind)`, a field of a constructor; `Ctor(name, slots)`; `Op(name, params, reply)`, a request of a group |
| `Parts` | `NoParts`, `Part(first, rest)` |

- **Lists are parts.** The parser writes a rule with as many children as it has parameters and clauses. A clause matches a constructor with a fixed number of fields, so a declaration held as a value writes each list as `Parts`. The two writings hold the same things in the same order, and each is recovered from the other.
- **A rule's body** is its clauses, as `Parts` of `Clause` and `LossyClause` forms, or the block of an expression rule.
- **As it runs, and as written.** `definition` gives a rule or an answer as it runs, elaborated (V.5), and a type or a request group as written. `program()` gives the program as written, without the prelude, which is fixed and reached by name.
- **Holding a declaration grants nothing.** A declaration a program reads or builds declares nothing, runs nothing and installs nothing (VIII.3). Root's declaration can be read like any other, and no Root can be made from it.

```selvage
rule each_mirrored takes Parts returns Parts
    NoParts <-> NoParts
    Part(clause, rest) <-> Part(esualc, tser) where
        esualc is mirror(clause)
        tser is each_mirrored(rest)

rule turned takes Declaration returns Declaration
    RuleDecl(name, params, domain, codomain, row, body) <-> RuleDecl(name, params, codomain, domain, row, ydob) where
        ydob is each_mirrored(body)
```

`turned` is the inverse of a clause rule written in the language: the types it takes and returns change places, and each clause is mirrored. It is certified, and applied to `sequence(definition(quote tick))` it gives what `inverse` gives, but for the name (`examples/declarations.selv`).

**The census.** For the prelude and a program, taken as the values a program itself would hold, every node is checked three ways:

| Column | Established by |
|---|---|
| Represented | The node's tag is a constructor of a declared form type, with as many fields as the node has children |
| Taken apart | A one-clause rule written for that constructor, checked by the ordinary checker, matches the node and binds every field |
| Put together | The same clause builds the node again from what it bound, and the result is the same value |

For every declaration, its printed text must read back as the same declaration. On a program that uses every form the parser can write, 48 of `Code`'s 49 constructors are met, the forty-ninth being `After`, which only `mirror` writes; every constructor of every other form type is met; and nothing escapes.

**Not forms.** What a run has, and no program holds as a value: the answers installed around it, as a list; the run in progress and the runs the system may still rewind; the depth and its bound; the world decider and the record it replays. An answer instance is a value, and the journal is a form read through `Witness` (VII.2).

### VIII.2 Built-ins on code

| Built-in | Gives |
|---|---|
| `quote e` | The expression as a `Code` form |
| `definition(quote n)` | The declaration under the name `n`, a `Declaration`: a rule or an answer as it runs (elaborated), a type or a request group as written |
| `program()` | The program as written, a `Program` |
| `inverse(c)` | `invert` applied to the declaration of a rule or an answer, or to a clause, block or step |
| `sequence(c)` | `c` with all of its code written so that a clause can take it apart: every block as a sequence, `Then(first, rest)`, ending in `Done`, and every tuple as `Tupled(items)`. A declaration or a program stays what it is |
| `block(c)` | The other way. A sequence reads in order from either end: `Then(first, rest)`, or `After(before, last)` |
| `identity(v)` | The hash of `v`'s canonical encoding. Quoted code is a value, and its identity is of the form as written, names included (III.3) |
| `evaluate(c, quote x, v, …)` | The value of the expression `c` with the given bindings, once the checker admits `c`. A step, a declaration or a program is not an expression, and is refused |

```selvage
rule derivative(x: Text) takes Code returns Code
    Literal(c) => Literal(0) where
        discard c
    Name(v) => Literal(d) where
        d is 0
        if v = x
            add 1 to d
        discard v
    Add(u, v) => Add(du, dv) where
        du is derivative(x)(u)
        dv is derivative(x)(v)
    Multiply(u, v) => Add(Multiply(du, v2), Multiply(u2, dv)) where
        u2 is u
        v2 is v
        du is derivative(x)(u)
        dv is derivative(x)(v)
```

The variable is a parameter: the name `x` differentiates to 1, any other name to 0. `derivative("x")(quote x * x + 3 * x)` gives `1 * x + x * 1 + (0 * x + 3 * 1)`, which evaluates to 7 at x = 2, and `derivative("y")(quote x * y + 3 * x)` gives `0 * y + x * 1 + (0 * x + 3 * 0)`. `derivative` is lossy, and rewinding it returns the original code with the same identity.

**Inversion is a rule of the language.** Reversibility and code-as-data meet here. Steps, blocks and clauses are data, so the inverse of code is computed by a clause rule on `Code`. That rule is in the prelude, the checker certifies it like any rule, and it is the definition of inversion: `invert`, `inverse(c)`, `undo` and every derived inverse in the interpreter and in compiled code come from it.

```selvage
rule mirror takes Code returns Code
    Done <-> Done
    Then(step, rest) <-> After(tser, pets) where
        pets is mirror(step)
        tser is mirror(rest)
    After(rest, step) <-> Then(pets, tser) where
        pets is mirror(step)
        tser is mirror(rest)
    Let(p, e) <-> Was(p, e)
    Was(p, e) <-> Let(p, e)
    AddTo(e, t) <-> SubtractFrom(e, t)
    SubtractFrom(e, t) <-> AddTo(e, t)
    Swap(a, b) <-> Swap(a, b)
    Discard(x) <-> Restore(x)
    Restore(x) <-> Discard(x)
    If(c, yes, no) <-> If(c, sey, on) where
        sey is mirror(yes)
        on is mirror(no)
    RepeatWith(i, a, b, body) <-> RepeatDown(i, b, a, ydob) where
        ydob is mirror(body)
    RepeatDown(i, b, a, body) <-> RepeatWith(i, a, b, ydob) where
        ydob is mirror(body)
    Clause(left, right, steps) <-> Clause(right, left, spets) where
        spets is mirror(steps)
    LossyClause(left, right, steps) <-> LossyClause(right, left, spets) where
        spets is mirror(steps)
```

- **One definition.** `invert(c)` is `block(mirror(sequence(c)))`. The toolchain reads the clauses of `mirror` and runs them; it has no table of its own. A realization may run them faster, and must give what they give.
- **A sequence reads from either end.** A block is `Then(first, rest)`, ending in `Done`, or `After(before, last)`. Read from the other end, a sequence has the same steps in the opposite order, and nothing in the block is moved or changed. To invert a block, each step is read backward and the sequence is read from its other end. This is the same idea as one engine reading a rule both ways (VII.1).
- **Certified, on code.** Every clause is `<->`, and the clause test certifies `mirror` as a partial bijection. That is a statement about code as data, and it holds whatever the code does.
- **Loss stays loss.** `mirror` gives a lossy clause back with its `=>`, and reads `discard x` backward as `x was discarded`, which is a form of its own (`Restore`). Mirroring lossy code does not make it reversible:

| | What it is | What establishes it |
|---|---|---|
| Structural inversion | The code of the inverse | `mirror`, for any code |
| Recovery | The earlier state, rebuilt from what was kept | The journal, under the system's authority (VII.1) |
| Certified reversibility | The inverse returns the input with nothing kept | The checker's certificate, `<->` (II.4) |

**`mirror` is an involution.** For every code form c on which `mirror` is defined, mirror(mirror(c)) = c.

*Proof.* `mirror` is certified, so by Part 2 of XI.3 its derived inverse returns c from mirror(c). It remains to show that the derived inverse is `mirror` itself, as a function. The derived inverse has, for each clause `L <-> R where S` of `mirror`, the clause `R <-> L` with the steps of S read backward. For each of these, `mirror` has a clause with the same two sides, whose steps differ only in reading `x is mirror(y)` where the derived clause reads `y was mirror(x)`: this is a fact about the text of the rule, and it is checked (TestMirror). The sides are exclusive, so on any input the two rules take these paired clauses. Their steps apply `mirror`, or its derived inverse, to strictly smaller parts of the input, where the two agree by induction on the size of the input; the steps of one clause act on different parts, so their order does not matter. So the two rules give the same output, and refuse the same inputs. ∎

Which end a sequence is read from does not matter to the result: by induction on the sequence s, block(mirror(s)) is the steps of block(s), each mirrored, in the opposite order. So `invert` is the table of V.6, and `invert(invert(c)) = c`.

- **What `mirror` does not read.** The header of a rule or an answer is not `Code`, and stays so: code is the executable body, and a header names and types a declaration. `invert` flips its name and exchanges the types it takes and returns. A header is still a form: it is the head of a `Declaration`, which a rule takes apart (VIII.1).
- **Authority is unchanged.** The mirror of lossy code is code anyone may hold; running `x was discarded` still needs the system's authority (VIII.3).

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Inversion defined by the certified prelude rule `mirror`, which `invert` runs | Built | Ratified | TestMirror.test_the_inverter_is_a_certified_rule_of_the_prelude, test_invert_has_no_table_but_the_rule; TestInversion |
| `mirror` an involution | Built | Ratified | Proof, for the model of XI.3; TestMirror.test_mirror_is_its_own_inverse_clause_for_clause |
| The rule run by the interpreter, the clauses run by `invert`, and an independent table agreeing on every clause, certified or lossy | Built | Ratified | TestMirror.test_it_inverts_every_clause_certified_or_lossy_as_the_independent_table_does; the model generator (XI.2) |
| Blocks as sequences read from either end; `sequence` and `block` | Built | Ratified | TestMirror.test_a_sequence_reads_from_either_end |
| `x was discarded` as a form of its own | Built | Ratified | TestMirror.test_the_inverter_is_a_certified_rule_of_the_prelude; TestJournalContract |
| The header of a rule or an answer outside `Code`, inverted by `invert` itself | Built | Ratified | TestInversion.test_invert_is_an_involution |

### VIII.3 Authority over code

| Act | Who may | Implementation | Design | Evidence |
|---|---|---|---|---|
| Quote, inspect, transform, invert, hash, print | Anyone | Built | Ratified | TestSurface.test_quoted_code_is_data; TestInversion |
| `evaluate`: run constructed code | Anyone, once the checker admits it, afresh on each call: typed against its bindings, with no request, message, decision or consuming call | Built | Proposed | TestInversion.test_authority_stays_outside_the_code |
| `install`: put admitted code into a running program, keeping the replaced version in the journal | A slot's κ admission policy | Specified | Proposed | — |

An inverse, a code representation or a recorded decision confers no execution or installation authority. The roles stay apart: `mirror` says what the inverse of code is, the checker certifies, the journal retains, `install` changes the running program, κ admits a change, and `commit` ends what can be rewound. κ does not decide whether a transformation is reversible. Reading the κ of `install` as a realization of RME-7's κ is a candidate correspondence, not an identity.

Selvage's code is a tree, so a rule takes it apart one shape per clause; Io's code is a chain of messages to previous results.

---

## IX. Realization and Systems Programming

### IX.1 Realizations

| Realization | What it is | Implementation | Design | Evidence |
|---|---|---|---|---|
| Interpreter | The Python reference implementation, covering the most of the language; one forward engine runs rules, derived inverses, answers and decisions; the journal is Root's state | Built | Proposed | Every test class but TestC23Backend |
| REPL | `selvage repl`: declarations, statements and expressions in one live scope, checked before they run | Built | Proposed | TestMaybe.test_repl |
| C23 backend | `selvage build`: clang `-std=c23 -O2`. Fixed-width integers, `Bit`, `Bool`, `Trit`, `F64`, text output, tuples, records, variants, arrays, both kinds of rule, `_inv` functions compiled forward from the derived inverse, the journal and `decide` | Partial | Proposed | TestC23Backend: output and ε identical to the interpreter |
| Tools | `selvage invert FILE NAME` prints a derived inverse; `selvage lineage FILE [NAME…] [--verify]` prints the chain to `ccnot` | Built | Proposed | TestInversion.test_lineage_reaches_ccnot_from_every_rule, test_inverse_passes_the_ordinary_checker_as_source |
| Reversible and quantum profiles | Certified rules on finite shapes lowered to gate circuits or reversible oracles (IX.4); `selvage circuit FILE RULE INPUT` lays one out | Partial (reversible); Absent (quantum), apart from the `Measure` group, which nothing answers (VII.4) | Ratified | TestReversibleProfile; the circuits generator (XI.2); TestMeasure |

### IX.2 C23 coverage

| Area | Implementation |
|---|---|
| Expression and clause rules, words, `F64`, `Trit`, tuples, records, variants, arrays | Built |
| Derived inverses of certified rules | Built |
| Lossy rules: entries pushed to the journal, ε counted | Built |
| `decide` with world deciders `refuse`, `true`, `false`, `command:` | Built |
| Procedures: a reply the world gives is pushed to the journal and counted in ε | Built |
| Refusals: Root's answer only, status 70 | Built |
| A run that goes too deep, refused | Built: at the bound the program was built with, status 70, as in the interpreter (III.5) |
| `commit` | Built |
| Journal entries naming the code that kept them | Deferred until compiled code rewinds or answers `history`; it keeps values and their bit counts. The identities will be the interpreter's (VII.3) |
| Answers, `ask`, `->`, `with` (so a refusal taken by an installed answer), quoted code, recursive data, rewind | Absent |
| Freeing arrays at scope end | Partial |

### IX.3 C23 competitiveness

Selvage seeks to produce systems code competitive with C23 in speed, memory control, layout, interoperability and deployment. Each dimension is held to evidence on its own.

| Dimension | Objective | Implementation | Design | Evidence |
|---|---|---|---|---|
| Performance | Competitive generated machine code | Built | Ratified | Benchmarks (IX.5) |
| Memory and layout | Explicit representation; predictable allocation and lifetime; C-compatible structures | Partial | Ratified | Records and tuples are C structs; scope-end freeing incomplete |
| Interoperability | C ABI and FFI in both directions | Absent | Ratified | — |
| Systems control | Atomics, low-level access, hardware interaction; explicit safe and unsafe boundaries | Absent | Ratified | — |
| Deployment | Freestanding compilation with no mandatory general-purpose runtime | Absent | Ratified | The runtime header uses hosted stdio, and `popen` for deciders |
| Request lowering | A statically resolved request compiles to a direct call; a dynamic one costs explicit dispatch | Absent | Ratified | Answers are interpreter-only |
| Reversible operations | Inverses and kept losses without unnecessary overhead | Built | Ratified | Benchmarks; proved uncomputes compile to nothing |

### IX.4 Realization profiles

| Profile | Execution model | `ccnot` role | Implementation | Design | Evidence |
|---|---|---|---|---|---|
| Classical | C23 on a CPU: native machine instructions | Not used; lineage only | Built | Ratified | TestC23Backend; benchmarks (IX.5) |
| Reversible | Certified finite-shape rules lowered to X, CNOT and CCNOT circuits, with explicit uncomputation | The primitive gate | Partial: rules over bits whose words are layout | Ratified | TestReversibleProfile; the circuits generator (XI.2); gate rules and realization checks in the prelude |
| Quantum | Certified finite-shape rules realized as reversible oracles; quantum-specific operations through a separate interface | A native or synthesized gate | Absent: only the request group `Measure`, which nothing answers (VII.4) | Ratified | TestMeasure; the measure generator (XI.2) |

**What is built of the reversible profile.** `selvage/circuit.py` lays out a certified clause rule as X, CNOT and CCNOT gates, and `selvage circuit FILE RULE INPUT` prints it.
- *Bits are wires; words are layout.* Every `Bit` of the input is a wire. Every word is known when the circuit is laid out, and the circuit holds for every input whose words have those values. It is a circuit for those words, not for the rule at every word. Index arithmetic and loop bounds are worked out at layout, with the interpreter's own arithmetic.
- *What it lays out.*
  - `add x * y to z`, `add x to z` and `add 1 to z` on bits are a CCNOT, a CNOT and an X. A constant factor folds.
  - A call of `ccnot`, or of its derived inverse, is the gate.
  - Other certified rules are laid out in place.
  - A copy into a fresh name is a fresh wire and a CNOT. A fresh array of bits is fresh wires at 0.
  - A swap relabels wires and lays out no gate.
  - Loops and conditions on words are unrolled or decided at layout.
  - An uncompute undoes its copy, and gives the wire back, which must then be 0.
- *What it refuses, with the reason:*
  - a rule that is not certified;
  - a rule with no bit on a wire, which computes on words only: word arithmetic as gates would need adder circuits this profile does not lay out, so `orbit` and `prefix_sum` are refused;
  - a word computed from a bit;
  - a condition, an index or a clause choice that reads a bit;
  - messages, decisions and any other step outside the list above.
- *How a circuit is checked.* By classical simulation, which is exact for X, CNOT and CCNOT, since they permute basis states. Run forward, it must give what the interpreter gives, and refuse where the interpreter refuses. Run backward from its output, it must give its input back. The derived inverse, laid out on its own, must give the input back too. Every wire given back must be 0 where it is given back, and no wire may be left neither output nor given back.
- *Embeddings.* An ancilla may become an output, as a draw's bit or a child's cells do. A circuit run backward from an output it does not give ends with such a wire at 1, and refuses it, as `undo` does.
- *What it is not.* Nothing here runs on reversible or quantum hardware. A rule the profile lays out is eligible to be realized as a reversible oracle on such hardware; no backend for it exists. That a rule is certified does not make it lowerable: the refusals above are certified rules.

Gate counts, counted from the laid-out circuits (they are not timings):

| Rule | Laid out as | Ancillas |
|---|---|---|
| `tape_tick` | 2 CCNOT | none |
| `draw` | 2 CCNOT, 1 CNOT | 1, which becomes the bit drawn |
| `birth`, tapes of m and n cells | 2(m + n) CCNOT, m + n CNOT | m + n, which become the child's cells |
| 104 ticks of tapes of 8 and 13 cells from heads 0, one alignment | 208 CCNOT | none |
| `ripple_add` at width w | 2w CCNOT, 4w CNOT (laid out at widths 1 to 8) | none |
| `and_into`, `or_into`, `nand_into` (`examples/gates.selv`) | 1 CCNOT; 1 CCNOT and 5 X; 1 CCNOT and 1 X | 1 each, which becomes the result |

**The bridge, and its conditions.**
- A bijection on a finite state space is a permutation, and its permutation matrix is unitary. A certified rule on finite shapes is therefore a reversible oracle.
- A certified partial bijection extends to a permutation only when its domain and codomain are subsets of one finite ambient space whose complements have equal cardinality. A backend that needs this must specify the extension or the embedding it uses.
- "No garbage" is an obligation on the elaborated circuit: each explicit uncompute must actually return every scratch register to its initial state. It is a circuit-correctness obligation, not something a clause certificate guarantees by existing.

**Outside the kernel.** Superposition, phase operations, measurement and qubit management belong to a separately specified quantum realization interface. They are not part of Form, Rule or Request, and the three-mechanism kernel is unchanged. Measurement and reset are given their semantics in VII.4. Of the interface, only the request group `Measure` is declared, and nothing answers it (VII.4).

**Two limits a quantum profile must state,** because the classical language does not carry them over:
- **The journal cannot keep a qubit.** Every loss in a classical run is kept by Root (VII.2), and that is what lets a lossy run be rewound. Keeping what a discard of a qubit drops, or the state a qubit had before it was measured, would be cloning an unknown quantum state, which no operation does. So `discard`, which journals what it drops, does not apply to qubits; a measurement keeps its classical outcome and nothing of the state before it; and rewinding past a measurement or a reset is impossible in principle. Replay reproduces the recorded outcome, not the amplitudes (VII.4).
- **Births do not generalize.** A birth (VI.6) adds each bit the parent's tape shows into a fresh cell of the child, by a CNOT, and the reversible profile lays it out so. On basis states the child's cells are copies. On a parent in superposition the same gates entangle the child with the parent instead: no circuit gives an independent copy of an unknown quantum state. A birth is a valid reversible oracle; it is not a way to copy a quantum tape.

**Boundary.** A profile is a backend choice, not a dependency of every program. A classical backend never simulates a circuit because a transformation is reversible; it lowers the certified transformation to native instructions. The classical language remains classical unless a quantum realization is explicitly selected.

### IX.5 Measurements

These are historical measurements, reproducible with `bench/run.py` and `bench/io/run.py`; they are not guarantees of toolchain 0.4.7 or of the language. The table below was measured with toolchain 0.4.2; for these programs 0.4.3 emits the same C. The comparison with Io below was measured with 0.3.2, by a scaling method whose limits are stated there.

Seven benchmarks were written three ways, and every version prints the same results. Selvage and C23 are compiled with clang 18 `-std=c23 -O2`, Rust with rustc 1.97 `opt-level=2`. Times are medians of five runs on 2-core x86_64.

| Benchmark | Category | Selvage → C23 | C23 | Rust | vs C23 | vs Rust |
|---|---|---:|---:|---:|---:|---:|
| fib(38) | Ordinary | 0.140 s | 0.110 s | 0.123 s | 1.27 | 1.13 |
| collatz to 3M | Ordinary | 0.529 s | 0.530 s | 0.571 s | 1.00 | 0.93 |
| sieve to 50M | Ordinary | 0.435 s | 0.412 s | 0.390 s | 1.06 | 1.12 |
| n-body | Ordinary | 0.588 s | 0.601 s | 0.535 s | 0.98 | 1.10 |
| prefix sum + derived inverse | Reversible | 0.348 s | 0.284 s | 0.300 s | 1.23 | 1.16 |
| orbit + derived inverse | Reversible | 0.840 s | 0.705 s | 0.828 s | 1.19 | 1.01 |
| damped orbit, losses kept | Lossy | 0.536 s | 0.464 s | 0.536 s | 1.16 | 1.00 |
| **geometric mean** | | | | | **1.12** | **1.06** |

Selvage pays for its guarantees: it wraps where C's signed overflow is undefined, checks every index, bounds the depth of a run, and derives the inverses that C and Rust write by hand. On these programs it is within 27% of C23 on each, and 12% in the geometric mean.

**The cost of the depth bound.** Each rule receives the depth as an argument and compares it with the bound (III.5). Timed alternately with 0.4.1's compiled code on the same machine, over nine runs each, the bound costs 1.48× on `fib`, whose time is almost all calls, and within 2% on the other six; 1.06 in the geometric mean. On that machine the same 0.4.1 code measured 1.05 against C23 in the geometric mean, where an earlier session had measured 1.02: the C23 and Rust times themselves vary between sessions by up to half, so ratios measured together are what to compare.

**Against Io.** Io is measured at version 20260302, the final native build, tag `2026.04.20-native-final`. Io's numbers are doubles, so the programs are sized to keep every value exact, and all implementations print the same answers. Io's start-up time is subtracted. Compiled Selvage was run at about 100× the work and scaled down, with corrections for longer collatz chains and the sieve's n log log n growth; the scaling is the part of this method that most needs scrutiny.

| Benchmark | Io | Selvage → C23, same work | Compiled vs Io | Selvage interpreter vs Io |
|---|---:|---:|---:|---:|
| fib(28) | 0.288 s | 0.89 ms | 323× faster | 20.2× slower |
| collatz to 30,000 | 1.637 s | 3.41 ms | 480× faster | 15.5× slower |
| sieve to 300,000 | 0.663 s | 1.48 ms | 449× faster | 6.2× slower |
| prefix sum + derived inverse, 100k × 3 | 1.417 s | 1.47 ms | 967× faster | 3.4× slower |
| orbit, 100k steps + derived inverse | 0.405 s | 0.88 ms | 460× faster | 6.5× slower |
| n-body, 20k steps | 1.512 s | 1.22 ms | 1,243× faster | 7.0× slower |
| **geometric mean** | | | **581× faster** | **8.2× slower** |

The 581× is a property of these compiled programs, not of Selvage in general; Selvage's own interpreter is slower than Io's. This comparison was measured with toolchain 0.3.2, before the depth bound, which makes compiled `fib` about 1.5 times slower.

**Io's strengths, and where Selvage stands:**

| Io strength | Selvage counterpart | Implementation | Design |
|---|---|---|---|
| A live system: a REPL; inspect and change at the prompt | `selvage repl`, checked before it runs | Built | Proposed |
| Prototypes and delegation | Answers that delegate to the instance they hold (VI.3) | Built | Ratified |
| Resumable exceptions (`signal`, `withHandler`) | Answers that resume with a reply, certified both ways and rewindable | Built | Proposed |
| Code as message objects | `Code` forms, including steps and whole rules; inverses as code | Built | Proposed |
| User-defined control flow through lazy arguments | Notation: a certified rule on code forms, expanded when the program is built, invertible so errors point at the text as written | Specified | Proposed |
| Actors, futures, coroutines | Concurrent actors built on answer instances: a scheduler answer, mailboxes, linear continuations, seeded replay | Specified | Open |
| Changing a running system | `install` under κ (VIII.3) | Specified | Proposed |
| Universal message passing, even for arithmetic | Not adopted: arithmetic is certified updates, which keeps `ccnot`'s discipline and C23 speed | — | Proposed |

---

## X. RME-7 Integration

RME-7 shapes the libraries and the conformance tests, not the kernel. Mapping RME-7 offices one-to-one onto language features would overclaim. The split between conservative and dissipative transformation is an invariant of the language itself (II.5); the mathematics of a domain belongs to a library. Symbolic differentiation is such a library rule over forms, and not a kernel operation.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| The conservative/dissipative split: in `examples/orbit.selv` the leapfrog flow is certified and `undo` runs it back exactly; friction is declared loss, metered by ε at 64 bits a step | Built | Ratified | TestReversibility.test_undo_round_trips, test_rewind_lossy_rules, test_epsilon_counts_pruned_bits |
| Symbolic differentiation as a rule on code forms (VIII.2), the route to dH and dΦ | Built | Ratified | TestPrograms.test_interpreter_outputs (derivative) |
| The RME-7 prelude | Specified | Proposed | — |

**The RME-7 state-space form.** The library is written against this form, in Stratonovich convention (∘):

```
dX = [ J♯dH − G♯dH − G̃♯dΦ + F_X ] dt + Σ ∘ dW
dθ = F_θ(X, θ, Φ, κ, Ψ) dt
```

| Symbol | Is |
|---|---|
| X | The state variable |
| θ | The parameter state |
| J♯ | The Hamiltonian, conservative contribution |
| G♯ | The convergent contribution; the only G-operator designated convergent |
| G̃♯ = ωσ⁻¹ | The confinement contribution |
| F_X | Additional state-space forcing |
| Σ ∘ dW | The Stratonovich stochastic term |
| F_θ | The evolution of the parameter state |
| κ | An argument of F_θ, not an operator |
| γ | Derived, not an independent primitive |

**The RME-7 prelude** realizes the form as library types and rules:
- **Points and fibres.** Tangent and cotangent values carry their base point; operations on two fibres need the same base point.
- **Dimensions.** Records of rational exponents, normalized by a certified rule set, so equal dimensions have equal canonical forms. A Brownian increment carries Time^(1/2).
- **Operator roles as seals (R5).** J♯ is Conservative, G♯ Convergent and G̃♯ Confinement. Exchanging G♯ and G̃♯ fails to build.
- **The stochastic reading.** The format fixes Stratonovich. A realization declares its scheme: stochastic Heun is accepted; Euler–Maruyama is refused without an explicit drift correction. Noise is a request (`Noise`), separate from `maybe`.
- **γ_RME** is computed as a commutator of bundle maps: map-valued and derived, never a dynamical term.
- **κ** is an explicit argument of F_θ, and separately the admission policy of `install`. Reading the second as a realization of the first is a candidate correspondence, not an identity.
- **The conformance suite:** differential typing; role preservation; dimensional agreement; Brownian scaling; drift as a graph map with an empty discard set; convention; γ and κ; evidence binding; exact substep; rewind; loss accounting.

---

## XI. Verification and Evidence

### XI.1 Kinds of evidence

| Kind | What it is | What it establishes |
|---|---|---|
| Named test | A case of the conformance suite, cited by name (XI.4) | The behaviour on the cases it runs |
| Generated test | Random programs, each checked against a law (XI.2) | The law on what was generated. It is evidence, not proof |
| Static check | A property the checker enforces on every program | That every accepted program has the property, if the checker is sound (XI.3) |
| Runtime observation | A check run on demand against the running implementation (`lineage --verify`) | Agreement on the cases run |
| Proof | A proof stated in this description | The theorem, within its assumptions and scope. There is one: the soundness theorem, for the model of XI.3 |
| Theorem | A published result, cited (Bennett, Toffoli) | That a construction exists; not that this toolchain performs it |
| Benchmark | A reproducible measurement (IX.5) | A measured ratio on the listed programs |

Tests, proofs and implementation status are separate claims. A feature that is Built and tested is not thereby proven, and the examples, the normative rules and the toolchain's behaviour may not contradict one another (XI.6).

### XI.2 The inversion laws and generated rules

**The inversion laws** are checked by TestInversion on every rule and answer in the prelude and the examples:
- `invert(invert(r)) = r`;
- `parse(print(invert(r))) = invert(r)`, with equal identities;
- the inverse that runs is exactly `invert` of the code that runs;
- the printed inverse, appended to its program as plain source, passes the ordinary checker with the same class;
- running a rule and then its inverse restores state, journal and every installed answer;
- the elaborated code leaves nothing implicit.

**Generated certified rules.** `tests/roundtrip_gen.py` writes random clause rules over arrays and words: updates, swaps, temporaries, branches and loops, with indices that read the state. For each rule the checker certifies, it checks on random inputs that `undo` of the output is the input, that no two inputs share an output, and that a value the inverse accepts is one the rule produces.

| Toolchain | Rules generated | Certified and checked | Findings |
|---|---:|---:|---:|
| 0.3.2 | 1,500 | 698 | 149 |
| 0.3.3 and 0.3.4 | 11,500 | 4,093 | 0 |
| 0.4.0 | 3,000 | 1,099 | 0 |
| 0.4.1 | 3,000 | 1,052 | 0 |
| 0.4.2 | 3,000 | 1,081 | 0 |

The 0.3.2 findings are all one defect, an index that reads what its step changes, which R4 now refuses. It had passed all 59 example-based tests.

**Generated programs with an oracle.** `tests/generated_04.py` has one generator for each part of the language listed below. Each generator writes programs together with an oracle: a small model, independent of the checker and the interpreter, that predicts what the checker must accept or refuse and what a run must do. A disagreement is a finding.

| Generator | What it writes | What the oracle predicts | Generated | Findings |
|---|---|---|---|---:|
| Arrows | Clause rules with and without a loss, under each arrow | Which arrow is accepted; the inverse keeps the arrow; `undo` of a lossy rule is refused; a rewind restores the input and the journal exactly; an older run is not rewound first | 600 rules; 1,376 rewinds | 0 |
| Delegation | Families of answers over two groups, their states single instances, tuples and records, chained up to three deep | Who answers each request and through which component; which families are refused as ambiguous; the reply and state after a message, and after taking it back; which installed answer takes an `ask` of either group; the row, group by group | 600 families; 757 messages; 381 asks | 0 |
| Rows | Expression rules that compute, call certified and lossy rules, decide crisp and undecided conditions, commit, message and install certified and lossy answers, and call one another | Each rule's row and whether it is a function; that leaving any group out is refused; the journal's entries after a run, and ε | 1,831 rules; 2,322 rows cut; 1,800 runs | 0 |
| Between runs | A lossy run followed by functions and procedures | Whether the run can still be rewound | 600 sequences | 0 |
| Operators | Expressions over every operator class, in steps and in functions | The lineage links, one for each class used and none for a class not used | 600 rules; 1,837 links | 0 |
| `Any` | Declarations with `Any` in one type position, at any depth | Accepted without it, refused with it | 600 pairs | 0 |
| Refusal | Procedures that refuse by division, index, image or request, under nested answers for `Refusal` and other answers | What is printed, which answer takes each refusal, and whether Root ends the run | 600 programs; 187 refusals taken, 325 runs ended | 0 |
| Seal (adversarial authority) | Programs that try one of 23 routes to what is sealed to Root, with forged journals, varied states and rows: sending `keep`, making, installing, packing or opening a root, answering `System`, re-sealing, redeclaring, reading without `Witness`, taking back, asking through constructed code | That every one is refused, by the rule and with its reason, and not by an accident of the implementation | 600 programs: 549 refused by the checker, 51 in the run | 0 |
| Witness (adversarial disclosure) | Runs that keep secret values, then inner code that asks `history` under hosts it installs itself and hosts installed around it: closed, counting, holding a copy, keeping a record, redacting, and answers for other groups, one of them holding a `Witness` answer. And hosts that give their copy back while trying to keep what they read by each route: their state, a condition, a loop, the journal, another request, a component, a lossy rule | Exactly what inner code reads; that no kept value reaches it past a host that withholds it; each host's state afterwards, counts and copies rewound where a copy was given back; that giving back through a kept record is refused; the journal unchanged unless a record was kept; the inner rule's row; that each host trying to keep what it gives back is refused by the checker, and each host that keeps nothing passes | 600 programs: 333 open, 88 redacted, 151 closed; 831 rows cut; 28 withdrawals refused; 1,050 retaining hosts refused | 0 |
| Depth | Programs whose `main` makes three calls that nest: a clause rule calling itself and its `undo`, mutual recursion, a call inside a tuple, a self tail call, a rule reached through an answer. Each runs at the bound it just fits, one less, one more and one at random | What is printed before the refusal, whether the run is refused, and its reason | 600 programs; 2,231 runs, 1,031 refused | 0 |
| Structures (the theorem) | Clause rules over two words, an answer instance and a variant: updates, swaps, calls and their `undo`, partial bijections, messages sent and taken back, instances opened and packed again, decisions, branches, counted loops with bounds that read the data, and tuples of temporaries given back in their own pattern or in another. About half read what a step changes | Nothing about what the checker accepts. For every rule it certifies, Parts 1 to 3 of XI.3: `undo` returns the input, no two inputs share an output, and a value the inverse accepts is one the rule produces | 600 rules: 295 certified; 2,445 round trips; 1,076 values refused by the inverse | 0 |
| Decisions | Clause rules with one to three decisions, crisp and undecided, among exact and lossy steps, run under stacks of answers for `Decide` that defer, reply true or reply false, with the world settling last. Each run that asked the world is replayed from its own record, and from records with a decision missing, out of order, or in another context | The arrow and the row; the output; the journal's `Decided` entries, with how many answers were asked and whether the world settled, and each charged by the answers installed; each answer's state; that the rewind restores the input, every answer and the journal; that a replay of the run's own record reproduces it, and that every other record is refused | 600 rules; 3,600 runs: 1,015 settled by an answer, 940 by the world; 1,955 decisions charged; 3,600 rewinds; 654 replays, 1,462 wrong records refused | 0 |
| Journal | Five rules: one of three clauses with overlapping right sides, whose clauses drop values themselves or through a helper; one that calls itself; two that call each other. The same program under other names for every rule, under other names for every variable, with clauses in another order and declarations in another order; with a called rule changed; and with a forged entry in the journal | The identity each entry names: the clause that kept it, the same under every renaming, of rules and of variables, and every reordering, level by level through the recursion; that every rule's identity is unchanged by names and by where it is declared; that changing a called rule changes the identity of exactly the code that calls it; who each entry was kept by; that the rewind restores the input; that an entry naming code that is no clause of the rule is refused, and one that differs only in who kept it is not; that code, or rules, sharing an identity are refused and not told apart by it | 600 programs; 2,400 runs, 1,456 of them recursive; 6,991 entries; 588 renamed, 307 with variables renamed, 446 reordered, 596 with declarations moved; 600 callees changed; 5,498 forged entries refused | 0 |
| Names | Certified rules from the round-trip and structures generators, under other names for every variable, and for those bound inside the clause only; the same rules with one use made to refer to another binding. Eleven arrangements of bindings: a name bound again after it was given back, two loops with one counter name, a loop in a loop, which variable is read, a variable twice in a pattern, the sides of a clause, a parameter, two branches with one name, a name bound after a block bound it, a constructor, a quoted name. Nine ways of binding a name that is bound. A program with two requests of one signature and two answers with the same code, under other names for every group, request and answer, and with one reference moved to the twin | That renaming variables leaves the program accepted and every identity as it was; that a use referring to another binding is other code; for each arrangement, which renamings keep the identity and which changes do not; that each rebinding is refused, for that reason; that renaming a group, a request or an answer changes no identity of theirs or of the rules that send, ask and make them; that the twins have identities of their own, and a reference moved to a twin changes exactly the rules that hold it; that a run keeps entries under the same identities, shows its own program's names in `by`, and rewinds | 600 programs: 265 certified rules, every one renamed, 147 with inner bindings renamed alone, 168 with a use changed; 1,650 arrangements; 1,350 rebindings refused; 300 programs renamed, 300 references moved to a twin; 600 runs | 0 |
| Accounting | Lossy and certified rules written as tables of clauses over `Bit`, `Bool`, `Trit`, `Text` and small types with constructors: values, names and constructors with names on the left, some names given back on the right and the rest discarded; copies dropped while what they copy stands, or after it has changed, and then what they copy dropped as well; values made by a constructor and dropped | Its own model of each rule: its own values and matcher, and its own reading of VII.5, deciding which constructors are still possible and which values are still computable by going through every input. For every input: the output, the entries kept and the bits charged, and that the rewind gives the input back. For every output: that the charges of the inputs giving it are the lengths of a code for them. For a run of several inputs: ε, in the interpreter and in compiled code, compiled for every eighth rule and every third that drops a copy | 600 rules, 566 of them lossy; 5,927 runs, 14,557 entries, 123,131 bits; 2,936 choices kept and 2,246 not needed; 50 constructors ruled out; 608 values dropped for nothing; 105 copies dropped after what they copy changed; 1,032 outputs weighed; 116 compiled | 0 |
| Extent | Certified rules over bits, from `ccnot`, `cnot`, NOT and exchange, with ancillas set to constants and wires given back against constants; and rules over words, with additions, multiplications by constants, halvings and divisions by a wire | Over bits, a gate simulator of its own, run on every input, gives the extent of the rule and of its inverse. Over words, what may be claimed from how the rule was put together, and every claim tried: a rule said to take every input is run on values chosen to make it refuse, and a rule said to be onto is run backward on outputs chosen at random | 600 rules: 400 over bits (144 permutations, 148 embeddings, 58 partial inverses, 50 partial), 200 over words (99 not established); 1,989 claims tried | 0 |
| Forms | Programs from five other generators: round-trip rules, structures, tables of clauses, gate and word rules, and procedures with rows. To each, rules written in Selvage that read `program()` and say of every declaration its kind, its name, how many parameters, clauses, constructors or requests it has, and its row or its groups | The same, read off the source as text with no parser. Also: every declaration written as a value and back is the same; the program as a value prints as the program; the census finds nothing escaping and every constructor taken apart and put together; every clause written out whole, mirrored and written back is the clause `invert` gives; a name given back against an expression that reads it is refused | 600 programs, 457 accepted: 1,787 declarations; 457 programs read alike by a rule and from the text; 1,204 clauses mirrored; 2,633 constructors taken apart over 269,969 nodes; 457 self-reading uncomputes refused | 0 |
| Model | Rules the round-trip and structures generators write, where the checker certifies them | The model of XI.3, written out as a second evaluator that shares no code with the interpreter: the forward run, refusals included; `invert` as the model's table; `undo` as the model's inverse; every proved uncompute holding when it is reached | 600 programs: 275 certified rules; 2,750 forward and 2,750 inverse runs; 704 proved uncomputes reached | 0 |
| Tape | Tapes of 2 to 16 cells, random contents and heads; up to 40 draws, a birth in half of them, up to 10 draws from the child | A model of wiring 1 written from its description, sharing no code with the interpreter: every draw, the parent and the child after a birth, the child's draws; every draw and birth taken back restores the tape; a tick and its derived inverse | 600 tapes: 11,771 draws, 291 births, 12,062 taken back, 600 ticks undone | 0 |
| Circuits | Gate rules over bits from the extent generator; the prelude's `exchange`, `fanout` and `ripple_add` at widths 1 to 6; the CCNOT tape's three rules at 2 to 6 cells a tape and random heads | The interpreter, on every input of a gate rule and six random inputs of the others: a circuit gives what the interpreter gives and refuses where it refuses; run backward, it gives its input back; the derived inverse, laid out on its own, gives it back too | 600 of each: 10,816 runs, 14,311 gates laid out, 10,220 inverses laid out, 596 refused alike | 0 |
| Measure | Procedures, one to four deep, that output, ask `measure`, call a clause rule that asks it, and call the next, some of it inside stand-in answers for `Measure` installed with `with`; each program also written with `<->` on the clause rule, and without `Measure` in the row of a rule that reaches it | An oracle that follows the calls: an ask the innermost stand-in takes gets that stand-in's reply, and one nothing takes ends the run at Root, after what was output before, with the reason a request nobody answers is given. The clause rule with `<->` is refused as world input, and a row without `Measure` is refused | 600 programs: 345 asks taken by stand-ins, 456 runs refused at Root and 144 completed; 361 wrong arrows and 544 missing rows refused | 0 |
| Declared types | At each of the sixteen sites where a value meets a declared type, a program that gives a `Trit` where a `Bool` is declared, under fresh names and beside a word, a `Bit` or a `Text`; and the same program with a `Bool` there. `set` to a literal on every word type and `F64`; a literal given as a rule's input and as its parameter; `set` on a `Trit` | That a `Bool` is a sub-shape of `Trit` and not the reverse: the program with a `Trit` refused with its reason and no failure of the toolchain, the program with a `Bool` accepted. A literal is of the declared type and is charged its width; `set` on a `Trit` is charged 2 bits whatever it replaces, and every run rewinds | 600 programs of each kind at all 16 sites: 600 refused, 600 accepted; 600 literals set, 1,130 literals given as words, 600 `Trit`s set; 2,400 rewinds | 0 |

**The mutation check.** Generated tests are only as good as their oracles, so `tools/mutation_check.py` breaks the toolchain one way at a time and runs the generator that should notice. Each of its 153 mutations undoes one piece of the behaviour above: an arrow accepted on the wrong class, an ambiguity resolved silently, `System` inferred from the word `decide`, a world reply not kept, an operator left unlabelled, a sealed request sent, `history` going straight to Root past its host, a copy given back through a kept record, a host keeping what it gives back, a run nesting past its bound or a bound off by one, a self tail call adding depth, answers for `Decide` consulted in the wrong order, an obligation of XI.3 removed, an uncompute proved in another pattern. Seven break inversion, five of them by changing a clause of the rule `mirror` in the prelude: an update or a discard read backward as itself, a counted loop keeping its direction, a loop body left unmirrored, a lossy clause mirrored as a certified one, which the checker itself refuses. Three break replay: a record for another question or another context taken as the answer, a record not used up. Five break the journal's identities: an entry taken back whatever code kept it, a clause chosen backward by its place, an entry kept under the rule's first clause, identities compared without the forms they name. Six break the identity of code: a call holding the name of the rule called, a rule's identity holding its own name, the members of a cycle told apart by name, a changed rule keeping its identity, exclusive clauses taken in the order written, rules sharing an identity unnoticed. Ten break what code refers to: a variable or a parameter identified by its name, a name bound again taken for the same variable, quoted code read as code, a message holding the name of its request, an instance or a type the name of its answer, a row the names of its groups, answers with the same code or requests with the same signature made one. Three break the scope rule: a name bound again where it is bound, a counter taking the name of a parameter or of the loop it is in, a counter taking a bound name in a body. Fourteen break accounting: a clause choice kept whatever the output shows, or counted among all the clauses, or taken back where none was kept; a variant charged for every constructor or sixteen bits; a `Trit` by the value it holds; a value still computable charged, or counted as computable after what it came from changed; a constructor ruled out wrongly, or not ruled out; compiled code charging a choice, a variant or a computable value the old way; a literal in a constructor keeping the type of a literal. Five break the extent report: a rule taken as onto because it takes every input, a refused input passed over, a division or a `was` against a constant taken as unable to refuse, fewer inputs than outputs not noticed. One cites Boolean logic as a theorem again. Nine break the forms: a constructor of `Code` missing from the prelude, a declaration losing its row or exchanging its types on the way to a value, a tuple left as the parser wrote it or its members reversed, `program()` giving the prelude as well, an answer's clauses reversed, a request group losing a request, a name given back against an expression that reads it. Sixteen break declared types: a `Trit` accepted where a `Bool` is declared, at each kind of site in turn and at all at once; a rule that reads backward into a `Bool` ending the check with a failure; `set` leaving a literal at a literal's width, or holding what it replaces in a `Trit` as a `Bool`; a literal keeping its width as a rule's input or parameter. Two break the charge for a `Text`, in each backend; one charges a decision by the answers asked; one gives a value taken back no type, so that compiled code cannot type what the two directions share. All 140 are noticed. Five of them break the CCNOT tape of VI.6: a CCNOT dropped, a CCNOT aimed two cells ahead, a head turned round, a draw observing before its tick, a child started with its head moved. Five break the reversible profile (IX.4): a CNOT laid out with its control and target exchanged, a copy sharing its wire, an uncompute laying out no gate, a constant 0 counted as 1, a loop laid out one pass short. Three break the `Measure` group of VII.4: Root answering it, a request nobody answers given 0, an `ask` in a clause rule taken as no world input.

A generator counts a refused program as a refusal its oracle may have expected, so each first requires the toolchain to accept its own prelude.

**Agreement with the previous toolchains.** On 3,000 generated rules, 0.3.4 and 0.4.0 give the same verdict on every rule, the same refusal text on the 1,923 they refuse (1,310 of them under R4), and the same outputs and `undo` results on the 1,077 they certify. On another 3,000, 0.4.0 and 0.4.1 agree the same way (1,948 refused, 1,339 under R4), and every example prints the same output with the same ε. On 600 round-trip rules, 600 structures rules and every example, 0.4.1 and 0.4.2 agree on all but 36 structures rules. Those are the corrected defect (XII.6): each gives a tuple of temporaries back in another pattern, 0.4.1 certified it and returned a wrong value from `undo` in 171 of 188 runs, and 0.4.2 refuses the false uncompute when it runs. On another 600 of each and every unchanged example, 0.4.2 and 0.4.3, which inverts through `mirror`, agree on every verdict, output and `undo` result. On another 600 of each and every example, 0.4.3 and 0.4.4 agree the same way; the two examples that print the journal differ only in the identities their entries now carry. 0.4.4 and 0.4.5 agree the same way on another 600 of each and every example; calls resolved to identities change no verdict and no output on them. 0.4.5 and 0.4.6 agree the same way on another 600 of each and every example: no generated rule and no example binds a name twice, and the two examples that print the journal differ only in the identities their entries carry. 0.4.6 and 0.4.7 agree on another 600 of each, verdict for verdict and output for output, and every example prints the same. ε is unchanged on every example but `derivative`, where it falls from 102 to 90: its output shows which clause ran on five of the seven runs that kept a choice, and on the other two the choice is among two clauses, not four. 0.4.7 and 0.4.8 agree on another 600 of each, verdict for verdict and output for output; every example prints the same but `derivative`, which now takes its variable. 0.4.8 and 0.4.9 agree on another 600 of each and on every example, verdict for verdict, output for output and `undo` for `undo`; the eighteen generators of 0.4.8, run unchanged against 0.4.9 at 300 programs each, find nothing. Run against 0.4.8, the generators of 0.4.9 find each corrected defect: the declared-types generator 228 findings, the accounting generator 291 and the decisions generator 63, at 120 programs each.

**Required evidence for G1.**

| Requirement | Implementation | Design |
|---|---|---|
| Generated certified rules: updates, swaps, temporaries, branches, loops | Built | Ratified |
| Generated lossy rules, checked under rewind for state and journal | Built | Ratified |
| Generated messages to answers, sent, taken back and rewound | Built | Ratified |
| Generated decisions: in procedures, settled by the world and by answers | Built | Ratified |
| Generated decisions inside clause rules | Built | Ratified |
| The soundness theorem stated, with its assumptions and scope (XI.3) | Built | Ratified |
| The proof of the theorem, for its model (XI.3) | Built | Ratified |
| The model compared with the interpreter on generated rules | Built | Proposed |
| Every code block of this description examined by the toolchain (XI.6) | Built | Ratified |

### XI.3 The soundness theorem

**Statement.** Let r be a clause rule the checker classes as a bijection or a partial bijection, with its parameters fixed. Consider forward runs of r that end without a refusal.
1. **Injective.** No two inputs give the same output.
2. **Inverted.** If r takes x to y, the derived inverse `invert(r)`, run on y with the same parameters, ends without a refusal and returns x. It keeps nothing, takes nothing back, and leaves every answer it messaged as it was before the forward run.
3. **Refused outside the image.** If y is the output of no input, the derived inverse refuses y.
4. **With the journal.** For any clause rule r, lossy ones included: if r takes state x, installed answers H and journal J to y, H′ and J′, then `invert(r)`, run under the system's authority on y, H′ and J′, returns x, H and J.

Equality throughout is sameness (III.3).

**What is proved, and of what.** The theorem is proved below for a model: a mathematical account of values, patterns, steps and `invert`, given in this section. It is a written proof, not a machine-checked one. Two things connect the model to the toolchain, and neither is proved:
- that the checker establishes the obligations O1 to O6 for every rule it certifies;
- that the interpreter runs each step as the model defines it, and that `invert` is the model's table.

Both rest on tests. For the second, the model is written out as a second evaluator, sharing no code with the interpreter, and the two are compared on generated rules (XI.2).

**The model.**

- **Values** are words, floats, Booleans, trits, text, tuples, forms, arrays and instances, taken in canonical form, so that equal values are the same value. A value is a tree: no part of it is shared with another value (III.2).
- **A state** σ is a finite map from names to values: the names a clause owns at that moment, called live. The rule's parameters π are a second map, which no step changes. A loop counter is a parameter of the loop's body.
- **An expression** e in a step is pure: it holds no request, no decision and no consuming call, and an expression rule it calls is a function (V.3). Its value ⟦e⟧σ is determined by π and by the values σ gives the names e reads. It may be a refusal, written ⊥, as every partial operation below may.
- **A pattern** p is linear: each name occurs in it once. match(p, v) is the map on p's names under which p reads v, or ⊥ when v has not p's shape. build(p, σ) is the value p reads under σ. They undo each other:

    (M)  build(p, match(p, v)) = v whenever match(p, v) ≠ ⊥,  and  match(p, build(p, β)) = β for every map β on p's names.

- **A step** s denotes a partial function F<sub>s</sub> on states. Writing σ∖p for σ without p's names:

| Step s | F<sub>s</sub>(σ) |
|---|---|
| `p is e` | σ ∪ match(p, ⟦e⟧σ) |
| `p was e` | σ∖p, provided build(p, σ) = ⟦e⟧(σ∖p); otherwise ⊥. Where the checker marked the step proved, the comparison is not made (O5) |
| `add e to t`, `subtract e from t` | σ with the cell t holding σ(t) ± ⟦e⟧σ, in ℤ/2ⁿ. The cell is a name, an element `a[i]` or a field |
| `swap t and u` | σ with the two cells exchanged |
| `p is g(k)(x)` | (σ∖x) ∪ match(p, G<sub>κ</sub>(build(x, σ))), where κ = ⟦k⟧σ and G is the function of rule g |
| `p was g(k)(x)` | (σ∖p) ∪ match(x, G⁻<sub>κ</sub>(build(p, σ))), where G⁻ is the function of `invert(g)`. `undo g` exchanges g and `invert(g)` in these two rows |
| `r is t -> op(a)` | With (ρ, s′) = A(op(⟦a⟧σ), s), where s is the state of the instance σ(t) and A the function of the rule that answers `op` for it: σ with t's state s′, and match(r, ρ) added. Under delegation A acts on the component and leaves the rest of the state as it was |
| `r was t -> op(a)` | With (q, s) = A⁻(build(r, σ), s′): σ∖r with t's state s, provided q = op(⟦a⟧(σ∖r)); otherwise ⊥ |
| `i is A(k) from p` | (σ∖p) ∪ {i ↦ the instance of A with parameters ⟦k⟧σ and state build(p, σ)} |
| `i was A(k) from p` | (σ∖i) ∪ match(p, v), provided σ(i) is an instance of A with parameters ⟦k⟧σ and state v; otherwise ⊥ |
| `d is decide e`, `d was decide e`, e a `Bool` | As `d is e` and `d was e` |
| `if c` A `otherwise` B | F<sub>A</sub>(σ) when ⟦c⟧σ is true, F<sub>B</sub>(σ) when it is false |
| `repeat with i from a to b` A | With α = ⟦a⟧σ and β = ⟦b⟧σ: F<sub>A</sub> applied with i = α, α+1, …, β in turn. `from b down to a` applies it with i = β, …, α |

- **A block** S = s₁ … s<sub>n</sub> denotes F<sub>S</sub> = F<sub>s<sub>n</sub></sub> ∘ … ∘ F<sub>s₁</sub>.
- **A clause** `L <-> R where S` denotes C(x) = build(R, F<sub>S</sub>(match(L, x))). **A rule** with clauses C₁ … C<sub>m</sub> denotes G(x) = C<sub>k</sub>(x) for the first k whose left side matches x, and ⊥ if none does.
- **`invert`** is the table of V.6: it reverses each block, replaces each step by its backward reading, and exchanges the sides of each clause. Written s̄ for a step and S̄ for a block, S̄ = s̄<sub>n</sub> … s̄₁. Applied twice it gives the code back.

**What the checker establishes.** A step *writes* the names it binds, consumes or updates; writing an element of an array, or the state of an instance, writes the array or the instance. For a rule the checker certifies, and for its derived inverse, which the checker checks as it checks any rule:

| | Obligation | Where stated |
|---|---|---|
| O1 | Every expression in a step is pure, and every step is one of the forms in the table above: none discards, overwrites, rounds, asks, decides a `Trit`, or calls or messages a lossy rule | II.4 (R2), V.6 |
| O2 | A step binds only names that are not live, or that the same step consumes. Every name bound is consumed exactly once. A block leaves live exactly the names it found; the two branches of an `if` consume the same names | II.4 (R3) |
| O3 | In an update, neither the amount nor an index of the target reads the cell the step changes; where two elements of one array cannot be told apart beforehand, the step compares their indices when it runs and refuses if they are equal. A parameter of a call reads no name the call consumes; an argument of a message does not read the instance; a parameter of an instance reads no name of its state | II.4 (R4) |
| O4 | The branches of an `if` write no name its condition reads. A loop's body writes no name its count or bounds read, and not its counter | V.6 |
| O5 | A `was` marked proved follows, in the same block, an `is` of the same pattern and the same expression, and no step between them writes a name of the pattern or a name the expression reads | V.5 |
| O6 | No value matches the left sides of two clauses, and none matches the right sides of two | II.4 (R2) |

**Lemma 1 (frame).** If F<sub>s</sub>(σ) = σ′ then σ and σ′ agree on every name s does not write, and ⟦e⟧σ′ = ⟦e⟧σ for every expression e that reads no name s writes. The same holds for a block.

*Proof.* Each row of the table changes σ only at names the step binds, consumes or updates; a call or a message changes only what it consumes, binds or addresses, since values share nothing. An expression's value is determined by the names it reads. For a block, by induction on its length. ∎

**Lemma 2 (step) and Lemma 3 (block).** Let the code satisfy O1 to O5. If F<sub>s</sub>(σ) = σ′ ≠ ⊥ then F<sub>s̄</sub>(σ′) = σ; and if F<sub>S</sub>(σ) = σ′ ≠ ⊥ then F<sub>S̄</sub>(σ′) = σ.

*Proof.* By induction on the length of the run, so that Part 2 may be assumed for every rule called or messaged inside it, and within that on the structure of the code. Lemma 3 follows from Lemma 2 by induction on n: F<sub>S̄</sub> ∘ F<sub>S</sub> = F<sub>s̄₁</sub> ∘ … ∘ (F<sub>s̄<sub>n</sub></sub> ∘ F<sub>s<sub>n</sub></sub>) ∘ … ∘ F<sub>s₁</sub>, and each inner pair is the identity where it is defined. Lemma 2, case by case:

- **`p is e`.** σ′ = σ ∪ match(p, v) with v = ⟦e⟧σ. By O2 p's names are not live in σ, so e does not read them, and ⟦e⟧(σ′∖p) = ⟦e⟧σ = v. By (M), build(p, σ′) = v. So `p was e` makes its comparison, finds it true, and gives σ′∖p = σ.
- **`p was e`.** σ′ = σ∖p, and build(p, σ) = ⟦e⟧σ′: the step compared them, or it was marked proved. In the second case, by O5 an earlier `p is e` in the same block made them equal, by the case above, and by Lemma 1 every step between kept them equal, since none wrote a name of p or a name e reads. Then `p is e` gives σ′ ∪ match(p, ⟦e⟧σ′) = σ′ ∪ match(p, build(p, σ)) = σ, by (M).
- **`add e to t`.** By O3 the amount and the indices of t do not read the cell changed, so in σ′ the same cell is selected and e has the same value v (Lemma 1). Subtracting gives (σ(t) + v) − v = σ(t) in ℤ/2ⁿ. `subtract` is the same.
- **`swap t and u`.** By O3 the same two cells are selected in σ′, and exchanging them again restores σ.
- **`p is g(k)(x)`.** Let κ = ⟦k⟧σ and y = G<sub>κ</sub>(build(x, σ)), so σ′ = (σ∖x) ∪ match(p, y). By O3 k reads no name of x, and by O2 no name of p that is not a name of x; so k reads only names the step does not write, and ⟦k⟧σ′ = κ (Lemma 1). By (M) build(p, σ′) = y. The run of g is shorter, so Part 2 gives G⁻<sub>κ</sub>(y) = build(x, σ). By O2 p's names are not live in σ∖x, so σ′∖p = σ∖x, and by (M) the result is (σ∖x) ∪ match(x, build(x, σ)) = σ.
- **`p was g(k)(x)`.** The same argument with g and `invert(g)` exchanged. `invert(g)` satisfies the obligations, being checked like any rule, and its inverse is g; so Part 2, applied to `invert(g)`, gives G<sub>κ</sub>(G⁻<sub>κ</sub>(v)) = v.
- **A message, and a message taken back.** As the two cases above, with the rule that answers `op` in place of g. By O3 the arguments do not read the instance, and by O2 they do not read the reply's names, so they have the same value on the way back, and the request recovered by A⁻ is compared with the one sent and found equal. Under delegation the same holds of the component, and the rest of the instance's state was never changed.
- **`i is A(k) from p` and `i was A(k) from p`.** By O3 the parameters have the same value before and after. By (M), unpacking the instance just packed gives back p's names, and packing what was just unpacked gives back the instance.
- **`decide` on a `Bool`.** As `p is e` and `p was e`.
- **`if c` A `otherwise` B.** Say ⟦c⟧σ is true, so σ′ = F<sub>A</sub>(σ). By O4 A writes no name c reads, so ⟦c⟧σ′ is true (Lemma 1) and the inverse runs Ā. A is a smaller block, so F<sub>Ā</sub>(σ′) = σ.
- **`repeat with i from a to b` A.** By O4 the bounds are the same in σ′, and the body does not write i. The inverse runs Ā with i = β, …, α: each undoes the forward iteration with the same i, last first. ∎

**Proof of Part 2.** Let G(x) = y through clause k: β = match(L<sub>k</sub>, x), σ₁ = F<sub>S<sub>k</sub></sub>(β), y = build(R<sub>k</sub>, σ₁). By O2 the names live in σ₁ are exactly those of R<sub>k</sub>. The clauses of `invert(r)` are `R_j <-> L_j where S̄_j`. By (M), match(R<sub>k</sub>, y) = σ₁, and by O6 no other right side matches y, so the inverse runs clause k. By Lemma 3, F<sub>S̄<sub>k</sub></sub>(σ₁) = β, and by (M) build(L<sub>k</sub>, β) = x. So G⁻(y) = x. By O1 no step of either run keeps anything or takes anything back. An answer the run messaged is an instance held in the state, and the state was restored. ∎

**Proof of Part 1.** If G(x) = G(x′) = y, then by Part 2 x = G⁻(y) = x′. ∎

**Proof of Part 3.** Suppose G⁻(y) = x ≠ ⊥. `invert(r)` satisfies O1 to O6, and its inverse is r. Part 2, applied to `invert(r)`, gives G(x) = y. So a y that is the output of no input is refused. ∎

**The journal (Part 4).** The state is extended to (σ, H, J): H is the list of installed answers, innermost first, and J the journal, newest entry first. The steps a lossy rule adds:

| Step | Forward | Backward, under the system's authority |
|---|---|---|
| `discard x` | Removes x and puts `Dropped(c, σ(x))` on J, c naming the clause that runs | `x was discarded`: takes `Dropped(c, v)` off J and binds x to v |
| `p is ask op(a)` | The nearest instance in H that answers `op` answers it by its rule A, which may put entries on J; p is bound to the reply | `p was ask op(a)`: A⁻ runs on the reply and that instance's state, and the request it recovers is compared with the one sent |
| `d is decide e`, e a `Trit` | If ⟦e⟧σ is true or false, d is bound to it and nothing else happens. If it is `maybe`, `settle` goes to the answers for `Decide` in H, innermost first, until one replies true or false; if none does, the world replies. Then `Decided(c, m, w)` is put on J, m being the number of answers asked and w whether the world settled it, and d is bound to the reply | `d was decide e`: d is removed. If ⟦e⟧σ is true or false it is compared with d. Otherwise `Decided(c, m, w)` is taken off J and `settle` is taken back from the first m answers for `Decide`, last asked first, each with the reply it gave |
| A clause chosen where sides overlap | After the clause's steps, with y the output: if y matches the right side of one clause, nothing. Otherwise `Chose(c, m)` is put on J, c naming the clause and m counting the clauses whose right side y matches | If y matches the left side of one clause of the inverse, that clause runs. Otherwise the inverse takes `Chose` off first and runs the clause that is the mirror of c |

An entry names a clause by the identity of its code (VII.3); who it was kept by is left out here, since nothing goes by it. `set` and a rounding update are elaborated into an exchange and a `discard` (V.5). A call or a message to a lossy rule acts as in the model above, on the journal as well.

**Lemma 4.** Let the code satisfy O1 without its restriction to certified forms, and O2 to O5. If a step s takes (σ, H, J) to (σ′, H′, J′), then J′ = Δ·J for some entries Δ, the step having only added to the journal; and s̄, run under the system's authority on (σ′, H′, Δ·J), gives (σ, H, J). The same holds for a block.

*Proof.* As Lemmas 2 and 3, by induction on the length of the run, now assuming Part 4 for every rule called, messaged or asked. A step of the certified forms leaves H and J alone when what it calls or messages is certified; when that is lossy, Part 4 for it gives the claim. For a block with steps adding Δ₁, …, Δ<sub>n</sub> in turn, J′ = Δ<sub>n</sub> ⋯ Δ₁·J, and S̄ runs s̄<sub>n</sub> first, which removes Δ<sub>n</sub>: the journal is used as a stack. The new cases:
- **`discard x`.** Immediate from the table.
- **`ask`.** By assumption H holds the same answers in the same order on the way back, and which instance answers `op` depends on what the answers are, not on their states; so the same instance is found. Part 4 for its rule removes what that rule added, restores its state and returns the request, which is equal to the one sent because the arguments read nothing the step writes.
- **`decide`.** d is not live before the step, so e does not read it, and ⟦e⟧ has the same value on the way back. If that value is true or false, the step is `d is e`. If it is `maybe`: the first m answers for `Decide` are the same m (assumption), the question and its context are recomputed from the same expression and the same values, and each answer gave `maybe` except the last asked, which gave the reply unless the world settled it. Taking `settle` back from each, last first, removes its entries and restores its state, by Part 4 for its rule. The world's reply was an input to the forward run; the inverse does not ask for it again.
- **A clause chosen.** The right side of the clause that ran matches its own output y. If no other right side does, the inverse, whose left sides are those right sides, finds exactly one clause that matches y, and it is the mirror of the one that ran; both directions make the same count from the same y, so they agree on whether an entry was kept. Otherwise `Chose` is the newest entry of the run, so the inverse reads it before anything else. It names the clause c that ran; the clauses of the inverse are the mirrors of the rule's clauses, and `mirror` is one-to-one (VIII.2), so exactly the mirror of c is selected, clauses with the same code being the same clause. The inverse then proceeds as in Part 2. ∎

**Proof of Part 4.** As Part 2, with Lemma 4 in place of Lemma 3, and with the clause read from `Chose` where O6 does not hold. ∎

**A rewind is bound to its run.** Part 4 is about the inverse applied to the output of a run, with the journal as that run left it. The system applies it only then: a rewind is refused unless the value offered is the same as the run's output, compared on the canonical form and not on a hash (III.3), and nothing has been kept since the run ended (VII.1). A rewind that is not refused therefore meets the hypotheses of Part 4, and restores the input, the installed answers and the journal.

**Assumptions.**
- The code is the elaborated code (V.5), built from the steps above.
- An expression rule called inside a step is a function (V.3): deterministic, and it ends.
- Values are owned and never shared (III.2), and word arithmetic is in ℤ/2ⁿ.
- The answers installed are the same, in number and order, for a run and for its inverse.
- An identity names one piece of code. A run holds the canonical form behind each identity it uses and refuses a shared one (VII.3), so this is checked, not assumed.

**Scope.** The theorem does not cover:
- runs that do not end, or that the depth bound refuses (R8);
- the C23 backend's agreement with the interpreter, which rests on the agreement tests;
- the faithfulness of gate-level realizations, which rests on lineage and `--verify`;
- procedures, `with`, a refusal taken by an installed answer, concurrency, or constructed code run by `evaluate`.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| The theorem, for the model of this section | Built | Ratified | Proof (this section; written, not machine-checked) |
| The checker establishes O1 to O6 for every rule it certifies | Built | Ratified | Generated rules: 0 findings (XI.2); the mutation check, which removes obligations one at a time; TestSoundness; TestDeclaredTypes.test_no_certified_rule_decides_a_trit. No proof |
| The interpreter runs the model, and `invert` is its table | Built | Ratified | TestGenerated04.test_the_interpreter_and_invert_are_the_model_of_the_proof; TestMirror. No proof for the interpreter; that `mirror` gives the table is proved in VIII.2 |
| Parts 1 to 3, as behaviour of the toolchain | Built | Ratified | TestGenerated04.test_the_theorem_holds_on_rules_that_call_message_and_open; TestSoundness.test_generated_rules_round_trip; TestInversion |
| Part 4, as behaviour of the toolchain | Built | Ratified | TestGenerated04.test_arrows_state_the_certificate_and_lossy_runs_rewind, test_decisions_inside_clause_rules_are_kept_and_rewound, test_an_entry_names_its_code_under_renaming_and_reordering; TestJournalContract; TestSemanticContracts |
| A rewind bound to its run, on the canonical form | Built | Ratified | TestSemanticContracts.test_a_rewind_is_bound_by_the_canonical_form_and_not_by_a_hash; TestGenerated04.test_a_kept_reply_stands_between_runs |

### XI.4 The suite

Toolchain 0.5.0 passes 199 tests. Every test source is in the notation of this description.

| Test class | Tests | Covers |
|---|---:|---|
| TestSurface | 3 | Parsing and printing round trips; layout outside identity; quoted code as data |
| TestCCNOT | 6 | `ccnot`'s table; the gate rules; Bit updates as gates; `ripple_add` against machine addition |
| TestChecker | 9 | Classes of every example rule; refusals (linearity, R4, rows, loss, conditions); the arrow and the certificate; inversion keeping the arrow; derivation for records and delegation for answers; functions and procedures; R6 rows through calls and `with`; `Any`; the run-time alias check |
| TestReversibility | 6 | `undo` round trips and refusals outside the image; rewinding lossy rules and requests; ε |
| TestPrograms | 3 | The examples' output; the defined-behaviour battery, ending with status 70; the default depth bound reached in every shape, and no further |
| TestMaybe | 8 | Kleene tables; undecided conditions refused; escalation; record and replay; rewinding a decision; the REPL |
| TestC23Backend | 17 | Output and ε identical to the interpreter, generated procedures included; the charges of VII.5 alike, the corrected ones against one expected ε; a name bound twice refused alike by the run and the build; a text the same bytes in both, and a NUL in one refused alike; derived inverses compiled; sameness; refusals with status 70; the depth bound, at chosen bounds and at the default, identical to the interpreter's; the depth argument as the backend's own |
| TestMirror | 5 | Inversion as the prelude's certified rule: `invert` having no table but the rule; the rule its own inverse, clause for clause; the rule run by the interpreter, the clauses run by `invert` and an independent table agreeing on every clause, certified or lossy; sequences read from either end |
| TestInversion | 10 | The inversion laws; loss as a message to Root through Object; authority; lineage reaching `ccnot`; delegation keeping each certificate where it is answered |
| TestJournalIdentity | 6 | An entry naming the code that kept it, by identity; no identity changed by renaming a rule or reordering its clauses; a call holding the identity of the rule called, under another name, declared elsewhere, or changed; rules that call themselves or each other; code taking back only what its mirror kept, whoever it was kept by; identities of code and of rules compared as the forms they name |
| TestCodeIdentity | 11 | Variables identified by their binding, under renaming and under every change of binding structure; the example of III.3; the order of declaration as a tie-breaker only; quoted code as written; a ring that shares an identity and stays a ring; no name bound where it is already bound; requests and answers referred to by identity, with same-signature requests and same-code answers kept apart; exclusive clauses a set and first-match clauses a sequence; a cycle identified as a whole, under renaming and reordering; rules that share an identity interchangeable, a ring of them being the rule that calls itself; an identity granting no authority |
| TestJournalContract | 5 | Entries appended and restored exactly; rewinds out of step refused; only the system writes: ten routes refused by the seal; control-flow obligations |
| TestSemanticContracts | 10 | `history` as a copy; the escalation path rebuilt; crisp `decide`; clause-choice order; a rewind bound to its run by the canonical form; replay matched on question and context, each record once and in order; Kleene circuits; `repeat n times` refused with what replaces it |
| TestTwoTiers | 4 | No lossy clause in the prelude; ordinary gates as a reversible gate and a `discard`, resting on `ccnot` and on Root's `keep`; certified code unable to rest on a dissipative rule; Boolean logic run on the Kleene circuits |
| TestAccounting | 9 | A clause choice kept only where the output leaves one; a dropped value charged by its type; only the constructors still possible counted; a value still computable dropped for nothing; the charges of the inputs that share an output a code; a `Text` charged its length and its bytes; a word charged its declared width however it was written; a decision charged by the answers installed, at 14, 15 and 16; ε as the sum |
| TestDeclaredTypes | 5 | A `Trit` refused at each of the sixteen sites where a `Bool` is declared, with its reason, and the same program with a `Bool` accepted; a `Bool` given where a `Trit` is; no certified rule deciding a `Trit`; `set` writing its value in the cell's type; a request's arguments and an answer's reply and state compared with what is declared |
| TestExtent | 4 | Gates as permutations and an ancilla as an embedding, with its inverse partial; rules over words settled by their steps or by counting; nothing claimed that is not established; an answer's rule for each request, settled each of the three ways |
| TestDeclarations | 8 | The form types as the prelude's own text, and a declaration not being `Code`; the example; every declaration held as a value and written back; `definition` for rules, answers, types and requests; the program as a form; all of the code written to be taken apart; holding a declaration granting nothing; a name not given back against an expression that reads it |
| TestCensus | 3 | Every form the parser writes taken apart and put together; nothing escaping in any example; a tag with no constructor reported |
| TestBuiltValues | 2 | A literal inside a constructor taking the type its field declares; a copied instance sharing nothing with the original |
| TestCcnotTape | 8 | Moop's trace printed byte for byte, in the interpreter and compiled; draws and births taken back, and a draw the tape did not give refused; fewer than two cells refused; the three names not declared again, and no request for the tape; the tick realized by `ccnot`; extents as established, the birth not onto; on its domain, the tick a permutation and a draw and a birth one-to-one and not onto, over every state with 2 or 3 cells on each tape; outside it, every input refused in both backends |
| TestReversibleProfile | 6 | The tape's three rules laid out and their gate counts; one alignment of 8 and 13 cells as 208 CCNOTs, against 104 interpreted ticks; an ancilla given back at 0, and an embedding refusing what it does not give; rules that are not the tape (`ripple_add` on all 512 inputs at width 4, the gates of `examples/gates.selv`, a swap as a relabelling); what the profile refuses, with its reasons; `selvage circuit` |
| TestMeasure | 4 | The group `Measure` in the prelude, answered by nothing, and its two names not declared again; `ask measure()` refused at Root with status 70, and not built in compiled code; a rule that asks lossy and one that draws certified; a program's stand-in taking the request inside its `with` only |
| TestSoundness | 10 | R4 for indices and parameters, under either arrow; sameness; instance unpacking; an uncompute proved only in the pattern that bound it; generated certified rules; the description check; a refused example checked for its reason; a generator requiring its prelude |
| TestSealAndWitness | 14 | The seal as a rule about places; `history` through `Witness`; Root's three groups kept apart; hosts deciding what inner code reads; an inquiry leaving the journal as it was; giving the copy back: what was transactional rewound, a kept record refusing it, a refused withdrawal leaving the answers further out as they stood, a host keeping nothing of it; a host in its installer's row; the one request passed outward; instance states typed; commit points in the row; layout as the only lineage exemption |
| TestGenerated04 | 23 | The twenty-two generators of XI.2, each with its oracle; an untaken refusal ending the run with status 70 |

### XI.5 What the suite does not yet cover

1. That the checker establishes the obligations O1 to O6, and that the interpreter runs the model of XI.3. Both rest on generated tests and the mutation check, not on proof.
2. The C23 backend against the model. It is compared with the interpreter (TestC23Backend), and the interpreter with the model.
3. A refusal raised while an answer is answering.
4. Seals between places other than the prelude and the program, which need modules.
5. The information lower bound for closed types (VII.5): tested on small types by going through every input, and not proved.

### XI.6 The description check

`tools/check_description.py` examines every code block of this description with the toolchain, and the suite runs it (TestSoundness). The description and the toolchain share one notation, so a block is checked as written, arrows included.

| Verdict | Blocks | Which |
|---|---:|---|
| Passes the checker, with the blocks before it | 14 | `and_into` and `and_gate`; `tally`, `sum` and `cross`; `leapfrog`; `damped_orbit`; `Ledger` and `pay`; `Count` and `Resettable`; `flip`; `Tally`; `by_severity`, `urgent` and `route`; `Log` and `Recorder`; `Closed`, `redact` and `Redacting`; `and_table`; `each_mirrored` and `turned`; `derivative` |
| Is the prelude's own text | 4 | `ccnot`; `trit_and`; the roots (VII.2); `mirror` (VIII.2) |
| Is what `invert` derives | 1 | `undo leapfrog` and `undo damped_orbit` |
| Is refused by the checker, for the reason its first line gives | 1 | `Hoard` (VII.2) |
| Awaits a ratified form that is not built | 0 | |
| Fails | 0 | |

**A block that awaits.** When the description shows a ratified form the toolchain has not built, the check does not skip the block. It takes out the one named difference and requires what remains to be the prelude's text, declaration for declaration; any other difference fails. No block awaits at present.

What the check does not examine: the claims made in prose and tables.

| Item | Implementation | Design | Evidence |
|---|---|---|---|
| Code blocks examined as written, arrows included | Built | Ratified | TestSoundness.test_the_description_s_code_blocks_check |
| A block that shows a refused program, refused for its stated reason | Built | Ratified | TestSoundness.test_a_refused_example_is_checked_for_its_reason |
| The roots block checked as the prelude's own text | Built | Ratified | The same test |
| Status tables generated from tests tagged with the entries they support | Deferred | Ratified | — |

---

## XII. Open Design Register

### XII.1 Ratified rulings

The short labels are the identifiers under which rulings were made. Some recur, because rulings were made in separate batches, and some coincide with labels used elsewhere in this description (the hard constraints H1 and H2, the checking rules R1 to R8, the guarantees G1 to G11). A label alone is therefore not a unique reference: where it matters, cite the ruling with its subject.

| Ruling | Adopted | Consequence |
|---|---|---|
| R1 | `<->` is a certified correspondence | It marks the clauses of rules the checker certifies, bijective or partial-bijective |
| R1 | `=>` is declared loss | Lossy clauses use `=>`; `uses Discard` is removed; `invert(L => R) = R => L` |
| R2 | `<-` is field-only derivation | It derives record types, not answer behaviour |
| R2 | Prototypes delegate through Request | The parent's rules run on the parent's own state, keeping their certificates; lineage marks the link `delegated`; `Object` takes a `Root` instance and delegates `keep` to it |
| R3 | Twelve parts | One authoritative location per concept |
| R3 | Status on two axes plus evidence | Implementation and design are reported independently |
| Q1 | Soft constraint 9 kept: CCNOT primitive (reversible realization) | `ccnot` stays the four-clause prelude rule and the base of lineage; the derived gate rules stay in the prelude; it is not on the ordinary execution path. The clause test certifies; `ccnot` grounds realization lineage (II.3) |
| Q1 | Quantum readiness added as a realization objective | Not a replacement for constraint 9; it authorizes no quantum claim about ordinary execution (I.3) |
| Q2 | Three realization profiles | Classical Built, Reversible Specified, Quantum Absent; the permutation–unitary bridge with its partial-bijection and uncompute conditions; quantum operations outside the kernel (IX.4) |
| Q3 | Measurement is a Request | World input, kept, `=>`, a commit point; replay reproduces the outcome, not the amplitudes. Reset is lossy state preparation (VII.4) |
| P1 | Functions and procedures | An expression rule with an empty `uses` row is a function: recomputable, keeping nothing. Otherwise it is a procedure: it keeps and accounts for world replies, and lists `System` when it reaches `keep`, which is R6 applied uniformly. A procedure's overwrites are not kept. A procedure that receives a world decision and keeps the reply accounts for it in its signature; `System` is never inferred from the word `decide` alone (V.3) |
| P2 | Lineage for operators | One theorem link per operator class, the operators inside update expressions included (VII.6). A verified gate-level multiply is deferred until that lineage is stable |
| P3 | Journal, Witness, Root | `keep` in a group only the system sends; `history` through `Witness`, which a host may answer to limit what inner code retrieves; the three checks by name replaced by a Root seal that is an authority boundary, not another naming convention (VII.2, VII.3) |
| P4 | Evidence for G1 | Generated-rule testing, extended to lossy rules, messages and decisions; a soundness theorem stated with its assumptions and scope, and proved; every code block of the description examined. Generated tests are evidence, not proof (XI) |
| P5 | Delegation | To the one state component that answers the request; several are refused. The whole state need not be one instance. A message naming a request no component answers is refused by the checker. An `ask` with no local answer continues outward; that is not itself a refusal, which occurs when the authority it reaches resolves it under P8 (VI.2, VI.3) |
| P6 | Description integrity | Deprecated forms in XII.2 only; evidence cells name tests; status tables generated from tagged tests; normative, implemented, tested, proven and deferred kept apart (I.1) |
| P7 | `Any` | Confined to the prelude's journal and `Code`; refused in a program's declarations; no type parameters yet (III.1) |
| P8 | Refusal | A request Root answers by ending the run; an installed answer may take it first (VI.5) |
| D1 | A taken refusal | It aborts the computation within its enclosing `with`, and execution resumes after that boundary. The body computes `()`. No general substitution rule follows from this; substitution stays open (VI.5) |
| D2 | Raising a refusal | A refusal a program raises itself needs `Refusal` in the row; those the system raises need no row (VI.5) |
| D3 | Effect accounting | A group leaves a row only when all its requests are answered, never because one was (VI.2) |
| D4 | Components | The state itself, tuple members and record fields. Discovery is one level deep; deeper delegation is an explicit chain. No unrestricted recursive discovery (VI.3) |
| D5 | Groups | An answer handles only its declared groups (VI.3) |
| D6 | World decisions | A decision the world settles is distinguished from one an installed answer supplies; only the first is retained as a world reply (V.3) |
| D7 | Operator lineage | Boolean logic carries a link. The exemption for index and count expressions is for structural circuit layout only, not for semantic operators in bit-level rules (VII.6) |
| D8 | Exit status | 70 for a refusal nothing took; 1 for a program the checker did not accept (VI.5) |
| D9 | Root | Root supplies the default, terminal answer to a refusal and stays distinguishable from an installed answer, which intercepts the request. Answers for several groups are permitted (VI.5, VII.2) |
| Q2 | `commit` in a row | An empty row cannot conceal a world interaction or a retained effect. A commit that changes retained or observable state is accounted for in the row, in the existing group that owns the effect, and its rule is a procedure. No group is invented for `commit` (V.3) |
| Q3 | The outward path for P3 | Ratified narrowly: inner code asks through `Witness`, the host's answer mediates disclosure, and Root answers `history` under its seal. A capability boundary, not a universal execution restriction. Outward-only requests in general stay Proposed (VI.2, VII.2) |
| E1 | A seal is written `request G for A` | A seal says where a request is answerable. It does not by itself grant authority to every answer in that place (IV, VII.3) |
| E2 | A seal a program declares binds nothing inside the program | Authority comes from the seal and its place, not from spelling (VII.3) |
| E3 | An answer whose state holds a sealed instance is sealed with it | `Object` is sealed this way (VII.3) |
| E4 | A request the prelude's sealed answer declares and has no clause for is answered by the system | Root answers `refuse` this way, with no check on the name `Root` (VII.3) |
| E5 | The outward path, stated without naming `Witness` | An answer may ask the request it is answering only where a sealed answer gives the final reply. A narrow exception to ordinary resolution, not an authorization of arbitrary recursive propagation (VI.2) |
| E6 | What an answer's rules ask is in the row of whoever messages or installs it | Delegation does not conceal the effects of what it delegates to (VI.2) |
| E7 | `commit` in `System`; `output` in `Output` | The two are not merged (V.3) |
| E8 | Giving the copy back, with a qualification | A host may count an inquiry transactionally; when a host nearer the asker gives its copy back, the inquiry's transactional effects are rewound, and the answers further out are as they were. A host that keeps the disclosed value, or a durable record of the disclosure, cannot be passed back through, and a host cannot claim to pass the copy back while keeping what it read (VII.2) |
| E9 | Depth | A run nested too deep is a defined refusal, with status 70 (III.5, VI.5) |
| — | Depth in compiled code | A correctness requirement: the interpreter and the C23 backend agree on excessive nesting, and compiled code never crashes where the interpreter refuses (III.5) |
| F1, F4 | Depth and tail calls | Depth counts every rule invocation in progress. A self tail call adds nothing, and the interpreter runs it as a loop and accumulates no frames (III.5, V.3) |
| F2, F3 | The bound | 10,000 by default; set for the interpreter at run time and for compiled code when it is built. The depth argument compiled code passes is a mechanism of that backend, not a parameter of the language. Both backends agree on the refusal (III.5) |
| F5 | Replay | Ordered and consuming: the next record is matched against the question and its context, used once, and then the next is next. No reuse and no searching ahead; a record that does not match is refused (VI.4) |
| F6 | What a host may keep under E8 | Its reply may depend on what it read, by value or by condition. Nothing else of it may be kept by a host that gives its copy back (VII.2) |
| F7 | Refused examples | A block of the description may show a refused program; the check verifies the reason. Every generator first establishes that its own prelude is accepted (XI.2, XI.6) |
| R9 | `mirror` defines inversion | The prelude's rule `mirror` is the normative definition of structural inversion. `invert` is its host realization; `inverse(c)` and `undo` derive from the same definition; the host keeps no inversion table of its own, and an independent implementation exists only as a test oracle. The language defines its own inversion; the host executes that definition (V.6, VIII.2) |
| R10 | `Restore` | `x was discarded` has a form of its own. Structural inversion, recovery and certified reversibility stay three things: a lossy rule keeps its `=>` when mirrored, `mirror` being a bijection on code does not make a computation reversible, and recovery still needs the system's authority (II.2, VIII.2) |
| R11 | Two-ended sequences | Reading a sequence from its other end reverses the order of its steps and moves nothing. `Then`, `After` and `Done` keep their roles, and `sequence` and `block` stay distinct. A structural property, not a memory layout (VIII.2) |
| — | Headers of rules and answers as `Code` | Rejected. Code is the executable body; a header names and types a declaration, and inverting it flips the name and exchanges the types. The host keeps that small piece of logic. The aim is to remove duplicated language semantics, not every host operation. No new representation of declarations is authorized (VIII.2) |
| R13 | Journal entries name code by identity | An entry identifies the code that kept it by code identity, not by a rule's name and a clause's number, using the identity the language already has. Code identity is not artifact, specialization or closure-environment identity. Event identity and provenance are preserved (VII.3) |
| G1 | The code an entry names | The clause that kept it, or a procedure's own body. A declaration's identity is not put in the place of its body's (VII.3) |
| G2 | Provenance | `by` describes where an entry came from. It never decides which clause a rewind selects, whether an entry may be restored, whether two pieces of code are equal, or whether an answer has authority (VII.3) |
| G3 | Events | An entry's place in the journal orders it within its run. No event identifier is added, and the place is not unique across runs (VII.3) |
| G4 | Hash and equality | A hash finds an identity; it does not prove equality. A run keeps the canonical form behind each identity it uses, compares forms when an identity recurs, and refuses if one identity names two forms (III.3) |
| G5 | Replay | The next record or a refusal; no searching ahead (VI.4) |
| G6 | Forged entries | Accepted with its boundary: the guarantee is program-level journal integrity, not cryptographic integrity against a compromised host (VII.3) |
| Q1 | Calls identify rules by identity | A caller holds the identity of the rule it calls, so its own identity does not depend on the name it calls it by. Renaming a rule changes no caller; changing a rule changes its callers. Calls are resolved before the caller is encoded; rules in cycles are resolved deterministically, with no second identity system (III.3) |
| Q2 | Identities in compiled entries | Deferred until compiled code rewinds or answers `history`. When it does, its entries carry the same identities as the interpreter's (VII.3, IX.2) |
| H1 | A rule's identity | The identity of its canonical executable structure, without its own name: parameters, types, row, and clauses or body. The existing identity function is used; rules have no identity scheme of their own (III.3) |
| H2 | Clause order | Mutually exclusive clauses are a set. First-match clauses are a sequence. Clauses are not sorted merely because their syntax looks alike (III.3) |
| H3 | Cycles | Rules that call one another are identified as a whole, deterministically (III.3) |
| H4 | Members that share an identity | Adopted with a safeguard: two members may share an identity only if they are indistinguishable under the language's observable semantics. Members whose code looks alike but whose places or relationships produce different behaviour are not merged. Sharing an identity must imply being interchangeable (III.3) |
| H5 | What is resolved | Adopted with an extension: quoted names remain data, and semantic references resolve to identities (III.3) |
| H6 | Variable names | Modified. Variable names do not affect code identity: consistent renaming of bound variables preserves it, and binding positions are normalized deterministically. Scope, binding relationships, free variables, capture and shadowing, and pattern structure are preserved. This is alpha-equivalence, not textual normalization (III.3) |
| Q1 | Identity under renaming of variables | Identity is invariant under consistent variable renaming. The journal identifies the same executable code after it (III.3, VII.3) |
| Q2 | References to requests and answers | Resolved by identity, not display name: rule calls, requests in messages and in `ask`, and answers through `from`. Quoted request and answer names are ordinary data. Display names remain for diagnostics and provenance. References are resolved, not declarations made interchangeable: types, groups, clauses and authority stay distinct. A request's identity confers no authority to answer it; an answer's identity does not override its declared groups; a seal remains an independent constraint (III.3) |
| J1 | No shadowing | A name may not be bound again within a region in which its earlier binding is still visible, alike for `is`, patterns and loop counters. A spelling may be used again in a scope that does not overlap. Alpha-equivalence applies to legal bindings: an attempted shadowing is refused, not given a second binding identity (IV, III.3) |
| J2 | Group identity | Adopted with a qualification: from the ordered sequence of request signatures; groups with identical signatures are told apart by declaration order within that class of duplicates, and by nothing else. Identical groups are not merged, since they may carry distinct authority (III.3) |
| J3 | Request identity | The group's identity and the request's position in the group's sequence. Renaming changes nothing; reordering does (III.3) |
| J4 | Answer identity | Adopted with a qualification: from the identity of its executable code; identical code is told apart by declaration order within that class of duplicates. Identical answers are not merged, since they may be installed or delegated to independently (III.3) |
| J5 | Resolution order | Modified: groups and requests, then answers, then rules, canonicalizing the graph. An answer type in a request's signature is a category of type, not a reference to one declaration. Types and constructors keep their names as nominal values; quoted names stay data; messages, `ask` and `from` resolve to identities (III.3) |
| J6 | Quoted code | Data everywhere. Its identity is that of the quoted form: no call in it is resolved and no name normalized, and `identity(v)` gives that identity (III.3, VIII.2) |
| J7 | Indistinguishable rings | Adopted with a condition: where full refinement finds nothing to tell the members of a ring apart, they may share one identity, that of the equivalent rule that calls itself. This is an equivalence of identity and not a rewrite of execution: the call graph, the depth of invocation, the order of execution and positions in the journal keep their run-time meanings (III.3) |
| K1 | The two-tier law | Every dissipative user-level operation is realized through conservative computation and an explicit loss boundary; what restoration needs is retained through the authorized `keep`. The prelude holds no `=>` clause and there are no irreversible gate primitives. `keep` stays under the System and Root authority model, and the system does not silently preserve every overwritten value (II.5) |
| K2 | Exact loss accounting | What is retained to discriminate is set by the ambiguity that remains once the output is seen: no clause tag where the output determines the clause, ⌈log₂ n⌉ where n clauses remain possible; only the constructors still possible; only payload that cannot be reconstructed. The interpreter and compiled code use one definition, and the oracle computes what is retained independently (VII.5) |
| K3 | Onto and embedding | The checker reports whether a certified transformation is onto its declared codomain, apart from whether it is injective: a permutation, an embedding, or an inverse that is partial. `<->` is not weakened (V.2) |
| K4 | Declarations as forms | Option B: a `Declaration` form distinct from `Code`, and a `Program` form. Nothing in the language's semantic structure escapes representation as a form. Typed distinctions remain essential, and no form need inherit behaviour through a prototype chain. A form census reports what is represented, inspectable and transformable (VIII.1) |
| K5 | Certified encoding | For each serializable form type, a certified reversible encoding onto its valid bit arrays, with domain and valid range explicit; no universal bijection between every value and every bit array is claimed. Built after K4 (VIII.1) |
| K6 | Boolean logic | Realized through the existing Kleene circuits. A change in the conformance record: no new prelude code, primitive or gate family (VII.6) |
| RME-7 | Placement | The conservative/dissipative distinction is an architectural invariant of the language. RME-7 remains a library and conformance influence, not a source of kernel features; symbolic differentiation remains a library-level transformation over forms (X) |
| Open 12 | Identity from inside the language | Deferred: no built-in returns the identity under which the current rule, clause or answer runs, since a program whose behaviour depends on its own identity refers to itself. `identity(v)` of a value or a quoted form stays. Identity remains visible to the checker, the tests, journal diagnostics and the host (III.3) |
| L1 | Constructor exclusion | A constructor is excluded only when the value is constructed in the current clause, or one earlier clause accounts for every input of the current clause that has that constructor. No collective exclusion across several earlier clauses: an upper bound on the loss is preferred to an analysis soundness does not need (VII.5) |
| L2 | Zero-charge drops | A dropped value that can still be computed keeps its journal entry and is charged nothing. Accounting and journal storage are separate specifications; the entry keeps `Discard` and `Restore` uniform under `mirror` (VII.5) |
| L3 | Accounting conventions | `F64` 64 bits, an array's length 64, `Text` 8 a byte, an open form 16 and its parts. Conventions of accounting, not claims about storage, entropy or dissipation (VII.5) |
| L4 | Clause choice | `Chose` is kept only when the output matches the right sides of more than one clause. A rule may be lossy while a particular run loses nothing and stays eligible for rewind (VII.3, VII.5) |
| L5 | Extent reporting | The R2 classes keep their names; extent is analysed apart: every input run where there are at most 4,096, otherwise the steps, otherwise counting, otherwise one-to-one and nothing more. No arithmetic proof search. How an extent was established is evidence, not a further guarantee (V.2) |
| L6 | The no-refusal list | Kept short, as a sufficient test: failing it does not show that a rule refuses. A call into a recursive cycle counts as able to refuse. "Cannot refuse" is apart from the depth bound, as in the scope of the soundness theorem. An operation joins the list only when its inability to refuse is established and tested (V.2) |
| T1 | `Text` accounting | A dropped `Text` is charged as an array of bytes: 64 bits for its length and 8 bits a byte. This revises L3 and the charge ε for rules that discard `Text`. The ruling alone authorizes no toolchain change (VII.5) |
| T2 | Open types | `Any` and code keep their accounting conventions and stay outside the lower-bound theorem. No charge for the kind of value is introduced (VII.5) |
| T3 | The information lower bound | Accepted as a proof obligation for closed types, `Text` included under T1. Its proof must establish the inverse run as a decoder, the adequacy of the summed charges, and what is held fixed, decisions being outside it. A proof sketch is not represented as a proof (VII.5, XI.5) |
| T4 | Memory Modification Theory | A working name for the general frame: computation as the controlled modification of organized memory, with Selvage as its realization and testbed. Formal adoption follows proof of checker soundness and of the information lower bound |
| Open 13 | The differentiation variable | `derivative` takes its variable as a parameter: the name differentiates to 1, other names to 0. The parameterized rule is the library rule; no wrapper is added (VIII.2) |
| R12 | Rewindable `install` | Deferred. A journaled modification under κ admission, κ staying distinct from certification and from inversion (VIII.3) |

Taken in admitting the CCNOT tape (VI.6). They are the merge plan's G3 to G7 between moop and Selvage, entered here as C1 to C5 because G1 to G11 are taken. The maintainer ruled C1 to C5 on 2026-11-17; C5 changed how C3 and C4 are carried out, and they are given here as ruled after it. Ratified 2026-11-18, and moved here from XII.6 unchanged:

| # | Decision | Where | The alternative |
|---|---|---|---|
| C1 | The CCNOT tape defines `draw`: a deterministic observation, the same in every backend, with no claim of randomness or independence. Another generator is a rule of its own, never an implementation of the tape | VI.6 | A faster generator for `draw` on the CPU (a certified rule over words is about 100 times faster per bit), giving the backends different values; or `draw` as a general generator interface |
| C2 | The tick's head arithmetic is written inline: six names reserved, the transition visible where it is defined | VI.6 | Two helper functions for the head moves: about twice as fast per tick, and two more reserved names |
| C3 | A program makes its tape and passes it to `draw` and `birth`; no tape is ambient | VI.6 | A tape held by `Object`, so that a draw works anywhere, with a ruling on where its seed comes from (open question 10) |
| C4 | The names `CcnotTape`, `tape_tick`, `draw` and `birth`. `tape_tick`, not `tape_step`, because a step is a statement of a clause; `tick` is taken by `examples/declarations.selv` | VI.6 | Other names; before C5, also a request group `Draw` and a record `Tapes` |
| C5 | `draw` and `birth` are prelude rules over the tape, with no request group, so that no program can stand in for the tape's draw: a prelude rule's name cannot be declared again. The reservation is of the rule names only; a program's own request may share the word | VI.6 | An answer `CcnotTape` for a request group `Draw`, which any program could answer as well; or that answer with a new kind of seal letting anyone send the group's requests and only the prelude answer them: a new declaration and a new case of R5, and draws left to the interpreter until answers compile. A namespace shared by rules and requests, to close the residual word, is a separate question |

Taken in declaring the request group `Measure` (VII.4), the merge plan's Phase 7 between moop and Selvage. It carries out Q3 as far as it can go with no quantum backend. The maintainer ruled N1 to N3 on 2026-11-18: N1 adopted, N2 adopted with a qualification, N3 adopted for now. Ratified the same day, with these dispositions:

| # | Ratified disposition |
|---|---|
| N1 | `Measure` is a prelude request group with no prelude answer |
| N2 | The group remains unsealed; explicit stand-in answers are permitted, but do not establish physical measurement |
| N3 | `measure()` remains argument-free until quantum state and register types exist; revisit its signature with the measurement semantics |

The decisions as entered, moved here from XII.6 unchanged:

| # | Decision | Where | The alternative |
|---|---|---|---|
| N1 | The group `Measure`, with the one request `measure() returns Bit`, is declared in the prelude, and nothing answers it: an `ask` reaches Root and is refused. Its two names are the prelude's | VII.4 | The group in an example, reserving no names but giving no signature that every program shares and a profile could answer; or no declaration until a backend exists |
| N2 | `Measure` is not sealed: a program may install an answer of its own, a stand-in, as it may for `Refusal` and `Witness`. Ruled with a qualification: environmental measurement, answered by the environment, and a stand-in, a modelled reply for tests, simulations or controlled experiments, are kept apart; a stand-in implements the request's contract and does not establish that a physical measurement occurred | VII.4 | Sealed to Root, which under R5 would forbid programs to ask it as well; or a new kind of seal that lets anyone ask and only the system answer: a new declaration and a new case of R5, the alternative C5 also declined |
| N3 | `measure` takes no argument, for now. What is measured is left to the quantum interface; when qubit types or registers exist, the signature is revisited with the semantics of measurement, the update of the state, the outcome's representation and its irreversibility | VII.4, XII.5 | An argument naming a qubit, such as an index: a way of naming qubits before there is any qubit management |

Enforcement, as built (VII.4): the interpreter refuses an unanswered request at run time, with status 70. Compiled code refuses any program that asks for `measure` at build time, with status 1, because compiled code cannot currently express requests, even when a stand-in answer exists.

Adopted with the rulings:
- reversibility, recoverability and retrieval authority are distinct (II.2);
- `keep` has the exact domain K : Entry × Journal → NonEmptyJournal (VII.3);
- `ccnot` is the reversible-realization primitive, not a fourth mechanism (II.3);
- MAYBE is a general decision protocol, `defer` is its protocol outcome for `maybe`, and replay establishes reproducibility, not truth (VI.4);
- hash identity does not establish equality (III.3);
- F64 retention is a storage convention (III.4);
- C23 competitiveness spans layout, ABI/FFI, atomics, freestanding operation and static request lowering, each with its own status (IX.3);
- P1, P3 and P8 form one boundary: P1 determines what is retained, P3 who may inspect it, and P8 who disposes of a refused request;
- delegation is not authority transfer without limits. A component answers within its declared groups. `Witness` mediates historical knowledge. Root governs system-level authority. Refusal provides the terminal boundary when no installed answer handles a request. These four are not to be collapsed into a general-purpose permission mechanism;
- a value cannot be withdrawn from an inquiry chain after an intermediary has kept that value (VII.2, G11);
- `Witness`, Root and giving the copy back are not generalized into a broader permission framework;
- a representation can be reversible without its computation being reversible; a computation can be recoverable without being reversible; and neither property establishes authority to recover (II.2);
- code is identified by what it structurally is and what it references, not by the names it is given (III.3);
- names identify things for readers; identities identify things for execution; canonical forms establish structural equality; authority determines what execution is permitted to do. These are four separate responsibilities. Identity resolution never becomes authority resolution: a program knowing the identity of a request or an answer does not thereby gain permission to invoke, intercept or replace it (III.3);
- one typed representational foundation, conservative system realization, and explicit user-level dissipation: without an irreversible gate set, without declarations turned into executable `Code`, and without authority granted through identity (II.5, VIII.1).

Kept Proposed by ruling:
- every request made inside an answer resolving outward from it (VI.2). Only the path P3 requires is ratified.

Deferred by ruling:
- the second part of P2, a verified gate-level multiply (VII.6);
- status tables generated from tagged tests (XI.6);
- rewindable `install` under κ (R12);
- code identities in compiled journal entries, until compiled code rewinds (Q2);
- a built-in for the identity under which code runs (Open 12);
- the name Memory Modification Theory, until the two theorems are proved (T4).

### XII.2 Deprecated by the rulings

Deprecated forms are listed here and nowhere else in this description.

| Deprecated form | Replaced by | In toolchain 0.5.0 |
|---|---|---|
| `<->` on every clause, lossy ones included | `<->` certified only; `=>` for lossy clauses (R1) | Refused |
| `uses Discard` declaring loss | The `=>` arrow (R1) | Refused |
| `<-` on answers, inheriting request rules onto the child's state | Delegation to the one state component that answers (R2, P5) | Refused |
| `repeat n times` | `repeat with i from 1 to n` (audit ruling A2) | Refused, with what replaces it |
| `Object <- Root`, with `history` on Object | `Object` taking `Root` and delegating to it (R2) | Removed |
| `inherited` as a lineage certificate | `delegated` (R2) | Removed |
| Every expression rule classed as a function; a decision made directly in one neither kept nor counted | Functions and procedures (P1) | Removed |
| Every `with` taking every request out of the row | A request leaves the row only when the installed answer answers it (P5) | Removed |
| Lineage for steps only | A link for each operator class inside expressions (P2) | Removed |
| `history` in `System`, open to any rule that lists it | `history` in `Witness` (P3) | Refused |
| Three checks on the name `keep`, and one on the name `Root` | The Root seal (P3) | Removed |
| `commit` under an empty row | `commit` in `System` (Q2) | Refused |
| Index and count expressions exempt from lineage wherever they stand in a bit-level rule | Exempt only when they are structural layout (D7) | Removed |
| `Any` accepted in a program's declarations | Confined to the prelude and `Code` (P7) | Refused |
| A refusal always ends the run | A request an installed answer may take first (P8) | Removed |
| The interpreter ending a refused run with status 1 | Status 70, as in compiled code (P8) | Removed |
| A journal entry naming the rule that kept it by its name, and a clause by its number | The identity of the code (R13) | Removed |
| A call identified, in its caller's identity, by the name of the rule called | By the identity of the rule called (Q1) | Removed |
| The names of variables as part of code identity | Variables identified by their binding: alpha-equivalence (H6, Q1) | Removed |
| Requests and answers referred to by name in code identity | By their identities; names kept for reading (H5, Q2) | Removed |
| A clause choice kept on every run of a rule whose clauses overlap, and charged among all its clauses | Kept only where the output matches more than one right side, and charged among those (K2) | Removed |
| A dropped record or variant charged 16 bits for what it is | The bits that tell apart the constructors it may still have (K2) | Removed |
| Boolean logic resting on `ccnot` by a cited theorem | Realized by the Kleene circuits, and run (K6) | Removed |
| A certified rule reported by its class alone | Its extent reported apart from it (K3) | Removed |
| `Code` built by the toolchain, with constructors for some of the forms the parser writes | `Code` and the other form types declared in the prelude, with a constructor for every form (K4) | Removed |
| `definition` giving a rule's or an answer's declaration as `Code`, which no rule could take apart | A `Declaration`, for rules, answers, types and request groups (K4) | Removed |
| `derivative` treating every name as the variable | The variable as a parameter (Open 13) | Removed |
| `x was discarded` as a `Was` | A form of its own, `Restore` (R10) | Removed |
| An inversion table in the toolchain | The prelude's rule `mirror` (R9) | Removed |
| One status label per entry | Implementation, design and evidence (R3, P6) | Description only |

### XII.3 Changes from 0.3.2 in this description

| Where | Change |
|---|---|
| Opening | Language identity restated; `ccnot` named the realization primitive |
| I | Status model; constraints with three status fields; ladder with `ccnot` at Tier 1 |
| II.2 | Reversibility, recoverability and authority separated |
| II.4 | R2 requires the arrow to match the class; R6 no longer carries `Discard` |
| III | Modular integer domains, nominal types, ownership, identity versus equality, F64 convention |
| IV | `=>` arrow; clause-free answers; `<-` on answers removed |
| V | Classes with arrows; `invert` keeps the arrow; all examples in 0.4 notation |
| VI.3 | Prototypes by delegation |
| VI.4 | MAYBE as a general protocol; `defer`; record fields named by what they identify |
| VII.2–3 | Roots in their delegation form; `keep`'s certificate separated from authority, storage and accounting |
| IX.3 | C23 competitiveness on seven dimensions |
| XI | Evidence kinds; the 0.3.2 suite as baseline; what a 0.4 suite must add |
| I.3, II.3, VII.4, IX.4 | Quantum readiness as a realization objective; certification distinguished from lineage; measurement and reset; realization profiles |
| II.4, V.6 | R4 covers the index of a changed cell and the parameters of a consuming call |
| III.1, III.3 | `Any` listed; sameness defined, `=` on `F64` stated as IEEE |
| I.1 | Deferred added to the implementation values; normative, implemented, tested, proven and deferred told apart |
| IV, VI.2, VII.2 | Answers for several groups; requests from inside an answer resolving outward; `Witness` and `Refusal` groups; Root answering all three |
| V.3 | Functions and procedures |
| VI.3 | Delegation to the one state component that answers |
| VI.5 | Refusal as a request |
| VII.3, VII.7 | The Root seal as an authority boundary; G3 and G8 marked Partial; G10 added |
| VII.6 | A link for each operator class inside expressions; `inherited` removed |
| XI | Evidence kinds; generated rules; the soundness theorem with its assumptions and scope; the suite by class; the description check |
| Throughout | Evidence cells name the tests |

With toolchain 0.4.0:

| Where | Change |
|---|---|
| I.1, XI.4 | The suite of 82 tests in this description's notation; an entry is Built only with a named test |
| II.4 | R2 and R6 Built; R6 states what an installed answer takes out of a row |
| V.2, V.6 | The arrow check and `invert` keeping the arrow Built |
| V.3 | What counts as a reply from the world; what a procedure keeps; steps call functions only |
| VI.2 | An `ask` an installed answer does not take continues outward, in the run and in the row |
| VI.3 | Components and groups stated; delegation Built |
| VI.5 | What happens when an answer takes a refusal; the `Recorder` example; what may run inside |
| VII.1 | Entries kept after a run stand between it and its rewind |
| VII.2 | The roots as built: `Witness` awaited, `history` still in `System` |
| VII.6 | The operator classes in a table, with Boolean logic and circuit layout; `computes with` links |
| IX.2 | Procedures and refusals in compiled code |
| XI.2 | Seven generators with oracles; the mutation check; agreement with 0.3.4 |
| XI.5, XI.6 | What the suite does not yet cover; the description check on blocks as written |
| XII.6 | Decisions taken while building, awaiting a ruling |

With toolchain 0.4.1:

| Where | Change |
|---|---|
| II.4 | R5 Built, with how a seal is written; R6 covers what an answer's rules ask, and commit points; R8 Partial, for depth in compiled code |
| III.1 | An instance's state and parameters are typed |
| IV | `request G for A` |
| V.3 | Commit points in the row |
| VI.2 | An answer has no row; the one request passed outward; requests in general not restricted |
| VI.5 | A handled refusal and a terminal refusal kept distinguishable |
| VII.2 | The roots as built, with `Witness`; the disclosure path; the `Closed` and `Redacting` hosts |
| VII.3 | The Root seal as built: how it is written, places, holding a sealed instance, the system's half |
| VII.6 | The lineage exemption limited to structural layout |
| XI.2 | Generators for adversarial authority and adversarial disclosure; 39 mutations |
| XI.5, XI.6 | Depth in compiled code; no block of the description awaits |
| XII.1, XII.6 | D1 to D9, Q2 and Q3 entered as rulings; the decisions taken while building P3 |

With toolchain 0.4.2:

| Where | Change |
|---|---|
| I.1, XI.4 | A stated proof; the suite of 108 tests |
| II.4, VII.7 | R8 and G6 Built: depth refused alike in both backends; G1 resting on the proof; G11 added |
| III.3 | A rewind bound to its run by the canonical form, and replay matched on question and context, Built |
| III.5 | The depth bound: what it counts, its default, the same in both backends |
| V.3 | A self tail call a loop in both backends |
| V.5 | When an uncompute is proved |
| VI.4 | Replay using each record once, in order; decisions inside clause rules generated |
| VII.2 | Giving the copy back: what was transactional rewound, a kept record refusing it, a host keeping nothing of it; the refused `Hoard` |
| VII.3 | A seal says where a request is answerable, not who has authority |
| IX.2, IX.5 | Depth in compiled code; the benchmarks measured again, with the cost of the bound |
| XI.2 | Generators for depth, structures, decisions in clause rules and the model; 60 mutations; agreement with 0.4.1 |
| XI.3 | The model, the obligations O1 to O6, and the proof |
| XI.5, XI.6 | Coverage restated; a block may show a refused program |
| XII.1, XII.6 | E1 to E9 entered as rulings, E8 with its qualification; the decisions taken while building 0.4.2 |

With toolchain 0.4.3:

| Where | Change |
|---|---|
| V.6, VIII.2 | Inversion defined by the prelude's certified rule `mirror`, which `invert` runs; blocks as sequences read from either end; `x was discarded` a form of its own; the involution proved |
| VIII.3 | The roles of `mirror`, the checker, the journal, `install`, κ and `commit` kept apart |
| XI.2, XI.4 | Mutations of the rule `mirror` itself, 64 in all; the suite of 112 tests; agreement with 0.4.2 |
| XII.4 to XII.6 | The journal in the same substrate as an open question; rewindable `install` after it; F8 to F10, and the recommendations awaiting a ruling |

With toolchain 0.4.4:

| Where | Change |
|---|---|
| II.2 | A representation can be reversible without its computation being so; neither establishes authority |
| VI.4 | Replay ordered and consuming, a mismatch refused |
| VII.2, VII.3 | Entries name the code that kept them, by identity; code takes back what its mirror kept; `by` as provenance |
| XI.2, XI.4 | A generator for the journal's identities; replay in the decisions generator; 72 mutations; the suite of 120 tests |
| XI.3 | Entries by identity in Part 4; a rewind bound to its run |
| XII.1, XII.6 | F1 to F7 and R9 to R11 ratified; headers as `Code` rejected; R13 ratified and built; the decisions taken while building it |

With toolchain 0.4.5:

| Where | Change |
|---|---|
| III.3 | Code identified by what it is and what it references: calls resolved to rule identities; a rule's identity; cycles; names, identities, canonical forms and provenance kept apart |
| VII.3 | No entry's `code` changed by renaming any rule; program-level integrity and its boundary; position as order within a run |
| IX.2 | Identities in compiled entries deferred, with parity required |
| XI.2, XI.4 | The journal generator extended to called rules, declarations, changed callees and recursion; 78 mutations; the suite of 122 tests |
| XII.1, XII.6 | G1 to G6, Q1 and Q2 entered as rulings; the decisions taken while resolving calls |

With toolchain 0.4.6:

| Where | Change |
|---|---|
| III.3 | The four responsibilities; the canonical form of code, with variables by their binding and requests, answers and groups by identity; how declarations with the same signatures or code are told apart; interchangeable members; what `identity(v)` is of |
| IV | A name bound once where it can be seen |
| VII.3 | No entry's `code` changed by renaming a variable, a request, a group or an answer |
| VIII.2 | `identity(v)` of quoted code as the form as written |
| XI.2, XI.4 | The names generator; the journal generator renaming variables; 91 mutations; the suite of 131 tests |
| XII.1, XII.2, XII.6 | H1 to H6, Q1 and Q2 entered as rulings; what they replace; the decisions taken while building them |

With toolchain 0.4.7:

| Where | Change |
|---|---|
| I.3 | System-facing reversibility, homoiconicity and the placement of RME-7 ratified |
| II.5 | The two tiers: conservative realization, dissipative use, one set of gates |
| III.3, IV | The order of declaration as a tie-breaker only; quoted code as written; a ring that stays a ring; no shadowing ratified |
| V.2 | The extent of a certified rule, and how it is established |
| VII.5 | What an entry is charged: clause choices, constructors still possible, values still computable; the charges as a code |
| VII.6 | Boolean logic realized by the Kleene circuits |
| VIII.1 | Declarations, the program, the form census and typed encodings as ratified forms not yet built |
| XI.2, XI.3, XI.4 | The accounting and extent generators; 111 mutations; the clause-choice case of the proof; the suite of 152 tests |
| XII.1, XII.2, XII.6 | J1 to J7, K1 to K6, the placement of RME-7 and the deferral of open question 12 entered as rulings; what they replace; the decisions taken while building them |

Editorial revision of the 0.4.7 description, after review. It changes no semantics and no toolchain behaviour:

| Where | Change |
|---|---|
| Opening, I.0 | What a certificate establishes and what a realization needs besides; rewind eligibility; a guide to the description, with the implementation boundary stated first |
| I.2, I.3 | H1 and H2 stated against realization lineage and `mirror`; homoiconicity's built and specified coverage told apart; quantum readiness by profile |
| III.1, VI.4 | The two-bit realization of `Trit`, with the pair 01 outside it |
| III.3 | The refinement that identifies a cycle, step by step; a ring of shorter period |
| VIII.1 | The pair 01 named as an invalid `Trit` encoding under K5 |
| VIII.2 | `derivative` stated to be an example in one variable |
| IX.1, IX.5 | The interpreter's row corrected; the benchmarks labelled historical, with the toolchains that measured them |
| XII.1 | Ruling labels described as batch-scoped; one adopted principle moved out of a list it was misfiled in |
| XII.5 | The differentiation variable added as an open question |

With toolchain 0.4.9:

| Where | Change |
|---|---|
| Opening, I.0 | Execution stated as steps that are partial functions on states; code as data and reversibility stated as four separate claims; restoration subject to authority in the central proposition; a table of what is proved, what is an open obligation and what rests on tests |
| II.4, III.1 | `Bool` a sub-shape of `Trit` in one direction only, at every site where a value meets a declared type; `Trit(b)` |
| VII.5 | `Text` charged as an array of bytes, built; a decision charged by the answers installed; a value charged by its declared type; T5 and its qualification |
| XI.2, XI.4 | The declared-types generator; `Text` in the accounting generator; decision charges in the decisions generator; 140 mutations; the suite of 174 tests; agreement of 0.4.8 and 0.4.9 |
| XII.4, XII.6 | The corrections of 0.4.9; the defects corrected; the decisions taken in building them |

With toolchain 0.4.8:

| Where | Change |
|---|---|
| X | The RME-7 state-space form stated in full, with its notation and constraints |
| VII.5, XI.5 | The lower bound stated for closed types, as Kraft's inequality, and recorded as an open proof obligation; `Text` charged as an array of bytes, ratified and not built; open types outside the bound |
| XII.1 | T1 to T4 entered as rulings |
| I.3, III.1, VIII.1 | Declarations and the program as forms; the form types as the prelude's text; every form the parser writes a constructor; the form census |
| V.2 | "Cannot refuse" stated apart from the depth bound, and as a sufficient test |
| VIII.2 | `definition` for every kind of declaration; `program()`; `sequence` and `block` over all of the code; `evaluate` refusing what is not an expression; `derivative` with its variable as a parameter |
| XI.2, XI.4 | The forms generator; 120 mutations; the suite of 164 tests |
| XII.1, XII.2, XII.6 | L1 to L6 and the differentiation variable entered as rulings; what they replace; the decisions taken while building K4 |

With toolchain 0.5.0:

| Where | Change |
|---|---|
| III.1, IV | A text holds no NUL byte, refused alike by `check`, `run` and `build`; `Bit` described as the 1-bit unsigned word (A3) |
| V.2 | The extent of each answer rule reported under the answer |
| XII.2 | `repeat n times` deprecated (A2), replaced by `repeat with` |
| VI.6 | The CCNOT tape in the prelude, pinned to moop's trace; its domain stated, with each rule's extent and the refusals outside it |
| VII.4 | The request group `Measure`, declared and answered by nothing |
| IX.4 | The reversible profile, in part, with `selvage circuit`; the two limits a quantum profile must state |
| XI.2, XI.4 | The tape, circuits and measure generators; 153 mutations; the suite of 199 tests |
| XII.1, XII.6 | C1 to C5 and N1 to N3 ratified and moved to XII.1; the decisions taken in building the merge |

### XII.4 Implementation backlog

Built in toolchain 0.4.0, the first group the rulings set:
- **Semantic corrections.** The `=>` notation, the arrow check and no `uses Discard`; delegation to the one answering component and the roots in their delegating form (R2, P5); functions and procedures (P1); a lineage link per operator class (P2-A); `Any` confined (P7); refusal as a request (P8). With them: generated tests for each change, the mutation check, and the description check on blocks as written (part of P4).

Built in toolchain 0.4.1, the second group:
- **Journal and authority** (P3). `keep` alone in `System`, sealed to Root; `history` through `Witness`; hosts that decide what inner code reads, on the one outward path the ruling ratified; the Root seal under R5 in place of the checks by name. With it: `commit` in the row (Q2), the lineage exemption limited to layout (D7), and adversarial generators for authority and disclosure.

Built in toolchain 0.4.2, the third group:
- **Depth in compiled code** (E9), as a correctness requirement: the interpreter and the C23 backend refuse excessive nesting alike, with status 70.
- **Verification** (P4). The soundness theorem proved for its model; the model written out as a second evaluator and compared with the interpreter; generated decisions inside clause rules; rewind binding and replay matched on canonical forms; the mutation check extended. With them: giving the copy back as qualified by E8.

Built in toolchain 0.4.3:
- **Inversion in the language.** `mirror` in the prelude as the definition of inversion, certified and its own inverse; `invert` running it, with no table of its own; lossy code mirrored without being certified.

Built in toolchain 0.4.4:
- **Conformance to F1 to F7,** each with its own tests; replay made ordered and consuming (F5).
- **Journal identity** (R13). Entries name the code that kept them by identity; take-backs and the choice of clause go by it.

Built in toolchain 0.4.5:
- **Calls by identity** (Q1). A call holds the identity of the rule called; rule identities, with cycles resolved as a whole; identity collisions among rules refused.

Built in toolchain 0.4.6, in the order the ruling set:
- **Alpha-equivalence** (H6, Q1). Variables identified by their binding; one scope rule for every binding form.
- **Requests by identity** (Q2), in messages and in `ask`.
- **Answers by identity** (Q2), through `from`, with groups and seals deciding as before.
- **The canonical graph verified** (H1 to H4): cycles, exclusive clause sets, first-match order, interchangeable members.
- **The journal under renaming**: the same entries after every harmless renaming, other entries after a change of code.

Built in toolchain 0.4.7, in the order the ruling set:
- **J1 to J7 specified and tested**: binding, declaration, reference, quotation and cycle identity.
- **The two-tier law and the Boolean realization recorded** (K1, K6).
- **Exact loss accounting** (K2), with an independent oracle and agreement between the interpreter and compiled code.
- **Onto and embedding** (K3): the extent of a certified rule.

Built in toolchain 0.4.8:
- **Declaration and Program forms** (K4). Rule, answer, type and request declarations as forms a rule takes apart; the program as a form; the form census, with nothing escaping.
- **The differentiation variable** as a parameter (Open 13).

Built in toolchain 0.4.9, a release of corrections:
- **Declared types enforced** (R1). A `Trit` is refused wherever a `Bool` is declared; a request's arguments, and an answer's reply and state, are compared with what is declared; `set` writes its value in the cell's type; a literal given as a rule's input or parameter is of the declared type there.
- **`Text` charged as an array of bytes** (T1), in both backends, with the accounting generator extended to `Text`.
- **A decision charged by the answers installed** (Q13, Proposed).
- **A value taken back typed** as it was discarded, so that lossy rules which change or copy an input before discarding it compile.
- **The declared-types generator** (XI.2), and a regression test for each correction.

Built in toolchain 0.5.0: corrections, the audit rulings, and the merge with moop's CCNOT tape:
- **A copied instance shares nothing.** A copy of an answer instance, directly or inside a record or tuple, copies its state, so a message to one copy leaves the others as they were (III.2).
- **A text holds no NUL byte** (III.1, IV): a literal with one is refused alike by `check`, `run` and `build`, where 0.4.9 printed it in the interpreter and an empty line compiled.
- **The extent of each answer rule** (V.2), reported under the answer, and checked on every generated rule hosted by an answer.
- **`repeat n times` removed** (audit ruling A2): one keyword, one `Code` constructor and one clause of `mirror` fewer; `repeat with i from 1 to n` replaces it everywhere, examples and benchmarks included.
- **`Bit` described as the 1-bit unsigned word** (audit ruling A3); the toolchain already treated it so.
- **The CCNOT tape in the prelude** (VI.6): the record `CcnotTape` and the rules `tape_tick`, `draw` and `birth`, pinned to a trace of moop's implementation in both backends, with the tape generator and five mutations.
- **The CCNOT tape's domain stated** (VI.6): the domain D, each rule's extent on it with a proof, and every input outside it refused in both backends.
- **The reversible profile, in part** (IX.4): certified rules over bits, their words laid out, lowered to X, CNOT and CCNOT and checked by simulation; `selvage circuit`; the circuits generator and five mutations. The CCNOT tape is its first program.
- **The request group `Measure`** (VII.4): declared in the prelude and answered by nothing, so an `ask measure()` is refused at Root with status 70; the two limits a quantum profile must state (IX.4); the measure generator and three mutations.

Ratified and next:
- **Typed encode and decode** (K5): for each serializable form type, tests that decoding an encoding gives the value, that encoding a decoding gives the canonical encoding, that an invalid encoding is refused, that the distinctions of identity are kept, and that the interpreter and compiled code agree.

Deferred by ruling:
1. **Documentation synchronization** (P6). Tests tagged with the entries they support; status tables generated from them.
2. **Realization enhancement** (P2-B). A gate-level multiply, verified, once operator-class lineage is stable.
3. **Rewindable `install` under κ** (R12). κ admits a modification to the running program; it does not decide whether a transformation is reversible, which is the checker's certificate, nor how code is inverted, which is `mirror` (VIII.3).

After these:

4. **Ownership, memory and type semantics completed:** scope-end freeing; layout.
5. **C23 interoperability and control:** C ABI and FFI, atomics, freestanding runtime, static request lowering, answers in C; the depth bound at less cost in deep recursion (IX.5); rewind and `history` in compiled code, with entries carrying the interpreter's identities (Q2).
6. **Typed code** `Code(T)`, once the untyped model shows a concrete failure.
7. **The RME-7 prelude** and its conformance suite; seals for roles and units; evidence binding (G5).
8. **Concurrency,** after its scheduling, message-ordering and replay semantics are specified.
9. **The reversible profile:** lowering certified finite-shape rules to X, CNOT and CCNOT circuits, with a check that every uncompute restores its scratch registers; the partial-bijection embedding. Built in part (IX.4): rules over bits whose words are layout, with that check. What remains: conditions and clause choices on bits (controlled blocks), word arithmetic as adder circuits, the extension of a partial bijection to a permutation (IX.4), and a backend that runs the circuits.
10. **The quantum realization interface:** qubit management, superposition and phase operations, a measurement backend, reset. The request group `Measure` is declared, and nothing answers it (VII.4). This item waits on quantum state and a backend that supports it: the declared request does not open it.
11. **Notation and the derived printer.**

### XII.5 Open questions

1. **The working name**, and whether the mechanisms keep the names Form, Rule and Request.
2. **Crisp `Trit` decisions.** A `decide` on a `Bool` is certified. Whether the checker should also certify a `decide` on a `Trit` it can prove never `maybe`, such as `x or true`.
3. **The escalation terminal.** Whether the world's `defer` must always end in refusal (the current rule), or may take an explicitly declared default.
4. **κ admission for `install`:** who holds a slot's policy, and what it may inspect.
5. **Concurrency without a foundational scheduler.** Actors can be built from Request, but deterministic replay of a concurrent run needs a precise account of scheduling, message ordering and external input; actor composition does not by itself make concurrency reversible.
6. **Unsafe operations.** How an explicit unsafe boundary interacts with certification and the journal.
7. **The quantum realization interface.** Qubit management, phase operations, superposition, the measurement backend and the reset implementation are Absent, and their interface is Open. Only the request group `Measure` is declared, answered by nothing; what `measure` measures is part of the open interface, and its signature is to be revisited with it (N3).
8. **Modules.** A program is one file. A seal other than Root's needs a place that holds it, which is a module. Type parameters are set aside until the boundaries of the existing language are settled (P7).
9. **What an answer that takes `refuse` may reply.** Recording a refusal is built: what ran inside is aborted, and it must compute `()`. Substituting a result, so that the refused computation goes on, needs a rule for when the class of the rule that refused is unchanged.
10. **Whether `Object` should own a request.** As ruled it has no clause and delegates everything to Root.
11. **Whether every request made inside an answer should resolve outward from it.** Only the `Witness` path is ratified. Other requests resolve from the innermost installed answer, so two installed answers can ask each other without end; such a run is refused at the depth bound.
12. **The identity under which code runs, from inside the language.** Deferred by ruling (XII.1).
13. **Decisions inside the lower bound.** A decision is charged by the answers installed (VII.5), so the ways it can be settled are charged the lengths of a code. Whether the world's reply can be brought inside the obligation is open.

### XII.6 Decisions awaiting a ruling

Earlier decisions are rulings: C1 to C5, D1 to D9, E1 to E9, F1 to F7, G1 to G6, H1 to H6, J1 to J7, K1 to K6, L1 to L6, N1 to N3, R9 to R11 and T1 to T4 (XII.1). None of the following is itself ruled: the toolchain behaves as stated, and each stands as Proposed until ruled.

Taken while building 0.4.8, for the declaration and program forms:

| # | Decision | Where | The alternative |
|---|---|---|---|
| M1 | The form types are declared in the prelude's text, `Code` among them. The toolchain no longer holds a table of `Code`'s constructors | VIII.1 | Building them in the toolchain, as `Code` was: a second place where the language's forms are defined |
| M2 | A list is `Parts`, and a declaration held as a value writes each of its lists so. The parser's own writing, with as many children as members, stays what the toolchain works on, and the toolchain goes between the two | VIII.1 | One writing for both, which means either the parser writing lists as parts or clauses matching any number of children |
| M3 | `Code` gains a constructor for every form the parser already wrote and no rule could match: the logical and comparison operators, `Index`, `Field`, `Undo`, `Quote`, `Decide`, `Request`, `Ask`, `Send`, `Instance`, `With`, `Set`, `Output`, `Commit`, `Do`, `RepeatWhile`, and `Tupled`. Their names join the prelude's, which a program may not declare again | VIII.1 | Leaving them out, with the census reporting them as escaping |
| M4 | `sequence` and `block` write all of the code, tuples included, not only the blocks of steps. Quoted code and literals are left as they are | VIII.2 | A separate pair of built-ins for tuples |
| M5 | A field of a constructor is held as `Slot`, because `Field` is the expression `x.f` | VIII.1 | One name for both, which a nominal type cannot have |
| M6 | `definition` gives rules and answers as they run and types and request groups as written; `program()` gives the program as written and leaves out the prelude | VIII.1, VIII.2 | The program with the prelude before it; or everything as written, with the elaborated code under another built-in |
| M7 | The census counts a constructor as taken apart when a one-clause rule for it matches a node and binds its fields, and as put together when that clause rebuilds the node. Its nodes are every declaration as written and every derived inverse as it runs. The state of a run is listed as not being a form | VIII.1 | A census of declared types only, which would not show a form the parser writes and no type declares |
| M8 | `derivative`'s `Name` clause gives `Literal(d)` with `d` a counted `I64`, so its result is evaluated at an integer. A clause cannot choose between two right sides by a condition | VIII.2 | A way for a clause to bind one name in both branches of an `if`, which would let it give `Literal(1)` or `Literal(0)` as written |

Taken in entering T1 to T4, and while building 0.4.9. T5 and Q13 were recommended for ratification in review, T5 with the qualification that its proof show the entries of the runs sharing a result to be uniquely decodable:

| # | Decision | Where | The alternative |
|---|---|---|---|
| T5 | The lower bound is stated as Kraft's inequality over the runs that share a result, with the bound of ⌈log₂ N⌉ holding for the largest charge | VII.5 | A bound of ⌈log₂ N⌉ on every run's charge. The charges do not meet it: three inputs that share an output are charged 1, 2 and 2 |
| Q13 | A decision is charged 1 + ⌈log₂(n + 1)⌉, n being the answers installed for `Decide`, however many were asked. The ways it can be settled are then charged the lengths of a code | VII.5 | By the answers asked, as 0.4.8 charged: with fifteen answers or more installed, not a code |
| U1 | A `Trit` is refused wherever a value meets a declared `Bool`: input, parameter, result, field, request argument, answer reply and state, the value `set` gives, the other side of a `swap`, and a name given back | II.4 (R1), III.1 | Refusing it only where a `decide` reads such a name, which would leave `maybe` in names declared `Bool` |
| U2 | `Trit(b)` gives a `Bool` as a `Trit`, unchanged, as `U8(x)` converts. `set` on a `Trit` to a `Bool` is elaborated with it | III.1, V.5 | A conversion used by elaboration alone, with no name a program can write |
| U3 | `set` writes its value in the type of the cell: a literal as the cell's word, a `Bool` as a `Trit`. Where the value has a narrower type that cannot be written so, as `(0, true)` set to a `(U8, Trit)`, the program is refused with a reason | V.5 | Refusing `set` to a literal on a word narrower than `I64`, where `U8(0)` is the way to write it |
| U4 | A literal given as a clause rule's input or parameter is of the type declared there, in the interpreter as in compiled code | III.1, VII.5 | Holding it at a literal's width until it meets another word |
| U5 | A rule that, read backward, would put a `Trit` where a `Bool` is declared is refused as written, with the reason its inverse gives | V.6 | Treating it as a failure of the toolchain, as for other inverses that fail to check |

Defects found while building 0.4.2 to 0.4.9, and after it, and corrected:

| Defect | Present in | Found by | Now |
|---|---|---|---|
| A copy of an answer instance shared its state's arrays with the original: after `y is x`, a message to `x` changed `y`, directly and through records and tuples. Values are owned and copied, never shared (III.2) | 0.4.9 and earlier | A conformance test of the CCNOT tape, which is an instance holding arrays | Copied with its state (TestBuiltValues.test_a_copied_instance_shares_nothing) |
| A text holding a NUL byte printed the NUL in the interpreter and an empty line in compiled code, which holds a text as a C string | 0.4.9 and earlier | Review of 0.4.9 | Refused alike by `check`, `run` and `build` (TestC23Backend.test_text_is_the_same_bytes_in_both_backends) |
| `selvage check` printed an answer as `bijection` with no extent, though its rules may be embeddings: a deposit replies `Deposited` and never `Withdrew` | 0.4.7 to 0.4.9 | Review of a certified answer whose rule is an embedding | Each answer rule's extent is reported (TestExtent.test_an_answer_s_rules_report_their_extent) |
| A name given back against an expression that reads it, `n was 0 + n`, passed the checker's reading of the rule and failed in its derived inverse, ending the check with an internal failure and no refusal | 0.3.4 to 0.4.7 | Writing a program that uses every form, for the census | Refused, with its reason (TestDeclarations) |
| `evaluate` given a step ended the interpreter with an error of its own and no refusal | 0.3.4 to 0.4.7 | The test that holding a declaration grants nothing | Refused: `evaluate` runs an expression (VIII.2) |
| This description said every expression was a form; twenty-four forms the parser writes were no constructor of `Code`, and no rule could match `a and b` | 0.3.2 to 0.4.7 | The form census | Each is a constructor (VIII.1, M3) |
| A name already bound could be bound again in an expression rule, by `is` or inside a block. The interpreter and compiled code then disagreed: for a rebinding the C build failed; for a binding inside a block the interpreter printed the inner value after the block and compiled code the outer one | 0.3.4 to 0.4.5 | Writing the scope cases that alpha-equivalence must preserve | Refused by the checker (IV, J1) |
| A loop counter could take the name of a parameter, or of the counter of the loop around it. The outer name was lost to the rest of the rule; one arrangement made the checker fail on a rule's derived inverse. With a name already bound in an expression rule, the interpreter refused the run and compiled code ran it | 0.3.4 to 0.4.5 | The same cases | Refused by the checker (IV, J1) |
| A `Trit` was accepted where a `Bool` is declared, at fifteen of the sixteen sites where a value meets a declared type; only an instance's state refused it. A name declared `Bool` could hold `maybe`, so a rule the checker certified could decide a `Trit`: `(t, b) <-> (t, b, d) where swap t and b; d is decide b` asked on `(maybe, true)`, kept a `Decided` entry, and its `undo` refused its output, against Part 2 of XI.3. The theorem for the model stood; the claim that the checker meets O1 did not. A dropped value declared `Bool` was charged 1 or 2 bits by what it held, which is not a code | 0.3.4 to 0.4.8 | Checking the assumptions of a proof of the lower bound | Refused at every site, with its reason (U1) |
| A request's arguments, and an answer's reply and state, were not compared with the types declared for them: a `Text` was accepted where an `I64` is declared | 0.3.4 to 0.4.8 | Correcting the defect above | Refused (U1) |
| A literal given where a narrower word is declared kept a literal's width in the interpreter. Its arithmetic was the declared type's, but dropped it was charged 64 bits where compiled code charged 8, so the backends reported different ε | 0.4.0 to 0.4.8 | Checking the assumptions of a proof of the lower bound | Of the declared type (U4); ε the same in both backends |
| `set n to 0`, with `n` a word narrower than `I64`, ended the check with an internal failure and no refusal | 0.4.0 to 0.4.8 | The same | Written in the cell's type (U3) |
| The value `set` replaced in a `Trit` was charged as a `Bool`: 1 bit for true or false, 2 for maybe | 0.4.0 to 0.4.8 | The same | Charged as a `Trit`, 2 bits (U2, U3) |
| A lossy rule that changed an input, or copied it, and then discarded it could not be compiled: its derived inverse gave a value it takes back no type, and recorded that over the type of an expression the two directions share | 0.4.0 to 0.4.8 | Extending the accounting generator | A value taken back has the type it had when discarded; compiled code agrees with the interpreter on ε |
| A literal inside a constructor, on a side that is built, kept the type of a literal instead of the type its field declares: `(b, Lamp(1, Red)) <-> b` run backward gave a `Lamp` whose first field was an `I64` where the type says `Bit`. The value printed alike and was not the same value | 0.3.4 to 0.4.6 | The accounting generator, whose rewinds compare canonical forms | A literal takes the type of its place, inside a constructor as elsewhere (TestBuiltValues) |
| The two backends disagreed on ε for a dropped `Trit` holding true or false (1 bit in the interpreter, 2 in compiled code) and for a dropped `Text` (8 bits a byte in the interpreter, nothing in compiled code) | 0.4.0 to 0.4.6 | Stating one definition of the charge for both backends (K2) | Both charge by the definition of VII.5 (TestC23Backend.test_the_backends_charge_alike) |
| An uncompute was marked proved, and its check omitted, when its pattern rearranged the pattern that bound it: `(b, a) was (x, y)` after `(a, b) is (x, y)`. A rule could be certified whose `undo` returned a wrong value: on the 36 such generated rules that 0.4.1 certified, its `undo` failed to return the input in 171 of 188 runs | 0.3.4 to 0.4.1 | Stating obligation O5 for the proof (XI.3) | Proved only in the pattern that bound it; otherwise checked when it runs (V.5) |
| A host could copy what it read into its own state and give its copy back, leaving the answers further out as if nothing had been disclosed | 0.4.1 | The E8 qualification | Refused by the checker (VII.2) |
| The interpreter ran a self tail call as recursion, though the description said it was a loop | 0.4.1 | Building the depth bound | A loop in both backends (V.3) |
| Every generator counted a refused program as a refusal its oracle might have expected, so a toolchain that refused its own prelude passed them all | 0.4.0 to 0.4.2 | A mutation of `mirror` that the checker refuses | Each generator first requires the prelude to be accepted (XI.2) |
| Replay looked through its record for a decision with the same question and context, so records could answer out of order | 0.4.2 to 0.4.3 | The ruling on F5 | The next record or a refusal (VI.4) |
| Compiled code crashed where the interpreter refused a run for its depth | 0.4.1, where it was listed as not covered | The ruling on E9 | Refused alike (III.5) |

---

## Sources

- Bennett, C. H. (1973). Logical reversibility of computation. *IBM Journal of Research and Development* 17(6), 525–532.
- Cuccaro, S. A., Draper, T. G., Kutin, S. A., & Moulton, D. P. (2004). A new quantum ripple-carry addition circuit. arXiv:quant-ph/0410184.
- Dekorte, S. Io programming language, repository and release notes (2025–2026). https://github.com/IoLanguage/io
- Kleene, S. C. (1952). *Introduction to Metamathematics*. North-Holland. §64, the strong three-valued logic.
- Kloeden, P. E., & Platen, E. (1992). *Numerical Solution of Stochastic Differential Equations*. Springer.
- Levesque, D., & Verlet, L. (1993). Molecular dynamics and time reversibility. *Journal of Statistical Physics* 72, 519–537.
- Stefik, A., & Siebert, S. (2013). An empirical investigation into programming language syntax. *ACM Transactions on Computing Education* 13(4), 19.
- Toffoli, T. (1980). Reversible computing. *ICALP 1980*, LNCS 85, 632–644.
- Yokoyama, T., & Glück, R. (2007). A reversible programming language and its invertible self-interpreter. *PEPM 2007*.
- ISO/IEC 9899:2024 (C23), §7.20 `<stdckdint.h>`.
