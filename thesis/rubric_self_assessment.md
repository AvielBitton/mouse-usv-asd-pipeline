# Rubric self-assessment

Mapping the thesis to the HIT grading criteria (`hit/exam/*.docx`). This is the authors' self-check, not an official grade.

## Examiner evaluation (/100)
| Criterion | Weight | How addressed |
|---|---|---|
| Spec / research question + work plan | 10 | Ch.1 states the evolved research questions (RQ1–RQ3 + engineering); Ch.4 the methodology; Appendix A.2 the work plan/timeline. |
| Product meets design + answers research questions | 50 | Ch.5 answers each RQ with sourced results (best-in-scenario table); Ch.6 interprets; Ch.7 documents the delivered, reproducible system. |
| Level of final work incl. technical writing | 30 | Formal register, defined terms, consistent notation, 22 publication-grade figures, IEEE references, calibrated claims. |
| Bonus (originality / publication potential) | +10 | Reproducibility + data-integrity contribution; honest leakage-aware evaluation; a published software artifact (Zenodo). |

## Supervisor evaluation (/100)
| Criterion | Weight | How addressed |
|---|---|---|
| Spec / research question + work plan | 10 | As above. |
| Problem identification, autonomy, initiative, originality | 20 | Ch.7 + Ch.3: rebuilt a broken pipeline, discovered & corrected a data error, built a GUI tool; inherited-vs-new inventory (Table 5). |
| Schedule adherence + interim report | 10 | Timeline (Fig. of Appendix A.2); the project built on the interim report. |
| Product meets design + answers RQs | 20 | Ch.5–6. |
| Level of final work incl. technical writing | 30 | As above. |

## Defence (/100)
| Criterion | Weight | Note |
|---|---|---|
| Presentation quality | 50 | The signature pipeline figure (Fig. 1), the reported-vs-corrected figure (Fig. 6), and the headline dumbbell (Fig. 11) are designed to carry the talk. |
| Answering examiner questions | 50 | The limitations chapter and gaps list anticipate the likely questions (strain confound, per-subject metric, feature ceiling). |

## Definition-of-done checklist
- [x] Every rubric criterion addressed.
- [x] Every quantitative claim sourced (integrity pass: 42 result cells + dataset tokens verified; traceability table).
- [x] No invented numbers; gaps explicitly flagged (`GAPS.md`).
- [x] Structure follows the bilingual exemplar (title page, תקציר + Abstract, TOC, List of Figures, Abbreviations, chapters, References, Appendices).
- [x] All 22 figures generated from real data/diagrams, captioned, numbered, and referenced in text.
- [x] Interim-vs-repo and roles conflicts surfaced in-text, not hidden.
- [x] Note: final-grade weighting formula is not specified in the rubric docs (admin gap #13); a bonus draft manuscript is optional (gap #12).
