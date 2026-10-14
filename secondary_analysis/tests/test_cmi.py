import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from secondary_analysis.cmi import HEURISTIC_LABEL, analyze_tags, cmi, heuristic_annotation, heuristic_tag, switch_points


class CmiTests(unittest.TestCase):
    def test_empty_and_all_universal(self):
        for tokens in ([], [("19", "univ"), (".", "univ"), ("Tara", "univ")]):
            self.assertEqual(cmi(tokens), 0)
            self.assertEqual(switch_points(tokens), 0)

    def test_monolingual(self):
        for tag in ("hi", "en"):
            self.assertEqual(cmi([("a", tag), ("b", tag), ("19", "univ")]), 0)

    def test_balanced_excludes_universal(self):
        result = analyze_tags([("a", "hi"), ("b", "en"), (".", "univ"), ("c", "hi"), ("d", "en")])
        self.assertEqual(result, dict(cmi=50.0, N=5, U=1, hi=2, en=2, switch_points=3, switch_policy="skip_univ"))

    def test_unbalanced_and_switch_skip_policy(self):
        tokens = [("a", "hi"), ("b", "hi"), ("c", "univ"), ("d", "en"), ("e", "univ"), ("f", "hi")]
        self.assertEqual(cmi(tokens), 25)
        self.assertEqual(switch_points(tokens), 2)

    def test_invalid_tags_and_tokens_rejected(self):
        for tokens in ([('a', 'other')], [(19, 'univ')]):
            with self.assertRaises(ValueError):
                cmi(tokens)

    def test_heuristic_labels_and_names(self):
        tagged = heuristic_tag("Tara has 19 beads aur kul kitne hain?", names=["InventedName"])
        self.assertEqual(tagged, [("Tara", "univ"), ("has", "en"), ("19", "univ"), ("beads", "en"),
                                  ("aur", "hi"), ("kul", "hi"), ("kitne", "hi"), ("hain", "hi"), ("?", "univ")])
        self.assertEqual(heuristic_tag("InventedName Zorbin 1.25, to the"),
                         [("InventedName", "univ"), ("Zorbin", "univ"), ("1.25", "univ"),
                          (",", "univ"), ("to", "univ"), ("the", "univ")])
        draft = heuristic_annotation("aur beads")
        self.assertEqual(draft["label"], HEURISTIC_LABEL)
        self.assertFalse(draft["human_corrected"])
        self.assertEqual(draft["heuristic_diagnostic"]["cmi"], 50)
        self.assertIsInstance(draft["tokens"], list)

    def test_cli_writes_editable_tags_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tags.json"
            command = [sys.executable, "-B", "-m", "secondary_analysis.cmi", "Tara has 19 beads aur", "--output", str(path)]
            subprocess.run(command, check=True, capture_output=True)
            content = path.read_bytes()
            self.assertFalse(json.loads(content)["human_corrected"])
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
