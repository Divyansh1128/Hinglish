"""Phase-2 power and precision for Delta_C, grounded in REAL Pilot-B outcomes.

PLANNING ONLY. Reads the stored per-family Pilot-B outcomes of the UNCHANGED
models (results/pilot_b/*/per_rendering.csv); no trained model exists. The
pilot supplies baseline accuracy and discordance *proxies*; the trained-arm
seed-to-seed discordance is unobserved and is varied as a sensitivity grid.
FINAL_TEST is not read (it stays untouched).

Run from anywhere (Python >= 3.9, standard library only):
    python3 research/phase2_power/phase2_power.py
Deterministic: every scenario has a fixed seed (CRC32 of its label + BASE_SEED),
so CSV/JSON outputs are byte-identical across reruns on the same Python.
Only manifest.json carries a timestamp.

Family model (per C-form family, for the E+R arm; three-point mixture):
  solid   (pi = 1)      fraction s
  fragile (pi = p_f)    fraction f   (each checkpoint correct w.p. p_f)
  hard    (pi = 0)      fraction h
calibrated so mean accuracy = p0 and the discordance between two
independently trained checkpoints of the same arm = q0 = 2 f p_f (1 - p_f).
Default p_f = 0.5 (f = 2 q0, h = 1 - p0 - q0); if that makes h < 0, h = 0 and
p_f is solved; combinations needing p_f >= 1 are infeasible and reported.
E+C arm: pi' = pi + k (1 - pi), k = delta / (1 - p0) (proportional use of
headroom; delta > 1 - p0 is impossible). Seeds are conditionally independent
given the family; seed s of E+C is paired with seed s of E+R.
"""
from __future__ import annotations

import csv
import hashlib
import json
import math
import platform
import random
import statistics
import zlib
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
PILOT = ROOT / "results" / "pilot_b"
MODELS = ("qwen3-4b", "qwen3-8b", "llama-3.2-3b")
BASE_SEED = 20261027
N_SEEDS = 3
Z = 1.959963984540054
REPS_GRID = 4000
REPS_SCALE = 2000
P0_GRID = (0.943, 0.857, 0.700)          # pilot Qwen3-4B C, Qwen3-4B R, ~Llama C
Q0_GRID = (0.035, 0.071, 0.114, 0.200)   # half of min proxy, 5/70, 8/70, 14/70
DELTAS = (0.0, 0.03, 0.05, 0.10)
N_MAIN = 100
N_SCALE = (100, 200, 300, 600)
RETENTION_MARGIN = 0.02
USEFUL = 0.05


# ---------------------------------------------------------------- pilot data
def load_pilot():
    out = {}
    for m in MODELS:
        with open(PILOT / m / "per_rendering.csv", newline="", encoding="utf-8") as fh:
            for r in csv.DictReader(fh):
                strict = r["correct"] == "True"
                num_v1 = r["numeric_correct"] == "True"
                # v2 proxy: v1 match, or strict-correct whose only v1 failure is a
                # trailing rupee sign (lower bound: strict failures are not rescued).
                trailing_rupee = (strict and r["numeric_status"] == "unsupported_answer"
                                  and r["extracted_final"].strip().endswith("₹"))
                out[(m, r["family_id"], r["form"])] = (strict, num_v1, num_v1 or trailing_rupee)
    return out


def pilot_estimates(data):
    fams = sorted({k[1] for k in data})
    n = len(fams)
    est = {"families": n, "source": "results/pilot_b/*/per_rendering.csv (unchanged models)"}
    acc = {}
    for m in MODELS:
        for form in "ERC":
            vals = [data[(m, f, form)] for f in fams]
            acc[f"{m}/{form}"] = {
                "strict": sum(v[0] for v in vals), "numeric_v1": sum(v[1] for v in vals),
                "numeric_v2_proxy": sum(v[2] for v in vals), "n": n}
    est["accuracy_counts"] = acc

    def disc(a, b):
        plus = sum(data[(a[0], f, a[1])][0] and not data[(b[0], f, b[1])][0] for f in fams)
        minus = sum(data[(b[0], f, b[1])][0] and not data[(a[0], f, a[1])][0] for f in fams)
        return {"first_only": plus, "second_only": minus, "discordant": plus + minus,
                "rate": round((plus + minus) / n, 4)}
    pairs = {
        "qwen3-4b C vs qwen3-8b C (cross-checkpoint, same form)": (("qwen3-4b", "C"), ("qwen3-8b", "C")),
        "qwen3-4b E vs qwen3-8b E": (("qwen3-4b", "E"), ("qwen3-8b", "E")),
        "qwen3-4b R vs qwen3-8b R": (("qwen3-4b", "R"), ("qwen3-8b", "R")),
        "qwen3-4b C vs R (same checkpoint, cross-form)": (("qwen3-4b", "C"), ("qwen3-4b", "R")),
        "qwen3-4b C vs E": (("qwen3-4b", "C"), ("qwen3-4b", "E")),
        "qwen3-4b E vs R": (("qwen3-4b", "E"), ("qwen3-4b", "R")),
        "qwen3-4b C vs llama-3.2-3b C": (("qwen3-4b", "C"), ("llama-3.2-3b", "C")),
    }
    est["discordance_strict"] = {k: disc(*v) for k, v in pairs.items()}
    est["qwen3-4b_families_failing_any_form"] = sum(
        any(not data[("qwen3-4b", f, x)][0] for x in "ERC") for f in fams)
    est["qwen3-4b_families_failing_all_forms"] = sum(
        all(not data[("qwen3-4b", f, x)][0] for x in "ERC") for f in fams)
    return est


# ---------------------------------------------------------------- family model
def mixture(p0, q0):
    """Return list of (fraction, pi) or None if (p0, q0) is infeasible."""
    if not (0 < p0 < 1 and 0 <= q0 <= 0.5):
        return None
    if q0 == 0:
        return [(p0, 1.0), (1 - p0, 0.0)]
    f, pf = 2 * q0, 0.5
    h = 1 - p0 - q0
    if h < 0:
        pf = q0 / (2 * (1 - p0))
        if pf >= 1:
            return None
        f, h = (1 - p0) / (1 - pf), 0.0
    s = 1 - f - h
    if s < -1e-12:
        return None
    comps = [(max(s, 0.0), 1.0), (f, pf), (h, 0.0)]
    assert abs(sum(w * p for w, p in comps) - p0) < 1e-9
    assert abs(sum(w * 2 * p * (1 - p) for w, p in comps) - q0) < 1e-9
    return comps


def draw_family(rng, comps):
    u, acc = rng.random(), 0.0
    for w, p in comps:
        acc += w
        if u < acc:
            return p
    return comps[-1][1]


def seed_of(label):
    return (zlib.crc32(label.encode()) + BASE_SEED) & 0xFFFFFFFF


def binom_two_sided_p(k, m):
    if m == 0:
        return 1.0
    lo = min(k, m - k)
    tail = sum(math.comb(m, j) for j in range(lo + 1)) / 2 ** m
    return min(1.0, 2 * tail)


def simulate_dataset(rng, comps, k, n):
    """Return per-family seed-averaged d_i and per-seed (plus, minus) counts."""
    d = []
    plus = [0] * N_SEEDS
    minus = [0] * N_SEEDS
    for _ in range(n):
        pi = draw_family(rng, comps)
        pi_c = pi + k * (1 - pi)
        tot = 0
        for s in range(N_SEEDS):
            a = 1 if (pi_c >= 1 or rng.random() < pi_c) else 0   # E+C on C
            b = 1 if (pi >= 1 or (pi > 0 and rng.random() < pi)) else 0  # E+R on C
            tot += a - b
            if a > b:
                plus[s] += 1
            elif b > a:
                minus[s] += 1
        d.append(tot / N_SEEDS)
    return d, plus, minus


def wald(d):
    n = len(d)
    m = math.fsum(d) / n
    sd = statistics.stdev(d) if n > 1 else 0.0
    half = Z * sd / math.sqrt(n)
    return m, m - half, m + half


def run_scenario(p0, q0, delta, n, reps):
    label = f"p0={p0}|q0={q0}|delta={delta}|n={n}"
    comps = mixture(p0, q0)
    row = {"p0": p0, "q0": q0, "delta_pp": round(100 * delta, 1), "families": n,
           "seeds": N_SEEDS, "reps": reps}
    if comps is None:
        row["status"] = "infeasible (p0,q0)"
        return row
    if delta > 1 - p0 + 1e-12:
        row["status"] = f"infeasible: delta > headroom {100 * (1 - p0):.1f} pp"
        return row
    k = delta / (1 - p0)
    rng = random.Random(seed_of(label))
    lb_pos = lb_useful = all3 = mcn = 0
    halves, ests, between_q = [], [], []
    for _ in range(reps):
        d, plus, minus = simulate_dataset(rng, comps, k, n)
        m, lo, hi = wald(d)
        ests.append(m)
        halves.append((hi - lo) / 2)
        lb_pos += lo > 0
        lb_useful += lo > USEFUL
        all3 += all(p > q for p, q in zip(plus, minus))
        for p, q in zip(plus, minus):
            mcn += (p > q and binom_two_sided_p(p, p + q) < 0.05)
        between_q.append(sum(p + q for p, q in zip(plus, minus)) / (N_SEEDS * n))
    row.update({
        "status": "ok",
        "mix_solid_fragile_hard": "/".join(f"{w:.3f}" for w, _ in comps),
        "fragile_pi": round(comps[1][1], 3),
        "between_arm_discordance": round(statistics.mean(between_q), 4),
        "power_lb_gt_0": round(lb_pos / reps, 4),
        "power_lb_gt_5pp": round(lb_useful / reps, 4),
        "p_all_3_seeds_positive": round(all3 / reps, 4),
        "per_seed_mcnemar_power": round(mcn / (reps * N_SEEDS), 4),
        "mean_estimate_pp": round(100 * statistics.mean(ests), 2),
        "median_ci_halfwidth_pp": round(100 * statistics.median(halves), 2),
        "mde80_pp_approx": round(100 * (Z + 0.8416212335729143) / Z * statistics.median(halves), 2),
    })
    return row


def retention(p0_e, q0, n, reps):
    """E+C vs E+E on E with no true difference: P(lower bound > -margin)."""
    comps = mixture(p0_e, q0)
    if comps is None:
        return {"p0_E": p0_e, "q0": q0, "families": n, "status": "infeasible"}
    rng = random.Random(seed_of(f"retention|{p0_e}|{q0}|{n}"))
    ok, halves = 0, []
    for _ in range(reps):
        d, _, _ = simulate_dataset(rng, comps, 0.0, n)
        m, lo, hi = wald(d)
        ok += lo > -RETENTION_MARGIN
        halves.append((hi - lo) / 2)
    return {"p0_E": p0_e, "q0": q0, "families": n, "status": "ok",
            "p_noninferiority_shown_at_true_0": round(ok / reps, 4),
            "median_ci_halfwidth_pp": round(100 * statistics.median(halves), 2)}


def specificity_halfwidth(p0_c, p0_r, q0, n, reps):
    """Delta_C - Delta_R under the null, C and R outcomes independent given family."""
    cc, cr = mixture(p0_c, q0), mixture(p0_r, q0)
    if cc is None or cr is None:
        return {"status": "infeasible"}
    rng = random.Random(seed_of(f"spec|{p0_c}|{p0_r}|{q0}|{n}"))
    halves = []
    for _ in range(reps):
        dc, _, _ = simulate_dataset(rng, cc, 0.0, n)
        dr, _, _ = simulate_dataset(rng, cr, 0.0, n)
        _, lo, hi = wald([a - b for a, b in zip(dc, dr)])
        halves.append((hi - lo) / 2)
    return {"p0_C": p0_c, "p0_R": p0_r, "q0": q0, "families": n, "status": "ok",
            "median_ci_halfwidth_pp": round(100 * statistics.median(halves), 2)}


def validate_bootstrap(p0, q0, delta, n, reps=300, draws=2000):
    """Check the Wald shortcut against a real percentile family bootstrap."""
    comps = mixture(p0, q0)
    k = delta / (1 - p0)
    rng = random.Random(seed_of(f"validate|{p0}|{q0}|{delta}|{n}"))
    agree = w_pos = b_pos = 0
    for _ in range(reps):
        d, _, _ = simulate_dataset(rng, comps, k, n)
        _, lo, _ = wald(d)
        boots = sorted(math.fsum(rng.choices(d, k=n)) / n for _ in range(draws))
        b_lo = boots[int(0.025 * draws)]
        w_pos += lo > 0
        b_pos += b_lo > 0
        agree += (lo > 0) == (b_lo > 0)
    return {"p0": p0, "q0": q0, "delta_pp": 100 * delta, "families": n, "reps": reps,
            "bootstrap_draws": draws, "wald_power": round(w_pos / reps, 4),
            "percentile_bootstrap_power": round(b_pos / reps, 4),
            "decision_agreement": round(agree / reps, 4)}


def self_checks():
    assert binom_two_sided_p(0, 6) == 2 / 64
    assert binom_two_sided_p(3, 6) == 1.0
    for p0 in P0_GRID:
        for q0 in Q0_GRID:
            c = mixture(p0, q0)
            if c:
                assert abs(sum(w for w, _ in c) - 1) < 1e-9
    assert mixture(0.943, 0.2) is None
    # null scenario must not be biased
    r = run_scenario(0.857, 0.114, 0.0, 100, 400)
    assert abs(r["mean_estimate_pp"]) < 1.0, r
    return "passed"


def write_csv(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main():
    checks = self_checks()
    data = load_pilot()
    est = pilot_estimates(data)
    (HERE / "pilot_estimates.json").write_text(json.dumps(est, indent=2) + "\n", encoding="utf-8")

    grid = [run_scenario(p0, q0, d, N_MAIN, REPS_GRID)
            for p0 in P0_GRID for q0 in Q0_GRID for d in DELTAS]
    write_csv(HERE / "power_grid_n100.csv", grid)

    scale = [run_scenario(p0, q0, d, n, REPS_SCALE)
             for (p0, q0) in ((0.943, 0.071), (0.857, 0.114))
             for d in (0.03, 0.05, 0.10) for n in N_SCALE]
    write_csv(HERE / "n_scaling.csv", scale)

    sec = {
        "retention_E_margin_2pp": [retention(0.943, q, N_MAIN, REPS_SCALE) for q in (0.035, 0.071, 0.114)],
        "specificity_null_halfwidth": [specificity_halfwidth(0.943, 0.857, q, N_MAIN, REPS_SCALE) for q in (0.035, 0.071, 0.114)],
        "hoeffding_radius_pp_n100": round(100 * math.sqrt(2 * math.log(40) / N_MAIN), 2),
        "bootstrap_validation": [validate_bootstrap(0.857, 0.114, 0.05, N_MAIN),
                                 validate_bootstrap(0.943, 0.071, 0.05, N_MAIN)],
    }
    (HERE / "secondary_and_validation.json").write_text(json.dumps(sec, indent=2) + "\n", encoding="utf-8")

    outs = ["pilot_estimates.json", "power_grid_n100.csv", "n_scaling.csv", "secondary_and_validation.json"]
    manifest = {
        "label": "PLANNING ONLY - unchanged-model pilot proxies, simulated trained arms",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "python": platform.python_version(),
        "base_seed": BASE_SEED, "self_checks": checks,
        "inputs_sha256": {f"results/pilot_b/{m}/per_rendering.csv":
                          hashlib.sha256((PILOT / m / "per_rendering.csv").read_bytes()).hexdigest() for m in MODELS},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "outputs_sha256": {o: hashlib.sha256((HERE / o).read_bytes()).hexdigest() for o in outs},
    }
    (HERE / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
