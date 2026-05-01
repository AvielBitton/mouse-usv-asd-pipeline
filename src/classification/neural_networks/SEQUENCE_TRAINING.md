# Sequence Modeling Pipeline

This pipeline trains deep learning models on **ordered syllable sequences** to classify
mouse pups as Wild-Type (WT) or ASD-model (HET). Unlike the tabular pipeline
(`src/classification/tabular/train_classifier.py`) which aggregates features per recording, this pipeline preserves
the temporal ordering and "syntax" of vocalizations.

## Quick Start

```bash
# BiLSTM with group-aware split (recommended)
python src/classification/neural_networks/sequence_pipeline.py --model bilstm --group-split

# 1D-CNN with random split
python src/classification/neural_networks/sequence_pipeline.py --model cnn1d

# Transformer with group-aware split
python src/classification/neural_networks/sequence_pipeline.py --model transformer --group-split
```

## Data Flow

```
segmentation_classification_all_data.xlsx (125K syllable rows)
    │
    ├── Filter: keep only WT and HT genotypes
    ├── Clean: clip Duration/ISI outliers, fill ISI NaN with 0
    ├── Group by: (mouse Name, Day, Session) → 442 sessions
    ├── Order by: Path + Syllable order (chronological)
    └── Add: recording_boundary marker (1 at first syllable of each recording)
            │
            ▼
    Per-session syllable sequence (median 236 syllables)
    Each syllable = 14-dim feature vector:
      - 4 continuous: Start Hz, End Hz, Duration, ISI
      - 8 embedding: Syllable type (0-10) → learned 8-dim
      - 2 binary: Noise flag, Recording boundary
            │
            ▼
    Pad/truncate to MAX_SEQ_LEN (default: 256)
            │
            ▼
    Train sequence model → Predict WT (1) vs HT (0)
```

## Models

| Model | Architecture | Parameters | Strength |
|---|---|---|---|
| `bilstm` | 2-layer Bidirectional LSTM | ~149K | Temporal dependencies |
| `cnn1d` | 3-layer Conv1D + Global Pool | ~86K | Local n-gram patterns |
| `transformer` | 2-layer Transformer Encoder | ~73K | Long-range attention |

All models share the same input/output interface. Static metadata (mother genotype,
sex, day, session) is concatenated to the sequence encoder output before classification.

## CLI Options

| Flag | Default | Description |
|---|---|---|
| `--model` | `bilstm` | Model architecture: `bilstm`, `cnn1d`, or `transformer` |
| `--group-split` | off | Split by mouse identity (prevents data leakage) |
| `--data-path` | `outputs/external/segmentation_classification_all_data.xlsx` | Syllable data file |
| `--max-seq-len` | `256` | Maximum sequence length (pad/truncate) |
| `--epochs` | `100` | Maximum training epochs |
| `--batch-size` | `32` | Batch size |
| `--lr` | `0.001` | Learning rate |
| `--results-dir` | auto | Override results directory |

## Split Modes

### Random split (default)
Sessions are split randomly 60/20/20. Sessions from the same mouse **can** appear
in different sets. This mirrors `train_classifier.py` without `--group-split`.

### Group-aware split (`--group-split`)
Mice are split 60/20/20, then all sessions of each mouse go to the same set.
**No mouse appears in more than one set.** This is the scientifically correct
evaluation but reduces effective diversity.

## Output Structure

```
results/neural_networks/<model>_<split>/
├── logs/out.txt              # Full training log
├── model/<model>_best.pt     # Best model checkpoint (by val AUC)
├── model/scaler.pkl          # StandardScaler fit on training data
├── plots/
│   ├── training_curves.png   # Loss, accuracy, AUC over epochs
│   ├── confusion_matrix.png  # Normalized confusion matrix
│   ├── confusion_matrix_counts.png
│   └── roc_curve.png         # ROC curve with AUC
└── results.json              # Machine-readable metrics
```

## Key Design Decisions

**Why session-level, not recording-level?**
Individual recordings contain a median of only 5 syllables — too short for meaningful
sequence patterns. Grouping by mouse-day-session gives a median of 236 syllables.

**Why recording_boundary feature?**
When concatenating recordings within a session, the ISI between the last syllable
of one recording and the first of the next doesn't exist. We fill ISI with 0 and
mark the boundary with a binary feature so the model knows the ISI is synthetic.

**Class imbalance handling:**
`BCEWithLogitsLoss` with `pos_weight = n_ht / n_wt` down-weights the majority
class (WT) to balance the effective contribution of both classes.

## Dependencies

Requires PyTorch (`torch>=2.0.0`), added to `requirements.txt`.
All other dependencies (pandas, sklearn, matplotlib, seaborn) are already present.
