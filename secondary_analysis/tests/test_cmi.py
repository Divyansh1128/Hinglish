import csv
import hashlib
import json
import subprocess
import sys
import tempfile
import unicodedata
import unittest
from pathlib import Path

from secondary_analysis.cmi import (
    HEURISTIC_LABEL, analyze_tags, cmi, heuristic_annotation, heuristic_tag,
    switch_points, tokenize, write_dataset_sheets,
)


class CmiTests(unittest.TestCase):
    def test_empty_and_all_shared(self):
        for tokens in ([], [("19", "SHARED"), (".", "SHARED"), ("Tara", "SHARED")]):
            result = analyze_tags(tokens)
            self.assertEqual(result["CMI_v1"], 0)
            self.assertTrue(result["no_language_tokens"])
            self.assertEqual(result["switch_points"], 0)

    def test_monolingual(self):
        for tag in ("HI", "EN", "hi", "en"):
            result = analyze_tags([("a", tag), ("b", tag), ("19", "univ")])
            self.assertEqual(result["cmi"], 0)
            self.assertFalse(result["no_language_tokens"])

    def test_balanced_excludes_shared_and_breaks_at_period(self):
        # Previously expected 3 switches across '.', contrary to spec §5.
        result = analyze_tags([("a", "hi"), ("b", "en"), (".", "univ"), ("c", "hi"), ("d", "en")])
        self.assertEqual(result["cmi"], 50.0)
        self.assertEqual((result["N"], result["U"], result["H"], result["E"]), (5, 1, 2, 2))
        self.assertEqual(result["switch_points"], 2)
        self.assertEqual(result["MIXED"], 0)
        self.assertEqual(result["UNCERTAIN"], 0)

    def test_legacy_mapping_matches_canonical(self):
        old = [("aur", "hi"), ("19", "univ"), ("beads", "en")]
        new = [("aur", "HI"), ("19", "SHARED"), ("beads", "EN")]
        self.assertEqual(analyze_tags(old), analyze_tags(new))
        self.assertEqual(analyze_tags(old)["hi"], 1)
        self.assertEqual(analyze_tags(old)["en"], 1)

    def test_unbalanced_and_switch_skip_policy(self):
        tokens = [("a", "hi"), ("b", "hi"), ("c", "univ"), ("d", "en"), ("e", "univ"), ("f", "hi")]
        self.assertEqual(cmi(tokens), 25)
        self.assertEqual(switch_points(tokens), 2)

    def test_unresolved_missing_and_breaks_switches(self):
        for unresolved in ("MIXED", "UNCERTAIN"):
            with self.subTest(tag=unresolved):
                result = analyze_tags([("aur", "HI"), ("x", unresolved), ("beads", "EN"), ("19", "SHARED")])
                self.assertIsNone(result["cmi"])
                self.assertIsNone(result["CMI_v1"])
                self.assertEqual(result[unresolved], 1)
                self.assertEqual((result["N"], result["U"], result["H"], result["E"]), (4, 1, 1, 1))
                self.assertEqual(result["switch_points"], 0)
                self.assertFalse(result["no_language_tokens"])
        both = analyze_tags([("a", "MIXED"), ("b", "UNCERTAIN")])
        self.assertEqual((both["MIXED"], both["UNCERTAIN"]), (1, 1))
        self.assertIsNone(both["cmi"])

    def test_sentence_boundaries(self):
        for boundary in (".", "?", "!", "...", "\n", "\r\n"):
            with self.subTest(boundary=boundary):
                tokens = [("aur", "HI"), (boundary, "SHARED"), ("beads", "EN")]
                self.assertEqual(switch_points(tokens), 0)
                self.assertEqual(cmi(tokens), 50)
        self.assertEqual(switch_points([("aur", "HI"), ("beads", "EN")], sentence_ends=[0]), 0)
        self.assertEqual(switch_points([("aur", "HI"), (",", "SHARED"), ("beads", "EN")]), 1)
        self.assertEqual(switch_points([("aur", "HI"), ("1.25", "SHARED"), ("beads", "EN")]), 1)

    def test_invalid_tags_and_tokens_rejected(self):
        for tokens in ([('a', 'other')], [(19, 'univ')], [('a', [])], [('a', 'mixed')]):
            with self.subTest(tokens=tokens), self.assertRaises(ValueError):
                cmi(tokens)

    def test_heuristic_labels_and_names(self):
        self.assertEqual(heuristic_tag("Tara has 19 beads aur kul kitne hain?"),
                         [("Tara", "SHARED"), ("has", "EN"), ("19", "SHARED"), ("beads", "EN"),
                          ("aur", "HI"), ("kul", "HI"), ("kitne", "HI"), ("hain", "HI"), ("?", "SHARED")])
        # Unknown capitalized words and homographs used to become univ; §5
        # requires UNCERTAIN until a human resolves their meaning/name status.
        self.assertEqual(heuristic_tag("InventedName Zorbin 1.25, to the is me kg", names=["InventedName"]),
                         [("InventedName", "SHARED"), ("Zorbin", "UNCERTAIN"), ("1.25", "SHARED"),
                          (",", "SHARED"), ("to", "UNCERTAIN"), ("the", "UNCERTAIN"),
                          ("is", "UNCERTAIN"), ("me", "UNCERTAIN"), ("kg", "SHARED")])
        self.assertEqual(heuristic_tag("bus cycle jag tikat pensil"),
                         [(w, "UNCERTAIN") for w in "bus cycle jag tikat pensil".split()])
        draft = heuristic_annotation("aur beads")
        self.assertEqual(draft["label"], HEURISTIC_LABEL)
        self.assertFalse(draft["human_corrected"])
        self.assertEqual(draft["heuristic_diagnostic"]["cmi"], 50)
        self.assertIsNone(heuristic_annotation("aur unknown beads")["heuristic_diagnostic"]["cmi"])

    def test_tokenization_and_nfc_offsets(self):
        text = "Cafe\u0301's Hindi-English 1.25kg 3/8 L, लड़के!"
        normalized = unicodedata.normalize("NFC", text)
        tokens = tokenize(text)
        self.assertEqual([t["token"] for t in tokens],
                         ["Café's", "Hindi", "-", "English", "1.25", "kg", "3/8", "L", ",", "लड़के", "!"])
        for token in tokens:
            self.assertEqual(normalized[token["start"]:token["end"]], token["token"])
        draft = heuristic_annotation(text)
        self.assertEqual(draft["text_sha256"], hashlib.sha256(normalized.encode()).hexdigest())
        self.assertNotEqual(draft["source_text_sha256"], draft["text_sha256"])

    def test_newline_metadata_and_diagnostics(self):
        draft = heuristic_annotation("aur\n\nbeads, aur! beads")
        tokens = draft["tokens"]
        self.assertEqual([t["token"] for t in tokens], ["aur", "beads", ",", "aur", "!", "beads"])
        self.assertEqual([t["sentence_id"] for t in tokens], [0, 1, 1, 1, 1, 2])
        self.assertEqual([t["sentence_end"] for t in tokens], [True, False, False, False, True, False])
        self.assertEqual(draft["heuristic_diagnostic"]["switch_points"], 1)

    def test_cli_writes_editable_tags_without_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "tags.json"
            command = [sys.executable, "-B", "-m", "secondary_analysis.cmi", "Tara has 19 beads aur", "--output", str(path)]
            subprocess.run(command, check=True, capture_output=True)
            content = path.read_bytes()
            self.assertFalse(json.loads(content)["human_corrected"])
            self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
            self.assertEqual(path.read_bytes(), content)


class DatasetSheetTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.dataset = self.root / "dataset.json"
        self.output = self.root / "new_sheets"
        self.data = dict(borrowing_policy="DRAFT policy; HUMAN MUST FREEZE", families=[
            dict(family_id=f"family-{i}", gold={"value": "GOLD_SENTINEL_DO_NOT_EXPORT"},
                 reference_solution_en="SOLUTION_SENTINEL_DO_NOT_EXPORT", forms={
                     "E": dict(text="ENGLISH_SENTINEL_DO_NOT_EXPORT"),
                     "R": dict(rendering_id=f"family-{i}-R", text="Tara aur\nbeads?"),
                     "C": dict(rendering_id=f"family-{i}-C", text="Tara has 1.25kg aur beads."),
                 }) for i in range(2)])
        self.save()

    def save(self):
        self.dataset.write_text(json.dumps(self.data), encoding="utf-8")

    def command(self, *extra):
        return [sys.executable, "-B", "-m", "secondary_analysis.cmi", "--dataset", str(self.dataset),
                "--output-dir", str(self.output), *extra]

    def test_cli_all_renderings_editable_csv_no_gold_or_e(self):
        original = self.dataset.read_bytes()
        result = subprocess.run(self.command(), check=True, capture_output=True, text=True)
        self.assertIn(HEURISTIC_LABEL, result.stdout)
        self.assertIn("One human must correct", result.stdout)
        self.assertEqual({p.name for p in self.output.iterdir()}, {"R.csv", "C.csv"})
        for form, count in (("R", 8), ("C", 14)):
            content = (self.output / f"{form}.csv").read_text()
            for secret in ("GOLD_SENTINEL", "SOLUTION_SENTINEL", "ENGLISH_SENTINEL"):
                self.assertNotIn(secret, content + result.stdout + result.stderr)
            with (self.output / f"{form}.csv").open(newline="", encoding="utf-8") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), count)
            self.assertEqual({r["rendering_id"] for r in rows}, {f"family-{i}-{form}" for i in range(2)})
            for row in rows:
                self.assertEqual(row["label"], HEURISTIC_LABEL)
                self.assertEqual(row["human_corrected"], "False")
                self.assertEqual(row["form"], form)
                self.assertEqual((row["tagger"], row["adjudicator"]), ("", ""))
                self.assertEqual(row["borrowing_policy"], self.data["borrowing_policy"])
                source = self.data["families"][int(row["family_id"][-1])]["forms"][form]["text"]
                self.assertEqual(source[int(row["start"]):int(row["end"])], row["token"])
                self.assertEqual(row["text_sha256"], hashlib.sha256(source.encode()).hexdigest())
        self.assertEqual(self.dataset.read_bytes(), original)

    def test_refuses_existing_directory_without_modification(self):
        write_dataset_sheets(self.dataset, self.output)
        contents = {p.name: p.read_bytes() for p in self.output.iterdir()}
        result = subprocess.run(self.command(), capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual({p.name: p.read_bytes() for p in self.output.iterdir()}, contents)
        empty = self.root / "empty"
        empty.mkdir()
        with self.assertRaises(FileExistsError):
            write_dataset_sheets(self.dataset, empty)
        self.assertEqual(list(empty.iterdir()), [])

    def test_refuses_pilot_and_symlinked_pilot(self):
        pilot = self.root / "pilot"
        pilot.mkdir()
        alias = self.root / "elsewhere"
        alias.symlink_to(pilot, target_is_directory=True)
        for path in (pilot / "sheets", alias / "sheets"):
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "pilot/"):
                write_dataset_sheets(self.dataset, path)
        command = [sys.executable, "-B", "-m", "secondary_analysis.cmi", "aur", "--output", str(pilot / "tags.json")]
        self.assertNotEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(list(pilot.iterdir()), [])

    def test_malformed_or_incomplete_dataset_creates_no_directory(self):
        mutations = [lambda d: d.update(families=[]),
                     lambda d: d["families"][1]["forms"].pop("C"),
                     lambda d: d["families"][1]["forms"]["C"].update(text=""),
                     lambda d: d["families"][1].update(family_id="family-0"),
                     lambda d: d["families"][1]["forms"]["C"].update(rendering_id="family-0-C")]
        for mutation in mutations:
            copy = json.loads(json.dumps(self.data))
            mutation(copy)
            self.dataset.write_text(json.dumps(copy))
            with self.assertRaises(ValueError):
                write_dataset_sheets(self.dataset, self.output)
            self.assertFalse(self.output.exists())
        self.dataset.write_text("{")
        self.assertNotEqual(subprocess.run(self.command(), capture_output=True).returncode, 0)
        self.assertFalse(self.output.exists())

    def test_string_forms_and_supplied_names(self):
        self.data = dict(families=[dict(family_id="string", forms={"R": "InventedName aur", "C": "InventedName beads"})])
        self.save()
        self.assertEqual(write_dataset_sheets(self.dataset, self.output, names=["InventedName"]), {"R": 2, "C": 2})
        with (self.output / "R.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(rows[0]["tag"], "SHARED")
        self.assertEqual(rows[0]["rendering_id"], "string-R")
        self.assertIn("NOT FROZEN", rows[0]["borrowing_policy"])

    def test_csv_formula_text_escaped(self):
        self.data["families"][0]["forms"]["R"]["text"] = "= + - @ aur"
        self.save()
        write_dataset_sheets(self.dataset, self.output)
        with (self.output / "R.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual([r["token"] for r in rows[:4]], ["'=", "'+", "'-", "'@"])

    def test_cli_invalid_mode_combinations(self):
        for extra in (["unexpected text"], ["--output", str(self.root / "tags.json")]):
            self.assertNotEqual(subprocess.run(self.command(*extra), capture_output=True).returncode, 0)
        missing_output = self.command()[:-2]
        self.assertNotEqual(subprocess.run(missing_output, capture_output=True).returncode, 0)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
