# 30-family pilot — draft annotation package v2

All 30 families and 90 E/R/C texts remain **DRAFT**, AI-authored and awaiting two independent bilingual reviews and adjudication. Eight renderings in six families were repaired from v1: PIL004 E/R/C, PIL006 R, PIL008 C, PIL016 C, PIL025 C and PIL026 C. PIL004 is now a versioned revision of an original illustrative example; v1 remains unchanged. Gold, units and source/template identities are preserved. No independent human solutions, agreement, acceptance, split audit or reviewed pilot result is claimed. The separate Qwen GPU demo is technical feasibility evidence only.

## Send these files

- Give only `R01_review_packet.zip` to reviewer R01 and only `R02_review_packet.zip` to reviewer R02. They should unzip, read README.md, open stage1.html in Chrome/Edge, solve and download the JSON, then import it into stage2.html to judge the triplets. They can download/import progress between sittings. No network or sign-in is needed. The browser forms use downloaded JSON, not persistent cloud storage.
- Give `A01_adjudication_packet.zip` only to the separate adjudicator. Keep its answer key away from reviewers until both independent stage1 submissions have been collected. Assign actual people locally; R01/R02/A01 are placeholders, not assertions of completed annotation.
- Return R01 and R02 stage1/stage2 JSONs (four files), A01 adjudication JSON, and any documented text-repair records. Preserve first-pass answers/ratings; do not overwrite them. If HTML is inconvenient, print it and transcribe judgments into the corresponding blank form with explicit transcription attribution. Do not fill answers from the key.

## Acceptance and independence

Use the rubric in `pilot_review_packet.md`. Both reviewers solve before gold; afterward verify quantities, entities, units, relations, time, requested unknown and assumptions. For ACCEPT, each form requires correct classification, naturalness and readability >=4, equivalence and no unresolved ambiguity. An adjudicator must resolve disagreements, confirm gold/units and sign off the borrowing policy. Rejected/edited drafts remain development exclusions. Revised items receive a new version and hashes and must be independently re-reviewed. Thirty IDs are not proof of thirty independent families: inspect shared templates, reverse variants, numerical siblings and external sources. PIL002/PIL010 and PIL005/PIL021 are explicit near-relationship audit priorities. More basic relations may also overlap.

The proposed six topics have five candidates each. Some skills naturally cross topics; record that rather than interpreting topic counts as independent abilities. Difficulty has not been measured. Do not change questions by consulting pilot model answers before freezing the accepted data.

## Files and input-schema mapping

`coordinator/pilot_dataset.DRAFT.json` uses the existing `test1-1` input fields. Its `kind: reviewed` names the intended execution mode, while status DRAFT and empty reviews deliberately prevent reviewed execution. Do not upload these drafts as accepted data. `coordinator/split_manifest.DRAFT.json` reserves all candidate identities and known software fixtures; its human audit is pending. The 16 future training-smoke families and future confirmatory sets have NOT been authored. Add their identities as they are created; keep every pilot/draft/smoke descendant excluded forever. Unique IDs cannot detect semantic overlap automatically.

Raw stage1/stage2 annotation files use `annotation-draft-1` and are not pilot input files. Retain them as the annotation trail. After adjudication, convert each reviewer to `reviewer_id`, true (only if actually attested) `independent_solve_before_gold`, and E/R/C `forms` with current `text_sha256`, independent equation, exact canonical answer/unit, semantic_equivalence, ambiguity_resolved, classification, naturalness, readability and disposition. Use semantic equivalence true only if all seven checks are true. Preserve original answer/unit if canonical normalization is necessary, with a documented exact conversion in the annotation trail. A unit disagreement or correction must not be silently rewritten. Map A01's real decision to adjudication status/unresolved_issues/reviewed_at. Set family ACCEPT only after all checks and re-reviews are complete; the original pilot validator must pass unchanged. Split audit separately requires a real reviewer decision and timestamp. The human-approved final borrowing policy must be frozen before generation.

`draft_register.json` holds richer provenance/surface-control fields excluded by the strict runnable schema; unmeasured token counts and unannotated spans are null, not invented. Individual proposed family groups are provisional, not certified independent. Gold is exact integer/decimal/rational; unit conversions multiply the predicted value to canonical gold units. These policies are proposals set before research generations. Canonical count units avoid the metadata issue observed in the software demo. Source release terms are unassigned, not a fabricated external license.

Rebuild with `python3 pilot/annotation_draft_v2/build_packet.py`; verify with `python3 pilot/annotation_draft_v2/verify_packet.py`. Rebuilding touches this draft distribution, not returned reviews; store actual submissions separately with versioned filenames. Do not rebuild over human-edited draft JSON. The notebook and model/scorer configuration are unchanged. Software checks do not certify translation equivalence, naturalness or family independence.

## Version and exposure instructions

Use only these v2 packets for a new review round. Existing v1 submissions remain evidence for v1; do not rename or force-import them. The forms reject mismatched dataset versions. Re-review changed triplets and preserve original responses. The coordinator repair log and AI reports contain proposed answers/interpretation hints and must stay away from reviewers before independent solving. Record actual prior exposure; changing version does not restore blinding.

Optional PIL009/PIL019 terminology changes were deferred to humans. Family ancestry questions, including PIL002/PIL010, PIL011/PIL012 and PIL005/PIL021, remain unresolved; 30 IDs are not proof of independence. Borrowing policy remains proposed. No family is ACCEPT.

The builder reuses maintained v1 generation logic plus repairs.json; it refuses to overwrite existing generated v2 data. Do not delete submissions to bypass this guard. Use a new version for further changes.
