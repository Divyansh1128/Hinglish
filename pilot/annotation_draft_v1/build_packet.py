"""Build unvalidated review materials, never accepted experimental inputs.

Run with Python 3.10+, standard library only. No model outputs inform these drafts.
Original PIL001–005 wording is read verbatim from the governing review packet.
"""
from pathlib import Path
from fractions import Fraction as F
from collections import Counter
import hashlib
import html
import json
import random
import re
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
VERSION = 'pilot-draft-v1'
FORMS = ('E', 'R', 'C')
BORROWING = ('PROPOSED v1, NOT YET HUMAN-FROZEN: Arabic digits, mathematical symbols, '
             'variable names, INR/rupee notation, %, L, mL, m, cm, km, kg, g, h, minute, '
             'metre, litre, kilometre, centimetre, millilitre, kilogram, gram, hour and their ordinary Roman spellings may be shared. '
             'Established Hindi loan nouns bus, cycle, jag, tikat and pensil are proposed common borrowings. '
             'Names are shared entities. R must otherwise use Hindi phrasing in '
             'Roman script; substantive English clauses/relations are disallowed. '
             'C requires a productive English predicate, clause or mathematical '
             'relation alongside Hindi; object nouns alone do not qualify. '
             'Reviewers must flag disputed borrowings before the policy is frozen.')

def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n' if not isinstance(value, str) else value, encoding='utf-8')

def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def seed(n, topic, structure, texts, value, unit, equation, solution, calculation, focus, roles):
    assert len(texts) == 3
    assert F(value) == calculation, (n, value, calculation)
    return dict(n=n, topic=topic, structure=structure, texts=texts, value=value,
                unit=unit, equation=equation, solution=solution, calculation=str(calculation),
                focus=focus, roles=roles)

def seeds():
    packet = (ROOT / 'pilot_review_packet.md').read_text(encoding='utf-8')
    prior = []
    specs = [
        ('comparison_remaining', 'direct_fewer_than', '31', 'marbles', '36 - 5', F(36)-5, ['comparison']),
        ('two_step_money', 'purchase_cost_then_change', '30', 'INR', '150 - 5 * 24', F(150)-5*24, ['unit_price']),
        ('rates_units', 'initial_stock_plus_rate_times_time', '32', 'L', '20 + 3 * 4', F(20)+3*4, ['rate']),
        ('fractions_percentages', 'remove_fraction_of_original', '15', 'm', '24 * (1 - 3/8)', F(24)*(1-F(3,8)), ['fraction_base', 'operation', 'requested_answer']),
        ('ratios', 'total_partition_by_ordered_ratio', '12', 'marbles', '30 * 2 / (2 + 3)', F(30)*2/5, ['ratio_order', 'total']),
    ]
    for n, spec in enumerate(specs, 1):
        section = packet.split(f'### PIL{n:03d}:', 1)[1].split('\n### ', 1)[0]
        texts = [re.search(rf'^- {form}: (.+)$', section, re.M).group(1) for form in FORMS]
        solution = re.search(r'^- Shared English solution: (.+)$', section, re.M).group(1)
        focus = re.search(r'^- Review focus: (.+)$', section, re.M).group(1)
        topic, structure, value, unit, equation, calculation, roles = spec
        prior.append(seed(n, topic, structure, texts, value, unit, equation, solution, calculation, focus, roles))
    return prior + [
        seed(6, 'comparison_remaining', 'ordered_stock_changes', [
            'A library has 42 books on a shelf. Readers borrow 13 of them, and then 8 different books are added to that shelf. No other books move. How many books are on the shelf now?',
            'Ek pustakalaya ki ek almaari mein 42 kitaabein hain. Padhne waale unmein se 13 kitaabein le jaate hain, aur phir us almaari mein 8 doosri kitaabein rakhi jaati hain. Koi aur kitaab na nikaali jaati hai na rakhi jaati hai. Ab us almaari mein kitni kitaabein hain?',
            'Ek library ki shelf par 42 books hain. Readers borrow 13 of them, aur phir us shelf par 8 doosri books rakhi jaati hain. No other books move. Ab shelf par kitni books hain?'
        ], '37', 'books', '42 - 13 + 8', 'After borrowing, 42 - 13 = 29 books remain. Adding 8 gives 37. FINAL: 37 books', F(42)-13+8,
             'Preserve the order, the additional books, and the no-other-changes condition.', ['subtraction', 'negation']),
        seed(7, 'comparison_remaining', 'transfer_to_equalize_two_stocks', [
            'Nisha has 28 beads and Kabir has 16 beads. Nisha gives some of her beads to Kabir until they have equal numbers. How many beads does Nisha give Kabir?',
            'Nisha ke paas 28 moti hain aur Kabir ke paas 16 moti hain. Nisha apne kuch moti Kabir ko deti hai, taaki dono ke paas motiyon ki sankhya baraabar ho jaaye. Nisha Kabir ko kitne moti deti hai?',
            'Nisha ke paas 28 beads hain aur Kabir ke paas 16 beads hain. Nisha gives some of her beads to Kabir until their counts are equal. Nisha Kabir ko kitne beads deti hai?'
        ], '6', 'beads', '(28 - 16) / 2', 'Each transferred bead reduces the difference by 2. The difference is 12, so 6 beads are transferred. FINAL: 6 beads', F(28-16,2),
             'A transfer changes both counts; do not treat this as adding new beads.', ['transfer', 'equality']),
        seed(8, 'comparison_remaining', 'capacity_after_loss', [
            'A box holds at most 60 pencils. It contains 34 pencils, and 7 of these are removed. What is the greatest number of pencils that can now be added without exceeding the capacity?',
            'Ek dabbe mein zyaada se zyaada 60 pensilein aa sakti hain. Usmein 34 pensilein hain aur unmein se 7 nikaal di jaati hain. Dabbe ki jagah se zyaada bhare bina ab usmein zyaada se zyaada kitni pensilein aur rakhi ja sakti hain?',
            'Ek box mein at most 60 pencils aa sakti hain. Usmein 34 pencils hain aur 7 nikaal di jaati hain. How many more pencils can be added without exceeding the capacity?'
        ], '33', 'pencils', '60 - (34 - 7)', 'There are 34 - 7 = 27 pencils left. The free capacity is 60 - 27 = 33. FINAL: 33 pencils', F(60)-(34-7),
             'The unknown is additional capacity, not the number remaining; confirm Roman spelling pensilein.', ['capacity', 'requested_answer']),
        seed(9, 'comparison_remaining', 'recover_original_then_compare', [
            'Saira uses 9 stickers and has 14 stickers left. Before she used any, Imran had 4 more stickers than Saira. How many stickers did Imran have?',
            'Saira 9 chipkaane waali parchiyan istemaal karti hai aur uske paas 14 parchiyan bachti hain. Saira ke parchiyan istemaal karne se pehle, Imran ke paas Saira se 4 zyaada parchiyan thi. Imran ke paas kitni parchiyan thi?',
            'Saira 9 stickers use karti hai aur uske paas 14 stickers bachte hain. Before she used any, Imran had 4 more stickers than Saira. Imran ke paas kitne stickers the?'
        ], '27', 'stickers', '14 + 9 + 4', 'Saira originally had 14 + 9 = 23 stickers. Imran had 4 more, so he had 27. FINAL: 27 stickers', F(14)+9+4,
             'Comparison refers to Saira before use. R description of stickers especially needs naturalness review.', ['time_condition', 'comparison']),
        seed(10, 'two_step_money', 'mixed_basket_then_change', [
            'Arun buys 3 pens at INR 18 each and 1 notebook at INR 35. There are no extra charges. He pays INR 200. How much change does he receive?',
            'Arun 3 kalamein khareedta hai, har kalam INR 18 ki, aur 1 kaapi INR 35 ki. Koi aur paisa nahi liya jaata. Vah INR 200 deta hai. Use kitne rupaye vaapas milte hain?',
            'Arun 3 pens khareedta hai; each pen costs INR 18, aur 1 notebook INR 35 ki hai. There are no extra charges. Vah INR 200 deta hai. Use kitna change milta hai?'
        ], '111', 'INR', '200 - (3 * 18 + 35)', 'The basket costs 54 + 35 = INR 89. The change is 200 - 89 = INR 111. FINAL: INR 111', F(200)-(3*18+35),
             'Both product prices are per item; assess overlap with PIL002 despite the additional basket term.', ['unit_price', 'negation']),
        seed(11, 'two_step_money', 'partial_refund_less_fixed_fee', [
            'Three tickets cost INR 180 in total and have equal prices. One ticket is cancelled. Its full price is refunded, but INR 15 is deducted from that refund as a cancellation fee. How much money is returned?',
            '3 tikaton ki kul keemat INR 180 hai aur har tikat ki keemat baraabar hai. 1 tikat radd ki jaati hai. Uski poori keemat vaapas ki jaati hai, lekin radd karne ke shulk ke taur par usi rakam mein se INR 15 kaat liye jaate hain. Kitne rupaye vaapas milte hain?',
            '3 tickets ki total keemat INR 180 hai aur sabki keemat baraabar hai. 1 ticket cancel hoti hai. Its full price is refunded, but INR 15 is deducted from that refund as a cancellation fee. Kitne rupaye vaapas milte hain?'
        ], '45', 'INR', '180 / 3 - 15', 'One ticket costs INR 60. Deducting INR 15 leaves INR 45. FINAL: INR 45', F(180,3)-15,
             'The fee is deducted once, from the one-ticket refund, not the entire prepaid sum.', ['refund', 'deduction']),
        seed(12, 'two_step_money', 'equal_bill_share_plus_individual_tip', [
            'Four friends split an INR 216 food bill equally. Each friend then pays an additional INR 9 tip. How much does each friend pay in total?',
            '4 dost khaane ka INR 216 ka kharch baraabar baantte hain. Phir har dost apni taraf se INR 9 bakhshish aur deta hai. Har dost kul kitne rupaye deta hai?',
            '4 dost INR 216 ka food bill equally split karte hain. Each friend then pays an additional INR 9 tip. Har dost total kitne rupaye deta hai?'
        ], '63', 'INR', '216 / 4 + 9', 'Each bill share is INR 54. Adding the individual tip gives INR 63. FINAL: INR 63', F(216,4)+9,
             'INR 9 is per friend, not a single shared tip; review bakhshish naturalness.', ['equal_division', 'individual_addition']),
        seed(13, 'two_step_money', 'budget_with_fixed_fee_maximum_count', [
            'Leela can spend at most INR 150. A delivery fee of INR 30 is charged once for the order. Each pen costs INR 20, and there are no other charges. What is the greatest number of pens she can buy?',
            'Leela zyaada se zyaada INR 150 kharch kar sakti hai. Poore saamaan ko ghar pahunchane ke liye ek hi baar INR 30 liye jaate hain. Har kalam ki keemat INR 20 hai aur koi aur paisa nahi liya jaata. Vah zyaada se zyaada kitni kalamein khareed sakti hai?',
            'Leela at most INR 150 kharch kar sakti hai. A delivery fee of INR 30 is charged once for the order. Har pen INR 20 ka hai aur koi aur charge nahi hai. Maximum kitne pens khareed sakti hai?'
        ], '6', 'pens', '(150 - 30) / 20', 'After delivery, INR 120 remains. At INR 20 each, at most 6 pens can be bought. FINAL: 6 pens', F(150-30,20),
             'A fixed once-per-order fee differs from a per-pen fee. All pens are whole objects.', ['budget_bound', 'fixed_fee']),
        seed(14, 'fractions_percentages', 'fraction_of_subgroup', [
            'A class has 40 students. Girls make up 2/5 of the class, and 3/4 of those girls attend a music club. How many girls in the class attend the music club?',
            'Ek kaksha mein 40 vidyarthi hain. Unmein se 2/5 ladkiyan hain, aur un ladkiyon mein se 3/4 sangeet ki mandali mein jaati hain. Kaksha ki kitni ladkiyan sangeet ki mandali mein jaati hain?',
            'Ek class mein 40 students hain. Girls make up 2/5 of the class, aur un girls mein se 3/4 music club attend karti hain. Class ki kitni girls music club attend karti hain?'
        ], '12', 'girls', '40 * 2/5 * 3/4', 'There are 16 girls. Three quarters of 16 is 12. FINAL: 12 girls', F(40)*F(2,5)*F(3,4),
             'The second fraction is of girls, not of the whole class.', ['fraction_base', 'subgroup']),
        seed(15, 'fractions_percentages', 'successive_percentage_changes', [
            'An item costs INR 200 before discounts. Its price is reduced by 20%, and then the reduced price is reduced by a further 10%. What is the final price, with no other charges?',
            'Chhooton se pehle ek cheez ki keemat INR 200 hai. Pehle keemat 20% ghataayi jaati hai, aur phir ghati hui keemat ko 10% aur ghataaya jaata hai. Koi aur paisa nahi liya jaata. Aakhiri keemat kitne rupaye hai?',
            'Discounts se pehle ek item ki keemat INR 200 hai. Its price is reduced by 20%, aur phir reduced price par 10% aur discount milta hai. No other charges hain. Final price kitne rupaye hai?'
        ], '144', 'INR', '200 * (1 - 20/100) * (1 - 10/100)', 'After the first discount the price is INR 160. Reducing that by 10% leaves INR 144. FINAL: INR 144', F(200)*F(80,100)*F(90,100),
             'The second discount applies to the reduced price; percentages cannot simply be added.', ['percentage_change', 'fraction_base']),
        seed(16, 'fractions_percentages', 'recover_whole_from_remaining_percent', [
            'After 25% of a sack of rice is used, 72 kg remains. There is no other change in its contents. How many kilograms of rice were in the sack originally?',
            'Chaawal ki ek bori ka 25% chaawal istemaal karne ke baad 72 kg chaawal bachta hai. Usmein aur koi badlaav nahi hota. Shuru mein bori mein kitne kilogram chaawal tha?',
            'Chaawal ki ek sack ka 25% use karne ke baad 72 kg bachta hai. There is no other change in its contents. Originally sack mein kitne kilograms chaawal tha?'
        ], '96', 'kg', '72 / (1 - 25/100)', 'The remaining 72 kg is 75% of the original. The original is 72 / (3/4) = 96 kg. FINAL: 96 kg', F(72)/F(3,4),
             'Remaining versus used percentage; kg/kilogram is a proposed standard unit borrowing.', ['remaining_percentage', 'requested_answer']),
        seed(17, 'fractions_percentages', 'fractional_quantity_equal_shares', [
            'A jug contains 3/4 L of juice. All of it is shared equally among 3 children, with none spilled. How many litres of juice does each child receive?',
            'Ek jag mein 3/4 L ras hai. Poora ras 3 bachchon mein baraabar baanta jaata hai aur kuch bhi nahi girta. Har bachche ko kitne litre ras milta hai?',
            'Ek jug mein 3/4 L juice hai. All of it is shared equally among 3 children, aur kuch bhi spill nahi hota. Har child ko kitne litres juice milta hai?'
        ], '1/4', 'L', '(3/4) / 3', 'Dividing 3/4 L equally among 3 children gives 1/4 L each. FINAL: 1/4 L', F(3,4)/3,
             'Division of a fraction, equal sharing, and complete distribution must be unchanged.', ['equal_division', 'quantity']),
        seed(18, 'ratios', 'ratio_with_difference', [
            'Two positive numbers are in the ratio 5:3. The larger number exceeds the smaller by 14. What is the larger number?',
            '2 dhanaatmak sankhyaon ka anupaat 5:3 hai. Badi sankhya chhoti sankhya se 14 zyaada hai. Badi sankhya kya hai?',
            '2 positive numbers ka ratio 5:3 hai. The larger number exceeds the smaller by 14. Bada number kya hai?'
        ], '35', '', '14 / (5 - 3) * 5', 'The difference is 2 parts, so each part is 7. The larger number is 5 * 7 = 35. FINAL: 35', F(14,2)*5,
             'Difference is not total; assess formal Hindi vocabulary and C phrasing.', ['comparison', 'ratio']),
        seed(19, 'ratios', 'mixture_component_given_other_component', [
            'A drink is prepared with syrup and water in the volume ratio 2:5. If 350 mL of water is used, how many millilitres of syrup are needed?',
            'Ek pey mein sharbat ke gaadhe ghol aur paani ki maatra ka anupaat 2:5 rakha jaata hai. Agar 350 mL paani liya jaaye, to kitne millilitre gaadhe ghol ki zaroorat hogi?',
            'Ek drink mein syrup aur water ka volume ratio 2:5 hai. If 350 mL of water is used, kitne millilitres syrup chahiye?'
        ], '140', 'mL', '350 * 2 / 5', 'Five water parts total 350 mL, so one part is 70 mL. Two syrup parts require 140 mL. FINAL: 140 mL', F(350)*F(2,5),
             'The known amount is water alone. Confirm R gaadha ghol denotes the syrup component rather than the finished drink.', ['ratio', 'condition']),
        seed(20, 'ratios', 'compose_two_ratios_shared_middle', [
            'Positive quantities A, B and C satisfy A:B = 2:3 and B:C = 4:5. What is A/C? Give a number or fraction.',
            'Dhanaatmak maatraon A, B aur C ke liye A:B = 2:3 aur B:C = 4:5 hai. A/C ka maan kya hai? Ek sankhya ya bhinn mein bataaiye.',
            'Positive quantities A, B aur C ke liye A:B = 2:3 hai, and B:C equals 4:5. A/C kya hai? Give a number or fraction.'
        ], '8/15', '', '(2/3) * (4/5)', 'A/C = (A/B) * (B/C) = (2/3) * (4/5) = 8/15. FINAL: 8/15', F(2,3)*F(4,5),
             'The requested scalar is A/C, not a colon-form answer. All quantities are positive.', ['ratio', 'requested_answer']),
        seed(21, 'ratios', 'change_one_component_then_recompute_ratio', [
            'A box contains only red and blue balls in the ratio 3:4. It contains 15 red balls. Then 5 blue balls are added and none are removed. What is the new ratio of red balls to blue balls? Give it as a number or fraction, red count divided by blue count.',
            'Ek dabbe mein sirf laal aur neeli gendein hain aur unki sankhya ka anupaat 3:4 hai. Laal gendein 15 hain. Phir 5 neeli gendein aur daali jaati hain aur koi gend nikaali nahi jaati. Ab laal aur neeli gendon ki sankhya ka naya anupaat kya hai? Laal gendon ki sankhya ko neeli gendon ki sankhya se bhaag dekar sankhya ya bhinn mein bataaiye.',
            'Ek box mein sirf red aur blue balls hain, ratio 3:4 hai, aur red balls 15 hain. Then 5 blue balls are added and none are removed. Naya red-to-blue ratio kya hai? Give red count divided by blue count as a number or fraction.'
        ], '3/5', '', '15 / (15 * 4/3 + 5)', 'Initially there are 20 blue balls. After adding 5, the red-to-blue ratio is 15/25 = 3/5. FINAL: 3/5', F(15)/(F(15)*F(4,3)+5),
             'New ratio versus old ratio, red/blue order, and scalar-answer convention. Assess overlap with PIL005.', ['addition', 'negation', 'ratio_order']),
        seed(22, 'rates_units', 'speed_with_minutes_to_hours', [
            'A bus travels at a constant speed of 60 km per hour for 45 minutes, without stopping. How many kilometres does it travel?',
            'Ek bus bina ruke 45 minute tak lagaataar 60 km prati ghante ki raftaar se chalti hai. Vah kitne kilometre chalti hai?',
            'Ek bus 45 minutes tak bina ruke chalti hai, at a constant speed of 60 km per hour. Vah kitne kilometres travel karti hai?'
        ], '45', 'km', '60 * 45 / 60', '45 minutes is 3/4 hour. The distance is 60 * 3/4 = 45 km. FINAL: 45 km', F(60)*F(45,60),
             'Minutes must become hours; the constant speed and no-stop assumptions must match.', ['rate', 'time_condition']),
        seed(23, 'rates_units', 'convert_length_then_count_segments', [
            'A 2.4 m cord is cut into pieces exactly 30 cm long. Cutting loses no length and the whole cord is used. How many pieces are made?',
            '2.4 m lambi ek dori ko theek 30 cm lambe tukdon mein kaata jaata hai. Kaatne mein koi lambai nahi ghatti aur poori dori istemaal hoti hai. Kitne tukde bante hain?',
            '2.4 m lambi cord ko exactly 30 cm long pieces mein cut kiya jaata hai. Cutting loses no length aur poori cord use hoti hai. Kitne pieces bante hain?'
        ], '8', 'pieces', '2.4 * 100 / 30', 'The cord is 240 cm long. At 30 cm per piece, it makes 8 pieces. FINAL: 8 pieces', F('2.4')*100/30,
             'Length units differ and no kerf is lost; count is not a length.', ['unit_length', 'negation']),
        seed(24, 'rates_units', 'simultaneous_additive_work_rates', [
            'Two machines work together without stopping. One seals 6 boxes per minute and the other seals 4 different boxes per minute. How many minutes do they need to seal 90 boxes in total?',
            '2 yantra bina ruke ek saath kaam karte hain. Ek har minute 6 dabbe band karta hai aur doosra har minute 4 alag dabbe band karta hai. Dono milkar kul 90 dabbe band karne mein kitne minute lenge?',
            '2 machines bina ruke ek saath kaam karti hain. One seals 6 boxes per minute and the other seals 4 different boxes per minute. Total 90 boxes seal karne mein kitne minutes lagenge?'
        ], '9', 'minute', '90 / (6 + 4)', 'Together the machines seal 10 boxes per minute. They need 90/10 = 9 minutes. FINAL: 9 minute', F(90,10),
             'Rates add because the machines process distinct boxes simultaneously; review yantra naturalness.', ['rate', 'simultaneous_work']),
        seed(25, 'rates_units', 'piecewise_journey_times', [
            'A cyclist completes a 120 km journey without stops. The first 40 km are travelled at 20 km per hour and the remaining distance at 40 km per hour. How many hours does the journey take?',
            'Ek cycle savaar bina ruke 120 km ka safar poora karta hai. Pehle 40 km vah 20 km prati ghante ki raftaar se chalta hai aur baaki doori 40 km prati ghante ki raftaar se. Safar mein kul kitne ghante lagte hain?',
            'Ek cyclist bina ruke 120 km ka journey complete karta hai. The first 40 km are travelled at 20 km per hour, aur remaining distance par speed 40 km per hour hai. Total kitne hours lagte hain?'
        ], '4', 'h', '40 / 20 + (120 - 40) / 40', 'The first segment takes 2 hours and the remaining 80 km takes 2 hours. Total time is 4 hours. FINAL: 4 h', F(40,20)+F(80,40),
             'The remaining distance is 80 km; do not average speeds arithmetically.', ['segment_rate', 'requested_answer']),
        seed(26, 'elementary_algebra', 'direct_linear_equation', [
            'A number x satisfies 3x + 7 = 28. What is x?',
            'Ek sankhya x ke liye 3x + 7 = 28 hai. x ka maan kya hai?',
            'Ek number x ke liye three times x plus 7 equals 28, yaani 3x + 7 = 28. x kya hai?'
        ], '7', '', '(28 - 7) / 3', 'Subtracting 7 gives 3x = 21. Dividing by 3 gives x = 7. FINAL: 7', F(28-7,3),
             'C verbalizes the relation while retaining the equation; document this additional surface redundancy.', ['equation_relation']),
        seed(27, 'elementary_algebra', 'consecutive_integer_sum', [
            'The sum of two consecutive integers is 41. What is the smaller integer?',
            '2 lagaataar poornankon ka yog 41 hai. Chhota poornank kya hai?',
            '2 consecutive integers ka sum 41 hai. What is the smaller integer?'
        ], '20', '', '(41 - 1) / 2', 'Let the smaller integer be x. Then x + (x + 1) = 41, so x = 20. FINAL: 20', F(41-1,2),
             'Consecutive means a difference of 1, not consecutive odd integers; review poornank vocabulary.', ['requested_answer']),
        seed(28, 'elementary_algebra', 'rectangle_perimeter_inverse', [
            'A rectangle has perimeter 50 cm and width 9 cm. What is its length in centimetres?',
            'Ek aayat ka parimaap 50 cm hai aur chaudaai 9 cm hai. Uski lambai kitne centimetre hai?',
            'Ek rectangle ka perimeter 50 cm hai aur width 9 cm hai. What is its length in centimetres?'
        ], '16', 'cm', '50 / 2 - 9', 'The length plus width is 25 cm. Subtracting the 9 cm width gives a length of 16 cm. FINAL: 16 cm', F(50,2)-9,
             'Perimeter versus area; assess standard educational Hindi aayat/parimaap naturalness.', ['requested_answer']),
        seed(29, 'elementary_algebra', 'eliminate_shared_unknown_price', [
            'Two pens and one notebook cost INR 58. One pen and one notebook cost INR 39. All pens have the same price and all notebooks have the same price. What is the price of one pen?',
            '2 kalamein aur 1 kaapi milkar INR 58 ki hain. 1 kalam aur 1 kaapi milkar INR 39 ki hain. Sab kalamon ki keemat ek jaisi hai aur sab kaapiyon ki keemat ek jaisi hai. 1 kalam ki keemat kitne rupaye hai?',
            '2 pens aur 1 notebook ki total cost INR 58 hai. One pen and one notebook cost INR 39. Sab pens ki price ek jaisi hai aur sab notebooks ki price ek jaisi hai. 1 pen ki price kitne rupaye hai?'
        ], '19', 'INR', '58 - 39', 'Subtracting the two baskets cancels the notebook and one pen. The extra pen costs INR 19. FINAL: INR 19', F(58)-39,
             'Shared prices are invariant; the asked unknown is one pen rather than the notebook.', ['basket_relation']),
        seed(30, 'elementary_algebra', 'positive_square_root_domain', [
            'A positive number x satisfies x squared equals 49. What is x?',
            'Ek dhanaatmak sankhya x ka varg 49 hai. x ka maan kya hai?',
            'Ek positive number x hai, and x squared equals 49. x kya hai?'
        ], '7', '', 'x^2 = 49; x > 0; x = 7', 'Both 7 and -7 have square 49, but x is positive. Therefore x = 7. FINAL: 7', F(7),
             'Positivity is essential: exactly one root is requested. The reference check also verifies 7 squared is 49.', ['equation_relation']),
    ]

UNITS = {
    'marbles': (['marble', 'kanche', 'kancha'], {}),
    'INR': (['rupee', 'rupees', 'rupaye', 'rupaya', 'rs', 'Rs.'], {}),
    'L': (['l', 'litre', 'litres', 'liter', 'liters'], {'mL': '1/1000', 'millilitre': '1/1000', 'millilitres': '1/1000'}),
    'm': (['metre', 'metres', 'meter', 'meters'], {'cm': '1/100', 'centimetre': '1/100', 'centimetres': '1/100'}),
    'books': (['book', 'kitaabein', 'kitaab'], {}),
    'beads': (['bead', 'moti'], {}),
    'pencils': (['pencil', 'pensilein', 'pensil'], {}),
    'stickers': (['sticker', 'parchiyan', 'parchi'], {}),
    'pens': (['pen', 'kalamein', 'kalam'], {}),
    'girls': (['girl', 'ladkiyan', 'ladki'], {}),
    'kg': (['kilogram', 'kilograms'], {'g': '1/1000', 'gram': '1/1000', 'grams': '1/1000'}),
    'mL': (['ml', 'millilitre', 'millilitres', 'milliliter', 'milliliters'], {'L': '1000', 'litre': '1000', 'litres': '1000'}),
    'km': (['kilometre', 'kilometres', 'kilometer', 'kilometers'], {'m': '1/1000', 'metre': '1/1000', 'metres': '1/1000'}),
    'pieces': (['piece', 'tukde', 'tukda'], {}),
    'minute': (['minutes', 'min'], {'h': '60', 'hour': '60', 'hours': '60'}),
    'h': (['hour', 'hours', 'ghante', 'ghanta'], {'minute': '1/60', 'minutes': '1/60', 'min': '1/60'}),
    'cm': (['centimetre', 'centimetres', 'centimeter', 'centimeters'], {'m': '100', 'metre': '100', 'metres': '100'}),
    '': ([], {}),
}

def build_family(s):
    fid = f"PIL{s['n']:03d}"
    aliases, conversions = UNITS[s['unit']]
    forms = {f: dict(rendering_id=f'{fid}-{f}-v1', text=t, creator_type='AI_DRAFT',
                     generation_or_edit_history=('Verbatim carry-forward of illustrative draft in pilot_review_packet.md; no human review.'
                                                 if s['n'] <= 5 else 'New AI-authored draft 2026-10-10; no human review.'),
                     switching_roles=s['roles'] if f == 'C' else [])
             for f, t in zip(FORMS, s['texts'])}
    return dict(family_id=fid, source_family_id=f'{fid}-authored-source', template_group_id=f'{fid}-proposed-family',
                topic=s['topic'], split_role='PILOT_EVAL', version='v1', authoring_origin='AI_DRAFT',
                provenance=('Carried forward unchanged from pilot_review_packet.md, section 4.' if s['n'] <= 5
                            else 'AI-authored original candidate for this pilot review; no external source used.'),
                source_license='No external source used; release terms not assigned. Human edits and any introduced sources must be logged before release.',
                reference_equation=s['equation'], reference_solution_en=s['solution'].replace(' FINAL:', '\nFINAL:'), status='DRAFT',
                gold=dict(value=s['value'], unit=s['unit'], aliases=aliases, conversions=conversions,
                          unit_omission_allowed=True, rounding_rule='exact'), forms=forms,
                review=dict(reviewers=[], adjudication=None))

def identity(f):
    return {k:f[k] for k in ('family_id', 'source_family_id', 'template_group_id')}

def blank_response(f, form):
    r = f['forms'][form]
    return dict(family_id=f['family_id'], rendering_id=r['rendering_id'], intended_form=form,
                text_sha256=sha(r['text']), independent_equation='', independent_reasoning='',
                independent_answer='', independent_unit='', solved_at_utc='',
                classification='', naturalness=None, readability=None, ambiguity_flag=None,
                issue_notes='', disposition='PENDING', semantic_checks=None,
                english_spans=[], permitted_borrowings=[], reviewed_at_utc='')

REVIEW_GUIDE = '''# Independent bilingual review — DRAFT, not validated data

This packet contains 90 renderings of 30 proposed mathematical families. All are AI-authored drafts. Your assigned ID is a pseudonym; do not enter personal details.

1. Work alone. Do not consult the other reviewer, reference key, model outputs or translation tools. In `stage1.html`, solve the randomized questions and save an equation, reasoning, exact answer and unit for every rendering **before opening stage2**. All forms and the same item content are visible; this is not blinded to language or family membership.
2. Save stage1 JSON with the button at the bottom. Preserve that first submission. You may do several sittings: download progress, then import that JSON to continue. Data remain in your browser tab until downloaded; closing the tab can lose unsaved edits.
3. After independent solutions are saved, open `stage2.html`, import your stage1 JSON and compare the E/R/C triplets. Do not change the frozen stage1 answers. Record semantic checks, actual form classification, naturalness and readability (1–5), ambiguity, English spans/borrowings and issues. If a stage1 solution needs correction, explain it in stage2 issue notes rather than silently replacing it.
4. ACCEPT requires matching mathematical content, correct E/R/C classification, no ambiguity, and naturalness/readability >=4. Otherwise choose REVISE or EXCLUDE and explain. You can question the proposed reference answer later; do not adjust your solve to match it.
5. Download both completed JSONs and return them to the coordinator. Stage2 submissions are review proposals, never automatic dataset acceptance. Do not email or otherwise share anything automatically.

Naturalness: 1 difficult; 2 awkward; 3 understandable but conspicuously unnatural; 4 plausible educational wording; 5 fluent/idiomatic. Readability: 1 largely unreadable; 2 substantial effort; 3 needs repairs; 4 readily readable; 5 immediately clear. Rate E readability too to match the pilot schema.

For each triplet verify: quantities; entities; units; rate/comparison direction; time conditions; requested unknown; explicit assumptions. C must contain a productive English clause/predicate/relation, beyond object names. R uses Hindi phrasing in Roman script with the proposed borrowing policy. Flag policy problems rather than forcing unnatural replacements. Repaired text needs a new version and both reviewers must re-review.

These materials contain no model results or gold answers. No reviewer agreement or acceptance has been recorded.
'''

def page(reviewer, stage, dataset, order):
    """Standalone browser forms with explicit local JSON export/import, no networking."""
    by_id = {f['family_id']:f for f in dataset['families']}
    rows = [blank_response(by_id[fid], form) for fid, form in order]
    packet = dict(schema_version='annotation-draft-1', dataset_version=VERSION, reviewer_id=reviewer,
                  stage=stage, independent_solve_before_gold=None, started_at_utc='', completed_at_utc='',
                  rows=rows)
    data_js = json.dumps(packet, ensure_ascii=False).replace('<', '\\u003c')
    parts = []
    for i, (fid, form) in enumerate(order):
        f = by_id[fid]
        r = f['forms'][form]
        if stage == 2 and i % 3 == 0:
            parts.append(f'<h2>{fid} — compare this triplet</h2>')
        parts.append(f'<section data-index="{i}"><h3>{i+1}. {r["rendering_id"]} — intended {form}</h3><p class="question">{html.escape(r["text"])}</p>')
        if stage == 1:
            for key, label in [('independent_equation', 'Your equation'), ('independent_reasoning', 'Your reasoning'), ('independent_answer', 'Exact answer (e.g. 1/4 or 0.25)'), ('independent_unit', 'Unit (blank if dimensionless)'), ('solved_at_utc', 'Solved at (UTC timestamp)')]:
                parts.append(f'<label>{label}<textarea data-key="{key}"></textarea></label>')
            parts.append('<button type="button" data-stamp="solved_at_utc">Mark this solve finished (UTC)</button>')
        else:
            parts.append('<p class="locked">Your imported stage1 solve: <span data-solve></span></p>')
            parts.append('<label>Actual classification<select data-key="classification"><option value="">Choose</option><option>E</option><option>R</option><option>C</option><option>UNCLEAR</option></select></label>')
            for k in ('naturalness', 'readability'):
                parts.append(f'<label>{k} (1–5)<select data-key="{k}"><option value="">Choose</option>' + ''.join(f'<option>{n}</option>' for n in range(1,6)) + '</select></label>')
            parts.append('<label>Ambiguity?<select data-key="ambiguity_flag"><option value="">Choose</option><option value="true">Yes</option><option value="false">No</option></select></label>')
            for k in ('quantities', 'entities', 'units', 'relations_rates', 'time_conditions', 'requested_unknown', 'explicit_assumptions'):
                parts.append(f'<label>{k}: equivalent across triplet?<select data-semantic="{k}"><option value="">Choose</option><option value="true">Yes</option><option value="false">No</option></select></label>')
            parts.append('<label>Disposition<select data-key="disposition"><option>PENDING</option><option>ACCEPT</option><option>REVISE</option><option>EXCLUDE</option></select></label>')
            for k, label in [('english_spans','Productive English spans (one per line, C); otherwise blank'), ('permitted_borrowings','Shared borrowings found (one per line)'), ('issue_notes','Issues, proposed edits, solution corrections, and reasons'), ('reviewed_at_utc','Reviewed at (UTC timestamp)')]:
                parts.append(f'<label>{label}<textarea data-key="{k}"></textarea></label>')
            parts.append('<button type="button" data-stamp="reviewed_at_utc">Mark this review finished (UTC)</button>')
        parts.append('</section>')
    return '''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>''' + reviewer + f''' stage{stage}</title>
<style>body{{max-width:900px;margin:30px auto;padding:16px;font:17px system-ui;color:#142331;background:#fafafa}}section{{background:white;border:1px solid #bdc7d1;margin:24px 0;padding:20px;break-inside:avoid}}label{{display:block;margin:10px 0}}textarea{{width:96%;min-height:45px;font:16px system-ui}}select,button{{font:16px system-ui;padding:7px}}.question{{font-size:19px;line-height:1.5}}.banner{{background:#fff0b8;padding:15px}}.locked{{background:#eaf2f8;padding:12px}}button{{margin:8px}}@media print{{button,input{{display:none}}}}</style>
<h1>{reviewer} — stage {stage}</h1><p class="banner">DRAFT — NO HUMAN VALIDATION. Do stage1 first without gold. Stage2 contains no answer key. Save downloads before closing this page.</p>
<p>{html.escape(BORROWING)}</p><p>Read README.md for ratings and workflow. Import a saved same-reviewer progress JSON, or (stage2) your frozen stage1 JSON.</p>
<input type="file" id="import" accept=".json"><button id="save">Download progress JSON</button><p id="message"></p>
<label><input type="checkbox" id="attest"> I personally solved all renderings before seeing reference answers (check only when true).</label>
<label>Completion timestamp in UTC (leave blank until done)<input id="completed" placeholder="YYYY-MM-DDTHH:MM:SSZ"></label>
''' + '\n'.join(parts) + '''<button id="saveBottom">Download progress JSON</button><script>
'use strict';
let packet = ''' + data_js + ''';
function fill(){document.querySelectorAll('section').forEach(s=>{const r=packet.rows[+s.dataset.index];s.querySelectorAll('[data-key]').forEach(e=>{const v=r[e.dataset.key];e.value=Array.isArray(v)?v.join('\\n'):(v===null?'':String(v));});s.querySelectorAll('[data-semantic]').forEach(e=>{const v=(r.semantic_checks||{})[e.dataset.semantic];e.value=v===null||v===undefined?'':String(v);});const x=s.querySelector('[data-solve]');if(x)x.textContent=[r.independent_equation,r.independent_reasoning,r.independent_answer,r.independent_unit].join(' | ');});document.getElementById('attest').checked=packet.independent_solve_before_gold===true;document.getElementById('completed').value=packet.completed_at_utc||'';}
function collect(){document.querySelectorAll('section').forEach(s=>{const r=packet.rows[+s.dataset.index];s.querySelectorAll('[data-key]').forEach(e=>{const k=e.dataset.key;let v=e.value;if(k==='naturalness'||k==='readability')v=v?Number(v):null;else if(k==='ambiguity_flag')v=v===''?null:v==='true';else if(k==='english_spans'||k==='permitted_borrowings')v=v.split('\\n').map(x=>x.trim()).filter(Boolean);r[k]=v;});if(s.querySelector('[data-semantic]')){r.semantic_checks={};s.querySelectorAll('[data-semantic]').forEach(e=>{r.semantic_checks[e.dataset.semantic]=e.value===''?null:e.value==='true';});}});packet.independent_solve_before_gold=document.getElementById('attest').checked?true:null;packet.completed_at_utc=document.getElementById('completed').value;}
function save(){if(packet.stage===2&&!packet.stage1_submission_sha256){document.getElementById('message').textContent='Import your completed stage1 submission first.';return;}collect();const b=new Blob([JSON.stringify(packet,null,2)],{type:'application/json'});const a=document.createElement('a');a.href=URL.createObjectURL(b);a.download=packet.reviewer_id+'_stage'+packet.stage+'_responses.json';a.click();URL.revokeObjectURL(a.href);document.getElementById('message').textContent='Downloaded locally. Preserve each submission; do not overwrite first-pass ratings.';}
document.getElementById('save').onclick=save;document.getElementById('saveBottom').onclick=save;
document.getElementById('import').onchange=async e=>{try{const incoming=JSON.parse(await e.target.files[0].text());if(incoming.schema_version!==packet.schema_version||incoming.reviewer_id!==packet.reviewer_id||incoming.dataset_version!==packet.dataset_version||incoming.rows.length!==90)throw Error('Wrong reviewer/version/size');if(incoming.stage!==packet.stage && !(packet.stage===2&&incoming.stage===1))throw Error('Wrong stage');const map=new Map(incoming.rows.map(r=>[r.rendering_id,r]));if(map.size!==90)throw Error('Duplicate IDs');const merged=packet.rows.map(r=>{const x=map.get(r.rendering_id);if(!x||x.text_sha256!==r.text_sha256||x.family_id!==r.family_id||x.intended_form!==r.intended_form)throw Error('Text/ID mismatch: re-review changed text');return {...x};});if(packet.stage===2&&incoming.stage===1&&(incoming.independent_solve_before_gold!==true||!incoming.completed_at_utc))throw Error('Attest only after all independent solves are finished, and record the stage1 completion timestamp');if(packet.stage===2&&incoming.stage===1&&!incoming.rows.every(r=>r.independent_equation.trim()&&r.independent_reasoning.trim()&&r.independent_answer.trim()&&r.solved_at_utc.trim()))throw Error('Finish and timestamp all stage1 independent solves before stage2');if(packet.stage===2&&incoming.stage===1){packet.stage1_submission_sha256=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',await e.target.files[0].arrayBuffer())),b=>b.toString(16).padStart(2,'0')).join('');}if(packet.stage===2&&incoming.stage===2){if(!incoming.stage1_submission_sha256)throw Error('Missing original stage1 submission hash');packet.stage1_submission_sha256=incoming.stage1_submission_sha256;}packet.rows=merged;packet.independent_solve_before_gold=incoming.independent_solve_before_gold;packet.completed_at_utc=incoming.stage===packet.stage?incoming.completed_at_utc:'';fill();document.getElementById('message').textContent='Imported. Imported answers are read-only in stage2.';}catch(err){document.getElementById('message').textContent='Import rejected: '+err.message;}};
document.querySelectorAll('[data-stamp]').forEach(b=>{b.onclick=()=>{b.closest('section').querySelector('[data-key="'+b.dataset.stamp+'"]').value=new Date().toISOString();};});
fill();
</script></html>'''

def main():
    candidates = seeds()
    families = [build_family(s) for s in candidates]
    dataset = dict(schema_version='test1-1', version=VERSION, kind='reviewed', borrowing_policy=BORROWING, families=families)
    # kind is a mode designation. The DRAFT status and empty review fields block execution.
    demo = json.loads((ROOT/'test1_pilot/fixtures/demo_dataset.json').read_text())
    fixture = json.loads((ROOT/'test1_pilot/fixtures/format_smoke.json').read_text())
    retired = [identity(f) for f in demo['families']]
    smoke = [{k:fixture[k] for k in ('family_id','source_family_id','template_group_id')}]
    splits = dict(schema_version='test1-1', version=VERSION+'-splits', kind='reviewed',
                  audit=dict(approved=False, reviewer_id='', unresolved_matches=None, audited_at=''),
                  PILOT_EVAL=[identity(f) for f in families], SMOKE_TRAIN=smoke, RETIRED_DRAFT=retired,
                  CONFIRM_TRAIN=[], FINAL_TEST=[], development_exclusion_ids=sorted({v for r in [*families,*smoke,*retired] for k,v in r.items() if k in ('family_id','source_family_id','template_group_id')}))
    write(OUT/'coordinator/pilot_dataset.DRAFT.json', dataset)
    write(OUT/'coordinator/split_manifest.DRAFT.json', splits)
    key = ['# A01 adjudication key — do not share before independent solves\n',
           '**DRAFT — NOT HUMAN-VALIDATED.** Reference calculations are AI-authored and checked programmatically. They can be challenged. A01 is a role placeholder, not evidence of a review.\n',
           'Collect and preserve both stage1 submissions before revealing this key. Compare independent solutions and stage2 judgments, resolve disagreements with written reasons, and version/re-review text repairs. Check family relationships beyond surface wording.\n',
           BORROWING+'\n']
    register = []
    for s,f in zip(candidates,families):
        key += [f'## {f["family_id"]} — {f["topic"]}\n', f'Proposed structure: `{s["structure"]}` (independence UNVERIFIED).\n']
        key += [f'- {form}: {f["forms"][form]["text"]}\n' for form in FORMS]
        key += [f'\nEquation: `{s["equation"]}`. Proposed exact gold: **{s["value"]} {s["unit"]}**.\n',
                f'Shared English solution: {s["solution"]}\n',
                f'Predeclared unit policy: `{json.dumps(f["gold"],ensure_ascii=False)}`. All questions request exact answers; no rounding/tolerance. Unit omission allowed; explicit incorrect units rejected.\n',
                f'Review focus: {s["focus"]}\n']
        register.append(dict(family_id=f['family_id'], proposed_structure=s['structure'], independence_status='UNVERIFIED',
                             source_url_or_record=f['provenance'], source_license=f['source_license'], original_creation_date=None if s['n'] <= 5 else '2026-10-10',
                             operation_count=None, operation_count_note='Annotate consistently after the counting convention is frozen.',
                             exclusion_reason='Development exposure: reserve family and all descendants permanently.',
                             focus=s['focus'], renderings=[dict(form=form, text_sha256=sha(f['forms'][form]['text']),
                             raw_character_count=len(f['forms'][form]['text']), formatted_prompt_tokens=None,
                             formatted_training_tokens=None, supervised_target_tokens=None,
                             Hindi_spans=None, English_spans=None, romanization_notes='Provisional readable Roman Hindi; bilingual review pending.') for form in FORMS]))
    write(OUT/'A01/answer_key.md','\n'.join(key))
    write(OUT/'coordinator/draft_register.json',register)
    write(OUT/'A01/adjudication.PENDING.json',dict(schema_version='annotation-adjudication-1', dataset_version=VERSION,
          adjudicator_id='A01', role_assignment_confirmed=False, borrowing_policy_decision='PENDING', borrowing_policy_final='',
          split_audit=dict(status='PENDING', reviewer_id='', audited_at_utc='', unresolved_matches=None, notes=''),
          family_relationship_checks=[dict(family_id_a='', family_id_b_or_external_source='', match_method='',
          near_duplicate_evidence='', mathematical_family_relationship='', reviewer_decision='PENDING', action='')],
          families=[dict(family_id=f['family_id'], status='PENDING', unresolved_issues=None, independent_gold_check='',
          final_equation='', final_answer='', final_unit='', agreement_notes='', decision_reason='', proposed_text_repairs={},
          gold_unit_policy_approved=None, reviewed_at_utc='') for f in families]))
    write(OUT/'A01/README.md','# A01: adjudication\n\nDo not release answer_key.md to R01 or R02 until their independent solves have been submitted. Preserve all raw submissions. Use adjudication.PENDING.json to record real decisions and reasons. Confirm role assignment; the ID is only a pseudonymous role placeholder. A repaired item requires a new text hash/version and independent re-review by both reviewers. Do not mark acceptance to match an expected model outcome.\n\nAfter reviews return, give the original stage1/stage2 files and your completed adjudication to the research assistant. The pilot import schema is described in ../README.md; these raw forms must not be uploaded directly to Colab.\n')
    orders = {}
    for reviewer, seed_value in [('R01',4101),('R02',4102)]:
        order=[(f['family_id'],form) for f in families for form in FORMS]
        random.Random(seed_value).shuffle(order)
        paired=list(families)
        random.Random(seed_value+100).shuffle(paired)
        triplet_order=[(f['family_id'],form) for f in paired for form in FORMS]
        orders[reviewer]=dict(stage1_seed=seed_value,stage2_family_seed=seed_value+100,
                              stage1=order,stage2=triplet_order)
        write(OUT/reviewer/'README.md',REVIEW_GUIDE+'\nAssigned role: '+reviewer+'.\n\n'+BORROWING+'\n')
        write(OUT/reviewer/'stage1.html',page(reviewer,1,dataset,order))
        write(OUT/reviewer/'stage2.html',page(reviewer,2,dataset,triplet_order))
    write(OUT/'coordinator/randomization.json',orders)
    write(OUT/'README.md', '''# 30-family pilot — draft annotation package v1

All 30 families and 90 E/R/C texts are **DRAFT**, AI-authored and awaiting two independent bilingual reviews and adjudication. PIL001–005 retain the earlier illustrative wording verbatim; the other 25 are new candidates. No independent human solutions, agreement, acceptance, split audit or reviewed pilot result is claimed. The separate Qwen GPU demo is technical feasibility evidence only.

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

Rebuild with `python3 pilot/annotation_draft_v1/build_packet.py`; verify with `python3 pilot/annotation_draft_v1/verify_packet.py`. Rebuilding touches this draft distribution, not returned reviews; store actual submissions separately with versioned filenames. Do not rebuild over human-edited draft JSON. The notebook and model/scorer configuration are unchanged. Software checks do not certify translation equivalence, naturalness or family independence.
''')
    for role in ('R01','R02','A01'):
        target=OUT/(f'{role}_review_packet.zip' if role!='A01' else 'A01_adjudication_packet.zip')
        with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as archive:
            for p in sorted((OUT/role).iterdir()):
                archive.write(p, f'{role}/{p.name}')
    hashes={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.rglob('*')) if p.is_file() and p.suffix != '.pyc' and p.name not in ('checksums.sha256','verification.json')}
    write(OUT/'checksums.sha256',''.join(f'{v}  {k}\n' for k,v in hashes.items()))
    print(json.dumps(dict(status='DRAFT — NO HUMAN VALIDATION',families=len(families),renderings=90,
                          topics=dict(Counter(f['topic'] for f in families)),output=str(OUT)),indent=2))

if __name__=='__main__':
    main()
