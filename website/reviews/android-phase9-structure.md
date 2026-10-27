# Phase 9 structure: Kotlin Multiplatform

Defined before authoring, 2026-10-25. This is the teaching plan, not a statement that the lessons are complete or independently reviewed. All 19 original chapters remain read-only and render in full. No technical correction is approved by this plan.

## Reader journey and boundaries

Begin with a product decision: two native apps implement the same business rule and drift apart. Decide which rule to share, prove the platform boundary, then follow the shared module through execution, Apple consumption, testing, distribution and operation. This is an optional specialisation; it must not imply every Android team needs KMP or shared UI.

Use a decision route for adoption topics, a boundary/request trace for library topics, and artifact/evidence routes for build and release topics. Do not force the coroutine chapter's story shape on all 19. Plain language continues through staff-level material. Keep the original internals, code, tradeoffs, questions and references; additions explain how those pieces connect.

| Chapter | Opening problem and sequence | Mechanism / visual | Production and staff decision |
|---|---|---|---|
| KMP decision matrix | Android and iOS calculate different prices → name the shared invariant → score a narrow pilot → measure → decide | Shareability boundary plus pilot/revisit trace | Ownership, rollback, opportunity cost; no universal adoption score |
| Overview and K1 vs K2 | A common function needs a platform service → common contract → target implementation → compilation | Source-set dependencies and target compilation; historical K1/K2 context remains labelled | Compiler upgrades and source portability are separate decisions |
| Shared domain boundaries | An Android exception leaks into an iOS screen → domain contract → explicit platform adapter → consumer policy | Error and dependency boundaries; one failure crossing the seam | Cancellation, time/IDs/randomness, small stable public surface |
| Architecture and module boundaries | Both teams want reuse but different UI → logic-only versus shared UI → platform hosts | Two ownership diagrams and an injected service trace | Team responsibilities, escape hatches and change cost |
| Build system and source sets | ARM64 framework works on a device but not the simulator → target identity → variant selection → packaging | Source visibility graph and distinct device/simulator slices | Pin a tested toolchain and inspect artifact identity |
| Libraries ecosystem | A dependency works on Android but breaks the proposed next target → target matrix → API policy → consumer probe | Common API boundary and dependency qualification sequence | Compatibility includes exports, tools, maintenance and size |
| Networking with Ktor | One shared repository needs two platform transports → common policy → engine → response/failure | Request through client/plugins/engine; cancellation ownership | Auth, timeout, partial migration and native integration tests |
| Persistence | Shared data rules need platform storage → schema/transactions → driver/builder → migration | Domain/store boundary; schema evolution and reopen trace | Data shape, platform support, secure storage and migration ownership |
| Dependency injection | Common code tries to construct an Android service → platform composition root → shared constructor | Runtime object graph versus compile-time availability | Manual wiring is an option; scope lifetime remains explicit |
| Compose Multiplatform | A shared screen has correct pixels but wrong platform interaction → sharing boundary → native host → acceptance gates | Host/screen/platform seams; input/accessibility journey | UI sharing requires platform behaviour, performance and release evidence |
| Resource sharing | A string is available in IDE but absent in consumer build → declarations → generated accessor → packaged resource | Resource build-to-consumer path | Localization, packaging and native UI access are separate concerns |
| Concurrency and memory | A shared object crosses threads safely but still leaks across Swift/Kotlin → current memory manager → ownership graph | Historical versus current model; retained cross-runtime references | Race safety, cancellation and memory ownership each need tests |
| Swift interop | Kotlin API compiles but is awkward or unsafe from Swift → export path → generated surface → consumer test | Established Objective-C bridge versus Swift export, explicitly version-scoped | Nullability, errors, coroutine observation and cancellation |
| iOS distribution | A framework builds locally but consumers cannot fetch/link it → slices → archive → package → Xcode | Artifact pipeline with source/build identity | Signing, checksums, export surface, ownership and release governance |
| Binary compatibility | A harmless-looking change breaks an older consumer → source/ABI/wire/behaviour dimensions → checks | Compatibility grid and old-consumer/new-library trace | Deprecation and mixed-version support windows |
| Testing and mocking | commonTest is green while the Apple integration fails → shared contract tests → adapter/consumer tests | Test matrix and one controlled failure path | What each target's evidence proves; no claim of universal mock portability |
| Observability and symbolication | A native crash has an address but no release identity → build IDs → symbols → verified crash report | Android R8 and Apple dSYM paths, kept distinct | Privacy, symbol retention, error taxonomy and ownership |
| CI/CD | Linux checks pass but Apple packaging is broken → shared checks → Mac jobs → cache → consumer artifact | Platform jobs/dependencies and artifact provenance | Cost, coverage, cache correctness and release gates |
| Adoption and migration | A rewrite proposal has no measurable goal → pilot → adapters → rollout → measure → continue/rollback | Incremental replacement sequence | Organisational cost, ownership and revisitable success criteria |

## Content, Q&A and accessibility

Questions and added checkpoints appear in Q&A; answers have a separate heading. Content carries the explanatory traces. Each temporal model has explicit controls and static steps; reduced motion preserves its meaning. Layout must reflow at phone/tablet/foldable/desktop widths with enlarged text. A browser sweep is evidence for the tested browser, not every OS or physical device.

## Sources and verification plan

Primary starting points: [KMP documentation](https://kotlinlang.org/docs/multiplatform.html), [hierarchical source sets](https://kotlinlang.org/docs/multiplatform/multiplatform-hierarchy.html), [Native memory management](https://kotlinlang.org/docs/native-memory-manager.html), [Objective-C/Swift interop](https://kotlinlang.org/docs/native-objc-interop.html), [Swift export](https://kotlinlang.org/docs/native-swift-export.html), [Compose Multiplatform](https://www.jetbrains.com/help/kotlin-multiplatform-dev/compose-multiplatform.html), [Ktor engines](https://ktor.io/docs/client-engines.html), and each original chapter's version-specific official references. Inspect relevant contracts before adding a claim; a link in this plan does not mean every linked page has already been verified.

The owner's *Manifest Android Interview*, Jaewoong Eum, edition 2025-06-16, was identified and its introduction and relevant networking/WebView pages read during Phase 5 preparation (PDF pp. 7, 184–188, 248–255). It supplies Android teaching questions, not authoritative coverage of these KMP-specific APIs. Do not cite it as proof of Swift export, Apple packaging or current KMP support.

For each chapter, record preservation/added coverage, sources actually read, original findings and any held teaching. Build and browser-check the integrated tree, then have an independent reviewer inspect technical claims and the planned narrative. Compiler/Apple runtime claims require their stated evidence; do not invent an Apple build or physical-device test.
