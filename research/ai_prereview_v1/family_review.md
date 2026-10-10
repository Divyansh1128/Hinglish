# Family structure and review-integrity prereview

**AI REVIEW — NOT HUMAN VALIDATION.** Date: 2026-10-10. Scope: all 30 candidates in `pilot-draft-v1`, inspected for mathematical relation structure, possible shared lineage, and review/split metadata. This is a coordinator-facing audit, not a reviewer submission or approval. It contains structural solutions and must not be given to reviewers before independent solving. No draft, proposed key, review submission, or acceptance field was modified.

## Decision

Do not yet assert that the dataset contains 30 independent mathematical families. It contains 30 candidate IDs with deliberately varied structures, but their independence is explicitly UNVERIFIED. The strongest potential shared-template cases are **PIL002/PIL010** and **PIL011/PIL012**. **PIL005/PIL021** deserves high-priority authoring-history inspection because it reuses a two-colour ratio story with an extension. None is proved to share a source merely by resembling another problem.

Keep the topic target of five accepted families each. If a pair has shared source/template ancestry, one cannot fill two independent slots: retire/replace a slot and preserve both candidates and descendants as development exclusions. New numbers, names, objects, or IDs do not establish a new family. Conversely, grouping every instance of subtraction, ratios, division, or a linear equation together would erase valid distinctions between independently authored problems. Resolve ancestry using actual construction history plus relation graphs, not expression equivalence alone.

## Per-family structural inspection

Notation describes relationships, not a verified independent-authoring record. “No close candidate flagged” means no strong within-set relationship was identified in this reading; it is not external-source clearance. Priority H asks for source/template adjudication first, M asks for a targeted check, and L records mostly generic skill overlap. These are AI triage priorities, not ACCEPT/REVISE/EXCLUDE dispositions.

| ID | Structural signature and requested unknown | Within-set relationship and triage |
| --- | --- | --- |
| PIL001 | Direct comparison: known collection A, B = A − d; ask B | L: PIL009 includes a comparison but first reconstructs an earlier quantity. Direct comparison alone does not imply common lineage. |
| PIL002 | Purchase/change: c = payment − quantity × unit price | H: PIL010 repeats this purchase/change backbone and adds one fixed-price product. Inspect whether PIL010 was derived by extending this example. |
| PIL003 | Initial stock plus constant inflow: final = initial + rate × duration, no outflow/capacity loss | M: PIL024 shares rates but combines two production rates and asks time; PIL022 asks distance with time conversion. Distinct relation roles unless derived from a common authored source. |
| PIL004 | Remaining fraction: remainder = initial × (1 − removed fraction) | M: PIL016 inverts the same removal/remainder relation to ask initial stock. Check reverse-unknown ancestry; fractions versus percentages alone do not distinguish families. |
| PIL005 | Two-component ratio and known total: first = total × a/(a+b) | H: PIL021 reuses a two-colour container ratio story, but provides one component and updates the other before asking a ratio. Inspect shared-story/source extension. |
| PIL006 | Sequential stock changes: final = initial − removed + added | M: PIL008 removes stock then asks unused capacity; it is not a mere numeric substitution in this expression. Check whether both were generated from a common stock-change template. |
| PIL007 | Transfer conserves total and equalizes two stocks: transfer = (A−B)/2 | L: PIL018 uses a known difference but a proportional constraint, not transfer conservation. No close candidate flagged. |
| PIL008 | Remove from stock then fill to capacity: addable = capacity − (stock − removed) | M: PIL006 shares the removal story but has different unknown/constraint. PIL013 shares maximization wording, not the same mathematical model. |
| PIL009 | Reconstruct earlier stock, then compare another person's earlier stock: other = remainder + used + difference | L/M: PIL001 shares the comparison subrelation; PIL006 shares additive arithmetic. Timing and inverse reconstruction distinguish the current task. Ask whether it was an explicit extension of PIL001. |
| PIL010 | Purchase/change with two products: c = payment − (quantity × price + fixed item price) | H: PIL002 is the direct simpler purchase/change backbone. Added operation and changed stationery do not by themselves establish independence. |
| PIL011 | Equal-price decomposition then fee: refund = total ticket cost/count − cancellation fee | H: PIL012 has total/count followed by a per-person adjustment of the opposite sign. Check a common “divide then adjust money” template; different contexts and signs are insufficient ancestry evidence. |
| PIL012 | Equal sharing plus individual surcharge: each pays = bill/count + tip | H: paired concern with PIL011. PIL017 shares equal division only, with no financial adjustment. |
| PIL013 | Budget with fixed fee and per-item cost: maximum integer count = floor((budget−fee)/price) | M: PIL026 solves the affine inverse without an integer-budget constraint. Current numbers divide exactly, so this example does not actually exercise rounding down; preserve that difficulty limitation. Check direct word-problem conversion ancestry if recorded. |
| PIL014 | Nested subsets: club girls = class size × girls fraction × club fraction among girls | L/M: PIL015 also multiplies sequential factors, but changes a price base across discounts; subset conditioning and temporal reductions differ. Same algebraic product alone is not enough to merge. |
| PIL015 | Sequential discounts on changing base: final price = original × (1−d1) × (1−d2) | M: PIL004 is one removal fraction; PIL014 is nested subset selection. Check explicit one-step-to-two-step extension history if any. |
| PIL016 | Inverse percentage remainder: original = remainder/(1−used fraction) | M: PIL004 has the same core stock-removal relation with the unknown reversed. Source history determines whether this is an inverse sibling. |
| PIL017 | Equal partition of fractional volume: share = volume/children | L: PIL023 is measurement division (how many fixed-size pieces), unlike partitive division (size per recipient). PIL011/PIL012 add adjustments. No direct numerical sibling identified. |
| PIL018 | Ratio plus known difference: larger = difference × a/(a−b) | L/M: PIL005 scales a ratio using total instead of difference. PIL007 uses conservation/transfer. Retain relation distinction; inspect ratio-template construction history. |
| PIL019 | Scale known second component to first: syrup = water × a/b | M: PIL021 uses this inference as its first substep before update; PIL005 gives a total instead. A shared ratio calculation is insufficient without source/template evidence. |
| PIL020 | Compose two ratios through shared middle quantity: A/C = (A/B) × (B/C) | L: PIL014 multiplies factors but with subset semantics. No close candidate flagged. |
| PIL021 | Infer second count from ratio and first count, add to second, request new first/second ratio | H: PIL005 has same two-colour container theme; M: PIL019 shares initial scaling substep. Current multi-step relation is different, so review lineage before merging or claiming independence. |
| PIL022 | Constant speed × converted duration gives distance | M: PIL025 splits a journey and asks sum of times; PIL003 has initial stock; PIL024 combines rates. Same rate skill is expected within the topic. |
| PIL023 | Convert length units, then measurement division by piece length | L/M: PIL017 also divides a quantity, but asks share size rather than number of pieces. PIL022 also converts units; the physical relations differ. No direct numerical sibling identified. |
| PIL024 | Add independent production rates, then time = target/(r1+r2) | M: PIL003/PIL022 share rate relations but different state/unknowns. “Different boxes” avoids double counting; it should remain matched across forms. |
| PIL025 | Partition journey distance, then sum segment times: d1/v1 + (D−d1)/v2 | M: PIL022 has one constant-speed segment. Check whether this is an extension of the same authored travel problem; it adds a real relation but not necessarily independent ancestry. |
| PIL026 | Explicit affine equation: ax+b=c, ask x | M: PIL013 is a contextual affine-budget inverse; PIL027 can reduce to this form. Bare algebra form alone cannot define all linear problems as one family. C's extra verbal scaffolding is a separate equivalence issue flagged in the readiness audit. |
| PIL027 | Two consecutive integers: x+(x+1)=sum, ask smaller | M: PIL026 is the resulting affine equation family at an abstract algebra level, but consecutive-integer modelling adds a relation. Inspect whether numbers/equation were lifted from one shared source. |
| PIL028 | Rectangle perimeter: P=2(length+width), ask length | L/M: shares one-variable inverse arithmetic with PIL026/PIL027 but adds geometric definition; no demonstrated shared ancestry. |
| PIL029 | Difference of two purchase equations with a shared notebook term: pen price = total1−total2 | L: PIL002/PIL010 concern paid change, not cancellation of an unknown shared price. PIL001 also subtracts, which is merely skill overlap. No close candidate flagged. |
| PIL030 | Positive-root selection: x²=k, x>0 | L: distinct nonlinear relation/branch constraint in this set. Shared answer value with another item would not indicate lineage. No close candidate flagged. |

## Replacement and adjudication priorities

1. Ask the original drafting coordinator to record whether PIL010 was constructed by extending PIL002, and whether PIL011/PIL012 came from the same divide-and-adjust template. Preserve the actual drafting prompt/source record if available. If history is unavailable, record UNKNOWN and seek adjudication; do not replace that uncertainty with “independent” because IDs differ.
2. Resolve PIL005/PIL021 and PIL004/PIL016 next. Distinguish shared story or inverse-version ancestry from independently composed tasks using the same skill. Review PIL019/PIL021 as a subproblem relationship, and PIL022/PIL025 as a possible single-to-multiple-segment extension.
3. Check the remaining M cases as a documented whole-set audit. Do not limit the ledger to the two pairs already discussed in earlier notes. A01 should record candidate IDs, relation evidence, source-history evidence, decision, rationale, and replacement/retirement mapping.
4. If dependence is established, choose a replacement with a different relation structure and demonstrably separate authoring origin within the affected topic. Do not simply change numbers, objects, or unknowns in the flagged source. Replacement text and all E/R/C forms need new versions and the full review procedure. No replacement is created or accepted by this audit.

No numerical count of “independent families remaining” is defensible from these flags. In particular, subtracting each flagged pair would double-count overlapping relationships and mistake shared skills for confirmed ancestry.

## Metadata and exclusion check

Direct JSON inspection found:

- 30 families, 90 renderings, five candidate families in each of six topics.
- All 30 have `status: DRAFT`, `authoring_origin: AI_DRAFT`, empty reviewer lists and null adjudication. All 30 register entries have `independence_status: UNVERIFIED`.
- Dataset and split `kind: reviewed` describes the intended execution mode only. It cannot serve as evidence of completed review.
- The split audit is pending: `approved: false`, blank reviewer/time, `unresolved_matches: null`. Null is not zero unresolved matches.
- All 30 family/source/template triples agree between dataset and PILOT_EVAL manifest; all 90 corresponding identity strings occur in the development exclusions.
- There are 99 unique exclusion IDs in total: the 90 candidate identity strings plus three identities each for two demo families and one format-only smoke fixture. The lone SMOKE_TRAIN fixture is not the proposed set of 16 training-smoke families. CONFIRM_TRAIN and FINAL_TEST remain empty.
- These 99 strings cover the currently declared identities. They cannot automatically detect unregistered descendants with new IDs; ancestry decisions and future cross-split audits remain required. Retired candidates, repaired descendants and discovered relatives must stay excluded from later confirmatory training/final test.
- The provenance statements say original AI candidates/no external source used for PIL006–030 and carry-forward for PIL001–005. This records an authoring claim, not certified originality or a pretrained-model contamination audit. Release terms remain unassigned.

Two AI agents reviewing the same draft are not the two bilingual human reviewers required by the present protocol. This report must not populate R01/R02/A01 records, calculate human agreement, or bypass validation. Reviewer exposure remains unknown: repository access does not prove that gold was seen, but repository gold makes access separation insufficient. Record actual material/item exposure and timing, retain disclosures, and use eligible unexposed reviewers for first independent solves. If no such process can be completed, retain draft status and label any optional engineering use as AI-prereviewed/demo rather than reviewed research evidence.

## Evidence and reproducibility

Sources inspected: [governing packet](../../pilot_review_packet.md), [draft dataset](../../pilot/annotation_draft_v1/coordinator/pilot_dataset.DRAFT.json), [draft register](../../pilot/annotation_draft_v1/coordinator/draft_register.json), [split manifest](../../pilot/annotation_draft_v1/coordinator/split_manifest.DRAFT.json), and [existing readiness audit](../astra_review_readiness_v1.md). Packet opening claims about missing later drafts/GPU work are historical; this audit uses the actual current draft metadata.

SHA-256 of inspected inputs:

```text
ab37f175df6dc5b7d02ee7ed8a4fc5cacf090e419a8e4272950b9fd269aee92e  pilot_dataset.DRAFT.json
25f63f4c5ef8783936741136a0217cacd54c794268f1ccb56263dcbe3b00c0e0  split_manifest.DRAFT.json
bd51d39034618f284f09d2ea020e9d63f4b2bb20a90b8771cd78adb85a8e02f0  draft_register.json
```

This audit uses text/metadata inspection and deterministic count/set checks. It is not an exhaustive external corpus search, blinded independent solve, or human semantic certification.
