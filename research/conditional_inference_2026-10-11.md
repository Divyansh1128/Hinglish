# Conditional inference contract: seed-averaged paired family differences

11 October 2026. **Research design recommendation, not an approved preregistration or model result.** No training, reviewed pilot, human acceptance, or new model inference was performed for this note. It resolves an analysis-design gap in [the experiment specification](astra_experiment_spec_v1.md) and [validity planning](astra_validity_and_power_v1.md); it does not change the frozen pilot software.

## Decision

Use a confidence-interval-first report for the primary E+C-trained minus E+R-trained C accuracy difference. Keep the three trained pairs fixed when resampling families. Do not report a finite-sample exact sign-flip p-value for the weak null of zero mean improvement. Before confirmation, choose the family population, topic weights, author scope and independent sampling unit. A bootstrap cannot make a purposively selected benchmark representative, and three seeds cannot establish training-process generalization.

Retain the proposed paired percentile family bootstrap as an **approximate conditional interval**, subject to design simulations and independence assumptions. Always label its coverage target and report degeneracy. Add a prespecified conservative bounded-mean reference interval when its independence assumptions hold. Neither method can correct lineage overlap or shared author dependence by merely increasing the resample count.

## What is the probability statement about?

| Target | Interpretation and allowable uncertainty |
| --- | --- |
| These exact curated families and these exact checkpoints | Once deterministic generations are resolved, the complete benchmark difference is a finite-set descriptive quantity. There is no family-sampling uncertainty about that census. Bootstrap intervals describe a hypothetical reweighting/sampling model, not uncertainty about its arithmetic value. Scoring/annotation uncertainty is handled by audit, not hidden in the bootstrap. |
| New families under a specified authoring/sampling process, conditional on these checkpoints | A family interval may describe uncertainty under that explicit process. Sampling assumptions must be defended; a hand-selected collection does not become a probability sample because it has topic balance. |
| New authors and new families | Requires independent author replication and a sampling/cluster model covering author variation. One or two purposively chosen authors cannot support a broad author-population interval. |
| New training seeds/corpora/backbones | Not covered by a family-only interval. Report each of the three seed-pair effects and their range; keep any seed resampling a sensitivity analysis. The training corpus and backbone are also fixed unless independently replicated. |

The conditional target is a useful limited claim: performance under this trained recipe/checkpoint set and a documented held-out construction process. Independent writing supports transfer relevance but does not establish representative sampling of all Hinglish users or problems.

## Proposed analysis contract

1. Freeze one primary C rendering per family; optional variants receive fixed within-family weights. Let `d_i = mean_s(y_i,s,EC,C - y_i,s,ER,C)`, with the same three paired seeds and complete prediction vectors retained. With one rendering, `d_i` belongs to `{−1, −2/3, −1/3, 0, 1/3, 2/3, 1}`. Do not majority-vote seeds or turn `3N` results into independent families.
2. Freeze nonnegative weights `w_i` summing to one. Equal-family weighting gives `1/N`; equal-topic weighting gives `1/(H*n_h)` in topic h, with H=6. Report `estimate = sum_i w_i*d_i`, sample counts, author/lineage counts, per-seed effects, and absolute arm accuracies. Do not change weights after results.
3. Require all planned inference items to resolve. Infrastructure failures make the run incomplete; response/scoring failures remain zeros under the frozen policy. No complete-case removal and no best-attempt/seed selection.
4. For the new-family conditional claim, use 10,000 paired bootstrap resamples, analysis seed 101. Resample whole family records, carrying every arm/form/seed/variant together. For fixed equal-topic strata, draw `n_h` families with replacement within each topic and combine using frozen topic weights. Specify the software version and quantile interpolation rule in the eventual analysis manifest. The existing pilot keeps its implemented pooled-family procedure.
5. Report the 2.5% and 97.5% percentile endpoints as an **approximate 95% conditional interval**, not an exact interval. Log the number of distinct observed differences, zero-variance strata, bootstrap zero-width status, and number of independent units. Do not silently switch to BCa, studentization or another interval after seeing which gives a favorable answer.
6. Report the bounded reference interval below under its explicit independence assumptions in every eligible analysis, not only when the bootstrap looks undesirable. Prespecify which interval supports any inferential claim; never select whichever excludes zero. Until calibration and sampling design are settled, the bootstrap is a descriptive model-based uncertainty display, not a certified confirmatory procedure.
7. Keep one primary contrast. Specificity, E+E comparisons, English retention, topics and variants remain descriptive unless their hypothesis family and multiplicity rule are separately frozen. Useful-gain/retention margins remain unapproved discussion values. An interval crossing zero is inconclusive; it does not prove equality.

## Topic and author dependence

The six named topics are fixed strata, not six independent draws from a universe of topics. Resampling within topic preserves their intended mixture; it does not remove residual shared-template or shared-author effects. A known lineage group must be the independent unit before this analysis, even if it contains several IDs.

Choose one author scope before final outcomes:

- **Conditional on named authors:** fix their mix and, where the design permits, resample families within predeclared author-by-topic cells. This needs independent family construction conditional on those authors/cells. It does not generalize to new authors. Empty or one-family cells cannot supply useful within-cell variation and must be disclosed, not merged opportunistically.
- **Generalizing across authors:** resample complete author blocks, retaining all of each author's topics and family records together. Specify whether authors or families define the target weighting. Equal-author averaging changes the estimand when authors supply unequal numbers of families; ordinary resampling of author blocks followed by pooling family records produces a ratio estimator and needs its own calibration. Do not pretend either is the original fixed-weight family bootstrap.
- **Crossed/coauthored data:** where families have several authors or shared generators/editors, a simple nested author bootstrap is not automatically valid. Record that graph and plan a crossed design or restrict claims. With too few independent authors, give author-level descriptive effects and restrict the inference target; a bootstrap is not a substitute for independent authors.

Shared dependence can make ordinary standard errors too small, and cluster methods need sufficient independent clusters; large numbers of rows inside a few clusters do not solve that problem. This motivates the design choices above, rather than a claim that an off-the-shelf cluster procedure is exact here. [Cameron and Miller, 2015, §§II and VI](https://faculty.econ.ucdavis.edu/faculty/cameron/research/Cameron_Miller_JHR_2014_July_09.pdf)

## A conservative reference that does not collapse at zero variance

For independent random family summaries `D_i ∈ [−1,1]` and predetermined weights, our application of Hoeffding's bounded-sum inequality gives

`P(|sum_i w_i D_i − sum_i w_i E[D_i]| ≥ r) ≤ 2 exp(−r²/(2 sum_i w_i²))`.

Thus at alpha=.05 use `r = sqrt(2 log(40) sum_i w_i²)` and intersect `[estimate−r, estimate+r]` with `[−1,1]`. Equal-family weights give `sqrt(2 log(40)/N)`; equal-topic weights give `sum_i w_i² = sum_h 1/(H² n_h)`. This derivation requires independence and fixed weights, but not identical family distributions or nonzero observed variance. It is a finite-sample conservative bound for its stated expectation, not proof that the sample construction represents the intended population. [Hoeffding, 1963, Theorem 2, pp. 16–17](https://www.cs.rpi.edu/academics/courses/spring06/random/hoefding.pdf)

For independent author clusters with fixed cluster masses `W_g`, aggregate the weighted within-author effects to `Z_g ∈ [−1,1]`; apply the same derivation to `sum_g W_g Z_g` with `sum_g W_g²`, not `sum_i w_i²`. This covers arbitrary within-cluster dependence only under independent clusters and the fixed-weight target. It does not license treating two authors as hundreds of independent families. Resampling random cluster sizes or using data-dependent ratios requires a different derivation.

The bound is often too wide for a five-point decision; that is useful evidence about how much precision requires extra assumptions. It must not be advertised as an efficient sample-size rule. More adaptive bounds are available, but introducing them now would add implementation/calibration work without changing the next human-review gate. No source here establishes a universal safe minimum family or author count.

If all observed `d_i=0`, the empirical bootstrap is exactly `[0,0]`. Its inability to generate unobserved discordance is not proof of population equality. Keep the raw bootstrap output plus an unmistakable `degenerate` flag, a substantive warning and the conservative reference where eligible. The same issue arises if all observed differences equal a nonzero constant. Do not add jitter or call a zero-width interval perfectly precise. Near-degenerate data need the same caution even when the numerical width is nonzero.

## Why not call the sign-flip test exact?

The weak null is `sum_i w_i E[D_i]=0`. Sign flips require additional invariance for finite-sample exactness: in the i.i.d. scalar case, a zero-centered symmetric distribution suffices. For example `P(D=1)=1/4` and `P(D=−1/3)=3/4` has mean zero but is asymmetric; it is compatible with three-seed averages. Exchanging signs invents a different distribution. Paired training seeds are not randomized assignments of the training treatment independently to each held-out family.

Some sign-flip procedures can be asymptotically valid under weaker assumptions; therefore lack of symmetry does **not** imply that every such method must fail asymptotically. It does invalidate an unqualified finite-sample exactness claim. We do not need a formal p-value to answer the immediate planning question. [Ritzwoller, Romano and Shaikh, 2025, Definition 2.1, Example 2.1 and §3.2](https://home.uchicago.edu/amshaikh/webfiles/randreview.pdf)

## Model-free calibration specification

Before adopting an approximate confirmatory interval, simulate data from explicitly known family-generating processes, keeping the three checkpoints' parameters fixed in each conditional experiment. Generate paired binary arm outcomes or explicitly realizable three-seed difference vectors. Randomizing seed effects anew in each simulated dataset evaluates a different, unconditional target unless the truth is conditioned accordingly.

| Case | What it checks |
| --- | --- |
| Symmetric zero mean, moderate discordance | Baseline interval coverage and false positive exclusion of zero |
| Asymmetric zero mean: 1 with probability 1/4, −1/3 otherwise | Weak mean null differs from symmetry; sparse/discrete finite-sample behavior |
| Rare nonzero effect, e.g. 1 with probability .01, 0 otherwise | Many observed all-zero datasets despite a positive population mean; degeneracy and undercoverage |
| True point mass at 0 and at a nonzero permitted value | Arithmetic/flag behavior; distinguish genuine generator degeneracy from merely unobserved tails |
| Six fixed topics with different means, variances and unequal counts | Correct frozen weights and stratified versus pooled resampling targets |
| Strong within-author or shared-lineage dependence | Failure of naive family inference; cluster target/weighting and independent-unit counts |
| Three seeds with correlated and heterogeneous paired errors | Preservation of the whole family vector and conditional versus seed-process uncertainty |
| Positive/negative effects, floor/ceiling-compatible outcome tables | Coverage, width and sign errors without impossible probability tables |

Vary N over the pilot and plausible confirmatory budgets. Report the exact data-generating distribution and truth, simulation seed, number of Monte Carlo repetitions, bootstrap draws, coverage with Monte Carlo uncertainty, median/upper-tail width, degeneracy rate, and positive/negative false exclusions. Do not call interval exclusion probability “power” without naming the interval rule and alternative. Record coverage at null and nonzero truths; null-size checks alone do not establish interval coverage.

For estimated coverage c with M independent repetitions, `sqrt(c*(1−c)/M)` is the Monte Carlo standard-error diagnostic. Near 95% coverage, M=5,000 gives about .0031. A small exploratory run can reveal gross failures but cannot certify one-percentage-point coverage accuracy. Freeze the scenario grid and the operational acceptance criterion before comparing candidates; retain unfavorable scenarios. No finite scenario list proves uniform coverage, and simulation under independent families cannot validate actual authoring independence.

## What changed and what is still open

The earlier proposal already restricted inference to fitted checkpoints. This note makes the sampling population, author scope, weak-null distinction, degeneracy behavior and conservative reference explicit. It avoids automatically promoting a 10,000-draw bootstrap into a calibrated confirmatory test. The frozen pilot remains descriptive and unchanged.

Still pending: actual accepted families; final sampling/author design; practical effect and retention margins; annotation budget; trained-arm dependence information from permitted development work; final interval adoption and calibration; confirmatory sample/resource freeze. Versioned draft-v2 repairs are complete; the next gate remains genuine human review. AI analysis cannot supply acceptance or reviewer exposure attestations.

Search was bounded to sources that change these decisions: the author-hosted randomization review, the original bounded-sum inequality, and the author-hosted cluster-inference guide. Empirical-Bernstein and general two-sample permutation papers were screened but not adopted as extra procedures. No new novelty claim is made.

## Completed screening, separate from final calibration

The [synthetic screening run](conditional_calibration/README.md) implements 18 cases using 250 datasets per case and 10,000 bootstrap draws. It exposes rare-event degeneracy and conditional-versus-broader target differences. Random-offset conditional coverage is averaged across realizations, not guaranteed uniformly for every fixed checkpoint/author configuration. Topic-stratified and author-block procedures remain uncalibrated. The pilot software is unchanged.
