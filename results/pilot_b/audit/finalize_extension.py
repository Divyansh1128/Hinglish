"""Finalize the post-hoc audit extension (Qwen3-8B, Llama-3.2-3B) from the returned human check.

Final label = human label where checked (all disagreement rows + seeded random agreed rows), else the
unanimous label of taggers A/B/C. Descriptive only; never changes strict scores. Stdlib only."""
import csv, json, collections
from pathlib import Path
HERE = Path(__file__).resolve().parent
MODELS = ("qwen3-8b", "llama-3.2-3b")
def jl(p): return {r["rendering_id"]: r for r in (json.loads(l) for l in open(p, encoding="utf-8") if l.strip())}
human = list(csv.DictReader(open(HERE / "human_check_extension_returned.csv", encoding="utf-8-sig")))
out = {"agreement": {}, "summary": {}}
for m in MODELS:
    A, B, C = jl(HERE / f"claude_tags_{m}.jsonl"), jl(HERE / f"gpt_tags_{m}.jsonl"), jl(HERE / f"second_tags_{m}.jsonl")
    rows = [json.loads(l) for l in open(HERE / f"{m}_outputs_for_audit.jsonl", encoding="utf-8") if l.strip()]
    hm = {h["rendering_id"]: h for h in human if h["model"] == m}
    agree = collections.Counter()
    for rid, h in hm.items():
        for name, T in (("A", A), ("B", B), ("C", C)):
            agree[name + "_cat"] += T[rid]["category"] == h["YOUR_category"]
            agree[name + "_eng"] += T[rid]["english_status"] == h["YOUR_english_status"]
        agree["disagree_rows"] += h["why_listed"] == "TAGGERS DISAGREE"
    agree["checked"] = len(hm)
    out["agreement"][m] = dict(agree)
    final, cats = [], collections.Counter()
    for r in rows:
        rid = r["rendering_id"]
        if rid in hm:
            cat, eng, src = hm[rid]["YOUR_category"], hm[rid]["YOUR_english_status"], "human"
        else:
            labs = {(T[rid]["category"], T[rid]["english_status"]) for T in (A, B, C)}
            assert len(labs) == 1, f"{m} {rid}: unchecked row without unanimous tags"
            (cat, eng), src = labs.pop(), "ai_unanimous"
        form = rid.split("-")[1]
        strict = str(r.get("strict_correct", r.get("correct")))
        final.append({"rendering_id": rid, "form": form, "strict_correct": strict, "category": cat, "english_status": eng, "label_source": src})
    with open(HERE / f"final_audit_{m}.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(final[0])); w.writeheader(); w.writerows(final)
    summ = {"rows": len(final), "human_checked": sum(x["label_source"] == "human" for x in final)}
    for form in "ERC":
        sub = [x for x in final if x["form"] == form]
        summ[form] = {"category": dict(collections.Counter(x["category"] for x in sub)),
                      "english": dict(collections.Counter(x["english_status"] for x in sub)),
                      "strict_failures": sum(x["strict_correct"] != "True" for x in sub),
                      "format_only_failures": sum(x["strict_correct"] != "True" and x["category"] == "format_only" for x in sub)}
    out["summary"][m] = summ
(HERE / "final_audit_extension_summary.json").write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
print(json.dumps(out["agreement"], indent=1))
for m in MODELS:
    s = out["summary"][m]; print(m, {f: (s[f]["strict_failures"], s[f]["format_only_failures"], s[f]["english"].get("compliant")) for f in "ERC"})
