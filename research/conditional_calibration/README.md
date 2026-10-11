# Synthetic interval stress tests — 11 October 2026

**MODEL-FREE DESIGN CHECKS. These are not model accuracy, pilot outcomes or a training benefit.** No project questions, generations or human submissions are read. The unchanged pilot implementation is not modified.

## Decision from this screening

Keep a limited, checkpoint-conditional interpretation of the eventual paired-family interval. Do not treat a 95% percentile bootstrap label as guaranteed 95% coverage. These cases expose both sparse-data failure and the difference between new-family uncertainty and new-seed/new-author uncertainty. They do not certify a final confirmatory method; author/topic sampling and fuller calibration remain pending.

The [analysis contract](../conditional_inference_2026-10-11.md) explains the inferential targets and the conservative bounded reference. The [sampling plan](../sampling_and_annotation_plan_2026-10-11.md) explains practical author and annotation choices.

## Reproduce

Use Python with NumPy 1.26.4. The saved run used existing Python 3.12.7 / NumPy 1.26.4, with no installation or GPU:

```sh
python research/conditional_calibration/calibrate.py
```

On the project Mac, the existing interpreter is `/opt/anaconda3/bin/python`. This absolute path is not required elsewhere. A rerun replaces only this directory's generated CSV and manifest. Code, output SHA-256, actual versions, seeds, UTC time and limitations are recorded in `manifest.json`; CSV uses LF bytes for Git portability. The run took about 22 seconds.

There are 18 cells: six synthetic processes × N=30/120/300 families, S=3 paired seed differences. Each cell contains 250 simulated datasets and 10,000 bootstrap resamples per dataset: 4,500 synthetic datasets and 45 million bootstrap draws. This is a bounded screening grid. At 95% coverage, 250 repetitions have roughly 1.4 percentage points of Monte Carlo standard error; this is not enough to certify one-point coverage accuracy. Wilson intervals quantify Monte Carlo uncertainty, including at 0/1 rates. They are not Wilson intervals for seed-averaged research accuracy.

## Exact synthetic processes

Each entry `D_is` is in {-1,0,1} and can be realized as the difference of two binary correctness outcomes. We simulate the primary contrast only, not a full three-arm empirical dataset. Concordant both-correct versus both-wrong allocation has no effect on this difference; no baseline accuracy is inferred.

- **symmetric_null:** discordance q=.20, mean difference zero for all seeds.
- **correlated_gain:** q=.20, mean difference .05 for all seeds.
- **asymmetric_null:** a family vector is (1,1,1) with probability 1/4; otherwise it has one randomly chosen −1 and two zeros. Its seed-average is 1 or −1/3, with mean exactly zero but no sign symmetry.
- **rare_gain:** all seeds share a family Bernoulli(.003) difference. True mean is .003, a hypothetical 0.3-point effect. An all-zero observed sample is common; it does not establish zero population effect.
- **random_seeds:** baseline mean .05; each of three seeds receives an independent ±.08 offset, drawn once per dataset. Its conditional target is .05 plus the realized mean offset; the broader new-seed target is .05.
- **random_authors:** baseline mean .05; three equally represented authors receive independent ±.08 offsets, drawn once per dataset. Its conditional target is .05 plus the realized mean author offset; the broader new-author target is .05.

For the q=.20 cases, `p_plus=(q+delta_is)/2`, `p_minus=(q-delta_is)/2`; the remainder is zero. A uniform draw selects the category. Seventy percent of families share that uniform across seeds; the others use independent uniforms. Rows are independent conditional on realized author/seed offsets. This gives within-family dependence without inventing extra independent sample units.

Data seed is 20261011 and bootstrap seed is 101, with NumPy SeedSequence([master, case index, N]) and sequential replicates. All assumptions were chosen as stress cases, not estimated from project data.

## Interval calculation and targets

Average the three differences within each family, then average families equally. Resample whole family summaries. For this unweighted scalar mean, multinomial resampling of the histogram of row sums is exactly the same bootstrap distribution as resampling rows; it avoids allocating huge prediction arrays. This shortcut is not an implementation for joint multivariate, stratified or author-block analysis. Use NumPy's linear interpolation for the 2.5% and 97.5% percentiles.

Also calculate the prespecified independent-family bounded reference with radius `sqrt(2 log(40)/N)`, clipped to [-1,1]. It has a conservative guarantee only for the independent bounded-family conditional expectation under the stated assumptions. Its broad-target column is deliberately a misspecification diagnostic, not a guarantee for new seeds/authors. It is very wide; do not choose it or the bootstrap after observing which is favorable.

For random-offset cases, reported conditional-target coverage is **averaged over newly realized offsets**. It is not repeated coverage at one fixed checkpoint/author configuration or a uniform conditional-coverage guarantee. Pooled family resampling in the author case includes between-fixed-author mean variation; it is not the proposed stratified fixed-author bootstrap and can be conservative for that conditional target. No author-block method is calibrated here.

## Selected results

Coverage below means the fraction of synthetic intervals containing the known generating mean. It is not accuracy or the probability that a particular interval contains its parameter.

| Synthetic case | N | Coverage of conditional target | Coverage of broader target | Zero-width rate |
| --- | ---: | ---: | ---: | ---: |
| Symmetric null | 30 | 91.2% | 91.2% | 0% |
| Symmetric null | 300 | 97.2% | 97.2% | 0% |
| Correlated five-point gain | 300 | 94.8% | 94.8% | 0% |
| Asymmetric zero-mean null | 300 | 93.6% | 93.6% | 0% |
| Rare 0.3-point gain | 30 | 6.8% | 6.8% | 93.2% |
| Rare 0.3-point gain | 300 | 59.6% | 59.6% | 40.0% |
| Random seed offsets | 300 | 95.2% | 55.2% | 0% |
| Random author offsets | 300 | 97.6% | 65.2% | 0% |

For example, the Monte Carlo Wilson interval for the seed-offset conditional coverage is approximately 91.8–97.2%. The rare-case N=30 coverage interval is approximately 4.3–10.6%; its failure is much larger than simulation noise. The N=30 symmetric-null interval is approximately 87.0–94.1%, another reason not to assume nominal coverage in small samples. See the full CSV for all cells, Monte Carlo uncertainty, widths and positive/negative exclusion rates. Exclusion rates are properties of this interval rule under each stated generator, not general power estimates for the eventual study.

The rare case has expected all-zero probability `(1-.003)^N`. The bootstrap cannot recover a missing tail from an all-zero empirical distribution. Its unmodified output must retain a degeneracy flag; zero-width must never be reported as perfect precision or equivalence. [SciPy's bootstrap documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.bootstrap.html) likewise warns about degenerate resampling; changing to BCa is not an automatic cure.

## Verification and remaining scope

Five validation categories passed: valid binary-realizable differences; degenerate sample behavior; an exact asymmetric zero-mean construction; histogram resampling versus enumeration and theoretical moment identities; weight/shape guards and bounded/Monte Carlo interval boundaries. A separate AI code audit checked generator means, conditioning and resampling semantics. Source/output hashes and LF serialization are independently checked at publication.

Not covered: topic-stratified or author-stratified/cluster bootstrap calibration, broad non-i.i.d. constructions, all possible effect distributions, formal p-values, negative nonzero effect grid, actual training randomness, real sampling independence or a final operational acceptance threshold. The grid is useful failure diagnosis, not a universal method certificate. Any later expanded calibration should be a versioned design change, with unfavorable cases retained.
