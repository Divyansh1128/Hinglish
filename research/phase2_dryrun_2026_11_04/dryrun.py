"""CPU operator rehearsal. Run from the repo root with python3 -B <this file>.

Only GPU/model/tokenizer/Hub operations and the explicitly labelled FINAL_TEST loaders are substituted.
All training plans, authenticated TRAIN loading, exposure order, masking, 60-update orchestration, disk writes,
attempt logs, recovery, engine journals/scoring/exports, freeze CLI, and analysis run for real.
The FINAL_TEST fixture is made from DEV; the real FINAL_TEST file is never loaded here.
Outputs are SYNTHETIC SOFTWARE CHECKS, never study results or hardware feasibility evidence.
"""
import contextlib
import copy
import io
import json
import shutil
import sys
import tempfile
import types
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "test1_pilot")]
from t4_smoke import phase2_eval as E, train_phase2 as T, train_smoke as S
from t4_smoke import test_train_phase2 as F
from t4_smoke.test_labels import FakeTokenizer
from hinglish_pilot import engine, hf_backend
from phase2_analysis import analyze as A

OUT = Path(__file__).resolve().parent
SCOPE = "SYNTHETIC CPU DRY RUN: DEV substituted for FINAL_TEST; no GPU, Hub, model or study results"


class Tokenizer(FakeTokenizer):
    def convert_tokens_to_ids(self, token):
        return self.special_tokens[token]


class Model:
    def __init__(self, seed):
        self.seed = seed

    def save_pretrained(self, folder, **kwargs):
        folder = Path(folder)
        folder.mkdir(parents=True, exist_ok=True)
        (folder / "adapter_model.safetensors").write_text(f"MOCK MODEL {self.seed}")
        (folder / "adapter_config.json").write_text(json.dumps({"fixture": SCOPE, "r": 16}))


class Trainer(T.Phase2Trainer):
    """Replace tensor operations; inherit the actual Phase2Trainer.update and its step/schedule/cursor checks."""
    fail = False

    def __init__(self, torch, model, trainable, keep, sequence, sampler):
        fixture, _ = F.fake_trainer()
        self.__dict__.update(fixture.__dict__)
        self.__dict__.pop("loss", None)
        self.torch, self.model, self.trainable = torch, model, trainable
        self.sequence, self.sampler = sequence, sampler
        self.scaler.state_dict = lambda: {"scale": self.scaler.get_scale()}
        self.optimizer.state_dict = lambda: {"state": {}, "param_groups": self.optimizer.param_groups}

    def loss(self, example):
        if self.fail and self.cursor == 16:
            raise OSError("injected GPU/runtime I/O failure")
        return F.FakeLoss(1.0)

    def probe(self, example):
        return [0.0]  # model logits only


@contextlib.contextmanager
def runtime():
    torch = F.fake_trainer()[0].torch
    rng = types.SimpleNamespace(numpy=lambda: types.SimpleNamespace(tobytes=lambda: b"MOCK RNG"))
    torch.get_rng_state = torch.cuda.get_rng_state = lambda: rng
    torch.manual_seed = torch.cuda.manual_seed_all = lambda seed: None
    torch.save = lambda state, path: Path(path).write_text("MOCK GPU STATE\n" + repr(state))
    torch.equal = lambda a, b: a == b
    sampler = types.SimpleNamespace(error=None, take=lambda: 10, stop=lambda: None)
    sampler_factory = lambda: types.SimpleNamespace(start=lambda: sampler)
    safetensors = types.ModuleType("safetensors")
    safetensors_torch = types.ModuleType("safetensors.torch")
    safetensors_torch.load_file = lambda path: {}  # empty mocked trainable tensors

    class Backend(engine.FakeBackend):
        def __init__(self, config, adapter_path=None):
            self.metadata = F.synthetic_t4_metadata(config["adapter"])
            self.metadata["verification_scope"] = SCOPE
            self.load_report = {"fixture": SCOPE}

    with contextlib.ExitStack() as stack:
        patches = [mock.patch.object(T, "gpu_name", return_value=("Tesla T4", (7, 5))),
                   mock.patch.object(S, "versions", return_value=dict(S.PINS, torch=S.TORCH_BUILD)),
                   mock.patch.object(S, "gpu_setup", return_value=(torch, [])),
                   mock.patch.object(S, "environment", return_value=F.synthetic_environment()),
                   mock.patch.object(S, "MemorySampler", sampler_factory),
                   mock.patch.object(S, "load_tokenizer", Tokenizer),
                   mock.patch.object(T, "verify_hub_files", return_value=dict(T.HUB_FILES)),
                   mock.patch.object(T, "verify_chat_template", return_value=T.CHAT_TEMPLATE["digest"]),
                   mock.patch.object(T, "load_model", side_effect=lambda torch, seed: (Model(seed), [], True, {"fixture": SCOPE})),
                   mock.patch.object(T, "weight_shard_hashes", return_value=F.SYNTHETIC_SHARDS),
                   mock.patch.object(T, "Phase2Trainer", Trainer),
                   mock.patch.object(engine, "environment", F.synthetic_environment),
                   mock.patch.object(hf_backend, "HFBackend", Backend),
                   mock.patch.dict(sys.modules, {"safetensors": safetensors, "safetensors.torch": safetensors_torch})]
        for patch in patches:
            stack.enter_context(patch)
        yield


def refused(call):
    try:
        call()
    except (ValueError, T.Refused) as error:
        return {"refused": True, "error": str(error)}
    raise AssertionError("Expected refusal was accepted")


def final_fixture():
    """100 independent fixture identities with DEV content; engine schema validation remains active."""
    dev = json.loads((ROOT / E.FROZEN["dev"][0]).read_bytes())
    families = [copy.deepcopy(dev[i % 40]) for i in range(100)]
    for i, family in enumerate(families):
        family["split_role"] = "FINAL_TEST"
        for key in E.IDENTITY:
            family[key] = f"DRYRUN-{key}-{i:03d}"
        for form, rendering in family["forms"].items():
            rendering["rendering_id"] = f"DRYRUN-{i:03d}-{form}"
            rendering["text"] += f" Synthetic fixture {i}."
    raw = json.dumps(families).encode()
    with mock.patch.dict(E.FROZEN, final_test=("final_test.DEV-FIXTURE.json", E.sha256(raw), "FINAL_TEST", 100)):
        dataset, splits = E.inputs(raw, "final_test", E.split_identities(ROOT))
    return families, dataset, splits


def main():
    summary = {"scope": SCOPE, "integration_breaks": [{
        "problem": "builder used spaced JSON for generation_config.engine_config_sha256; analysis uses compact engine JSON",
        "evidence": "before_config_digest_fix.json", "resolution": "builder and runtime validators now use the engine canonical digest"}],
        "checks": {}}
    work = Path(tempfile.mkdtemp(prefix="phase2_round3_"))
    transcript = io.StringIO()
    try:
        with contextlib.redirect_stdout(transcript), contextlib.redirect_stderr(transcript), runtime():
            inputs = work / "inputs"
            inputs.mkdir()
            manifest = inputs / T.MANIFEST_NAME
            manifest.write_bytes((ROOT / "phase2" / T.MANIFEST_NAME).read_bytes())
            for source in list(S.TRAIN_FILES) + [T.EXPOSURE_ORDER_PATH, E.FROZEN["dev"][0], "phase2/PREREGISTRATION.md"]:
                shutil.copyfile(ROOT / source, inputs / Path(source).name)
            (inputs / "identities.json").write_text(json.dumps(E.split_identities(ROOT)))
            train, baseline = work / "train", work / "baseline_dev"
            assert E.main(["evaluate", "--split", "dev", "--inputs", str(inputs), "--run-dir", str(baseline / "base"),
                           "--implementation-manifest", str(manifest)]) == 0
            baseline_sha = T.verify_baseline(baseline, manifest)
            train_args = ["train", "--train-root", str(train), "--inputs", str(inputs), "--baseline-dir", str(baseline)]
            # One infrastructure failure with a real finish event, then the plan's from-scratch retry.
            Trainer.fail = True
            assert T.main(train_args) == T.EXIT_CODES["infrastructure"]
            Trainer.fail = False
            assert T.main(train_args) == 0
            E.run_dev_sanity(train, inputs)
            # Simulate SIGKILL after ER/11 start + STARTED report, before an outcome can be logged.
            writer = T.WriterLock(train, heartbeat_seconds=0).acquire()
            action = T.next_run(T.plan(T.read_log(train / T.ATTEMPT_LOG)))
            keys = {key: action[key] for key in ("arm", "seed", "slot", "attempt")}
            folder = T.attempt_dir(train, action["arm"], action["seed"], action["attempt"])
            folder.mkdir(parents=True)
            T.log_event(train / T.ATTEMPT_LOG, "start", **keys, identity=T.attempt_identity(inputs, baseline_sha),
                        writer_session=writer.session_id)
            S.write_json(folder / "train_report.json", dict(keys, status="STARTED", failure_class=None))
            summary["checks"]["B4_live_writer"] = refused(lambda: T.WriterLock(train).acquire())
            summary["checks"]["B4_no_automatic_reconciliation"] = refused(lambda: T.reconcile(train))
            T.recover_stale_writer(train, confirmed_no_other_session=True)
            while T.next_run(T.plan(T.read_log(train / T.ATTEMPT_LOG)))["kind"] != "complete":
                E.run_dev_sanity(train, inputs)
                assert T.main(train_args) == 0
                E.run_dev_sanity(train, inputs)
            folders = E.require_dev_sanity(train, manifest)
            assert len(folders) == 9
            entries = T.read_log(train / T.ATTEMPT_LOG)
            assert sum(e.get("outcome") == "valid" for e in entries) == 9
            assert sum(e.get("outcome") == "infrastructure" for e in entries) == 2
            # Invoke the actual freeze-manifest CLI; feed its exact schema/hash output to evaluation + analysis.
            freeze_stdout = io.StringIO()
            with contextlib.redirect_stdout(freeze_stdout):
                assert E.main(["freeze-manifest", "--train-root", str(train), "--baseline-dir", str(baseline),
                               "--manifest", str(manifest), "--root", str(ROOT)]) == 0
            frozen_path = inputs / "ADAPTERS_FROZEN.md"
            frozen_path.write_text(freeze_stdout.getvalue())
            frozen = E.parse_frozen(frozen_path.read_text())
            assert frozen["schema"] == "phase2-adapters-frozen-3" and frozen["S"] == 3
            assert frozen["baseline_dev_results_zip_sha256"] == baseline_sha
            assert frozen["implementation_manifest_sha256"] == S.file_sha256(manifest)
            assert frozen["attempt_log_sha256"] == S.file_sha256(train / T.ATTEMPT_LOG)
            for path, sha in frozen["training_logs_sha256"].items():
                assert S.file_sha256(train / path) == sha
            families, dataset, splits = final_fixture()
            real_loader = E.load_evaluation_inputs

            def evaluation_loader(folder, split):
                return (copy.deepcopy(dataset), copy.deepcopy(splits)) if split == "final_test" else real_loader(folder, split)

            checkpoints = {}
            with mock.patch.object(E, "load_evaluation_inputs", evaluation_loader):
                for adapter, adapter_dir in [(None, None)] + E.gate(frozen, train, baseline_dir=baseline, manifest_path=manifest):
                    key = (A.UNCHANGED, None) if adapter is None else (adapter["arm"], adapter["seed"])
                    run_dir = work / "final_eval" / A.checkpoint_name(key)
                    args = ["evaluate", "--split", "final_test", "--inputs", str(inputs), "--run-dir", str(run_dir),
                            "--train-root", str(train), "--baseline-dir", str(baseline), "--implementation-manifest", str(manifest)]
                    if adapter:
                        args += ["--adapter-dir", str(adapter_dir), "--adapter-record", str(adapter_dir.parent / "final_adapter.json")]
                    assert E.main(args) == 0
                    checkpoints[key] = run_dir.parent / (run_dir.name + "_results.zip")
            # Mock only the FINAL_TEST dataset loader; baseline loading and all analysis checks are unchanged.
            with mock.patch.object(A, "load_frozen_dataset", return_value=("FINAL_TEST", A.DATASET_SHA256["FINAL_TEST"], families)):
                result = A.run_analysis(work / "NEVER_READ_FINAL_TEST.json", checkpoints, None, work / "analysis",
                                        frozen_path, manifest, baseline / "base_results.zip")
                summary["checks"]["B3_caller_k_refused"] = refused(lambda: A.analyze(A.assemble(
                    "NEVER_READ", checkpoints, frozen_path, manifest, baseline / "base_results.zip"), 40))
            # Original B1 shape: coherently record non-T4 hardware and wrong torch, then require refusal.
            implementation = A.load_implementation_manifest(manifest)
            run = A.load_run(checkpoints[(A.UNCHANGED, None)])
            run["manifest"]["backend"].update(hardware="NVIDIA A100", capability=[8, 0])
            run["environment"]["packages"]["torch"] = "0.0.0"
            for session in run["manifest"]["sessions"]:
                session.update(backend=copy.deepcopy(run["manifest"]["backend"]), environment=copy.deepcopy(run["environment"]))
            run["manifest"]["execution_sha256"] = engine.digest({"backend": run["manifest"]["backend"], "environment": run["environment"]})
            summary["checks"]["B1_wrong_hardware_and_environment"] = refused(lambda: A.check_environment("probe", run, implementation))
            for name, edit in [("unverified_GPU", lambda r: r["manifest"]["backend"].update(gpu_verified=False)),
                               ("wrong_torch", lambda r: r["environment"]["packages"].update(torch="0.0.0"))]:
                run = A.load_run(checkpoints[(A.UNCHANGED, None)])
                edit(run)
                for session in run["manifest"]["sessions"]:
                    session.update(backend=copy.deepcopy(run["manifest"]["backend"]), environment=copy.deepcopy(run["environment"]))
                run["manifest"]["execution_sha256"] = engine.digest({"backend": run["manifest"]["backend"], "environment": run["environment"]})
                summary["checks"]["B1_" + name] = refused(lambda: A.check_environment("probe", run, implementation))
            assert result["status"] == "COMPLETE"
            baseline_run = A.load_run(baseline / "base_results.zip")
            expected_k = sum(row["correct"] is True and row["form"] == "C" for row in baseline_run["selected"].values())
            assert result["ceiling_risk_proxy"]["correct"] == expected_k
            summary.update(status="PASS", valid_adapters=len(folders), infrastructure_failures=2,
                           training_starts=sum(e["event"] == "start" for e in entries), dev_generations=120 + 9 * 120,
                           final_fixture_generations=10 * 300, schema=frozen["schema"], retained=frozen["retained_seeds"],
                           baseline_derived_k=expected_k, hashes={"implementation": frozen["implementation_manifest_sha256"],
                           "baseline_zip": baseline_sha, "freeze": S.file_sha256(frozen_path),
                           "attempt_log": frozen["attempt_log_sha256"]}, frozen_log_files=len(frozen["training_logs_sha256"]))
            (OUT / "synthetic_freeze.md").write_text(frozen_path.read_text())
            shutil.copyfile(work / "analysis" / "phase2_analysis.json", OUT / "synthetic_analysis.json")
    except BaseException as error:
        summary.update(status="FAIL", error=f"{type(error).__name__}: {error}")
        raise
    finally:
        (OUT / "dryrun.log").write_text(SCOPE + "\n" + transcript.getvalue())
        (OUT / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        shutil.rmtree(work)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
