# skill-paper-bilingual-translator-agent-llm

这是一个面向 Codex / AI Agent 的论文 PDF 双语翻译技能项目。它把英文科研论文 PDF 翻译成中文阅读版，并通过 PDFMathTranslate / `pdf2zh` 尽量保留原论文的版式、公式、图表、表格、题注和参考文献结构。

项目的目标不是做论文问答或文献综述，而是提供一套可复用的 Agent 工作流：先做单页冒烟测试，再执行全文翻译，最后对生成的 PDF 做基础质量检查并报告风险页。

## 功能特点

- 支持本地论文 PDF、arXiv PDF 链接和目录批量翻译。
- 默认生成中文翻译 PDF 与中英双语对照 PDF。
- 强制先跑单页冒烟测试，降低全文翻译后才发现排版问题的风险。
- 提供 `qa_pdf2zh_output.py`，用于检查输出文件是否可打开、页数是否匹配、是否包含中文文本，以及哪些页面可能仍有较多英文残留。
- 记录 Windows 环境下 `pdf2zh` 安装、路径、依赖下载和首次运行的常见注意事项。

## 目录结构

```text
.
├── README.md
├── skills/
│   └── paper-bilingual-translator/
│       ├── SKILL.md
│       ├── README.md
│       ├── examples/
│       │   └── usage_examples.md
│       └── scripts/
│           └── qa_pdf2zh_output.py
├── outputs/                 # 本地翻译输出，默认不提交
└── tmp_pdf2zh_download/      # 临时下载缓存，默认不提交
```

## 安装与依赖

建议使用 Python 3.10 到 3.12。Windows 上优先使用 Python 3.12：

```powershell
py -3.12 -m pip install --user --progress-bar off --only-binary=:all: pdf2zh==1.9.11
py -3.12 -m pip install --user pymupdf
```

检查 `pdf2zh` 是否可用：

```powershell
pdf2zh --help
pdf2zh --version
```

如果 `pdf2zh.exe` 不在 `PATH` 中，可检查类似路径：

```text
C:\Users\<user>\AppData\Roaming\Python\Python312\Scripts\pdf2zh.exe
```

## 基本用法

先对第 1 页做冒烟测试：

```powershell
pdf2zh input.pdf -li en -lo zh -o output_smoke -p 1 -t 1
```

确认首页、作者、摘要、公式和图表版式基本可接受后，再运行全文翻译：

```powershell
pdf2zh input.pdf -li en -lo zh -o output_full -t 1
```

翻译完成后运行 QA：

```powershell
python skills/paper-bilingual-translator/scripts/qa_pdf2zh_output.py --source input.pdf --output-dir output_full --report output_full/qa_report.md
```

常见输出文件包括：

- `*-mono.pdf`：中文翻译版。
- `*-dual.pdf`：双语对照版。通常是原文页和译文页交错排列；如需“左英文、右中文”的阅读效果，请在 PDF 阅读器中开启双页或面对页视图。

## Codex Skill 使用方式

技能主体位于：

```text
skills/paper-bilingual-translator/
```

如需安装到 Codex 本地技能目录，可将该目录复制到：

```text
%USERPROFILE%\.codex\skills\paper-bilingual-translator\
```

之后，当用户提出“翻译英文论文 PDF”“生成中英双语对照 PDF”“保留公式和图表排版”等请求时，Agent 应按 `SKILL.md` 中的工作流执行。

## 质量检查原则

每次交付前至少确认：

- `mono.pdf` 和 `dual.pdf` 都已生成且可打开。
- `mono.pdf` 页数与源 PDF 一致。
- `dual.pdf` 页数通常约为源 PDF 的两倍。
- 翻译页包含中文文本。
- 标题页、摘要页、首个正文页、图表题注、公式和参考文献经过人工抽查或被明确标记为需要人工复核。

标题页和摘要页属于高风险区域，常见问题包括英文残留、侧边 arXiv 标记位置异常、两栏文本错位或作者信息排版不稳。遇到问题时，应先用 `-p` 参数隔离单页重试，再考虑 `--babeldoc`、`--compatible` 或 `--skip-subset-fonts`。

## 不适用场景

本项目不用于：

- 普通文本翻译。
- Word 文档翻译。
- 网页翻译。
- 论文问答、摘要生成或文献综述写作。
- Zotero、Obsidian、Streamlit 等集成开发。

如果用户的主要目标是理解论文内容，应改用论文阅读、文献调研或中英对照全文解读工作流。
