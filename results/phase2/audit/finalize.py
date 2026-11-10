"""Phase-2 failure audit: final labels from the returned human checks (descriptive; strict scores unchanged).

All 331 rows are now human-checked, so every final label is the human label. The fallback rules below
(kept from the 65-row interim finalisation, git 94de9de) no longer fire.

Category: human label where checked (65 rows), otherwise the agreed A/B category (all unchecked rows agree).
English status: human label where checked; otherwise the agreed A/B label; for the unchecked English-only
disagreements (terse "label = equation" outputs) the human's adjudicated reading of the rule is applied, i.e.
tagger B's label (the human chose B's reading on 13/15 sampled rows). These rows are marked
label_source = "rule_adjudicated" and counted separately. Stdlib only."""
import csv, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
def jl(p): return [json.loads(l) for l in open(p, encoding="utf-8") if l.strip()]
rows = jl(HERE / "phase2_outputs_for_audit.jsonl")
A = {r["rendering_id"]: r for r in jl(HERE / "claude_tags.jsonl")}
B = {r["rendering_id"]: r for r in jl(HERE / "gpt_tags.jsonl")}
H = {}
for name in ("human_check_returned.csv", "human_check_remaining_part1_returned.csv", "human_check_remaining_part2_returned.csv"):
    for r in csv.DictReader(open(HERE / name, encoding="utf-8-sig")):
        assert r["rendering_id"] not in H, r["rendering_id"]
        H[r["rendering_id"]] = r
# Amendment 1 item 17: every audited output is human-checked (65 + 133 + 133 = 331).
assert set(H) == {r["rendering_id"] for r in rows}, len(H)
final = []
for r in rows:
    i = r["rendering_id"]
    if i in H:
        cat, eng, src = H[i]["YOUR_category"], H[i]["YOUR_english_status"], "human"
    else:
        assert A[i]["category"] == B[i]["category"], i
        cat = A[i]["category"]
        if A[i]["english_status"] == B[i]["english_status"]:
            eng, src = A[i]["english_status"], "ai_agreed"
        else:
            eng, src = B[i]["english_status"], "rule_adjudicated"
    final.append({"rendering_id": i, "arm": r["arm"], "seed": r["seed"], "category": cat, "english_status": eng, "label_source": src})
with open(HERE / "final_audit.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=list(final[0])); w.writeheader(); w.writerows(final)
summary = {"rows": len(final), "label_source": dict(collections.Counter(x["label_source"] for x in final))}
for arm in ("ER", "EC", "all"):
    sub = [x for x in final if arm == "all" or x["arm"] == arm]
    summary[arm] = {"failures": len(sub), "category": dict(collections.Counter(x["category"] for x in sub)),
                    "format_only": sum(x["category"] == "format_only" for x in sub),
                    "substantive": sum(x["category"] not in ("format_only", "no_error", "language_drift") for x in sub),
                    "english": dict(collections.Counter(x["english_status"] for x in sub))}
summary["human_vs_taggers"] = {why: {k: sum(1 for h in H.values() if h["why_listed"] == why and h["YOUR_" + f] == h["tagger_" + t + "_" + g])
                                     for k, f, t, g in (("A_category", "category", "A", "category"), ("B_category", "category", "B", "category"),
                                                        ("A_english", "english_status", "A", "english"), ("B_english", "english_status", "B", "english"))}
                               | {"rows": sum(1 for h in H.values() if h["why_listed"] == why)}
                               for why in sorted({h["why_listed"] for h in H.values()})}
(HERE / "final_audit_summary.json").write_text(json.dumps(summary, indent=1, sort_keys=True) + "\n")
print(json.dumps({k: summary[k] for k in ("ER", "EC", "all", "label_source")}, indent=1))
