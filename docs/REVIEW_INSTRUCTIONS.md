# How to review a family batch

For the human reviewer. Start with **Pilot-B**: `autoverify_runs/pilot_b/verification/review_sheet_FULL.csv` (70 families, about 4–5 hours across several sittings).

## What is already done for you

Every family was written by an AI, its answer was computed in code, and **Claude and GPT each solved all three versions blind**. For Pilot-B, both agreed with the computed answer on all 210 texts. **You do not need to re-solve the maths.** Your job is the part AIs cannot judge reliably: **language and meaning**.

## Setup (2 minutes)

1. Open the CSV in Google Sheets (File → Import → Upload) or Excel.
2. **Hide the last column, `gold_after_review`**, before you start. Read the questions first and look at the answer only afterwards, so it doesn't bias you.
3. Rows are ordered: `flagged` first (problems found automatically, read `flag_reasons`), then `sample`, then `full_review`. All 70 need a decision.

## For each row (about 3–5 minutes)

Read E, then R, then C, and fill the five columns:

| Column | What to write | How to judge |
|---|---|---|
| `equivalence_ok` | `yes` / `no` | Do all three versions ask the **same question with the same numbers**? Nothing added, dropped or changed in meaning. Watch for: "each" vs "total", who has more or less, per item vs once. |
| `naturalness_R (1-5)` | 1–5 | Would a real person write this Romanized Hindi? 5 = completely natural, 4 = fine, 3 = understandable but stiff, 2 = awkward, 1 = wrong or unreadable. R should be mostly Hindi; numbers, units and common words like bus, ticket, kg are fine. |
| `naturalness_C (1-5)` | 1–5 | Is this real Hinglish, the way people actually mix? It **must contain at least one English phrase or clause**, not just English nouns. Same 1–5 scale. |
| `decision` | `ACCEPT` / `REVISE` / `REJECT` | See below. |
| `notes` | free text | Required for REVISE or REJECT. Write the problem, and your corrected sentence if you have one. |

**Decisions:**
- **ACCEPT**: equivalence yes, and both naturalness scores are 4 or 5.
- **REVISE**: fixable. Awkward wording (a score of 2–3), a questionable English word in R, or a small meaning slip. Write the fix in `notes`; the AI applies it and the family is re-checked.
- **REJECT**: the question is ambiguous (more than one reasonable answer), the versions can't be made equivalent, or it is a famous textbook problem.

After deciding, unhide `gold_after_review` and glance at it. If the answer looks wrong to you, add a note.

## Known items to rule on in Pilot-B

- **PB051** (flagged): "10:05 to 10:25", is that 20 or 21 minutes? If a reasonable reader could say 21, REVISE it (e.g. "for 20 minutes") or REJECT it.
- **PB013** (flagged): R and C say "dono" ("both"); the checker counted it as an extra number. Probably ACCEPT if the meaning matches E.
- **`anupaat` (ratio)** appears in PB037–PB042. You marked it "no idea" earlier. Judge whether ordinary people would understand it; if not, REVISE to a simpler phrasing.
- **English words in R not on the borrowing list:** samosa, petrol, auto, taxi, cake, mobile phone, printer, computer, cement and others. If people really say them in Hindi, accept; if a natural Hindi word exists and sounds better, suggest it.
- Possibly awkward: **PB026, PB044, PB054, PB059, PB070**.

## When you finish

Save the file with the same name and tell Claude. Claude applies the REVISE fixes as new versions, re-runs the checks, and freezes the accepted families with hashes. Rows you haven't finished stay pending, so partial progress is fine; just say how far you got.

## Honesty rules

- Judge from your own sense of the language. A dictionary is fine for spellings. **Don't ask an AI to fill the columns**: the paper reports this as human review.
- If you are unsure, write `unsure` in notes rather than guessing.
