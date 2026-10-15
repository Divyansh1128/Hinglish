"""Optional matplotlib figures (PDF + PNG). Importing raises ImportError without matplotlib."""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402

FORMS = ("E", "R", "C")
# Okabe-Ito colorblind-safe hues; validated for CVD separation. Values are also printed
# directly on every mark so identity and magnitude never rely on colour alone.
FORM_COLORS = {"E": "#0072B2", "R": "#E69F00", "C": "#009E73"}
CORRECT, INCORRECT = "#0072B2", "#D55E00"
INK, MUTED = "#222222", "#666666"


def _style(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(MUTED)
    ax.tick_params(colors=INK, labelsize=9)


def _save(fig, folder, name):
    paths = []
    for ext in ("pdf", "png"):
        path = folder / f"{name}.{ext}"
        meta = {"CreationDate": None} if ext == "pdf" else {"Software": None}
        fig.savefig(path, dpi=300, bbox_inches="tight", metadata=meta)
        paths.append(path)
    plt.close(fig)
    return paths


def accuracy_bars(result, folder):
    acc = result["accuracy"]
    ys = [acc[f]["accuracy"] for f in FORMS]
    lows = [acc[f]["accuracy"] - acc[f]["wilson_95_interval"][0] for f in FORMS]
    highs = [acc[f]["wilson_95_interval"][1] - acc[f]["accuracy"] for f in FORMS]
    fig, ax = plt.subplots(figsize=(3.6, 3.0))
    ax.bar(FORMS, ys, width=0.6, color=[FORM_COLORS[f] for f in FORMS], edgecolor="white", linewidth=2, zorder=2)
    ax.errorbar(FORMS, ys, yerr=[lows, highs], fmt="none", ecolor=INK, elinewidth=1, capsize=4, zorder=3)
    for x, form in enumerate(FORMS):
        a = acc[form]
        ax.text(x, a["wilson_95_interval"][1] + 0.03, f"{a['correct']}/{a['denominator']}",
                ha="center", va="bottom", fontsize=8, color=INK)
    ax.set_ylim(0, 1.12)
    ax.set_yticks([0, 0.25, 0.5, 0.75, 1.0])
    ax.set_ylabel("Strict accuracy", color=INK, fontsize=9)
    ax.set_xlabel("Input form", color=INK, fontsize=9)
    ax.yaxis.grid(True, color="#e5e5e5", linewidth=0.6, zorder=0)
    ax.set_axisbelow(True)
    _style(ax)
    ax.set_title(f"{result['families']} families; Wilson 95% intervals", fontsize=9, color=MUTED)
    return _save(fig, folder, "accuracy_by_form")


def family_heatmap(result, folder):
    rows = result["family_rows"]
    grid = [[1 if row[f] else 0 for f in FORMS] for row in rows]
    height = max(2.0, 0.28 * len(rows) + 1.0)
    fig, ax = plt.subplots(figsize=(3.2, height))
    ax.imshow(grid, cmap=ListedColormap([INCORRECT, CORRECT]), vmin=0, vmax=1, aspect="auto")
    for y, values in enumerate(grid):
        for x, value in enumerate(values):
            ax.text(x, y, "✓" if value else "✗", ha="center", va="center", color="white", fontsize=9,
                    fontweight="bold")
    ax.set_xticks(range(len(FORMS)), FORMS)
    ax.set_yticks(range(len(rows)), [row["family_id"] for row in rows], fontsize=7)
    ax.xaxis.tick_top()
    ax.set_xticks([x - 0.5 for x in range(1, len(FORMS))], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, len(rows))], minor=True)
    ax.grid(which="minor", color="white", linewidth=2)
    ax.tick_params(which="minor", length=0)
    for spine in ax.spines.values():
        spine.set_visible(False)
    ax.tick_params(colors=INK, labelsize=8)
    handles = [plt.Rectangle((0, 0), 1, 1, color=CORRECT), plt.Rectangle((0, 0), 1, 1, color=INCORRECT)]
    ax.legend(handles, ["✓ correct", "✗ incorrect"], loc="upper center", bbox_to_anchor=(0.5, -0.02),
              ncol=2, frameon=False, fontsize=8)
    return _save(fig, folder, "family_heatmap")


def make_figures(result, folder):
    """Write both figures for a complete run; return the written paths."""
    folder.mkdir(parents=True, exist_ok=True)
    return accuracy_bars(result, folder) + family_heatmap(result, folder)
