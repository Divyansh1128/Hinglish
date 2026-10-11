# Sampling and annotation plan — 11 October 2026

**PROPOSAL; no new dataset, reviewer assignment, accepted review, training or experimental result.** This translates the [experiment specification](astra_experiment_spec_v1.md) and [power scenarios](astra_validity_and_power_v1.md) into a feasible human-work plan. The current [v2 packet](../pilot/annotation_draft_v2/README.md) contains 30 AI-authored draft families, including eight repaired renderings in six families. Those repairs improve candidate materials; they do not create new independent families or restore a reviewer's blinding.

User response, 11 October 2026: annotation person-hour budget is **not decided; keep multiple scope options**. This confirms no final sample-size commitment and does not approve any illustrative time estimate.

## Recommendation and scope choices

Finish genuine review of the existing 30-family diagnostic pilot first. Record annotation time and repair demand during that work. Reserve independent final-test authors before creating confirmatory training text. Choose the later evaluation size from available people/time, desired precision, training feasibility and a frozen analysis target; no family count below is a mandatory publication threshold.

| Tier | Proposed role | What the study could honestly claim |
| --- | --- | --- |
| 30 pilot families | Existing unchanged-model diagnostic, after acceptance | Pipeline, language/data quality, runtime, scoring and difficulty diagnostics; no training-effect estimate |
| 100 new final families | Resource-limited three-arm study if feasible | A bounded estimate for the tested authors, topics, checkpoints and recipe; likely inconclusive for modest effects |
| 300 new final families | Larger independent-author evaluation | More useful family precision, without a guarantee of small-effect detection or training-process generalization |
| 600 new final families | Larger annotation commitment, only if supported by capacity | Better precision under the chosen design; still not automatic power for a useful effect or a tight English-retention claim |

The prior exact calculations concern **one fixed checkpoint pair**, assumed discordance and assumed true effects. At a five-point gain and 20% discordance, their positive-direction power is about 14.2%, 44.6% and 76.0% for N=100, 300 and 600. These are not empirical estimates, not power for the proposed seed-averaged endpoint, and not a recommendation to chase a significant result. The actual three-seed analysis still needs its inferential assumptions frozen. A smaller, transparently descriptive project can be defensible; it must narrow its claims before outcomes rather than overstate precision afterwards.

## Proposed population and sampling frame

Define the target as **curated elementary mathematics in six specified topics, rendered under a documented Roman-Hindi/Hinglish policy by the participating authors**. This is narrower than all Hinglish speakers, all educational levels or all mathematics. The topic frame is:

1. `comparison_remaining`
2. `two_step_money`
3. `fractions_percentages`
4. `ratios`
5. `rates_units`
6. `elementary_algebra`

For each topic, make a pre-outcome specification ledger with: intended concept; operation/constraint graph; requested unknown; number of solution steps; representations; units/conversions; numerical domain; explicit assumptions; source and template ancestry; and the authoring role. Avoid allocating hundreds of slots by taking five familiar templates and changing their numbers. A broad topic or operation is not itself a family; conversely, superficial story changes do not make a templated numerical sibling independent.

Use five slots per topic for N=30, 50 for N=300 and 100 for N=600. For N=100, a proposed fixed allocation is 17/17/17/17/16/16 in the order above. Freeze this allocation before evaluation. If the target is equal-topic performance, average the six topic means equally; do not accidentally give the 17-item topics more weight. Report actual accepted counts. The existing 30-family pilot's implemented analysis remains unchanged.

Construct a candidate pool and record its order before model evaluation. Accept/reject using mathematical validity, language equivalence, lineage, permissions and the rubric, without access to model success. Replenish failed slots with independently constructed candidates matching the predeclared stratum; retain exclusions and reasons. Freeze the final accepted pool and hashes before any final-model outputs are inspected. This is a curated sampling process, not a random sample of every possible problem or speaker; interval interpretations must reflect that limitation.

Difficulty descriptors are intended construction criteria, not established psychometric levels. Pilot difficulty may inform the next version of these criteria before final data are frozen. Do not remove final questions because the baseline or a trained arm gets them wrong/right.

## Author separation and the claim it supports

Use role-based identifiers, with real assignments recorded privately. One workable **proposal** is a training-author pool and a disjoint final-author pool. Final authors receive mathematical specifications, the same language policy and task scope, but no training wording, training solutions, draft model outputs or desired answer patterns. They create E/R/C renderings and a proposed solution independently of training text. A separate reviewer pair solves and reviews; an adjudicator resolves issues. An author should not count as either independent reviewer of their own item.

Within final data, spread every author's allocation across topics rather than assigning one author only algebra and another only money. Balance authors as far as capacity permits, with an assignment table frozen before evaluation. If authors specialize by form, cross those assignments across topics/families so form is not perfectly confounded with a single writer. Record both the mathematical-specification author and each rendering's author/editor, including AI assistance and repair history. Human editing does not erase AI origin.

Two or more final authors give a useful check on style sensitivity; they do not by themselves establish population-level author generalization. The simplest defensible primary claim conditions on the participating authors and fitted checkpoints. Report author-level results descriptively alongside family-level uncertainty. Many families from two authors remain two sampled styles, not hundreds of independent author draws. A family bootstrap conditional on fixed authors does not estimate uncertainty for new authors or a new training corpus.

If the intended claim concerns a wider population of authors, define that population, recruitment and sampling process first, recruit enough independently sampled authors to assess between-author variation, and prespecify appropriate clustered/crossed analysis and calibration. Do not improvise that claim by treating author labels as independent after collection. The current power table does not account for author clustering. If only one final author is available, describe transfer to that held-out author's style and limit the conclusion accordingly.

One primary E/R/C triplet per family keeps the workload interpretable. An optional spelling/style variant belongs to the same family, with frozen within-family weights; it does not increase independent N. If language reviewers also authored training material, disclose that and preserve their lack of access to final model outputs. Independent mathematical solving is independence from the proposed answer and the other reviewer, not a claim that seeing one rendering never informs a later rendering of the same family.

## Provenance, ancestry and split safeguards

Maintain a coordinator ledger spanning pilot, rejected drafts, software fixtures, future training smoke, TRAIN, any independent DEV, and FINAL_TEST. Store candidate/family IDs, source/template IDs, parents, author-role IDs, dates, exact text hashes, construction notes, source links where relevant, permissions and disposition. Keep personal contact details out of shareable artifacts. Unknown permissions stay unknown; an internal AI-origin statement is not a declared release license or proof of originality.

Apply these distinctions explicitly:

| Change | Consequence |
| --- | --- |
| Grammar, shelf/cupboard wording, equivalent fraction notation, removing extra explanation | A versioned repair of the same family; new hashes and re-review |
| New numbers, names, objects, paraphrase, spelling or translated form | Same family/ancestry unless substantive evidence establishes otherwise; never automatically a new independent slot |
| New mathematical construction from a distinct specification | Candidate new family, subject to source/template/graph review; a new ID alone is insufficient |
| A broad common skill such as two-step subtraction | A similarity flag, not automatic proof that all instances are one family |
| Unresolved ancestry | Hold out of the accepted independent count until adjudicated; conservative grouping or replacement, with records |

Every existing pilot candidate, rejected draft, smoke fixture and descendant remains permanently excluded from confirmatory TRAIN and FINAL_TEST. Version 2 still inherits version 1 ancestry. PIL002/PIL010, PIL011/PIL012 and PIL005/PIL021 remain review priorities; resolving those examples does not certify all other pairs. The 16 future training-smoke families still need independent construction/review and permanent development exclusion.

Review authoring history and mathematical structure across splits before freeze; use automated similarity only to prioritize inspection. Do not claim the audit certifies absence from model pretraining. For a doubtful shared source/template crossing TRAIN and FINAL_TEST, preserve the relationship and move the entire related group to an appropriate nonconfirmatory role or replace it before final evaluation. Do not hide the overlap by deleting its parent identifier.

## Annotation counts and explicit time assumptions

For N candidate families with three forms and two reviewers:

- Stage1 requires **6N individual rendering solutions** across reviewers (3N per reviewer).
- Stage2 requires **2N triplet reviews**, including **6N form-specific classifications/naturalness/readability assessments** and the required equivalence checks.
- Every family requires adjudicator sign-off, even if its reviewers agree; flagged families may require more investigation and re-review.
- These repeated assessments are quality checks. They do not turn N mathematical families into 6N independent problems.

The following estimates are **unmeasured scheduling assumptions**, not observed productivity or minimum time standards. Reviewers should spend the time correctness requires. The numbers exclude recruitment/training, breaks, meetings, exposure replacement, lineage audits across a large pool, permission work and coordination.

Assume 3 minutes per stage1 rendering; 5 minutes per stage2 triplet per reviewer; 2 minutes of adjudicator review per family plus 8 extra minutes for 25% flagged families. Base review time is therefore `(6×3 + 2×5 + 2 + .25×8)N = 32N` person-minutes.

For planning only, assume 20% of families need one repair cycle: 6 author minutes plus a complete repeated reviewer/adjudicator allowance of 32 minutes. This adds `.20×38N = 7.6N` minutes. Initial independent mathematical specification and E/R/C authoring are provisionally budgeted at 20 minutes per family (8 specification, 12 rendering/solution preparation), another assumption requiring measurement. Existing pilot drafts have already been authored; do not bill that illustrative initial-authoring allowance as new work completed today.

| Candidate families N | Stage1 solutions | Stage2 triplet reviews | Base review hours | Assumed repair/re-review hours | Initial authoring hours | Illustrative total person-hours |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| 30 | 180 | 60 | 16.0 | 3.8 | 10.0 | 29.8 |
| 100 | 600 | 200 | 53.3 | 12.7 | 33.3 | 99.3 |
| 300 | 1,800 | 600 | 160.0 | 38.0 | 100.0 | 298.0 |
| 600 | 3,600 | 1,200 | 320.0 | 76.0 | 200.0 | 596.0 |

These are aggregate person-hours, not elapsed days. Each of the two reviewers has a base `14N/60` hours: 7, 23.3, 70 or 140 hours respectively. Adjudication contributes `4N/60` base hours. Parallel work reduces calendar time only if eligible people actually have that capacity; no available hours are known yet. A repaired family's repeated reviews must be recorded as repeated/versioned decisions, not invented fresh blindness after seeing gold.

The table covers N candidates through an assumed repair cycle, **not a guarantee of N accepted independent families**. Rejection or merging reduces the accepted count. As a separate sensitivity, 20% unrecoverable rejection would require approximately `ceil(N/.8)` candidates: 38, 125, 375 or 750. This attrition assumption is distinct from the repair assumption, unmeasured, and not permission to accept low-quality items to meet a quota. Budget extra full candidate work if attrition occurs. Training/DEV/smoke annotation and optional variants are additional to this final-test table.

During the existing pilot review, voluntarily record active task time by stage (without capturing private browsing or inactivity), number of flags, repairs, re-reviews and lineage exclusions. Use median and range for scheduling; preserve raw decisions. Use these measurements to revise the later budget before final-data generation. Do not pressure reviewers to match the assumed minutes or use speed as acceptance evidence.

## Review execution and remaining human decisions

For the current pilot, use only the v2 reviewer packets for the new round. Obtain actual gold-exposure disclosures first; repository access alone neither establishes exposure nor protects blinding. Supply only the appropriate role packet, keep coordinator/answer-key material away from stage1 reviewers, and preserve authentic responses. Exposure to v1 answers can still matter for v2; changing a version does not erase it. Where solve-before-gold is impossible, use eligible unexposed reviewers or genuinely new candidates and retain exposed judgments with their actual status. Do not mark an exposed reviewer as unexposed merely because they review a repair.

Return the four real R01/R02 stage1/stage2 JSONs, A01 adjudication and repair/re-review records. Acceptance, borrowing policy, exact gold/units, unresolved lineage and split audit require genuine decisions and the unchanged strict validator. AI pre-review and numerical checks cannot supply that approval.

Before committing to final-data collection, the user/faculty must decide: the target author population and permitted AI assistance; available independent authors/reviewers and hours; useful-effect and English-retention margins; the affordable family/seed scope; and whether the paper will make a conditional descriptive or stronger confirmatory claim. The earlier +5-point gain and −2-point English margin remain discussion proposals. Record these decisions before trained-arm outcomes. The next experiment is still the accepted unchanged-model pilot, followed by separately scoped training feasibility; no training is authorized by this plan.
