#!/usr/bin/env python3
"""Shared figure style (colorblind-safe Okabe-Ito) + diagram helpers + manifest."""
import json
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

REPO = Path(__file__).resolve().parents[2]
FIGDIR = REPO / "thesis" / "figures"
MANIFEST = REPO / "thesis" / "figure_manifest.json"

# Okabe-Ito colorblind-safe palette
OI = {
    "black": "#000000", "orange": "#E69F00", "skyblue": "#56B4E9",
    "green": "#009E73", "yellow": "#F0E442", "blue": "#0072B2",
    "vermillion": "#D55E00", "purple": "#CC79A7", "grey": "#999999",
}
WT_C, HT_C = OI["blue"], OI["vermillion"]
MODEL_C = {
    "xgboost": OI["blue"], "xgboost_tuned": OI["skyblue"], "tabpfn": OI["green"],
    "bilstm": OI["orange"], "cnn1d": OI["purple"], "transformer": OI["vermillion"],
}
DEP_C, INDEP_C = OI["skyblue"], OI["vermillion"]


def apply_style():
    plt.rcParams.update({
        "figure.dpi": 120, "savefig.dpi": 300, "savefig.bbox": "tight",
        "font.size": 11, "axes.titlesize": 12, "axes.titleweight": "bold",
        "axes.labelsize": 11, "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.6,
        "legend.frameon": False, "figure.facecolor": "white", "axes.facecolor": "white",
        "font.family": "DejaVu Sans",
    })


# ---------- diagram primitives ----------
def box(ax, x, y, w, h, text, fc="#FFFFFF", ec=OI["black"], fontsize=9.5,
        text_color="#000000", lw=1.4, rounding=0.02, bold=False):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.01,rounding_size={rounding}",
                       fc=fc, ec=ec, lw=lw, zorder=2)
    ax.add_patch(p)
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            fontsize=fontsize, color=text_color, zorder=3,
            fontweight="bold" if bold else "normal", wrap=True)
    return (x, y, w, h)


def arrow(ax, xy_from, xy_to, color=OI["black"], lw=1.6, style="-|>", rad=0.0):
    a = FancyArrowPatch(xy_from, xy_to, arrowstyle=style, mutation_scale=14,
                        lw=lw, color=color, zorder=1,
                        connectionstyle=f"arc3,rad={rad}")
    ax.add_patch(a)


def blank_ax(fig_w, fig_h, xlim=(0, 100), ylim=(0, 100)):
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.set_xlim(*xlim)
    ax.set_ylim(*ylim)
    ax.axis("off")
    return fig, ax


# ---------- manifest ----------
def _load_manifest():
    if MANIFEST.exists():
        return json.loads(MANIFEST.read_text())
    return {}


def save(fig, num, title, caption, sources):
    """Save fig as PNG+PDF under figures/, register in manifest. num like 'F1','F4b'."""
    FIGDIR.mkdir(parents=True, exist_ok=True)
    stem = f"fig_{num.lower()}"
    png = FIGDIR / f"{stem}.png"
    pdf = FIGDIR / f"{stem}.pdf"
    fig.savefig(png)
    fig.savefig(pdf)
    plt.close(fig)
    m = _load_manifest()
    m[num] = {"number": num, "title": title, "caption": caption,
              "sources": sources if isinstance(sources, list) else [sources],
              "png": str(png.relative_to(REPO)), "pdf": str(pdf.relative_to(REPO))}
    MANIFEST.write_text(json.dumps(m, indent=2))
    print(f"  saved {num}: {png.name}")


def reset_manifest():
    if MANIFEST.exists():
        MANIFEST.unlink()
