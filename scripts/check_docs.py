#!/usr/bin/env python3
"""Repo quality gates for the Android Staff Engineer Playbook.

Run from the repo root:  python3 scripts/check_docs.py

Checks (each maps to a defect class that has actually occurred in this repo):
  1. Broken internal links      — relative link targets that don't exist.
  2. Link text/target mismatch  — link text names `foo.md` but the target is `bar.md`
                                  (stale redirects left behind when files are created later).
  3. Unfinished-content markers — literal `*TODO: ...*` or standalone `TBD` shipped in content.
  4. Thin-file guard            — non-stub content files under the word floor must either be
                                  expanded or explicitly allowlisted below (visible debt).
  5. Currency reminder (WARN-ONLY) — rows in the milestones.md Currency Watchlist whose
                                  last-checked date is older than STALE_DAYS. Never fails
                                  the build: the passage of time must not break unrelated
                                  PRs. It nags until the row is re-verified and re-dated.

Exit code 0 = all clean; 1 = at least one violation (CI fails).
"""

import datetime
import os
import re
import sys

WORD_FLOOR = 400
STALE_DAYS = 180

# Files that are known-thin and tracked for expansion (see milestones.md, G14).
# Remove entries as they are expanded. Adding to this list requires a reason.
THIN_FILE_ALLOWLIST: set[str] = set()

# Top-level TOC/index files and templates are exempt from the word floor.
EXEMPT_DIRS = {"templates"}


def iter_md_files():
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", ".github", "node_modules"}]
        for f in sorted(files):
            if f.endswith(".md"):
                yield os.path.normpath(os.path.join(root, f))


def currency_warnings() -> list[str]:
    """Warn-only: watchlist rows in milestones.md older than STALE_DAYS."""
    warnings = []
    try:
        with open("milestones.md", encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return warnings
    section = re.search(r"## Currency Watchlist(.*?)(?:\n## |\Z)", text, flags=re.DOTALL)
    if not section:
        return warnings
    today = datetime.date.today()
    for m in re.finditer(r"^\|\s*`([^`|]+)`[^|]*\|[^|]*\|[^|]*\|\s*(\d{4}-\d{2}-\d{2})\s*\|",
                         section.group(1), flags=re.MULTILINE):
        path, date_str = m.group(1), m.group(2)
        age = (today - datetime.date.fromisoformat(date_str)).days
        if age > STALE_DAYS:
            warnings.append(f"{path}: last checked {date_str} ({age} days ago)")
    return warnings


def main() -> int:
    broken, mismatches, todos, thin = [], [], [], []

    for path in iter_md_files():
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        # 1. Broken internal links
        for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            link = m.group(1)
            if link.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target = link.split("#")[0]
            if not target:
                continue
            resolved = os.path.normpath(os.path.join(os.path.dirname(path), target))
            if not os.path.exists(resolved):
                broken.append(f"{path}: {link}")

        # 2. Link text/target mismatch (text looks like a filename but names a different file)
        for m in re.finditer(r"\[`?([a-z0-9][a-z0-9-]*\.md)`?\]\(([^)#\s]+\.md)", text):
            label, target_base = m.group(1), os.path.basename(m.group(2))
            if label != target_base:
                mismatches.append(f"{path}: text '{label}' -> target '{target_base}'")

        # 3. Unfinished-content markers.
        # Inline code spans and fenced code blocks are stripped first so that
        # documentation ABOUT the markers (e.g. CONTRIBUTING.md) doesn't trip the gate.
        prose = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
        prose = re.sub(r"`[^`\n]*`", "", prose)
        for m in re.finditer(r"\*TODO:[^*]*\*|(?<![\w/])TBD(?![\w/])", prose):
            todos.append(f"{path}: {m.group(0)[:70]}")

        # 4. Thin-file guard (content files only: depth > 1, not stubs, not templates)
        rel_parts = path.split(os.sep)
        if len(rel_parts) > 1 and rel_parts[0] not in EXEMPT_DIRS:
            if "cross-reference stub" not in text and path not in THIN_FILE_ALLOWLIST:
                words = len(text.split())
                if words < WORD_FLOOR:
                    thin.append(f"{path}: {words} words (floor {WORD_FLOOR})")

    failed = False
    for title, items in [
        ("Broken internal links", broken),
        ("Link text/target mismatches (stale redirects)", mismatches),
        ("Unfinished-content markers (TODO/TBD)", todos),
        ("Thin content files (expand, or allowlist with a reason)", thin),
    ]:
        if items:
            failed = True
            print(f"\n✗ {title}: {len(items)}")
            for item in items:
                print(f"    {item}")
        else:
            print(f"✓ {title}: none")

    stale = currency_warnings()
    if stale:
        print(f"\n⚠ Currency watchlist rows past {STALE_DAYS} days (warning only, build not failed):")
        for item in stale:
            print(f"    {item}")
    else:
        print("✓ Currency watchlist: all rows fresh")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
