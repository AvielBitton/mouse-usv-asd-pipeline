"""Sequence modeling pipeline for USV recording classification.

Trains BiLSTM, 1D-CNN, or Transformer models on ordered syllable sequences
grouped at the mouse-day-session level to classify WT vs HT genotype.
"""

import argparse
import json
import math
import os
import pickle
import random
import sys
import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import torch
import torch.nn as nn
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    roc_auc_score,
    roc_curve,
)
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from torch.utils.data import DataLoader, Dataset

warnings.filterwarnings("ignore", category=FutureWarning)

DATA_PATH = os.path.join(
    "outputs", "external", "segmentation_classification_all_data.xlsx"
)

CONTINUOUS_FEATURES = [
    "Start Point (Hz)",
    "End Point (Hz)",
    "Duration (time)",
    "ISI_time",
]
NUM_SYLLABLE_TYPES = 11
SYLLABLE_EMBED_DIM = 8

SEED = 100


def set_seed(seed: int):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def _load_dataframe(data_path: str):
    """Load data from CSV cache if available, otherwise from Excel."""
    csv_path = data_path.replace(".xlsx", ".csv")
    if os.path.exists(csv_path):
        print(f"Loading from CSV cache: {csv_path}")
        return pd.read_csv(csv_path)
    print(f"Loading from Excel (slow): {data_path}")
    df = pd.read_excel(data_path, engine="openpyxl")
    df.to_csv(csv_path, index=False)
    print(f"Cached as CSV: {csv_path}")
    return df


def load_and_prepare(data_path: str, max_seq_len: int):
    """Load, clean, group by mouse-day-session, and return sequences."""
    df = _load_dataframe(data_path)

    df = df[df["Offspring Genotype"].isin(["WT", "HT"])].copy()

    df["Duration (time)"] = df["Duration (time)"].clip(upper=1.0)
    df["ISI_time"] = df["ISI_time"].clip(lower=0.0, upper=10.0)
    df["ISI_time"] = df["ISI_time"].fillna(0.0)

    df["recording_boundary"] = (
        df["Syllable order (in recording)"] == 1
    ).astype(int)

    df["Sex_enc"] = (df["Sex"] == "M").astype(float)

    df = df.sort_values(["Name", "Day", "Session", "Path",
                         "Syllable order (in recording)"])

    group_key = df["Name"] + "_d" + df["Day"].astype(str) + "_s" + df["Session"].astype(str)
    df["group_key"] = group_key

    sequences = []
    for gk, grp in df.groupby("group_key", sort=False):
        cont = grp[CONTINUOUS_FEATURES].values.astype(np.float32)
        syl_type = grp["Syllable number"].values.astype(np.int64)
        noise = grp["Noise"].values.astype(np.float32)
        rec_bound = grp["recording_boundary"].values.astype(np.float32)

        meta = np.array([
            grp["Mother Genotype (binary)"].iloc[0],
            grp["Sex_enc"].iloc[0],
            grp["Day"].iloc[0],
            grp["Session"].iloc[0],
        ], dtype=np.float32)

        label = float(grp["Offspring Genotype (binary)"].iloc[0])
        mouse_name = grp["Name"].iloc[0]

        sequences.append({
            "continuous": cont,
            "syllable_type": syl_type,
            "noise": noise,
            "rec_boundary": rec_bound,
            "metadata": meta,
            "label": label,
            "mouse": mouse_name,
            "group_key": gk,
            "length": len(grp),
        })

    lengths = [s["length"] for s in sequences]
    print(f"Loaded {len(sequences)} sessions from {df['Name'].nunique()} mice")
    print(f"Sequence lengths: min={min(lengths)}, median={np.median(lengths):.0f}, "
          f"max={max(lengths)}, P95={np.percentile(lengths, 95):.0f}")
    print(f"MAX_SEQ_LEN={max_seq_len}")
    print(f"Labels: WT={sum(1 for s in sequences if s['label']==1.0)}, "
          f"HT={sum(1 for s in sequences if s['label']==0.0)}")

    return sequences


# ---------------------------------------------------------------------------
# Splitting
# ---------------------------------------------------------------------------

def random_split_sequences(sequences, seed):
    """Random session-level split (60/20/20)."""
    indices = list(range(len(sequences)))
    labels = [s["label"] for s in sequences]

    idx_trainval, idx_test = train_test_split(
        indices, test_size=0.2, random_state=seed, stratify=labels,
    )
    labels_trainval = [labels[i] for i in idx_trainval]
    idx_train, idx_val = train_test_split(
        idx_trainval, test_size=0.25, random_state=seed, stratify=labels_trainval,
    )
    return (
        [sequences[i] for i in idx_train],
        [sequences[i] for i in idx_val],
        [sequences[i] for i in idx_test],
    )


def group_split_sequences(sequences, seed):
    """Split by mouse identity (60/20/20), no leakage."""
    mouse_labels = {}
    for s in sequences:
        if s["mouse"] not in mouse_labels:
            mouse_labels[s["mouse"]] = s["label"]

    mice = list(mouse_labels.keys())
    labels = [mouse_labels[m] for m in mice]

    mice_trainval, mice_test = train_test_split(
        mice, test_size=0.2, random_state=seed, stratify=labels,
    )
    labels_trainval = [mouse_labels[m] for m in mice_trainval]
    mice_train, mice_val = train_test_split(
        mice_trainval, test_size=0.25, random_state=seed, stratify=labels_trainval,
    )

    train_set = set(mice_train)
    val_set = set(mice_val)
    test_set = set(mice_test)
    assert train_set.isdisjoint(val_set), "Leakage: train/val mice overlap"
    assert train_set.isdisjoint(test_set), "Leakage: train/test mice overlap"
    assert val_set.isdisjoint(test_set), "Leakage: val/test mice overlap"

    train = [s for s in sequences if s["mouse"] in train_set]
    val = [s for s in sequences if s["mouse"] in val_set]
    test = [s for s in sequences if s["mouse"] in test_set]
    return train, val, test


def log_split_info(train, val, test, is_group_split):
    strategy = "group-aware (by mouse)" if is_group_split else "random (session-level)"
    print(f"\n=== Split Info ===")
    print(f"Strategy: {strategy}")
    print(f"Train: {len(train)} sessions | Val: {len(val)} sessions | Test: {len(test)} sessions")

    for name, subset in [("Train", train), ("Val", val), ("Test", test)]:
        mice = set(s["mouse"] for s in subset)
        n_wt = sum(1 for s in subset if s["label"] == 1.0)
        n_ht = sum(1 for s in subset if s["label"] == 0.0)
        total = len(subset)
        print(f"  {name}: {len(mice)} mice, WT={n_wt} ({100*n_wt/total:.0f}%), "
              f"HT={n_ht} ({100*n_ht/total:.0f}%)")

    if not is_group_split:
        train_mice = set(s["mouse"] for s in train)
        val_mice = set(s["mouse"] for s in val)
        test_mice = set(s["mouse"] for s in test)
        overlap_tv = len(train_mice & val_mice)
        overlap_tt = len(train_mice & test_mice)
        if overlap_tv or overlap_tt:
            print(f"  WARNING: mouse overlap -- train/val: {overlap_tv}, "
                  f"train/test: {overlap_tt} shared mice")
    print("==================\n")


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------

class USVSequenceDataset(Dataset):
    def __init__(self, sequences, max_seq_len, scaler=None, fit_scaler=False):
        self.max_seq_len = max_seq_len
        self.data = []

        all_cont = np.concatenate([s["continuous"] for s in sequences], axis=0)
        if fit_scaler:
            self.scaler = StandardScaler().fit(all_cont)
        else:
            self.scaler = scaler

        for s in sequences:
            length = min(s["length"], max_seq_len)
            cont = self.scaler.transform(s["continuous"][:length])
            syl = s["syllable_type"][:length]
            noise = s["noise"][:length]
            rec_b = s["rec_boundary"][:length]

            cont_pad = np.zeros((max_seq_len, cont.shape[1]), dtype=np.float32)
            cont_pad[:length] = cont
            syl_pad = np.zeros(max_seq_len, dtype=np.int64)
            syl_pad[:length] = syl
            noise_pad = np.zeros(max_seq_len, dtype=np.float32)
            noise_pad[:length] = noise
            recb_pad = np.zeros(max_seq_len, dtype=np.float32)
            recb_pad[:length] = rec_b

            self.data.append({
                "continuous": torch.tensor(cont_pad),
                "syllable_type": torch.tensor(syl_pad),
                "noise": torch.tensor(noise_pad),
                "rec_boundary": torch.tensor(recb_pad),
                "metadata": torch.tensor(s["metadata"]),
                "label": torch.tensor(s["label"]),
                "length": length,
            })

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def collate_fn(batch):
    return {
        "continuous": torch.stack([b["continuous"] for b in batch]),
        "syllable_type": torch.stack([b["syllable_type"] for b in batch]),
        "noise": torch.stack([b["noise"] for b in batch]),
        "rec_boundary": torch.stack([b["rec_boundary"] for b in batch]),
        "metadata": torch.stack([b["metadata"] for b in batch]),
        "label": torch.stack([b["label"] for b in batch]),
        "length": torch.tensor([b["length"] for b in batch]),
    }


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------

class BiLSTMClassifier(nn.Module):
    def __init__(self, num_cont, meta_dim, hidden_size=64, num_layers=2,
                 dropout=0.3):
        super().__init__()
        self.syl_embed = nn.Embedding(NUM_SYLLABLE_TYPES, SYLLABLE_EMBED_DIM)
        input_dim = num_cont + SYLLABLE_EMBED_DIM + 2  # +noise +rec_boundary
        self.lstm = nn.LSTM(
            input_dim, hidden_size, num_layers=num_layers,
            batch_first=True, bidirectional=True, dropout=dropout if num_layers > 1 else 0,
        )
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size * 2 + meta_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, cont, syl_type, noise, rec_boundary, metadata, lengths):
        emb = self.syl_embed(syl_type)
        x = torch.cat([cont, emb, noise.unsqueeze(-1), rec_boundary.unsqueeze(-1)], dim=-1)

        packed = nn.utils.rnn.pack_padded_sequence(
            x, lengths.cpu().clamp(min=1), batch_first=True, enforce_sorted=False,
        )
        _, (h_n, _) = self.lstm(packed)
        fwd = h_n[-2]
        bwd = h_n[-1]
        hidden = torch.cat([fwd, bwd], dim=-1)

        combined = torch.cat([hidden, metadata], dim=-1)
        return self.classifier(combined).squeeze(-1)


class CNN1DClassifier(nn.Module):
    def __init__(self, num_cont, meta_dim, dropout=0.3):
        super().__init__()
        self.syl_embed = nn.Embedding(NUM_SYLLABLE_TYPES, SYLLABLE_EMBED_DIM)
        input_dim = num_cont + SYLLABLE_EMBED_DIM + 2

        self.conv = nn.Sequential(
            nn.Conv1d(input_dim, 64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.Conv1d(64, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
            nn.Conv1d(128, 128, kernel_size=3, padding=1),
            nn.BatchNorm1d(128),
            nn.ReLU(),
        )
        self.classifier = nn.Sequential(
            nn.Linear(128 + meta_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, cont, syl_type, noise, rec_boundary, metadata, lengths):
        emb = self.syl_embed(syl_type)
        x = torch.cat([cont, emb, noise.unsqueeze(-1), rec_boundary.unsqueeze(-1)], dim=-1)

        x = x.transpose(1, 2)  # (batch, channels, seq_len)
        x = self.conv(x)
        x = x.transpose(1, 2)  # (batch, seq_len, channels)

        mask = torch.arange(x.size(1), device=x.device).unsqueeze(0) < lengths.unsqueeze(1)
        x = x * mask.unsqueeze(-1).float()
        pooled = x.sum(dim=1) / lengths.unsqueeze(-1).float().clamp(min=1)

        combined = torch.cat([pooled, metadata], dim=-1)
        return self.classifier(combined).squeeze(-1)


class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=1024, dropout=0.1):
        super().__init__()
        self.dropout = nn.Dropout(dropout)
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        if d_model % 2 == 1:
            pe[:, 1::2] = torch.cos(position * div_term[:-1])
        else:
            pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)
        self.register_buffer("pe", pe)

    def forward(self, x):
        x = x + self.pe[:, :x.size(1)]
        return self.dropout(x)


class TransformerClassifier(nn.Module):
    def __init__(self, num_cont, meta_dim, d_model=64, nhead=4,
                 num_layers=2, dim_feedforward=128, dropout=0.3, max_len=1024):
        super().__init__()
        self.syl_embed = nn.Embedding(NUM_SYLLABLE_TYPES, SYLLABLE_EMBED_DIM)
        input_dim = num_cont + SYLLABLE_EMBED_DIM + 2

        self.input_proj = nn.Linear(input_dim, d_model)
        self.cls_token = nn.Parameter(torch.randn(1, 1, d_model))
        self.pos_enc = PositionalEncoding(d_model, max_len=max_len + 1, dropout=dropout)

        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model, nhead=nhead, dim_feedforward=dim_feedforward,
            dropout=dropout, batch_first=True,
        )
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=num_layers)
        self.classifier = nn.Sequential(
            nn.Linear(d_model + meta_dim, 64),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(64, 1),
        )

    def forward(self, cont, syl_type, noise, rec_boundary, metadata, lengths):
        emb = self.syl_embed(syl_type)
        x = torch.cat([cont, emb, noise.unsqueeze(-1), rec_boundary.unsqueeze(-1)], dim=-1)
        x = self.input_proj(x)

        batch_size = x.size(0)
        cls = self.cls_token.expand(batch_size, -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = self.pos_enc(x)

        # lengths+1 for the CLS token
        pad_mask = torch.arange(x.size(1), device=x.device).unsqueeze(0) >= (lengths.unsqueeze(1) + 1)
        x = self.transformer(x, src_key_padding_mask=pad_mask)

        cls_out = x[:, 0]
        combined = torch.cat([cls_out, metadata], dim=-1)
        return self.classifier(combined).squeeze(-1)


MODEL_REGISTRY = {
    "bilstm": BiLSTMClassifier,
    "cnn1d": CNN1DClassifier,
    "transformer": TransformerClassifier,
}


def build_model(model_name, num_cont, meta_dim, max_seq_len, device):
    if model_name == "transformer":
        model = TransformerClassifier(num_cont, meta_dim, max_len=max_seq_len)
    else:
        model = MODEL_REGISTRY[model_name](num_cont, meta_dim)
    return model.to(device)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------

def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss = 0
    all_preds, all_labels = [], []

    for batch in loader:
        cont = batch["continuous"].to(device)
        syl = batch["syllable_type"].to(device)
        noise = batch["noise"].to(device)
        rec_b = batch["rec_boundary"].to(device)
        meta = batch["metadata"].to(device)
        labels = batch["label"].to(device)
        lengths = batch["length"].to(device)

        optimizer.zero_grad()
        logits = model(cont, syl, noise, rec_b, meta, lengths)
        loss = criterion(logits, labels)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
        optimizer.step()

        total_loss += loss.item() * len(labels)
        preds = (torch.sigmoid(logits) >= 0.5).float()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())

    avg_loss = total_loss / len(all_labels)
    acc = accuracy_score(all_labels, all_preds)
    return avg_loss, acc


@torch.no_grad()
def evaluate(model, loader, criterion, device):
    model.eval()
    total_loss = 0
    all_preds, all_labels, all_probs = [], [], []

    for batch in loader:
        cont = batch["continuous"].to(device)
        syl = batch["syllable_type"].to(device)
        noise = batch["noise"].to(device)
        rec_b = batch["rec_boundary"].to(device)
        meta = batch["metadata"].to(device)
        labels = batch["label"].to(device)
        lengths = batch["length"].to(device)

        logits = model(cont, syl, noise, rec_b, meta, lengths)
        loss = criterion(logits, labels)

        total_loss += loss.item() * len(labels)
        probs = torch.sigmoid(logits)
        preds = (probs >= 0.5).float()
        all_preds.extend(preds.cpu().numpy())
        all_labels.extend(labels.cpu().numpy())
        all_probs.extend(probs.cpu().numpy())

    avg_loss = total_loss / len(all_labels)
    acc = accuracy_score(all_labels, all_preds)
    try:
        auc = roc_auc_score(all_labels, all_probs)
    except ValueError:
        auc = 0.0
    return avg_loss, acc, auc, np.array(all_preds), np.array(all_labels), np.array(all_probs)


def train_model(model, train_loader, val_loader, device, epochs, lr,
                pos_weight, model_path):
    pw = torch.tensor([pos_weight], device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", patience=5, factor=0.5,
    )

    best_auc = 0.0
    patience_counter = 0
    patience = 15
    history = {"train_loss": [], "val_loss": [], "train_acc": [], "val_acc": [], "val_auc": []}

    for epoch in range(1, epochs + 1):
        train_loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        val_loss, val_acc, val_auc, _, _, _ = evaluate(model, val_loader, criterion, device)

        scheduler.step(val_auc)
        history["train_loss"].append(train_loss)
        history["val_loss"].append(val_loss)
        history["train_acc"].append(train_acc)
        history["val_acc"].append(val_acc)
        history["val_auc"].append(val_auc)

        current_lr = optimizer.param_groups[0]["lr"]
        print(f"Epoch {epoch:3d}/{epochs} | "
              f"Train Loss: {train_loss:.4f} Acc: {train_acc:.3f} | "
              f"Val Loss: {val_loss:.4f} Acc: {val_acc:.3f} AUC: {val_auc:.3f} | "
              f"LR: {current_lr:.6f}")

        if val_auc > best_auc:
            best_auc = val_auc
            patience_counter = 0
            torch.save(model.state_dict(), model_path)
        else:
            patience_counter += 1
            if patience_counter >= patience:
                print(f"Early stopping at epoch {epoch} (best AUC: {best_auc:.3f})")
                break

    print(f"Best validation AUC: {best_auc:.3f}")
    model.load_state_dict(torch.load(model_path, weights_only=True))
    return history


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def plot_training_curves(history, plots_dir):
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))

    axes[0].plot(history["train_loss"], label="Train", linewidth=2)
    axes[0].plot(history["val_loss"], label="Validation", linewidth=2)
    axes[0].set_title("Loss", fontsize=16)
    axes[0].set_xlabel("Epoch", fontsize=14)
    axes[0].legend(fontsize=12)

    axes[1].plot(history["train_acc"], label="Train", linewidth=2)
    axes[1].plot(history["val_acc"], label="Validation", linewidth=2)
    axes[1].set_title("Accuracy", fontsize=16)
    axes[1].set_xlabel("Epoch", fontsize=14)
    axes[1].legend(fontsize=12)

    axes[2].plot(history["val_auc"], label="Validation AUC", linewidth=2, color="green")
    axes[2].set_title("Validation AUC-ROC", fontsize=16)
    axes[2].set_xlabel("Epoch", fontsize=14)
    axes[2].legend(fontsize=12)

    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "training_curves.png"), dpi=200)
    plt.close()


def plot_confusion_matrices(y_true, y_pred, plots_dir):
    cm = confusion_matrix(y_true, y_pred)
    fig, ax = plt.subplots(figsize=(6, 5))
    sns.set(font_scale=1.4)
    sns.heatmap(
        cm / cm.sum(axis=1, keepdims=True),
        annot=True, fmt=".2%", cmap="Blues", ax=ax,
        xticklabels=["HT (0)", "WT (1)"],
        yticklabels=["HT (0)", "WT (1)"],
    )
    ax.set_title("Confusion Matrix", fontsize=18)
    ax.set_xlabel("Predicted", fontsize=14)
    ax.set_ylabel("True", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "confusion_matrix.png"), dpi=300)
    plt.close()

    fig, ax = plt.subplots(figsize=(6, 5))
    sns.heatmap(
        cm, annot=True, fmt="d", cmap="Blues", ax=ax,
        xticklabels=["HT (0)", "WT (1)"],
        yticklabels=["HT (0)", "WT (1)"],
    )
    ax.set_title("Confusion Matrix (counts)", fontsize=18)
    ax.set_xlabel("Predicted", fontsize=14)
    ax.set_ylabel("True", fontsize=14)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "confusion_matrix_counts.png"), dpi=300)
    plt.close()


def plot_roc_curve(y_true, y_prob, plots_dir):
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    auc_val = roc_auc_score(y_true, y_prob)
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(fpr, tpr, linewidth=2, label=f"AUC = {auc_val:.3f}")
    ax.plot([0, 1], [0, 1], "k--", linewidth=1)
    ax.set_xlabel("False Positive Rate", fontsize=14)
    ax.set_ylabel("True Positive Rate", fontsize=14)
    ax.set_title("ROC Curve", fontsize=18)
    ax.legend(fontsize=12)
    plt.tight_layout()
    plt.savefig(os.path.join(plots_dir, "roc_curve.png"), dpi=300)
    plt.close()


# ---------------------------------------------------------------------------
# CLI & Main
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Train sequence models for Mouse USV ASD detection",
    )
    parser.add_argument(
        "--model", type=str, default="bilstm",
        choices=sorted(MODEL_REGISTRY),
        help="Model architecture (default: bilstm).",
    )
    parser.add_argument(
        "--group-split", action="store_true",
        help="Use group-aware split by mouse identity (prevents data leakage).",
    )
    parser.add_argument(
        "--data-path", type=str, default=DATA_PATH,
        help="Path to the syllable-level Excel file.",
    )
    parser.add_argument(
        "--max-seq-len", type=int, default=256,
        help="Maximum sequence length (default: 256).",
    )
    parser.add_argument("--epochs", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-3)
    parser.add_argument("--results-dir", type=str, default=None)
    return parser.parse_args()


def main():
    args = parse_args()
    set_seed(SEED)

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    # --- results directory ---
    if args.results_dir:
        results_dir = args.results_dir
    else:
        subdir = args.model
        if not args.group_split:
            subdir += "_base"
        else:
            subdir += "_group_split"
        results_dir = os.path.join("results", "neural_networks", subdir)

    plots_dir = os.path.join(results_dir, "plots")
    model_dir = os.path.join(results_dir, "model")
    logs_dir = os.path.join(results_dir, "logs")
    for d in [plots_dir, model_dir, logs_dir]:
        os.makedirs(d, exist_ok=True)

    # --- tee stdout to log file ---
    orig_stdout = sys.stdout
    log_fp = open(os.path.join(logs_dir, "out.txt"), "w")

    class _Tee:
        def __init__(self, *streams):
            self._streams = streams
        def write(self, msg):
            for s in self._streams:
                s.write(msg)
                s.flush()
        def flush(self):
            for s in self._streams:
                s.flush()

    sys.stdout = _Tee(orig_stdout, log_fp)

    active_flags = []
    if args.model != "bilstm":
        active_flags.append(f"--model {args.model}")
    if args.group_split:
        active_flags.append("--group-split")
    print(f"Active flags: {active_flags if active_flags else 'none (baseline)'}")
    print(f"Model: {args.model}")
    print(f"Results directory: {results_dir}")

    # --- load data ---
    sequences = load_and_prepare(args.data_path, args.max_seq_len)

    # --- split ---
    if args.group_split:
        train_seqs, val_seqs, test_seqs = group_split_sequences(sequences, SEED)
    else:
        train_seqs, val_seqs, test_seqs = random_split_sequences(sequences, SEED)

    log_split_info(train_seqs, val_seqs, test_seqs, args.group_split)

    # --- datasets ---
    train_ds = USVSequenceDataset(train_seqs, args.max_seq_len, fit_scaler=True)
    val_ds = USVSequenceDataset(val_seqs, args.max_seq_len, scaler=train_ds.scaler)
    test_ds = USVSequenceDataset(test_seqs, args.max_seq_len, scaler=train_ds.scaler)

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True,
                              collate_fn=collate_fn, drop_last=False)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False,
                            collate_fn=collate_fn)
    test_loader = DataLoader(test_ds, batch_size=args.batch_size, shuffle=False,
                             collate_fn=collate_fn)

    # --- class weight ---
    n_wt = sum(1 for s in train_seqs if s["label"] == 1.0)
    n_ht = sum(1 for s in train_seqs if s["label"] == 0.0)
    pos_weight = n_ht / max(n_wt, 1)
    print(f"Class balance in train: WT={n_wt}, HT={n_ht}, pos_weight={pos_weight:.3f}")

    # --- build model ---
    num_cont = len(CONTINUOUS_FEATURES)
    meta_dim = 4
    model = build_model(args.model, num_cont, meta_dim, args.max_seq_len, device)
    total_params = sum(p.numel() for p in model.parameters())
    print(f"Model parameters: {total_params:,}")

    # --- train ---
    model_path = os.path.join(model_dir, f"{args.model}_best.pt")
    history = train_model(
        model, train_loader, val_loader, device,
        args.epochs, args.lr, pos_weight, model_path,
    )

    # --- evaluate on test ---
    pw = torch.tensor([pos_weight], device=device)
    criterion = nn.BCEWithLogitsLoss(pos_weight=pw)
    test_loss, test_acc, test_auc, test_preds, test_labels, test_probs = evaluate(
        model, test_loader, criterion, device,
    )
    train_loss, train_acc, train_auc, _, _, _ = evaluate(
        model, train_loader, criterion, device,
    )

    print(f"\n=== Test Results ===")
    print(f"Test Accuracy:  {test_acc:.4f}")
    print(f"Test AUC-ROC:   {test_auc:.4f}")
    print(f"Train Accuracy: {train_acc:.4f}")
    print(f"Train AUC-ROC:  {train_auc:.4f}")

    report_str = classification_report(test_labels, test_preds, zero_division=0,
                                       target_names=["HT (0)", "WT (1)"])
    report_dict = classification_report(test_labels, test_preds, zero_division=0,
                                        output_dict=True)
    print(f"\nClassification Report:\n{report_str}")

    # --- plots ---
    plot_training_curves(history, plots_dir)
    plot_confusion_matrices(test_labels, test_preds, plots_dir)
    try:
        plot_roc_curve(test_labels, test_probs, plots_dir)
    except ValueError:
        print("Could not generate ROC curve (single class in test set)")

    # --- save results JSON for executive summary ---
    results_data = {
        "model": args.model,
        "group_split": args.group_split,
        "test_accuracy": float(test_acc),
        "test_auc": float(test_auc),
        "train_accuracy": float(train_acc),
        "classification_report": report_dict,
        "num_train": len(train_seqs),
        "num_val": len(val_seqs),
        "num_test": len(test_seqs),
        "total_params": total_params,
        "epochs_trained": len(history["train_loss"]),
        "best_val_auc": float(max(history["val_auc"])) if history["val_auc"] else 0,
    }
    with open(os.path.join(results_dir, "results.json"), "w") as f:
        json.dump(results_data, f, indent=2)

    # --- save scaler ---
    with open(os.path.join(model_dir, "scaler.pkl"), "wb") as f:
        pickle.dump(train_ds.scaler, f)

    print(f"\nDone. Results saved to {results_dir}/")

    sys.stdout = orig_stdout
    log_fp.close()


if __name__ == "__main__":
    main()
