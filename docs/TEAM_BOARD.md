# Team board

Agents: **Astra** (research, `gpt-6-astra` via Codex), **Sol** (code, `gpt-6.1-sol` via Codex), **Claude** (review/integration, Claude Code; also dispatches Astra and Sol). The user decides anything marked HUMAN.

Rules: read this board and the latest file in `handoffs/` before starting. One agent writes at a time. No commits, pushes, resets or branch changes unless the user asks. Every cycle must change data, code or results, or end with a question for the user; a new planning document alone does not complete a cycle. Keep `pilot/annotation_draft_v1/`, `pilot/annotation_draft_v2/` and scorer v1.0.0 unchanged.

| # | Task | Owner | Status | Output |
| --- | --- | --- | --- | --- |
| 1 | Pre-pilot scoring/process review | Claude | DONE 2026-10-14 | `research/claude_review/` |
| 2 | Pre-pilot endpoint spec (secondary numeric endpoint, unit-alias checklist, error taxonomy, English compliance, CMI, consent note) | Astra | DONE 2026-10-14 | `research/pre_pilot_endpoint_spec_v1.md`, `docs/DECISIONS.md`, `docs/THESIS_OUTLINE.md` |
| 3 | Review Astra's spec | Claude | DONE 2026-10-14 | `handoffs/2026-10-14_claude_review_of_astra_spec.md` |
| 4 | Decide which spec proposals to adopt | Claude (delegated by user) | DONE 2026-10-14: lean package adopted, D017–D019 | `docs/DECISIONS.md` |
| 5 | Implement adopted spec as a versioned analysis module, CMI calculator, excluded format-smoke fixtures, tests | Sol, Claude | BUILT 2026-10-14, UNADOPTED (aligned to spec by Claude) | `secondary_analysis/` |
| 6 | Review Sol's code | Claude | DONE 2026-10-14 | `handoffs/2026-10-14_claude_review_of_sol.md` |
| 7 | Evaluation dates and milestone timeline | HUMAN | DONE 2026-10-14: minor-project evaluation November 2026 (exact date TBC); final submission May 2027 | Timeline below |
| 8 | v2 human review (R01, R02, A01) | HUMAN | First returned set (20 Oct) not independent, recorded in `pilot/reviews_v2_returned_2026-10-20/PROVENANCE.md`; round 2 R01 and R02 COMPLETE (independent; 80/90 answer and 83/90 disposition agreement); A01 packet ready (`pilot/reviews_v2_round2/A01_round2_packet.zip`) | reviewer JSONs |
| 9 | FMT2 format test on Colab T4 (36 excluded prompts) | HUMAN runs Colab; Claude analyses | DONE 2026-10-14: 36/36 complete; see `research/fmt2_format_test_2026-10-14/` | `colab_notebooks/model_screening/ModelTest_Qwen3-4B.ipynb` → results ZIP |
| 10 | Confirm prompt v2 (D020): rerun FMT2 notebook (fixtures 0.2.0) on Colab T4 | HUMAN runs Colab; Claude analyses | DONE 2026-10-14: 0/36 format failures; prompt v2 frozen | `research/fmt2_format_test_2026-10-14/` |
| 11 | Align `t4_smoke/protocol.py` instruction with prompt v2 before any training | Sol | IN PROGRESS 2026-10-15 | code + tests |
| 12 | Operation-vocabulary literature check, lexicon, pilot covariate tags, exploratory analysis plan | Astra | IN PROGRESS 2026-10-15 | `research/operation_vocabulary_2026-10-15.md` |
| 13 | CMI aligned to spec tags + heuristic pre-tag sheet CLI | Sol | IN PROGRESS 2026-10-15 | `secondary_analysis/cmi.py` |
| 14 | Minor-project report draft and slide outline from real evidence | Claude | DRAFTED 2026-10-15 (pilot section pending) | `docs/minor_project/` |
| 15 | Deep research: datasets for scale-up, T4 training feasibility, publication venues, tokenization/mechanism controls | Claude subagents | IN PROGRESS 2026-10-15 | `research/claude_deep_research/` |
| 16 | Paper-analysis tool: results ZIP → Markdown/LaTeX tables, figures | Claude subagent, Claude | DONE 2026-10-15: 13 tests; verified on both real FMT2 ZIPs (tables match stored metrics exactly) | `paper_analysis/` |
| 17 | Training label builder: completion-only labels, think-block masking, matched-target check | Sol | DONE 2026-10-15 | `t4_smoke/labels.py` |
| 18 | EACL SRW paper plan and pre-pilot freeze list | Astra | DONE 2026-10-15 | `research/eacl_srw_paper_plan_2026-10-15.md` |
| 19 | Second unchanged model for the pilot: selection research | Claude subagent (Astra-2), GPT cross-check | DONE 2026-10-15: Phi-4-mini-instruct recommended; MIT and EACL dates confirmed by GPT cross-check; load untested | `research/claude_deep_research/second_model_2026-10-15.md` |
| 20 | Phase-2 family authoring kit: guide, JSON template, validator | Claude subagent (Sol-2) | DONE 2026-10-15: 10 tests | `authoring/` |
| 21 | Self-translate and operation-gloss probe: frozen prompts and data builders (no inference) | Claude subagent (Sol-3) | DONE 2026-10-15: 11 tests | `exploratory/` |
| 22 | Fix 5 bugs from GPT cross-review (`handoffs/2026-10-15c_sol2_gpt_review.md`): nested-ZIP memory bound, -ST ID collision, output-name collision, zlib error, CSV header check | Claude subagent | DONE 2026-10-15: all 5 fixed with regression tests | `paper_analysis/`, `exploratory/` |
| 23 | Lexicon confirmation by the user (bilingual) | HUMAN | DONE 2026-10-15: 24/25 reviewed and endorsed by the user (13–25 AI-assisted drafting); `anupat` unconfirmed | `research/lexicon_confirmation_user_2026-10-15.md` |
| 24 | Phi-4-mini T4 load + format test (36 excluded prompts) | HUMAN runs Colab; Claude analyses | DONE 2026-10-15: loads, but inline FINAL and R repetition collapse; excluded from the pilot (D025) | `research/fmt2_phi4mini_2026-10-15/` |
| 25 | Granite-3.3-2B T4 load + format test (36 excluded prompts) | HUMAN runs Colab; Claude analyses | DONE 2026-10-15: 0/36 strict (commentary after FINAL); pilot stays single-backbone (D026) | `research/fmt2_granite2b_2026-10-15/` |
| 26 | Automated verification pipeline: blind solver tasks, Claude/GPT answer comparison, flags, review sheet | Sol | DONE 2026-10-15: 23 tests | `autoverify/` |
| 27 | Checker validation protocol, drafter split, second-annotator plan | Astra | DONE 2026-10-15 | `research/autoverify_protocol_2026-10-15.md` |
| 28 | Draft 70 Pilot-B families (operation-word balanced) | Claude subagent | DONE 2026-10-15: 70 families, checker clean | `pilot_b/` |
| 29 | Draft 140 FINAL_TEST + DEV families (GPT) and 160 TRAIN families (2 Claude subagents) | GPT drafter, Claude subagents | TRAIN 160/160 done; FINAL_TEST 84/100 and DEV 34/40 (GPT paused by Codex usage limit until 18:48) | `phase2/` |
| 30 | FMT2 screening runs: Qwen3-1.7B, Qwen3-8B, Gemma-3-4B, Llama-3.2-3B (≤3/36 invalid to join the pilot) | HUMAN runs Colab; Claude analyses | 1.7B FAIL (D029); 8B PASS, joins pilot (D030); Gemma excluded, CUDA failure under FP16 (D031); Llama PASS, joins pilot (D032) | `colab_notebooks/model_screening/` |
| 31 | Pilot-B blind solve + comparison: Claude 210/210 and GPT 210/210 match gold; 2/70 families flagged (PB013, PB051) | Claude + GPT solvers | DONE 2026-10-15 | `autoverify_runs/pilot_b/` |
| 32 | **Human review of all 70 Pilot-B families** | HUMAN | DONE 2026-10-16: 57 ACCEPT, 13 REVISE applied as v2; blind re-solve 15/15 both solvers; Pilot-B FROZEN (`pilot_b/FROZEN.md`) | `autoverify_runs/pilot_b/verification/review_sheet_FULL.csv` |
| 33 | Phase-2 blind solve: Claude 900/900, GPT 897/900 match gold (TRA072 GPT error); strict flags 10 FINAL_TEST + 6 TRAIN/DEV | Claude + GPT solvers | DONE 2026-10-16 | `autoverify_runs/phase2/verification/` |
| 34 | **Human review: FINAL_TEST (100, full) and TRAIN+DEV (flagged + 20% sample)** | HUMAN | FINAL_TEST and TRAIN+DEV DONE and FROZEN 2026-10-16 (`phase2/*_FROZEN.md`) | `review_FINAL_TEST.csv`, `review_TRAIN_DEV.csv` |
| 35 | EACL SRW paper draft (pilot results as placeholders; [VERIFY] items listed) | Claude subagent | DRAFTED 2026-10-16 | `paper/eacl_srw_draft.md` |
| 36 | **Pilot-B evaluation runs: Qwen3-4B, Qwen3-8B, Llama-3.2-3B (210 prompts each)** | HUMAN runs Colab; Claude analyses | ALL DONE 2026-10-20: see `results/pilot_b/SUMMARY.md` | `results/pilot_b/` |

## Timeline (proposed by Claude 2026-10-14; exact November date TBC by the user)

Target for the November minor evaluation: a human-reviewed, frozen 30-family pilot and a complete unchanged-model Test 1 run with analysis. Training is not needed for November.

| By | Milestone | Owner |
| --- | --- | --- |
| 20 Oct | Endpoint spec reviewed and decisions made (tasks 2–4) | Astra, Claude, HUMAN |
| 27 Oct | Secondary endpoint, CMI and excluded format fixtures implemented; format-fixture T4 run | Sol, HUMAN runs Colab |
| 31 Oct | R01/R02 reviews and A01 adjudication returned; data and splits frozen | HUMAN |
| 7 Nov | Reviewed pilot run on T4, all outputs audited, analysis written | HUMAN runs Colab, Claude, Astra |
| Before evaluation | Minor-project presentation/report from pilot results | All |
| Dec–Jan | Training feasibility smoke; scale data beyond 30 families | Sol, Astra, HUMAN |
| Feb–Mar | E+E / E+R / E+C training and held-out evaluation | All |
| Apr | Analysis and thesis writing | All |
| May 2027 | Final submission | HUMAN |

Slip rule: if human review is not back by 31 Oct, present the minor evaluation as design + software + format-fixture evidence, clearly labelled, rather than delaying the human gate.
