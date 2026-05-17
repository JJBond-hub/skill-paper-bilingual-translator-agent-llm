# skill-paper-bilingual-translator-agent-llm

这是一个面向 Codex / AI Agent 的论文 PDF 双语翻译 Skill 包装项目。

本项目的重点不是重新实现 PDF 翻译引擎，而是把“使用 PDFMathTranslate / `pdf2zh` 翻译英文科研论文 PDF，并交付中文阅读版和中英双语对照版”的流程整理成可复用的 Codex Skill。具体的使用细则、命令模板、QA 要求和风险处理流程，已经放在：

```text
skills/paper-bilingual-translator/SKILL.md
```

## 项目来源说明

`PDFMathTranslate` / `pdf2zh` 是独立的开源项目，本仓库不是它的原始仓库，也不是其官方分发版本。

上游项目地址：

- PDFMathTranslate GitHub: <https://github.com/PDFMathTranslate/PDFMathTranslate>
- pdf2zh PyPI: <https://pypi.org/project/pdf2zh/>

本仓库只是对上游工具的使用方式做了一层 Agent 工作流包装，主要补充：

- Codex Skill 触发说明。
- 适合论文 PDF 翻译的标准操作流程。
- 单页冒烟测试、全文翻译和交付前 QA 的步骤。
- Windows 环境下安装、路径和首次运行的注意事项。
- 对标题页、摘要页、公式、图表、题注和参考文献等高风险区域的检查建议。

如果需要了解、安装或贡献 PDFMathTranslate / `pdf2zh` 本身，请以其上游项目文档为准。

## 仓库结构

```text
.
├── README.md
└── skills/
    └── paper-bilingual-translator/
        ├── SKILL.md
        ├── README.md
        ├── examples/
        │   └── usage_examples.md
        └── scripts/
            └── qa_pdf2zh_output.py
```

## Skill 内容

核心 Skill 位于：

```text
skills/paper-bilingual-translator/
```

其中：

- `SKILL.md`：Codex / AI Agent 应遵循的完整工作流。
- `README.md`：该 Skill 的简要说明。
- `examples/usage_examples.md`：典型使用请求和执行方式示例。
- `scripts/qa_pdf2zh_output.py`：用于检查 `pdf2zh` 输出 PDF 的辅助 QA 脚本。

## 适用范围

本 Skill 适用于：

- 将英文科研论文 PDF 翻译为中文阅读 PDF。
- 生成 `pdf2zh` 的 `*-mono.pdf` 和 `*-dual.pdf` 输出。
- 在尽量保留原论文版式、公式、图表、表格和题注的前提下制作双语阅读材料。
- 为 Codex / AI Agent 提供稳定、可复用、可检查的论文 PDF 翻译流程。

本 Skill 不用于论文问答、文献综述写作、普通文本翻译、Word 文档翻译、网页翻译，或 Zotero / Obsidian / Streamlit 等集成开发。

## 使用方式

把 `skills/paper-bilingual-translator/` 安装或复制到 Codex 的本地 skills 目录后，当用户提出“翻译英文论文 PDF”“生成中英双语对照 PDF”“保留公式和图表排版”等请求时，Agent 应按照 `SKILL.md` 中的流程执行。

根 README 只保留项目说明；所有实际执行细则请查看 `skills/paper-bilingual-translator/SKILL.md`。
