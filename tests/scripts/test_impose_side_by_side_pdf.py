from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fitz


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPT = (
    REPO_ROOT
    / "skills"
    / "paper-bilingual-translator"
    / "scripts"
    / "impose_side_by_side_pdf.py"
)


def write_sample_pdf(path: Path, labels: list[str], width: float = 200, height: float = 300) -> None:
    doc = fitz.open()
    try:
        for label in labels:
            page = doc.new_page(width=width, height=height)
            page.insert_text((36, 72), label, fontsize=18)
        doc.save(path)
    finally:
        doc.close()


class SideBySideImpositionTest(unittest.TestCase):
    def test_creates_one_wide_page_per_source_page(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.pdf"
            translated = tmp_path / "paper-mono.pdf"
            output = tmp_path / "paper-side-by-side.pdf"
            write_sample_pdf(source, ["source page 1", "source page 2"])
            write_sample_pdf(translated, ["translated page 1", "translated page 2"])

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source",
                    str(source),
                    "--translated",
                    str(translated),
                    "--output",
                    str(output),
                    "--margin",
                    "10",
                    "--gutter",
                    "20",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 0, completed.stderr)
            with fitz.open(output) as doc:
                self.assertEqual(doc.page_count, 2)
                self.assertAlmostEqual(doc[0].rect.width, 440)
                self.assertAlmostEqual(doc[0].rect.height, 320)
                text = doc[0].get_text("text")
                self.assertIn("source page 1", text)
                self.assertIn("translated page 1", text)

    def test_rejects_mismatched_page_counts_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source = tmp_path / "source.pdf"
            translated = tmp_path / "paper-mono.pdf"
            output = tmp_path / "paper-side-by-side.pdf"
            write_sample_pdf(source, ["source page 1", "source page 2"])
            write_sample_pdf(translated, ["translated page 1"])

            completed = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "--source",
                    str(source),
                    "--translated",
                    str(translated),
                    "--output",
                    str(output),
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(completed.returncode, 2)
            self.assertIn("same page count", completed.stderr)
            self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
