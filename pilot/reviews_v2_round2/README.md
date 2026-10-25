# v2 review round 2 (two different people, working separately)

Returned files are stored unchanged. Checks are recorded on receipt.

| File | Received | SHA-256 | Checks |
|---|---|---|---|
| R01_stage1_responses.json | 2026-10-25 | 5445234d04d626f666db9719c165d3afdf5c912158ff5c5b933adf9e80d48e7d | 90/90 solved, all clicked timestamps (ms precision) over 2 days with natural gaps; attested; 83/90 match the reference (7 differences for A01); no similarity to the round-1 files |
| R01_stage2_responses.json | 2026-10-25 | 70ff4722dd916fe6bcd49f29529c6c0f122b4a7a78f68cf8fea6ff3270e9a24b | stage1 hash and answers intact; clicked timestamps over 3 days; 85 ACCEPT / 4 REVISE / 1 PENDING (PIL030-C) in the first submission, kept as `R01_stage2_responses.first_submission.json`; 3 ambiguity flags; 5 self-corrections of stage1 slips in notes. Note style differs from stage1 (more formal); coordinator asked to confirm no AI or help and no reference exposure |
| R02_stage1_responses.json | pending | | |
| R02_stage2_responses.json | pending | | |

**R01 stage2 re-submission (2026-10-25, SHA-256 0f773fc95d3ee9e4f457b6a85669802623d94e440bd6f0a5501a97dab42149bf).** The only change is PIL030-C: PENDING → ACCEPT. The coordinator states R01 is a separate, independent person. R01 is treated as complete.

Rubric inconsistencies, left as entered (human judgments) and **for A01 to resolve**:
- ACCEPT with ambiguity = Yes: PIL030-C, PIL013-C, PIL014-E.
- ACCEPT with the semantic check explicit_assumptions = No: PIL021-E.
- ACCEPT with readability below 4: PIL018-R (3), PIL030-R (2).
- Missing reviewed_at timestamp: PIL017-R.
- REVISE: PIL019-R, PIL024-R, PIL006-R, PIL009-R (naturalness); see the notes.
