#!/usr/bin/env python3
"""Run a safe pdf2zh smoke-test then full-translation workflow.

This wrapper prevents a common failure mode: after translating page 1 for a
smoke test, the full translation accidentally reuses the smoke output directory
or cache and page 1 is not translated again cleanly. The wrapper always creates
separate smoke/full directories and refreshes the pdf2zh cache by default.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


@dataclass(frozen=True)
class WorkflowPaths:
    source: Path
    output_root: Path
    smoke_dir: Path
    full_dir: Path
    side_by_side: Path | None


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run pdf2zh safely: page-1 smoke test in one directory, then full "
            "translation in a separate directory with cache refresh enabled."
        )
    )
    parser.add_argument("--source", required=True, help="Source PDF path or URL.")
    parser.add_argument(
        "--output-root",
        required=True,
        help="Root output directory containing smoke/ and full/ subdirectories.",
    )
    parser.add_argument(
        "--pdf2zh",
        default="pdf2zh",
        help="pdf2zh executable path. Default: pdf2zh.",
    )
    parser.add_argument("--lang-in", default="en", help="Source language. Default: en.")
    parser.add_argument("--lang-out", default="zh", help="Target language. Default: zh.")
    parser.add_argument("--thread", default="1", help="pdf2zh thread count. Default: 1.")
    parser.add_argument(
        "--smoke-pages",
        default="1",
        help="Smoke-test page selection passed to pdf2zh -p. Default: 1.",
    )
    parser.add_argument(
        "--skip-smoke",
        action="store_true",
        help="Skip the smoke test and only run full translation.",
    )
    parser.add_argument(
        "--reuse-cache",
        action="store_true",
        help="Do not pass --ignore-cache. Not recommended after smoke tests.",
    )
    parser.add_argument(
        "--side-by-side",
        action="store_true",
        help="Create a physical left-original/right-Chinese PDF after full translation.",
    )
    parser.add_argument(
        "--impose-script",
        help="Path to impose_side_by_side_pdf.py. Defaults next to this script.",
    )
    parser.add_argument(
        "--extra-arg",
        action="append",
        default=[],
        help="Additional argument passed to both pdf2zh calls. Repeat as needed.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print planned commands as JSON without executing them.",
    )
    return parser.parse_args(argv)


def resolve_paths(args: argparse.Namespace) -> WorkflowPaths:
    source = Path(args.source).expanduser()
    if not looks_like_url(args.source):
        source = source.resolve()
        if not source.exists():
            raise FileNotFoundError(f"Source PDF does not exist: {source}")

    output_root = Path(args.output_root).expanduser().resolve()
    smoke_dir = output_root / "smoke"
    full_dir = output_root / "full"
    side_by_side = output_root / "side-by-side.pdf" if args.side_by_side else None
    return WorkflowPaths(
        source=source,
        output_root=output_root,
        smoke_dir=smoke_dir,
        full_dir=full_dir,
        side_by_side=side_by_side,
    )


def looks_like_url(value: str) -> bool:
    return value.startswith(("http://", "https://"))


def build_pdf2zh_command(
    pdf2zh: str,
    source: Path,
    output_dir: Path,
    args: argparse.Namespace,
    pages: str | None,
) -> list[str]:
    command = [
        pdf2zh,
        str(source),
        "-li",
        args.lang_in,
        "-lo",
        args.lang_out,
        "-o",
        str(output_dir),
        "-t",
        str(args.thread),
    ]
    if pages:
        command.extend(["-p", pages])
    if not args.reuse_cache:
        command.append("--ignore-cache")
    command.extend(args.extra_arg)
    return command


def build_impose_command(
    paths: WorkflowPaths,
    impose_script: Path,
) -> list[str]:
    if paths.side_by_side is None:
        raise ValueError("side_by_side output is not enabled.")
    return [
        sys.executable,
        str(impose_script),
        "--source",
        str(paths.source),
        "--output-dir",
        str(paths.full_dir),
        "--output",
        str(paths.side_by_side),
    ]


def default_impose_script() -> Path:
    return Path(__file__).resolve().with_name("impose_side_by_side_pdf.py")


def build_plan(args: argparse.Namespace, paths: WorkflowPaths) -> list[list[str]]:
    commands: list[list[str]] = []
    if not args.skip_smoke:
        commands.append(
            build_pdf2zh_command(
                args.pdf2zh,
                paths.source,
                paths.smoke_dir,
                args,
                args.smoke_pages,
            )
        )
    commands.append(
        build_pdf2zh_command(args.pdf2zh, paths.source, paths.full_dir, args, None)
    )
    if args.side_by_side:
        impose_script = (
            Path(args.impose_script).expanduser().resolve()
            if args.impose_script
            else default_impose_script()
        )
        commands.append(build_impose_command(paths, impose_script))
    return commands


def create_output_dirs(paths: WorkflowPaths, skip_smoke: bool) -> None:
    paths.output_root.mkdir(parents=True, exist_ok=True)
    if not skip_smoke:
        paths.smoke_dir.mkdir(parents=True, exist_ok=True)
    paths.full_dir.mkdir(parents=True, exist_ok=True)


def run_command(command: list[str]) -> None:
    printable = " ".join(command)
    print(f"Running: {printable}")
    subprocess.run(command, check=True)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        paths = resolve_paths(args)
        commands = build_plan(args, paths)
        if args.dry_run:
            print(json.dumps(commands, ensure_ascii=False, indent=2))
            return 0
        create_output_dirs(paths, args.skip_smoke)
        for command in commands:
            run_command(command)
    except subprocess.CalledProcessError as exc:
        print(f"Command failed with exit code {exc.returncode}: {exc.cmd}", file=sys.stderr)
        return exc.returncode
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
