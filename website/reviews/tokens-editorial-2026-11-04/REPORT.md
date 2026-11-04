# Reader tokens and lesson prose review

This follow-up covers the remaining ReaderShell layout values and FigureMap geometry defaults, plus the length of website-authored lesson additions. It starts from website main `c0de5a37becd14e3912e5be1ff1239fb2de12434`, the reviewed PR #26 merge. It changes website layers only. The source snapshot, original chapters, corrections, code examples, figures, animation data and current Q&A experience remain unchanged. This branch requires owner review before merging or publishing.

## Token ownership

The six ReaderShell stylesheets and FigureMap's CSS section now use 978 named `componentCss` values in the design-system registry. The renderer consumes 103 `figureGeometry` values for markers, cards, labels, groups, routing clearances, fit attempts and sequence lanes. Existing `figure` tokens still own typography, overall frame sizes and compact composition budgets. Structural zeroes, full-size percentages and single fractional tracks remain literal CSS; algorithmic ratios, collision samples and solver cost weights remain Python constants.

CSS macros expand before asset hashing and emission. This preserves relative units, local variable references, declaration order and media queries. A root custom property containing another variable would resolve its references before inheritance, so moving every composite value to root variables could change its meaning. The build-time choice follows the [CSS Variables specification](https://www.w3.org/TR/css-variables-1/#cycles). Unknown or malformed macros, duplicate token names and new raw component dimensions fail authoring checks. Geometry validation rejects invalid and non-finite values. Regression tests cover these failure cases and verify that changing a sequence-spacing token changes its drawing.

All seven compiled stylesheet sources match the base commit byte-for-byte. Before the final build, a direct renderer comparison also matched all 220 original figure models and 75 converted static maps. The final build parity evidence records complete SVG and stylesheet comparisons, covering the relationship maps and compact alternatives too.

## Editorial decisions

The inventory covers all 238 rendered chapters. It counts authored prose and inline identifiers, ordinary tables, answer guidance, hero descriptions, shared interview prompts and the legacy Coroutines additions. It excludes figures, animation payloads and fenced examples. Generated navigation chrome and repeated copies of an authored hero description are excluded. The two cross-reference stubs are reported separately. This is a consistent review aid, not a reading-time estimate or a new publication gate.

The initial inventory identified 48 chapters above the roughly quarter-length working target. Their narrative additions were read for repetition and teaching value. Twenty-one lessons lose 629 words: chapter-outline previews already served by navigation, definitions repeated in the original Overview or First Principles, and two overbroad staff-lens claims. The concrete opening situations and decision examples remain. Exact removed passages are retained in `editorial-edits.json`.

The revised inventory leaves 47 chapters above the soft target. Their individual dispositions are in `editorial-dispositions.json`. Many have short original chapters; their measurement guidance, lifecycle examples or answer explanations still earn their space. Health Connect's ratio largely reflects its five answer-guidance blocks. The system-design exceptions include existing interview prompts and recap checklists; these remain part of the current approved experience. No lesson required splitting after this review. The other 188 non-stub chapters were screened by length rather than subjected to a claim of full editorial review.

A protected-content comparison checks all 21 edited files against the base commit: figure elements, script payloads, fenced code, details elements and answer-guidance blocks are byte-identical. No technical fact or example was added. The inventory parser uses Python's documented [HTMLParser](https://docs.python.org/3/library/html.parser.html) and [AST](https://docs.python.org/3/library/ast.html) APIs; tests distinguish visible prose from nested figures and code.

## Validation and boundaries

The local build preserves all 30,397 original units across 249 pages. Figure checks pass for 220 original and 197 teaching models. Desktop (1440px) and phone (375px) frame checks pass across all 238 chapters: 291 figures, 137 relationship maps and 4,469 labels, including 122 static comparisons/timelines and 447 cards. The 64 website tests, 31 checker tests, docs gate, 74 Java compilation/behavior checks and 15 browser-script syntax checks pass. The edited Content Providers opening was also inspected at 1280×900 and 1024×900; it wraps within the sheet with no horizontal overflow.

`render-parity.json` records 251 HTML files, 543 identical SVGs and eight identical emitted stylesheets against the base build. The six browser audits and real publication gate still require fresh final evidence. Kotlin fragment evidence may carry forward only when its content hashes match, as checked by the gate.

This work does not convert the 41 remaining source chapters or add practice mode. Complex diagrams retain labelled local scrolling. The single consolidated manual phone review remains deferred until all planned trees and pages are integrated; automated phone checks continue here. Approval of this PR will not imply approval of those separate milestones.
