"""Phase-2 planning rerun at the observed unchanged-DEV C accuracy (version 1). PLANNING ONLY.

PREREGISTRATION section 5 with Amendment 1 item 7 and Amendment 2 item 8: after the unchanged
Qwen3-4B DEV run, the original power grid is rerun "for the record" with p0 = k/40, where k is
the observed unchanged-model DEV C strict count. The design, the labels and the thresholds
never change because of this rerun.

The simulation logic is imported, unchanged, from the original planning script
``research/phase2_power/phase2_power.py`` (SHA-256 pinned below and checked at import); that
script and its archived outputs are not modified. This file only:

* replaces p0 by k/40 and reruns the original q0 x delta grid (Q0_GRID x DELTAS, N = 100,
  S = 3, the original reps and per-cell seeds), with every infeasible cell reported explicitly
  as the original code reports it;
* handles the boundary p0 = 1 (k = 40), which the original mixture rejects: with zero headroom
  every family is solid, so seed discordance q0 > 0 and any gain delta > 0 are impossible, and
  the single admissible cell (q0 = 0, delta = 0) is degenerate (every family contrast is 0, the
  interval has zero width, and the registered label would be "inconclusive—degenerate empirical
  interval"). That cell is added to the report only for p0 = 1.

Usage (from anywhere; standard library only):

    python3 research/phase2_power/phase2_power_dev_rerun_v1.py --k K --out NEW_DIR [--reps 4000]

Writes NEW_DIR/power_grid_dev_k{K}.csv and NEW_DIR/manifest.json (label PLANNING ONLY).
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import platform
import random
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VERSION = "phase2_power_dev_rerun_v1"
DEV_FAMILIES = 40
ORIGINAL_PATH = HERE / "phase2_power.py"
ORIGINAL_SHA256 = "7620f4dba1417c2b916567b6df96619df5f815624323b8ee31dce58844290803"  # PREREGISTRATION §9
DEGENERATE_STATUS = ("admissible: degenerate zero-headroom cell (p0 = 1, q0 = 0, delta = 0; every family contrast 0, "
                     "zero-width interval, label 'inconclusive—degenerate empirical interval')")


def load_original():
    """Import the original planning script after checking that it is byte-identical to the registered one."""
    actual = hashlib.sha256(ORIGINAL_PATH.read_bytes()).hexdigest()
    if actual != ORIGINAL_SHA256:
        raise ValueError(f"{ORIGINAL_PATH.name} SHA-256 {actual} is not the registered {ORIGINAL_SHA256}")
    spec = importlib.util.spec_from_file_location("phase2_power_original", ORIGINAL_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


P = load_original()


def p0_from_k(k):
    if type(k) is not int or not 0 <= k <= DEV_FAMILIES:
        raise ValueError(f"k must be the unchanged-model DEV C strict count, an integer 0-{DEV_FAMILIES}")
    return k / DEV_FAMILIES


def zero_headroom_cell(q0, delta, n, reps):
    """p0 = 1: the original mixture() rejects it. Only (q0 = 0, delta = 0) is admissible, and it is degenerate."""
    row = {"p0": 1.0, "q0": q0, "delta_pp": round(100 * delta, 1), "families": n, "seeds": P.N_SEEDS, "reps": reps}
    if q0 > 0:
        row["status"] = "infeasible: p0 = 1 leaves no fragile families, so seed discordance q0 > 0 is impossible"
        return row
    if delta > 0:
        row["status"] = "infeasible: delta > headroom 0.0 pp"
        return row
    # The admissible cell, simulated with the original machinery: every family solid (pi = 1), no gain (k = 0).
    comps = [(1.0, 1.0)]
    rng = random.Random(P.seed_of(f"p0={1.0}|q0={q0}|delta={delta}|n={n}"))
    halves, ests, lb_pos, lb_useful, all3, mcn = [], [], 0, 0, 0, 0
    for _ in range(reps):
        d, plus, minus = P.simulate_dataset(rng, comps, 0.0, n)
        m, lo, hi = P.wald(d)
        ests.append(m)
        halves.append((hi - lo) / 2)
        lb_pos += lo > 0
        lb_useful += lo > P.USEFUL
        all3 += all(p > q for p, q in zip(plus, minus))
        mcn += sum(p > q and P.binom_two_sided_p(p, p + q) < 0.05 for p, q in zip(plus, minus))
    row.update({
        "status": DEGENERATE_STATUS,
        "mix_solid_fragile_hard": "1.000/0.000/0.000",
        "fragile_pi": None,
        "between_arm_discordance": 0.0,
        "power_lb_gt_0": round(lb_pos / reps, 4),
        "power_lb_gt_5pp": round(lb_useful / reps, 4),
        "p_all_3_seeds_positive": round(all3 / reps, 4),
        "per_seed_mcnemar_power": round(mcn / (reps * P.N_SEEDS), 4),
        "mean_estimate_pp": round(100 * statistics.mean(ests), 2),
        "median_ci_halfwidth_pp": round(100 * statistics.median(halves), 2),
        "mde80_pp_approx": None,
    })
    return row


def rerun_grid(k, n=None, reps=None):
    """The original q0 x delta grid at p0 = k/40, every cell reported (feasible, infeasible or degenerate)."""
    p0 = p0_from_k(k)
    n = P.N_MAIN if n is None else n
    reps = P.REPS_GRID if reps is None else reps
    rows = []
    for q0 in P.Q0_GRID:
        for delta in P.DELTAS:
            rows.append(zero_headroom_cell(q0, delta, n, reps) if p0 == 1 else P.run_scenario(p0, q0, delta, n, reps))
    if p0 == 1:
        rows.append(zero_headroom_cell(0.0, 0.0, n, reps))
    for row in rows:
        row["dev_k"] = k
        row["dev_n"] = DEV_FAMILIES
    return rows


def summary(rows):
    feasible = [r for r in rows if r["status"] == "ok"]
    return {"cells": len(rows), "feasible": len(feasible),
            "degenerate": sum(r["status"] == DEGENERATE_STATUS for r in rows),
            "infeasible": sum(r["status"].startswith("infeasible") for r in rows),
            "feasible_cells": [[r["q0"], r["delta_pp"]] for r in feasible]}


def main(argv=None):
    parser = argparse.ArgumentParser(description="PLANNING ONLY: rerun the Phase-2 power grid at p0 = k/40.")
    parser.add_argument("--k", type=int, required=True, help="unchanged-model DEV C strict count out of 40")
    parser.add_argument("--out", required=True, help="new output directory")
    parser.add_argument("--reps", type=int, default=P.REPS_GRID, help=f"datasets per cell (original {P.REPS_GRID})")
    args = parser.parse_args(argv)
    out = Path(args.out)
    if out.exists() and any(out.iterdir()):
        print(f"REFUSED: output directory {out} must be new or empty", file=sys.stderr)
        return 2
    rows = rerun_grid(args.k, reps=args.reps)
    out.mkdir(parents=True, exist_ok=True)
    name = f"power_grid_dev_k{args.k}.csv"
    P.write_csv(out / name, rows)
    manifest = {
        "label": "PLANNING ONLY - original Phase-2 power grid rerun at the observed unchanged-DEV C accuracy; "
                 "design, labels and thresholds unchanged (PREREGISTRATION §5, Amendment 1 item 7, Amendment 2 item 8)",
        "version": VERSION, "dev_k": args.k, "dev_n": DEV_FAMILIES, "p0": p0_from_k(args.k),
        "q0_grid": list(P.Q0_GRID), "delta_grid": list(P.DELTAS), "families": P.N_MAIN, "seeds": P.N_SEEDS,
        "reps": args.reps, "base_seed": P.BASE_SEED, "python": platform.python_version(),
        "original_script": {"path": "research/phase2_power/phase2_power.py", "sha256": ORIGINAL_SHA256},
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "summary": summary(rows),
        "outputs_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()},
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(manifest, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
