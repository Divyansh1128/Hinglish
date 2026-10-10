# Hinglish Mathematical Reasoning in LLMs

A Delhi Technological University BTech research project investigating how language form affects mathematical reasoning, and whether code-mixed training offers benefits beyond Romanized-Hindi exposure.

**Current status, 10 October 2026:** pilot software implemented; fake-backend software checks and a short real-Qwen T4 inference smoke completed; 30 AI-authored draft families prepared for human review. **No reviewed research pilot, fine-tuning, confirmatory experiment, or demonstrated training benefit has been completed.**

Start with the [teammate guide PDF](output/pdf/Hinglish_Math_Teammate_Guide.pdf), then [current progress and next steps](docs/PROJECT_STATUS.md). Older planning documents are retained as dated proposals; their pending/completed statements must be read with this current status.

For continuing research in a new assistant session, use the [Astra research master prompt](docs/ASTRA_RESEARCH_MASTER_PROMPT.md), which includes verified achievements, open questions and bounded subagent tasks.

## What E, R and C mean

| Form | Input language |
| --- | --- |
| E | English |
| R | Hindi phrasing written in Roman script, under a borrowing policy |
| C | Roman-script Hindi-English code mixing, with productive English clauses or relations |

Test 1 evaluates mathematically equivalent E/R/C questions using one unchanged checkpoint, one fixed English instruction and one scorer. A fresh context is used for every question. The intended reviewed pilot has 30 independent mathematical families, each with three renderings: **90 prompts represent 30 families, not 90 independent problems.**

The later training comparison is **E+E versus E+R versus E+C**, matching mathematical content, English solution supervision and example exposure. It remains a proposed experiment. Matching exposure and updates does not necessarily match input tokens or runtime; those must be measured. Existing bilingual/code-mixed mathematics studies mean publication novelty cannot be assumed; see the [updated closest-work matrix](research/astra_closest_work_update_2026-10-10.md).

## Run the notebooks

- [Main Test 1 Colab notebook](test1_pilot/Hinglish_Math_Test1_Pilot_Colab.ipynb): self-contained; upload this .ipynb to Colab. Default fake-backend demo needs no GPU. Reviewed mode requires genuinely accepted data and a split audit; it rejects drafts.
- [Qwen GPU smoke notebook](test1_pilot/Hinglish_Math_Qwen_GPU_Smoke_Colab.ipynb): short technical inference check on excluded synthetic fixtures. It does not measure research performance or train the model.
- [Portable software bundle](test1_pilot/Hinglish_Test1_Portable.zip): editable code, tests and notebook. It is optional when running the self-contained notebook.
- [Exact Colab instructions](test1_pilot/README.md), [input contract](test1_pilot/DATA_CONTRACT.md), and [verification record](test1_pilot/VERIFICATION.md).

Primary inference condition: Qwen/Qwen3-4B, NF4 with double quantization, FP16 computation, SDPA math backend, non-thinking greedy decoding, batch 1 and 1,024 output tokens. Every run records immutable model/tokenizer revisions, configuration, environment, hardware, outputs and failures. The real T4 smoke establishes short-input inference feasibility only. Full-pilot and training feasibility are still pending.

## Human review comes next

The [annotation package](pilot/annotation_draft_v1/README.md) has five draft families in each of six topics. All texts remain AI_DRAFT and all acceptance decisions are pending.

1. Assign two independent Hindi-English bilingual reviewers to R01 and R02, and a separate adjudicator to A01. These labels are pseudonyms, not completed reviews.
2. Give each reviewer only their own [R01 ZIP](pilot/annotation_draft_v1/R01_review_packet.zip) or [R02 ZIP](pilot/annotation_draft_v1/R02_review_packet.zip). They solve randomized stage1 questions before consulting reference answers, save the JSON, and import it into stage2 to compare the triplets and rate language quality.
3. The coordinator collects both independent submissions before revealing the [A01 key and decision packet](pilot/annotation_draft_v1/A01_adjudication_packet.zip). Record repairs, disagreements, exact gold/unit decisions, family relationships and split exclusions; repaired texts require new versions and independent re-review.
4. Freeze accepted data, review hashes, borrowing policy and splits; then run the unchanged-model pilot and inspect all raw outputs.

**Reviewers:** the coordinator folder, A01 key and historical illustrative problems contain proposed answers. Avoid reading those before your independent solves. If you have already seen a proposed answer, report that exposure to the coordinator; do not attest otherwise. GitHub access is not a blind-review firewall. Automated checks cannot certify mathematical equivalence, naturalness or family independence.

## Repository map

| Location | Contents and status |
| --- | --- |
| `research/` | Literature comparison, design decisions, returned-demo audits and annotation handoff |
| `pilot_review_packet.md` | Historical governing pilot/review protocol; proposed training-smoke section remains unexecuted |
| `pilot/annotation_draft_v1/` | Thirty draft families, reviewer forms, key, proposed split manifest and verification |
| `pilot/scripts/` | Original exact numeric scorer and tests |
| `test1_pilot/` | Runnable Test 1 notebook, helper modules, fixtures, templates, tests and versioned archives |
| `t4_smoke/` | Preparatory training-smoke validation/protocol code; no training run claimed |
| `synopsis/faculty_synopsis.md` | Faculty-facing proposal; not an experimental report |
| `docs/` | Teammate guide source and current status |
| `output/pdf/` | Shareable teammate guide |

Machine caches, Colab runtime directories, credentials, raw conversation transcripts, returned personal reviews and older personalized submission documents are excluded from version control. The project has no declared software or dataset release license yet; do not imply one from AI authorship. Record permissions and introduced sources before any public dataset release.

## Local software checks

From the repository root, without CUDA dependencies:

```sh
python3 -B -m unittest discover -s pilot/scripts -p 'test_*.py' -v
python3 -B -m unittest discover -s t4_smoke -p 'test_*.py' -v
PYTHONPATH=test1_pilot python3 -B -m unittest discover -s test1_pilot/tests -p 'test_*.py' -v
python3 -B pilot/annotation_draft_v1/verify_packet.py
```

The annotation verifier also uses Node.js for JavaScript syntax and simulated import/export checks. See each package README for builders and dependencies. These are software checks; they do not establish human approval or full GPU feasibility. Do not rebuild draft distributions over returned human edits. For actual research runs, return one results ZIP plus the executed notebook, preserving all original automatic scores and any separately versioned manual audit overlays.

## Current research decisions

The [consolidated experiment specification](research/astra_experiment_spec_v1.md) preserves the three-arm comparison and separates requirements from unapproved recommendations. Read the [statistical planning analysis](research/astra_validity_and_power_v1.md) and [review-readiness audit](research/astra_review_readiness_v1.md) before preparing accepted inputs. Planning calculations are synthetic assumptions, not model results. Reviewer exposure remains unconfirmed; PIL026-C wording and candidate family relationships require human resolution. The next gate remains human acceptance followed by the unchanged-model pilot.
