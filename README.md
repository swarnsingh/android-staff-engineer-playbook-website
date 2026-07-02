# Android Staff Engineer Playbook

A long-term knowledge base for Android and Mobile Platform Engineering. Not an interview-cramming repo — a 1-2 year study guide aimed at Senior → Staff Mobile Platform Engineer depth.

> If a Senior Android engineer studies this repository end-to-end and understands every topic deeply, they should be able to operate at Staff Mobile Platform Engineer level.

---

## Philosophy

Optimize for:

- **Depth.** First principles over surface coverage.
- **Mental models.** Understanding why a system exists before how it works.
- **Production engineering.** Failure modes, observability, rollout — not just happy paths.
- **Systems thinking.** How decisions ripple across architecture, organization, and time.
- **Long-term maintainability.** This repo is built to grow for 10 years without collapsing into entropy.

Do NOT optimize for: interview cramming, LeetCode patterns, flashcards, cheatsheets.

The repo should feel like a combination of:

- A university textbook
- A production engineering handbook
- A Staff Engineer playbook
- An Android systems encyclopedia

---

## How This Repo Is Organized

Every file is exactly one of four kinds. Each kind has its own template in [`templates/`](templates/).

| Kind | What it is | Example | Template |
|---|---|---|---|
| **Canonical** | The single source of truth for a concept | `distributed-systems/idempotency.md` | [`templates/canonical.md`](templates/canonical.md) |
| **Application** | Applies a canonical concept to a concrete system | `mobile-system-design/offline-sync.md` | [`templates/application.md`](templates/application.md) |
| **Decision** | A recorded tradeoff and choice (ADR) | `backend-for-mobile/sse-vs-websockets.md` | [`templates/decision.md`](templates/decision.md) |
| **Blueprint** | A complete end-to-end system reference | `reference-architectures/e-commerce-app.md` | [`templates/blueprint.md`](templates/blueprint.md) |

Two rules govern the whole repo. Both live in [`CONTRIBUTING.md`](CONTRIBUTING.md):

1. **Single Canonical Owner.** Every concept lives in exactly one file. Other files cross-reference it.
2. **Structure Freeze.** Folder structure is fixed. New knowledge fits into an existing tree; it never spawns a new pillar.

---

## Where to Start

- New to the repo? Read [`CONTRIBUTING.md`](CONTRIBUTING.md) first — it's short and explains how files relate.
- Looking for a study sequence? See [`learning-paths.md`](learning-paths.md).
- Need a term defined? See [`glossary.md`](glossary.md).

## The Knowledge Trees

Each top-level file is a table of contents for its tree. Start with whichever matches the question you're answering.

**Foundations**
- [`engineering-fundamentals.md`](engineering-fundamentals.md) — timeless concepts (state machines, backpressure, fault tolerance)
- [`computer-science.md`](computer-science.md) — complexity, data structures, algorithms, and their Android/Kotlin implications
- [`principles.md`](principles.md) — decision heuristics
- [`patterns.md`](patterns.md) — design and resilience patterns

**Platform & Language**
- [`android.md`](android.md) — Android platform, top to bottom
- [`kotlin.md`](kotlin.md) — language design and internals

**System Design**
- [`mobile-system-design.md`](mobile-system-design.md) — the design framework + worked problems + platform/SDK design
- [`reference-architectures.md`](reference-architectures.md) — blueprints for whole apps

**Infrastructure & Operations**
- [`distributed-systems.md`](distributed-systems.md) — consistency, idempotency, consensus
- [`backend-for-mobile.md`](backend-for-mobile.md) — BFFs, API evolution, transport protocols, push vs poll
- [`release-engineering.md`](release-engineering.md) — rollouts, kill switches, CI/CD
- [`observability.md`](observability.md) — logging, metrics, tracing, SLOs
- [`platform-engineering.md`](platform-engineering.md) — internal platforms, developer experience
- [`security.md`](security.md) — threats, privacy, compliance

**Career & Decisions**
- [`leadership.md`](leadership.md) — incident response, technical leadership
- [`career.md`](career.md) — senior → staff progression

Decision files (the `Decision` kind in the table above) live alongside the topic they decide. For example, `backend-for-mobile/sse-vs-websockets.md` decides a transport choice and sits in the BFM tree, not in a separate `adr/` folder. This co-location keeps the decision next to the canonical concept it relates to. See [`templates/decision.md`](templates/decision.md) for the template.

---

## Technical Constraints

- Raw Markdown only. Mermaid and ASCII diagrams. No PNG, no HTML, no MDX.
- Must render correctly in GitHub.
- File naming: kebab-case throughout.
- Cross-references: relative GitHub-rendered links.

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the full convention list.

---

## License

This work is licensed under a [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-nc-sa/4.0/).

> [!WARNING]
> **© 2026 Swaran Singh Aulakh. All Rights Reserved.**
> 
> You are free to read, share, and adapt this material for personal or educational use, provided you give appropriate credit. **Commercial use, including reproducing this content for paid courses, books, or monetized platforms, is strictly prohibited without explicit written permission.**
