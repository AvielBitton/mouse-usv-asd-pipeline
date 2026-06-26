#!/usr/bin/env python3
"""Data-driven figures F5-F21 (built only from result reports / data files)."""
import json, pickle, traceback, warnings
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import roc_curve, auc, precision_recall_curve, average_precision_score, confusion_matrix
import figstyle as S

warnings.filterwarnings("ignore")
REPO = Path(__file__).resolve().parents[2]
OI = S.OI
COMP = json.loads((REPO / "thesis" / "data_composition.json").read_text())
MR = json.loads((REPO / "thesis" / "master_results.json").read_text())
CSV = REPO / "outputs/external/input/segmentation_classification_all_data.csv"
THR = REPO / "results/tabular_models/threshold"


def mr(family=None, scope=None, split=None, model=None):
    out = []
    for r in MR:
        if family and r["family"] != family: continue
        if scope and r["scope"] != scope: continue
        if split and r["split"] != split: continue
        if model and r["model"] != model: continue
        out.append(r)
    return out


def _bar(ax, labels, vals, colors, title, ylab="mice", rot=0):
    b = ax.bar(range(len(labels)), vals, color=colors, edgecolor="black", lw=0.6)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=rot, fontsize=9)
    ax.set_title(title, fontsize=11); ax.set_ylabel(ylab)
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v}", ha="center", va="bottom", fontsize=8.5)
    ax.margins(y=0.18)


# ---------------- F5 dataset composition small multiples ----------------
def f5():
    fig, axes = plt.subplots(2, 3, figsize=(12, 7))
    g = COMP["raw"]["genotype_mice"]
    _bar(axes[0, 0], ["WT", "HT", "UNK"], [g.get("WT", 0), g.get("HT", 0), g.get("UNK", 0)],
         [S.WT_C, S.HT_C, OI["grey"]], "Mice by offspring genotype")
    ym = COMP["year"]["mice"]; yk = sorted(ym)
    _bar(axes[0, 1], yk, [ym[k] for k in yk], [OI["blue"]] * len(yk), "Mice by year")
    sm = COMP["strain"]["mice"]
    _bar(axes[0, 2], ["BALB/c\n(strain2)", "BALB/c+C57\n(strain1)"],
         [sm.get("BALB/C", 0), sm.get("BALB/C+BLACK/C57", 0)], [OI["purple"], OI["green"]], "Mice by strain")
    xm = COMP["sex"]["mice"]
    _bar(axes[1, 0], ["F", "M", "U"], [xm.get("F", 0), xm.get("M", 0), xm.get("U", 0)],
         [OI["orange"]] * 3, "Mice by sex")
    dm = COMP["day"]["mice"]; dk = sorted(dm, key=int)
    _bar(axes[1, 1], [f"P{k}" for k in dk], [dm[k] for k in dk], [OI["skyblue"]] * len(dk), "Mice by postnatal day")
    yr = COMP["year"]["rows"]
    _bar(axes[1, 2], yk, [yr[k] for k in yk], [OI["blue"]] * len(yk), "Syllables by year", ylab="syllables")
    fig.suptitle("Dataset composition (raw corpus: 126 mice, 35 dams, 125,576 syllables)", fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    S.save(fig, "F5", "Dataset composition (small multiples)",
           "Counts of mice and syllables across genotype, year, strain, sex, and postnatal day for the raw "
           "corpus. The cohort is WT-skewed (~3:1) and longitudinal (P4/P6 dominate).",
           ["thesis/data_composition.json", "outputs/external/input/segmentation_classification_all_data.csv"])


# ---------------- F6 class balance + syllables/mouse ----------------
def f6():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    lc = COMP["tabular_baseline"]["label_counts"]
    wt, ht = lc["WT"], lc["HT"]
    axes[0].pie([wt, ht], labels=[f"WT\n{wt}", f"HT\n{ht}"], colors=[S.WT_C, S.HT_C],
                autopct="%1.1f%%", startangle=90, wedgeprops=dict(width=0.42, edgecolor="white"),
                textprops=dict(fontsize=10))
    axes[0].set_title(f"Recording-level class balance\n(baseline: {wt+ht:,} recordings)")
    df = pd.read_csv(CSV, low_memory=False)
    spm = df.groupby("Name").size().values
    axes[1].hist(spm, bins=24, color=OI["blue"], edgecolor="black", lw=0.5)
    med = np.median(spm)
    axes[1].axvline(med, color=OI["vermillion"], lw=2, label=f"median = {med:.0f}")
    axes[1].set_xlabel("syllables per mouse"); axes[1].set_ylabel("number of mice")
    axes[1].set_title("Syllables per mouse (n = 126)"); axes[1].legend()
    fig.tight_layout()
    S.save(fig, "F6", "Class balance and syllables-per-subject",
           f"Left: recording-level class balance ({wt:,} WT / {ht:,} HT, ~3:1). Right: per-mouse syllable "
           f"counts (median {med:.0f}), showing the strongly longitudinal structure that motivates "
           f"subject-grouped evaluation.",
           ["thesis/data_composition.json", "outputs/external/input/segmentation_classification_all_data.csv"])


# ---------------- F7 syllable-type histogram ----------------
def f7():
    complexity = {
        "Complex": "Single vowel", "Upward": "Single vowel", "Flat": "Single vowel",
        "Downward": "Single vowel", "Chevron": "Single vowel", "Short": "Single vowel",
        "Frequency steps": "Multiple vowels", "Two syllables": "Multiple vowels",
        "Composite": "Advanced harmonic", "Harmonic": "Advanced harmonic",
        "Undefined": "Undefined",
    }
    cgrp_c = {"Single vowel": OI["blue"], "Multiple vowels": OI["green"],
              "Advanced harmonic": OI["orange"], "Undefined": OI["grey"]}
    st = COMP["syllable_type"]["rows"]
    items = sorted(st.items(), key=lambda kv: -kv[1])
    labels = [k for k, _ in items]; vals = [v for _, v in items]
    cols = [cgrp_c[complexity.get(k, "Undefined")] for k in labels]
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(range(len(labels)), vals, color=cols, edgecolor="black", lw=0.6)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=35, ha="right", fontsize=9.5)
    ax.set_ylabel("syllable count")
    for i, v in enumerate(vals):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=8.3)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c, ec="black") for c in cgrp_c.values()]
    ax.legend(handles, cgrp_c.keys(), title="complexity group", fontsize=9)
    ax.set_title("Syllable-type distribution (125,576 syllables, CNN typing)")
    ax.margins(y=0.12)
    fig.tight_layout()
    S.save(fig, "F7", "Syllable-type distribution",
           "Distribution of the 10 confidently-typed classes plus the post-hoc low-confidence 'Undefined' "
           "class, coloured by complexity group. 'Frequency steps' dominates; 'Undefined' (~10%) is dropped "
           "in the tabular track but retained in the sequence track.",
           ["thesis/data_composition.json", "docs/segmentation_process.md"])


# ---------------- F8 acoustic features by genotype ----------------
def f8():
    df = pd.read_csv(CSV, low_memory=False)
    df = df[df["Offspring Genotype"].isin(["WT", "HT"])]
    specs = [("Start Point (Hz)", "Start frequency (kHz)", 1e-3, (20, 125)),
             ("End Point (Hz)", "End frequency (kHz)", 1e-3, (20, 125)),
             ("Duration (time)", "Duration (ms)", 1e3, (0, 200)),
             ("ISI_time", "Inter-syllable interval (ms)", 1e3, (0, 600))]
    fig, axes = plt.subplots(1, 4, figsize=(13.5, 4.4))
    for ax, (col, lab, sc, clip) in zip(axes, specs):
        data = []
        for g in ("WT", "HT"):
            v = (df[df["Offspring Genotype"] == g][col].dropna() * sc)
            v = v[(v >= clip[0]) & (v <= clip[1])]
            data.append(v.values)
        bp = ax.boxplot(data, labels=["WT", "HT"], patch_artist=True, showfliers=False, widths=0.55)
        for patch, c in zip(bp["boxes"], [S.WT_C, S.HT_C]):
            patch.set_facecolor(c); patch.set_alpha(0.75)
        for med in bp["medians"]:
            med.set_color("black"); med.set_linewidth(1.6)
        ax.set_ylabel(lab); ax.set_title(col.replace(" (time)", "").replace(" Point", ""))
    fig.suptitle("Acoustic-feature distributions by genotype (syllable level)", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F8", "Acoustic-feature distributions by genotype",
           "Per-syllable start/end frequency, duration and inter-syllable interval for WT vs HT (outliers "
           "hidden, display-clipped). These are the spectral/temporal features Shekel et al. (2021) reported "
           "as most ASD-sensitive.",
           ["outputs/external/input/segmentation_classification_all_data.csv",
            "hit/research/Shekel et al_2021 (3).pdf"])


# ---------------- F9 master performance dumbbell ----------------
def f9():
    models = [("xgboost", "XGBoost (inherited)"), ("xgboost_tuned", "XGBoost-tuned"), ("tabpfn", "TabPFN")]
    metrics = [("test_acc", "Test accuracy"), ("weighted_f1", "Weighted F1"), ("auc", "ROC-AUC")]
    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.4))
    for ax, (mk, mlab) in zip(axes, metrics):
        for i, (mod, lab) in enumerate(models):
            dep = mr("tabular", "pooled", "dependent", mod)[0]
            ind = mr("tabular", "pooled", "independent", mod)[0]
            dv, iv = float(dep[mk]), float(ind[mk])
            ax.plot([dv, iv], [i, i], color=OI["grey"], lw=2, zorder=1)
            ax.scatter([dv], [i], color=S.DEP_C, s=90, zorder=2, label="dependent" if i == 0 else "")
            ax.scatter([iv], [i], color=S.INDEP_C, s=90, zorder=2, label="independent" if i == 0 else "")
            ax.text(dv, i + 0.18, f"{dv:.3f}", ha="center", fontsize=8, color=S.DEP_C)
            ax.text(iv, i - 0.28, f"{iv:.3f}", ha="center", fontsize=8, color=S.INDEP_C)
        ax.set_yticks(range(len(models))); ax.set_yticklabels([l for _, l in models], fontsize=9.5)
        ax.set_title(mlab); ax.set_xlim(0.6, 0.95); ax.invert_yaxis()
    axes[0].legend(loc="center left", fontsize=9)
    fig.suptitle("Tabular model performance — subject-dependent vs subject-independent (pooled, recording level)",
                 fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F9", "Master performance — dependent vs independent",
           "Headline comparison of the three tabular models on the pooled baseline. Each dumbbell links the "
           "optimistic subject-dependent score (light) to the honest subject-independent score (dark). TabPFN "
           "is best on both; the dependent→independent drop is the cost of generalizing to unseen mice.",
           ["thesis/master_results.json"])


# ---------------- F10 generalization gap (HT recall/precision) ----------------
def f10():
    models = [("xgboost", "XGBoost"), ("xgboost_tuned", "XGBoost-tuned"), ("tabpfn", "TabPFN")]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6))
    for ax, (mk, title) in zip(axes, [("ht_recall", "HT recall (catching ASD-model pups)"),
                                       ("ht_precision", "HT precision (false-alarm control)")]):
        for mod, lab in models:
            dep = float(mr("tabular", "pooled", "dependent", mod)[0][mk])
            ind = float(mr("tabular", "pooled", "independent", mod)[0][mk])
            ax.plot([0, 1], [dep, ind], "-o", color=S.MODEL_C[mod], lw=2, ms=7, label=lab)
            ax.text(-0.04, dep, f"{dep:.2f}", ha="right", va="center", fontsize=8.5, color=S.MODEL_C[mod])
            ax.text(1.04, ind, f"{ind:.2f}", ha="left", va="center", fontsize=8.5, color=S.MODEL_C[mod])
        ax.set_xticks([0, 1]); ax.set_xticklabels(["subject-\ndependent", "subject-\nindependent"])
        ax.set_xlim(-0.35, 1.35); ax.set_ylim(0.3, 1.0); ax.set_title(title)
    axes[1].axhspan(0.45, 0.55, color=OI["grey"], alpha=0.18)
    axes[1].text(0.5, 0.5, "~0.50 precision wall", ha="center", fontsize=8.5, style="italic")
    axes[0].legend(fontsize=9, loc="lower left")
    fig.suptitle("Generalization gap — minority-class behaviour, dependent → independent", fontsize=12, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F10", "Generalization gap (HT recall & precision)",
           "Slope chart of HT recall and HT precision as evaluation moves from subject-dependent to "
           "subject-independent. HT precision stays pinned near 0.50 for every model — a property of the "
           "features, not the estimator.",
           ["thesis/master_results.json"])


# ---------------- ROC/PR/confusion helpers ----------------
PROB_RUNS = {
    "dependent": [("xgboost", "xgboost_subject_eval_dependent_baseline", "XGBoost"),
                  ("xgboost_tuned", "xgboost_tuned_dependent_subject_eval_dependent_baseline", "XGBoost-tuned"),
                  ("tabpfn", "tabpfn_subject_eval_dependent_baseline", "TabPFN")],
    "independent": [("xgboost", "xgboost_subject_eval_independent_baseline", "XGBoost"),
                    ("xgboost_tuned", "xgboost_tuned_independent_subject_eval_independent_baseline", "XGBoost-tuned"),
                    ("tabpfn", "tabpfn_subject_eval_independent_baseline", "TabPFN")],
}


def _probs(dirname):
    p = THR / dirname / "probabilities_test.csv"
    d = pd.read_csv(p)
    return d["y_true"].values, d["p_ht"].values, str(p.relative_to(REPO))


def f11_roc():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    srcs = []
    for ax, split in zip(axes, ["dependent", "independent"]):
        for mod, dirn, lab in PROB_RUNS[split]:
            y, p, sp = _probs(dirn); srcs.append(sp)
            fpr, tpr, _ = roc_curve(y, p)
            ax.plot(fpr, tpr, color=S.MODEL_C[mod], lw=2, label=f"{lab} (AUC {auc(fpr, tpr):.3f})")
        ax.plot([0, 1], [0, 1], "--", color=OI["grey"], lw=1)
        ax.set_xlabel("False positive rate"); ax.set_ylabel("True positive rate")
        ax.set_title(f"ROC — subject-{split}"); ax.legend(fontsize=9, loc="lower right")
    fig.suptitle("ROC curves — headline tabular models", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F11", "ROC curves (headline tabular models)",
           "ROC for XGBoost, XGBoost-tuned and TabPFN, recomputed from held-out test probabilities. AUC "
           "drops markedly from the dependent to the independent split, quantifying the leakage in the "
           "optimistic regime.", sorted(set(srcs)))


def f12_pr():
    fig, axes = plt.subplots(1, 2, figsize=(11, 5))
    srcs = []
    for ax, split in zip(axes, ["dependent", "independent"]):
        base = None
        for mod, dirn, lab in PROB_RUNS[split]:
            y, p, sp = _probs(dirn); srcs.append(sp)
            prec, rec, _ = precision_recall_curve(y, p)
            ax.plot(rec, prec, color=S.MODEL_C[mod], lw=2, label=f"{lab} (AP {average_precision_score(y, p):.3f})")
            base = y.mean()
        ax.axhline(base, ls="--", color=OI["grey"], lw=1, label=f"HT prevalence {base:.2f}")
        ax.set_xlabel("Recall (HT)"); ax.set_ylabel("Precision (HT)")
        ax.set_title(f"Precision–Recall — subject-{split}"); ax.legend(fontsize=8.5, loc="upper right")
        ax.set_ylim(0, 1.02)
    fig.suptitle("Precision–Recall curves (minority HT class)", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F12", "Precision–Recall curves (HT class)",
           "Precision–recall for the HT (ASD-model) minority class. The dashed line is HT prevalence "
           "(no-skill). Precision degrades sharply at high recall on the independent split.", sorted(set(srcs)))


def f13_confusion():
    panels = [("dependent", "tabpfn_subject_eval_dependent_baseline", "TabPFN · dependent"),
              ("independent", "tabpfn_subject_eval_independent_baseline", "TabPFN · independent"),
              ("dependent", "xgboost_subject_eval_dependent_baseline", "XGBoost · dependent")]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    srcs = []
    for ax, (split, dirn, title) in zip(axes, panels):
        y, p, sp = _probs(dirn); srcs.append(sp)
        cm = confusion_matrix(y, (p >= 0.5).astype(int))
        im = ax.imshow(cm, cmap="Blues")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, f"{cm[i, j]:,}", ha="center", va="center",
                        color="white" if cm[i, j] > cm.max() / 2 else "black", fontsize=12, fontweight="bold")
        ax.set_xticks([0, 1]); ax.set_xticklabels(["pred WT", "pred HT"])
        ax.set_yticks([0, 1]); ax.set_yticklabels(["true WT", "true HT"])
        ax.set_title(title, fontsize=10.5); ax.grid(False)
    fig.suptitle("Confusion matrices at the default 0.5 threshold", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F13", "Confusion matrices (headline models)",
           "Test-set confusion matrices at threshold 0.5. The dominant error in every panel is WT recordings "
           "predicted HT (false positives), consistent with the ~0.50 HT-precision ceiling.", sorted(set(srcs)))


# ---------------- F14 feature importance ----------------
def f14():
    names = ['syll1_s_freq','syll2_s_freq','syll3_s_freq','syll4_s_freq','syll5_s_freq','syll6_s_freq','syll7_s_freq','syll8_s_freq','syll9_s_freq','syll10_s_freq','syll1_e_freq','syll2_e_freq','syll3_e_freq','syll4_e_freq','syll5_e_freq','syll6_e_freq','syll7_e_freq','syll8_e_freq','syll9_e_freq','syll10_e_freq','syll1_dist','syll2_dist','syll3_dist','syll4_dist','syll5_dist','syll6_dist','syll7_dist','syll8_dist','syll9_dist','syll10_dist','syll1_dur','syll2_dur','syll3_dur','syll4_dur','syll5_dur','syll6_dur','syll7_dur','syll8_dur','syll9_dur','syll10_dur','mother_gen','pup_sex','avg_ISI_time','pup_age','session','pup_strain']
    pretty = {"mother_gen": "Mother genotype", "pup_sex": "Sex", "avg_ISI_time": "Avg ISI",
              "pup_age": "Age (postnatal day)", "session": "Session", "pup_strain": "Strain"}
    paths = {"dependent": "results/tabular_models/xgboost_subject_eval_dependent_baseline/model/xgboost_model.pkl",
             "independent": "results/tabular_models/xgboost_subject_eval_independent_baseline/model/xgboost_model.pkl"}
    imps, srcs = [], []
    for split, rp in paths.items():
        m = pickle.load(open(REPO / rp, "rb")); imps.append(m.feature_importances_); srcs.append(rp)
    avg = np.mean(imps, axis=0)
    order = np.argsort(avg)[::-1][:15][::-1]
    labels = [pretty.get(names[i], names[i]) for i in order]
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(range(len(order)), avg[order], color=OI["blue"], edgecolor="black", lw=0.5)
    ax.set_yticks(range(len(order))); ax.set_yticklabels(labels, fontsize=9.5)
    ax.set_xlabel("mean XGBoost gain importance (averaged over dependent & independent)")
    ax.set_title("Top-15 features driving WT-vs-HT classification")
    fig.tight_layout()
    S.save(fig, "F14", "Feature importance (XGBoost)",
           "Top-15 features by XGBoost gain importance, averaged across the dependent and independent models. "
           "Per-syllable-type start/end frequencies and durations dominate — consistent with Shekel et al. "
           "(2021); note the syllN columns map type N→slot via a documented off-by-one.", srcs)


# ---------------- F15 per-strain heatmap ----------------
def f15():
    def get(scope, split, mk):
        rows = mr("tabular", scope, split, "xgboost")
        return float(rows[0][mk]) if rows and rows[0][mk] != "" else np.nan
    metrics = [("test_acc", "Accuracy"), ("ht_f1", "HT F1"), ("ht_recall", "HT recall"), ("ht_precision", "HT prec.")]
    strains = ["strain1", "strain2"]
    splits = ["dependent", "independent"]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2))
    for ax, split in zip(axes, splits):
        grid = np.array([[get(s, split, mk) for mk, _ in metrics] for s in strains])
        im = ax.imshow(grid, cmap="RdYlGn", vmin=0.1, vmax=0.95, aspect="auto")
        ax.set_xticks(range(len(metrics))); ax.set_xticklabels([l for _, l in metrics], fontsize=9)
        ax.set_yticks(range(2)); ax.set_yticklabels(["strain1\n(2022-24)", "strain2\n(2015/18)"], fontsize=9.5)
        for i in range(2):
            for j in range(len(metrics)):
                ax.text(j, i, f"{grid[i, j]:.2f}", ha="center", va="center", fontsize=10, fontweight="bold")
        ax.set_title(f"XGBoost · subject-{split}"); ax.grid(False)
    fig.suptitle("Per-strain results — strong strain1 vs collapsing strain2", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F15", "Per-strain comparison",
           "XGBoost per-strain results. strain1 (recent mixed-background cohort) is highly separable even "
           "leak-free (acc 0.90), whereas strain2 (small pure-BALB/c cohort) collapses on the minority class "
           "under the independent split — evidence that strain/cohort confounds genotype.",
           ["thesis/master_results.json"])


# ---------------- F16 HT-precision wall ----------------
def f16():
    rows = [r for r in MR if r["family"] == "tabular" and r["ht_precision"] != ""]
    labels, vals, cols = [], [], []
    for r in sorted(rows, key=lambda r: float(r["ht_precision"])):
        labels.append(f"{r['model']} · {r['scope']} · {r['split'][:3]}")
        vals.append(float(r["ht_precision"])); cols.append(S.MODEL_C.get(r["model"], OI["grey"]))
    fig, ax = plt.subplots(figsize=(9, 6.5))
    ax.hlines(range(len(vals)), 0, vals, color=OI["grey"], lw=1.4)
    ax.plot(vals, range(len(vals)), "o", ms=8)
    for i, (v, c) in enumerate(zip(vals, cols)):
        ax.plot(v, i, "o", ms=9, color=c)
    ax.axvspan(0.45, 0.55, color=OI["grey"], alpha=0.18)
    ax.axvline(0.5, color=OI["vermillion"], ls="--", lw=1.3)
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels, fontsize=8.5)
    ax.set_xlabel("HT precision (at threshold 0.5)"); ax.set_xlim(0.3, 0.75)
    ax.set_title("The HT-precision wall (~0.50) across tabular configurations")
    fig.tight_layout()
    S.save(fig, "F16", "HT-precision wall",
           "HT precision at the default threshold across every tabular configuration clusters near 0.50 "
           "(only the easier strain1 cohort escapes). About half of all positive calls are false alarms — a "
           "ceiling set by the features.", ["thesis/master_results.json"])


# ---------------- F17 threshold objectives ----------------
def f17():
    df = pd.read_csv(REPO / "results/tabular_models/threshold_objectives/summary_objectives.csv")
    df["run"] = df["run"].str.strip()
    runs = [("tabpfn / dependent", "TabPFN · dependent"), ("tabpfn / independent", "TabPFN · independent")]
    objs = ["@0.5", "youden", "f1", "target_recall", "balanced"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.8))
    for ax, (run, title) in zip(axes, runs):
        sub = df[df["run"] == run].set_index("objective")
        x = range(len(objs))
        for mk, c, lab in [("balanced_accuracy", OI["black"], "balanced acc"),
                           ("ht_recall", S.HT_C, "HT recall"), ("ht_precision", OI["green"], "HT precision")]:
            ax.plot(x, [sub.loc[o, mk] for o in objs], "-o", color=c, lw=2, label=lab)
        ax.set_xticks(list(x)); ax.set_xticklabels(objs, rotation=20, fontsize=9)
        ax.set_title(title); ax.set_ylim(0.4, 1.02)
    axes[0].legend(fontsize=9, loc="lower left")
    fig.suptitle("Decision-threshold objectives — moving the operating point (TabPFN)", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F17", "Threshold-objective operating points",
           "Effect of the threshold objective on TabPFN. On the dependent split, f1/target_recall lift HT "
           "precision to ~0.62 while holding recall ~0.81; on the independent split, Youden/balanced "
           "degenerate (recall→1, precision pinned ~0.48), so target_recall is the only sensible objective.",
           ["results/tabular_models/threshold_objectives/summary_objectives.csv"])


# ---------------- F18 sequence collapse + CV deflation ----------------
def f18():
    exp = pd.read_csv(REPO / "results/neural_networks/experiments/_summary/master_metrics.csv")
    levers = ["A_control", "B_beta0.5", "C_beta0", "D_sampler", "E_focal", "F_regsmall", "G_augment", "H_cv_Dsampler"]
    cols = [("bilstm", "dependent"), ("bilstm", "independent"), ("cnn1d", "dependent"),
            ("cnn1d", "independent"), ("transformer", "dependent"), ("transformer", "independent")]
    grid = np.full((len(levers), len(cols)), np.nan)
    for i, lev in enumerate(levers):
        for j, (mdl, sp) in enumerate(cols):
            row = exp[(exp["label"] == f"{lev}__{mdl}__{sp}")]
            if len(row):
                grid[i, j] = float(row["test_balanced_accuracy"].values[0])
    fig, axes = plt.subplots(1, 2, figsize=(13, 5), gridspec_kw={"width_ratios": [1.55, 1]})
    ax = axes[0]
    im = ax.imshow(np.ma.masked_invalid(grid), cmap="RdYlGn", vmin=0.45, vmax=0.72, aspect="auto")
    ax.set_xticks(range(len(cols)))
    ax.set_xticklabels([f"{m}\n{s[:3]}" for m, s in cols], fontsize=8.5)
    ax.set_yticks(range(len(levers))); ax.set_yticklabels(levers, fontsize=9)
    for i in range(len(levers)):
        for j in range(len(cols)):
            if not np.isnan(grid[i, j]):
                ax.text(j, i, f"{grid[i, j]:.2f}", ha="center", va="center", fontsize=8)
    ax.set_title("A–H lever sweep · balanced accuracy"); ax.grid(False)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04, label="balanced acc")
    # CV deflation
    ax2 = axes[1]
    dep_single = float(mr("sequence", "D_sampler", "dependent", "bilstm")[0]["balanced_acc"])
    ind_single = float(mr("sequence", "D_sampler", "independent", "bilstm")[0]["balanced_acc"])
    cv = {"dependent": (0.6095, 0.0550), "independent": (0.5627, 0.0632)}
    x = [0, 1, 3, 4]
    vals = [dep_single, cv["dependent"][0], ind_single, cv["independent"][0]]
    errs = [0, cv["dependent"][1], 0, cv["independent"][1]]
    colors = [S.DEP_C, S.DEP_C, S.INDEP_C, S.INDEP_C]
    ax2.bar(x, vals, yerr=errs, color=colors, edgecolor="black", lw=0.7, capsize=5, width=0.8)
    for xi, v in zip(x, vals):
        ax2.text(xi, v + 0.01, f"{v:.3f}", ha="center", fontsize=9, fontweight="bold")
    ax2.set_xticks(x)
    ax2.set_xticklabels(["dep\nsingle", "dep\n5-fold", "indep\nsingle", "indep\n5-fold"], fontsize=9)
    ax2.axhline(0.5, color=OI["grey"], ls="--", lw=1)
    ax2.set_ylim(0.45, 0.78); ax2.set_ylabel("balanced accuracy")
    ax2.set_title("BiLSTM (balanced sampler):\nsingle-split vs 5-fold CV")
    fig.suptitle("Sequence models — imbalance levers and cross-validation deflation", fontsize=12.5, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    S.save(fig, "F18", "Sequence-model lever sweep and CV deflation",
           "Left: balanced accuracy across the A–H imbalance-handling levers (E run only for BiLSTM). Right: "
           "the lucky single-split BiLSTM independent score (0.704) deflates to 0.563 ± 0.063 under 5-fold "
           "grouped CV — the honest sequence-model signal is weak and data-limited.",
           ["results/neural_networks/experiments/_summary/master_metrics.csv",
            "results/neural_networks/experiments/H_cv_Dsampler__bilstm__independent/results.json",
            "results/neural_networks/experiments/H_cv_Dsampler__bilstm__dependent/results.json"])


# ---------------- F19 annotated segmentation example ----------------
import os, re, glob
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


def f19():
    import librosa
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
        raise RuntimeError("no recording resolved for F19")
    syl = df[(df["Path"] == chosen["Path"]) & (df["Name"] == chosen["Name"])]
    y, sr = librosa.load(wav, sr=None)
    n_fft = 2048
    D = librosa.amplitude_to_db(np.abs(librosa.stft(y, n_fft=n_fft, hop_length=256)), ref=np.max)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft) / 1000.0
    times = librosa.frames_to_time(np.arange(D.shape[1]), sr=sr, hop_length=256)
    m = freqs <= 125
    fig, ax = plt.subplots(figsize=(12, 4.8))
    ax.pcolormesh(times, freqs[m], D[m, :], cmap="magma", shading="auto", vmin=-65, vmax=0,
                  rasterized=True)
    from matplotlib.patches import Rectangle
    for _, s in syl.iterrows():
        t0, t1 = s["Start point(s)"], s["End point(s)"]
        f0, f1 = s["Start Point (Hz)"] / 1000, s["End Point (Hz)"] / 1000
        lo, hi = min(f0, f1), max(f0, f1)
        ax.add_patch(Rectangle((t0, lo - 4), t1 - t0, (hi - lo) + 8, fill=False,
                               edgecolor=OI["skyblue"], lw=1.3))
    ax.set_ylabel("Frequency (kHz)"); ax.set_xlabel("Time (s)"); ax.set_ylim(0, 125)
    ax.set_xlim(times[0], times[-1])
    ax.set_title(f"Detected USV syllables overlaid on the spectrogram ({len(syl)} syllables, 250 kHz)")
    ax.grid(False)
    rel = os.path.relpath(wav, REPO)
    S.save(fig, "F19", "Annotated segmentation example",
           f"Spectrogram of a representative pup recording with the {len(syl)} automatically detected "
           f"syllables overlaid (blue boxes span each call's time extent and start/end-frequency band). "
           f"Source: {rel}.",
           [str(CSV.relative_to(REPO)), "docs/segmentation_process.md"])


# ---------------- F20 Gantt (interim plan) ----------------
def f20():
    phases = [
        ("Initiation & topic approval", 0, 1), ("Literature & environment setup", 1, 2),
        ("Full proposal (seminar)", 2, 1), ("Pipeline reconstruction & refactor", 3, 2),
        ("Data exploration & verification", 4, 2), ("Single source of truth & docs", 5, 2),
        ("Segmentation GUI to researcher", 7, 2), ("Project consolidation", 8, 1),
        ("Full end-to-end model runs", 8, 2), ("Final conclusions", 10, 1),
        ("Thesis & final presentation", 10, 2),
    ]
    fig, ax = plt.subplots(figsize=(11, 5))
    for i, (lab, start, dur) in enumerate(phases):
        ax.barh(i, dur, left=start, color=OI["blue"], edgecolor="black", lw=0.6, alpha=0.85)
    ax.axvline(2, color=OI["vermillion"], ls="--", lw=1.5)
    ax.text(2.1, len(phases) - 0.5, "interim report", color=OI["vermillion"], fontsize=9)
    ax.set_yticks(range(len(phases))); ax.set_yticklabels([p[0] for p in phases], fontsize=9)
    ax.invert_yaxis(); ax.set_xlabel("project month"); ax.set_xlim(0, 12)
    ax.set_title("Project plan (redrawn from the interim report)")
    fig.tight_layout()
    S.save(fig, "F20", "Project timeline / Gantt (interim plan)",
           "Planned project schedule redrawn from the interim report's work plan; the dashed line marks the "
           "interim-report milestone.", ["hit/project/Project+Midterm+-+Chen+Aharon+%26+Aviel+Bitton.pdf"])


# ---------------- F21 git work timeline ----------------
def f21():
    miles = [
        ("2023-05", "Inherited prototype\n(single XGBoost)"), ("2025-11", "Authors take over"),
        ("2026-03", "Whole-pipeline\nrefactor (src/)"), ("2026-04", "Subject-independent\nsplit → leakage found"),
        ("2026-04", "Genotype fix\n14 mice / 2,495 rows"), ("2026-04", "TabPFN added"),
        ("2026-05", "Sequence models\n(BiLSTM/CNN/Transf.)"), ("2026-05", "Per-strain analysis"),
        ("2026-06", "Threshold tuning"), ("2026-06", "Thesis preparation"),
    ]
    fig, ax = plt.subplots(figsize=(12.5, 4.2))
    xs = list(range(len(miles)))
    ax.plot(xs, [0] * len(xs), "-", color=OI["grey"], lw=2, zorder=1)
    for i, (date, lab) in enumerate(miles):
        up = i % 2 == 0
        y = 1 if up else -1
        ax.plot(i, 0, "o", ms=11, color=OI["blue"] if i > 0 else OI["vermillion"], zorder=2)
        ax.annotate(f"{lab}", (i, 0), (i, y), ha="center", va="bottom" if up else "top",
                    fontsize=8.2, arrowprops=dict(arrowstyle="-", color=OI["grey"], lw=0.8))
        ax.text(i, y + (0.55 if up else -0.55), date, ha="center", fontsize=8, fontweight="bold",
                va="bottom" if up else "top", color=OI["black"])
    ax.set_ylim(-2.6, 2.6); ax.set_xlim(-0.6, len(miles) - 0.4); ax.axis("off")
    ax.set_title("Project work timeline (reconstructed from the commit history)", fontweight="bold")
    fig.tight_layout()
    S.save(fig, "F21", "Commit-derived work timeline",
           "Milestones reconstructed from the local git history (chronology only — no metrics). From the "
           "inherited single-model prototype to the final multi-model, leak-free pipeline.",
           ["local git log (chronology only)"])


def main():
    S.apply_style()
    figs = [f5, f6, f7, f8, f9, f10, f11_roc, f12_pr, f13_confusion, f14, f15, f16, f17, f18, f19, f20, f21]
    for fn in figs:
        try:
            fn()
        except Exception as e:
            print(f"  !! {fn.__name__} FAILED: {e}")
            traceback.print_exc()


if __name__ == "__main__":
    main()
