# paper-bilingual-translator

`paper-bilingual-translator` is a Codex Skill for guiding Codex or another AI agent to translate English academic paper PDFs into Chinese reading PDFs with PDFMathTranslate / `pdf2zh`.

This README is written for language models and agents. Treat `SKILL.md` as the authoritative instruction file for the actual workflow, command sequence, QA requirements, and failure handling.

## Scope

Use this Skill only when the user wants to:

- translate an English academic paper PDF into Chinese;
- generate `pdf2zh` `*-mono.pdf` and `*-dual.pdf` outputs;
- optionally create a physical `*-side-by-side.pdf` where each wide page places the original page on the left and the Chinese translation on the right;
- preserve the source paper layout, formulas, figures, tables, captions, and references as much as possible;
- process a local PDF, an arXiv PDF URL, or a directory of paper PDFs;
- deliver real PDF files plus a concise QA summary.

Do not use this Skill for paper Q&A, abstract writing, literature reviews, plain text translation, Word document translation, web page translation, or Zotero / Obsidian / Streamlit integration work.

## Upstream Tool

This Skill wraps the workflow around PDFMathTranslate / `pdf2zh`; it does not implement the PDF translation engine itself.

Upstream references:

- PDFMathTranslate GitHub: <https://github.com/PDFMathTranslate/PDFMathTranslate>
- pdf2zh PyPI: <https://pypi.org/project/pdf2zh/>

When tool behavior, CLI options, or installation details differ from this repository, prefer the upstream documentation unless `SKILL.md` records a local workflow decision.

## Location

Repository copy:

```text
skills/paper-bilingual-translator/
```

Typical local Codex skill copy:

```text
C:\Users\liu'jia'yao\.codex\skills\paper-bilingual-translator\
```

When updating the Skill, keep the repository copy and any installed local Codex copy synchronized when needed.

## Expected Outputs

`pdf2zh` normally generates:

- `*-mono.pdf`: Chinese translation PDF.
- `*-dual.pdf`: bilingual comparison PDF.
- `*-side-by-side.pdf`: optional post-processed PDF created by this Skill's imposition helper.

The `dual.pdf` output usually interleaves original and translated pages. To get the common "original on the left, Chinese on the right" reading experience, open `dual.pdf` in a PDF reader and enable two-page or facing-pages view.

When the user wants each physical PDF page to contain both versions side by side, run:

```bash
python scripts/impose_side_by_side_pdf.py --source input.pdf --output-dir output_full --output output_full/input-side-by-side.pdf
```

## Standard Agent Workflow

For a new paper, first run a one-page smoke test:

```bash
pdf2zh input.pdf -li en -lo zh -o output_smoke -p 1 -t 1
```

If the smoke test is acceptable, run the full translation:

```bash
pdf2zh input.pdf -li en -lo zh -o output_full -t 1
```

Then run the bundled QA helper:

```bash
python scripts/qa_pdf2zh_output.py --source input.pdf --output-dir output_full --report output_full/qa_report.md
```

If requested, create the side-by-side imposition PDF before delivery:

```bash
python scripts/impose_side_by_side_pdf.py --source input.pdf --output-dir output_full --output output_full/input-side-by-side.pdf
```

Report the generated files, page counts, side-by-side output path if created, QA findings, and any pages that need manual review.

## Installation Notes

On Windows, prefer Python 3.12 for the tested `pdf2zh` path:

```bash
py -3.12 -m pip install --user --progress-bar off --only-binary=:all: pdf2zh==1.9.11
```

Observed local notes:

- `pdf2zh` has heavy dependencies and installation may take several minutes.
- A plain `pip install pdf2zh` may appear stuck during dependency resolution.
- The first translation may download the doclayout ONNX model and Chinese font assets.
- `pdf2zh.exe` may be installed in the Python user-level `Scripts` directory and may not be on `PATH`.

## Known Output Risks

Always inspect title and abstract pages. In local SpatialBench testing, the first translated page showed partial English residue in the abstract area and unstable side-marker layout. This is a common PDF layout risk and should be reported clearly rather than hidden.

Useful retry patterns:

```bash
pdf2zh input.pdf -li en -lo zh -o retry_page1 -p 1 --ignore-cache -t 1
pdf2zh input.pdf -li en -lo zh -o retry_babeldoc --babeldoc -t 1
pdf2zh input.pdf -li en -lo zh -o retry_compatible --compatible -t 1
pdf2zh input.pdf -li en -lo zh -o retry_fonts --skip-subset-fonts -t 1
```

## Files

```text
paper-bilingual-translator/
├── SKILL.md
├── README.md
├── examples/
│   └── usage_examples.md
└── scripts/
    ├── impose_side_by_side_pdf.py
    └── qa_pdf2zh_output.py
```
