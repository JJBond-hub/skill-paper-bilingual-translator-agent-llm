# 使用示例

## 单篇论文冒烟测试

用户请求：

> 帮我把 `paper.pdf` 翻译成中文，并生成中英文对照 PDF。

推荐先执行：

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_smoke -p 1 -t 1
```

在运行全文翻译前先检查第 1 页，重点查看标题、作者信息、摘要、侧边标记、URL 和第一节正文。

## 全文翻译

冒烟测试通过后执行：

```bash
pdf2zh paper.pdf -li en -lo zh -o translated_full -t 1
```

然后运行：

```bash
python scripts/qa_pdf2zh_output.py --source paper.pdf --output-dir translated_full --report translated_full/qa_report.md
```

交付时报告生成的 `mono` 和 `dual` 文件、页数以及 QA 警告。

## arXiv 论文

用户请求：

> 把这篇 arXiv 论文翻译成中文，保留公式和图表：https://arxiv.org/pdf/2501.00001.pdf

命令：

```bash
pdf2zh https://arxiv.org/pdf/2501.00001.pdf -li en -lo zh -o translated_arxiv -t 1
```

如果第一页包含 arXiv 标记或元数据侧栏，翻译后需要人工检查。

## 左右对照阅读视图

用户请求：

> 我需要类似左边英文、右边中文的论文阅读 PDF。

说明：

```text
使用生成的 *-dual.pdf，并在 PDF 阅读器中开启双页或面对页视图。
```

如果用户要求每一个物理 PDF 页面都做成左右并排的宽页面，应视为 `pdf2zh` 之后的额外 PDF 后处理任务。

## 摘要页问题或英文残留

用户请求：

> 摘要部分没有完全翻译，首页排版也有点怪。

先只调试受影响页面：

```bash
pdf2zh paper.pdf -li en -lo zh -o retry_page1 -p 1 --ignore-cache -t 1
```

然后尝试以下命令之一：

```bash
pdf2zh paper.pdf -li en -lo zh -o retry_babeldoc -p 1 --babeldoc --ignore-cache -t 1
pdf2zh paper.pdf -li en -lo zh -o retry_compatible -p 1 --compatible --ignore-cache -t 1
pdf2zh paper.pdf -li en -lo zh -o retry_fonts -p 1 --skip-subset-fonts --ignore-cache -t 1
```

如果问题仍然存在，应明确报告受影响页面，并把标题/摘要的手工修正作为单独任务处理。

## 批量翻译

用户请求：

> 把 `papers` 文件夹里的英文论文都翻译成中文双语 PDF。

命令：

```bash
pdf2zh --dir papers -li en -lo zh -o translated_batch -t 1
```

运行前统计 `papers` 中的 PDF 数量；运行后列出每篇论文生成的 `mono` 和 `dual` PDF，并标记缺失输出。

## 安装慢或首次运行慢

如果 `pip install pdf2zh` 看起来卡住了，优先使用：

```bash
py -3.12 -m pip install --user --progress-bar off --only-binary=:all: pdf2zh==1.9.11
```

如果第一次翻译花时间下载模型或字体，应说明这是一次性初始化成本。
