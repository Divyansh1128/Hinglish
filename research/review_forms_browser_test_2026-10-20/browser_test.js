// Real-browser check of the reviewer forms (copies only). Artificial answers; nothing is submitted.
const puppeteer = require('puppeteer-core');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const T = __dirname, DL = path.join(T, 'dl');
const sleep = ms => new Promise(r => setTimeout(r, ms));
async function waitFile(name){ for(let i=0;i<50;i++){ const p=path.join(DL,name); if(fs.existsSync(p)&&fs.statSync(p).size>0) return p; await sleep(200);} throw Error('no download '+name); }
(async () => {
  const browser = await puppeteer.launch({ executablePath:'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless:'new', args:['--no-first-run'] });
  const page = await browser.newPage();
  const errors = []; page.on('pageerror', e => errors.push(e.message)); page.on('console', m => { if (m.type()==='error') errors.push(m.text()); });
  const cdp = await page.createCDPSession(); await cdp.send('Page.setDownloadBehavior', { behavior:'allow', downloadPath:DL });
  const msg = () => page.$eval('#message', e => e.textContent);
  const res = [];
  // ---- Stage 1: partial solve, download progress, resume ----
  await page.goto('file://' + path.join(T,'pkt/R01/stage1.html'));
  res.push(['stage1 loads; sections', await page.$$eval('section', s => s.length)]);
  res.push(['stage1 shows no gold/answer key text', !(await page.content()).toLowerCase().includes('gold_value')]);
  await page.$$eval('section', (secs) => secs.slice(0,5).forEach((s,i) => { s.querySelector('[data-key="independent_equation"]').value='2+3'; s.querySelector('[data-key="independent_reasoning"]').value='test '+i; s.querySelector('[data-key="independent_answer"]').value='5'; }));
  await page.click('#save'); const p1 = await waitFile('R01_stage1_responses.json');
  const partial = JSON.parse(fs.readFileSync(p1)); res.push(['progress download has 90 rows, 5 answered', partial.rows.length===90 && partial.rows.filter(r=>r.independent_answer==='5').length===5]);
  fs.renameSync(p1, path.join(DL,'progress.json'));
  await page.reload(); const inp = await page.$('#import'); await inp.uploadFile(path.join(DL,'progress.json')); await sleep(500);
  res.push(['resume import message', await msg()]);
  res.push(['resume restores answers', (await page.$$eval('[data-key="independent_answer"]', e=>e.filter(x=>x.value==='5').length))===5]);
  // complete all solves with stamp buttons, attest, completion time
  await page.$$eval('section', secs => secs.forEach(s => { s.querySelector('[data-key="independent_equation"]').value ||= '1+1'; s.querySelector('[data-key="independent_reasoning"]').value ||= 'r'; s.querySelector('[data-key="independent_answer"]').value ||= '2'; s.querySelector('[data-stamp]').click(); }));
  await page.click('#attest'); await page.$eval('#completed', e => e.value = new Date().toISOString());
  await page.click('#saveBottom'); const s1 = await waitFile('R01_stage1_responses.json');
  const s1json = JSON.parse(fs.readFileSync(s1)); res.push(['stage1 final: all stamped and attested', s1json.rows.every(r=>r.solved_at_utc) && s1json.independent_solve_before_gold===true]);
  const s1hash = crypto.createHash('sha256').update(fs.readFileSync(s1)).digest('hex');
  // ---- Stage 2 ----
  await page.goto('file://' + path.join(T,'pkt/R01/stage2.html'));
  await page.click('#save'); await sleep(300); res.push(['stage2 save blocked before import', await msg()]);
  await (await page.$('#import')).uploadFile(path.join(DL,'progress.json')); await sleep(500);
  res.push(['stage2 rejects unfinished stage1', await msg()]);
  await (await page.$('#import')).uploadFile(s1); await sleep(500); res.push(['stage2 import of finished stage1', await msg()]);
  await page.$$eval('section', secs => secs.forEach(s => { s.querySelectorAll('select').forEach(sel => { if (sel.options.length>1) sel.selectedIndex = 1; }); s.querySelector('[data-stamp]').click(); }));
  await page.click('#save'); const s2 = await waitFile('R01_stage2_responses.json'); const s2json = JSON.parse(fs.readFileSync(s2));
  res.push(['stage2 export keeps stage1 hash', s2json.stage1_submission_sha256 === s1hash]);
  res.push(['stage2 keeps stage1 answers unchanged', s2json.rows.every((r,i)=>r.independent_answer===s1json.rows.find(x=>x.rendering_id===r.rendering_id).independent_answer)]);
  res.push(['stage2 ratings recorded', s2json.rows.filter(r=>r.naturalness!==null && r.disposition).length]);
  // ---- Cross-reviewer guard ----
  await page.goto('file://' + path.join(T,'pkt/R02/stage2.html')); await (await page.$('#import')).uploadFile(s1); await sleep(500);
  res.push(['R02 stage2 rejects R01 file', await msg()]);
  res.push(['page JS errors', errors.length ? errors : 'none']);
  console.log(JSON.stringify(res, null, 1));
  await browser.close();
})().catch(e => { console.error('FAILED', e); process.exit(1); });
