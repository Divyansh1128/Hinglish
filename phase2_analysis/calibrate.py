"""Calibration of the IMPLEMENTED Phase-2 interval and labels by simulation (Amendment 1 item 16).

Standard library only, deterministic seeds. Every simulated dataset is analysed with the
functions of ``phase2_analysis/analyze.py`` themselves: the shared ``random.Random(101)``
resampling matrix (10,000 x 100 by default), ``interval_summary`` (linear quantiles,
degeneracy, Wald, clipped Hoeffding), ``decision_label`` with the degenerate override and
``retention_flags``. Only the bootstrap sums are computed by a faster but identical route
(column counts of the same matrix); they are checked against ``analyze.resample_sums`` for
the first dataset of every scenario.

Model (conditional on fixed checkpoints, N = 100 families, S = 3 seeds). Families are drawn
independently from a population; each family's outcome vector for the fixed checkpoints is
part of the draw. For one contrast "first arm − second arm" on one form:

    b ~ Bernoulli(p0)                            LATENT second-arm family state
    e = b, except: b = 1 -> e = 0 w.p. loss;     LATENT first-arm family state (sticky family
                   b = 0 -> e = 1 w.p. gain      gains/losses, identical in all seeds)
    second arm, seed k: b XOR Bernoulli(q)       seed-level discordance q
    first arm,  seed k: e XOR Bernoulli(q)

The conditional target (the population mean of the seed-averaged family contrast d_i) is
exactly  (1 − 2q) · [(1 − p0) · gain − p0 · loss].

p0 is a LATENT accuracy, not an observed one (Sol review R10, Amendment 2 item 8). The
expected OBSERVED accuracy of the second arm (the comparator, E+R on C for the primary) is
q + (1 − 2q) · p0, and of the first arm q + (1 − 2q) · P(e = 1). So null_ceiling's latent 0.943
with q = 0.035 is an observed comparator accuracy of about 0.912; the scenario
null_ceiling_observed instead has an observed comparator accuracy of exactly 0.943, with the
latent value solved as (0.943 − q) / (1 − 2q).

Each scenario has a primary component (E+C − E+R on C) and an independent English-retention
component (E+C − E+E on E), so the retention trade-off flag is also exercised. Unfavourable
cases are kept and reported as they come out.

Usage: python3 -B -m phase2_analysis.calibrate [--datasets 1000] [--resamples 10000] [--workers 8]
Writes phase2_analysis/calibration.json and phase2_analysis/CALIBRATION.md.
"""

import argparse
import json
import multiprocessing
import os
import platform
import random
import sys
import time
from collections import Counter
from fractions import Fraction
from operator import add
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from phase2_analysis import analyze as A  # noqa: E402

CALIBRATION_VERSION = "phase2_calibration 1.1.0"
N, S = 100, 3
BASE_SEED = 20261103
OUT_DIR = Path(__file__).resolve().parent
PRIMARY_LABELS = (A.USEFUL, A.SUPPORT, A.NULL, A.HARM, A.INCONCLUSIVE, A.DEGENERATE)


def gain_for(target, p0, q, loss=0.0):
    """Sticky gain probability that gives the requested target."""
    return (target / (1 - 2 * q) + p0 * loss) / (1 - p0)


def loss_for(target, p0, q, gain=0.0):
    return ((1 - p0) * gain - target / (1 - 2 * q)) / p0


def component(p0, q, gain=0.0, loss=0.0):
    require = A.require
    require(0 <= p0 <= 1 and 0 <= q < 0.5 and 0 <= gain <= 1 and 0 <= loss <= 1, f"bad component {p0, q, gain, loss}")
    return dict(p0=p0, q=q, gain=gain, loss=loss)


def target(c):
    return (1 - 2 * c["q"]) * ((1 - c["p0"]) * c["gain"] - c["p0"] * c["loss"])


def latent_first(c):
    """P(e = 1): the latent first-arm family state."""
    return c["p0"] * (1 - c["loss"]) + (1 - c["p0"]) * c["gain"]


def observed_accuracy(c, arm="second"):
    """Expected observed per-seed accuracy of one arm: q + (1 − 2q) · latent state."""
    latent = c["p0"] if arm == "second" else latent_first(c)
    return c["q"] + (1 - 2 * c["q"]) * latent


def latent_for_observed(observed, q):
    """The latent p0 whose observed second-arm accuracy is `observed` at seed discordance q."""
    return (observed - q) / (1 - 2 * q)


# Typical retention component (no true effect) and the +5 pp primary used with retention cases.
RET_NULL = component(0.9, 0.035)
PRI_PLUS5 = component(0.7, 0.05, gain_for(0.05, 0.7, 0.05))

OBSERVED_CEILING = 0.943  # Pilot-B Qwen3-4B C, 66/70 (PREREGISTRATION §9)
CEILING_LATENT = latent_for_observed(OBSERVED_CEILING, 0.035)

SCENARIOS = [
    # name, group, description, primary component, retention component
    # p0 is the latent second-arm state; observed accuracies are q + (1 − 2q) · latent (see the docstring).
    ("null_typical", "null", "Δ_C = 0; latent C state 0.60, seed discordance q 0.05 (observed E+R C accuracy 0.59)",
     component(0.6, 0.05), RET_NULL),
    ("null_ceiling", "null", "Δ_C = 0 at a LATENT C state of 0.943 with q 0.035; the observed E+R C accuracy is "
     "q + (1 − 2q) · 0.943 ≈ 0.912, not 0.943",
     component(0.943, 0.035), RET_NULL),
    ("null_asymmetric_churn", "asymmetric", "Δ_C = 0 from offsetting sticky gains (0.15) and losses (0.10); latent C state 0.60",
     component(0.6, 0.05, 0.15, 0.10), RET_NULL),
    ("plus3_with_losses", "asymmetric", "Δ_C = +3 pp: sticky gains with 5% sticky losses (latent C state 0.70)",
     component(0.7, 0.05, gain_for(0.03, 0.7, 0.05, 0.05), 0.05), RET_NULL),
    ("minus3_losses_only", "asymmetric", "Δ_C = −3 pp from sticky losses only (latent C state 0.70)",
     component(0.7, 0.05, 0.0, loss_for(-0.03, 0.7, 0.05)), RET_NULL),
    ("sparse_zero", "sparse/degenerate", "Δ_C = 0 with no discordance at all (every family contrast 0)",
     component(0.9, 0.0), RET_NULL),
    ("sparse_one_family", "sparse/degenerate", "Δ_C = +1 pp: one expected discordant family (P(d_i = +1) = .01, q 0)",
     component(0.9, 0.0, 0.1), RET_NULL),
    ("sparse_two_families", "sparse/degenerate", "Δ_C = +2 pp: two expected discordant families (P(d_i = +1) = .02, q 0)",
     component(0.9, 0.0, 0.2), RET_NULL),
    ("boundary_plus5", "margin boundary", "Δ_C = +5 pp exactly (useful-support boundary), gains only",
     PRI_PLUS5, RET_NULL),
    ("boundary_plus5_with_losses", "margin boundary", "Δ_C = +5 pp exactly with 5% sticky losses",
     component(0.7, 0.05, gain_for(0.05, 0.7, 0.05, 0.05), 0.05), RET_NULL),
    ("ceiling_plus3", "ceiling", "Δ_C = +3 pp at a latent E+R C state of 0.943, q 0.035 (observed E+R C accuracy ≈ 0.912)",
     component(0.943, 0.035, gain_for(0.03, 0.943, 0.035)), RET_NULL),
    ("ceiling_plus5", "ceiling", "Δ_C = +5 pp at a latent E+R C state of 0.943, q 0.035 (observed E+R C accuracy ≈ 0.912)",
     component(0.943, 0.035, gain_for(0.05, 0.943, 0.035)), RET_NULL),
    ("retention_boundary_minus2", "margin boundary", "Retention = −2 pp exactly (latent E+E E state 0.90, q 0.035); Δ_C = +5",
     PRI_PLUS5, component(0.9, 0.035, 0.0, loss_for(-0.02, 0.9, 0.035))),
    ("retention_boundary_minus2_sparse", "sparse/degenerate",
     "Retention = −2 pp exactly from two expected lost families (P(d_i = −1) = .02, q 0); Δ_C = +5",
     PRI_PLUS5, component(0.9, 0.0, 0.0, loss_for(-0.02, 0.9, 0.0))),
    ("retention_zero_sparse", "sparse/degenerate", "Retention = 0 with no English discordance (always degenerate); Δ_C = +5",
     PRI_PLUS5, component(0.9, 0.0)),
    ("retention_minus4", "asymmetric", "Retention = −4 pp (latent E+E E state 0.90, q 0.035); Δ_C = +5 (trade-off case)",
     PRI_PLUS5, component(0.9, 0.035, 0.0, loss_for(-0.04, 0.9, 0.035))),
    # Added under Amendment 2 item 8 (Sol review R10), appended so every earlier scenario keeps its seed.
    ("null_ceiling_observed", "null",
     f"Δ_C = 0 at an OBSERVED E+R C accuracy of {OBSERVED_CEILING} (q 0.035; latent C state solved as "
     f"(0.943 − q)/(1 − 2q) = {CEILING_LATENT:.4f})",
     component(CEILING_LATENT, 0.035), RET_NULL),
]


def draw_numerators(rng, c, n=N, seeds=S):
    """Family numerators n_i = Σ_k first_k − Σ_k second_k (d_i = n_i / S), one per family."""
    out = []
    for _ in range(n):
        b = rng.random() < c["p0"]
        e = b
        if b and c["loss"] and rng.random() < c["loss"]:
            e = False
        elif not b and c["gain"] and rng.random() < c["gain"]:
            e = True
        first = sum((e != (rng.random() < c["q"])) for _ in range(seeds))
        second = sum((b != (rng.random() < c["q"])) for _ in range(seeds))
        out.append(first - second)
    return out


def column_counts(indices, n=N):
    """cols[i][r] = number of times family i is drawn in matrix row r."""
    cols = [[0] * len(indices) for _ in range(n)]
    for r, row in enumerate(indices):
        for i in row:
            cols[i][r] += 1
    return cols


def fast_sums(numerators, cols):
    """Equal to analyze.resample_sums(numerators, indices), computed from column counts."""
    R = len(cols[0])
    groups = {}
    for i, v in enumerate(numerators):
        if v:
            groups[v] = list(map(add, groups[v], cols[i])) if v in groups else cols[i]
    sums = [0] * R
    for v, counts in groups.items():
        sums = list(map(add, sums, [v * c for c in counts])) if v != 1 else list(map(add, sums, counts))
    return sums


def _empty_tally():
    return dict(datasets=0, covered=0, miss_low=0, miss_high=0, wald_covered=0, hoeffding_covered=0, degenerate=0,
                all_identical=0, zero_width=0, nonzero_total=0, halfwidth_pp=[], labels=Counter(), raw_labels=Counter(),
                flags=Counter())


def _raw_label(lower, upper):
    """The section 8 table without the degenerate override (for comparison only)."""
    L, U = lower / A.PP, upper / A.PP
    if L > 5:
        return A.USEFUL
    if 0 < L <= 5:
        return A.SUPPORT
    if U < 0:
        return A.HARM
    if L <= 0 and U >= 5:
        return A.INCONCLUSIVE
    return A.NULL


def _record(tally, summary, true_value):
    tally["datasets"] += 1
    t = Fraction(true_value).limit_denominator(10 ** 6)
    covered = summary["lower"] <= t <= summary["upper"]
    tally["covered"] += covered
    tally["miss_low"] += summary["upper"] < t  # interval entirely below the target
    tally["miss_high"] += summary["lower"] > t
    w = summary["wald_95_pp"]
    h = summary["hoeffding_95_pp"]
    tally["wald_covered"] += w[0] <= 100 * true_value <= w[1]
    tally["hoeffding_covered"] += h[0] <= 100 * true_value <= h[1]
    tally["degenerate"] += summary["degenerate"]
    tally["all_identical"] += summary["all_contrasts_identical"]
    tally["zero_width"] += summary["zero_width"]
    tally["nonzero_total"] += summary["nonzero_family_contrasts"]
    tally["halfwidth_pp"].append((summary["bootstrap_95_pp"][1] - summary["bootstrap_95_pp"][0]) / 2)


def run_scenario(args):
    """Simulate one scenario; returns a JSON-ready dict."""
    index, datasets, resamples = args
    name, group, description, primary, retention = SCENARIOS[index]
    rng = random.Random(BASE_SEED + index)
    indices = A.bootstrap_indices(N, resamples=resamples)
    cols = column_counts(indices)
    pri, ret = _empty_tally(), _empty_tally()
    t_pri, t_ret = target(primary), target(retention)
    checked = False
    for _ in range(datasets):
        n_pri = draw_numerators(rng, primary)
        n_ret = draw_numerators(rng, retention)
        sums_pri, sums_ret = fast_sums(n_pri, cols), fast_sums(n_ret, cols)
        if not checked:  # identical to the implemented resampling
            A.require(sums_pri == A.resample_sums(n_pri, indices) and sums_ret == A.resample_sums(n_ret, indices),
                      "fast bootstrap sums differ from analyze.resample_sums")
            checked = True
        s_pri = A.interval_summary(n_pri, S, indices, A.DIFFERENCE_BOUNDS, (0, 5), sums=sums_pri)
        s_ret = A.interval_summary(n_ret, S, indices, A.DIFFERENCE_BOUNDS, (0, -2), sums=sums_ret)
        label = A.decision_label(s_pri["lower"], s_pri["upper"], s_pri["degenerate"])
        flags = A.retention_flags(s_ret["lower"], s_ret["upper"], s_ret["degenerate"], label, True)
        _record(pri, s_pri, t_pri)
        _record(ret, s_ret, t_ret)
        pri["labels"][label] += 1
        pri["raw_labels"][_raw_label(s_pri["lower"], s_pri["upper"])] += 1
        for f in flags["flags"]:
            ret["flags"][f] += 1
    return dict(name=name, group=group, description=description, seed=BASE_SEED + index,
                primary=_summarise(pri, primary, t_pri), retention=_summarise(ret, retention, t_ret))


def _summarise(tally, comp, true_value):
    M = tally["datasets"]
    widths = sorted(tally["halfwidth_pp"])
    out = dict(component=comp, target_pp=100 * true_value, datasets=M,
               latent_second_arm_state=comp["p0"], latent_first_arm_state=latent_first(comp),
               observed_second_arm_accuracy=observed_accuracy(comp, "second"),
               observed_first_arm_accuracy=observed_accuracy(comp, "first"),
               coverage=tally["covered"] / M, interval_below_target=tally["miss_low"] / M,
               interval_above_target=tally["miss_high"] / M,
               wald_coverage=tally["wald_covered"] / M, hoeffding_coverage=tally["hoeffding_covered"] / M,
               degenerate_rate=tally["degenerate"] / M, all_contrasts_identical_rate=tally["all_identical"] / M,
               zero_width_rate=tally["zero_width"] / M, mean_nonzero_family_contrasts=tally["nonzero_total"] / M,
               median_halfwidth_pp=widths[M // 2], halfwidth_pp_range=[widths[0], widths[-1]])
    if tally["labels"]:
        out["labels"] = {k: tally["labels"][k] / M for k in PRIMARY_LABELS}
        out["labels_without_degenerate_override"] = {k: tally["raw_labels"][k] / M for k in PRIMARY_LABELS[:-1]}
    if tally["flags"]:
        out["flags"] = {k: tally["flags"][k] / M for k in (A.WITHIN, A.LOSS, A.BEYOND, A.TRADE_OFF, A.NOT_ESTABLISHED,
                                                          A.DEGENERATE)}
    return out


def simulate(datasets=1000, resamples=A.RESAMPLES, workers=None):
    jobs = [(i, datasets, resamples) for i in range(len(SCENARIOS))]
    workers = workers or min(len(jobs), os.cpu_count() or 1)
    if workers > 1:
        with multiprocessing.get_context("spawn").Pool(workers) as pool:
            return pool.map(run_scenario, jobs)
    return [run_scenario(job) for job in jobs]


def headline(results):
    by = {r["name"]: r for r in results}
    null_names = ("null_typical", "null_ceiling", "null_ceiling_observed", "null_asymmetric_churn", "sparse_zero")
    nulls = [by[n]["primary"] for n in null_names]
    support = lambda p: p["labels"][A.SUPPORT] + p["labels"][A.USEFUL]
    covs = [r["primary"]["coverage"] for r in results] + [r["retention"]["coverage"] for r in results]
    return dict(
        null_false_support_rate={n: support(by[n]["primary"]) for n in null_names},
        max_null_false_support_rate=max(support(p) for p in nulls),
        primary_coverage={r["name"]: r["primary"]["coverage"] for r in results},
        retention_coverage={r["name"]: r["retention"]["coverage"] for r in results},
        coverage_range=[min(covs), max(covs)],
        useful_support_at_plus5={n: by[n]["primary"]["labels"][A.USEFUL]
                                 for n in ("boundary_plus5", "boundary_plus5_with_losses", "ceiling_plus5")},
        within_margin_at_minus2={n: by[n]["retention"]["flags"][A.WITHIN]
                                 for n in ("retention_boundary_minus2", "retention_boundary_minus2_sparse")},
        degenerate={n: dict(primary_degenerate=by[n]["primary"]["degenerate_rate"],
                            primary_coverage=by[n]["primary"]["coverage"],
                            primary_labels=by[n]["primary"]["labels"],
                            retention_degenerate=by[n]["retention"]["degenerate_rate"],
                            retention_coverage=by[n]["retention"]["coverage"])
                    for n in ("sparse_zero", "sparse_one_family", "sparse_two_families",
                              "retention_boundary_minus2_sparse", "retention_zero_sparse")})


def _pct(x):
    return f"{100 * x:.1f}%"


def markdown(report):
    s = report["settings"]
    lines = ["# Phase-2 interval calibration (Amendment 1 item 16; Amendment 2 item 8)", "",
             f"`{report['version']}`, generated by `phase2_analysis/calibrate.py` (standard library, deterministic seeds "
             f"{BASE_SEED} + scenario index). Python {s['python_version']}. Analysis code `phase2_analysis/analyze.py` "
             f"SHA-256 `{report['analyze_sha256']}`.", "",
             f"Each scenario: {s['datasets']:,} simulated FINAL_TEST datasets, N = {N} families, S = {S} seeds, "
             f"analysed with the implemented procedure: the shared `random.Random(101)` matrix "
             f"({s['resamples']:,} x {N}{'' if s['resamples'] == A.RESAMPLES else ', i.e. the first rows of the real 10,000 x 100 matrix; fewer resamples than the real analysis'}), "
             "linear quantiles h = (R − 1)p, the degenerate-interval override, the section 8 label table and the "
             "Amendment 1 retention flags. Monte Carlo SE of a rate near 95% is about "
             f"{100 * (0.95 * 0.05 / s['datasets']) ** 0.5:.1f} pp; near 2.5% about {100 * (0.025 * 0.975 / s['datasets']) ** 0.5:.1f} pp.",
             "", "Target: the conditional population mean of the seed-averaged family contrast (fixed checkpoints, "
             "independent families); see the module docstring for the generating model. Coverage counts L ≤ target ≤ U "
             "with closed bounds. Unfavourable cases are kept.", "",
             "Scenario p0 values are LATENT family states; the expected observed accuracy of an arm is "
             "q + (1 − 2q) · latent state (Amendment 2 item 8, Sol review R10). The archived null_ceiling scenario "
             "therefore has an observed comparator accuracy of about 0.912; null_ceiling_observed, added before any "
             "Phase-2 output, has an observed comparator accuracy of 0.943.", ""]
    h = report["headline"]
    lines += ["## Headline", "",
              f"- **Null false-support rate** (Support or Useful support when Δ_C = 0): "
              + "; ".join(f"{k} {_pct(v)}" for k, v in h["null_false_support_rate"].items())
              + f" (max {_pct(h['max_null_false_support_rate'])}).",
              f"- **Coverage of the conditional target** across all scenario components: "
              f"{_pct(h['coverage_range'][0])}–{_pct(h['coverage_range'][1])}.",
              "- **Useful support at true Δ_C = +5 pp**: " + "; ".join(f"{k} {_pct(v)}" for k, v in h["useful_support_at_plus5"].items()) + ".",
              "- **Within-margin criterion met at true retention = −2 pp** (false 'within margin'): "
              + "; ".join(f"{k} {_pct(v)}" for k, v in h["within_margin_at_minus2"].items()) + ".",
              "- **Degenerate cases**: " + "; ".join(
                  f"{k}: primary degenerate {_pct(v['primary_degenerate'])}, coverage {_pct(v['primary_coverage'])}; "
                  f"retention degenerate {_pct(v['retention_degenerate'])}, coverage {_pct(v['retention_coverage'])}"
                  for k, v in h["degenerate"].items()) + ".", ""]
    lines += ["## Primary Δ_C (E+C − E+R on C)", "",
              "| Scenario | Target (pp) | Coverage | Below / above | Wald | Hoeffding | Degenerate | Non-zero fam. | Median half-width | "
              + " | ".join(PRIMARY_LABELS) + " |", "|---|---:|---:|---|---:|---:|---:|---:|---:|" + "---:|" * len(PRIMARY_LABELS)]
    for r in report["scenarios"]:
        p = r["primary"]
        lines.append(f"| {r['name']} | {p['target_pp']:+.2f} | {_pct(p['coverage'])} | {_pct(p['interval_below_target'])} / "
                     f"{_pct(p['interval_above_target'])} | {_pct(p['wald_coverage'])} | {_pct(p['hoeffding_coverage'])} | "
                     f"{_pct(p['degenerate_rate'])} | {p['mean_nonzero_family_contrasts']:.1f} | {p['median_halfwidth_pp']:.2f} | "
                     + " | ".join(_pct(p["labels"][k]) for k in PRIMARY_LABELS) + " |")
    lines += ["", "Without the degenerate override the same intervals would have been labelled (for comparison only):", "",
              "| Scenario | " + " | ".join(PRIMARY_LABELS[:-1]) + " |", "|---|" + "---:|" * (len(PRIMARY_LABELS) - 1)]
    for r in report["scenarios"]:
        p = r["primary"]["labels_without_degenerate_override"]
        lines.append(f"| {r['name']} | " + " | ".join(_pct(p[k]) for k in PRIMARY_LABELS[:-1]) + " |")
    flag_names = (A.WITHIN, A.LOSS, A.BEYOND, A.TRADE_OFF, A.NOT_ESTABLISHED, A.DEGENERATE)
    lines += ["", "## English retention (E+C − E+E on E; trade-off uses the simulated primary label)", "",
              "| Scenario | Target (pp) | Coverage | Below / above | Degenerate | Non-zero fam. | Median half-width | "
              + " | ".join(flag_names) + " |", "|---|---:|---:|---|---:|---:|---:|" + "---:|" * len(flag_names)]
    for r in report["scenarios"]:
        p = r["retention"]
        lines.append(f"| {r['name']} | {p['target_pp']:+.2f} | {_pct(p['coverage'])} | {_pct(p['interval_below_target'])} / "
                     f"{_pct(p['interval_above_target'])} | {_pct(p['degenerate_rate'])} | {p['mean_nonzero_family_contrasts']:.1f} | "
                     f"{p['median_halfwidth_pp']:.2f} | " + " | ".join(_pct(p["flags"][k]) for k in flag_names) + " |")
    lines += ["", "## Scenarios", "",
              "p0 is the latent second-arm family state. Observed accuracies are the expected per-seed accuracies "
              "q + (1 − 2q) · latent state (second arm = comparator: E+R for Δ_C, E+E for retention).", "",
              "| Scenario | Group | Description | Primary (p0, q, gain, loss) | Primary observed comparator / first arm | "
              "Retention (p0, q, gain, loss) | Retention observed comparator / first arm |",
              "|---|---|---|---|---:|---|---:|"]
    for r in report["scenarios"]:
        fmt = lambda c: ", ".join(f"{c[k]:.4g}" for k in ("p0", "q", "gain", "loss"))
        obs = lambda p: f"{p['observed_second_arm_accuracy']:.4f} / {p['observed_first_arm_accuracy']:.4f}"
        lines.append(f"| {r['name']} | {r['group']} | {r['description']} | {fmt(r['primary']['component'])} | "
                     f"{obs(r['primary'])} | {fmt(r['retention']['component'])} | {obs(r['retention'])} |")
    lines += ["", "## Reading", "", *report["reading"], ""]
    return "\n".join(lines) + "\n"


def reading(results):
    """Plain statements derived from the numbers (no selection of favourable cases)."""
    by = {r["name"]: r for r in results}
    out = []
    low = [(r["name"], part, r[part]["coverage"]) for r in results for part in ("primary", "retention")
           if r[part]["coverage"] < 0.93]
    if low:
        out.append("- Coverage below 93% (unfavourable; kept): " + "; ".join(f"{n} {p} {_pct(c)}" for n, p, c in low) + ".")
    else:
        out.append("- No scenario component had coverage below 93%.")
    for n in ("sparse_one_family", "sparse_two_families"):
        p = by[n]["primary"]
        out.append(f"- {n}: the interval is degenerate in {_pct(p['degenerate_rate'])} of datasets and covers the "
                   f"positive target in {_pct(p['coverage'])}; with the override these become "
                   f"'{A.DEGENERATE}' instead of 'Informative null' "
                   f"(Informative null {_pct(p['labels'][A.NULL])} with override vs "
                   f"{_pct(p['labels_without_degenerate_override'][A.NULL])} without).")
    r = by["retention_boundary_minus2_sparse"]["retention"]
    out.append(f"- retention_boundary_minus2_sparse: degenerate {_pct(r['degenerate_rate'])}; the override keeps the "
               f"false 'within-margin criterion met' rate at {_pct(r['flags'][A.WITHIN])}.")
    nc, nco = by["null_ceiling"]["primary"], by["null_ceiling_observed"]["primary"]
    out.append(f"- Latent vs observed: null_ceiling has latent C state {nc['latent_second_arm_state']:.3f}, i.e. an "
               f"observed E+R C accuracy of {nc['observed_second_arm_accuracy']:.4f}; null_ceiling_observed has an "
               f"observed E+R C accuracy of {nco['observed_second_arm_accuracy']:.4f} (latent "
               f"{nco['latent_second_arm_state']:.4f}): coverage {_pct(nco['coverage'])}, false support "
               f"{_pct(nco['labels'][A.SUPPORT] + nco['labels'][A.USEFUL])}, median half-width "
               f"{nco['median_halfwidth_pp']:.2f} pp, degenerate {_pct(nco['degenerate_rate'])}.")
    out.append("- 'Within-margin criterion met' is a descriptive interval criterion, not multiplicity-controlled "
               "non-inferiority; 'Informative null' rules out ≥ 5 pp gains under this sampling model only.")
    return out


def main(argv=None):
    parser = argparse.ArgumentParser(description="Calibrate the implemented Phase-2 interval and labels by simulation.")
    parser.add_argument("--datasets", type=int, default=1000, help="simulated datasets per scenario")
    parser.add_argument("--resamples", type=int, default=A.RESAMPLES, help="bootstrap rows used (first rows of the matrix)")
    parser.add_argument("--workers", type=int, default=0, help="processes (default: one per scenario up to CPU count)")
    parser.add_argument("--out-dir", default=str(OUT_DIR))
    args = parser.parse_args(argv)
    A.require(args.datasets >= 1 and 1 <= args.resamples <= A.RESAMPLES, "bad settings")
    started = time.time()
    results = simulate(args.datasets, args.resamples, args.workers or None)
    report = dict(version=CALIBRATION_VERSION,
                  analyze_sha256=A.sha256((ROOT / "phase2_analysis" / "analyze.py").read_bytes()),
                  settings=dict(N=N, S=S, datasets=args.datasets, resamples=args.resamples, base_seed=BASE_SEED,
                                bootstrap_seed=A.BOOTSTRAP_SEED, python_version=platform.python_version(),
                                matrix_sha256_full=A.FINAL_TEST_MATRIX_SHA256),
                  headline=headline(results), scenarios=results, reading=reading(results))
    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / "calibration.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (out / "CALIBRATION.md").write_text(markdown(report), encoding="utf-8")
    print(f"calibration written to {out} in {time.time() - started:.0f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
