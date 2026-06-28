# Milestones

Working tracker for the canonical-content fill-in plan. This file is for the writer, not the reader of the repo. Update as work progresses.

---

## Operating Rules

These are the constraints every milestone is shaped by. If a future session forgets these, the work will drift.

1. **Breadth over depth.** Fill foundational canonical files across many trees before going deep into any single system. The repo's value as a Staff study path comes from broad foundations, not exhaustive coverage of one example.
2. **Quality bar: SDE-1 to Staff.** Every canonical file must be readable by someone who has never seen the concept and still useful to a Staff engineer. Teach from first principles. Define vocabulary on first use. Use code examples (Kotlin preferred) where they sharpen explanation.
4. **Single-canonical-owner rule still applies.** When in doubt, consult [`CONTRIBUTING.md`](CONTRIBUTING.md) — the Canonical Ownership Map pins contested concepts.
5. **Structure freeze still applies.** No new folders. New content fills existing trees.

---

## Status Legend

- ✅ **done** — file is full canonical-quality content, committed
- 🟡 **partial** — some files in the milestone are done, others pending
- ⬜ **pending** — milestone not yet started
- 🚫 **blocked** — needs user decision before starting

---

## Done So Far

| File | Kind | Commit |
|---|---|---|
| `engineering-fundamentals/state-machines.md` | canonical | `4d7cb3c` then refined `7b7a8f1` |
| `distributed-systems/idempotency.md` | canonical | `371fd62` |
| `adr/003-sse-vs-websockets.md` | decision | `371fd62` (kept as-is) |
| `reference-architectures/offline-first-app.md` | blueprint | `371fd62` |
| `engineering-fundamentals/sync-vs-async.md` | canonical | M1 batch |
| `engineering-fundamentals/latency-vs-throughput.md` | canonical | M1 batch |
| `engineering-fundamentals/caching.md` | canonical | M1 batch |
| `engineering-fundamentals/backpressure.md` | canonical | M1 batch |
| `engineering-fundamentals/fault-tolerance.md` | canonical | M1 batch |
| `engineering-fundamentals/time-and-clocks.md` | canonical | M1+M2 session |
| `distributed-systems/cap-theorem.md` | canonical | M2 session |
| `distributed-systems/consistency-models.md` | canonical | M2 session |
| `distributed-systems/delivery-semantics.md` | canonical | M2 session |
| `distributed-systems/vector-clocks.md` | canonical | M2 session |
| `distributed-systems/crdts.md` | canonical | M2 session |
| `distributed-systems/consensus-basics.md` | canonical | M2 session |

Plus: README, CONTRIBUTING, 4 templates, 17 tree-level TOCs, 207 stubs.

---

## Active Milestones (in execution order)

Each milestone is roughly one session's worth of work for a moderately-sized batch. Bigger canonical files (e.g., `caching.md`, `coroutines.md`) may take a session each on their own.

### M1 — Bedrock Fundamentals ✅

6 canonical files. The substrate every later file links to. All done.

- ~~`engineering-fundamentals/sync-vs-async.md`~~
- ~~`engineering-fundamentals/latency-vs-throughput.md`~~
- ~~`engineering-fundamentals/caching.md`~~
- ~~`engineering-fundamentals/backpressure.md`~~
- ~~`engineering-fundamentals/fault-tolerance.md`~~
- ~~`engineering-fundamentals/time-and-clocks.md`~~

### M2 — Distributed Systems Core ✅

All 7 canonical files done (including idempotency.md from earlier).

- ~~`distributed-systems/idempotency.md`~~
- ~~`distributed-systems/cap-theorem.md`~~
- ~~`distributed-systems/consistency-models.md`~~
- ~~`distributed-systems/delivery-semantics.md`~~
- ~~`distributed-systems/vector-clocks.md`~~
- ~~`distributed-systems/crdts.md`~~
- ~~`distributed-systems/consensus-basics.md`~~

### M3 — Patterns + Key Principles ✅

18 canonical files. The core structural tools.

- ~~`patterns/repository.md`~~
- ~~`patterns/adapter.md`~~
- ~~`patterns/factory.md`~~
- ~~`patterns/strategy.md`~~
- ~~`patterns/observer.md`~~
- ~~`patterns/state.md`~~
- ~~`patterns/builder.md`~~
- ~~`patterns/decorator.md`~~
- ~~`patterns/command.md`~~
- ~~`patterns/circuit-breaker.md`~~
- ~~`patterns/retry.md`~~
- ~~`patterns/saga.md`~~
- ~~`principles/simplicity.md`~~
- ~~`principles/determinism.md`~~
- ~~`principles/design-for-failure.md`~~
- ~~`principles/make-invalid-states-impossible.md`~~
- ~~`principles/prefer-deletion.md`~~
- ~~`principles/composition-over-inheritance.md`~~

Remaining 5 principles (least-knowledge, single-responsibility, locality-of-reference, optimize-for-change, progressive-disclosure) can land in M20 or piecewise.

### M4 — Observability Spine ✅

9 canonical files. Unlocks `android/observability/*` application files later.

- ~~logging, structured-logging, metrics, tracing, distributed-tracing, slis, slos, error-budgets, alerting, dashboards~~ (10 if you count distributed-tracing as full canonical here)

### M5 — Kotlin Language Depth ✅

10 canonical files. Deep JVM knowledge for performance and API design.

- ~~coroutines, null-safety, generics, variance, inline-functions, reified-types, sealed-classes, data-classes, delegation, memory-model~~

Variables, functions, extensions, jvm-interop, bytecode can land in a smaller follow-up.

### M6 — Android Architecture + Lifecycle ✅

8 canonical files.

- ~~activity, fragment, viewmodel, navigation, savedstatehandle, process-death-and-state-restoration, structured-concurrency, flow~~

### M7 — Android Concurrency ✅

7 canonical files. How to execute work safely in a hostile, battery-optimized OS.

- ~~coroutines-under-the-hood, threads-and-looper, shared-flow-and-state-flow, synchronization-and-mutex, services, workmanager, battery-optimizations~~

### M8 — Android Data & DI ✅

4 canonical files. Managing local state and dependency graphs.

- ~~room, datastore, paging, dependency-injection~~

### M9 — Android Networking & Security ✅

3 canonical files. Communicating with the outside world securely.

- ~~retrofit-and-okhttp, graphql, security-and-keystore~~

### M10 — Android Performance ✅

5 canonical files. Tracking down and eliminating dropped frames and memory bloat.

- ~~jank, anrs, memory-management-and-leaks, baseline-profiles, app-size-and-r8~~

### M11 — Android Compose ✅

4 canonical files. The paradigm shift from Imperative XML to Declarative State functions.

- ~~recomposition-and-state, modifiers-and-layout, side-effects, compose-navigation~~

### M12 — Android OS Internals & Build ✅

7 canonical files. The absolute deepest layer of Android and observability.

- ~~the-binder, the-zygote, art-and-dalvik, gradle-and-build-systems~~
- ~~`android/observability/new-relic.md` (application), `android/observability/crash-monitoring.md` (application), `android/observability/logging.md` (application)~~

### M13 — Backend-for-Mobile ✅

6 canonical files. The bridge between the device and the cloud.

- ~~bff-pattern, api-design-for-mobile, transport-protocols, push-vs-poll-vs-sse-vs-websockets, rate-limiting, data-formats~~

### M14 — Mobile System Design — Framework + NFRs ✅

7 canonical files. How to answer "Design WhatsApp" without failing.

- ~~design-framework, non-functional-requirements, performance, accessibility, localization-and-internationalization, security-and-privacy, versioning-and-backward-compatibility~~

### M15 — Worked Design Problems (Part 1) ✅

8 architecturally distinct problems.

- ~~offline-sync, chat-messaging, file-downloader, image-loading, notification-system, payment-flow, pagination, search~~

### M16 — Worked Design Problems (Part 2) ✅

8 remainder.

- ~~news-feed, google-maps-location-system, youtube-video-streaming, stock-trading-app, ride-hailing, caching-library, typeahead-autocomplete-search, collaborative-editing~~

### M17 — Platform & SDK Design ✅

9 canonical files.

- ~~feature-flags-and-remote-config, telemetry-sdk, analytics-sdk, app-startup, authentication, push-notifications, deep-links-and-universal-links, a-b-testing-infrastructure, experimentation-platform~~

### M18 — Release Engineering ✅

8 canonical files.

- ~~staged-rollouts, kill-switches, crash-rate-gating, ci-cd-for-mobile, code-signing, play-store-internals, app-bundles, release-strategy~~

### M19 — Reference Architecture Blueprints ✅ (offline-first-app.md done)

8 blueprints total.

- ~~consumer-app, merchant-app, banking-app, e-commerce-app, ride-hailing-app, social-media-app, video-streaming-app~~

### M20 — ADRs ✅

5 generally-applicable ADRs.

- ~~001 — MVVM vs MVI~~
- ~~004 — Room vs DataStore~~
- ~~005 — GraphQL vs REST~~
- ~~006 — Monolith vs Modularization~~
- ~~007 — Hilt vs Manual DI~~



### M21 — Computer Science (lean) ✅

4 canonical files. Deliberately small per spec.

- ~~hashing, trees, graphs, system-complexity~~

### M22 — Security, Leadership, Platform, Career ✅

All files across these four non-technical domains have been successfully generated and cross-linked.

### M23 — Polish ✅

- Fill the remaining 5 lesser-priority principles files (least-knowledge, single-responsibility, locality-of-reference, optimize-for-change, progressive-disclosure)
- Fill remaining Kotlin smaller files (variables, functions, extensions, jvm-interop, bytecode)
- Populate `glossary.md` entries as canonical files are written
- Write actual content for `learning-paths.md` sequences
- Cross-reference audit: walk every canonical file's Further Reading section, verify links work

---

## Gaps Identified (Post-Audit, 2026-06)

A folder-by-folder audit after M22 surfaced content that was checked off as ✅ but doesn't meet the SDE-1-to-Staff bar. Tracking here so future sessions don't re-discover the same debt.

### G1 — Reference architectures (thin) 🟡

7 of 8 blueprints are 54-70 lines; only `offline-first-app.md` (250) is full-depth. Each blueprint should be ~350-450 lines with: architectural signature, HLD diagram, per-layer blueprint, top 5 scaling bottlenecks with code, tech summary, cross-references, further reading.

- `reference-architectures/banking-app.md` (55 lines → target 400)
- `reference-architectures/consumer-app.md` (55 → 400)
- `reference-architectures/e-commerce-app.md` (62 → 400)
- `reference-architectures/merchant-app.md` (54 → 400)
- `reference-architectures/ride-hailing-app.md` (63 → 400)
- `reference-architectures/social-media-app.md` (70 → 400)
- `reference-architectures/video-streaming-app.md` (59 → 400)

### G2 — Career, leadership, platform-engineering (thin) ⬜

15 files at 30-44 lines each. Narrative is present; concrete artifacts (RFC templates, COE templates, design-review rubrics, Gradle convention plugin code, BoM publishing pipelines, real promo packets) are absent. Target ~250-350 lines per file with real templates inline.

- `career/` 5 files
- `leadership/` 5 files
- `platform-engineering/` 5 files

### G3 — Thin ADRs ⬜

5 ADRs at 40-50 lines each. ADR 003 (115) and 008 (152) set the bar. Pattern: context, alternatives, decision, consequences, plus enough code that a reader can verify the decision was applied.

- `adr/001-mvvm-vs-mvi.md` (41 → 180)
- `adr/004-room-vs-datastore.md` (39 → 180)
- `adr/005-graphql-vs-rest.md` (42 → 180)
- `adr/006-monolith-vs-modularization.md` (43 → 180)
- `adr/007-hilt-vs-manual-di.md` (43 → 180)

### G4 — Kotlin files missing bytecode evidence ⬜

8 files have decent length but no `javap -c` output. Pattern established in `bytecode.md`, `inline-functions.md`, `reified-types.md`.

- `kotlin/coroutines.md` — add suspend state-machine bytecode
- `kotlin/null-safety.md` — add `ifnull` branch bytecode
- `kotlin/data-classes.md` — add generated `equals/hashCode` bytecode
- `kotlin/delegation.md` — add `getfield`/`invokevirtual` for delegated properties
- `kotlin/sealed-classes.md` — add `tableswitch` bytecode for `when`
- `kotlin/generics.md` — add type-erasure bytecode evidence
- `kotlin/memory-model.md` — add stack-frame / GC roots evidence
- `kotlin/variance.md` — add wildcard bytecode for `in`/`out`

### G5 — Stub-revealed Android gaps ⬜

After deleting the 43 root stubs, these topics have no canonical anywhere in the repo. Some are covered indirectly; others are genuine holes.

- `android/compose/compose-runtime.md` (new file; deeper than recomposition-and-state)
- `android/compose/stability.md` (Compose `@Stable`/`@Immutable` deep dive)
- `android/compose/snapshot-system.md` (Snapshot state internals)
- `android/data-and-di/components.md` (Hilt component hierarchy)
- `android/data-and-di/scopes.md` (Hilt scopes vs coroutine scopes)
- `android/architecture/state-management.md` (or fold into `viewmodel.md`)
- `android/performance/rendering.md` (RenderThread + Skia)
- `android/performance/startup.md` (deeper than the cross-folder coverage)
- `android/os-internals/ksp.md`
- `android/os-internals/convention-plugins.md`
- `android/os-internals/multi-module.md`
- `android/testing/unit-testing.md` (new subfolder)
- `android/testing/ui-testing.md`
- `android/testing/journey-testing.md`

### G6 — Patterns and backend-for-mobile depth bump ⬜

Mid-tier (~150-200 lines each). To hit staff-FAANG bar, each needs: failure-mode tables, mobile-integration code (not just JVM examples), and the `Common Pitfalls` + `Probing Questions` polish.

- `patterns/` 12 files
- `backend-for-mobile/` 6 files

---

## Execution Order (Gap Closure Plan)

In order of impact-per-effort:

1. **G1 (reference architectures)** — highest impact for interview prep; format already proven by `offline-first-app.md`.
2. **G2 (career/leadership/platform-engineering)** — most direct path to staff promotion-doc utility.
3. **G4 (Kotlin bytecode evidence)** — narrow, fast, technical depth.
4. **G3 (thin ADRs)** — short, set the bar for decision documentation.
5. **G5 (Android subfolder gaps)** — fill the holes the stub deletion exposed.
6. **G6 (patterns / backend-for-mobile depth bump)** — final polish.

---

## Blocked — Decisions Needed ✅

All decisions made; gap closure proceeds per the execution order above.

---

## How to Update This File

After each writing session:

1. Move completed files from their milestone into the **Done So Far** table with the commit hash.
2. Flip the milestone's status emoji (⬜ → 🟡 → ✅).
3. If you discover a new deferred item or blocker, add it under the appropriate section.
4. If priorities shift, reorder milestones — but document why in the commit message.

This file is the persistent context. If a future session opens cold, this file plus `CONTRIBUTING.md` plus the v2 spec is enough to continue without re-deriving the plan.
