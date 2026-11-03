"""Tests for research/phase2_power/phase2_power_dev_rerun_v1.py (planning only; Amendment 2 item 8, Sol review R9)."""
import contextlib
import csv
import hashlib
import importlib.util
import io
import json
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
POWER = ROOT / "research" / "phase2_power"
REPS = 40  # small for speed; the script's default is the original 4,000


def load():
    spec = importlib.util.spec_from_file_location("phase2_power_dev_rerun_v1", POWER / "phase2_power_dev_rerun_v1.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


R = load()
P = R.P


def cells(rows):
    return {(r["q0"], r["delta_pp"]): r for r in rows}


class DevRerunTests(unittest.TestCase):
    def test_original_script_and_archive_unchanged(self):
        self.assertEqual(hashlib.sha256((POWER / "phase2_power.py").read_bytes()).hexdigest(), R.ORIGINAL_SHA256)
        self.assertTrue(R.ORIGINAL_SHA256.startswith("7620f4db") and R.ORIGINAL_SHA256.endswith("0803"))  # §9
        manifest = json.loads((POWER / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["script_sha256"], R.ORIGINAL_SHA256)
        for name, checksum in manifest["outputs_sha256"].items():
            self.assertEqual(hashlib.sha256((POWER / name).read_bytes()).hexdigest(), checksum, name)
        # The original grid is used as is; the original still rejects p0 = 1.
        self.assertEqual((P.Q0_GRID, P.DELTAS, P.N_MAIN, P.N_SEEDS), ((0.035, 0.071, 0.114, 0.2), (0.0, 0.03, 0.05, 0.1), 100, 3))
        self.assertIsNone(P.mixture(1, 0))

    def test_k40_only_the_degenerate_zero_headroom_cell_is_admissible(self):
        rows = R.rerun_grid(40, reps=REPS)
        self.assertEqual(len(rows), len(P.Q0_GRID) * len(P.DELTAS) + 1)
        admissible = [r for r in rows if not r["status"].startswith("infeasible")]
        self.assertEqual(len(admissible), 1)
        cell = admissible[0]
        self.assertEqual((cell["p0"], cell["q0"], cell["delta_pp"]), (1.0, 0.0, 0.0))
        self.assertEqual(cell["status"], R.DEGENERATE_STATUS)
        self.assertIn("degenerate", cell["status"])
        self.assertEqual((cell["power_lb_gt_0"], cell["power_lb_gt_5pp"], cell["mean_estimate_pp"],
                          cell["median_ci_halfwidth_pp"], cell["p_all_3_seeds_positive"], cell["per_seed_mcnemar_power"]),
                         (0.0, 0.0, 0.0, 0.0, 0.0, 0.0))
        grid = [r for r in rows if r is not cell]
        self.assertEqual({(r["q0"], r["delta_pp"]) for r in grid},
                         {(q, round(100 * d, 1)) for q in P.Q0_GRID for d in P.DELTAS})  # whole original grid reported
        for r in grid:
            self.assertTrue(r["status"].startswith("infeasible"), r)
        self.assertEqual(R.summary(rows), {"cells": 17, "feasible": 0, "degenerate": 1, "infeasible": 16, "feasible_cells": []})

    def test_k39(self):
        rows = R.rerun_grid(39, reps=REPS)
        self.assertEqual(len(rows), 16)
        self.assertTrue(all(r["p0"] == 0.975 for r in rows))
        by = cells(rows)
        # Headroom 2.5 pp: only delta = 0 fits, and only q0 = 0.035 has a feasible mixture.
        self.assertEqual(R.summary(rows)["feasible_cells"], [[0.035, 0.0]])
        for q0 in (0.071, 0.114, 0.2):
            for d in (0.0, 3.0, 5.0, 10.0):
                self.assertEqual(by[(q0, d)]["status"], "infeasible (p0,q0)")
        for d in (3.0, 5.0, 10.0):
            self.assertEqual(by[(0.035, d)]["status"], "infeasible: delta > headroom 2.5 pp")
        self.assertNotIn(R.DEGENERATE_STATUS, {r["status"] for r in rows})

    def test_k38(self):
        rows = R.rerun_grid(38, reps=REPS)
        by = cells(rows)
        self.assertTrue(all(r["p0"] == 0.95 for r in rows))
        # Headroom 5 pp: delta 0, 3 and 5 fit (5 pp exactly at the boundary); q0 0.035 and 0.071 have mixtures.
        self.assertEqual(R.summary(rows)["feasible_cells"],
                         [[q, d] for q in (0.035, 0.071) for d in (0.0, 3.0, 5.0)])
        for q0 in (0.035, 0.071):
            self.assertEqual(by[(q0, 10.0)]["status"], "infeasible: delta > headroom 5.0 pp")
        for q0 in (0.114, 0.2):
            for d in (0.0, 3.0, 5.0, 10.0):
                self.assertEqual(by[(q0, d)]["status"], "infeasible (p0,q0)")

    def test_feasible_cells_equal_the_original_logic(self):
        for k in (38, 30):
            for row in R.rerun_grid(k, reps=REPS):
                if row["status"] == "ok":
                    original = P.run_scenario(k / 40, row["q0"], row["delta_pp"] / 100, 100, REPS)
                    self.assertEqual({key: v for key, v in row.items() if key not in ("dev_k", "dev_n")}, original)

    def test_k_validation(self):
        for bad in (41, -1, 38.0, "38", True, None):
            with self.assertRaises(ValueError):
                R.rerun_grid(bad, reps=REPS)

    def test_cli_writes_planning_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "rerun"
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(R.main(["--k", "40", "--out", str(out), "--reps", "5"]), 0)
                self.assertEqual(R.main(["--k", "40", "--out", str(out), "--reps", "5"]), 2)  # never overwrites
            manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
            self.assertTrue(manifest["label"].startswith("PLANNING ONLY"))
            self.assertEqual((manifest["dev_k"], manifest["p0"], manifest["summary"]["degenerate"]), (40, 1.0, 1))
            self.assertEqual(manifest["original_script"]["sha256"], R.ORIGINAL_SHA256)
            with open(out / "power_grid_dev_k40.csv", newline="", encoding="utf-8") as fh:
                rows = list(csv.DictReader(fh))
            self.assertEqual(len(rows), 17)
            self.assertEqual(hashlib.sha256((out / "power_grid_dev_k40.csv").read_bytes()).hexdigest(),
                             manifest["outputs_sha256"]["power_grid_dev_k40.csv"])


if __name__ == "__main__":
    unittest.main()
