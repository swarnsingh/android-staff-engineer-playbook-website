# Observability publication review — 2026-11-01

## Scope and source authority

This release publishes the Observability learning path and all eleven chapters in the source index's guided order. The path groups signal selection and correlation first, reliability contracts second, and human response and investigation last. Each page receives a concise introduction, and every original Mermaid diagram receives a designed FigureMap. No new animation was added: the figures explain relationships, measurement boundaries, and policy decisions without requiring motion or playback controls.

The source authority is merged playbook PR #72, commit `7666569cf77db7616d43f05cf041c438cb947035`. All twelve Observability Markdown snapshots, including the index, were compared byte-for-byte with that commit. Their individual hashes and reference commit are recorded in `source-snapshot.json`. No chapter prose was edited during website authoring. The original code, tables, question-and-answer material, headings, and Mermaid source are preserved in the rendered reading order.

Three already-published Android pages also receive the merged corrections: Retrofit/OkHttp, ANRs, and memory management/leaks. Their immutable raw snapshots remain unchanged. A separately identified, owner-approved source-sync inventory applies after the existing 743 correction records. The gate requires those original records exactly once, permits only the three declared supplementary records, verifies their merge commit and approval metadata, and checks that each effective chapter's SHA-256 matches the merged source. This reconciles the new source release explicitly rather than weakening the original inventory check. Audit pair counts classify the first route segment, so Android's nested observability directory remains part of the original 928-pair Kotlin/Android baseline.

## Figures and shared rendering

Eleven original diagrams now use the existing FigureMap component, with automatic layout, role-coloured cards, labelled relationships, owner boundaries, captions, text transcripts, and official references. Original Mermaid remains available as preserved source text; no Mermaid picture is published. The six-participant distributed trace uses the shared sequence renderer, and the other models use relationship layouts. Wide diagrams retain readable labels in the shared local scroll region on phones.

Visual inspection exposed a pre-existing shared renderer defect: marker definitions used prefixed IDs while arrow paths referenced unprefixed IDs. The resulting lines lacked visible arrowheads even though geometry checks passed. The renderer now derives both definitions and references from one marker ID, consistent with the [SVG marker reference contract](https://www.w3.org/TR/SVG2/painting.html#MarkerEndProperty). Three regression tests cover map edges, bidirectional edges, sequence messages and self steps, and distinct IDs between figures. Those tests failed on the old renderer and pass with the fix. No per-topic CSS, geometry constants, fonts, or colours were introduced.

The owner also approved a report-only repair to the existing Computer Science publication report. Its initial-draft numbers were distinguished from the stored 195-page integration evidence, and the report was expanded above the repository's 400-word minimum. No Computer Science lesson, code pair, or topic model changed.

## Validation results

The normal build passes without pending figures, preserving 26,240 original units across 207 pages. All 167 FigureMap models pass validation. The desktop frame check covers 200 chapter pages, 166 chapter figures, 138 relationship maps, and 3,304 labels without a reported frame problem. Local CI passes twenty website tests, thirty-one docs-checker tests, the docs gate, and syntax checks for ten browser scripts.

Focused real-browser preview checks cover fifteen pages: the twelve Observability pages and the three updated Android pages. Across four widths (320, 375, 768, and 1440 CSS pixels) and four themes, all 240 checks pass. They detect no page-level horizontal overflow, failed resources, runtime exceptions, rendered Mermaid images, or unresolved SVG marker references. Desktop and phone-width screenshots of the trace figure were inspected and retained.

Fresh full-site audits ran after rebasing onto website main `f330e9e` and after the arrowhead fix. Browser preservation passes 207/207 pages, 7112/7112 code checks, and 1299/1299 question-and-answer checks.
- binder: 560 checks; successful completion.
- motion: 13 checks; successful completion.
- refinement: 69 checks; successful completion.
- ux: 278 checks; successful completion.
- qa-tampering: 31 checks; successful completion.

The superseded pre-fix audit is not used as publication evidence. The publication gate and final project-prefix build pass against this fresh folder. Existing Fundamentals compilation evidence is carried forward only because its required fragment hashes remain unchanged and the gate verifies them again.

## Limits

These are Chromium browser checks and width simulations, not physical-phone, foldable, Safari, Firefox, or screen-reader tests. The source review's Kotlin and Python probes do not establish a complete Android application, Hilt graph, persistent credential store, or live Play/BigQuery integration. In particular, the source's Play API encoding remains explicitly unverified, and its educational release adapter must hold until the encoding is verified. This is separate from the website publication pipeline. The chapter captions and diagrams are explanatory models rather than production measurements, and source references remain the authority for changing platform behavior.
