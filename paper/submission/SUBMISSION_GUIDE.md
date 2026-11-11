# EACL 2027 SRW — final submission package

Updated 11 November 2026. **Files prepared; no final-track submission performed.** The anonymous paper and supplement have been rebuilt for the completed training study. Remaining human form facts: reviewer payment and actual institutional ethics-review determination. Consent and author order were confirmed by the user; consent is not institutional approval.

## Upload exactly these two artifacts

1. `EACL2027_SRW_submission.pdf`: anonymous ACL review PDF, **4 content pages**, 8 PDF pages including limitations, ethics, references and appendices.
2. `supplementary_anonymous.zip`: anonymous code/data/outcome supplement, if the direct-SRW form permits supplemental ZIP upload. The included stdlib verifier reproduces the stored primary result without GPU access. FINAL_TEST wording/raw responses/weights are withheld; this limitation is explicit.

`EACL2027_SRW_author_package.zip` is a convenience archive for the authors. **Do not upload that whole archive:** it contains names and author-only instructions. Extract it and upload only the two files above. `metadata.md` supplies the current abstract and author order; `responsible_nlp_checklist.md` supplies evidence-based form answers; `PACKAGE_VERIFICATION.md` records checks and remaining limits.

## Verified venue requirements

Checked 11 November against [the official SRW call](https://2027.eacl.org/calls/srw/) and [ARR CFP](https://aclrollingreview.org/cfp). Short research papers allow four content pages; references, limitations/ethics and allowed appendices follow the applicable ACL rules. Use the official ACL review template. First author must be a student. Anonymous paper and supplement; identifiable preprints are allowed under the stated policy, so making the repository private is not automatically required.

| Milestone | Official date, AoE |
| --- | --- |
| Mentorship feedback | 5 December 2026 |
| Direct SRW submission | **15 December 2026, 23:59 UTC−12** |
| Notification | 5 January 2027 |
| Camera-ready | 19 January 2027 |

The direct deadline is 16 December 2026 at 17:29 IST. Aim to upload earlier. The call also lists an apparently inconsistent ARR-commitment year; this package uses the unambiguous **direct SRW** route and does not silently correct that separate date.

## Final upload steps

1. Incorporate any mentorship feedback received before the deadline; rebuild/reverify if the paper changes.
2. Ensure all four authors have verified OpenReview profiles and have approved this final version. Enter names/profiles only in author fields, not the anonymous PDF/supplement.
3. Open the [direct SRW submission site](https://openreview.net/group?id=eacl.org/EACL/2027/SRW). Make a **new research-paper/short-paper submission**, not an update only to mentorship #12.
4. Select archival publication if it remains the team's choice. Paste the updated title/abstract/keywords and enter the confirmed author order from `metadata.md`.
5. Complete the actual venue form/checklist truthfully. Resolve the two unconfirmed facts above. Follow any direct-SRW profile/service requirements shown in its form; do not assume all ARR-cycle-specific requirements apply identically.
6. Upload the anonymous PDF and supplementary ZIP, inspect the preview and filenames, then submit. Save the submission ID and receipt. This task does not submit or contact anyone.

## Rebuild locally

From the repository root:

```sh
(cd paper/latex && tectonic main.tex)
python3 -B paper/submission/build_package.py
python3 -B tmp/submission_bundle/anon_supplement/verify_scores.py
```

The builder updates only the anonymous supplementary ZIP and temporary staging files. After a manuscript edit, copy the visually checked `paper/latex/main.pdf` to the submission PDF, regenerate metadata from its abstract, update checksums and rebuild the author convenience ZIP. Do not change frozen research artifacts to fix packaging.
