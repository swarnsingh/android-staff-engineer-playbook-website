# Reader Website: Build Guide and Handover

This folder builds the reader website for the playbook. Read [`../content-rulebook.md`](../content-rulebook.md) first, especially sections 16–19: the original chapters are read-only, every page must contain its original chapter in full, and the website adds a clearly labelled teaching layer on top. This guide explains how the build works and where the work stands, so another model or person can continue it.

## Current state

- **Repository:** private `swarnsingh/android-staff-engineer-playbook-website`. Current work: `codex/reader-website-fixes`, published from `main`. Historical branches `codex/reader-website` (`60b8c2a`) and `claude/reader-website-kotlin` (`8a77e22`) are preserved unchanged. The original playbook repository receives no pushes or merges.
- **Scope:** the Kotlin tree — `kotlin.md` plus all 22 Kotlin chapters render as pages.
- **Originals:** read-only snapshot from `60b8c2a`; provenance and file hashes are recorded in `../source-snapshot.json`. Do not edit them.
- **Corrections:** 292 proposals from Codex's audits sit in `content/corrections-*.json`, plus 3 new findings. All are triaged in `reviews/corrections-triage.md` (revised after Codex's review). None is approved yet, so none is applied.

### Progress by chapter

| Chapter | Blend file | Status |
| --- | --- | --- |
| `kotlin.md` (learning path) | — | Original only |
| language-core/variables | `variables.blend` | Blended |
| language-core/null-safety | `null-safety.blend` | Blended |
| language-core/functions | `functions.blend` | Blended |
| language-core/extensions | `extensions.blend` | Blended |
| language-core/data-classes | `data-classes.blend` | Blended |
| language-core/value-classes | `value-classes.blend` | Blended |
| language-core/sealed-classes | `sealed-classes.blend` | Blended |
| language-core/delegation | `delegation.blend` | Blended |
| type-system/generics | `generics.blend` | Blended |
| type-system/variance | `variance.blend` | Blended |
| compiler-features/inline-functions | `inline-functions.blend` | Blended |
| compiler-features/reified-types | `reified-types.blend` | Blended |
| coroutines-and-flow/coroutines | `coroutines.blend` + `content/coroutine-*.html` | Blended |
| coroutines-and-flow/channels-and-select | `channels-and-select.blend` | Blended |
| coroutines-and-flow/flow-operators-and-backpressure | `flow-operators-and-backpressure.blend` | Blended |
| coroutines-and-flow/callbackflow-and-bridging-callbacks | `callbackflow-and-bridging-callbacks.blend` | Blended |
| coroutines-and-flow/coroutines-debugging-and-profiling | `coroutines-debugging-and-profiling.blend` | Blended |
| coroutines-and-flow/test-dispatchers-virtual-time | `test-dispatchers-virtual-time.blend` | Blended |
| runtime-and-jvm/memory-model | `memory-model.blend` | Blended |
| runtime-and-jvm/jvm-interop | `jvm-interop.blend` | Blended |
| runtime-and-jvm/bytecode | `bytecode.blend` | Blended |
| version-updates/kotlin-2-4-update | `kotlin-2-4-update.blend` | Blended |

Update this table whenever a chapter changes state.

## Build and preview

```bash
python3 -m venv .venv && .venv/bin/pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 -m http.server 4174 --bind 127.0.0.1 --directory website/dist
```

Run from the repository root. The build writes `website/dist/` (ignored by git), renders each Mermaid diagram with `npx @mermaid-js/mermaid-cli` (cached in `website/.cache/`; pass `--skip-diagrams` to skip), and then runs the preservation check. It exits non-zero if any original content is missing. Set `SITE_BASE=/android-staff-engineer-playbook/` to build for a project path such as GitHub Pages.

## How a page is assembled

`scripts/build.py` parses each original chapter with markdown-it and renders it into `templates/reader.html`. Sections are grouped into six parts (`PARTS` in the script) by their headings; parts only move forward. Then it adds, in order: the chapter's blend fragments, the Codex coroutine fragments for the coroutines page (each wrapped in a labelled `.blend` container), and approved corrections. An approved correction highlights the changed words (`mark.correction-mark`, when the change is one line outside code) and adds a `.correction-note` to its section with the reason, the original wording and the sources.

`scripts/check_preservation.py` reads only the original areas of each page (`.original-opening` and `section#section-…`), skipping labelled additions. Every original heading, paragraph, list item, table row, code block, HTML block and diagram source must appear there in order, as many times as in the Markdown, and statically accessible; any other text there fails the build. Heading levels and the single page title are checked. Only actual Mermaid source may use the diagram-disclosure exemption. It first runs eleven adversarial fixtures, including disguised diagram disclosures, transparent prose and demoted headings. These static checks do not evaluate a browser CSS cascade. Invoke the separate read-only `scripts/browser_preservation.js` function in a rendered Content page, passing the parsed `dist/coverage/diagram-sources.json` map to check stylesheet-driven visibility, including inherited opacity and hidden ancestors.

## Writing a blend file

Create `content/blend/<chapter-file-stem>.blend` (for example `variables.blend`). It is Markdown with raw HTML allowed, split by markers:

- `<!-- @opening -->` — a problem-first story that replaces the generic intro.
- `<!-- @before Heading :: kind -->` / `<!-- @after Heading :: kind -->` — a fragment placed before, or at the end of, the section with that visible H2 text.
- `<!-- @diagram <hash> -->` — a designed redraw shown instead of a Mermaid diagram; the original stays one tap away. Hashes are the first 16 hex characters of the SHA-256 of the diagram source.
- `<!-- @part Heading :: KEY -->` — override the part a section belongs to.

Kinds: `story`, `guide`, `visual`, `animation`, `check`, `deeper`, `staff`, `try`, `bridge`. The build fails if a marker targets a heading or diagram that does not exist. Keep raw HTML blocks free of blank lines, or Markdown will end the block early. Use `variables.blend` as the reference example.

### Visual components (`blend.css`)

`viz-flow` (steps with arrows), `viz-cols` (comparison columns), `viz-grid`, `viz-stack`, `viz-tree`, `viz-lanes` (timelines with `.mark` positioned by `--at` and `--len`), and `viz-pair` (source beside generated output). Cards are `.node`, with `data-state` set to `active`, `done`, `error`, `warn` or `ghost`. All of them reflow on narrow screens.

### Animations (`blend.js`)

A `<figure class="stepper">` contains a `.stage` with elements marked `data-el="id"` (shown, hidden or given a state per step) and `data-text="id"` (text replaced per step), followed by `<script type="application/json" class="steps">`. Each step has `label`, `caption`, and optional `add`, `remove`, `state` and `text`. Frames are always folded from step one. The build prints every step as a numbered list, so no meaning depends on motion or JavaScript.

## Decisions so far

- Original chapters stay untouched and in their original order; additions are labelled.
- Corrections are website-only, applied only when approved, and visibly marked.
- Visuals and animations are used wherever they teach; added prose stays concise.
- Kotlin first; other trees follow the same approach.

## Self-review (Kotlin tree)

- **Coverage:** all 23 pages blended. 92 visuals, 33 of them step-through animations. 3,521 original units preserved, 0 missing.
- **Length:** added reading prose is about 10% of the page. Short chapters gain the most (value classes, test dispatchers, callbackFlow: 35–45% including animation captions).
- **Splitting:** not needed. The longest chapters (JVM interop, extensions, functions) run about 4.3–5.3k words, which is 20–25 minutes, and the outline, story bands and per-section links make them navigable.
- **Devices:** 23 pages × 320/390/768/1280px pass: no horizontal scroll, no wide figures, all animations ready, no broken images. Light and dark themes checked.
- **Animation gaps closed:** Kotlin 2.4 (context-parameter resolution), Coroutines (cancellation then cleanup), JVM interop (where a Java null fails). Each was compiled and run first.
- **Accuracy:** claims the blends rely on were compiled and run locally. Errors found in the originals are logged in the triage, not edited.
- **Inline correction marks:** every single-line fix outside a table or code is highlighted where it stands; list and heading syntax stays outside the mark. Table-row and code fixes rely on the section note.
- **Codex review (2026-10-25):** all 11 findings reproduced and fixed: stricter preservation check, CH4/C24 amended code, VA2 and the cancellation/concurrency rows re-verdicted, three blend claims corrected (Flow buffering, JVM names, extension mocking), reduced motion now stops running animations, coroutine supplements labelled, correction markers built.

## Next steps

1. The owner reviews the exact texts in `reviews/corrections-with-edits.md` (and `.json`) for the 23 "approve with edit" rows, including the revised CH4 actor proposal. Then the owner approves `reviews/corrections-triage.md` (all 292 + 3 new reviewed: 199 approve, 23 approve with edit, 73 reject). Then set `"status": "approved"` (and amended text) in `content/corrections-*.json` and add the three new findings. The markers are already built; check each approved page after the build.
2. Repeat the blend for the next tree.

## Regression checks for the final review fixes

Run the static build and repository documentation checker as above. The build itself runs the preservation fixtures and checks all 23 pages; it does not claim to execute CSS. `scripts/browser_preservation.js` is a read-only async function for browser QA: evaluate the function and invoke it after the Content view has loaded. It returns the source path, checked text-node count, diagram count and a problem list. It neither changes the page nor opens disclosures. Run it on each generated Kotlin page and on disposable fixtures with hidden stylesheets, inherited zero opacity and falsely labelled diagram disclosures. Do not use a static membership count as evidence that browser visibility passed.

For Kotlin, run `python3 website/scripts/check_kotlin_examples.py`. This compiles the exact CH4 proposal from the JSON with the chapter’s command types and the fixture in `tests/CartActorRegression.kt`. It uses existing Kotlin 2.4.21 and kotlinx.coroutines/core-test 1.11.0 artifacts from local Gradle or Maven caches; it does not execute Gradle or download dependencies. `KOTLIN_COMPILER_CP` and `KOTLIN_TEST_CP` can point at explicitly installed compiler and test classpaths on another machine. A missing dependency is reported as a prerequisite, not a passing test.

The actor regression checks expected failure followed by recovery, shutdown while processing with 256 additional queued or suspended submissions, enqueue before startup followed by cancellation, cancellation before the first dispatch, construction after owner cancellation, fast rejection after shutdown, and unexpected-error reporting. The channel is cancelled from the worker Job’s completion handler, so shutdown does not depend on entering a coroutine body. Undelivered checkout replies are released by the channel callback; the executing request completes its own reply before propagating cancellation or unexpected failure. Expected I/O failure is the only locally recovered error in this teaching example. The owner remains responsible for the uncaught-error policy.

The same executable fixture verifies the value-class animation’s reuse example: a generic helper can place one boxed value in two list positions. Allocation counts must not be inferred from list length. The revised animation distinguishes boxed representation from fresh allocation and illustrates the shared reference explicitly.

CH4 is still a proposal. Tests compile it only in a temporary directory; they do not add approval statuses, edit original chapters or apply corrections to the active website. Keep the Markdown and JSON proposals in sync and re-run the checks when the wording changes. A successful check records the contracts exercised by those cases; it is not a blanket guarantee for every callback API, dispatcher, browser engine or physical device.
