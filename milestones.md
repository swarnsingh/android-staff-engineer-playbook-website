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

The G12–G17 quality roadmap (from the 2026-07 principal-level audit) is **complete** — all six milestones merged (PRs #1–#10). Full scope of every milestone is preserved in the **Completed Roadmap** section below. Future work starts a new roadmap section here *before* it lands, not only recorded after.

| Track | Status | Notes |
|---|---:|---|
| M1-M23 initial buildout | ✅ | Original canonical files, platform breadth, reference architecture, polish, and KMP subfolder buildout complete |
| G1-G8 post-audit gap closure | ✅ | Reference architecture depth, leadership/platform depth, decision files, Kotlin practical depth, Android gaps, patterns/BFM, Ktor, Compose Navigation 3, KMP |
| G9 Staff/Principal expansion | ✅ | API evolution, sync protocol evolution, observability, release decision trees, testing strategy, platform engineering, security/privacy, architecture governance |
| G10 one-place depth expansion | ✅ | Correctness fixes, CS foundations, Android OS primitives, coroutine/Flow mastery, Compose/performance, data/networking/KMP production, distributed backend contracts |
| G11 Kotlin folder structure | ✅ | Flat Kotlin files moved into learning-domain subfolders; links updated; canonical ownership preserved |
| G12 correctness pass | ✅ | Fixed Strong Skipping semantics (`===` for unstable params), lambda/method-reference memoization guidance, R8/`@Stable` failure mode, AIDL append-only evolution rules, ART escape-analysis nuance, Binder buffer/thread-pool precision; repaired 16 stale link redirects; filled 3 TODO placeholders in offline-first blueprint; refreshed stale versions/DSLs. All factual changes verified against current official docs/AOSP source |
| G13 quality infrastructure | ✅ | CI quality gates on every PR (`scripts/check_docs.py` via GitHub Actions): broken links, stale text/target redirects, TODO/TBD markers, thin-file floor. PR template with kind/canonical-owner/fact-verification checklist. CONTRIBUTING: documented the gates, fixed the self-contradicting ADR naming rule, classified release digests (`kotlin/version-updates/`) as Application files under the Staleness Strategy |
| G14 consistency & editorial | ✅ | Expanded the five thin files to canonical depth (replication & leader election, streaming logs & partitioning, mobile client consistency contracts, KMP shared domain boundaries, SRP) — each gained Why It Matters, Mental Model, production example, tradeoffs, and probing questions. Renamed `new-relic.md` → `mobile-apm-and-rum.md` and reworked it vendor-neutrally (W3C Trace Context, Android vitals baseline, corrected memory-allocator overstatement). Tone pass: normalized the repeated "Junior Engineer" opener trope and hyperbole across 6 files |
| G15 Tier 1 content | ✅ | All four sub-PRs done: 1 (SDUI + WebView/hybrid, PR #4), 2 (testing strategy, PR #5), 3 (2026 currency: on-device AI, Privacy Sandbox phaseout, 16 KB pages, PR #6), 4 (Play Billing & subscriptions, PR #7) — see Active Roadmap below |
| G16 Tier 2 differentiators | ✅ | Both sub-PRs done: 1 (Media3, custom lint rules, value classes, PR #8), 2 (View interop & migration + form-factors matrix, PR #9) — see Active Roadmap below |
| G17 final audit & close-out | ✅ | Automated audit re-run green; cross-file adversarial pass over all 12 G15–G16 files (no contradictions found); learning-paths refreshed with 5 new entries; roadmap closed out (PR #10) |
| G18 world-class hardening | ✅ | Glossary +16 terms (all G12–G16 vocabulary); Currency Watchlist (9 rows) + CONTRIBUTING pointer + warn-only CI staleness reminder; self-assessment checkpoints on all 4 learning paths (PR #11) |

Latest cleanup/audit commits:

- `26d8a97` — fixed one broken internal docs link and updated outdated Swift export wording.
- `fd420ce` — cleaned up this milestone tracker.

---

## Active Roadmap — Maintenance

### G18 — World-Class Hardening ✅ (PR #11)

Post-program hardening from the "what's still pending for world-class" review. In-repo items only; human expert review and going public are owner-driven and tracked outside this file.

- ✅ `glossary.md`: 16 new terms covering all G12–G16 vocabulary (AICore, LiteRT, SDUI, Strong Skipping, RTDN, entitlement, grace period/account hold, replacement mode, value class, ViewCompositionStrategy, Widevine L1/L3, UAST, lint baseline, Glance, GMD, W3C Trace Context, 16 KB pages) with cross-links.
- ✅ Currency process: **Currency Watchlist** below (9 rows: file → fast-moving claims → primary source → last-checked date), pointer from CONTRIBUTING's Staleness Strategy (per-file footers stay banned), and a warn-only check in `scripts/check_docs.py` that nags when a row passes 180 days without ever failing the build.
- ✅ `learning-paths.md`: a 4-question self-assessment **Checkpoint** at the end of each of the four paths, answerable only from the linked material.

Deliberately not done here: per-file "Last verified" footers (contradict the documented Staleness Strategy), external-contributor templates (deferred until the repo goes public), and worked "wrong answers" per design topic (large content effort — candidate for a future milestone).

---

## Currency Watchlist

The fastest-moving files in the repo, per the [Staleness Strategy](CONTRIBUTING.md#staleness-strategy). Each names a specific version, deadline, or platform policy that *will* change. Re-verify against the listed source on roughly a quarterly cadence (the CI script prints a reminder when a row goes stale past 180 days) and update the date when done.

| File | Fast-moving claims | Primary source | Last checked |
|---|---|---|---|
| `mobile-system-design/on-device-ai.md` | ML Kit GenAI API statuses (Beta/Alpha), Gemini Nano generations, device coverage | developers.google.com/ml-kit/genai | 2026-07-15 |
| `security/privacy-sandbox.md` | Phaseout status, what remains supported | privacysandbox.google.com/overview/status | 2026-07-15 |
| `release-engineering/16kb-page-sizes.md` | Play deadlines, AGP/NDK version floors, backcompat behavior | developer.android.com/guide/practices/page-sizes | 2026-07-15 |
| `mobile-system-design/play-billing-and-subscriptions.md` | PBL current version, PBL 8+ deadline, replacement-mode APIs | developer.android.com/google/play/billing/release-notes | 2026-07-15 |
| `android/media/media3-player-architecture.md` | Media3 version, Compose UI artifact split | developer.android.com/jetpack/androidx/releases/media3 | 2026-07-15 |
| `android/compose/form-factors-matrix.md` | Wear/TV/Glance artifact versions and stability, car category rules | developer.android.com/jetpack/androidx/releases | 2026-07-15 |
| `android/compose/stability.md` | Compose compiler behavior (Strong Skipping), collections-immutable version | developer.android.com + kotlinlang.org | 2026-07-15 |
| `android/compose/compose-runtime.md` | Compose compiler plugin configuration and Strong Skipping default | developer.android.com/develop/ui/compose/performance/stability/strongskipping + kotlinlang.org/docs/compose-compiler-options.html | 2026-07-30 |
| `android/compose/recomposition-and-state.md` | Strong Skipping default and unstable-parameter comparison behavior | developer.android.com/develop/ui/compose/performance/stability/strongskipping | 2026-07-30 |
| `android/kotlin-multiplatform/foundations/overview-and-k1-vs-k2.md` | K2 migration behavior, Swift export status/features, Kotlin/Native runtime, hierarchy-template rules | kotlinlang.org/docs/k2-compiler-migration-guide.html + native-swift-export.html + multiplatform-hierarchy.html | 2026-07-30 |
| `android/kotlin-multiplatform/foundations/architecture-and-module-boundaries.md` | AndroidX KMP ViewModel support and SwiftUI ownership guidance; Swift export status | developer.android.com/kotlin/multiplatform/viewmodel + kotlinlang.org/docs/native-swift-export.html | 2026-07-30 |
| `android/kotlin-multiplatform/shared-domain-boundaries.md` | Objective-C/Swift export exception, Flow, cancellation, and sealed-type mappings | kotlinlang.org/docs/native-objc-interop.html + native-swift-export.html | 2026-07-30 |
| `android/kotlin-multiplatform/tooling/build-system-and-source-sets.md` | Android-KMP plugin DSL/limitations, KGP compatibility, native export and hierarchy behavior | developer.android.com/kotlin/multiplatform/plugin + kotlinlang.org/docs/multiplatform/multiplatform-compatibility-guide.html | 2026-07-30 |
| `android/kotlin-multiplatform/ecosystem/libraries-ecosystem.md` | Room/DataStore/Coil/OkHttp target support and kotlinx-datetime platform behavior | developer.android.com/kotlin/multiplatform + official library documentation linked in the topic | 2026-07-30 |
| `android/kotlin-multiplatform/ecosystem/persistence.md` | Room/DataStore KMP version floors, supported APIs, and iOS storage guidance | developer.android.com/kotlin/multiplatform/room + developer.android.com/kotlin/multiplatform/datastore | 2026-07-30 |
| `android/kotlin-multiplatform/ecosystem/dependency-injection.md` | Koin runtime/compiler-plugin versions, RC status, Kotlin compatibility, KMP validation, and deprecated KSP path | insert-koin.io/docs/setup/compiler-plugin + insert-koin.io/docs/support/releases | 2026-07-30 |
| `android/kotlin-multiplatform/ui-sharing/compose-multiplatform.md` | Compose Multiplatform version/platform floors, iOS rendering and input behavior, Navigation, Android-only APIs | kotlinlang.org/docs/multiplatform/compose-compatibility-and-versioning.html + compose-navigation.html + compose-android-only-components.html | 2026-07-30 |
| `android/kotlin-multiplatform/ui-sharing/resource-sharing.md` | Compose Resources formats, qualifiers, generated accessors, publication requirements, web loading behavior | kotlinlang.org/docs/multiplatform/compose-multiplatform-resources.html + compose-multiplatform-resources-setup.html + compose-multiplatform-resources-usage.html | 2026-07-30 |
| `android/kotlin-multiplatform/tooling/swift-interop.md` | Objective-C export mappings, Swift export Alpha capabilities/limits, SKIE compatibility and generated features | kotlinlang.org/docs/native-objc-interop.html + native-swift-export.html + skie.touchlab.co | 2026-07-30 |
| `android/testing/testing-strategy.md` | GMD/ATD APIs, sharding property (experimental namespace) | developer.android.com/studio/test/gradle-managed-devices | 2026-07-15 |
| `android/testing/ui-testing.md` | Compose Preview Screenshot Testing plugin status, version, and requirements | developer.android.com/studio/preview/compose-screenshot-testing | 2026-07-29 |
| `kotlin/version-updates/` (all digests) | Release-delta claims by construction | kotlinlang.org release notes | 2026-07-15 |
| `release-engineering/android-platform-compatibility.md` | Target API deadlines, toolchain/API compatibility | developer.android.com/google/play/requirements/target-sdk | 2026-07-29 |
| `release-engineering/android-developer-verification.md` | Enforcement dates, regions, registration workflows, account limits | developer.android.com/developer-verification | 2026-07-29 |

Rows are added when a new file names a version/deadline/policy; rows are never removed while the file keeps such claims.

---

## Completed Roadmap — G12–G17 Quality Program

Closed out 2026-07-15 with PR #10. Full milestone scope is retained below for history — it documents what was planned, what shipped, and where plans changed on verified evidence (see G15 sub-item 3).

**Origin.** A 2026-07 principal-level audit of the full repo (285 files, ~531k words) assessed technical accuracy, structural integrity, and coverage against staff-level expectations. It found three classes of issues, which map directly to the milestones below:

1. **Correctness defects** — confirmed technical errors in flagship files (Compose Strong Skipping semantics, AIDL evolution rules, ART escape analysis, Binder precision), 16 stale link redirects, 3 shipped TODO placeholders → **G12**.
2. **Missing enforcement** — nothing prevented those defect classes from landing again (no CI, no PR gates, taxonomy ambiguities in CONTRIBUTING) → **G13**.
3. **Consistency and coverage gaps** — five files at a fraction of sibling depth, a vendor-named file in the observability TOC, a repeated tone trope → **G14**; seven staff-level topics with no dedicated treatment → **G15**; differentiator topics → **G16**; and a final re-audit → **G17**.

**Operating rules for this program.** One milestone per PR (sub-PRs where scoped below); every PR is Codex-reviewed and merged before the next begins; every factual claim is verified against current official docs/source at writing time; commits carry no LLM attribution; CI quality gates must be green.

### G12 — Correctness Pass ✅ (PR #1)

- ✅ `android/compose/stability.md`: Strong Skipping compares unstable params with `===` not `equals()`; lambda vs method-reference memoization guidance corrected (function references un-memoized until Compose compiler 1.5.1/1.5.5); bogus R8-strips-`@Stable` failure mode replaced; modern `composeCompiler {}` metrics DSL; `kotlinx-collections-immutable` bumped to 0.5.1.
- ✅ `android/os-internals/the-binder.md`: AIDL append-only evolution (transaction codes from declaration order); corrected AOSP link; `BINDER_VM_SIZE`/thread-pool precision from `ProcessState.cpp`; (post-review) structured-AIDL qualification on field additions.
- ✅ `kotlin/runtime-and-jvm/memory-model.md`: HotSpot scalar replacement vs ART's more conservative `escape.cc` + LSE distinction.
- ✅ 16 stale link redirects repaired; 3 TODO placeholders in `reference-architectures/offline-first-app.md` filled ((post-review) convergence SLO scoped to foreground sync).

### G13 — Quality Infrastructure ✅ (PR #2)

- ✅ `scripts/check_docs.py` + GitHub Actions workflow: broken links, stale text/target redirects, TODO/TBD markers, thin-file floor — fails every PR that regresses.
- ✅ PR template: file kind, canonical owner, fact-verification, TOC updates, local gate run.
- ✅ CONTRIBUTING: gates documented; ADR naming contradiction fixed; release digests classified as Application files.

### G14 — Consistency & Editorial ✅ (PR #3)

- ✅ Five thin files expanded to canonical depth: `distributed-systems/replication-and-leader-election.md`, `distributed-systems/streaming-logs-partitioning.md`, `distributed-systems/mobile-client-consistency-contracts.md`, `android/kotlin-multiplatform/shared-domain-boundaries.md`, `principles/single-responsibility.md` ((post-review) Swift-bridge caveats on sealed exhaustiveness and coroutine cancellation, verified via KT-47610).
- ✅ `new-relic.md` → `mobile-apm-and-rum.md`: vendor-neutral APM/RUM treatment (W3C Trace Context, Android vitals baseline, memory-allocator overstatement fixed).
- ✅ Tone normalization across 6 files; this Active Roadmap section added to the tracker.

### G15 — Tier 1 Content: The Seven Missing Topics ✅

Staff-level topics with no dedicated treatment anywhere in the repo, ordered by interview/production impact. Four sub-PRs:

1. ✅ **Platform architecture** (PR #4): `mobile-system-design/server-driven-ui.md` (capability negotiation, tolerant reader, fallback chains, action-as-enum vs interpreter — the #1 gap) + `android/networking-and-security/webview-and-hybrid.md` (origin-scoped bridges, WebViewAssetLoader, `isForMainFrame` navigation gating, 3-DS example).
2. ✅ **Testing at scale** (PR #5): `android/testing/testing-strategy.md` — tier economics and placement, flake quarantine pipeline with retry-policy honesty, CI topology (PR gate budget / merge queue / nightly device matrix), Gradle Managed Devices + ATD (verified), consumer-driven contract tests against BFFs, governance metrics (escaped defects over line coverage).
3. ✅ **2026 currency** (PR #6): `mobile-system-design/on-device-ai.md` (Gemini Nano/AICore/ML Kit GenAI layering, LiteRT + CompiledModel API, on-device vs cloud routing, fleet-coverage fallback) + `security/privacy-sandbox.md` — rewritten from the original plan after online verification: Privacy Sandbox on Android was deprecated 2025-10-17, so the file covers the phaseout, what replaces it, and the platform-bet lessons + `release-engineering/16kb-page-sizes.md` (Play requirement since 2025-11-01 for API 35+ targets; ELF + zip alignment, AGP 8.5.1/NDK r28 floors, CI gate, 16 KB emulator testing).
4. ✅ **Commerce** (PR #7): `mobile-system-design/play-billing-and-subscriptions.md` — sibling of `payment-flow.md` (card checkout ≠ Play Billing): product/base-plan/offer model, server-as-source-of-truth entitlement service (RTDN as trigger + `subscriptionsv2.get`, verify→grant→acknowledge ordering, 3-day ack window), involuntary-churn lifecycle (grace/hold/canceled-vs-expired, restore vs resubscribe, `linkedPurchaseToken` dedup), replacement modes incl. PBL 8.1+ `SubscriptionProductReplacementParams`, PBL 8+ publishing gate (2026-08-31), license-tester time compression. Cross-linked from `payment-flow.md`.

### G16 — Tier 2 Differentiators ✅

Two sub-PRs:

1. ✅ **Media, tooling, language** (PR #8): `android/media/media3-player-architecture.md` (new Media section — component model, buffering economics, session ownership, cache vs downloads, Widevine L1/L3 fallback, player pooling, Media3 1.10 Compose UI) + `platform-engineering/custom-lint-and-static-analysis.md` (detector anatomy, `lintChecks` vs `lintPublish`, TestLintTask, baseline-and-ratchet rollout, analysis-tool portfolio) + `kotlin/language-core/value-classes.md` (boxing rules, mangling/`@JvmName` as permanent API decisions, vs typealias/data class, Compose stability).
2. ✅ **Hybrid UI & form factors** (PR #9): `android/compose/view-interop-and-migration.md` (ComposeView/ViewCompositionStrategy pitfalls, AndroidView factory/update/onReset contract, AndroidViewBinding/AndroidFragment as transitional tools, seam costs, phased migration strategy with navigation-last sequencing) + `android/compose/form-factors-matrix.md` (Wear Compose Material 3 stable with parallel artifact set, Compose for TV stable with Leanback formally deprecated, Car App Library template/category gating, Glance-as-RemoteViews constraints, decision framework and leverage sequencing). Media3 cross-link restored.

### G17 — Final Audit & Close-out ✅ (PR #10)

- ✅ Automated audit re-run: links, redirects, TODO markers, thin-file floor — all green across the repo; all 12 G15–G16 files clear the depth floor (850–2,050 words).
- ✅ Adversarial cross-consistency pass: scanned the pre-existing corpus for claims contradicting the new content (Privacy Sandbox status, billing APIs, Leanback recommendations) — none found; every new-file claim had already been source-verified at writing time plus two Codex review rounds per PR.
- ✅ `learning-paths.md` refreshed: Play Billing and On-Device AI added to Path 1, Custom Lint Rules and Privacy Sandbox to Path 2, Mobile APM & RUM to Path 3. `README.md` reviewed — deliberately evergreen, no changes needed. Tree TOCs were wired per-PR and verified current.
- ✅ Roadmap closed out: this section retitled Completed with full scope retained.

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
- Probing-question answer keys are an active migration: the quality script reports the exact remaining count without failing unrelated pull requests. Updated and new topics must add keys under the contribution standard.
- External resources are now crawled by `scripts/check_external_links.py` on a weekly schedule and manual dispatch; the July 29, 2026 remediation pass found no remaining definitive 404/410 responses.
- A full human grammar and technical review across the whole corpus remains stronger than automated checks and should proceed domain by domain.

### Visual quality baseline

The July 29, 2026 visual pass established a maintainable baseline:

- 251 Mermaid diagrams render successfully through the pinned Mermaid CLI.
- All 65 legacy ASCII blocks in `mobile-system-design/` were replaced with Mermaid architecture, sequence, pipeline, or state diagrams plus text takeaways.
- High-value Android, Compose, performance, testing, Kotlin, KMP, build, security, release, and resilience topics received focused visual upgrades.
- All older architecture ASCII outside mobile system design has now been migrated to Mermaid. The visual checker enforces a zero-diagram baseline while ignoring box-drawing characters that are part of executable source-code examples.
- Local image assets require meaningful alt text, repository-local storage, explicit attribution, and verified reuse rights; no third-party image assets were needed for this pass.

---

## How To Update This File

After future roadmap work:

1. Add a short milestone section only if there is a real new roadmap track.
2. Mark status honestly: ✅, 🟡, ⬜, or 🚫.
3. Link the canonical owner files instead of duplicating long checklists.
4. Add commit hashes for substantial completed tracks.
5. Remove stale "current execution" notes as soon as the work is committed.
