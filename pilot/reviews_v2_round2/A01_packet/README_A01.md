# A01 — adjudication (round 2)

You are the **third, independent person**. You are not R01 or R02, and you have not discussed the questions with them. Two bilingual reviewers (R01, R02) each solved and rated 30 maths problems; every problem is written three ways (E English, R Romanized Hindi, C Hindi–English mixed), 90 texts in all. Your job is to make the final decision for each problem. About 1–1.5 hours.

## Files
- `A01_worksheet.csv`: **one row per problem.** Open it in Google Sheets or Excel. Problems with something to resolve come first (**15 of 30**); the column `ISSUES_TO_RESOLVE` says what.
- `answer_key.md`: the reference solutions. You may use them; you are the adjudicator.
- `reviewer_files/`: the reviewers' raw submissions, for reference only. Do not edit them.

## For each row, fill the six A01 columns on the right
| Column | What to write |
|---|---|
| `A01_status` | **ACCEPT**: maths correct, E/R/C mean the same, R and C read naturally (4+), not ambiguous. **REVISE**: fixable; give the fix. **EXCLUDE**: ambiguous or not fixable. |
| `A01_final_answer`, `A01_final_unit` | The correct answer and unit. Usually the same as `reference_answer`; if you think the reference is wrong, say so. |
| `A01_gold_and_units_ok` | yes / no |
| `A01_decision_reason` | One line, required for every row with issues (e.g. "R01's 26 is an arithmetic slip; reference 31 correct"). |
| `A01_proposed_text_repairs` | Only for REVISE, e.g. `R: <new sentence>`. |

## How to resolve common issues
- **A reviewer's answer differs from the reference:** check who is right. A reviewer's slip does **not** make the problem bad; a wrong reference or an ambiguous question does.
- **One reviewer says REVISE, the other ACCEPT:** read the text yourself and decide. Naturalness complaints ("stilted", "formal word") justify REVISE only if you also find it unnatural.
- **"ACCEPT inconsistent with its own ratings/flags":** a reviewer marked ACCEPT but also low readability, ambiguity or a failed check. Decide from the text itself.
- **PIL004-C classified UNCLEAR:** this packet's rule says C needs a productive English clause or relation, not just English nouns. Decide whether "…3/8 hissa cut kar diya gaya… remaining length…" meets it.

## Also please answer (bottom of your reply)
1. **Look-alike problems:** check PIL002 vs PIL010, PIL005 vs PIL021 and PIL011 vs PIL012. Are any of them essentially the same problem with different numbers? If so, which one should be EXCLUDED?
2. **Borrowing policy:** is the list of allowed English words in R (in `reviewer_files`, or the stage pages) acceptable? Anything to add or remove?
3. **Your consent and credit preference**, and confirmation that you are independent of R01 and R02.

Return the filled `A01_worksheet.csv` and your answers to the coordinator. Do not send anything to the reviewers.
