# A01 adjudication key — do not share before independent solves

**DRAFT — NOT HUMAN-VALIDATED.** Reference calculations are AI-authored and checked programmatically. They can be challenged. A01 is a role placeholder, not evidence of a review.

Collect and preserve both stage1 submissions before revealing this key. Compare independent solutions and stage2 judgments, resolve disagreements with written reasons, and version/re-review text repairs. Check family relationships beyond surface wording.

PROPOSED v1, NOT YET HUMAN-FROZEN: Arabic digits, mathematical symbols, variable names, INR/rupee notation, %, L, mL, m, cm, km, kg, g, h, minute, metre, litre, kilometre, centimetre, millilitre, kilogram, gram, hour and their ordinary Roman spellings may be shared. Established Hindi loan nouns bus, cycle, jag, tikat and pensil are proposed common borrowings. Names are shared entities. R must otherwise use Hindi phrasing in Roman script; substantive English clauses/relations are disallowed. C requires a productive English predicate, clause or mathematical relation alongside Hindi; object nouns alone do not qualify. Reviewers must flag disputed borrowings before the policy is frozen.

## PIL001 — comparison_remaining

Proposed structure: `direct_fewer_than` (independence UNVERIFIED).

- E: Riya has 36 marbles. Aman has 5 fewer marbles than Riya. How many marbles does Aman have?

- R: Riya ke paas 36 kanche hain. Aman ke paas Riya se 5 kam kanche hain. Aman ke paas kitne kanche hain?

- C: Riya ke paas 36 marbles hain. Aman has 5 fewer marbles than Riya. Aman ke paas kitne marbles hain?


Equation: `36 - 5`. Proposed exact gold: **31 marbles**.

Shared English solution: Aman has 5 fewer marbles than Riya, so 36 - 5 = 31. FINAL: 31 marbles

Predeclared unit policy: `{"value": "31", "unit": "marbles", "aliases": ["marble", "kanche", "kancha"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: preserve the comparison's subject and direction. The C English clause carries the mathematical relationship; mark that switching role.

## PIL002 — two_step_money

Proposed structure: `purchase_cost_then_change` (independence UNVERIFIED).

- E: Meena buys 5 notebooks at INR 24 each. She pays the shopkeeper INR 150. How much change should she receive?

- R: Meena ne 5 kaapiyan khareedin. Har kaapi ki keemat INR 24 hai. Usne dukandaar ko INR 150 diye. Use kitne rupaye vaapas milne chahiye?

- C: Meena ne 5 notebooks khareedin; each costs INR 24. Usne shopkeeper ko INR 150 diye. Use kitna change milna chahiye?


Equation: `150 - 5 * 24`. Proposed exact gold: **30 INR**.

Shared English solution: The notebooks cost 5 x 24 = INR 120. The change is 150 - 120 = INR 30. FINAL: INR 30

Predeclared unit policy: `{"value": "30", "unit": "INR", "aliases": ["rupee", "rupees", "rupaye", "rupaya", "rs", "Rs."], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: each notebook costs INR 24, rather than all five together; requested answer is change, rather than purchase cost.

## PIL003 — rates_units

Proposed structure: `initial_stock_plus_rate_times_time` (independence UNVERIFIED).

- E: A tank initially contains 20 L of water. Water is added at 3 L per minute for 4 minutes. No water leaves the tank, and it has enough capacity. How many litres of water are in the tank at the end?

- R: Ek tanki mein pehle se 20 L paani hai. Usmein 4 minute tak har minute 3 L paani dala jaata hai. Koi paani bahar nahi nikalta aur tanki mein is paani ke liye kaafi jagah hai. Aakhir mein tanki mein kul kitne litre paani hoga?

- C: Ek tank mein pehle se 20 L paani hai. Water is added at 3 L per minute for 4 minutes. Koi paani bahar nahi nikalta aur tank mein enough space hai. Aakhir mein total kitne litres paani hoga?


Equation: `20 + 3 * 4`. Proposed exact gold: **32 L**.

Shared English solution: Adding water for 4 minutes adds 3 x 4 = 12 L. The total is 20 + 12 = 32 L. FINAL: 32 L

Predeclared unit policy: `{"value": "32", "unit": "L", "aliases": ["l", "litre", "litres", "liter", "liters"], "conversions": {"mL": "1/1000", "millilitre": "1/1000", "millilitres": "1/1000"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: filling continues for the full interval; no outflow or overflow changes the result. Decide how minute/litre are treated in the borrowing policy.

## PIL004 — fractions_percentages

Proposed structure: `remove_fraction_of_original` (independence UNVERIFIED).

- E: A ribbon is 24 m long. Three-eighths (3/8) of its original length is cut off. What length of ribbon remains, in metres?

- R: Ek feete ki lambai 24 m hai. Uski shuruaati lambai ka 3/8 hissa kaat diya gaya. Bache hue feete ki lambai kitne metre hai?

- C: Ek ribbon ki length 24 m hai. Uski original length ka 3/8 hissa cut kar diya gaya. Ribbon ki remaining length kitne metres hai?


Equation: `24 * (1 - 3/8)`. Proposed exact gold: **15 m**.

Shared English solution: The removed length is 24 x 3/8 = 9 m. The remaining length is 24 - 9 = 15 m. FINAL: 15 m

Predeclared unit policy: `{"value": "15", "unit": "m", "aliases": ["metre", "metres", "meter", "meters"], "conversions": {"cm": "1/100", "centimetre": "1/100", "centimetres": "1/100"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: the removed fraction refers to original length, and the question asks for the remainder. Ask reviewers whether the final R/C sentences need a more natural phrasing.

## PIL005 — ratios

Proposed structure: `total_partition_by_ordered_ratio` (independence UNVERIFIED).

- E: A bag contains only red and blue marbles. The ratio of red marbles to blue marbles is 2:3. There are 30 marbles in total. How many red marbles are there?

- R: Ek thaili mein sirf laal aur neele kanche hain. Laal aur neele kanchon ki sankhya ka anupaat 2:3 hai. Kul 30 kanche hain. Laal kanche kitne hain?

- C: Ek bag mein sirf red aur blue marbles hain. Red to blue ratio 2:3 hai aur total 30 marbles hain. Red marbles kitne hain?


Equation: `30 * 2 / (2 + 3)`. Proposed exact gold: **12 marbles**.

Shared English solution: There are 2 + 3 = 5 ratio parts. Each part is 30/5 = 6 marbles, so there are 2 x 6 = 12 red marbles. FINAL: 12 marbles

Predeclared unit policy: `{"value": "12", "unit": "marbles", "aliases": ["marble", "kanche", "kancha"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: red:blue order, exactly two colours, and naturalness of formal Hindi anupaat versus the English phrase.

## PIL006 — comparison_remaining

Proposed structure: `ordered_stock_changes` (independence UNVERIFIED).

- E: A library has 42 books on a shelf. Readers borrow 13 of them, and then 8 different books are added to that shelf. No other books move. How many books are on the shelf now?

- R: Ek pustakalaya ki ek almaari mein 42 kitaabein hain. Padhne waale unmein se 13 kitaabein le jaate hain, aur phir us almaari mein 8 doosri kitaabein rakhi jaati hain. Koi aur kitaab na nikaali jaati hai na rakhi jaati hai. Ab us almaari mein kitni kitaabein hain?

- C: Ek library ki shelf par 42 books hain. Readers borrow 13 of them, aur phir us shelf par 8 doosri books rakhi jaati hain. No other books move. Ab shelf par kitni books hain?


Equation: `42 - 13 + 8`. Proposed exact gold: **37 books**.

Shared English solution: After borrowing, 42 - 13 = 29 books remain. Adding 8 gives 37. FINAL: 37 books

Predeclared unit policy: `{"value": "37", "unit": "books", "aliases": ["book", "kitaabein", "kitaab"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Preserve the order, the additional books, and the no-other-changes condition.

## PIL007 — comparison_remaining

Proposed structure: `transfer_to_equalize_two_stocks` (independence UNVERIFIED).

- E: Nisha has 28 beads and Kabir has 16 beads. Nisha gives some of her beads to Kabir until they have equal numbers. How many beads does Nisha give Kabir?

- R: Nisha ke paas 28 moti hain aur Kabir ke paas 16 moti hain. Nisha apne kuch moti Kabir ko deti hai, taaki dono ke paas motiyon ki sankhya baraabar ho jaaye. Nisha Kabir ko kitne moti deti hai?

- C: Nisha ke paas 28 beads hain aur Kabir ke paas 16 beads hain. Nisha gives some of her beads to Kabir until their counts are equal. Nisha Kabir ko kitne beads deti hai?


Equation: `(28 - 16) / 2`. Proposed exact gold: **6 beads**.

Shared English solution: Each transferred bead reduces the difference by 2. The difference is 12, so 6 beads are transferred. FINAL: 6 beads

Predeclared unit policy: `{"value": "6", "unit": "beads", "aliases": ["bead", "moti"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: A transfer changes both counts; do not treat this as adding new beads.

## PIL008 — comparison_remaining

Proposed structure: `capacity_after_loss` (independence UNVERIFIED).

- E: A box holds at most 60 pencils. It contains 34 pencils, and 7 of these are removed. What is the greatest number of pencils that can now be added without exceeding the capacity?

- R: Ek dabbe mein zyaada se zyaada 60 pensilein aa sakti hain. Usmein 34 pensilein hain aur unmein se 7 nikaal di jaati hain. Dabbe ki jagah se zyaada bhare bina ab usmein zyaada se zyaada kitni pensilein aur rakhi ja sakti hain?

- C: Ek box mein at most 60 pencils aa sakti hain. Usmein 34 pencils hain aur 7 nikaal di jaati hain. How many more pencils can be added without exceeding the capacity?


Equation: `60 - (34 - 7)`. Proposed exact gold: **33 pencils**.

Shared English solution: There are 34 - 7 = 27 pencils left. The free capacity is 60 - 27 = 33. FINAL: 33 pencils

Predeclared unit policy: `{"value": "33", "unit": "pencils", "aliases": ["pencil", "pensilein", "pensil"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The unknown is additional capacity, not the number remaining; confirm Roman spelling pensilein.

## PIL009 — comparison_remaining

Proposed structure: `recover_original_then_compare` (independence UNVERIFIED).

- E: Saira uses 9 stickers and has 14 stickers left. Before she used any, Imran had 4 more stickers than Saira. How many stickers did Imran have?

- R: Saira 9 chipkaane waali parchiyan istemaal karti hai aur uske paas 14 parchiyan bachti hain. Saira ke parchiyan istemaal karne se pehle, Imran ke paas Saira se 4 zyaada parchiyan thi. Imran ke paas kitni parchiyan thi?

- C: Saira 9 stickers use karti hai aur uske paas 14 stickers bachte hain. Before she used any, Imran had 4 more stickers than Saira. Imran ke paas kitne stickers the?


Equation: `14 + 9 + 4`. Proposed exact gold: **27 stickers**.

Shared English solution: Saira originally had 14 + 9 = 23 stickers. Imran had 4 more, so he had 27. FINAL: 27 stickers

Predeclared unit policy: `{"value": "27", "unit": "stickers", "aliases": ["sticker", "parchiyan", "parchi"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Comparison refers to Saira before use. R description of stickers especially needs naturalness review.

## PIL010 — two_step_money

Proposed structure: `mixed_basket_then_change` (independence UNVERIFIED).

- E: Arun buys 3 pens at INR 18 each and 1 notebook at INR 35. There are no extra charges. He pays INR 200. How much change does he receive?

- R: Arun 3 kalamein khareedta hai, har kalam INR 18 ki, aur 1 kaapi INR 35 ki. Koi aur paisa nahi liya jaata. Vah INR 200 deta hai. Use kitne rupaye vaapas milte hain?

- C: Arun 3 pens khareedta hai; each pen costs INR 18, aur 1 notebook INR 35 ki hai. There are no extra charges. Vah INR 200 deta hai. Use kitna change milta hai?


Equation: `200 - (3 * 18 + 35)`. Proposed exact gold: **111 INR**.

Shared English solution: The basket costs 54 + 35 = INR 89. The change is 200 - 89 = INR 111. FINAL: INR 111

Predeclared unit policy: `{"value": "111", "unit": "INR", "aliases": ["rupee", "rupees", "rupaye", "rupaya", "rs", "Rs."], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Both product prices are per item; assess overlap with PIL002 despite the additional basket term.

## PIL011 — two_step_money

Proposed structure: `partial_refund_less_fixed_fee` (independence UNVERIFIED).

- E: Three tickets cost INR 180 in total and have equal prices. One ticket is cancelled. Its full price is refunded, but INR 15 is deducted from that refund as a cancellation fee. How much money is returned?

- R: 3 tikaton ki kul keemat INR 180 hai aur har tikat ki keemat baraabar hai. 1 tikat radd ki jaati hai. Uski poori keemat vaapas ki jaati hai, lekin radd karne ke shulk ke taur par usi rakam mein se INR 15 kaat liye jaate hain. Kitne rupaye vaapas milte hain?

- C: 3 tickets ki total keemat INR 180 hai aur sabki keemat baraabar hai. 1 ticket cancel hoti hai. Its full price is refunded, but INR 15 is deducted from that refund as a cancellation fee. Kitne rupaye vaapas milte hain?


Equation: `180 / 3 - 15`. Proposed exact gold: **45 INR**.

Shared English solution: One ticket costs INR 60. Deducting INR 15 leaves INR 45. FINAL: INR 45

Predeclared unit policy: `{"value": "45", "unit": "INR", "aliases": ["rupee", "rupees", "rupaye", "rupaya", "rs", "Rs."], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The fee is deducted once, from the one-ticket refund, not the entire prepaid sum.

## PIL012 — two_step_money

Proposed structure: `equal_bill_share_plus_individual_tip` (independence UNVERIFIED).

- E: Four friends split an INR 216 food bill equally. Each friend then pays an additional INR 9 tip. How much does each friend pay in total?

- R: 4 dost khaane ka INR 216 ka kharch baraabar baantte hain. Phir har dost apni taraf se INR 9 bakhshish aur deta hai. Har dost kul kitne rupaye deta hai?

- C: 4 dost INR 216 ka food bill equally split karte hain. Each friend then pays an additional INR 9 tip. Har dost total kitne rupaye deta hai?


Equation: `216 / 4 + 9`. Proposed exact gold: **63 INR**.

Shared English solution: Each bill share is INR 54. Adding the individual tip gives INR 63. FINAL: INR 63

Predeclared unit policy: `{"value": "63", "unit": "INR", "aliases": ["rupee", "rupees", "rupaye", "rupaya", "rs", "Rs."], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: INR 9 is per friend, not a single shared tip; review bakhshish naturalness.

## PIL013 — two_step_money

Proposed structure: `budget_with_fixed_fee_maximum_count` (independence UNVERIFIED).

- E: Leela can spend at most INR 150. A delivery fee of INR 30 is charged once for the order. Each pen costs INR 20, and there are no other charges. What is the greatest number of pens she can buy?

- R: Leela zyaada se zyaada INR 150 kharch kar sakti hai. Poore saamaan ko ghar pahunchane ke liye ek hi baar INR 30 liye jaate hain. Har kalam ki keemat INR 20 hai aur koi aur paisa nahi liya jaata. Vah zyaada se zyaada kitni kalamein khareed sakti hai?

- C: Leela at most INR 150 kharch kar sakti hai. A delivery fee of INR 30 is charged once for the order. Har pen INR 20 ka hai aur koi aur charge nahi hai. Maximum kitne pens khareed sakti hai?


Equation: `(150 - 30) / 20`. Proposed exact gold: **6 pens**.

Shared English solution: After delivery, INR 120 remains. At INR 20 each, at most 6 pens can be bought. FINAL: 6 pens

Predeclared unit policy: `{"value": "6", "unit": "pens", "aliases": ["pen", "kalamein", "kalam"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: A fixed once-per-order fee differs from a per-pen fee. All pens are whole objects.

## PIL014 — fractions_percentages

Proposed structure: `fraction_of_subgroup` (independence UNVERIFIED).

- E: A class has 40 students. Girls make up 2/5 of the class, and 3/4 of those girls attend a music club. How many girls in the class attend the music club?

- R: Ek kaksha mein 40 vidyarthi hain. Unmein se 2/5 ladkiyan hain, aur un ladkiyon mein se 3/4 sangeet ki mandali mein jaati hain. Kaksha ki kitni ladkiyan sangeet ki mandali mein jaati hain?

- C: Ek class mein 40 students hain. Girls make up 2/5 of the class, aur un girls mein se 3/4 music club attend karti hain. Class ki kitni girls music club attend karti hain?


Equation: `40 * 2/5 * 3/4`. Proposed exact gold: **12 girls**.

Shared English solution: There are 16 girls. Three quarters of 16 is 12. FINAL: 12 girls

Predeclared unit policy: `{"value": "12", "unit": "girls", "aliases": ["girl", "ladkiyan", "ladki"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The second fraction is of girls, not of the whole class.

## PIL015 — fractions_percentages

Proposed structure: `successive_percentage_changes` (independence UNVERIFIED).

- E: An item costs INR 200 before discounts. Its price is reduced by 20%, and then the reduced price is reduced by a further 10%. What is the final price, with no other charges?

- R: Chhooton se pehle ek cheez ki keemat INR 200 hai. Pehle keemat 20% ghataayi jaati hai, aur phir ghati hui keemat ko 10% aur ghataaya jaata hai. Koi aur paisa nahi liya jaata. Aakhiri keemat kitne rupaye hai?

- C: Discounts se pehle ek item ki keemat INR 200 hai. Its price is reduced by 20%, aur phir reduced price par 10% aur discount milta hai. No other charges hain. Final price kitne rupaye hai?


Equation: `200 * (1 - 20/100) * (1 - 10/100)`. Proposed exact gold: **144 INR**.

Shared English solution: After the first discount the price is INR 160. Reducing that by 10% leaves INR 144. FINAL: INR 144

Predeclared unit policy: `{"value": "144", "unit": "INR", "aliases": ["rupee", "rupees", "rupaye", "rupaya", "rs", "Rs."], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The second discount applies to the reduced price; percentages cannot simply be added.

## PIL016 — fractions_percentages

Proposed structure: `recover_whole_from_remaining_percent` (independence UNVERIFIED).

- E: After 25% of a sack of rice is used, 72 kg remains. There is no other change in its contents. How many kilograms of rice were in the sack originally?

- R: Chaawal ki ek bori ka 25% chaawal istemaal karne ke baad 72 kg chaawal bachta hai. Usmein aur koi badlaav nahi hota. Shuru mein bori mein kitne kilogram chaawal tha?

- C: Chaawal ki ek sack ka 25% use karne ke baad 72 kg bachta hai. There is no other change in its contents. Originally sack mein kitne kilograms chaawal tha?


Equation: `72 / (1 - 25/100)`. Proposed exact gold: **96 kg**.

Shared English solution: The remaining 72 kg is 75% of the original. The original is 72 / (3/4) = 96 kg. FINAL: 96 kg

Predeclared unit policy: `{"value": "96", "unit": "kg", "aliases": ["kilogram", "kilograms"], "conversions": {"g": "1/1000", "gram": "1/1000", "grams": "1/1000"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Remaining versus used percentage; kg/kilogram is a proposed standard unit borrowing.

## PIL017 — fractions_percentages

Proposed structure: `fractional_quantity_equal_shares` (independence UNVERIFIED).

- E: A jug contains 3/4 L of juice. All of it is shared equally among 3 children, with none spilled. How many litres of juice does each child receive?

- R: Ek jag mein 3/4 L ras hai. Poora ras 3 bachchon mein baraabar baanta jaata hai aur kuch bhi nahi girta. Har bachche ko kitne litre ras milta hai?

- C: Ek jug mein 3/4 L juice hai. All of it is shared equally among 3 children, aur kuch bhi spill nahi hota. Har child ko kitne litres juice milta hai?


Equation: `(3/4) / 3`. Proposed exact gold: **1/4 L**.

Shared English solution: Dividing 3/4 L equally among 3 children gives 1/4 L each. FINAL: 1/4 L

Predeclared unit policy: `{"value": "1/4", "unit": "L", "aliases": ["l", "litre", "litres", "liter", "liters"], "conversions": {"mL": "1/1000", "millilitre": "1/1000", "millilitres": "1/1000"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Division of a fraction, equal sharing, and complete distribution must be unchanged.

## PIL018 — ratios

Proposed structure: `ratio_with_difference` (independence UNVERIFIED).

- E: Two positive numbers are in the ratio 5:3. The larger number exceeds the smaller by 14. What is the larger number?

- R: 2 dhanaatmak sankhyaon ka anupaat 5:3 hai. Badi sankhya chhoti sankhya se 14 zyaada hai. Badi sankhya kya hai?

- C: 2 positive numbers ka ratio 5:3 hai. The larger number exceeds the smaller by 14. Bada number kya hai?


Equation: `14 / (5 - 3) * 5`. Proposed exact gold: **35 **.

Shared English solution: The difference is 2 parts, so each part is 7. The larger number is 5 * 7 = 35. FINAL: 35

Predeclared unit policy: `{"value": "35", "unit": "", "aliases": [], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Difference is not total; assess formal Hindi vocabulary and C phrasing.

## PIL019 — ratios

Proposed structure: `mixture_component_given_other_component` (independence UNVERIFIED).

- E: A drink is prepared with syrup and water in the volume ratio 2:5. If 350 mL of water is used, how many millilitres of syrup are needed?

- R: Ek pey mein sharbat ke gaadhe ghol aur paani ki maatra ka anupaat 2:5 rakha jaata hai. Agar 350 mL paani liya jaaye, to kitne millilitre gaadhe ghol ki zaroorat hogi?

- C: Ek drink mein syrup aur water ka volume ratio 2:5 hai. If 350 mL of water is used, kitne millilitres syrup chahiye?


Equation: `350 * 2 / 5`. Proposed exact gold: **140 mL**.

Shared English solution: Five water parts total 350 mL, so one part is 70 mL. Two syrup parts require 140 mL. FINAL: 140 mL

Predeclared unit policy: `{"value": "140", "unit": "mL", "aliases": ["ml", "millilitre", "millilitres", "milliliter", "milliliters"], "conversions": {"L": "1000", "litre": "1000", "litres": "1000"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The known amount is water alone. Confirm R gaadha ghol denotes the syrup component rather than the finished drink.

## PIL020 — ratios

Proposed structure: `compose_two_ratios_shared_middle` (independence UNVERIFIED).

- E: Positive quantities A, B and C satisfy A:B = 2:3 and B:C = 4:5. What is A/C? Give a number or fraction.

- R: Dhanaatmak maatraon A, B aur C ke liye A:B = 2:3 aur B:C = 4:5 hai. A/C ka maan kya hai? Ek sankhya ya bhinn mein bataaiye.

- C: Positive quantities A, B aur C ke liye A:B = 2:3 hai, and B:C equals 4:5. A/C kya hai? Give a number or fraction.


Equation: `(2/3) * (4/5)`. Proposed exact gold: **8/15 **.

Shared English solution: A/C = (A/B) * (B/C) = (2/3) * (4/5) = 8/15. FINAL: 8/15

Predeclared unit policy: `{"value": "8/15", "unit": "", "aliases": [], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The requested scalar is A/C, not a colon-form answer. All quantities are positive.

## PIL021 — ratios

Proposed structure: `change_one_component_then_recompute_ratio` (independence UNVERIFIED).

- E: A box contains only red and blue balls in the ratio 3:4. It contains 15 red balls. Then 5 blue balls are added and none are removed. What is the new ratio of red balls to blue balls? Give it as a number or fraction, red count divided by blue count.

- R: Ek dabbe mein sirf laal aur neeli gendein hain aur unki sankhya ka anupaat 3:4 hai. Laal gendein 15 hain. Phir 5 neeli gendein aur daali jaati hain aur koi gend nikaali nahi jaati. Ab laal aur neeli gendon ki sankhya ka naya anupaat kya hai? Laal gendon ki sankhya ko neeli gendon ki sankhya se bhaag dekar sankhya ya bhinn mein bataaiye.

- C: Ek box mein sirf red aur blue balls hain, ratio 3:4 hai, aur red balls 15 hain. Then 5 blue balls are added and none are removed. Naya red-to-blue ratio kya hai? Give red count divided by blue count as a number or fraction.


Equation: `15 / (15 * 4/3 + 5)`. Proposed exact gold: **3/5 **.

Shared English solution: Initially there are 20 blue balls. After adding 5, the red-to-blue ratio is 15/25 = 3/5. FINAL: 3/5

Predeclared unit policy: `{"value": "3/5", "unit": "", "aliases": [], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: New ratio versus old ratio, red/blue order, and scalar-answer convention. Assess overlap with PIL005.

## PIL022 — rates_units

Proposed structure: `speed_with_minutes_to_hours` (independence UNVERIFIED).

- E: A bus travels at a constant speed of 60 km per hour for 45 minutes, without stopping. How many kilometres does it travel?

- R: Ek bus bina ruke 45 minute tak lagaataar 60 km prati ghante ki raftaar se chalti hai. Vah kitne kilometre chalti hai?

- C: Ek bus 45 minutes tak bina ruke chalti hai, at a constant speed of 60 km per hour. Vah kitne kilometres travel karti hai?


Equation: `60 * 45 / 60`. Proposed exact gold: **45 km**.

Shared English solution: 45 minutes is 3/4 hour. The distance is 60 * 3/4 = 45 km. FINAL: 45 km

Predeclared unit policy: `{"value": "45", "unit": "km", "aliases": ["kilometre", "kilometres", "kilometer", "kilometers"], "conversions": {"m": "1/1000", "metre": "1/1000", "metres": "1/1000"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Minutes must become hours; the constant speed and no-stop assumptions must match.

## PIL023 — rates_units

Proposed structure: `convert_length_then_count_segments` (independence UNVERIFIED).

- E: A 2.4 m cord is cut into pieces exactly 30 cm long. Cutting loses no length and the whole cord is used. How many pieces are made?

- R: 2.4 m lambi ek dori ko theek 30 cm lambe tukdon mein kaata jaata hai. Kaatne mein koi lambai nahi ghatti aur poori dori istemaal hoti hai. Kitne tukde bante hain?

- C: 2.4 m lambi cord ko exactly 30 cm long pieces mein cut kiya jaata hai. Cutting loses no length aur poori cord use hoti hai. Kitne pieces bante hain?


Equation: `2.4 * 100 / 30`. Proposed exact gold: **8 pieces**.

Shared English solution: The cord is 240 cm long. At 30 cm per piece, it makes 8 pieces. FINAL: 8 pieces

Predeclared unit policy: `{"value": "8", "unit": "pieces", "aliases": ["piece", "tukde", "tukda"], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Length units differ and no kerf is lost; count is not a length.

## PIL024 — rates_units

Proposed structure: `simultaneous_additive_work_rates` (independence UNVERIFIED).

- E: Two machines work together without stopping. One seals 6 boxes per minute and the other seals 4 different boxes per minute. How many minutes do they need to seal 90 boxes in total?

- R: 2 yantra bina ruke ek saath kaam karte hain. Ek har minute 6 dabbe band karta hai aur doosra har minute 4 alag dabbe band karta hai. Dono milkar kul 90 dabbe band karne mein kitne minute lenge?

- C: 2 machines bina ruke ek saath kaam karti hain. One seals 6 boxes per minute and the other seals 4 different boxes per minute. Total 90 boxes seal karne mein kitne minutes lagenge?


Equation: `90 / (6 + 4)`. Proposed exact gold: **9 minute**.

Shared English solution: Together the machines seal 10 boxes per minute. They need 90/10 = 9 minutes. FINAL: 9 minute

Predeclared unit policy: `{"value": "9", "unit": "minute", "aliases": ["minutes", "min"], "conversions": {"h": "60", "hour": "60", "hours": "60"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Rates add because the machines process distinct boxes simultaneously; review yantra naturalness.

## PIL025 — rates_units

Proposed structure: `piecewise_journey_times` (independence UNVERIFIED).

- E: A cyclist completes a 120 km journey without stops. The first 40 km are travelled at 20 km per hour and the remaining distance at 40 km per hour. How many hours does the journey take?

- R: Ek cycle savaar bina ruke 120 km ka safar poora karta hai. Pehle 40 km vah 20 km prati ghante ki raftaar se chalta hai aur baaki doori 40 km prati ghante ki raftaar se. Safar mein kul kitne ghante lagte hain?

- C: Ek cyclist bina ruke 120 km ka journey complete karta hai. The first 40 km are travelled at 20 km per hour, aur remaining distance par speed 40 km per hour hai. Total kitne hours lagte hain?


Equation: `40 / 20 + (120 - 40) / 40`. Proposed exact gold: **4 h**.

Shared English solution: The first segment takes 2 hours and the remaining 80 km takes 2 hours. Total time is 4 hours. FINAL: 4 h

Predeclared unit policy: `{"value": "4", "unit": "h", "aliases": ["hour", "hours", "ghante", "ghanta"], "conversions": {"minute": "1/60", "minutes": "1/60", "min": "1/60"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: The remaining distance is 80 km; do not average speeds arithmetically.

## PIL026 — elementary_algebra

Proposed structure: `direct_linear_equation` (independence UNVERIFIED).

- E: A number x satisfies 3x + 7 = 28. What is x?

- R: Ek sankhya x ke liye 3x + 7 = 28 hai. x ka maan kya hai?

- C: Ek number x ke liye three times x plus 7 equals 28, yaani 3x + 7 = 28. x kya hai?


Equation: `(28 - 7) / 3`. Proposed exact gold: **7 **.

Shared English solution: Subtracting 7 gives 3x = 21. Dividing by 3 gives x = 7. FINAL: 7

Predeclared unit policy: `{"value": "7", "unit": "", "aliases": [], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: C verbalizes the relation while retaining the equation; document this additional surface redundancy.

## PIL027 — elementary_algebra

Proposed structure: `consecutive_integer_sum` (independence UNVERIFIED).

- E: The sum of two consecutive integers is 41. What is the smaller integer?

- R: 2 lagaataar poornankon ka yog 41 hai. Chhota poornank kya hai?

- C: 2 consecutive integers ka sum 41 hai. What is the smaller integer?


Equation: `(41 - 1) / 2`. Proposed exact gold: **20 **.

Shared English solution: Let the smaller integer be x. Then x + (x + 1) = 41, so x = 20. FINAL: 20

Predeclared unit policy: `{"value": "20", "unit": "", "aliases": [], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Consecutive means a difference of 1, not consecutive odd integers; review poornank vocabulary.

## PIL028 — elementary_algebra

Proposed structure: `rectangle_perimeter_inverse` (independence UNVERIFIED).

- E: A rectangle has perimeter 50 cm and width 9 cm. What is its length in centimetres?

- R: Ek aayat ka parimaap 50 cm hai aur chaudaai 9 cm hai. Uski lambai kitne centimetre hai?

- C: Ek rectangle ka perimeter 50 cm hai aur width 9 cm hai. What is its length in centimetres?


Equation: `50 / 2 - 9`. Proposed exact gold: **16 cm**.

Shared English solution: The length plus width is 25 cm. Subtracting the 9 cm width gives a length of 16 cm. FINAL: 16 cm

Predeclared unit policy: `{"value": "16", "unit": "cm", "aliases": ["centimetre", "centimetres", "centimeter", "centimeters"], "conversions": {"m": "100", "metre": "100", "metres": "100"}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Perimeter versus area; assess standard educational Hindi aayat/parimaap naturalness.

## PIL029 — elementary_algebra

Proposed structure: `eliminate_shared_unknown_price` (independence UNVERIFIED).

- E: Two pens and one notebook cost INR 58. One pen and one notebook cost INR 39. All pens have the same price and all notebooks have the same price. What is the price of one pen?

- R: 2 kalamein aur 1 kaapi milkar INR 58 ki hain. 1 kalam aur 1 kaapi milkar INR 39 ki hain. Sab kalamon ki keemat ek jaisi hai aur sab kaapiyon ki keemat ek jaisi hai. 1 kalam ki keemat kitne rupaye hai?

- C: 2 pens aur 1 notebook ki total cost INR 58 hai. One pen and one notebook cost INR 39. Sab pens ki price ek jaisi hai aur sab notebooks ki price ek jaisi hai. 1 pen ki price kitne rupaye hai?


Equation: `58 - 39`. Proposed exact gold: **19 INR**.

Shared English solution: Subtracting the two baskets cancels the notebook and one pen. The extra pen costs INR 19. FINAL: INR 19

Predeclared unit policy: `{"value": "19", "unit": "INR", "aliases": ["rupee", "rupees", "rupaye", "rupaya", "rs", "Rs."], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Shared prices are invariant; the asked unknown is one pen rather than the notebook.

## PIL030 — elementary_algebra

Proposed structure: `positive_square_root_domain` (independence UNVERIFIED).

- E: A positive number x satisfies x squared equals 49. What is x?

- R: Ek dhanaatmak sankhya x ka varg 49 hai. x ka maan kya hai?

- C: Ek positive number x hai, and x squared equals 49. x kya hai?


Equation: `x^2 = 49; x > 0; x = 7`. Proposed exact gold: **7 **.

Shared English solution: Both 7 and -7 have square 49, but x is positive. Therefore x = 7. FINAL: 7

Predeclared unit policy: `{"value": "7", "unit": "", "aliases": [], "conversions": {}, "unit_omission_allowed": true, "rounding_rule": "exact"}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.

Review focus: Positivity is essential: exactly one root is requested. The reference check also verifies 7 squared is 49.
