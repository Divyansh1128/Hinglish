"""Phase-2 failure audit: sheet of the 266 rows not yet human-checked.

Amendment 1 item 17 requires a human check of every audited output (all 331). The first
human check covered 65 rows (human_check_returned.csv). This writes the other 266, split into
two halves (one per checker), in the same columns. Stdlib only."""
import csv, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
rows = jl(HERE / "phase2_outputs_for_audit.jsonl")
A = {r["rendering_id"]: r for r in jl(HERE / "claude_tags.jsonl")}
B = {r["rendering_id"]: r for r in jl(HERE / "gpt_tags.jsonl")}
done = {r["rendering_id"].lstrip("﻿") for r in csv.DictReader(open(HERE / "human_check_returned.csv", encoding="utf-8-sig"))}
assert len(done) == 65
todo = [r for r in rows if r["rendering_id"] not in done]
assert len(todo) == 266
fields = ["rendering_id", "arm", "seed", "why_listed", "question", "model_output", "gold", "gold_unit", "strict_invalid_reason",
          "tagger_A_category", "tagger_A_english", "tagger_A_reason", "tagger_B_category", "tagger_B_english", "tagger_B_reason",
          "YOUR_category", "YOUR_english_status", "YOUR_note"]
# Interleaved so each checker sees both arms (a checker effect must not line up with the arm contrast).
for name, part in (("human_check_remaining_part1.csv", todo[0::2]), ("human_check_remaining_part2.csv", todo[1::2])):
    with open(HERE / name, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
        for r in part:
            i = r["rendering_id"]
            why = "TAGGERS AGREE" if A[i]["english_status"] == B[i]["english_status"] else "ENGLISH STATUS DISAGREE"
            w.writerow({"rendering_id": i, "arm": r["arm"], "seed": r["seed"], "why_listed": why, "question": r["question"],
                        "model_output": r["model_output"], "gold": r["gold"], "gold_unit": r["gold_metadata"].get("unit", ""),
                        "strict_invalid_reason": r["strict_invalid_reason"] or "wrong value",
                        "tagger_A_category": A[i]["category"], "tagger_A_english": A[i]["english_status"], "tagger_A_reason": A[i]["reason"],
                        "tagger_B_category": B[i]["category"], "tagger_B_english": B[i]["english_status"], "tagger_B_reason": B[i]["reason"],
                        "YOUR_category": "", "YOUR_english_status": "", "YOUR_note": ""})
    print(name, len(part))
