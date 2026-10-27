#!/usr/bin/env python3
"""Repo quality gates for the Android Staff Engineer Playbook.

Run from the repo root after installing requirements-quality.txt:
  python3 scripts/check_docs.py

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
  7. Question/answer coverage   — paired questions need an immediate nonempty answer;
                                  existing separate keys retain their ordinal checks.
                                  Legacy missing-key debt remains warning-only.
  8. Guided-index coverage     — every topic file appears in its tree's parent sequence.

Exit code 0 = all clean; 1 = at least one violation (CI fails).
"""

import datetime
import os
import re
import sys

from markdown_it import MarkdownIt

WORD_FLOOR = 400
STALE_DAYS = 180

# Files that are known-thin and tracked for expansion (see milestones.md, G14).
# Remove entries as they are expanded. Adding to this list requires a reason.
THIN_FILE_ALLOWLIST: set[str] = {
    # Reproduction commands and evidence boundaries for fixtures, not a knowledge chapter.
    "website/validation/README.md",
    # Component contracts are short references; the 400-word chapter floor does not apply.
    "website/design-system/components/Checkpoint/README.md",
    "website/design-system/components/ReadingSheet/README.md",
    "website/design-system/components/CodeCard/README.md",
    "website/design-system/components/Callout/README.md",
    "website/design-system/components/WideDiagram/README.md",
    # Planning record for three testing chapters, not a reader-facing lesson.
    "website/reviews/android-phase6-structure.md",
    # Instructions shipped inside the generated private review package, not a knowledge chapter.
    "website/PRIVATE-PREVIEW.md",
}

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

MARKDOWN = MarkdownIt("commonmark")


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
    """Return ordered-list numbers rendered at the document root.

    CommonMark list parsing depends on container context, interruption rules, marker
    width, and indentation. Delegating those rules to a CommonMark parser avoids
    treating nested lists, block quotes, or code examples as questions or answers.
    A root ordered list emits ``list_item_open`` tokens at level 1; items inside any
    other block container have a greater level.
    """
    return [
        int(token.info)
        for token in MARKDOWN.parse(section)
        if token.type == "list_item_open"
        and token.level == 1
        and token.markup in {".", ")"}
    ]


def root_section(text: str, heading: str) -> list | None:
    """Read an H2 section using Markdown blocks, excluding fenced/quoted headings."""
    tokens = MARKDOWN.parse(text)
    for index, token in enumerate(tokens):
        if (token.type == "heading_open" and token.tag == "h2"
                and token.level == 0 and tokens[index + 1].content == heading):
            start = index + 3
            end = next((i for i in range(start, len(tokens))
                        if tokens[i].type == "heading_open" and tokens[i].level == 0
                        and tokens[i].tag in {"h1", "h2"}), len(tokens))
            return tokens[start:end]
    return None


def question_answer_coverage(text: str) -> tuple[bool, list[str]]:
    """Accept adjacent Question/Answer headings and legacy numbered answer keys.

    Return warning-only legacy missing-key debt separately from malformed coverage.
    Only dedicated Probing Questions are inspected; ordinary checklists stay lists.
    """
    questions = root_section(text, "Probing Questions")
    if not questions:
        return False, []
    headings = [(i, token.tag, questions[i + 1].content)
                for i, token in enumerate(questions)
                if token.type == "heading_open" and token.level == 0]
    paired = [(i, name) for i, tag, name in headings
              if tag == "h3" and re.match(r"^Question(?:\s|$)", name, re.I)]
    has_answer_heading = any(tag == "h4" and name.casefold() == "answer"
                             for _, tag, name in headings)
    if paired or has_answer_heading:
        errors = []
        numbers = []
        if not paired:
            return False, ["paired answers have no numbered Question headings"]
        if root_section(text, "Answer Key") is not None:
            errors.append("paired questions also contain a separate Answer Key")
        if any(i < paired[0][0] and tag == "h4" and name.casefold() == "answer"
               for i, tag, name in headings):
            errors.append("Answer heading appears before the first Question")
        for start, name in paired:
            match = re.fullmatch(r"Question\s+(\d+)(?:\s*[:.—-]\s*(.+))?", name, re.I)
            numbers.append(int(match.group(1)) if match else None)
            end = next((i for i, tag, _ in headings if i > start and tag == "h3"), len(questions))
            answers = [i for i, tag, title in headings
                       if start < i < end and tag == "h4" and title.casefold() == "answer"]
            if len(answers) != 1:
                errors.append(f"{name}: expected one immediate Answer heading, found {len(answers)}")
                continue
            answer = answers[0]
            if any(start < i < answer for i, _, _ in headings):
                errors.append(f"{name}: Answer must be the next heading after the question")
            meaningful = lambda blocks: any(
                t.type in {"inline", "fence", "code_block"} and t.content.strip()
                and not (i and blocks[i - 1].type == "heading_open")
                for i, t in enumerate(blocks))
            if not (match and match.group(2)) and not meaningful(questions[start + 3:answer]):
                errors.append(f"{name}: question text is empty")
            if not meaningful(questions[answer + 3:end]):
                errors.append(f"{name}: answer text is empty")
        expected = list(range(1, len(paired) + 1))
        if numbers != expected:
            errors.append(f"paired question numbers {numbers}; expected {expected}")
        return False, errors

    # Keep the legacy contract: every present numbered key covers each numbered
    # question exactly once, while wholly absent keys remain migration warnings.
    answers = root_section(text, "Answer Key")
    if answers is None:
        return True, []
    ordinals = lambda blocks: [int(t.info) for t in blocks if t.type == "list_item_open"
                              and t.level == 1 and t.markup in {".", ")"}]
    question_numbers, answer_numbers = ordinals(questions), ordinals(answers)
    expected = list(range(1, len(question_numbers) + 1))
    if question_numbers != expected or answer_numbers != expected:
        return False, [f"questions {question_numbers}, answers {answer_numbers}; expected {expected}"]
    return False, []


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

        missing_key, coverage_problems = question_answer_coverage(text)
        if missing_key:
            missing_answer_keys.append(path)
        answer_key_mismatches.extend(f"{path}: {problem}" for problem in coverage_problems)

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
        ("Question/answer coverage mismatches", answer_key_mismatches),
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
        print("✓ Probing questions: paired answers or legacy answer keys are present")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
