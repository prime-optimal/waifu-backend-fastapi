#!/usr/bin/env python3
"""Render Mermaid diagrams to PNG and SVG assets using mermaid-cli."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence


DEFAULT_SCALE = 3.0
DEFAULT_SOURCES = ("docs/diagrams",)
OUTPUT_EXTENSIONS = ("png", "svg")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render Mermaid diagrams to PNG and SVG using mermaid-cli (mmdc)."
    )
    parser.add_argument(
        "paths",
        nargs="*",
        default=list(DEFAULT_SOURCES),
        help="Directories or .mermaid files to render (default: docs/diagrams).",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=DEFAULT_SCALE,
        help="PNG scale factor passed to mermaid-cli (default: %(default)s).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-render outputs even when the PNG/SVG is newer than the source diagram.",
    )
    parser.add_argument(
        "--cli",
        default=os.environ.get("MERMAID_CLI"),
        help="Override mermaid-cli executable (default: detect 'mmdc' or fall back to 'npx --yes @mermaid-js/mermaid-cli').",
    )
    return parser.parse_args()


def resolve_cli(cli_override: str | None) -> Sequence[str]:
    if cli_override:
        return cli_override.split()
    if shutil.which("mmdc"):
        return ["mmdc"]
    if shutil.which("npx"):
        return ["npx", "--yes", "@mermaid-js/mermaid-cli"]
    sys.exit("Neither 'mmdc' nor 'npx' was found on PATH; install mermaid-cli before running.")


def gather_sources(paths: Iterable[str]) -> list[Path]:
    resolved: list[Path] = []
    for item in paths:
        path = Path(item).resolve()
        if path.is_file() and path.suffix == ".mermaid":
            resolved.append(path)
        elif path.is_dir():
            resolved.extend(path.rglob("*.mermaid"))
        else:
            print(f"Skipping {path}: not a .mermaid file or directory", file=sys.stderr)
    return sorted(set(resolved))


def should_render(source: Path, output: Path, force: bool) -> bool:
    if force or not output.exists():
        return True
    return source.stat().st_mtime > output.stat().st_mtime


def render_diagram(cli: Sequence[str], source: Path, scale: float, force: bool) -> None:
    for extension in OUTPUT_EXTENSIONS:
        output = source.with_suffix(f".{extension}")
        if not should_render(source, output, force):
            continue
        cmd = list(cli) + ["-i", str(source), "-o", str(output)]
        if extension == "png":
            cmd += ["-s", str(scale)]
        subprocess.run(cmd, check=True)
        print(f"Rendered {output.relative_to(Path.cwd())}")


def main() -> None:
    args = parse_args()
    cli = resolve_cli(args.cli)
    sources = gather_sources(args.paths)

    if not sources:
        print("No Mermaid diagrams found.")
        return

    for source in sources:
        render_diagram(cli, source, args.scale, args.force)


if __name__ == "__main__":
    main()
