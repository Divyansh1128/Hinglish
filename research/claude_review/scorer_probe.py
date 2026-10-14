"""Model-free probe of the frozen scorer v1.0.0 against plausible output formats.

Synthetic strings only: no model was run. Each probe applies one formatting
variant to every draft family's own gold value/unit, so a failure means the
format is rejected, never that the arithmetic is wrong. Does not print gold.

Run from the repository root: python3 -B research/claude_review/scorer_probe.py
"""
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'pilot' / 'scripts'))
from scorer import SCORER_VERSION, score_response  # noqa: E402

DATASET = ROOT / 'pilot' / 'annotation_draft_v2' / 'coordinator' / 'pilot_dataset.DRAFT.json'

ALL = {
    'plain FINAL line': lambda v, u: f'Work.\nFINAL: {v} {u}',
    'markdown header before FINAL': lambda v, u: f'Work.\n### Final Answer\nFINAL: {v} {u}',
    'bold marker **FINAL:**': lambda v, u: f'Work.\n**FINAL:** {v} {u}',
    'bold value FINAL: **v**': lambda v, u: f'Work.\nFINAL: **{v}**',
    'LaTeX FINAL: \\boxed{v}': lambda v, u: f'Work.\nFINAL: \\boxed{{{v}}}',
    'LaTeX FINAL: $v$': lambda v, u: f'Work.\nFINAL: ${v}$',
    'note after FINAL line': lambda v, u: f'Work.\nFINAL: {v} {u}\n(Answer in {u or "units"}.)',
    '"I cannot" inside reasoning': lambda v, u: f'I cannot add these directly, so subtract first.\nFINAL: {v} {u}',
}
INR = {'prefix Rs.': 'FINAL: Rs. {v}', 'prefix Rs': 'FINAL: Rs {v}', 'prefix ₹': 'FINAL: ₹{v}',
       'suffix rupaye': 'FINAL: {v} rupaye', 'suffix /-': 'FINAL: ₹{v}/-'}
ALGEBRA = {'FINAL: v': 'FINAL: {v}', 'FINAL: x = v': 'FINAL: x = {v}'}
HINDI_UNITS = {'kg': 'kilo', 'minute': 'minat', 'L': 'litar', 'm': 'mitar', 'km': 'kilomitar'}


def summary(results):
    reasons = Counter(r['invalid_reason'] or 'accepted' for r in results)
    return f"{sum(r['correct'] for r in results)}/{len(results)} accepted  {dict(reasons)}"


def main():
    families = json.loads(DATASET.read_text(encoding='utf-8'))['families']
    gold = [f['gold'] for f in families]
    print(f'Scorer {SCORER_VERSION}; {len(families)} DRAFT families (not human-accepted)\n')
    print('All families, value + canonical unit:')
    for name, make in ALL.items():
        print(f'  {name:32s} ' + summary([score_response(make(g['value'], g['unit']).rstrip(), g) for g in gold]))
    money = [g for g in gold if g['unit'] == 'INR']
    print(f'\nINR families ({len(money)}):')
    for name, text in INR.items():
        print(f'  {name:32s} ' + summary([score_response('Work.\n' + text.format(v=g['value']), g) for g in money]))
    algebra = [f['gold'] for f in families if f['topic'] == 'elementary_algebra' and not f['gold']['unit']]
    print(f'\nDimensionless elementary_algebra families ({len(algebra)}):')
    for name, text in ALGEBRA.items():
        print(f'  {name:32s} ' + summary([score_response('Work.\n' + text.format(v=g['value']), g) for g in algebra]))
    print('\nRomanized-Hindi unit words not in aliases/conversions:')
    for unit, word in HINDI_UNITS.items():
        group = [g for g in gold if g['unit'] == unit]
        if group:
            print(f'  {unit:6s} -> {word:10s} ' + summary([score_response(f"Work.\nFINAL: {g['value']} {word}", g) for g in group]))


if __name__ == '__main__':
    main()
