# Anonymous SRW paper build

Updated 11 November 2026. Run `tectonic main.tex` from this directory. ACL style files are unchanged. The current PDF has eight pages; Abstract through Conclusion ends on page 4. Limitations/Ethics, references and Appendices A–D follow. Appendix C reports the completed fine-tuning experiment; Appendix D discloses the pre-training CPU test-access deviation and reproduction limits.

Build: successful, no undefined citations/references or overfull boxes. Underfull-box warnings remain. Tectonic reports an invalid UTF-8 sequence in the upstream lineno.sty comment; extracted PDF text has no replacement characters and page rendering is checked separately. The official style file was not altered.

Paper source updates on this date correct stale test-set status, a missing punctuation mark, overly causal training-target wording, exact output-length scope and an error-decomposition overstatement. The official Llama 3.2 model card is now cited. No research scores or frozen source/data were changed.

The earlier October build notes and resolved TODO list remain in Git history. See `../submission/PACKAGE_VERIFICATION.md` for the current release checks and `../submission/SUBMISSION_GUIDE.md` for upload instructions. Always visually inspect a new PDF after edits; do not assume page count or prior checks remain valid.
