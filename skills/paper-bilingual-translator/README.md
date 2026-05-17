# paper-bilingual-translator

`paper-bilingual-translator` 是一个 Codex Skill，用于指导 Codex 或其他 AI Agent 使用 PDFMathTranslate / `pdf2zh` 将英文科研论文 PDF 翻译成中文阅读 PDF。

它的范围刻意保持很窄：不做论文问答、文献综述写作、Zotero 集成、Obsidian 集成、Streamlit 界面开发，也不做逐段手工翻译。

## 安装位置

项目内副本：

```text
skills/paper-bilingual-translator/
```

Codex 本地技能副本：

```text
C:\Users\liu'jia'yao\.codex\skills\paper-bilingual-translator\
```

更新技能时，建议保持两个位置的内容同步。

## 输出文件

`pdf2zh` 通常会生成：

- `*-mono.pdf`：中文翻译 PDF。
- `*-dual.pdf`：双语对照 PDF。

如果想获得常见的“左边原文、右边中文”阅读体验，请在 PDF 阅读器中打开 `dual.pdf` 并启用双页或面对页视图。`dual.pdf` 通常是原文页和译文页交错排列，而不是每一页都做成宽幅左右分栏。

## 推荐工作流

先运行单页冒烟测试：

```bash
pdf2zh input.pdf -li en -lo zh -o output_smoke -p 1 -t 1
```

检查通过后再运行全文翻译：

```bash
pdf2zh input.pdf -li en -lo zh -o output_full -t 1
```

最后运行 QA：

```bash
python scripts/qa_pdf2zh_output.py --source input.pdf --output-dir output_full --report output_full/qa_report.md
```

## 安装说明

Windows 上建议优先使用 Python 3.12：

```bash
py -3.12 -m pip install --user --progress-bar off --only-binary=:all: pdf2zh==1.9.11
```

本地测试中的常见注意事项：

- `pdf2zh` 依赖较重，安装可能需要几分钟。
- 直接执行 `pip install pdf2zh` 时，依赖解析阶段可能看起来像是卡住了。
- 首次翻译可能会下载 doclayout ONNX 模型和中文字体。
- `pdf2zh.exe` 可能安装在 Python 用户级 `Scripts` 目录下，未必自动进入 `PATH`。

## 已知输出风险

务必检查标题页和摘要页。以 SpatialBench 测试论文为例，第一页译文曾出现摘要区域英文残留、侧边标记排版不稳等问题。这是一类常见 PDF 版式风险，不代表需要立刻放弃 `pdf2zh`。

可尝试的重试命令：

```bash
pdf2zh input.pdf -li en -lo zh -o retry_page1 -p 1 --ignore-cache -t 1
pdf2zh input.pdf -li en -lo zh -o retry_babeldoc --babeldoc -t 1
pdf2zh input.pdf -li en -lo zh -o retry_compatible --compatible -t 1
pdf2zh input.pdf -li en -lo zh -o retry_fonts --skip-subset-fonts -t 1
```

## 文件结构

```text
paper-bilingual-translator/
├── SKILL.md
├── README.md
├── examples/
│   └── usage_examples.md
└── scripts/
    └── qa_pdf2zh_output.py
```
