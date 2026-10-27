// Builds docs/minor_project/minor_evaluation_presentation.pptx
const pptxgen = require("pptxgenjs");
const { applyTheme } = require(process.env.SKILL + "/scripts/apply_theme.js");
const REPO = "/Users/divyanshraj/Desktop/Major Project";
const OUT = REPO + "/docs/minor_project/minor_evaluation_presentation.pptx";
const FIG_A = REPO + "/paper/figures/accuracy_by_form.png";
const FIG_ORIG = "/tmp/deckbuild/fig/original_cohort_accuracy.pdf.png";
const FIG_STRAT = "/tmp/deckbuild/fig/pilotb_r_by_stratum.pdf.png";

const THEME = {
  name: "Hinglish Audit",
  headFontFace: "Cambria",
  bodyFontFace: "Calibri",
  colors: {
    dk1: "1E1E24", lt1: "FFFFFF", dk2: "1F2F4A", lt2: "EEF2F7",
    accent1: "0072B2", accent2: "E69F00", accent3: "009E73", accent4: "D55E00",
    accent5: "CC79A7", accent6: "56B4E9", hlink: "0072B2", folHlink: "6A3D9A",
  },
};
const K = {
  ink: "1E1E24", navy: "1F2F4A", muted: "4A5568", tint: "EEF2F7", line: "C9D2DE",
  E: "0072B2", R: "E69F00", C: "009E73", dev: "D55E00", orig: "CC79A7", white: "FFFFFF",
};

const pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.333 x 7.5
pres.theme = { headFontFace: THEME.headFontFace, bodyFontFace: THEME.bodyFontFace };
pres.title = "Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs";
pres.subject = "Minor project evaluation, November 2026";

const W = 13.333, M = 0.55;

pres.defineSlideMaster({
  title: "TITLE_DARK",
  background: { color: K.navy },
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 1.5, w: W - 2 * M, h: 2.0, fontFace: "Cambria", fontSize: 40, bold: true, color: K.white, align: "left", valign: "bottom", margin: 0 }, text: "" } },
  ],
});
pres.defineSlideMaster({
  title: "CONTENT",
  background: { color: K.white },
  margin: [0.5, 0.55, 0.6, 0.55],
  objects: [
    { placeholder: { options: { name: "title", type: "title", x: M, y: 0.35, w: 9.45, h: 0.85, fontFace: "Cambria", fontSize: 30, bold: true, color: K.navy, align: "left", valign: "middle", margin: 0 }, text: "" } },
  ],
  slideNumber: { x: W - 1.0, y: 7.0, w: 0.5, h: 0.3, fontFace: "Calibri", fontSize: 12, color: K.muted, align: "right" },
});

let n = 0;
function content(title, section) {
  n++;
  const s = pres.addSlide({ masterName: "CONTENT", sectionTitle: section });
  s.addText(title, { placeholder: "title" });
  return s;
}
// Evidence-type tag, top right (text label, so colour is not the only cue)
function tag(s, text, color) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x: W - M - 2.55, y: 0.5, w: 2.55, h: 0.55, fill: { color }, line: { color }, rectRadius: 0.1, objectName: "evidence-tag" });
  s.addText(text, { x: W - M - 2.55, y: 0.5, w: 2.55, h: 0.55, fontSize: 14, bold: true, color: K.white, align: "center", valign: "middle", margin: 0, isTextBox: true, objectName: "evidence-tag-text" });
}
function source(s, text) {
  s.addText("Source: " + text, { x: M, y: 7.0, w: W - 2 * M - 0.7, h: 0.3, fontSize: 12, color: K.muted, margin: 0, isTextBox: true, objectName: "source" });
}
function bullets(s, items, opt) {
  const runs = items.map((t, i) => {
    const o = { bullet: true, breakLine: i < items.length - 1, paraSpaceAfter: 8 };
    if (typeof t === "string") return { text: t, options: o };
    return { text: t.text, options: Object.assign(o, t.options || {}) };
  });
  s.addText(runs, Object.assign({ fontSize: 18, color: K.ink, valign: "top", margin: [2, 4, 2, 0], isTextBox: true }, opt));
}
function card(s, x, y, w, h, fill) {
  s.addShape(pres.shapes.ROUNDED_RECTANGLE, { x, y, w, h, fill: { color: fill || K.tint }, line: { color: fill || K.tint }, rectRadius: 0.08 });
}
function badge(s, x, y, letter, color, d) {
  d = d || 0.6;
  s.addShape(pres.shapes.OVAL, { x, y, w: d, h: d, fill: { color }, line: { color } });
  s.addText(letter, { x, y, w: d, h: d, fontSize: 20, bold: true, color: K.white, align: "center", valign: "middle", margin: 0, isTextBox: true });
}
// Native table helper
function table(s, rows, opt) {
  const hdr = rows[0].map((c) => ({ text: c, options: { bold: true, color: K.white, fill: { color: K.navy }, align: "center", valign: "middle" } }));
  const body = rows.slice(1).map((r, ri) => r.map((c, ci) => {
    const o = { color: K.ink, fill: { color: ri % 2 ? "F7F9FC" : K.white }, align: ci === 0 ? "left" : "center", valign: "middle" };
    if (typeof c === "object") return { text: c.text, options: Object.assign(o, c.options) };
    return { text: c, options: o };
  }));
  s.addTable([hdr, ...body], Object.assign({ fontFace: "Calibri", fontSize: 18, border: { type: "solid", pt: 0.75, color: K.line }, margin: [3, 6, 3, 6] }, opt));
}
const DEV = (s) => tag(s, "DEVELOPMENT EVIDENCE", K.dev);
const PB = (s) => tag(s, "PILOT-B RESULT", K.E);
const OR = (s) => tag(s, "ORIGINAL-PILOT RESULT", "8E4A73");

// ---------- 1. Title ----------
pres.addSection({ title: "Introduction" });
{
  n++;
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Introduction" });
  s.addText("Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs", { placeholder: "title" });
  s.addText("Hinglish mathematical reasoning in LLMs: does the language form of a maths problem change the answer?", { x: M, y: 3.7, w: 10.5, h: 0.9, fontSize: 22, italic: true, color: "CADCFC", margin: 0, isTextBox: true });
  s.addText("Minor project evaluation, November 2026", { x: M, y: 4.7, w: 10, h: 0.5, fontSize: 20, color: K.white, margin: 0, isTextBox: true });
  const lines = [["Student name", "____________________"], ["Roll number", "____________________"], ["Supervisor", "____________________"]];
  s.addText(lines.map((l, i) => ({ text: l[0] + ":  " + l[1], options: { breakLine: i < 2 } })), { x: M, y: 5.45, w: 7, h: 1.3, fontSize: 18, color: K.white, margin: 0, valign: "top", paraSpaceAfter: 4, isTextBox: true });
  ["E", "R", "C"].forEach((f, i) => badge(s, W - M - 2.3 + i * 0.85, 5.75, f, K[f], 0.65));
  s.addNotes("About 20 seconds. One sentence on the question: the same maths in three language forms (English, Romanized Hindi, Hinglish) - does the answer change? Headline we will defend: holding the maths fixed, small models lose accuracy on Romanized Hindi rather than on code-mixing, by a strongly model-specific amount, and answer formats must be checked on excluded data first.");
}

// ---------- 2. Motivation + design ----------
{
  const s = content("Same maths, three language forms", "Introduction");
  const forms = [
    ["E", "English", "“How many marbles does Aman have?”"],
    ["R", "Romanized Hindi", "“Aman ke paas kitne kanche hain?”"],
    ["C", "Hinglish (insertional)", "“23 add karta hai”, “apples aur bananas ka ratio 3:7 hai”"],
  ];
  forms.forEach((f, i) => {
    const y = 1.45 + i * 1.35;
    card(s, M, y, 6.3, 1.15);
    badge(s, M + 0.25, y + 0.27, f[0], K[f[0]]);
    s.addText([{ text: f[1], options: { bold: true, breakLine: true } }, { text: f[2], options: { italic: true } }], { x: M + 1.05, y: y + 0.08, w: 5.1, h: 1.0, fontSize: 18, color: K.ink, valign: "middle", margin: 0, isTextBox: true });
  });
  s.addText("Indian users mix Hindi and English in Roman script; benchmarks are mostly English or Devanagari.", { x: M, y: 5.6, w: 6.3, h: 0.9, fontSize: 18, color: K.muted, margin: 0, valign: "top", isTextBox: true });
  s.addText("The confound", { x: 7.35, y: 1.45, w: 5.4, h: 0.45, fontSize: 22, bold: true, color: K.navy, margin: 0, isTextBox: true });
  bullets(s, ["A drop could come from vocabulary, spelling, mixing, wording, or the evaluation protocol itself"], { x: 7.35, y: 1.95, w: 5.4, h: 1.2 });
  s.addText("Our design", { x: 7.35, y: 3.3, w: 5.4, h: 0.45, fontSize: 22, bold: true, color: K.navy, margin: 0, isTextBox: true });
  bullets(s, ["Matched families: one problem, three renderings", "Gold answer computed in code", "Every analysis paired by family"], { x: 7.35, y: 3.8, w: 5.4, h: 1.8 });
  source(s, "docs/minor_project/slides_outline.md; docs/DECISIONS.md (D033, C definition)");
  s.addNotes("About 80 seconds. Read the three forms aloud and stress that only the language changes. Indian users mix Hindi and English in Roman script, but benchmarks are mostly English or Devanagari. Unrelated English and Hinglish questions cannot separate the possible causes of a drop (vocabulary, spelling, mixing, wording, or the evaluation protocol). Holding the maths fixed can: one problem, three renderings, gold computed in code, and every analysis paired by family. C is insertional Hinglish (Hindi grammar with English nouns, verbs and relation words), the definition adopted after review (D033).");
}

// ---------- 3. RQs and related work ----------
{
  const s = content("Research questions and related work", "Introduction");
  card(s, M, 1.45, 5.95, 1.75);
  s.addText([{ text: "RQ1 (this phase)", options: { bold: true, color: K.navy, breakLine: true } }, { text: "Does an unchanged model's accuracy differ across E, R and C?" }], { x: M + 0.25, y: 1.55, w: 5.5, h: 1.9, fontSize: 20, color: K.ink, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });
  card(s, 6.83, 1.45, 5.95, 1.75);
  s.addText([{ text: "RQ2 / RQ3 (major phase)", options: { bold: true, color: K.navy, breakLine: true } }, { text: "Does E+C training beat matched E+R training on held-out C? Transfer and English retention?" }], { x: 7.08, y: 1.55, w: 5.5, h: 1.9, fontSize: 20, color: K.ink, valign: "top", margin: 0, paraSpaceAfter: 6, isTextBox: true });
  s.addText("Prior work already shows Romanized and code-mixed drops", { x: M, y: 3.85, w: 12.2, h: 0.45, fontSize: 20, bold: true, color: K.navy, margin: 0, isTextBox: true });
  s.addText("MGSM, Anand et al., CodeMixBench, Indi-RomCoM, Sarvam-M, CodeMixTax: an E/R/C gap alone is not novel.", { x: M, y: 4.3, w: 12.2, h: 0.5, fontSize: 18, color: K.ink, margin: 0, isTextBox: true });
  s.addText("Our contributions", { x: M, y: 4.95, w: 12.2, h: 0.45, fontSize: 20, bold: true, color: K.navy, margin: 0, isTextBox: true });
  bullets(s, ["A format-measurement caution", "A paired, reviewed E/R/C resource with operation-word balance", "A pre-registered diagnostic pilot; the controlled training comparison comes next"], { x: M, y: 5.4, w: 12.2, h: 1.5 });
  source(s, "docs/minor_project/slides_outline.md");
  s.addNotes("About 50 seconds. RQ1 is this phase: does an unchanged model's accuracy differ across E, R and C? RQ2 and RQ3 are the major phase: does E+C training beat matched E+R training on held-out C, and what about transfer and English retention? Be explicit that we do not claim the gap as a discovery: MGSM, Anand et al., CodeMixBench, Indi-RomCoM, Sarvam-M and CodeMixTax already show Romanized or code-mixed drops. Our contributions are a format-measurement caution, a paired reviewed E/R/C resource with operation-word balance, and a pre-registered diagnostic pilot; the controlled training comparison comes next.");
}

// ---------- 4. Data ----------
pres.addSection({ title: "Data and protocol" });
{
  const s = content("Data: 370 frozen families", "Data and protocol");
  table(s, [
    ["Split", "Families", "Drafted by", "Human review"],
    ["Pilot-B (evaluated)", "70", "Claude", "One bilingual reviewer: 57 ACCEPT / 13 REVISE / 0 REJECT"],
    ["Phase-2 FINAL_TEST", "100", "GPT", "One reviewer: 32 ACCEPT / 68 REVISE"],
    ["Phase-2 DEV", "40", "GPT", { text: "Sample review of 45 TRAIN/DEV families: 19 ACCEPT / 26 REVISE", options: { rowspan: 2 } }],
    ["Phase-2 TRAIN", "160", "Claude"],
  ], { x: M, y: 1.45, w: 12.23, colW: [2.9, 1.4, 1.7, 6.23], rowH: 0.5 });
  bullets(s, [
    "All frozen 16 Oct with SHA-256 hashes; FINAL_TEST untouched until the confirmatory evaluation",
    "Blind dual-LLM solving: Pilot-B 210/210 (and 15/15 revised); Phase 2 Claude 900/900, GPT 897/900 (one family, GPT error)",
    "No Qwen model ever drafted, solved or checked items",
    "Original 30-family pilot: separate cohort, next slide",
  ], { x: M, y: 4.25, w: 12.2, h: 2.6 });
  source(s, "docs/minor_project/slides_outline.md (pilot_b/FROZEN.md, phase2/*_FROZEN.md)");
  s.addNotes("About 60 seconds. 70 + 100 + 40 + 160 = 370 frozen families, all hashed on 16 October; FINAL_TEST stays untouched until the one confirmatory evaluation. Every item was solved blind by two LLMs: Pilot-B 210/210 (and 15/15 revised renderings); Phase 2 Claude 900/900 and GPT 897/900, the misses all one family and a GPT error. No Qwen model ever drafted, solved or checked items. Review finding: GPT-drafted Romanized Hindi was over-formal (68/100 FINAL_TEST families needed repair, against 13/70 for Claude-drafted Pilot-B); this is descriptive and confounded with the split. C was redefined as insertional Hinglish after review (D033).");
}

// ---------- 5. Original pilot provenance ----------
{
  const s = content("Original pilot: 24-family cohort, honest provenance", "Data and protocol");
  const steps = [
    ["Authoring (D038)", "E written by the author; R and C AI-translated (OpenAI GPT via Codex), then human-reviewed"],
    ["Stage 1: maths", "Solved independently by two human solvers"],
    ["Stage 2: language (D037)", "One human reviewer (R02) plus adjudicator A01. R01's stage-2 file marked 70/90 renderings as unverified AI prefill: excluded from all human-review claims"],
    ["Cohort (D036)", "30 → 24 families, accepted by A01 without repair. Excluded: PIL010 (near-duplicate); 5 repairs with no independent re-review"],
  ];
  steps.forEach((st, i) => {
    const y = 1.35 + i * 1.38;
    card(s, M, y, 8.4, 1.25);
    badge(s, M + 0.2, y + 0.34, String(i + 1), K.navy, 0.56);
    s.addText([{ text: st[0], options: { bold: true, color: K.navy, breakLine: true } }, { text: st[1] }], { x: M + 0.95, y: y + 0.04, w: 7.3, h: 1.17, fontSize: 18, color: K.ink, valign: "middle", margin: 0, isTextBox: true });
  });
  card(s, 9.25, 1.35, 3.53, 5.39, "FBEFF5");
  s.addText([
    { text: "Why it matters", options: { bold: true, color: "8E4A73", breakLine: true } },
    { text: "Different C definition from Pilot-B (D033) and different review provenance.", options: { breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Reported separately; never pooled with Pilot-B.", options: { bold: true, breakLine: true } },
    { text: " ", options: { breakLine: true, fontSize: 8 } },
    { text: "Conversion cross-checked against an independent GPT (Sol) implementation: cohort, hashes, answers and decisions all match." },
  ], { x: 9.45, y: 1.55, w: 3.15, h: 4.3, fontSize: 18, color: K.ink, valign: "top", margin: 0, isTextBox: true });
  source(s, "docs/DECISIONS.md (D033, D036, D037, D038); results/pilot_original/SUMMARY.md");
  s.addNotes("About 60 seconds. Be precise about provenance. D038: the English statements of the original 30 families were written by the author; R and C were AI-translated with OpenAI GPT via Codex and then human-reviewed (the 10 October AI_DRAFT metadata is mistaken for E; frozen files unchanged). The maths was solved independently by two humans. D037: R01's stage-2 file marks 70/90 renderings as unverified AI-prefill suggestions, so the language review is one human (R02) plus adjudicator A01, and R01's AI-prefilled judgments are excluded from human-review claims and agreement statistics; the pre-registration was amended before any cohort output. D036: the cohort is the 24 families accepted by A01 without repair; PIL010 is a near-duplicate and five repaired families lack an independent re-review. The original pilot keeps its own C definition, so it is reported separately and never pooled.");
}

// ---------- 6. Pipeline ----------
{
  const s = content("Pipeline and protocol", "Data and protocol");
  const boxes = [["Frozen data", "SHA-256 hashed"], ["Colab T4", "NF4 4-bit, FP16, greedy, thinking off, 1,024 tokens"], ["Journal", "append-only, fresh context, safe resume"], ["Scorers", "strict v1.0.0 (primary) + numeric_literal_v1"], ["Results ZIP", "checksummed"]];
  const bw = 2.15, gap = 0.37;
  boxes.forEach((b, i) => {
    const x = M + i * (bw + gap);
    card(s, x, 1.55, bw, 2.1, i === 3 ? "E3F0F8" : K.tint);
    s.addText([{ text: b[0], options: { bold: true, color: K.navy, breakLine: true } }, { text: b[1], options: { fontSize: 18 } }], { x: x + 0.12, y: 1.65, w: bw - 0.24, h: 1.9, fontSize: 20, color: K.ink, align: "center", valign: "middle", margin: 0, isTextBox: true });
    if (i < boxes.length - 1) s.addShape(pres.shapes.RIGHT_ARROW, { x: x + bw + 0.06, y: 2.45, w: gap - 0.12, h: 0.3, fill: { color: K.muted }, line: { color: K.muted } });
  });
  bullets(s, [
    "One English instruction (prompt v2) for all forms and all models",
    "Wilson 95% intervals; paired differences with 10,000 family-bootstrap resamples",
    "Analysis plan pre-registered (pilot_b/PREREGISTRATION.md) before any Pilot-B output",
    "The pipeline refuses to resume after any code, data or config change",
  ], { x: M, y: 4.1, w: 12.2, h: 2.7 });
  source(s, "docs/minor_project/slides_outline.md; results/pilot_b/SUMMARY.md");
  s.addNotes("About 40 seconds. Frozen data goes into a Colab T4 notebook: NF4 4-bit weights, FP16, greedy decoding, thinking off, 1,024 new tokens, fresh context per prompt. Outputs go to an append-only journal with resume; the pipeline refuses to resume after any code, data or config change. The strict scorer v1.0.0 is primary, numeric_literal_v1 secondary, and every run's results ZIP hash is recorded. One English instruction (prompt v2) for all forms and models. Wilson 95% intervals, paired differences with 10,000 family-bootstrap resamples. The analysis plan was pre-registered before any Pilot-B output.");
}

// ---------- 7. Dev finding 1 ----------
pres.addSection({ title: "Development evidence" });
{
  const s = content("Dev finding 1: answer format confounds measurement", "Development evidence");
  DEV(s);
  s.addText("Prompt v1 → v2 on 36 excluded fixture prompts (Qwen3-4B)", { x: M, y: 1.4, w: 12.2, h: 0.45, fontSize: 20, bold: true, color: K.navy, margin: 0, isTextBox: true });
  table(s, [
    ["Measure", "Prompt v1", "Prompt v2"],
    ["Format failures (of 36)", "10", "0"],
    ["Strict correct E / R / C (of 12 each)", "9 / 7 / 9", "12 / 10 / 12"],
    ["R explanations in Devanagari (of 12)", "8", "0"],
  ], { x: M, y: 1.95, w: 8.2, colW: [4.6, 1.8, 1.8], rowH: 0.55 });
  card(s, 9.15, 1.95, 3.63, 2.2);
  s.addText([{ text: "Typical v1 failure", options: { bold: true, color: K.navy, breakLine: true } }, { text: "FINAL: 8 unitless", options: { fontFace: "Courier New", breakLine: true } }, { text: "after a correct dimensionless answer" }], { x: 9.35, y: 2.05, w: 3.25, h: 2.0, fontSize: 18, color: K.ink, valign: "middle", margin: 0, isTextBox: true });
  bullets(s, [
    "One disclosed prompt revision (D020), frozen before any pilot output",
    "The fixtures also changed slightly, so 10 → 0 is a development comparison, not an isolated prompt effect",
  ], { x: M, y: 4.55, w: 12.2, h: 2.2 });
  source(s, "docs/minor_project/slides_outline.md; docs/DECISIONS.md (D020). Excluded fixtures, not evaluation data");
  s.addNotes("About 50 seconds. Development evidence on excluded fixtures, not evaluation data. With prompt v1, 10 of 36 fixture prompts failed on format, for example FINAL: 8 unitless after a correct dimensionless answer; with v2, 0 of 36. Strict correct went from 9/7/9 to 12/10/12 of 12, and R explanations in Devanagari from 8/12 to 0/12. This was one disclosed prompt revision (D020), frozen before any pilot output. The fixtures also changed slightly, so 10 to 0 is a development comparison, not an isolated prompt effect.");
}

// ---------- 8. Dev finding 2 ----------
{
  const s = content("Dev finding 2: screening 7 models", "Development evidence");
  DEV(s);
  const ok = (t) => ({ text: t, options: { bold: true, color: "00704F" } });
  table(s, [
    ["Model", "Strict-invalid (of 36)", "Correct E / R / C (of 12)", "Outcome"],
    ["Qwen3-4B", "0", "12 / 10 / 12", ok("Included (primary)")],
    ["Qwen3-8B", "0", "12 / 12 / 12", ok("Included")],
    ["Llama-3.2-3B", "2", "12 / 9 / 9", ok("Included")],
    ["Qwen3-1.7B", "36", "–", "Excluded: instruction echo"],
    ["Phi-4-mini", "14", "–", "Excluded: inline FINAL, R repetition"],
    ["Granite-3.3-2B", "36", "–", "Excluded: commentary after FINAL"],
    ["Gemma-3-4B", "no outputs", "–", "Excluded: CUDA error under FP16"],
  ], { x: M, y: 1.4, w: 12.23, colW: [2.5, 2.6, 3.1, 4.03], rowH: 0.47 });
  bullets(s, [
    "Pre-declared rule: ≤ 3/36 strict-invalid, no per-model tuning → three backbones",
    "Hypothesis (n = 2, unreviewed): Qwen3-4B's R errors misread bhaag (divide) and bhinn (fraction / “different”); tested on slide 11",
  ], { x: M, y: 5.35, w: 12.2, h: 1.55 });
  source(s, "docs/minor_project/slides_outline.md; docs/DECISIONS.md (D028, D030–D032)");
  s.addNotes("About 50 seconds. Development evidence. Within Qwen3, instruction following broke before maths did: Qwen3-1.7B echoed the instruction on all 36. Phi-4-mini put FINAL inline and repeated itself in R; Granite added commentary after FINAL; Gemma-3-4B produced no outputs because of a CUDA error under FP16. The pre-declared rule (at most 3/36 strict-invalid, no per-model tuning) left three backbones. Without this screen, a multi-model comparison would mostly measure formatting. The bhaag/bhinn idea - Qwen3-4B's two remaining errors were R misreadings of bhaag (divide) and bhinn (fraction or 'different'), and Llama gave the same wrong answer on the bhinn item - is a hypothesis from n = 2 unreviewed items; slide 11 tests it.");
}

// ---------- 9. Pilot-B accuracy ----------
pres.addSection({ title: "Pilot-B results" });
{
  const s = content("Romanized Hindi is the lowest form for every model", "Pilot-B results");
  PB(s);
  s.addImage({ path: FIG_A, x: 1.45, y: 1.3, w: 10.4, h: 10.4 * 520 / 1440, altText: "Strict accuracy by form (E, R, C) with 95% Wilson intervals for Qwen3-4B, Qwen3-8B and Llama-3.2-3B, 70 families per bar" });
  table(s, [
    ["Strict accuracy, % [95% Wilson]", "E", "R", "C"],
    ["Qwen3-4B (primary)", "94.3 [86.2, 97.8]", "85.7 [75.7, 92.1]", "94.3 [86.2, 97.8]"],
    ["Qwen3-8B", "98.6 [92.3, 99.7]", "91.4 [82.5, 96.0]", "98.6 [92.3, 99.7]"],
    ["Llama-3.2-3B", "94.3 [86.2, 97.8]", "57.1 [45.5, 68.1]", "70.0 [58.5, 79.5]"],
  ], { x: M, y: 5.15, w: 12.23, colW: [3.83, 2.8, 2.8, 2.8], rowH: 0.42 });
  source(s, "results/pilot_b/SUMMARY.md; figure paper/figures/accuracy_by_form.png. 70 families × 3 forms per model");
  s.addNotes("About 60 seconds. 70 families times 3 forms = 210 prompts per model; all three runs are complete (210/210) and checksum-verified, with no refusals. R is the lowest bar for every model: Qwen3-4B 94.3 / 85.7 / 94.3 percent, Qwen3-8B 98.6 / 91.4 / 98.6, Llama-3.2-3B 94.3 / 57.1 / 70.0. This is single-reviewer data (D035) and a diagnostic sample of 70 families.");
}

// ---------- 10. Paired differences ----------
{
  const s = content("Paired differences: the gap is model-dependent", "Pilot-B results");
  PB(s);
  const c = (d, ci, disc) => ({ text: [{ text: d + " " + ci, options: { breakLine: true } }, { text: "discordant " + disc, options: { color: K.muted } }] });
  table(s, [
    ["Model", "E − R (pp)", "E − C (pp)", "R − C (pp)"],
    ["Qwen3-4B (primary)", c("+8.6", "[−1.4, +18.6]", "9/3"), c("0.0", "[−7.1, +7.1]", "3/3"), c("−8.6", "[−15.7, −1.4]", "1/7")],
    ["Qwen3-8B", c("+7.1", "[0.0, +14.3]", "6/1"), c("0.0", "[−4.3, +4.3]", "1/1"), c("−7.1", "[−14.3, 0.0]", "1/6")],
    ["Llama-3.2-3B", c("+37.1", "[+24.3, +50.0]", "28/2"), c("+24.3", "[+11.4, +37.1]", "21/4"), c("−12.9", "[−27.1, +1.4]", "10/19")],
  ], { x: M, y: 1.4, w: 12.23, colW: [3.03, 3.07, 3.07, 3.06], rowH: [0.5, 0.8, 0.8, 0.8] });
  const tk = [
    ["R deficit", "about 7–9 points for Qwen, 37 for Llama"],
    ["C = E for Qwen", "0.0 for both sizes; Qwen3-4B R − C interval excludes 0"],
    ["Scale helps", "4B → 8B improves every form; R deficit stays (8.6 → 7.1 pp)"],
  ];
  tk.forEach((t, i) => {
    const x = M + i * 4.16;
    card(s, x, 4.75, 3.9, 1.95);
    s.addText([{ text: t[0], options: { bold: true, color: K.navy, breakLine: true } }, { text: t[1] }], { x: x + 0.2, y: 4.85, w: 3.5, h: 1.75, fontSize: 18, color: K.ink, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
  });
  source(s, "results/pilot_b/SUMMARY.md; discordant counts from slides_outline.md. 95% family bootstrap, 10,000 resamples (seed 101)");
  s.addNotes("About 60 seconds. Each cell is the paired difference in percentage points with its 95% bootstrap interval, and the discordant families (first form correct only / second form correct only). For Qwen the E-R intervals cross or touch zero, so call the R deficit modest; for Qwen3-4B the R-C interval excludes zero (C better in 7 families, R in 1). For Llama the R deficit is 37 points and C sits in between. Headline: Romanized Hindi, not code-mixing, is the hard case.");
}

// ---------- 11. Operation-word stratum ----------
{
  const s = content("The operation-word hypothesis is not supported", "Pilot-B results");
  tag(s, "PILOT-B, DESCRIPTIVE", K.E);
  s.addImage({ path: FIG_STRAT, x: 0.9, y: 1.3, w: 11.5, h: 11.5 * 900 / 2400, altText: "Strict R accuracy by operation-word stratum for three models: C keeps Hindi op-word (18 families), C switches to English (17), no Hindi op-word (35)" });
  bullets(s, [
    "R accuracy keep / switch / none: Qwen3-4B 89 / 82 / 86%; Qwen3-8B 94 / 94 / 89%; Llama 67 / 59 / 51%",
    "R errors are spread across families with and without Hindi operation words; many Llama R errors are plain arithmetic slips (PB017: 1200 − 3×265 = 405, answered 435)",
  ], { x: M, y: 5.7, w: 12.2, h: 1.25, paraSpaceAfter: 4 });
  source(s, "results/pilot_b/*/RESULTS.md; figure report/figures/pilotb_r_by_stratum.pdf. Strata of 17–35 families");
  s.addNotes("About 40 seconds. An honest null: the development hypothesis from slide 8 does not explain the gap. R accuracy is similar whether C keeps R's Hindi operation word (18 families), switches it to English (17), or there is no Hindi operation word (35): Qwen3-4B 89, 82, 86 percent; Qwen3-8B 94, 94, 89; Llama 67, 59, 51. Many Llama R errors are plain arithmetic slips, for example PB017: 1200 minus 3 times 265 is 405, Llama answered 435. Strata are small and descriptive.");
}

// ---------- 12. Audit ----------
{
  const s = content("Output audit (Qwen3-4B): what the failures are", "Pilot-B results");
  PB(s);
  const stats = [["18", "strict failures"], ["6", "format-only"], ["12", "substantive"]];
  stats.forEach((st, i) => {
    const y = 1.45 + i * 1.12;
    s.addText(st[0], { x: M, y, w: 1.4, h: 0.95, fontSize: 48, bold: true, color: i === 1 ? K.muted : K.navy, fontFace: "Cambria", align: "right", valign: "middle", margin: 0, isTextBox: true });
    s.addText(st[1], { x: M + 1.55, y, w: 2.4, h: 0.95, fontSize: 20, color: K.ink, valign: "middle", margin: 0, isTextBox: true });
  });
  table(s, [
    ["", "E", "R", "C"],
    ["Substantive errors", "1", "8", "3"],
    ["English-compliant explanations (of 70)", "70", "53", "59"],
  ], { x: 4.75, y: 1.5, w: 8.03, colW: [4.43, 1.2, 1.2, 1.2], rowH: 0.55 });
  s.addText("R substantive: wrong relation or operation 4, misread quantity 2, arithmetic slip 1, unresolved 1", { x: 4.75, y: 3.3, w: 8.03, h: 0.7, fontSize: 18, color: K.muted, margin: 0, valign: "top", isTextBox: true });
  bullets(s, [
    "Two independent AI pre-taggers (Claude, GPT), blind to each other: category agreement 206/210 (κ = 0.94), English compliance 208/210 (κ = 0.96)",
    "Human check of 24 rows (4 disagreements + 20 seeded random); labels are AI pre-tags, human-checked on disagreements and a sample",
    "An audit of model outputs, not of the dataset",
  ], { x: M, y: 4.85, w: 12.2, h: 2.05, paraSpaceAfter: 4 });
  source(s, "results/pilot_b/audit/README.md; results/pilot_b/audit/final_audit_summary.json");
  s.addNotes("About 50 seconds. This is the pre-registered audit endpoint (endpoint 6) for the primary backbone. Of Qwen3-4B's 18 strict failures, 6 are format-only, so 12 are substantive errors: E 1, R 8, C 3. Explanations follow the English instruction on 70/70 E, 53/70 R and 59/70 C outputs, so R also drifts most in language. Method: Claude and GPT tagged all 210 outputs independently and blind to each other (kappa 0.94 for error category, 0.96 for English compliance). A human checked the 4 disagreements plus 20 seeded random agreed rows; the human agreed with tagger A on 22/24 and tagger B on 21/24. The coordinator did the human check. So the labels are AI pre-tags, human-checked on disagreements and a sample. It audits model outputs, not the dataset.");
}

// ---------- 13. Residual format + exploratory ----------
{
  const s = content("Residual format effects and an exploratory note", "Pilot-B results");
  PB(s);
  card(s, M, 1.45, 6.0, 4.6);
  s.addText("Format effects shrink but do not vanish", { x: M + 0.25, y: 1.6, w: 5.5, h: 0.5, fontSize: 20, bold: true, color: K.navy, margin: 0, isTextBox: true });
  bullets(s, [
    "Llama: numeric endpoint agrees with strict on all 210, so its gaps are not formatting",
    "Qwen3-4B: unlisted unit phrases (11 years old, 13 years old, 4 bags of cement) and the spelling 300 rupye cost 4 strict points",
    "Numeric endpoint gap: trailing ₹ (FINAL: 1575 ₹) explains every strict-correct / numeric-fail case (30 Qwen3-4B, 36 Qwen3-8B); reported as pre-registered, not corrected",
  ], { x: M + 0.25, y: 2.15, w: 5.5, h: 3.8, paraSpaceAfter: 6 });
  card(s, 6.83, 1.45, 5.95, 4.6, "FDF1E6");
  s.addText("Exploratory, not pre-registered (Llama)", { x: 7.08, y: 1.6, w: 5.5, h: 0.5, fontSize: 20, bold: true, color: "A04400", margin: 0, isTextBox: true });
  bullets(s, [
    "Explains in Romanized-Hindi prose on 60/70 R and 27/70 C outputs, despite the English instruction (E: 0/70)",
    "On C: Hindi-prose answers correct 13/27 (48%) vs 36/43 (84%) for English explanations",
    "Observational: harder items may trigger both",
  ], { x: 7.08, y: 2.15, w: 5.5, h: 3.8, paraSpaceAfter: 6 });
  source(s, "results/pilot_b/SUMMARY.md; results/pilot_b/{qwen3-4b,qwen3-8b,llama-3.2-3b}/RESULTS.md");
  s.addNotes("About 50 seconds. Format problems shrink but do not vanish after the prompt fix. For Llama the numeric endpoint agrees with strict on all 210, so its gaps are not formatting. For Qwen3-4B, 3 of 4 E failures are correct values with unlisted unit phrases and 1 C failure is the spelling 300 rupye: together 4 strict points. The secondary numeric endpoint has a specification gap: a trailing rupee symbol explains every strict-correct, numeric-fail case (30 for Qwen3-4B, 36 for Qwen3-8B); we report it as pre-registered rather than correcting it post hoc. Exploratory and not pre-registered: Llama explains in Romanized-Hindi prose on 60/70 R and 27/70 C outputs, and on C those answers are correct 48% of the time against 84% for English explanations. This is observational; harder items may trigger both.");
}

// ---------- 14. Original cohort results ----------
pres.addSection({ title: "Original-pilot results" });
{
  const s = content("Original cohort replicates the direction", "Original-pilot results");
  OR(s);
  s.addImage({ path: FIG_ORIG, x: 2.35, y: 1.25, w: 8.6, h: 8.6 * 866 / 2400, altText: "Original 24-family cohort: strict accuracy by form with 95% Wilson intervals for three models" });
  table(s, [
    ["Paired difference, pp [95%]", "E − R", "E − C", "R − C"],
    ["Qwen3-4B (primary)", "+8.3 [0.0, +20.8]", "0.0 [0.0, 0.0]", "−8.3 [−20.8, 0.0]"],
    ["Qwen3-8B", "+4.2 [0.0, +12.5]", "0.0 [0.0, 0.0]", "−4.2 [−12.5, 0.0]"],
    ["Llama-3.2-3B", "+25.0 [+4.2, +45.8]", "−4.2 [−16.7, +8.3]", "−29.2 [−45.8, −12.5]"],
  ], { x: M, y: 4.45, w: 12.23, colW: [3.83, 2.8, 2.8, 2.8], rowH: 0.4 });
  s.addText("24 families, 72/72 per model, 0 strict-invalid. Qwen near ceiling (E 100%); zero-width intervals at ceiling are not evidence of equivalence. Never pooled with Pilot-B.", { x: M, y: 6.15, w: 12.2, h: 0.75, fontSize: 18, color: K.ink, margin: 0, valign: "top", isTextBox: true });
  source(s, "results/pilot_original/SUMMARY.md; figure report/figures/original_cohort_accuracy.pdf");
  s.addNotes("About 50 seconds. The 24-family original cohort was run under the same frozen protocol: all runs complete (72/72), checksums verified, zero strict-invalid outputs. Accuracies E / R / C: Qwen3-4B 100.0 / 91.7 / 100.0; Qwen3-8B 100.0 / 95.8 / 100.0; Llama-3.2-3B 87.5 / 62.5 / 91.7. The pre-specified comparison with Pilot-B is descriptive, with no pooling and no tests: the direction replicates for every model, R lowest and C at or near E. Qwen is near ceiling here because the items are easier. Llama's R deficit replicates (Pilot-B E-R +37.1, cohort +25.0), and here C matches E for Llama too (Pilot-B C was 70.0%). Zero-width intervals at ceiling are not evidence of population equivalence. Provenance as on slide 5: E by the author, R and C GPT-translated then reviewed.");
}

// ---------- 15. Limitations ----------
pres.addSection({ title: "Limitations and plan" });
{
  const s = content("Limitations", "Limitations and plan");
  const L = [
    ["Scale", "Diagnostic: 70 + 24 families; strata of 17–35"],
    ["Review", "Single bilingual reviewer for Pilot-B and FINAL_TEST; TRAIN/DEV sample-reviewed; original pilot: one human language reviewer + adjudicator"],
    ["AI-drafted items", "Claude drafted and solved Pilot-B; original R/C GPT-translated; different C definitions across cohorts"],
    ["Models", "Small, 4-bit, greedy, non-thinking; screening excluded 4 of 7"],
    ["No Devanagari arm", "R gap mixes script, vocabulary, register, spelling; contamination cannot be audited"],
    ["Audit", "AI pre-tags, human-checked on 24/210; primary backbone only"],
  ];
  L.forEach((l, i) => {
    const col = i % 3, row = Math.floor(i / 3);
    const x = M + col * 4.16, y = 1.5 + row * 2.6;
    card(s, x, y, 3.9, 2.3);
    s.addText([{ text: l[0], options: { bold: true, color: K.navy, breakLine: true } }, { text: l[1] }], { x: x + 0.2, y: y + 0.15, w: 3.5, h: 2.0, fontSize: 18, color: K.ink, valign: "top", margin: 0, paraSpaceAfter: 4, isTextBox: true });
  });
  source(s, "docs/minor_project/slides_outline.md; docs/DECISIONS.md (D035–D038); results/pilot_b/audit/README.md");
  s.addNotes("About 40 seconds. Emphasise what the evidence does not show: no causal mechanism and no training result yet. The samples are diagnostic (70 Pilot-B and 24 original-cohort families, strata of 17 to 35). Review is thin: one bilingual reviewer for Pilot-B and FINAL_TEST, TRAIN/DEV only sample-reviewed, and the original pilot's language review is one human plus an adjudicator after excluding R01's AI-prefilled judgments. Items are AI-drafted: Claude drafted and solved Pilot-B; the original pilot's R and C were GPT-translated. Models are small, 4-bit, greedy and non-thinking, and format screening excluded 4 of 7. There is no Devanagari arm, so the R gap mixes script, vocabulary, register and spelling, and contamination cannot be audited. The output audit covers the primary backbone and is AI pre-tagged with a human check on 24 of 210 rows.");
}

// ---------- 16. Status and plan ----------
{
  n++;
  const s = pres.addSlide({ masterName: "TITLE_DARK", sectionTitle: "Limitations and plan" });
  s.addText("Status and plan to May 2027", { x: M, y: 0.4, w: 12, h: 0.85, fontFace: "Cambria", fontSize: 30, bold: true, color: K.white, margin: 0, isTextBox: true });
  s.addText("Done", { x: M, y: 1.4, w: 5.8, h: 0.45, fontSize: 22, bold: true, color: "CADCFC", margin: 0, isTextBox: true });
  const done = [
    "Pilot-B: 3 models, 210/210 each, checksum-verified",
    "Original 24-family cohort: 3 models, 72/72 each",
    "Qwen3-4B output audit (endpoint 6)",
    "EACL 2027 SRW pre-submission mentorship: submitted 26 Oct on OpenReview (Submission #12)",
  ];
  s.addText(done.map((t, i) => ({ text: t, options: { bullet: true, breakLine: i < done.length - 1, paraSpaceAfter: 8 } })), { x: M, y: 1.9, w: 5.8, h: 3.6, fontSize: 18, color: K.white, valign: "top", margin: [2, 4, 2, 0], isTextBox: true });
  const plan = [
    ["5 Dec 2026", "Mentor feedback due"],
    ["15 Dec 2026", "Final paper: new submission to the SRW track"],
    ["Dec–Jan", "T4 training feasibility smoke test; second-annotator sample"],
    ["Feb–Mar", "E+E / E+R / E+C fine-tuning on frozen TRAIN/DEV; one confirmatory FINAL_TEST run"],
    ["Apr–May", "Analysis, thesis; training study for ARR May 2027 (date unconfirmed)"],
  ];
  s.addText("Next", { x: 6.85, y: 1.4, w: 5.9, h: 0.45, fontSize: 22, bold: true, color: "CADCFC", margin: 0, isTextBox: true });
  plan.forEach((p, i) => {
    const y = 1.9 + i * 0.86;
    s.addShape(pres.shapes.OVAL, { x: 6.85, y: y + 0.1, w: 0.22, h: 0.22, fill: { color: K.R }, line: { color: K.R } });
    s.addText([{ text: p[0] + "  ", options: { bold: true, color: K.R } }, { text: p[1] }], { x: 7.25, y, w: 5.55, h: 0.8, fontSize: 18, color: K.white, valign: "top", margin: 0, isTextBox: true });
  });
  s.addText("Holding the maths fixed, small models lose accuracy on Romanized Hindi rather than on code-mixing, by a strongly model-specific amount; check answer formats on excluded data first.", { x: M, y: 6.25, w: 12.2, h: 0.9, fontSize: 20, italic: true, color: K.white, margin: 0, valign: "top", isTextBox: true });
  s.addNotes("About 40 seconds. Done: Pilot-B with three models (210/210 each), the original 24-family cohort with three models (72/72 each), and the Qwen3-4B output audit. The paper 'Romanized Hindi Is Harder Than Hinglish: A Scoring-Aware Audit of Small LLMs' was submitted on 26 October to the EACL 2027 Student Research Workshop pre-submission mentorship on OpenReview, Submission #12, under CC BY 4.0. Mentor feedback is due 5 December; the final paper needs a new submission to the SRW track by 15 December 2026. Then: December-January, a T4 training feasibility smoke test and a second-annotator sample; February-March, E+E / E+R / E+C fine-tuning on frozen TRAIN/DEV and one confirmatory run on FINAL_TEST; April-May, analysis, thesis, and the training study for ARR May 2027 (date unconfirmed). Close on the headline: holding the maths fixed, small models lose accuracy on Romanized Hindi rather than on code-mixing, by a strongly model-specific amount, and answer formats must be checked on excluded data first.");
}

(async () => {
  await pres.writeFile({ fileName: OUT });
  await applyTheme(OUT, THEME);
  console.log("wrote", OUT, n, "slides");
})();
