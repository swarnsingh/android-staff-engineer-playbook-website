# Contributing

These are the rules that keep this repo coherent as it grows to hundreds of files. They are not stylistic preferences — they are the structural commitments that prevent the repo from collapsing into entropy.

Read this before adding any file.

---

## The Four Kinds of Files

Every file is exactly one of:

| Kind | Purpose | Template |
|---|---|---|
| **Canonical** | The single source of truth for a concept | [`templates/canonical.md`](templates/canonical.md) |
| **Application** | Applies a canonical concept to a concrete system (AirBridge, BizBrew, etc.) | [`templates/application.md`](templates/application.md) |
| **Decision** | An ADR — recorded tradeoff and choice | [`templates/decision.md`](templates/decision.md) |
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
  airbridge/deterministic-resume.md
```

When writing an application file, if you find yourself explaining what a concept *is*, stop and link to the canonical owner instead.

This rule is non-negotiable. It is what makes 400 files maintainable.

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
| Complexity analysis / Big-O | `engineering-fundamentals/complexity-analysis.md` | `computer-science/big-o.md` (short stub linking back) |
| Coroutines — language mechanics | `kotlin/coroutines.md` | `android/coroutines.md` |
| Coroutines — Android platform usage | `android/coroutines.md` (application file) | All Android topics referencing async |
| App Bundles & Dynamic Delivery | `release-engineering/app-bundles.md` | `android/app-bundles.md` (short stub) |
| Release strategy | `release-engineering/release-strategy.md` | `mobile-system-design.md` cross-links |
| Image loading | `mobile-system-design/image-loading.md` (single entry) | — |
| State machines — mechanics | `engineering-fundamentals/state-machines.md` | All application FSMs link here |
| State machines — pattern | `patterns/state.md` | Cross-link both ways |
| Observability concepts | `observability/` tree | `android/observability/` is application-only |
| Distributed tracing | `observability/distributed-tracing.md` | `distributed-systems/distributed-tracing.md` (stub) |
| Idempotency | `distributed-systems/idempotency.md` | `airbridge/`, `mobile-system-design/` |
| Determinism — heuristic | `principles/determinism.md` | Cross-link to mechanics |
| Determinism — mechanics | `engineering-fundamentals/` | Cross-link to principle |

## General Disambiguation Rule

When a word could live in multiple trees:

- **Fundamental** = mechanics (how it works, the substrate)
- **Pattern** = implementation (a reusable shape that solves a class of problems)
- **Principle** = decision heuristic (what a Staff engineer reaches for when choosing)
- **Application** = a specific use in AirBridge, BizBrew, or another concrete system

Same concept, multiple angles — link between them, never duplicate.

---

## Conventions

### File naming

- All filenames are **kebab-case**: `state-machines.md`, `app-startup.md`, `deterministic-resume.md`
- No spaces, no underscores, no PascalCase
- ADRs: zero-padded three-digit prefix → `adr/003-sse-vs-websockets.md`

### Cross-references

- Inter-file links are **relative paths**, GitHub-rendered
- Examples:
  - From `airbridge/deterministic-resume.md` → `../distributed-systems/idempotency.md`
  - From `mobile-system-design/offline-sync.md` → `../engineering-fundamentals/state-machines.md`
- Section anchors use GitHub's auto-generated kebab-case slugs: `../patterns/retry.md#exponential-backoff`
- Never use absolute URLs to point inside the repo

### Diagrams

- Mermaid first, ASCII second
- No PNG, screenshots, or external image hosts
- Must render in GitHub

---

## Staleness Strategy

Do **not** add manual "Last verified" footers. They lie within a quarter.

Instead:

- **Canonical files** are written at the conceptual level that does not go stale. "How a coroutine suspends" is timeless; "the exact behavior of `LaunchedEffect` in Compose 1.7" is not.
- **Application files** are where version-specific detail lives, and are explicitly expected to be revised as Android, Compose, Kotlin, and library versions evolve. Revision is the normal lifecycle of an application file, not a sign of decay.

If a canonical file finds itself naming a specific version, that detail belongs in an application file instead.

---

## How to Add a New File

1. **Identify the kind.** Canonical, application, decision, or blueprint?
2. **Find the canonical owner.** Use the Canonical Ownership Map above. If you're adding the canonical, make sure no other file is already claiming the role.
3. **Copy the template** from `templates/` into the right folder.
4. **Rename** the file in kebab-case.
5. **Fill it in.** For canonical files, follow all relevant sections (omit the optional anchor-example sections if not applicable). For application files, link to the canonical owner instead of redefining.
6. **Cross-reference.** Add links from related files to the new one, and vice versa.
7. **Update the top-level TOC** for the tree the file belongs to.

---

## Writing Style

- Short paragraphs
- Avoid academic language
- Diagrams over text where they help
- Examples over theory
- Build intuition first, then expertise
- Always explain tradeoffs, failures, and production concerns
