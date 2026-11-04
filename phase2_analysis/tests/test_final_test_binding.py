"""FINAL_TEST input binding (PREREGISTRATION Amendment 2 item 7, Amendment 3 item 3; Sol review R1, R2 and re-review
B1, B3), on DEV fixtures only.

FINAL_TEST contents are never read. The FINAL_TEST loader (``analyze.load_frozen_dataset``) is mocked to return
the 40 DEV families under the FINAL_TEST role and hash, and the dataset path handed to the analysis does not
exist. Engine runs are produced by the real engine in mode ``phase2_final_test`` with a scripted backend; only
the engine's own 100-family FINAL_TEST data validation is mocked so that the DEV families can be used.
The freeze (``ADAPTERS_FROZEN.md``) and implementation manifest are synthetic fixtures in their real formats.

Two kinds of fixture run exist, both produced on a CPU without any model:
* ``RUNS`` (``FinalTestFixtureBackend``): honest CPU-fixture metadata (``hardware='none: ...'``,
  ``gpu_verified=False``, the local package versions). The FINAL_TEST route must refuse them (B1).
* ``SIM`` (``SimulatedT4Backend`` + ``simulated_environment``): SIMULATED compliant T4 metadata and pinned
  package versions, clearly labelled as such inside the metadata, used to exercise the same study validator on
  compliant input and on deliberately noncompliant edits of it. No GPU result is claimed.
The unchanged-model DEV baseline is a SIMULATED-compliant phase2_dev run on DEV, exported as the engine's ZIP.
"""
import hashlib
import json
import shutil
import tempfile
import unittest
import uuid
from pathlib import Path
from unittest import mock

import test_analyze as base  # same directory (unittest discover -s phase2_analysis/tests)
from phase2_analysis import analyze as A
from test1_pilot.hinglish_pilot import engine
from test1_pilot.hinglish_pilot import report as engine_report

ROOT = Path(__file__).resolve().parents[2]
NOT_READ = Path("/nonexistent/final_test.v3.json")  # the mocked loader never opens a file
SEEDS = (11, 22, 33)
RESERVE = 44
LLAMA = "meta-llama/Llama-3.2-3B-Instruct"


def sha(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


SHARDS = {f"model-0000{i}-of-00003.safetensors": sha(f"fixture shard {i}") for i in (1, 2, 3)}
TEMPLATE = sha("fixture chat template")


# The section-2 stack as recorded in phase2/IMPLEMENTATION_MANIFEST.md "dependencies" (evaluation + adapter_evaluation).
DEPENDENCIES = {"evaluation": {"torch": "2.11.0+cu130", "transformers": "4.51.3", "bitsandbytes": "0.50.2",
                               "accelerate": "1.6.0", "huggingface-hub": "0.30.2", "tokenizers": "0.21.1",
                               "safetensors": "0.5.3"},
                "adapter_evaluation": {"peft": "0.15.2"}}
PINNED = {name: version for group in DEPENDENCIES.values() for name, version in group.items()}
SIMULATED_LABEL = "SIMULATED compliant T4 metadata written by a CPU unit test; no GPU and no model were used"
SIMULATED_QUANTIZATION = {"quant_method": "bitsandbytes", "load_in_4bit": True, "load_in_8bit": False,
                          "bnb_4bit_quant_type": "nf4", "bnb_4bit_use_double_quant": True,
                          "bnb_4bit_compute_dtype": "float16", "bnb_4bit_quant_storage": "uint8"}


def simulated_environment(*args, **kwargs):
    """engine.environment() with the pinned package versions substituted (SIMULATED; the CPU has no torch)."""
    environment = REAL_ENVIRONMENT(*args, **kwargs)
    environment["packages"] = dict(environment["packages"], **PINNED)
    environment["simulated_fixture"] = SIMULATED_LABEL
    return environment


REAL_ENVIRONMENT = engine.environment


def adapter_entry(arm, seed, attempt=1):
    return dict(arm=arm, seed=seed, attempt=attempt, adapter_model_sha256=sha(f"adapter model {arm} {seed} {attempt}"),
                adapter_config_sha256=sha(f"adapter config {arm} {seed} {attempt}"))


class FinalTestFixtureBackend(base.ScriptedBackend):
    """Scripted answers; metadata shaped like hf_backend.HFBackend's Phase-2 metadata (no model is loaded)."""

    def __init__(self, key, adapter):
        super().__init__(key)
        self.metadata = dict(backend="huggingface", hardware="none: scripted test fixture on DEV families",
                             model_revision=A.QWEN_REVISION, tokenizer_revision=A.QWEN_REVISION,
                             chat_template_sha256=TEMPLATE, gpu_verified=False, adapter=adapter,
                             base_weight_shards_sha256=dict(SHARDS))


class SimulatedT4Backend(FinalTestFixtureBackend):
    """SIMULATED compliant execution metadata shaped like hf_backend.HFBackend on a Tesla T4 (CPU test; no GPU)."""

    def __init__(self, key, adapter):
        super().__init__(key, adapter)
        self.metadata.update(hardware="Tesla T4", gpu_total_bytes=15828320256, capability=[7, 5], torch_cuda="13.0",
                             quantization=dict(SIMULATED_QUANTIZATION), attention=A.PRESCRIBED_ATTENTION,
                             compute_dtype="float16", gpu_verified=True, simulated_fixture=SIMULATED_LABEL)


def final_test_config(adapter, mode=A.FINAL_TEST_MODE):
    config = engine.default_config(mode)
    config.update(model_revision=A.QWEN_REVISION, tokenizer_revision=A.QWEN_REVISION, adapter=adapter)
    return config


def make_run(root, key, adapter, mode=A.FINAL_TEST_MODE, simulated=False, backend=None, max_items=None):
    dataset, splits = base.wrapped_dev()
    backend = backend or (SimulatedT4Backend if simulated else FinalTestFixtureBackend)
    with mock.patch.object(engine, "validate", lambda *args, **kwargs: None), \
            mock.patch.object(engine, "environment", simulated_environment if simulated else REAL_ENVIRONMENT):
        # validate is mocked because the FINAL_TEST mode expects 100 families; DEV has 40.
        engine.run(root, dataset, splits, final_test_config(adapter, mode), backend(key, adapter), max_items=max_items)
    return root


def implementation_manifest_document():
    """The fields of phase2/IMPLEMENTATION_MANIFEST.md that the analysis binds to, for the current engine files."""
    folder = ROOT / "test1_pilot" / "hinglish_pilot"
    group = [f"test1_pilot/hinglish_pilot/{p.name}" for p in sorted(folder.glob("*.py"))]
    return {"schema": A.IMPLEMENTATION_SCHEMA,
            "groups": {"engine": group},
            "files": {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in group},
            "prompt": {"version": engine.PROMPT_VERSION, "instruction_sha256": sha(engine.INSTRUCTION)},
            "model": {"id": A.QWEN_ID, "revision": A.QWEN_REVISION, "tokenizer_revision": A.QWEN_REVISION,
                      "chat_template": {"digest": TEMPLATE}},
            "generation_config": {"engine_config_sha256": {
                "final_test": engine.digest(final_test_config(None)),
                "dev": engine.digest(final_test_config(None, A.DEV_MODE))},
                "decoding": {"max_infrastructure_retries": 1}},
            "dependencies": json.loads(json.dumps(DEPENDENCIES))}


def frozen_document(implementation_sha, seeds=SEEDS, slots=None, adapters=None, baseline_sha=None):
    slots = slots or seeds
    S = len(seeds)
    return {"schema": "phase2-adapters-frozen-3", "base_model": A.QWEN_ID, "base_revision": A.QWEN_REVISION,
            "baseline_dev_results_zip_sha256": baseline_sha or BASELINE_SHA,
            "implementation_manifest_sha256": implementation_sha, "exposure_order_file_sha256": sha("exposure order"),
            "base_weight_shards_sha256": dict(SHARDS), "attempt_log_sha256": sha("attempt log"),
            "training_logs_sha256": {f"{arm}-s{s}/attempt-1/train_report.json": sha(f"report {arm} {s}")
                                     for s in seeds for arm in sorted(A.ARMS)},
            "retained_seeds": [{"slot": slot, "seed": seed} for slot, seed in zip(slots, seeds)], "S": S,
            "confirmatory": S == 3, "descriptive_only": S < 3,
            "adapters": adapters if adapters is not None else
            [adapter_entry(arm, s) for s in seeds for arm in sorted(A.ARMS)]}


def fenced(document, title):
    return f"# {title} (test fixture)\n\n```json\n" + json.dumps(document, indent=2) + "\n```\n"


def final_test_loader(path):
    """Mock of the FINAL_TEST loader: DEV families under the FINAL_TEST role and hash; no file is read."""
    return "FINAL_TEST", A.DATASET_SHA256["FINAL_TEST"], [dict(f) for f in base.FAMILIES]


def resign(run_dir, **changes):
    """Change config fields of a run and re-sign its manifest and journal (an archive a modified engine could write)."""
    config = engine.read(run_dir / "experiment_config.json")
    config.update(changes)
    engine.write(run_dir / "experiment_config.json", config)
    new = engine.digest(config)
    manifest = engine.read(run_dir / "run_manifest.json")
    manifest["config_sha256"] = new
    if "mode" in changes:
        manifest["mode"] = changes["mode"]
    engine.write(run_dir / "run_manifest.json", manifest)
    for path in sorted((run_dir / "journal").glob("*.json")):
        record = engine.read(path)
        record.pop("record_sha256")
        record["config_sha256"] = new
        record["record_sha256"] = engine.digest(record)
        engine.write(path, record)


TMP = None
RUNS = {}  # (arm, seed) / (UNCHANGED, None) -> FINAL_TEST-mode run with honest CPU-fixture metadata (refused: B1)
SIM = {}  # the same runs with SIMULATED compliant T4 metadata and pinned package versions
EXTRA = {}  # odd (simulated-compliant) runs used by refusal tests
BASELINE = None  # SIMULATED-compliant unchanged-model phase2_dev run on DEV, as the engine's results ZIP
BASELINE_SHA = None


def setUpModule():
    global TMP, BASELINE, BASELINE_SHA
    TMP = tempfile.TemporaryDirectory()
    root = Path(TMP.name)
    for runs, simulated, prefix in ((RUNS, False, "cpu"), (SIM, True, "sim")):
        runs[(A.UNCHANGED, None)] = make_run(root / f"{prefix}-unchanged", (A.UNCHANGED, None), None, simulated=simulated)
        for seed in SEEDS + (RESERVE,):
            for arm in A.ARMS:
                runs[(arm, seed)] = make_run(root / f"{prefix}-{arm}-{seed}", (arm, seed), adapter_entry(arm, seed),
                                             simulated=simulated)
        runs[("EC", 22)] = engine_report.export(runs[("EC", 22)])  # one input as the engine's results ZIP
    EXTRA["EC11_no_adapter"] = make_run(root / "EC-11-no-adapter", ("EC", 11), None, simulated=True)
    EXTRA["phase2_dev_mode"] = make_run(root / "unchanged-dev-mode", (A.UNCHANGED, None), None, mode=A.DEV_MODE,
                                        simulated=True)
    BASELINE = engine_report.export(make_run(root / "baseline-dev", (A.UNCHANGED, None), None, mode=A.DEV_MODE,
                                             simulated=True))
    BASELINE_SHA = hashlib.sha256(BASELINE.read_bytes()).hexdigest()


def tearDownModule():
    TMP.cleanup()


def checkpoints(seeds=SEEDS, runs=None):
    """The CPU-fixture runs (RUNS) by default; ``simulated`` gives the simulated-compliant ones."""
    runs = RUNS if runs is None else runs
    out = {(A.UNCHANGED, None): str(runs[(A.UNCHANGED, None)])}
    out.update({(arm, s): str(runs[(arm, s)]) for s in seeds for arm in A.ARMS})
    return out


def simulated(seeds=SEEDS):
    return checkpoints(seeds, SIM)


class Fixture(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.tmp = Path(temp.name)
        self.impl_doc = implementation_manifest_document()
        self.impl = self.write("IMPLEMENTATION_MANIFEST.md", fenced(self.impl_doc, "Implementation manifest"))
        self.frozen = self.write_frozen()

    def write(self, name, text):
        path = self.tmp / name
        path.write_text(text, encoding="utf-8")
        return path

    @property
    def impl_sha(self):
        return hashlib.sha256(self.impl.read_bytes()).hexdigest()

    def write_frozen(self, name="ADAPTERS_FROZEN.md", **kwargs):
        kwargs.setdefault("implementation_sha", self.impl_sha)
        return self.write(name, fenced(frozen_document(kwargs.pop("implementation_sha"), **kwargs), "Adapters frozen"))

    def assemble(self, runs, frozen="default", impl="default", baseline="default"):
        frozen = self.frozen if frozen == "default" else frozen
        impl = self.impl if impl == "default" else impl
        baseline = BASELINE if baseline == "default" else baseline
        with mock.patch.object(A, "load_frozen_dataset", side_effect=final_test_loader) as loader:
            study = A.assemble(NOT_READ, runs, frozen, impl, baseline)
        loader.assert_called_once_with(NOT_READ)
        return study

    def refused(self, pattern, runs, **kwargs):
        with self.assertRaisesRegex(A.AnalysisError, pattern):
            self.assemble(runs, **kwargs)

    def copy(self, key, name="copy"):
        target = self.tmp / name
        shutil.copytree(SIM[key], target)
        return target


class FreezeBindingTests(Fixture):
    """R1: checkpoints, retained seeds and S come from phase2/ADAPTERS_FROZEN.md."""

    def test_frozen_set_is_accepted_and_confirmatory(self):
        study = self.assemble(simulated())
        self.assertEqual((study["role"], study["seeds"], study["labels"]), ("FINAL_TEST", [11, 22, 33], True))
        result = A.analyze(study)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["results"])
        self.assertTrue(result["analysis_type"].startswith("confirmatory (S = 3"))
        self.assertEqual(result["freeze"]["sha256"], hashlib.sha256(self.frozen.read_bytes()).hexdigest())
        self.assertEqual(result["freeze"]["implementation_manifest"]["sha256"], self.impl_sha)
        self.assertEqual(result["freeze"]["baseline_dev_results_zip_sha256"], BASELINE_SHA)
        self.assertEqual(result["freeze"]["package_pins"], dict(sorted(PINNED.items())))
        self.assertEqual(result["ceiling_risk_proxy"]["correct"], base.PROXY_K)  # derived from the baseline ZIP
        self.assertIn(BASELINE_SHA, result["ceiling_risk_proxy"]["source"])
        self.assertIsNotNone(result["endpoints"]["strict"]["decision_label"])
        self.assertNotIn(A.DEV_NOT_RESULTS, result["warnings"])
        self.assertEqual({i["checkpoint"]: i["adapter"] for i in result["inputs"]}[ "EC:11"], adapter_entry("EC", 11))
        text = A.markdown(result)
        self.assertIn("ADAPTERS_FROZEN.md", text)
        self.assertNotIn("NOT RESULTS", text)

    def test_swapped_arm_inputs_are_refused(self):
        # Sol's probe: swap only the EC:11 and ER:11 input paths.
        runs = simulated()
        runs[("EC", 11)], runs[("ER", 11)] = runs[("ER", 11)], runs[("EC", 11)]
        self.refused("(EC:11: run adapter ER:11 .* frozen slot EC:11|ER:11: run adapter EC:11 .* frozen slot ER:11)", runs)
        runs = simulated()
        runs[("EE", 22)], runs[("EE", 33)] = runs[("EE", 33)], runs[("EE", 22)]  # swap across seeds
        self.refused("is not the frozen slot", runs)

    def test_trained_label_without_adapter_is_refused(self):
        runs = simulated()
        runs[("EC", 11)] = str(EXTRA["EC11_no_adapter"])
        self.refused("EC:11: no adapter loaded under a trained-arm label", runs)
        # Sol's probe: an existing-style DEV fixture run (no adapter, pilot_b mode, unpinned revision) under a
        # trained label is refused too.
        runs[("EC", 11)] = str(base.make_run(self.tmp / "dev-style", ("EC", 11)))
        self.refused("Refused", runs)

    def test_unchanged_label_with_adapter_is_refused(self):
        runs = simulated()
        runs[(A.UNCHANGED, None)] = str(SIM[("EE", RESERVE)])
        self.refused("unchanged-model run has an adapter loaded", runs)

    def test_missing_runs_are_refused(self):
        runs = simulated()
        del runs[("EC", 33)]
        self.refused(r"missing \['EC:33'\]", runs)
        # Omitting a whole frozen seed cannot silently become a reduced-S analysis.
        self.refused(r"missing \['EC:33', 'EE:33', 'ER:33'\]", simulated((11, 22)))
        runs = simulated()
        del runs[(A.UNCHANGED, None)]
        self.refused(r"missing \['unchanged'\]", runs)

    def test_extra_seed_is_refused(self):
        self.refused(r"extra or substituted \['EC:44', 'EE:44', 'ER:44'\]", simulated(SEEDS + (RESERVE,)))
        runs = simulated()
        runs[("EC", RESERVE)] = str(SIM[("EC", RESERVE)])
        self.refused(r"missing none; extra or substituted \['EC:44'\]", runs)

    def test_substituted_seed_is_refused(self):
        # A reserve triplet offered in place of a frozen seed, honestly labelled ...
        self.refused(r"missing \['EC:33', 'EE:33', 'ER:33'\]; extra or substituted \['EC:44', 'EE:44', 'ER:44'\]",
                     simulated((11, 22, RESERVE)))
        # ... or relabelled as the frozen seed.
        runs = simulated()
        for arm in A.ARMS:
            runs[(arm, 33)] = str(SIM[(arm, RESERVE)])
        self.refused("run adapter .*:44 .* is not the frozen slot .*:33", runs)

    def test_reserve_seed_and_reduced_s_come_from_the_freeze(self):
        frozen = self.write_frozen("reserve.md", seeds=(11, 22, RESERVE), slots=(11, 22, 33))
        study = self.assemble(simulated((11, 22, RESERVE)), frozen=frozen)
        self.assertEqual((study["seeds"], study["labels"]), ([11, 22, 44], True))
        self.assertTrue(any("33→44" in w for w in study["warnings"]))
        self.refused("extra or substituted", simulated(), frozen=frozen)
        # A reduced-S freeze: the descriptive report follows the freeze, not the operator.
        reduced = self.write_frozen("reduced.md", seeds=(11, 22))
        self.refused(r"extra or substituted \['EC:33', 'EE:33', 'ER:33'\]", simulated(), frozen=reduced)
        result = A.analyze(self.assemble(simulated((11, 22)), frozen=reduced))
        self.assertEqual((result["S"], result["freeze"]["confirmatory"]), (2, False))
        self.assertTrue(result["analysis_type"].startswith("descriptive reduced-S report (S = 2, from the freeze)"))
        self.assertIsNone(result["endpoints"]["strict"]["decision_label"])
        self.assertIsNone(result["endpoints"]["strict"]["retention_flags"])

    def test_adapter_hashes_and_attempt_must_match_the_frozen_slot(self):
        for field, value in (("adapter_model_sha256", sha("other model")), ("adapter_config_sha256", sha("other config")),
                             ("attempt", 2)):
            adapters = [adapter_entry(arm, s) for s in SEEDS for arm in sorted(A.ARMS)]
            target = next(a for a in adapters if (a["arm"], a["seed"]) == ("ER", 22))
            target[field] = value
            frozen = self.write_frozen(f"{field}.md", adapters=adapters)
            with self.subTest(field=field):
                self.refused("ER:22: run adapter ER:22 .* is not the frozen slot ER:22", simulated(), frozen=frozen)

    def test_freeze_and_implementation_manifest_are_required(self):
        self.refused(r"requires --frozen", simulated(), frozen=None)
        self.refused(r"requires --implementation-manifest", simulated(), impl=None)
        other = self.write_frozen("other-impl.md", implementation_sha=sha("another implementation manifest"))
        self.refused("implementation manifest is not the one recorded in the freeze", simulated(), frozen=other)

    def test_dev_fixture_route_is_separate(self):
        with self.assertRaisesRegex(A.AnalysisError, "DEV fixture route is separate"):
            A.assemble(base.DEV, simulated(), self.frozen, self.impl)
        with self.assertRaisesRegex(A.AnalysisError, "DEV fixture route is separate"):
            A.assemble(base.DEV, simulated(), None, self.impl)

    def test_cli_requires_and_uses_the_freeze(self):
        args = ["--dataset", str(NOT_READ), "--unchanged", str(SIM[(A.UNCHANGED, None)]),
                "--baseline-dev-results", str(BASELINE)]
        for (arm, seed), path in simulated().items():
            if arm != A.UNCHANGED:
                args += ["--run", f"{arm}:{seed}={path}"]
        import contextlib
        import io
        with mock.patch.object(A, "load_frozen_dataset", side_effect=final_test_loader), \
                contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(A.main(args + ["--out", str(self.tmp / "a")]), 2)
            bound = ["--frozen", str(self.frozen), "--implementation-manifest", str(self.impl)]
            # B3: the ceiling-risk count is never caller-supplied on the FINAL_TEST route ...
            self.assertEqual(A.main(args + bound + ["--out", str(self.tmp / "k"), "--ceiling-risk-proxy-k", "40"]), 2)
            # ... and the frozen baseline archive is required.
            no_baseline = [a for a in args if a not in ("--baseline-dev-results", str(BASELINE))]
            self.assertEqual(A.main(no_baseline + bound + ["--out", str(self.tmp / "nb")]), 2)
            self.assertEqual(A.main(args + ["--out", str(self.tmp / "b")] + bound), 0)
        self.assertIn("requires --frozen", err.getvalue())
        self.assertIn("a caller-supplied k (--ceiling-risk-proxy-k) is not accepted", err.getvalue())
        self.assertIn("requires --baseline-dev-results", err.getvalue())
        self.assertIn("FINAL_TEST COMPLETE confirmatory", out.getvalue())
        data = json.loads((self.tmp / "b" / "phase2_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["freeze"]["retained_seeds"], [{"slot": s, "seed": s} for s in SEEDS])
        self.assertEqual(data["ceiling_risk_proxy"]["correct"], base.PROXY_K)
        self.assertIn("derived", data["ceiling_risk_proxy"]["source"])

    def test_freeze_parser_refuses_malformed_manifests(self):
        good = frozen_document(self.impl_sha)
        A.parse_frozen(fenced(good, "ok"))
        bad = {
            "S differs": dict(good, S=2),
            "base model": dict(good, base_model=LLAMA),
            "base revision": dict(good, base_revision="0" * 40),
            "not a reserve": dict(good, retained_seeds=[{"slot": 11, "seed": 11}, {"slot": 22, "seed": 22},
                                                        {"slot": 33, "seed": 99}]),
            "confirmatory flag": dict(good, confirmatory=False, descriptive_only=True),
            "duplicate adapter": dict(good, adapters=good["adapters"][:-1] + [good["adapters"][0]]),
            "attempt 3": dict(good, adapters=[dict(good["adapters"][0], attempt=3)] + good["adapters"][1:]),
            "no shards": dict(good, base_weight_shards_sha256={}),
            "schema": dict(good, schema="phase2-adapters-frozen-2"),
            "no baseline": {k: v for k, v in good.items() if k != "baseline_dev_results_zip_sha256"},
            "S = 0": dict(good, retained_seeds=[], S=0, adapters=[]),
        }
        for name, document in bad.items():
            with self.subTest(name), self.assertRaises(A.AnalysisError):
                A.parse_frozen(fenced(document, name))
        with self.assertRaisesRegex(A.AnalysisError, "no ```json block"):
            A.parse_frozen("# empty\n")

    def test_fixture_freeze_matches_the_operator_schema(self):
        # Read-only cross-check with the freeze writer's own parser (t4_smoke/phase2_eval.py).
        from t4_smoke import phase2_eval
        self.assertIn(phase2_eval.FROZEN_SCHEMA, A.FROZEN_SCHEMAS)
        self.assertEqual(phase2_eval.tp.MAX_ATTEMPTS, A.MAX_ADAPTER_ATTEMPTS)
        text = self.frozen.read_text(encoding="utf-8")
        operator = phase2_eval.parse_frozen(text)
        ours = A.parse_frozen(text)
        self.assertEqual(sorted(e["seed"] for e in operator["retained_seeds"]), ours["seeds"])
        self.assertEqual(operator["base_weight_shards_sha256"], ours["unchanged"]["base_weight_shards_sha256"])


class ExecutionValidationTests(Fixture):
    """R2: backbone, mode, instruction, implementation manifest and attempt budget."""

    def test_llama_is_an_error_not_a_warning(self):
        # Sol's probe: a Llama-3.2-3B config with revision 000...000 under role FINAL_TEST.
        config = engine.default_config(A.FINAL_TEST_MODE, LLAMA)
        config.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
        with self.assertRaisesRegex(A.AnalysisError, "Llama-3.2-3B included"):
            A.check_config(config, "FINAL_TEST")
        config.update(model_revision=A.QWEN_REVISION, tokenizer_revision=A.QWEN_REVISION)
        with self.assertRaisesRegex(A.AnalysisError, "is not Qwen/Qwen3-4B"):
            A.check_config(config, "FINAL_TEST")
        # A whole archive produced with the Llama backbone is refused before any analysis.
        runs = simulated()
        target = self.copy((A.UNCHANGED, None))
        resign(target, model_id=LLAMA)
        runs[(A.UNCHANGED, None)] = str(target)
        self.refused("is not Qwen/Qwen3-4B", runs)
        self.assertNotIn("secondary backbone", Path(A.__file__).read_text(encoding="utf-8"))

    def test_qwen_revision_must_be_pinned(self):
        for field in ("model_revision", "tokenizer_revision"):
            runs = simulated()
            target = self.copy(("EC", 11), field)
            resign(target, **{field: "1" * 40})
            runs[("EC", 11)] = str(target)
            with self.subTest(field=field):
                self.refused("pinned Qwen3-4B revision", runs)

    def test_wrong_mode_is_refused(self):
        runs = simulated()
        runs[(A.UNCHANGED, None)] = str(EXTRA["phase2_dev_mode"])
        self.refused("mode 'phase2_dev', required 'phase2_final_test'", runs)
        target = self.copy(("ER", 33))
        manifest = engine.read(target / "run_manifest.json")
        engine.write(target / "run_manifest.json", dict(manifest, mode="phase2_dev"))  # manifest-only mismatch
        runs = simulated()
        runs[("ER", 33)] = str(target)
        self.refused("run manifest mode 'phase2_dev'", runs)

    def test_instruction_must_be_the_frozen_text(self):
        self.assertEqual(A.FROZEN_INSTRUCTION, engine.INSTRUCTION)
        self.assertEqual(A.FROZEN_INSTRUCTION_SHA256, sha(engine.INSTRUCTION))
        for name, instruction in (("v1", engine.INSTRUCTION_V1), ("edited", engine.INSTRUCTION + " ")):
            target = self.copy(("EE", 11), name)
            resign(target, instruction=instruction)
            runs = simulated()
            runs[("EE", 11)] = str(target)
            with self.subTest(name):
                self.refused("instruction is not the frozen test1-english-final-v2 text", runs)
        # Uniform but wrong across all runs is still refused (the old check only required agreement).
        config = final_test_config(None)
        with self.assertRaisesRegex(A.AnalysisError, "instruction"):
            A.check_config(dict(config, instruction=engine.INSTRUCTION_V1), "DEV")
        # An implementation manifest that records another instruction is refused too.
        doc = json.loads(json.dumps(self.impl_doc))
        doc["prompt"]["instruction_sha256"] = sha(engine.INSTRUCTION_V1)
        impl = self.write("impl-v1.md", fenced(doc, "Implementation manifest"))
        frozen = self.write_frozen("impl-v1-frozen.md", implementation_sha=hashlib.sha256(impl.read_bytes()).hexdigest())
        self.refused("instruction other than the frozen", simulated(), frozen=frozen, impl=impl)

    def manifest_variant(self, name, change):
        doc = json.loads(json.dumps(self.impl_doc))
        change(doc)
        impl = self.write(f"{name}-impl.md", fenced(doc, "Implementation manifest"))
        frozen = self.write_frozen(f"{name}-frozen.md", implementation_sha=hashlib.sha256(impl.read_bytes()).hexdigest())
        return dict(frozen=frozen, impl=impl)

    def test_engine_sources_must_match_the_implementation_manifest(self):
        target = self.copy(("EC", 33), "edited-source")
        (target / "source" / "report.py").write_bytes(b"# edited after the freeze\n")
        runs = simulated()
        runs[("EC", 33)] = str(target)
        self.refused("engine source snapshot differs from the implementation manifest: report.py", runs)
        target = self.copy(("EC", 33), "missing-source")
        (target / "source" / "hf_backend.py").unlink()
        runs[("EC", 33)] = str(target)
        self.refused("engine source snapshot differs .*hf_backend.py", runs)
        # The manifest's own record differs (e.g. a different backend file was frozen).
        variant = self.manifest_variant("backend-file", lambda d: d["files"].__setitem__(
            "test1_pilot/hinglish_pilot/hf_backend.py", sha("another backend")))
        self.refused("engine source snapshot differs .*hf_backend.py", simulated(), **variant)
        target = self.copy(("ER", 11), "code-hash")
        manifest = engine.read(target / "run_manifest.json")
        engine.write(target / "run_manifest.json", dict(manifest, code_sha256=sha("other code")))
        runs = simulated()
        runs[("ER", 11)] = str(target)
        self.refused("engine code hash differs", runs)

    def test_execution_configuration_must_match_the_implementation_manifest(self):
        variant = self.manifest_variant("config", lambda d: d["generation_config"]["engine_config_sha256"].__setitem__(
            "final_test", sha("another configuration")))
        self.refused("execution configuration differs from the implementation manifest", simulated(), **variant)
        target = self.copy(("EE", 33), "decode-note")
        resign(target, decode_policy_note="changed")  # a field outside FROZEN_CONFIG
        runs = simulated()
        runs[("EE", 33)] = str(target)
        self.refused("execution configuration differs", runs)

    def test_backend_must_match(self):
        cases = {"chat template": ("chat_template_sha256", sha("other template"), "chat template differs"),
                 "shards": ("base_weight_shards_sha256", {"x.safetensors": sha("x")}, "base weight shards differ"),
                 "fake backend": ("backend", "fake", "not the Hugging Face backend"),
                 "revision": ("model_revision", "2" * 40, "backend revision")}
        for name, (field, value, pattern) in cases.items():
            target = self.copy(("EC", 11), name.replace(" ", "-"))
            manifest = engine.read(target / "run_manifest.json")
            manifest["backend"] = dict(manifest["backend"], **{field: value})
            engine.write(target / "run_manifest.json", manifest)
            runs = simulated()
            runs[("EC", 11)] = str(target)
            with self.subTest(name):
                self.refused(pattern, runs)
        variant = self.manifest_variant("template", lambda d: d["model"]["chat_template"].__setitem__(
            "digest", sha("other template")))
        self.refused("chat template differs", simulated(), **variant)

    def three_attempts(self, name):
        """A copy of the unchanged run in which one rendering has two failed attempts before its scored one."""
        target = self.copy((A.UNCHANGED, None), name)
        first = sorted((target / "journal").glob("*.01.json"))[0]
        record = engine.read(first)
        rid = record["rendering_id"]
        first.unlink()
        for number in (1, 2):
            failed = {k: v for k, v in record.items() if k != "record_sha256"}
            failed.update(attempt_id=uuid.uuid4().hex, attempt_number=number, status="infrastructure_failure",
                          infrastructure_failure=True, error_code="generation_failed", raw_response=None,
                          correct=None, retry_reason=None if number == 1 else "previous_infrastructure_failure")
            failed["record_sha256"] = engine.digest(failed)
            engine.write(target / "journal" / f"{rid}.{number:02d}.json", failed)
        scored = {k: v for k, v in record.items() if k != "record_sha256"}
        scored.update(attempt_number=3, retry_reason="previous_infrastructure_failure")
        scored["record_sha256"] = engine.digest(scored)
        engine.write(target / "journal" / f"{rid}.03.json", scored)
        return target, rid

    def test_attempts_above_the_configured_budget_are_refused(self):
        target, rid = self.three_attempts("three")
        with self.assertRaisesRegex(A.AnalysisError, f"{rid} has 3 attempts, above the configured budget of 2"):
            A.load_run(target)
        runs = simulated()
        runs[(A.UNCHANGED, None)] = str(target)
        self.refused("above the configured budget", runs)
        # Two attempts are within budget only when the configuration allows one retry.
        target = self.copy((A.UNCHANGED, None), "two")
        record = engine.read(sorted((target / "journal").glob("*.01.json"))[0])
        failed = {k: v for k, v in record.items() if k != "record_sha256"}
        failed.update(attempt_id=uuid.uuid4().hex, status="infrastructure_failure", error_code="generation_failed",
                      raw_response=None, correct=None)
        failed["record_sha256"] = engine.digest(failed)
        scored = {k: v for k, v in record.items() if k != "record_sha256"}
        scored.update(attempt_number=2, retry_reason="previous_infrastructure_failure")
        scored["record_sha256"] = engine.digest(scored)
        engine.write(target / "journal" / f"{record['rendering_id']}.01.json", failed)
        engine.write(target / "journal" / f"{record['rendering_id']}.02.json", scored)
        self.assertEqual(A.load_run(target)["attempt_budget"], 2)
        resign(target, max_infrastructure_retries=0)
        with self.assertRaisesRegex(A.AnalysisError, "has 2 attempts, above the configured budget of 1"):
            A.load_run(target)
        # The configured budget itself must be the one in the implementation manifest.
        variant = self.manifest_variant("retries", lambda d: d["generation_config"]["decoding"].__setitem__(
            "max_infrastructure_retries", 0))
        self.refused("attempt budget differs from the implementation manifest", simulated(), **variant)

    def test_real_implementation_manifest_format_is_parsed(self):
        path = ROOT / "phase2" / "IMPLEMENTATION_MANIFEST.md"
        if not path.is_file():
            self.skipTest("phase2/IMPLEMENTATION_MANIFEST.md not built")
        parsed = A.load_implementation_manifest(path)
        self.assertEqual(parsed["engine_sources"]["scorer_v1.py"], A.SCORER_SHA256)
        self.assertIn("hf_backend.py", parsed["engine_sources"])
        self.assertEqual(parsed["max_infrastructure_retries"], 1)
        # B1: the real manifest's dependency pins are returned and contain the section-2 stack, PEFT included.
        self.assertEqual({k: parsed["package_pins"][k] for k in A.STACK_PINS}, A.STACK_PINS)
        self.assertEqual(parsed["package_pins"], PINNED)  # the fixtures simulate exactly the real pins
        self.assertTrue(A._is_sha(parsed["dev_config_sha256"]))

DELETE = object()


def reexecute(run_dir, backend=None, packages=None, environment=None, sessions=None, digest=True):
    """Rewrite a run directory's recorded execution (manifest backend, every session, environment.json) and, unless
    ``digest`` is False, recompute its execution digest consistently: the archive another machine or a modified engine
    could write. ``sessions`` (a function of the new session list) may then alter individual sessions."""
    manifest = engine.read(run_dir / "run_manifest.json")
    env = engine.read(run_dir / "environment.json")

    def apply(record, changes):
        for key, value in (changes or {}).items():
            if value is DELETE:
                record.pop(key, None)
            else:
                record[key] = value
        return record

    apply(manifest["backend"], backend)
    apply(env["packages"], packages)
    apply(env, environment)
    manifest["sessions"] = [dict(s, backend=json.loads(json.dumps(manifest["backend"])),
                                 environment=json.loads(json.dumps(env))) for s in manifest["sessions"]]
    if digest:
        manifest["execution_sha256"] = engine.digest({"backend": manifest["backend"], "environment": env})
    if sessions is not None:
        manifest["sessions"] = sessions(manifest["sessions"])
    engine.write(run_dir / "run_manifest.json", manifest)
    engine.write(run_dir / "environment.json", env)
    return run_dir


class EnvironmentBindingTests(Fixture):
    """Sol re-review B1 / Amendment 3 item 3: recorded hardware, settings, package versions, sessions and the execution
    digest are checked against the implementation manifest and section 2 on the FINAL_TEST route."""

    def check(self, run_dir, key=(A.UNCHANGED, None)):
        return A.check_final_test_run(key, A.load_run(run_dir), A.load_frozen(self.frozen),
                                      A.load_implementation_manifest(self.impl))

    def edited(self, name, key=("EC", 11), **changes):
        return reexecute(self.copy(key, name), **changes)

    def test_cpu_fixture_runs_are_refused(self):
        # Sol's R2 probe: the honest CPU fixtures (hardware 'none: ...', gpu_verified False) were accepted with labels.
        self.assertFalse(FinalTestFixtureBackend(("EC", 11), adapter_entry("EC", 11)).metadata["gpu_verified"])
        self.refused("recorded hardware 'none: scripted test fixture on DEV families' is not a Tesla T4", checkpoints())
        with self.assertRaisesRegex(A.AnalysisError, "is not a Tesla T4"):
            self.check(RUNS[(A.UNCHANGED, None)])

    def test_sol_wrong_recorded_environment_probe_is_refused(self):
        # Sol's probe verbatim: A100, capability [8, 0], gpu_verified False, torch 0.0.0, sessions agreeing.
        loaded = A.load_run(RUNS[(A.UNCHANGED, None)])
        manifest = json.loads(json.dumps(loaded["manifest"]))
        manifest["backend"].update(hardware="NVIDIA A100", gpu_verified=False, capability=[8, 0])
        for session in manifest["sessions"]:
            session["backend"] = manifest["backend"]
            session["environment"]["packages"]["torch"] = "0.0.0"
        loaded["manifest"] = manifest
        with self.assertRaisesRegex(A.AnalysisError, "NVIDIA A100"):
            A.check_final_test_run((A.UNCHANGED, None), loaded, A.load_frozen(self.frozen),
                                   A.load_implementation_manifest(self.impl))
        # The same probe on an otherwise compliant (simulated) run, digest re-signed, with gpu_verified kept True:
        # each noncompliant fact alone is refused.
        for name, changes, pattern in (
                ("a100", dict(backend=dict(hardware="NVIDIA A100-SXM4-40GB", capability=[8, 0])), "NVIDIA A100"),
                ("torch0", dict(packages={"torch": "0.0.0"}), "torch '0.0.0' \\(pinned '2.11.0\\+cu130'\\)")):
            target = reexecute(self.copy((A.UNCHANGED, None), name), **changes)
            with self.subTest(name), self.assertRaisesRegex(A.AnalysisError, pattern):
                self.check(target)

    def test_simulated_compliant_metadata_is_accepted(self):
        for key in [(A.UNCHANGED, None), ("EE", 11), ("ER", 33)]:
            self.assertIsNone(self.check(SIM[key], key))
        meta = A.load_run(SIM[("EC", 11)])["manifest"]["backend"]
        self.assertEqual(meta["simulated_fixture"], SIMULATED_LABEL)  # clearly labelled as a simulation
        # A legitimate resumed run (two identical sessions) is accepted.
        target = self.edited("resumed", sessions=lambda ss: ss + [dict(ss[0], started_at="later")])
        self.assertIsNone(self.check(target, ("EC", 11)))
        study = self.assemble({**simulated(), ("EC", 11): str(target)})
        self.assertTrue(study["labels"])

    def test_noncompliant_backend_metadata_is_refused(self):
        quant = dict(SIMULATED_QUANTIZATION)
        cases = {
            "A100": ({"hardware": "NVIDIA A100-SXM4-40GB"}, "is not a Tesla T4"),
            "L4": ({"hardware": "NVIDIA L4", "capability": [8, 9]}, "is not a Tesla T4"),
            "no hardware": ({"hardware": DELETE}, "recorded hardware None"),
            "capability": ({"capability": [8, 0]}, "capability \\[8, 0\\]"),
            "capability text": ({"capability": "7.5"}, "capability '7.5'"),
            "gpu_verified False": ({"gpu_verified": False}, "gpu_verified is False"),
            "gpu_verified missing": ({"gpu_verified": DELETE}, "gpu_verified is 'missing'"),
            "gpu_verified text": ({"gpu_verified": "True"}, "gpu_verified is 'True'"),
            "attention": ({"attention": "sdpa"}, "recorded attention 'sdpa'"),
            "flash attention": ({"attention": "flash_attention_2"}, "recorded attention"),
            "dtype": ({"compute_dtype": "bfloat16"}, "compute dtype 'bfloat16'"),
            "no quantization": ({"quantization": DELETE}, "no recorded quantization"),
            "fp4": ({"quantization": dict(quant, bnb_4bit_quant_type="fp4")}, "bnb_4bit_quant_type='fp4'"),
            "single quant": ({"quantization": dict(quant, bnb_4bit_use_double_quant=False)}, "bnb_4bit_use_double_quant=False"),
            "8 bit": ({"quantization": dict(quant, load_in_4bit=False, load_in_8bit=True)}, "load_in_4bit=False"),
            "fp32 compute": ({"quantization": dict(quant, bnb_4bit_compute_dtype="float32")}, "bnb_4bit_compute_dtype"),
        }
        for name, (changes, pattern) in cases.items():
            target = self.edited(name.replace(" ", "-"), backend=changes)
            runs = {**simulated(), ("EC", 11): str(target)}
            with self.subTest(name):
                self.refused("EC:11: .*" + pattern, runs)

    def test_package_versions_must_match_the_manifest_pins(self):
        cases = {"torch": "0.0.0", "transformers": "4.52.0", "bitsandbytes": "0.45.0", "accelerate": "1.7.0",
                 "peft": "0.16.0", "huggingface-hub": "0.31.0", "tokenizers": None, "safetensors": DELETE}
        for package, version in cases.items():
            target = self.edited(f"pkg-{package}", packages={package: version})
            runs = {**simulated(), ("EC", 11): str(target)}
            with self.subTest(package):
                self.refused(f"package versions differ from the implementation manifest pins: {package} ", runs)
        # PEFT is required for every Phase-2 archive, also the unchanged-model run (Amendment 3 item 3).
        target = reexecute(self.copy((A.UNCHANGED, None), "no-peft"), packages={"peft": None})
        self.refused("unchanged: session 1 of 1 package versions differ .*peft None \\(pinned '0.15.2'\\)",
                     {**simulated(), (A.UNCHANGED, None): str(target)})

    def test_every_session_is_validated(self):
        def second(**changes):
            def edit(sessions):
                extra = json.loads(json.dumps(sessions[0]))
                for part, values in changes.items():
                    extra[part].update(values) if isinstance(values, dict) else extra.__setitem__(part, values)
                return sessions + [extra]
            return edit
        cases = {
            "empty": (lambda ss: [], "records no engine session"),
            "missing": (None, "records no engine session"),
            "not a list": (lambda ss: ss[0], "records no engine session"),
            "no environment": (lambda ss: [{k: v for k, v in ss[0].items() if k != "environment"}],
                               "session 1 of 1 lacks its backend or environment record"),
            "other backend": (second(backend={"hardware": "NVIDIA A100"}), "session 2 of 2 ran on a different backend"),
            "other torch": (second(environment={"packages": dict(PINNED, torch="0.0.0")}),
                            "session 2 of 2 package versions differ .*torch '0.0.0'"),
            "other python": (second(environment={"python": "3.9.0"}),
                             "session 2 of 2: backend and environment do not match the execution digest"),
        }
        for name, (edit, pattern) in cases.items():
            target = self.copy(("ER", 22), name.replace(" ", "-"))
            if edit is None:
                manifest = engine.read(target / "run_manifest.json")
                del manifest["sessions"]
                engine.write(target / "run_manifest.json", manifest)
            else:
                reexecute(target, sessions=edit)
            with self.subTest(name):
                self.refused("ER:22: .*" + pattern, {**simulated(), ("ER", 22): str(target)})

    def test_execution_digest_must_be_valid(self):
        cases = {
            "tampered digest": (lambda d: reexecute(d, digest=False, sessions=lambda ss: ss) and
                                _edit_manifest(d, execution_sha256=sha("another execution")),
                                "session 1 of 1: backend and environment do not match the execution digest"),
            "no digest": (lambda d: _edit_manifest(d, execution_sha256=DELETE), "no valid execution digest"),
            "malformed digest": (lambda d: _edit_manifest(d, execution_sha256="T4"), "no valid execution digest"),
            "backend edited, digest stale": (lambda d: reexecute(d, backend={"gpu_total_bytes": 1}, digest=False),
                                             "do not match the execution digest"),
            "environment.json differs": (lambda d: _edit_environment_file(d, python="3.9.0"),
                                         "environment.json and the backend record do not match the execution digest"),
            "environment.json packages": (lambda d: _edit_environment_file(d, packages=dict(PINNED, torch="0.0.0")),
                                          "environment.json package versions differ"),
        }
        for name, (edit, pattern) in cases.items():
            target = self.copy(("EE", 33), name.replace(" ", "-").replace(".", "-"))
            edit(target)
            with self.subTest(name):
                self.refused("EE:33: .*" + pattern, {**simulated(), ("EE", 33): str(target)})
        # A ZIP lacking environment.json is refused when it is read.
        target = self.copy(("EE", 33), "no-environment-file")
        (target / "environment.json").unlink()
        self.refused("missing environment.json", {**simulated(), ("EE", 33): str(target)})

    def test_manifest_pins_are_returned_and_checked(self):
        parsed = A.load_implementation_manifest(self.impl)
        self.assertEqual(parsed["package_pins"], PINNED)
        variants = {
            "torch 0.0.0": (lambda d: d["dependencies"]["evaluation"].__setitem__("torch", "0.0.0"),
                            "does not pin the section-2 stack: torch '0.0.0'"),
            "no peft": (lambda d: d["dependencies"].pop("adapter_evaluation"), "dependencies.adapter_evaluation"),
            "peft other": (lambda d: d["dependencies"]["adapter_evaluation"].__setitem__("peft", "0.14.0"),
                           "peft '0.14.0'"),
            "no dependencies": (lambda d: d.pop("dependencies"), "lacks its dependency pins"),
            "conflict": (lambda d: d["dependencies"]["adapter_evaluation"].__setitem__("torch", "2.5.0"),
                         "pins torch twice"),
            "no DEV config": (lambda d: d["generation_config"]["engine_config_sha256"].pop("dev"),
                              "DEV engine configuration hash"),
        }
        for name, (change, pattern) in variants.items():
            variant = ExecutionValidationTests.manifest_variant(self, name.replace(" ", "-"), change)
            with self.subTest(name):
                self.refused(pattern, simulated(), **variant)
        # Runs matching a manifest's extra pin are checked against it too (pins come from the manifest).
        variant = ExecutionValidationTests.manifest_variant(self, "extra-pin", lambda d: d["dependencies"][
            "evaluation"].__setitem__("numpy", "9.9.9"))
        self.refused("numpy", simulated(), **variant)


def _edit_manifest(run_dir, **changes):
    manifest = engine.read(run_dir / "run_manifest.json")
    for key, value in changes.items():
        if value is DELETE:
            manifest.pop(key, None)
        else:
            manifest[key] = value
    engine.write(run_dir / "run_manifest.json", manifest)
    return run_dir


def _edit_environment_file(run_dir, **changes):
    env = engine.read(run_dir / "environment.json")
    env.update(changes)
    engine.write(run_dir / "environment.json", env)
    return run_dir


class FailingSimulatedBackend(SimulatedT4Backend):
    """Simulated-compliant metadata; every attempt on the first DEV family's C rendering fails (unresolved)."""

    def generate(self, prepared, config, seed):
        if base.FAMILIES[0]["forms"]["C"]["text"] in prepared["rendered_prompt"]:
            raise RuntimeError("simulated infrastructure failure")
        return super().generate(prepared, config, seed)


def expected_k(key):
    """Strict-correct C count of the scripted plan for ``key`` on the 40 DEV families."""
    return sum(base.strict_value(base.plan(key, j, "C", f["family_id"] in base.RUPEE)) for j, f in enumerate(base.FAMILIES))


class BaselineDerivationTests(Fixture):
    """Sol re-review B3 (analysis side) / Amendment 3 item 3: k comes from the frozen unchanged-model DEV archive."""

    def baseline(self, name, key=(A.UNCHANGED, None), adapter=None, mode=A.DEV_MODE, simulated=True,
                 backend=None, max_items=None, edit=None):
        """A baseline results ZIP made by the real engine, and a freeze recording its SHA-256."""
        run_dir = make_run(self.tmp / name, key, adapter, mode=mode, simulated=simulated, backend=backend,
                           max_items=max_items)
        if edit is not None:
            edit(run_dir)
        archive = engine_report.export(run_dir)
        frozen = self.write_frozen(f"{name}-frozen.md", baseline_sha=hashlib.sha256(archive.read_bytes()).hexdigest())
        return archive, frozen

    def test_k_is_derived_from_the_frozen_baseline(self):
        study = self.assemble(simulated())
        self.assertEqual(expected_k((A.UNCHANGED, None)), base.PROXY_K)
        self.assertEqual({k: study["baseline"][k] for k in ("sha256", "generations", "k", "n")},
                         {"sha256": BASELINE_SHA, "generations": 120, "k": base.PROXY_K, "n": 40})
        result = A.analyze(study)
        proxy = result["ceiling_risk_proxy"]
        self.assertEqual((proxy["correct"], proxy["fired"]), (base.PROXY_K, False))
        self.assertIn(f"SHA-256 {BASELINE_SHA}", proxy["source"])
        self.assertIn("Source of k: derived", A.markdown(result))
        # A caller-supplied k is refused on the FINAL_TEST route, whatever its value.
        for k in (base.PROXY_K, 40, 0):
            with self.subTest(k=k), self.assertRaisesRegex(A.AnalysisError, "caller-supplied k"):
                A.analyze(study, k)

    def test_k_follows_the_archive(self):
        # Same validator, another scripted outcome pattern: k is whatever the frozen archive's C scores say.
        key = ("EC", 11)  # scripted answers of the EC:11 plan, produced by the unchanged model's configuration
        archive, frozen = self.baseline("other-k", key=key)
        k = expected_k(key)
        self.assertNotEqual(k, base.PROXY_K)
        result = A.analyze(self.assemble(simulated(), frozen=frozen, baseline=archive))
        self.assertEqual(result["ceiling_risk_proxy"]["correct"], k)
        self.assertEqual(result["ceiling_risk_proxy"]["fired"], k >= 38)
        # The default freeze records another baseline: this archive is then refused by hash.
        self.refused("baseline results ZIP SHA-256 .* is not the frozen", simulated(), baseline=archive)

    def test_baseline_must_be_given_as_the_frozen_zip(self):
        self.refused("requires --baseline-dev-results", simulated(), baseline=None)
        self.refused("a results ZIP, not a run directory", simulated(), baseline=EXTRA["phase2_dev_mode"])
        self.refused("baseline results ZIP not found", simulated(), baseline=self.tmp / "absent_results.zip")

    def test_metadata_only_zip_is_refused(self):
        # Sol's B3 probe shape: a ZIP holding just run_manifest.json and experiment_config.json (with checksums).
        import zipfile
        members = {"run_manifest.json": json.dumps({"status": "COMPLETE", "mode": A.DEV_MODE, "completed": 120,
                                                    "unresolved": 0}).encode(),
                   "experiment_config.json": json.dumps({"adapter": None, "model_id": A.QWEN_ID}).encode()}
        members["checksums.sha256"] = "".join(f"{hashlib.sha256(v).hexdigest()}  {k}\n"
                                              for k, v in members.items()).encode()
        archive = self.tmp / "metadata-only_results.zip"
        with zipfile.ZipFile(archive, "w") as z:
            for name, blob in members.items():
                z.writestr(name, blob)
        frozen = self.write_frozen("metadata-only.md", baseline_sha=hashlib.sha256(archive.read_bytes()).hexdigest())
        self.refused("missing (dataset.json|generation_attempts.jsonl|environment.json)", simulated(),
                     frozen=frozen, baseline=archive)

    def test_incomplete_or_unresolved_baseline_is_refused(self):
        archive, frozen = self.baseline("partial", max_items=60)
        self.refused("unchanged-DEV baseline: 60/120 resolved generations; exactly 120", simulated(),
                     frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("unresolved", backend=FailingSimulatedBackend)
        self.refused("unchanged-DEV baseline: 119/120 resolved generations", simulated(), frozen=frozen, baseline=archive)

    def test_baseline_must_be_the_unchanged_model_on_dev(self):
        archive, frozen = self.baseline("adapter", key=("EC", 11), adapter=adapter_entry("EC", 11))
        self.refused("baseline: not the unchanged model", simulated(), frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("final-mode", mode=A.FINAL_TEST_MODE)
        self.refused("baseline: mode 'phase2_final_test'", simulated(), frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("other-config", edit=lambda d: resign(d, decode_policy_note="changed"))
        self.refused("baseline: execution configuration differs from the implementation manifest's DEV", simulated(),
                     frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("llama", edit=lambda d: resign(d, model_id=LLAMA))
        self.refused("baseline: not Qwen/Qwen3-4B", simulated(), frozen=frozen, baseline=archive)

    def test_baseline_environment_is_validated_too(self):
        archive, frozen = self.baseline("cpu", simulated=False)  # honest CPU-fixture metadata
        self.refused("unchanged-DEV baseline: recorded hardware 'none: .*' is not a Tesla T4", simulated(),
                     frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("torch0", edit=lambda d: reexecute(d, packages={"torch": "0.0.0"}))
        self.refused("unchanged-DEV baseline: session 1 of 1 package versions differ .*torch", simulated(),
                     frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("no-sessions", edit=lambda d: reexecute(d, sessions=lambda ss: []))
        self.refused("unchanged-DEV baseline: the archive records no engine session", simulated(),
                     frozen=frozen, baseline=archive)
        archive, frozen = self.baseline("shards", edit=lambda d: reexecute(
            d, backend={"base_weight_shards_sha256": {"x.safetensors": sha("x")}}))
        self.refused("unchanged-DEV baseline: base weight shards differ from the freeze", simulated(),
                     frozen=frozen, baseline=archive)



if __name__ == "__main__":
    unittest.main()
