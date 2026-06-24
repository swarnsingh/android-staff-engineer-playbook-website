# Milestones

Working tracker for the canonical-content fill-in plan. This file is for the writer, not the reader of the repo. Update as work progresses.

---

## Operating Rules

These are the constraints every milestone is shaped by. If a future session forgets these, the work will drift.

1. **Breadth over anchor depth.** Fill foundational canonical files across many trees before going deep into any anchor system. The repo's value as a Staff study path comes from broad foundations, not exhaustive coverage of one example.
2. **Anchor systems (AirBridge, BizBrew) are deferred.** Both are real but incomplete projects. Until the systems are stable enough to write canonical reference material about, the following are deferred:
   - All `airbridge/*` application files (beyond stubs).
   - All `bizbrew/*` application files.
   - Anchor-specific ADRs (002 — POST vs WebSockets; 008 — LWW vs CRDT if framed AirBridge-specific).
   - The `## AirBridge Example` and `## BizBrew Example` sections in **new** canonical files — omit them per the v2 spec's "optional, prefer omission to filler" rule. Already-written files (`state-machines.md`, `idempotency.md`) keep what they have.
   - Scale-number TODOs in `airbridge.md` / `bizbrew.md`.
3. **Quality bar: SDE-1 to Staff.** Every canonical file must be readable by someone who has never seen the concept and still useful to a Staff engineer. Teach from first principles. Define vocabulary on first use. Use code examples (Kotlin preferred) where they sharpen explanation.
4. **Single-canonical-owner rule still applies.** When in doubt, consult [`CONTRIBUTING.md`](CONTRIBUTING.md) — the Canonical Ownership Map pins contested concepts.
5. **Structure freeze still applies.** No new folders. New content fills existing trees.

---

## Status Legend

- ✅ **done** — file is full canonical-quality content, committed
- 🟡 **partial** — some files in the milestone are done, others pending
- ⬜ **pending** — milestone not yet started
- 🚫 **blocked** — needs user decision before starting
- 🅿️ **deferred** — anchor-related, waiting on AirBridge/BizBrew project maturity

---

## Done So Far

| File | Kind | Commit |
|---|---|---|
| `engineering-fundamentals/state-machines.md` | canonical | `4d7cb3c` then refined `7b7a8f1` |
| `distributed-systems/idempotency.md` | canonical | `371fd62` |
| `airbridge/upload-state-machine.md` | application | `7b7a8f1` (kept as-is; do not extend until anchor matures) |
| `adr/003-sse-vs-websockets.md` | decision | `371fd62` (kept as-is) |
| `reference-architectures/offline-first-app.md` | blueprint | `371fd62` |

Plus: README, CONTRIBUTING, 4 templates, 17 tree-level TOCs, anchor definitions (placeholder), 207 stubs.

---

## Active Milestones (in execution order)

Each milestone is roughly one session's worth of work for a moderately-sized batch. Bigger canonical files (e.g., `caching.md`, `coroutines.md`) may take a session each on their own.

### M1 — Bedrock Fundamentals ⬜

6 canonical files. The substrate every later file links to.

- `engineering-fundamentals/sync-vs-async.md`
- `engineering-fundamentals/latency-vs-throughput.md`
- `engineering-fundamentals/caching.md`
- `engineering-fundamentals/backpressure.md`
- `engineering-fundamentals/fault-tolerance.md`
- `engineering-fundamentals/time-and-clocks.md`

### M2 — Distributed Systems Core 🟡 (idempotency.md done)

4 canonical files remaining.

- `distributed-systems/cap-theorem.md`
- `distributed-systems/consistency-models.md`
- `distributed-systems/delivery-semantics.md`
- `distributed-systems/vector-clocks.md`
- `distributed-systems/crdts.md`
- `distributed-systems/consensus-basics.md`

### M3 — Patterns + Key Principles ⬜

Small files; batched. ~18 files total.

**Patterns (12):** repository, adapter, factory, strategy, observer, state, builder, decorator, command, circuit-breaker, retry, saga

**Principles (6 most-leveraged):** simplicity, determinism, design-for-failure, make-invalid-states-impossible, prefer-deletion, composition-over-inheritance

Remaining 5 principles (least-knowledge, single-responsibility, locality-of-reference, optimize-for-change, progressive-disclosure) can land in M20 or piecewise.

### M4 — Observability Spine ⬜

9 canonical files. Unlocks `android/observability/*` application files later.

- logging, structured-logging, metrics, tracing, distributed-tracing, slis, slos, error-budgets, alerting, dashboards (10 if you count distributed-tracing as full canonical here)

### M5 — Kotlin Language Depth ⬜

10 canonical files.

- coroutines, null-safety, generics, variance, inline-functions, reified-types, sealed-classes, data-classes, delegation, memory-model

Variables, functions, extensions, jvm-interop, bytecode can land in a smaller follow-up.

### M6 — Android Architecture + Lifecycle ⬜

8 canonical files.

- activity, fragment, viewmodel, navigation, savedstatehandle, process-death-and-state-restoration, structured-concurrency, flow

### M7 — Android Performance + Concurrency ⬜

8 canonical files.

- jank, anrs, baseline-profiles, startup, rendering, memory-management-and-leak-detection, doze-app-standby-and-battery-optimization, workmanager-and-background-execution-constraints

Plus `shared-flow.md`, `state-flow.md` (smaller, can batch in).

### M8 — Android Compose + Data + DI ⬜

12 canonical files.

- compose-runtime, recomposition, stability, snapshot-system, side-effects, state-management
- room, paging, datastore
- hilt, scopes, components

### M9 — Android Networking + Build + Internals ⬜

9 canonical files + 3 application files in `android/observability/`.

- retrofit, okhttp, graphql
- gradle, ksp, convention-plugins, multi-module, r8-proguard
- binder-and-ipc
- `android/observability/new-relic.md` (application), `android/observability/crash-monitoring.md` (application), `android/observability/logging.md` (application)

### M10 — Backend-for-Mobile ⬜

6 canonical files.

- bff-pattern, api-design-for-mobile, transport-protocols, push-vs-poll-vs-sse-vs-websockets, rate-limiting, data-formats

### M11 — Mobile System Design — Framework + NFRs ⬜

7 canonical files. The meta-skills before worked problems.

- design-framework, non-functional-requirements, performance, accessibility, localization-and-internationalization, security-and-privacy, versioning-and-backward-compatibility

### M12 — Worked Design Problems (Part 1) ⬜

8 architecturally distinct problems.

- offline-sync, chat-messaging, file-downloader, image-loading, notification-system, payment-flow, pagination, search

### M13 — Worked Design Problems (Part 2) ⬜

8 remainder.

- news-feed, google-maps-location-system, youtube-video-streaming, stock-trading-app, ride-hailing, caching-library, typeahead-autocomplete-search, collaborative-editing

### M14 — Platform & SDK Design ⬜

9 canonical files (excluding `airbridge-at-scale.md`, which is anchor-specific).

- feature-flags-and-remote-config, telemetry-sdk, analytics-sdk, app-startup, authentication, push-notifications, deep-links-and-universal-links, a-b-testing-infrastructure, experimentation-platform

### M15 — Release Engineering ⬜

8 canonical files.

- staged-rollouts, kill-switches, crash-rate-gating, ci-cd-for-mobile, code-signing, play-store-internals, app-bundles, release-strategy

### M16 — Reference Architecture Blueprints 🟡 (offline-first-app.md done)

8 blueprints remaining. Multi-tenant-app is BizBrew-anchored → 🅿️ deferred.

- consumer-app, merchant-app, banking-app, e-commerce-app, ride-hailing-app, social-media-app, video-streaming-app
- ~~multi-tenant-app~~ 🅿️ deferred

### M17 — ADRs (non-anchor) ⬜

5 ADRs that don't depend on anchor systems being stable.

- 001 — MVVM vs MVI
- 004 — Room vs DataStore
- 005 — GraphQL vs REST
- 006 — Monolith vs Modularization
- 007 — Hilt vs Manual DI

🅿️ Deferred: 002 (POST vs WebSockets — AirBridge-specific), 008 (LWW vs CRDT — AirBridge/BizBrew choice, may be writable generically later)

### M18 — Computer Science (lean) ⬜

4 canonical files. Deliberately small per spec.

- hashing, trees, graphs, system-complexity

### M19 — Security + Leadership 🚫

Topics partly enumerated.

- `security/privacy-gdpr-data-residency.md` (canonical)
- `leadership/incident-response-on-call.md` (canonical)
- Plus 🚫 needs more topic enumeration for `security/`, `leadership/`, and the still-empty `platform-engineering/`, `career/` trees.

### M20 — Polish ⬜

- Fill the remaining 5 lesser-priority principles files (least-knowledge, single-responsibility, locality-of-reference, optimize-for-change, progressive-disclosure)
- Fill remaining Kotlin smaller files (variables, functions, extensions, jvm-interop, bytecode)
- Populate `glossary.md` entries as canonical files are written (running task — do it incrementally, not at the end)
- Write actual content for `learning-paths.md` sequences
- Cross-reference audit: walk every canonical file's Further Reading section, verify links work
- Convert `[VERIFY]`/`TODO` markers in anchor files when projects mature

---

## Deferred (waiting on anchor project maturity) 🅿️

- `airbridge/deterministic-resume.md` (application)
- Any further `airbridge/*` files beyond `upload-state-machine.md`
- All `bizbrew/*` application files
- ADR 002 (POST vs WebSockets — AirBridge-specific)
- ADR 008 (LWW vs CRDT — could be written generically if needed; defer for now)
- `reference-architectures/multi-tenant-app.md` (BizBrew-anchored)
- `mobile-system-design/airbridge-at-scale.md` (AirBridge-specific)
- Scale numbers in `airbridge.md` and `bizbrew.md` (currently `TODO`)
- Anchor Example sections in new canonical files (omit per v2 optional-omission rule)

---

## Blocked — Decisions Needed 🚫

These can't move until you make a content decision.

- **`platform-engineering/` topics:** spec doesn't enumerate any. Suggested starter list: internal-developer-platforms, design-systems-architecture, library-versioning, sdk-distribution, build-graph-scaling. Confirm or override.
- **`career/` topics:** spec doesn't enumerate any. Suggested starter list: senior-to-staff-progression, scope-and-ambiguity, technical-leadership, writing-rfcs, performance-reviews-and-promotion. Confirm or override.
- **Additional `security/` topics** beyond Privacy/GDPR: suggested — auth-on-mobile, secure-storage-on-android, key-management, certificate-pinning, attestation. Confirm or override.
- **Additional `leadership/` topics** beyond Incident Response: suggested — running-a-design-review, influence-without-authority, technical-mentorship, escalation-and-decision-making. Confirm or override.

---

## How to Update This File

After each writing session:

1. Move completed files from their milestone into the **Done So Far** table with the commit hash.
2. Flip the milestone's status emoji (⬜ → 🟡 → ✅).
3. If you discover a new deferred item or blocker, add it under the appropriate section.
4. If priorities shift, reorder milestones — but document why in the commit message.

This file is the persistent context. If a future session opens cold, this file plus `CONTRIBUTING.md` plus the v2 spec is enough to continue without re-deriving the plan.
