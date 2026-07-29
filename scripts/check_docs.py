#!/usr/bin/env python3
"""Repo quality gates for the Android Staff Engineer Playbook.

Run from the repo root:  python3 scripts/check_docs.py

Checks (each maps to a defect class that has actually occurred in this repo):
  1. Broken internal links      — relative link targets that don't exist.
  2. Broken heading anchors     — internal fragments that do not match a Markdown heading.
  3. Link text/target mismatch  — link text names `foo.md` but the target is `bar.md`
                                  (stale redirects left behind when files are created later).
  4. Unfinished-content markers — literal `*TODO: ...*` or standalone `TBD` shipped in content.
  5. Thin-file guard            — non-stub content files under the word floor must either be
                                  expanded or explicitly allowlisted below (visible debt).
  6. Currency reminder (WARN-ONLY) — rows in the milestones.md Currency Watchlist whose
                                  last-checked date is older than STALE_DAYS. Never fails
                                  the build: the passage of time must not break unrelated
                                  PRs. It nags until the row is re-verified and re-dated.
  7. Answer-key coverage        — existing debt is warning-only while topics migrate, but
                                  every present key must answer each numbered question once.
  8. Guided-index coverage     — every topic file appears in its tree's parent sequence.

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
EXEMPT_DIRS = {"assets", "templates"}

TREE_INDEXES = {
    "android.md",
    "backend-for-mobile.md",
    "career.md",
    "computer-science.md",
    "distributed-systems.md",
    "engineering-fundamentals.md",
    "kotlin.md",
    "leadership.md",
    "mobile-system-design.md",
    "observability.md",
    "patterns.md",
    "platform-engineering.md",
    "principles.md",
    "reference-architectures.md",
    "release-engineering.md",
    "security.md",
}

TREE_INDEX_FOLDERS = {
    "android.md": "android",
    "backend-for-mobile.md": "backend-for-mobile",
    "career.md": "career",
    "computer-science.md": "computer-science",
    "distributed-systems.md": "distributed-systems",
    "engineering-fundamentals.md": "engineering-fundamentals",
    "kotlin.md": "kotlin",
    "leadership.md": "leadership",
    "mobile-system-design.md": "mobile-system-design",
    "observability.md": "observability",
    "patterns.md": "patterns",
    "platform-engineering.md": "platform-engineering",
    "principles.md": "principles",
    "reference-architectures.md": "reference-architectures",
    "release-engineering.md": "release-engineering",
    "security.md": "security",
}


def iter_md_files():
    for root, dirs, files in os.walk("."):
        dirs[:] = [d for d in dirs if d not in {".git", ".github", "node_modules"}]
        for f in sorted(files):
            if f.endswith(".md"):
                yield os.path.normpath(os.path.join(root, f))


def github_heading_anchors(text: str) -> set[str]:
    """Approximate GitHub's Markdown heading IDs, including duplicate suffixes."""
    anchors, counts = set(), {}
    for line in text.splitlines():
        match = re.match(r"^#{1,6}\s+(.+?)\s*#*$", line)
        if not match:
            continue
        heading = re.sub(r"<[^>]+>", "", match.group(1).strip().lower())
        heading = re.sub(r"[`*_~]", "", heading)
        base = "".join(ch for ch in heading if ch.isalnum() or ch in " -_")
        base = re.sub(r"\s", "-", base)
        occurrence = counts.get(base, 0)
        counts[base] = occurrence + 1
        anchors.add(base if occurrence == 0 else f"{base}-{occurrence}")
    return anchors


def numbered_ordinals(section: str) -> list[int]:
    """Return ordered-list numbers using either Markdown delimiter (`1.` or `1)`)."""
    return [
        int(value)
        for value in re.findall(r"^(\d+)[.)]\s+", section, flags=re.MULTILINE)
    ]


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


def orphaned_topics() -> list[str]:
    """Return topic files not linked from their owning top-level guided index."""
    orphaned = []
    for index, folder in TREE_INDEX_FOLDERS.items():
        try:
            with open(index, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            orphaned.append(f"{index}: index is missing")
            continue

        linked = set()
        for match in re.finditer(r"\[[^\]]*\]\(([^)\s]+\.md)(?:#[^)]*)?\)", text):
            target = match.group(1).split("#", 1)[0]
            linked.add(os.path.normpath(os.path.join(os.path.dirname(index), target)))

        for root, dirs, files in os.walk(folder):
            dirs[:] = [d for d in dirs if d not in {".git", "node_modules"}]
            for name in files:
                if name.endswith(".md"):
                    path = os.path.normpath(os.path.join(root, name))
                    if path not in linked:
                        orphaned.append(f"{path}: not linked from {index}")
    return orphaned


def main() -> int:
    paths = list(iter_md_files())
    anchors_by_path = {}
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            anchors_by_path[path] = github_heading_anchors(fh.read())

    broken, broken_anchors, mismatches, todos, thin = [], [], [], [], []
    missing_answer_keys, answer_key_mismatches, unordered_indexes = [], [], []

    for path in paths:
        with open(path, encoding="utf-8") as fh:
            text = fh.read()

        # 1. Broken internal links
        for m in re.finditer(r"\[[^\]]*\]\(([^)\s]+)\)", text):
            link = m.group(1)
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            target, separator, fragment = link.partition("#")
            resolved = path if not target else os.path.normpath(
                os.path.join(os.path.dirname(path), target)
            )
            if target and not os.path.exists(resolved):
                broken.append(f"{path}: {link}")
                continue
            if separator and fragment and resolved.endswith(".md"):
                anchors = anchors_by_path.get(resolved, set())
                if fragment not in anchors:
                    broken_anchors.append(f"{path}: {link}")

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

        questions = re.search(
            r"^## Probing Questions\s*$(.*?)(?=^## |\Z)",
            text,
            flags=re.MULTILINE | re.DOTALL,
        )
        if questions:
            answer_key = re.search(
                r"^## Answer Key\s*$(.*?)(?=^## |\Z)",
                text,
                flags=re.MULTILINE | re.DOTALL,
            )
            if not answer_key:
                missing_answer_keys.append(path)
            else:
                question_ordinals = numbered_ordinals(questions.group(1))
                answer_ordinals = numbered_ordinals(answer_key.group(1))
                expected_ordinals = list(range(1, len(question_ordinals) + 1))
                if (
                    question_ordinals != expected_ordinals
                    or answer_ordinals != expected_ordinals
                ):
                    answer_key_mismatches.append(
                        f"{path}: questions {question_ordinals}, answers {answer_ordinals}; "
                        f"expected {expected_ordinals}"
                    )

        if path.removeprefix("./") in TREE_INDEXES:
            if not re.search(r"^## Guided Reading Sequence\s*$", text, flags=re.MULTILINE):
                unordered_indexes.append(path)

        # 4. Thin-file guard (content files only: depth > 1, not stubs, not templates)
        rel_parts = path.split(os.sep)
        if len(rel_parts) > 1 and rel_parts[0] not in EXEMPT_DIRS:
            if "cross-reference stub" not in text and path not in THIN_FILE_ALLOWLIST:
                words = len(text.split())
                if words < WORD_FLOOR:
                    thin.append(f"{path}: {words} words (floor {WORD_FLOOR})")

    unindexed_topics = orphaned_topics()
    failed = False
    for title, items in [
        ("Broken internal links", broken),
        ("Broken internal heading anchors", broken_anchors),
        ("Link text/target mismatches (stale redirects)", mismatches),
        ("Unfinished-content markers (TODO/TBD)", todos),
        ("Thin content files (expand, or allowlist with a reason)", thin),
        ("Answer keys whose numbered answers do not match their questions", answer_key_mismatches),
        ("Tree indexes without a Guided Reading Sequence", unordered_indexes),
        ("Topic files missing from their guided tree index", unindexed_topics),
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

    if missing_answer_keys:
        print(
            f"⚠ Answer-key migration debt: {len(missing_answer_keys)} topic files have "
            "probing questions but no answer key (warning only)"
        )
    else:
        print("✓ Probing questions: every topic has an answer key")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
