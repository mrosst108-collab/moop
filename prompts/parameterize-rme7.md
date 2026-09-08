# Filling the RME-7 slots

Seven protos are preopened in the world, one per RME-7 primitive:
`jsharp`, `gsharp`, `gtildesharp`, `sigma`, `f`, `kappa`, `gamma`. Each is
a **slot**: an ordinary proto with a body and no messages. To parameterize
a primitive, teach its slot. `examples/rme7.moop` teaches all seven from
the relay's offices (`asdg-rme7.md` §3.1); load it into a session with

```sh
cat examples/rme7.moop - | ./build/moop
```

| slot | office (relay) | teaching | what it does in moop |
|------|----------------|----------|----------------------|
| `jsharp` | conservative circulation | `ask maybe` | steps the body one reversible tick; the answer is the observed bit |
| `gsharp` | dissipative; the only office that converges | `0` | the answer forgets the input entirely: maximal dissipation, a fixed point |
| `gtildesharp` | confinement without convergence | `mirrors 1` | an involution on the body: twice is identity, so the value stays on a two-point level set and never converges |
| `sigma` | stochastic driving, intra-track | `ask maybe` | the replayable draw |
| `sigma` | port coupling `Σ_ij` | `mirrors port` | exchanges bodies with `port`: cross-track relation carried on the port, gate-backed |
| `f` | generator-level self-modification | `a f` | births a fresh proto from itself — moop's only way to change behavior is to generate anew and rebind, never to re-parent |
| `kappa` | integrity gate | `inherits port` | admits by provenance: the slot passes, a slot born from it does not |
| `gamma` | derived, `[G♯, G̃♯]`, not an operator | confine, then converge | a trajectory through the other two; answers what converged, has no value of its own |

A slot's body is a track (state on the tapes); what you teach is its
generator. Slots born from a slot (`s is a sigma`) inherit what it was
taught and may override. Until taught, a slot says so: `nothing in the
lineage hosts "drive"`.

Rules, from `rosst-cp-v6.md` §7 and `asdg-rme7.md`:

- Retrieve the spec; do not reconstruct operator semantics. §3 is
  unpopulated, so no teaching makes a slot *be* its primitive — it makes
  the slot answer as taught. The table above is role-plus-constraint at
  most, and says so.
- Teach from the surface language. Do not host C messages, verdicts, or
  tables on a slot.
- Do not add a slot, a second Σ, or a coupling path: coupling is `<->`.
- Report what was taught, not what was "implemented".
