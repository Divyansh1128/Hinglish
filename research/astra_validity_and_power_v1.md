# Validity and sample-size planning for the E+E / E+R / E+C study

Version 1; evidence/search date: 10 October 2026. **PROPOSED DESIGN AND MODEL-FREE PLANNING; NO REVIEWED PILOT OR TRAINING RESULTS.** All numerical scenarios below are hypothetical. The existing T4 run establishes short inference feasibility, not training feasibility or accuracy on accepted research data.

## Recommendation

Retain the controlled three-arm question, and make transfer to independently written C renderings the principal scientific test. Keep the 30-family pilot descriptive. Under the explicit single-checkpoint assumptions below, detecting a genuine five-percentage-point gain needs hundreds to over a thousand independent families; 30 families provide only about 1–3% probability of a positive statistically significant result in the illustrated scenarios. More renderings or seeds cannot be counted as more independent problems.

The immediate gate remains genuine human review, gold-exposure disclosure and family/split adjudication. While that proceeds, freeze the meaning of “useful gain,” the intended test population, author/style separation, and conditional-versus-training-process claims. After the unchanged pilot, conduct separately authorized training feasibility and budgeting before selecting confirmatory sample size. This is an evidence-informed design recommendation, not approval to train.

Prospective power analysis is appropriate for this decision. Card et al. distinguish assumptions about effect size and agreement from observations, and describe paired-classifier planning in §§2–3.1. Here we use exact finite sums rather than infer power from observed demo accuracy. [Card et al., EMNLP 2020, §§2–3.1](https://aclanthology.org/2020.emnlp-main.745.pdf)

## Established requirements, recommendations and open decisions

| Category | Status |
|---|---|
| Established | E+E, E+R and E+C start at the same checkpoint; matched mathematical families/exposure and identical complete English solution targets; paired training seeds; every arm evaluated on E/R/C; permanent development exclusions |
| Established | Pilot 30 families/90 renderings; frozen scorer; invalid/refused/truncated outputs incorrect; infrastructure-incomplete runs remain incomplete; family-level uncertainty |
| Recommended here | Main held-out C text written by bilingual authors independent of training-text generation/editing, without access to training wording or model outputs; one primary contrast; equal family/seed weighting |
| Recommended here | Conditional inference over families for the fitted checkpoints as the default statistical claim; per-seed results and crossed-resampling sensitivity reported separately |
| Proposed, not approved | +5 pp useful C gain; no more than −2 pp English degradation versus exposure-matched E+E; these are project decision examples, not literature-derived universal margins |
| Open before confirmation | Population/topic weights; accepted families; training family count/recipe; checkpoint policy; number of seeds; primary C rendering type; margins; final test size; resources; whether any formal retention/equivalence claim is affordable |

No current accepted data, estimated trained-arm discordance or measured seed variance support choosing a single final N now.

## Matching that is sufficient for this question

For every training family i, store E_i, R_i, C_i and a complete English target T_i. Each arm sees two positions per exposure cycle: E+E=(E_i,T_i),(E_i,T_i); E+R=(E_i,T_i),(R_i,T_i); E+C=(E_i,T_i),(C_i,T_i). Repeated E records are intentional exposures: preprocessing must not deduplicate them. Match family-index schedules, topic distribution, complete supervised target strings, total example exposure, optimizer updates, effective batch size, adapter/optimizer settings, validation use and checkpoint-selection rule. Loss is restricted to the English completion. Ensure all complete targets fit; no silent truncation.

Pair seeds across arms and make the seed-specific family schedule identical. Use separate run/checkpoint directories and record all seeds, not the best seed. Same seed does not guarantee identical stochastic trajectories with different token lengths. Freeze either a fixed-update checkpoint or one shared, predetermined selection criterion on independent development families; choosing each arm's best final-test checkpoint is invalid. If selection uses E-only development accuracy, that is a documented language preference, not neutral tuning.

The treatment changes vocabulary, wording, sequence length and switches jointly. Matching examples and updates does **not** equalize prompt tokens, padding, compute or loss normalization automatically. Record formatted input/target tokens, padding, update time and any packing policy. Prefer disabling packing initially to simplify example exposure; if packing is needed, audit exact arm-wise exposures and effective token weighting. Do not truncate or inject padding as a post-hoc “token control.” A separately preregistered token-budget study could answer a different question.

E+E tests the additional maths-exposure explanation, E+R tests the Romanized-Hindi alternative, and an unchanged checkpoint contextualizes adaptation. E/R/C alone cannot isolate the effect of Latin script relative to Devanagari. The defensible estimand is a training-data-rendering intervention under the tested recipe, not a pure switching mechanism.

The historical two-arm/three-seed recipe is superseded. Three arms × three seeds × 256 optimizer updates would be **2,304** updates, not 1,536. If that recipe is eventually approved, project training time as

`3 × 256 × (median_EE_update_seconds + median_ER_update_seconds + median_EC_update_seconds) / 3600`,

plus measured loading, downloads, save/reload, validation and interruption costs, a stated safety margin, annotation, and final inference. All numbers remain a forecast until measured. Single-T4 inference fit does not imply optimizer/adapter/backward-pass fit.

## Family firewall and transfer design

All translations, paraphrases, spelling variants and numerical siblings remain one family for splitting and inference. Investigate template/source relationships, not just text hashes. AI-origin candidates retain that origin after human correction. Group broader related families conservatively or remove ambiguous overlaps from the confirmatory pool; do not manufacture independence by choosing new numbers. Exclude all pilot, rejected drafts, smoke families and descendants from both confirmatory training and final test. Review source/license records separately from statistical validity. Neither surface similarity tools nor the manifest certify absence from the model's pretraining.

Create a frozen final-test sampling frame before model evaluation. Balance six topics if equal-topic performance is the target; state that this is a curated six-topic population, not all Hinglish maths or all bilingual users. Authors should receive a mathematical specification with quantities/constraints, rather than training sentences. Have another bilingual reviewer verify equivalence, borrowing policy and naturalness without model success influencing acceptance. Do not select final families based on pilot difficulty or whether E+C looks good.

Suggested rendering design:

| Rendering set | Intended role | Statistical handling |
|---|---|---|
| Independent-author E/R/C triplet on each new held-out family | Principal transfer population; choose C here as primary endpoint before confirmation | Each family receives equal weight; all forms paired |
| Separately reviewed C paraphrase or natural Roman spelling variant | Robustness to wording/spelling, preferably same held-out families | Average within family for a prespecified robustness contrast; no increase in independent N |
| Familiar generation-style C rendering, if affordable | Diagnose distribution/style adaptation | Secondary, clearly distinguished from independent-author transfer |

Decide in advance whether the primary outcome uses one independently authored C rendering or averages a fixed number; no best-of-variant scoring. Variant families must not have siblings in training. If several authors create many questions, shared author style can introduce another cluster. Spread work across authors, use whole-author holdouts when feasible, report author-level variation, and restrict claims if only one held-out author is available. Adding renderings tests linguistic robustness and improves within-family characterization, not mathematical-family diversity.

## Estimands and aggregation

Let y(i,s,a,l,v) be binary correctness for family i, paired training seed s, arm a, input form l and predetermined variant v. Infrastructure completeness is resolved before analysis; answer failures remain zero. Average variants within family with equal, frozen weights to obtain z(i,s,a,l). For a single rendering, z=y.

Define d(i,s,l)=z(i,s,E+C,l)−z(i,s,E+R,l). Primary:

`Delta_C_hat = (1/N) Σ_i [(1/S) Σ_s d(i,s,C)]`.

Every family and seed has equal weight. If topic counts differ and an equal-topic estimand was frozen, average families within topic and then average the six topics. Do not retrospectively change weights to improve the result.

Secondary specificity:

`Specificity_hat = (1/N) Σ_i [(1/S) Σ_s {d(i,s,C)−d(i,s,R)}]`.

Preserve the paired four outcomes in every resample. Specificity indicates relative adaptation to input forms, not an internal linguistic reasoning mechanism. Report absolute accuracy and per-seed effects alongside both contrasts. E+E-relative contrasts on C and English retention distinguish extra practice and tradeoffs. Do not pool E/R/C as N×3 independent binary trials, majority-vote seeds, report a best seed, or use N×S as independent sample size.

## Uncertainty and testing options

There are two separate uncertainty targets:

1. **New families, conditional on the S trained checkpoint pairs.** Use 10,000 paired FAMILY bootstrap resamples, seed 101; average the same S seeds in each sampled family. Resample complete records across arms/forms/variants. For a deliberately stratified six-topic sample, resample within topic and preserve frozen topic weights in the new confirmatory analysis. The existing pilot's frozen pooled-family bootstrap is unchanged. Report 95% percentile intervals as approximate, with small-sample/discrete/degenerate warnings. All-zero discordance gives a degenerate bootstrap interval; it is not certainty of population equality. Per-arm Wilson intervals apply to one binary result per independent family/checkpoint; they do not apply mechanically to fractional scores averaged across seeds/variants.
2. **New training randomness and new families.** The same families are crossed with seeds. A family-only bootstrap omits training-process uncertainty. If adequately many paired seeds are affordable, explore separate resampling of family and paired-seed indices, preserving all arm/form associations. Multiway resampling is approximate and can be conservative; its coverage is not guaranteed in this small design. With three seeds, use it only as sensitivity and report all three effects/range, not a calibrated universal-algorithm claim. [Owen and Eckles, 2012, crossed-array bootstrap](https://projecteuclid.org/journals/annals-of-applied-statistics/volume-6/issue-3/Bootstrapping-data-arrays-of-arbitrary-order/10.1214/12-AOAS547.pdf)

For one fitted pair with one binary C rendering per independent family, exact two-sided McNemar tests equal marginal correctness using discordant counts. It conditions on discordance, rather than using two unpaired proportion tests. That is the planning test below. [statsmodels, McNemar exact-test definition](https://www.statsmodels.org/dev/generated/statsmodels.stats.contingency_tables.mcnemar.html)

For the seed-averaged primary estimate, retain the family-level effect interval as the default result. If a formal conditional p-value is required, prespecify a justified family-level paired randomization procedure that swaps the whole checkpoint-arm prediction vector within a family, and assess exchangeability and calibration on separate design simulations. This is not simply McNemar after pooling seeds. Its stronger exchangeability null is not automatically the weak null of mean difference zero. Do not claim an exact test from an unjustified sign flip. Dror et al. discuss matching statistical tests to experimental assumptions and metrics. [Dror et al., ACL 2018](https://aclanthology.org/P18-1128.pdf)

Whole-seed arm-label swapping offers only 2^S sign patterns: a symmetric two-sided test has minimum attainable p=2/2^S. With S=3, that is .25; S=5, .0625; at least six are needed even to make p<.05 possible, not sufficient for reliable power. Equal positive signs in three seeds are useful consistency evidence, not a decisive training-process hypothesis test. Seed replication also does not resample the training corpus or establish another-backbone generalization.

One primary endpoint/contrast avoids a fishing expedition. Keep specificity, E+E contrasts, retention, translation, topics and spelling/style outcomes descriptive with clearly labeled unadjusted intervals unless their confirmatory hypothesis family and multiplicity correction are frozen. If secondary hypothesis tests are essential, specify a fixed list and a correction such as Holm before generation; do not discover whichever form/topic is significant. Repeated prompts, checkpoint searches, interim peeks and final-test reruns are further multiplicity/selection, not harmless evaluation. Report development compute and selection policy; budget itself changes model-comparison conclusions. [Dodge et al., EMNLP 2019](https://aclanthology.org/D19-1224/)

## Reproducible paired-power scenarios

Files under [astra_power](astra_power/) are model-free and read no project generations. Reproduce:

```sh
python3 research/astra_power/paired_planning.py
```

No dependencies beyond the Python standard library; no CUDA, training or paid APIs. `planning_manifest.json` records UTC timestamp, Python version, assumptions, code/output hashes and seed 20261010 for validation simulation. Exact summation itself has no random seed. Files carry PLANNING labels.

For a single fixed pair, let D_i∈{−1,0,1}, assumed improvement δ=E[D_i] and assumed discordance q=P(|D_i|=1). Then p+=P(D=1)=(q+δ)/2, p−=(q−δ)/2, with |δ|≤q. For baseline B accuracy b:

`both_correct = b − p−; both_wrong = 1 − b − p+`.

Require all four cells nonnegative. We assume b=.55 to instantiate valid paired tables; this is not measured. For fixed feasible δ and q, McNemar power does not depend on how the concordant mass divides into both-correct and both-wrong. Baseline still matters for floor/ceiling feasibility and interpretation.

Under these i.i.d.-family assumptions:

`M ~ Binomial(N,q); B_plus | M=m ~ Binomial(m,(q+δ)/(2q))`.

For each m, exact rejection at α=.05 is based on the two symmetric Binomial(m,.5) tails. Sum rejection probability over M. Floating-point evaluation of the finite sums is “exact power” in the probabilistic-method sense, rather than an asymptotic approximation. Report both any-direction rejection and correct-positive-direction rejection; the table uses the latter, preventing rare wrong-sign detections from being called beneficial power. Parameter assumptions are not empirical estimates, and these calculations are **not** power for seed-averaged/bootstrap/equivalence/retention endpoints.

| Assumed discordance q | True gain δ | N=30 | N=100 | N=300 | N=600 | N=1,000 | Approx. N for 80%* |
|---:|---:|---:|---:|---:|---:|---:|---:|
| .10 | +3 pp | 0.5% | 8.7% | 30.4% | 60.4% | 83.5% | 870 |
| .10 | +5 pp | 1.2% | 24.1% | 74.5% | 97.3% | 99.9% | 312 |
| .10 | +10 pp | 7.3% | 94.2% | 100.0% | 100.0% | 100.0% | 77 |
| .20 | +3 pp | 1.7% | 6.5% | 17.9% | 34.2% | 53.8% | 1,742 |
| .20 | +5 pp | 2.9% | 14.2% | 44.6% | 76.0% | 93.8% | 626 |
| .20 | +10 pp | 9.9% | 54.4% | 97.4% | 100.0% | 100.0% | 155 |
| .40 | +3 pp | 2.3% | 5.0% | 10.9% | 19.4% | 30.5% | 3,487 |
| .40 | +5 pp | 3.4% | 9.3% | 24.7% | 46.6% | 69.0% | 1,254 |
| .40 | +10 pp | 8.0% | 29.9% | 76.1% | 97.0% | 99.9% | 312 |

*The last column is a large-sample approximation, not the exact minimum or an approved sample size:

`N_80 ≈ ceil[(z_.975 sqrt(q) + z_.80 sqrt(q−δ²))² / δ²]`.

Exact discreteness can require more families (e.g. N=300 gives only 74.5% for δ=.05,q=.10). The exact grid is the useful evidence here. A five-point gain at N=30 equals only 1.5 expected net extra correct families; high variance and sparse discordance make the descriptive pilot appropriate. More discordance at the same mean difference means more gains offset by losses, hence greater variance. Topic-specific inference with five families is weaker still.

The script checks seven categories: binomial normalization/means/endpoints/large-N stability; exact critical boundaries; null size≤.05 and deterministic alternatives; independent brute multinomial enumeration for N=0…8; impossible paired-cell rejection; crossed-variance identities; and Monte Carlo validation. At q=.20,δ=.05, 20,000 simulations yielded 0.02785 any-direction rejections at N=30 versus exact .030135, and .44785 at N=300 versus exact .445964. Both were within five Monte Carlo standard errors. These synthetic checks verify calculations, not research effects.

## Why seeds do not multiply the sample size

Separate sensitivity—not a bounded binary generator—uses the additive crossed model

`D_is = μ + U_i + V_s + W_is`,

with independent zero-mean random effects of variances σ_F², σ_S², σ_FS². Directly summing covariances gives

`Var(mean D) = σ_F²/N + σ_S²/S + σ_FS²/(N S)`.

This is an algebraic planning model for dependence. Individual D values here are continuous; it is not a claim that arbitrary Gaussian draws form actual correctness tables. We explore q=.20,δ=.05 (total single-cell variance .1975), family variance shares .30/.80 and seed-effect SDs 0/.01/.03. All are assumed; the returned inference smoke supplies no trained-seed estimate.

Example with 80% family share and three-point seed-effect SD:

| Families N | Paired seeds S | Correct crossed SE | Incorrect i.i.d. N×S SE | 1.96×crossed SE (sensitivity, not calibrated CI) |
|---:|---:|---:|---:|---:|
| 30 | 3 | 7.74 pp | 4.68 pp | 15.18 pp |
| 30 | 10 | 7.41 pp | 2.57 pp | 14.52 pp |
| 300 | 3 | 2.95 pp | 1.48 pp | 5.78 pp |
| 300 | 10 | 2.51 pp | 0.81 pp | 4.92 pp |
| 1,000 | 3 | 2.17 pp | 0.81 pp | 4.25 pp |
| 1,000 | 10 | 1.59 pp | 0.44 pp | 3.11 pp |

When family variation dominates, extra seeds barely rescue 30 families. When seed variation matters, increasing N alone leaves the σ_S²/S floor. Equal seeds are useful for stability and pairing, but their uncertainty must not be disguised as thousands of independent renderings. Under constrained resources, a carefully limited conditional claim plus transparent seed variation is more honest than claiming reliable algorithm-level significance.

## Useful-gain and English-retention decisions

**Proposal only:** consider +5 percentage points absolute C accuracy versus E+R a useful gain, because acquiring/reviewing C-specific training has a real cost. Consider more than −2 pp English accuracy versus E+E unacceptable for an unqualified useful-adaptation claim; also report English versus the unchanged checkpoint and E+R. These round values make the decision concrete but are not established by a deployment study. The user/faculty must adopt or revise them before confirmatory outcomes. A different application, annotation cost or safety need can justify different margins.

Separate statistical superiority to zero from usefulness. A 5 pp point estimate with a CI crossing zero is inconclusive. A positive interval entirely below 5 pp can establish a small advantage while failing the proposed usefulness criterion. To confidently claim “at least 5 pp,” the lower confidence bound must exceed .05 and power must be planned against a true effect greater than .05. The table tests the zero-difference null; it does not establish practical superiority beyond the margin.

English noninferiority within 2 pp is a precision-demanding additional endpoint. For a fixed pair with no true English difference and assumed q_E=.20, a rough one-sided α=.05, 80%-power normal approximation is

`N ≈ (z_.95 + z_.80)² q_E / .02² ≈ 3,092 families`.

This is a scale warning, not exact planning: actual paired counts, seed effects and chosen comparison change it. For q_E=.10/.40, the same rough calculation is about 1,546/6,183. An underpowered failure to detect English loss does not certify retention. If this precision is unaffordable, report the tradeoff interval and a limited conclusion; do not widen the acceptable margin after seeing the result.

Formal equivalence of E+C and E+R requires a prespecified interval of negligible effects and a justified paired test or calibrated interval. Nonsignificance is not equivalence; a wide interval around zero is inconclusive. A conventional TOST has two one-sided α=.05 tests (equivalent to a valid 90% two-sided interval inside the bounds), but this primer's t-test formulas cannot be copied mechanically onto our clustered binary/seed-averaged endpoint. Build appropriate planning/calibration if equivalence becomes a goal. [Lakens, 2017, equivalence primer](https://pmc.ncbi.nlm.nih.gov/articles/PMC5502906/)

## Interpretation and stopping rules

| Finding | Defensible conclusion |
|---|---|
| C gain transfers across held-out authors/styles/spellings, coherent across seeds | Transfer value under this checkpoint/recipe/population; replication strengthens, rather than proves universal generality |
| Gain only for familiar generator/style | Distribution/style adaptation; do not describe broad Hinglish reasoning gains |
| C gain with material English degradation | Adaptation tradeoff, with estimated costs; not unqualified improvement |
| R gain and C gain differ in the specificity contrast | Relative specialization; no internal mechanism is identified |
| Narrow effect interval excluding a useful positive gain | Evidence against a gain of that useful size in this setting, not proof of exact equality |
| Wide interval overlapping zero and useful gains/losses | Inconclusive; retain both possibilities and do not select the best-looking seed/topic |
| E+C worse with sufficiently precise negative difference | Evidence against this data choice under this recipe; investigate without rewriting the confirmatory outcome |
| Repeated floor/ceiling or severe parsing failures in development | Pilot indicates a measurement/difficulty problem; version development protocol; construct a new frozen final test without accuracy-favoring selection |

Do not grow the final sample repeatedly until p<.05 or change the primary contrast after outcomes. Final size and allowable handling of missing/infrastructure failures belong in the preregistration. Any blinded information-based sample-size re-estimation needs a separately prespecified valid procedure; this document does not authorize one. A null or tradeoff result can still answer a useful controlled question if its intervals, transfer design and limitations are clear.

## Concrete next choices

1. Complete genuine annotation/exposure/family adjudication. Freeze the 30-family pilot as development only.
2. Freeze the primary final C population, equal-family weighting, pairing/variant handling and conditional claim language. Reserve independent authors before training-text generation.
3. Ask the user/faculty to adopt practical margins without presenting them as already approved. Freeze them before trained-arm outcomes.
4. Run the unchanged-model pilot after acceptance. It can diagnose difficulty/scoring/runtime; its E-vs-C discordance is **not** an estimate of E+C-trained-vs-E+R-trained discordance.
5. Measure bounded training feasibility on separate excluded inputs. Use three-arm budget projections; no full training now.
6. Revisit a range of q, δ and seed-variance assumptions using independent development data if available. Choose an affordable design and narrow the claim honestly if power/retention precision cannot be achieved. Keep final-test outcomes untouched until this decision is frozen.

Version 1 created as a planning artifact. No AI-authored review approval, trained model, confirmatory score, completed reviewed pilot or observed improvement is claimed.
