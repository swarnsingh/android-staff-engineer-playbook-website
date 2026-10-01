# Milestones

Working tracker for the canonical-content fill-in plan. This file is for maintainers, not readers of the playbook.

Current state: the original canonical buildout, post-audit gap closure, Staff/Principal expansion, one-place depth expansion, and Kotlin folder structure cleanup are complete through G11. G19 records the repository-wide correctness and curriculum audit opened on 2026-08-01.

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
| G12 correctness pass | ✅ | Fixed Strong Skipping semantics (`===` for unstable params), lambda/method-reference memoization guidance, R8/`@Stable` failure mode, AIDL append-only evolution rules, ART escape-analysis nuance, and the Binder issues scoped in G12; repaired 16 stale link redirects; filled 3 TODO placeholders in the offline-first blueprint; refreshed stale versions/DSLs. The later G19 audit supersedes unresolved Binder accounting and ANR wording. |
| G13 quality infrastructure | ✅ | CI quality gates on every PR (`scripts/check_docs.py` via GitHub Actions): broken links, stale text/target redirects, TODO/TBD markers, thin-file floor. PR template with kind/canonical-owner/fact-verification checklist. CONTRIBUTING: documented the gates, fixed the self-contradicting ADR naming rule, classified release digests (`kotlin/version-updates/`) as Application files under the Staleness Strategy |
| G14 consistency & editorial | ✅ | Expanded the five thin files to canonical depth (replication & leader election, streaming logs & partitioning, mobile client consistency contracts, KMP shared domain boundaries, SRP) — each gained Why It Matters, Mental Model, production example, tradeoffs, and probing questions. Renamed `new-relic.md` → `mobile-apm-and-rum.md` and reworked it vendor-neutrally (W3C Trace Context, Android vitals baseline, corrected memory-allocator overstatement). Tone pass: normalized the repeated "Junior Engineer" opener trope and hyperbole across 6 files |
| G15 Tier 1 content | ✅ | All four sub-PRs done: 1 (SDUI + WebView/hybrid, PR #4), 2 (testing strategy, PR #5), 3 (2026 currency: on-device AI, Privacy Sandbox phaseout, 16 KB pages, PR #6), 4 (Play Billing & subscriptions, PR #7) — see Active Roadmap below |
| G16 Tier 2 differentiators | ✅ | Both sub-PRs done: 1 (Media3, custom lint rules, value classes, PR #8), 2 (View interop & migration + form-factors matrix, PR #9) — see Active Roadmap below |
| G17 final audit & close-out | ✅ | Automated audit re-run green; cross-file adversarial pass over all 12 G15–G16 files (no contradictions found); learning-paths refreshed with 5 new entries; roadmap closed out (PR #10) |
| G18 world-class hardening | ✅ | Glossary +16 terms (all G12–G16 vocabulary); Currency Watchlist (9 rows) + CONTRIBUTING pointer + warn-only CI staleness reminder; self-assessment checkpoints on all 4 learning paths (PR #11) |
| G19 repository-wide correctness and curriculum audit | 🟡 | 305-file static inventory; candidate edits landed for 10 P0 targets, with independent domain review and full quality-gate validation still pending; broader source, curriculum, pedagogy, and governance work remains |

Latest cleanup/audit commits:

- `26d8a97` — fixed one broken internal docs link and updated outdated Swift export wording.
- `fd420ce` — cleaned up this milestone tracker.

---

## Active Roadmap — Maintenance

### G19 — Repository-wide technical and curriculum audit 🟡

**Audit scope (2026-08-01).** A static inventory covered all 305 Markdown files (about 91,500 lines and 664,400 whitespace-delimited words), not only the Android tree. The review combined repository-wide searches for versioned claims, absolutes, deprecated APIs, source coverage, missing standard sections, duplicate ownership, and misleading teaching language with targeted reading of high-risk Android, Kotlin, backend-for-mobile, release, security, distributed-systems, and reference-architecture material. The existing structural checks could not be executed in this environment because the pinned `markdown-it-py` dependency and Mermaid CLI were unavailable; that limitation is not evidence that the corpus is clean.

This is a **triage report, not a declaration that every unlisted sentence is correct**. A world-class handbook needs named domain reviewers and a claim-to-primary-source review, file by file. Search results are leads; a maintainer must reproduce each proposed correction against the linked primary source before changing teaching text. Vendor blogs, Medium, Wikipedia, and recollection are not acceptable arbiters when an Android, Kotlin, AOSP, IETF, W3C, Gradle, or library source exists.

#### P0 — Candidate correctness fixes applied; cross-section verification pending (2026-08-01)

| Location | Problem found | Candidate correction and primary source for reviewer verification |
|---|---|---|
| `backend-for-mobile/rate-limiting.md` | “Never automatically retry a 429” contradicts HTTP semantics and the chapter's own retry teaching. | Teach policy-driven retry: honor `Retry-After` when present, cap attempts, add jitter, respect idempotency and deadline, and do not turn a server hint into an instruction that a human must retry. Validate against [RFC 6585 §4](https://www.rfc-editor.org/rfc/rfc6585.html#section-4) and [`Retry-After` in RFC 9110 §10.2.3](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3). |
| `android/networking-and-security/retrofit-and-okhttp.md` | “After ~5 leaked calls, the pool is exhausted and all future requests hang” confuses OkHttp's default five *idle* connections with a maximum connection/request count. | Keep the real warning—response bodies must be closed—but explain that leaks prevent reuse and consume sockets/resources; concurrency is governed separately by the dispatcher and peer/protocol. Validate against OkHttp [`ResponseBody`](https://lysine.dev/okhttp/5.x/okhttp/okhttp3/-response-body/index.html), [`ConnectionPool`](https://lysine.dev/okhttp/5.x/okhttp/okhttp3/-connection-pool/index.html), and [`Dispatcher`](https://lysine.dev/okhttp/5.x/okhttp/okhttp3/-dispatcher/index.html). |
| `android/networking-and-security/graphql.md` | “In REST, a 404 or 500 status code tells you everything” is false; HTTP status does not encode domain outcome or necessarily explain an error. “GraphQL … almost always 200” also hides the GraphQL-over-HTTP status rules. | Separate transport, protocol, and domain errors for both styles; teach partial GraphQL data and negotiated media-type behavior. Validate against [GraphQL Response](https://graphql.org/learn/response/) and the [GraphQL-over-HTTP specification](https://graphql.github.io/graphql-over-http/draft/). |
| `backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md` | The “up to 10 seconds” FCM budget is presented as a stable guarantee, and “the OS wakes up your app” overstates best-effort delivery. | Use Firebase's “several seconds” wording, distinguish normal/high-priority handling, foreground/background notification behavior, Doze, priority deprioritization, and when expedited WorkManager may follow high-priority delivery. Validate against [Receive messages](https://firebase.google.com/docs/cloud-messaging/android/receive), [message priority](https://firebase.google.com/docs/cloud-messaging/android/message-priority), and [message types](https://firebase.google.com/docs/cloud-messaging/customize-messages/set-message-type). |
| `backend-for-mobile/transport-protocols.md` | “Must use exactly one `OkHttpClient` singleton” turns a reuse recommendation into a false global invariant. The QUIC prose also implies migration is seamless before partially retracting it. | Recommend sharing clients/pools where configurations are compatible; document legitimate isolation for trust material, proxies, authentication, or lifecycle boundaries. Describe QUIC migration as capability- and path-dependent. Validate against OkHttp's [client reuse guidance](https://lysine.dev/okhttp/5.x/okhttp/okhttp3/-ok-http-client/index.html) and [RFC 9000 §9](https://www.rfc-editor.org/rfc/rfc9000.html#section-9). |
| `backend-for-mobile/api-design-for-mobile.md` | “GraphQL: No versions. Add new fields, never delete old fields” is an unsafe universal. Schemas evolve, fields may be deprecated and removed under a compatibility/support policy, and adding fields can still break poorly written clients. | Teach observable client usage, persisted-query compatibility, deprecation windows, supported-app cohorts, and the limits of “additive equals safe.” Validate against GraphQL [validation](https://spec.graphql.org/October2021/#sec-Validation) and [deprecation/introspection](https://spec.graphql.org/October2021/#sec-Field-Deprecation). |
| `android/observability/crash-monitoring.md` | Native crashes do not “vaporize the JVM”; they terminate the Linux app process. Sending expected operational failures to “standard Analytics” conflates product analytics, logs, metrics, traces, and sampled diagnostic events. | Use process/runtime terminology and a telemetry decision table based on actionability, volume, privacy, sampling, and retention. Validate native-crash behavior against Android's [Diagnose native crashes](https://source.android.com/docs/core/tests/debug/native-crash) and telemetry choices against the [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/). |
| `android/observability/logging.md` | “Verbose … never compiled into production,” forcing every codebase through Timber, and “guarantee release-stripping” are policy opinions presented as platform facts. | Distinguish log priority from compile-time removal; show R8 assumptions and side-effect caveats explicitly; make the logging facade a contextual architecture decision, not a universal Staff rule. Validate against Android [`Log`](https://developer.android.com/reference/android/util/Log) and R8's [optimization documentation](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization). |
| `android/performance/baseline-profiles.md` and `android/os-internals/art-and-dalvik.md` | Claims such as “5 minutes,” “entire APK/100%,” “startup was instant,” “battery life soared,” “3x storage,” and “catastrophic flaw” mix an imprecise history lesson with invented universal measurements. | Replace rhetoric with the documented evolution from install-time AOT to hybrid JIT/AOT and profile-guided compilation; scope measurements to devices/workloads. Validate against [ART JIT](https://source.android.com/docs/core/runtime/jit-compiler), [ART configuration](https://source.android.com/docs/core/runtime/configure), and [Baseline Profiles](https://developer.android.com/topic/performance/baselineprofiles/overview). |
| `android/os-internals/the-binder.md` | A fixed “15 plus main binder thread” model and “the next caller … ANRs” make implementation detail sound universal and immediate. | Explain userspace pool configuration, blocking, nested calls, process-specific limits, and the fact that an ANR depends on which thread is blocked and for how long. Validate against current AOSP [`ProcessState.cpp`](https://android.googlesource.com/platform/frameworks/native/+/master/libs/binder/ProcessState.cpp) and Android [ANR diagnosis](https://developer.android.com/topic/performance/vitals/anr). |

#### P1 — High-impact precision and currency work

1. **Remove “Staff Rule” absolutism.** Search results contain many `always`, `never`, `guarantee`, “mathematically impossible,” and fabricated numerical thresholds. Retain genuine security/protocol invariants, but rewrite preferences as defaults with assumptions, exceptions, and evidence. Start with `principles/design-for-failure.md`, `principles/determinism.md`, `principles/optimize-for-change.md`, Android observability, testing, transport, and push chapters.
2. **Separate fact, heuristic, and example.** Statements such as inheritance deeper than two levels being “almost always a mistake,” every network exception going to Crashlytics, screenshot tests always belonging on the JVM, and every WebSocket closing in `onStop()` can be useful defaults only when labeled and bounded. Each decision should name workload, lifecycle, privacy, and operational constraints.
3. ✅ **Expand the Currency Watchlist (2026-08-03).** Replaced incidental `compileSdk`/`targetSdk` values with current-project version-catalog aliases; retained lesson-specific floors. Added rows for Compose Navigation, CI/CD toolchain/plugin compatibility, signing policy/tool availability, and App Bundle delivery/size policy. Compose Runtime and Compose Multiplatform were already tracked; `principles/progressive-disclosure.md` no longer needs a row after its incidental value became symbolic.
4. ✅ **Fix Navigation terminology (2026-08-03).** Named Navigation Compose 2.x and Navigation 3 as separately maintained stable lines, removed stale “Current Stable” and `2.8+` labels from current guidance, and moved release-channel currency to the watchlist. Validated against [Navigation releases](https://developer.android.com/jetpack/androidx/releases/navigation) and [Navigation 3 releases](https://developer.android.com/jetpack/androidx/releases/navigation3).
5. ✅ **Audit Ktor engine claims (2026-08-03).** Removed the unsupported Android-engine deprecation and OkHttp-default claims, documented dependency-driven engine selection and current capability differences, added nearby primary documentation, and added the file to the watchlist. Validated against [Ktor client engines](https://ktor.io/docs/client-engines.html), the [`Android` engine API](https://api.ktor.io/ktor-client-android/io.ktor.client.engine.android/-android/index.html), and [Ktor releases](https://ktor.io/docs/releases.html).
6. **Reconcile duplicate transport decisions.** `backend-for-mobile/sse-vs-websockets.md` and `backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md` overlap substantially. Give one canonical ownership of SSE/WebSocket mechanics and make the other an application/decision that links rather than reteaches handshakes, background behavior, and retry.
7. **Reconcile tracing ownership.** `observability/distributed-tracing.md`, `observability/tracing.md`, and the bridge at `distributed-systems/distributed-tracing.md` risk three explanations of the same propagation model. Define one owner for trace context, sampling, and spans; keep mobile instrumentation and distributed-systems implications as applications.
8. **Make GraphQL chapters consistent.** `android/networking-and-security/graphql.md`, `backend-for-mobile/graphql-vs-rest.md`, and `backend-for-mobile/api-design-for-mobile.md` currently teach overlapping error/versioning rules with different precision. Establish one contract model and cross-link it.
9. **Correct telemetry taxonomy repository-wide.** “Analytics,” “Crashlytics,” logging, non-fatals, metrics, and traces are sometimes used as interchangeable destinations. Add a canonical signal-selection matrix covering product events, operational events, exceptions, logs, metrics, traces, privacy classification, cardinality, sampling, and deletion.
10. **Replace untestable marketing prose.** Phrases such as “easy,” “brutal,” “ruthlessly,” “instantly,” “incredibly,” “agonizingly,” “bulletproof,” and “only way” obscure mechanisms and weaken credibility. A technical handbook should say what fails, under which condition, how it is observed, and what mitigation costs.

#### P1 — Source and evidence deficiencies

The source distribution is uneven. Android has 249 links to a primary-ish platform/language domain across 101 topic files, while backend-for-mobile has 1 across 8 files, distributed systems 0 across 12, reference architectures 0 across 8, and the principles/patterns trees almost none. Eighty-four Markdown files have no `## Further Reading`; some are indexes or bridges, but the list also includes all eight reference architectures, nearly all mobile-system-design applications, most release chapters, four security chapters, and several KMP topics.

Required standard:

- Every externally falsifiable platform, protocol, language, compiler, runtime, library, or policy claim has a nearby primary source or a clearly mapped `Further Reading` entry.
- Every number states its provenance, measurement environment, and whether it is an example, target, or platform limit.
- Every third-party library recommendation names the evaluated version/date, maintenance and security posture, exit strategy, and official documentation.
- Reference architectures cite the official constraints they rely on, even though the architecture itself is an informed design.
- General distributed-systems chapters prefer original papers/specifications or authoritative project docs over Wikipedia and secondary explainers; HTTP uses current RFCs, observability uses W3C/OpenTelemetry specs, and Android behavior uses developer.android.com/AOSP.
- `example.com` and `api.example.com` remain acceptable inside illustrative code but must not be counted as evidence. Medium and vendor marketing may be optional experience reports, never the sole support for a factual claim.

#### P1 — Missing Staff-level curriculum depth

The repository is broad, but “read everything = operate at Staff level” is not yet defensible. Add or deepen these cross-cutting competencies without creating duplicate canonical owners:

- **Architecture economics:** option value, cost of delay, build-versus-buy, staffing/ownership cost, migration ROI, and measuring whether an architecture change worked.
- **Fleet reality:** OEM behavior, low-RAM devices, locale/network/device distributions, rooted/compromised devices, long-tail old versions, and evidence-based compatibility policy.
- **API/library stewardship:** binary/source/behavioral compatibility, semantic versioning limits, deprecation telemetry, API review, consumer fixtures, and emergency rollback for SDKs.
- **Data governance:** retention/deletion, consent transitions, subject requests, data lineage, telemetry minimization, regional routing, backups, and incident evidence—not legal conclusions masquerading as universal GDPR rules.
- **Supply-chain security:** dependency provenance, SBOMs, signing/attestation boundaries, secret exposure response, malicious SDK review, reproducible-build limitations, and Play Integrity threat-model limits.
- **Production experimentation:** sample-ratio mismatch, guardrails, novelty/peeking, interference, assignment persistence across devices, exposure logging, and ethical/privacy review.
- **Accessibility and internationalization validation:** automated versus manual limits, TalkBack/switch/keyboard testing, bidirectional text, pseudolocales, font scaling, and release gates tied to representative journeys.
- **Incident learning:** mobile-specific detection delay, bad-version cohort isolation, privacy-safe diagnostics, hotfix versus kill-switch decision, post-incident corrective-action ownership, and effectiveness review.
- **Organizational design:** team API boundaries, platform adoption incentives, paved-road product management, RFC/ADR lifecycle, reversible decisions, conflict resolution, succession, and avoiding Staff-engineer bottlenecks.
- **Hands-on assessment:** capstones with artifacts and rubrics. Probing questions alone do not prove the reader can author an RFC, diagnose Perfetto/system traces, lead a rollout incident, design a migration, or defend an SLO and cost model.

#### P2 — Pedagogy, consistency, and maintainability

1. Add a short **scope/version/assumptions** block to application and blueprint files.
2. Add **evidence-backed worked cases** with competing options, rejected alternatives, rollout, observability, failure injection, and post-launch measurement. Many current examples jump directly to an idealized answer.
3. Add **anti-answer rubrics**: what a plausible but unsafe design says, how a reviewer detects it, and what evidence changes the decision.
4. Make diagrams traceable to prose invariants and failure cases; diagram rendering is syntax validation, not semantic validation.
5. Add executable samples or separately tested companion projects for code whose exact API syntax is instructional. Uncompiled snippets silently rot.
6. Replace “Junior engineer”/“Staff engineer” caricatures with decision-quality language. Seniority is not evidence; assumptions, mechanisms, and outcomes are.
7. Define editorial rules for units, percentile notation, API-level formatting, Kotlin style, capitalization (`machine code`, `username`), and vendor-neutral terminology.
8. Add an issue identifier and owner to every audit item. A completed-roadmap narrative without owners, acceptance tests, or review records cannot prove closure.

#### Recommended execution order and exit criteria

| Phase | Work | Exit criteria |
|---|---|---|
| 1 — Stop teaching known errors 🟡 | Candidate P0 edits now cover introductions, diagrams, examples, failure modes, Staff guidance, questions, and answer keys in the affected chapters; independent verification remains pending. | Two reviewers, including one domain owner; official-source verification; contradiction search; docs and visual checks green. |
| 2 — Claim inventory | Generate a machine-readable inventory of versions, deadlines, numbers, absolutes, deprecations, and external links. | Every hit classified as invariant, sourced fact, heuristic, example, or defect; fast-moving facts enter the watchlist. |
| 3 — Domain review | Review Android/AOSP, Kotlin/KMP, backend/protocols, security/privacy, observability, distributed systems, release, and leadership as separate batches. | Named qualified reviewer; checklist and disposition log; no unowned factual claims; cross-tree contradiction scan. |
| 4 — Staff outcomes | Add capstones and rubrics spanning architecture, production operations, organizational influence, economics, and migration. | A learner produces reviewable artifacts and can be assessed against explicit evidence-based criteria. |
| 5 — Sustainable governance | Enforce source classes, freshness, snippet compilation where feasible, terminology, and review ownership in CI/review templates. | Quarterly currency SLO, domain-owner rotation, sampled factual audit, and defect escape-rate dashboard. |

**Definition of “world class.”** Green Markdown checks, file length, and diagram count are hygiene, not quality. The playbook reaches the goal only when representative Staff Android engineers can use it to make and explain production decisions, independent domain experts find no material factual errors in sampled chapters, versioned claims remain current within a published SLO, exercises assess real artifacts, and maintainers can trace important claims to primary evidence.

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
| `security/privacy-sandbox.md` | Phaseout status, what remains supported | privacysandbox.google.com/overview/status | 2026-10-01 |
| `security/certificate-pinning.md` | Network Security Config pin expiry, stack coverage, and Cronet pin API | developer.android.com/privacy-and-security/security-config + developer.android.com/develop/connectivity/cronet/reference/org/chromium/net/CronetEngine.Builder | 2026-10-01 |
| `mobile-system-design/security-and-privacy.md` | Network Security Config pin expiration and cleartext policy behavior | developer.android.com/privacy-and-security/security-config + developer.android.com/guide/topics/manifest/application-element.html | 2026-10-01 |
| `observability/metrics.md` | Firebase Performance automatic trace setup and supported HTTP/S libraries | firebase.google.com/docs/perf-mon/get-started-android + firebase.google.com/docs/perf-mon/troubleshooting | 2026-10-01 |
| `release-engineering/16kb-page-sizes.md` | Play deadlines, AGP/NDK version floors, backcompat behavior | developer.android.com/guide/practices/page-sizes | 2026-10-01 |
| `mobile-system-design/play-billing-and-subscriptions.md` | PBL current version, PBL 8+ deadline, replacement-mode APIs | developer.android.com/google/play/billing/release-notes | 2026-07-15 |
| `android/media/media3-player-architecture.md` | Media3 version, Compose UI artifact split | developer.android.com/jetpack/androidx/releases/media3 | 2026-10-01 |
| `android/compose/form-factors-matrix.md` | Wear/TV/Glance artifact versions and stability, car category rules | developer.android.com/jetpack/androidx/releases + developer.android.com/training/cars/whats-new | 2026-10-01 |
| `android/compose/stability.md` | Compose compiler behavior (Strong Skipping), collections-immutable version | developer.android.com + kotlinlang.org | 2026-07-15 |
| `android/compose/compose-navigation.md` | Navigation 2 and Navigation 3 stable/prerelease channels, maintenance status, typed-route and multiplatform capability boundaries | developer.android.com/jetpack/androidx/releases/navigation + developer.android.com/jetpack/androidx/releases/navigation3 | 2026-08-03 |
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
| `android/kotlin-multiplatform/tooling/ios-distribution.md` | XCFramework tasks/slices, direct/CocoaPods/SwiftPM integration, binary checksums, exported dependency behavior | kotlinlang.org/docs/multiplatform/multiplatform-ios-integration-overview.html + multiplatform-build-native-binaries.html + multiplatform-spm-export.html | 2026-07-30 |
| `android/kotlin-multiplatform/binary-compatibility-api-evolution.md` | Kotlin ABI-validation DSL/tasks, KLib guarantees, Swift export stability, version-overload and deprecation behavior | kotlinlang.org/docs/gradle-binary-compatibility-validation.html + api-guidelines-backward-compatibility.html + kotlin-evolution-principles.html | 2026-07-30 |
| `android/kotlin-multiplatform/production/testing-and-mocking.md` | Kotlin/Android test source-set names, runner/task behavior, coroutine test API, Compose UI test API, mocking-library target support | kotlinlang.org/docs/multiplatform/multiplatform-run-tests.html + developer.android.com/kotlin/multiplatform/plugin + official library documentation linked in the topic | 2026-07-30 |
| `android/kotlin-multiplatform/kmp-observability-crash-symbolication.md` | Kotlin/Native crash bridge requirements (CrashKiOS), SKIE error mapping, R8 mapping configs | touchlab.github.io/CrashKiOS + skie.touchlab.co + developer.android.com/studio/build/shrink-code | 2026-07-30 |
| `android/kotlin-multiplatform/production/ci-cd-for-kmp.md` | GitHub Actions macOS runner pricing ratio, KMMBridge plugin versions and SPM integration | github.com/pricing + touchlab.co/kmmbridge | 2026-07-30 |
| `android/kotlin-multiplatform/ecosystem/networking-with-ktor.md` | Ktor engine capabilities (Darwin vs OkHttp), proxy/TLS protocol negotiation | ktor.io/docs/client-engines.html | 2026-07-30 |
| `android/kotlin-multiplatform/production/concurrency-and-memory.md` | Kotlin/Native memory manager flags, GC allocators (mimalloc), kotlinx-coroutines 1.7.0 behavior, Swift Export Alpha status, Flow bridging | kotlinlang.org/docs/native-memory-manager.html + kotlinlang.org/docs/native-swift-export.html + github.com/Kotlin/kotlinx.coroutines | 2026-07-30 |
| `android/testing/testing-strategy.md` | GMD/ATD APIs, sharding property (experimental namespace) | developer.android.com/studio/test/gradle-managed-devices | 2026-07-15 |
| `android/testing/ui-testing.md` | Compose Preview Screenshot Testing plugin status, version, and requirements | developer.android.com/studio/preview/compose-screenshot-testing | 2026-07-29 |
| `android/networking-and-security/ktor-vs-retrofit.md` | Ktor client engine support matrix and Android/API-level floors | ktor.io/docs/client-engines.html | 2026-08-03 |
| `kotlin/version-updates/` (all digests) | Release-delta claims by construction | kotlinlang.org release notes | 2026-07-15 |
| `release-engineering/ci-cd-for-mobile.md` | AGP/Gradle compatibility, Compose BOM, AndroidX Benchmark/Baseline Profile, and publishing/testing plugin versions | developer.android.com/build/releases/gradle-plugin + developer.android.com/develop/ui/compose/bom + developer.android.com/jetpack/androidx/releases/benchmark | 2026-08-03 |
| `release-engineering/code-signing.md` | Play App Signing policy, signing-scheme guidance, Build Tools availability, and AGP signing defaults | support.google.com/googleplay/android-developer/answer/9842756 + developer.android.com/tools/releases/build-tools | 2026-08-03 |
| `release-engineering/app-bundles.md` | Play App Bundle requirements, Play Feature/Asset Delivery behavior, compressed download limits, and AGP dynamic-feature configuration | developer.android.com/guide/app-bundle/faq + developer.android.com/guide/playcore/feature-delivery + developer.android.com/build/releases/gradle-plugin | 2026-08-03 |
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
3. ✅ **2026 currency** (PR #6): `mobile-system-design/on-device-ai.md` (Gemini Nano/AICore/ML Kit GenAI layering, LiteRT + CompiledModel API, on-device vs cloud routing, fleet-coverage fallback) + `security/privacy-sandbox.md` — rewritten from the original plan after online verification: Privacy Sandbox on Android was deprecated 2025-10-17, so the file covers the phaseout, what replaces it, and the platform-bet lessons + `release-engineering/16kb-page-sizes.md` (16 KB support for API 35+ targets; the originally announced 2025-11-01 Play deadline was later moved to 2027-02-01; ELF + zip alignment, AGP 8.5.1/NDK r28 floors, CI gate, 16 KB emulator testing).
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

- 299 Mermaid diagrams render successfully through the pinned Mermaid CLI.
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
