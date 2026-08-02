# Defense presentation — Analysis of USVs for Autism Detection

M.Sc. defense deck for **Chen Aharon & Aviel Bitton** (advisor Dr. Dror Lederman, HIT).
Slides in English, speaker notes in Hebrew. Built as a single self-contained HTML file
(offline, fonts + figures embedded as base64) that renders like a "Claude Design" deck and
exports to clean 16:9 PDF.

## Deliverables (this folder)

| File | What it is |
|---|---|
| `defense_deck_v2.html` | **The deck.** Open in Chrome, press **F** for fullscreen. Self-contained/offline. |
| `defense_deck.pdf` | The deck as a 30-page 16:9 PDF (one slide per page). |
| `defense_notes_handout.html` / `.pdf` | Per-slide **Hebrew speaker notes** (what to say, transitions, who presents, time budget). Print this / keep on a tablet — it is **not** projected. |

## Presenting (keyboard)

- **→ / Space / PageDown** — next (advances staged reveals within a slide, then next slide)
- **← / PageUp** — back · **Home / End** — first / last
- **N** — toggle the on-screen Hebrew notes panel (for rehearsal)
- **F** — fullscreen

## Structure — 24 talk slides (~30 min) + 6 Q&A appendix slides

Act 1 Why (Aviel): title · personal motivation · the problem · why USVs · calls have shape
Act 2 Questions/Engineering (Chen): research questions · inherited prototype · the process timeline · single source of truth · the segmentation app
Act 3 Data/Method (Chen→Aviel): the pipeline · the data · the models & TabPFN · **two-questions evaluation**
Act 4 Results (Aviel): TabPFN headline · the 0.829 decomposed · ROC · the precision wall · **sequence-NN attempt (×2)** · the strain confound
Act 5 Close (both): conclusions · future work · thank you
Appendix (Q&A): master table · **feature-importance + mother-genotype confound** · confusion matrices · design matrix · best-per-scenario · threshold tuning

## Regenerate after edits

Edit the deck in `build/deck_template.html` (plain HTML; figures are `{{IMG:...}}` tokens,
fonts are `{{FONT:...}}` tokens — filled at build time from `build/assets` and `build/fonts`).

```bash
bash build/render_pdf.sh          # rebuilds HTML + both PDFs (needs google-chrome)
# or just the HTML:
python3 build/build_deck.py
```

PDF is produced with Chrome headless — `@page{size:1280px 720px}` gives exact 16:9 and
backgrounds print automatically. Verified on Chrome 143.

## Notes for the presenters

- **Timing is tight** (~1.4 min/slide). Rehearse to ~28 min. Slides **17 (ROC)** and
  **20 (sequence result)** are the easiest to cut / merge if you run long.
- **The mother-genotype question is the likeliest hard question.** The book's Figure 21
  shows *Mother genotype* dominating gain importance, because it is predictive by the
  breeding cross (a WT dam yields only WT pups). Appendix slide **A2** frames this honestly:
  it is a metadata confound; the genuine acoustic signal is what the subject-independent,
  ROC-AUC, and precision-wall results reflect. A metadata-free ablation is stated as future work.
- Fig24 (the app screenshot) had a personal Windows path redacted to `…\USV_Recordings`.
