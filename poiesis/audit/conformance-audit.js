export const meta = {
  name: 'poiesis-conformance-audit',
  description: 'Audit the poiesis substrate against the 12 specification audit questions, adversarially verifying each finding',
  whenToUse: 'Run after substantive changes to src/rme/. Reports INCOMPLETE rather than clean when any stage fails.',
  phases: [
    { title: 'Audit', detail: 'one agent per audit question, hunting for bypasses' },
    { title: 'Refute', detail: 'two skeptics per finding, prompted to refute' },
    { title: 'Critic', detail: 'what was not examined' },
  ],
}

/* ---------------------------------------------------------------------------
 * FAILURE SEMANTICS — the reason this file exists in the repository.
 *
 * The first run of this audit returned `confirmed: []`.  That was not a clean
 * bill of health: the verification stage had crashed on a scripting error
 * (promises passed to parallel(), which takes thunks) and every finding was
 * dropped to null.  An empty result and a total apparatus failure were
 * indistinguishable at the call site.
 *
 * A harness that converts agent failure into an empty finding set violates
 * exactly the non-vacuity principle the substrate exists to enforce.  So:
 *
 *     AN INCOMPLETE AUDIT IS NOT A NEGATIVE AUDIT RESULT.
 *
 *     successful verification  -> finding may be confirmed or refuted
 *     verification failure     -> UNRESOLVED   (never "refuted")
 *     agent failure            -> AUDIT FAILURE
 *     missing result           -> AUDIT FAILURE
 *     empty result             -> meaningful ONLY if every required stage ran
 *
 * Accordingly this script returns a `status` field before anything else, and
 * `status: "complete"` is reachable only when no stage failed.  A reader who
 * checks nothing but `confirmed` still cannot mistake a broken run for a
 * clean one, because `confirmed` is absent unless the run completed.
 * ------------------------------------------------------------------------- */

const ROOT = '/home/user/moop/poiesis'

const CONTEXT = `
You are auditing a C23 substrate at ${ROOT}. Read the ACTUAL CODE; do not reason from description.

  src/rme/port.h        X-macro port schema, RmePortStatus {UNDEFINED,ACTIVE,VESTIGIAL}
  src/rme/proto.*       RmePrototype record, uniform port access
  src/rme/contract.*    per-port active/vestigial contracts, compatibility, elision permission
  src/rme/conform.*     rme7_conforms() - Axis A
  src/rme/bind.*        BindValid(T): Reads(T) vs Fields(ArgType(T))
  src/rme/compose.*     rme_admissible() and rme_compose_valid() - Axis B
  src/rme/nest.*        NestedValid
  src/rme/graph.*       rme_project(), rme_graph_scc(), rme_graph_has_cycle()
  src/rme/classify.*    rme_classify() - Axis C
  src/rme/schedule.*    rme_envelope/rme_dispatch, SCC groups
  src/rme/actor.*       RmeActor, RmeCapability, RmeConstructionContext (Grant)
  src/rme/validate.*    OPAQUE RmeValidated, rme_validate() - THE validation boundary
  src/awv/awv.*         AWV as a client (src/rme/ must not depend on it)
  tests/                94 passing tests; tests/negative/ four must-not-compile files
  SPEC.md               the normative specification

Invariants claimed:
  F2  Status(p) in {ACTIVE, VESTIGIAL}; UNDEFINED=0 is a construction sentinel only
  F5  no connection relation may be INFERRED from coexistence, nesting, name equality or order
  F6  "RME-7-conformant" and "classified RME-7" are distinct predicates
  F7  prototype validity/conformance are NONHEREDITARY
  F8  an actor's authority/capability/provenance confers NO validation or conformance
  F9  bidirectional: capability does not establish validity; validation grants no authority
  F10 authority, provenance and semantic predicates are distinct typed relations
  Participates(p,R_C) => Status(p) = ACTIVE, unconditional
  Admissible != Declared != Executed; Admissible does NOT imply Declared
  Elision removes from DISPATCH, never from ENVELOPE
  A released validated handle must never become valid for a later object

AUDIT STANDARD: ask whether an INVALID STATE CAN BYPASS A CHECK, not whether the happy path works.
Look for paths reaching a guarded state without passing the guard; checks that pass vacuously;
silent wrong answers (a failure reported as a valid verdict); type signatures permitting contract
violation; and any place a test would still pass if the invariant were deleted.

Report only defects you can point to in specific code. An empty list is a valid, useful result.
Do NOT report style, naming, or missing features.
`

const FINDINGS = {
  type: 'object',
  properties: {
    question: { type: 'string' },
    findings: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          title: { type: 'string' },
          file: { type: 'string' },
          line: { type: 'integer' },
          bypass: { type: 'string' },
          evidence: { type: 'string' },
          category: { type: 'string', enum: ['implementation-defect','test-defect','underspecification','frozen-contradiction','overstated-claim'] },
          severity: { type: 'string', enum: ['high','medium','low'] },
        },
        required: ['title','file','bypass','evidence','category','severity'],
      },
    },
  },
  required: ['question','findings'],
}

const VERDICT = {
  type: 'object',
  properties: { refuted: { type: 'boolean' }, reason: { type: 'string' } },
  required: ['refuted','reason'],
}

const QUESTIONS = [
  { id: 'Q1',  q: 'Where is each invariant REPRESENTED? Find any claimed invariant with no representation in any type or function.' },
  { id: 'Q2',  q: 'Where is each invariant VALIDATED? Find any invariant represented but never checked on any path.' },
  { id: 'Q3',  q: 'What is the FIRST POINT at which invalid external data can enter? Enumerate public entry points taking caller-supplied data and identify which lack validation.' },
  { id: 'Q4',  q: 'Can invalid external data BYPASS validation? Trace every route to a validated state and find one skipping rme_validate().' },
  { id: 'Q5',  q: 'At what boundary does an object acquire the validated-prototype type, and can any path reach it without crossing? Scrutinise validate.c: opacity, the arena, monotonic allocation, epoch checks, rme_validated_proto.' },
  { id: 'Q6',  q: 'Can an optimizer/elision path destroy a required boundary distinction? Examine schedule.c. NOTE: the E_dispatch subset-of E_envelope check is KNOWN to be structurally vacuous; do not re-report it, look for anything else.' },
  { id: 'Q7',  q: 'Can the API expose an operation whose TYPE permits violating its contract? Look for void*, non-const self on queries, out-params left uninitialised on refusal, enums accepting out-of-domain values.' },
  { id: 'Q8',  q: 'Can classification MUTATE or ESTABLISH conformance? Check rme_classify and callees for writes to prototype state or paths where classification influences rme7_conforms.' },
  { id: 'Q9',  q: 'Can composition be INFERRED where no R_C was declared (F5)? Check compose.c for coexistence, name equality, adjacency or ordering treated as a connection.' },
  { id: 'Q10', q: 'Can a VESTIGIAL endpoint enter R_C? Verify the ACTIVE requirement on every path, both sides, including empty relation, duplicate edges, self-composition P==Q.' },
  { id: 'Q11', q: 'Can an undeclared transition dependency enter without changing ArgType? Check bind.c for ways a read counts as represented when it is not.' },
  { id: 'Q12', q: 'Can the classifier obtain information the declared interface does not expose? Check rme_classify/rme_project for statics, globals, reentrancy and aliasing.' },
]

const failures = []
function note(stage, what) { failures.push(`${stage}: ${what}`); log(`FAILURE ${stage}: ${what}`) }

phase('Audit')
const audited = await pipeline(
  QUESTIONS,
  (item) =>
    agent(`${CONTEXT}\n\nAUDIT QUESTION ${item.id}:\n${item.q}\n\nRead the relevant sources thoroughly. Return findings for this question only.`,
          { label: `audit:${item.id}`, phase: 'Audit', schema: FINDINGS })
      .then((r) => {
        /* A null result is an AGENT FAILURE, not "no findings". */
        if (!r) { note('audit', `${item.id} returned no result`); return { id: item.id, failed: true, findings: [] } }
        return { id: item.id, failed: false, findings: r.findings || [] }
      }),
  (res) => {
    if (res.failed || res.findings.length === 0) return { ...res, confirmed: [], unresolved: [] }
    /* parallel() takes THUNKS, not promises.  Passing promises is what broke
     * the first run and silently emptied every finding set. */
    return parallel(res.findings.map((f) => () =>
      parallel([
        () => agent(`${CONTEXT}\n\nA prior auditor claims this DEFECT:\n\nTITLE: ${f.title}\nFILE: ${f.file}\nBYPASS: ${f.bypass}\nEVIDENCE: ${f.evidence}\n\nREFUTE it. Read the actual code. Is the claimed bypass reachable through the PUBLIC API as written? A claim is wrong if the guard exists elsewhere on the path, the type system prevents it, it requires undefined behaviour or editing src/, or it misreads the invariant. Default refuted=true when uncertain.`,
                     { label: `refute:${item_label(f)}`, phase: 'Refute', schema: VERDICT }),
        () => agent(`${CONTEXT}\n\nA prior auditor claims this DEFECT:\n\nTITLE: ${f.title}\nFILE: ${f.file}\nBYPASS: ${f.bypass}\nEVIDENCE: ${f.evidence}\n\nREPRODUCIBILITY lens: can you write a concrete C snippet using ONLY the public headers, without editing src/, that exhibits the claimed invalid state? If you cannot construct one, refuted=true. If you can, give the snippet.`,
                     { label: `repro:${item_label(f)}`, phase: 'Refute', schema: VERDICT }),
      ]).then((vs) => {
        /* A verifier that failed leaves the finding UNRESOLVED.  It is never
         * silently treated as refuted, and never dropped. */
        if (vs.some((v) => !v)) {
          note('refute', `verifier failed for "${f.title}" (${f.file}) -- finding unresolved`)
          return { finding: f, state: 'unresolved' }
        }
        return { finding: f, state: vs.every((v) => !v.refuted) ? 'confirmed' : 'refuted',
                 verdicts: vs.map((v) => v.reason) }
      })
    )).then((rs) => {
      if (rs.some((r) => !r)) note('refute', `${res.id}: a verification thunk threw`)
      const good = rs.filter(Boolean)
      return {
        ...res,
        confirmed:  good.filter((r) => r.state === 'confirmed'),
        unresolved: good.filter((r) => r.state === 'unresolved'),
      }
    })
  }
)

function item_label(f) { return (f.file || 'unknown').split('/').pop() }

for (const a of audited) { if (!a) note('audit', 'a pipeline item produced no result') }
const rows = audited.filter(Boolean)
if (rows.length !== QUESTIONS.length) note('audit', `${QUESTIONS.length - rows.length} question(s) produced nothing`)
for (const r of rows) { if (r.failed) note('audit', `${r.id} failed`) }

const confirmed  = rows.flatMap((r) => r.confirmed  || [])
const unresolved = rows.flatMap((r) => r.unresolved || [])

phase('Critic')
const critic = await agent(
  `${CONTEXT}\n\nTwelve audit questions were run. ${confirmed.length} findings survived two independent refutation attempts; ${unresolved.length} could not be verified.\n\nConfirmed:\n${JSON.stringify(confirmed, null, 2)}\n\nYou are the COMPLETENESS CRITIC. What was NOT examined? Name specific files, functions or invariant classes no question covered, and any SPEC.md claim with no corresponding check in code or tests. Cite paths. This is a list of gaps, not a summary.`,
  { label: 'completeness-critic', phase: 'Critic' }
)
if (!critic) note('critic', 'completeness critic produced no result')

/* `status` comes first and gates everything.  `confirmed` is present ONLY on a
 * complete run, so an incomplete audit cannot be read as a clean one even by a
 * caller who inspects nothing else. */
const complete = failures.length === 0
log(complete
  ? `audit COMPLETE: ${confirmed.length} confirmed, ${unresolved.length} unresolved`
  : `audit INCOMPLETE: ${failures.length} stage failure(s) -- results are NOT a negative result`)

return complete
  ? { status: 'complete', confirmed, unresolved, critic, failures: [] }
  : { status: 'incomplete', failures, partial_confirmed: confirmed, partial_unresolved: unresolved,
      note: 'An incomplete audit is not a negative audit result. Do not read this as a clean run.' }
