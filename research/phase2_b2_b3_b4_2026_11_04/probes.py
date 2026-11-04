"""Sol's 4 November re-review probes for B2, B3 (training side) and B4, adapted so they run on both the reviewed code
(7e84654) and the repaired code. TRAIN/DEV and synthetic artifacts only; no model, no FINAL_TEST content.

Run from a repository root: python3 -B research/phase2_b2_b3_b4_2026_11_04/probes.py [ROOT]
Why adapted: Sol's script calls reconcile() outside its attempt() wrapper (the repaired reconcile now raises, which
would abort the script), and its write_baseline() fixture is now a realistic archive; the metadata-only ZIP it used
is kept as write_metadata_only_baseline(). Each probe prints {"accepted": bool, ...}; accepted=False is a refusal.
"""
import contextlib
import copy
import hashlib
import inspect
import io
import json
import sys
import tempfile
from pathlib import Path
from unittest import mock

ROOT = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "test1_pilot")]
from t4_smoke import train_phase2 as T  # noqa: E402
from t4_smoke import phase2_eval as E  # noqa: E402
from t4_smoke import test_phase2_eval as gate_fixtures  # noqa: E402
import t4_smoke.test_train_phase2 as F  # noqa: E402


def attempt(call):
    try:
        value = call()
    except Exception as error:
        return {"accepted": False, "exception": type(error).__name__, "message": str(error)[:400]}
    return {"accepted": True, "value": value}


def main():
    result = {"root": str(ROOT), "data": "TRAIN/DEV and synthetic fixtures only"}
    quiet = io.StringIO()
    with contextlib.redirect_stdout(quiet), contextlib.redirect_stderr(quiet):
        with tempfile.TemporaryDirectory() as temp:
            train = F.TrainerFixture(temp)
            # B2 (Sol R4 probe 1): zero-filled tokenizer.json and chat-template entries in the trainer's manifest.
            doc = T.parse_manifest((train.inputs / T.MANIFEST_NAME).read_text())
            doc["model"].update(hub_files={"tokenizer.json": "0" * 64}, chat_template={"digest": "0" * 64})
            train.write_manifest("```json\n" + json.dumps(doc) + "\n```\n")
            result["B2_trainer_zeroed_hub_and_template_entries"] = attempt(lambda: T.verify_implementation(train.inputs)[1])

        with tempfile.TemporaryDirectory() as temp:
            train = F.TrainerFixture(temp)
            # B3 (Sol R8 probe): a ZIP of two metadata JSON files, no dataset, journal, sources or generations.
            writer = getattr(F, "write_metadata_only_baseline", F.write_baseline)
            digest = writer(train.baseline, train.manifest_sha)
            new_api = "manifest" in inspect.signature(T.verify_baseline).parameters
            argument = train.inputs / T.MANIFEST_NAME if new_api else train.manifest_sha
            result["B3_metadata_only_baseline_zip"] = attempt(lambda: T.verify_baseline(train.baseline, argument) == digest)
            # B4 (Sol probe): a valid start event for EC/11, then reconcile() with no confirmation that the writer died.
            T.log_event(train.log, "start", arm="EC", seed=11, slot=11, attempt=1, identity=T.attempt_identity(train.inputs, digest))
            result["B4_reconcile_open_attempt_without_confirmation"] = attempt(
                lambda: [e["outcome"] for e in T.reconcile(train.train_root)])
            result["B4_next_run_after_that"] = attempt(lambda: T.next_run(T.plan(T.read_log(train.log))))
            if hasattr(T, "WriterLock"):
                first = T.WriterLock(train.train_root, session_id="session-A", heartbeat_seconds=0).acquire()
                result["B4_second_concurrent_writer"] = attempt(lambda: T.WriterLock(train.train_root).acquire().session_id)
                first.release()
            else:
                result["B4_second_concurrent_writer"] = {"accepted": True, "value": "no writer lock exists in this version"}

        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            # B3 (Sol): bind_implementation records a supplied manifest hash without checking the running code.
            doc = T.parse_manifest((ROOT / "phase2/IMPLEMENTATION_MANIFEST.md").read_text())
            doc["files"]["test1_pilot/hinglish_pilot/engine.py"] = "0" * 64
            wrong = temp / "WRONG_MANIFEST.md"
            wrong.write_text("```json\n" + json.dumps(doc) + "\n```\n")
            result["B3_bind_manifest_not_describing_running_engine"] = attempt(
                lambda: E.bind_implementation(temp / "runs" / "base", wrong))

        with tempfile.TemporaryDirectory() as temp:
            temp = Path(temp)
            # B2 (Sol R4 probe 2): real current file digests, only dependencies.evaluation.torch = 0.0.0.
            doc = T.parse_manifest((ROOT / "phase2/IMPLEMENTATION_MANIFEST.md").read_text())
            doc["dependencies"]["evaluation"]["torch"] = "0.0.0"
            manifest = temp / "IMPLEMENTATION_MANIFEST.md"
            manifest.write_text("```json\n" + json.dumps(doc) + "\n```\n")
            manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
            with mock.patch.object(gate_fixtures, "MANIFEST_SHA", manifest_sha):
                gate_fixtures.complete_slots(temp / "train")
            result["B2_freeze_wrong_non_file_stack_torch_0.0.0"] = attempt(lambda: E.freeze_manifest(
                temp / "train", manifest_path=manifest, root=ROOT)["S"])
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
