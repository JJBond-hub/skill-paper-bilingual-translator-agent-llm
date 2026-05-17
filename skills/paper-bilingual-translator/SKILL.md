---
name: paper-bilingual-translator
description: Guide Codex or an AI agent to translate English academic paper PDFs into Chinese bilingual reading PDFs using PDFMathTranslate / pdf2zh. Use when the user wants to translate scholarly PDFs, arXiv papers, batches of papers, or generate Chinese-English layout-preserving paper PDFs with mono and dual outputs, while checking formulas, figures, tables, captions, references, title pages, abstracts, and likely untranslated or mis-laid-out pages.
---

# paper-bilingual-translator

## Purpose

Use this Skill only for translating English academic paper PDFs into Chinese PDF reading materials with PDFMathTranslate / `pdf2zh`.

The expected deliverables are real PDF files, usually:

- `*-mono.pdf`: Chinese translation PDF
- `*-dual.pdf`: bilingual comparison PDF

`pdf2zh` is the command-line interface of the PDFMathTranslate toolchain. Do not ask the user to switch from `pdf2zh` to PDFMathTranslate as if they were separate tools.

## When To Use

Use this Skill when the user asks for:

- translating an English academic paper PDF
- generating a Chinese-English bilingual PDF
- preserving the paper layout, formulas, figures, tables, captions, and references
- translating an arXiv PDF
- batch-translating papers
- creating a paper reading file similar to left-original / right-Chinese comparison

Typical Chinese requests include:

- "帮我翻译这篇论文"
- "生成双语对照 PDF"
- "像论文原文一样保留排版翻译"
- "把 arXiv 论文翻译成中文"
- "给我生成中英文对照版本"
- "保留公式和图表翻译 PDF"

## When Not To Use

Do not use this Skill for:

- plain text translation
- Word document translation
- web page translation
- abstract generation
- paper reading Q&A
- literature review writing
- plugin entrypoint development
- Obsidian, Zotero, or Streamlit integration

If the user mainly wants to understand a paper, recommend a paper-reading or literature-survey workflow instead.

## Output Semantics

Explain the comparison layout clearly:

- `dual.pdf` normally interleaves original and translated pages. For an 18-page source PDF, a normal `dual.pdf` may have 36 pages.
- To get the visual effect of "left side original, right side Chinese", open `dual.pdf` in a PDF reader and enable two-page / facing-pages view.
- If the user requires one physical wide page with English on the left half and Chinese on the right half, treat that as a post-processing imposition task after `pdf2zh`; it is not the default `pdf2zh` output.

## Environment Setup

Prefer Python 3.10-3.12. Avoid Python 3.13+ unless the installed `pdf2zh` version explicitly supports it.

Check availability:

```bash
pdf2zh --help
pdf2zh --version
```

On Windows, `pdf2zh.exe` may be installed under the Python user Scripts directory and not be on `PATH`, for example:

```text
C:\Users\<user>\AppData\Roaming\Python\Python312\Scripts\pdf2zh.exe
```

If `pdf2zh` is missing, install with Python 3.12 when available:

```bash
py -3.12 -m pip install --user --progress-bar off --only-binary=:all: pdf2zh==1.9.11
```

Observed installation notes:

- `pdf2zh` has many large dependencies, including layout, OCR, PDF, image, and UI packages.
- A normal `pip install pdf2zh` may appear to hang for minutes during dependency resolution or large wheel download.
- `--only-binary=:all:` helps avoid source builds and made installation much more predictable in testing.
- First translation may download the doclayout ONNX model and Source Han Serif Chinese font; this can add noticeable time.

## Standard Workflow

1. Confirm the input is a local PDF path, arXiv PDF URL, or directory of PDFs.
2. Check `pdf2zh --help` and `pdf2zh --version`.
3. For a new paper, run a one-page smoke test before translating the full file:

```bash
pdf2zh input.pdf -li en -lo zh -o output_smoke -p 1 -t 1
```

4. Inspect the smoke-test output, especially the title page, authors, abstract, and first section.
5. If the smoke test is acceptable, run the full translation:

```bash
pdf2zh input.pdf -li en -lo zh -o output_full -t 1
```

6. Run QA on the output:

```bash
python scripts/qa_pdf2zh_output.py --source input.pdf --output-dir output_full --report output_full/qa_report.md
```

7. Report the output directory, generated files, page counts, and known risks.

## Command Patterns

Single local paper:

```bash
pdf2zh paper.pdf -li en -lo zh -o translated -t 1
```

arXiv PDF:

```bash
pdf2zh https://arxiv.org/pdf/2501.00001.pdf -li en -lo zh -o translated -t 1
```

Batch directory:

```bash
pdf2zh --dir papers -li en -lo zh -o translated -t 1
```

Specific pages for debugging:

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_page1 -p 1 -t 1
pdf2zh paper.pdf -li en -lo zh -o translated_pages1_3 -p 1-3 -t 1
```

Compatibility retry:

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_compatible --compatible -t 1
```

Experimental backend retry:

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_babeldoc --babeldoc -t 1
```

Font-subset compatibility retry:

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_no_subset --skip-subset-fonts -t 1
```

Ignore cache when rechecking a failed page:

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_retry -p 1 --ignore-cache -t 1
```

## QA Requirements

Always verify the generated PDF files before delivery.

Minimum checks:

- `mono.pdf` exists and can be opened.
- `dual.pdf` exists and can be opened.
- `mono.pdf` page count equals the source page count.
- `dual.pdf` page count is usually twice the source page count.
- At least the first pages of `mono.pdf` contain Chinese text.
- For `dual.pdf`, translated pages contain Chinese; original pages may not.
- Title page, abstract, figure captions, table captions, references, and the first body page are manually inspected or flagged for manual inspection.

Use the bundled QA helper when available:

```bash
python scripts/qa_pdf2zh_output.py --source input.pdf --output-dir translated --report translated/qa_report.md
```

Treat QA warnings as review cues, not automatic failure. Many figure-only or reference pages may naturally contain little Chinese text.

## Known Risk: Title And Abstract Pages

Title pages and abstract pages are high-risk because academic PDFs often combine:

- centered title and author blocks
- two-column text
- side arXiv stamps
- italic abstract text
- URLs and citation numbers
- tightly packed first-section text

In testing with the SpatialBench paper, the first translated page showed partial problems: some abstract text remained in English and a side stamp / metadata region was laid out awkwardly. When this happens, do not claim the translation is flawless. Flag the page and suggest one or more targeted retries.

Recommended debugging sequence:

1. Re-run only the affected page with `-p`.
2. Try `--babeldoc` for the affected page or full paper.
3. Try `--compatible` if page objects or fonts look broken.
4. Try `--skip-subset-fonts` if Chinese fonts display poorly.
5. Try `--ignore-cache` when a retry seems to reuse bad cached content.
6. If the first page remains poor, deliver the PDF with a clear note and optionally offer manual correction or separate title/abstract translation outside the PDF.

## Failure Handling

If installation is slow:

- Use Python 3.12 and `--only-binary=:all:`.
- Disable the progress bar to reduce noisy output.
- Allow several minutes for large wheels.
- Check whether the package was partially installed before retrying.

If the first run is slow:

- Expect one-time downloads of layout model and Chinese font assets.
- Record this as first-run setup time, not normal per-paper runtime.

If translation service fails:

- Retry a small page range first.
- Reduce `-t` to 1.
- Use another service only if credentials or environment are available.
- Avoid sending private or unpublished papers to online translation services without user confirmation.

If layout is poor:

- Compare `mono.pdf` and `dual.pdf`.
- Try `--compatible`, `--babeldoc`, or `--skip-subset-fonts`.
- If only a few pages are bad, isolate them with `-p` before rerunning the whole paper.

## Delivery Format

When finished, report:

- input file or directory
- output directory
- generated `mono` and `dual` PDF filenames
- page counts
- whether the dual PDF should be viewed in two-page mode
- QA result summary
- any pages with likely untranslated text, layout damage, or manual-review risk

Do not paste the whole translated paper into chat. The deliverable is the generated PDF plus a concise QA note.
