# Android Phase 7: original-content findings and evidence

**Completion update, 27 October 2026:** The owner authorized the remaining corrections. The findings below are the historical incoming review; current per-finding dispositions, primary sources and validation are in [the completion report](completion/REPORT.md) and [backlog ledger](completion/backlog.json). Website corrections are rendered through the approved overlay and the same text is proposed in source PR #57. Earlier “pending/unapproved/unchanged” statements describe the original review date.


Written 2026-10-25. **All findings are proposals only. Nothing is approved or applied.** Original Markdown is read-only. Neutral notes identify every affected H2 listed below; held explanatory replacements live in pending-android-phase7-teaching.blend. No Android framework build, device profile, benchmark measurement or hosted-preview validation was performed for this authoring pass.

## Coverage and method

Read all fifteen Phase 7 originals in full, plus rulebook §§16–19 and the handover. Added fifteen short openings, fifteen designed dependency/decision visuals, fifteen controlled four-step sequences and forty-five checkpoint questions. Numbers in added figures are illustrative calculations, not app benchmarks. Original diagrams remain in their normal renderer, in source order. Claims in the new layer were checked against current primary documentation; links appear in each blend. API documentation/source reasoning is distinguished from compilation: no new runnable Kotlin is introduced and no framework snippets were compiled.

## Companion book: actual pages read

Manifest Android Interview, Jaewoong Eum, user-supplied 2025-06-16 edition, 459 PDF pages. Fully extracted and read PDF **66–69** (printed 63–66, retention/ANRs), **107–108** (printed 104–105, ART/Dalvik/DEX), **111–114** (printed 108–111, R8/app size), **165–168** (printed 162–165, bitmap sizing/caching), and **235–238** (printed 232–235, Baseline Profiles/transition to business logic). Keyword-search hits on other pages were located, not read in full, and are not claimed as consultation. The book is a companion: its blanket modern-ART no-JIT statement and numerical/profile-install promises were not copied into teaching. Current primary contracts take precedence; one-eighth cache allocation is an example, not a universal safety guarantee.

## Pending original findings

### P7SU1 · P2 · android/performance/startup.md:153

**Affected H2 sections:** App Startup Library — Initialization Orchestration; Application.onCreate — The Silent Killer; Failure Modes; Answer Key.

**Original anchor:** `**Lazy by default.**`.

**Finding:** The shown manifest metadata opts these initializers into automatic startup execution. Consolidating providers does not itself defer their work. The later eager-init paragraph also places provider initialisation inside Application.onCreate although providers initialise earlier.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/libraries/app-startup). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, distinguish automatic provider initialisation from explicitly disabled discovery plus manual lazy initialisation. Explain that lazy dependencies can still be reached through an eager initializer.

### P7SU2 · P2 · android/performance/startup.md:186

**Affected H2 sections:** Activity.onCreate Optimization; Patterns That Help.

**Original anchor:** `// Anything else: defer`.

**Finding:** lifecycleScope.launch is not a background or after-first-frame boundary. Main.immediate can begin this work inline on Main.

**Evidence:** [Primary contract/source](https://developer.android.com/reference/androidx/lifecycle/LifecycleKt). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, use a genuinely deferred, lifecycle-correct boundary and appropriate dispatcher for the specific work. Keep first-frame timing explicit.

### P7SU3 · P2 · android/performance/startup.md:479

**Affected H2 sections:** Patterns That Help.

**Original anchor:** ``postFrameCallback` defers to after the first frame draws.`.

**Finding:** The callback is scheduled for the next frame, on the Looper thread; it is not an after-draw or background guarantee. Work there can delay frame traversal.

**Evidence:** [Primary contract/source](https://developer.android.com/reference/android/view/Choreographer#postFrameCallback(android.view.Choreographer.FrameCallback)). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, remove the after-draw/background promise and show a verified completion boundary appropriate to the intended work.

### P7SU4 · P2 · android/performance/startup.md:22

**Affected H2 sections:** Three Startup Types; Diagnosing Slow Startup.

**Original anchor:** `Anything above ~1500ms`.

**Finding:** The stated cold slow-start threshold and 5% alert policy are not established Play Vitals contracts. The current Play help distinguishes cold/warm/hot slow-start definitions; product budgets must be labelled separately.

**Evidence:** [Primary contract/source](https://support.google.com/googleplay/android-developer/answer/9844486?hl=en). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, use current documented Vitals definitions with a date and separate illustrative product budgets from platform reporting thresholds.

### P7SU5 · P2 · android/performance/startup.md:233

**Affected H2 sections:** Baseline Profiles — AOT Compilation for Hot Paths; Common Pitfalls; Answer Key.

**Original anchor:** `First launches see no AOT compilation`.

**Finding:** This contradicts profile-guided installed-code execution. AOT/JIT performance is workload dependent; the unconditional 20–40%/200–400ms gains, fixed generated path and one compilation state as the universal first launch are not guaranteed.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/baselineprofiles/overview). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, reuse the conditional explanation in the canonical Baseline Profiles chapter: verify packaged rules, installation and compilation, then measure the journey. Label observed sample results with their setup.

### P7SU6 · P2 · android/performance/startup.md:438

**Affected H2 sections:** Patterns That Help.

**Original anchor:** `suspend fun observe(): Flow<Theme>`.

**Finding:** The non-suspending composable calls a suspend function to obtain its Flow. That call is not valid Kotlin merely because the result is collected later.

**Evidence:** [Primary contract/source](https://kotlinlang.org/docs/composing-suspending-functions.html). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, make the flow-producing accessor non-suspending or obtain it in an appropriate coroutine/state owner. Compile the exact corrected snippet with its actual declarations.

### P7SU7 · P2 · android/performance/startup.md:498

**Affected H2 sections:** Failure Modes.

**Original anchor:** `adb install --apex`.

**Finding:** --apex is for APEX packages, not a way to install an ordinary application APK with a Baseline Profile. This does not repair profile installation.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/baselineprofiles/overview). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, use the supported profile installation/verification or Macrobenchmark workflow for the Android version and installer path.

### P7SU8 · P2 · android/performance/startup.md:18

**Affected H2 sections:** Three Startup Types.

**Original anchor:** `swiped from recents, Doze`.

**Finding:** Removing a task and entering Doze do not universally kill the process. Cold/warm/hot is determined from actual process and Activity state, not these actions alone.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/issues/launch-time). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, describe the state that defines each start and treat user actions as conditional examples, not deterministic process-kill mechanisms.

### P7SU9 · P3 — evidence/API clarification · android/performance/startup.md:566

**Affected H2 sections:** Answer Key.

**Original anchor:** `This introduces a synchronous network/disk I/O block`.

**Finding:** The hypothetical remote-config call has no API/signature here. An asynchronous SDK fetch does not become synchronous network I/O merely because it is invoked during onCreate; dependencies can still delay readiness.

**Evidence:** [Primary contract/source](https://firebase.google.com/docs/remote-config/get-started?platform=android). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, identify the concrete API and whether code awaits/blocks its result; separate launch dependency from synchronous execution.

### P7SU10 · P3 — evidence/API clarification · android/performance/startup.md:40

**Affected H2 sections:** The Cold-Start Pipeline; App Startup Library — Initialization Orchestration; Baseline Profiles — AOT Compilation for Hot Paths.

**Original anchor:** `Typical cost (cold)`.

**Finding:** Unattributed typical stage timings and fixed App Startup/Profile gains are presented without a workload, device, build or measurement record. They are not reproducible evidence for this repository.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/issues/launch-time). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, label these as illustrative only or replace them with actual reproducible measurements. Remove universal “single biggest” or “free perf” conclusions unsupported by the setup.

### P7JK1 · P2 · android/performance/jank.md:9

**Affected H2 sections:** Overview; First Principles; Mental Model; Answer Key.

**Original anchor:** `Main Thread has exactly **16.6ms**`.

**Finding:** A display interval is not a universal exact Main-thread allowance. App/GPU/system pipelines overlap and actual expected frame intervals determine deadlines; the same arithmetic does not identify the responsible stage.

**Evidence:** [Primary contract/source](https://perfetto.dev/docs/data-sources/frametimeline). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, scope arithmetic as a simplified refresh interval and diagnose expected versus actual frame/presentation evidence, preserving pipeline overlap.

### P7JK2 · P2 · android/performance/jank.md:122

**Affected H2 sections:** Historical Context; Internal Mechanics (Jetpack Compose); Production Example; Probing Questions; Answer Key.

**Original anchor:** `Compose *always* recomposes`.

**Finding:** Strong skipping permits restartable functions with unstable arguments to be skipped. An invalidated parent also does not force every heavy child to execute; the immutable annotations are contracts, not unconditional repairs for mutable data.

**Evidence:** [Primary contract/source](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, state the compiler/configuration assumptions, distinguish invalidation from actual child execution and honour observable/immutable data contracts before annotations.

### P7JK3 · P2 · android/performance/jank.md:77

**Affected H2 sections:** Internal Mechanics (Jetpack Compose).

**Original anchor:** `Modifier.offset(y = offset.dp)`.

**Finding:** ScrollState.value is a pixel offset. Reinterpreting it as dp changes the visual result with density, while the lambda variant uses pixels. These are not equivalent before/after effects.

**Evidence:** [Primary contract/source](https://developer.android.com/develop/ui/compose/performance/bestpractices). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, convert pixel offset using density in the composition variant, then compare with the pixel-based IntOffset variant.

### P7JK4 · P2 · android/performance/jank.md:185

**Affected H2 sections:** Failure Modes; Probing Questions; Answer Key.

**Original anchor:** `instantiating objects inside an `onDraw` method guarantees dropped frames`.

**Finding:** Allocation churn can contribute to latency, but a single allocation or a fixed claimed pause does not guarantee a missed frame. The given object rates and 5–10ms pauses are not measured here.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/memory-overview). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, describe allocation pressure as a measured risk and remove unsupported fixed rates, pause lengths and guarantees.

### P7JK5 · P2 · android/performance/jank.md:150

**Affected H2 sections:** Failure Modes.

**Original anchor:** `release { debuggable true }`.

**Finding:** A debuggable release build changes performance characteristics; the quoted repair conflicts with the release-equivalent non-debuggable profileable benchmarking guidance.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, use the supported non-debuggable profileable release-equivalent target and document deviations from the shipped artifact.

### P7JK6 · P2 · android/performance/jank.md:212

**Affected H2 sections:** Common Misconceptions; Answer Key; Further Reading.

**Original anchor:** `A 5000ms blockage triggers an ANR`.

**Finding:** ANR triggering depends on a monitored operation and its applicable timeout; it is not an unconditional stopwatch for every block. ANR handling is also not universally an OS-level crash.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, qualify input dispatch versus component ANRs and remove claims that arbitrary five-second blocks always produce the same dialog/crash behavior.

### P7RD1 · P2 · android/performance/rendering.md:41

**Affected H2 sections:** The Three Phases the App Owns; Compose vs Views — Different Pipelines; Real Android Patterns; Answer Key.

**Original anchor:** `For Compose: a single layout pass per recomposition.`.

**Finding:** Composition, layout and drawing are independently invalidated. The table’s redraw/re-measure triggers, per-composable display-list cache, direct Skia backend and universal less-than-half-time comparison overstate the architecture. drawWithCache also invalidates on observed state changes, not size alone.

**Evidence:** [Primary contract/source](https://developer.android.com/develop/ui/compose/phases). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, explain independent phase reads/invalidation and the Android rendering host path. Remove unmeasured universal speed comparisons and describe draw cache invalidation accurately.

### P7RD2 · P2 · android/performance/rendering.md:135

**Affected H2 sections:** Vsync and Choreographer; Answer Key.

**Original anchor:** `vsync N+2`.

**Finding:** The exact N+1/N+2 presentation formula is not established from UI duration alone. Buffering, expected frame deadlines, rendering and system presentation matter.

**Evidence:** [Primary contract/source](https://perfetto.dev/docs/data-sources/frametimeline). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, use expected/actual frame evidence and label any fixed-vsync timeline as an explicitly scoped illustrative model.

### P7RD3 · P2 · android/performance/rendering.md:274

**Affected H2 sections:** RecyclerView / LazyColumn — Where Rendering Matters Most; Answer Key.

**Original anchor:** “onCreateViewHolder runs once per item type”.

**Finding:** A holder is created whenever a new instance is needed, including multiple holders of the same type. setHasFixedSize concerns the RecyclerView’s overall size, not fixed item sizes or eliminating every measure pass.

**Evidence:** [Primary contract/source](https://developer.android.com/reference/androidx/recyclerview/widget/RecyclerView.Adapter). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, describe holder creation/reuse and the overall-size contract accurately; measure rather than guarantee a skipped entire pass.

### P7RD4 · P2 · android/performance/rendering.md:291

**Affected H2 sections:** RecyclerView / LazyColumn — Where Rendering Matters Most; Failure Modes; Answer Key.

**Original anchor:** `Without it, Compose treats every row as a different type`.

**Finding:** The default contentType is null, so items share a compatible type rather than each receiving a unique type. Keys preserve identity/state but are not an unconditional no-recomposition guarantee.

**Evidence:** [Primary contract/source](https://developer.android.com/develop/ui/compose/performance/bestpractices). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, describe explicit contentType as separating compatible structures; distinguish keys, state movement and skipping.

### P7RD5 · P2 · android/performance/rendering.md:385

**Affected H2 sections:** Real Android Patterns.

**Original anchor:** `size(Size.ORIGINAL)`.

**Finding:** The request explicitly asks for original size but the following explanation promises display-size downsampling. The shown code does not demonstrate that claim.

**Evidence:** [Primary contract/source](https://coil-kt.github.io/coil/compose/). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, remove the original-size override or provide the intended pixel constraints, with density/crop and library version stated.

### P7RD6 · P2 · android/performance/rendering.md:404

**Affected H2 sections:** Real Android Patterns.

**Original anchor:** `key = { it.id() }`.

**Finding:** The shown FeedItem declarations have subtype id properties but no common id() function. This snippet is incomplete as standalone Kotlin, unlike its apparent ready-to-use presentation.

**Evidence:** [Primary contract/source](https://kotlinlang.org/docs/interfaces.html). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, add a common id property or a defined exhaustive extension and adjust the key call consistently; compile the corrected declarations together.

### P7RD7 · P2 · android/performance/rendering.md:313

**Affected H2 sections:** SurfaceFlinger and Layers.

**Original anchor:** `TextureView` paints to a regular layer (cheaper than `SurfaceView``.

**Finding:** SurfaceView versus TextureView has workload/composition tradeoffs; TextureView is not universally cheaper. A Surface is a producer/consumer buffer interface, not just one allocation, and z-order does not universally bypass composition.

**Evidence:** [Primary contract/source](https://source.android.com/docs/core/graphics/surfaceflinger-windowmanager). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, explain buffer queues and device/workload-specific composition cost without a universal cheaper/bypass claim.

### P7RD8 · P3 — evidence/API clarification · android/performance/rendering.md:327

**Affected H2 sections:** Vulkan vs OpenGL ES.

**Original anchor:** `Vulkan reduces per-frame CPU cost by ~5–15%`.

**Finding:** No reproducible measurement supports that gain or the claim about the default on most Android 12+ devices. Backend choice depends on device/build, not just OS release.

**Evidence:** [Primary contract/source](https://developer.android.com/develop/ui/views/graphics/hardware-accel). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, record backend and device/build assumptions and remove unsupported fixed improvements. Validate target-device traces rather than infer a fleet default.

### P7RD9 · P2 · android/performance/rendering.md:471

**Affected H2 sections:** Common Rendering Bottlenecks; Failure Modes; Common Pitfalls.

**Original anchor:** `long-running work needs `Dispatchers.IO``.

**Finding:** CPU-heavy computation should not automatically be dispatched to IO; use an appropriate dispatcher. A scope such as viewModelScope alone also does not move heavy work off Main.

**Evidence:** [Primary contract/source](https://developer.android.com/kotlin/coroutines/coroutines-best-practices). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, distinguish blocking I/O from CPU work and make the main-safe work boundary explicit. Avoid universal hardware-bitmap and clip-to-outline fixes without checking their contracts.

### P7AN1 · P2 · android/performance/anrs.md:22

**Affected H2 sections:** Overview; Historical Context; Mental Model; Failure Modes; Common Misconceptions; Answer Key; Further Reading.

**Original anchor:** `BroadcastReceiver Timeout:** 10 seconds`.

**Finding:** Receiver/service deadlines vary by component flags, OS and CPU starvation. ANRs need not freeze/kill the process or show the same dialog. The kernel/ActivityManager attribution and identical Play penalty claim are inaccurate; user-perceived and overall rates differ.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, qualify each monitored operation, use current documented AOSP defaults and separate observed user impact, process state and platform reporting.

### P7AN2 · P2 · android/performance/anrs.md:25

**Affected H2 sections:** Historical Context; Further Reading.

**Original anchor:** `deprecated `SharedPreferences``.

**Finding:** SharedPreferences is discouraged for many uses but its public interface is not marked deprecated; DataStore is not Google-mandated for every app.

**Evidence:** [Primary contract/source](https://developer.android.com/reference/android/content/SharedPreferences). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, distinguish recommendation and tradeoff from formal API deprecation or mandate.

### P7AN3 · P2 · android/performance/anrs.md:150

**Affected H2 sections:** Staff Engineer Thinking; Answer Key.

**Original anchor:** ``StrictMode` instantly crashes`.

**Finding:** Configured detection and penalties determine StrictMode behavior. penaltyLog does not imply penaltyDeath, and a claimed 90% catch rate has no measurement here.

**Evidence:** [Primary contract/source](https://developer.android.com/reference/android/os/StrictMode.ThreadPolicy.Builder). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, show a specific policy and describe exactly which violations/penalties it enables; remove the invented catch percentage.

### P7AN4 · P2 · android/performance/anrs.md:69

**Affected H2 sections:** Internal Mechanics.

**Original anchor:** `blocked on a `Mutex``.

**Finding:** If this means kotlinx.coroutines Mutex, lock() suspends without blocking its thread. That differs from a Java monitor/Lock or runBlocking bridge; the identifier must be qualified.

**Evidence:** [Primary contract/source](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.sync/-mutex/lock.html). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, use an actual blocking primitive for the Main-thread example, or explain the separate responsiveness/deadlock dependency of a suspended coroutine.

### P7MM1 · P2 · android/performance/memory-management-and-leaks.md:22

**Affected H2 sections:** Overview; Why It Matters; Historical Context; First Principles; Staff Engineer Thinking; Answer Key.

**Original anchor:** `It cleans up memory in the background without freezing the UI.`.

**Added after review:** the Staff Engineer Thinking bitmap passage places pixel data in the managed heap budget (“can instantly exhaust the strict heap budget”), but since Android 8.0 (API 26) “the bitmap pixel data is stored in the native heap” ([Manage bitmap memory](https://developer.android.com/topic/performance/graphics/manage-memory)). `OutOfMemoryError` is thrown by the runtime in the process, not by the OS (Overview).

**Finding:** Concurrent GC still has pauses. The next sentence says ART cannot clean up what it cannot reach, reversing the earlier reachability explanation. Active coroutines are not intrinsically separate GC roots; a managed heap cap is not a total-process-memory cap. Fixed 95% leak capture/instant OOM claims are not measured guarantees.

**Evidence:** [Primary contract/source](https://developer.android.com/topic/performance/memory-overview). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, distinguish strong reachability and actual roots, concurrent work with pause phases, managed heap versus total pressure, and conditional resource exhaustion.

### P7MM2 · P2 · android/performance/memory-management-and-leaks.md:197

**Affected H2 sections:** Internal Mechanics; Production Example; Answer Key.

**Original anchor:** `This safely kills any running coroutines`.

**Finding:** Lifecycle cancellation is cooperative and does not instantly kill arbitrary non-cooperative work or erase every retained reference. The Activity example also omits super.onCreate, and the Fragment onViewCreated override omits required parameters.

**Evidence:** [Primary contract/source](https://kotlinlang.org/docs/cancellation-and-timeouts.html). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, show valid lifecycle signatures/super calls and explain cancellation plus cleanup and reference release, without a guaranteed instant memory-recovery claim.

### P7MB1 · P3 — evidence/API clarification · android/performance/macrobenchmark-and-perfetto.md:115

**Affected H2 sections:** Custom Trace Sections.

**Original anchor:** `suspend fun loadFeed() = trace`.

**Finding:** The tracing API/import/version is unspecified around a suspend/withContext boundary. Classic synchronous Android trace sections must begin and end on the same thread; a suspend inline block can resume elsewhere. Current tracing releases provide coroutine-aware APIs, but this snippet does not identify one.

**Evidence:** [Primary contract/source](https://developer.android.com/jetpack/androidx/releases/tracing). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, name the chosen tracing dependency/import and use its documented coroutine-aware tracing or a correctly paired async section. Do not claim a framework build verified this snippet.

### P7TH1 · P2 · android/performance/thermal-low-end-device-strategy.md:31

**Affected H2 sections:** Thermal Status.

**Original anchor:** `private val listener = PowerManager.OnThermalStatusChangedListener`.

**Finding:** The API-29 listener is instantiated during construction, while only start/stop are annotated RequiresApi(29). Those annotations alone do not guard construction on an older supported OS.

**Evidence:** [Primary contract/source](https://developer.android.com/reference/android/os/PowerManager.OnThermalStatusChangedListener). This is a documentation/source comparison; no Android compilation or device measurement is claimed.

**Proposed repair, awaiting approval:** After approval, isolate and guard the whole API-29 implementation or require API29 for the class/instantiation boundary, with a declared fallback for older OS versions.

## Reviewed without a new original correction proposal

Baseline Profiles, Native Memory & Bitmaps, Battery & Power Profiling, Network Radio Wakeups, Logging, Crash Monitoring and Mobile APM & RUM received teaching layers without a new confirmed original correction proposal in this pass. This means no new material defect was established by the checks performed, not a guarantee that every original historical/statistical claim was independently re-experimented. The original logging/crash/RUM examples remain conceptual where their source declares them so.

## Authoring checks and limits

Marker, stepper, question-count, prose-budget and read-only snapshot results are recorded after the authoring validation below. Parent owns final integrated preservation, resource readiness, enlarged-text/browser checks, independent review, and private publication. Those results must be reported separately.

## Added after independent review (2026-10-26)

Each new finding has an **Under review** note before every listed H2. Coverage extensions to existing findings are noted in the affected blends: P7JK1 also covers jank Common Misconceptions and Probing Questions; P7AN1 also covers ANR Why It Matters and Tradeoffs; P7RD2 also covers The Rendering Pipeline (One Frame). Notes now identify each passage by its opening words rather than by ID alone.

| ID | Chapter, sections | Original says | Problem | Evidence |
|---|---|---|---|---|
| P7AS1 | App Size and R8: Tradeoffs; Probing Questions; Answer Key (9) | `android.enableR8.fullMode=true` turns R8 “up to maximum”; unmeasured 3-day, 10% size and 5% speed figures | Full mode has been the default since AGP 8.0 (opt out with `android.enableR8.fullMode=false`); it was opt-in only from AGP 7.0. The effect figures are unmeasured | [Enable app optimization](https://developer.android.com/topic/performance/app-optimization/enable-app-optimization) (“8.0: Full mode by default”) |
| P7AS2 | App Size and R8: Internal Mechanics; Failure Modes; Answer Key (5) | `getIdentifier` is reflection; the shrinker “cannot see” the dynamic name, deletes the resource or replaces it with a 1×1 dummy | `getIdentifier` is a resource lookup, not reflection. In the default (non-strict) mode the shrinker keeps resources whose names match string constants in code; strict mode is needed before such resources are removed. The 1×1 replacement describes older behaviour | [Customize which resources to keep](https://developer.android.com/topic/performance/app-optimization/customize-which-resources-to-keep) (“Unless you're using strict checking…”) |
| P7AS3 | App Size and R8: Staff Engineer Thinking; Answer Key (8) | Reject PRs with large PNG/JPG illustrations that can be recreated as vectors | Android recommends limiting vector images to about 200 × 200 dp, because larger ones “can take too long to draw”, and first load can cost more CPU than a raster image | [Vector Asset Studio](https://developer.android.com/studio/write/vector-asset-studio) |
| P7SU11 | Startup: Macrobenchmark — Measuring Startup Properly | “Macrobenchmark + Play Vitals + your dashboard all pick this up” (`reportFullyDrawn`) | Android vitals measures start-up to the first frame (time to initial display); its documentation does not use `reportFullyDrawn` | [Android vitals: start-up time](https://support.google.com/googleplay/android-developer/answer/9844486) |
| P7SU12 | Startup: Diagnosing Slow Startup | `adb shell perfetto … -c - <<EOF` with a text config and bare `linux.ftrace` | A text config needs `--txt`; without ftrace events or atrace categories the trace cannot show the “ActivityStart” and “Choreographer#doFrame” slices the section tells readers to find | [Perfetto CLI](https://perfetto.dev/docs/reference/perfetto-cli) (`--txt` “parse the config file as pbtxt”) |
| P7RD10 | Rendering: Measuring Rendering — Tools | `perfetto -t 10s -c -` with a text config; “use `adb shell systrace`” | The text config needs `--txt`, and simple-mode `-t` is mixed with a config file; systrace is a deprecated host-side script, not a device shell command | [Perfetto CLI](https://perfetto.dev/docs/reference/perfetto-cli) |
| P7RD11 | Rendering: Measuring Rendering — Tools; Common Rendering Bottlenecks | “Red horizontal line = 16ms target”; overdraw “red = 3x+” | The documentation's horizontal line for 16.67 ms is green; overdraw shows pink for 3× and red for 4× or more | [Inspect GPU rendering](https://developer.android.com/topic/performance/rendering/inspect-gpu-rendering) |
| P7AN5 | ANRs: Internal Mechanics; Answer Key (2) | The kernel routes the tap to InputDispatcher, which “queues the event in your app's Main Thread MessageQueue”; InputDispatcher is “an internal watchdog system” | InputReader and InputDispatcher run in system_server and deliver events to the app window over an input channel; the dispatcher does not insert messages into the app's MessageQueue. An input-dispatch ANR is the window not responding to a dispatched event within the timeout | [Input (AOSP)](https://source.android.com/docs/core/interaction/input); [Diagnose and fix ANRs](https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs) |
| P7JK7 | Jank: Tradeoffs; Answer Key (9) | Without `key`, deleting item 2 makes Compose “recompose items #3 through #1000”; keys let items move “without recomposing” | LazyColumn composes only visible items, so items far off-screen are not recomposed; keys preserve item identity and state across moves. Same claim as P7RD4 in the rendering chapter | [Compose performance best practices](https://developer.android.com/develop/ui/compose/performance/bestpractices) |

**Candidate, not filed:** Memory Failure Modes says an unregistered receiver lets a system service hold a hard reference that leaks the Activity. The framework reports a leaked registration at context teardown and unregisters it ([StrictMode `detectLeakedRegistrationObjects`](https://developer.android.com/reference/android/os/StrictMode.VmPolicy.Builder#detectLeakedRegistrationObjects())). Verify against current frameworks/base before filing.

**Evidence quality:** the original 33 findings each cite one primary page with a shared boilerplate line. Several bundle multiple claims under that one source (notably P7AN1, P7RD1 and P7MM1). Before approval, the owner should ask for each sub-claim to be split, or quoted from its own source; the ANR guide's documented timeouts are a concrete starting point for P7AN1.
