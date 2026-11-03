"""Tests for phase2_analysis/calibrate.py (Amendment 1 item 16)."""
import json
import random
import unittest
from pathlib import Path

from phase2_analysis import analyze as A
from phase2_analysis import calibrate as C

HERE = Path(__file__).resolve().parents[1]


class CalibrationTests(unittest.TestCase):
    def test_fast_sums_equal_implemented_resampling(self):
        indices = A.bootstrap_indices(C.N, resamples=300)
        cols = C.column_counts(indices)
        rng = random.Random(5)
        for _ in range(20):
            nums = [rng.choice((-3, -2, -1, 0, 0, 0, 0, 1, 2, 3)) for _ in range(C.N)]
            self.assertEqual(C.fast_sums(nums, cols), A.resample_sums(nums, indices))
        self.assertEqual(C.fast_sums([0] * C.N, cols), [0] * 300)

    def test_matrix_rows_are_the_real_matrix_prefix(self):
        self.assertEqual(A.bootstrap_indices(C.N, resamples=50), A.bootstrap_indices(C.N)[:50])

    def test_targets(self):
        for c, expected in ((C.component(0.7, 0.05, C.gain_for(0.05, 0.7, 0.05)), 0.05),
                            (C.component(0.9, 0.035, 0.0, C.loss_for(-0.02, 0.9, 0.035)), -0.02),
                            (C.component(0.9, 0.0, 0.1), 0.01),
                            (C.component(0.6, 0.05, 0.15, 0.10), 0.0)):
            self.assertAlmostEqual(C.target(c), expected, places=12)
            rng = random.Random(1)
            nums = C.draw_numerators(rng, c, n=60000)
            self.assertAlmostEqual(sum(nums) / (3 * len(nums)), expected, delta=0.006)
        names = [s[0] for s in C.SCENARIOS]
        self.assertEqual(len(names), len(set(names)))
        targets = {s[0]: (C.target(s[3]), C.target(s[4])) for s in C.SCENARIOS}
        self.assertAlmostEqual(targets["boundary_plus5"][0], 0.05)            # margin boundary Δ_C = +5
        self.assertAlmostEqual(targets["retention_boundary_minus2"][1], -0.02)  # margin boundary retention = −2
        self.assertEqual([s[3]["p0"] for s in C.SCENARIOS if s[1] == "ceiling"], [0.943, 0.943])
        self.assertEqual({s[1] for s in C.SCENARIOS}, {"null", "asymmetric", "sparse/degenerate", "margin boundary", "ceiling"})

    def test_scenario_deterministic_and_degenerate_handling(self):
        index = [s[0] for s in C.SCENARIOS].index("sparse_zero")
        first = C.run_scenario((index, 3, 200))
        self.assertEqual(first, C.run_scenario((index, 3, 200)))
        p = first["primary"]
        self.assertEqual((p["degenerate_rate"], p["coverage"], p["labels"][A.DEGENERATE]), (1.0, 1.0, 1.0))
        self.assertEqual(p["labels_without_degenerate_override"][A.NULL], 1.0)  # what the override prevents
        ret = C.run_scenario(([s[0] for s in C.SCENARIOS].index("retention_zero_sparse"), 3, 200))["retention"]
        self.assertEqual(ret["flags"][A.DEGENERATE], 1.0)
        self.assertEqual(ret["flags"][A.WITHIN], 0.0)

    def test_report_rendering(self):
        results = C.simulate(datasets=2, resamples=100, workers=1)
        self.assertEqual(len(results), len(C.SCENARIOS))
        head = C.headline(results)
        report = dict(version=C.CALIBRATION_VERSION, analyze_sha256="x", headline=head, scenarios=results,
                      reading=C.reading(results), settings=dict(N=100, S=3, datasets=2, resamples=100, python_version="3"))
        text = C.markdown(report)
        self.assertIn("Null false-support rate", text)
        self.assertIn("fewer resamples than the real analysis", text)
        json.dumps(report)

    def test_archived_calibration_matches_current_code(self):
        data = json.loads((HERE / "calibration.json").read_text(encoding="utf-8"))
        self.assertEqual(data["analyze_sha256"], A.sha256((HERE / "analyze.py").read_bytes()))
        self.assertEqual((data["settings"]["N"], data["settings"]["S"]), (100, 3))
        self.assertEqual(data["settings"]["resamples"], 10000)
        self.assertGreaterEqual(data["settings"]["datasets"], 1000)
        self.assertEqual([s["name"] for s in data["scenarios"]], [s[0] for s in C.SCENARIOS])
        self.assertTrue((HERE / "CALIBRATION.md").is_file())


if __name__ == "__main__":
    unittest.main()
