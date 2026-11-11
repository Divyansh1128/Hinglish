"""Check released score matrix; no model inference or rescoring. Python 3.9+."""
import csv, hashlib, random
from collections import Counter
from fractions import Fraction
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    for line in (root / 'checksums.sha256').read_text().splitlines():
        expected, name = line.split('  ', 1)
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == expected, name
    rows = list(csv.DictReader((root / 'phase2/scored_outcomes.csv').open()))
    runs = ['unchanged'] + [f'{a}-s{s}' for a in ['EE', 'ER', 'EC'] for s in [11, 22, 33]]
    expected = {(r, f'FT{i:03d}', f) for r in runs for i in range(1,101) for f in 'ERC'}
    keys = [(x['checkpoint'], x['family_id'], x['form']) for x in rows]
    assert len(rows) == 3000 and set(keys) == expected and len(set(keys)) == 3000
    assert all(x['correct'] in ['True', 'False'] for x in rows)
    values = {k: int(x['correct'] == 'True') for k, x in zip(keys,rows)}
    for run in runs:
        print(run, {f:sum(values[run,f'FT{i:03d}',f] for i in range(1,101)) for f in 'ERC'})
    d = [sum(values[f'EC-s{s}', f'FT{i:03d}', 'C'] - values[f'ER-s{s}', f'FT{i:03d}', 'C'] for s in [11,22,33]) for i in range(1,101)]
    rng = random.Random(101)
    digest = hashlib.sha256()
    samples = []
    for _ in range(10000):
        ix = [rng.randrange(100) for _ in range(100)]
        digest.update((','.join(map(str,ix))+'\n').encode())
        samples.append(Fraction(sum(d[i] for i in ix),300))
    samples.sort()
    def quantile(p):
        h=9999*p; lo=h.numerator//h.denominator
        return samples[lo]+(h-lo)*(samples[min(lo+1,9999)]-samples[lo])
    result=(Fraction(sum(d),300),quantile(Fraction(25,1000)),quantile(Fraction(975,1000)))
    assert result == (Fraction(-13,300), Fraction(-2,25), Fraction(-1,150)), result
    assert digest.hexdigest() == '33f4920eab5738cf29b346be8d63a15115f9fcbda58699ee9fc44b031e46e6a1'
    audit=list(csv.DictReader((root/'phase2/final_audit.csv').open()))
    assert len(audit)==331 and len({r['rendering_id'] for r in audit})==331
    assert all(r['label_source']=='human' for r in audit)
    incorrect={f"{r['checkpoint']}:{r['rendering_id']}" for r in rows if r['checkpoint'].startswith(('EC-','ER-')) and r['form']=='C' and r['correct']=='False'}
    assert {r['rendering_id'] for r in audit}==incorrect
    print('PASS: checksums, 3,000 unique outcomes, all 331 human-labelled failure rows.')
    print('Primary pp:',*[round(float(v)*100,6) for v in result], 'decision: Harm')
    print('Conditional on trained checkpoints; this verifies stored outcomes, not raw-answer scoring.')

if __name__ == '__main__': main()
