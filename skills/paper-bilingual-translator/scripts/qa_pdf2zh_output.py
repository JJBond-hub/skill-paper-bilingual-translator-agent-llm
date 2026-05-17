#!/usr/bin/env python3
"""QA helper for PDFMathTranslate / pdf2zh outputs.

The script checks generated mono/dual PDFs for openability, page counts, CJK
coverage, and pages that may still contain substantial untranslated English.
It is intentionally heuristic: warnings identify pages to inspect manually.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(
        "PyMuPDF is required. Install it with: python -m pip install pymupdf"
    ) from exc


CJK_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
LATIN_WORD_RE = re.compile(r"[A-Za-z][A-Za-z\-]{2,}")


@dataclass
class PageSignal:
    page_number: int
    chars: int
    cjk_chars: int
    latin_words: int

    @property
    def has_cjk(self) -> bool:
        return self.cjk_chars > 0

    @property
    def cjk_ratio(self) -> float:
        return self.cjk_chars / self.chars if self.chars else 0.0

    @property
    def suspicious_english_heavy(self) -> bool:
        return self.latin_words >= 80 and (not self.has_cjk or self.cjk_ratio < 0.25)


@dataclass
class PdfReport:
    label: str
    path: Path | None
    expected_pages: int | None
    openable: bool
    page_count: int | None
    page_count_ok: bool | None
    signals: list[PageSignal]
    error: str | None = None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check pdf2zh mono/dual outputs for basic translation QA."
    )
    parser.add_argument("--source", required=True, help="Original source PDF path.")
    parser.add_argument(
        "--output-dir", required=True, help="Directory containing pdf2zh output PDFs."
    )
    parser.add_argument(
        "--report", help="Optional markdown report path, e.g. output/qa_report.md."
    )
    parser.add_argument(
        "--sample-pages",
        type=int,
        default=6,
        help="Number of leading pages to summarize in detail. Default: 6.",
    )
    parser.add_argument(
        "--scan-all",
        action="store_true",
        help="Scan all pages for CJK and English-heavy signals. Default scans all too for counts; this flag is kept for explicitness.",
    )
    return parser.parse_args()


def count_pages(pdf_path: Path) -> int:
    with fitz.open(pdf_path) as doc:
        return doc.page_count


def find_output_pdf(output_dir: Path, suffix: str) -> Path | None:
    candidates = sorted(output_dir.glob(f"*{suffix}.pdf"))
    if candidates:
        return candidates[0]
    return None


def analyze_pdf(label: str, path: Path | None, expected_pages: int | None) -> PdfReport:
    if path is None:
        return PdfReport(
            label=label,
            path=None,
            expected_pages=expected_pages,
            openable=False,
            page_count=None,
            page_count_ok=False,
            signals=[],
            error=f"Missing *-{label}.pdf output",
        )

    try:
        doc = fitz.open(path)
    except Exception as exc:  # pragma: no cover - corrupt file path
        return PdfReport(
            label=label,
            path=path,
            expected_pages=expected_pages,
            openable=False,
            page_count=None,
            page_count_ok=False,
            signals=[],
            error=str(exc),
        )

    signals: list[PageSignal] = []
    try:
        for index in range(doc.page_count):
            text = doc[index].get_text("text")
            chars = len(text.strip())
            cjk_chars = len(CJK_RE.findall(text))
            latin_words = len(LATIN_WORD_RE.findall(text))
            signals.append(
                PageSignal(
                    page_number=index + 1,
                    chars=chars,
                    cjk_chars=cjk_chars,
                    latin_words=latin_words,
                )
            )
        page_count = doc.page_count
    finally:
        doc.close()

    page_count_ok = expected_pages is None or page_count == expected_pages
    return PdfReport(
        label=label,
        path=path,
        expected_pages=expected_pages,
        openable=True,
        page_count=page_count,
        page_count_ok=page_count_ok,
        signals=signals,
    )


def summarize_signals(
    label: str, signals: Iterable[PageSignal]
) -> tuple[int, list[int], list[int], list[int]]:
    signal_list = list(signals)
    cjk_pages = [s.page_number for s in signal_list if s.has_cjk]
    no_cjk_pages = [s.page_number for s in signal_list if not s.has_cjk]
    if label == "dual":
        english_heavy = [
            s.page_number
            for s in signal_list
            if s.has_cjk and s.suspicious_english_heavy
        ]
    else:
        english_heavy = [
            s.page_number for s in signal_list if s.suspicious_english_heavy
        ]
    return len(cjk_pages), cjk_pages, no_cjk_pages, english_heavy


def format_report(source: Path, output_dir: Path, source_pages: int, reports: list[PdfReport], sample_pages: int) -> str:
    lines: list[str] = []
    lines.append("# pdf2zh QA Report")
    lines.append("")
    lines.append(f"- Source: `{source}`")
    lines.append(f"- Output directory: `{output_dir}`")
    lines.append(f"- Source pages: {source_pages}")
    lines.append("")

    for report in reports:
        lines.append(f"## {report.label}.pdf")
        if report.path is None:
            lines.append(f"- Status: missing ({report.error})")
            lines.append("")
            continue

        lines.append(f"- File: `{report.path.name}`")
        lines.append(f"- Openable: {report.openable}")
        lines.append(f"- Pages: {report.page_count}")
        if report.expected_pages is not None:
            lines.append(f"- Expected pages: {report.expected_pages}")
            lines.append(f"- Page count OK: {report.page_count_ok}")

        cjk_count, cjk_pages, no_cjk_pages, english_heavy = summarize_signals(
            report.label, report.signals
        )
        lines.append(f"- Pages with CJK text: {cjk_count}")
        lines.append(f"- Pages without CJK text: {no_cjk_pages or 'none'}")
        lines.append(
            f"- Likely untranslated or English-heavy translated pages: {english_heavy or 'none'}"
        )
        lines.append("- Leading-page sample:")
        for signal in report.signals[:sample_pages]:
            lines.append(
                "  - "
                f"p{signal.page_number}: "
                f"cjk={signal.cjk_chars}, "
                f"latin_words={signal.latin_words}, "
                f"cjk_ratio={signal.cjk_ratio:.3f}, "
                f"english_heavy={signal.suspicious_english_heavy}"
            )
        if report.label == "dual":
            lines.append(
                "- Note: dual PDFs often interleave original and translated pages; no-CJK original pages are expected."
            )
        lines.append("")

    lines.append("## Manual Review Notes")
    lines.append("- Always inspect title, author, abstract, first body page, captions, tables, formulas, and references.")
    lines.append("- Title/abstract pages are high-risk for partial English residue or awkward layout.")
    lines.append("- Treat English-heavy warnings as review targets, not automatic failures.")
    lines.append("")
    return "\n".join(lines)


def print_console_summary(markdown: str) -> None:
    print(markdown)


def main() -> int:
    args = parse_args()
    source = Path(args.source).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()

    if not source.exists():
        print(f"Source PDF does not exist: {source}", file=sys.stderr)
        return 2
    if not output_dir.exists():
        print(f"Output directory does not exist: {output_dir}", file=sys.stderr)
        return 2

    source_pages = count_pages(source)
    mono = find_output_pdf(output_dir, "-mono")
    dual = find_output_pdf(output_dir, "-dual")
    reports = [
        analyze_pdf("mono", mono, source_pages),
        analyze_pdf("dual", dual, source_pages * 2),
    ]

    markdown = format_report(source, output_dir, source_pages, reports, args.sample_pages)
    print_console_summary(markdown)

    if args.report:
        report_path = Path(args.report).expanduser()
        if not report_path.is_absolute():
            report_path = Path.cwd() / report_path
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(markdown, encoding="utf-8")

    has_missing_or_bad = any(not r.openable or r.page_count_ok is False for r in reports)
    return 1 if has_missing_or_bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
