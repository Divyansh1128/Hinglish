# Test 1 review readiness audit — v1

Audit date: 10 October 2026. Status: **AI static audit; no human acceptance, reviewed pilot or new GPU execution.** This document evaluates the existing draft distribution rather than replacing it. See the [machine-readable audit](astra_review_audit/static_audit_v1.json) for input hashes and exact checks.

The next gate is an honestly documented human review and family audit. The software and short Qwen/T4 smoke are sufficient to prepare that gate; another toy GPU run will not resolve equivalence, independence or reviewer exposure. Before reviewers start, establish who has already seen proposed answers, give them only their separated packets, and address the clear surface asymmetry in PIL026 through versioned repair/re-review if it is retained. Keep the candidate set DRAFT until real submissions support acceptance.

## What was inspected and verified

Read the root README/current status, governing review packet, annotation README, all 30 candidate E/R/C texts and proposed keys, draft register, split manifest, A01 pending decisions, reviewer HTML/embedded blank packets, strict validator, scorer, runner/report/backend, software verification and returned GPU audit. No applicable AGENTS.md was found in the project tree or its home/Desktop ancestors. The source files and returned archives were not edited.

The additional model-free audit checked arithmetic against exact gold using a restricted AST arithmetic walker and `Fraction`, with no `eval()`. PIL030 was checked by its positive-root constraint and squaring 7. Every proposed English reference final was also passed to the existing scorer. These checks verify internal arithmetic/format consistency, not language equivalence or valid authorship/family decisions.

| Evidence | Verified state | Limit |
| --- | --- | --- |
| Candidate coverage | 30 IDs, 90 texts; five candidates in each of six topics | Thirty IDs do not establish thirty independent families |
| Proposed keys | All 30 arithmetic/reference-final checks pass | Human independent solves and equivalence are still required |
| Acceptance | All 30 statuses DRAFT; dataset review lists empty and adjudication null | No human acceptance supplied in inspected files |
| Reviewer distributions | Four embedded packets have 90 rows each; zero answers, no attestation/completion timestamp, all dispositions PENDING | These are distribution templates; a person's progress elsewhere is unknown |
| A01 | Zero accepted decisions; real role assignment and borrowing/split decisions pending | Placeholder A01 is not a completed review |
| Strict reviewed execution | Unchanged validator rejects the drafts: `Human acceptance missing or demo status invalid` | `kind: reviewed` only names intended execution mode |
| Split ledger | 99 development identity strings: 90 pilot identity strings plus nine software-fixture strings | Individualized source/template IDs are provisional semantic groupings |
| Later sets | CONFIRM_TRAIN and FINAL_TEST empty; only the format fixture occupies SMOKE_TRAIN | The 16 future training-smoke families do not exist yet |
| Prior software checks | Recorded 29 model-free test methods, packet syntax/stub-DOM checks and notebook checks | Not reinterpreted as real-browser, human or GPU validation |
| Qwen smoke | Returned audit records six short scored fixtures completed, no infrastructure failures/truncation | Two toy families; not research accuracy, full-pilot or training feasibility |

The proposed scalar answers are all positive: 27 integers and three non-integer fractions. Six gold answers are dimensionless. Median raw character counts are E 142.5, R 164.0 and C 150.5. These characterize the current draft set; they are neither token measurements nor evidence of model difficulty or a causal length effect.

## Reviewer exposure must be established honestly

`git ls-files` confirms the coordinator dataset/register, A01 answer key, pending adjudication and historical five-example review packet are tracked. The repository therefore gives authorized readers access to proposed answers. A private repository protects access from the public; it does not separate a teammate reviewer from gold. An isolated R01/R02 ZIP contains no key, but previous reading of the repository, synopsis, historical examples, chats or A01 packet can still compromise a solve-before-gold claim.

**Actual exposure is unknown.** Availability of reviewers and existence of a readable key are not evidence that any reviewer saw it. Request a short genuine exposure record before stage1: pseudonymous reviewer, items/material seen, approximate timing, whether proposed answers or another person's solutions were seen, and which items were independently solved first. Store personal assignment/contact details outside the shareable repository. Keep the disclosure alongside raw submissions; the runnable schema does not contain a detailed exposure ledger.

Use these outcomes:

1. If neither reviewer saw gold before solving, retain their real timestamped attestations and original stage1 files.
2. If someone independently solved before later seeing gold, retain contemporaneous evidence and disclose the later exposure. Do not recreate an earlier timestamp.
3. If a reviewer saw gold first for an item, preserve the exposed response for descriptive annotation, but do not map it to `independent_solve_before_gold: true`. Obtain an independent solve from an unexposed reviewer, replacing that review role where necessary. Two genuinely eligible reviewers per family and a separate adjudicator must support final acceptance.
4. If eligible reviewers cannot be obtained, author genuinely new versioned candidates and have unexposed reviewers solve them, or keep the affected families DRAFT. Merely changing numbers does not create an independent replacement family. Original candidates and descendants remain development exclusions.

Do not distribute this audit's key-derived discussion or the proposed answer key to stage1 reviewers. They should receive their own packet and the language/rubric instructions only. A coordinator can use this document to arrange the process without coaching a reviewer toward a particular numerical answer.

The stage1 ordering randomizes E/R/C renderings; each person eventually sees siblings of the same family. Thus independence means two reviewers solving without gold/one another's solutions, not 90 independent problem judgments per reviewer. Family-level reporting and the later paired design must preserve that distinction. Reviewers are visibly aware of intended language form; do not call the process fully blinded.

## Family relationships: targeted decisions needed

Sharing a basic skill is not itself duplication. Shared authored/source problem, paraphrase, number substitution or a minimally altered template is. Use equations, quantities/unknowns, relation graphs and actual authoring history together; similarity flags alone do not decide acceptance. The present AI-authored provenance does not establish whether every new candidate was conceived independently. Ask A01 to document the decision and evidence in `family_relationship_checks` for every plausible relationship, prioritizing:

| Candidate relationship | Observed structure | What a human audit must resolve |
| --- | --- | --- |
| PIL002 / PIL010 | Payment minus basket cost; the latter adds a second product term | Is this a minimally extended purchase/change template from the same authoring family? If yes, retain one family slot and retire/replace the other |
| PIL005 / PIL021 | Two-colour ordered-ratio story; total partition versus given one component, addition and new ratio | Same underlying source with a follow-up, or independently authored relation/unknown? Added complexity alone cannot establish independence |
| PIL006 / PIL008 | Stock after removal, with addition versus remaining capacity | Skill overlap may be legitimate; determine whether one is a direct rearrangement/numerical sibling of the other |
| PIL011 / PIL012 | Equal split of money followed by fixed subtraction/addition | Different financial contexts do not alone certify independence; inspect template origin and relation roles |
| PIL004 / PIL016 | Fraction removed; remaining amount versus recovering initial amount | Check reverse-unknown versions/source lineage rather than merging every percentage/fraction problem |
| PIL019 / PIL021 | Infer another component from an ordered ratio; the latter continues with an update | Record whether shared story/template ancestry exists |
| PIL003 / PIL024 / PIL022 | Rate × time/quantity relations; initial amount, combined rates and time conversion differ | Do not collapse all rate skills; inspect direct numerical/paraphrase ancestry and relation differences |
| PIL026 / PIL027 / PIL028 | Linear inverse relations in symbolic/consecutive/perimeter forms | Different contextual models can be distinct; a generic linear-equation skill is not automatically one family |

This is a prioritized reading audit, not a certified exhaustive overlap search. External-source matching is still pending. Unique strings such as `PIL010-proposed-family` cannot prove the semantic claim they name.

If a relationship is confirmed, map its source/template ancestry honestly in the coordinator ledger and retire/replace a slot with a genuinely distinct family. The strict validator forbids repeated source/template identity fields in the accepted 30-family dataset, so do not evade the decision with fresh unrelated IDs. Replacements must preserve five accepted families per topic if that frozen pilot target is retained. No accepted set has been constructed here.

## Language, borrowing and surface-control priorities

Every C candidate has a plausible productive English span on inspection; this is a flag for human verification, not a classification certificate. R generally uses Hindi clauses, but formal vocabulary and periphrastic substitutions can systematically make R harder or less natural than C. The proposed borrowing list must be decided before the final classification/ratings, with bilingual reviewers able to flag exceptions. Do not force unusual Hindi simply to remove ordinary loanwords.

| Priority | Current issue | Recommended review action |
| --- | --- | --- |
| PIL026 | C gives an English verbal restatement of `3x + 7 = 28` while E/R provide the equation without that duplicate restatement | Treat as extra verbal scaffolding/surface redundancy. Prefer matched information/redundancy in all forms, with natural versioned rewrites and independent re-review before freeze |
| PIL009-R | `chipkaane waali parchiyan` for stickers; longer temporal clause | Assess naturalness and whether the referent/timing is readily understood; retain low first-pass ratings if repaired |
| PIL012-R | `bakhshish` for a per-person tip | Decide idiomatic educational wording without changing who pays or the per-person amount |
| PIL018/020/027/028/030-R | Formal terms such as dhanaatmak, maatraon, bhinn, poornank, aayat, parimaap and varg | These may be correct educational Hindi; assess the intended audience rather than declaring them bad. Compare register/difficulty with everyday C terms |
| PIL019-R | `sharbat ke gaadhe ghol` as the syrup component | Confirm it denotes a component, not the finished drink, and retains a volume ratio |
| PIL024-R | `yantra` for machines | Decide naturalness versus a permitted common borrowing before acceptance |
| PIL027/028-C | Productive English largely carries the requested answer; other items switch the operative relation | Validity may differ by switching role. Annotate spans/roles and report descriptively; a mixed set cannot identify a causal switching-location effect |
| PIL020/021 | Explicit number/fraction output for ratios | Preserve the same scalar-answer convention across all forms. A mathematically conventional colon ratio will otherwise fail the existing scalar scorer |

The draft register honestly leaves English/Hindi spans, operation counts and tokenizer lengths unmeasured. Have humans annotate the meaningful spans and disputed borrowings; freeze a consistent operation-count rule if that field is used. Measure formatted prompt tokens with the exact selected tokenizer/template during preflight. Character counts cannot substitute for token counts.

Equivalence review must cover all seven comparisons in the form: quantities, entities, units, mathematical relations, time/order, requested unknown and explicit assumptions. A naturalness rating alone cannot satisfy equivalence. Record human text edits and keep AI_DRAFT origin; human review does not turn an AI-authored item into independently human-authored data.

## Gold, scoring and what Test 1 can measure

The current draft policies already use canonical units for count objects, unlike the defective v1 count demo. All 30 reference final lines score correct. Proposed exact conversions have been software checked, but accepted conversions, alias spellings, permitted omissions and physical assumptions still require A01's real decision. Fractional gold and conversion multipliers must remain exact numeric strings. No blanket tolerance is needed for this draft set.

When a reviewer independently gives an equivalent value in another unit, preserve that answer/unit verbatim in stage1. Mapping to the strict pilot input requires a documented exact canonical conversion and retained originals, not a silent rewrite to match the key. A01 must resolve a genuine disagreement rather than treating the proposed key as ground truth. Repairing text, interpretation or gold creates a new version with an explicit audit trail and any required independent re-review.

The frozen scorer rejects missing or multiple FINAL markers, nonterminal final fields, refusals, token-limit truncation, invalid units and non-scalar forms. Numerically equivalent fractions/decimals and predeclared conversions are accepted. Arbitrary trailing unit words are not accepted. One Hindi explanation can have a correct final number; explanation-language compliance needs a separate manual diagnostic, since the numeric scorer does not test English prose.

The returned T4 run's **original automatic 0/6** remains the correct record of its frozen endpoint. Its six final numeric values match proposed fixture gold only in a post-hoc technical check. Three count outputs exposed blank-unit fixture metadata; three fractional outputs had dimensionless suffixes (`whole`, `fraction`, `part`). The count metadata was repaired in demo-v2; the dimensionless scoring policy was not widened. Neither the toy numerical success nor all-format failure estimates floor/ceiling effects in the 30-family research pilot.

Six research candidates have dimensionless gold, so diagnose suffix failures carefully in the reviewed pilot. Keep primary automatic outcomes, invalid reasons and raw text. Have humans separately assess mathematical interpretation and explanation language using an overlay, without replacing the primary score or choosing retries by answer quality. If systematic format failures dominate, version a protocol/scorer change before a distinct later experiment and apply any bug-fix rescoring consistently to stored outputs. The governing packet's more-than-3/90 invalid/truncated scaling trigger is an existing proposal, not permission to revise a run silently.

The runner reserves input plus the full 1,024-token output budget within the selected context cap and tokenizes all questions before scored generation. It fails rather than silently truncating questions. It records one scoring attempt per rendering, fixed order and immutable inputs/configuration; wrong/invalid answers are not retried. Infrastructure failures leave the run incomplete, and reports suppress headline accuracy/comparisons until resolved. The reports provide E/R/C Wilson intervals, E-C/E-R/R-C family-level paired bootstrap intervals, discordance, failure/token/runtime/memory summaries and descriptive topics.

The 30-family pilot can expose equivalent-language rendering problems, format compliance, answer correctness, latency/tokens/memory and coarse floor/ceiling behavior in this set. It cannot estimate a training effect or establish switching mechanisms. All-positive mostly-integer keys and many short basic problems justify inspecting ceiling effects, not asserting a ceiling. Topic slices have only five families; report their small denominators explicitly. The reported T4 per-generation reserved peak and endpoint free-memory measurements are limited engineering observations, not proof that the longer full workload or optimizer states fit.

## Concrete gate and handoff

Before starting reviewer work, the coordinator should establish actual prior exposure and real role assignments. Preserve only pseudonymous IDs in the shared results. Give each eligible reviewer their separated packet and ask for uncoached stage1 solves before the proposed key or other reviewer's solutions. Use the pre-generation surface audit to decide any PIL026 repair; do not wait for a model to reveal whether redundancy helps.

Collect genuine R01/R02 stage1 and stage2 JSONs, plus A01's completed adjudication and exposure/repair records. Store immutable originals outside the draft builder's output path. Stage2 imports the original stage1 hash and makes those answers read-only, but that software restriction cannot prove truthful independent work. A01 must confirm gold/unit policy, family relationships, borrowing policy and split audit. Any text repair must have versioned hashes and real independent re-review. Preserve disagreement and first-pass ratings for reporting.

After the final accepted inputs are assembled, run the existing validator unchanged, ensure the five-per-topic target and complete permanent exclusion ledger, and freeze all inputs/configuration/prompt/scorer hashes before reviewed inference. Every pilot, retired candidate, software fixture and descendant stays outside later CONFIRM_TRAIN and FINAL_TEST. New IDs do not break the ancestry obligation. The format fixture stored under SMOKE_TRAIN is excluded engineering material, not one of the sixteen unauthored training-smoke families.

The real-browser annotation workflow remains unverified: the previous Node checks used a stub DOM. Before a reviewer spends time on all 90 rows, perform a disposable software-only browser check for download, stage1 import into stage2 and saved progress resume using fictional answers, and keep those files clearly separate from submissions. This is not a new human review and must not populate any acceptance decision. A conversion/import procedure for actual reviewed files also needs to preserve raw answers and exposure records; no automated approval importer has been claimed.

After the unchanged-model reviewed run, return one results ZIP and the executed notebook separately if the ZIP cannot capture it reliably. Independently audit all 90 raw generations, preserving the automatic scores and using versioned overlays. Resolve the actual parsing/truncation/difficulty diagnostics before proposing scaling; separately prepare distinct reviewed training-smoke families when that later stage is authorized.

Source/release terms remain unassigned. The candidates declare no external source used, which is a recorded authoring statement rather than exhaustive originality certification. Log any human-introduced sources/permissions and settle software/dataset release terms before public release. No full training, new inference, approval autofill, external message or paid API was performed for this audit.

## Evidence links

- [Current status](../docs/PROJECT_STATUS.md) and [root README](../README.md): completion claims and the repository exposure notice.
- [Governing review packet](../pilot_review_packet.md), sections 1–6: family, language, review, split, output and descriptive-pilot rules; its opening no-GPU/no-25-drafts statements are historical.
- [Annotation README](../pilot/annotation_draft_v1/README.md), [draft data](../pilot/annotation_draft_v1/coordinator/pilot_dataset.DRAFT.json), [register](../pilot/annotation_draft_v1/coordinator/draft_register.json), [split manifest](../pilot/annotation_draft_v1/coordinator/split_manifest.DRAFT.json) and [pending decisions](../pilot/annotation_draft_v1/A01/adjudication.PENDING.json): actual draft state.
- [Packet verification](../pilot/annotation_draft_v1/verification.json): existing arithmetic/units/syntax/stub-DOM limits.
- [Data validator](../test1_pilot/hinglish_pilot/data.py), [scorer](../test1_pilot/hinglish_pilot/scorer_v1.py), [runner](../test1_pilot/hinglish_pilot/engine.py), [backend](../test1_pilot/hinglish_pilot/hf_backend.py) and [report](../test1_pilot/hinglish_pilot/report.py): inspected software behavior.
- [Returned GPU audit](test1_gpu_smoke_audit_2026-10-10/README.md), [audit measurements](test1_gpu_smoke_audit_2026-10-10/audit.json) and [preserved returned evidence](demo_evidence/README.md): original score versus technical numeric diagnostic and limited T4 inference evidence.
