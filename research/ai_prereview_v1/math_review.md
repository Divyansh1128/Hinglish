# Mathematical and unit pre-review — all 30 candidate families

**AI REVIEW — NOT HUMAN VALIDATION.** Date: 2026-10-10. This reviewer is an AI subagent, not R01, R02 or A01. The proposed gold was accessible during this review; these are calculations from question text, **not blind, solve-before-gold human responses**. No acceptance, human rating, agreement statistic or completed adjudication is supplied. No original dataset record was changed.

Source: [candidate dataset](../../pilot/annotation_draft_v1/coordinator/pilot_dataset.DRAFT.json), schema `test1-1`, SHA256 `ab37f175df6dc5b7d02ee7ed8a4fc5cacf090e419a8e4272950b9fd269aee92e`. Governing requirements: [review packet](../../pilot_review_packet.md) and [data contract](../../test1_pilot/DATA_CONTRACT.md). Historical completion statements in the review packet are not treated as current project status.

## Outcome and limits

All **30 proposed gold numbers match calculations reconstructed from the question texts**. All 27 declared unit-conversion entries have the correct direction and factor. This result establishes internal mathematical consistency under the intended readings, not semantic equivalence, naturalness, family independence or research acceptance.

Five surface/equivalence issues merit targeted human decisions: PIL008-C omits explicit maximization; PIL006-R changes a shelf to a cupboard; PIL019-R does not explicitly name volume; PIL026-C adds a verbal equation restatement; PIL004-E adds a verbal fraction restatement. The first three can affect how a problem is read, although the intended answer remains recoverable. The last two introduce asymmetric explanatory redundancy; its effect on model performance is unknown.

## Per-family calculations and comparison

“No issue detected” below means no mathematical discrepancy found in this AI pass. Every row remains pending human review. Calculations were separately specified from the natural-language problems and checked using exact `fractions.Fraction` arithmetic against stored gold; the dataset's `reference_equation` expressions were not executed.

| Family | Text-derived calculation and answer | E/R/C information, units and ambiguity check | Proposed action |
|---|---|---|---|
| PIL001 | Aman = 36 − 5 = **31 marbles**. | All forms retain Aman as the smaller count and Riya as the reference. Gold canonical `marbles`; Hindi aliases refer to the same object. | No mathematical repair identified. |
| PIL002 | Cost = 5 × 24 = 120; change = 150 − 120 = **INR 30**. | Each-versus-total price and change request preserved. Normal single-purchase convention is sufficient; no unmentioned taxes should be invented. | No mathematical repair identified. Audit ancestry against PIL010 separately. |
| PIL003 | Added water = 3 × 4 = 12 L; final = 20 + 12 = **32 L**. | Initial volume, sustained inflow, interval, no outflow and adequate capacity are present in all forms. `32000 mL` converts exactly to 32 L. | No mathematical repair identified. |
| PIL004 | Removed = 24 × 3/8 = 9 m; remaining = **15 m**. | Original-length base and requested remainder preserved. E includes “Three-eighths (3/8)”; R/C supply only `3/8`. This is extra verbal scaffolding in E, not a different numerical problem. `1500 cm` = 15 m. | Human decision on matching fraction presentation across forms; version/re-review any change. |
| PIL005 | Five ratio parts = 30; red = 2 × 6 = **12 marbles**. | Only two colours and total preserved. R's “laal aur neele … anupaat” uses ordinary listed-order convention; explicit “laal se neele” could remove residual order doubt if reviewers require it. | No gold repair. Check ordered-ratio interpretation and family ancestry against PIL021. |
| PIL006 | 42 − 13 + 8 = **37 books**. | E/C count a particular shelf; R counts an `almaari` (cupboard/bookcase). Arithmetic is unchanged because all movements concern the same container, but the entity granularity differs. All exclude other movements. | Prefer a documented, natural Hindi rendering of the same shelf-level location; do not silently equate cupboard and shelf. |
| PIL007 | 28 − x = 16 + x; 2x = 12; **6 beads** transferred. | Transfer direction and equality condition preserved. Both end with 22; subtracting the whole difference would be wrong. | No mathematical repair identified. |
| PIL008 | After removal: 34 − 7 = 27; free capacity: 60 − 27 = **33 pencils**. | E/R explicitly ask for greatest/maximum additions. C asks “How many more … can be added without exceeding the capacity?” Conventionally it asks remaining capacity, but 0–33 additions satisfy the literal capacity condition. | Add **“What is the greatest number of additional pencils…”** or equivalent explicit maximum to C; human approve, new version and re-review. |
| PIL009 | Saira initially = 14 + 9 = 23; Imran then = 23 + 4 = **27 stickers**. | All forms place the comparison before Saira's use. R substitutes “chipkaane waali parchiyan” for stickers; intended count relation preserved, but object wording needs naturalness review. | No gold repair. Preserve the before-use time reference in any wording repair. |
| PIL010 | Basket = 3 × 18 + 35 = 89; change = 200 − 89 = **INR 111**. | Unit price of each pen, one notebook, no charges and paid amount match. | No mathematical repair. Inspect purchase/change family relation to PIL002. |
| PIL011 | Equal ticket price = 180/3 = 60; net refund = 60 − 15 = **INR 45**. | All specify only one ticket cancelled and fee deducted from that ticket's refund. “Full price refunded, but fee deducted” is clarified by the subtraction clause. | No mathematical repair identified. |
| PIL012 | Each share = 216/4 = 54; each tip = 9; each total = **INR 63**. | Tip explicitly per friend, not shared across four. R `bakhshish` needs naturalness assessment, but does not change the intended calculation. | No mathematical repair identified. |
| PIL013 | Budget after one delivery fee = 150 − 30 = 120; maximum count = floor(120/20) = **6 pens**. | Single order fee, no other charges and maximum preserved. Exact divisibility means this item does not distinguish floor reasoning from ordinary division. | No gold repair; describe tested skill modestly. Do not change numbers merely to create an “independent” family. |
| PIL014 | Girls = 40 × 2/5 = 16; attending girls = 16 × 3/4 = **12 girls**. | Second fraction refers to girls, not the entire class, in every form. Asked entity is girls attending, not all club attendees. | No mathematical repair identified. |
| PIL015 | After first discount = 200 × 4/5 = 160; second = 160 × 9/10 = **INR 144**. | All specify the second discount on the reduced price and exclude other charges. | No mathematical repair identified. |
| PIL016 | Remaining fraction = 3/4; original = 72 ÷ (3/4) = **96 kg**. | Original rice contents are the intended percentage base. R explicitly repeats rice; E/C use ordinary sack-of-rice shorthand. No other content change. `96000 g` = 96 kg. | No mathematical repair identified; if clarifying content versus packaging, apply consistently. |
| PIL017 | (3/4)/3 = **1/4 L** per child. | Entire amount, equal sharing, three recipients, no spill preserved. `0.25 L` and `250 mL` are exact equivalents. | No mathematical repair identified. |
| PIL018 | Let values be 5k and 3k; 2k = 14; larger = **35**. | Positive numbers and larger-minus-smaller difference preserved. Dimensionless scalar; no physical unit is implied. | No mathematical repair identified. Human review formal R terminology. |
| PIL019 | Five water parts = 350 mL; one part = 70 mL; syrup = **140 mL**. | E/C explicitly specify **volume** ratio. R uses `maatra` (amount/quantity) and mL, which strongly suggests volume but is less explicit; syrup is rendered as concentrated solution, not finished drink. `0.14 L` = 140 mL. | Make the same volumetric relation explicit in natural R wording, subject to bilingual review; preserve syrup-versus-water order. |
| PIL020 | A/C = (A/B)(B/C) = (2/3)(4/5) = **8/15**. | Positivity and both linked ratios present. Every form explicitly requests scalar number/fraction, so colon notation is outside the stated output form. No unit. | No mathematical repair. Do not accept approximate decimal `0.5333` as exact 8/15. |
| PIL021 | Initial blue = 15 × 4/3 = 20; final blue = 25; red/blue = 15/25 = **3/5**. | Only red/blue, five additional blue, no removal, ratio direction and scalar answer convention preserved. `0.6` is exact; colon `3:5` expresses the same math but violates the frozen scalar parser convention. | No gold repair. Keep semantic-versus-format distinction in manual scoring audit; inspect ancestry against PIL005. |
| PIL022 | 45 minutes = 3/4 hour; distance = 60 × 3/4 = **45 km**. | Speed, duration, uninterrupted travel preserved. R wording describes sustained rate even though it does not separately translate “constant” as an adjective. `45000 m` = 45 km. | No mathematical repair identified. |
| PIL023 | 2.4 m = 240 cm; pieces = 240/30 = **8 pieces**. | No cutting loss and full use specified in all forms. Asked number of pieces, not cuts; seven cuts would answer a different question. | No mathematical repair identified. |
| PIL024 | Joint rate = 6 + 4 = 10 boxes/minute; time = 90/10 = **9 minutes**. | Concurrent uninterrupted work and separate boxes intended in all forms. “Different boxes” is ordinarily understood as disjoint work; an explicit no-double-counting phrase could clarify equally across forms if human reviewers find it necessary. `0.15 h` = 9 minutes. | No established gold error. Do not impose additional cycle/start-up assumptions absent from the elementary constant-rate model. |
| PIL025 | First segment = 40/20 = 2 h; rest = (120 − 40)/40 = 2 h; total = **4 h**. | Segment boundary, total distance, both speeds and no stops preserved. Average speed must not be the unweighted mean of 20 and 40. `240 minutes` = 4 h. | No mathematical repair identified. |
| PIL026 | 3x = 28 − 7 = 21; **x = 7**. | Same equation and unknown, but C gives both verbal equation and symbols while E/R give symbols only. This is unequal scaffolding, not numerical inequivalence. | Remove C-only restatement or add genuinely parallel restatement to all forms, while preserving substantive code mixing. All repaired forms require re-review. |
| PIL027 | x + (x + 1) = 41; **x = 20**, with other integer 21. | Consecutive integers, sum and smaller requested integer preserved. No positivity assumption is needed for uniqueness. | No mathematical repair identified. |
| PIL028 | 2(length + 9) = 50; length = 25 − 9 = **16 cm**. | Rectangle, perimeter, width and requested length preserved. Result exceeds width, so ordinary naming convention is consistent. `0.16 m` = 16 cm. | No mathematical repair identified. Human review R educational vocabulary. |
| PIL029 | (2p + n) − (p + n) = 58 − 39; **p = INR 19**. | Constant pen/notebook prices make cancellation valid in all forms. Implied notebook price 20 is positive and consistent. | No mathematical repair identified. |
| PIL030 | x² = 49 gives ±7; positivity selects **7**. | Positive condition and square relation preserved. No unit. Losing “positive” in a repair would introduce two valid answers. | No mathematical repair identified. |

## Exact units and permitted conversion audit

The contract maps a supplied unit to a multiplier into the gold's canonical unit. The nine groups below contain three declared conversion keys each, giving **27 checked entries**. Singular/plural keys have the same exact multiplier. These are internal checks of current policy, not requests to broaden it after seeing model outputs.

| Family | Canonical unit | Declared alternate unit group | Multiplier into canonical | Concrete equivalent answer |
|---|---|---|---|---|
| PIL003 | L | mL / millilitre / millilitres | 1/1000 | 32000 mL → 32 L |
| PIL004 | m | cm / centimetre / centimetres | 1/100 | 1500 cm → 15 m |
| PIL016 | kg | g / gram / grams | 1/1000 | 96000 g → 96 kg |
| PIL017 | L | mL / millilitre / millilitres | 1/1000 | 250 mL → 1/4 L |
| PIL019 | mL | L / litre / litres | 1000 | 0.14 L → 140 mL |
| PIL022 | km | m / metre / metres | 1/1000 | 45000 m → 45 km |
| PIL024 | minute | h / hour / hours | 60 | 0.15 h → 9 minutes |
| PIL025 | h | minute / minutes / min | 1/60 | 240 minutes → 4 h |
| PIL028 | cm | m / metre / metres | 100 | 0.16 m → 16 cm |

Every item currently allows omitted units because the question fixes the requested quantity; this does not license an explicitly wrong unit. Count units are stored explicitly, avoiding the original smoke fixture's blank-count-unit problem. PIL018, PIL020, PIL021, PIL026, PIL027 and PIL030 are dimensionless. A correct numeric answer followed by an undeclared noun can still fail the strict parser. Preserve the original automatic result and separately record the human semantic diagnosis; do not silently upgrade scores.

INR entries permit named currency aliases but no paise conversion. Physical-unit lists omit some otherwise valid spellings/conversions. That is a deliberately bounded accepted-answer policy, not an arithmetic error. If human reviewers consider additional forms necessary, specify them consistently **before** research generation, version the metadata and validate the complete policy. Do not add only forms observed in a favoured condition's outputs.

All values are exact; no item requests rounding. PIL020 has a repeating decimal expansion, so a finite rounded decimal cannot equal its exact answer. No floating-point epsilon is appropriate. The ratio prompts' requested scalar convention should be disclosed when interpreting formatting failures.

## Proposed repair candidates for human evaluation

These are unapproved alternatives, not replacement dataset records:

- **PIL008-C:** Keep the first two sentences; replace the final question with “What is the greatest number of additional pencils that can be added without exceeding the capacity?” This retains a substantive English request and explicit maximization.
- **PIL026:** A compact C candidate is “Ek number x satisfies 3x + 7 = 28. What is x?” This removes the C-only verbal duplicate while retaining an English predicate and request. Bilingual reviewers must judge whether it is natural code mixing; do not mark it accepted from this AI suggestion.
- **PIL004:** A possible common surface policy is `3/8` alone in all forms. Any change to the preserved historical E example must create a new rendering version rather than rewriting history.
- **PIL006-R:** Ask reviewers for the natural shelf-level equivalent under the borrowing policy. Replacing `almaari` with a forced literal Hindi construction without human judgment could worsen the R condition.
- **PIL019-R:** Ask reviewers to express a ratio **by volume**, with both component volumes in mL. Do not substitute a mass ratio or use the finished drink as the syrup component.

## Research interpretation and next gate

Correct golds do not certify 30 independent families. PIL002/PIL010 and PIL005/PIL021 need source/template lineage decisions; shared skills alone do not establish duplication. Human review must also evaluate the longer/formal R phrasings, productive switches, and actual reviewer exposure to proposed answers.

The existing paired pilot remains unavailable as accepted research data until the genuine independent-review and adjudication requirements are met. Keep these AI observations as a coordinator pre-review aid; do not distribute this answer-bearing report to reviewers before any intended solve-before-gold stage. Archive repair proposals and human decisions, preserve original versions, and re-review the exact hashes of changed renderings.
