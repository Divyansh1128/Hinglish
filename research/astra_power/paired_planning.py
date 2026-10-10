"""MODEL-FREE PLANNING ONLY. No project generations or pilot scores are read.

Run with Python >=3.10: python3 research/astra_power/paired_planning.py
Exact power means finite probability summation (floating-point arithmetic),
not a claim that the hypothetical population parameters describe the project.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import random
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from statistics import NormalDist

SEED = 20261010
ALPHA = 0.05
SAMPLE_SIZES = (30, 100, 300, 600, 1000)
BASELINE = 0.55  # ASSUMPTION, NOT AN OBSERVED ACCURACY


def binomial_pmf(n: int, p: float) -> list[float]:
    """Normalized recurrence starting at the mode avoids tail underflow."""
    if not isinstance(n, int) or n < 0 or not 0 <= p <= 1:
        raise ValueError("Require integer n>=0 and probability p in [0,1]")
    probs = [0.0] * (n + 1)
    if p in (0, 1):
        probs[0 if p == 0 else n] = 1.0
        return probs
    mode = min(n, math.floor((n + 1) * p))
    probs[mode] = 1.0
    for k in range(mode + 1, n + 1):
        probs[k] = probs[k - 1] * (n - k + 1) / k * p / (1 - p)
    for k in range(mode - 1, -1, -1):
        probs[k] = probs[k + 1] * (k + 1) / (n - k) * (1 - p) / p
    total = math.fsum(probs)
    return [x / total for x in probs]


def paired_probabilities(baseline: float, delta: float, discordance: float) -> dict:
    """A=E+C; B=E+R. D=A_correct-B_correct."""
    if not 0 <= baseline <= 1 or not 0 <= discordance <= 1:
        raise ValueError("Invalid baseline/discordance")
    if abs(delta) > discordance:
        raise ValueError("|delta| cannot exceed discordance")
    plus = (discordance + delta) / 2
    minus = (discordance - delta) / 2
    result = {
        "A_only_correct": plus,
        "B_only_correct": minus,
        "both_correct": baseline - minus,
        "both_wrong": 1 - baseline - plus,
    }
    if min(result.values()) < -1e-12 or max(result.values()) > 1 + 1e-12:
        raise ValueError("Baseline, delta and discordance imply an impossible paired table")
    return {k: max(0.0, v) for k, v in result.items()}


@lru_cache(maxsize=None)
def critical_tail(m: int, alpha: float = ALPHA) -> int:
    """Largest k < m/2 with 2*P[Bin(m,.5)<=k] <= alpha; -1=no rejection."""
    null = binomial_pmf(m, 0.5)
    cumulative = 0.0
    critical = -1
    for k in range((m + 1) // 2):
        cumulative += null[k]
        if 2 * cumulative <= alpha + 1e-14:
            critical = k
        else:
            break
    return critical


@lru_cache(maxsize=None)
def conditional_rejection(m: int, theta: float, alpha: float = ALPHA) -> tuple[float, float]:
    k = critical_tail(m, alpha)
    if k == -1:
        return 0.0, 0.0
    probs = binomial_pmf(m, theta)
    low = math.fsum(probs[:k + 1])
    high = math.fsum(probs[m - k:])
    return low + high, high


def exact_power(n: int, delta: float, discordance: float, alpha: float = ALPHA) -> dict:
    if not isinstance(n, int) or n < 0 or not 0 <= discordance <= 1 or abs(delta) > discordance:
        raise ValueError("Invalid paired-power inputs")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be in (0,1)")
    if discordance == 0:
        return {"power_two_sided_any_direction": 0.0, "power_positive_direction": 0.0}
    theta = (discordance + delta) / (2 * discordance)
    m_probs = binomial_pmf(n, discordance)
    any_direction = []
    positive = []
    for m, weight in enumerate(m_probs):
        reject, reject_positive = conditional_rejection(m, theta, alpha)
        any_direction.append(weight * reject)
        positive.append(weight * reject_positive)
    return {
        "power_two_sided_any_direction": math.fsum(any_direction),
        "power_positive_direction": math.fsum(positive),
    }


def approximate_n80(delta: float, discordance: float) -> int:
    """Large-sample paired-McNemar planning approximation, NOT exact minimum N."""
    if delta <= 0 or delta > discordance:
        raise ValueError("Require 0<delta<=discordance")
    z_alpha = NormalDist().inv_cdf(1 - ALPHA / 2)
    z_power = NormalDist().inv_cdf(0.8)
    return math.ceil((z_alpha * math.sqrt(discordance)
                      + z_power * math.sqrt(discordance - delta ** 2)) ** 2 / delta ** 2)


def crossed_variance(n: int, seeds: int, variance_family: float,
                     variance_seed: float, variance_interaction: float) -> float:
    """Derived additive crossed-random-effects sensitivity, not a binary generator."""
    if min(n, seeds) <= 0 or min(variance_family, variance_seed, variance_interaction) < 0:
        raise ValueError("Require positive counts and nonnegative variances")
    return variance_family / n + variance_seed / seeds + variance_interaction / (n * seeds)


def validate() -> dict:
    checks = []
    for n in (0, 1, 5, 30, 1000):
        for p in (0.0, 0.1, 0.5, 0.9, 1.0):
            probs = binomial_pmf(n, p)
            assert abs(math.fsum(probs) - 1) < 1e-12
            assert abs(math.fsum(k * v for k, v in enumerate(probs)) - n * p) < 1e-9
    checks.append("PMF normalization, mean, p=0/1, n=0 and n=1000")
    assert critical_tail(5) == -1 and critical_tail(6) == 0
    assert abs(2 * binomial_pmf(6, .5)[0] - .03125) < 1e-12
    checks.append("Exact binomial boundary: five all-direction discordances cannot reject; six can")
    assert exact_power(30, 0, 0)["power_two_sided_any_direction"] == 0
    assert exact_power(5, 1, 1)["power_two_sided_any_direction"] == 0
    assert exact_power(6, 1, 1)["power_two_sided_any_direction"] == 1
    for q in (.1, .2, .4, 1):
        for n in (6, 30, 100, 300):
            assert exact_power(n, 0, q)["power_two_sided_any_direction"] <= ALPHA + 1e-12
    checks.append("Zero discordance; deterministic alternative; exact null size <=.05")
    # Independent brute-force multinomial enumeration for small N.
    q, delta = .4, .1
    plus, minus, same = (q + delta) / 2, (q - delta) / 2, 1 - q
    for n in range(9):
        brute = 0.0
        for b in range(n + 1):
            for c in range(n - b + 1):
                m = b + c
                k = critical_tail(m)
                if k >= 0 and (b <= k or b >= m - k):
                    factor = math.comb(n, b) * math.comb(n - b, c)
                    brute += factor * plus ** b * minus ** c * same ** (n - m)
        assert abs(brute - exact_power(n, delta, q)["power_two_sided_any_direction"]) < 1e-12
    checks.append("Independent brute multinomial sum equals conditional-binomial sum for n=0..8")
    for parameters in ((.9, .1, .4), (.55, .2, .1), (-.1, .1, .2)):
        try:
            paired_probabilities(*parameters)
        except ValueError:
            pass
        else:
            raise AssertionError("Impossible paired-table parameters were accepted")
    checks.append("Impossible paired tables rejected")
    v = crossed_variance(30, 3, .1, .0004, .0971)
    assert math.isclose(v, .1/30 + .0004/3 + .0971/90)
    assert crossed_variance(30, 3, .1, 0, 0) == .1 / 30
    assert crossed_variance(300, 3, 0, .0004, 0) == .0004 / 3
    checks.append("Crossed variance identity and family-only/seed-only limits")
    rng = random.Random(SEED)
    simulations = []
    for n in (30, 300):
        repetitions, rejected = 20000, 0
        for _ in range(repetitions):
            b = c = 0
            for _ in range(n):
                u = rng.random()
                if u < .125: b += 1
                elif u < .20: c += 1
            k = critical_tail(b + c)
            rejected += int(k >= 0 and (b <= k or b >= b + c - k))
        observed = rejected / repetitions
        expected = exact_power(n, .05, .2)["power_two_sided_any_direction"]
        mc_se = math.sqrt(expected * (1 - expected) / repetitions)
        assert abs(observed - expected) < 5 * mc_se
        simulations.append({"n": n, "repetitions": repetitions, "simulation_seed": SEED,
                            "simulated_rejection_rate": observed, "exact_expected_power": expected,
                            "Monte_Carlo_standard_error": mc_se})
    checks.append("Seeded 20,000-replicate multinomial sanity checks agree within five MC standard errors")
    return {"status": "PASS", "checks": checks, "simulation_checks": simulations}


def write_csv(path: Path, records: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(records)


def main() -> None:
    out = Path(__file__).resolve().parent
    checks = validate()
    rows = []
    for q in (.10, .20, .40):
        for delta in (.03, .05, .10):
            population = paired_probabilities(BASELINE, delta, q)
            for n in SAMPLE_SIZES:
                rows.append({"status": "PLANNING_NOT_OBSERVATIONS", "n_independent_families": n,
                             "baseline_assumed": BASELINE, "gain_assumed": delta,
                             "discordance_assumed": q, "alpha": ALPHA,
                             **population, **exact_power(n, delta, q),
                             "approximate_n_for_80_percent_power_NOT_exact": approximate_n80(delta, q)})
    write_csv(out / "paired_power_scenarios.csv", rows)
    # Continuous variance sensitivity only: no claim to simulate bounded binary answers.
    crossed = []
    total_var = .20 - .05**2
    for family_fraction in (.30, .80):
        for seed_sd in (0, .01, .03):
            vf, vs = family_fraction * total_var, seed_sd**2
            ve = total_var - vf - vs
            for n in (30, 300, 1000):
                for s in (1, 3, 5, 10):
                    variance = crossed_variance(n, s, vf, vs, ve)
                    crossed.append({"status": "PLANNING_CROSSED_VARIANCE_SENSITIVITY",
                                    "n_independent_families": n, "paired_training_seeds": s,
                                    "family_fraction_assumed": family_fraction,
                                    "seed_effect_SD_assumed": seed_sd,
                                    "variance_family": vf, "variance_seed": vs,
                                    "variance_interaction": ve,
                                    "SE_crossed": math.sqrt(variance),
                                    "SE_incorrect_iid_NS": math.sqrt(total_var/(n*s)),
                                    "normal_95_halfwidth_NOT_calibrated_CI": 1.959963984540054*math.sqrt(variance)})
    write_csv(out / "crossed_variance_scenarios.csv", crossed)
    manifest = {"status": "MODEL_FREE_PLANNING_ONLY", "created_utc": datetime.now(timezone.utc).isoformat(),
                "python": platform.python_version(), "code_SHA256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                "seed_for_Monte_Carlo_validation_only": SEED,
                "exact_power_random_seed": None,
                "assumptions": {"baseline": BASELINE, "discordance": [.1,.2,.4], "gains": [.03,.05,.1],
                                "alpha": ALPHA, "independent_identically_distributed_families_single_checkpoint_pair": True},
                "checks": checks,
                "outputs": {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                            for p in (out / "paired_power_scenarios.csv", out / "crossed_variance_scenarios.csv")}}
    (out / "planning_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"status": checks["status"], "power_scenarios": len(rows), "crossed_scenarios": len(crossed),
                      "code_SHA256": manifest["code_SHA256"], "checks": len(checks["checks"])}, indent=2))


if __name__ == "__main__":
    main()
