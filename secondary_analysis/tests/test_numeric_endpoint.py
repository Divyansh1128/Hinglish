import hashlib
import unittest
from pathlib import Path

from pilot.scripts.scorer import score_response as original_score
from test1_pilot.hinglish_pilot.scorer_v1 import score_response as portable_score
from secondary_analysis.numeric_endpoint import evaluate_numeric, extract_numeric, numeric_correct

ROOT = Path(__file__).resolve().parents[2]
FROZEN_SCORER_SHA256 = "c48f9d12e733eb1bfe5af5b1fece6e3ff69cb2342a97fe3ba8ac9f01f68dbbbc"


def gold(value="19", unit="", aliases=(), conversions=None):
    return dict(value=value, unit=unit, aliases=list(aliases), conversions=conversions or {},
                unit_omission_allowed=True, rounding_rule="exact")


# Synthetic values only: no pilot data or existing format fixture is loaded.
# Every category in scorer_probe_output.txt, including accepted controls.
PROBE_CASES = [
    ("plain FINAL line", "FINAL: 19", gold(), None),
    ("markdown header", "## Answer\nFINAL: 19", gold(), None),
    ("bold marker", "**FINAL:** 19", gold(), "final_not_terminal_line"),
    ("bold value", "FINAL: **19**", gold(), "invalid_number"),
    ("boxed value", r"FINAL: \boxed{19}", gold(), "invalid_number"),
    ("dollar value", "FINAL: $19$", gold(), "invalid_number"),
    ("note after FINAL", "FINAL: 19\nChecked the result.", gold(), "final_not_terminal_line"),
    ("cannot in reasoning", "I cannot use the shortcut, so I add directly.\nFINAL: 19", gold(), "refusal"),
    ("prefix Rs.", "FINAL: Rs. 19", gold(unit="INR", aliases=["Rs.", "rupaye"]), "invalid_number"),
    ("prefix Rs", "FINAL: Rs 19", gold(unit="INR", aliases=["Rs.", "rupaye"]), "invalid_number"),
    ("prefix rupee symbol", "FINAL: ₹19", gold(unit="INR", aliases=["Rs.", "rupaye"]), None),
    ("suffix rupaye", "FINAL: 19 rupaye", gold(unit="INR", aliases=["Rs.", "rupaye"]), None),
    ("currency slash dash", "FINAL: ₹19/-", gold(unit="INR", aliases=["Rs.", "rupaye"]), "invalid_answer"),
    ("dimensionless plain", "FINAL: 19", gold(), None),
    ("x assignment", "FINAL: x = 19", gold(), "invalid_number"),
    *[("romanized " + unit, "FINAL: 19 " + unknown, gold(unit=unit), "invalid_unit")
      for unit, unknown in [("kg", "kilo"), ("minute", "minat"), ("L", "litar"), ("m", "mitar"), ("km", "kilomitar")]],
]


class NumericTests(unittest.TestCase):
    def test_all_probe_cases_extract_correctly(self):
        for name, response, expected, _ in PROBE_CASES:
            with self.subTest(name=name):
                self.assertTrue(numeric_correct(response, expected))
                self.assertEqual(extract_numeric(response)["value"], "19")

    def test_all_probe_cases_keep_both_frozen_scorers_unchanged(self):
        paths = [ROOT / "pilot/scripts/scorer.py", ROOT / "test1_pilot/hinglish_pilot/scorer_v1.py"]
        self.assertEqual(paths[0].read_bytes(), paths[1].read_bytes())
        for path in paths:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), FROZEN_SCORER_SHA256)
        for name, response, expected, reason in PROBE_CASES:
            with self.subTest(name=name):
                a, b = original_score(response, expected), portable_score(response, expected)
                self.assertEqual(a, b)
                self.assertEqual(a["scorer_version"], "1.0.0")
                self.assertEqual(a["invalid_reason"], reason)
                self.assertEqual(a["correct"], reason is None)

    def test_extraction_paths(self):
        for text, label in [("**FINAL:** 19", "bold_marker"), ("FINAL: **19**", "bold"),
                            (r"FINAL: \boxed{19}", "boxed"), ("FINAL: $19$", "dollar"),
                            ("FINAL: x = 19", "assignment"), ("FINAL: n=19", "assignment"),
                            ("FINAL: ₹19/-", "currency_slash_dash"), ("**FINAL: 19**", "bold_line")]:
            with self.subTest(text=text):
                self.assertIn(label, extract_numeric(text)["extraction_path"])
                self.assertEqual(extract_numeric(text)["value"], "19")

    def test_single_final_ignores_and_flags_later_lines(self):
        result = extract_numeric("Reasoning mentions 300.\nFINAL: 19 kg\nNote: batch 500 is next.")
        self.assertEqual((result["value"], result["suffix"], result["final_markers"]), ("19", "kg", 1))
        self.assertTrue(result["trailing_nonblank"])
        self.assertFalse(extract_numeric("FINAL: 19\n\n  \n")["trailing_nonblank"])

    def test_multiple_finals_always_fail(self):
        for response in ("FINAL: 19\nFINAL: 20", "FINAL: 19\n**FINAL:** 19", "Reasoning: FINAL: 3\nFINAL: 19"):
            with self.subTest(response=response):
                self.assertIsNone(extract_numeric(response)["value"])
                self.assertEqual(extract_numeric(response)["status"], "multiple_finals")
                self.assertFalse(numeric_correct(response, gold()))

    def test_no_recovery_without_a_line_start_marker(self):
        for response in ("19", "x = 19", r"\boxed{19}", "Reasoning contains 100.\nx = 19", ""):
            self.assertEqual(extract_numeric(response)["status"], "missing_final")
        for response in ("The FINAL: 19", "- FINAL: 19", "### FINAL: 19", "`FINAL: 19`"):
            self.assertEqual(extract_numeric(response)["status"], "unsupported_marker")
        self.assertEqual(extract_numeric("FINAL:")["status"], "empty_final")
        self.assertEqual(extract_numeric("FINAL: no answer")["status"], "unsupported_answer")

    def test_not_generated_and_truncated(self):
        self.assertEqual(extract_numeric(None)["status"], "not_generated")
        result = evaluate_numeric("FINAL: 19", gold(), truncated=True)
        self.assertEqual(result["status"], "truncated")
        self.assertFalse(result["correct"])

    def test_exact_fractions_decimals_percent(self):
        for text, expected in [("FINAL: -1.25", "-5/4"), ("FINAL: +.125", "1/8"),
                               ("FINAL: 3 / 8", "3/8"), ("FINAL: 1.5/3", "1/2"),
                               ("FINAL: 12.5%", "1/8"), ("FINAL: ०.१२५", "1/8"),
                               ("FINAL: −3", "-3"), ("FINAL: 19.", "19"), ("final : 19", "19")]:
            with self.subTest(text=text):
                self.assertEqual(extract_numeric(text)["value"], expected)
                self.assertTrue(numeric_correct(text, gold(expected)))

    def test_grouping(self):
        for text in ("FINAL: ₹1,41,150/-", "FINAL: INR 141,150", "FINAL: Rs. 1,41,150", "FINAL: 1,41,150 Rs."):
            self.assertEqual(extract_numeric(text)["value"], "141150")
        for number in ("1,2,3", "01,000", "1,234,56"):
            with self.subTest(number=number):
                self.assertEqual(extract_numeric("FINAL: " + number)["status"], "invalid_numeric_grouping")

    def test_nested_wrappers_and_currency(self):
        for text in (r"FINAL: **\boxed{19}**", "FINAL: Rs. **19**", "FINAL: $x = 19$",
                     "**final**: **19**", "**final:** 19", "FINAL: **19 kg**", "FINAL: 19kg"):
            with self.subTest(text=text):
                self.assertEqual(extract_numeric(text)["value"], "19")

    def test_malformed_and_non_scalar_answers(self):
        for response, reason in [("FINAL: 19 or 20", "unsupported_answer"), ("FINAL: 19+2", "unsupported_answer"),
                                 ("FINAL: 19, 20", "invalid_numeric_grouping"), ("FINAL: 19.2.3", "unsupported_answer"),
                                 ("FINAL: 19/0", "zero_denominator"), ("FINAL: (19, 20)", "unsupported_answer"),
                                 ("FINAL: 3:5", "unsupported_answer"), ("FINAL: 1e3", "unsupported_answer"),
                                 (r"FINAL: \frac{19}{1}", "unsupported_answer"), (r"FINAL: \text{19}", "unsupported_answer"),
                                 ("FINAL: $$19$$", "unsupported_answer"), ("FINAL: **19", "malformed_wrapper"),
                                 ("FINAL: $19", "malformed_wrapper"), (r"FINAL: \boxed{19", "malformed_wrapper"),
                                 ("FINAL: ₹19 /- kg", "unsupported_answer")]:
            with self.subTest(response=response):
                result = extract_numeric(response)
                self.assertIsNone(result["value"])
                self.assertEqual(result["status"], reason)

    def test_no_unit_conversion_and_suffix_flags(self):
        expected = gold("19/10", "kg", ["kilograms"], {"g": "1/1000"})
        self.assertFalse(numeric_correct("FINAL: 1900 g", expected))  # equivalent quantity, other unit
        self.assertTrue(numeric_correct("FINAL: 1.9 g", expected))     # right literal, wrong unit
        result = evaluate_numeric("FINAL: 1.9 kilos", expected)
        self.assertTrue(result["correct"])
        self.assertTrue(result["unvalidated_suffix"])
        self.assertEqual(result["unknown_unit"], "kilos")
        self.assertFalse(evaluate_numeric("FINAL: 1.9 KILOGRAMS", expected)["unvalidated_suffix"])
        self.assertFalse(evaluate_numeric("FINAL: 1.9", expected)["unvalidated_suffix"])
        self.assertEqual(evaluate_numeric("FINAL: 2", expected)["status"], "mismatch")

    def test_refusal_text_does_not_veto(self):
        self.assertTrue(numeric_correct("I cannot add these directly.\nFINAL: 19", gold()))

    def test_functions_do_not_mutate_gold(self):
        import copy
        expected = gold(unit="kg", conversions={"g": "1/1000"})
        before = copy.deepcopy(expected)
        numeric_correct("FINAL: 19000 g", expected)
        self.assertEqual(expected, before)


if __name__ == "__main__":
    unittest.main()
