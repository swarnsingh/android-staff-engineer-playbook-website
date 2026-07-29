# Contributing

These are the rules that keep this repo coherent as it grows to hundreds of files. They are not stylistic preferences — they are the structural commitments that prevent the repo from collapsing into entropy.

Read this before adding any file.

---

## The Four Kinds of Files

Every file is exactly one of:

| Kind | Purpose | Template |
|---|---|---|
| **Canonical** | The single source of truth for a concept | [`templates/canonical.md`](templates/canonical.md) |
| **Application** | Applies a canonical concept to a concrete system | [`templates/application.md`](templates/application.md) |
| **Decision** | A reusable comparison with decision criteria and contextual defaults | [`templates/decision.md`](templates/decision.md) |
| **Blueprint** | A complete end-to-end reference architecture | [`templates/blueprint.md`](templates/blueprint.md) |

If a new file doesn't fit one of these, it doesn't belong in this repo.

---

## Rule 1 — Single Canonical Owner

Every concept lives in exactly one file. Other files cross-reference it; they do not re-explain it.

Example:

```text
Idempotency

Canonical owner:
  distributed-systems/idempotency.md

Referenced from:
  mobile-system-design/offline-sync.md
  mobile-system-design/file-downloader.md
```

When writing an application file, if you find yourself explaining what a concept *is*, stop and link to the canonical owner instead.

This rule is non-negotiable. It is what makes hundreds of files maintainable.

---

## Rule 2 — Structure Freeze

The folder structure is fixed. New knowledge fits into an existing tree.

- Do not create new top-level folders.
- Do not rename or reorganize folders.
- Do not introduce parallel folders that overlap with existing ones.

When new knowledge appears:

1. Find its canonical owner. Add it there.
2. If the canonical owner doesn't exist yet, create that file (in the right tree).
3. Cross-reference from other relevant files.

---

## Canonical Ownership Map

When the same word could plausibly live in multiple trees, this table pins the single home. Keep it in sync as new contested concepts emerge.

| Concept | Canonical owner | Cross-references from |
|---|---|---|
| Complexity analysis / Big-O | `engineering-fundamentals/complexity-analysis.md` | `computer-science/big-o.md` (bridge file linking back) |
| Coroutines — language mechanics | `kotlin/coroutines-and-flow/coroutines.md` | `android/concurrency/coroutines-under-the-hood.md` (platform application) |
| App Bundles & Dynamic Delivery | `release-engineering/app-bundles.md` | (cross-referenced from `android.md` index) |
| Release strategy | `release-engineering/release-strategy.md` | `mobile-system-design.md` cross-links |
| Image loading | `mobile-system-design/image-loading.md` (single entry) | — |
| State machines — mechanics | `engineering-fundamentals/state-machines.md` | All application FSMs link here |
| State machines — pattern | `patterns/state.md` | Cross-link both ways |
| Observability concepts | `observability/` tree | `android/observability/` is application-only |
| Distributed tracing | `observability/distributed-tracing.md` | `distributed-systems/distributed-tracing.md` (bridge file) |
| Idempotency | `distributed-systems/idempotency.md` | `mobile-system-design/` |
| Determinism — heuristic | `principles/determinism.md` | Cross-link to mechanics |
| Determinism — mechanics | `engineering-fundamentals/` | Cross-link to principle |

## General Disambiguation Rule

When a word could live in multiple trees:

- **Fundamental** = mechanics (how it works, the substrate)
- **Pattern** = implementation (a reusable shape that solves a class of problems)
- **Principle** = decision heuristic (what a Staff engineer reaches for when choosing)
- **Application** = a specific use in a concrete system

Same concept, multiple angles — link between them, never duplicate.

---

## Conventions

### File naming

- All filenames are **kebab-case**: `state-machines.md`, `app-startup.md`, `deterministic-resume.md`
- No spaces, no underscores, no PascalCase
- Decision files: plain kebab-case named for the comparison, co-located in the tree they inform → `backend-for-mobile/sse-vs-websockets.md`. No numeric prefixes. Project-specific ADRs should live in the consuming project's decision log, because status, owner, and date cannot be truthfully generalized in this educational repository.

### Cross-references

- Inter-file links are **relative paths**, GitHub-rendered
- Examples:
  - From `mobile-system-design/offline-sync.md` → `../engineering-fundamentals/state-machines.md`
- Section anchors use GitHub's auto-generated kebab-case slugs: `../patterns/retry.md#exponential-backoff`
- Never use absolute URLs to point inside the repo

### Diagrams, images, and attribution

Visuals must teach the same model as the surrounding text. If a diagram and the prose disagree, update them together in the same pull request; a visually attractive contradiction is still a documentation defect.

Use this order of preference:

1. **Mermaid** for flows, sequences, state machines, dependency graphs, timelines, and system boundaries. It is editable, diffable, and rendered by GitHub.
2. **Local SVG** only when Mermaid cannot express the idea clearly. Keep text selectable where practical and preserve the editable source when the SVG was exported from another tool.
3. **Local PNG, JPEG, or WebP** only when the appearance of a real tool or interface is itself part of the lesson, such as a Perfetto trace or Play Console control. Do not use raster images for architecture that can be expressed as Mermaid or SVG.
4. **ASCII** only when fixed-width source layout is the subject. Migrate existing architecture ASCII to Mermaid when touching it.

Additional requirements:

- Never hotlink an image. Store reusable assets under `assets/<knowledge-tree>/` and reference them with a relative path.
- Give every image meaningful alt text. Follow every Mermaid diagram with a short plain-language takeaway; GitHub rendering and assistive-technology support must not be the only way to learn the concept.
- Do not rely on color alone. Labels, line styles, or shapes must carry the meaning in both light and dark themes.
- Keep one diagram focused on one question. Split a diagram when labels become smaller than the surrounding prose or when unrelated flows cross.
- Use current primary sources for technical behavior. A blog can improve presentation or provide an experience report, but it cannot override Android, Kotlin, AOSP, IETF, or library documentation.
- Prefer an original diagram validated against primary sources. Copy or adapt an external visual only when the specific asset is licensed for reuse.
- Record every local non-Mermaid asset in [`assets/ATTRIBUTION.md`](assets/ATTRIBUTION.md): local path, page where used, creator, source URL, license, changes, and retrieval date. Mark repository-authored assets as original. Page-level licenses do not automatically cover third-party media embedded on that page.
- Put a `Source:` or `Validated against:` link next to a visual when its accuracy depends on versioned platform or API behavior. Track fast-moving claims through the existing Currency Watchlist rather than adding decorative verification dates everywhere.
- Run `python3 scripts/check_visuals.py --renderer "npx --yes @mermaid-js/mermaid-cli@11.16.0"` before pushing a visual change.

### Probing questions and answer keys

- Probing questions are retrieval and reasoning checks, not links that send the reader elsewhere to discover the basic answer.
- Put a concise `## Answer Key` after `## Probing Questions` in the same file. Number answers in the same order as the questions.
- Explain the expected reasoning, decision criteria, or failure mode. Do not copy the chapter into the answer key and do not paste official documentation.
- Cite current primary sources in `## Further Reading` for claims about platform behavior, policies, versions, compiler behavior, or APIs. The repository teaches the answer; the official source proves and deepens it.
- When updating an older topic that has questions but no key, add the key as part of that change. Existing files are migrated incrementally and tracked as documentation debt.

### Guided reading sequences

- Every top-level knowledge-tree index (`android.md`, `kotlin.md`, `security.md`, and peers) must contain a `## Guided Reading Sequence`.
- The sequence is normative: number phases and topics in prerequisite order. A reader following links top to bottom should not need knowledge introduced only later.
- State prerequisites that live in another tree, identify optional/specialist branches, and finish with a clear next tree or checkpoint.
- Keep the complete catalog in the same parent index. Do not create a second unordered list that conflicts with the guided order.
- When adding a topic, insert it at the correct learning point instead of appending it for convenience. Update [`learning-paths.md`](learning-paths.md) only when the whole-repository phase order changes.

---

## Staleness Strategy

Do **not** add manual "Last verified" footers. They lie within a quarter.

Instead:

- **Canonical files** are written at the conceptual level that does not go stale. "How a coroutine suspends" is timeless; "the exact behavior of `LaunchedEffect` in Compose 1.7" is not.
- **Application files** are where version-specific detail lives, and are explicitly expected to be revised as Android, Compose, Kotlin, and library versions evolve. Revision is the normal lifecycle of an application file, not a sign of decay.

If a canonical file finds itself naming a specific version, that detail belongs in an application file instead.

**Currency watchlist.** Application files whose claims are *guaranteed* to move — version numbers, platform deadlines, API stability levels — are tracked in the [Currency Watchlist in `milestones.md`](milestones.md#currency-watchlist) with their primary source and a last-checked date. That table (maintainer-facing, not reader-facing footers) is the re-verification queue: work through stale rows quarterly, re-verify against the listed source, and update the date. The CI script prints a non-failing reminder when a row passes 180 days.

**Release digests** (e.g. `kotlin/version-updates/kotlin-2-4-update.md`) are **Application files** under this strategy: they exist precisely to hold version-specific detail, and they follow the application lifecycle — revised or superseded as releases land. When a feature described in a digest becomes stable, long-lived guidance about it graduates into the owning canonical file; the digest keeps only the release-delta framing.

---

## How to Add a New File

1. **Identify the kind.** Canonical, application, decision, or blueprint?
2. **Find the canonical owner.** Use the Canonical Ownership Map above. If you're adding the canonical, make sure no other file is already claiming the role.
3. **Copy the template** from `templates/` into the right folder.
4. **Rename** the file in kebab-case.
5. **Fill it in.** For canonical files, follow all relevant sections. For application files, link to the canonical owner instead of redefining.
6. **Cross-reference.** Add links from related files to the new one, and vice versa.
7. **Place it in the guided sequence.** Add it to the owning top-level index at the correct prerequisite point, not merely at the end.

---

## Quality Gates (CI)

Every PR runs `python3 scripts/check_docs.py` via GitHub Actions ([`.github/workflows/quality.yml`](.github/workflows/quality.yml)). It fails the build on:

1. **Broken internal links and anchors** — a relative target or heading fragment doesn't exist.
2. **Stale redirects** — link text naming `foo.md` while the target is `bar.md`.
3. **Unfinished content** — literal `*TODO: …*` or standalone `TBD` markers.
4. **Near-empty files** — non-stub content files under 400 words (expand them, or allowlist in the script with a reason).
5. **Learning-order integrity** — every knowledge-tree index has a guided sequence and every topic appears in its owning index.
6. **Visual integrity** — Mermaid blocks are rendered, local images must exist under `assets/`, alt text is required, hotlinks are rejected, and reused assets must appear in the attribution registry.
7. **External-link health** — a scheduled and manually runnable job checks cited web resources. Definitive 404/410 responses fail; access controls and transient network failures are reported without making ordinary pull requests flaky.

Run it locally before pushing. A green check is a merge precondition, not a suggestion.

**Fact verification.** Any claim about compiler/runtime/API behavior, versions, or platform policy must be verified against current official documentation or source (developer.android.com, kotlinlang.org, AOSP) at writing time — not written from memory. Cite the sources in Further Reading.

---

## Writing Style

- Short paragraphs
- Avoid academic language
- Diagrams over text where they help
- Examples over theory
- Build intuition first, then expertise
- Always explain tradeoffs, failures, and production concerns
