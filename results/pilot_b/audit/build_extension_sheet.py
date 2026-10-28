"""Post-hoc audit extension (Qwen3-8B, Llama-3.2-3B): agreement between the two AI taggers and the human-check sheet.

Taggers: A = Claude Opus (claude_tags_<model>.jsonl), B = Claude Sonnet (second_tags_<model>.jsonl), each blind to
the other. Both are Claude models (GPT unavailable), so the sheet adds every disagreement plus 30 seeded random
agreed rows per model (vs 20 for the pre-registered Qwen3-4B audit). Usage: python3 -B build_extension_sheet.py
"""
import csv
import json
import random
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
MODELS = ('qwen3-8b', 'llama-3.2-3b')
SAMPLE = 30
SEED = 101


def load(path):
    return {row['rendering_id']: row for row in map(json.loads, path.read_text().splitlines()) if row}


def kappa(pairs):
    n = len(pairs)
    observed = sum(a == b for a, b in pairs) / n
    left, right = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(left[k] * right[k] for k in left) / n ** 2
    return observed if expected == 1 else (observed - expected) / (1 - expected)


summary, sheet = {}, []
for model in MODELS:
    inputs = load(HERE / f'{model}_outputs_for_audit.jsonl')
    a, b = load(HERE / f'claude_tags_{model}.jsonl'), load(HERE / f'second_tags_{model}.jsonl')
    assert set(inputs) == set(a) == set(b) and len(inputs) == 210, model
    ids = sorted(inputs)
    stats = {}
    for field in ('category', 'english_status'):
        pairs = [(a[i][field], b[i][field]) for i in ids]
        stats[field] = {'agree': sum(x == y for x, y in pairs), 'n': len(pairs), 'kappa': round(kappa(pairs), 3)}
    disagree = [i for i in ids if (a[i]['category'], a[i]['english_status']) != (b[i]['category'], b[i]['english_status'])]
    agreed = [i for i in ids if i not in disagree]
    sample = sorted(random.Random(f'{SEED}-{model}').sample(agreed, SAMPLE))
    stats.update(disagreements=len(disagree), random_agreed_sample=SAMPLE)
    summary[model] = stats
    for why, chosen in (('TAGGERS DISAGREE', disagree), ('RANDOM AGREED SAMPLE', sample)):
        for i in chosen:
            row = inputs[i]
            sheet.append({'model': model, 'rendering_id': i, 'why_listed': why, 'question': row['question'],
                          'model_output': row['model_output'], 'gold': row['gold'], 'strict_correct': row['strict_correct'],
                          'tagger_A_category': a[i]['category'], 'tagger_A_english': a[i]['english_status'],
                          'tagger_A_reason': a[i]['reason'], 'tagger_B_category': b[i]['category'],
                          'tagger_B_english': b[i]['english_status'], 'tagger_B_reason': b[i]['reason'],
                          'YOUR_category': '', 'YOUR_english_status': '', 'YOUR_note': ''})

with open(HERE / 'human_check_sheet_extension.csv', 'w', newline='', encoding='utf-8-sig') as handle:
    writer = csv.DictWriter(handle, fieldnames=list(sheet[0]))
    writer.writeheader()
    writer.writerows(sheet)
(HERE / 'extension_agreement.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps(summary, indent=2), len(sheet), 'sheet rows')
