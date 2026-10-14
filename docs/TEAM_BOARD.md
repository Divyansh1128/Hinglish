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
| 8 | v2 human review (R01, R02, A01) | HUMAN | IN PROGRESS (packets distributed) | reviewer JSONs |
| 9 | FMT2 format test on Colab T4 (36 excluded prompts) | HUMAN runs Colab; Claude analyses | READY 2026-10-14 | `secondary_analysis/Hinglish_FMT2_Format_Test_Colab.ipynb` → results ZIP |

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
