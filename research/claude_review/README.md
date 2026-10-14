# Claude review v1: pre-pilot scoring and process risks

Dated 14 October 2026. Reviewer: Claude, an AI coworker alongside Astra (research) and Sol (code). **This is AI review plus model-free software probes. It is not human validation, adjudication, or an experimental result.** No model inference, training or paid API was run. No other repository file was changed.

Status read: `README.md` and `docs/PROJECT_STATUS.md` (11 October). No `AGENTS.md` exists in the repository. Older planning documents were treated as historical.

## What was checked

| Check | Result | Kind of evidence |
| --- | --- | --- |
| `pilot/scripts` tests | 3 tests OK | Software verification |
| `t4_smoke` tests | 4 tests OK | Software verification |
| `test1_pilot/tests` | 22 tests OK; local demo export ran | Software verification (fake backend) |
| `annotation_draft_v1` and `v2` verifiers | Ran to completion; working tree unchanged afterwards | Software verification |
| Code read | `scorer_v1.py`, `engine.py`, `hf_backend.py`, `report.py` | AI review |
| Scorer probe | `scorer_probe.py` → `scorer_probe_output.txt` | Synthetic strings applied to each DRAFT family's gold; model-free |

The probe never runs a model and prints no gold values. A rejection means the format is rejected. It does not mean the arithmetic was wrong.

## Main finding: the strict endpoint may measure format compliance more than mathematics

The protocol and scorer v1.0.0 are frozen, and the review below does **not** propose weakening them. The concern is that the pilot gets one run against a frozen scorer. Several plausible ways of writing a *correct* answer score as invalid. Some of these are more likely in R/C than in E, which would bias the E/R/C comparison the pilot exists to measure.

Probe results (`scorer_probe_output.txt`):

| Correct-answer variant | Accepted | Reason |
| --- | --- | --- |
| `FINAL: <v> <unit>` (instructed format) | 30/30 | — |
| `**FINAL:** <v>` (Markdown bold marker) | 0/30 | `final_not_terminal_line` |
| `FINAL: **<v>**`, `\boxed{<v>}`, `$<v>$` | 0/30 each | `invalid_number` |
| Any line after the FINAL line | 0/30 | `final_not_terminal_line` |
| "I cannot …" anywhere in the reasoning | 0/30 | `refusal` (regex matches the whole response) |
| `FINAL: Rs. <v>` / `Rs <v>` (6 INR families) | 0/6 | `invalid_number`: `Rs.` is accepted only as a suffix, despite being an alias |
| `FINAL: ₹<v>/-` | 0/6 | `invalid_answer` |
| `FINAL: x = <v>` (3 dimensionless algebra families) | 0/3 | `invalid_number` |
| Hindi unit words `kilo`, `minat`, `litar`, `mitar`, `kilomitar` | 0/6 total | `invalid_unit` |

Notes on how likely these are:

- The returned T4 smoke outputs ended with a terminal `FINAL:` line and failed only on units. The Markdown/LaTeX cases are therefore **untested risks, not observed failures**. Qwen-family models often use Markdown and `\boxed{}` in mathematical answers, but this has not been measured under our prompt.
- The alias lists are uneven across units. Count nouns have romanized-Hindi aliases (`kanche`, `kitaab`, `ladkiyan`). `h` has `ghante`, but `minute`, `kg`, `L`, `m` and `km` have none. The smoke run already showed one R explanation drifting into Hindi. If the model echoes the question's unit vocabulary, R/C outputs will hit `invalid_unit` more often than E. That is a form-dependent penalty.
- The packet threshold says more than 3/90 invalid outputs requires protocol revision. The smoke run was 6/6 invalid. As things stand, there is a real chance the first reviewed pilot run gets spent on format diagnosis.

### Recommended decisions (all must happen **before** the reviewed pilot generation, while revision is still clean)

These are proposals for the humans to decide on, then for Sol to implement where needed. None is applied here.

1. **A01 adjudication of gold/units (human):** extend the existing gold/unit check to the alias lists. Decide whether `Rs.`/`Rs` prefixes and common romanized unit words (`kilo`, `minat`, `litar`, …) count as valid units. Apply this consistently across E/R/C families. This is a gold-metadata decision inside the existing review step, not a scorer change. Any change needs a new data version per the README.
2. **Pre-specify a secondary endpoint now (Astra to specify, Sol to implement as a separately versioned analysis):** "extracted numeric value equals gold", computed alongside the unchanged strict endpoint and reported per form with its invalid-reason breakdown. If this is defined after the outputs are seen, it becomes a post-hoc choice, which the smoke audit already had to label "POST-HOC SOFTWARE DIAGNOSTIC". Defined now, it is a legitimate secondary measure, and the strict primary endpoint stays intact.
3. **Measure format compliance on excluded fixtures first (Sol):** add new, excluded format-smoke fixtures covering currency, algebra (`x = …`), ratio and metric-unit items in E/R/C, and run them through the existing GPU smoke notebook. This gives an empirical format-failure rate without exposing pilot items. If the rate is high, adopt a prompt revision (for example, forbidding Markdown/LaTeX on the FINAL line) as a new `prompt_version` **before** the pilot. That is within the protocol's "new explicitly versioned protocol" rule.
4. **Refusal detection (Astra/Sol, versioned):** the `refusal` regex matching anywhere in the response is a scoring rule, so it is not changed here. Its false-positive rate should be checked on the fixture run above, and any change should become scorer v1.1 adopted before the pilot.
5. **English-output compliance is not implemented:** `PROJECT_STATUS.md` says to diagnose it separately, but `report.py` computes no such measure. Pre-specify a simple per-form rate, even manual tagging in the audit CSV, so R/C language drift is reported rather than noticed anecdotally.

## Correction to Claude's earlier chat suggestions

Two suggestions I made earlier in chat need correcting after reading the protocol:

- **"Run the model on the 30 drafts now" would violate the protocol.** The README forbids changing questions after consulting pilot model answers before freeze. Running drafts while v2 human review is in progress risks contaminating that review. Recommendation 3 above replaces it: measure format behavior on *excluded* fixtures only.
- **Inter-annotator agreement is already planned.** `pilot_review_packet.md` line 34 specifies raw agreement, adjudication counts and rating distributions. Cohen's kappa per rating dimension could be added as a descriptive extra, with the packet's caution about 30 families.

## Other gaps (lower priority)

- **No timeline.** `pilot_review_packet.md` records "no fixed deadline", but a BTech project has evaluation dates. Without them, the Astra/Sol loop has no stopping rule. Most recent cycles produced design documents, and there is still no human-accepted item or reviewed run. Proposal: record the university's actual milestone dates in `docs/PROJECT_STATUS.md` (owner: user) and order the gates against them.
- **Code-mixing is not quantified.** No code-mixing index or switch-point count exists for C renderings. Computing a descriptive CMI per C (and R) text is model-free and cheap, and it would let the report characterize "C" beyond the policy definition. `draft_register.json` already has null slots for unannotated spans.
- **No pre-specified error taxonomy.** Freezing manual-audit `category` values (misread quantity, wrong operation, arithmetic slip, unit error, format-only, language drift) before the pilot would make the audit CSV analyzable and support a strong report chapter.
- **No reviewer consent/credit note.** Human reviewers are about to contribute. A short consent and acknowledgement note is cheap and expected in a thesis.
- **Single backbone.** This is already listed as optional. A second unchanged model on the same frozen pilot data (inference only) would strengthen Test 1 descriptively. It needs its own versioned config, because `validate_config` intentionally accepts Qwen3-4B only.

## Things that look sound

Fresh context per rendering, a seeded order, an atomic attempt journal, refusal to resume on code/data/environment changes, no retry of generated outputs, no truncation, preserved original scores with versioned manual overlays, family-level paired bootstrap, and suppression of headline numbers on incomplete runs. The care around reviewer blinding and exposure disclosure is unusually thorough.

## Files changed

- `research/claude_review/README.md` (this file)
- `research/claude_review/scorer_probe.py` (model-free probe; imports `pilot/scripts/scorer.py` read-only)
- `research/claude_review/scorer_probe_output.txt` (probe output)

No other files were created, modified, committed or pushed.
