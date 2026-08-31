# rme7py — the RME-7 primitives as a warranted class hierarchy

Python 3.11+, no dependencies.

```sh
python3 -m unittest discover -s tests -t . -q
```

## The state-space variant this is built against

```
dX_i = ( J_i♯(dH_i) − G_i♯(dH_i) − G̃_i♯(dΦ_i) ) dt
       + Σ_ii ∘ dW_i + Σ_{j≠i} Σ_ij(X_j → X_i) ∘ dW_ij

dθ_i = F_i( X_i, θ_i, Φ_i, κ_i, Ψ_i ) dt
```

with `Σ_ij = A_i ∘ κ_i ∘ T_ij` and `γ = [G♯, G̃♯]`. The state equation has
**two positions** — the metriplectic triple under `dt`, `Σ` under `dW` — and
the drift operators differ in **operand**: `J♯(dH)` and `G♯(dH)` consume the
same one-form, `G̃♯(dΦ)` does not.

## The rule this hierarchy obeys

> A class may subclass another only when a **recorded** property distinguishes
> the child from its siblings.

A hierarchy over the seven slots is exactly where an implementation
convenience becomes grammar: pick a nesting and you have silently asserted a
dependency order.

**Four properties are recorded, and they are not enough.**

| property | values | source | basis |
|---|---|---|---|
| **kind** | operator · admissibility · invariant | the retrieved ontology | recorded |
| **position** | drift of X · diffusion of X · drift of θ | the canonical form | recorded |
| **operand** | `dH` · `dΦ` · `dW` | the canonical form | recorded |
| **index** | diagonal · off-diagonal | the canonical form | recorded |
| **algebra** | antisymmetric · positive semidefinite | the removal witnesses | **derived** |

Grouping the seven leaves by the four recorded properties leaves **exactly one
collision: `J♯` and `G♯`.** Both are operators, both stand in the drift of `X`,
both consume `dH`, and neither carries an object index. Nothing the format
*states* tells them apart.

Only the fifth separates them, and it is **derived rather than recorded** — it
follows from the recorded removal witnesses, since `⟨v, Mv⟩ = 0` for all `v`
iff `M` is antisymmetric and `⟨v, Mv⟩ ≥ 0` iff `M` is positive semidefinite.
The witness is the ground; the algebraic form is what the witness entails.

That distinction is kept rather than smoothed over, because it is the
difference between a property the format states and one an argument supplies,
and collapsing them would let a derivation pass as a record. A test asserts
that every class declaring an algebra names the witness it derives from.

Worth noticing which pair it is: `J♯` and `G♯` are also the pair the equation
groups by shared operand, and the pair a metriplectic system consists of.
Their whole distinction is carried by their witnesses.

Every class states its own `WARRANT`, and a test fails if any class merely
inherits its parent's — so nothing enters the hierarchy without saying why.

```
Primitive
├── Operator                          kind: an additive term
│   ├── StateOperator                 position: stands in dX
│   │   ├── DriftOperator             position: under dt
│   │   │   ├── EnergyDrift           operand: dH
│   │   │   │   ├── ConservativeTransport   J♯   antisymmetric
│   │   │   │   └── DissipativeDescent      G♯   positive semidefinite
│   │   │   └── PurposeDrift          operand: dΦ
│   │   │       └── TeleologicalConfinement G̃♯  antisymmetric
│   │   └── DiffusionOperator         position: under dW
│   │       ├── SelfNoise                   Σ_ii
│   │       └── Channel                     Σ_ij = A ∘ κ ∘ T
│   └── GeneratorOperator             position: stands in dθ
│       └── AutopoieticFeedback             F
├── AdmissibilityStructure            kind: a gate, not a term
│   └── StructuralAdmissibility             κ
└── Invariant                         kind: in no equation
    └── PathDependence                      γ = [G♯, G̃♯]
```

```python
>>> ConservativeTransport.depth()
6
>>> for name, why in ConservativeTransport.warrants(): ...
Primitive              the seven typed format-level slots
Operator               KIND: appears as an additive term in the equations
StateOperator          POSITION: stands in dX
DriftOperator          POSITION: under dt -- the deterministic part of dX
EnergyDrift            OPERAND: applied to dH, the energy one-form
ConservativeTransport  ALGEBRA: antisymmetric, so Hdot = 0 -- it conserves H
```

## What the hierarchy deliberately does not do

**No leaf subclasses another leaf.** `J♯` is not a parent of `G♯`. Branching is
by property, never by one primitive depending on another — the dependency
orderings on record disagree with each other, and none of them is grammar.

**κ and γ are not `Operator`s.** So no code path can treat a gate or an
invariant as an additive term. The format's rule is enforced by the type
system rather than checked at runtime.

**`F` is not a `StateOperator`.** Putting `F` in `dX` turns generator change
into state forcing, and here it is unspellable.

**`Σ` is one slot with two instance classes.** Splitting it into two
primitives would corrupt the 5 + 1 + 1 count. `SelfNoise` and `Channel`
subclass one `DiffusionOperator`, which says exactly what is meant — same
slot, two typed instances — and is the one place where classes express
something a flat enumeration could not.

## The witnesses

Three rows of the removal matrix are statements of linear algebra and nothing
more, so they are executed rather than tabulated:

```
Hdot   = 0     under an antisymmetric J♯      circulation is not descent
Hdot  <= 0     under a positive-semidefinite G♯
Phidot = 0     under an antisymmetric G̃♯      confinement is not descent
```

These are **mathematical witnesses, not an RME-7 realization.** They establish
that the declared algebraic forms have the consequences claimed for them. They
establish nothing about what `J♯` *is* — the operator semantics remain
unpopulated, and no amount of linear algebra supplies them.

The positive-semidefinite test checks **every** principal minor, not only the
leading ones: `diag(0, −1)` has both leading minors zero and is indefinite, so
a leading-minors test would wrongly accept it. There is a test for that.
