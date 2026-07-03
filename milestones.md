# Milestones

Working tracker for the canonical-content fill-in plan. This file is for maintainers, not readers of the playbook.

Current state: the original canonical buildout, post-audit gap closure, Staff/Principal expansion, one-place depth expansion, and Kotlin folder structure cleanup are complete through G11.

---

## Operating Rules

1. **Breadth before deep specialization.** Keep the playbook useful across Android, Kotlin, distributed systems, mobile architecture, release engineering, security, observability, and staff-level leadership.
2. **SDE-1 to Staff clarity.** Canonical files should teach from first principles, define vocabulary, and still include Staff-level tradeoffs, failure modes, and review checklists.
3. **Single-canonical-owner rule.** When a concept crosses folders, one file owns the canonical treatment and other files cross-link to it. See [`CONTRIBUTING.md`](CONTRIBUTING.md).
4. **Structure discipline.** Prefer strengthening existing folders and indexes. Add new files only when the concept has no clean canonical owner.
5. **Commit by milestone.** Substantial roadmap work should land as scoped commits with neutral commit messages.

---

## Status Legend

- ✅ **done** — completed and committed
- 🟡 **partial** — started but not complete
- ⬜ **pending** — not started
- 🚫 **blocked** — needs a user/product decision

---

## Current Status

All tracked roadmap and structural cleanup milestones are complete.

| Track | Status | Notes |
|---|---:|---|
| M1-M23 initial buildout | ✅ | Original canonical files, platform breadth, reference architecture, polish, and KMP subfolder buildout complete |
| G1-G8 post-audit gap closure | ✅ | Reference architecture depth, leadership/platform depth, decision files, Kotlin practical depth, Android gaps, patterns/BFM, Ktor, Compose Navigation 3, KMP |
| G9 Staff/Principal expansion | ✅ | API evolution, sync protocol evolution, observability, release decision trees, testing strategy, platform engineering, security/privacy, architecture governance |
| G10 one-place depth expansion | ✅ | Correctness fixes, CS foundations, Android OS primitives, coroutine/Flow mastery, Compose/performance, data/networking/KMP production, distributed backend contracts |
| G11 Kotlin folder structure | ✅ | Flat Kotlin files moved into learning-domain subfolders; links updated; canonical ownership preserved |

Latest cleanup/audit commits:

- `26d8a97` — fixed one broken internal docs link and updated outdated Swift export wording.
- `fd420ce` — cleaned up this milestone tracker.

---

## Completed Foundation Milestones

### M1 — Bedrock Fundamentals ✅

Completed canonical fundamentals:

- `engineering-fundamentals/sync-vs-async.md`
- `engineering-fundamentals/latency-vs-throughput.md`
- `engineering-fundamentals/caching.md`
- `engineering-fundamentals/backpressure.md`
- `engineering-fundamentals/fault-tolerance.md`
- `engineering-fundamentals/time-and-clocks.md`

### M2 — Distributed Systems Core ✅

Completed:

- `distributed-systems/idempotency.md`
- `distributed-systems/cap-theorem.md`
- `distributed-systems/consistency-models.md`
- `distributed-systems/delivery-semantics.md`
- `distributed-systems/vector-clocks.md`
- `distributed-systems/crdts.md`
- `distributed-systems/consensus-basics.md`

### M3-M23 — Initial Playbook Buildout ✅

Completed major areas:

- Patterns and core principles
- Observability spine
- Kotlin language depth
- Android architecture, concurrency, data/DI, networking/security, performance, Compose, OS internals, build systems, observability, and testing
- Backend-for-mobile
- Mobile system design framework and worked problems
- Platform and SDK design
- Release engineering
- Reference architecture blueprints
- ADRs and decision files
- Computer science foundations and interview-oriented algorithms
- Security, leadership, platform, and career tracks
- Polish pass for remaining Kotlin, principles, glossary, learning paths, and cross-links

Historical detail lives in git history. This file now tracks current roadmap state instead of preserving every old checklist line.

---

## Completed Gap Closure

### G1-G8 — Post-Audit Depth Closure ✅

Completed:

- Reference architecture depth bump
- Career, leadership, and platform-engineering depth
- Decision file depth bump
- Kotlin practical interview depth
- Android subfolder gaps
- Patterns and backend-for-mobile depth bump
- Ktor vs Retrofit coverage
- Compose Navigation 3 coverage
- Kotlin Multiplatform subfolder with foundations, tooling, ecosystem, UI sharing, and production files

One intentional exclusion remains:

- `android/testing/journey-testing.md` was dropped by user decision and should not be reintroduced unless the user explicitly asks.

### G9 — Staff/Principal Depth Expansion ✅

Completed:

- Mobile API evolution
- Schema and sync protocol evolution
- Mobile observability architecture
- Release engineering decision trees
- Testing strategy at scale
- Platform engineering for mobile organizations
- Security and privacy threat modeling
- Principal architecture governance

### G10 — One-Place Depth Expansion ✅

Completed:

- G10a — correctness fixes
- G10b — computer science interview foundations
- G10c — Android OS fundamentals and app components
- G10d — coroutines, Flow, and concurrency mastery
- G10e — Compose, performance, and adaptive UI depth
- G10f — data, networking, security, and KMP production depth
- G10g — distributed systems and backend-for-mobile depth

Recent G10 commits:

- `2a30956` — correctness fixes and G10 plan
- `a325a1b` — computer science foundations
- `f42c742` — Android OS foundations
- `fe7610e` — coroutine/Flow mastery
- `7d0e46a` — Compose and performance strategy
- `98ebad2` — data, networking, and KMP production boundaries
- `1e19317` — distributed backend mobile contracts
- `26d8a97` — docs link and Swift export wording audit

---

## Completed Structural Cleanup

### G11 — Kotlin Subfolder Structure ✅

Goal: make the `kotlin/` tree match the learning domains already shown in `kotlin.md`, so learners can navigate Kotlin from basics to Staff-level runtime/concurrency depth without scanning one flat list of files.

Why it matters: Kotlin is one of the densest folders in the repo. The index now groups it conceptually, but the filesystem is still flat. That mismatch creates friction for readers and makes future Kotlin additions harder to place consistently.

Proposed target structure:

- `kotlin/language-core/`
  - `variables.md`
  - `functions.md`
  - `extensions.md`
  - `null-safety.md`
  - `data-classes.md`
  - `sealed-classes.md`
  - `delegation.md`
- `kotlin/type-system/`
  - `generics.md`
  - `variance.md`
- `kotlin/compiler-features/`
  - `inline-functions.md`
  - `reified-types.md`
- `kotlin/coroutines-and-flow/`
  - `coroutines.md`
  - `channels-and-select.md`
  - `flow-operators-and-backpressure.md`
  - `callbackflow-and-bridging-callbacks.md`
  - `coroutines-debugging-and-profiling.md`
  - `test-dispatchers-virtual-time.md`
- `kotlin/runtime-and-jvm/`
  - `memory-model.md`
  - `jvm-interop.md`
  - `bytecode.md`
- `kotlin/version-updates/`
  - `kotlin-2-4-update.md`

Execution checklist:

1. ✅ Move files with `git mv` so history is preserved.
2. ✅ Update `kotlin.md` links to the new subfolder paths.
3. ✅ Update all cross-folder links from Android, KMP, learning paths, README, and related files.
4. ✅ Update `CONTRIBUTING.md` canonical ownership map where it references `kotlin/coroutines-and-flow/coroutines.md`.
5. ✅ Run a full local Markdown link check across the repo.
6. ✅ Run `git diff --check`.
7. ✅ Commit as a dedicated structural cleanup commit.

Non-goals:

- Do not rewrite Kotlin topic content during the move unless a link or ownership note must change.
- Do not create new Kotlin topics in this milestone.
- Do not change Kotlin canonical ownership; this is navigation cleanup, not content redefinition.

Validation result:

- Full local Markdown link check: `0` broken links across `1,606` local links.

---

## Known Non-Roadmap Cleanup

These are not active milestone blockers, but they are worth handling in a future polish pass:

- `reference-architectures/offline-first-app.md` still has product-specific threshold and convergence-window choices to resolve in a future polish pass.
- External web links have not been fully crawled. Internal Markdown links were checked after G10 and reported `0` broken links across `1,569` local links.
- A full human grammar/technical review across all 285 Markdown files is still stronger than automated grep checks.

---

## How To Update This File

After future roadmap work:

1. Add a short milestone section only if there is a real new roadmap track.
2. Mark status honestly: ✅, 🟡, ⬜, or 🚫.
3. Link the canonical owner files instead of duplicating long checklists.
4. Add commit hashes for substantial completed tracks.
5. Remove stale "current execution" notes as soon as the work is committed.
