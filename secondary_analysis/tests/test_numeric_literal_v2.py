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


class AmendmentOneFixtureTests(unittest.TestCase):
    """Frozen fixtures for PREREGISTRATION.md Amendment 1 item 1 (Astra review 2026-11-03 section 1)."""

    def assert_new_path(self, text, value="5", path=None):
        self.assertEqual(v1.extract_numeric(text)["status"], "unsupported_answer", text)
        result = v2.extract_numeric(text)
        self.assertEqual((result["status"], result["value"]), ("extracted", value), text)
        labels = result["extraction_path"].split("|")
        self.assertTrue(v2.uses_new_path(result), text)
        if path:
            self.assertIn(path, labels, text)
        self.assertEqual(v2.evaluate_numeric(text, gold(value, "rupees"))["status"], "match", text)

    def assert_rejected(self, text):
        result = v2.extract_numeric(text)
        self.assertIsNone(result["value"], text)
        self.assertEqual(result, dict(v1.extract_numeric(text), endpoint=v2.ENDPOINT_VERSION), text)
        self.assertFalse(v2.numeric_correct(text, gold("5", "rupees")), text)

    def test_adjacency(self):
        for text in ("FINAL: rupees5", "FINAL: rupees 5", "FINAL: rupees \t 5", "FINAL: RuPeE5", "FINAL: rupees.5",
                     "FINAL: rupees**5**", "FINAL: rupees$5$", r"FINAL: rupees\boxed{5}"):
            self.assert_new_path(text, "1/2" if text.endswith(".5") else "5", "currency_prefix_word")
        self.assert_new_path("FINAL: rupees-5", "-5", "currency_prefix_word")
        self.assert_new_path("FINAL: rupees+5", "5", "currency_prefix_word")
        for text in ("FINAL: 5₹", "FINAL: 5 ₹", "FINAL: 5\t₹", "FINAL: **5**₹", "FINAL: $5$ ₹", r"FINAL: \boxed{5}₹",
                     "FINAL: 5/1 ₹", "FINAL: 500% ₹"):
            self.assert_new_path(text, "5", "currency_suffix_symbol")
        # Not followed by whitespace/digit/sign/decimal point/wrapper opener, or '₹' not directly after the scalar.
        for text in ("FINAL: rupeesx 5", "FINAL: rupeess 5", "FINAL: rupees,5", "FINAL: rupees(5)", "FINAL: rupees:5",
                     "FINAL: rupees/5", "FINAL: rupees#5", "FINAL: rupees*5", "FINAL: rupees", "FINAL: 5 only ₹",
                     "FINAL: 5 kg ₹", "FINAL: 5/- ₹", "FINAL: rupees 5/-", "FINAL: 5 ₹ only", "FINAL: ₹",
                     "FINAL: 5 (₹)", "FINAL: 5 ₹/-"):
            self.assert_rejected(text)
        self.assertEqual(v2._PREFIX_WORD.match("rupees,5"), None)  # the prefix itself is refused, not only the parse

    def test_assignments(self):
        self.assert_new_path("FINAL: x = rupees 5", path="currency_prefix_word")
        self.assert_new_path("FINAL: x=5₹", path="currency_suffix_symbol")
        self.assert_new_path("FINAL: X = **5** ₹", path="currency_suffix_symbol")
        self.assertIn("assignment", v2.extract_numeric("FINAL: x = rupees 5")["extraction_path"].split("|"))
        for text in ("FINAL: rupees x = 5", "FINAL: x = rupees y = 5", "FINAL: total = rupees 5", "FINAL: ₹ x = 5 ₹"):
            self.assert_rejected(text)

    def test_nested_wrappers(self):
        for text in ("FINAL: **$5$** ₹", "FINAL: $**5**$₹", r"FINAL: \boxed{**5**} ₹", "FINAL: **5 ₹**",
                     "FINAL: **$5$ ₹**"):
            self.assert_new_path(text, path="currency_suffix_symbol")
        for text in ("FINAL: rupees **$5$**", "FINAL: **rupees $5$**", r"FINAL: rupees \boxed{$5$}", "FINAL: $rupees 5$"):
            self.assert_new_path(text, path="currency_prefix_word")
        for text in ("FINAL: **5** **₹**", "FINAL: rupees **₹5**", "FINAL: **rupees 5 ₹**", "FINAL: **5**$₹$",
                     "FINAL: rupees **5", r"FINAL: \boxed{5 ₹ ₹}"):
            self.assert_rejected(text)

    def test_punctuation(self):
        for text in ("FINAL: rupees 5.", "FINAL: 5 ₹.", "FINAL: 5₹ .", "**FINAL:** 5 ₹", "**FINAL: rupees 5**"):
            self.assert_new_path(text)
        for text in ("FINAL: 5₹,", "FINAL: 5 ₹!", "FINAL: rupees. 5", "FINAL: rupees, 5", "FINAL: rupees - 5",
                     "FINAL: 5 ₹ /-", "FINAL: 5 ₹;", "FINAL: `rupees 5`", "FINAL: rupees_5", "FINAL: 5 ₹.."):
            self.assert_rejected(text)

    def test_multiple_markers(self):
        for text in ("FINAL: rupees 5 Indian rupees", "FINAL: rupees 5 Rs only", "FINAL: rupee 5 inr", "FINAL: rupees 5 RS",
                     "FINAL: rupees 5 indian Rs", "FINAL: ₹ rupees 5", "FINAL: INR rupees 5", "FINAL: Rs. rupees 5",
                     "FINAL: rupees rupee 5", "FINAL: 5₹₹", "FINAL: 5 ₹ ₹", "FINAL: rupees 5 ₹", "FINAL: Rs 5 ₹",
                     "FINAL: rupees 5 Rs.", "FINAL: x = rupees 5 INR", "FINAL: rupees 5 rupees"):
            self.assert_rejected(text)
        # A non-currency suffix word is not a marker; a currency word inside a hyphenated token is not a token.
        self.assert_new_path("FINAL: rupees 5 only")
        self.assert_new_path("FINAL: rupees 5 rupees-only")
        # Old v1 two-marker successes are kept, including for non-rupee gold.
        for text in ("FINAL: Rs 5 rupees", "FINAL: ₹5 INR", "FINAL: 5 Rs INR", "FINAL: INR 5 Rs"):
            for expected in (gold("5", "rupees"), gold("5", "apples", ())):
                with self.subTest(text=text, unit=expected["unit"]):
                    self.assertEqual(v2.evaluate_numeric(text, expected),
                                     dict(v1.evaluate_numeric(text, expected), endpoint=v2.ENDPOINT_VERSION))
                    self.assertTrue(v2.numeric_correct(text, expected))

    def test_gold_unit_normalised_by_strip_and_casefold(self):
        for unit in ("rupees", " Rupees ", "RUPEE", "\tINR\n", "Rs", "  RS. ", "₹", " ₹ "):
            self.assertTrue(v2.gold_is_rupees(dict(unit=unit)), repr(unit))
        for unit in ("rs .", "indian rupees", "rupiah", "paise", "rs-", "r s", "", None, "$", "INR​"):
            self.assertFalse(v2.gold_is_rupees(dict(unit=unit)), repr(unit))

    def test_non_rupee_gold_returns_v1(self):
        for text in ("FINAL: rupees 5", "FINAL: 5 ₹", "FINAL: x = rupees **5**", "FINAL: 5 ₹."):
            for unit in ("apples", "dollars", "", "rs .", "paise", "Indian rupees"):
                expected = gold("5", unit, ())
                with self.subTest(text=text, unit=unit):
                    result = v2.evaluate_numeric(text, expected)
                    self.assertEqual(result, dict(v1.evaluate_numeric(text, expected), endpoint=v2.ENDPOINT_VERSION))
                    self.assertEqual((result["status"], result["correct"]), ("unsupported_answer", False))

    def test_mismatches(self):
        for text, unit in (("FINAL: rupees 6", "rupees"), ("FINAL: 6 ₹", " INR "), ("FINAL: rupees 5.01", "Rs."),
                           ("FINAL: -5 ₹", "₹"), ("FINAL: rupees 1/2", "rupee"), ("FINAL: 5% ₹", "rs")):
            with self.subTest(text=text):
                result = v2.evaluate_numeric(text, gold("5", unit, ()))
                self.assertEqual((result["status"], result["correct"]), ("mismatch", False))
                self.assertTrue(v2.uses_new_path(result))
        # Exact value comparison: equal fractions match.
        self.assertTrue(v2.numeric_correct("FINAL: rupees 10/2", gold("5", "rupees", ())))
        self.assertTrue(v2.numeric_correct("FINAL: 5.0 ₹", gold("5", "rupees", ())))


if __name__ == "__main__":
    unittest.main()
