"""Phase-2 failure audit: tagger agreement and the human-check sheet (all disagreements + 20 seeded random agreed rows).

A = Claude (claude_tags.jsonl), B = GPT (gpt_tags.jsonl), both blind to each other. Mirrors the Pilot-B audit. Stdlib only."""
import csv, json, random, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
rows = jl(HERE / "phase2_outputs_for_audit.jsonl")
A = {r["rendering_id"]: r for r in jl(HERE / "claude_tags.jsonl")}
B = {r["rendering_id"]: r for r in jl(HERE / "gpt_tags.jsonl")}
assert len(rows) == len(A) == len(B) == 331 and set(A) == set(B) == {r["rendering_id"] for r in rows}
def kappa(pairs):
    n = len(pairs); po = sum(a == b for a, b in pairs) / n
    ca, cb = collections.Counter(a for a, _ in pairs), collections.Counter(b for _, b in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / n / n
    return round((po - pe) / (1 - pe), 3) if pe < 1 else 1.0
ids = [r["rendering_id"] for r in rows]
cat = [(A[i]["category"], B[i]["category"]) for i in ids]
eng = [(A[i]["english_status"], B[i]["english_status"]) for i in ids]
fo = [(A[i]["category"] == "format_only", B[i]["category"] == "format_only") for i in ids]
agreement = {"rows": len(ids), "category_agree": sum(a == b for a, b in cat), "category_kappa": kappa(cat),
             "english_agree": sum(a == b for a, b in eng), "english_kappa": kappa(eng),
             "format_only_vs_substantive_agree": sum(a == b for a, b in fo), "format_only_kappa": kappa(fo),
             "A_category": dict(collections.Counter(a for a, _ in cat)), "B_category": dict(collections.Counter(b for _, b in cat))}
# Category disagreements are all checked. English-status-only disagreements (214) are systematic: terse
# "label = equation" outputs read as compliant by A and as no_explanation by B (a rule ambiguity), so a seeded
# sample of 15 is adjudicated instead of all of them. Plus 20 seeded rows on which both labels agree.
rng = random.Random(101)
disagree = [i for i in ids if A[i]["category"] != B[i]["category"]]
english_only = [i for i in ids if A[i]["category"] == B[i]["category"] and A[i]["english_status"] != B[i]["english_status"]]
agreed = [i for i in ids if A[i]["category"] == B[i]["category"] and A[i]["english_status"] == B[i]["english_status"]]
sample = rng.sample(agreed, 20)
english_sample = rng.sample(english_only, 15)
listed = ([(i, "TAGGERS DISAGREE (category)") for i in disagree] + [(i, "RANDOM AGREED SAMPLE") for i in sample]
          + [(i, "ENGLISH STATUS DISAGREE (sample)") for i in english_sample])
listed.sort(key=lambda t: ids.index(t[0]))
by = {r["rendering_id"]: r for r in rows}
fields = ["rendering_id", "arm", "seed", "why_listed", "question", "model_output", "gold", "gold_unit", "strict_invalid_reason",
          "tagger_A_category", "tagger_A_english", "tagger_A_reason", "tagger_B_category", "tagger_B_english", "tagger_B_reason",
          "YOUR_category", "YOUR_english_status", "YOUR_note"]
with open(HERE / "human_check_sheet.csv", "w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for i, why in listed:
        r = by[i]
        w.writerow({"rendering_id": i, "arm": r["arm"], "seed": r["seed"], "why_listed": why, "question": r["question"],
                    "model_output": r["model_output"], "gold": r["gold"], "gold_unit": r["gold_metadata"].get("unit", ""),
                    "strict_invalid_reason": r["strict_invalid_reason"] or "wrong value",
                    "tagger_A_category": A[i]["category"], "tagger_A_english": A[i]["english_status"], "tagger_A_reason": A[i]["reason"],
                    "tagger_B_category": B[i]["category"], "tagger_B_english": B[i]["english_status"], "tagger_B_reason": B[i]["reason"],
                    "YOUR_category": "", "YOUR_english_status": "", "YOUR_note": ""})
agreement.update({"disagreement_rows": len(disagree), "sample_rows": len(sample), "english_sample_rows": len(english_sample), "sheet_rows": len(listed),
                  "category_only_disagreements": sum(A[i]["category"] != B[i]["category"] for i in ids),
                  "english_only_disagreements": sum(A[i]["category"] == B[i]["category"] and A[i]["english_status"] != B[i]["english_status"] for i in ids)})
(HERE / "agreement.json").write_text(json.dumps(agreement, indent=1, sort_keys=True) + "\n")
print(json.dumps(agreement, indent=1, sort_keys=True))
