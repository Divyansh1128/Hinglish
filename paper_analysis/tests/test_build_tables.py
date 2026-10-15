import contextlib
import copy
import csv
import hashlib
import importlib.util
import io
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "test1_pilot"))

from hinglish_pilot.engine import FakeBackend, default_config, read, run  # noqa: E402
from hinglish_pilot.report import export  # noqa: E402
from paper_analysis import build_tables as bt  # noqa: E402
from paper_analysis.safezip import UnsafeArchive, read_zip, verify_checksums  # noqa: E402

HAS_MPL = importlib.util.find_spec("matplotlib") is not None
# FakeBackend answers 'FINAL: 5' for DEMO-ADD, 'FINAL: 0.5' for DEMO-HALF, otherwise no FINAL line.
# Patterns vary by form so paired differences and bootstrap intervals are non-trivial.
PATTERNS = [("ADD", "ADD", "ADD"), ("ADD", None, "HALF"), ("ADD", "ADD", None),
            (None, "ADD", "ADD"), ("ADD", "HALF", None), ("HALF", None, "ADD")]
TOPICS = ["comparison_remaining", "two_step_money", "fractions_percentages", "ratios", "rates_units",
          "elementary_algebra"]


def synthetic_dataset():
    base = read(ROOT / "test1_pilot" / "fixtures" / "demo_dataset.json")
    template = base["families"][0]
    families, exclusions = [], []
    for index, pattern in enumerate(PATTERNS, 1):
        family = copy.deepcopy(template)
        fid = f"pa-{index}"
        family.update(family_id=fid, source_family_id=fid + "-source", template_group_id=fid + "-template",
                      topic=TOPICS[index - 1])
        for form, marker in zip("ERC", pattern):
            prefix = f"DEMO-{marker}: " if marker else "Plain: "
            family["forms"][form]["rendering_id"] = f"{fid}-{form}"
            family["forms"][form]["text"] = f"{prefix}family {index} form {form}: 2 and 3 counters, how many?"
        families.append(family)
        exclusions += [fid, fid + "-source", fid + "-template"]
    base["families"] = families
    splits = read(ROOT / "test1_pilot" / "fixtures" / "demo_splits.json")
    splits["development_exclusion_ids"] = exclusions
    return base, splits


def config():
    value = default_config("demo")
    value.update(model_revision="0" * 40, tokenizer_revision="0" * 40)
    return value


def rewrite(source, target, change):
    """Copy a ZIP, letting change(members_dict) mutate the content."""
    with zipfile.ZipFile(source) as archive:
        members = {name: archive.read(name) for name in archive.namelist()}
    change(members)
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, blob in members.items():
            archive.writestr(name, blob)
    return target


def rechecksum(members):
    lines = "".join(f"{hashlib.sha256(blob).hexdigest()}  {name}\n"
                    for name, blob in members.items() if name != "checksums.sha256")
    members["checksums.sha256"] = lines.encode()


def quiet(function, *args, **kwargs):
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        return function(*args, **kwargs)


class BuildTablesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.dir = Path(cls.tmp.name)
        dataset, splits = synthetic_dataset()
        manifest = run(cls.dir / "synthetic", dataset, splits, config(), FakeBackend())
        assert manifest["status"] == "COMPLETE"
        cls.complete = export(cls.dir / "synthetic")
        demo = read(ROOT / "test1_pilot" / "fixtures" / "demo_dataset.json")
        demo_splits = read(ROOT / "test1_pilot" / "fixtures" / "demo_splits.json")
        run(cls.dir / "demo", demo, demo_splits, config(), FakeBackend())
        cls.demo = export(cls.dir / "demo")
        manifest = run(cls.dir / "partial", dataset, splits, config(), FakeBackend(), max_items=5)
        assert manifest["status"] == "INCOMPLETE"
        cls.incomplete = export(cls.dir / "partial")
        cls.count = 0

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def out(self):
        type(self).count += 1
        return self.dir / f"out-{self.count}"

    def members(self, path):
        with zipfile.ZipFile(path) as archive:
            return {name: archive.read(name) for name in archive.namelist()}

    # ------------------------------------------------------------ integrity

    def test_every_checksum_entry_verified(self):
        members = read_zip(self.complete.read_bytes())
        listed = verify_checksums(members)
        self.assertEqual(set(listed), set(members) - {"checksums.sha256"})
        self.assertIn("generation_attempts.jsonl", listed)
        out = self.out()
        bt.build([self.complete], out, figures=False)
        self.assertIn(f"All {len(listed)} checksums.sha256 entries verified.",
                      (out / "synthetic" / "tables.md").read_text(encoding="utf-8"))

    def test_tampered_member_rejected_and_nothing_written(self):
        def change(members):
            members["predictions.csv"] = members["predictions.csv"].replace(b"True", b"False", 1)
        bad = rewrite(self.complete, self.dir / "tampered_results.zip", change)
        with self.assertRaisesRegex(UnsafeArchive, "checksum mismatch for 'predictions.csv'"):
            bt.build([bad], self.out(), figures=False)
        out = self.out()
        self.assertEqual(quiet(bt.main, [str(bad), "--out", str(out), "--no-figures"]), 1)
        self.assertFalse(out.exists())

    def test_tampered_score_with_recomputed_checksums_rejected(self):
        def change(members):
            lines = members["generation_attempts.jsonl"].decode().splitlines()
            record = json.loads(lines[0])
            record["correct"] = not record["correct"]
            lines[0] = json.dumps(record, ensure_ascii=False)
            members["generation_attempts.jsonl"] = ("\n".join(lines) + "\n").encode()
            rechecksum(members)
        bad = rewrite(self.complete, self.dir / "rescored_results.zip", change)
        with self.assertRaisesRegex(bt.AnalysisError, "record_sha256"):
            bt.build([bad], self.out(), figures=False)

    def test_missing_or_unlisted_checksum_coverage_rejected(self):
        def extra(members):
            members["notes.txt"] = b"unlisted"
        with self.assertRaisesRegex(UnsafeArchive, "not covered"):
            verify_checksums(read_zip(rewrite(self.complete, self.dir / "extra.zip", extra).read_bytes()))

        def drop(members):
            del members["checksums.sha256"]
        with self.assertRaisesRegex(UnsafeArchive, "missing checksums"):
            verify_checksums(read_zip(rewrite(self.complete, self.dir / "nosum.zip", drop).read_bytes()))

    def test_traversal_absolute_and_symlink_members_rejected(self):
        for name in ("../evil.txt", "/etc/evil.txt", "a/../../evil.txt", "C:/evil.txt", "a\\..\\evil.txt", "a//b.txt"):
            buffer = io.BytesIO()
            with zipfile.ZipFile(buffer, "w") as archive:
                archive.writestr(zipfile.ZipInfo(name), b"x")
            with self.subTest(name=name), self.assertRaises(UnsafeArchive):
                read_zip(buffer.getvalue())
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as archive:
            info = zipfile.ZipInfo("link")
            info.external_attr = (0o120777 << 16)
            archive.writestr(info, b"/etc/passwd")
        with self.assertRaisesRegex(UnsafeArchive, "symlink"):
            read_zip(buffer.getvalue())
        # Traversal hidden inside an inner ZIP of an outer ZIP.
        inner = io.BytesIO()
        with zipfile.ZipFile(inner, "w") as archive:
            archive.writestr(zipfile.ZipInfo("../../escape.json"), b"{}")
        outer = self.dir / "outer_traversal.zip"
        with zipfile.ZipFile(outer, "w") as archive:
            archive.writestr("part_results.zip", inner.getvalue())
        with self.assertRaisesRegex(UnsafeArchive, "traversal"):
            bt.build([outer], self.out(), figures=False)

    def test_refuses_nonempty_output_directory(self):
        out = self.out()
        out.mkdir()
        (out / "keep.txt").write_text("x")
        with self.assertRaisesRegex(bt.AnalysisError, "non-empty"):
            bt.build([self.complete], out, figures=False)
        self.assertEqual([p.name for p in out.iterdir()], ["keep.txt"])

    # ------------------------------------------------------------ exact agreement with report.py

    def test_accuracy_and_bootstrap_exactly_equal_stored_metrics(self):
        members = self.members(self.complete)
        stored = json.loads(members["metrics.json"])
        out = self.out()
        bt.build([self.complete], out, figures=False)
        summary = json.loads((out / "synthetic" / "summary.json").read_text(encoding="utf-8"))
        self.assertEqual(summary["accuracy"], stored["accuracy"])
        self.assertEqual(summary["paired"], stored["paired"])
        for form in "ERC":
            self.assertEqual(summary["accuracy"][form]["wilson_95_interval"], stored["accuracy"][form]["wilson_95_interval"])
        for name in ("E-R", "E-C", "R-C"):
            self.assertEqual(summary["paired"][name]["bootstrap_95_interval"], stored["paired"][name]["bootstrap_95_interval"])
        self.assertEqual(summary["bootstrap_seed"], 101)
        self.assertEqual(summary["bootstrap_resamples"], 10000)
        self.assertTrue(all(state == "match" for state in summary["consistency"].values()), summary["consistency"])
        # The synthetic design must exercise non-zero, non-degenerate intervals.
        self.assertEqual({f: stored["accuracy"][f]["correct"] for f in "ERC"}, {"E": 4, "R": 3, "C": 3})
        self.assertNotEqual(stored["paired"]["E-R"]["bootstrap_95_interval"][0],
                            stored["paired"]["E-R"]["bootstrap_95_interval"][1])
        tables = (out / "synthetic" / "tables.md").read_text(encoding="utf-8")
        lo, hi = stored["accuracy"]["E"]["wilson_95_interval"]
        self.assertIn(f"| E | 4/6 | 66.7 | [{100*lo:.1f}, {100*hi:.1f}] |", tables)
        self.assertIn("| E−R | +16.7 |", tables)

    def test_numeric_endpoint_matches_secondary_report(self):
        from secondary_analysis.report_secondary import analyze as analyze_secondary
        secondary, _ = analyze_secondary(self.dir / "synthetic")
        out = self.out()
        bt.build([self.complete], out, figures=False)
        summary = json.loads((out / "synthetic" / "summary.json").read_text(encoding="utf-8"))
        for form in "ERC":
            self.assertEqual(summary["numeric"][form]["numeric_correct"], secondary["by_form"][form]["numeric_correct"])
            self.assertEqual(summary["numeric"][form]["strict_correct"], secondary["by_form"][form]["strict_correct"])
        self.assertTrue((out / "synthetic" / "tables" / "numeric.tex").is_file())

    # ------------------------------------------------------------ incomplete runs

    def test_incomplete_run_suppresses_headline_tables(self):
        out = self.out()
        bt.build([self.incomplete], out, figures=True)
        folder = out / "partial"
        text = (folder / "tables.md").read_text(encoding="utf-8")
        self.assertIn("Status: **INCOMPLETE**; 5/18", text)
        self.assertIn("headline accuracy, paired comparisons", text)
        names = sorted(p.stem for p in (folder / "tables").glob("*.md"))
        self.assertEqual(names, ["invalid", "resources"])
        self.assertFalse((folder / "figures").exists())
        summary = json.loads((folder / "summary.json").read_text(encoding="utf-8"))
        self.assertIsNone(summary["accuracy"])
        self.assertIsNone(summary["paired"])
        self.assertIsNone(summary["numeric"])
        self.assertEqual(summary["consistency"]["metrics.json status"], "match")
        with (out / "per_rendering.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 18)
        self.assertEqual(sum(r["status"] == "unresolved" for r in rows), 13)

    # ------------------------------------------------------------ outputs

    def test_outer_zip_with_inner_results_and_combined_csv(self):
        outer = self.dir / "FMT2_like_results_bundle.zip"
        with zipfile.ZipFile(outer, "w") as archive:
            archive.write(self.complete, "part-a_results.zip")
            archive.write(self.demo, "part-b_results.zip")
            archive.writestr("fmt2_status.json", "{}")
        out = self.out()
        result = bt.build([outer], out, figures=False)
        self.assertEqual(result["runs"], [("part-a", "COMPLETE"), ("part-b", "COMPLETE")])
        with (out / "per_rendering.csv").open(newline="", encoding="utf-8") as stream:
            rows = list(csv.DictReader(stream))
        self.assertEqual(len(rows), 18 + 6)
        self.assertEqual({r["run_slug"] for r in rows}, {"part-a", "part-b"})
        stored = {r["rendering_id"]: r["correct"] for r in csv.DictReader(io.StringIO(
            self.members(self.complete)["predictions.csv"].decode()))}
        self.assertEqual({r["rendering_id"]: r["correct"] for r in rows if r["run_slug"] == "part-a"}, stored)
        self.assertIn("non-results member", (out / "README.md").read_text(encoding="utf-8"))

    def test_latex_tables_use_booktabs_and_escape(self):
        out = self.out()
        bt.build([self.complete], out, figures=False)
        tex = (out / "synthetic" / "tables.tex").read_text(encoding="utf-8")
        for token in (r"\toprule", r"\midrule", r"\bottomrule", r"95\% CI", r"E$-$R", r"\label{tab:synthetic-paired}",
                      "DEMO --- NOT RESEARCH EVIDENCE", r"missing\_final"):
            self.assertIn(token, tex)
        for key in ("accuracy", "paired", "invalid", "resources", "numeric"):
            self.assertTrue((out / "synthetic" / "tables" / f"{key}.md").is_file())
            self.assertTrue((out / "synthetic" / "tables" / f"{key}.tex").is_file())
        self.assertEqual(bt.tex_escape("a_b & 5% #1 $x {y} ~^\\"),
                         r"a\_b \& 5\% \#1 \$x \{y\} \textasciitilde{}\textasciicircum{}\textbackslash{}")

    @unittest.skipUnless(HAS_MPL, "matplotlib not installed")
    def test_figures_written_as_pdf_and_png(self):
        out = self.out()
        self.assertEqual(quiet(bt.main, [str(self.complete), "--out", str(out)]), 0)
        names = sorted(p.name for p in (out / "synthetic" / "figures").iterdir())
        self.assertEqual(names, ["accuracy_by_form.pdf", "accuracy_by_form.png",
                                 "family_heatmap.pdf", "family_heatmap.png"])

    def test_missing_matplotlib_skips_figures_gracefully(self):
        from unittest import mock
        out = self.out()
        with mock.patch.dict(sys.modules, {"matplotlib": None, "paper_analysis.figures": None}):
            result = bt.build([self.complete], out, figures=True)
        self.assertIn("matplotlib not available: figures skipped.", result["notes"])
        self.assertFalse((out / "synthetic" / "figures").exists())
        self.assertTrue((out / "synthetic" / "tables" / "accuracy.tex").is_file())

    # ------------------------------------------------------------ regressions (GPT review 2026-10-15c)

    def test_nested_zip_expansion_respects_cumulative_budget(self):
        """Bug 1: inner archives each within limits must not jointly exceed the total bound."""
        from unittest import mock
        from paper_analysis import safezip
        outer = self.dir / "nested_bomb.zip"
        with zipfile.ZipFile(outer, "w", zipfile.ZIP_DEFLATED) as archive:
            for index in range(4):
                inner = io.BytesIO()
                with zipfile.ZipFile(inner, "w", zipfile.ZIP_DEFLATED) as nested:
                    for part in range(4):
                        nested.writestr(f"file{part}.bin", b"\x00" * 500)
                archive.writestr(f"run{index}_results.zip", inner.getvalue())
        with mock.patch.object(safezip, "MAX_MEMBER_BYTES", 1024), mock.patch.object(safezip, "MAX_TOTAL_BYTES", 2048):
            # The outer archive alone is within the bound; only the cumulative expansion is not.
            self.assertLessEqual(sum(map(len, read_zip(outer.read_bytes()).values())), 2048)
            with self.assertRaisesRegex(UnsafeArchive, "cumulative"):
                bt._expand_inputs([outer])
            out = self.out()
            self.assertEqual(quiet(bt.main, [str(outer), "--out", str(out), "--no-figures"]), 1)
            self.assertFalse(out.exists())

    def test_run_slugs_never_shadow_top_level_outputs(self):
        """Bug 3: a run named README.md / per_rendering.csv must not take the top-level file path."""
        for name in ("README.md_results.zip", "per_rendering.csv_results.zip", "readme.md_results.zip"):
            with self.subTest(name=name):
                source = self.dir / "slugs" / name
                source.parent.mkdir(exist_ok=True)
                source.write_bytes(self.complete.read_bytes())
                out = self.out()
                self.assertEqual(quiet(bt.main, [str(source), "--out", str(out), "--no-figures"]), 0)
                self.assertTrue((out / "README.md").is_file())
                self.assertTrue((out / "per_rendering.csv").is_file())
        used = set()
        self.assertEqual([bt._slug(s, used) for s in ("a_results.zip", "A_results.zip")], ["a", "A-2"])

    def test_corrupt_deflate_member_is_unsafe_archive(self):
        """Bug 4: an invalid DEFLATE stream raises UnsafeArchive, not zlib.error."""
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("file.txt", b"hello" * 100)
        blob = bytearray(buffer.getvalue())
        name_length = int.from_bytes(blob[26:28], "little")
        extra_length = int.from_bytes(blob[28:30], "little")
        blob[30 + name_length + extra_length] = 0xFF
        with self.assertRaisesRegex(UnsafeArchive, "cannot read 'file.txt'"):
            read_zip(bytes(blob))
        path = self.dir / "corrupt_deflate_results.zip"
        path.write_bytes(bytes(blob))
        out = self.out()
        self.assertEqual(quiet(bt.main, [str(path), "--out", str(out), "--no-figures"]), 1)
        self.assertFalse(out.exists())

    def test_malformed_predictions_and_metrics_rejected_with_exit_1(self):
        """Bug 5: malformed predictions.csv headers / metrics.json shape exit 1 without a traceback."""
        def bad_header(members):
            members["predictions.csv"] = b"wrong_header\nfoo\n"
            rechecksum(members)

        def bad_metrics(members):
            members["metrics.json"] = b"[]"
            rechecksum(members)
        for change, pattern in ((bad_header, "predictions.csv"), (bad_metrics, "malformed run content")):
            with self.subTest(change=change.__name__):
                bad = rewrite(self.complete, self.dir / f"{change.__name__}_results.zip", change)
                with self.assertRaisesRegex(bt.AnalysisError, pattern):
                    bt.build([bad], self.out(), figures=False)
                out = self.out()
                self.assertEqual(quiet(bt.main, [str(bad), "--out", str(out), "--no-figures"]), 1)
                self.assertFalse(out.exists())


if __name__ == "__main__":
    unittest.main()
