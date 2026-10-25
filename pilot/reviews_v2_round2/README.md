# v2 review round 2 (two different people, working separately)

Returned files are stored unchanged. Checks are recorded on receipt.

| File | Received | SHA-256 | Checks |
|---|---|---|---|
| R01_stage1_responses.json | 2026-10-25 | 5445234d04d626f666db9719c165d3afdf5c912158ff5c5b933adf9e80d48e7d | 90/90 solved, all clicked timestamps (ms precision) over 2 days with natural gaps; attested; 83/90 match the reference (7 differences for A01); no similarity to the round-1 files |
| R01_stage2_responses.json | 2026-10-25 | 70ff4722dd916fe6bcd49f29529c6c0f122b4a7a78f68cf8fea6ff3270e9a24b | stage1 hash and answers intact; clicked timestamps over 3 days; 85 ACCEPT / 4 REVISE / 1 PENDING (PIL030-C) in the first submission, kept as `R01_stage2_responses.first_submission.json`; 3 ambiguity flags; 5 self-corrections of stage1 slips in notes. Note style differs from stage1 (more formal); coordinator asked to confirm no AI or help and no reference exposure |
| R02_stage1_responses.json | 2026-10-26 | c3b35de0ed8b420975816a16aa257603feb2e59d182bc6bd0adf37504e265b9b | 90/90 answered, 89 clicked timestamps (ms) over 5 days; attested; 87/90 match the reference; value agreement with R01 80/90 (10 for A01); low similarity to R01 and to round 1 |
| R02_stage2_responses.json | 2026-10-26 | c2e7279abc43bd6a4cf90e551b8e0a1da441f97266ed33cf5f654e6c7bace603 | stage1 hash and answers intact; all 90 rated; 87 ACCEPT / 3 REVISE (PIL004-C classified UNCLEAR; PIL020-R/C), no notes on REVISE items; disposition agreement with R01 83/90 |

**R01 stage2 re-submission (2026-10-25, SHA-256 0f773fc95d3ee9e4f457b6a85669802623d94e440bd6f0a5501a97dab42149bf).** The only change is PIL030-C: PENDING → ACCEPT. The coordinator states R01 is a separate, independent person. R01 is treated as complete.

Rubric inconsistencies, left as entered (human judgments) and **for A01 to resolve**:
- ACCEPT with ambiguity = Yes: PIL030-C, PIL013-C, PIL014-E.
- ACCEPT with the semantic check explicit_assumptions = No: PIL021-E.
- ACCEPT with readability below 4: PIL018-R (3), PIL030-R (2).
- Missing reviewed_at timestamp: PIL017-R.
- REVISE: PIL019-R, PIL024-R, PIL006-R, PIL009-R (naturalness); see the notes.

**A01 packet built 2026-10-26:** `A01_round2_packet.zip` (worksheet with 15 of 30 families flagged, answer key, raw reviewer files, instructions). Give it only to a third independent person.

**A01 worksheet returned 2026-10-26** (`A01_worksheet_returned.csv`, SHA-256 ece059d68bbb0d4233ce8e8b06dfec403c31ba92136b8299ae9aec709fd65a18). The coordinator states A01 is a third person, independent of R01 and R02. All 30 rows decided with reasons; gold and units confirmed correct for all 30.
- ACCEPT 24; REVISE 5 (PIL009-R, PIL015-R, PIL019-R, PIL024-R wording; PIL020 E/R/C asks for a fraction in lowest terms); EXCLUDE 1 (PIL010, near-duplicate of PIL002).
- Pending from A01: decisions on the PIL005/PIL021 and PIL011/PIL012 relationships, borrowing-policy view (adding 'machine' to R), consent and credit.
- Pending decision: re-review of the 5 repaired families by R01 and R02 (packet rule) before acceptance.

**A01 follow-up (2026-10-26, via the coordinator):** PIL005 and PIL021 are accepted as distinct families (both kept). A01 consents and does not require credit. Still pending: the PIL011/PIL012 relationship and the borrowing-policy view on adding 'machine' to R.
