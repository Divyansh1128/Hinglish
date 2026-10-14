import json
import unittest
from fractions import Fraction
from pathlib import Path

from secondary_analysis.numeric_endpoint import numeric_correct
from test1_pilot.hinglish_pilot.data import validate_gold

FIXTURE = Path(__file__).resolve().parents[1] / "format_fixtures.json"


class FixtureTests(unittest.TestCase):
    def test_schema_ids_exclusion_and_coverage(self):
        data = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.assertEqual(data["label"], "EXCLUDED_FORMAT_FIXTURE")
        self.assertEqual(data["adoption_status"], "UNADOPTED")
        self.assertFalse(data["human_validated"])
        self.assertFalse(data["model_inference_performed"])
        self.assertEqual(len(data["families"]), 12)
        identities, render_ids, texts = [], [], []
        units = set()
        for family in data["families"]:
            self.assertEqual(family["status"], "EXCLUDED_FORMAT_FIXTURE")
            self.assertEqual(family["split_role"], "EXCLUDED_FORMAT_FIXTURE")
            self.assertEqual(family["authoring_origin"], "AI_SYNTHETIC_UNREVIEWED")
            validate_gold(family["gold"])
            self.assertTrue(numeric_correct("FINAL: " + family["gold"]["value"] + " " + family["gold"]["unit"], family["gold"]))
            units.add(family["gold"]["unit"])
            identities.extend(family[k] for k in ("family_id", "source_family_id", "template_group_id"))
            self.assertEqual(set(family["forms"]), {"E", "R", "C"})
            for form, rendering in family["forms"].items():
                self.assertEqual(rendering["status"], "EXCLUDED_FORMAT_FIXTURE")
                self.assertEqual(rendering["rendering_id"], family["family_id"] + "-" + form)
                self.assertTrue(rendering["text"].strip())
                render_ids.append(rendering["rendering_id"])
                texts.append(" ".join(rendering["text"].casefold().split()))
        self.assertEqual(len(set(render_ids)), 36)
        self.assertEqual(len(set(identities)), 36)
        self.assertEqual(len(set(texts)), 36)
        self.assertTrue(all(identity.startswith("FMT2-") for identity in identities + render_ids))
        self.assertEqual(set(data["development_exclusion_ids"]), set(identities + render_ids))
        self.assertTrue({"INR", "kg", "L", "km", "minute", "beads", ""} <= units)

    def test_independently_check_synthetic_arithmetic(self):
        expected = [7*43+29, 132400+8750, Fraction(58+14, 9), 4*(17-11), Fraction(11, 17),
                    Fraction(7, 27), Fraction(345+85, 100), 6*Fraction(625, 1000),
                    Fraction(270-45, 100), Fraction(180+65, 100), 4*13+7, 8*13+5]
        data = json.loads(FIXTURE.read_text())
        for family, value in zip(data["families"], expected):
            with self.subTest(family=family["family_id"]):
                self.assertEqual(Fraction(family["gold"]["value"]), value)


if __name__ == "__main__":
    unittest.main()
