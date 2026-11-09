# Whole-site source resync

## Scope and source

All 16 trees (295 Markdown files, including tree indexes) now match the merged playbook byte for byte at source main `93bc3fec641330108b9ee80102d0ea2392edc371`. Every file was copied from exact `git show` bytes. `source-snapshot.json` records the new SHA-256 hashes and per-tree provenance:

- **Kotlin, Android, Computer Science, Engineering Fundamentals** were published from older snapshots (`60b8c2a`, and `b8b5617` for Engineering Fundamentals) with a website correction overlay. They now carry merged source at `127811c` (source PR #83). Their content is identical at `93bc3fe`. That covers 105 files: Android 63, Kotlin 22, Computer Science 7, Engineering Fundamentals 13.
- **Patterns, Leadership, Mobile System Design, Observability, Security, Release Engineering** pick up source PR #83's reference-link repairs in 14 files, recorded at `127811c`.
- **Platform Engineering** picks up source PR #84's primary-source re-review in 6 chapters, recorded at `93bc3fe`.

Principles, Reference Architectures, Career, Distributed Systems and Backend for Mobile already matched and are unchanged.

## Correction overlay retired

Each of the 1,084 approved corrections on the four older trees is now carried by the merged source. They are marked `superseded-by-merged-source` and are no longer applied; the records stay as the audit trail.

- 1,065 match the source text exactly.
- 14 were insertions that the source already contains, so applying them would duplicate text.
- 5 were refined further in source: IM01, VR53, completion:221, completion:385 and completion:506.

A replay check confirmed the result. Excluding the newly appended "Official verification references" sections and #83's link repairs, every changed file renders identically to the previous corrected website text.

The reader-visible changes on these trees are:

- 90 new "Official verification references" sections;
- #83's reference-link repairs in 21 Android and Kotlin files;
- correction highlights and per-chapter correction history removed, because there is no overlay left to show.

## Checker updates

- `check_completion.py` used to require 743 and 747 applied Kotlin and Android corrections. It now asserts three things: the four trees have merged-source provenance, none of their corrections is applied, and each of the 1,084 retired records either appears in the source or had its original wording replaced there.
- `check_review_data.py` checks the 24 historical Kotlin triage proposals differently on resynced trees: their reviewed original wording must now be absent.

## Diagrams and blends

Every original Mermaid block on the older trees hashes to the same key as before, so all FigureMaps and blend anchors resolve unchanged. Platform Engineering's `sdk-distribution` AAR diagram changed. It now shows bundled local JARs, the R.txt symbol table, `public.txt` and `lint.jar`. Its FigureMap model was updated to match after checking the official [AAR anatomy](https://developer.android.com/studio/projects/android-library#aar-contents), which lists both as optional entries.

## Validation

- Build: 35,912 original units preserved in order across 295 pages; all 22 preservation tampering fixtures detected.
- Figures: 268 original and 197 teaching models, 0 problems.
- Frames: desktop and 375 px passed across 279 pages, 339 figures and 5,144 labels.
- CI: 64 website tests, 31 docs tests, 74 Computer Science Java examples, the docs gate and 15 browser-script syntax checks passed.
- Browser audits: all six suites passed:
  - 295 pages;
  - 8,908 code readability cases;
  - 1,732 Q&A pairs;
  - Binder 560, Motion 13, Refinement 69, UX 278, Q&A tampering 31.
- The compiled Engineering Fundamentals Kotlin fragments still hash to the recorded evidence.
- The external link check found no missing resources among 1,257 unique links. It reported 3 soft warnings.

## Limits

Phone evidence is automated, and no new screenshots were taken. The reading text of the four older trees is unchanged apart from the items above, and Platform Engineering's #84 text is the owner-reviewed source. Source `milestones.md` also changed in #84. The website's copy is a recorded link target, not a tree, and is left as it was.
