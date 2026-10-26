"""Regenerate the report's extra figures from stored per-rendering scores (no rescoring).

Run from the repository root:  python3 -B report/figures/make_figures.py
Reads only results/<cohort>/<model>/per_rendering.csv and, for the stratum tags,
pilot_b/pilot_b_families.v2.json (the same rule as results/pilot_b/strata.py).
Writes report/figures/original_cohort_accuracy.pdf and report/figures/pilotb_r_by_stratum.pdf.
"""
import csv, json, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt

MODELS = [('qwen3-4b', 'Qwen3-4B (primary)'), ('qwen3-8b', 'Qwen3-8B'), ('llama-3.2-3b', 'Llama-3.2-3B')]
COLORS = {'E': '#0072B2', 'R': '#E69F00', 'C': '#009E73'}  # Okabe-Ito, same as paper Figure 1
OUT = 'report/figures/'

def wilson(k, n, z=1.959963984540054):
    p = k / n; c = (p + z*z/(2*n)) / (1 + z*z/n); r = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n)) / (1 + z*z/n)
    return max(0, c - r), min(1, c + r)

def rows(cohort, slug):
    return list(csv.DictReader(open(f'results/{cohort}/{slug}/per_rendering.csv', encoding='utf-8-sig')))

def style(ax):
    ax.spines[['top', 'right']].set_visible(False)
    ax.yaxis.grid(True, color='#dddddd', lw=0.6); ax.set_axisbelow(True)

# Figure A: original cohort, strict accuracy by form with Wilson intervals (24 families per bar).
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
for ax, (slug, title) in zip(axes, MODELS):
    rs = rows('pilot_original', slug)
    for i, form in enumerate('ERC'):
        xs = [r for r in rs if r['form'] == form]; k = sum(r['correct'] == 'True' for r in xs); n = len(xs)
        lo, hi = wilson(k, n); p = k / n
        ax.bar(i, 100*p, color=COLORS[form], width=0.65)
        ax.errorbar(i, 100*p, yerr=[[100*(p-lo)], [100*(hi-p)]], color='black', capsize=3, lw=1)
        ax.text(i, 3, f'{100*p:.1f}', ha='center', va='bottom', fontsize=7, color='white', fontweight='bold')
    ax.set_xticks(range(3), ['E', 'R', 'C']); ax.set_title(title, fontsize=8); ax.set_ylim(0, 105); style(ax)
axes[0].set_ylabel('Strict accuracy (%)', fontsize=8)
fig.tight_layout(); fig.savefig(OUT + 'original_cohort_accuracy.pdf')

# Figure B: Pilot-B strict R accuracy by pre-registered operation-word stratum (descriptive).
fams = {f['family_id']: f for f in json.load(open('pilot_b/pilot_b_families.v2.json', encoding='utf-8'))}
def stratum(f):
    p = f['provenance']
    return 'keep' if 'C KEEPS' in p else 'switch' if 'C SWITCHES' in p else 'none'
SLAB = {'keep': 'C keeps\nHindi op-word', 'switch': 'C switches\nto English', 'none': 'No Hindi\nop-word'}
SCOL = {'keep': '#E69F00', 'switch': '#E69F00', 'none': '#E69F00'}
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.7), sharey=True)
for ax, (slug, title) in zip(axes, MODELS):
    rs = [r for r in rows('pilot_b', slug) if r['form'] == 'R']
    for i, s in enumerate(('keep', 'switch', 'none')):
        xs = [r for r in rs if stratum(fams[r['family_id']]) == s]; k = sum(r['correct'] == 'True' for r in xs); n = len(xs)
        lo, hi = wilson(k, n); p = k / n
        ax.bar(i, 100*p, color=SCOL[s], width=0.65, hatch=('' if s != 'none' else '//'), edgecolor='white', lw=0)
        ax.errorbar(i, 100*p, yerr=[[100*(p-lo)], [100*(hi-p)]], color='black', capsize=3, lw=1)
        ax.text(i, 3, f'{k}/{n}', ha='center', va='bottom', fontsize=7, color='black')
    ax.set_xticks(range(3), [SLAB[s] for s in ('keep', 'switch', 'none')], fontsize=6.5)
    ax.set_title(title, fontsize=8); ax.set_ylim(0, 105); style(ax)
axes[0].set_ylabel('Strict R accuracy (%)', fontsize=8)
fig.tight_layout(); fig.savefig(OUT + 'pilotb_r_by_stratum.pdf')
print('ok')
