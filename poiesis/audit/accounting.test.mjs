import { accounting } from './accounting.mjs';
const ok = (r) => ({ id: r, failed: false, confirmed: [], unresolved: [] });
const cases = [
  ['all verification stages crashed (THE ORIGINAL DEFECT)', accounting([null,null,null],'c',3), 'incomplete'],
  ['one audit agent returned no result',                    accounting([ok('Q1'),null],'c',2), 'incomplete'],
  ['a verifier failed on a finding',                        accounting([{id:'Q1',failed:false,confirmed:[],unresolved:[{finding:{title:'x'}}]}],'c',1), 'incomplete'],
  ['completeness critic produced no result',                accounting([ok('Q1')],null,1), 'incomplete'],
  ['audit agent flagged itself failed',                     accounting([{id:'Q1',failed:true,confirmed:[],unresolved:[]}],'c',1), 'incomplete'],
  ['POSITIVE CONTROL: clean run, no findings',              accounting([ok('Q1'),ok('Q2')],'c',2), 'complete'],
  ['POSITIVE CONTROL: clean run with a confirmed finding',  accounting([{id:'Q1',failed:false,confirmed:[{title:'real'}],unresolved:[]}],'c',1), 'complete'],
];
let pass=0, fail=0;
for (const [name, got, want] of cases) {
  const statusOk = got.status === want;
  const fieldOk = want === 'complete' ? Array.isArray(got.confirmed) : got.confirmed === undefined;
  if (statusOk && fieldOk) { pass++; console.log(`ok   - ${name}  [status=${got.status}, confirmed=${got.confirmed===undefined?'ABSENT':'present'}]`); }
  else { fail++; console.log(`FAIL - ${name}  [status=${got.status} want=${want}, confirmed=${got.confirmed===undefined?'ABSENT':'present'}]`); }
}
console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail ? 1 : 0);
