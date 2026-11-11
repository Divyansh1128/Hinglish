# Hinglish Mathematical Reasoning in LLMs

A Delhi Technological University BTech research project on mathematical reasoning across English (E), Hindi written in Roman script (R), and Roman-script Hindi–English code mixing (C).

**Current status: 11 November 2026.** Both unchanged-model pilot cohorts, T4 training feasibility, nine controlled QLoRA training runs and the final evaluation are complete. The final training result is negative: **E+C minus E+R accuracy on C = −4.33 percentage points [−8.00, −0.67]**, under the frozen strict endpoint. The pre-registered label is **Harm**, specific to this recipe and dataset; it is not a universal claim about Hinglish training.

Start with [current project status](docs/PROJECT_STATUS.md) and the [next-step plan](docs/NEXT_STEPS_2026-11-11.md). The [decision log](docs/DECISIONS.md) records adopted decisions. Older dated documents and introductory guides describe earlier stages and are not the current status.

## Completed experiments

| Study | Scope | Outcome |
| --- | --- | --- |
| Excluded format/model screening | Seven candidate models; fixed inclusion rule | Qwen3-4B, Qwen3-8B and Llama-3.2-3B qualified |
| Pilot-B | 70 matched E/R/C families; three models | R lowest for all three; Qwen E/C aggregate strict accuracy equal |
| Original pilot | 24 accepted families from 30 candidates; three models | Same R-lowest direction; Qwen near ceiling |
| T4 training smoke | Three arms, checkpoint reload and longer engineering probe | Passed; memorisation warning informed the later schedule before main training |
| Phase-2 training | 160 TRAIN families; E+E/E+R/E+C × seeds 11/22/33 | Nine valid runs, 60 updates each; adapters frozen |
| Phase-2 FINAL_TEST | 100 families × E/R/C × ten checkpoints | All 3,000 outputs complete; E+C below E+R on C; all trained arms below unchanged model |
| Phase-2 failure audit | All 331 incorrect C outputs from E+R/E+C | Human labels recorded for all rows; the E+C deficit is not explained away by format-only errors |

The pilots are reported separately because their review procedures and C definitions differ. Equal observed accuracy is not evidence of equivalence. The Phase-2 bootstrap resamples families, retaining seed pairing; its interval is conditional on the trained checkpoints and does not cover training-seed variance. No training, prompt or scorer changes were made in response to final-test outcomes.

## Evidence and report navigation

- [Pilot-B results](results/pilot_b/SUMMARY.md) and [original-pilot results](results/pilot_original/SUMMARY.md).
- [Training smoke](results/training_smoke/README.md), [training records](results/phase2/train/README.md), and [final analysis](results/phase2/final_test/phase2_analysis.md).
- [Independent final-result verification](handoffs/2026-11-10_sol_verify_final_test.md) and [human failure-audit summary](results/phase2/audit/final_audit_summary.json).
- [Pre-registration](phase2/PREREGISTRATION.md), [implementation freeze](phase2/IMPLEMENTATION_MANIFEST.md), and [adapter freeze](phase2/ADAPTERS_FROZEN.md).
- [Paper source](paper/latex/main.tex), [paper PDF](paper/latex/main.pdf), [report source](report/final_report.tex), and [report PDF](report/final_report.pdf). Check generated PDFs against the latest sources before sharing.
- [Novelty refresh](research/novelty_refresh_2026-10-27.md): prior work already reports R below C; position this work as a scoring-aware audit and controlled training follow-up, not discovery of that ordering.

The decision log records an EACL 2027 SRW **pre-submission mentorship** submission on 26 October (OpenReview #12), not acceptance or final-track submission. Publication dates remain recorded planning dates until checked against the current call.

## Data and review provenance

Pilot-B has full-family review by one bilingual reviewer. The original cohort has two independent human mathematical solves, language review by one human plus adjudicator, and excludes unverified AI-prefilled judgments from human-review claims. Phase-2 FINAL_TEST received full-family review; TRAIN/DEV received flagged and sample-based review. AI drafting and solver checks do not replace human validation. See the freeze documents and D033–D038 for details.

## Software and reproducibility

- `test1_pilot/`: original self-contained Colab evaluation notebook, helpers, fixtures and portable bundle.
- `colab_notebooks/`: model screening, pilot evaluation and Phase-2 notebooks. Completed experiments should not be casually rerun or tuned on FINAL_TEST.
- `t4_smoke/`, `phase2/`, `phase2_analysis/`: training engineering, frozen study records and registered analysis.
- `secondary_analysis/`: separately versioned diagnostic endpoints; strict scorer v1.0.0 stays primary.
- `analysis/`: explicitly exploratory post-hoc analyses, which do not replace the registered result.
- `pilot/`, `pilot_b/`, `authoring/`, `autoverify/`: historical review packets and dataset preparation.

A read-only consistency check validates the final archives and published strict/numeric counts without modifying results:

```sh
python3 -B analysis/phase2_exploratory/error_analysis.py --check
```

It passed on 11 November: ten complete runs, 3,000 outputs and all 60 checkpoint-by-form endpoint counts. This is a software consistency check, not a new experiment or independent human review.

Code: MIT ([LICENSE](LICENSE)). Data: CC BY 4.0 ([DATA_LICENSE.md](DATA_LICENSE.md)). Preserve frozen packets, original generations, scores, reviewer provenance and exclusions. Do not commit credentials or new personal reviewer material.
