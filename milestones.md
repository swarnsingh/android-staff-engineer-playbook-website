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
| `backend-for-mobile/sse-vs-websockets.md` | decision | `371fd62` (kept as-is) |
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

### G1 — Reference architectures (depth bump) ✅

All 8 blueprints now at ~285-354 lines, each with distinct architectural signature, HLD diagram, per-layer blueprint, top scaling bottlenecks with code, tech summary, cross-references.

- ✅ `reference-architectures/offline-first-app.md` (250)
- ✅ `reference-architectures/banking-app.md` (293)
- ✅ `reference-architectures/consumer-app.md` (285)
- ✅ `reference-architectures/e-commerce-app.md` (297)
- ✅ `reference-architectures/merchant-app.md` (291)
- ✅ `reference-architectures/ride-hailing-app.md` (354)
- ✅ `reference-architectures/social-media-app.md` (318)
- ✅ `reference-architectures/video-streaming-app.md` (353)

### G2 — Career, leadership, platform-engineering depth ✅

All 15 files now at ~250-525 lines each with real templates inline (RFC, COE, design-review rubrics, Gradle convention plugins, BoM publishing pipelines, promo packets).

- ✅ `career/` 5 files (writing-rfcs, scope-and-ambiguity, performance-reviews-and-promotion, senior-to-staff-progression, technical-leadership)
- ✅ `leadership/` 5 files (escalation-and-decision-making, incident-response-on-call, influence-without-authority, running-a-design-review, technical-mentorship)
- ✅ `platform-engineering/` 5 files (build-graph-scaling 384, design-systems-architecture 424, internal-developer-platforms 310, library-versioning 375, sdk-distribution 536)

### G3 — Decision file depth bump ✅

All 6 decision files now at 342-520 lines with full Android-specific code, failure mode tables, 12+ probing questions.

- ✅ `android/architecture/mvvm-vs-mvi.md` (342)
- ✅ `android/data-and-di/room-vs-datastore.md` (492)
- ✅ `backend-for-mobile/graphql-vs-rest.md` (465)
- ✅ `android/architecture/modularization-strategies.md` (392)
- ✅ `android/data-and-di/hilt-vs-koin-vs-manual-di.md` (520)
- ✅ `backend-for-mobile/sse-vs-websockets.md` (450)

### G4 — Kotlin files practical interview depth ✅ (REDIRECTED from bytecode)

**Note:** Original plan was bytecode evidence (`javap -c`). Redirected per user request: bytecode is engineer-curiosity content, not interview-ready. Refocused on practical Job/SupervisorJob/scopes/dispatchers depth that maps to staff interviews. All 8 files at 423-567 lines.

- ✅ `kotlin/coroutines.md` (567) — Job/SupervisorJob/scopes/dispatchers/cancellation/timeouts
- ✅ `kotlin/null-safety.md` (474) — operators, lateinit vs lazy, platform types, Android NPE traps
- ✅ `kotlin/data-classes.md` (486) — generated methods, when to use, Compose stability
- ✅ `kotlin/delegation.md` (459) — lazy modes, observable/vetoable, Android `by` delegates
- ✅ `kotlin/sealed-classes.md` (500) — vs enum/interface, exhaustive when, polymorphic JSON
- ✅ `kotlin/generics.md` (526) — bounded, reified, variance basics, type tokens
- ✅ `kotlin/memory-model.md` (492) — stack/heap, GC roots, 6 Android leak patterns, LeakCanary
- ✅ `kotlin/variance.md` (423) — `out`/`in`, Nothing, function-type variance, Java interop

### G5 — Stub-revealed Android gaps ✅

13 of 14 done. Journey-testing dropped per user.

- ✅ `android/compose/compose-runtime.md` (426)
- ✅ `android/compose/stability.md` (436)
- ✅ `android/compose/snapshot-system.md` (471)
- ✅ `android/data-and-di/components.md` (511)
- ✅ `android/data-and-di/scopes.md` (436)
- ✅ `android/architecture/state-management.md` (566)
- ✅ `android/performance/rendering.md` (505)
- ✅ `android/performance/startup.md` (522)
- ✅ `android/os-internals/ksp.md` (518)
- ✅ `android/os-internals/convention-plugins.md` (684)
- ✅ `android/os-internals/multi-module.md` (507)
- ✅ `android/testing/unit-testing.md` (725) — new subfolder created
- ✅ `android/testing/ui-testing.md` (724)
- 🚫 `android/testing/journey-testing.md` — dropped per user decision

### G6 — Patterns and backend-for-mobile depth bump ✅

All 16 pattern and backend-for-mobile files have been updated to Staff-level depth with Android-specific code (e.g. OkHttp, Flow, Compose), failure mode tables, and probing questions.

**5 high-priority files** (Completed):
- ✅ `patterns/decorator.md` (OkHttp Interceptors, Compose Modifiers)
- ✅ `patterns/observer.md` (Flow/StateFlow, Lifecycle safety)
- ✅ `patterns/state.md` (Sealed classes, MVI reducers, ExoPlayer)
- ✅ `backend-for-mobile/api-design-for-mobile.md` (Retrofit, Error Envelopes)
- ✅ `backend-for-mobile/bff-pattern.md` (Android client orchestration, SDUI)

**7 medium-priority files** (Completed):
- ✅ `patterns/adapter.md` (RecyclerView.Adapter, Compose AndroidView, ACL)
- ✅ `patterns/builder.md` (OkHttp.Builder, DSLs, Kotlin Named Args)
- ✅ `patterns/circuit-breaker.md` (OkHttp Interceptor implementation, Fallback UI)
- ✅ `patterns/command.md` (WorkManager Command Bus, Offline queues)
- ✅ `patterns/factory.md` (ViewModelProvider.Factory, Hilt AssistedInject)
- ✅ `patterns/repository.md` (Single-source-of-truth Room+Retrofit)
- ✅ `patterns/retry.md` (OkHttp + WorkManager retry, Exponential Backoff)
- ✅ `patterns/saga.md` (WorkManager-based saga, compensating actions)
- ✅ `backend-for-mobile/rate-limiting.md` (Client-side Flow throttling)

**3 lower-priority files** (Completed / Light-touch):
- ✅ `patterns/strategy.md` (DI-injected strategy added)
- ✅ `backend-for-mobile/data-formats.md` (Moshi vs kotlinx.serialization added)
- ✅ `backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md`
- ✅ `backend-for-mobile/transport-protocols.md`

### G7 — Newly discovered gaps (post-2026-06 session) 🟡

#### G7a — Ktor coverage ✅

Mentioned in 12 files in passing but never explained as a topic. Created dedicated decision file.

- ✅ `android/networking-and-security/ktor-vs-retrofit.md` (668 lines) — full decision file with KMP focus

#### G7b — Compose Navigation 3 ✅

Major restructure of existing file. Both Nav 2 (current stable) and Nav 3 (2024 alpha) now covered with decision table, Nav 2 ↔ Nav 3 API mapping, migration phases, scenes for multi-pane layouts.

- ✅ `android/compose/compose-navigation.md` (674 lines)

### G8 — Kotlin Multiplatform subfolder ✅ DONE

KMP is mentioned in 22 files in passing but has no dedicated coverage. User decision: create dedicated subfolder `android/kotlin-multiplatform/` with 15 in-depth canonical files. Topic curriculum agreed and execution started.

**Folder:** `android/kotlin-multiplatform/`

**Phase 1 — Foundations:**
- ✅ `foundations/overview-and-k1-vs-k2.md` — Compiler-level (JVM, Native, Wasm), K2 speedups, `expect`/`actual`.
- ✅ `foundations/architecture-and-module-boundaries.md` — Shared Logic vs Shared UI, Domain/Data sharing patterns.

**Phase 2 — Tooling:**
- ✅ `tooling/build-system-and-source-sets.md` — Gradle KMP plugin, source sets (`commonMain`, `iosMain`), Version Catalogs.
- ✅ `tooling/ios-distribution.md` — Frameworks, CocoaPods plugin, SwiftPM, XCFramework.
- ✅ `tooling/swift-interop.md` — Swift↔Kotlin via Obj-C bridge, SKIE, Direct Swift Export.

**Phase 3 — Ecosystem:**
- ✅ `ecosystem/libraries-ecosystem.md` — KMP-ready matrix vs non-KMP.
- ✅ `ecosystem/networking-with-ktor.md` — Ktor patterns across platforms, engine selection.
- ✅ `ecosystem/persistence.md` — SQLDelight, Multiplatform Settings, Realm.
- ✅ `ecosystem/dependency-injection.md` — Koin shared modules and iOS initialization.

**Phase 4 — UI Sharing:**
- ✅ `ui-sharing/compose-multiplatform.md` — CMP vs Jetpack Compose, iOS Canvas vs UIKit.
- ✅ `ui-sharing/resource-sharing.md` — JetBrains Compose Resources (strings, fonts, vectors).

**Phase 5 — Production:**
- ✅ `production/concurrency-and-memory.md` — K/Native memory model, coroutines on iOS main thread.
- ✅ `production/testing-and-mocking.md` — `commonTest`, MocKMP, iOS simulator tests from Gradle.
- ✅ `production/ci-cd-for-kmp.md` — Automating builds, macOS runners, caching Native tasks.
- ✅ `production/adoption-and-migration.md` — Incremental migration, case studies.

**Cross-linking required when KMP folder lands:** Update `ktor-vs-retrofit.md`, `hilt-vs-koin-vs-manual-di.md`, `modularization-strategies.md`, `library-versioning.md`, and others that currently mention KMP in passing.

### G9 — Staff/Principal depth expansion 🟡

Post-correction roadmap. The repo is already Staff-shaped; this gap exists to push it from deep encyclopedia to production ownership manual. Each item should upgrade existing files first. Add new files only if the concept cannot fit an existing owner without violating the single-canonical-owner rule.

#### G9a — Mobile API evolution ✅

Goal: teach how Android clients survive backend change while old app versions remain in the wild for months or years.

- ✅ `backend-for-mobile/api-design-for-mobile.md` — old-client safety, compatibility contracts, handshake design, negative capability testing.
- ✅ `backend-for-mobile/bff-pattern.md` — BFF as a mobile compatibility boundary, not only a payload aggregator.
- ✅ `backend-for-mobile/graphql-vs-rest.md` — GraphQL vs REST vs BFF decision criteria for old-client support, caching, and schema governance.
- ✅ `mobile-system-design/versioning-and-backward-compatibility.md` — compatibility matrix, sunset runbook, forced-upgrade failure modes.
- ✅ `release-engineering/kill-switches.md` — API/server kill switches, capability-gated fallback behavior.

Why it matters: backend deploys continuously; mobile deploys through stores, user choice, OEMs, and long-tail app versions. Staff engineers need to design the contract so backend velocity does not become mobile fragility.

#### G9b — Schema and sync protocol evolution ✅

Goal: make offline-first content production-grade across long-offline clients, app upgrades, and server protocol changes.

- ✅ `mobile-system-design/offline-sync.md` — outbox payload versions, op compaction, delta-token invalidation, tombstone retention.
- ✅ `android/data-and-di/room.md` — multi-hop migration discipline, destructive fallback policy, exported schema review.
- ✅ `android/data-and-di/datastore.md` — preference/proto migrations, corruption handlers.

Why it matters: real sync systems fail at version boundaries, not only under network loss.

#### G9c — Mobile observability architecture ✅

Goal: teach how Staff engineers detect, explain, and prevent mobile regressions.

- ✅ `observability/slis.md`
- ✅ `observability/slos.md`
- ✅ `android/observability/crash-monitoring.md`
- ✅ `android/performance/anrs.md`
- ✅ `android/performance/startup.md`
- ✅ `android/performance/jank.md`

Why it matters: Staff-level mobile engineering is measured through crash-free users, ANR rate, startup p95/p99, jank, trace propagation, sampling, release dashboards, and privacy-safe telemetry.

Depth add: alert thresholds and fatigue. Dashboards are not enough; alerts need clear ownership, burn-rate logic, release awareness, and thresholds that page only for user-impacting regressions.

#### G9d — Release engineering decision trees ✅

Goal: turn rollout content into operational playbooks.

- ✅ `release-engineering/release-strategy.md`
- ✅ `release-engineering/staged-rollouts.md`
- ✅ `release-engineering/crash-rate-gating.md`
- ✅ `release-engineering/kill-switches.md`
- ✅ `release-engineering/ci-cd-for-mobile.md`

Why it matters: Principal-level judgment appears during bad releases: halt rollout, rollback, hotfix, remote-disable, device/OEM gating, and risk communication.

#### G9e — Testing strategy at scale ⬜

Goal: teach test portfolio design for large Android codebases.

- ⬜ `android/testing/unit-testing.md`
- ⬜ `android/testing/ui-testing.md`
- ⬜ `mobile-system-design/non-functional-requirements.md`
- ⬜ `platform-engineering/internal-developer-platforms.md`

Why it matters: the Staff lens is not "write tests"; it is fake servers, contract tests, screenshot tests, macrobenchmarks, flake management, CI sharding, and ownership.

Depth add: synthetic testing in production. Use controlled test accounts and canary workflows to validate login, checkout, sync, push, and payments against real production dependencies without polluting user data.

#### G9f — Platform engineering for mobile organizations ⬜

Goal: cover leverage across many teams.

- ⬜ `platform-engineering/build-graph-scaling.md`
- ⬜ `platform-engineering/internal-developer-platforms.md`
- ⬜ `platform-engineering/design-systems-architecture.md`
- ⬜ `platform-engineering/library-versioning.md`
- ⬜ `android/os-internals/convention-plugins.md`
- ⬜ `android/os-internals/multi-module.md`
- ⬜ `android/performance/app-size-and-r8.md` — app size budgets, CI gates, owner attribution, R8/resource shrinking, and dynamic feature governance.
- ⬜ `release-engineering/app-bundles.md` — AAB delivery strategy, split APK behavior, and size risk during rollout.

Why it matters: Staff engineers often own build speed, dependency governance, shared architecture, design systems, and paved roads.

#### G9g — Security and privacy threat modeling ⬜

Goal: move security from checklist to threat-model thinking.

- ⬜ `security/auth-on-mobile.md`
- ⬜ `security/key-management.md`
- ⬜ `security/secure-storage-on-android.md`
- ⬜ `security/attestation.md`
- ⬜ `security/privacy-gdpr-data-residency.md`
- ⬜ `android/networking-and-security/security-and-keystore.md`

Why it matters: Staff engineers must reason about rooted devices, token theft, cert pinning tradeoffs, Play Integrity limits, local storage limits, location privacy, and data minimization.

#### G9h — Principal architecture governance ⬜

Goal: teach how architectural decisions scale across teams.

- ⬜ `career/writing-rfcs.md`
- ⬜ `leadership/running-a-design-review.md`
- ⬜ `leadership/escalation-and-decision-making.md`
- ⬜ `platform-engineering/internal-developer-platforms.md`
- ⬜ `templates/decision.md`

Why it matters: Principal work is decision quality at org scale: RFCs, ADRs, tech radar, review rituals, ownership boundaries, migration plans, and deprecation discipline.

Recommended execution order: G9a → G9b → G9c → G9d → G9e → G9f → G9g → G9h.

---

## Execution Order (Gap Closure Plan) — Updated 2026-06

In order of impact-per-effort:

1. ✅ **G1** (reference architectures) — DONE
2. ✅ **G2** (career/leadership/platform-engineering) — DONE
3. ✅ **G3** (decision file depth bump) — DONE
4. ✅ **G4** (Kotlin practical depth, redirected from bytecode) — DONE
5. ✅ **G5** (Android subfolder gaps, journey-testing dropped) — DONE
6. ✅ **G6** (patterns + BFM depth bump) — DONE
7. ✅ **G7a** (Ktor) — DONE
8. ✅ **G7b** (Nav 3) — DONE
9. ✅ **G8** (KMP subfolder, 15 files) — DONE
10. 🟡 **G9** (Staff/Principal depth expansion) — IN PROGRESS

---

## Blocked — Decisions Needed ✅

All decisions made. Current execution: G9e testing strategy at scale.

---

## How to Update This File

After each writing session:

1. Move completed files from their milestone into the **Done So Far** table with the commit hash.
2. Flip the milestone's status emoji (⬜ → 🟡 → ✅).
3. If you discover a new deferred item or blocker, add it under the appropriate section.
4. If priorities shift, reorder milestones — but document why in the commit message.

This file is the persistent context. If a future session opens cold, this file plus `CONTRIBUTING.md` plus the v2 spec is enough to continue without re-deriving the plan.
