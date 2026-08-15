/* The audit harness's failure accounting, extracted so it is testable
 * WITHOUT spending agents.  What failed in the first audit run was not an
 * agent but this logic: crashed stages produced nulls, and nulls read as
 * "no findings".  Kept in step with conformance-audit.js. */
export function accounting(rows, criticResult, questionCount) {
  const failures = [];
  const note = (stage, what) => failures.push(`${stage}: ${what}`);

  for (const a of rows) if (!a) note('audit', 'a pipeline item produced no result');
  const kept = rows.filter(Boolean);
  if (kept.length !== questionCount)
    note('audit', `${questionCount - kept.length} question(s) produced nothing`);
  for (const r of kept) if (r.failed) note('audit', `${r.id} failed`);
  for (const r of kept)
    for (const u of (r.unresolved || []))
      note('refute', `verifier failed for "${u.finding.title}" -- unresolved`);
  if (!criticResult) note('critic', 'completeness critic produced no result');

  const confirmed  = kept.flatMap((r) => r.confirmed  || []);
  const unresolved = kept.flatMap((r) => r.unresolved || []);

  /* `confirmed` is ABSENT unless the run completed, so a caller reading only
   * that field cannot mistake a broken run for a clean one. */
  return failures.length === 0
    ? { status: 'complete', confirmed, unresolved, failures: [] }
    : { status: 'incomplete', failures,
        partial_confirmed: confirmed, partial_unresolved: unresolved,
        note: 'An incomplete audit is not a negative audit result.' };
}
