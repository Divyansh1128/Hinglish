"""Tests for phase2_analysis/analyze.py on synthetic engine runs over DEV only.

Run directories are produced by the real engine (test1_pilot/hinglish_pilot/engine.run) with a
scripted subclass of the engine's FakeBackend, on phase2/dev.v2.json wrapped exactly as the
Pilot-B notebooks wrap their data. FINAL_TEST contents are never read.
"""
import contextlib
import io
import json
import random
import shutil
import tempfile
import unittest
from fractions import Fraction
from pathlib import Path

from phase2_analysis import analyze as A
from test1_pilot.hinglish_pilot import engine
from test1_pilot.hinglish_pilot import report as engine_report

ROOT = Path(__file__).resolve().parents[2]
DEV = ROOT / "phase2" / "dev.v2.json"
SEEDS = (11, 22, 33)
FAMILIES = json.loads(DEV.read_text(encoding="utf-8"))
INDEX = {f["family_id"]: j for j, f in enumerate(FAMILIES)}
RUPEE = {f["family_id"] for f in FAMILIES if f["gold"]["unit"] == "rupees"}


def plan(key, j, form, rupee):
    """Synthetic outcome for checkpoint key on family index j: 'right', 'wrong', 'rupee_suffix' or 'none'."""
    arm, seed = key
    if arm == A.UNCHANGED:
        good = j % 4 != 0
    elif form == "C" and arm == "EC":
        good = (j + seed) % 3 != 0 or j % 2 == 0
    elif form == "C" and arm == "ER":
        good = (j + seed) % 3 != 0
    elif form == "R" and arm == "ER":
        good = j % 7 != 0
    elif form == "E" and arm == "EC":
        good = j % 5 != 0 and j != seed % 40
    else:
        good = j % 5 != 0
    if not good:
        return "none" if j % 11 == 0 else "wrong"
    return "rupee_suffix" if rupee and arm == "EC" and seed == 11 else "right"


def strict_value(outcome):
    return int(outcome in ("right", "rupee_suffix"))  # scorer v1.0.0 accepts '3600 ₹' for rupee gold


def v1_value(outcome):
    return int(outcome == "right")


class ScriptedBackend(engine.FakeBackend):
    """FakeBackend with scripted answers. Labelled 'huggingface' only so engine.run accepts a
    non-demo mode; the hardware field says it is a test fixture."""
    metadata = dict(engine.FakeBackend.metadata, backend="huggingface", hardware="none: scripted FakeBackend test fixture")

    def __init__(self, key):
        self.key = key
        self.by_text = {f["forms"][form]["text"]: (f, form) for f in FAMILIES for form in "ERC"}

    def generate(self, prepared, config, seed):
        text = prepared["rendered_prompt"].split("\nUSER: ", 1)[1].rsplit("\nASSISTANT:", 1)[0]
        family, form = self.by_text[text]
        outcome = plan(self.key, INDEX[family["family_id"]], form, family["family_id"] in RUPEE)
        value = family["gold"]["value"]
        answer = {"right": f"Working.\nFINAL: {value}", "rupee_suffix": f"Working.\nFINAL: {value} ₹",
                  "wrong": "Working.\nFINAL: -987654", "none": "I could not finish."}[outcome]
        return {"raw_response": answer, "output_tokens": len(answer.split()), "latency_seconds": 0.001,
                "truncated": False, "finish_reason": "fake", "memory": {"measurement_scope": "fake"}}


def wrapped_dev():
    """DEV in the engine's pilot_b input format (same wrapper as colab_notebooks/build_pilot_b_notebooks.py)."""
    review = {"reviewers": [{"reviewer_id": "TEST-REV", "reviewed_at": "2026-11-03", "scope": "test fixture"}],
              "adjudication": None}
    families = [dict(f, split_role="PILOT_B_EVAL", review=review) for f in FAMILIES]
    ids = sorted({f[k] for f in FAMILIES for k in ("family_id", "source_family_id", "template_group_id")})
    dataset = dict(schema_version="test1-1", version="phase2-dev-v2-test", kind="pilot_b",
                   borrowing_policy="D033 (test fixture)", families=families)
    splits = dict(schema_version="test1-1", version="phase2-dev-v2-test", kind="pilot_b", audit=None, PILOT_EVAL=[],
                  SMOKE_TRAIN=[], RETIRED_DRAFT=[], CONFIRM_TRAIN=[], FINAL_TEST=[], development_exclusion_ids=ids)
    return dataset, splits


def make_run(root, key, max_items=None):
    dataset, splits = wrapped_dev()
    config = engine.default_config("pilot_b")
    config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
    engine.run(root, dataset, splits, config, ScriptedBackend(key), max_items=max_items)
    return root


TMP = None
CHECKPOINTS = {}


def setUpModule():
    global TMP
    TMP = tempfile.TemporaryDirectory()
    base = Path(TMP.name)
    for key in [(A.UNCHANGED, None)] + [(a, s) for a in A.ARMS for s in SEEDS]:
        name = A.UNCHANGED if key[0] == A.UNCHANGED else f"{key[0]}-{key[1]}"
        CHECKPOINTS[key] = str(make_run(base / name, key))
    # One checkpoint goes in as the engine's ZIP export.
    CHECKPOINTS[("EC", 22)] = str(engine_report.export(Path(CHECKPOINTS[("EC", 22)])))


def tearDownModule():
    TMP.cleanup()


def expected_y(key, endpoint):
    out = {}
    for f in FAMILIES:
        fid = f["family_id"]
        out[fid] = {}
        for form in "ERC":
            o = plan(key, INDEX[fid], form, fid in RUPEE)
            out[fid][form] = strict_value(o) if endpoint == "strict" else v1_value(o) if endpoint == "numeric_literal_v1" \
                else strict_value(o)
    return out


class AnalysisTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.study = A.assemble(DEV, dict(CHECKPOINTS))
        cls.result = A.analyze(cls.study, "not_fired")

    def out(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name) / "analysis"

    def test_dev_accepted_and_runs_verified(self):
        self.assertEqual(self.study["role"], "DEV")
        self.assertEqual(self.result["status"], "COMPLETE")
        self.assertEqual(self.result["families"], 40)
        self.assertEqual({i["kind"] for i in self.result["inputs"]}, {"directory", "zip"})
        self.assertTrue(any("DEV runs" in w for w in self.result["warnings"]))

    def test_estimates_match_direct_computation(self):
        for endpoint in A.ENDPOINTS:
            y = {key: expected_y(key, endpoint) for key in CHECKPOINTS}
            est = self.result["endpoints"][endpoint]["estimands"]
            for name, form, first, second, _ in A.DIFFERENCES:
                total = Fraction(0)
                for fid in INDEX:
                    a = Fraction(sum(y[(first, s)][fid][form] for s in SEEDS), 3)
                    b = y[(A.UNCHANGED, None)][fid][form] if second == A.UNCHANGED else \
                        Fraction(sum(y[(second, s)][fid][form] for s in SEEDS), 3)
                    total += a - b
                with self.subTest(endpoint=endpoint, estimand=name):
                    self.assertEqual(est[name]["estimate"], total / 40)
            self.assertEqual(est["S3"]["estimate"], est["delta_C"]["estimate"] - est["delta_R"]["estimate"])
            for key in CHECKPOINTS:
                for form in "ERC":
                    k = sum(y[key][fid][form] for fid in INDEX)
                    self.assertEqual(self.result["endpoints"][endpoint]["accuracy"][A.checkpoint_name(key)][form]["correct"], k)

    def test_v2_differs_from_v1_only_on_rupee_families(self):
        acc = {e: self.result["endpoints"][e]["accuracy"]["EC:11"] for e in A.ENDPOINTS}
        gained = sum(1 for fid in RUPEE for form in "ERC"
                     if plan(("EC", 11), INDEX[fid], form, True) == "rupee_suffix")
        self.assertGreater(gained, 0)
        self.assertEqual(sum(acc["numeric_literal_v2"][f]["correct"] - acc["numeric_literal_v1"][f]["correct"] for f in "ERC"),
                         gained)
        for key in CHECKPOINTS:
            if key != ("EC", 11):
                name = A.checkpoint_name(key)
                self.assertEqual(self.result["endpoints"]["numeric_literal_v1"]["accuracy"][name],
                                 self.result["endpoints"]["numeric_literal_v2"]["accuracy"][name])

    def test_per_seed_mcnemar_counts(self):
        rows = self.result["endpoints"]["strict"]["per_seed"]["delta_C"]["seeds"]
        for s in SEEDS:
            a = [strict_value(plan(("EC", s), j, "C", f["family_id"] in RUPEE)) for j, f in enumerate(FAMILIES)]
            b = [strict_value(plan(("ER", s), j, "C", f["family_id"] in RUPEE)) for j, f in enumerate(FAMILIES)]
            first_only = sum(x and not z for x, z in zip(a, b))
            second_only = sum(z and not x for x, z in zip(a, b))
            self.assertEqual((rows[str(s)]["first_only"], rows[str(s)]["second_only"]), (first_only, second_only))
            self.assertEqual(Fraction(rows[str(s)]["mcnemar_exact_p_exact"]), A.mcnemar_exact(first_only, second_only))
            self.assertEqual(rows[str(s)]["estimate"], Fraction(first_only - second_only, 40))

    def test_labels_come_from_strict_unrounded_bounds(self):
        strict = self.result["endpoints"]["strict"]
        primary = strict["estimands"]["delta_C"]
        self.assertEqual(strict["decision_label"], A.decision_label(primary["lower"], primary["upper"]))
        self.assertIsNone(self.result["endpoints"]["numeric_literal_v1"]["decision_label"])
        self.assertIsNone(self.result["endpoints"]["numeric_literal_v2"]["decision_label"])
        for name in A.RETENTION:
            e = strict["estimands"][name]
            self.assertEqual(strict["retention_labels"][name], A.retention_label(e["lower"], e["upper"], strict["decision_label"]))

    def test_bootstrap_determinism(self):
        rng = random.Random(101)
        first = [rng.randrange(40) for _ in range(40)]
        indices = A.bootstrap_indices(40)
        self.assertEqual(len(indices), 10000)
        self.assertEqual(indices[0], first)
        self.assertEqual(indices, A.bootstrap_indices(40))
        again = A.analyze(A.assemble(DEV, dict(CHECKPOINTS)), "not_fired")
        self.assertEqual(A.to_json(again), A.to_json(self.result))

    def test_pairing_one_index_sequence_whole_family_records(self):
        for endpoint in A.ENDPOINTS:
            est = self.result["endpoints"][endpoint]["estimands"]
            # S3 per family before averaging, same resampled families as Δ_C and Δ_R in every resample.
            self.assertEqual(est["S3"]["_sums"], [c - r for c, r in zip(est["delta_C"]["_sums"], est["delta_R"]["_sums"])])
        # Identical arms paired by family give a zero-width interval; unpaired resampling would not.
        y = {key: expected_y(key, "strict") for key in CHECKPOINTS}
        for s in SEEDS:
            y[("EC", s)] = {fid: dict(y[("ER", s)][fid]) for fid in INDEX}
        nums = A.family_numerators(y, list(INDEX), list(SEEDS))
        summary = A.interval_summary(nums["delta_C"], 3, A.bootstrap_indices(40), 2)
        self.assertEqual((summary["estimate"], summary["lower"], summary["upper"]), (0, 0, 0))
        self.assertTrue(summary["degenerate"])
        self.assertEqual(A.decision_label(summary["lower"], summary["upper"]), A.NULL)  # L exactly 0 through the pipeline

    def test_pairing_by_family_id_not_position(self):
        y = {key: expected_y(key, "strict") for key in CHECKPOINTS}
        ids = list(INDEX)
        shuffled = {key: dict(reversed(list(v.items()))) for key, v in y.items()}
        self.assertEqual(A.family_numerators(y, ids, list(SEEDS)), A.family_numerators(shuffled, ids, list(SEEDS)))
        # Input order of the runs does not matter either.
        reordered = dict(reversed(list(CHECKPOINTS.items())))
        self.assertEqual(A.to_json(A.analyze(A.assemble(DEV, reordered), "not_fired")), A.to_json(self.result))

    def test_outputs_written_and_holm_only_on_request(self):
        out = self.out()
        result = A.run_analysis(DEV, dict(CHECKPOINTS), "not_fired", out)
        self.assertIsNone(result["endpoints"]["strict"]["holm"])
        data = json.loads((out / "phase2_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["endpoints"]["strict"]["decision_label"], result["endpoints"]["strict"]["decision_label"])
        text = (out / "phase2_analysis.md").read_text(encoding="utf-8")
        self.assertIn("DEV RUNS", text)
        self.assertIn("Holm correction not requested", text)
        held = A.analyze(self.study, "not_fired", holm_requested=True)["endpoints"]["strict"]["holm"]
        self.assertEqual(set(held), set(A.HOLM_FAMILY))

    def test_ceiling_flag_suffix_and_order(self):
        out = self.out()
        result = A.run_analysis(DEV, dict(CHECKPOINTS), "fired", out)
        label = result["endpoints"]["strict"]["decision_label"]
        self.assertTrue(label.endswith(" (ceiling-limited)"))
        text = (out / "phase2_analysis.md").read_text(encoding="utf-8")
        self.assertLess(text.index("Precision:"), text.index("Decision label"))
        self.assertLess(text.index("## S2"), text.index("Decision label"))
        with self.assertRaises(A.AnalysisError):
            A.analyze(self.study, "maybe")

    def test_cli(self):
        out = self.out()
        args = ["--dataset", str(DEV), "--unchanged", CHECKPOINTS[(A.UNCHANGED, None)], "--ceiling-flag", "not_fired",
                "--out", str(out)]
        for (arm, seed), path in CHECKPOINTS.items():
            if arm != A.UNCHANGED:
                args += ["--run", f"{arm}:{seed}={path}"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(A.main(args), 0)
            self.assertEqual(A.main(args), 2)  # refuses to overwrite
        self.assertIn("REFUSED", err.getvalue())


class RefusalTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)

    def test_refuses_dataset_not_final_test_or_dev(self):
        other = self.tmp / "dev_reformatted.json"
        other.write_text(json.dumps(FAMILIES, indent=2, ensure_ascii=False), encoding="utf-8")  # same content, other bytes
        with self.assertRaisesRegex(A.AnalysisError, "neither the pre-registered FINAL_TEST nor the DEV hash"):
            A.assemble(other, dict(CHECKPOINTS))
        with self.assertRaisesRegex(A.AnalysisError, "neither"):
            A.load_frozen_dataset(ROOT / "phase2" / "train_A.v2.json")
        self.assertEqual(set(A.DATASET_SHA256), {"FINAL_TEST", "DEV"})

    def copy_run(self, key):
        target = self.tmp / "copy"
        shutil.copytree(CHECKPOINTS[key], target)
        return target

    def test_refuses_run_whose_snapshot_differs_from_frozen_file(self):
        target = self.copy_run(("ER", 11))
        dataset = json.loads((target / "dataset.json").read_text(encoding="utf-8"))
        dataset["families"][0]["forms"]["C"]["text"] += " (edited)"
        engine.write(target / "dataset.json", dataset)
        manifest = json.loads((target / "run_manifest.json").read_text(encoding="utf-8"))
        engine.write(target / "run_manifest.json", dict(manifest, dataset_sha256=engine.digest(dataset)))
        checkpoints = dict(CHECKPOINTS)
        checkpoints[("ER", 11)] = str(target)
        with self.assertRaisesRegex(A.AnalysisError, "Refused"):
            A.assemble(DEV, checkpoints)
        engine.write(target / "run_manifest.json", manifest)  # snapshot no longer matches its own manifest
        with self.assertRaisesRegex(A.AnalysisError, "dataset snapshot does not match manifest"):
            A.assemble(DEV, checkpoints)

    def test_refuses_tampered_scores_and_scorer(self):
        target = self.copy_run(("EE", 22))
        path = sorted((target / "journal").glob("*.json"))[0]
        record = json.loads(path.read_text(encoding="utf-8"))
        engine.write(path, dict(record, correct=not record["correct"]))
        with self.assertRaisesRegex(A.AnalysisError, "checksum corruption"):
            A.load_run(target)
        engine.write(path, record)
        (target / "source" / "scorer_v1.py").write_text("# changed\n", encoding="utf-8")
        with self.assertRaisesRegex(A.AnalysisError, "frozen scorer"):
            A.load_run(target)

    def test_refuses_broken_design(self):
        missing = {k: v for k, v in CHECKPOINTS.items() if k != ("EC", 33)}
        with self.assertRaisesRegex(A.AnalysisError, "all three arms"):
            A.assemble(DEV, missing)
        same = dict(CHECKPOINTS)
        same[("EC", 33)] = CHECKPOINTS[("ER", 33)]
        with self.assertRaisesRegex(A.AnalysisError, "given twice"):
            A.assemble(DEV, same)
        bad_seed = {(k[0], 99 if k[1] == 33 else k[1]): v for k, v in CHECKPOINTS.items()}
        with self.assertRaisesRegex(A.AnalysisError, "Seeds"):
            A.assemble(DEV, bad_seed)
        with self.assertRaises(A.AnalysisError):
            A.parse_checkpoints("u", ["XX:11=path"])

    def test_final_test_requires_pinned_revision(self):
        config = engine.default_config("pilot_b")
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
        A.check_config(config, "DEV")
        with self.assertRaisesRegex(A.AnalysisError, "pinned Qwen3-4B revision"):
            A.check_config(config, "FINAL_TEST")
        config.update(model_revision=A.QWEN_REVISION, tokenizer_revision=A.QWEN_REVISION)
        A.check_config(config, "FINAL_TEST")
        with self.assertRaisesRegex(A.AnalysisError, "max_new_tokens"):
            A.check_config(dict(config, max_new_tokens=512), "FINAL_TEST")

    def test_incomplete_run_suppresses_headline(self):
        partial = make_run(self.tmp / "partial", (A.UNCHANGED, None), max_items=5)
        checkpoints = dict(CHECKPOINTS)
        checkpoints[(A.UNCHANGED, None)] = str(partial)
        result = A.analyze(A.assemble(DEV, checkpoints), "not_fired")
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertNotIn("endpoints", result)
        self.assertIn("suppressed", A.markdown(result))


class LabelTests(unittest.TestCase):
    pp = A.PP

    def label(self, lo, hi):
        return A.decision_label(Fraction(lo) * self.pp, Fraction(hi) * self.pp)

    def test_decision_label_boundaries(self):
        tiny = Fraction(1, 10 ** 9)
        self.assertEqual(self.label(0, 3), A.NULL)                     # L exactly 0
        self.assertEqual(self.label(0, 0), A.NULL)
        self.assertEqual(self.label(0, 5), A.INCONCLUSIVE)             # L exactly 0, U exactly 5
        self.assertEqual(self.label(-1, 5), A.INCONCLUSIVE)            # U exactly 5
        self.assertEqual(self.label(-1, 5 - tiny), A.NULL)
        self.assertEqual(self.label(5, 9), A.SUPPORT)                  # L exactly 5
        self.assertEqual(self.label(5 + tiny, 9), A.USEFUL)
        self.assertEqual(self.label(tiny, 4), A.SUPPORT)
        self.assertEqual(self.label(-3, 0), A.NULL)                    # U exactly 0
        self.assertEqual(self.label(-3, -tiny), A.HARM)
        self.assertEqual(A.decision_label(Fraction(1, 20), Fraction(1, 10), ceiling=True), "Support (ceiling-limited)")

    def test_labels_exhaustive_and_exclusive(self):
        grid = [Fraction(k, 2) for k in range(-16, 17)]
        for lo in grid:
            for hi in grid:
                if lo <= hi:
                    self.assertIn(self.label(lo, hi), (A.USEFUL, A.SUPPORT, A.NULL, A.HARM, A.INCONCLUSIVE))

    def test_retention_labels(self):
        r = lambda lo, hi, primary=A.NULL: A.retention_label(Fraction(lo) * self.pp, Fraction(hi) * self.pp, primary)
        self.assertEqual(r(-2, 1), "retention not established")       # L exactly −2 is not > −2
        self.assertEqual(r(Fraction(-199, 100), 1), "retained")
        self.assertEqual(r(-5, -1), "degraded")
        self.assertEqual(r(-5, 0), "retention not established")         # U exactly 0
        self.assertEqual(r(-5, -3, A.SUPPORT), "retention trade-off")
        self.assertEqual(r(-5, -3, "Useful support (ceiling-limited)"), "retention trade-off")
        self.assertEqual(r(-5, -2, A.SUPPORT), "degraded")             # U exactly −2 is not < −2
        self.assertEqual(r(-5, -3, A.NULL), "degraded")

    def test_intervals_and_tests(self):
        self.assertAlmostEqual(100 * A.hoeffding_radius(100, 2), 27.16, places=2)
        self.assertEqual(A.mcnemar_exact(0, 5), Fraction(1, 16))
        self.assertEqual(A.mcnemar_exact(3, 3), 1)
        self.assertEqual(A.mcnemar_exact(0, 0), 1)
        self.assertEqual(A.quantile([0, 10], Fraction(1, 4)), Fraction(5, 2))
        held = A.holm({"a": Fraction(1, 100), "b": Fraction(3, 100), "c": Fraction(2, 100)})
        self.assertEqual(held["a"], (Fraction(3, 100), True))
        self.assertEqual(held["c"], (Fraction(4, 100), True))
        self.assertEqual(held["b"], (Fraction(4, 100), True))
        held = A.holm({"a": Fraction(1, 100), "b": Fraction(6, 100), "c": Fraction(3, 100)})
        self.assertEqual([held[k][1] for k in "acb"], [True, False, False])
        p = A.bootstrap_p_values(dict(_sums=[-3, -2, 0, 1, 5], _scale=100))
        self.assertEqual(p["one_sided_vs_minus2pp"], Fraction(2, 5))
        self.assertEqual(p["two_sided_vs_0"], Fraction(1))

    def test_strata_from_dev_provenance(self):
        counts = {}
        for f in FAMILIES:
            s = A.stratum(f["provenance"])
            counts[s] = counts.get(s, 0) + 1
        self.assertEqual(counts, {"keep": 10, "switch": 10, "none": 20})
        self.assertEqual(A.stratum("C KEEPS it. C SWITCHES it to English."), "unclassified")
        self.assertEqual(A.stratum("No operation-word note."), "unclassified")
        # Other authoring styles: every family classified; Pilot-B agrees with results/pilot_b/strata.py.
        for name in ("train_A.v2.json", "train_B.v2.json"):
            for f in json.loads((ROOT / "phase2" / name).read_text(encoding="utf-8")):
                self.assertNotEqual(A.stratum(f["provenance"]), "unclassified", f["family_id"])
        for f in json.loads((ROOT / "pilot_b" / "pilot_b_families.v2.json").read_text(encoding="utf-8")):
            p = f["provenance"]
            self.assertEqual(A.stratum(p), "keep" if "C KEEPS" in p else "switch" if "C SWITCHES" in p else "none")


if __name__ == "__main__":
    unittest.main()
