# Platform Engineering reader release review — 29 October 2026

## Scope and intent

This release registers the six original Platform Engineering chapters and their learning path in the reader website. The chapter order follows the guided reading sequence in `platform-engineering.md`: internal developer platforms, design systems, library versioning, SDK distribution, custom lint and static analysis, and build graph scaling. The path groups those chapters into three navigation phases: paved roads and shared UI, distribution and guardrails, and build feedback. The site navigation now uses that reading order. Each chapter and the path has one short introduction line in `website/content/platform-engineering.json`.

The original Markdown chapters and index were treated as read-only. Their SHA-256 digests are recorded under `platform-engineering_sha256` in `source-snapshot.json`, and the review-data check verifies the exact file set and bytes. This is a lean release: it adds no teaching-layer blend files, chapter-specific CSS, component styling, or new animation. Existing prose, examples, probing questions, and answer keys remain in their original order. Topic registration changes are limited to the shared build, catalog, source check, audit choice, and completion check files required by `AGENTS.md`.

## Designed figures

All five original Mermaid diagrams in this topic have matching FigureMap models in `website/content/diagram-models/figures/platform-engineering.json`. They cover the two ownership routes in an internal developer platform, the three tiers of design tokens, contents of an Android AAR, a deep Gradle module chain, and a wider Gradle fan-out. Each model is keyed to the exact original diagram source hash, has a numbered title and a caption stating its point, and cites official Android, Gradle, or Material sources. Arrows describe relationships with visible labels. Platform and feature ownership, and the AAR package, are expressed as boundaries rather than arrows. Roles use the shared FigureMap color and border-pattern system, so meaning does not depend on color alone. Layout is automatic; no topic-specific coordinates or style values were introduced. The original Mermaid source remains available as preserved text beside each designed figure.

## Checks and evidence

After rebasing onto the latest main, the normal build rendered 159 pages and verified 19,767 original units in order with no preservation problems. `dev.py figures` passed 89 models with no problems. `dev.py frames` checked 154 pages, 89 figures, 118 relationship maps, and 1,892 labels, reporting no frame or label problems. `dev.py ci` passed 15 website unit tests, 31 documentation unit tests, the documentation check, and syntax checks for all 10 browser scripts.

The fresh `dev.py audit platform-engineering-2026-10-29` completed all six browser audit groups. The browser group passed 159 of 159 pages, 5,624 of 5,624 code checks, and 1,194 of 1,194 question-answer pairs. The binder matrix passed 560 of 560 checks; motion passed 13 of 13; refinement passed 69 of 69; UX passed 278 of 278; and tampering fixtures passed 31 of 31. The JSON evidence files in this folder retain the detailed results. The audit covers the computer-science changes already present on main as well as this platform topic, while this release authors only platform content.

## Limits

This release presents the original chapters and designed figure replacements. It does not claim an editorial correction pass over every original technical assertion, nor does it add the optional teaching layer described in the wider rulebook. The figure sources support the specific relationships drawn; the source chapters remain the owner's original text. The gate and GitHub Pages deployment are separate publication checks and must pass before the release is considered live.
