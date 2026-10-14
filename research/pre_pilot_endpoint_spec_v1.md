# Pre-pilot endpoint specification v1 — proposal

14 October 2026 · Astra (AI research agent) · **Pending human decision; not adopted.**

All prescriptions below are proposals for adoption before reviewed-pilot generation. Recorded probe observations are model-free software evidence, not human validation or research performance. No model inference, training or paid API was used. This document contains no coordinator gold values. The unchanged strict scorer v1.0.0 and original automatic reports remain authoritative for the primary endpoint.

## Evidence and corrections to Claude's review

Re-ran `python3 -B research/claude_review/scorer_probe.py`: all reported counts/reasons reproduce. Plain FINAL passes 30/30; bold marker, bold value, boxed value, dollar-delimited value, a trailing note and incidental “I cannot” each fail 30/30. Rs./Rs prefixes fail 6/6; variable assignment fails 3/3; the five tested romanized unit spellings fail on all six applicable cases. These are synthetic responses applied to draft metadata, not pilot generations. Both scorer source copies are byte-identical.

Corrections/limits: (a) Rs./Rs **prefixes cannot be enabled through aliases**: prefix parsing recognizes only ₹/INR; suffix aliases already include Rs./rs. (b) Blank trailing lines pass; the probe tests a nonblank trailing note. (c) Bold/LaTeX value probes omit units, so their first `invalid_number` failure does not demonstrate that removing the wrapper alone would make every unit-bearing response valid. (d) A form-dependent format penalty is a hypothesis, not an established bias or frequency estimate. No evidence here establishes how often this prompt produces Markdown/LaTeX. (e) The >3/90 invalid/truncated gate concerns protocol revision before scaling; it neither authorizes answer-dependent retries nor erases the first pilot. Eight additional independent synthetic assertions confirm the prefix/suffix distinction, blank-line behavior, incidental/quoted refusal hits and refusal wording missed by the regex.

## 1. Secondary endpoint: extracted numeric value equals gold

Proposed identifier: `numeric_literal_v1`. It measures exact equality of one declared scalar's literal value to the frozen canonical gold value. It is **not semantic accuracy**: units, variable identity and reasoning validity are not checked. A right numeral with a wrong unit can pass; an equivalent quantity expressed in another unit can fail. Do not call the strict-minus-secondary difference “format-only errors” without manual audit.

Apply this deterministic procedure to every selected generated response, independently of strict correctness. Extraction must not consult gold or form; gold is used only for the final comparison. Save original text and byte/character offsets, extracted surface, transformations, rational value, status and flags.

1. Normalize CRLF/CR to LF; translate Devanagari digits and Unicode minus U+2212 as v1.0.0 does. Trim line-edge whitespace, retaining original offsets. No general spelling repair or Unicode compatibility folding. A truncated generation fails with `truncated`, even if it contains an answer. Infrastructure failure is `not_generated`, never an extracted answer.
2. Count case-insensitive `\bFINAL\s*:` occurrences across the entire response, using horizontal whitespace inside this marker (no cross-line matching). Zero gives `missing_final`; more than one gives `multiple_finals`, including quoted/repeated identical markers. Never choose the last or gold-matching answer.
3. The sole marker must begin its trimmed line as `FINAL:`, `**FINAL:**` or `**FINAL**:` (case-insensitive; horizontal whitespace around the colon permitted). Try these marker forms first. Otherwise accept a whole-line bold wrapper `**FINAL: ...**` by removing that balanced outer wrapper and requiring a plain initial marker. If neither rule applies, fail `unsupported_marker`. No heading, bullet, code-fence, inline prose or alternate answer label is stripped. An answer must be on the same line.
4. Ignore all other lines for numeric extraction, including nonblank trailing lines; record `trailing_nonblank=true` when present. Even contradictory trailing prose is not used to select another value: this diagnostic concerns the declared FINAL line only. Another FINAL marker still fails step 2. Never recover an answer from reasoning, a standalone box or a later line.
5. Parse the answer by the grammar below, consuming the entire line; strip at most one terminal sentence period first. `D(t)` means `t` or any balanced nesting of `**t**`, `$t$`, `\boxed{t}` with nonempty contents. Wrappers must enclose a complete grammatical component, not arbitrary fragments. Allow spaces inside wrappers; reject unmatched wrappers, `$$`, underscores, backticks, `\text{}`, `\frac{}` and other LaTeX commands.

   `answer := D([assignment] [currency_prefix] D(scalar) [suffix])`

   `assignment := one ASCII letter followed by '='`; it is optional and does not validate the requested variable. `currency_prefix := ₹ | INR | Rs. | Rs` (case-insensitive words; word boundary after letters; optional whitespace before number). Prefixes are accepted for extraction irrespective of gold unit. Do not support multiple prefixes or assignments, inequalities, expressions, ranges, lists, colon ratios or scientific notation.
6. `scalar` uses v1.0.0's numeric grammar and grouping validation: signed integer/finite decimal (including leading-dot decimal), optionally divided by a signed integer with nonzero denominator; optional terminal `%`. Spaces around `/` are allowed. Accept Western or Indian comma grouping only as validated by v1.0.0. Convert exactly with rational arithmetic; `%` divides by 100. No floating tolerance, rounding, expression evaluation or word-to-number conversion. One percent sign only.
7. `suffix` is either `/-` when a currency prefix is present, or one or more Unicode-letter words separated by spaces (internal apostrophes/hyphens allowed); an optional period is allowed after the single suffix word `Rs`. It may be absent or follow the scalar without a space. Suffixes are retained but ignored numerically, whether known, missing, wrong or combined with a currency prefix. No digits, extra math operators, punctuation or wrapper syntax may remain in a suffix. Unknown word suffixes are flagged `unvalidated_suffix`; do not infer that they denote a valid unit. No unit conversions are performed for this endpoint.
8. If parsing succeeds, `numeric_equal = (extracted_fraction == Fraction(frozen_gold_value))`; status is `match` or `mismatch`. Gold parse errors stop analysis as data errors. A valid unequal number is a mismatch, not an extraction failure. The strict refusal regex does not veto this endpoint; preserve `strict_refusal_hit` and obtain an independent manual refusal tag. Thus incidental refusal language cannot prevent extraction, but a numeric match cannot certify willingness to answer.

For parser failures use exactly one reason: `empty_final`, `malformed_wrapper`, `invalid_numeric_grouping`, `zero_denominator`, or `unsupported_answer`, after the earlier ordered reasons `not_generated`, `truncated`, `missing_final`, `multiple_finals`, `unsupported_marker`. Wrapper balance is checked before numeric validation; grouping before denominator; other grammar failures use `unsupported_answer`. Do not scan for an alternative numeric substring after failure.

Report E/R/C separately: unchanged strict correct/30, secondary match/30, secondary status counts, and strict invalid-reason counts including valid-but-wrong as a separate cell. Cross-tabulate each strict reason against secondary match/mismatch/extraction failure; also show the strict-correct × numeric-match 2×2 table. Missing/invalid/refused-without-parse/truncated generations do not disappear from denominators. For incomplete runs show expected/completed/missing counts and suppress both headline rates/comparisons, matching existing report behavior. On a complete run add descriptive Wilson intervals and paired family differences for the secondary endpoint, using the existing 10,000-resample, seed-101 family method in a separate analysis artifact; 90 prompts still represent 30 families.

**Protection against post-hoc rescue:** human-sign and timestamp this specification, exact parser fixtures/expected outputs, unit/borrowing decisions, code/version hashes, endpoint order and report tables before the first reviewed-pilot generation. Disclose that earlier excluded smoke outputs informed the proposal. Test only new excluded fixtures before freeze; use identical rules for E/R/C and publish all endpoint outcomes regardless of direction. Do not promote the secondary endpoint, alter its grammar from pilot outputs, exclude failures or retry answers. Any later change is a separately versioned exploratory sensitivity analysis with original results preserved. Unit-metadata or prompt repairs after viewing pilot outputs create a development revision, not a clean replacement pilot.

## 2. A01 unit-alias checklist (human gold metadata)

Create an adjudication ledger keyed by canonical unit: candidate spelling, accept/reject, meaning, exact multiplier, allowed omission, rationale, reviewer and date. Apply the same decision to every occurrence of that unit across families and E/R/C; no form-specific alias sets. Aliases require factor 1; other scales belong in `conversions`. Review genuine ambiguous usages in context, not by string similarity. Preserve drafts; approved changes enter a new accepted data version with review history, never an overwrite of v1/v2.

| Unit/domain | Candidates and checks for A01; none newly approved here |
|---|---|
| INR | Existing suffixes Rs., rs, rupaya, rupaye, rupee(s); consider rupaiya, rupaiye. Decide whether Rs./Rs prefix and ₹…/- are linguistically acceptable and record this separately: **metadata cannot make those formats pass strict v1.0.0**. No request to edit its parser. |
| kg / g | kilo, kilogram(s), kilogramme(s), kilogaram; gram(s), gramme(s), garam. Reject ambiguous spellings unless context resolves them; “kilo” must mean kilogram, not an arbitrary kilo-unit. Gram forms require a conversion when canonical unit is kg. |
| minute / h | minat, minut, minute(s), min; ghanta, ghante, ghanton, hour(s), hr, hrs. Check the direction of minute↔hour conversion. |
| L / mL | litar, leetar, liter(s), litre(s); milliliter(s), millilitre(s), mililitar; spelling variants and case normalization. mL is a conversion for L and vice versa, never an equal-scale alias. |
| m / cm / km | mitar, meetar, meter(s), metre(s); sentimitar, centimeter(s), centimetre(s); kilomitar, kilometer(s), kilometre(s). Cross-scale entries require conversion factors. |
| Counts | Check existing kancha/kanche, kitaab/kitaabein, moti, ladki/ladkiyan, pensil/pensilein, kalam/kalamein, tukda/tukde, parchi/parchiyan; consider kitab/kitabein, kitaaben, ladkiyaan. Confirm each noun denotes the requested entity; do not alias all count nouns together. |
| Dimensionless / ratios / percent | Keep empty canonical unit distinct from count units. Do not add arbitrary whole/part/fraction suffixes to cure smoke failures. Freeze scalar ratio orientation and percent convention; `a:b` stays outside the proposed scalar parser. |

Check normalized-key collisions, positive exact conversion factors, singular/plural forms, omission policy and missing aliases in conversion dictionaries too. The current draft allows omission throughout; A01 must affirm this deliberately. Unit acceptance and the shared-token borrowing list are separate decisions: a legitimate unit can still violate the requested output language, and a shared borrowing need not be an answer-unit alias. Any wording repair requires versioning and independent re-review under the existing workflow.

## 3. Fixed manual-audit taxonomy

Audit every completed output, not only disagreements, with pseudonymous reviewer, date, quoted evidence span and reason. Propose two independent bilingual audit passes, then adjudication; retain original tags and report agreement/adjudication counts. Hide automatic scores/secondary outcomes for the initial pass where practical. These are proposed assignments, not completed reviews. `manual_correct` remains a separate documented semantic judgment and must never be populated automatically from numeric equality; an indeterminate judgment stays blank with a reason.

Use exactly one `category` value in each existing `manual_audit.csv` row. Select the first applicable category in this precedence order; record additional applicable values as `additional_categories=[...]` in `reason`. This keeps the existing CSV schema and avoids overwriting automatic columns. If two mathematical causes cannot be distinguished, use `unresolved`, not a guessed cause.

| Ordered category | Operational meaning |
|---|---|
| `truncated` | Output-cap termination prevents a complete-response judgment; still describe visible errors. |
| `refusal` | Explicitly declines the task without subsequently giving an unambiguous committed answer; quoted/incidental inability is not enough. |
| `unresolved` | Ambiguous/missing answer or insufficient evidence to assign a cause; also record suspected item/gold/scorer defect for adjudication. |
| `misread_quantity` | Uses the wrong stated value, entity or requested target, supported by the response. |
| `wrong_relation_operation` | Represents the stated relation incorrectly, including reversed comparison/ratio or wrong operation. |
| `arithmetic_slip` | Correct setup but erroneous arithmetic/algebraic execution. |
| `unit_error` | Wrong physical unit, conversion or count referent; not merely an accepted synonym rejected by metadata. |
| `format_only` | Human finds the answer mathematically and dimensionally correct; strict failure is solely serialization or a documented scorer false positive. Numeric equality alone is insufficient. |
| `language_drift` | No earlier issue; meaningful non-English generated prose violates the English-output policy below. |
| `no_error` | No identified mathematical, unit, format or output-language issue. |

No generated row exists for unresolved infrastructure failure: retain it in the attempt/error ledger, not as invented audited text. Report primary categories and additional-category counts separately (the latter can overlap). The independent language and refusal tags below remain available even when an earlier category takes precedence. Any later taxonomy extension is an exploratory version, never a silent recoding.

## 4. English-output compliance, per input form

In a versioned sidecar keyed by run/rendering/attempt IDs, manually tag `english_status` as `compliant`, `non_english`, `no_explanation`, or `uncertain`. Retain raw tags and adjudication. Judge the entire generated prose, including headings, final-line prose and trailing notes; exclude numbers, equations, variable names, proper names, FINAL marker, approved unit spellings and verbatim input excerpts explicitly marked as quotations. Save excluded spans; an unmarked restatement counts as generated prose. Use a separate frozen output allowlist, not automatic exemption for every input borrowing.

`compliant` requires at least one English explanatory proposition about the solution and no non-English lexical prose outside the exemptions. An English refusal alone or bare calculations/answer are `no_explanation`; any non-exempt Hindi/other-language prose gives `non_english`, even alongside English. Ambiguous romanized homographs unresolved after context review give `uncertain`. Apply non_english before no_explanation; unresolved ambiguity before compliant. Spelling/grammar mistakes in identifiable English are not language drift. Truncated outputs may receive a visible-text tag but do not count as fully compliant.

For each E/R/C report all four tag counts, unreviewed count, and `fully_compliant / expected 30`, where fully compliant requires a complete generated response tagged compliant. Missing, truncated and unreviewed cases cannot inflate the numerator. Also report compliant/fully-audited, nontruncated generated outputs with that denominator explicitly stated. Suppress headline rates on incomplete generation or audit. Language compliance never changes either automatic correctness endpoint.

## 5. Code-mixing index for R and C input texts

Compute on question text only, excluding the common English instruction and reference solution. Use manually adjudicated word labels; do not equate Roman script with English or use an unvalidated automatic detector. Freeze the token/tag table and borrowing policy before pilot generation; store text hash, token offsets/surface, tag, rationale, tagger and adjudicator. Propose two independent bilingual taggers and report agreement before adjudication.

Tokenization proposal: NFC text; maximal letter/combining-mark sequences are words, retaining an internal apostrophe between letters; split hyphens and punctuation as separate tokens. Digit runs with internal numeric separators are number tokens; split letters from adjacent digits (so a quantity plus unit has two tokens). Preserve symbol/punctuation tokens separately, ignore whitespace. No BPE/subword tokens, transliteration normalization or splitting Hindi inflectional suffixes into extra words. English-Hindi mixed morphology within one word gets `MIXED`; deliberate abbreviations are interpreted in context.

Tags: `HI` (Hindi in Roman script, including recognizable spelling variants), `EN` (English lexical material), `SHARED` (numbers, punctuation, symbols, variables, proper names, unit notation and **only** frozen common borrowings), `MIXED` (within-word material from both languages), `UNCERTAIN` (unresolved homograph/unknown). Annotate borrowed multiword expressions token-by-token under a frozen phrase rule. Disambiguate `to`, `is`, `me`, etc. by syntax/meaning; do not mark them SHARED merely because their spellings occur in both languages. Proposed existing borrowings include bus, cycle, jag, tikat and pensil; a Hindi inflection of a borrowing is HI unless that full form is explicitly shared under the frozen policy. Productive English clauses/relations remain EN even when they contain shared words.

For fully adjudicated bilingual texts, let H and E be HI/EN counts, U the SHARED count, and N=H+E+U. Propose `CMI_v1 = 100 × (1 − max(H,E)/(N−U))` if N>U; otherwise 0 with `no_language_tokens=true`. This is the basic word-count CMI of [Das & Gambäck (2014), §3.3](https://aclanthology.org/W14-5152.pdf), with this project's explicitly frozen borrowing policy. Its bilingual range is 0–50; it does not encode switch placement or naturalness. If MIXED or UNCERTAIN remains, set headline CMI to missing and report their counts; do not silently discard them. This conservative missingness rule and borrowing treatment are project proposals, not claims about the paper's annotation scheme.

Optionally report switch count separately: remove SHARED tokens, then count adjacent HI↔EN changes within each sentence; never bridge `.`, `?`, `!` or a newline, and never bridge unresolved/MIXED tokens. Record sentence boundaries during adjudication. Report per-text counts/CMI, and per-form unweighted mean, median, range, nonzero proportion and missing coverage, plus paired C−R differences by family. Do not pool all words as the headline average, set a CMI threshold to certify C, or reject R solely for nonzero CMI: human productive-switch and borrowing judgments remain governing. CMI is descriptive, not evidence of a training effect.

## 6. Refusal regex: pre-pilot decision and fixture gate

Recommend **retaining v1.0.0 as the primary scorer for this pilot** and recording manual actual-refusal tags independently. The probe proves a false-positive mechanism; it does not estimate its frequency. A start-of-response regex alone is insufficient: an opening “I cannot add directly…” can still be valid reasoning. Conversely, some genuine refusals never use the current phrases.

Sol may prepare an isolated v1.1 candidate **only after human approval**, leaving v1.0.0 unchanged. Proposed candidate policy: when an otherwise strict-valid terminal scalar answer exists, do not let a global refusal phrase veto it; retain the regex hit as a diagnostic. “Strict-valid” means parsing/unit validation succeeds with the refusal check disabled, irrespective of numeric correctness. With no strict-valid final answer, retain the v1.0.0 refusal decision. This repairs incidental hits but can accept a number explicitly disclaimed as a guess; human fixtures must test that limitation. Do not automatically adopt this policy or claim it detects all semantic refusals.

Decision evidence: freeze at least 40 new answer-string cases, balanced 20 expected strict accepts and 20 expected rejects, independently labeled before candidate evaluation. Include direct refusals, contractions/curly apostrophes, quotations, reported speech, negated inability, “cannot add directly” at the start/middle/end, refusal followed by a committed answer, refusal plus explicitly disclaimed/quoted number, missing/duplicate FINAL, malformed number/unit, truncation and refusal paraphrases with no regex hit. Vary E/R/C context equally where relevant; the same answer must score identically across forms with the same gold metadata. Check expected correctness **and reason/diagnostic flags**, not just aggregate accuracy.

Require zero unexpected accepts/rejects on this fixed suite and no regressions in existing scorer tests; compare a human audit of any separately authorized excluded model-smoke outputs as additional evidence. If disclaimed-answer cases fail, this simple candidate is not eligible: revise only on development fixtures, add independently labeled holdout cases, and rerun the gate. No observed smoke regex hits does not establish safety. Recommendation: no v1.1 adoption until this gate and explicit pre-generation human sign-off. If approved, report it as an additional versioned sensitivity score beside the unchanged v1.0.0 primary; changing the primary itself requires a different explicitly approved protocol, outside this proposal.

## 7. New EXCLUDED format-smoke fixtures for Sol

Propose ten new underlying engineering families × E/R/C = 30 prompts, authored from scratch with fresh provenance/source/template IDs. The briefs below are coverage targets, not pilot transformations or certified-independent items. Do not copy pilot wording, equations, contexts or substitute numbers into pilot families. A human lineage audit must reject any candidate that turns out to share a pilot family; assigning a fresh ID alone proves nothing. All fixtures/descendants stay permanently excluded from PILOT_EVAL, confirmatory training and final test; use the existing smoke role/exclusion ledger, without presenting them as the planned training-smoke families.

| Proposed IDs (each with -E/-R/-C) | Fresh construction brief and format coverage |
|---|---|
| FMT26-CUR-A | Flat booking fee plus a nonuniform itemized service charge; currency numeral and Rs./Rs suffix/prefix variants. |
| FMT26-CUR-B | Currency-denomination reconciliation with an explicitly defined transaction structure; ₹, INR, /-, decimal and comma-grouping cases. |
| FMT26-ALG-A | Solve a newly authored bracketed linear calibration equation for one scalar variable; bare value versus `x = v`. |
| FMT26-ALG-B | Invert a newly authored affine sensor rule with a negative fractional result; signs, exact fractions and wrapped values. |
| FMT26-RAT-A | Ordered ratio of two independently specified machine cycle lengths, explicitly requesting a single fraction; contrast scalar fraction with rejected colon notation. |
| FMT26-RAT-B | Compare two rates in a fresh scientific measurement context; freeze numerator/denominator orientation and test reciprocal errors. |
| FMT26-MET-A | Fresh tare-mass measurement with mixed scales; kg/g, kilo variants, missing unit and wrong-scale controls. |
| FMT26-MET-B | Fresh instrument calibration converting a measured length between scales; m/cm/km and mitar/kilomitar variants. |
| FMT26-MET-C | Fresh volumetric instrument reading with an explicitly specified calibration offset; L/mL and litar variants. |
| FMT26-MET-D | Fresh instrument timing log with explicitly specified pauses; minute/hour and minat/ghante variants. |

Each family gets human-checked E/R/C mathematical equivalence and gold metadata before use; R/C remain engineering text unless language validation is documented. Add deterministic answer variants for every family: instructed FINAL; each supported bold/box/dollar placement; assignment where applicable; currency prefixes; accepted/rejected aliases; blank/nonblank trailing lines; wrong value/sign/unit; equivalent converted quantity; unknown word suffix; multi-number prose; duplicate/missing FINAL; malformed wrapper/grouping; zero denominator; percent; refusal/contextual inability; and truncation. Freeze expected strict and secondary results, including strict-pass/secondary-fail conversion cases. These string tests are not model-format frequency measurements.

Building/running model-free fixtures is distinct from a GPU run: any later authorized generation smoke must record fixed prompt/config, all 30 outputs and denominators per form without selecting successful examples or retrying invalid answers. Prompt changes require a new version before the pilot; repeated smoke tuning is development. No GPU execution is authorized by this document.

## 8. Proposed reviewer consent and credit note

“You are invited to help review bilingual mathematics questions and/or tag model outputs for a student research project. Participation is voluntary; you may decline or stop without penalty. Before starting, the coordinator will explain the expected work/time, any compensation, what submissions and timestamps are retained, who can access them, and the withdrawal deadline before anonymized aggregation/public release. We use pseudonymous reviewer IDs and keep contact/identity mappings separately; public sharing of contributions or quotations requires the stated permission. Please disclose prior answer exposure; there is no penalty for honest disclosure. Choose separately whether to be named in acknowledgements, credited by pseudonym, or remain unnamed; contribution-based authorship is a separate discussion, not promised by participation. Please confirm consent and your credit preference before work continues.” Coordinator to supply actual terms and check institutional requirements; this proposed wording is not evidence that anyone has consented.

## Decisions needed from the user

- Adopt `numeric_literal_v1` and its exact grammar, denominator/freeze rules and limitations alongside the unchanged strict primary?
- Assign A01 the alias/omission ledger and freeze separate input-borrowing/output-language allowlists; approve a new accepted metadata version if changes are needed?
- Approve the taxonomy, two-pass audit/tagging workload, CMI missingness policy and consent/credit terms; identify responsible humans?
- Retain v1.0.0 only, or authorize a v1.1 candidate for gated supplementary scoring? Authorize fixture construction separately from any later GPU run?

## Tasks for Sol

- After recorded human decisions, implement only adopted rules in a separately versioned analysis module/sidecars; preserve scorer v1.0.0, `report.py` automatic scoring, original raw outputs and draft v1/v2.
- Build the excluded fixture registry and fixed acceptance/rejection tests; obtain human gold, language and lineage decisions. Add tests for malformed/ambiguous inputs, conversion discordance, reason precedence and form invariance.
- Validate exact-value extraction, per-form denominators/cross-tabs, incomplete-run suppression, ID/hash joins and CMI tokenization/formula/coverage on synthetic data; never infer human tags from numeric matches.
- Export endpoint versions, fixtures, hashes and manual tag/audit revisions in a companion analysis package without replacing automatic artifacts. Return model-free test evidence and unresolved choices to Claude for review before any pilot-generation freeze.
