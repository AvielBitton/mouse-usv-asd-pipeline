#!/usr/bin/env python3
"""
Fig04 — annotated USV spectrogram (presentation-quality).

Spectrogram of one representative mouse-pup USV recording with the detector's
syllable bounding boxes overlaid. Rebuild of the visual layer only.

IMPORTANT — what this script does and does not do
--------------------------------------------------
* The detector is NOT run here. It already ran offline; its results live in the
  CSV (segmentation_classification_all_data.csv). This script only *reads* the
  detected box coordinates and *draws* them.
* The recording selection, box coordinates, and spectrogram (STFT) are copied
  verbatim from thesis/build/make_figures.py::f19() and are marked DO NOT MODIFY.
* Every knob below is display-only: view cropping (xlim/ylim), colours, fonts,
  axes. No detection is added, moved, resized, filtered, or removed. All 35
  boxes for the chosen recording are drawn, including any false positives.

Run:
    python3 hit_presentention/build/make_fig04_spectrogram.py
"""

# ==========================================================================
#  DISPLAY PARAMETERS  —  edit freely, nothing here touches the detector/data
# ==========================================================================
TIME_WINDOW = (0.0, 10.0)      # seconds — VIEW crop only (set_xlim), not a data cut
FREQ_WINDOW = (30, 125)        # kHz     — VIEW crop only (set_ylim), not a data cut
SHOW_TITLE = False             # no title, and no reserved space above the axes
BOX_COLOR = "#38BDF8"          # detected-syllable box colour
BOX_LINEWIDTH = 1.2
CMAP = "inferno"               # do not change without asking (was "magma" originally — see notes)
DPI = 300
FIGSIZE = (14, 6)
TRANSPARENT_BG = True          # surround transparent; spectrogram area stays dark

# --- extra visual knobs (all display-only; safe to tune) ------------------
FOREGROUND_COLOR = "#14181D"   # axis labels / ticks / spines (deck ink). Use "#FFFFFF" on dark slides.
VMIN_DB = -65                  # colormap intensity floor (unchanged from original)
VMAX_DB = 0                    # colormap intensity ceiling (unchanged from original)
AXIS_LABEL_FONTSIZE = 14
TICK_FONTSIZE = 12
OUTPUT_DIR = None              # None -> hit_presentention/presentation_figures
FILENAME_TEMPLATE = "Fig04_annotated_{a:g}-{b:g}s.png"

# --- optional DISPLAY-ONLY notch filter (default OFF) ---------------------
# Visually attenuates the fixed horizontal noise bands (~32/40/65 kHz) in the
# *displayed* spectrogram only. The detector never sees this — its results were
# computed offline from the raw recording and are read from the CSV as-is.
DISPLAY_NOTCH_FILTER = False
NOTCH_BANDS_KHZ = (32, 40, 65) # centres of the persistent noise bands
NOTCH_HALFWIDTH_KHZ = 1.5      # half-height of each attenuated band
NOTCH_ATTENUATION_DB = 12      # dB knocked off inside each band (display dimming)
# ==========================================================================
#  END OF PARAMETERS
# ==========================================================================

import os, re, glob
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

REPO = Path(__file__).resolve().parents[2]
CSV = REPO / "outputs/external/input/segmentation_classification_all_data.csv"


# ==========================================================================
#  DETECTOR / DATA LOGIC  —  DO NOT MODIFY
#  Verbatim from thesis/build/make_figures.py::f19(). Detections are
#  pre-computed and read from the CSV; nothing here runs the detector.
# ==========================================================================
def _resolve_wav(path, name):
    norm = lambda s: re.sub(r"[^a-z0-9]", "", str(s).lower())
    base = os.path.splitext(path.split("/")[-1])[0]
    parts = path.split("/")
    dd = norm(next((p for p in parts if p.lower().startswith("day")), ""))
    ss = norm(next((p for p in parts if p.lower().startswith("session")), ""))
    nn = norm(name)
    cands = glob.glob(f"{REPO}/USV_Recordings/**/{base}.WAV", recursive=True) + \
            glob.glob(f"{REPO}/USV_Recordings/**/{base}.wav", recursive=True)
    for c in cands:
        cn = norm(c)
        if nn in cn and dd in cn and ss in cn:
            return c
    return None


def select_recording_and_syllables():
    """Pick the same recording f19() picks and return its detected syllables.
    The detector already ran on the full recording; we only read its output."""
    df = pd.read_csv(CSV, low_memory=False)
    sub = df[df["Noise"] == 0]
    g = (sub.groupby(["Path", "Name"])
         .agg(n=("Path", "size"), shz=("Start Point (Hz)", "mean")).reset_index())
    g = g[(g["n"] >= 15) & (g["n"] <= 35) & (g["shz"] > 55000) & (g["shz"] < 92000)] \
        .sort_values("n", ascending=False)
    wav = chosen = None
    for _, row in g.head(60).iterrows():
        r = _resolve_wav(row["Path"], row["Name"])
        if r:
            wav, chosen = r, row
            break
    if wav is None:
        raise RuntimeError("no recording resolved for Fig04")
    syl = df[(df["Path"] == chosen["Path"]) & (df["Name"] == chosen["Name"])]
    return wav, chosen, syl


def compute_spectrogram(wav):
    """STFT of the FULL recording, identical to f19() (n_fft=2048, hop=256, sr=None)."""
    import librosa
    y, sr = librosa.load(wav, sr=None)
    n_fft = 2048
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=n_fft, hop_length=256)), ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft) / 1000.0
    times = librosa.frames_to_time(np.arange(D.shape[1]), sr=sr, hop_length=256)
    return D, freqs, times, sr
# ==========================================================================
#  END DO-NOT-MODIFY BLOCK
# ==========================================================================


def _apply_display_notch(D_disp, freqs):
    """DISPLAY-ONLY visual attenuation of the fixed noise bands.

    Operates on a copy of the spectrogram matrix that is used solely for
    pcolormesh. It never feeds the detector (the detector ran offline; its
    results are read from the CSV). This is a flat per-band dB dimming — no
    smoothing, interpolation, or synthesis.
    """
    for center in NOTCH_BANDS_KHZ:
        band = np.abs(freqs - center) <= NOTCH_HALFWIDTH_KHZ
        D_disp[band, :] = np.maximum(D_disp[band, :] - NOTCH_ATTENUATION_DB, VMIN_DB)
    return D_disp


def count_syllables(syl, window):
    """Console-only counting for the slide caption. Draws nothing, filters nothing."""
    a, b = window
    t0 = syl["Start point(s)"].to_numpy(dtype=float)
    t1 = syl["End point(s)"].to_numpy(dtype=float)
    n_total = len(syl)
    n_overlap = int(((t1 > a) & (t0 < b)).sum())      # at least partly visible in the view
    n_contained = int(((t0 >= a) & (t1 <= b)).sum())  # fully inside the view
    return n_total, n_overlap, n_contained


def main():
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
        "svg.fonttype": "none",
    })

    wav, chosen, syl = select_recording_and_syllables()
    D, freqs, times, sr = compute_spectrogram(wav)

    # ---- display-only data reduction (verbatim from f19): plot up to 125 kHz ----
    m = freqs <= 125
    freqs_m = freqs[m]
    D_disp = D[m, :].copy()   # copy is display-only; detector output is untouched
    if DISPLAY_NOTCH_FILTER:
        print("  [WARNING] DISPLAY_NOTCH_FILTER is ON — the SHOWN spectrogram is "
              "visually attenuated around %s kHz. This is display-only; the detector "
              "boxes come from the raw recording and are unchanged." % (NOTCH_BANDS_KHZ,))
        D_disp = _apply_display_notch(D_disp, freqs_m)

    # ---- figure ----
    fig, ax = plt.subplots(figsize=FIGSIZE)
    ax.pcolormesh(times, freqs_m, D_disp, cmap=CMAP, shading="auto",
                  vmin=VMIN_DB, vmax=VMAX_DB, rasterized=True)

    # ---- detected syllable boxes (drawn exactly as f19; none added/moved/dropped) ----
    for _, s in syl.iterrows():
        t0, t1 = s["Start point(s)"], s["End point(s)"]
        f0, f1 = s["Start Point (Hz)"] / 1000, s["End Point (Hz)"] / 1000
        lo, hi = min(f0, f1), max(f0, f1)
        ax.add_patch(Rectangle((t0, lo - 4), t1 - t0, (hi - lo) + 8, fill=False,
                               edgecolor=BOX_COLOR, lw=BOX_LINEWIDTH))

    # ---- VIEW crop only (does not touch the data arrays or the detector) ----
    ax.set_xlim(*TIME_WINDOW)
    ax.set_ylim(*FREQ_WINDOW)

    # ---- typography ----
    ax.set_xlabel("Time (s)", fontsize=AXIS_LABEL_FONTSIZE, color=FOREGROUND_COLOR)
    ax.set_ylabel("Frequency (kHz)", fontsize=AXIS_LABEL_FONTSIZE, color=FOREGROUND_COLOR)
    if SHOW_TITLE:
        ax.set_title("Detected USV syllables overlaid on the spectrogram",
                     fontsize=AXIS_LABEL_FONTSIZE + 1, color=FOREGROUND_COLOR, pad=8)

    # ---- axes & frame: keep left+bottom, drop top+right, thin outward ticks ----
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    for sp in ("left", "bottom"):
        ax.spines[sp].set_visible(True)
        ax.spines[sp].set_color(FOREGROUND_COLOR)
        ax.spines[sp].set_linewidth(0.8)
    ax.tick_params(direction="out", length=3.5, width=0.8,
                   labelsize=TICK_FONTSIZE, colors=FOREGROUND_COLOR)
    ax.grid(False)

    # ---- background: surround transparent, spectrogram stays dark ----
    if TRANSPARENT_BG:
        fig.patch.set_alpha(0.0)
        ax.set_facecolor("none")
    else:
        fig.patch.set_facecolor("white")
        ax.set_facecolor("white")

    # ---- save ----
    out_dir = Path(OUTPUT_DIR) if OUTPUT_DIR else (REPO / "hit_presentention" / "presentation_figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    a, b = TIME_WINDOW
    out = out_dir / FILENAME_TEMPLATE.format(a=a, b=b)
    fig.savefig(out, dpi=DPI, bbox_inches="tight", pad_inches=0.05, transparent=TRANSPARENT_BG)
    plt.close(fig)

    # ---- console report (for the slide caption; nothing is drawn on the image) ----
    n_total, n_overlap, n_contained = count_syllables(syl, TIME_WINDOW)
    rel_wav = os.path.relpath(wav, REPO)
    print(f"  recording : {rel_wav}")
    print(f"  view      : time {TIME_WINDOW} s, freq {FREQ_WINDOW} kHz"
          f"{'  [+display notch]' if DISPLAY_NOTCH_FILTER else ''}")
    print(f"  syllables : {n_total} total in this recording (all drawn, incl. false positives)")
    print(f"              {n_overlap} fall within the {TIME_WINDOW[0]:g}-{TIME_WINDOW[1]:g}s view"
          + (f" ({n_contained} fully inside)" if n_contained != n_overlap else ""))
    print(f"  saved     : {out}")


if __name__ == "__main__":
    main()
