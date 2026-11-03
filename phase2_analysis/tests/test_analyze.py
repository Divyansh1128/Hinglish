"""Tests for phase2_analysis/analyze.py on synthetic engine runs over DEV only.

Run directories are produced by the real engine (test1_pilot/hinglish_pilot/engine.run) with a
scripted subclass of the engine's FakeBackend, on phase2/dev.v2.json wrapped exactly as the
Pilot-B notebooks wrap their data. FINAL_TEST contents are never read.
"""
import contextlib
import io
import json
import math
import statistics
import platform
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


class FailingBackend(ScriptedBackend):
    """Fails every attempt on the first DEV family's C rendering (infrastructure failure, retries exhausted)."""

    def generate(self, prepared, config, seed):
        if FAMILIES[0]["forms"]["C"]["text"] in prepared["rendered_prompt"]:
            raise RuntimeError("simulated infrastructure failure")
        return super().generate(prepared, config, seed)


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
PROXY_K = 30  # unchanged DEV C strict count used by the fixtures (proxy not fired)
FINAL_MATRIX_SHA256 = "33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1"


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
        cls.result = A.analyze(cls.study, PROXY_K)

    def out(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        return Path(temp.name) / "analysis"

    def test_dev_accepted_and_runs_verified(self):
        self.assertEqual(self.study["role"], "DEV")
        self.assertEqual(self.result["status"], "COMPLETE")
        self.assertEqual(self.result["families"], 40)
        self.assertEqual({i["kind"] for i in self.result["inputs"]}, {"directory", "zip"})
        self.assertIn(A.DEV_NOT_RESULTS, self.result["warnings"])
        self.assertIn("not results", A.DEV_NOT_RESULTS)
        self.assertFalse(self.result["results"])
        self.assertIsNone(self.result["freeze"])
        self.assertIn("NOT RESULTS", A.markdown(self.result))

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
        self.assertTrue(self.result["analysis_type"].startswith("not results: DEV fixture route"))
        self.assertEqual(strict["decision_label"],
                         A.decision_label(primary["lower"], primary["upper"], primary["degenerate"]))
        self.assertIsNone(self.result["endpoints"]["numeric_literal_v1"]["decision_label"])
        self.assertIsNone(self.result["endpoints"]["numeric_literal_v2"]["decision_label"])
        self.assertIsNone(self.result["endpoints"]["numeric_literal_v1"]["retention_flags"])
        self.assertEqual(set(strict["retention_flags"]), set(A.RETENTION))  # all five English contrasts
        for name in A.RETENTION:
            e = strict["estimands"][name]
            self.assertEqual(strict["retention_flags"][name],
                             A.retention_flags(e["lower"], e["upper"], e["degenerate"], strict["decision_label"],
                                               name in ("ret_E_EC_EE", "ret_E_EC_unchanged")))
            if name not in ("ret_E_EC_EE", "ret_E_EC_unchanged"):
                self.assertIsNone(strict["retention_flags"][name]["retention_trade_off"])

    def test_bootstrap_determinism(self):
        rng = random.Random(101)
        first = [rng.randrange(40) for _ in range(40)]
        second = [rng.randrange(40) for _ in range(40)]  # row-major: row 2 continues the same stream
        indices = A.bootstrap_indices(40)
        self.assertEqual(len(indices), 10000)
        self.assertEqual(indices[:2], [first, second])
        self.assertEqual(indices, A.bootstrap_indices(40))
        boot = self.result["bootstrap"]
        self.assertEqual(boot["matrix_sha256"], A.matrix_sha256(indices))
        self.assertEqual((boot["seed"], boot["resamples"], boot["families"]), (101, 10000, 40))
        self.assertEqual(self.result["python_version"], platform.python_version())
        self.assertIn("not run", boot["crossed_family_seed_resampling"])
        again = A.analyze(A.assemble(DEV, dict(CHECKPOINTS)), PROXY_K)
        self.assertEqual(A.to_json(again), A.to_json(self.result))

    def test_matrix_shared_by_every_interval(self):
        indices = A.bootstrap_indices(40)
        ids = sorted(INDEX)
        y = {key: expected_y(key, "strict") for key in CHECKPOINTS}
        nums = A.family_numerators(y, ids, list(SEEDS))
        est = self.result["endpoints"]["strict"]["estimands"]
        for name in A.ESTIMAND_ORDER:
            self.assertEqual(est[name]["_sums"], A.resample_sums(nums[name], indices), name)
        row = self.result["endpoints"]["strict"]["per_seed"]["delta_C"]["seeds"]["22"]
        a = [y[("EC", 22)][fid]["C"] - y[("ER", 22)][fid]["C"] for fid in ids]
        self.assertEqual(row["_sums"], A.resample_sums(a, indices))

    def test_records_sorted_by_family_id(self):
        study = dict(self.study, families=list(reversed(self.study["families"])))
        self.assertEqual(A.to_json(A.analyze(study, PROXY_K)), A.to_json(self.result))
        # A position-based (unsorted) pairing of matrix rows would differ for an asymmetric contrast.
        y = {key: expected_y(key, "strict") for key in CHECKPOINTS}
        rev = list(reversed(sorted(INDEX)))
        nums = A.family_numerators(y, rev, list(SEEDS))["delta_C"]
        self.assertNotEqual(A.resample_sums(nums, A.bootstrap_indices(40)),
                            self.result["endpoints"]["strict"]["estimands"]["delta_C"]["_sums"])

    def test_wilson_per_checkpoint_over_n(self):
        for endpoint in A.ENDPOINTS:
            for name, forms in self.result["endpoints"][endpoint]["accuracy"].items():
                for form, a in forms.items():
                    self.assertEqual(a["n"], 40)
                    self.assertEqual(a["wilson_95"], A.wilson(a["correct"], 40))

    def test_missing_answer_in_generated_response_scores_zero(self):
        run = self.study["runs"][(A.UNCHANGED, None)]
        rows = [r for r in run["selected"].values() if r["raw_response"] == "I could not finish."]
        self.assertTrue(rows)
        y = A.outcomes(self.study)
        for r in rows:
            for endpoint in A.ENDPOINTS:
                self.assertEqual(y[endpoint][(A.UNCHANGED, None)][r["family_id"]][r["form"]], 0)
        self.assertEqual(self.result["status"], "COMPLETE")
        self.assertTrue(all(i["unresolved"] == 0 for i in self.result["inputs"]))

    def test_degeneracy_counts_tails_and_headroom_reported(self):
        strict = self.result["endpoints"]["strict"]
        y = {key: expected_y(key, "strict") for key in CHECKPOINTS}
        nums = A.family_numerators(y, sorted(INDEX), list(SEEDS))
        for name in A.ESTIMAND_ORDER:
            e = strict["estimands"][name]
            self.assertEqual(e["nonzero_family_contrasts"], sum(1 for x in nums[name] if x))
            refs = [t["reference_pp"] for t in e["bootstrap_tails"]]
            self.assertEqual(refs, [0, 5] if name == "delta_C" else [0, -2] if name in A.RETENTION else [0])
            for t in e["bootstrap_tails"]:
                self.assertEqual(t["at_or_below"], sum(1 for x in e["_sums"] if Fraction(x, 120) <= t["reference_pp"] * A.PP))
                self.assertEqual(t["at_or_above"], sum(1 for x in e["_sums"] if Fraction(x, 120) >= t["reference_pp"] * A.PP))
            self.assertEqual(e["hoeffding_bounds"], [-2, 2] if name == "S3" else [-1, 1])
        er_c = sum(y[("ER", s)][fid]["C"] for s in SEEDS for fid in INDEX) / 120
        self.assertAlmostEqual(strict["ER_C_headroom"], 1 - er_c)
        text = A.markdown(self.result)
        self.assertIn("E+R C headroom", text)
        self.assertIn("Non-zero family contrasts", text)
        self.assertIn("Bootstrap tails", text)

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
        summary = A.interval_summary(nums["delta_C"], 3, A.bootstrap_indices(40))
        self.assertEqual((summary["estimate"], summary["lower"], summary["upper"]), (0, 0, 0))
        self.assertTrue(summary["degenerate"])
        self.assertEqual(summary["nonzero_family_contrasts"], 0)
        # Amendment 1 item 2: no longer an 'Informative null'.
        self.assertEqual(A.decision_label(summary["lower"], summary["upper"], summary["degenerate"]), A.DEGENERATE)

    def test_pairing_by_family_id_not_position(self):
        y = {key: expected_y(key, "strict") for key in CHECKPOINTS}
        ids = list(INDEX)
        shuffled = {key: dict(reversed(list(v.items()))) for key, v in y.items()}
        self.assertEqual(A.family_numerators(y, ids, list(SEEDS)), A.family_numerators(shuffled, ids, list(SEEDS)))
        # Input order of the runs does not matter either.
        reordered = dict(reversed(list(CHECKPOINTS.items())))
        self.assertEqual(A.to_json(A.analyze(A.assemble(DEV, reordered), PROXY_K)), A.to_json(self.result))

    def test_outputs_written_and_no_holm(self):
        out = self.out()
        result = A.run_analysis(DEV, dict(CHECKPOINTS), PROXY_K, out)
        self.assertNotIn("holm", result["endpoints"]["strict"])
        self.assertFalse(hasattr(A, "holm") or hasattr(A, "bootstrap_p_values") or hasattr(A, "HOLM_FAMILY"))
        data = json.loads((out / "phase2_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["endpoints"]["strict"]["decision_label"], result["endpoints"]["strict"]["decision_label"])
        self.assertNotIn("\"holm", json.dumps(data).casefold())  # no Holm key anywhere
        text = (out / "phase2_analysis.md").read_text(encoding="utf-8")
        self.assertIn("DEV RUNS", text)
        self.assertIn("no Holm", text)
        self.assertIn("descriptive", result["secondaries"])

    def test_ceiling_risk_proxy_renamed_and_primary_first(self):
        texts, labels = {}, {}
        for k in (37, 38, 40, 0):
            out = self.out()
            result = A.run_analysis(DEV, dict(CHECKPOINTS), k, out)
            proxy = result["ceiling_risk_proxy"]
            self.assertEqual(proxy["name"], "high unchanged-DEV accuracy (ceiling-risk proxy)")
            self.assertEqual(proxy["fired"], k >= 38)                       # boundary: 37 no, 38 yes
            self.assertEqual((proxy["correct"], proxy["n"]), (k, 40))
            self.assertEqual(proxy["wilson_95"], A.wilson(k, 40))
            self.assertAlmostEqual(proxy["dev_headroom"], 1 - k / 40)
            labels[k] = result["endpoints"]["strict"]["decision_label"]
            texts[k] = (out / "phase2_analysis.md").read_text(encoding="utf-8")
            text = texts[k]
            self.assertLess(text.index("## Primary: Δ_C"), text.index("ceiling-risk proxy"))
            self.assertLess(text.index("Decision label"), text.index("## S2"))
            self.assertLess(text.index("## S2"), text.index("## S1"))
            self.assertNotIn("ceiling-limited", text)
        self.assertEqual(len(set(labels.values())), 1)  # the proxy never changes the label
        self.assertIn("**fired**", texts[38])
        self.assertIn("**not fired**", texts[37])
        for bad in (41, -1, "38", True, 38.0, None):
            with self.assertRaises(A.AnalysisError):
                A.analyze(self.study, bad)

    def test_cli(self):
        out = self.out()
        args = ["--dataset", str(DEV), "--unchanged", CHECKPOINTS[(A.UNCHANGED, None)], "--ceiling-risk-proxy-k", "30",
                "--out", str(out)]
        for (arm, seed), path in CHECKPOINTS.items():
            if arm != A.UNCHANGED:
                args += ["--run", f"{arm}:{seed}={path}"]
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(A.main(args), 0)
            self.assertEqual(A.main(args), 2)  # refuses to overwrite
            with self.assertRaises(SystemExit):
                A.main(args + ["--holm"])  # the flag no longer exists
            with self.assertRaises(SystemExit):
                A.main([a for a in args if a not in ("--ceiling-risk-proxy-k", "30")] + ["--ceiling-flag", "fired"])
        self.assertIn("REFUSED", err.getvalue())

    def test_reduced_s_descriptive_without_labels(self):
        for seeds in ((11,), (11, 22), (22, 33)):
            checkpoints = {k: v for k, v in CHECKPOINTS.items() if k[0] == A.UNCHANGED or k[1] in seeds}
            study = A.assemble(DEV, checkpoints)
            result = A.analyze(study, PROXY_K)
            S = len(seeds)
            with self.subTest(seeds=seeds):
                self.assertEqual(result["S"], S)
                self.assertEqual(result["status"], "COMPLETE")
                self.assertTrue(result["analysis_type"].startswith("not results: DEV fixture route, reduced-S"))
                self.assertTrue(any("reduced-S" in w for w in result["warnings"]))
                strict = result["endpoints"]["strict"]
                self.assertIsNone(strict["decision_label"])
                self.assertIsNone(strict["retention_flags"])
                y = {key: expected_y(key, "strict") for key in checkpoints}
                for name, form, first, second, _ in A.DIFFERENCES:
                    total = Fraction(0)
                    for fid in INDEX:
                        a = Fraction(sum(y[(first, s)][fid][form] for s in seeds), S)  # 1/S averaging
                        b = y[(A.UNCHANGED, None)][fid][form] if second == A.UNCHANGED else \
                            Fraction(sum(y[(second, s)][fid][form] for s in seeds), S)
                        total += a - b
                    self.assertEqual(strict["estimands"][name]["estimate"], total / 40)
                text = A.markdown(result)
                self.assertNotIn("**Decision label", text)
                self.assertIn("No decision label", text)


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
        config = engine.default_config(A.FINAL_TEST_MODE)
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
        A.check_config(config, "DEV")
        with self.assertRaisesRegex(A.AnalysisError, "pinned Qwen3-4B revision"):
            A.check_config(config, "FINAL_TEST")
        config.update(model_revision=A.QWEN_REVISION, tokenizer_revision=A.QWEN_REVISION)
        A.check_config(config, "FINAL_TEST")
        with self.assertRaisesRegex(A.AnalysisError, "max_new_tokens"):
            A.check_config(dict(config, max_new_tokens=512), "FINAL_TEST")
        with self.assertRaisesRegex(A.AnalysisError, "mode"):
            A.check_config(dict(config, mode="phase2_dev"), "FINAL_TEST")
        with self.assertRaisesRegex(A.AnalysisError, "mode"):
            A.check_config(dict(config, mode="pilot_b"), "FINAL_TEST")

    def test_incomplete_run_suppresses_headline(self):
        partial = make_run(self.tmp / "partial", (A.UNCHANGED, None), max_items=5)
        checkpoints = dict(CHECKPOINTS)
        checkpoints[(A.UNCHANGED, None)] = str(partial)
        result = A.analyze(A.assemble(DEV, checkpoints), PROXY_K)
        self.assertEqual(result["status"], "INCOMPLETE")
        self.assertEqual(result["unresolved_items"], 120 - 5)
        self.assertNotIn("endpoints", result)
        self.assertIn("suppressed", A.markdown(result))

    def test_one_unresolved_item_after_exhausted_retries_suppresses_primary(self):
        dataset, splits = wrapped_dev()
        config = engine.default_config("pilot_b")
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
        root = self.tmp / "failing"
        engine.run(root, dataset, splits, config, FailingBackend(("EC", 33)))
        run = A.load_run(root)
        self.assertEqual((run["complete"], run["unresolved"], run["attempts"]), (False, 1, 121))  # 1 + 1 retry
        checkpoints = dict(CHECKPOINTS)
        checkpoints[("EC", 33)] = str(root)
        result = A.analyze(A.assemble(DEV, checkpoints), PROXY_K)
        self.assertEqual((result["status"], result["unresolved_items"]), ("INCOMPLETE", 1))
        self.assertNotIn("endpoints", result)
        text = A.markdown(result)
        self.assertNotIn("Decision label", text)
        self.assertIn("unresolved", text)

    def test_s_zero_refused(self):
        with self.assertRaisesRegex(A.AnalysisError, "S = 0"):
            A.assemble(DEV, {(A.UNCHANGED, None): CHECKPOINTS[(A.UNCHANGED, None)]})


class LabelTests(unittest.TestCase):
    pp = A.PP

    def label(self, lo, hi, degenerate=False):
        return A.decision_label(Fraction(lo) * self.pp, Fraction(hi) * self.pp, degenerate)

    def test_decision_label_boundaries(self):
        tiny = Fraction(1, 10 ** 9)
        self.assertEqual(self.label(0, 3), A.NULL)                     # L exactly 0
        self.assertEqual(self.label(0, 5), A.INCONCLUSIVE)             # L exactly 0, U exactly 5
        self.assertEqual(self.label(-1, 5), A.INCONCLUSIVE)            # U exactly 5
        self.assertEqual(self.label(-1, 5 - tiny), A.NULL)
        self.assertEqual(self.label(5, 9), A.SUPPORT)                  # L exactly 5
        self.assertEqual(self.label(5 + tiny, 9), A.USEFUL)
        self.assertEqual(self.label(tiny, 4), A.SUPPORT)
        self.assertEqual(self.label(-3, 0), A.NULL)                    # U exactly 0
        self.assertEqual(self.label(-3, -tiny), A.HARM)

    def test_degenerate_override(self):
        self.assertEqual(A.DEGENERATE, "inconclusive—degenerate empirical interval")
        for lo, hi in ((0, 0), (3, 3), (-4, -4), (7, 7)):              # zero width: never null/support/harm
            self.assertEqual(self.label(lo, hi), A.DEGENERATE)
        for lo, hi in ((1, 9), (-3, 2), (-6, -1), (6, 8)):             # all family contrasts identical
            self.assertEqual(self.label(lo, hi, degenerate=True), A.DEGENERATE)
        # All identical non-zero contrasts (constant +1/3 per family) through the interval code.
        s = A.interval_summary([1] * 40, 3, A.bootstrap_indices(40))
        self.assertTrue(s["all_contrasts_identical"] and s["zero_width"] and s["degenerate"])
        self.assertEqual((s["lower"], s["upper"], s["nonzero_family_contrasts"]), (Fraction(1, 3), Fraction(1, 3), 40))
        self.assertEqual(A.decision_label(s["lower"], s["upper"], s["degenerate"]), A.DEGENERATE)
        # Zero width although contrasts differ (a resampling matrix that never draws family 0).
        z = A.interval_summary([3, 0, 0], 3, [[1, 2, 1]] * 50)
        self.assertEqual((z["all_contrasts_identical"], z["zero_width"], z["degenerate"]), (False, True, True))
        self.assertEqual(z["estimate"], Fraction(1, 3))  # the point estimate is still reported
        # Not degenerate: distinct values and positive width.
        d = A.interval_summary([1, 0, -1, 0], 1, A.bootstrap_indices(4))
        self.assertFalse(d["degenerate"])

    def test_labels_exhaustive_and_exclusive(self):
        grid = [Fraction(k, 2) for k in range(-16, 17)]
        for lo in grid:
            for hi in grid:
                if lo <= hi:
                    self.assertIn(self.label(lo, hi), (A.USEFUL, A.SUPPORT, A.NULL, A.HARM, A.INCONCLUSIVE, A.DEGENERATE))
                    self.assertEqual(self.label(lo, hi) == A.DEGENERATE, lo == hi)

    def flags(self, lo, hi, primary=A.NULL, eligible=True, degenerate=False):
        return A.retention_flags(Fraction(lo) * self.pp, Fraction(hi) * self.pp, degenerate, primary, eligible)

    def test_retention_flags_boundaries(self):
        tiny = Fraction(1, 10 ** 9)
        f = self.flags(-2, 1)                                           # L exactly −2 is not > −2
        self.assertFalse(f["within_margin_criterion_met"])
        self.assertEqual(f["flags"], [A.NOT_ESTABLISHED])
        self.assertTrue(self.flags(-2 + tiny, 1)["within_margin_criterion_met"])
        self.assertFalse(self.flags(-5, 0)["loss_detected"])           # U exactly 0
        self.assertTrue(self.flags(-5, -tiny)["loss_detected"])
        self.assertFalse(self.flags(-5, -2)["loss_beyond_margin"])      # U exactly −2
        self.assertTrue(self.flags(-5, -2 - tiny)["loss_beyond_margin"])
        # Independent flags: within-margin and loss detected together.
        both = self.flags(Fraction(-3, 2), Fraction(-1, 2))
        self.assertEqual(both["flags"], [A.WITHIN, A.LOSS])
        self.assertEqual(self.flags(-5, -3)["flags"], [A.LOSS, A.BEYOND])

    def test_retention_trade_off(self):
        tiny = Fraction(1, 10 ** 9)
        for primary in (A.SUPPORT, A.USEFUL):
            f = self.flags(-5, -3, primary)
            self.assertTrue(f["retention_trade_off"])
            self.assertEqual(f["flags"], [A.LOSS, A.BEYOND, A.TRADE_OFF])
            self.assertFalse(self.flags(-5, -2, primary)["retention_trade_off"])        # U exactly −2
            self.assertTrue(self.flags(-5, -2 - tiny, primary)["retention_trade_off"])
            self.assertIsNone(self.flags(-5, -3, primary, eligible=False)["retention_trade_off"])
        for primary in (A.NULL, A.HARM, A.INCONCLUSIVE, A.DEGENERATE):
            self.assertFalse(self.flags(-5, -3, primary)["retention_trade_off"])

    def test_retention_degenerate_override(self):
        for lo, hi, degenerate in ((0, 0, False), (-3, -3, False), (-1, 1, True), (-5, -3, True)):
            f = self.flags(lo, hi, A.SUPPORT, degenerate=degenerate)
            self.assertEqual(f["override"], A.DEGENERATE)
            self.assertEqual(f["flags"], [A.DEGENERATE])
            self.assertFalse(f["within_margin_criterion_met"] or f["loss_detected"] or f["loss_beyond_margin"]
                             or f["retention_trade_off"])

    def test_quantile_wald_hoeffding(self):
        values = list(range(10000))
        self.assertEqual(A.quantile(values, Fraction(25, 1000)), Fraction(249975, 1000))   # h = 9999 * .025
        self.assertEqual(A.quantile(values, Fraction(975, 1000)), Fraction(9749025, 1000))
        self.assertEqual(A.quantile([0, 10], Fraction(1, 4)), Fraction(5, 2))
        self.assertEqual(A.Z95, 1.959963984540054)
        nums = [1, 0, 0, -1, 1]
        s = A.interval_summary(nums, 1, A.bootstrap_indices(5, resamples=50))
        half = 1.959963984540054 * statistics.stdev([1.0, 0.0, 0.0, -1.0, 1.0]) / math.sqrt(5)   # ddof 1
        self.assertAlmostEqual(s["wald_95_pp"][0], 100 * (0.2 - half))
        self.assertAlmostEqual(s["wald_95_pp"][1], 100 * (0.2 + half))
        self.assertAlmostEqual(100 * A.hoeffding_radius(100, 2), 100 * 2 * math.sqrt(math.log(40) / 200))
        self.assertAlmostEqual(100 * A.hoeffding_radius(100, 2), 27.16, places=2)
        self.assertAlmostEqual(100 * A.hoeffding_radius(100, 4), 54.32, places=2)
        # Clipping to [a, b].
        self.assertEqual(A.hoeffding_interval(Fraction(9, 10), 100, (-1, 1))[0][1], 1.0)
        self.assertEqual(A.hoeffding_interval(Fraction(-9, 10), 100, (-1, 1))[0][0], -1.0)
        self.assertEqual(A.hoeffding_interval(Fraction(-18, 10), 100, (-2, 2))[0][0], -2.0)
        self.assertAlmostEqual(A.hoeffding_interval(Fraction(18, 10), 100, (-2, 2))[0][0], 1.8 - 0.5432, places=3)
        clipped = A.interval_summary([1] * 100, 1, A.bootstrap_indices(100, resamples=20))
        self.assertEqual(clipped["hoeffding_95_pp"][1], 100.0)
        s3 = A.interval_summary([-2] * 100, 1, A.bootstrap_indices(100, resamples=20), A.S3_BOUNDS)
        self.assertEqual(s3["hoeffding_95_pp"][0], -200.0)
        self.assertAlmostEqual(s3["hoeffding_radius_pp"], 54.32, places=2)

    def test_matrix_for_final_test_size(self):
        m = A.bootstrap_indices(100)
        rng = random.Random(101)
        self.assertEqual((len(m), {len(r) for r in m}), (10000, {100}))
        self.assertEqual(m[0], [rng.randrange(100) for _ in range(100)])
        self.assertEqual(m[-1][-1], [rng.randrange(100) for _ in range(100 * 9999)][-1])
        self.assertEqual(A.matrix_sha256(m), FINAL_MATRIX_SHA256)  # pinned for the pre-registered 10,000 x 100 matrix
        self.assertEqual(A.FINAL_TEST_MATRIX_SHA256, FINAL_MATRIX_SHA256)
        self.assertEqual(A.matrix_sha256([[1, 2], [3, 40]]),
                         __import__("hashlib").sha256(b"1,2\n3,40\n").hexdigest())

    def test_tails(self):
        s = A.interval_summary([1, 0, 0, -1], 1, [[0, 0, 0, 0], [1, 1, 1, 1], [3, 3, 3, 3], [0, 1, 2, 3]], references=(0, -2))
        t0, t2 = s["bootstrap_tails"]
        self.assertEqual((t0["at_or_below"], t0["at_or_above"], t0["resamples"]), (3, 3, 4))  # ties count in both tails
        self.assertEqual((t2["at_or_below"], t2["at_or_above"]), (1, 3))                      # −4/4 = −100 pp <= −2 pp

    def test_mcnemar(self):
        self.assertEqual(A.mcnemar_exact(0, 5), Fraction(1, 16))
        self.assertEqual(A.mcnemar_exact(3, 3), 1)
        self.assertEqual(A.mcnemar_exact(0, 0), 1)

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
