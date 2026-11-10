"""Build the descriptive Phase-2 C-failure audit packet using only the stdlib.

Usage (from any directory): python3 -B results/phase2/audit/build_packet.py
Stored strict scores and numeric_literal_v1 diagnostics are copied, never rescored.
"""

import hashlib
import json
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

HERE = Path(__file__).resolve().parent
ARCHIVE = HERE.parent / "final_test" / "Phase2_FinalTest_results.zip"
OUTPUT = HERE / "phase2_outputs_for_audit.jsonl"
ARMS = ("ER", "EC")
SEEDS = (11, 22, 33)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def lines(archive, name):
    return [json.loads(line) for line in archive.read(name).splitlines() if line.strip()]


def build_packet():
    packet = []
    with ZipFile(ARCHIVE) as archive:
        require(len(archive.namelist()) == len(set(archive.namelist())), "Duplicate ZIP members")
        for arm in ARMS:
            for seed in SEEDS:
                run = f"{arm}-s{seed}"
                prefix = f"final_test/{run}/"
                families = lines(archive, prefix + "dataset_snapshot.jsonl")
                require(len(families) == 100, f"{run}: expected 100 families")
                inputs = {}
                for family in families:
                    for form, rendering in family["forms"].items():
                        rid = rendering["rendering_id"]
                        require(rid not in inputs, f"{run}: duplicate input {rid}")
                        inputs[rid] = (family, form, rendering)
                attempts_name = prefix + "generation_attempts.jsonl"
                generated = {}
                for row in lines(archive, attempts_name):
                    if row["status"] != "generated":
                        require(row["infrastructure_failure"], f"{run}: unexplained failed attempt")
                        continue
                    rid = row["rendering_id"]
                    require(rid not in generated, f"{run}: duplicate generation {rid}")
                    require(type(row["correct"]) is bool, f"{run}: nonboolean strict score")
                    generated[rid] = row
                require(set(generated) == set(inputs) and len(generated) == 300,
                        f"{run}: incomplete generation coverage")

                # Re-exports contain duplicate diagnostic folders: require their
                # per-rendering results to agree, then use one deterministically.
                diagnostics = sorted(n for n in archive.namelist()
                                     if n.startswith(prefix + "secondary_diagnostic_")
                                     and n.endswith("/secondary_metrics.json"))
                require(diagnostics, f"{run}: missing numeric diagnostic")
                numeric = None
                for name in diagnostics:
                    diagnostic = json.loads(archive.read(name))
                    require(diagnostic["source_sha256"]["generation_attempts.jsonl"]
                            == hashlib.sha256(archive.read(attempts_name)).hexdigest(),
                            f"{run}: numeric diagnostic journal hash mismatch")
                    records = diagnostic["renderings"]
                    candidate = {r["rendering_id"]: r for r in records}
                    require(len(records) == len(candidate) == 300
                            and set(candidate) == set(generated), f"{run}: numeric coverage mismatch")
                    require(numeric is None or numeric == candidate,
                            f"{run}: conflicting numeric diagnostic exports")
                    numeric = candidate

                for rid in sorted(generated):
                    row = generated[rid]
                    family, form, rendering = inputs[rid]
                    require(row["family_id"] == family["family_id"] and row["form"] == form
                            and row["input_text"] == rendering["text"] and row["gold"] == family["gold"],
                            f"{run}: input/journal mismatch {rid}")
                    secondary = numeric[rid]
                    require(secondary["attempt_id"] == row["attempt_id"]
                            and secondary["strict_correct"] == row["correct"]
                            and secondary["strict_invalid_reason"] == row["invalid_reason"]
                            and secondary["truncated"] == row["truncated"]
                            and secondary["numeric"]["endpoint"] == "numeric_literal_v1",
                            f"{run}: diagnostic/journal mismatch {rid}")
                    if form != "C" or row["correct"]:
                        continue
                    gold = family["gold"]
                    packet.append({
                        "rendering_id": f"{run}:{rid}",
                        "family_id": family["family_id"], "form": form,
                        "question": rendering["text"],
                        "gold": f"{gold['value']} {gold['unit']}".strip(),
                        "reference_equation": family["reference_equation"],
                        "model_output": row["raw_response"],
                        "strict_correct": row["correct"],
                        "strict_invalid_reason": row["invalid_reason"],
                        "truncated": row["truncated"],
                        "arm": arm, "seed": seed, "source_rendering_id": rid,
                        "gold_metadata": gold, "numeric": secondary["numeric"],
                        "attempt_id": row["attempt_id"], "run_id": row["run_id"],
                    })
    counts = Counter(row["arm"] for row in packet)
    require(counts == {"ER": 159, "EC": 172} and len(packet) == 331,
            f"Unexpected failure coverage: {dict(counts)}")
    require(len({r["rendering_id"] for r in packet}) == len(packet), "Duplicate audit IDs")
    OUTPUT.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in packet), encoding="utf-8")
    print(json.dumps({"total": len(packet), "by_arm": dict(counts), "by_run": dict(Counter(
        f"{r['arm']}-s{r['seed']}" for r in packet))}, indent=2))


if __name__ == "__main__":
    build_packet()
