/* Rebuild: cd docs/minor_project/deck && node build_deck.js
 * Evidence is checked against the report, results and the review rulings.
 * White canvas, Georgia titles, Calibri body; tables/charts remain editable.
 * Source checks run BEFORE writing the deck and stop on any disagreement.
 */
'use strict';
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const pptxgen = require('pptxgenjs');
const JSZip = require('jszip');
const ROOT = path.resolve(__dirname, '../../..');
const read = p => fs.readFileSync(path.join(ROOT, p), 'utf8');
const pilot = [
  { model: 'Qwen3-4B', dir: 'qwen3-4b', values: [94.3,85.7,94.3], ci: [[86.2,97.8],[75.7,92.1],[86.2,97.8]] },
  { model: 'Qwen3-8B', dir: 'qwen3-8b', values: [98.6,91.4,98.6], ci: [[92.3,99.7],[82.5,96.0],[92.3,99.7]] },
  { model: 'Llama-3.2-3B', dir: 'llama-3.2-3b', values: [94.3,57.1,70.0], ci: [[86.2,97.8],[45.5,68.1],[58.5,79.5]] },
];
const original = [
  { model: 'Qwen3-4B', values: [100.0,91.7,100.0], ci: [[86.2,100.0],[74.2,97.7],[86.2,100.0]] },
  { model: 'Qwen3-8B', values: [100.0,95.8,100.0], ci: [[86.2,100.0],[79.8,99.3],[86.2,100.0]] },
  { model: 'Llama-3.2-3B', values: [87.5,62.5,91.7], ci: [[69.0,95.7],[42.7,78.8],[74.2,97.7]] },
];
const seedRows = [
  ['EE:11',62,41,44], ['EE:22',63,41,41], ['EE:33',59,39,44],
  ['ER:11',61,42,44], ['ER:22',56,35,47], ['ER:33',61,37,50],
  ['EC:11',64,43,41], ['EC:22',58,41,46], ['EC:33',54,40,41],
  ['unchanged',85,63,66],
];
const arms = [
  ['unchanged',85,63,66], ['E+E',61.3,40.3,43.0],
  ['E+R',59.3,38.0,47.0], ['E+C',58.7,41.3,42.7],
];
function verifySources() {
  for (const p of pilot) {
    const src = read(`results/pilot_b/${p.dir}/RESULTS.md`);
    ['E','R','C'].forEach((form,i) => {
      const row = src.split('\n').find(l => l.startsWith(`| ${form} |`));
      assert(row, `Slide 6: missing ${p.model}/${form}`);
      const match = row.match(/\|\s*([\d.]+)%\s*\|\s*\[([\d.]+),\s*([\d.]+)\]/);
      assert(match, `Slide 6: unreadable ${p.model}/${form}`);
      assert.deepEqual(match.slice(1).map(Number), [p.values[i], ...p.ci[i]], `Slide 6: disagreement ${p.model}/${form}`);
    });
  }
  const analysis = read('results/phase2/final_test/phase2_analysis.md');
  assert(analysis.includes('Δ_C = -4.33 pp [-8.00, -0.67]'), 'Slide 9: primary result disagrees');
  assert(analysis.includes('**Decision label: Harm**'), 'Slide 9: label disagrees');
  const strict = analysis.split('## Accuracy by checkpoint — strict')[1].split('## Accuracy by checkpoint — numeric')[0];
  for (const [id,...expected] of seedRows) {
    const row = strict.split('\n').find(l => l.startsWith(`| ${id} |`));
    assert(row, `Slide 10/B1: missing ${id}`);
    assert.deepEqual([...row.matchAll(/(\d+)\/100/g)].map(m=>+m[1]), expected, `Slide 10/B1: ${id} disagrees`);
  }
  const perSeed = analysis.split('## Per seed (strict, descriptive)')[1];
  [11,22,33].forEach((seed,i)=>assert(perSeed.includes(`| Primary: E+C − E+R on C | ${seed} | ${[-3,-1,-9][i]}.00 pp`), `Slide 9: seed ${seed} disagrees`));
  // Means are checked, never used to replace the brief's displayed precision.
  arms.slice(1).forEach((arm,i)=>arm.slice(1).forEach((v,j)=> {
    const mean = seedRows.slice(i*3,i*3+3).reduce((a,r)=>a+r[j+1],0)/3;
    assert.equal(Number(mean.toFixed(1)),v,`Slide 10: ${arm[0]} mean disagrees`);
  }));
  const chapter = read('report/phase2_chapter.tex');
  assert(chapter.includes('median output length is 42.0 tokens for trained checkpoints versus 113.0 for unchanged'), 'Slide 10: median length disagrees');
  const audit = read('results/phase2/audit/README.md');
  assert(audit.includes('E+R 46 format-only + 113 substantive (159); E+C 40 format-only + 132 substantive (172)'), 'Slide 11: human audit disagrees');
  console.log('Verified slide 6, 9 and 10 data against source results; audit counts also match.');
}

const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'Divyansh Raj, Ayush Kumar Singh, Divyanshu Mishra';
pptx.subject = 'DTU Applied Mathematics minor project evaluation';
pptx.title = 'Language and maths in small LLMs';
pptx.company = 'Delhi Technological University';
pptx.lang = 'en-IN';
pptx.theme = { headFontFace:'Georgia', bodyFontFace:'Calibri', lang:'en-IN' };
const W=13.333333, H=7.5;
const C = { E:'3B4A5A', R:'B5532F', C:'2E7D74', grey:'8A8F96', ink:'222222', rule:'C9CDD1', pale:'E8EAEC' };
const forms=['E','R','C'];
const titles = [];
const layout = []; // Conservative text-fit and canvas checks, independent of PowerPoint autofit.

function wrap(text,width,size,font='Calibri') {
  const em = font==='Georgia' ? 0.56 : font==='Consolas' ? 0.60 : 0.52;
  const capacity = Math.floor((width*72-8)/(size*em));
  assert(capacity>0, 'Text box too narrow');
  return String(text).split('\n').flatMap(para=> {
    if (!para) return [''];
    const lines=[]; let line='';
    for (const word of para.split(/\s+/)) {
      assert(word.length<=capacity, `Unbreakable word is too wide: ${word}`);
      if (line && line.length+1+word.length>capacity) { lines.push(line); line=word; }
      else line += (line?' ':'')+word;
    }
    lines.push(line); return lines;
  });
}
function text(s,t,x,y,w,h,size=20,opts={}) {
  const font=opts.fontFace||'Calibri';
  const lines=wrap(t,w,size,font);
  const required=lines.length*size/72*1.18+0.06;
  assert(required<=h+0.025, `Slide ${s._slideNum}: text needs ${required.toFixed(2)}in, has ${h}: ${t}`);
  assert(x>=0 && y>=0 && x+w<=W+0.01 && y+h<=H+0.01, `Text outside slide: ${t}`);
  assert(size>=16 || opts.small, `Body below 16pt: ${t}`);
  s.addText(lines.join('\n'), {x,y,w,h,fontFace:font,fontSize:size,color:C.ink,
    margin:0,breakLine:false,valign:'mid',paraSpaceAfterPt:0,...opts});
  layout.push({slide:s._slideNum,text:t,x,y,w,h,size,lines:lines.length});
}
function line(s,x1,y1,x2,y2,color=C.rule,width=0.7,extra={}) {
  s.addShape(pptx.ShapeType.line,{x:x1,y:y1,w:x2-x1,h:y2-y1,line:{color,width,...extra}});
}
function rect(s,x,y,w,h,fill,stroke=fill) {
  s.addShape(pptx.ShapeType.rect,{x,y,w,h,fill:{color:fill},line:{color:stroke,width:0.7}});
}
function base(title,source='',cover=false) {
  const s=pptx.addSlide(); s.background={color:'FFFFFF'}; titles.push(title);
  assert.equal(wrap(title,12.03,28,'Georgia').length,title.split('\n').length, `Title needs an intentional break: ${title}`);
  assert(!/(?:results|report|docs)\//.test(source), `Keep repository paths in notes: ${source}`);
  if (!cover) {
    text(s,title,.65,.35,12.03,1.05,28,{fontFace:'Georgia'});
    line(s,.65,1.50,12.68,1.50);
    if(source) text(s,source,.65,6.91,11.5,.25,11,{color:C.grey,small:true});
    text(s,'DTU · Applied Mathematics · Minor project evaluation',.65,7.20,11,.25,11,{color:C.grey,small:true});
    text(s,String(s._slideNum),12.00,7.16,.65,.25,11,{color:C.grey,align:'right',small:true});
  }
  return s;
}
function notes(s,presenter,body,sources) { s.addNotes(`${presenter}: ${body}\n\nSources: ${sources}`); }
function table(s,rows,x,y,widths,rowH=0.52,size=18,header=true) {
  const total=widths.reduce((a,b)=>a+b,0);
  rows.forEach((r,i)=> {
    let xx=x;
    r.forEach((cell,j)=> {
      const val=typeof cell==='object'?cell.t:String(cell);
      const color=typeof cell==='object'?cell.color:C.ink;
      text(s,val,xx+.08,y+i*rowH+.025,widths[j]-.16,rowH-.05,size,{color,bold:header&&i===0});
      xx+=widths[j];
    });
    line(s,x,y+(i+1)*rowH,x+total,y+(i+1)*rowH,i===0&&header?C.grey:C.pale,i===0&&header?.8:.45);
  });
}


function slide01() {
  const s=base('Language and maths in small LLMs','',true);
  text(s,'Language and maths in small LLMs',.75,.75,11.8,.7,28,{fontFace:'Georgia'});
  text(s,'Hinglish, Romanized Hindi and English',.75,1.65,11.8,.6,24);
  line(s,.75,2.65,12.55,2.65);
  text(s,'Divyansh Raj (23/MC/195)\nAyush Kumar Singh (23/MC/194)\nDivyanshu Mishra (23/MC/196)',.75,3.25,6.1,1.3,22);
  text(s,'B.Tech. Mathematics and Computing\nDepartment of Applied Mathematics\nDelhi Technological University',7.1,3.25,5.4,1.4,20);
  text(s,'Supervisor: Dr. Dinesh Udar',.75,5.45,11.8,.5,22);
  text(s,'Minor project evaluation, November 2026',.75,6.25,11.8,.45,20,{color:C.grey});
  notes(s,'Divyansh','We ask whether changing only the language of a maths problem changes a small model’s answer. We compare English, Romanized Hindi and Hinglish, then test whether Hinglish training helps. Our supervisor is Dr. Dinesh Udar, Assistant Professor in the Department of Applied Mathematics at DTU.','docs/minor_project/deck/DECK_BRIEF.md; report/final_report.tex');
}
function slide02() {
  const s=base('Three language forms','PB017, Pilot-B');
  const examples=[
    ['English (E)','Imran had ₹1200. He bought 3 shirts at ₹265 each.','How much money did he have left?'],
    ['Romanized Hindi (R)','Imran ke paas ₹1200 the. Usne ₹265 waali 3 kameezein khareedin.','Uske paas kitne rupaye bache?'],
    ['Hinglish /\ncode-mixed (C)','Imran ke paas ₹1200 the. Usne ₹265 waali 3 kameezein khareedin.','How much money did he have left?']
  ];
  examples.forEach(([label,statement,question],i)=>{
    const y=1.78+i*1.25;
    text(s,label,.7,y,3.3,.75,20,{color:C[forms[i]],bold:true});
    text(s,statement,4.15,y,8.45,.72,20);
    text(s,question,4.15,y+.73,8.45,.40,20,{bold:true});
  });
  text(s,'Romanized Hindi = Hindi written in Latin script.',.7,5.58,11.9,.38,18);
  text(s,'Here, the Hinglish form changes the question sentence to English.',.7,6.02,11.9,.38,18);
  text(s,'Correct answer: ₹405 (₹1200 − 3 × ₹265 = ₹405)',.7,6.46,11.9,.40,20,{bold:true});
  notes(s,'Divyansh','These are the verbatim PB017 forms. Romanized Hindi means Hindi written in Latin script. This particular Hinglish example changes the question sentence to English, rather than defining every possible code-mixed form. Only the wording changes: mathematics, quantities and answer stay fixed.','docs/minor_project/deck/DECK_BRIEF.md; results/pilot_b/audit/llama-3.2-3b_outputs_for_audit.jsonl');
}
function slide03() {
  const s=base('Research questions','Prior work: CodeMixTax (2026)');
  text(s,'Phase 1',.75,1.95,2,.45,22,{color:C.grey});
  text(s,'Do unchanged models answer English, Romanized Hindi\nand Hinglish equally well?',3,1.90,9.5,1,24);
  line(s,.75,3.25,12.5,3.25);
  text(s,'Phase 2',.75,3.65,2,.45,22,{color:C.grey});
  text(s,'Does English + Hinglish training help on Hinglish\nmore than English + Romanized Hindi training?',3,3.60,9.5,1,24);
  text(s,'Prior work reports a similar language gap. We test it with controlled\nquestion families and compare training languages.',.75,5.3,11.8,1,22,{bold:true});
  notes(s,'Divyansh','CodeMixTax already reports Romanized Hindi below Romanized Hinglish on aligned GSM8K. Our contribution is controlled question families, a scoring-aware audit and a training-language comparison. CodeMixTax is an author research report, not a peer-reviewed paper. Citation: Sthānika (2026), The code-mixing tax on romanized Hindi, measured. Research report, 9 September 2026. https://sthanika.ai/research/codemix-tax-2026','report/final_report.tex, Related Work; paper/latex/main.tex; docs/minor_project/deck/DECK_BRIEF.md');
}
function slide04() {
  const s=base('How the data was built','Reviewed, version-locked data');
  text(s,'A family is the same maths problem in three language forms.',.7,1.77,11.9,.5,22);
  const steps=[['1','AI draft + code-computed answer'],['2','Blind solving by Claude and GPT'],['3','Bilingual human review'],['4','Version locked after review']];
  steps.forEach(([n,t],i)=>{
    const col=i%2,row=Math.floor(i/2),x=.7+col*6.15,y=2.55+row*.72;
    text(s,n,x,y,.5,.45,22,{color:C.grey}); text(s,t,x+.6,y,5.35,.45,20);
  });
  text(s,'70 pilot + 160 train + 40 dev + 100 test = 370 families',.7,4.30,11.9,.52,24,{bold:true});
  text(s,'Original 24-family cohort: separate from the 370.',.7,4.96,11.9,.42,20);
  text(s,'Phase 2: 300 families × 3 forms = 900 renderings',.7,5.58,11.9,.42,20);
  text(s,'Claude solved 900/900, GPT 897/900.\nAll 3 misses were one family, a GPT error.',.7,6.08,11.9,.7,20);
  notes(s,'Divyansh','Gold answers were computed in code. Blind solving checked whether the drafted renderings yielded those answers, followed by bilingual review. Claude solved all 900 Phase-2 renderings and GPT 897. The three GPT misses were the three forms of one family and were adjudicated as a GPT error. Version locking with SHA-256 establishes integrity after review, not validity on its own. The 70 Pilot-B families and 300 Phase-2 families total 370. The original 24-family cohort is separate.','report/final_report.tex, data construction and frozen dataset appendix; docs/minor_project/deck/DECK_BRIEF.md');
}
function slide05() {
  const s=base('Answer format and the prompt revision','Development only, 36 excluded prompts');
  text(s,'A correct number in the wrong format counts as wrong.',.7,1.75,11.9,.45,22,{bold:true});
  text(s,'Real example: FINAL: 8 unitless (right value, rejected suffix)',.7,2.30,11.9,.45,20);
  text(s,'10 / 36',.7,3.00,4.2,1.15,66,{fontFace:'Georgia'});
  text(s,'→',5.0,3.00,1.2,1.15,54,{color:C.grey,align:'center'});
  text(s,'0 / 36',6.4,3.00,4.2,1.15,66,{fontFace:'Georgia'});
  text(s,'format failures, prompt v1',.7,4.18,4.6,.4,18,{color:C.grey});
  text(s,'after the v2 revision',6.4,4.18,4.6,.4,18,{color:C.grey});
  text(s,'Romanized Hindi explanations in Devanagari: 8/12 → 0/12',.7,4.82,11.9,.42,20);
  line(s,.7,5.45,12.6,5.45);
  text(s,'v1: “<number or fraction> <unit when applicable>”',.7,5.62,11.9,.40,18);
  text(s,'v2: “write nothing after a pure number or fraction”',.7,6.04,11.9,.40,18);
  text(s,'Qwen3-4B. Fixtures also changed, so this does not isolate the prompt’s effect.',.7,6.48,11.9,.36,16);
  notes(s,'Ayush','Strict scoring requires exactly one terminal FINAL line and an exact number plus an allowed unit only where appropriate. FINAL: 8 unitless is a real numerically correct but invalid answer. The v1 and v2 excerpts are from the frozen-prompt appendix. V2 also specifies English explanations even for non-English questions and English units. Devanagari explanations violate the language instruction but the report explicitly says script drift itself affects neither scoring endpoint. One ambiguous R fixture and a unit alias changed between runs, so the before/after counts are development evidence rather than an isolated prompt intervention. All fixtures are permanently excluded. The seven-model operational screen is in the backup.','report/final_report.tex, development findings and frozen-prompt appendix');
}
function accuracyChart(s,data) {
  const bottom=5.45,top=2.62,scale=(bottom-top)/100;
  text(s,'Strict accuracy (%)',.7,1.66,5,.36,17,{color:C.grey});
  [0,50,100].forEach(v=>{const y=bottom-v*scale;text(s,String(v),.7,y-.14,.6,.3,16,{align:'right',color:C.grey});line(s,1.47,y,12.5,y,v===0?C.grey:C.pale,v===0?.9:.45);});
  line(s,1.47,top,1.47,bottom,C.grey,.7);
  data.forEach((p,i)=>{
    const gx=2+i*3.5;
    forms.forEach((form,j)=>{
      const x=gx+j*.83,value=p.values[j],[lo,hi]=p.ci[j],center=x+.27;
      rect(s,x,bottom-value*scale,.54,value*scale,C[form]);
      line(s,center,bottom-hi*scale,center,bottom-lo*scale,C.ink,.7);
      [lo,hi].forEach(v=>line(s,center-.10,bottom-v*scale,center+.10,bottom-v*scale,C.ink,.7));
      text(s,value.toFixed(1),x-.13,bottom-hi*scale-.38,.8,.31,16,{align:'center',color:C[form]});
      text(s,form,x-.1,5.56,.75,.37,18,{align:'center',color:C[form]});
    });
    text(s,p.model,gx-.35,6.00,3,.42,20,{align:'center'});
  });
}
function slide06() {
  const s=base('Romanized Hindi was least accurate\nin all three tested models','Pilot-B, 70 families, individual Wilson 95% accuracy intervals');
  accuracyChart(s,pilot);
  text(s,'Qwen: Hinglish matched English. Llama: Hinglish also fell, less than R.',.7,6.53,11.9,.36,18);
  notes(s,'Ayush','Each model answers the same 70 Pilot-B families. Whiskers are individual Wilson 95% accuracy intervals, not paired difference intervals. Do not infer significance from overlap. See the paired-difference backup. Equal aggregate E and C accuracy for the Qwen models is not an equivalence result.','results/pilot_b/qwen3-4b/RESULTS.md; results/pilot_b/qwen3-8b/RESULTS.md; results/pilot_b/llama-3.2-3b/RESULTS.md; report/final_report.tex');
}
function slide06b() {
  const s=base('The original cohort shows the same direction','Original pilot, 24 families, two independent solvers, individual Wilson 95% intervals');
  accuracyChart(s,original);
  text(s,'A separate, earlier cohort: reported on its own, never pooled with Pilot-B.',.7,6.53,11.9,.36,18);
  notes(s,'Ayush','This is the original 24-family cohort, reviewed separately with two independent human solvers and an adjudicator. It uses an older, clause-based definition of Hinglish, so it is never pooled with Pilot-B. Romanized Hindi is again the lowest form for all three models. Both Qwen models are near ceiling here, so the cohort mainly confirms direction. For Llama, Hinglish (91.7) is above English (87.5) here, unlike Pilot-B.','report/final_report.tex, original cohort results');
}
function slide07() {
  const s=base('R errors are not concentrated in items\nwith Hindi operation words','Pilot-B, 70 families, descriptive, small strata');
  table(s,[['R accuracy (%)','C keeps word','C switches word','No word'],['Families','18','17','35'],['Qwen3-4B','89','82','86'],['Qwen3-8B','94','94','89'],['Llama','67','59','51']],.7,1.85,[3.5,2.8,2.8,2.8],.54,20);
  text(s,'Strata: a Hindi operation word stays in C, becomes English, or is absent.\nExample: “bhaag” (divide) stays as “bhaag” or switches to “divide”.',.7,4.73,11.9,.78,18);
  text(s,'PB017, Llama on R (actual output excerpt)',.7,5.64,11.9,.36,18,{color:C.grey});
  text(s,'“₹1200 - ₹765 (3 kameezein ke daam) = ₹435 bache hain.”',.7,6.05,11.9,.4,20);
  text(s,'Correct: 1200 − 3 × 265 = 405',.7,6.50,11.9,.40,20,{bold:true});
  notes(s,'Ayush','The strata describe whether the Hinglish form keeps or switches a Hindi operation word from R, or no lexicon word occurs. They are small and unequal, so they do not establish a causal operation-word effect or exclude one. The displayed PB017 excerpt was verified read-only against raw_response in generation_attempts.jsonl inside the nested Llama results ZIP. The full response is: Imran ke paas ₹1200 the, aur usne ₹265 waali 3 kameezein khareedin. Isliye, uske paas ₹1200 - ₹765 (3 kameezein ke daam) = ₹435 bache hain. FINAL: 435. It miscalculates 3 × 265 as 765.','results/raw_zips/PilotB_results_Llama-3.2-3B-Instruct.zip; results/pilot_b/llama-3.2-3b/per_rendering.csv; results/pilot_b/strata.py; report/final_report.tex');
}
function slide08() {
  const s=base('Phase 2: training comparison','Qwen3-4B, 160 training families, 100 untouched test families');
  text(s,'Qwen3-4B with QLoRA (parameter-efficient fine-tuning)',.7,1.76,11.9,.45,22);
  table(s,[['Training arm','Question languages','Solution language'],['E+E','English twice (duplicate)','English'],['E+R','English + Romanized Hindi','English'],['E+C','English + Hinglish','English']],.7,2.43,[2.5,6.4,3],.61,21);
  text(s,'320 examples per arm. Same families, English targets and settings.\n3 paired seeds (11, 22, 33), 60 updates per run. Input tokens differ.',.7,5.02,11.9,.82,20);
  text(s,'Δ(C): E+C accuracy minus E+R accuracy on Hinglish questions,\naveraged over 3 paired seeds',.7,6.02,11.9,.78,20,{bold:true});
  notes(s,'Ayush','E+E duplicates each English example, whereas E+R and E+C use two question renderings per family, giving 320 examples per arm. English solution targets, problem families, training settings and paired seeds are fixed. QLoRA adapts a small set of parameters on a quantized backbone. There are 16 examples per update, 20 updates per pass and three passes, for 60 updates. Matched example exposure does not match tokens or runtime. The primary estimand averages E+C minus E+R strict accuracy on Hinglish over 100 families and three paired seeds. Preregistration and three amendments were frozen before Phase-2 output.','report/final_report.tex, Phase 2; report/phase2_chapter.tex; phase2/PREREGISTRATION.md');
}
function slide09() {
  const s=base('E+C scored 4.33 percentage points\nbelow E+R on Hinglish','100 Phase 2 test families, strict accuracy');
  text(s,'Δ(C): E+C accuracy minus E+R accuracy on Hinglish questions,\naveraged over 3 paired seeds',.7,1.72,11.9,.75,20);
  text(s,'−4.33',.7,2.42,3.6,1.15,66,{fontFace:'Georgia'});
  text(s,'percentage points\n95% CI [−8.00, −0.67]',4.35,2.55,4.6,.9,22);
  text(s,'Pre-registered\nlabel: Harm',9.2,2.55,3.4,.9,22,{bold:true});
  text(s,'CI: paired bootstrap over the 100 test families, seeds kept together',.7,3.72,11.9,.35,17,{color:C.grey});
  const x0=1.55,x1=6.5,zero=4.75,bottom=6.38,scale=(bottom-zero)/10;
  text(s,'Per-seed difference (pp)',.7,4.22,5.9,.32,17);
  [0,-5,-10].forEach(v=>{const y=zero-v*scale;text(s,String(v).replace('-','−'),.7,y-.16,.6,.33,16,{align:'right',color:C.grey});line(s,x0,y,x1,y,v===0?C.ink:C.pale,v===0?1:.5);});
  line(s,x0,zero,x0,bottom,C.grey,.7);
  [-3,-1,-9].forEach((v,i)=>{
    const x=2.15+i*1.7,y=zero-v*scale;
    s.addShape(pptx.ShapeType.ellipse,{x:x-.065,y:y-.065,w:.13,h:.13,line:{color:C.ink},fill:{color:C.ink}});
    text(s,String(v).replace('-','−'),x+.13,y-.17,.55,.40,20,{bold:true});
    text(s,`Seed ${[11,22,33][i]}`,x-.5,6.51,1.2,.32,16,{align:'center'});
  });
  table(s,[['Hinglish accuracy (%)',''],['Unchanged model','66.0'],['E+E','43.0'],['E+R','47.0'],['E+C','42.7']],7.28,4.22,[3.9,1.45],.45,19);
  notes(s,'Divyanshu','The primary estimate is E+C minus E+R strict accuracy on Hinglish, averaged over the three paired seeds and 100 test families. It is minus 4.33 percentage points, with a paired family bootstrap 95% interval from minus 8.00 to minus 0.67 and the registered Harm label. Seed effects are minus 3, minus 1 and minus 9 pp. Each bootstrap resample draws 100 family rows with replacement, retaining all seed and arm outcomes together, then averages the paired difference. There are 10,000 resamples with analysis seed 101. This is conditional on these trained checkpoints, not an interval for training-seed variation. The unchanged-model comparison is a separate table. pp means percentage points. See the methods backup for limits.','results/phase2/final_test/phase2_analysis.md; report/phase2_chapter.tex');
}
function slide10() {
  const s=base('All trained arms lost accuracy\nand wrote much shorter answers');
  const bottom=4.23,top=2.20,scale=(bottom-top)/100;
  text(s,'Accuracy (%)',.7,1.73,2,.32,17);
  const full=['English','Romanized Hindi','Hinglish'];
  forms.forEach((form,j)=>{
    const left=1.5+j*3.83,right=left+3.38;
    text(s,full[j],left,1.76,3.38,.40,20,{color:C[form],align:'center'});
    [0,50,100].forEach(v=>{const y=bottom-v*scale;line(s,left,y,right,y,v===0?C.grey:C.pale,v===0?.8:.4);if(j===0)text(s,String(v),.7,y-.15,.6,.3,16,{color:C.grey,align:'right'});});
    line(s,left,top,left,bottom,C.grey,.7);
    arms.forEach((a,i)=>{
      const x=left+.16+i*.82,v=a[j+1];rect(s,x,bottom-v*scale,.50,v*scale,C[form]);
      text(s,v.toFixed(1),x-.18,bottom-v*scale-.34,.86,.31,16,{align:'center',color:C[form]});
      text(s,i===0?'Base':a[0],x-.1,4.32,.74,.33,16,{align:'center'});
    });
  });
  text(s,'100 Phase 2 test families. Base = unchanged. Median length: 113.0 to 42.0 tokens.',.7,4.80,11.9,.37,18,{bold:true});
  text(s,'Likely explanation: our training solutions were short, and the model copied that style.\nPhase 3 tests training on the model’s own step-by-step solutions.',.7,5.20,11.9,.66,18);
  line(s,.7,5.97,12.6,5.97);
  text(s,'Question excerpt: Aspataal upkaran ki jama raashi INR 900 mein se patti ke INR 120 aur\nsafai ke INR 45 kaat leta hai. How much of the deposit is refunded in rupees?',.7,6.05,11.9,.56,15,{small:true});
  text(s,'Trained model: Refund = 120 + 45 = 165 rupees. FINAL: 165 rupees',.7,6.57,11.9,.31,15,{small:true});
  text(s,'Correct: 900 − 120 − 45 = 735',.7,6.87,11.9,.30,14,{small:true,bold:true});
  notes(s,'Divyanshu','Every trained arm loses accuracy on every form relative to the unchanged model on the same 100 test families. Trained-arm bars are means across three seeds. The median output length falls from 113.0 to 42.0 tokens. Short English solution targets are the likely explanation: the model copied their terse style. This remains a hypothesis, not a demonstrated causal mechanism. Phase 3 is at design stage and will test self-distillation with the model’s own step-by-step targets. The refund example combines its question context, actual trained-model output and correct subtraction in one block.','results/phase2/final_test/phase2_analysis.md; report/phase2_chapter.tex; analysis/phase2_exploratory/README.md; docs/minor_project/deck/DECK_BRIEF.md');
}
function slide11() {
  const s=base('Checks on the Phase 2 result');
  text(s,'A second AI agent recomputed every number from the raw predictions:\nexact match',.7,1.84,11.9,.9,23,{bold:true});
  text(s,'Failures among 600 Hinglish answers\n(100 questions × 3 seeds × 2 arms)',.7,3.02,11.9,.86,22);
  table(s,[['Failure type','E+R','E+C'],['Real errors','113','132'],['Format-only failures','46','40'],['All failures','159','172']],.7,3.90,[6.3,2.8,2.8],.56,23);
  text(s,'E+C: 19 more real errors, 6 fewer format-only',.7,6.25,11.9,.43,22,{bold:true});
  notes(s,'Divyanshu','Real error means the answer is mathematically incorrect or the problem is misread, rather than merely breaking the output format. Format-only means the correct mathematical answer is present but strict formatting fails. The 600 answers cover 100 Hinglish questions, three seeds and two arms. All 331 failures were human checked. E+C has 19 more real errors and six fewer format-only failures. A second AI agent recomputed every reported number from raw predictions and matched exactly; this is a computational check, not external replication. Two interrupted evaluation runs were recovered under the registered rule with no answer generated twice.','results/phase2/audit/README.md; report/phase2_chapter.tex');
  text(s,'Real error = wrong maths or reading. Format-only = correct value, invalid format.',.7,6.74,11.9,.33,16);
}
function slide12() {
  const s=base('Scope and limitations','One backbone, one training recipe, 100 test families');
  const limits=[
    ['Qwen3-4B and one recipe','Other backbones or richer targets may behave differently.'],
    ['100 test families','Intervals assume independent families from this authoring process.'],
    ['Mostly one bilingual reviewer','Independent linguistic validation is limited.'],
    ['AI-drafted items, no Devanagari arm','Script effects remain unresolved.']
  ];
  limits.forEach(([a,b],i)=>{const y=1.90+i*1.1;text(s,a,.75,y,11.8,.4,22,{bold:true});text(s,b,.75,y+.46,11.8,.4,20);});
  notes(s,'Divyanshu','The Phase-2 comparison concerns Qwen3-4B, 60 QLoRA updates on short English targets and 100 test families. One backbone limits generalisation. Family intervals are conditional on trained checkpoints and this authoring/review process, with template and author dependence a limitation. Most sets have one bilingual reviewer, limiting independent linguistic validation. AI-drafted items and the absence of a Devanagari arm leave script, vocabulary and register effects unresolved.','report/final_report.tex, limitations; report/phase2_chapter.tex');
}
function slide13() {
  const s=base('Project status and next steps','November 2026');
  const xs=[.7,4.75,8.8],width=3.8;
  ['Completed','In progress','Upcoming'].forEach((h,i)=>{text(s,h,xs[i],1.83,width,.45,24,{bold:true});line(s,xs[i],2.42,xs[i]+width,2.42);});
  text(s,'Reviewed data and pipeline\n\nPhases 1–2\n\nFull human audit\n\nSRW paper draft and\nmentorship submission',xs[0],2.68,width,3.75,20,{valign:'top'});
  text(s,'Phase 3: training on the model’s own step-by-step solutions (self-distillation), to test whether Hinglish training helps once the short-target damage is removed',xs[1],2.68,width,3.15,20,{valign:'top'});
  text(s,'Design stage, no results',xs[1],6.08,width,.43,19,{bold:true});
  text(s,'SRW mentor feedback\n5 Dec 2026\n\nFinal SRW submission\n15 Dec 2026\n\nPhase 3 runs\n\nThesis, ARR submission\nand final evaluation\nMay 2027',xs[2],2.68,width,3.95,19,{valign:'top'});
  notes(s,'Divyanshu','Phases 1 and 2 are complete. Completed work includes 370 plus 24 data families, the pipeline, evaluations, analysis, full human failure audit and an SRW draft submitted for mentorship on 26 October. Phase 3 is underway at design stage only, with no results. It will train on the model’s own step-by-step solutions to test whether Hinglish helps after the short-target damage is removed. Upcoming dates are mentor feedback on 5 December 2026, final SRW submission on 15 December 2026, Phase-3 runs, and thesis, ARR submission and final evaluation in May 2027.','report/final_report.tex, project status; user-provided Phase-3 status and dates');
}
function slide14() {
  const s=base('Findings and Phase 3');
  text(s,'Romanized Hindi was least accurate across the three tested models.',.75,2.12,11.8,.9,24,{bold:true});
  text(s,'Qwen3-4B, this recipe: E+C scored below E+R on Hinglish.',.75,3.55,11.8,.95,24,{bold:true});
  text(s,'Phase 3 will test the model’s own step-by-step training solutions.',.75,5.15,11.8,.9,23);
  text(s,'Questions?',.75,6.45,11.8,.4,18,{color:C.grey});
  notes(s,'Divyanshu','The first finding is bounded to the three tested unchanged models. The training result is bounded to Qwen3-4B and this short-target QLoRA recipe: E+C scores below E+R on Hinglish. It is not a general claim about Hinglish training. Phase 3 is at design stage, testing targets based on the model’s own step-by-step solutions. We welcome questions.','report/final_report.tex; results/phase2/final_test/phase2_analysis.md; user-provided Phase-3 status');
}
function backup01() {
  const s=base('Phase 2 accuracy by training arm and seed','100 Phase 2 test families, strict accuracy (%)');
  const rows=[['Arm','Seed',{t:'English',color:C.E},{t:'Romanized Hindi',color:C.R},{t:'Hinglish',color:C.C}],
    ...seedRows.map(([id,...v])=>{const [arm,seed]=id.split(':');return [arm==='unchanged'?'Unchanged':{'EE':'E+E','ER':'E+R','EC':'E+C'}[arm],seed||'—',...v.map(n=>n.toFixed(1))];})];
  table(s,rows,.7,1.80,[2.4,1.6,2.4,3.1,2.4],.43,20);
  text(s,'E+E = English twice. E+R = English + Romanized Hindi. E+C = English + Hinglish.',.7,6.65,11.9,.29,14,{small:true});
  notes(s,'Divyanshu','All nine trained checkpoints plus the unchanged reference are shown. Seed identifies the training random seed, paired across arms. Values are strict percent correct on 100 families per form. Main-deck trained values average the three seeds.','results/phase2/final_test/phase2_analysis.md');
}
function backup02() {
  const s=base('Pilot paired accuracy differences','Pilot-B, 70 families, paired difference 95% bootstrap intervals');
  text(s,'pp = percentage points. A − B means accuracy on A minus accuracy on B.',.7,1.73,11.9,.37,18);
  const groups=[['Qwen3-4B',['+8.6 [−1.4, +18.6]','0.0 [−7.1, +7.1]','−8.6 [−15.7, −1.4]']],['Qwen3-8B',['+7.1 [0.0, +14.3]','0.0 [−4.3, +4.3]','−7.1 [−14.3, 0.0]']],['Llama-3.2-3B',['+37.1 [+24.3, +50.0]','+24.3 [+11.4, +37.1]','−12.9 [−27.1, +1.4]']]];
  groups.forEach(([model,vals],i)=>{
    const y=2.27+i*1.48;
    text(s,model,.7,y,3.0,.42,22,{bold:true});
    table(s,[['E − R',vals[0]],['E − C',vals[1]],['R − C',vals[2]]],4.0,y,[2.2,6.4],.45,21,false);
    if(i<2)line(s,.7,y+1.36,12.6,y+1.36);
  });
  notes(s,'Ayush','Each difference subtracts the second form from the first within the same families. Bootstrap resampling keeps the forms paired by family. These are paired-difference intervals, unlike the individual Wilson accuracy intervals on slide 6. Qwen E−R intervals include or touch zero. Llama E−R and E−C intervals exclude zero. R−C excludes zero for Qwen3-4B, touches zero for Qwen3-8B and crosses zero for Llama. Intervals do not establish equivalence when zero is included.','results/pilot_b/qwen3-4b/RESULTS.md; results/pilot_b/qwen3-8b/RESULTS.md; results/pilot_b/llama-3.2-3b/RESULTS.md');
}
function backup03() {
  const s=base('Seven-model format screen','Development only, 36 excluded prompts per model, frozen v2 prompt');
  text(s,'Inclusion threshold: at most 3/36 strict-invalid outputs',.7,1.76,11.9,.43,22);
  table(s,[['Model','Strict-invalid','Outcome'],['Qwen3-4B','0/36','Included'],['Qwen3-8B','0/36','Included'],['Llama-3.2-3B','2/36','Included'],['Qwen3-1.7B','36/36','Format non-compliance'],['Phi-4-mini','14/36','Format non-compliance'],['Granite-3.3-2B','36/36','Format non-compliance']],.7,2.40,[4.1,2.6,5.2],.49,21);
  text(s,'Gemma-3-4B: no outputs (CUDA error under FP16)',.7,6.10,11.9,.44,22,{bold:true});
  text(s,'An operational compliance screen, not a ranking of mathematical ability.',.7,6.61,11.9,.37,18);
  notes(s,'Ayush','The frozen prompt and scorer were not tuned per model. Qwen3-1.7B echoed the instruction, Phi produced inline FINAL markers and repetition, and Granite appended commentary after FINAL. Gemma loaded but could not generate due to CUDA errors under FP16, so it has no output-format rate. Phi and Granite were excluded before the threshold was formalised but both exceed it. The screen selects models compatible with the recipe rather than ranking mathematical ability.','report/final_report.tex, seven-model screening');
}
function backup04() {
  const s=base('Phase 2 uncertainty and run recovery','Registered analysis and recovery rules');
  text(s,'Paired family bootstrap',.7,1.85,11.9,.45,24,{bold:true});
  text(s,'Resample 100 test families with replacement, keeping both arms and all\n3 seeds together. Average the paired differences. 10,000 resamples, seed 101.',.7,2.47,11.9,.85,21);
  text(s,'The 95% interval is conditional on the trained checkpoints. It does not\ncover training-seed variation or dependence from shared authors/templates.',.7,3.60,11.9,.85,21);
  line(s,.7,4.75,12.6,4.75);
  text(s,'Interrupted-run recovery',.7,5.02,11.9,.45,24,{bold:true});
  text(s,'Two runs resumed under the registered rule.\nSuccessful outputs were reused. No answer was generated twice.',.7,5.67,11.9,.85,21);
  notes(s,'Divyanshu','The registered paired family bootstrap uses 10,000 family resamples, analysis seed 101, with the three seed outcomes and paired arms retained within each row. Crossed family-by-seed resampling was not run. The finite-set mean is descriptive; intervals invoke hypothetical independent families from this authoring/review process. The wider conservative Hoeffding interval was −31.50 to +22.83 pp. Interrupted runs preserved successful outputs and resumed only missing generations, with no answer generated twice.','results/phase2/final_test/phase2_analysis.md; report/phase2_chapter.tex; phase2/PREREGISTRATION.md');
}
async function main() {
  verifySources();
  [slide01,slide02,slide03,slide04,slide05,slide06,slide06b,slide07,slide08,slide09,slide10,slide11,slide12,slide13,slide14,backup01,backup02,backup03,backup04].forEach(build=>build());
  const output=path.join(__dirname,'minor_evaluation_v2.pptx');
  await pptx.writeFile({fileName:output,compression:true});
  // PptxGenJS 3.12 declares a slideMaster override per slide although it writes
  // only slideMaster1. Remove only declarations whose target does not exist.
  const zip=await JSZip.loadAsync(fs.readFileSync(output));
  const contentTypes=await zip.file('[Content_Types].xml').async('string');
  zip.file('[Content_Types].xml',contentTypes.replace(/<Override\b[^>]*PartName="([^"]+)"[^>]*\/>/g,
    (entry,part)=>zip.file(part.replace(/^\//,''))?entry:''));
  fs.writeFileSync(output,await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'}));
  console.log(`Built 15 main slides + 4 backups. Checked ${layout.length} text boxes for conservative fit.\n${output}`);
  titles.forEach((title,i)=>console.log(`${i+1}. ${title.replace(/\n/g,' ')}`));
}
main().catch(err=>{ console.error(err.stack); process.exitCode=1; });
