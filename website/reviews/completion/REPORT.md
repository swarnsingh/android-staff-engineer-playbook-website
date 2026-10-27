# Android and Kotlin completion review

The retained backlog is resolved for final owner/Gemini review. It covers **515 review entries**: 295 Kotlin triage rows, 206 numbered Android findings across nine phases, and 14 candidate/note/teaching follow-ups. These entries overlap and include non-defects; the count is not a count of distinct bugs. The [ledger](backlog.json) records 435 verified-fix dispositions, 42 already-applied dispositions and 38 justified no-change decisions, with primary evidence for every entry.

The website now applies **743 exact replacements across 84 chapters**, including the previous 86 replacements. The canonical 743 are in [corrections-z-completion.json](../../content/corrections-z-completion.json). Incorrect active explanations and repeated answers were corrected together. Some earlier Kotlin Reject decisions were superseded after checking the actual compiler/API contract; the old triage is retained as history. Original website Markdown remains the hash-checked snapshot, and the same corrected lesson text is merged into the original repository by the owner in [source PR #57](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/57). Source-only reference lists are the only permitted alignment difference. [Sync provenance](source-sync.json) pins the 743 records to merged commit b8b56170e3b78f26ad73807b626acfb9530deb47.

The [public reader](https://swarnsingh.github.io/android-staff-engineer-playbook-website/) and [design-system gallery](https://swarnsingh.github.io/android-staff-engineer-playbook-website/design-system/) use one website repository and its GitHub Pages workflow. [Website PR #1](https://github.com/swarnsingh/android-staff-engineer-playbook-website/pull/1) contains the implementation and evidence. Source PR #57 was merged by the owner as b8b56170e3b78f26ad73807b626acfb9530deb47; website PR #1 remains available for review. The original source repository remains private, unrelated local work is preserved, and the cancelled restart automation remains paused.

## What was resolved

- Kotlin language/JVM claims: constants, nullability, smart casts, inline/reified behavior, value-class boxing, generic variance, Java overloads/visibility and bytecode. Allocation and optimizer claims now distinguish source representation from runtime allocation.
- Coroutine contracts: cancellation ownership, supervision/error handling, bounded channel and Flow behavior, scheduler deadlines and finite versus continuing test collections. The upload batch example restores failed/cancelled work and releases ownership, while explicitly requiring a durable outbox/idempotency for stronger delivery guarantees.
- Android state/data/DI: lifecycle and process-death distinctions, constructors and binding ownership, saved state, Room/DataStore migration/backup contracts, Paging result types and custom Hilt component creation.
- Compose: public snapshot APIs, phase-specific invalidation, strong skipping and immutable element contracts, modifier order, adaptive layout and supported widget/navigation behavior.
- Networking/security/media: Retrofit converter/request boundaries, Ktor result/retry policy and imports, callback capability races, WebView trust/navigation/cookie/renderer recovery, DRM entitlement and state-dependent decoder ownership.
- Testing/performance/build/KMP: matching JUnit lifecycle and Hilt fake bindings, real accessibility/idling APIs, clock versus external-work synchronization, conditional service/power limits, startup/render/ANR contracts, reproducible measurement rather than invented gains, Gradle task/cache/settings-plugin behavior, KSP discovery, Native/Apple build boundaries, export-specific cancellation and symbol packaging.
- All retained candidates and smaller notes have a disposition. The KSP consumer-classpath claim was corrected without inventing its missing reproduction. The dSYM guidance now depends on actual linkage/loaded images and matching UUIDs, rather than assuming every static XCFramework needs a separate framework dSYM. The former KMP templates and Phase 7 staff notes already have topic-specific mechanisms and decisions; their older pending descriptions are superseded.

220 resolved “awaiting owner approval” fragments were removed from active lessons. Held review fragments and phase reports remain archived history with an explicit current-status link. Seventeen full temporal scenes, 119 illustrated state sequences and static decision diagrams remain; a comparison or decision does not receive a fabricated transport animation.

## Verification

| Gate | Result and evidence |
|---|---|
| Source and website alignment | All 84 corrected chapters match before source-only reference lists; every retained entry has primary evidence |
| Static build/preservation | 125 pages, 15,564 original units in order, zero problems; 22 tampering fixtures remain effective |
| Final browser sweep | [125/125 pages](browser.json), 1,750 layouts, 8,880 illustrated states and 1,808 full-scene states; zero runtime/preservation/layout failures |
| Binder | [448 combinations](binder.json), zero problems |
| Playback/reduced motion | [13 motion regressions](motion.json), all pass |
| Gallery/navigation/reading controls | [69 checks](refinement.json), all pass |
| Real Android framework validation | [18 extracted fixture records](../../validation/android/fixtures.json), real Android/Hilt/Room/Compose/lifecycle/Ktor dependencies; Hilt and accessibility instrumentation examples compile |
| Runtime tests | [22 JVM/Robolectric tests](android-runtime.json), zero failures/errors, including two template ViewModel tests |
| Kotlin compiler/JVM | [Explicit fields, inline filter, direct field access, internal extension names and negative compilation](kotlin-compiler.txt); [six focused regressions](kotlin-regression.txt); [retained actor/boxing regressions](kotlin-actor.txt) |
| Shared-renderer regression | Three tests cover cross-cell correction marks, ordinary prose highlighting and fenced code |
| Documentation | Source link/anchor/index/answer/content gates and all 15 checker unit tests pass |
| Gradle plugin contract | Real settings plugin and explicit hook task compile and validate; no local hook installed or example cache contacted |
| Citation links | 266 incoming primary URLs checked; two stale URLs corrected to live owning-project documentation, with [repair evidence](primary-link-repairs.json) |

After the full sweep, the final consistency review corrected repeated explanations and synchronized the merged source inventory, including the updated citation anchors, tracing coordinate, startup documentation discrepancy and workflow authentication setup. The [delta record](render-deltas.json) identifies every affected page; the [16-page merged-source recheck](merged-sync-browser.json) covers all those pages in addition to the full repaired-renderer sweep.

The preservation gate caught a malformed correction mark spanning table cells in Coroutines after the broader content pass. The renderer now excludes partial table-row replacements from inline highlighting, retaining their section disclosure instead. All three renderer tests, the static build and the full browser sweep were repeated after that repair. [The earlier sweep](browser-before-renderer-fix.json) is retained as history, not the final proof.

## Gradle questions and bounded answers

Every command below ran through the installed `gradle-run` compact wrapper in workflow `fe76d123c6107442037e38f525c47fff`. No full Gradle logs are published. A final rerun after the merged-source sync uses the same real Android tasks. The nested Android tasks were `./gradlew :app:compileDebugKotlin`, `./gradlew :app:testDebugUnitTest` and `./gradlew :app:compileDebugAndroidTestKotlin`; the plugin probe used `./gradlew -p ../gradle-probe verifyDocumentationPlugins`. [The final bounded status](gradle-final-status.json) identifies its successful result.

| Quoted verification question | Bounded answer |
|---|---|
| “Does the Android validation project compile with Kotlin 2.4.21 and the real Android and Compose dependencies?” | Yes, compileDebugKotlin passed. |
| “Do the pinned Hilt and Room processors compile in the Android validation project?” | Yes, compileDebugKotlin passed with both real processors. |
| “Do the extracted lifecycle, state, snapshot, service, Room transaction and Hilt component examples compile with their real framework APIs?” | Yes after supplying the missing Dagger annotation import in the extraction context; run 4 passed. |
| “Do the corrected real-API fixtures and runtime regressions pass for Room atomicity, snapshots, upload recovery, lifecycle gating, scheduler boundaries and JVM overloads?” | Yes, the targeted runtime suite passed. |
| “Do the corrected Ktor client and result wrapper pass 401 mapping, retry safety and cancellation tests with Ktor MockEngine?” | Missing client imports were caught and fixed in the lesson; all four network regressions passed in the final run. |
| “Do the corrected Ktor fixtures and Compose input, merging and animation-clock contracts pass with the real libraries?” | The first run exposed a test observation error. After its repair, all these tests pass. |
| “Do all completion runtime regressions pass and do the extracted Hilt and accessibility instrumentation examples compile with their real processors and APIs?” | The initial run retained the animation-test failure; final run 9 passes both tasks. |
| “After correcting the test observation to read animation state during composition, do all runtime regressions pass and do the Hilt and accessibility examples compile?” | Yes: 22 tests, zero failures; instrumentation compilation passed. |
| “Do the corrected convention-plugin excerpts compile, configure the settings cache and register an explicit hook task without installing a hook?” | The compiler caught an unavailable Project.uri helper in the Settings plugin. The lesson now constructs java.net.URI explicitly. |
| “After replacing the unavailable Project.uri helper, do the convention plugins compile, configure the settings cache and register the explicit hook task without installing a hook?” | Yes, run 11 passed; no hook installed. |
| “After syncing merged PR 57 and the tracing artifact coordinate, do all runtime regressions and instrumentation compilation still pass?” | Yes: the final run passed all 22 runtime tests and instrumentation compilation. |

The animation-test repair reads the animated value during composition so updates invalidate the observed scope, and uses an explicit duration scale and clock. It does not hide a product failure by weakening the assertion.

## Scope of confidence

This closes the known retained review backlog. It is not an assertion that every sentence in 123 chapters was independently proved or every inherited excerpt is a standalone application. The [validation README](../../validation/README.md) identifies imports, enclosing context and application-owned helpers supplied around selected exact excerpts. Framework classes come from the real pinned libraries.

Chromium checks emulate layout widths; they are not physical phone/tablet, Safari/WebKit, screen-reader or accessibility-conformance certification. Instrumentation examples were compiled, not run on a device. No performance measurement, peripheral/camera, real FCM/Doze delivery, DRM-license, Apple simulator or particular XCFramework archive result is claimed. Full Xcode is not installed; Apple-specific boundaries and conditional symbol guidance follow official Kotlin/Apple/project contracts. Device/product release verification must use the actual application, toolchain and policy; it is not an unresolved factual correction hidden behind a passing build.

The Gradle workflow was finished after its successful final validation; finish removed only wrapper-owned logs. The bounded result and test artifacts above remain.

The website documentation CI initially applied its 400-word chapter floor to the 234-word validation runbook. The checker now records an explicit short-reference exemption, consistent with component/runbook references; no lesson floor was lowered. The documentation gate and all 15 checker tests were rerun.
