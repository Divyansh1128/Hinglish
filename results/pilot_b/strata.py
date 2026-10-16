"""Pre-registered descriptive operation-word strata (pilot_b/PREREGISTRATION.md, endpoint 5).

Usage: python3 -B results/pilot_b/strata.py results/pilot_b/<model>/per_rendering.csv
Stratum is taken from frozen family provenance: 'C KEEPS' / 'C SWITCHES' / no Hindi operation word.
Counts and percentages only; no inference.
"""
import csv, json, sys, collections
fams = {f['family_id']: f for f in json.load(open('pilot_b/pilot_b_families.v2.json'))}
def stratum(f):
    p = f['provenance']
    return 'keep' if 'C KEEPS' in p else 'switch' if 'C SWITCHES' in p else 'none'
rows = list(csv.DictReader(open(sys.argv[1], encoding='utf-8-sig')))
key = next(k for k in rows[0] if k in ('strict_correct', 'correct'))
tab = collections.defaultdict(lambda: [0, 0])
for r in rows:
    s = stratum(fams[r['family_id']]); c = tab[(s, r['form'])]
    c[0] += r[key] in ('True', 'true', '1'); c[1] += 1
print('| Stratum | Families | E | R | C |\n|---|---:|---:|---:|---:|')
for s in ('keep', 'switch', 'none'):
    n = tab[(s, 'E')][1]
    print(f'| {s} | {n} | ' + ' | '.join(f'{tab[(s,f)][0]}/{n} ({100*tab[(s,f)][0]/n:.0f}%)' for f in 'ERC') + ' |')
