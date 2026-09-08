# Filling the RME-7 slots

Seven protos are preopened in the world, one per RME-7 primitive:
`jsharp`, `gsharp`, `gtildesharp`, `sigma`, `f`, `kappa`, `gamma`. Each is
a **slot**: an ordinary proto with a body and no messages. To parameterize
a primitive, teach its slot:

```
sigma ask drive is ask maybe
kappa ask admit is
    ask maybe

sigma ask drive
```

A slot's body is a track (state on the tapes); what you teach is its
generator. Slots born from a slot (`s is a sigma`) inherit what it was
taught and may override. Until taught, a slot says so: `nothing in the
lineage hosts "drive"`.

Rules, from `rosst-cp-v6.md` §7 and `asdg-rme7.md`:

- Retrieve the spec; do not reconstruct operator semantics. §3 is
  unpopulated, so no teaching makes a slot *be* its primitive — it makes
  the slot answer as taught. Say so: role-plus-constraint at most.
- Teach from the surface language. Do not host C messages, verdicts, or
  tables on a slot.
- Do not add a slot, a second Σ, or a coupling path: coupling is `<->`.
- Report what was taught, not what was "implemented".
