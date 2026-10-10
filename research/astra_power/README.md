# Model-free sample-size planning

**PLANNING ONLY. These are synthetic assumptions, not pilot/model results.**

From the project root:

```sh
python3 research/astra_power/paired_planning.py
```

Requires Python 3.10+ and only its standard library. Runtime on the available Mac was approximately four seconds. The script reads no dataset, reviewer submissions or generations and uses no GPU/network/API. A rerun replaces only its generated planning tables/manifest in this directory.

- `paired_power_scenarios.csv`: 45 scenarios for a **single fixed checkpoint pair**, one binary result per independent family, exact two-sided conditional-binomial McNemar testing at alpha .05. Contains any-direction and positive-direction rejection probabilities; use the positive-direction field for beneficial-effect detection. Baseline .55, gains .03/.05/.10 and discordance .10/.20/.40 are assumptions.
- `crossed_variance_scenarios.csv`: 72 algebraic dependence sensitivities, not calibrated confidence intervals or a binary correctness simulator. Shows why family-by-seed observations cannot be treated as independent.
- `planning_manifest.json`: UTC timestamp, Python version, code/output SHA-256, seven passed check categories, seeded Monte Carlo sanity results.
- `paired_planning.py`: maintained source and embedded checks. Monte Carlo sanity seed is 20261010; exact finite power summation has no random seed.

The approximate 80%-power N column is a large-sample screening calculation, **not** an exact minimum, approved final sample or power for the seed-averaged confirmatory analysis. Final size requires a frozen estimand/test, practical margin, population and resource plan. Variant counts and repeated seeds do not increase independent family count. Consult [the full validity/planning note](../astra_validity_and_power_v1.md) for the formulas, assumptions, limitations and sources.
