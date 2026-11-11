# Submission package verification — 11 November 2026

Status: **technical artifacts prepared; final submission not performed**. Payment and institutional ethics-review status remain author-only form questions. The user confirmed teammate review, consent and the four-author order. No institutional approval, exemption or payment status was inferred.

## Checks performed

- Built the anonymous PDF with the unchanged official ACL style. Eight total pages; main content ends on page four; limitations start on page five. All eight rendered pages inspected; changed appendix pages re-rendered and inspected after the final edit. No clipped text, table overflow or missing visible glyphs identified.
- Tectonic completed without errors, overfull boxes or undefined citations/references. Underfull-box warnings and an upstream lineno.sty encoding warning remain; extracted PDF text contains no replacement characters. Metadata author/title fields are empty.
- All 22 cited keys resolve uniquely. Existing citations retain earlier primary-source verification records; this task checked the newly added official Meta model-card citation and current venue/ARR rules. It did not repeat a full literature search or independently revalidate every older paper's claims.
- Updated abstract matches the manuscript and includes the negative training result. Checklist now covers training, complete final evaluation and qualified compute accounting, rather than claiming inference only.
- Supplement built from an explicit allowlist: no personal reviewer submissions, .DS_Store, caches, model weights, FINAL_TEST text/raw responses, repository identity or local identifying paths. Automated project-name/person/credential-pattern checks passed; this is bounded screening, not proof against every possible indirect identifier.
- All included JSON parses and Python files parse. Source and anonymized-copy hashes are distinguished. Supplement source inspection is supported; end-to-end GPU reproduction is not claimed while final-test text/weights are withheld.
- Extracted the delivered supplement into a clean temporary folder. Its no-dependency verifier passed checksum checks, 3,000 unique outcomes, exact primary bootstrap (-13/300; bounds -2/25 and -1/150), fixed resampling-matrix hash and all 331 human-labelled failure rows. Deliberately altering a copied score matrix caused rejection.
- Existing read-only exploratory checker passes all 60 published strict/numeric checkpoint × form counts. Frozen implementation manifest still verifies at `726241c5726aaba2c51fc027866dd572abfc13d02ef9235d1901af87a9f5b43d`.
- Final inference latency from committed rows: 8.291 GPU-hours. Approximate training updates: 3 GPU-hours. Neither is a complete total including development/screening/load/failed sessions.

## Research-preserving edits

Corrected obsolete “not yet evaluated” wording; removed an unsupported causal wording about targets; corrected global output-token median (113 unchanged vs 42 trained); retained unscored residual in the exploratory decomposition; narrowed the independent-verification claim to what was verified; added the pre-training CPU access deviation and attestational limits. Frozen scores, datasets, protocol, implementations and model outputs were unchanged.

## Human/form gate

Use the confirmed author order in metadata, with verified OpenReview profiles. Each author should inspect this assembled version before submission. Reviewer payment and actual institutional ethics determination remain unspecified despite confirmation of consent; fill those factually. The package is not evidence of submission, acceptance or ethics approval. Mentorship feedback may prompt a later version before the verified direct deadline.

The anonymous upload files are the paper PDF and supplementary ZIP only. The outer author package includes names and must NOT be uploaded wholesale as supplementary material.
