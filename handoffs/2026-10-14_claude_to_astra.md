# Claude → Astra, 14 October 2026

Task 2 on docs/TEAM_BOARD.md.

Read first: README.md, docs/PROJECT_STATUS.md, docs/TEAM_BOARD.md, research/claude_review/README.md. Run `python3 -B research/claude_review/scorer_probe.py` and confirm or dispute its findings.

Write ONE document: research/pre_pilot_endpoint_spec_v1.md. Everything in it is a proposal awaiting a human decision. It must be adoptable BEFORE the reviewed pilot generation. Cover:

1. Secondary endpoint "extracted numeric value equals gold": exact extraction rules (including Markdown bold, \boxed{}, $..$, `x = v`, `Rs.` prefix, trailing lines), reported beside the unchanged strict primary endpoint, per form, with invalid-reason breakdown. State precisely how it avoids becoming a post-hoc rescue.
2. Unit-alias checklist for the A01 adjudicator: Rs./Rs prefix, kilo, minat, litar, mitar, kilomitar and any others you find, applied consistently across E/R/C. This is a gold-metadata decision inside human review, not a scorer change.
3. A fixed manual-audit error taxonomy (category values for manual_audit.csv).
4. An English-output compliance measure per form (manual tagging is acceptable).
5. A code-mixing index definition for R and C texts (word-level language tagging rules for romanized text, shared tokens like numbers/names/borrowings, formula).
6. Whether the refusal regex (matches "I cannot" anywhere) should become scorer v1.1 before the pilot, and what fixture evidence would decide it.
7. A list of new EXCLUDED format-smoke fixtures for Sol to build (currency, algebra, ratio, metric units; E/R/C each). Do not reuse or derive from pilot families.
8. A one-paragraph reviewer consent/credit note.

End with a short "Decisions needed from the user" list and a "Tasks for Sol" list.

Constraints: modify no other file. Do not change scorer v1.0.0, report.py scoring, or pilot/annotation_draft_v1/ and v2/. Do not quote gold values from coordinator files (reviewers may read research/). No model inference, training or paid APIs. No commits, pushes, resets or branch changes. Distinguish AI proposals from human validation and experimental results. Keep it concise: aim for under 250 lines.

When finished, also write handoffs/2026-10-14_astra_to_claude.md: files changed, what you disputed in Claude's review, open questions.
