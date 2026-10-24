# Reader Website: Build Guide and Handover

This folder builds the reader website for the playbook. Read [`../content-rulebook.md`](../content-rulebook.md) first, especially sections 16–18: the original chapters are read-only, every page must contain its original chapter in full, and the website adds a clearly labelled teaching layer on top. This guide explains how the build works and where the work stands, so another model or person can continue it.

## Current state

- **Branch:** `claude/reader-website-kotlin` (built on Codex's snapshot `60b8c2a` on `codex/reader-website`). Nothing is pushed or merged without the owner's approval.
- **Scope:** the Kotlin tree — `kotlin.md` plus all 22 Kotlin chapters render as pages.
- **Originals:** byte-identical to `main`. Do not edit them.
- **Corrections:** 292 proposals from Codex's automated audits sit in `content/corrections-*.json`. None is approved, so none is applied. They still need sorting into factual errors, needed updates and wording-only changes (drop the last), then the owner's approval per item.

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
| coroutines-and-flow/coroutines | Codex fragments in `content/coroutine-*.html` | Partly blended; needs a `.blend` |
| coroutines-and-flow/channels-and-select | — | To do |
| coroutines-and-flow/flow-operators-and-backpressure | — | To do |
| coroutines-and-flow/callbackflow-and-bridging-callbacks | — | To do |
| coroutines-and-flow/coroutines-debugging-and-profiling | — | To do |
| coroutines-and-flow/test-dispatchers-virtual-time | — | To do |
| runtime-and-jvm/memory-model | — | To do |
| runtime-and-jvm/jvm-interop | — | To do |
| runtime-and-jvm/bytecode | — | To do |
| version-updates/kotlin-2-4-update | — | To do |

Update this table whenever a chapter changes state.

## Build and preview

```bash
python3 -m venv .venv && .venv/bin/pip install -r website/requirements.txt
.venv/bin/python website/scripts/build.py
python3 -m http.server 4174 --bind 127.0.0.1 --directory website/dist
```

Run from the repository root. The build writes `website/dist/` (ignored by git), renders each Mermaid diagram with `npx @mermaid-js/mermaid-cli` (cached in `website/.cache/`; pass `--skip-diagrams` to skip), and then runs the preservation check. It exits non-zero if any original content is missing. Set `SITE_BASE=/android-staff-engineer-playbook/` to build for a project path such as GitHub Pages.

## How a page is assembled

`scripts/build.py` parses each original chapter with markdown-it and renders it into `templates/reader.html`. Sections are grouped into six parts (`PARTS` in the script) by their headings; parts only move forward. Then it adds, in order: the chapter's blend fragments, the Codex coroutine fragments for the coroutines page, and approved corrections (none yet). `scripts/check_preservation.py` compares every original heading, paragraph, list item, table row, code block and diagram source with the page's Content tab.

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

## Next steps

1. Blend the remaining Kotlin chapters, verifying added code and claims.
2. Self-review every page for length, splitting and visual coverage.
3. Sort the 292 corrections and get the owner's approval.
4. Replace the Codex audit notes in `reviews/` with the reviewed corrections table.
