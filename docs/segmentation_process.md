# Segmentation Process — End-to-End Documentation

> **Purpose.** This document is the canonical, research-grade reference for how raw
> mouse ultrasonic-vocalization (USV) recordings become the syllable-level table
> `segmentation_classification_all_data.xlsx` / `.csv` — the file every downstream
> modeling step starts from. It maps **every column**, explains **how each value is
> computed and why**, records the **technical parameters**, assesses whether the
> approach is **state of the art**, and collects **open questions / concerns** worth
> raising in a methods section.
>
> Audience: the authors of the project's research paper (and Claude, when drafting
> the segmentation / preprocessing methodology). Wherever possible, claims are tied
> to a concrete code path so they can be verified and cited.
>
> Resolves Issue #63.

---

## 0. Two producers of the same schema

There are **two surfaces** that run the same segmentation algorithm and emit the same
syllable-level schema. They are **not** two different methods — they are the same code in
two packagings:

| Producer | What it is | Output | Used for |
|----------|-----------|--------|----------|
| **USV Segmentation app** (the project's own GUI, packaged as a Windows executable) | A standalone build of this segmentation pipeline with a graphical front-end, so the lab can run it without Python. **Authors: Chen Aharon & Aviel Bitton.** Published on Zenodo, **v1.0.2**, 2026-05-09, CC-BY-4.0, **DOI [10.5281/zenodo.20096810](https://zenodo.org/records/20096810)** (portable `.exe` + installer `.exe`). | `outputs/external/input/segmentation_classification_all_data.xlsx` (+ `.csv`) | **The canonical / preferred training source.** Carries *correct individual genotyping*. |
| **This repo's preprocessing pipeline** (`src/preprocessing/run_pipeline.py`) | The same algorithm as Python source (steps in §3–§6), so new years (2023/2024) can be processed and the external file reproduced/extended | `outputs/legacy/<file>.xlsx` per metadata batch, then `outputs/legacy/aggregated/all_data.*` | Reproduction, new-data ingestion, validation against the external file. |

Because the app is a build of the same pipeline, **everything in §3–§7 describes what the
app does too** — the app is the citable artifact (DOI above), and the source in this repo
is the inspectable reference. The external file is **preferred for all training**
(`train_classifier.py --external`) because the pipeline's *metadata* once mislabeled
genotype (all pups of HET mothers were labeled HET — see §9.7), whereas the external file
carries per-animal genotyping.

> **For the paper.** Cite the segmentation tool as: *Aharon, C. & Bitton, A. (2026). USV
> Segmentation (v1.0.2) [Software]. Zenodo. https://doi.org/10.5281/zenodo.20096810.* The
> `.exe` is a frozen build (PyInstaller-style, ~3 GB because it bundles TensorFlow +
> CUDA/runtime) of exactly the steps documented here.

> **State of the file today.** `segmentation_classification_all_data.csv` currently holds
> **125,576 syllable rows** (one header + 125,576 data rows) across **31 columns**.

The remainder of this document follows the pipeline's code paths (which are open and
inspectable) as the reference description of the algorithm the standalone app also runs.

---

## 1. Pipeline overview

```
raw WAV recordings  ┐
metadata workbooks  ┘
        │  (1) ingestion / metadata + audio load          steps/prepare_file_inputs.py, utils/recordings_loader.py
        ▼
   SEGMENTATION  ──────────────────────────────────────── steps/segmentation.py + legacy/Segmentation.py
   (detect syllable start/end times per recording)
        │   → rows = one per detected syllable; cols: Path, metadata, Start point(s), End point(s), Duration (time)
        ▼
   BASIC FEATURES  ───────────────────────────────────── steps/compute_basic_features.py + legacy/features.py
   (ISI_time, Start Point (Hz), End Point (Hz))
        ▼
   SYLLABLE CLASSIFICATION (BiT R50×3 CNN)  ──────────── steps/classification.py + legacy/statistics_generator.py
   (Syllable number 0–9 from a 128×128 spectrogram; +10 = post-hoc low-confidence)
        ▼
   COLUMN ENRICHMENT  ────────────────────────────────── steps/enrich_columns.py
   (Index, Year, binary genotypes, groups, order, Noise, supplement, Strain, type labels, complexity)
        ▼
   segmentation_classification_all_data.xlsx / .csv   ← THE STARTING POINT FOR MODELING
        │
        ▼ (downstream, documented elsewhere)
   tabular feature aggregation → all_data_external_main.csv → XGBoost / TabPFN / sequence models
```

Orchestration: `src/preprocessing/run_pipeline.py` (steps 2–7 in the file's own
comments). Per-file workbooks are written to `outputs/legacy/`; the external/canonical
file is consumed from `outputs/external/input/`.

---

## 2. Data ingestion

### 2.1 Inputs

1. **Audio**: `.wav` recordings, one file per *recording* (a take inside a session),
   laid out as
   `USV_Recordings/{year}/{mother_folder}/{pup_folder}/day_{day}/session{session}/{rec}.wav`.
   Sampling rate **Fs = 250,000 Hz** (250 kHz) — required to capture mouse USVs, which
   sit between ~35 kHz and ~125 kHz (above the human hearing range; *ultrasonic*).
2. **Metadata workbooks**: `metadata/Data {year} For Syl Segmentation_{n}.xlsx`. One row
   per recording, supplying the animal/experiment context that segmentation cannot infer
   from audio.

### 2.2 Required metadata columns

`METADATA_REQUIRED_COLUMNS` (`utils/io_utils.py`):

```
Mother, Mother Genotype, Name, Sex, Offspring Genotype, Day, Session, Recording Number
```

Loader robustness (`read_metadata_as_lists`, `normalize_metadata_columns`):
- **Header auto-detection** — scans the first 20 rows, tolerating banner/title rows.
- **Alias map** — accepts English variants *and Hebrew labels* (e.g. `אם`→`Mother`,
  `גנוטיפ גור`→`Offspring Genotype`, `מין`→`Sex`). See `docs/Metadata_Structure.md`.
- **`Sex` normalization** — every value coerced to `M` / `F` / `U`.
- **`Session` normalization** — `normalize_session_cell`; note `Session=0` is treated as
  `1` (a recording must belong to a session).

### 2.3 Path resolution (audio ↔ metadata join)

Audio files are matched to metadata rows by `build_recording_base_path` +
`resolve_wav_path` (`utils/audio_paths.py`) using a two-pass fuzzy matcher:
1. **Identity-key match** — strips colour suffixes (`RED`, `BLUE`, …), genotype suffixes
   (`WT`/`HT`/`KO`), supplement markers (`SUP`/`SUPP`), and parenthetical notes, so
   `24277J-2A (J)` matches folder `24277J-2A (BLUE) WT-WT-WT`.
2. **Prefix / token fallback** for non-canonical 2023+ layouts.

This is the single biggest source of *silent data loss*: if a WAV cannot be resolved, the
recording is skipped (and counted as `missing_count`). The same resolver is reused by the
CNN step so segmentation and classification stay consistent.

---

## 3. Segmentation algorithm (syllable boundary detection)

**Goal:** given one recording's waveform, output a list of `[start_time, end_time]`
pairs, one per detected syllable (a "call"). This is the heart of the process.

**Driver:** `steps/segmentation.py → segment_single_recording()`
**Core math:** `legacy/Segmentation.py` (a cleaned Colab export of the lab's MATLAB-style
algorithm).

**Top-level constants** (`steps/segmentation.py`):

| Constant | Value | Meaning |
|----------|-------|---------|
| `FRAME_LENGTH` | `0.006` s (6 ms) | analysis frame length |
| `OVERLAP` | `0.7` | frame **step** as a fraction of the frame (see §3.2 caveat) |
| `THRESH` | `20` | silence/tonality threshold (`silence_th`) |
| `HARMONY_TH` | `0.009` | relative energy threshold for harmonic detection |
| `Fs` | `250000` | sampling rate |

### 3.1 Preprocessing — `Preprocessing(signal, Fs)`

1. **DC removal**: `signal -= mean(signal)`.
2. **Low-pass FIR (Remez/Parks-McClellan)**: `fir_remez_lpf(100000, 120000, 0.5, 40, 250000)`
   — passband to 100 kHz, stopband from 120 kHz, 0.5 dB passband ripple, 40 dB stopband
   attenuation. Removes content near/above Nyquist (125 kHz) and out-of-band hiss.
3. **Band-stop FIR at 50 kHz**: `fir_remez_bsf(48000, 49500, 50500, 52000, 0.5, 40, 250000)`
   — notches a persistent **50 kHz artifact** (equipment/electrical interference that
   would otherwise be mistaken for vocal energy).

*Why:* mouse USVs are tonal, narrowband, frequency-modulated whistles. Cleaning the band
before energy analysis improves the signal-to-noise ratio of the detector.

### 3.2 Framing — `farming(signal, Fs, FrameLength, Overlap)`

The recording is cut into short, overlapping **analysis frames** so the detector can ask
"is there a vocalization *right here*?" on a fine time grid. Long-signal spectral analysis
only makes sense on quasi-stationary slices, and a 6 ms slice is short enough that a
frequency-modulated USV looks locally tonal inside it.

- `win = FrameLength·Fs = 0.006 × 250000 = 1500` samples → each frame spans **6 ms**.
- `inc = round(Overlap·win) = round(0.7 × 1500) = 1050` samples → frames advance by the
  **hop** of `inc` samples = **4.2 ms**.
- **Overlap region** between consecutive frames = `win − inc = 450` samples = **1.8 ms**.
- **Frame rate** (analysis points per second) = `Fs/inc = 250000/1050 ≈ 238 frames/s`.
  This 4.2 ms grid is the **temporal resolution of boundary detection** — start/end times
  are quantized to multiples of ~4.2 ms before the call-level rules in §3.6 refine them.
- Each frame is multiplied by a **Hamming window** before analysis.
- `mind` = sample index at the centre of each frame; combined with `ind2` (the trim
  offset, §3.3) it converts frame indices back to **absolute times in seconds**.

**Why a window (and why Hamming)?** Slicing a signal with a hard rectangular cut creates
discontinuities at the frame edges, which smear energy across the spectrum (*spectral
leakage*) and would create spurious "frequencies" in the energy detector. Tapering each
frame to zero at its edges with a Hamming window suppresses those edge effects (Hamming
gives ≈ −43 dB peak side-lobes), so the per-channel energy in §3.5 reflects genuine tonal
content rather than windowing artifacts. The price is slightly wider main lobes (a small
loss of frequency sharpness) — an acceptable trade for a detector keyed on energy
concentration, not exact pitch.

> ⚠️ **Naming caveat worth flagging in the paper.** The parameter is called `Overlap` but
> is used as the *frame-step fraction*. With `inc = 0.7·win`, consecutive frames advance by
> 70 % of the window, so the **actual overlap is 30 %** (1.8 ms), not 70 %. State the real
> overlap (30 %) in the methods section to avoid a reproducibility discrepancy.

### 3.3 Leading-silence trim — `trim_leading_silence(signal)`

If the recording starts with a run of exact zeros (some hardware pads the file head),
the signal is shifted so analysis starts at the first real sample. Returns `ind2`, the
sample offset, which is later added back so reported times are relative to the original
file start.

### 3.4 Cochlear (ERB / gammatone) filterbank — `MakeERBFilters` + `ERBFilterBank`

Each frame is passed through a **bank of 90 gammatone filters** (Patterson–Holdsworth
cochlear model; Glasberg & Moore parameters `EarQ = 9.26449`, `minBW = 24.7`, `order = 1`):

- `numChannels = 90`, `lowFreq = 35000` Hz.
- Centre frequencies are **ERB-spaced (quasi-logarithmic) from 35 kHz to Fs/2 = 125 kHz**
  across the 90 channels — i.e. the band where mouse USVs live. ERB spacing packs more,
  narrower filters at low frequencies and fewer, wider ones high up.
- **Filter realization:** each channel is Slaney's **4th-order gammatone**, implemented as
  an IIR filter (`forward` = 5 numerator taps, `feedback` = 9 denominator taps → 8th-order
  recursive realization) and applied with `scipy.signal.lfilter`. `MakeERBFilters` returns
  the coefficient banks once; `ERBFilterBank` runs all 90 filters over a frame.

*Why a cochlear model here?* The gammatone bank gives an ERB-spaced, sharply-tuned spectral
decomposition that emphasizes narrowband tonal energy — the classic auditory front-end,
with much sharper tuning than a same-size linear FFT filterbank. **Note for the methods
section:** this is a model of the *mammalian cochlea* repurposed to the ultrasonic band — a
pragmatic reuse (it works simply as a bank of sharp, perceptually-spaced band-pass
filters), not a biologically literal "what the mouse hears."

> 🧹 **Vestigial CLI branches.** `Syllables_Detection_ERB` contains
> `if len(sys.argv)-1 == 7:` guards (and a `*M` variadic) left over from when this ran as a
> command-line script with positional arguments. Inside the pipeline/app `sys.argv` never
> has 7 args, so those branches are **dead code** and do not affect results — but they make
> the function look more conditional than it is. Worth pruning, and worth *not* citing as
> active logic in the paper.

### 3.5 Per-frame syllable presence — `Syllables_Detection_ERB` & `Syllables_Detection2`

For each frame:
1. Filter through the bank, square, and sum across channels → **per-channel energy**;
   `Energy`, `Max = max(Energy)`.
2. `we = where(Energy > 0.2·Max)` → `Freq_var` = number of channels carrying >20 % of the
   peak energy. **This is the tonality test.** A *vocal* (whistle) frame concentrates
   energy in few channels (small `Freq_var`); broadband *noise* spreads energy across many
   channels (large `Freq_var`).
3. **Vocal decision:** `if Freq_var <= silence_th (=THRESH=20): frame is vocal`.
4. Within a vocal frame, find spectral **peaks** with energy `≥ th·Max`, where
   `th = 0.9` for the first/primary formant. Keep up to **3 formant frequencies** per frame
   (`AllFormant`, shape *frames × 3*).
5. **Harmonic refinement** (`Syllables_Detection2`): when a single fundamental is found, a
   *second* gammatone bank is built around `2·f` to look for the first harmonic, using
   `harmony_th = 0.009` and the extra constraint `peak > 10·mean_full_energy`. Detected
   harmonics are merged back, so harmonic/composite syllables are not split.

A frame is marked vocal in `SyllableVec[frm] = 1` when any formant is found.

**Gap bridging:** short voiced gaps of **2–4 frames** between vocal frames are *filled in*
(`SyllableVec` set to 1, and the missing formant is linearly interpolated from the
neighbours). This keeps a single frequency-modulated sweep from being chopped into pieces
by a momentary energy dip.

**Frequency continuity** — `frequency_continuity(x)`: enforces harmonic continuity,
requiring a harmony to persist across **at least ~3–4 consecutive frames** before it is
accepted (suppresses one-frame spectral flukes).

### 3.6 From frames to calls — `Rearrange_signal` + `Check_length_Call`

1. **`Rearrange_signal`** merges adjacent voiced frames into contiguous `[start, end]`
   spans based on the gaps between frame boundaries.
2. **`Check_length_Call`** applies the call-level temporal rules:

   | Constant | Value | Role |
   |----------|-------|------|
   | `MIN_BETWEEN_CALL` | `0.02` s (20 ms) | two detections closer than this are **merged into one call** |
   | `MIN_LENGTH` | `0.01` s (10 ms) | calls **shorter** than this are **discarded** |
   | `MAX_LENGTH` | `0.3` s (300 ms) | *defined but **not enforced*** — see flag below |

   So the final calls are: merge near-touching detections, then keep only those ≥ 10 ms.

**Syllables are disjoint, non-overlapping time spans.** Although the *analysis frames*
overlap by 1.8 ms (§3.2), the *syllables* themselves never overlap: each call is a
contiguous `[start, end]` interval, and `Check_length_Call` guarantees separation by
folding any two detections less than `MIN_BETWEEN_CALL = 20 ms` apart into a **single**
call. The practical consequences:
- A frequency-modulated sweep briefly dipping in energy is **kept whole** (frame-level gap
  bridging in §3.5 + the 20 ms call-level merge), rather than split into two syllables.
- The silent gap that *does* survive between two accepted calls is later measured as
  **`ISI_time`** (§4.1). By construction `ISI_time ≥ MIN_BETWEEN_CALL` within a recording —
  anything smaller was already merged away. This is the key link between the segmentation
  thresholds and the inter-syllable timing feature.

> ⚠️ **Bug/inconsistency to flag.** `MAX_LENGTH = 0.3` is declared in `Check_length_Call`
> but **never used** to filter — there is no upper-duration cutoff at segmentation time.
> Over-long "syllables" (e.g. merged noise) are therefore *not* rejected here; they survive
> into the table and are only loosely handled later (e.g. the CNN may label them, the
> `Noise` heuristic may flag some). Worth either documenting as intentional or fixing.

**Output of segmentation** (one row per call), written by `append_calls_to_sheet`:
`Path, Mother, Mother Genotype, Name, Sex, Offspring Genotype, Day, Session,
Recording Number, Start point(s), End point(s), Duration (time)` where
`Duration (time) = End − Start`.

---

## 4. Basic per-syllable features

**Driver:** `steps/compute_basic_features.py`; **math:** `legacy/features.py`.

### 4.1 `ISI_time` — Inter-Syllable Interval

```python
ISI[i] = start[i] − end[i−1]   if rec_num[i] == rec_num[i−1]   else NaN
```
The silent gap from the *previous* syllable's end to *this* syllable's start, within the
same recording. `NaN` at each recording's first syllable. ISI is a standard USV
quantity — abnormal inter-call timing/rhythm is a behavioral phenotype of interest in
autism models.

> ⚠️ **Edge case.** For the very first row (`i = 0`), the code compares against `[-1]`
> (Python wrap-around to the last element). In practice the boundary check usually yields
> `NaN`, but this wrap-around is a latent off-by-one worth noting.

### 4.2 `Start Point (Hz)` / `End Point (Hz)` — boundary frequencies

For each syllable, a **2000-sample window** (≈ 8 ms at 250 kHz) is taken around the start
boundary (`st1 = round(start·Fs) − 1000`, clamped ≥ 0) and around the end boundary
(`st2 = round(end·Fs) − 1000`):

1. **Welch PSD** of the window — `scipy.signal.welch`, `nperseg = 1024`, `noverlap = 625`.
   - **Why Welch (not a plain FFT)?** A single FFT of a short, noisy slice gives a
     high-variance spectrum. Welch's method splits the window into overlapping sub-segments,
     windows each, takes its periodogram, and **averages** them — trading a little frequency
     resolution for a much smoother, lower-variance PSD, so the true tonal peak stands out.
   - **Frequency resolution** = `Fs/nperseg = 250000/1024 ≈ 244 Hz` per bin (513 bins from 0
     to 125 kHz). This is the granularity of `Start/End Point (Hz)`.
   - **Sub-segment overlap** = `noverlap/nperseg = 625/1024 ≈ 61 %`. Each sub-segment spans
     `1024/Fs ≈ 4.1 ms`.
   - **How many sub-segments get averaged?** The analysis window is only 2000 samples
     (≈ 8 ms), so with step `1024 − 625 = 399` samples only ≈ **3 sub-segments** are
     averaged — modest smoothing, limited by the short window. (scipy's default Hann window
     is used inside Welch.)
   - `_welch_psd` clamps `nperseg`/`noverlap` to the segment length so windows near the file
     end — where fewer than 1024 samples remain — don't crash.
2. Restrict to **frequencies > 40,000 Hz** (`where(f > 40000)`) — ignore sub-ultrasonic
   energy / low-frequency noise; mouse USVs sit well above 40 kHz.
3. **Pick the strongest spectral peak** (`find_peaks` → `argmax`) in that band; its
   frequency is the start (resp. end) point in Hz. (Peak-picking, not the band centroid, so
   a clean tonal whistle maps to its carrier frequency.)
4. On any failure (no peak, empty band, exception) the value defaults to **0**, and the
   first 25 failures are logged.

> **Window placement nuance.** `st = round(boundary·Fs) − 1000` starts the 2000-sample
> window **1000 samples (≈ 4 ms) before** the detected boundary, so the boundary sits near
> the window centre. The measured "start/end frequency" is therefore the dominant tone in
> an ≈ 8 ms neighbourhood *around* the boundary, not at the exact instant — a deliberate
> smoothing that makes the estimate robust to the ~4.2 ms boundary quantization (§3.2).

*Why:* `Start/End Point (Hz)` capture the **frequency contour endpoints** of the call
(e.g. an upward sweep has end > start). These two numbers, with `Duration`, are the
primary acoustic descriptors that feed the tabular models.

> **Two execution modes**: in-memory (`StartEndFreq`, all waveforms held in RAM) vs.
> streaming (`StartEndFreq_from_paths`, one WAV loaded at a time, indexed by
> `(mother, name, day, session, rec_num)`). The streaming mode is what makes
> multi-thousand-row workbooks feasible on a laptop.

---

## 5. Syllable-type classification (CNN — BiT transfer learning)

**Driver:** `steps/classification.py`; **spectrogram + inference:**
`legacy/statistics_generator.py → Syl_Class_Vec`; **model:** `src/models/model_weights.h6`.

### 5.0 Model architecture — **BiT (Big Transfer) ResNet-50×3**, recovered from the SavedModel

`model_weights.h6` is **not** a single `.h5` file and **not** a small bespoke CNN — despite
its name and the repo's earlier "CNN classifier" wording. It is a **TensorFlow SavedModel
directory** (`saved_model.pb` + `variables/`), and inspecting its graph signature and
checkpoint variable shapes (no published model card exists — see §11) reveals it is a
**Big Transfer (BiT) model, ResNet-50 ×3**, fine-tuned with a 10-way head:

| Property | Value (recovered) | Evidence |
|----------|-------------------|----------|
| Input | `[-1, 128, 128, 3]` | `serving_default` signature `input_1` |
| Output | `[-1, 10]` (softmax over **10** classes) | signature output `dense` |
| Backbone | **BiT-M ResNet-50 ×3** (ResNet-v2 bottleneck, block depths **(3, 4, 6, 3)**, width ×3) | variable names `resnet/block{1..4}/unit{01..06}/{a,b,c}` |
| Conv type | **Weight-Standardized conv** (not plain Conv2D) | `…/standardized_conv2d/kernel` |
| Normalization | **Group Normalization** (not BatchNorm) | `…/group_norm/{gamma,beta}` |
| Stem | 7×7 conv, 3→192 ch + max-pool | `resnet/root_block/standardized_conv2d/kernel = [7,7,3,192]` |
| Block widths (inner / projected) | 192/768 → 384/1536 → 768/3072 → 1536/**6144** | bottleneck kernels per block |
| Classifier head | single `Dense(6144 → 10)` + bias, softmax | `layer_with_weights-1/kernel=[6144,10]`, `bias=[10]` |
| Backbone params | ≈ 211 M (R50×3 is a *large* model) | — |

**What this means.** *Weight Standardization + Group Normalization on a ResNet-v2* is the
exact signature of **BiT** (Kolesnikov et al., "Big Transfer (BiT): General Visual
Representation Learning," ECCV 2020; Google), distributed on TF-Hub as
`google/bit/m-r50x3` (pre-trained on **ImageNet-21k**). The syllable classifier is therefore
**transfer learning**: a large ImageNet-21k-pretrained BiT backbone with its 21k head
replaced by a `Dense(10)` head fine-tuned on mouse-USV syllable spectrograms. This is why
the spectrogram is shaped 128×128×**3** and scaled to ~[0,1] in §5.1 — it is being fed to an
RGB ImageNet model. BiT's GN+WS design is specifically what makes such models transfer and
fine-tune well from **small** downstream datasets, which fits a hand-labeled USV syllable
set.

> ⚠️ **The weights are not in this checkout.** `variables/` contains only
> `variables.index`; the actual weight shard
> `variables/variables.data-00000-of-00001` is listed in **`.gitignore`** (it is large,
> ~200 MB+). So the model **cannot be loaded or run from a clean clone** without obtaining
> the weight shard separately. `steps/classification.load_classification_model` +
> `_ensure_savedmodel_variable_filenames` only *rename* existing shards; they cannot
> conjure the missing data file. **Action item for reproducibility:** publish the weight
> shard (e.g. alongside the Zenodo app, §13) and document where to place it.

### 5.1 Per-syllable spectrogram construction

For each detected syllable (parameters from `Syl_Class_Vec`):

1. **Load** the recording once and cache it across consecutive syllables of the same file.
2. **Length normalization to `max_time = 0.25` s**: if the syllable is shorter, it is
   **center-padded with silence** symmetrically (`silence = zeros((max_time − dur)/2)` on
   each side) to 0.25 s; longer syllables are taken as-is. This gives the CNN a fixed-extent
   canvas and **centres the call**, so syllable *position* never leaks into the image — the
   network sees shape, not where in the buffer the call happened to fall.
3. **30 kHz high-pass** Butterworth filter (`order = 6`, `cutoff = 30 kHz`) — removes
   sub-ultrasonic energy/hum so the spectrogram's contrast is spent on the USV band, not on
   low-frequency clutter.
4. **STFT** — `librosa.stft(syl, n_fft = 2048, hop_length = 128, win_length = 512,
   window = 'hamming')`, then `|D|` (magnitude). This is the core time–frequency transform;
   its parameters set what the CNN can "see":

   | Parameter | Value | Physical meaning |
   |-----------|-------|------------------|
   | `win_length` | 512 samples = **2.048 ms** | the analysis window — the true time/frequency trade-off knob |
   | `hop_length` | 128 samples = **0.512 ms** | step between successive spectra (STFT columns) |
   | STFT overlap | `(512−128)/512` = **75 %** | consecutive windows overlap 3/4, giving a smooth, finely-sampled time axis |
   | `n_fft` | 2048 (≥ `win_length`) | FFT length; the 512-sample window is **zero-padded to 2048** |
   | Frequency bins | `n_fft/2+1` = **1025** rows, spaced `Fs/n_fft` = **122 Hz** | bin spacing on the frequency axis |
   | Effective freq. resolution | `≈ Fs/win_length` = **≈ 488 Hz** | *real* resolving power is set by the 2.048 ms window; zero-padding to 2048 only **interpolates** the spectrum (smoother bins) — it does **not** add genuine resolution |
   | Time columns | `≈ 0.25 s / hop` ≈ **~490** | before resizing |

   **The trade-off (worth stating explicitly in the paper).** A short 2.048 ms window gives
   **good time resolution** (it localizes fast frequency sweeps and onsets) at the cost of
   **coarse frequency resolution** (~488 Hz). For mouse USVs — which are fast, sweeping,
   frequency-modulated whistles — favouring time over frequency is the right call: the
   *shape* of the contour (up-sweep, chevron, steps) is what discriminates syllable types,
   and that shape is a temporal pattern. Zero-padding to `n_fft = 2048` then up-samples the
   frequency axis so the contour looks smooth to the CNN.
5. **Resize to 128×128** (bicubic, `cv2.resize`, 4×4 neighbourhood) — collapses the
   ~1025×~490 magnitude image to the CNN's fixed input. Because every syllable is resized to
   the same grid, absolute duration is **normalized away** at this stage (duration survives
   as its own numeric column, §7 #23, so the information is not lost — just moved out of the
   image).
6. **Normalize**: `D = D − 0.02·mean(D)` (a light pedestal/background subtraction — knocks
   down the low-level noise floor by 2 % of the mean so faint background doesn't dominate
   after scaling); tile to **3 identical channels** (the CNN expects an RGB-shaped tensor);
   cast `float32`; `D /= 255`.

### 5.2 Inference and post-processing

- Spectrograms are stacked and predicted in chunks (`_GLOBAL_INFERENCE_CHUNK = 2048`,
  capped lower for huge jobs) with `_PREDICT_BATCH_SIZE = 32` — purely a throughput
  optimization (minutes instead of hours).
- The model emits a **10-way softmax** (classes **0–9** only — see §5.0; there is no 11th
  output neuron). Post-processing (`classification.postprocess_predictions`):
  - `CONFIDENCE_THRESHOLD = 0.5`: **if max probability < 0.5 → class `10` (Undefined)**;
  - otherwise `argmax` → class **0–9**.
- **So `Syllable number == 10` is a post-hoc "low-confidence / unclassifiable" bucket added
  by the pipeline, not a category the network was trained to predict.** This matters for the
  paper: "Undefined" conflates *genuinely atypical calls* with *calls the model was merely
  unsure about*, and its prevalence is a direct function of the arbitrary 0.5 cutoff.
- Result is written to the **`Syllable number`** column. Raw probabilities are also dumped
  to a sibling `.npy`.

### 5.3 Syllable-type taxonomy (`Syllable number` → label)

`SYLLABLE_TYPE_MAP` (`steps/enrich_columns.py`) — the standard mouse-USV repertoire:

| # | Type | Complexity group | Complexity (numeric) |
|---|------|------------------|----------------------|
| 0 | Complex | Single Vowel | 1 |
| 1 | Frequency steps | Multiple Vowels | 2 |
| 2 | Composite | Advanced Harmonic | 3 |
| 3 | Two syllables | Multiple Vowels | 2 |
| 4 | Upward | Single Vowel | 1 |
| 5 | Flat | Single Vowel | 1 |
| 6 | Harmonic | Advanced Harmonic | 3 |
| 7 | Downward | Single Vowel | 1 |
| 8 | Chevron | Single Vowel | 1 |
| 9 | Short | Single Vowel | 1 |
| 10 | Undefined | Undefined | 0 |

The complexity grouping (`_complexity_numeric`) collapses the 11 types into 4 ordered
"complexity levels," a coarser feature: `Undefined(0) < Single Vowel(1) < Multiple
Vowels(2) < Advanced Harmonic(3)`.

### 5.4 The three time–frequency analyses, compared

The pipeline runs **three different short-time spectral analyses**, each tuned to a
different job. Conflating them is a common source of confusion, so the methods section
should present them side by side:

| | **Segmentation framing** (§3.2) | **Boundary frequency** (§4.2) | **CNN spectrogram** (§5.1) |
|---|---|---|---|
| Purpose | detect *where* a syllable is | measure start/end **pitch** | image the syllable **shape** for typing |
| Transform | gammatone filterbank energy | Welch PSD | STFT magnitude |
| Window | 1500 smp = **6 ms**, Hamming | 1024 smp ≈ **4.1 ms**, Hann | 512 smp = **2.05 ms**, Hamming |
| Step / overlap | 1050 smp / **30 %** | 399 smp / **61 %** | 128 smp / **75 %** |
| Freq. resolution | 90 ERB channels, 35–125 kHz | **≈ 244 Hz** | **≈ 488 Hz** (FFT-interpolated to 122 Hz bins) |
| Band of interest | tonality across 35–125 kHz | peak **> 40 kHz** | full band, HPF > 30 kHz |
| Output | per-frame vocal/not + formants | one Hz value per boundary | 128×128 image → class 0–9 (+10 post-hoc) |

Reading the table: detection uses the **longest** window (6 ms) because it only needs to
know energy is concentrated, not its exact value; pitch measurement uses a **medium**
window with variance-reducing averaging (Welch) because it needs a stable number; the CNN
uses the **shortest** window (2 ms) with the **most overlap** (75 %) because it needs to
resolve the fast temporal contour that defines syllable type. All three deliberately
ignore energy below ~30–40 kHz, where mouse USVs do not occur.

---

## 6. Column enrichment

**Driver:** `steps/enrich_columns.py → enrich_segmentation_columns`. Reads the workbook,
computes derived columns, **reorders to `FINAL_COLUMN_ORDER`**, writes back. All writes are
idempotent (re-running overwrites in place). Key derivations:

- **`Index`** — 1-based serial row id.
- **`Year`** — parsed from `Path` (`Path.split('/')[1]`), fallback to the run's year.
- **`Mother/Offspring Genotype (binary)`** — `HT → 1`, everything else (`WT`/`UNK`/`NAN`/…)
  `→ 0`. (HET is encoded as HT upstream; positive class = ASD model carrier.)
- **`Genotype Group`** (text) — `"<Mother>-<Offspring>"`, e.g. `WT-WT`, `HT-WT`, `HT-HT`;
  empty→`NAN`, unknown→`UNK`.
- **`Genotype Group (numeric)`** — `WT-WT=1`, `HT-WT=2`, `HT-HT=3`, anything else `=0`.
  (Encodes the genetic cross; `HT-WT` is the informative heterozygous-mother → WT-pup case.)
- **`Syllable order (in recording)`** — rank by ascending `Start point(s)` within each
  `Path` (nullable `Int64`).
- **`Syllables per recording`** — count of rows per `Path`.
- **`Noise`** — `1` when `Start Point (Hz) == End Point (Hz)`, else `0` (see §7 note).
- **`Supplement (Mother)` / `Supplement (Offspring)`** — metadata cell first, falling back
  to a `"sup"` substring test on `Name`/`Mother`/`Path` (dietary-supplement experimental
  arm).
- **`Strain`** — *text* label by year: `BALB/C` (2015/2018) vs `BALB/C+BLACK/C57` (2022+).
  ⚠️ This column is later **overwritten with a numeric strain id (1/2)** by the tabular
  feature-extraction step (`STRAIN_1_YEARS = {2022,2023,2024} → 1`, else `2`) before
  training. The text label exists only so the per-file workbook reads like the external app's.
- **`Syllable type` / `Complexity level` / `Complexity level (numeric)`** — mapped from
  `Syllable number` per §5.3.

---

## 7. Output schema — `segmentation_classification_all_data` (31 columns)

Canonical order (`FINAL_COLUMN_ORDER`). Each row = **one detected syllable**.

| # | Column | Source / step | Computation | Why it exists |
|---|--------|---------------|-------------|---------------|
| 1 | `Index` | enrich | 1..N serial | row id |
| 2 | `Path` | segmentation | WAV path | provenance / join key |
| 3 | `Year` | enrich | from `Path` | cohort / strain proxy |
| 4 | `Mother` | metadata | passthrough | dam identity (grouping/leakage control) |
| 5 | `Mother Genotype` | metadata | passthrough (HT/WT/…) | maternal genotype |
| 6 | `Mother Genotype (binary)` | enrich | HT→1 else 0 | model feature |
| 7 | `Supplement (Mother)` | enrich | metadata/`"sup"` heuristic | experimental arm |
| 8 | `Name` | metadata | passthrough | pup identity (subject id) |
| 9 | `Sex` | metadata | normalized M/F/U | covariate |
| 10 | `Offspring Genotype` | metadata | passthrough | **the label of interest (ASD model)** |
| 11 | `Offspring Genotype (binary)` | enrich | HT→1 else 0 | **target encoding** |
| 12 | `Genotype Group` | enrich | `"<M>-<O>"` | cross descriptor |
| 13 | `Genotype Group (numeric)` | enrich | 1/2/3/0 | cross feature |
| 14 | `Supplement (Offspring)` | enrich | metadata/`"sup"` | experimental arm |
| 15 | `Day` | metadata | passthrough | pup age (days) — USV repertoire is age-dependent |
| 16 | `Session` | metadata | normalized (0→1) | recording session |
| 17 | `Strain` | enrich → overwritten | text by year → numeric 1/2 | mouse strain feature |
| 18 | `Recording Number` | metadata | passthrough | recording id within session |
| 19 | `Syllable order (in recording)` | enrich | rank by start time | sequence position |
| 20 | `Syllables per recording` | enrich | count per `Path` | call-rate proxy |
| 21 | `Start point(s)` | **segmentation** | call start time (s) | temporal boundary |
| 22 | `End point(s)` | **segmentation** | call end time (s) | temporal boundary |
| 23 | `Duration (time)` | segmentation | `End − Start` (s) | **core acoustic feature** |
| 24 | `ISI_time` | basic features | `start[i]−end[i−1]` (same rec), else NaN | inter-call timing |
| 25 | `Start Point (Hz)` | basic features | Welch-PSD peak >40 kHz at start | **core acoustic feature** |
| 26 | `End Point (Hz)` | basic features | Welch-PSD peak >40 kHz at end | **core acoustic feature** |
| 27 | `Noise` | enrich | `1` if start Hz == end Hz | QA flag |
| 28 | `Syllable number` | **CNN** | argmax (or 10 if p<0.5) | syllable type id |
| 29 | `Syllable type` | enrich | label of #28 | human-readable type |
| 30 | `Complexity level` | enrich | group of #28 | coarse type |
| 31 | `Complexity level (numeric)` | enrich | 0–3 | coarse type (numeric) |

**Worked example (row 1 of the current file):**
`2015 / mother 08001P (HT) / pup 08130I (F, HT) / day 12 / session 1 / BALB/C /
T0000011 / syllable 1 of 1 / 0.5292–0.5436 s (dur 0.0144) / start=end=50781.25 Hz →
Noise=1 / Syllable number 9 = "Short" / Single Vowel (1)`. Note this row is flagged
`Noise=1` precisely because start Hz == end Hz.

---

## 8. Filtering & QA

The syllable table itself is **inclusive** — segmentation/QA flags are *columns*, not
row deletions, so downstream code can choose its own policy. Actual row filtering happens
at **aggregation** time (`steps/extract_features.py`, see `docs/BASELINE_DATA_FILTERS.md`):

- **Always dropped:** rows whose Mother *or* Offspring genotype is not WT/HET after
  `HT→HET` (keeps `pup_gen` binary).
- **`Noise == 1` rows are KEPT** in the baseline (`all_data_external_baseline.*`). The
  `--external-filter noise` ablation removes them.
- **Optional single-filter ablations:** `invalid_sex`, `noise`, `supplement_offspring`,
  `undefined_syllable`.

> **What `Noise == 1` actually means.** It is **not** a model-based noise classifier. It is
> the heuristic "the start-boundary peak frequency equals the end-boundary peak
> frequency." This catches perfectly flat detections (often equipment artifacts or
> degenerate windows where Welch returned the same bin twice), but it is **crude**: a
> genuine *flat* syllable (type 5) can trip it, and real noise with differing endpoints
> will not. Treat `Noise` as a weak QA hint, not ground truth.

---

## 9. Known edge cases

1. **Supplement offspring** — the dietary-supplement arm; flagged (§6) and offered as an
   ablation filter. Mixing them into the main analysis confounds genotype effects.
2. **Invalid sex** — `Sex` outside `{M,F}` (i.e. `U`/unknown) → `invalid_sex` filter.
3. **Undefined syllable type** — `Syllable number == 10`, assigned when the CNN's top
   probability `< 0.5` *or* the call is genuinely unclassifiable → `undefined_syllable`
   filter. These are low-confidence calls.
4. **Missing audio** — recordings whose WAV can't be resolved are skipped at ingestion
   (`missing_count`); they silently never reach the table.
5. **Welch failures / boundary windows** — default to `0 Hz` (and likely `Noise=1` if both
   ends fail), rather than dropping the row.
6. **`Session = 0`** — normalized to `1`.

### 9.7 Genotype-labeling correction (April 2026) — *critical for the paper*

*(Not an edge case of segmentation per se, but of the labels attached to each row — and
the single most important caveat for any analysis built on this table.)*

The original *metadata* labeled **all** pups of a HET mother as HET. Genetically wrong: a
HET × WT cross yields ~50 % HET and ~50 % WT offspring. **14 mice (2,495 rows across 6
metadata files)** were corrected HET→WT using individual genotyping from the external
segmentation file. **Consequence:** always train on the external file (`--external`); the
pipeline-aggregated `all_data.csv` carries the legacy error unless regenerated. See
`README.md` → "Data Correction (April 2026)".

---

## 10. Is this state of the art?

**Honest assessment for the methods/limitations section.**

**Segmentation (detection).** The approach — gammatone/ERB filterbank + per-frame energy
*tonality* thresholding + temporal merge/length rules — is a **classical DSP detector**,
methodologically closer to **MUPET** (Van Segbroeck et al., 2017) and **USVSEG**
(Tachibana et al., 2020) than to current deep-learning detectors. It is **not** state of
the art relative to:
- **DeepSqueak** (Coffey et al., 2019) — Faster-R-CNN object detection on sonograms;
- **VocalMat** (Fonseca et al., 2021) — CNN detection + contour analysis;
- **DAS / Deep Audio Segmenter** (Steinfath et al., 2021) — end-to-end neural segmentation.

*Strengths:* fully interpretable, no training data needed for detection, deterministic,
fast, and tuned to this lab's rig. *Weaknesses:* hard-coded thresholds (`THRESH=20`,
`th=0.9`, `harmony_th=0.009`, the energy ratios) are **not adaptive** and may not transfer
across microphones/rooms/noise floors; the missing `MAX_LENGTH` enforcement (§3.6); the
crude `Noise` heuristic (§8).

**Syllable typing (classification).** This is the **strongest, most modern component** of
the stack. The classifier is **BiT-M ResNet-50×3** (Big Transfer; Kolesnikov et al., ECCV
2020) — an ImageNet-21k-pretrained backbone with Weight Standardization + Group
Normalization, fine-tuned with a 10-way head (§5.0). Transfer learning from a large
pretrained vision model to spectrograms is a **well-founded, near-current** approach, and
BiT's GN+WS design is specifically chosen for good transfer from *small* labeled sets — a
sensible match to a hand-labeled USV repertoire. Caveats for the limitations section: (i)
R50×3 is **heavy** (≈ 211 M params) for a 10-class spectrogram task — likely over-capacity,
chosen for transfer convenience rather than efficiency; (ii) the `0.5`
confidence-to-"Undefined" rule is arbitrary (§5.2); (iii) **no model card** (training set,
per-class accuracy, class balance) is published (§11) — the column's reliability is
currently unquantified.

**Boundary-frequency features.** Welch-PSD peak picking for `Start/End Point (Hz)` is a
simple, defensible spectral estimator. Modern pipelines instead trace the **full
frequency contour** (mean/min/max/slope/bandwidth, frequency-modulation depth) per call —
richer than two endpoints. This is the clearest opportunity to strengthen the feature set.

**Bottom line.** The pipeline is a **hybrid**: a **classical, interpretable DSP detector**
for segmentation + boundary frequencies (predating current deep-learning USV tools), feeding
a **modern deep-transfer-learning classifier** (BiT R50×3) for syllable typing. For the
paper, position the *detection/feature* side as a reproducible classical baseline (with full
provenance), the *typing* side as transfer learning from ImageNet-21k, and frame
deep-learning **segmentation** and richer **contour features** as future work.

---

## 11. Open questions / things to verify before publishing

1. **Thresholds' provenance.** Were `THRESH=20`, `th=0.9`, `harmony_th=0.009`, the `0.2·Max`
   tonality ratio, and `MIN_LENGTH/MIN_BETWEEN_CALL` tuned empirically, inherited from the
   MATLAB original, or taken from a citable source? The paper needs this.
2. **`MAX_LENGTH` not enforced (§3.6)** — intentional or a latent bug? Quantify how many
   calls exceed 0.3 s.
3. **`Overlap` semantics (§3.2)** — confirm the intended overlap is 30 % (frame step 70 %),
   not 70 %.
4. **Detector validation.** Is there *any* hand-labeled ground truth to report
   precision/recall/boundary error against? Without it, detection quality is unquantified.
5. **`Noise` heuristic (§8)** — measure its false-positive rate against true flat syllables
   (type 5) before relying on it.
6. **CNN model card.** Architecture is now recovered (BiT-M R50×3, §5.0), but the
   **training data, labeling protocol, train/val split, per-class accuracy, and class
   balance** of `model_weights.h6` remain undocumented — all needed to defend the
   `Syllable type` column. Also confirm the exact BiT variant/source checkpoint
   (`google/bit/m-r50x3`?) and the fine-tuning recipe.
6b. **Missing weight shard.** `variables/variables.data-00000-of-00001` is `.gitignore`d and
   absent from the repo, so the classifier cannot run from a clean clone (§5.0). Decide
   where the weights are published (Zenodo app? a release asset?) and document it.
7. **ISI first-row wrap-around (§4.1)** — confirm it never corrupts a real ISI value.
8. **0-Hz fallbacks** — how many `Start/End Point (Hz) == 0` rows exist, and how are they
   handled downstream (kept as 0? imputed?).
9. **Pipeline vs. external parity** — has the repo's re-implementation been numerically
   diffed against the standalone app's output on a shared set of recordings? This validates
   the claim that they implement "the same algorithm."

---

## 12. Code-path index (for citation/verification)

| Step | File | Key symbols |
|------|------|-------------|
| Orchestration | `src/preprocessing/run_pipeline.py` | steps 2–7 |
| Ingestion / metadata | `steps/prepare_file_inputs.py`, `utils/recordings_loader.py`, `utils/io_utils.py` | `read_metadata_as_lists`, `METADATA_REQUIRED_COLUMNS`, `normalize_*` |
| Path resolution | `utils/audio_paths.py` | `build_recording_base_path`, `resolve_wav_path` |
| Segmentation driver | `steps/segmentation.py` | `segment_single_recording`, `FRAME_LENGTH/OVERLAP/THRESH/HARMONY_TH` |
| Segmentation math | `legacy/Segmentation.py` | `Preprocessing`, `farming`, `MakeERBFilters`, `ERBFilterBank`, `Syllables_Detection_ERB`, `Syllables_Detection2`, `frequency_continuity`, `Rearrange_signal`, `Check_length_Call` |
| Read-back | `steps/read_segmentation.py` | `read_segmentation_results`, `SEGMENTATION_RESULT_COLUMNS` |
| Basic features | `steps/compute_basic_features.py`, `legacy/features.py` | `ISI_time`, `StartEndFreq`, `StartEndFreq_from_paths`, `_welch_psd` |
| CNN classification | `steps/classification.py`, `legacy/statistics_generator.py` | `Syl_Class_Vec`, `postprocess_predictions`, `CONFIDENCE_THRESHOLD`, `LOW_CONFIDENCE_CLASS` |
| Classifier model | `src/models/model_weights.h6/` (SavedModel: `saved_model.pb` + `variables/`) | BiT-M R50×3 backbone + `Dense(6144→10)` head; weight shard is `.gitignore`d (§5.0) |
| Enrichment | `steps/enrich_columns.py` | `enrich_segmentation_columns`, `SYLLABLE_TYPE_MAP`, `FINAL_COLUMN_ORDER`, `_complexity_numeric` |
| Strain encoding | `utils/io_utils.py`, `steps/extract_features.py` | `STRAIN_1_YEARS`, `strain_from_year`, `_STRAIN_TEXT_TO_NUMERIC` |
| Aggregation / filters | `steps/extract_features.py` | `run_external_aggregated_feature_extraction`, filter names |
| Existing column table | `docs/Running_the_Pipeline.md` | "Segmentation Excel columns" |
| Baseline filters | `docs/BASELINE_DATA_FILTERS.md`, `docs/BASELINE_DATA_MANIFEST.md` | row counts / provenance |

---

*Parameter quick-reference (values as found in code, with derived physical quantities):*
`Fs=250000 (Nyquist 125 kHz) · FrameLength=0.006 s = 1500 smp · frame hop inc=0.7·win=1050 smp=4.2 ms
→ 30% overlap, ~238 frames/s · Hamming window ·
ERB gammatone: numChannels=90, lowFreq=35 kHz→125 kHz, EarQ=9.26449, minBW=24.7, order=1 (4th-order
gammatone / 8th-order IIR) · tonality ratio=0.2·Max · silence_th THRESH=20 · primary peak th=0.9 ·
harmony_th=0.009 · gap-bridge 2–4 frames · MIN_LENGTH=0.01 s · MIN_BETWEEN_CALL=0.02 s ·
MAX_LENGTH=0.3 s (declared, NOT enforced) · preproc LPF 100/120 kHz, BSF notch 50 kHz ·
Start/End-Hz: Welch nperseg=1024 (≈244 Hz res) noverlap=625 (61%), 2000-smp window centred −1000 smp,
peaks >40 kHz, ~3 segments averaged · CNN: HPF 30 kHz order 6, max_time=0.25 s symmetric pad,
STFT n_fft=2048 (122 Hz bins, ~488 Hz true res) hop=128=0.512 ms win=512=2.05 ms (75% overlap) Hamming,
|D|, resize 128×128 bicubic, D−=0.02·mean, 3ch, /255, conf thresh=0.5 → class 10.*

---

## 13. Citing the segmentation tool

> Aharon, C. & Bitton, A. (2026). **USV Segmentation** (v1.0.2) [Software]. Zenodo.
> https://doi.org/10.5281/zenodo.20096810 (CC-BY-4.0).

This Windows build (portable `.exe` + installer) is a frozen packaging of the exact
algorithm documented in §3–§6; it produced the canonical
`segmentation_classification_all_data.xlsx`. The Python source in `src/preprocessing/`
(this repo) is the inspectable reference for the same steps.
