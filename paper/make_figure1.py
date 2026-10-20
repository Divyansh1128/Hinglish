"""Figure 1: strict accuracy by form with Wilson 95% intervals, one panel per backbone (Pilot-B, 70 families).
Reads only results/pilot_b/<model>/per_rendering.csv (stored scores; no rescoring)."""
import csv, math
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
MODELS = [('qwen3-4b', 'Qwen3-4B (primary)'), ('qwen3-8b', 'Qwen3-8B'), ('llama-3.2-3b', 'Llama-3.2-3B')]
COLORS = {'E': '#0072B2', 'R': '#E69F00', 'C': '#009E73'}  # Okabe-Ito
def wilson(k, n, z=1.959963984540054):
    p = k/n; c = (p + z*z/(2*n))/(1 + z*z/n); r = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/(1 + z*z/n)
    return max(0, c-r), min(1, c+r)
fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.6), sharey=True)
for ax, (slug, title) in zip(axes, MODELS):
    rows = list(csv.DictReader(open(f'results/pilot_b/{slug}/per_rendering.csv', encoding='utf-8-sig')))
    for i, form in enumerate('ERC'):
        xs = [r for r in rows if r['form'] == form]; k = sum(r['correct'] == 'True' for r in xs); n = len(xs)
        lo, hi = wilson(k, n); p = k/n
        ax.bar(i, 100*p, color=COLORS[form], width=0.65)
        ax.errorbar(i, 100*p, yerr=[[100*(p-lo)], [100*(hi-p)]], color='black', capsize=3, lw=1)
        ax.text(i, 3, f'{100*p:.1f}', ha='center', va='bottom', fontsize=7, color='white', fontweight='bold')
    ax.set_xticks(range(3), ['E', 'R', 'C']); ax.set_title(title, fontsize=8); ax.set_ylim(0, 105)
    ax.spines[['top', 'right']].set_visible(False)
axes[0].set_ylabel('Strict accuracy (%)', fontsize=8)
fig.tight_layout(); fig.savefig('paper/figures/accuracy_by_form.pdf'); fig.savefig('paper/figures/accuracy_by_form.png', dpi=200)
print('ok')
