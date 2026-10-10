// Model-free import/export logic tests with a stub DOM, not a browser test.
// All generated responses below are artificial and remain in memory only.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const path = require('node:path');

async function test() {
  const source = fs.readFileSync(path.join(__dirname, 'R01/stage2.html'), 'utf8');
  const script = source.match(/<script>\n([\s\S]*?)\n<\/script>/)[1];
  const initial = JSON.parse(script.match(/let packet = ([\s\S]*?);\nfunction fill/)[1]);
  const elements = new Map();
  function element(id) {
    if (!elements.has(id)) elements.set(id, { value:'', checked:false, textContent:'' });
    return elements.get(id);
  }
  let downloads = 0;
  const context = vm.createContext({
    document: { getElementById: element, querySelectorAll:()=>[], createElement:()=>({click:()=>downloads++}) },
    crypto: crypto.webcrypto, Blob, URL:{createObjectURL:()=> 'blob:software-check-only', revokeObjectURL:()=>{}},
    Uint8Array, Map, Array, String, Number, Date, JSON, Error,
  });
  vm.runInContext(script, context);
  vm.runInContext('save()', context);
  assert.equal(downloads,0);
  assert.match(element('message').textContent,/Import your completed stage1/);
  const dummy = JSON.parse(JSON.stringify(initial));
  dummy.stage = 1;
  async function submit(payload) {
    const raw = JSON.stringify(payload);
    const buffer = new TextEncoder().encode(raw).buffer;
    await element('import').onchange({target:{files:[{text:async()=>raw, arrayBuffer:async()=>buffer}]}});
  }
  await submit(dummy);
  assert.match(element('message').textContent,/Attest only after/);
  dummy.independent_solve_before_gold=true;
  dummy.completed_at_utc='2026-10-10T00:00:00Z';
  await submit(dummy);
  assert.match(element('message').textContent,/Finish and timestamp/);
  // Dummy content is deliberately NOT real reviewer work or a correct answer key.
  for (const row of dummy.rows) {
    row.independent_equation='SOFTWARE FIXTURE ONLY';
    row.independent_reasoning='NOT A HUMAN REVIEW';
    row.independent_answer='0';
    row.solved_at_utc='2026-10-10T00:00:00Z';
  }
  const wrongReviewer=structuredClone(dummy); wrongReviewer.reviewer_id='R02';
  await submit(wrongReviewer); assert.match(element('message').textContent,/Wrong reviewer/);
  const wrongHash=structuredClone(dummy); wrongHash.rows[0].text_sha256='mismatch';
  await submit(wrongHash); assert.match(element('message').textContent,/Text\/ID mismatch/);
  const duplicates=structuredClone(dummy); duplicates.rows[0]=duplicates.rows[1];
  await submit(duplicates); assert.match(element('message').textContent,/Duplicate IDs/);
  const wrongVersion=structuredClone(dummy); wrongVersion.dataset_version='wrong';
  await submit(wrongVersion); assert.match(element('message').textContent,/Wrong reviewer\/version/);
  await submit(dummy);
  assert.match(element('message').textContent,/Imported/);
  let state=JSON.parse(vm.runInContext('JSON.stringify(packet)',context));
  const expected=crypto.createHash('sha256').update(JSON.stringify(dummy)).digest('hex');
  assert.equal(state.stage1_submission_sha256,expected);
  assert.equal(state.stage,2);
  assert.equal(state.rows[0].independent_answer,'0');
  assert.equal(state.completed_at_utc,'');
  vm.runInContext('save()',context);
  assert.equal(downloads,1);
  state=JSON.parse(vm.runInContext('JSON.stringify(packet)',context));
  await submit(state);
  const resumed=JSON.parse(vm.runInContext('JSON.stringify(packet)',context));
  assert.equal(resumed.stage1_submission_sha256,expected);
  assert.equal(resumed.rows[0].independent_answer,'0');
  console.log('PASS: stage2 gates, reviewer/version/hash/duplicate rejection, original-file hash, immutable answer export and resume; stub DOM only.');
}
test().catch(error=>{console.error(error);process.exitCode=1;});
