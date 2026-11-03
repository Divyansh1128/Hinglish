"""FINAL_TEST input binding (PREREGISTRATION Amendment 2 item 7; Sol review R1 and R2), on DEV fixtures only.

FINAL_TEST contents are never read. The FINAL_TEST loader (``analyze.load_frozen_dataset``) is mocked to return
the 40 DEV families under the FINAL_TEST role and hash, and the dataset path handed to the analysis does not
exist. Engine runs are produced by the real engine in mode ``phase2_final_test`` with a scripted backend; only
the engine's own 100-family FINAL_TEST data validation is mocked so that the DEV families can be used.
The freeze (``ADAPTERS_FROZEN.md``) and implementation manifest are synthetic fixtures in their real formats.
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


def final_test_config(adapter, mode=A.FINAL_TEST_MODE):
    config = engine.default_config(mode)
    config.update(model_revision=A.QWEN_REVISION, tokenizer_revision=A.QWEN_REVISION, adapter=adapter)
    return config


def make_run(root, key, adapter, mode=A.FINAL_TEST_MODE):
    dataset, splits = base.wrapped_dev()
    with mock.patch.object(engine, "validate", lambda *args, **kwargs: None):  # 40 DEV families, not 100
        engine.run(root, dataset, splits, final_test_config(adapter, mode), FinalTestFixtureBackend(key, adapter))
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
            "generation_config": {"engine_config_sha256": {"final_test": engine.digest(final_test_config(None))},
                                  "decoding": {"max_infrastructure_retries": 1}}}


def frozen_document(implementation_sha, seeds=SEEDS, slots=None, adapters=None):
    slots = slots or seeds
    S = len(seeds)
    return {"schema": "phase2-adapters-frozen-3", "base_model": A.QWEN_ID, "base_revision": A.QWEN_REVISION,
            "baseline_dev_results_zip_sha256": sha("unchanged DEV baseline results zip"),
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
RUNS = {}  # (arm, seed) / (UNCHANGED, None) -> path of a correctly made FINAL_TEST-mode fixture run
EXTRA = {}  # odd runs used by refusal tests


def setUpModule():
    global TMP
    TMP = tempfile.TemporaryDirectory()
    root = Path(TMP.name)
    RUNS[(A.UNCHANGED, None)] = make_run(root / "unchanged", (A.UNCHANGED, None), None)
    for seed in SEEDS + (RESERVE,):
        for arm in A.ARMS:
            RUNS[(arm, seed)] = make_run(root / f"{arm}-{seed}", (arm, seed), adapter_entry(arm, seed))
    RUNS[("EC", 22)] = engine_report.export(RUNS[("EC", 22)])  # one input as the engine's results ZIP
    EXTRA["EC11_no_adapter"] = make_run(root / "EC-11-no-adapter", ("EC", 11), None)
    EXTRA["phase2_dev_mode"] = make_run(root / "unchanged-dev-mode", (A.UNCHANGED, None), None, mode="phase2_dev")


def tearDownModule():
    TMP.cleanup()


def checkpoints(seeds=SEEDS):
    out = {(A.UNCHANGED, None): str(RUNS[(A.UNCHANGED, None)])}
    out.update({(arm, s): str(RUNS[(arm, s)]) for s in seeds for arm in A.ARMS})
    return out


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

    def assemble(self, runs, frozen="default", impl="default"):
        frozen = self.frozen if frozen == "default" else frozen
        impl = self.impl if impl == "default" else impl
        with mock.patch.object(A, "load_frozen_dataset", side_effect=final_test_loader) as loader:
            study = A.assemble(NOT_READ, runs, frozen, impl)
        loader.assert_called_once_with(NOT_READ)
        return study

    def refused(self, pattern, runs, **kwargs):
        with self.assertRaisesRegex(A.AnalysisError, pattern):
            self.assemble(runs, **kwargs)

    def copy(self, key, name="copy"):
        target = self.tmp / name
        shutil.copytree(RUNS[key], target)
        return target


class FreezeBindingTests(Fixture):
    """R1: checkpoints, retained seeds and S come from phase2/ADAPTERS_FROZEN.md."""

    def test_frozen_set_is_accepted_and_confirmatory(self):
        study = self.assemble(checkpoints())
        self.assertEqual((study["role"], study["seeds"], study["labels"]), ("FINAL_TEST", [11, 22, 33], True))
        result = A.analyze(study, base.PROXY_K)
        self.assertEqual(result["status"], "COMPLETE")
        self.assertTrue(result["results"])
        self.assertTrue(result["analysis_type"].startswith("confirmatory (S = 3"))
        self.assertEqual(result["freeze"]["sha256"], hashlib.sha256(self.frozen.read_bytes()).hexdigest())
        self.assertEqual(result["freeze"]["implementation_manifest"]["sha256"], self.impl_sha)
        self.assertEqual(result["freeze"]["baseline_dev_results_zip_sha256"], sha("unchanged DEV baseline results zip"))
        self.assertIsNotNone(result["endpoints"]["strict"]["decision_label"])
        self.assertNotIn(A.DEV_NOT_RESULTS, result["warnings"])
        self.assertEqual({i["checkpoint"]: i["adapter"] for i in result["inputs"]}[ "EC:11"], adapter_entry("EC", 11))
        text = A.markdown(result)
        self.assertIn("ADAPTERS_FROZEN.md", text)
        self.assertNotIn("NOT RESULTS", text)

    def test_swapped_arm_inputs_are_refused(self):
        # Sol's probe: swap only the EC:11 and ER:11 input paths.
        runs = checkpoints()
        runs[("EC", 11)], runs[("ER", 11)] = runs[("ER", 11)], runs[("EC", 11)]
        self.refused("(EC:11: run adapter ER:11 .* frozen slot EC:11|ER:11: run adapter EC:11 .* frozen slot ER:11)", runs)
        runs = checkpoints()
        runs[("EE", 22)], runs[("EE", 33)] = runs[("EE", 33)], runs[("EE", 22)]  # swap across seeds
        self.refused("is not the frozen slot", runs)

    def test_trained_label_without_adapter_is_refused(self):
        runs = checkpoints()
        runs[("EC", 11)] = str(EXTRA["EC11_no_adapter"])
        self.refused("EC:11: no adapter loaded under a trained-arm label", runs)
        # Sol's probe: an existing-style DEV fixture run (no adapter, pilot_b mode, unpinned revision) under a
        # trained label is refused too.
        runs[("EC", 11)] = str(base.make_run(self.tmp / "dev-style", ("EC", 11)))
        self.refused("Refused", runs)

    def test_unchanged_label_with_adapter_is_refused(self):
        runs = checkpoints()
        runs[(A.UNCHANGED, None)] = str(RUNS[("EE", RESERVE)])
        self.refused("unchanged-model run has an adapter loaded", runs)

    def test_missing_runs_are_refused(self):
        runs = checkpoints()
        del runs[("EC", 33)]
        self.refused(r"missing \['EC:33'\]", runs)
        # Omitting a whole frozen seed cannot silently become a reduced-S analysis.
        self.refused(r"missing \['EC:33', 'EE:33', 'ER:33'\]", checkpoints((11, 22)))
        runs = checkpoints()
        del runs[(A.UNCHANGED, None)]
        self.refused(r"missing \['unchanged'\]", runs)

    def test_extra_seed_is_refused(self):
        self.refused(r"extra or substituted \['EC:44', 'EE:44', 'ER:44'\]", checkpoints(SEEDS + (RESERVE,)))
        runs = checkpoints()
        runs[("EC", RESERVE)] = str(RUNS[("EC", RESERVE)])
        self.refused(r"missing none; extra or substituted \['EC:44'\]", runs)

    def test_substituted_seed_is_refused(self):
        # A reserve triplet offered in place of a frozen seed, honestly labelled ...
        self.refused(r"missing \['EC:33', 'EE:33', 'ER:33'\]; extra or substituted \['EC:44', 'EE:44', 'ER:44'\]",
                     checkpoints((11, 22, RESERVE)))
        # ... or relabelled as the frozen seed.
        runs = checkpoints()
        for arm in A.ARMS:
            runs[(arm, 33)] = str(RUNS[(arm, RESERVE)])
        self.refused("run adapter .*:44 .* is not the frozen slot .*:33", runs)

    def test_reserve_seed_and_reduced_s_come_from_the_freeze(self):
        frozen = self.write_frozen("reserve.md", seeds=(11, 22, RESERVE), slots=(11, 22, 33))
        study = self.assemble(checkpoints((11, 22, RESERVE)), frozen=frozen)
        self.assertEqual((study["seeds"], study["labels"]), ([11, 22, 44], True))
        self.assertTrue(any("33→44" in w for w in study["warnings"]))
        self.refused("extra or substituted", checkpoints(), frozen=frozen)
        # A reduced-S freeze: the descriptive report follows the freeze, not the operator.
        reduced = self.write_frozen("reduced.md", seeds=(11, 22))
        self.refused(r"extra or substituted \['EC:33', 'EE:33', 'ER:33'\]", checkpoints(), frozen=reduced)
        result = A.analyze(self.assemble(checkpoints((11, 22)), frozen=reduced), base.PROXY_K)
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
                self.refused("ER:22: run adapter ER:22 .* is not the frozen slot ER:22", checkpoints(), frozen=frozen)

    def test_freeze_and_implementation_manifest_are_required(self):
        self.refused(r"requires --frozen", checkpoints(), frozen=None)
        self.refused(r"requires --implementation-manifest", checkpoints(), impl=None)
        other = self.write_frozen("other-impl.md", implementation_sha=sha("another implementation manifest"))
        self.refused("implementation manifest is not the one recorded in the freeze", checkpoints(), frozen=other)

    def test_dev_fixture_route_is_separate(self):
        with self.assertRaisesRegex(A.AnalysisError, "DEV fixture route is separate"):
            A.assemble(base.DEV, checkpoints(), self.frozen, self.impl)
        with self.assertRaisesRegex(A.AnalysisError, "DEV fixture route is separate"):
            A.assemble(base.DEV, checkpoints(), None, self.impl)

    def test_cli_requires_and_uses_the_freeze(self):
        args = ["--dataset", str(NOT_READ), "--unchanged", str(RUNS[(A.UNCHANGED, None)]),
                "--ceiling-risk-proxy-k", str(base.PROXY_K)]
        for (arm, seed), path in checkpoints().items():
            if arm != A.UNCHANGED:
                args += ["--run", f"{arm}:{seed}={path}"]
        import contextlib
        import io
        with mock.patch.object(A, "load_frozen_dataset", side_effect=final_test_loader), \
                contextlib.redirect_stdout(io.StringIO()) as out, contextlib.redirect_stderr(io.StringIO()) as err:
            self.assertEqual(A.main(args + ["--out", str(self.tmp / "a")]), 2)
            self.assertEqual(A.main(args + ["--out", str(self.tmp / "b"), "--frozen", str(self.frozen),
                                            "--implementation-manifest", str(self.impl)]), 0)
        self.assertIn("requires --frozen", err.getvalue())
        self.assertIn("FINAL_TEST COMPLETE confirmatory", out.getvalue())
        data = json.loads((self.tmp / "b" / "phase2_analysis.json").read_text(encoding="utf-8"))
        self.assertEqual(data["freeze"]["retained_seeds"], [{"slot": s, "seed": s} for s in SEEDS])

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
        runs = checkpoints()
        target = self.copy((A.UNCHANGED, None))
        resign(target, model_id=LLAMA)
        runs[(A.UNCHANGED, None)] = str(target)
        self.refused("is not Qwen/Qwen3-4B", runs)
        self.assertNotIn("secondary backbone", Path(A.__file__).read_text(encoding="utf-8"))

    def test_qwen_revision_must_be_pinned(self):
        for field in ("model_revision", "tokenizer_revision"):
            runs = checkpoints()
            target = self.copy(("EC", 11), field)
            resign(target, **{field: "1" * 40})
            runs[("EC", 11)] = str(target)
            with self.subTest(field=field):
                self.refused("pinned Qwen3-4B revision", runs)

    def test_wrong_mode_is_refused(self):
        runs = checkpoints()
        runs[(A.UNCHANGED, None)] = str(EXTRA["phase2_dev_mode"])
        self.refused("mode 'phase2_dev', required 'phase2_final_test'", runs)
        target = self.copy(("ER", 33))
        manifest = engine.read(target / "run_manifest.json")
        engine.write(target / "run_manifest.json", dict(manifest, mode="phase2_dev"))  # manifest-only mismatch
        runs = checkpoints()
        runs[("ER", 33)] = str(target)
        self.refused("run manifest mode 'phase2_dev'", runs)

    def test_instruction_must_be_the_frozen_text(self):
        self.assertEqual(A.FROZEN_INSTRUCTION, engine.INSTRUCTION)
        self.assertEqual(A.FROZEN_INSTRUCTION_SHA256, sha(engine.INSTRUCTION))
        for name, instruction in (("v1", engine.INSTRUCTION_V1), ("edited", engine.INSTRUCTION + " ")):
            target = self.copy(("EE", 11), name)
            resign(target, instruction=instruction)
            runs = checkpoints()
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
        self.refused("instruction other than the frozen", checkpoints(), frozen=frozen, impl=impl)

    def manifest_variant(self, name, change):
        doc = json.loads(json.dumps(self.impl_doc))
        change(doc)
        impl = self.write(f"{name}-impl.md", fenced(doc, "Implementation manifest"))
        frozen = self.write_frozen(f"{name}-frozen.md", implementation_sha=hashlib.sha256(impl.read_bytes()).hexdigest())
        return dict(frozen=frozen, impl=impl)

    def test_engine_sources_must_match_the_implementation_manifest(self):
        target = self.copy(("EC", 33), "edited-source")
        (target / "source" / "report.py").write_bytes(b"# edited after the freeze\n")
        runs = checkpoints()
        runs[("EC", 33)] = str(target)
        self.refused("engine source snapshot differs from the implementation manifest: report.py", runs)
        target = self.copy(("EC", 33), "missing-source")
        (target / "source" / "hf_backend.py").unlink()
        runs[("EC", 33)] = str(target)
        self.refused("engine source snapshot differs .*hf_backend.py", runs)
        # The manifest's own record differs (e.g. a different backend file was frozen).
        variant = self.manifest_variant("backend-file", lambda d: d["files"].__setitem__(
            "test1_pilot/hinglish_pilot/hf_backend.py", sha("another backend")))
        self.refused("engine source snapshot differs .*hf_backend.py", checkpoints(), **variant)
        target = self.copy(("ER", 11), "code-hash")
        manifest = engine.read(target / "run_manifest.json")
        engine.write(target / "run_manifest.json", dict(manifest, code_sha256=sha("other code")))
        runs = checkpoints()
        runs[("ER", 11)] = str(target)
        self.refused("engine code hash differs", runs)

    def test_execution_configuration_must_match_the_implementation_manifest(self):
        variant = self.manifest_variant("config", lambda d: d["generation_config"]["engine_config_sha256"].__setitem__(
            "final_test", sha("another configuration")))
        self.refused("execution configuration differs from the implementation manifest", checkpoints(), **variant)
        target = self.copy(("EE", 33), "decode-note")
        resign(target, decode_policy_note="changed")  # a field outside FROZEN_CONFIG
        runs = checkpoints()
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
            runs = checkpoints()
            runs[("EC", 11)] = str(target)
            with self.subTest(name):
                self.refused(pattern, runs)
        variant = self.manifest_variant("template", lambda d: d["model"]["chat_template"].__setitem__(
            "digest", sha("other template")))
        self.refused("chat template differs", checkpoints(), **variant)

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
        runs = checkpoints()
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
        self.refused("attempt budget differs from the implementation manifest", checkpoints(), **variant)

    def test_real_implementation_manifest_format_is_parsed(self):
        path = ROOT / "phase2" / "IMPLEMENTATION_MANIFEST.md"
        if not path.is_file():
            self.skipTest("phase2/IMPLEMENTATION_MANIFEST.md not built")
        parsed = A.load_implementation_manifest(path)
        self.assertEqual(parsed["engine_sources"]["scorer_v1.py"], A.SCORER_SHA256)
        self.assertIn("hf_backend.py", parsed["engine_sources"])
        self.assertEqual(parsed["max_infrastructure_retries"], 1)


if __name__ == "__main__":
    unittest.main()
