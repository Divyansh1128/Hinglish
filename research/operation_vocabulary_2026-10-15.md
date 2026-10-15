# Operation vocabulary: bounded check and frozen DRAFT covariate

Task 12, Astra; task date 15 October 2026. Scope/provenance: [Claude's handoff](../handoffs/2026-10-15_claude_to_astra.md), [team board](../docs/TEAM_BOARD.md), and [D017–D020](../docs/DECISIONS.md). The [FMT2 v2 report](fmt2_format_test_2026-10-14/README.md#prompt-v2-confirmation-run-decision-d020) describes two R-only comprehension failures involving `bhaag`/`bhinn`; these are excluded development observations (n=2), not pilot results or proof of a lexical cause. Its assertion of rendering correctness is Claude's assessment, not independent bilingual validation. This document adds descriptive tags only; proposals below are not human-confirmed or adopted by silence.

## 1. Bounded literature check

One targeted search pass, capped at 15 minutes; sources accessed 14 October 2026 UTC. Queries combined Hindi/Hinglish/Romanized Hindi with mathematical-operation vocabulary, `bhinn`, ambiguity and benchmarks; separate queries covered MWP keyword cues and transliteration. Primary-paper follow-up was limited to the sources below; no general novelty audit was reopened.

| Primary source | Relevant evidence and boundary |
|---|---|
| [Patel, Bhattamishra & Goyal (2021), SVAMP](https://arxiv.org/abs/2103.07191) | English MWP solvers performed surprisingly well without the question or with bag-of-words input; controlled wording/problem variations exposed shallow heuristics. Pre-modern-LLM evidence about cue reliance, not Hindi homographs. |
| [Mirzadeh et al. (2024), GSM-Symbolic, §4.4](https://arxiv.org/html/2410.05229v1#S4.SS4) | GSM-NoOp reports LLMs turning irrelevant descriptions into operations, including subtraction for smaller fruits and multiplication for discount cues. Direct LLM operation-cue failure evidence in English; it does not establish the Hindi mechanism. |
| [Daroczy et al. (2020), linguistic/arithmetic interaction](https://link.springer.com/article/10.1007/s10339-019-00948-5) | A controlled human experiment crossed lexical consistency with arithmetic factors and found response-time effects/interactions. Supports distinguishing cue meaning from required operation; neither an LLM study nor Hindi evidence. |
| [Sharma, Mishra & Sharma (2022), HAWP, §§3–4, Table 3](https://aclanthology.org/2022.lrec-1.373.pdf) | 2,336 Hindi arithmetic problems and baseline solvers; dataset construction documents wrong word senses and translation errors. This is evidence of Hindi MWP language/annotation difficulty, not an LLM misreading study or a Romanized-Hindi benchmark. |
| [NVIDIA, GSM8K-Hi dataset card](https://huggingface.co/datasets/nvidia/GSM8K-Hi) | Human-reviewed/corrected machine translation of 1,319 GSM8K test items into Hindi. Hindi mathematical evaluation already exists; the card does not isolate operation-word ambiguity. |
| [Yang & Chai (2025), CodeMixBench, §4/Table 2](https://aclanthology.org/2025.emnlp-main.109.pdf) | CM-GSM8K includes Hindi–English and other language pairs; tested models score lower on hi-en than English in Table 2. Aggregate code-mixed math evidence, not a controlled `bhaag`/`bhinn` test; do not assume its script conditions equal this project's R/C definitions. |
| [Sarvam AI (2025), Sarvam-M, §§2.1/3](https://www.sarvam.ai/blogs/sarvam-m), [released GSM8K-Indic](https://huggingface.co/datasets/sarvamai/gsm8k-indic) | Native and Romanized Indic mathematical evaluation/training, including Hindi, is documented in an author technical report. Aggregate results do not identify which operation words caused errors. |
| [Bali et al. (2014), English–Hindi code mixing](https://aclanthology.org/W14-3914.pdf); [Roark et al. (2020), Dakshina, §3.3](https://aclanthology.org/2020.lrec-1.294.pdf) | Nonstandard spelling/transliteration complicates code-mixed processing; Dakshina collects multiple attested romanizations and explains why round-trip native-script reconstruction is imperfect. These motivate spelling/context controls, not claims of mathematical failure. |

**Finding:** related failure classes are documented, but this bounded check did **not locate a primary study isolating Hindi/Romanized-Hindi operation-word polysemy as the cause of LLM math errors**, nor a controlled equivalent study in another code-mixed/low-resource language. This is a retrieval limit, not a novelty claim. Lexical polysemy and transliteration ambiguity differ: [Collins' own Hindi entry](https://www.collinsdictionary.com/dictionary/hindi-english/%E0%A4%AD%E0%A4%BF%E0%A4%A8%E0%A5%8D%E0%A4%A8) records both fraction and different for भिन्न, so that ambiguity exists even in Devanagari. A wrong answer alone cannot show which sense the model used.

## 2. Proposed lexicon (every row requires bilingual human confirmation)

`P` means proposal requiring bilingual confirmation of meaning, naturalness, variants and ambiguity. Variants are candidate common spellings plus explicitly listed inflections, not measured usage frequencies or a standard transliteration scheme. `A` marks a proposed lexically ambiguous word family (polysemy or Roman spelling collision); `C` marks context-dependent relations/actions without a distinct homograph selected here. A-family exposure is a broad risk proxy, not a judgment that a particular sentence or every inflection is ambiguous. The lexicon is deliberately bounded, not an exhaustive inventory of Hindi mathematical language.

| Entry | English meaning | Ambiguity/context; flag | Spellings/inflections included (entry also included) | Status |
|---|---|---|---|---|
| jod | add; sum | join/joint versus addition; A | jodna, jodo, jor | P |
| ghata | subtract; decrease | Roman root can also represent घटा cloud-mass; inflected reduction family; A | ghatao, ghatana, ghataana, ghataayi, ghataai, ghataaya, ghataya, ghati, ghatti | P |
| guna | multiply; times | `guna` can collapse गुणा/गुण (multiplication/quality); A | gunaa, gunan | P |
| bhaag | divide; part/share | भाग part/division versus भाग run (imperative); A | bhag | P |
| bhinn | fraction | also different/distinct in Hindi itself; A | bhin, bhinna | P |
| anupat | ratio | direction and compared quantities need context; C | anupaat | P |
| pratishat | percent | base quantity and sequential changes matter; C | pratishaat, pratisat | P |
| kam | less; fewer | comparative relation, not an automatic subtraction instruction; C | kum | P |
| zyada | more; greater | comparative versus upper bound in `zyada se zyada`; C | zyaada, jyada, jyaada | P |
| bacha | remained; left | Roman consonant simplification can conflate बचा/बच्चा (remained/child); A | bachaa, bache, bachi, bachta, bachti, bachte | P |
| kul | total | also family/clan; A | kull | P |
| yog | sum | also yoga/union; A | yoga | P |
| varg | square | also class/category; A | varga | P |
| har | each/every; denominator | distributive versus mathematical noun हर; A | — | P |
| hissa | part/share | part of which whole is contextual; C | hisa, hissaa, hisse | P |
| baraabar | equal; equally | equality/distribution versus continuous occurrence; C | barabar, baraabr | P |
| baant | divide/share/distribute | sharing does not alone identify the requested quantity; C | bant, baantna, baanto, baanta, baanti, baante, baantte | P |
| vaapas | return; back | refund versus physical return; direction depends on entity; C | wapas, waapas, vapas | P |
| kaat | cut; deduct | physical cutting versus deduction; C | kat, kaata, kata, kaatna, kaatne | P |
| nikaal | remove; take out | also find/derive a result; C | nikal, nikaali, nikali, nikaalna | P |
| milkar | together; combined | combination versus joint work/rate; C | mil kar | P |
| prati | per; each | rate/denominator attachment matters; C | — | P |
| baaki | remaining; rest | remaining quantity versus distance/time; C | baki | P |
| bada / chhota | larger / smaller | size, value or age; direction needs context; C | bada, badi, bade, bara, chhota, chhoti, chhote, chota, choti, chote | P |
| ek jaisi | equal; same | same price versus same kind/appearance; C | ek jaisa, ek jaise | P |

Explicit `bachcha/bachche/bachchon` child forms are excluded. Context risks marked C must not be relabelled A after viewing pilot outputs.

## 3. Frozen descriptive tags for all 30 DRAFT families

Source: [coordinator DRAFT JSON](../pilot/annotation_draft_v2/coordinator/pilot_dataset.DRAFT.json), SHA-256 `9a4434b67941505e9a3679ba6cf0c344f50804230e4fd3591df1f3e192d4711a`. Freeze `operation_vocab_draft_v1`: NFC/casefold question text; tokenize maximal letter sequences; match only the listed finite entries/variants and contiguous multiword phrases, longest phrase first. No stemming, substring matches, English equivalents, symbols, numbers, answers, or generic `aur`/`se`/`mein` tags. List distinct matched surfaces in first-occurrence order, lowercased; `—` means no lexicon match, not no operation. Negated mentions still count as lexical exposure. Table cells contain IDs and words only.

| R rendering ID | Words | C rendering ID | Words |
|---|---|---|---|
| PIL001-R-v1 | kam | PIL001-C-v1 | — |
| PIL002-R-v1 | har, vaapas | PIL002-C-v1 | — |
| PIL003-R-v1 | har, kul | PIL003-C-v1 | — |
| PIL004-R-v2 | hissa, kaat, bache | PIL004-C-v2 | hissa |
| PIL005-R-v1 | anupaat, kul | PIL005-C-v1 | — |
| PIL006-R-v2 | nikaali | PIL006-C-v1 | — |
| PIL007-R-v1 | baraabar | PIL007-C-v1 | — |
| PIL008-R-v1 | zyaada, nikaal | PIL008-C-v2 | nikaal |
| PIL009-R-v1 | bachti, zyaada | PIL009-C-v1 | bachte |
| PIL010-R-v1 | har, vaapas | PIL010-C-v1 | — |
| PIL011-R-v1 | kul, har, baraabar, vaapas, kaat | PIL011-C-v1 | baraabar, vaapas |
| PIL012-R-v1 | baraabar, baantte, har, kul | PIL012-C-v1 | har |
| PIL013-R-v1 | zyaada, har | PIL013-C-v1 | har |
| PIL014-R-v1 | — | PIL014-C-v1 | — |
| PIL015-R-v1 | ghataayi, ghati, ghataaya | PIL015-C-v1 | — |
| PIL016-R-v1 | bachta | PIL016-C-v2 | bachta |
| PIL017-R-v1 | baraabar, baanta, har | PIL017-C-v1 | har |
| PIL018-R-v1 | anupaat, badi, chhoti, zyaada | PIL018-C-v1 | bada |
| PIL019-R-v1 | anupaat | PIL019-C-v1 | — |
| PIL020-R-v1 | bhinn | PIL020-C-v1 | — |
| PIL021-R-v1 | anupaat, nikaali, bhaag, bhinn | PIL021-C-v1 | — |
| PIL022-R-v1 | prati | PIL022-C-v1 | — |
| PIL023-R-v1 | kaata, kaatne, ghatti | PIL023-C-v1 | — |
| PIL024-R-v1 | har, milkar, kul | PIL024-C-v1 | — |
| PIL025-R-v1 | prati, baaki, kul | PIL025-C-v2 | — |
| PIL026-R-v1 | — | PIL026-C-v2 | — |
| PIL027-R-v1 | yog, chhota | PIL027-C-v1 | — |
| PIL028-R-v1 | — | PIL028-C-v1 | — |
| PIL029-R-v1 | milkar, ek jaisi | PIL029-C-v1 | ek jaisi |
| PIL030-R-v1 | varg | PIL030-C-v1 | — |

This is a repository-local pre-registration of descriptive DRAFT tags before pilot generation, not an external registry or human endorsement. **Do not use these tags to edit pilot wording, select items, tune the prompt, or score responses.** Preserve this snapshot. If independently required human review changes text, record a separately versioned pre-generation tag freeze on the accepted text using this same rule, with old/new IDs and hashes; do not silently apply these tags to changed renderings. Confirm meanings with a bilingual human before interpreting lexical causes; this file itself does not record that confirmation.

## 4. Pre-specified exploratory analysis (proposal)

Input-only coverage under this fixed rule: any lexicon match R 27/30, C 10/30; A-family exposure R 19/30, C 5/30; `{bhaag, bhinn}` exposure R 2/30, C 0/30. E has 0/30 matches. These are descriptive text counts, not error rates; the narrow FMT2-motivated C comparison has an empty exposed cell.

- Define `A_present=1` iff any matched surface belongs to an A row; otherwise 0. Freeze this classification independently of outputs. Separately tabulate the fixed FMT2-motivated subset `{bhaag, bhinn}` and listed variants as a sensitivity description; do not choose a better-looking word subset later. Describe C-only cues separately from lexical ambiguity.
- For each form R and C and each A_present stratum, report planned N, generated/scored N, audit-complete N, strict v1.0.0 failures/scored N, and numeric_literal_v1 nonmatches/scored N, as counts and percentages. Include invalid/unextractable generated answers as endpoint failures/nonmatches, not denominator exclusions. Keep these endpoint failure rates separate from semantic/audit errors. E uses this Hindi lexicon only as a zero-exposure reference: do not inherit an R tag onto E or claim an E exposed/unexposed comparison if its exposed cell is empty.
- Use the adopted [D018](../docs/DECISIONS.md) single bilingual auditor/A01 spot-check workflow and [fixed taxonomy §3](pre_pilot_endpoint_spec_v1.md#3-fixed-manual-audit-taxonomy). For every stratum report each primary category count/audit-complete N: `truncated`, `refusal`, `unresolved`, `misread_quantity`, `wrong_relation_operation`, `arithmetic_slip`, `unit_error`, `format_only`, `language_drift`, `no_error`. Preserve precedence; additional-category counts are separate and may overlap. Report the combined primary `misread_quantity` or `wrong_relation_operation` rate as the vocabulary-relevant descriptive outcome, never as proof of vocabulary causation.
- Quote response evidence in the eventual audit: wrong requested target maps to `misread_quantity`; an explicitly wrong relation/operation maps to `wrong_relation_operation`; insufficient evidence or suspected rendering defect maps to `unresolved`. Word presence or numeric mismatch must not assign a cause automatically. A01 reviews suspected non-equivalence; keep original outcomes and disclose any exclusions.
- Report missing generations, unresolved cases and unaudited outputs explicitly; use NA for empty cells, never 0%. Do not present a complete-run headline while generation/audit is incomplete. Once complete, show exposed-minus-unexposed percentage-point differences within form only; retain family IDs and descriptive E/R/C paired outcomes, without treating 90 renderings as independent families.
- **Thirty families cannot support inference about an ambiguity effect.** No significance tests, fitted interaction/regression claims, causal effects or population generalization are planned. Topic, difficulty, target type, sentence length, CMI, word family and form are confounded with exposure; this is hypothesis generation for training/confirmatory work. Freeze before generation, report all prespecified cells even if sparse, and disclose that the hypothesis originated in FMT2 development evidence.

## 5. Future post-pilot dataset design (proposals only)

- Build a bilingual-reviewed design matrix crossing mathematical operation/relation and complexity with operation-word language (Hindi/English), lexical ambiguity, spelling style and explicit versus implicit cues. Include unambiguous controls and reversed/unknown-target comparisons so `kam`/`zyada` cannot serve as one-operation shortcuts; distinguish fraction/count targets and numerator/denominator direction.
- Keep mathematical content and English solution targets paired across E/R/C, while counterbalancing which C items retain Hindi operation words versus English operation words. Otherwise an apparent C advantage can simply reflect removal of difficult Hindi vocabulary. Balance these cells across topics and matched E+E/E+R/E+C exposure budgets; exact quotas/sample size require later design and power decisions, not adoption here.
- Separate polysemy from Roman spelling collisions and unfamiliar formal vocabulary. Use reviewed native-script diagnostic counterparts and independently authored Roman spelling variants in a future evaluation to distinguish script from meaning effects. Preserve naturalness; do not manufacture errors with implausible wording or assume a dictionary ambiguity remains unresolved in context.
- Record intended sense, surface/lemma, operation role, cue position, variant, reviewer rationale and text hash; use independent bilingual review/adjudication for confirmatory data. Split by mathematical family/template before creating variants; keep all variants of a family together and reserve authors/styles or spellings for transfer evaluation. Permanently exclude FMT2 fixtures and pilot families from training; freeze lexicon, balancing rules and analysis before new held-out outputs.
