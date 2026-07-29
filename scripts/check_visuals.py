#!/usr/bin/env python3
"""Validate Markdown images and render every Mermaid block.

Run from the repository root:

    python3 scripts/check_visuals.py \
      --renderer "npx --yes @mermaid-js/mermaid-cli@11.16.0"

The renderer accepts a Markdown file containing all repository Mermaid blocks.
Rendering the aggregate keeps the browser startup cost low while still exercising
the same parser GitHub uses for Mermaid syntax.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import shlex
import subprocess
import sys
import tempfile


MERMAID_BLOCK = re.compile(
    r"^```mermaid[ \t]*\n(.*?)^```[ \t]*$", re.MULTILINE | re.DOTALL
)
MERMAID_START = re.compile(r"^```mermaid[ \t]*$", re.MULTILINE)
MARKDOWN_IMAGE = re.compile(r"!\[([^\]]*)\]\(([^)\s]+)(?:\s+['\"][^'\"]*['\"])?\)")
ALLOWED_ASSET_SUFFIXES = {".jpeg", ".jpg", ".png", ".svg", ".webp"}
SKIPPED_DIRS = {".git", "node_modules"}


def markdown_files() -> list[Path]:
    paths = []
    for root, dirs, files in os.walk("."):
        dirs[:] = [name for name in dirs if name not in SKIPPED_DIRS]
        paths.extend(Path(root, name) for name in files if name.endswith(".md"))
    return sorted(paths)


def collect_mermaid(paths: list[Path]) -> tuple[list[tuple[Path, int, str]], list[str]]:
    blocks: list[tuple[Path, int, str]] = []
    errors: list[str] = []
    for path in paths:
        text = path.read_text(encoding="utf-8")
        matches = list(MERMAID_BLOCK.finditer(text))
        starts = list(MERMAID_START.finditer(text))
        if len(matches) != len(starts):
            errors.append(f"{path}: unclosed or malformed Mermaid fence")
        for match in matches:
            line = text.count("\n", 0, match.start()) + 1
            body = match.group(1).strip()
            if not body:
                errors.append(f"{path}:{line}: empty Mermaid block")
                continue
            blocks.append((path, line, body))
    return blocks, errors


def check_images(paths: list[Path]) -> list[str]:
    errors: list[str] = []
    registry_path = Path("assets/ATTRIBUTION.md")
    registry = registry_path.read_text(encoding="utf-8") if registry_path.exists() else ""

    for path in paths:
        text = path.read_text(encoding="utf-8")
        if re.search(r"<img\b", text, flags=re.IGNORECASE):
            errors.append(f"{path}: HTML images are not allowed")
        for match in MARKDOWN_IMAGE.finditer(text):
            alt, target = match.group(1).strip(), match.group(2)
            line = text.count("\n", 0, match.start()) + 1
            if not alt or alt.lower() in {"image", "diagram", "screenshot"}:
                errors.append(f"{path}:{line}: image needs meaningful alt text")
            if target.startswith(("http://", "https://", "//")):
                errors.append(f"{path}:{line}: hotlinked images are not allowed: {target}")
                continue
            asset = (path.parent / target).resolve()
            try:
                relative = asset.relative_to(Path.cwd().resolve())
            except ValueError:
                errors.append(f"{path}:{line}: image resolves outside the repository: {target}")
                continue
            if not relative.parts or relative.parts[0] != "assets":
                errors.append(f"{path}:{line}: local images must live under assets/: {target}")
            if asset.suffix.lower() not in ALLOWED_ASSET_SUFFIXES:
                errors.append(f"{path}:{line}: unsupported image format: {target}")
            if not asset.is_file():
                errors.append(f"{path}:{line}: image does not exist: {target}")
            if relative.as_posix() not in registry:
                errors.append(
                    f"{path}:{line}: {relative.as_posix()} is missing from assets/ATTRIBUTION.md"
                )
    return errors


def render(blocks: list[tuple[Path, int, str]], renderer: str) -> list[str]:
    if not blocks:
        return []
    command = shlex.split(renderer)
    if not command:
        return ["renderer command is empty"]

    with tempfile.TemporaryDirectory(prefix="playbook-mermaid-") as temp_dir:
        temp = Path(temp_dir)
        source = temp / "all-diagrams.md"
        output = temp / "rendered.md"
        artefacts = temp / "artefacts"
        sections = []
        for index, (path, line, body) in enumerate(blocks, start=1):
            sections.append(
                f"## Diagram {index}: {path.as_posix()}:{line}\n\n"
                f"```mermaid\n{body}\n```\n"
            )
        source.write_text("\n".join(sections), encoding="utf-8")
        result = subprocess.run(
            command
            + [
                "--input",
                str(source),
                "--output",
                str(output),
                "--artefacts",
                str(artefacts),
                "--outputFormat",
                "svg",
                "--backgroundColor",
                "transparent",
                "--jobs",
                "4",
                "--quiet",
            ],
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        if result.returncode:
            detail = result.stdout.strip() or "renderer returned no diagnostic output"
            return [f"Mermaid rendering failed:\n{detail}"]
    return []


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--renderer",
        default="mmdc",
        help="Mermaid CLI command, including package-runner arguments when needed",
    )
    args = parser.parse_args()

    paths = markdown_files()
    blocks, errors = collect_mermaid(paths)
    errors.extend(check_images(paths))
    if not errors:
        errors.extend(render(blocks, args.renderer))

    if errors:
        print(f"✗ Visual validation failed: {len(errors)} problem(s)")
        for error in errors:
            print(f"    {error}")
        return 1

    print(f"✓ Visual validation passed: rendered {len(blocks)} Mermaid diagram(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
