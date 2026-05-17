#!/usr/bin/env python3
"""Create a physical left-original / right-Chinese PDF after pdf2zh.

The script takes the source PDF and a translated mono PDF, then places page N
from the source on the left and page N from the translated PDF on the right.
It uses PDF page embedding rather than raster screenshots, preserving vector
content whenever the source PDFs allow it.
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence

try:
    import fitz  # PyMuPDF
except ImportError as exc:  # pragma: no cover - environment-dependent
    raise SystemExit(
        "PyMuPDF is required. Install it with: python -m pip install pymupdf"
    ) from exc


@dataclass(frozen=True)
class ImpositionOptions:
    margin: float
    gutter: float
    strict_page_count: bool
    page_numbers: list[int] | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Post-process pdf2zh output into one wide PDF page per source page: "
            "original page on the left, translated mono page on the right."
        )
    )
    parser.add_argument("--source", required=True, help="Original source PDF path.")
    parser.add_argument(
        "--translated",
        help="Translated mono PDF path. If omitted, --output-dir is searched for *-mono.pdf.",
    )
    parser.add_argument(
        "--output-dir",
        help="pdf2zh output directory. Used to locate *-mono.pdf when --translated is omitted.",
    )
    parser.add_argument(
        "--output",
        help="Output side-by-side PDF path. Defaults next to the translated PDF.",
    )
    parser.add_argument(
        "--pages",
        help="Optional 1-based page selection, e.g. 1 or 1-3 or 1,3,5-7.",
    )
    parser.add_argument(
        "--margin",
        type=float,
        default=18.0,
        help="Outer margin in PDF points. Default: 18.",
    )
    parser.add_argument(
        "--gutter",
        type=float,
        default=24.0,
        help="Space between the original and translated pages in PDF points. Default: 24.",
    )
    parser.add_argument(
        "--allow-page-count-mismatch",
        action="store_true",
        help="Use the overlapping page range when source and translation page counts differ.",
    )
    return parser.parse_args()


def parse_page_selection(selection: str | None, page_count: int) -> list[int] | None:
    if not selection:
        return None

    pages: set[int] = set()
    for part in selection.split(","):
        token = part.strip()
        if not token:
            continue
        if "-" in token:
            start_text, end_text = token.split("-", 1)
            start = int(start_text)
            end = int(end_text)
            if start > end:
                raise ValueError(f"Invalid descending page range: {token}")
            pages.update(range(start, end + 1))
        else:
            pages.add(int(token))

    ordered_pages = sorted(pages)
    invalid = [page for page in ordered_pages if page < 1 or page > page_count]
    if invalid:
        raise ValueError(
            f"Page selection contains pages outside 1-{page_count}: {invalid}"
        )
    return ordered_pages


def find_mono_pdf(output_dir: Path) -> Path:
    candidates = sorted(output_dir.glob("*-mono.pdf"))
    if not candidates:
        raise FileNotFoundError(f"No *-mono.pdf found in {output_dir}")
    if len(candidates) > 1:
        names = ", ".join(path.name for path in candidates)
        raise FileExistsError(
            f"Multiple *-mono.pdf files found in {output_dir}; pass --translated. Found: {names}"
        )
    return candidates[0]


def default_output_path(translated: Path) -> Path:
    stem = translated.stem
    if stem.endswith("-mono"):
        stem = stem[: -len("-mono")]
    return translated.with_name(f"{stem}-side-by-side.pdf")


def fit_rect(source_rect: fitz.Rect, cell_rect: fitz.Rect) -> fitz.Rect:
    scale = min(cell_rect.width / source_rect.width, cell_rect.height / source_rect.height)
    width = source_rect.width * scale
    height = source_rect.height * scale
    x0 = cell_rect.x0 + (cell_rect.width - width) / 2
    y0 = cell_rect.y0 + (cell_rect.height - height) / 2
    return fitz.Rect(x0, y0, x0 + width, y0 + height)


def validate_inputs(source: Path, translated: Path) -> None:
    if not source.exists():
        raise FileNotFoundError(f"Source PDF does not exist: {source}")
    if not translated.exists():
        raise FileNotFoundError(f"Translated PDF does not exist: {translated}")
    if source.resolve() == translated.resolve():
        raise ValueError("Source and translated PDFs must be different files.")


def selected_page_numbers(
    source_pages: int,
    translated_pages: int,
    selection: str | None,
    strict_page_count: bool,
) -> list[int]:
    if source_pages != translated_pages and strict_page_count:
        raise ValueError(
            "Source and translated PDFs must have the same page count. "
            f"source={source_pages}, translated={translated_pages}. "
            "Pass --allow-page-count-mismatch to impose the overlapping range."
        )

    max_page = min(source_pages, translated_pages)
    pages = parse_page_selection(selection, max_page)
    return pages if pages is not None else list(range(1, max_page + 1))


def impose_side_by_side(
    source: Path,
    translated: Path,
    output: Path,
    options: ImpositionOptions,
) -> int:
    validate_inputs(source, translated)
    output.parent.mkdir(parents=True, exist_ok=True)

    with fitz.open(source) as source_doc, fitz.open(translated) as translated_doc:
        pages = options.page_numbers or selected_page_numbers(
            source_doc.page_count,
            translated_doc.page_count,
            None,
            options.strict_page_count,
        )
        result = fitz.open()
        try:
            for page_number in pages:
                index = page_number - 1
                source_page = source_doc[index]
                translated_page = translated_doc[index]
                source_rect = source_page.rect
                translated_rect = translated_page.rect

                cell_width = max(source_rect.width, translated_rect.width)
                cell_height = max(source_rect.height, translated_rect.height)
                page_width = options.margin * 2 + cell_width * 2 + options.gutter
                page_height = options.margin * 2 + cell_height
                out_page = result.new_page(width=page_width, height=page_height)

                left_cell = fitz.Rect(
                    options.margin,
                    options.margin,
                    options.margin + cell_width,
                    options.margin + cell_height,
                )
                right_cell = fitz.Rect(
                    options.margin + cell_width + options.gutter,
                    options.margin,
                    options.margin + cell_width * 2 + options.gutter,
                    options.margin + cell_height,
                )

                out_page.show_pdf_page(fit_rect(source_rect, left_cell), source_doc, index)
                out_page.show_pdf_page(
                    fit_rect(translated_rect, right_cell), translated_doc, index
                )

            result.set_metadata(
                {
                    "title": f"{source.stem} side-by-side bilingual PDF",
                    "subject": "Original pages on the left, translated pages on the right",
                    "creator": "paper-bilingual-translator impose_side_by_side_pdf.py",
                }
            )
            result.save(output, garbage=4, deflate=True)
        finally:
            result.close()

    return len(pages)


def resolve_paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    source = Path(args.source).expanduser().resolve()
    if args.translated:
        translated = Path(args.translated).expanduser().resolve()
    elif args.output_dir:
        translated = find_mono_pdf(Path(args.output_dir).expanduser().resolve()).resolve()
    else:
        raise ValueError("Pass either --translated or --output-dir.")

    output = (
        Path(args.output).expanduser().resolve()
        if args.output
        else default_output_path(translated).resolve()
    )
    return source, translated, output


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args() if argv is None else parse_args_from(argv)
    try:
        source, translated, output = resolve_paths(args)
        with fitz.open(source) as source_doc, fitz.open(translated) as translated_doc:
            pages = selected_page_numbers(
                source_doc.page_count,
                translated_doc.page_count,
                args.pages,
                not args.allow_page_count_mismatch,
            )
        count = impose_side_by_side(
            source,
            translated,
            output,
            ImpositionOptions(
                margin=args.margin,
                gutter=args.gutter,
                strict_page_count=not args.allow_page_count_mismatch,
                page_numbers=pages,
            ),
        )
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {count} side-by-side pages: {output}")
    return 0


def parse_args_from(argv: Sequence[str]) -> argparse.Namespace:
    original_argv = sys.argv
    try:
        sys.argv = [original_argv[0], *argv]
        return parse_args()
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
