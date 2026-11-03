import unittest

from secondary_analysis import numeric_endpoint as v1
from secondary_analysis import numeric_literal_v2 as v2
from secondary_analysis.rescore_pilot_b_v2 import MODELS, load, rescore


def gold(value="19", unit="INR", aliases=("Rs.",)):
    return dict(value=value, unit=unit, aliases=list(aliases), conversions={},
                unit_omission_allowed=True, rounding_rule="exact")


RUPEE_UNITS = ("rupees", "Rupee", "INR", "Rs", "rs.", "₹")
NON_RUPEE = (gold(unit="kg", aliases=["kilo"]), gold(unit="", aliases=[]), gold(unit="dollars", aliases=["$"]),
             gold(unit="paise", aliases=[]))


class NumericLiteralV2Tests(unittest.TestCase):
    def test_version_and_v1_untouched(self):
        self.assertEqual(v2.ENDPOINT_VERSION, "numeric_literal_v2")
        self.assertEqual(v1.ENDPOINT_VERSION, "numeric_literal_v1")
        self.assertEqual(v2.extract_numeric("FINAL: 19")["endpoint"], "numeric_literal_v2")

    def test_trailing_rupee_symbol(self):
        for text in ("FINAL: 19 ₹", "FINAL: 19₹", "FINAL: 19  ₹.", "FINAL: **19** ₹", "FINAL: **19 ₹**",
                     r"FINAL: \boxed{19} ₹", "FINAL: $19$ ₹", "**FINAL:** 19 ₹", "FINAL: x = 19 ₹"):
            with self.subTest(text=text):
                self.assertEqual(v1.extract_numeric(text)["status"], "unsupported_answer")
                result = v2.extract_numeric(text)
                self.assertEqual((result["status"], result["value"], result["suffix"]), ("extracted", "19", ""))
                self.assertIn("currency_suffix_symbol", result["extraction_path"].split("|"))
                for unit in RUPEE_UNITS:
                    self.assertTrue(v2.numeric_correct(text, gold(unit=unit)))
                self.assertEqual(v2.evaluate_numeric(text, gold())["status"], "match")
                self.assertEqual(v2.evaluate_numeric(text, gold("20"))["status"], "mismatch")

    def test_leading_rupees_word(self):
        for text in ("FINAL: rupees 19", "FINAL: Rupees 19", "FINAL: RUPEE 19", "FINAL: rupees19",
                     "FINAL: rupees **19**", "FINAL: **rupees 19**", "FINAL: x = rupees 19", "FINAL: rupees 1,41,150"):
            with self.subTest(text=text):
                self.assertEqual(v1.extract_numeric(text)["status"], "unsupported_answer")
                result = v2.extract_numeric(text)
                self.assertEqual(result["status"], "extracted")
                self.assertIn("currency_prefix_word", result["extraction_path"].split("|"))
        self.assertTrue(v2.numeric_correct("FINAL: rupees 19", gold()))
        self.assertTrue(v2.numeric_correct("FINAL: rupees 1,41,150", gold("141150", "rupees")))
        self.assertEqual(v2.evaluate_numeric("FINAL: Rupee 18", gold())["status"], "mismatch")

    def test_new_paths_do_not_count_for_non_rupee_gold(self):
        for text in ("FINAL: 19 ₹", "FINAL: rupees 19", "FINAL: **19** ₹"):
            for expected in NON_RUPEE:
                with self.subTest(text=text, unit=expected["unit"]):
                    self.assertEqual(v2.extract_numeric(text)["status"], "extracted")  # gold-blind
                    result = v2.evaluate_numeric(text, expected)
                    self.assertFalse(result["correct"])
                    self.assertEqual(result["status"], "unsupported_answer")
                    self.assertEqual(dict(result, endpoint=None), dict(v1.evaluate_numeric(text, expected), endpoint=None))

    def test_two_currency_markers_unsupported(self):
        for text in ("FINAL: ₹19 ₹", "FINAL: Rs. 19 ₹", "FINAL: INR 19₹", "FINAL: rupees ₹19", "FINAL: rupees Rs 19",
                     "FINAL: rupees 19 ₹", "FINAL: rupees 19 rupees", "FINAL: rupee 19 INR", "FINAL: 19 rupees ₹",
                     "FINAL: 19 ₹ ₹", "FINAL: rupees rupees 19", "FINAL: ₹ rupees 19"):
            with self.subTest(text=text):
                self.assertEqual(v2.extract_numeric(text)["status"], "unsupported_answer")
                self.assertFalse(v2.numeric_correct(text, gold()))

    def test_other_rejections_unchanged(self):
        for text in ("FINAL: 19 kg ₹", "FINAL: ₹", "FINAL: rupees", "FINAL: rupeesx 19", "FINAL: 19 ₹ only",
                     "FINAL: rupees 19/-", "FINAL: 19 or 20 ₹", "FINAL: paise 19"):
            with self.subTest(text=text):
                self.assertIsNone(v2.extract_numeric(text)["value"])
                self.assertEqual(v2.extract_numeric(text), dict(v1.extract_numeric(text), endpoint=v2.ENDPOINT_VERSION))
        self.assertEqual(v2.evaluate_numeric("FINAL: 19 ₹", gold(), truncated=True)["status"], "truncated")
        self.assertEqual(v2.extract_numeric("FINAL: 19 ₹\nFINAL: 19 ₹")["status"], "multiple_finals")

    def test_v1_accepted_answers_identical(self):
        for text in ("FINAL: ₹19", "FINAL: Rs. 19", "FINAL: 19 rupees", "FINAL: INR 19 rupees",
                     "FINAL: ₹19/-", "FINAL: 19", "FINAL: 19 Rs"):
            for expected in (gold(), *NON_RUPEE):
                with self.subTest(text=text, unit=expected["unit"]):
                    self.assertEqual(v2.evaluate_numeric(text, expected),
                                     dict(v1.evaluate_numeric(text, expected), endpoint=v2.ENDPOINT_VERSION))

    def test_identity_with_v1_on_stored_pilot_b_non_rupee_items(self):
        checked = rupee = 0
        for model in MODELS:
            for row in load(model):
                a = v1.evaluate_numeric(row["response"], row["gold"], row["truncated"])
                b = v2.evaluate_numeric(row["response"], row["gold"], row["truncated"])
                self.assertEqual(a["correct"], row["stored_v1"])
                if v2.gold_is_rupees(row["gold"]):
                    rupee += 1
                    if a["status"] != "unsupported_answer":
                        self.assertEqual(b, dict(a, endpoint=v2.ENDPOINT_VERSION))
                    continue
                checked += 1
                self.assertEqual(b, dict(a, endpoint=v2.ENDPOINT_VERSION), row["rendering_id"])
                self.assertEqual(v2.extract_numeric(row["response"], row["truncated"]),
                                 dict(v1.extract_numeric(row["response"], row["truncated"]), endpoint=v2.ENDPOINT_VERSION))
        self.assertEqual((checked, rupee), (3 * 150, 3 * 60))

    def test_pilot_b_planning_proxy(self):
        table = rescore("qwen3-4b")["table"]
        self.assertEqual(tuple(table["v1"][f] for f in "ERC"), (51, 58, 58))
        self.assertEqual(tuple(table["v2"][f] for f in "ERC"), (69, 61, 67))


if __name__ == "__main__":
    unittest.main()
