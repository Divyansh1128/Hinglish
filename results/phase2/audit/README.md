# Phase-2 C-failure audit (descriptive; GPT pre-tags complete)

10 November 2026. Implements the output-audit reporting requirement in `phase2/PREREGISTRATION.md` §12 and Amendment 1 item 17, using the frozen Pilot-B rubric. **All labels are descriptive AI pre-tags, never overwriting strict scores, numeric endpoints or the pre-registered decision label.** No mechanism claims are made.

- **Packet complete:** `phase2_outputs_for_audit.jsonl` contains every strict-incorrect C-form output of E+R (`ER`) and E+C (`EC`), seeds 11, 22 and 33: **159 + 172 = 331**. Per-run failure counts: ER-s11 56, ER-s22 53, ER-s33 50; EC-s11 59, EC-s22 54, EC-s33 59. No strict-correct outputs or other arms/forms are included.
- **GPT tags complete:** `gpt_tags.jsonl`, 331/331 rows, using the seven-field Pilot-B tag schema. GPT read every output individually in a shuffled, numbered review view with arm/seed labels hidden; no other tagger's labels were consulted. Repeated outputs were each reviewed, with shared reason wording for the same visible issue. A temporary serialization helper recorded the chosen labels; no heuristic classifier assigned them.
- **Claude Opus tags pending:** an independent pass over all 331 rows, blind to GPT's tags, is still required. Agreement has not been calculated.
- **Human check done:** a 65-row human check (see "Final audit" below) by team members Ayush Kumar Singh and Divyanshu Mishra (project authors); the original AI tags are retained alongside the final labels.
- **Deviation, being closed:** Amendment 1 item 17 requires a human check of **all 331** audited outputs. 266 remain. `build_remaining_sheet.py` writes them as `human_check_remaining_part1.csv` and `human_check_remaining_part2.csv` (133 rows each, interleaved so each checker sees both arms). When they return, `finalize.py` must take the human label for every row.

Build the packet from any working directory by running `python3 -B /absolute/path/to/results/phase2/audit/build_packet.py`. From the repository root, run `python3 -B results/phase2/audit/build_packet.py`. The stdlib-only builder reads `results/phase2/final_test/Phase2_FinalTest_results.zip` and writes only the packet. It requires complete 300-generation coverage per run, unique IDs, exact input/journal joins, numeric-diagnostic journal hashes and agreement across duplicate diagnostic exports, and the expected failure counts. It never rescores an output. Rebuilding the packet does not regenerate GPT tags.

The packet preserves all Pilot-B fields, plus `arm`, `seed`, `source_rendering_id`, full `gold_metadata`, the stored `numeric_literal_v1` result in `numeric`, and attempt/run IDs. The unique audit `rendering_id` is `<arm>-s<seed>:<source_rendering_id>` so the unchanged Pilot-B tag schema can join repeated renderings across six checkpoints. Original rendering IDs, question text, responses, gold, strict correctness, invalid reasons and truncation flags are preserved. The archive contains v1 diagnostics; no v2 result is invented or recomputed for this packet. Numeric equality alone does not establish `format_only`.

Primary-category GPT counts, in the rubric's precedence order:

| Category | ER | EC | Total |
|---|---:|---:|---:|
| truncated | 0 | 0 | 0 |
| refusal | 0 | 0 | 0 |
| unresolved | 0 | 2 | 2 |
| misread_quantity | 27 | 29 | 56 |
| wrong_relation_operation | 71 | 83 | 154 |
| arithmetic_slip | 8 | 10 | 18 |
| unit_error | 9 | 11 | 20 |
| format_only | 44 | 37 | 81 |
| language_drift | 0 | 0 | 0 |
| no_error | 0 | 0 | 0 |
| **Audited failures** | **159** | **172** | **331** |

Counts over **all C generations**, as required by the registration (100 families × three seeds per arm):

| Descriptive classification | ER / 300 | EC / 300 | Combined / 600 |
|---|---:|---:|---:|
| Stored strict-correct, outside failure audit | 141 (47.00%) | 128 (42.67%) | 269 (44.83%) |
| Failure tagged format_only | 44 (14.67%) | 37 (12.33%) | 81 (13.50%) |
| Failure with identified substantive issue | 115 (38.33%) | 133 (44.33%) | 248 (41.33%) |
| Failure tagged unresolved | 0 (0.00%) | 2 (0.67%) | 2 (0.33%) |

Within the failure-only packet, format-only is 81/331 (24.47%), identified substantive issues 248/331 (74.92%), and unresolved 2/331 (0.60%). Substantive here comprises `misread_quantity`, `wrong_relation_operation`, `arithmetic_slip` and `unit_error`; unresolved is kept separate. These pooled counts describe repeated family/seed records and do not treat them as independent observations or define a replacement accuracy endpoint.

Judgment details for human review: an appropriate count noun rejected by unitless or incomplete-alias metadata can be `format_only`, as can correct colon ratios, unsupported explanatory final-line qualifiers, repeated incidental `Final:` labels, and percent notation rejected by the strict convention. A dimensional unit attached to a dimensionless fraction, numerator or page number is `unit_error`. A visible mathematical error takes precedence even if the positive final answer matches gold: for example ER-s22:FT099-C has the correct positive quadratic root but an incorrect negative root, so its primary tag is `arithmetic_slip`. The two `unresolved` rows have unexplained final values incompatible with their visible reasoning. These remain GPT judgments pending independent tagging and full human checking; gold and scoring metadata are unchanged.

Failure-only English status: compliant 96, non_english 4, no_explanation 231, uncertain 0. Bare calculations and equation labels do not supply an English explanatory proposition. All 331 outputs are nontruncated; the 269 strict-correct outputs were not audited for language, so these are not whole-evaluation language-compliance rates. Additional-category counts (overlapping, separate from primary counts): wrong_relation_operation 15, arithmetic_slip 22, unit_error 27, language_drift 4.

Validation: 331 unique packet IDs and exactly one GPT tag per ID; exact seven-field schema; valid category/status enums and precedence; every evidence quote is an exact output substring of at most 25 whitespace-delimited words; packet rebuild is byte-identical. Only the five files in this audit directory were created for this task; no commit was made.

Source/archive SHA-256: `fb4a71ccb22d8d4f274ec3c94c0b7455f870aebe7fcc673d18e47632a0024f9a`.
Packet SHA-256: `28478c76228273225b67cf1783bf1b8fcf4bf88f085a19868b473eb1187bda36`.
GPT tags SHA-256: `562773a999848b2327809f68c6f0b3227a0ad549cacac207533f0d92187a886b`.

## Claude tags and agreement (10 November 2026)
Tagger A = Claude (`claude_tags.jsonl`, an Opus subagent blind to GPT's tags). Tagger B = GPT (`gpt_tags.jsonl`). Results are in `agreement.json`, produced by `build_human_sheet.py`.
- **Category:** 301/331 agree, κ = 0.869.
- **Format-only vs substantive:** 326/331 agree, κ = 0.96. A tags 86 rows format-only, B 81.
- **English status:** only 96/331 agree, κ ≈ 0. The split is systematic: on terse "label = equation" outputs (e.g. `Trays served = 72 - 11 - 4 = 57`), A applies `compliant` and B applies `no_explanation` (224 rows). This reflects an ambiguity in the rule for minimal English labels, not item-level noise. English status is therefore reported only together with the human adjudication.
- **Human-check sheet:** `human_check_sheet.csv`, 65 rows. It holds all 30 category disagreements, 20 seeded rows on which both labels agree, and 15 seeded rows from the 214 English-only disagreements, to adjudicate the rule (`random.Random(101)`). Pending return.
- **Item/metadata observations from tagger A (not acted on; scoring is frozen):** these all concern unit and alias metadata on correct answers:
  - FT007 ("trays" vs gold unit "meals");
  - FT009 ("slots" vs "visits");
  - the helpers/workers item and "roses" vs "stems";
  - percent-format and "6:1" ratio answers;
  - a "Final:" step label read as a second FINAL line.

  Tagger A also flags one possibly ambiguous "range" wording for the human to check.

## Final audit (10 November 2026)
`human_check_returned.csv`: 65/65 rows labelled, all with a note; no fixed column changed. The human's category matched A on 28/30 category disagreements and B on 1/30; on the 20 agreed rows it matched both taggers 20/20.
- **English status:** the human chose B's reading. Terse "label = equation" output counts as `no_explanation` on 13/15 sampled English disagreements and 28/30 overall. That reading is applied to the 199 unchecked English-only disagreements, marked `rule_adjudicated`.
- **Outputs:** `finalize.py` writes `final_audit.csv` and `final_audit_summary.json`.
- **Final split of C failures:**
  - E+R: 46 format-only and 113 substantive (159 failures);
  - E+C: 40 format-only and 132 substantive (172 failures).

  The confirmatory deficit of E+C is therefore substantive, not a formatting artifact (descriptive).
- **English status:** 232/331 failed outputs have no English explanatory sentence, only labelled equations.
