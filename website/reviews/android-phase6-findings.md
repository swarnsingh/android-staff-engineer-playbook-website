# Android Phase 6 — pending original findings

2026-10-25. Originals read in full and left unchanged. Every row is **unapproved**. These are website-only proposals for a later owner decision, not applied corrections. Active blends avoid teaching the disputed replacements. Neutral notices identify affected sections without publishing replacement text. Evidence below is documentation/source inspection and arithmetic; no Android build, device run or performance measurement was performed.

## Testing strategy

### TS1 — retry arithmetic / attempt count
- Note for the owner: the original's 78% equals 1 − 0.6³ ≈ 0.784, the chance that at least one of three runs *fails*, so the figure was probably inverted; the chapter's own "up to 3×" points to three total attempts (0.936).
- **Original section:** Flakiness as a System, Not a Nuisance.
- A 40% independent failure probability does not give 78% eventual pass under either ordinary interpretation of “3 retries”. Three total attempts yield `1 − .4³ = .936`; initial plus three retries yield `1 − .4⁴ = .9744`. Independence itself is a model assumption, not a measured flake property.
- **Proposal:** name total attempts versus retries and correct the calculation after owner approval. No numeric replacement enters the blend.

## Unit testing

### UT1 — polling assertions do not establish scheduler progress
- **Sections:** Coroutines Testing; Answer Key (3).
- **Verified (independent review, kotlinx-coroutines-test 1.11.0, Kotlin 2.4.21):** with either a launch-first or a fetch-first poller, the shown assertions observe 0 or 1 → 1 → 3 calls, not 1 → 2 → 4; work due exactly at the deadline runs only after `runCurrent()`. Answer 3's `advanceTimeBy(60.seconds)` likewise does not resume a `delay(60_000)` until `runCurrent()`. The `Duration` overload's KDoc does not restate the boundary; observed behaviour matches the `Long` overload.
- The sample asserts immediately after start and at `advanceTimeBy` deadlines. With the default standard test dispatcher, launched work is queued; advancing time excludes tasks exactly at the new deadline. `Poller.start` is not supplied, so its eager-start behavior cannot be assumed.
- **Evidence:** [advanceTimeBy contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/advance-time-by.html), [Android StandardTestDispatcher guide](https://developer.android.com/kotlin/coroutines/test#standardtestdispatcher).
- **Proposal:** supply the poller/scheduler assumptions and explicitly drive due work before count assertions; verify in a runnable harness before approving.

### UT2 — virtual-delay scope is overgeneralized
- **Sections:** Coroutines Testing; Answer Key (6). (The Common Pitfalls bullet that a `delay(5_000)` test takes five real seconds without virtual time is accurate and is not disputed.) The same-scheduler hazard also applies: a test dispatcher created as a property outside `runTest` uses a different scheduler (`Detected use of different schedulers`).
- Delays on a real IO/Default dispatcher are not skipped simply because the caller uses runTest. The guide limits virtual control to the shared test scheduler.
- **Evidence:** [dispatcher injection](https://developer.android.com/kotlin/coroutines/test#injecting-test-dispatchers).
- **Proposal:** qualify the claim by the dispatcher/scheduler actually used.

### UT3 — eager entry is presented as eager completion
- **Sections:** Coroutines Testing; Answer Key (2/6).
- UnconfinedTestDispatcher starts new coroutines eagerly; suspension can still return control before their final update. “Synchronous”/“instant” completion is conditional.
- **Evidence:** [UnconfinedTestDispatcher guide and suspending counterexample](https://developer.android.com/kotlin/coroutines/test#unconfinedtestdispatcher).
- **Proposal:** state the suspension boundary and keep explicit outcome synchronization where required.

### UT4 — Flow collection lifetime and tool mandate
- **Sections:** Flow Testing with Turbine; Failure Modes; Probing Questions (5); Answer Key (5).
- Finite flows can complete; collect is not inherently an infinite wait. Turbine is useful, not mandatory for all valid Flow tests.
- **Evidence:** [official Android Flow testing](https://developer.android.com/kotlin/flow/test) includes `first`, `toList`, continuous collection and backgroundScope patterns.
- **Proposal:** distinguish finite versus continuing flows and collector ownership rather than prescribing one library universally.

### UT5 — Jupiter lifecycle explanations
- **Sections:** Failure Modes (Nested row); Answer Key (11).
- Enclosing BeforeEach setup participates in nested tests. PER_CLASS is not the general fix for absent outer setup. BeforeAll supports static methods with PER_METHOD; PER_CLASS permits nonstatic methods.
- **Evidence:** [JUnit 5.11.4 nested tests and lifecycle](https://docs.junit.org/5.11.4/user-guide/index.html#writing-tests-nested), sections 2.12–2.13.
- **Proposal:** explain lifecycle and Kotlin inner-class/static method details independently.

## UI testing

### UI1 — Robolectric exclusions describe the wrong rendering model
- **Section:** Robolectric — JVM-Hosted Android.
- Robolectric has native Android graphics-backed mode; it is not generally Layoutlib font rendering. “Animations snap” is not a universal rule. Ordinary JVM I/O is not categorically prohibited by a local test runner.
- **Evidence:** [GraphicsMode source](https://github.com/robolectric/robolectric/blob/master/annotations/src/main/java/org/robolectric/annotation/GraphicsMode.java), [ValueAnimator shadow](https://github.com/robolectric/robolectric/blob/master/shadows/framework/src/main/java/org/robolectric/shadows/ShadowValueAnimator.java).
- **Proposal:** distinguish configured graphics/clock support from the recommendation to fake external I/O; remove unmeasured “90%” applicability as a universal fact.

### UI2 — snapshot task modes conflated
- **Section:** Paparazzi — Screenshot Testing on JVM.
- Also: "Any pixel diff fails the test" — verification fails above a configurable difference threshold, `maxPercentDifference`, default 0.01% ([SnapshotHandler.kt](https://github.com/cashapp/paparazzi/blob/master/paparazzi/src/main/java/app/cash/paparazzi/SnapshotHandler.kt)); the chapter's own Failure Modes row relies on that tolerance.
- Running tests generates a report; recording writes goldens; verification compares against recorded references. Merely running once does not mean references were recorded.
- **Evidence:** [Paparazzi Tasks](https://github.com/cashapp/paparazzi#tasks).
- **Proposal:** name the record and verify task modes explicitly.

### UI3 — Hilt example mixes lifecycle frameworks and binding types
- **Sections:** Hilt + Compose Tests; Test Robustness ("Reset all dependencies in `@BeforeEach`"); Real Patterns (Pattern 2 injects a concrete fake type with no shown binding); Failure Modes (snackbar row). These suites run on JUnit 4 rules (`AndroidJUnit4`, `createComposeRule`), where Jupiter's `@BeforeEach` never runs; the Hilt testing guide uses `@Before` and binds the interface ([Hilt testing](https://developer.android.com/training/dependency-injection/hilt-testing)).
- AndroidJUnit4 does not execute Jupiter BeforeEach. The shown provider binds CartRepository while the test injects FakeCartRepository, with no supplied binding/constructor for that concrete type; the snippet cannot establish that the test mutates the same fake the screen uses.
- **Evidence:** [Hilt test application, JUnit Before setup, typed replacement binding](https://developer.android.com/training/dependency-injection/hilt-testing).
- **Proposal:** use the matching lifecycle annotation and demonstrate one shared fake binding. Define the Hilt test host/application setup or link it explicitly.

### UI4 — clock freezing / idleness promises
- **Sections:** Test Robustness — Avoiding Flakiness; Failure Modes; Answer Key (4/10).
- The Before snippet pauses and resumes the clock before any test action: it does not disable Compose animations globally. awaitIdle is suspending and cannot be pasted into an ordinary non-suspending test as shown. Idleness is not a promise that arbitrary Main/background coroutines have completed.
- **Evidence:** [Compose synchronization](https://developer.android.com/develop/ui/compose/testing/synchronization), [awaitIdle API](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/junit4/ComposeTestRule#awaitIdle()).
- **Proposal:** separate automatic advancement, deliberate intermediate-frame tests and external-work synchronization.

### UI5 — test manifest names are not the supplied classes
- **Section:** Test Robustness — Avoiding Flakiness.
- `androidx.test.core.app.testing.HiltTestApplication` and `androidx.compose.ui.test.junit4.android.ComponentActivity` are not the Hilt application/ComponentActivity types used by the documented host setup. A manifest also does not disable animations by declaring these classes.
- **Evidence:** [Hilt application and host setup](https://developer.android.com/training/dependency-injection/hilt-testing#test-application); [Compose setup](https://developer.android.com/develop/ui/compose/testing#setup).
- **Proposal:** use documented fully-qualified classes and keep animation policy separate from host registration.

### UI6 — incompatible idling-resource type and unbalanced counter
- **Section:** Test Robustness — Avoiding Flakiness.
- Espresso CountingIdlingResource implements Espresso's interface; ComposeTestRule.registerIdlingResource expects Compose's interface. No adapter is shown. A throwing/cancelled load also bypasses decrement, permanently leaving the example busy.
- **Evidence:** [Espresso CountingIdlingResource](https://developer.android.com/reference/androidx/test/espresso/idling/CountingIdlingResource), [Compose IdlingResource](https://developer.android.com/reference/kotlin/androidx/compose/ui/test/IdlingResource).
- **Proposal:** choose the correct registration/adapter and balance increment/decrement including failure and cancellation.

### UI7 — accessibility rule chain is not the Compose API
- **Sections:** Accessibility Testing; Answer Key (9).
- The documented Compose API enables checks on an AndroidComposeTestRule with the accessibility artifact; the shown AccessibilityChecksRule chain is not that API. Semantic size/label checks alone are not a full accessibility audit.
- **Evidence:** [official Compose accessibility test setup](https://developer.android.com/develop/ui/compose/accessibility/testing).
- **Proposal:** show the documented dependency/rule extension and retain manual assistive-technology verification as complementary evidence.

### UI8 — descendant merging stated as unconditional
- **Sections:** Test Tags vs Semantic Properties; Failure Modes; Answer Key (5).
- Nested merging boundaries such as clickable children can remain separate; mergeDescendants does not blindly flatten every descendant. Text may also be merged into the parent and remain matchable there.
- **Evidence:** [merging boundaries and policies](https://developer.android.com/develop/ui/compose/accessibility/merging-clearing).
- **Proposal:** distinguish merged parent properties, independently merging descendants and deliberate unmerged-tree inspection.

### UI9 — controlled text-input failure misdiagnosed
- **Section:** Failure Modes (performTextInput row).
- Compose actions/assertions already synchronize. If a controlled TextField callback does not update its input state, an extra waitForIdle cannot supply the missing state update. A race is one possible cause, not an established diagnosis.
- **Evidence:** [default synchronization contract](https://developer.android.com/develop/ui/compose/testing/synchronization).
- **Proposal:** diagnose state wiring and async boundaries before prescribing a wait.

## Validation scope

Authoring uses 3 semantic figures, 3 step-through traces and 9 added Q&A checkpoints. Documentation inspected on 2026-10-25. No original fix is approved; no replacement depends on an active pending paragraph. No device, instrumented test, Gradle run or screenshot comparison is claimed. Integrated preservation and independent review are parent-agent gates.

## Added after independent review (2026-10-26)

### UT6 — `runTest` "swallows exception" row
- **Section:** Failure Modes (runTest row).
- `runTest` reports a failing test body and unhandled child exceptions at the end of the test, and already defaults to `StandardTestDispatcher`, so the prescribed fix changes nothing.
- **Evidence:** [runTest](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/run-test.html) ("Unhandled exceptions will be thrown at the end of the test"); [Android coroutine testing](https://developer.android.com/kotlin/coroutines/test).
- **Proposal:** diagnose exceptions caught by user code, or thrown on scopes or dispatchers outside the test scheduler.

### UT7 — Turbine's end-of-block contract
- **Section:** Flow Testing with Turbine ("Subscribes; runs the block; cancels on block exit" and the GOOD sample).
- At block end `test` cancels and calls `ensureAllEventsConsumed()`; completion and errors are events that must be consumed, so the GOOD sample fails for a finite flow such as `flowOf(item)` with an unconsumed Complete event.
- **Evidence:** [Turbine README](https://github.com/cashapp/turbine).
- **Proposal:** consume completion (`awaitComplete()`) or cancel/ignore remaining events explicitly for finite flows.

### UT8 — MockK failure-mode rows
- **Section:** Failure Modes ("Mock returns null for non-nullable | MockK strict mode"; "`coEvery` returns Unit but should suspend").
- A strict (default) MockK mock fails an unstubbed call rather than returning a value; a surprising null comes from relaxed mocks, so the row's cause is reversed. The `coEvery` row's symptom has no clear meaning; its cause and fix concern unstubbed Unit calls.
- **Evidence:** [MockK documentation](https://mockk.io/) ("By default mocks are strict"; the relaxed example returns null).
- **Proposal:** restate as an unstubbed-call failure, fixed by stubbing, `just Runs`, or `relaxUnitFun`/`relaxed`.

### UI10 — Gradle Play Publisher named as a Test Lab integration
- **Section:** Multi-Device Testing — Firebase Test Lab ("CI integration available via Gradle Play Publisher and Fladle").
- Gradle Play Publisher uploads and publishes artifacts to Google Play; it does not run Test Lab matrices. Fladle, the `gcloud` CLI or Firebase's own tooling are Test Lab integrations.
- **Evidence:** [Gradle Play Publisher](https://github.com/Triple-T/gradle-play-publisher); [Fladle](https://github.com/runningcode/fladle).

### UI11 — deprecated gesture API shown as current
- **Section:** Semantics — The Foundation (`performGesture { swipeLeft() }`).
- `performGesture` is `@Deprecated("Replaced by performTouchInput")`. Low severity.
- **Evidence:** androidx `compose/ui/ui-test/src/commonMain/kotlin/androidx/compose/ui/test/Actions.kt`.

### Candidate, not filed: ViewModel Loading → Success test
- With a fake whose `submit` does not suspend, a `StateFlow` collector on `UnconfinedTestDispatcher` can miss the conflated Loading state (reviewer harness observed `[Idle, Success]`). It needs a run with real Turbine before it becomes a finding.

## Teaching-layer changes after review
- All notes use the standard wording and identify the passage in words. The ui-testing stepper now says `performClick()` injects a touch click on Android ([Actions.android.kt](https://android.googlesource.com/platform/frameworks/support/+/refs/heads/androidx-main/compose/ui/ui-test/src/androidMain/kotlin/androidx/compose/ui/test/Actions.android.kt)).
- The three original Mermaid diagrams are redrawn faithfully. The unit-testing stepper now resolves the opening double-discount bug with the chapter's own `FakeCartRepository`, and adds a mock/fake/spy visual.
