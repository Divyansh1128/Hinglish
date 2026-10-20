# Real-browser test of the v2 reviewer forms, 20 October 2026

Closes the gap recorded in `pilot/annotation_draft_v2/README.md` ("full real-browser annotation behavior remains unverified"). Software verification only; no reviewer data involved.

Method: `browser_test.js` drives the installed Google Chrome (headless, via puppeteer-core) through COPIES of `R01/stage1.html`, `R01/stage2.html` and `R02/stage2.html`, using artificial answers. The distributed packets were not modified.

All 14 checks passed with no page JavaScript errors:
- stage1 loads 90 renderings and shows no gold
- partial progress downloads and resumes by import
- completing all solves with timestamps and the attestation exports correctly
- stage2 blocks saving before import and rejects an unfinished stage1
- stage2 accepts a finished stage1, keeps its answers unchanged and records its SHA-256
- ratings for all 90 rows export
- R02's stage2 rejects an R01 file

Usability notes for the coordinator (no change made, because the packets are already distributed):
1. In stage1, the import confirmation says "Imported answers are read-only in stage2". This is correct but may confuse reviewers.
2. The progress download and the final download use the same filename (`R01_stage1_responses.json`), so Chrome renames repeats ("(1)", "(2)"). Reviewers should return the **last** stage1 file, the one with all 90 solves and the attestation.
3. The packet's C definition is the original clause-based one; Pilot-B/Phase-2 use the revised insertional definition (D033). Analyses report the cohorts separately.
