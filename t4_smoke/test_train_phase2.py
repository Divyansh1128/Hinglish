"""Model-free tests of the Phase-2 training module (PREREGISTRATION §3 with Amendment 1 items 9-11 and Amendment 2
items 2-7)."""
import atexit
import contextlib
import copy
import hashlib
import importlib.util
import io
import json
import math
import shutil
import tempfile
import time
import types
import unittest
from pathlib import Path
import zipfile
from unittest import mock

from t4_smoke import train_phase2 as tp
from t4_smoke import train_smoke as ts
from t4_smoke.test_labels import FakeTokenizer

ROOT = Path(__file__).resolve().parents[1]


class ScheduleTests(unittest.TestCase):
    def test_lr_at_the_preregistered_points(self):
        self.assertAlmostEqual(tp.lr_at(1), 1e-4 / 6, places=15)
        self.assertAlmostEqual(tp.lr_at(6), 1e-4, places=15)
        self.assertAlmostEqual(tp.lr_at(7), 1e-4 * (0.1 + 0.9 * 0.5 * (1 + math.cos(math.pi / 54))), places=15)
        self.assertAlmostEqual(tp.lr_at(7), 9.9923867e-5, places=12)
        self.assertAlmostEqual(tp.lr_at(60), 1e-5, places=15)

    def test_warmup_linear_then_monotone_cosine(self):
        warm = [tp.lr_at(u) for u in range(1, 7)]
        for u, value in enumerate(warm, 1):
            self.assertAlmostEqual(value, 1e-4 * u / 6, places=15)
        decay = [tp.lr_at(u) for u in range(6, 61)]
        self.assertTrue(all(a > b for a, b in zip(decay, decay[1:])))
        self.assertAlmostEqual(tp.lr_at(33), 1e-4 * 0.55, places=15)  # cosine midpoint
        for bad in (0, 61):
            with self.assertRaises(ValueError):
                tp.lr_at(bad)

    def test_recipe_keeps_the_d021_recipe_and_d043_counts(self):
        for key, value in tp.RECIPE.items():
            if key in ts.RECIPE and key not in ("families", "updates", "lr_schedule", "data_order"):
                self.assertEqual(value, ts.RECIPE[key], key)
        recipe = tp.RECIPE
        self.assertEqual((recipe["families"], recipe["examples_per_arm"], recipe["passes"], recipe["updates_per_pass"],
                          recipe["updates"], recipe["accumulation"], recipe["lr"]), (160, 320, 3, 20, 60, 16, 1e-4))
        self.assertEqual(recipe["examples_per_arm"] * recipe["passes"], recipe["updates"] * recipe["accumulation"])
        self.assertEqual((tp.SEEDS, tp.RESERVE_SEEDS, recipe["checkpoint_every"]), ((11, 22, 33), (44, 55), 10))
        self.assertNotIn("seed", recipe)  # the run seed is a run argument, never a recipe constant
        self.assertEqual(recipe["content_batch_families"], 8)
        self.assertEqual(recipe["grad_scaler"], {"init_scale": 65536.0, "growth_factor": 2.0, "backoff_factor": 0.5,
                                                 "growth_interval": 2000})
        self.assertIn("not dropout", recipe["pairing_scope"])


class DataTests(unittest.TestCase):
    def test_all_160_frozen_train_families_and_only_the_train_files_are_read(self):
        read = []
        original = Path.read_bytes

        def spy(path):
            read.append(path.resolve())
            return original(path)

        with mock.patch.object(Path, "read_bytes", spy):
            data = tp.phase2_dataset(ROOT)
        self.assertEqual(sorted(read), sorted((ROOT / name).resolve() for name in ts.TRAIN_FILES))
        families = tp.validate_phase2_data(data)
        self.assertEqual(len(families), 160)
        self.assertEqual(sum(f["source_file"] == "phase2/train_A.v2.json" for f in families), 80)
        self.assertTrue(all(f["split_role"] == "CONFIRM_TRAIN" for f in families))
        self.assertEqual(data["sources"], ts.TRAIN_FILES)
        embedded = json.dumps(data)
        for marker in ("DV0", "FT0", '"gold"', "reference_equation"):
            self.assertNotIn(marker, embedded)

    def test_frozen_hashes_agree_with_the_frozen_notes(self):
        notes = (ROOT / "phase2" / "TRAIN_DEV_FROZEN.md").read_text()
        for name, digest in ts.TRAIN_FILES.items():
            self.assertIn(digest, notes)
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_hash_mismatch_and_tampering_are_refused(self):
        sources = ts.load_train_sources(ROOT)
        tampered = [(sources[0][0], sources[0][1].replace(b"FINAL", b"Final", 1)), sources[1]]
        with mock.patch.object(ts, "load_train_sources", return_value=tampered), \
                self.assertRaisesRegex(ValueError, "frozen SHA-256"):
            tp.phase2_dataset(ROOT)
        data = tp.phase2_dataset(ROOT)
        altered = copy.deepcopy(data)
        altered["families"][5]["completion"] += " "
        with self.assertRaisesRegex(ValueError, "changed"):
            tp.validate_phase2_data(altered)
        altered = copy.deepcopy(data)
        altered["families"].pop()
        with self.assertRaisesRegex(ValueError, "160"):
            tp.validate_phase2_data(altered)
        altered = copy.deepcopy(data)
        altered["sources"] = {"phase2/dev.v2.json": "0" * 64}
        with self.assertRaisesRegex(ValueError, "frozen TRAIN"):
            tp.validate_phase2_data(altered)

    def test_training_code_names_no_dev_or_final_test_file(self):
        for name in ("train_phase2.py", "train_smoke.py", "labels.py"):
            source = (ROOT / "t4_smoke" / name).read_text()
            for marker in ("dev.v2", "final_test.v", "dev.DRAFT", "final_test.DRAFT"):
                self.assertNotIn(marker, source, name)


class OrderAndPairingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.families = tp.validate_phase2_data(tp.phase2_dataset(ROOT))

    def test_order_follows_the_preregistered_rule(self):
        for seed in (11, 22, 33, 44, 55):
            for number in (1, 2, 3):
                expected = sorted((hashlib.sha256(f"phase2-D043:{seed}:{number}:{f['family_id']}".encode()).hexdigest(),
                                   f["family_id"]) for f in self.families)
                self.assertEqual(tp.pass_order(self.families, seed, number), [fid for _, fid in expected])

    def test_sequence_structure(self):
        sequence = tp.run_sequence(self.families, "EC", 11)
        self.assertEqual(len(sequence), 960)
        for number in range(3):
            block = sequence[number * 320:(number + 1) * 320]
            self.assertEqual(block[0::2], [(fid, "E") for fid in tp.pass_order(self.families, 11, number + 1)])
            self.assertEqual(block[1::2], [(fid, "C") for fid in tp.pass_order(self.families, 11, number + 1)])
        for update in range(1, 61):
            items = [sequence[c] for c in ts.update_cursors(update)]
            self.assertEqual(len({fid for fid, _ in items}), 8)
            self.assertEqual(tp.pass_of(update), (update - 1) // 20 + 1)

    def test_identical_order_across_arms_within_a_seed(self):
        for seed in tp.SEEDS + tp.RESERVE_SEEDS:
            sequences = {arm: tp.run_sequence(self.families, arm, seed) for arm in tp.ARMS}
            ids = {arm: [fid for fid, _ in seq] for arm, seq in sequences.items()}
            self.assertEqual(ids["EE"], ids["ER"])
            self.assertEqual(ids["EE"], ids["EC"])
            for arm, second in tp.ARMS.items():
                self.assertEqual([form for _, form in sequences[arm]], ["E", second] * 480)
            self.assertEqual(len({tp.order_sha256(self.families, seed)}), 1)
        self.assertNotEqual(tp.pass_order(self.families, 11, 1), tp.pass_order(self.families, 22, 1))
        self.assertNotEqual(tp.pass_order(self.families, 11, 1), tp.pass_order(self.families, 11, 2))
        self.assertNotEqual(tp.order_sha256(self.families, 11), tp.order_sha256(self.families, 22))

    def test_arms_share_targets_position_by_position(self):
        tokenizer = FakeTokenizer()
        examples = ts.build_examples(tokenizer, self.families)
        runs = {arm: tp.run_examples(examples, self.families, arm, 22) for arm in tp.ARMS}
        for index in range(0, 960, 7):
            targets = {arm: run[index]["input_ids"][run[index]["boundary_index"]:] for arm, run in runs.items()}
            self.assertEqual(targets["EE"], targets["ER"])
            self.assertEqual(targets["EE"], targets["EC"])
        self.assertEqual(runs["EE"][0]["input_ids"], runs["ER"][0]["input_ids"])  # probe example: E, identical
        self.assertNotEqual(runs["ER"][1]["input_ids"], runs["EC"][1]["input_ids"])

    def test_lora_initialisation_uses_the_run_seed_not_the_arm(self):
        seen = []

        def fake_smoke_load(torch):
            ts.seed_everything(torch, ts.RECIPE["seed"])  # what train_smoke.load_model does before get_peft_model
            return "model", [], True, {}

        with mock.patch.object(ts, "load_model", fake_smoke_load), \
                mock.patch.object(ts, "random") as fake_random:
            fake_random.seed.side_effect = seen.append
            torch = mock.MagicMock()
            for seed in (22, 22, 33):
                tp.load_model(torch, seed)
            self.assertEqual(seen, [22, 22, 33])
            torch.manual_seed.assert_called_with(33)
            torch.cuda.manual_seed_all.assert_called_with(33)
        self.assertEqual(ts.seed_everything.__name__, "seed_everything")  # restored

        def failing(torch):
            raise RuntimeError("load failed")

        with mock.patch.object(ts, "load_model", failing), self.assertRaises(RuntimeError):
            tp.load_model(mock.MagicMock(), 11)
        self.assertEqual(ts.seed_everything.__name__, "seed_everything")

    def test_pairing_report(self):
        base = {"order_sha256": "o", "initial_adapter_sha256": "i"}
        records = [dict(base, seed=11, arm=arm) for arm in tp.ARMS]
        self.assertEqual(tp.pairing(records)[11], {"arms": ["EC", "EE", "ER"], "same_order": True, "same_initial_adapter": True})
        records[1]["initial_adapter_sha256"] = "j"
        self.assertFalse(tp.pairing(records)[11]["same_initial_adapter"])



# ---------------------------------------------------------------- shared fixtures (also used by test_phase2_eval)

IDENTITY = {"implementation_manifest_sha256": "e" * 64, "baseline_dev_results_zip_sha256": "f" * 64,
            "exposure_order_file_sha256": tp.EXPOSURE_ORDER_SHA256, "recipe_sha256": ts.digest(tp.RECIPE)}


def _manifest_builder():
    if "builder" not in _CACHE:
        spec = importlib.util.spec_from_file_location("build_implementation_manifest_fixture",
                                                      ROOT / "phase2" / "build_implementation_manifest.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        _CACHE["builder"] = module
    return _CACHE["builder"]


_CACHE = {}


def live_manifest_text():
    """IMPLEMENTATION_MANIFEST.md exactly as the current builder derives it from this repository (computed, so the
    tests never depend on whether the committed file has been regenerated yet)."""
    if "text" not in _CACHE:
        _CACHE["text"] = _manifest_builder().current_text()
    return _CACHE["text"]


def live_manifest_document():
    return copy.deepcopy(_manifest_builder().parse(live_manifest_text()))


def fixture_manifest_text(code_dir=ROOT / "t4_smoke", **changes):
    """The live implementation manifest, describing the trainer code in ``code_dir`` and with top-level entries
    replaced by ``changes`` (TEST FIXTURE; unchanged it equals live_manifest_text())."""
    document = live_manifest_document()
    for name in tp.TRAINER_CODE:
        document["files"][f"t4_smoke/{name}"] = hashlib.sha256((Path(code_dir) / name).read_bytes()).hexdigest()
    document.update(changes)
    return _manifest_builder().render(document)


# ---- realistic unchanged-model DEV baselines (Amendment 3 item 3; Sol re-review B3)
# The real engine runs on the frozen DEV file through the real evaluate command; only the model backend and the
# package lookup are mocked. The backend's metadata simulates a COMPLIANT T4 run and says so in verification_scope;
# no model is loaded and no response is model output. These archives are SYNTHETIC TEST FIXTURES, never evidence.
SYNTHETIC_SCOPE = "SYNTHETIC CPU TEST FIXTURE: mocked backend on frozen DEV; no model was loaded or run"
SYNTHETIC_SHARDS = {f"model-0000{i}-of-00003.safetensors": f"{i}" * 64 for i in (1, 2, 3)}


def synthetic_t4_metadata(adapter=None):
    """Backend metadata with the keys hf_backend.HFBackend writes, holding the registered §2/§4 values (FIXTURE)."""
    return {"backend": "huggingface", "model_revision": ts.MODEL_REVISION, "tokenizer_revision": ts.MODEL_REVISION,
            "hardware": "Tesla T4", "gpu_total_bytes": 15828320256, "capability": list(tp.T4_CAPABILITY),
            "torch_cuda": "13.0", "quantization": dict(tp.QUANTIZATION, quant_method="bitsandbytes", load_in_8bit=False,
                                                       bnb_4bit_quant_storage="uint8"),
            "attention": tp.EXECUTION["attention"], "compute_dtype": tp.EXECUTION["compute_dtype"],
            "chat_template_sha256": tp.CHAT_TEMPLATE["digest"], "gpu_verified": True,
            "verification_scope": SYNTHETIC_SCOPE, "adapter": copy.deepcopy(adapter),
            "base_weight_shards_sha256": dict(SYNTHETIC_SHARDS)}


def synthetic_environment(names=None):
    """engine.environment() of a compliant Colab T4 runtime (FIXTURE): the registered pins, PEFT included."""
    from hinglish_pilot import engine, hf_backend
    pins = dict(hf_backend.PINS, **hf_backend.ADAPTER_PINS)
    return {"python": "3.12.12", "platform": "Linux", "machine": "x86_64",
            "packages": {name: pins.get(name) for name in (names or engine.PHASE2_PACKAGES)}}


def synthetic_t4_backend(adapter=None, **metadata_changes):
    from hinglish_pilot.engine import FakeBackend

    class SyntheticT4Backend(FakeBackend):  # FakeBackend.generate: fixed gold-blind strings, no inference
        metadata = dict(synthetic_t4_metadata(adapter), **metadata_changes)
        load_report = {"load_seconds": 0, "fixture": SYNTHETIC_SCOPE}

        def __init__(self, config=None, adapter_path=None):
            self.adapter_path = adapter_path
    return SyntheticT4Backend


@contextlib.contextmanager
def synthetic_t4_runtime(**metadata_changes):
    from hinglish_pilot import engine, hf_backend
    with mock.patch.object(hf_backend, "HFBackend", synthetic_t4_backend(None, **metadata_changes)), \
            mock.patch.object(engine, "environment", lambda names=None: synthetic_environment(names)):
        yield


def run_synthetic_baseline(store, manifest_text=None):
    """Phase2_Baseline_DEV's evaluate command under ``manifest_text`` (default: live) on DEV; returns its folder."""
    from t4_smoke import phase2_eval as pe
    store = Path(store)
    inputs = store / "inputs"
    inputs.mkdir(parents=True, exist_ok=True)
    (inputs / "dev.v2.json").write_bytes((ROOT / pe.FROZEN["dev"][0]).read_bytes())
    (inputs / "identities.json").write_text(json.dumps(pe.split_identities(ROOT)))
    (inputs / tp.MANIFEST_NAME).write_text(manifest_text or live_manifest_text())
    with synthetic_t4_runtime(), mock.patch("sys.stdout", io.StringIO()):
        code = pe.main(["evaluate", "--split", "dev", "--inputs", str(inputs), "--run-dir", str(store / "baseline_dev" / "base"),
                        "--implementation-manifest", str(inputs / tp.MANIFEST_NAME)])
    assert code == 0, "synthetic baseline fixture did not complete"
    return store / "baseline_dev"


def _baseline_template():
    if "baseline" not in _CACHE:
        folder = tempfile.mkdtemp(prefix="phase2_synthetic_baseline_")
        atexit.register(shutil.rmtree, folder, True)
        _CACHE["baseline"] = run_synthetic_baseline(folder)
    return _CACHE["baseline"]


def rewrite_archive(folder, change, fix_checksums=True):
    """Apply ``change(members)`` to the baseline ZIP in ``folder`` (dict name -> bytes), optionally recompute
    checksums.sha256, and re-record the new ZIP SHA-256 (a deliberately NONCOMPLIANT fixture)."""
    folder = Path(folder)
    archive = folder / "base_results.zip"
    with zipfile.ZipFile(archive) as z:
        members = {name: z.read(name) for name in z.namelist()}
    change(members)
    if fix_checksums:
        members["checksums.sha256"] = "".join(f"{hashlib.sha256(content).hexdigest()}  {name}\n"
                                              for name, content in members.items() if name != "checksums.sha256").encode()
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in members.items():
            z.writestr(name, content)
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    record = json.loads((folder / tp.BASELINE_RECORD).read_text())
    record["results_zip_sha256"] = digest
    (folder / tp.BASELINE_RECORD).write_text(json.dumps(record))
    return digest


def edit_json_member(name, edit):
    def change(members):
        value = json.loads(members[name])
        edit(value)
        members[name] = json.dumps(value).encode()
    return change


def write_baseline(folder, manifest_sha256=None, run_changes=None, **changes):
    """A complete, validating unchanged-model DEV baseline (record + real engine results ZIP) in ``folder``; returns
    the ZIP SHA-256. Built once under the live implementation manifest by run_synthetic_baseline (SYNTHETIC FIXTURE).
    ``manifest_sha256`` relabels the record for another manifest (tests that tamper with the trainer's manifest),
    ``run_changes`` edit the archive's run_manifest.json (checksums recomputed), ``changes`` the record."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    for path in _baseline_template().iterdir():
        if path.is_file():
            shutil.copyfile(path, folder / path.name)
    record = json.loads((folder / tp.BASELINE_RECORD).read_text())
    if manifest_sha256 is not None:
        record["implementation_manifest_sha256"] = manifest_sha256
    (folder / tp.BASELINE_RECORD).write_text(json.dumps(record))
    digest = record["results_zip_sha256"]
    if run_changes:
        digest = rewrite_archive(folder, edit_json_member("run_manifest.json", lambda run: run.update(run_changes)))
    if changes:
        record = json.loads((folder / tp.BASELINE_RECORD).read_text())
        record.update(changes)
        (folder / tp.BASELINE_RECORD).write_text(json.dumps(record))
    return digest


def write_metadata_only_baseline(folder, manifest_sha256):
    """The pre-Amendment-3 fixture Sol's B3 probe used: a record plus a ZIP of two metadata JSON files, without a
    dataset, journal, source snapshot or a single generation (NONCOMPLIANT FIXTURE; must be refused)."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    archive = folder / "base_results.zip"
    with zipfile.ZipFile(archive, "w") as z:
        z.writestr("run_manifest.json", json.dumps({"status": "COMPLETE", "mode": "phase2_dev", "completed": 120,
                                                    "unresolved": 0, "config_sha256": "c" * 64}))
        z.writestr("experiment_config.json", json.dumps({"adapter": None, "model_id": ts.MODEL_ID}))
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    record = {"schema": tp.BASELINE_SCHEMA, "run": "base", "split": "dev", "mode": "phase2_dev", "adapter": None,
              "model_id": ts.MODEL_ID, "model_revision": ts.MODEL_REVISION, "status": "COMPLETE", "completed": 120,
              "expected": 120, "unresolved": 0, "results_zip": "base_results.zip", "results_zip_sha256": digest,
              "implementation_manifest_sha256": manifest_sha256, "config_sha256": "c" * 64}
    (folder / tp.BASELINE_RECORD).write_text(json.dumps(record))
    return digest


class TrainerFixture:
    """inputs/ (manifest, exposure order, TRAIN bytes), a complete unchanged-DEV baseline and an empty train root."""

    def __init__(self, folder):
        self.root = Path(folder)
        self.inputs = self.root / "inputs"
        self.inputs.mkdir(parents=True)
        for name in ts.TRAIN_FILES:
            shutil.copyfile(ROOT / name, self.inputs / Path(name).name)
        shutil.copyfile(ROOT / tp.EXPOSURE_ORDER_PATH, self.inputs / "EXPOSURE_ORDER.json")
        self.write_manifest(fixture_manifest_text())
        self.train_root = self.root / "train"
        self.baseline = self.root / "baseline_dev"
        self.baseline_sha = write_baseline(self.baseline, self.manifest_sha)  # realistic synthetic DEV run
        self.log = self.train_root / tp.ATTEMPT_LOG

    def write_manifest(self, text):
        (self.inputs / tp.MANIFEST_NAME).write_text(text)
        self.manifest_sha = hashlib.sha256(text.encode()).hexdigest()

    def args(self, *extra):
        return ["train", "--train-root", str(self.train_root), "--inputs", str(self.inputs),
                "--baseline-dir", str(self.baseline), *extra]

    def entries(self):
        return tp.read_log(self.log)


# ---------------------------------------------------------------- Amendment 1 item 9: exposure order

class ExposureOrderTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = tp.phase2_dataset(ROOT)
        cls.families = tp.validate_phase2_data(cls.data)
        cls.document = json.loads((ROOT / tp.EXPOSURE_ORDER_PATH).read_text(encoding="utf-8"))

    def test_hash_input_is_exact_utf8_with_decimal_seed_and_pass(self):
        self.assertEqual(tp.order_input(44, 3, "TR-A-001"), b"phase2-D043:44:3:TR-A-001")
        self.assertEqual(tp.order_key(11, 2, "x"), hashlib.sha256("phase2-D043:11:2:x".encode("utf-8")).hexdigest())
        self.assertEqual(tp.order_input(11, 1, "ü"), "phase2-D043:11:1:ü".encode("utf-8"))
        for bad in ((True, 1), ("11", 1), (11.0, 1), (11, 0), (11, "1"), (-1, 1)):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                tp.order_input(*bad, "F1")

    def test_ties_are_broken_by_family_id(self):
        with mock.patch.object(tp, "order_key", return_value="0" * 64):
            self.assertEqual(tp.pass_order(["F3", "F1", "F2"], 11, 1), ["F1", "F2", "F3"])
        keys = {"A": "b", "B": "a", "C": "a"}
        with mock.patch.object(tp, "order_key", side_effect=lambda s, p, f: keys[f]):
            self.assertEqual(tp.pass_order(["A", "C", "B"], 11, 1), ["B", "C", "A"])

    def test_committed_exposure_order_is_current_and_complete(self):
        text = (ROOT / tp.EXPOSURE_ORDER_PATH).read_text(encoding="utf-8")
        self.assertEqual(text, tp.exposure_text(self.data), "Regenerate: python3 -B t4_smoke/train_phase2.py exposure-order")
        ids = sorted(f["family_id"] for f in self.families)
        self.assertEqual(sorted(self.document["seeds"]), ["11", "22", "33", "44", "55"])
        self.assertEqual(self.document["families_sha256"], self.data["families_sha256"])
        self.assertEqual(self.document["content_batch_families"], 8)
        for seed, entry in self.document["seeds"].items():
            self.assertEqual(entry["role"], "original" if int(seed) in tp.SLOTS else "reserve")
            self.assertEqual(len(entry["passes"]), 3)
            for number, ordered in enumerate(entry["passes"], 1):
                self.assertEqual(sorted(ordered), ids)
                expected = sorted(ids, key=lambda fid: (hashlib.sha256(f"phase2-D043:{seed}:{number}:{fid}".encode()).hexdigest(), fid))
                self.assertEqual(ordered, expected)
            self.assertEqual(entry["order_sha256"], tp.order_sha256(self.families, int(seed)))
            self.assertEqual(entry["order_sha256"], ts.digest(entry["passes"]))
        with mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(tp.main(["exposure-order", "--root", str(ROOT), "--check"]), 0)

    def test_training_checks_the_frozen_list(self):
        self.assertEqual(tp.check_exposure(self.document, self.data, 33), tp.order_sha256(self.families, 33))
        swapped = copy.deepcopy(self.document)
        first = swapped["seeds"]["22"]["passes"][1]
        first[0], first[1] = first[1], first[0]
        with self.assertRaisesRegex(tp.ProtocolFailure, "seed 22 differs"):
            tp.check_exposure(swapped, self.data, 22)
        missing = copy.deepcopy(self.document)
        del missing["seeds"]["55"]
        with self.assertRaisesRegex(tp.ProtocolFailure, "no list for seed 55"):
            tp.check_exposure(missing, self.data, 55)
        other = copy.deepcopy(self.data)
        other["families_sha256"] = "0" * 64
        with self.assertRaisesRegex(tp.ProtocolFailure, "other TRAIN data"):
            tp.check_exposure(self.document, other, 11)


# ---------------------------------------------------------------- Amendment 1 item 10: numerics (fake torch)

class FakeLoss:
    def __init__(self, value):
        self.value = value

    def detach(self):
        return self

    def __float__(self):
        return self.value

    def __truediv__(self, other):
        return self


class FakeScaler:
    def __init__(self, log, skip_at=None):
        self.log, self.skip_at, self.current, self.updates = log, skip_at, 65536.0, 0

    def get_scale(self):
        return self.current

    def scale(self, loss):
        return types.SimpleNamespace(backward=lambda: self.log.append(("backward", float(loss))))

    def unscale_(self, optimizer):
        self.log.append(("unscale",))

    def step(self, optimizer):
        self.log.append(("step", optimizer.param_groups[0]["lr"]))

    def update(self):
        self.updates += 1
        if self.updates == self.skip_at:
            self.current *= 0.5


def fake_trainer(*, losses=None, grad_norms=None, skip_at=None):
    log = []
    torch = types.SimpleNamespace(
        cuda=types.SimpleNamespace(synchronize=lambda: None, reset_peak_memory_stats=lambda: None, mem_get_info=lambda: (10, 20),
                                   max_memory_allocated=lambda: 1, max_memory_reserved=lambda: 2))
    norms = dict(grad_norms or {})

    def clip(parameters, clip_value):
        log.append(("clip", clip_value))
        return norms.get(len([e for e in log if e[0] == "clip"]), 0.5)

    torch.nn = types.SimpleNamespace(utils=types.SimpleNamespace(clip_grad_norm_=clip))
    trainer = tp.Phase2Trainer.__new__(tp.Phase2Trainer)
    trainer.torch, trainer.parameters, trainer.cursor = torch, [], 0
    trainer.attempted_steps = trainer.successful_steps = 0
    trainer.sequence = [{"family_id": f"F{i // 2:03d}", "form": "EC"[i % 2], "input_ids": [1, 2, 3, 4], "boundary_index": 1}
                        for i in range(960)]
    trainer.sampler = types.SimpleNamespace(take=lambda: None)
    trainer.scaler = FakeScaler(log, skip_at)
    trainer.optimizer = types.SimpleNamespace(param_groups=[{"lr": 0.0}], zero_grad=lambda set_to_none: log.append(("zero",)))
    values = dict(losses or {})
    counter = {"n": 0}

    def loss(example):
        counter["n"] += 1
        return FakeLoss(values.get(counter["n"], 1.0))

    trainer.loss = loss
    return trainer, log


class NumericsTests(unittest.TestCase):
    def test_scaler_is_pinned(self):
        torch = mock.MagicMock()
        tp.make_scaler(torch)
        torch.amp.GradScaler.assert_called_once_with("cuda", init_scale=65536.0, growth_factor=2.0, backoff_factor=0.5,
                                                     growth_interval=2000)
        sequence = [{}] * 960
        trainer = tp.Phase2Trainer(torch, mock.MagicMock(), [], True, sequence, mock.MagicMock())
        self.assertEqual(torch.amp.GradScaler.call_args_list[-1], mock.call("cuda", **tp.SCALER))
        self.assertIs(trainer.scaler, torch.amp.GradScaler.return_value)
        self.assertEqual(trainer.steps(), {"windows": 60, "attempted": 0, "successful": 0, "cursor": 0})
        with self.assertRaises(ValueError):
            tp.Phase2Trainer(torch, mock.MagicMock(), [], True, sequence[:-1], mock.MagicMock())

    def test_sixty_windows_sixty_successful_steps_lr_before_step_unscale_before_clip(self):
        trainer, log = fake_trainer()
        with mock.patch("sys.stdout", io.StringIO()):
            records = [trainer.update(u) for u in range(1, 61)]
        self.assertEqual(trainer.steps(), {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960})
        steps = [entry for entry in log if entry[0] == "step"]
        self.assertEqual(len(steps), 60)
        for u, (_, lr) in enumerate(steps, 1):
            self.assertEqual(lr, tp.lr_at(u))  # lr(u) was set before step u
        kinds = [entry[0] for entry in log]
        for u in range(60):
            window = kinds[u * 20:(u + 1) * 20]  # 16 backward, unscale, clip, step, zero
            self.assertEqual(window, ["backward"] * 16 + ["unscale", "clip", "step", "zero"])
        for u, record in enumerate(records, 1):
            self.assertEqual((record["attempted_step"], record["successful_step"]), (u, u))
            self.assertEqual((record["cursor_before"], record["cursor_after"]), ((u - 1) * 16, u * 16))
            self.assertEqual(record["pass_number"], (u - 1) // 20 + 1)
            self.assertFalse(record["skipped"])
        self.assertEqual(ts.summarize_updates(records, warmup=0, resume_after=0)["scaler_skips"], 0)
        with self.assertRaises(ValueError):  # no 61st window
            trainer.update(61)

    def test_scaler_skip_is_a_numerical_failure_and_nothing_continues(self):
        trainer, log = fake_trainer(skip_at=5)
        with mock.patch("sys.stdout", io.StringIO()):
            for u in range(1, 5):
                trainer.update(u)
            with self.assertRaisesRegex(tp.NumericalFailure, "GradScaler skipped") as caught:
                trainer.update(5)
        self.assertEqual(caught.exception.record["reason"].split(" (")[0], "GradScaler skipped the step")
        self.assertEqual(trainer.steps(), {"windows": 60, "attempted": 5, "successful": 4, "cursor": 80})
        with self.assertRaises(ValueError):  # neither replayed nor skipped: the run cannot continue
            trainer.update(6)
        with self.assertRaises(ValueError):
            trainer.update(5)

    def test_non_finite_loss_stops_before_backward_and_step(self):
        trainer, log = fake_trainer(losses={3: float("nan")})
        with self.assertRaisesRegex(tp.NumericalFailure, "non-finite loss") as caught:
            trainer.update(1)
        self.assertEqual([entry[0] for entry in log], ["backward", "backward"])
        self.assertEqual(caught.exception.record["cursor_at_failure"], 3)
        self.assertEqual(caught.exception.record["microbatch_losses"][-1], "nan")
        self.assertEqual(trainer.steps()["successful"], 0)

    def test_non_finite_gradient_stops_before_the_step(self):
        for value in (float("inf"), float("nan")):
            trainer, log = fake_trainer(grad_norms={1: value})
            with self.subTest(value=value), self.assertRaisesRegex(tp.NumericalFailure, "non-finite gradient"):
                trainer.update(1)
            self.assertNotIn("step", [entry[0] for entry in log])
            self.assertEqual(log[16:18], [("unscale",), ("clip", 1.0)])

    def test_non_finite_saved_parameters_are_detected(self):
        class Flag:
            def __init__(self, ok):
                self.ok = ok

            def all(self):
                return self.ok

        torch = types.SimpleNamespace(isfinite=lambda tensor: Flag(tensor != "bad"))
        self.assertEqual(tp.nonfinite_tensors(torch, [("a", "ok"), ("b", "bad")]), ["b"])
        self.assertEqual(tp.nonfinite_tensors(torch, [("a", "ok")]), [])



# ---------------------------------------------------------------- Amendment 2 item 7 (R4): authenticated inputs

class AuthenticatedInputTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.fixture = TrainerFixture(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def test_frozen_constants_match_the_committed_files(self):
        self.assertEqual(tp.EXPOSURE_ORDER_SHA256, hashlib.sha256((ROOT / tp.EXPOSURE_ORDER_PATH).read_bytes()).hexdigest())
        self.assertEqual(tp.TRAIN_FAMILIES_SHA256, tp.phase2_dataset(ROOT)["families_sha256"])
        self.assertEqual(tp.load_verified_train(ROOT / "phase2"), tp.phase2_dataset(ROOT))
        self.assertEqual(tp.load_verified_train(self.fixture.inputs)["families_sha256"], tp.TRAIN_FAMILIES_SHA256)

    def test_changed_train_bytes_are_a_protocol_error_even_with_a_recomputed_family_hash(self):
        """Sol R4 probe: a TRAIN completion changed and families_sha256 recomputed must not be accepted."""
        path = self.fixture.inputs / "train_A.v2.json"
        families = json.loads(path.read_bytes())
        families[5]["reference_solution_en"] = families[5]["reference_solution_en"] + " "
        path.write_text(json.dumps(families))
        with self.assertRaisesRegex(tp.ProtocolError, "frozen SHA-256"):
            tp.load_verified_train(self.fixture.inputs)
        data = tp.phase2_dataset(ROOT)
        data["families"][5]["completion"] += " "
        data["families_sha256"] = ts.digest(data["families"])  # self-consistent, but not the frozen families
        tp.validate_phase2_data(data)  # the self-consistency check alone accepts it (Sol's probe) ...
        self.assertNotEqual(data["families_sha256"], tp.TRAIN_FAMILIES_SHA256)  # ... the frozen hash does not
        with self.assertRaisesRegex(tp.ProtocolError, "other TRAIN data"):
            tp.verify_exposure(ROOT / "phase2", data, 11)

    def test_exposure_order_must_have_its_frozen_hash(self):
        data = tp.load_verified_train(self.fixture.inputs)
        self.assertEqual(tp.verify_exposure(self.fixture.inputs, data, 22),
                         (tp.order_sha256(data["families"], 22), tp.EXPOSURE_ORDER_SHA256))
        path = self.fixture.inputs / "EXPOSURE_ORDER.json"
        document = json.loads(path.read_text())
        document["seeds"]["22"]["passes"][0].reverse()
        document["seeds"]["22"]["order_sha256"] = ts.digest(document["seeds"]["22"]["passes"])
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(tp.ProtocolError, "frozen"):
            tp.verify_exposure(self.fixture.inputs, data, 22)

    def test_manifest_is_checked_against_the_running_code(self):
        manifest, digest = tp.verify_implementation(self.fixture.inputs)
        self.assertEqual(digest, self.fixture.manifest_sha)
        text = fixture_manifest_text()
        document = json.loads(text.split("```json\n")[1].split("\n```")[0])
        for change, pattern in ((lambda d: d["files"].update({"t4_smoke/train_phase2.py": "0" * 64}), "train_phase2.py"),
                                (lambda d: d["files"].update({"phase2/train_B.v2.json": "0" * 64}), "train_B"),
                                (lambda d: d["training"].update(recipe_sha256="0" * 64), "recipe"),
                                (lambda d: d["dependencies"].update(torch_build="2.5.1+cu121"), "torch build"),
                                (lambda d: d.update(schema="other"), "schema")):
            changed = json.loads(json.dumps(document))
            change(changed)
            self.fixture.write_manifest("```json\n" + json.dumps(changed) + "\n```\n")
            with self.subTest(pattern=pattern), self.assertRaisesRegex(tp.ProtocolError, pattern):
                tp.verify_implementation(self.fixture.inputs)


# ---------------------------------------------------------------- Amendment 2 item 2 (R3): failure classes

def write_attempt(folder, *, status="COMPLETE", failure_class=None, **final_changes):
    folder.mkdir(parents=True, exist_ok=True)
    report = {"status": status, "failure_class": failure_class, "error": "Traceback\nValueError: boom"}
    (folder / "train_report.json").write_text(json.dumps(report))
    if status == "COMPLETE":
        final = {"status": "COMPLETE", "updates": 60, "steps": {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960},
                 "scaler_skips": 0, "saved_parameters_finite": True, "resumed": False, "valid_for_gate": True}
        final.update(final_changes)
        (folder / "final_adapter.json").write_text(json.dumps(final))


def torch_oom():
    return type("OutOfMemoryError", (RuntimeError,), {"__module__": "torch.cuda"})("CUDA out of memory")


def hub_error():
    return type("HfHubHTTPError", (OSError,), {"__module__": "huggingface_hub.errors"})("502 Bad Gateway")


def network_error():
    return type("ProtocolError", (Exception,), {"__module__": "urllib3.exceptions"})("Connection aborted")


class FailureClassTests(unittest.TestCase):
    def test_classification_follows_the_typed_list(self):
        """Amendment 2 item 2 (Sol R3 probes included)."""
        cases = [(tp.NumericalFailure("x"), "training", "numerical"),
                 # protocol: every ProtocolError, wherever detected, and every unlisted exception
                 (tp.ProtocolError("hash mismatch"), "reload", "protocol"), (tp.ProtocolError("x"), "final", "protocol"),
                 (TypeError("bug"), "training", "protocol"), (AssertionError("hash mismatch"), "reload", "protocol"),
                 (ValueError("targets"), "labels", "protocol"), (ValueError("252 modules"), "model", "protocol"),
                 (RuntimeError("CUDA error: illegal memory access"), "training", "protocol"),
                 (KeyError("x"), "checkpoint", "protocol"), (MemoryError("host"), "training", "protocol"),
                 # infrastructure: the typed list only, at any stage
                 (OSError("Drive I/O"), "data", "infrastructure"), (FileNotFoundError("Drive"), "verify", "infrastructure"),
                 (OSError("download"), "model", "infrastructure"), (torch_oom(), "training", "infrastructure"),
                 (hub_error(), "tokenizer", "infrastructure"), (network_error(), "model", "infrastructure"),
                 (TimeoutError("read timed out"), "tokenizer", "infrastructure"),
                 (tp.CheckpointWriteError("failed checkpoint write"), "checkpoint", "infrastructure"),
                 (KeyboardInterrupt(), "training", "infrastructure")]
        for error, stage, expected in cases:
            with self.subTest(error=repr(error), stage=stage):
                self.assertEqual(tp.classify_failure(error, stage), expected)
        self.assertEqual(tp.infrastructure_kind(torch_oom()), "CUDA out-of-memory")
        self.assertEqual(tp.infrastructure_kind(OSError("x")), "Drive or filesystem OSError")
        self.assertEqual(tp.infrastructure_kind(hub_error()), "network or Hub download error")
        self.assertIsNone(tp.infrastructure_kind(TypeError("bug")))
        self.assertEqual(set(tp.INFRASTRUCTURE_KINDS), {"runtime disconnect or kill", "CUDA out-of-memory",
                                                       "Drive or filesystem OSError", "network or Hub download error",
                                                       "failed checkpoint write"})
        self.assertTrue(issubclass(tp.ProtocolError, ValueError))

    def test_checkpoint_write_failures_are_typed(self):
        for error in (OSError("No space left on device"), RuntimeError("[enforce fail at inline_container.cc:595] PytorchStreamWriter failed writing file"),
                      type("SafetensorError", (Exception,), {})("write failed")):
            with self.subTest(error=repr(error)), self.assertRaises(tp.CheckpointWriteError):
                with tp.checkpoint_write("checkpoint"):
                    raise error
        for error in (TypeError("bug"), tp.ProtocolError("x"), RuntimeError("CUDA error")):
            with self.subTest(error=repr(error)), self.assertRaises(type(error)):
                with tp.checkpoint_write("checkpoint"):
                    raise error

    def test_smoke_code_assertions_become_protocol_errors_at_detection(self):
        with self.assertRaisesRegex(tp.ProtocolError, "labels: targets differ"):
            with tp.protocol_assertions("labels"):
                raise ValueError("targets differ")
        with self.assertRaises(OSError):
            with tp.protocol_assertions("data"):
                raise OSError("Drive")
        with mock.patch.object(ts, "build_examples", side_effect=ValueError("Example exceeds 1024 tokens")), \
                self.assertRaisesRegex(tp.ProtocolError, "1024"):
            tp.prepare_examples(mock.MagicMock(), [])

    def test_restore_checkpoint_digest_and_identity_checks_raise_protocol_errors(self):
        """Sol R3: an identity or digest mismatch found at reload halts the study."""
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder)
            (out / "checkpoint").mkdir()
            report = {"data_sha256": "d", "arm": "EC", "seed": 11, "attempt": 1, "order_sha256": "o", "initial_adapter_sha256": "i"}
            meta = dict(report, recipe_sha256=ts.digest(tp.RECIPE), parameter_names=[], completed_updates=10)
            (out / "checkpoint" / "meta.json").write_text(json.dumps(dict(meta, order_sha256="other")))
            trainer = types.SimpleNamespace(trainable=[])
            with self.assertRaisesRegex(tp.ProtocolError, "different order_sha256") as caught:
                tp.restore_checkpoint(mock.MagicMock(), trainer, out, report)
            self.assertEqual(tp.classify_failure(caught.exception, "reload"), "protocol")
            (out / "checkpoint" / "meta.json").write_text(json.dumps(dict(meta, parameter_names=["x"])))
            with self.assertRaisesRegex(tp.ProtocolError, "parameter order"):
                tp.restore_checkpoint(mock.MagicMock(), trainer, out, report)

    def test_attempt_outcomes_from_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            self.assertEqual(tp.attempt_outcome(root / "none")[0], "infrastructure")
            write_attempt(root / "started", status="STARTED")
            self.assertEqual(tp.attempt_outcome(root / "started"), ("infrastructure", "run did not finish (status STARTED): runtime disconnect or crash"))
            for cls in tp.FAILURE_CLASSES:
                write_attempt(root / cls, status="FAILED", failure_class=cls)
                self.assertEqual(tp.attempt_outcome(root / cls), (cls, "ValueError: boom"))
            write_attempt(root / "unknown", status="FAILED", failure_class="mystery")
            self.assertEqual(tp.attempt_outcome(root / "unknown")[0], "protocol")  # unknown never earns a retry
            write_attempt(root / "valid")
            self.assertEqual(tp.attempt_outcome(root / "valid")[0], "valid")
            write_attempt(root / "resumed", resumed=True, valid_for_gate=False)
            self.assertEqual(tp.attempt_outcome(root / "resumed")[0], "resumed_invalid")
            write_attempt(root / "short", steps={"windows": 60, "attempted": 60, "successful": 59, "cursor": 960})
            self.assertEqual(tp.attempt_outcome(root / "short")[0], "protocol")
            write_attempt(root / "nosave")
            (root / "nosave" / "final_adapter.json").unlink()
            self.assertEqual(tp.attempt_outcome(root / "nosave")[0], "infrastructure")


class FakeRunTrainer:
    """Stands in for Phase2Trainer inside run_train; ``fail_at`` raises ``error`` (default NumericalFailure) there."""
    fail_at, short, error = None, False, None

    def __init__(self, torch, model, trainable, keep, sequence, sampler):
        self.scaler = types.SimpleNamespace(state_dict=lambda: {"scale": 65536.0})
        self.attempted = self.successful = 0

    def steps(self):
        successful = self.successful - (1 if self.short and self.successful == 60 else 0)
        return {"windows": 60, "attempted": self.attempted, "successful": successful, "cursor": self.successful * 16}

    def update(self, number):
        self.attempted += 1
        if number == self.fail_at:
            raise self.error or tp.NumericalFailure(f"NUMERICAL FAILURE at update {number}: GradScaler skipped the step",
                                                    {"update": number, "reason": "GradScaler skipped the step"})
        self.successful += 1
        return {"update": number, "seconds": 1.0, "microbatch_losses": [1.0], "skipped": False, "grad_norm": 0.5,
                "min_free_bytes": 1, "peak_allocated_bytes": 1, "peak_reserved_bytes": 1, "input_tokens": 1, "supervised_tokens": 1}


# ---------------------------------------------------------------- the trainer entry point (R3, R4, R5, R6, R8)

class TrainerEntryTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.fixture = TrainerFixture(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def train(self, trainer_class=None, *extra, stack="Tesla T4", patches=()):
        """Run ``train`` with the GPU parts mocked; returns (exit code, stderr, stdout)."""
        torch = mock.MagicMock()
        torch.cuda.mem_get_info.return_value = (1, 2)
        sampler = mock.MagicMock()
        sampler.return_value.start.return_value.error = None
        sampler.return_value.start.return_value.take.return_value = None
        audit = {"passed": True, "arms": {}, "max_input_tokens": 5, "last_target_is_im_end": True}
        err, out = io.StringIO(), io.StringIO()
        stack_check = mock.patch.object(tp, "check_stack", return_value=stack) if isinstance(stack, str) else \
            mock.patch.object(tp, "check_stack", side_effect=stack)
        with contextlib.ExitStack() as stack_context:
            for patch in (stack_check, mock.patch.object(ts, "gpu_setup", return_value=(torch, [])),
                          mock.patch.object(ts, "environment", return_value={}), mock.patch.object(ts, "MemorySampler", sampler),
                          mock.patch.object(ts, "load_tokenizer", return_value=mock.MagicMock(chat_template="t")),
                          # B2 boundary checks need the Hub; dedicated tests below run them for real
                          mock.patch.object(tp, "verify_hub_files", return_value=dict(tp.HUB_FILES)),
                          mock.patch.object(tp, "verify_chat_template", return_value=tp.CHAT_TEMPLATE["digest"]),
                          mock.patch.object(tp, "prepare_examples", return_value=({}, audit)),
                          mock.patch.object(tp, "run_examples", return_value=[{"family_id": "F", "form": "E"}] * 960),
                          mock.patch.object(tp, "load_model", return_value=("model", [], True, {})),
                          mock.patch.object(tp, "weight_shard_hashes", return_value={"model.safetensors": "h"}),
                          mock.patch.object(ts, "tensors_digest", return_value="init"),
                          mock.patch.object(tp, "Phase2Trainer", trainer_class or type("T", (FakeRunTrainer,), {})),
                          mock.patch.object(tp, "save_checkpoint"),
                          mock.patch.object(tp, "save_final_adapter", return_value={"adapter_model_sha256": "a" * 64,
                                                                                    "adapter_config_sha256": "b" * 64,
                                                                                    "saved_parameters_finite": True}),
                          mock.patch("sys.stderr", err), mock.patch("sys.stdout", out), *patches):
                stack_context.enter_context(patch)
            code = tp.main(self.fixture.args(*extra))
        return code, err.getvalue(), out.getvalue()

    def report(self, arm="EC", seed=11, attempt=1):
        return json.loads((tp.attempt_dir(self.fixture.train_root, arm, seed, attempt) / "train_report.json").read_text())

    def outcomes(self):
        return [(e["event"], e["arm"], e["seed"], e["attempt"], e.get("outcome")) for e in self.fixture.entries()]

    def test_valid_run_logs_start_and_finish_with_the_identity(self):
        code, err, _ = self.train()
        self.assertEqual(code, 0, err)
        self.assertEqual(self.outcomes(), [("start", "EC", 11, 1, None), ("finish", "EC", 11, 1, "valid")])
        identity = self.fixture.entries()[0]["identity"]
        self.assertEqual((identity["implementation_manifest_sha256"], identity["baseline_dev_results_zip_sha256"]),
                         (self.fixture.manifest_sha, self.fixture.baseline_sha))
        self.assertEqual(identity["stack"], dict(ts.PINS, torch=ts.TORCH_BUILD))
        final = json.loads((tp.attempt_dir(self.fixture.train_root, "EC", 11, 1) / "final_adapter.json").read_text())
        self.assertEqual(final["steps"], {"windows": 60, "attempted": 60, "successful": 60, "cursor": 960})
        self.assertEqual((final["implementation_manifest_sha256"], final["baseline_dev_results_zip_sha256"], final["slot"]),
                         (self.fixture.manifest_sha, self.fixture.baseline_sha, 11))
        self.assertEqual(final["exposure_order_file_sha256"], tp.EXPOSURE_ORDER_SHA256)
        self.assertEqual(final["order_sha256"], json.loads((ROOT / tp.EXPOSURE_ORDER_PATH).read_text())["seeds"]["11"]["order_sha256"])
        self.assertEqual(final["data_sha256"], tp.TRAIN_FAMILIES_SHA256)
        self.assertEqual(tp.valid_run_problems(final), [])
        code, err, _ = self.train()  # the plan moves on by itself: EC -> ER within slot 11
        self.assertEqual(self.outcomes()[-1], ("finish", "ER", 11, 1, "valid"))

    def test_no_baseline_or_a_baseline_under_another_manifest_refuses_before_any_attempt(self):
        """Amendment 2 item 6 (R8)."""
        (self.fixture.baseline / tp.BASELINE_RECORD).unlink()
        code, err, _ = self.train()
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("Phase2_Baseline_DEV", err)
        self.assertFalse(self.fixture.log.exists())
        for changes, run_changes, pattern in (({"implementation_manifest_sha256": "0" * 64}, None, "another|not"),
                                              ({"completed": 119}, None, "not a complete baseline"),
                                              ({}, {"status": "INCOMPLETE"}, "not a complete unchanged-model DEV run"),
                                              ({"results_zip_sha256": "0" * 64}, None, "differs from its recorded")):
            with self.subTest(changes=changes, run_changes=run_changes):
                write_baseline(self.fixture.baseline, self.fixture.manifest_sha, run_changes, **changes)
                code, err, _ = self.train()
                self.assertEqual(code, tp.EXIT_CODES["refused"])
                self.assertRegex(err, pattern)
                self.assertFalse(self.fixture.log.exists())
        write_baseline(self.fixture.baseline, self.fixture.manifest_sha)
        self.assertEqual(self.train()[0], 0)

    def test_stack_mismatch_or_non_t4_refuses_before_the_attempt_opens(self):
        """Amendment 2 item 3 (R5): no override exists and nothing is logged."""
        self.assertNotIn("--allow-stack-mismatch", (ROOT / "t4_smoke" / "train_phase2.py").read_text())
        code, err, _ = self.train(None, stack=tp.Refused("D021 stack mismatch: torch 2.11.0+cu130 expected"))
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("no attempt was opened", err)
        self.assertFalse(self.fixture.log.exists())
        self.assertFalse(tp.attempt_dir(self.fixture.train_root, "EC", 11, 1).exists())
        with mock.patch.object(ts, "versions", return_value=dict(ts.PINS, torch="2.5.1+cu121")), \
                mock.patch.object(tp, "gpu_name", return_value=("Tesla T4", (7, 5))):
            with self.assertRaisesRegex(tp.Refused, "stack mismatch"):
                tp.check_stack()
        with mock.patch.object(ts, "versions", return_value=dict(ts.PINS, torch=ts.TORCH_BUILD)):
            for name in (("NVIDIA L4", (8, 9)), (None, None), ("NVIDIA A100-SXM4-40GB", (8, 0))):
                with self.subTest(gpu=name), mock.patch.object(tp, "gpu_name", return_value=name), \
                        self.assertRaisesRegex(tp.Refused, "Tesla T4 required"):
                    tp.check_stack()
            with mock.patch.object(tp, "gpu_name", return_value=("Tesla T4", (7, 5))):
                self.assertEqual(tp.check_stack(), "Tesla T4")
        with mock.patch.object(ts, "gpu_setup") as setup:
            self.train(None, stack=tp.Refused("Tesla T4 required"))
        setup.assert_not_called()

    def test_operator_cannot_choose_the_run(self):
        """Amendment 2 item 4 (R6): --arm/--seed/--slot/--attempt only assert the plan's choice."""
        for extra in (["--arm", "EE", "--seed", "11", "--slot", "11", "--attempt", "1"],
                      ["--arm", "EC", "--seed", "22", "--slot", "22", "--attempt", "1"],
                      ["--arm", "EC", "--seed", "11", "--slot", "11", "--attempt", "2"]):
            with self.subTest(extra=extra):
                code, err, _ = self.train(None, *extra)
                self.assertEqual(code, tp.EXIT_CODES["refused"])
                self.assertIn("authorises EC seed 11 slot 11 attempt 1", err)
                self.assertFalse(self.fixture.log.exists())
        code, err, _ = self.train(None, "--arm", "EC", "--seed", "11", "--slot", "11", "--attempt", "1")
        self.assertEqual(code, 0, err)
        with mock.patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
            tp.main(self.fixture.args("--seed", "12"))

    def test_changed_configuration_or_implementation_is_refused(self):
        """Amendment 2 item 7 (R4): every attempt must have the identity of the earlier attempts."""
        self.assertEqual(self.train(None, patches=[mock.patch.object(FakeRunTrainer, "fail_at", 1),
                                                   mock.patch.object(FakeRunTrainer, "error", OSError("Drive gone"))])[0], 1)
        self.assertEqual(self.outcomes()[-1], ("finish", "EC", 11, 1, "infrastructure"))
        text = fixture_manifest_text() + "\n<!-- regenerated -->\n"
        self.fixture.write_manifest(text)
        write_baseline(self.fixture.baseline, self.fixture.manifest_sha)
        code, err, _ = self.train()
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("differs from earlier attempts", err)
        self.assertIn("implementation_manifest_sha256", err)
        self.assertEqual(len(self.fixture.entries()), 2)
        original = tp.attempt_identity(self.fixture.inputs, "x")
        with mock.patch.object(tp, "RECIPE", dict(tp.RECIPE, lr=2e-4)):  # a changed recipe is a changed identity
            self.assertNotEqual(tp.attempt_identity(self.fixture.inputs, "x")["recipe_sha256"], original["recipe_sha256"])

    def test_each_optional_run_assertion_can_be_supplied_independently(self):
        for option, value in (("--arm", "EC"), ("--seed", "11"), ("--slot", "11"), ("--attempt", "1")):
            with self.subTest(option=option):
                shutil.rmtree(self.fixture.train_root, ignore_errors=True)
                code, err, _ = self.train(None, option, value)
                self.assertEqual(code, 0, err)
                self.assertEqual(self.outcomes()[-1], ("finish", "EC", 11, 1, "valid"))
        shutil.rmtree(self.fixture.train_root, ignore_errors=True)
        code, err, _ = self.train(None, "--arm", "EE")
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("authorises EC", err)
        self.assertFalse(self.fixture.log.exists())

    def test_system_exit_records_infrastructure_at_setup_and_during_training(self):
        for stage in ("setup", "training"):
            with self.subTest(stage=stage):
                shutil.rmtree(self.fixture.train_root, ignore_errors=True)
                trainer = type("T", (FakeRunTrainer,), {"fail_at": 2, "error": SystemExit(9)})
                patches = [mock.patch.object(ts, "gpu_setup", side_effect=SystemExit(9))] if stage == "setup" else []
                code, _, _ = self.train(trainer, patches=patches)
                self.assertEqual(code, tp.EXIT_CODES["infrastructure"])
                report = self.report()
                self.assertEqual((report["status"], report["failure_stage"], report["failure_class"], report["failure_kind"]),
                                 ("FAILED", stage, "infrastructure", "runtime disconnect or kill"))
                self.assertEqual(self.outcomes()[-1], ("finish", "EC", 11, 1, "infrastructure"))
                self.assertEqual(tp.next_run(tp.plan(self.fixture.entries()))["attempt"], 2)

    def test_manifest_train_and_exposure_are_verified_inside_the_attempt(self):
        """R4: a manifest that does not describe the running trainer, changed TRAIN bytes or a changed exposure order
        are protocol failures detected at the trainer entry point; the study halts."""
        cases = (("manifest", lambda: self.fixture.write_manifest(fixture_manifest_text(code_dir=self.stale_code()))),
                 ("train", lambda: (self.fixture.inputs / "train_B.v2.json").write_bytes(
                     (ROOT / "phase2" / "train_B.v2.json").read_bytes().replace(b"FINAL", b"Final", 1))),
                 ("exposure", lambda: (self.fixture.inputs / "EXPOSURE_ORDER.json").write_text(
                     (ROOT / tp.EXPOSURE_ORDER_PATH).read_text() + " ")))
        for name, tamper in cases:
            with self.subTest(name=name):
                shutil.rmtree(self.fixture.train_root, ignore_errors=True)
                shutil.rmtree(self.fixture.inputs)
                self.fixture = TrainerFixture(Path(self.folder.name) / name)
                tamper()
                write_baseline(self.fixture.baseline, self.fixture.manifest_sha)
                code, err, _ = self.train()
                self.assertEqual(code, tp.EXIT_CODES["protocol"])
                report = self.report()
                self.assertEqual((report["failure_class"], report["study_halt"]), ("protocol", True))
                self.assertIn(report["failure_stage"], ("verify", "data"))
                self.assertNotIn("mask_audit", report)  # stopped before any tokenizer, label or model work
                self.assertIn("ProtocolError", report["error_type"])
                self.assertEqual(self.outcomes()[-1], ("finish", "EC", 11, 1, "protocol"))
                self.assertIn("THE STUDY HALTS", err)
                code, err, _ = self.train()
                self.assertEqual(code, tp.EXIT_CODES["refused"])
                self.assertIn("THE STUDY HALTS", err)

    def stale_code(self):
        folder = Path(self.folder.name) / "stale_code"
        folder.mkdir(exist_ok=True)
        for name in tp.TRAINER_CODE:
            (folder / name).write_bytes((ROOT / "t4_smoke" / name).read_bytes() + (b"\n# old\n" if name == "labels.py" else b""))
        return folder

    def test_drive_error_at_the_data_stage_is_infrastructure(self):
        """Sol R3 probe: OSError('Drive I/O') while reading data earns the one permitted retry."""
        code, err, _ = self.train(None, patches=[mock.patch.object(tp, "load_verified_train", side_effect=OSError("Drive I/O"))])
        self.assertEqual(code, tp.EXIT_CODES["infrastructure"])
        report = self.report()
        self.assertEqual((report["failure_stage"], report["failure_class"], report["failure_kind"]),
                         ("data", "infrastructure", "Drive or filesystem OSError"))
        self.assertNotIn("study_halt", report)
        self.assertEqual(tp.next_run(tp.plan(self.fixture.entries()))["attempt"], 2)

    def test_programming_error_halts_the_study(self):
        """Sol R3 probe: TypeError('bug') during training is protocol, never a retry or a reserve."""
        trainer = type("T", (FakeRunTrainer,), {"fail_at": 4, "error": TypeError("bug")})
        code, err, _ = self.train(trainer)
        self.assertEqual(code, tp.EXIT_CODES["protocol"])
        report = self.report()
        self.assertEqual((report["failure_class"], report["study_halt"], report["failure_stage"]), ("protocol", True, "training"))
        with self.assertRaises(tp.StudyHalted):
            tp.next_run(tp.plan(self.fixture.entries()))

    def test_cuda_oom_and_checkpoint_write_failure_are_infrastructure(self):
        for error, kind in ((torch_oom(), "CUDA out-of-memory"), (tp.CheckpointWriteError("failed checkpoint write"), "failed checkpoint write")):
            with self.subTest(kind=kind):
                shutil.rmtree(self.fixture.train_root, ignore_errors=True)
                trainer = type("T", (FakeRunTrainer,), {"fail_at": 2, "error": error})
                code, _, _ = self.train(trainer)
                self.assertEqual(code, tp.EXIT_CODES["infrastructure"])
                self.assertEqual((self.report()["failure_class"], self.report()["failure_kind"]), ("infrastructure", kind))
                self.assertEqual(self.report()["oom"], kind == "CUDA out-of-memory")

    def test_numerical_failure_halts_the_study(self):
        code = self.train(type("T", (FakeRunTrainer,), {"fail_at": 3}))[0]
        report = self.report()
        self.assertEqual(code, tp.EXIT_CODES["numerical"])
        self.assertEqual((report["status"], report["failure_class"], report["study_halt"], report["valid_for_gate"]),
                         ("FAILED", "numerical", True, False))
        self.assertEqual(report["failed_update"]["update"], 3)
        self.assertEqual(report["steps"], {"windows": 60, "attempted": 3, "successful": 2, "cursor": 32})
        self.assertEqual(len(report["updates"]), 2)
        self.assertFalse((tp.attempt_dir(self.fixture.train_root, "EC", 11, 1) / "final_adapter.json").exists())
        self.assertEqual(self.outcomes()[-1], ("finish", "EC", 11, 1, "numerical"))

    def test_step_count_mismatch_is_a_protocol_failure(self):
        code, err, _ = self.train(type("T", (FakeRunTrainer,), {"short": True}))
        self.assertEqual(code, tp.EXIT_CODES["protocol"])
        self.assertTrue(self.report()["study_halt"])
        self.assertIn("60 successful steps", self.report()["error"])
        self.assertIn("THE STUDY HALTS", err)

    def test_existing_attempt_evidence_is_never_overwritten(self):
        folder = tp.attempt_dir(self.fixture.train_root, "EC", 11, 1)
        folder.mkdir(parents=True)
        (folder / "train_report.json").write_text(json.dumps({"status": "FAILED"}))
        code, err, _ = self.train()
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("never overwritten", err)
        self.assertFalse(self.fixture.log.exists())

    def test_resume_is_engineering_only_and_never_valid(self):
        trainer = type("T", (FakeRunTrainer,), {"fail_at": 15, "error": OSError("Drive gone")})
        self.train(trainer)
        code, err, _ = self.train(None, "--resume")
        self.assertEqual(code, tp.EXIT_CODES["refused"])  # no checkpoint was left (save_checkpoint is mocked)
        (tp.attempt_dir(self.fixture.train_root, "EC", 11, 1) / "checkpoint").mkdir()
        def restored(torch, trainer, out, report):
            trainer.attempted = trainer.successful = 10
            return 10, {"passed": True}

        with mock.patch.object(tp, "restore_checkpoint", side_effect=restored):
            code, err, _ = self.train(None, "--resume")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.outcomes()[-2:], [("resume_start", "EC", 11, 1, None), ("resume_finish", "EC", 11, 1, "resumed_invalid")])
        self.assertEqual(tp.next_run(tp.plan(self.fixture.entries()))["attempt"], 2)


# ---------------------------------------------------------------- attempt log and seed plan (Amendment 1 item 11, Amendment 2 item 4)

class AttemptLogTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.log = self.root / tp.ATTEMPT_LOG

    def tearDown(self):
        self.folder.cleanup()

    def attempt(self, arm, seed, slot, outcome):
        """Log the plan's next run, which must be (arm, seed, slot)."""
        action = tp.next_run(self.plan())
        self.assertEqual((action["kind"], action["arm"], action["seed"], action["slot"]), ("train", arm, seed, slot))
        tp.log_event(self.log, "start", arm=arm, seed=seed, slot=slot, attempt=action["attempt"], identity=IDENTITY)
        tp.log_event(self.log, "finish", arm=arm, seed=seed, slot=slot, attempt=action["attempt"], outcome=outcome)
        return action["attempt"]

    def plan(self):
        return tp.plan(tp.read_log(self.log))

    def start(self, arm, seed, slot, attempt=1, identity=IDENTITY):
        return {"n": 99, "event": "start", "arm": arm, "seed": seed, "slot": slot, "attempt": attempt, "identity": identity}

    def test_log_is_append_only_and_hash_chained(self):
        tp.log_event(self.log, "start", arm="EC", seed=11, slot=11, attempt=1, identity=IDENTITY)
        tp.log_event(self.log, "finish", arm="EC", seed=11, slot=11, attempt=1, outcome="valid")
        first = self.log.read_text().splitlines()
        tp.log_event(self.log, "start", arm="ER", seed=11, slot=11, attempt=1, identity=IDENTITY)
        self.assertEqual(self.log.read_text().splitlines()[:2], first)  # earlier lines never rewritten
        self.assertEqual([e["n"] for e in tp.read_log(self.log)], [1, 2, 3])
        lines = self.log.read_text().splitlines()
        edited = json.loads(lines[1])
        edited["outcome"] = "infrastructure"
        self.log.write_text("\n".join([lines[0], json.dumps(edited), lines[2]]) + "\n")
        with self.assertRaisesRegex(tp.ProtocolFailure, "edited"):
            tp.read_log(self.log)
        self.log.write_text("\n".join([lines[0], lines[2]]) + "\n")
        with self.assertRaisesRegex(tp.ProtocolFailure, "broken"):
            tp.read_log(self.log)

    def test_next_run_follows_the_registered_order(self):
        """Amendment 2 item 4: slots 11 -> 22 -> 33, arms EC -> ER -> EE, no operator choice."""
        order = []
        while True:
            action = tp.next_run(self.plan())
            if action["kind"] == "complete":
                break
            order.append((action["slot"], action["arm"]))
            self.attempt(action["arm"], action["seed"], action["slot"], "valid")
        self.assertEqual(order, [(slot, arm) for slot in (11, 22, 33) for arm in ("EC", "ER", "EE")])
        current = self.plan()
        self.assertTrue(current["final"])
        self.assertEqual((current["S"], current["retained"]), (3, [(11, 11), (22, 22), (33, 33)]))
        self.assertEqual(tp.next_run(current), {"kind": "complete", "S": 3, "retained": [(11, 11), (22, 22), (33, 33)]})
        with mock.patch("sys.stdout", io.StringIO()) as out:
            tp.main(["plan", "--train-root", str(self.root)])
        self.assertIn("S = 3", out.getvalue())
        self.assertFalse(hasattr(tp, "next_action"))  # the operator-chosen ARM/SLOT interface is gone

    def test_a_slot_is_fully_settled_before_the_next_starts(self):
        self.attempt("EC", 11, 11, "valid")
        self.attempt("ER", 11, 11, "infrastructure")
        self.assertEqual(tp.next_run(self.plan())["arm"], "ER")  # retry before anything else
        self.attempt("ER", 11, 11, "valid")
        self.assertEqual((tp.next_run(self.plan())["slot"], tp.next_run(self.plan())["arm"]), (11, "EE"))
        self.assertIn("Next run (Amendment 2 item 4): EE seed 11 (slot 11) attempt 1", tp.describe_plan(self.plan()))
        for bad in (self.start("EC", 22, 22), self.start("EE", 33, 33), self.start("ER", 11, 11, 2)):
            with self.subTest(bad=bad), self.assertRaisesRegex(tp.ProtocolError, "registered order|next allowed|already valid"):
                tp.plan(tp.read_log(self.log) + [bad])

    def test_one_from_scratch_retry_then_whole_triplet_goes_to_the_next_reserve(self):
        self.assertEqual(self.attempt("EC", 11, 11, "valid"), 1)
        self.assertEqual(self.attempt("ER", 11, 11, "infrastructure"), 1)
        action = tp.next_run(self.plan())
        self.assertEqual((action["arm"], action["seed"], action["attempt"], action["retry"]), ("ER", 11, 2, True))
        self.attempt("ER", 11, 11, "infrastructure")
        current = self.plan()
        self.assertEqual(current["slots"][11]["chain"], [11, 44])
        action = tp.next_run(current)  # successful EC of seed 11 is retrained on the reserve too, first
        self.assertEqual((action["kind"], action["arm"], action["seed"], action["slot"], action["attempt"], action["reserve"]),
                         ("train", "EC", 44, 11, 1, True))
        with self.assertRaisesRegex(tp.ProtocolFailure, "retired|registered order"):
            tp.plan(tp.read_log(self.log) + [self.start("EE", 11, 11)])
        # The reserve has the same two-attempt limit; the next reserve then takes over; reserves are never reused.
        self.attempt("EC", 44, 11, "infrastructure")
        self.attempt("EC", 44, 11, "infrastructure")
        self.assertEqual(self.plan()["slots"][11]["chain"], [11, 44, 55])
        self.attempt("EC", 55, 11, "infrastructure")
        self.attempt("EC", 55, 11, "infrastructure")
        current = self.plan()
        self.assertEqual(current["slots"][11]["status"], "exhausted")
        action = tp.next_run(current)  # an exhausted slot is settled: slot 22 is next
        self.assertEqual((action["slot"], action["seed"], action["arm"]), (22, 22, "EC"))

    def test_reserves_are_taken_in_slot_order(self):
        """Replaces the pre-Amendment-2 test that let a reserve stay with a later slot (Sol R6)."""
        self.attempt("EC", 11, 11, "valid")
        self.attempt("ER", 11, 11, "valid")
        self.attempt("EE", 11, 11, "infrastructure")
        self.attempt("EE", 11, 11, "infrastructure")
        for arm in ("EC", "ER", "EE"):
            self.attempt(arm, 44, 11, "valid")
        self.attempt("EC", 22, 22, "infrastructure")
        self.attempt("EC", 22, 22, "infrastructure")
        current = self.plan()
        self.assertEqual(current["reserves_assigned"], {44: 11, 55: 22})
        self.assertEqual((current["slots"][11]["chain"], current["slots"][22]["chain"]), ([11, 44], [22, 55]))
        self.assertEqual(tp.next_run(current)["seed"], 55)
        with self.assertRaisesRegex(tp.ProtocolFailure, "registered order|reused"):
            tp.plan(tp.read_log(self.log) + [self.start("EC", 44, 22)])

    def test_sol_r6_sequence_is_refused(self):
        """Sol's probe: two failures for seed 22 before slot 11 is settled. The first such start is out of order."""
        tp.log_event(self.log, "start", arm="ER", seed=22, slot=22, attempt=1, identity=IDENTITY)
        with self.assertRaisesRegex(tp.ProtocolError, "out of the registered order.*EC seed 11 slot 11"):
            self.plan()
        self.log.unlink()
        self.attempt("EC", 11, 11, "valid")
        tp.log_event(self.log, "start", arm="EC", seed=44, slot=22, attempt=1, identity=IDENTITY)
        with self.assertRaisesRegex(tp.ProtocolError, "registered order"):
            self.plan()

    def test_numerical_or_protocol_failure_halts_without_reserve(self):
        for outcome in ("numerical", "protocol"):
            with self.subTest(outcome=outcome):
                self.log.unlink(missing_ok=True)
                self.attempt("EC", 11, 11, outcome)
                current = self.plan()
                self.assertTrue(current["halted"])
                self.assertEqual(current["slots"][11]["chain"], [11])
                self.assertEqual(current["reserves_assigned"], {})
                with self.assertRaisesRegex(tp.StudyHalted, "THE STUDY HALTS"):
                    tp.next_run(current)
                self.assertIn("STUDY HALTED", tp.describe_plan(current))

    def test_log_rejects_new_attempt_after_a_halt(self):
        for outcome in ("numerical", "protocol"):
            with self.subTest(outcome=outcome):
                self.log.unlink(missing_ok=True)
                self.attempt("EC", 11, 11, outcome)
                tp.log_event(self.log, "start", arm="ER", seed=11, slot=11, attempt=1, identity=IDENTITY)
                with self.assertRaisesRegex(tp.ProtocolFailure, "study halted"):
                    self.plan()

    def test_attempts_must_share_one_identity(self):
        """Amendment 2 item 7: a start without, or with a different, configuration identity is a protocol error."""
        self.attempt("EC", 11, 11, "infrastructure")
        for identity, pattern in ((dict(IDENTITY, implementation_manifest_sha256="0" * 64), "differs from earlier attempts"),
                                  (None, "without a configuration identity")):
            with self.subTest(pattern=pattern), self.assertRaisesRegex(tp.ProtocolError, pattern):
                tp.plan(tp.read_log(self.log) + [self.start("EC", 11, 11, 2, identity=identity)])
        self.assertEqual(self.plan()["identity"], IDENTITY)

    def test_resumed_run_is_never_valid(self):
        self.attempt("EC", 11, 11, "infrastructure")
        tp.log_event(self.log, "resume_start", arm="EC", seed=11, slot=11, attempt=1, identity=IDENTITY)
        tp.log_event(self.log, "resume_finish", arm="EC", seed=11, slot=11, attempt=1, outcome="valid")
        current = self.plan()
        self.assertEqual(current["slots"][11]["arms"]["EC"]["valid_attempt"], None)
        self.assertEqual(current["attempts"]["EC-s11"][0]["resume_outcome"], "resumed_invalid")
        self.assertEqual(tp.next_run(current)["attempt"], 2)
        with self.assertRaisesRegex(tp.ProtocolFailure, "bad resume"):  # one resume per attempt
            tp.plan(tp.read_log(self.log) + [dict(self.start("EC", 11, 11), event="resume_start")])

    def test_attempt_numbers_cannot_skip_or_exceed_two(self):
        with self.assertRaisesRegex(tp.ProtocolFailure, "next allowed|registered order"):
            tp.plan([dict(self.start("EC", 11, 11, 2), n=1)])
        self.attempt("EC", 11, 11, "infrastructure")
        self.attempt("EC", 11, 11, "valid")
        with self.assertRaisesRegex(tp.ProtocolFailure, "next allowed|already valid|registered order"):
            tp.plan(tp.read_log(self.log) + [self.start("EC", 11, 11, 3)])

    def test_open_attempts_are_closed_only_by_a_confirmed_recovery(self):
        """Amendment 3 item 2 (B4): reconcile never closes an open attempt without the operator's confirmation."""
        tp.log_event(self.log, "start", arm="EC", seed=11, slot=11, attempt=1, identity=IDENTITY)
        with self.assertRaisesRegex(tp.Refused, "RECOVER_STALE_WRITER"):
            tp.next_run(self.plan())
        self.assertIn("none while an attempt is open", tp.describe_plan(self.plan()))
        write_attempt(tp.attempt_dir(self.root, "EC", 11, 1), status="STARTED")
        with self.assertRaisesRegex(tp.Refused, "never treated as abandoned automatically"):
            tp.reconcile(self.root)
        self.assertEqual(len(tp.read_log(self.log)), 1)  # nothing appended
        closed = tp.reconcile(self.root, confirmed_no_other_session=True)
        self.assertEqual([(e["arm"], e["outcome"]) for e in closed], [("EC", "infrastructure")])
        self.assertIn("stale-writer recovery confirmed by the operator", closed[0]["detail"])
        self.assertEqual(tp.reconcile(self.root), [])
        self.assertEqual(tp.next_run(self.plan())["attempt"], 2)
        self.attempt("EC", 11, 11, "valid")
        tp.log_event(self.log, "start", arm="ER", seed=11, slot=11, attempt=1, identity=IDENTITY)
        write_attempt(tp.attempt_dir(self.root, "ER", 11, 1))  # killed after the report, before the finish
        self.assertEqual([(e["arm"], e["outcome"]) for e in tp.reconcile(self.root, confirmed_no_other_session=True)],
                         [("ER", "infrastructure")])
        tp.log_event(self.log, "start", arm="ER", seed=11, slot=11, attempt=2, identity=IDENTITY)
        write_attempt(tp.attempt_dir(self.root, "ER", 11, 2), status="FAILED", failure_class="protocol")
        closed = tp.reconcile(self.root, confirmed_no_other_session=True)  # a recovery never turns a halt into a retry
        self.assertEqual(closed[0]["outcome"], "protocol")
        with self.assertRaises(tp.StudyHalted):
            tp.next_run(self.plan())


# ---------------------------------------------------------------- B2: Hub files and chat template at the executable boundary

REAL_VERIFY_HUB_FILES, REAL_VERIFY_CHAT_TEMPLATE = tp.verify_hub_files, tp.verify_chat_template


def fake_hub(folder, contents):
    """A stand-in huggingface_hub module whose hf_hub_download serves ``contents`` {file: bytes} from ``folder``."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    calls = []

    def hf_hub_download(repo, name, revision=None, token=None):
        calls.append((repo, name, revision))
        (folder / name).write_bytes(contents[name])
        return str(folder / name)
    return types.SimpleNamespace(hf_hub_download=hf_hub_download, calls=calls)


class HubAndTemplateTests(unittest.TestCase):
    """Sol re-review B2: the trainer verifies the downloaded Hub files and the loaded chat template itself."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)

    def tearDown(self):
        self.folder.cleanup()

    def test_sol_probe_zeroed_hub_and_template_entries_are_refused(self):
        fixture = TrainerFixture(self.root / "probe")
        self.assertEqual(tp.verify_implementation(fixture.inputs)[1], fixture.manifest_sha)
        document = live_manifest_document()
        document["model"].update(hub_files={"tokenizer.json": "0" * 64}, chat_template={"digest": "0" * 64})
        fixture.write_manifest("```json\n" + json.dumps(document) + "\n```\n")
        with self.assertRaisesRegex(tp.ProtocolError, "Hub files, chat template"):
            tp.verify_implementation(fixture.inputs)
        self.assertEqual(live_manifest_document()["model"]["hub_files"], tp.HUB_FILES)
        self.assertEqual(live_manifest_document()["model"]["chat_template"], tp.CHAT_TEMPLATE)

    def test_downloaded_files_must_have_the_manifest_hashes(self):
        contents = {name: f"fixture {name}".encode() for name in tp.HUB_FILES}
        hashes = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
        hub = fake_hub(self.root / "hub", contents)
        with mock.patch.dict(tp.HUB_FILES, hashes), mock.patch.dict("sys.modules", {"huggingface_hub": hub}):
            manifest = {"model": {"hub_files": dict(hashes)}}
            self.assertEqual(tp.verify_hub_files(manifest), hashes)
            self.assertEqual({(repo, revision) for repo, _, revision in hub.calls}, {(ts.MODEL_ID, ts.MODEL_REVISION)})
            contents["tokenizer.json"] = b"other bytes"
            with self.assertRaisesRegex(tp.ProtocolError, "tokenizer.json at the pinned revision"):
                tp.verify_hub_files(manifest)
            with self.assertRaisesRegex(tp.ProtocolError, "other Hub files"):
                tp.verify_hub_files({"model": {"hub_files": {"tokenizer.json": hashes["tokenizer.json"]}}})

    def test_loaded_chat_template_must_be_the_manifests(self):
        template = "{{ fixture chat template }}"
        registered = dict(tp.CHAT_TEMPLATE, digest=ts.digest(template), utf8_sha256=ts.sha256(template.encode()))
        with mock.patch.dict(tp.CHAT_TEMPLATE, registered):
            manifest = {"model": {"chat_template": dict(registered)}}
            self.assertEqual(tp.verify_chat_template(types.SimpleNamespace(chat_template=template), manifest), registered["digest"])
            for other in ("{{ other }}", None, ""):
                with self.subTest(template=other), self.assertRaises(tp.ProtocolError):
                    tp.verify_chat_template(types.SimpleNamespace(chat_template=other), manifest)

    def test_direct_trainer_run_halts_on_wrong_hub_bytes_or_template(self):
        """The check is in the executable itself (tp.main), not only in the notebook's GPU cell."""
        entry = TrainerEntryTests()
        entry.setUp()
        self.addCleanup(entry.tearDown)
        hub = fake_hub(self.root / "hub", {name: b"not the pinned bytes" for name in tp.HUB_FILES})
        code, err, _ = entry.train(None, patches=[mock.patch.object(tp, "verify_hub_files", REAL_VERIFY_HUB_FILES),
                                                  mock.patch.dict("sys.modules", {"huggingface_hub": hub})])
        report = entry.report()
        self.assertEqual((code, report["failure_class"], report["failure_stage"]), (tp.EXIT_CODES["protocol"], "protocol", "hub"))
        self.assertNotIn("mask_audit", report)
        entry.tearDown()
        entry.setUp()
        code, err, _ = entry.train(None, patches=[mock.patch.object(tp, "verify_chat_template", REAL_VERIFY_CHAT_TEMPLATE)])
        report = entry.report()  # the harness tokenizer's template "t" is not the pinned one
        self.assertEqual((code, report["failure_class"], report["failure_stage"]), (tp.EXIT_CODES["protocol"], "protocol", "tokenizer"))
        self.assertIn("chat template", report["error"])


# ---------------------------------------------------------------- B3: the baseline archive itself is validated

def recompute(members, *names):
    """Re-derive run_manifest.json digests after a deliberate edit, so a deeper check must catch it (FIXTURE)."""
    run = json.loads(members["run_manifest.json"])
    fields = {"experiment_config.json": "config_sha256", "dataset.json": "dataset_sha256", "split_manifest.json": "split_sha256"}
    for name in names:
        run[fields[name]] = tp.engine_digest(json.loads(members[name]))
    members["run_manifest.json"] = json.dumps(run).encode()


def edit_backend(change):
    def apply(members):
        run = json.loads(members["run_manifest.json"])
        change(run["backend"])
        for session in run["sessions"]:
            session["backend"] = run["backend"]
        run["execution_sha256"] = tp.engine_digest({"backend": run["backend"], "environment": json.loads(members["environment.json"])})
        members["run_manifest.json"] = json.dumps(run).encode()
    return apply


def edit_environment(change):
    def apply(members):
        environment = json.loads(members["environment.json"])
        change(environment)
        members["environment.json"] = json.dumps(environment).encode()
        run = json.loads(members["run_manifest.json"])
        for session in run["sessions"]:
            session["environment"] = environment
        run["execution_sha256"] = tp.engine_digest({"backend": run["backend"], "environment": environment})
        members["run_manifest.json"] = json.dumps(run).encode()
    return apply


def edit_lines(name, change):
    def apply(members):
        lines = members[name].decode().splitlines()
        change(lines)
        members[name] = ("\n".join(lines) + "\n").encode()
    return apply


class BaselineValidationTests(unittest.TestCase):
    """Sol re-review B3: verify_baseline validates the actual ZIP: frozen DEV and source snapshot, a recomputed config
    digest, the registered execution and environment, exactly 120 resolved generations and the engine identity."""

    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.manifest = self.root / tp.MANIFEST_NAME
        self.manifest.write_text(live_manifest_text())
        self.baseline = self.root / "baseline_dev"
        self.digest = write_baseline(self.baseline)

    def tearDown(self):
        self.folder.cleanup()

    def refused(self, pattern):
        with self.assertRaisesRegex(tp.Refused, pattern):
            tp.verify_baseline(self.baseline, self.manifest)

    def test_realistic_synthetic_baseline_validates_and_is_labelled(self):
        self.assertEqual(tp.verify_baseline(self.baseline, self.manifest), self.digest)
        with zipfile.ZipFile(self.baseline / "base_results.zip") as z:
            run = json.loads(z.read("run_manifest.json"))
            journal = [json.loads(line) for line in z.read("generation_attempts.jsonl").decode().splitlines()]
            self.assertIn("source/engine.py", z.namelist())
        self.assertEqual(run["backend"]["verification_scope"], SYNTHETIC_SCOPE)  # clearly a fixture
        self.assertEqual((run["completed"], len(journal)), (120, 120))
        self.assertEqual(json.loads(z_read(self.baseline, "environment.json"))["packages"]["peft"], "0.15.2")

    def test_sol_probe_metadata_only_zip_is_refused(self):
        write_metadata_only_baseline(self.baseline, hashlib.sha256(self.manifest.read_bytes()).hexdigest())
        self.refused("not a complete engine export")

    def test_a_manifest_hash_alone_cannot_validate(self):
        with self.assertRaisesRegex(tp.Refused, "not only its SHA-256"):
            tp.verify_baseline(self.baseline, hashlib.sha256(self.manifest.read_bytes()).hexdigest())

    def test_noncompliant_archives_are_refused(self):
        def drop_generation(lines):
            del lines[0]

        def edit_response(lines):
            record = json.loads(lines[0])
            record["raw_response"] = "FINAL: 42"
            lines[0] = json.dumps(record)

        def change_dataset(members):
            dataset = json.loads(members["dataset.json"])
            dataset["families"][0]["forms"]["C"]["text"] += " changed"
            members["dataset.json"] = json.dumps(dataset).encode()
            recompute(members, "dataset.json")

        def change_config(members):
            config = json.loads(members["experiment_config.json"])
            config["max_new_tokens"] = 512
            members["experiment_config.json"] = json.dumps(config).encode()
            recompute(members, "experiment_config.json")

        def change_source(members):
            members["source/engine.py"] += b"\n# edited\n"

        def reverse_order(members):
            members["evaluation_order.json"] = json.dumps(json.loads(members["evaluation_order.json"])[::-1]).encode()

        cases = (
            ("one generation missing", edit_lines("generation_attempts.jsonl", drop_generation), "resolved generations"),
            ("journal edited", edit_lines("generation_attempts.jsonl", edit_response), "was edited"),
            ("other DEV data", change_dataset, "frozen DEV dataset"),
            ("other settings", change_config, "registered DEV configuration"),
            ("engine source", change_source, "engine source snapshot"),
            ("order", reverse_order, "evaluation order"),
            ("torch 0.0.0", edit_environment(lambda env: env["packages"].update(torch="0.0.0")), "torch '0.0.0'"),
            ("no PEFT recorded", edit_environment(lambda env: env["packages"].pop("peft")), "peft None"),
            ("A100", edit_backend(lambda backend: backend.update(hardware="NVIDIA A100-SXM4-40GB", capability=[8, 0])), "not a Tesla T4"),
            ("unverified GPU", edit_backend(lambda backend: backend.update(gpu_verified=False)), "gpu_verified"),
            ("other attention", edit_backend(lambda backend: backend.update(attention="sdpa flash")), "attention"),
            ("other quantization", edit_backend(lambda backend: backend["quantization"].update(bnb_4bit_quant_type="fp4")), "quant_type"),
            ("missing journal", lambda members: members.pop("generation_attempts.jsonl"), "lacks generation_attempts.jsonl"),
        )
        for name, change, pattern in cases:
            with self.subTest(name=name):
                write_baseline(self.baseline)
                rewrite_archive(self.baseline, change)
                self.refused(pattern)
        write_baseline(self.baseline)
        rewrite_archive(self.baseline, lambda members: members.update({"summary.md": b"edited"}), fix_checksums=False)
        self.refused("checksums.sha256")
        write_baseline(self.baseline, config_sha256="0" * 64)
        self.refused("config digest does not recompute")
        write_baseline(self.baseline)
        self.assertEqual(tp.verify_baseline(self.baseline, self.manifest), self.digest)


def z_read(folder, name):
    with zipfile.ZipFile(Path(folder) / "base_results.zip") as z:
        return z.read(name)


# ---------------------------------------------------------------- B4: one writer per training root

class WriterOwnershipTests(unittest.TestCase):
    """Amendment 3 item 2 (Sol re-review B4)."""

    def setUp(self):
        self.entry = TrainerEntryTests()
        self.entry.setUp()
        self.fixture = self.entry.fixture
        self.root = self.fixture.train_root

    def tearDown(self):
        self.entry.tearDown()

    def kill_after_start(self):
        """A session that acquired the lock, logged its start and wrote STARTED, then was killed (FIXTURE)."""
        tp.WriterLock(self.root, session_id="dead-session", heartbeat_seconds=0).acquire()
        tp.log_event(self.fixture.log, "start", arm="EC", seed=11, slot=11, attempt=1,
                     identity=tp.attempt_identity(self.fixture.inputs, self.fixture.baseline_sha))
        write_attempt(tp.attempt_dir(self.root, "EC", 11, 1), status="STARTED")

    def test_started_report_is_persisted_before_model_loading(self):
        seen = []

        def load_model(torch, seed):
            seen.append(self.entry.report()["status"])
            return "model", [], True, {}

        code, err, _ = self.entry.train(None, patches=[mock.patch.object(tp, "load_model", side_effect=load_model)])
        self.assertEqual((code, seen), (0, ["STARTED"]), err)
        self.assertEqual(self.entry.report()["writer_session"], self.fixture.entries()[0]["writer_session"])
        self.assertFalse((self.root / tp.WRITER_LOCK).exists())  # released after the outcome was logged

    def test_a_second_concurrent_writer_is_refused(self):
        other = tp.WriterLock(self.root, session_id="session-A", heartbeat_seconds=0).acquire()
        code, err, _ = self.entry.train()
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("session-A", err)
        self.assertIn("Only one session may write a training root", err)
        self.assertFalse(self.fixture.log.exists())
        self.assertTrue(other.owned())
        with self.assertRaises(tp.Refused):
            tp.WriterLock(self.root).acquire()
        other.release()
        self.assertEqual(self.entry.train()[0], 0)

    def test_sol_probe_open_attempt_is_refused_without_confirmation(self):
        tp.log_event(self.fixture.log, "start", arm="EC", seed=11, slot=11, attempt=1,
                     identity=tp.attempt_identity(self.fixture.inputs, self.fixture.baseline_sha))
        with self.assertRaisesRegex(tp.Refused, "never treated as abandoned"):
            tp.reconcile(self.root)
        code, err, _ = self.entry.train()  # no lock is held, but the attempt is open: still refused
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("RECOVER_STALE_WRITER", err)
        self.assertEqual(len(self.fixture.entries()), 1)
        with self.assertRaisesRegex(tp.Refused, "explicit confirmation"):
            tp.recover_stale_writer(self.root)

    def test_confirmed_recovery_is_logged_closes_as_infrastructure_and_releases(self):
        self.kill_after_start()
        code, err, _ = self.entry.train()
        self.assertEqual(code, tp.EXIT_CODES["refused"])
        self.assertIn("dead-session", err)
        code, err, out = self.entry.train(None, "--recover-stale-writer")
        self.assertEqual(code, 0, err)
        records = [json.loads(line) for line in (self.root / tp.WRITER_RECOVERIES).read_text().splitlines()]
        self.assertEqual(len(records), 1)
        self.assertEqual((records[0]["event"], records[0]["stale_lock"]["session_id"], records[0]["operator_confirmed_no_other_session"],
                          records[0]["open_attempts"]), ("stale_writer_recovered", "dead-session", True, ["EC-s11 attempt 1"]))
        self.assertEqual(self.entry.outcomes(), [("start", "EC", 11, 1, None), ("finish", "EC", 11, 1, "infrastructure"),
                                                 ("start", "EC", 11, 2, None), ("finish", "EC", 11, 2, "valid")])
        self.assertEqual(self.fixture.entries()[1]["recovery"]["stale_session"], "dead-session")
        self.assertFalse((self.root / tp.WRITER_LOCK).exists())

    def test_heartbeat_and_a_lost_lock(self):
        lock = tp.WriterLock(self.root, heartbeat_seconds=0.05).acquire()
        for _ in range(100):
            if (tp.read_writer_lock(self.root) or {}).get("heartbeats", 0) >= 2:
                break
            time.sleep(0.02)
        holder = tp.read_writer_lock(self.root)
        self.assertGreaterEqual(holder["heartbeats"], 2)
        self.assertEqual(holder["session_id"], lock.session_id)
        self.assertIn(lock.session_id, tp.describe_writer(self.root))
        (self.root / tp.WRITER_LOCK).write_text(json.dumps(dict(holder, session_id="someone-else")))
        self.assertFalse(lock.owned())
        self.assertFalse(lock.beat())
        self.assertFalse(lock.release())  # never removes another session's lock
        self.assertEqual(tp.read_writer_lock(self.root)["session_id"], "someone-else")

    def test_a_session_whose_attempt_was_recovered_never_appends_its_outcome(self):
        def recovered_meanwhile(torch, seed):  # another session, after the operator's confirmation, recovers the root
            tp.recover_stale_writer(self.root, confirmed_no_other_session=True)
            return "model", [], True, {}

        code, err, _ = self.entry.train(None, patches=[mock.patch.object(tp, "load_model", side_effect=recovered_meanwhile)])
        self.assertEqual(code, tp.EXIT_CODES["infrastructure"])
        self.assertIn("WRITER LOCK LOST", err)
        self.assertEqual(self.entry.outcomes(), [("start", "EC", 11, 1, None), ("finish", "EC", 11, 1, "infrastructure")])
        tp.plan(self.fixture.entries())  # the log stays consistent


if __name__ == "__main__":
    unittest.main()
