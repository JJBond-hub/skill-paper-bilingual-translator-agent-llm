# Known Installation Traps

This document records the failures that make `pdf2zh` unusable on a fresh
install, and the exact fix for each. Every entry was reproduced and then verified
fixed on:

- Windows 11, Python 3.12, `pdf2zh 1.9.11`, `httpx 0.28.1`, `bitstring 5.0.0`

Traps 1, 2 and 3 are **independent**. Fixing one only reveals the next, because
`pdf2zh` imports all of its translation backends unconditionally. Expect to hit
them in sequence on a clean machine.

These are all upstream issues in `pdf2zh` / its dependencies, not problems with
this Skill. They are documented here because the Skill is unusable until they are
cleared.

---

## Trap 1 — `NO_PROXY` containing a bracketed IPv6 literal breaks `import pdf2zh`

### Symptom

```
ValueError: invalid literal for int() with base 10: ':1]'

During handling of the above exception, another exception occurred:
  ...
  File "httpx/_urls.py", line 117, in __init__
  File "httpx/_urlparse.py", line 411, in normalize_port
httpx.InvalidURL: Invalid port: ':1]'
```

The traceback ends inside `ollama`, which looks like the culprit but is not:

```
File "pdf2zh/translator.py", line 11, in <module>
    import ollama
File "ollama/__init__.py", line 68, in <module>
    _client = Client()          # builds an httpx.Client at import time
```

### Root cause

```text
NO_PROXY=localhost,127.0.0.1,::1,[::1]
```

httpx parses every `NO_PROXY` entry into a `URLPattern`. Given the **bracketed**
form `[::1]` it treats the entry as a wildcard host and synthesises the pattern
`all://*[::1]`. The `*` makes httpx read `:1]` as a port number, which is not an
integer, so it raises `InvalidURL`.

Reproduce directly — this is the whole bug, no pdf2zh required:

```python
from httpx._utils import URLPattern
URLPattern("all://[::1]")    # OK
URLPattern("all://*[::1]")   # InvalidURL: Invalid port: ':1]'
```

Because `ollama` constructs an `httpx.Client` at import time, and `pdf2zh`
imports `ollama` unconditionally, this single environment entry makes
`import pdf2zh` fail — regardless of which `-s` engine you intend to use.

### Fix

Drop the bracketed form. `::1` without brackets is understood correctly:

```text
NO_PROXY=localhost,127.0.0.1,::1
```

On Windows the variable must be cleared in **every** place a stale copy can
survive, because Windows treats environment names case-insensitively and both
`NO_PROXY` and `no_proxy` may be present:

```powershell
[System.Environment]::SetEnvironmentVariable('NO_PROXY', 'localhost,127.0.0.1,::1', 'User')
```

Verify that no entry fails to parse:

```bash
python -c "from httpx._utils import get_environment_proxies as g; from httpx._urls import URL; [URL(k) for k in g()]" && echo "proxy env OK"
```

---

## Trap 2 — `tencentcloud-sdk-python-tmt` no longer ships `TextTranslateRequest`

### Symptom

```
ImportError: cannot import name 'TextTranslateRequest'
from 'tencentcloud.tmt.v20180321.models'
```

### Root cause

`pdf2zh/translator.py` does an unconditional top-level import:

```python
from tencentcloud.tmt.v20180321.models import (
    TextTranslateRequest,
    TextTranslateResponse,
)
```

`pyproject.toml` declares `tencentcloud-sdk-python-tmt` with no upper bound. The
class was removed between SDK **3.1.121** (has both) and **3.1.129** (has only
`ImageTranslateLLMRequest` / `ImageTranslateLLMResponse`). A fresh install
therefore resolves to a version that cannot satisfy the import.

Check your installed copy:

```bash
python -c "import tencentcloud.tmt.v20180321.models as m; print([n for n in dir(m) if not n.startswith('_')])"
```

If `TextTranslateRequest` is absent, this trap applies.

### Fix (pick one)

**Option A — pin the last working SDK** (the workaround upstream suggests):

```bash
pip install "tencentcloud-sdk-python-tmt==3.0.1257"
```

**Option B — inject stand-ins.** The two names are only ever touched inside the
Tencent backend (`translator.py` around lines 712-719), so stubs are enough to
let the import resolve. Place this in `sitecustomize.py` inside the environment's
`site-packages`, which Python loads automatically at startup:

```python
try:
    from tencentcloud.tmt.v20180321 import models as _m
except Exception:
    _m = None

if _m is not None:
    if not hasattr(_m, "TextTranslateRequest"):
        class TextTranslateRequest(_m.AbstractModel):
            def __init__(self):
                super().__init__()
                self.SourceText = self.Source = self.Target = self.ProjectId = None
        _m.TextTranslateRequest = TextTranslateRequest
    if not hasattr(_m, "TextTranslateResponse"):
        class TextTranslateResponse(_m.AbstractModel):
            def __init__(self):
                super().__init__()
                self.TargetText = self.Source = self.Target = self.RequestId = None
        _m.TextTranslateResponse = TextTranslateResponse
```

> Reported upstream as
> [PDFMathTranslate#1167](https://github.com/PDFMathTranslate/PDFMathTranslate/issues/1167)
> — check that issue first, it may already be fixed.

---

## Trap 3 — `bitstring` 5.x removed `BitStream`, which `babeldoc` imports

### Symptom

```
File ".../babeldoc/document_il/backend/pdf_creater.py", line 9, in <module>
    from bitstring import BitStream
ImportError: cannot import name 'BitStream' from 'bitstring'
```

### Root cause

`bitstring` 5.0.0 removed the mutable `BitStream` class. `babeldoc` declares
`bitstring>=4.3` with **no upper bound**, so a fresh install resolves to 5.x and
the import fails.

Note that `import pdf2zh` succeeds — the failure only appears on the CLI path,
which loads `babeldoc` through `pdf2zh/pdf2zh.py`.

Aliasing `Bits` to `BitStream` does **not** work: `babeldoc` calls `BitStream()`
and then mutates it with `append(...)`, and bitstring 5.x's `Bits` is immutable.

### Fix

```bash
pip install "bitstring>=4.3,<5"
```

Confirm:

```bash
python -c "import bitstring; print(bitstring.__version__, hasattr(bitstring,'BitStream'))"
# expect: 4.4.0 True
```

---

## Trap 4 — the default `google` engine hangs instead of failing

### Symptom

The process neither finishes nor errors. Observed: 20 minutes of wall time while
CPU time advanced by less than 2 seconds, and no output written. Cancelling is
the only way forward.

### Root cause

`GoogleTranslator` scrapes `https://translate.google.com/m` and extracts the
result with a regex, then calls `response.raise_for_status()`:

```python
self.endpoint = "https://translate.google.com/m"
...
response.raise_for_status()
re_result = re.findall(r'(?s)class="(?:t0|result-container)">(.*?)<', response.text)
```

In networks where that endpoint is blocked or rate-limited it returns **403/429**
(or never responds), and the failure surfaces as an indefinite wait rather than a
clear error.

Probe the endpoints from your machine before choosing an engine:

```bash
curl -sS -o /dev/null -w "%{http_code}\n" https://translate.google.com/m
curl -sS -o /dev/null -w "%{http_code}\n" https://www.bing.com/translator
```

### Fix

Select a reachable engine explicitly — do not rely on the default:

```bash
pdf2zh paper.pdf -li en -lo zh -s bing -o outdir -t 1
```

`bing` was verified working where `google` returned 403/429. Be aware that
`BingTranslator` also scrapes HTML for a session token, so it is exposed to the
same class of breakage. For a durable pipeline use a keyed service
(`-s openai`, `-s deepseek`, `-s silicon`, `-s azure`, …) or a local model.

To avoid waiting on a hang, bound the run and judge progress by CPU time rather
than wall time:

```powershell
$p = Start-Process pdf2zh -ArgumentList $args -NoNewWindow -PassThru
if (-not $p.WaitForExit(240000)) { taskkill /PID $p.Id /T /F }
```

---

## Trap 5 (not a bug) — `pdf2zh` does not create its output directory

### Symptom

Translation completes, every page is processed, then:

```
FileNotFoundError: [Errno 2] No such file or directory: 'outdir/paper-mono.pdf'
```

### Explanation

`-o/--output` must already exist. `pdf2zh` writes into it and does not create it.

### Fix

Create the directory before invoking, or use
`scripts/run_pdf2zh_workflow.py`, which creates `smoke/` and `full/` for you:

```bash
mkdir -p outdir && pdf2zh paper.pdf -li en -lo zh -s bing -o outdir -t 1
```

---

## Recommended setup order

A sequence that avoids rediscovering each trap one at a time:

```bash
# 1. Isolated env on Python 3.10-3.12 (NOT 3.13+; pdf2zh requires <3.13)
py -3.12 -m venv pdf2zh-venv

# 2. Install with both problem dependencies constrained up front
pdf2zh-venv/Scripts/python -m pip install --only-binary=:all: \
    pdf2zh==1.9.11 \
    "tencentcloud-sdk-python-tmt==3.0.1257" \
    "bitstring>=4.3,<5"

# 3. Sanitise NO_PROXY (no bracketed IPv6 form; set both cases on Windows)

# 4. Verify the full import chain before translating anything
pdf2zh-venv/Scripts/pdf2zh --version

# 5. Pick a reachable engine and use an existing output directory
mkdir -p out
pdf2zh-venv/Scripts/pdf2zh paper.pdf -li en -lo zh -s bing -o out -t 1
```

Success looks like this — a version string, exit code 0, no traceback:

```text
pdf2zh v1.9.11
```

Then translate with the Skill's normal workflow
(`scripts/run_pdf2zh_workflow.py`, or the manual two-step in `SKILL.md`).
