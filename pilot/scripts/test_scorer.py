import unittest

from scorer import SCORER_VERSION, score_response


def gold(value, unit="", aliases=(), omission=False, conversions=None):
    return {
        "value": value,
        "unit": unit,
        "aliases": list(aliases),
        "unit_omission_allowed": omission,
        "conversions": conversions or {},
    }


class ScorerTests(unittest.TestCase):
    def test_balanced_independent_cases(self):
        count = gold("35", "marbles", ["kanche"])
        money = gold("100000", "INR")
        metre = gold("1", "m", ["metre", "metres"], conversions={"cm": "1/100"})
        accepted = [
            ("FINAL: 35", gold("35")),
            ("Wrong intermediate: 99\nFINAL: 35", gold("35")),
            ("final: 35", gold("35")),
            ("FiNaL: 35\n\n", gold("35")),
            ("FINAL: +35", gold("35")),
            ("FINAL: -35", gold("-35")),
            ("FINAL: −35", gold("-35")),
            ("FINAL: ३५", gold("35")),
            ("FINAL: 0", gold("0")),
            ("FINAL: -0", gold("0")),
            ("FINAL: 1/3", gold("1/3")),
            ("FINAL: 2/6", gold("1/3")),
            ("FINAL: -1/-3", gold("1/3")),
            ("FINAL: 1/-3", gold("-1/3")),
            ("FINAL: 0.5", gold("1/2")),
            ("FINAL: .5", gold("1/2")),
            ("FINAL: 50%", gold("1/2")),
            ("FINAL: 0.333.", gold("333/1000")),
            ("FINAL: 35 marbles.", count),
            ("FINAL: 35 KANCHE", count),
            ("FINAL: 100 cm", metre),
            ("FINAL: 1 metre", metre),
            ("FINAL: ₹1,00,000", money),
            ("FINAL: INR 100,000", money),
            ("FINAL: 100000 rs", money),
            ("FINAL: 100000 rupees.", money),
            ("FINAL: 35", gold("35", "marbles", omission=True)),
            ("FINAL: 1,23,45,678", gold("12345678")),
            ("FINAL: 12,345,678", gold("12345678")),
            ("FINAL: 1,000/2", gold("500")),
        ]
        rejected = [
            ("FINAL: 34", gold("35")),
            ("35 is intermediate\nFINAL: 34", gold("35")),
            ("FINAL: .333", gold("1/3")),
            ("FINAL: 50", gold("1/2")),
            ("FINAL: -35", gold("35")),
            ("FINAL: 1/0", gold("0")),
            ("FINAL: NaN", gold("0")),
            ("FINAL: infinity", gold("0")),
            ("FINAL: 35 apples", count),
            ("FINAL: 35", count),
            ("FINAL: 1 kg", metre),
            ("FINAL: 1 cm", metre),
            ("FINAL: 50% m", metre),
            ("FINAL: ₹35", gold("35")),
            ("FINAL: INR 100000 m", money),
            ("FINAL: 1,00000", money),
            ("FINAL: 10,00,00", money),
            ("FINAL: 1,,000", gold("1000")),
            ("FINAL: 01,000", gold("1000")),
            ("FINAL: 1,234,56", gold("123456")),
            ("FINAL: 35 or 36", gold("35")),
            ("FINAL: 35 = 36", gold("35")),
            ("FINAL: 35\nFINAL: 35", gold("35")),
            ("FINAL: 35\nfinal: 36", gold("35")),
            ("FINAL: 35\nMore explanation", gold("35")),
            ("The answer is 35", gold("35")),
            ("FINAL:", gold("35")),
            ("I cannot answer.\nFINAL: 35", gold("35")),
            ("FINAL: __import__('os')", gold("35")),
            ("FINAL: 35..", gold("35")),
        ]
        self.assertEqual(len(accepted), len(rejected))
        self.assertGreaterEqual(len(accepted) + len(rejected), 40)
        for expected, cases in ((True, accepted), (False, rejected)):
            for response, reference in cases:
                with self.subTest(response=response, expected=expected):
                    result = score_response(response, reference)
                    self.assertIs(result["correct"], expected)
                    self.assertEqual(result["scorer_version"], SCORER_VERSION)
                    if expected:
                        self.assertIsNone(result["invalid_reason"])

    def test_normalization_and_schema(self):
        result = score_response("FINAL: 100 cm.", gold("1", "m", conversions={"cm": "1/100"}))
        self.assertEqual(result, {
            "correct": True,
            "invalid_reason": None,
            "extracted_final": "100 cm.",
            "normalized_value": "1",
            "normalized_unit": "m",
            "scorer_version": SCORER_VERSION,
        })
        result = score_response("FINAL: .333", gold("1/3"))
        self.assertFalse(result["correct"])
        self.assertIsNone(result["invalid_reason"])
        self.assertEqual(result["normalized_value"], "333/1000")

    def test_failure_reasons(self):
        for response, truncated, reason in [
            ("FINAL: 35", True, "truncated"),
            ("I cannot solve this", False, "refusal"),
            ("I can't solve this", False, "refusal"),
            ("", False, "missing_final"),
            ("FINAL: 35\nFINAL: 36", False, "multiple_finals"),
            ("FINAL: 35\ncontinued", False, "final_not_terminal_line"),
            ("FINAL:", False, "empty_final"),
            ("FINAL: 35 kg", False, "invalid_unit"),
            ("FINAL: 1/0", False, "zero_denominator"),
            ("FINAL: 1,00", False, "invalid_numeric_grouping"),
        ]:
            with self.subTest(response=response, truncated=truncated):
                result = score_response(response, gold("35"), truncated)
                self.assertFalse(result["correct"])
                self.assertEqual(result["invalid_reason"], reason)


if __name__ == "__main__":
    unittest.main()
