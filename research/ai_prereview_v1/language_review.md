# AI language pre-review of all 30 candidate triplets

**AI REVIEW — NOT HUMAN VALIDATION.** Date: 2026-10-10. This is a coordinator-facing editorial assessment, not an R01/R02 submission, independent human solve, adjudication, naturalness rating, or acceptance decision. The AI reviewer inspected proposed keys and prior audit findings. Do not claim this review was blind or independent of those materials. No source questions or approval fields were changed.

Input: [pilot-draft-v1](../../pilot/annotation_draft_v1/coordinator/pilot_dataset.DRAFT.json), SHA-256 `ab37f175df6dc5b7d02ee7ed8a4fc5cacf090e419a8e4272950b9fd269aee92e`. Read all 90 texts, the dataset's proposed borrowing policy, [governing rubric](../../pilot_review_packet.md), and [previous readiness audit](../astra_review_readiness_v1.md). Historical opening statements in the review packet are superseded by the actual current artifacts.

## Main findings

All 30 C renderings contain at least a plausible productive English predicate, clause or mathematical relation; none relies exclusively on object nouns. This is a text-based AI classification under the proposed policy, not a frozen human classification. PIL004 uses a mixed predicate and relational phrases rather than a full English clause; record that subtype explicitly. PIL027 and PIL028 place their clearest English clause in the requested answer. Those differences mean this set does not isolate the causal effect of switching location.

The most actionable issues are PIL026's unequal explanatory repetition, PIL006's shelf/cupboard entity mismatch, PIL008-C's less explicit maximum request, PIL004's unequal fraction notation and awkward R ending, and PIL016-C's less precise fraction-of-rice wording. The first two are directly observable surface/content differences. Whether the others create a meaningful comprehension difference requires human judgment; repair suggestions below prevent the ambiguity without using any model outcome.

No clear cross-form change of numeric quantities or reversal of the requested comparison was found in this reading. That statement is not an equivalence certificate. Formal Hindi vocabulary and everyday Hinglish vocabulary differ across several pairs. Formal vocabulary is not automatically defective: the target reader and frozen borrowing policy must decide whether it is appropriate, familiar and equally clear.

## Complete per-family review

“No issue found” means this AI reading found none; it never means ACCEPT. Priority **repair** denotes an actionable proposed edit; **human check** denotes a subjective or policy-dependent concern; **routine** still requires the full human rubric. No numerical naturalness/readability ratings are invented.

| Family | Equivalence, scaffolding and ambiguity | R phrasing / borrowing assessment | Productive C evidence and role | Proposed action |
| --- | --- | --- | --- | --- |
| PIL001 | Same 36, 5 fewer, Aman unknown; subject/direction retained. No unequal solution hint found. | `kanche`, `se 5 kam` are clear Hindi constructions. | `Aman has 5 fewer marbles than Riya` carries comparison. | Routine; independently confirm direction. |
| PIL002 | Same per-notebook price, quantity, payment and change request. R splits the purchase into more sentences but adds no operation hint. | `kaapiyan`, `dukandaar`, `vaapas` fit Hindi phrasing. | `each costs INR 24` expresses unit price. | Routine; freeze INR/rupee convention. |
| PIL003 | Initial volume, duration, rate, no outflow and adequate capacity preserved. | Permitted minute/litre forms; final `kitne litre paani hoga` may sound awkward to some readers. | Full filling-rate sentence; `enough space` is additional mixing. | Human check on final-sentence fluency; no necessary mathematical repair found. |
| PIL004 | Original-base fraction/remnant preserved, but E alone spells out `Three-eighths` in addition to `3/8`. R ending has awkward agreement; `feeta` can evoke tape but remains a cuttable strip. | `Ek feete`/`kitne metre hai` merit editorial repair; do not introduce unapproved English `ribbon` into R automatically. | `cut kar diya gaya` mixed predicate; `original length` and `remaining length` mathematical relations. | Repair candidate A below; document C subtype and human-check classification. |
| PIL005 | Only two colours, red:blue order and total preserved. R says `laal aur neele ... anupaat`; order is conventional but `laal ... ka neele ... se` could be clearer if humans flag it. | `anupaat` is normal formal mathematical Hindi; familiarity remains audience-dependent. | `Red to blue ratio 2:3` is a productive relation. | Routine with explicit ratio-order check; no mandatory rewrite. |
| PIL006 | E/C locate books on a shelf; R locates them in a cupboard. The arithmetic survives, but location granularity is not matched. Distinct added books and no other movements are preserved. | `pustakalaya` is formal; `padhne waale` is comprehensible. `almaari` does not mean a single shelf. | Borrowing clause plus `No other books move`. | Repair R location, candidate B; compare naturalness of `takhta` for this audience. |
| PIL007 | Transfer from Nisha to Kabir until equality retained, with both counts changing. | Clear Hindi direction and equality. | Full transfer-and-equality sentence. | Routine; do not misread as giving the initial difference. |
| PIL008 | All forms give capacity 60, initial 34, removal 7. E/R explicitly ask greatest allowable addition; C asks how many can be added. Pragmatic maximum is likely, but lesser additions are also possible literally. | `pensilein` follows proposed `pensil` borrowing; capacity sentence is verbose. | `at most 60` capacity relation and full English question. | Clarify C maximum, candidate C; optional R simplification below. |
| PIL009 | Before-use time reference and comparison preserved. | `chipkaane waali parchiyan` is an unusually long sticker paraphrase. `Saira ke parchiyan istemaal karne se pehle` merits fluent human editing. | Full temporal comparison clause. | Human check; candidate D preserves current no-sticker-borrowing policy. Do not declare the paraphrase universally unnatural. |
| PIL010 | Both basket terms, no extras and payment/change preserved. | `har kalam INR 18 ki` is an understandable elliptical phrase. | `each pen costs` and `There are no extra charges`. | Routine language review; separate ancestry audit with PIL002 remains necessary. |
| PIL011 | Equal prices, one cancellation and fee subtracted from that ticket's refund retained. | `radd`, `shulk`, `rakam` may be formal but do not introduce English clauses. Ticket/tikat borrowing is proposed. | Full refund/deduction sentence. | Human check that “full price refunded, but deduction” is understood consistently; no form-specific defect found. |
| PIL012 | Bill split equally followed by a tip per friend, not a shared tip, retained. | `bakhshish` can denote a tip/gratuity; user familiarity is subjective. | Full per-friend additional-tip sentence. | Human vocabulary check. Avoid expanding the borrowing list for this item alone. |
| PIL013 | Budget, one order-level fee, per-pen price, no extras and maximum retained. R adds home as the delivery destination, absent E/C; not answer-changing but an unnecessary entity detail. | Hindi phrasing clear; long delivery paraphrase is a possible length/register confound. | Full delivery-fee clause and `at most`. | Optional remove `ghar` in versioned R edit if strict surface matching is desired; otherwise record detail. |
| PIL014 | Nested fraction base correctly remains “those girls” in all forms. | `kaksha`, `vidyarthi`, `sangeet ki mandali` use more formal/localized register than E/C; club versus group is close but should be checked. | `Girls make up 2/5 of the class`; `attend karti hain`. | Human register/entity check; do not change subgroup base during editing. |
| PIL015 | Second discount applied to already reduced price in every form. | `Chhooton` spelling/initial capital may be less readily parsed than `Chhoot se pehle`; meaning remains inferable. | `Its price is reduced by 20%` plus reduced-price relation. | Human readability check; optional R first sentence `Chhoot lagne se pehle ek cheez ki keemat INR 200 hai.` |
| PIL016 | E/R clearly specify rice quantity removed. C says `sack ka 25% use`, potentially referring to the sack/container rather than its rice; rice later makes the intended reading likely. | Clear original-quantity Hindi; `bori ka 25% chaawal` can be made even more direct but is understandable. | `There is no other change in its contents` is a full English condition. | Clarify C fraction base, candidate E. |
| PIL017 | All juice, equal sharing, three children and no spill preserved. | `jag` explicitly proposed borrowing; `ras` is understandable but less conversational than juice for some readers. | Full equal-sharing sentence. | Human lexical/register check; no unequal arithmetic cue found. |
| PIL018 | Positive numbers, larger-minus-smaller difference and larger unknown preserved. | `dhanaatmak sankhyaon` and `anupaat` require mathematical Hindi literacy; valid terminology, not automatically poor naturalness. | Full `larger ... exceeds ... by 14` relation. | Human audience check; preserve positivity in any simplification. |
| PIL019 | Syrup:water order and water quantity retained. E/C say volume; R `maatra` is generic quantity, though mL supplies a strong volume cue. `sharbat ke gaadhe ghol` must mean concentrate, not finished drink. | Long culturally specific syrup paraphrase requires semantic/naturalness review. | `If 350 mL of water is used` plus volume-ratio relation. | Human check; optional R clarification candidate F, subject to acceptability of technical `aayatan`. |
| PIL020 | Positive A/B/C conditions, shared B, and scalar A/C request retained. | `dhanaatmak maatraon`, `bhinn` are formal but semantically appropriate. | `B:C equals 4:5`; English answer-format request. | Routine plus technical-term readability check. Preserve number/fraction output in all forms. |
| PIL021 | Ratio order, given red count, only blue addition, no removal and new ratio retained. All forms supply the same scalar-division explanation. | Long but content-matched; requested division clearly identifies numerator/denominator. | Full addition/no-removal clause and explicit output request. | Routine; do not remove scalar instruction from one form only. Ancestry audit separate. |
| PIL022 | Speed and full 45-minute travel duration preserved. R `lagaataar 60 ... raftaar` conveys maintaining that speed, though “constant” is less directly lexicalized. | `bus` permitted; `prati ghante` valid rate phrase. | `at a constant speed of 60 km per hour` mathematical relation. | Routine; humans can confirm constant-rate interpretation without forced rewrite. |
| PIL023 | Exact piece length, zero cutting loss and whole-cord use retained. | `theek`, `lambai nahi ghatti` understandable; physical idealization is explicit across forms. | `exactly 30 cm long` relation and `Cutting loses no length`. | Routine; same exactness and no-loss conditions must survive edits. |
| PIL024 | Simultaneous work/no stopping and distinct box streams retained; R `band` means close, while E/C `seals` is somewhat more specific. Mathematical rate task unaffected. | `yantra` is formal; machine is not on the current permitted list. Do not silently add it. | Full two-machine rate sentence. | Human vocabulary/action-equivalence check; ordinary closing versus sealing need not alter counts but record wording. |
| PIL025 | Total journey, first-segment length/rate, remaining-segment rate and no stops retained. | `cycle` proposed borrowing; Hindi sentence is readily interpretable. | Full first-segment relation and remaining-speed phrase. | Human C fluency check: `ka journey` is awkward; candidate G uses Hindi `safar` without changing mixing role. |
| PIL026 | C alone gives verbal equation plus symbolic equation; E/R have symbolic equation once. This is unequal representational scaffolding, regardless of equal gold. | R numeric-symbolic equation is clear. | Full verbal equation supplies productive relation in current C. | Repair C candidate H preserves English predicate while removing extra verbal expansion. |
| PIL027 | Consecutiveness, sum and smaller unknown preserved. | `lagaataar poornank` needs audience check; mathematical consecutiveness rather than a time sequence is intended. | Full English requested-answer sentence; relation otherwise mixed noun phrases. | Human terminology check. C qualifies via question but annotate requested-answer role. |
| PIL028 | Perimeter, width, length request and units preserved; no form gives perimeter formula. | `aayat`, `parimaap` are correct formal terms needing familiarity check. | Full English length question; earlier nouns alone would not establish productive C. | Human terminology/fluency check; do not add formula to R alone to explain words. |
| PIL029 | Two baskets, shared pen/notebook prices and pen unknown retained. R repeats equality conditions like E/C. | `kalamein`, `kaapi` are Hindi vocabulary; amount wording grammatical enough for human assessment. | Full second-basket price relation. | Routine; ensure same prices means within each object class, not pen price equals notebook price. |
| PIL030 | Positive root condition and square relation retained. E/C verbalize square; R uses mathematical Hindi term, with no extra symbolic duplicate. | `dhanaatmak`, `varg` legitimate educational terms with audience-dependent familiarity. | `x squared equals 49` full relation. | Human terminology check; never drop positivity during repair. |

## Exact proposed edits for coordinator consideration

These are AI-authored alternatives, not accepted wording. They require new rendering/family versions and hashes, edit provenance, and independent human re-review of the complete affected triplet. Original drafts and all descendants retain development exclusions. Do not overwrite earlier packets or silently apply these after reviews have begun. Where a candidate changes only one form, humans must still compare all three.

### A. PIL004: fraction representation and R fluency

Proposed E: `A ribbon is 24 m long. 3/8 of its original length is cut off. What length of ribbon remains, in metres?`

Proposed R: `Ek feeta 24 m lamba hai. Uski shuruaati lambai ka 3/8 hissa kaat diya gaya. Bache hue feete ki lambai metre mein kitni hai?`

Proposed C: `Ek ribbon ki length 24 m hai. Uski original length ka 3/8 hissa cut kar diya gaya. Ribbon ki remaining length metres mein kitni hai?`

This removes only E's extra written-out fraction and improves the two final questions. C retains its mixed predicate; if the adjudicator requires a full English clause rather than accepting productive mixed predicates, freeze that stricter policy for the entire dataset first. Do not opportunistically reclassify only this item.

### B. PIL006: preserve one shelf as the counted location

Proposed R: `Ek pustakalaya mein almaari ke ek takhte par 42 kitaabein hain. Padhne waale unmein se 13 kitaabein le jaate hain, aur phir usi takhte par 8 doosri kitaabein rakhi jaati hain. Koi aur kitaab na nikaali jaati hai na rakhi jaati hai. Ab us takhte par kitni kitaabein hain?`

`Almaari ka takhta` is a proposed shelf rendering, not a certified natural equivalent. Humans may choose another idiomatic Hindi expression; record the decision without adding English `shelf` to R unless the borrowing policy explicitly allows it. This preserves a single shelf, unlike the original cupboard-wide count.

### C. PIL008: explicit greatest-number request

Proposed C: `Ek box mein at most 60 pencils aa sakti hain. Usmein 34 pencils hain aur unmein se 7 nikaal di jaati hain. What is the greatest number of pencils that can now be added without exceeding the capacity?`

Optional R fluency alternative: `Ek dabbe mein zyaada se zyaada 60 pensilein aa sakti hain. Usmein 34 pensilein hain aur unmein se 7 nikaal di jaati hain. Ab usmein zyaada se zyaada kitni pensilein aur rakhi ja sakti hain, taaki kul sankhya 60 se zyaada na ho?`

The optional R alternative repeats the 60 limit more explicitly than E/C; prefer the original R if humans find it fluent, or match the repeated-limit phrasing across all forms. The necessary proposal is the C maximum request, not an automatic R rewrite.

### D. PIL009: improve temporal phrasing without a new loanword

Proposed R: `Saira 9 chipkaane waali parchiyan istemaal karti hai aur uske paas 14 parchiyan bachti hain. Jab Saira ne abhi koi parchi istemaal nahi ki thi, tab Imran ke paas usse 4 zyaada parchiyan thi. Us samay Imran ke paas kitni parchiyan thi?`

This still uses a potentially clumsy sticker paraphrase. A human-frozen policy allowing the conventional loanword `sticker` could support a shorter alternative across all relevant R records, but is a policy decision rather than a unilateral fix. Adding a temporal phrase does not add a solution operation.

### E. PIL016: state that rice is the consumed quantity

Proposed C: `Ek sack mein rakhe chaawal ka 25% use karne ke baad 72 kg chaawal bachta hai. There is no other change in its contents. Originally sack mein kitne kilograms chaawal tha?`

This clarifies the fraction base while retaining the existing English condition and original-amount question. It does not state the remaining percentage or introduce an inverse-operation hint.

### F. PIL019: optional explicit volume wording

Proposed R: `Ek pey banaane ke liye sharbat ke gaadhe ghol aur paani ke aayatan ka anupaat 2:5 rakha jaata hai. Agar 350 mL paani liya jaaye, to kitne millilitre gaadhe ghol ki zaroorat hogi?`

This matches “volume” explicitly but may increase formal-Hindi difficulty. The original mL already signals volume, so this is a human trade-off, not an established critical defect. Humans must confirm that `gaadha ghol` refers to the syrup ingredient. Avoid converting this into an extra explanatory parenthesis present only in R.

### G. PIL025: optional C gender/fluency edit

Proposed C: `Ek cyclist bina ruke 120 km ka safar complete karta hai. The first 40 km are travelled at 20 km per hour, aur remaining distance par speed 40 km per hour hai. Total kitne hours lagte hain?`

This removes awkward `ka journey` while leaving the productive English rate clause and every condition intact. Human speakers may prefer a different natural code-mixing pattern.

### H. PIL026: equal symbolic representation with productive English

Proposed C: `Ek number x hai that satisfies 3x + 7 = 28. x kya hai?`

E and R can remain as currently drafted. The C relative clause `that satisfies 3x + 7 = 28` supplies a productive English predicate, without reading out the equation a second time. Human naturalness is still unresolved. If reviewers prefer verbal equations, rewrite all three forms with matched verbal/symbolic content rather than retaining the duplication only in C.

## Decisions humans still need to make

1. Freeze audience and borrowing policy before assigning R/C labels. Existing proposed shared loan nouns are bus, cycle, jag, tikat and pensil; names, units, mathematical symbols and digits are also shared. `sticker`, `machine`, `tip`, `ratio` or `shelf` must not be inserted into R ad hoc without a documented policy decision.
2. Decide whether productive English verb stems inside Hindi light-verb constructions satisfy C, and annotate such cases separately from full English clauses. Do not demand identical switching locations after seeing model performance.
3. Compare all quantities, entities, units, relations, temporal order, requested unknowns and explicit assumptions after each repair. Formal Hindi terms may be appropriate; the acceptance criterion is actual human ratings, not this AI's stylistic preference.
4. Review the remaining 30-family ancestry and provenance questions independently. This language audit does not establish independence or external-source originality.
5. Keep these suggestions out of an untouched stage1 independent-solving packet. The report reveals comparisons and interpretation concerns and may coach answers, even though it does not provide a complete numerical key.

No proposed edit is a model-performance optimization. No model generations, review ratings, agreement statistics or acceptance statuses were produced here. The reviewed-pilot gate remains closed until genuine human evidence satisfies the unchanged contract, unless a separately declared AI-reviewed exploratory protocol is deliberately designed and labeled as such.
