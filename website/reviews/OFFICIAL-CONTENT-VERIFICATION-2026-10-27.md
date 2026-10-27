# Official-source content verification and applied corrections

The owner requested correction and publication of the issues in the two supplied reports, a separate PR in the original playbook repository, and official documentation as the source of truth. This review checks the reports' named issues against the current chapter text, official documentation, API contracts and implementation source. It does not assert that every statement in all 123 chapters has been independently audited.

## Applied scope

86 individual replacements across 31 chapters are applied to the website through its approved, labelled correction mechanism. The matching source changes are proposed on `codex/verified-content-corrections` in the private original playbook repository. Original-repository main and unrelated local changes remain untouched. Git history and the website's expandable correction records retain the old wording; the active explanation is corrected. This approval does not accept every older proposal in the 292-item backlog.

The exact old text, replacement, reason and official source URL are in the accompanying JSON manifest. Multiple replacements address repetitions of one underlying issue; 86 is a replacement count, not 86 independent defect categories. The original source PR includes citations in each changed chapter's references.

## Verified decisions

| Topic | Decision and primary evidence |
|---|---|
| Lifecycle and ViewModel retention | Fix split-screen/dialog examples for modern multi-resume, and describe ViewModelStore retention within the app process. [Multi-window](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode), [ComponentActivity source](https://raw.githubusercontent.com/androidx/androidx/androidx-main/activity/activity/src/main/java/androidx/activity/ComponentActivity.kt). |
| Binder saved state | Fix the system-wide limit claim: the currently 1 MB buffer is shared by transactions in the process. [Android guidance](https://developer.android.com/guide/components/activities/parcelables-and-bundles). |
| Compose strong skipping | Correct legacy universal non-skippability, capture memoization, illustrative compiler reports and repeated advice. Version the rule at Kotlin 2.0.20 defaults; keep invalidation distinct from parameter comparison. [Strong skipping](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping). |
| Navigation version | The Navigation chapter already says 2.8; correct the actual 2.7 claim in Modularization Strategies. [Type-safe APIs](https://developer.android.com/guide/navigation/design/type-safety). |
| Room transactions | The actual DAO receiver error is in Repository Source of Truth. Supply its owning RoomDatabase and call database.withTransaction. [Room release/API history](https://developer.android.com/jetpack/androidx/releases/room#2.1.0-alpha05). |
| Room relationships/invalidation | Remove inherent N+1 claims without replacing them with an unconditional two-query promise; clarify table invalidation versus projection and distinct results. [Relationships](https://developer.android.com/training/data-storage/room/relationships/one-to-many), [observable queries](https://developer.android.com/training/data-storage/room/async-queries). |
| Hilt and Dagger | Correct ViewModelComponent versus its retained ancestor and eager-singleton myths, including questions and answers. [Hilt components](https://dagger.dev/hilt/components.html), [scope semantics](https://dagger.dev/semantics/advanced.html#scopes). |
| Compose offset and nullable delegates | Show reads inside the offset placement lambda, and snapshot a nullable delegated property before smart casting. The report's claim that offset reads move directly to drawing is wrong. [Compose phases](https://developer.android.com/develop/ui/compose/phases), [smart-cast prerequisites](https://kotlinlang.org/docs/typecasts.html#smart-cast-prerequisites). |
| Flow and lifecycle | Replace emission inside withContext with flowOn, and gate the UI effect collector on STARTED with an explicit no-subscriber delivery caveat. [Flow builder API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/flow.html), [Android collection guidance](https://developer.android.com/kotlin/flow/stateflow-and-sharedflow). |
| WorkManager and alarms | Correct setExpedited's policy argument and quota semantics. Distinguish Android 12 permission introduction, Android 14 default denial for most new installs targeting Android 13+, and USE_EXACT_ALARM eligibility. [Work requests](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work#expedited), [exact alarms](https://developer.android.com/about/versions/14/changes/schedule-exact-alarms). |
| Looper | quitSafely drains due messages, not future delayed messages. [API contract](https://developer.android.com/reference/android/os/Looper#quitSafely()). |
| Retrofit and Apollo | Correct request construction/conversion boundaries and runtime proxies; expose ApolloResponse explicitly so the caller can handle data and failures without discarding intermediate responses. [RequestFactory](https://raw.githubusercontent.com/square/retrofit/trunk/retrofit/src/main/java/retrofit2/RequestFactory.java), [Retrofit proxy](https://raw.githubusercontent.com/square/retrofit/trunk/retrofit/src/main/java/retrofit2/Retrofit.java), [watchers](https://www.apollographql.com/docs/kotlin/caching/query-watchers). |
| Coroutine tests | Drain initial and exact-deadline work with runCurrent; remove Turbine-mandatory and collect-always-hangs claims. [Scheduler API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-coroutine-scheduler/advance-time-by.html), [Flow testing](https://developer.android.com/kotlin/flow/test). |
| ANR deadlines | Fix version/priority-specific broadcast deadlines and distinguish execute-service timeouts. The supplied report reversed the service values: official defaults are 20 seconds foreground, 200 seconds background. Keep promotion and service-duration timeouts separate. [ANR diagnosis](https://developer.android.com/topic/performance/anrs/diagnose-and-fix-anrs). |
| Build and runtime | clean removes project outputs rather than the shared build cache; Kotlin/JVM produces class bytecode before D8/R8; Zygote preloading is separate from ART app compilation. [Gradle cache](https://docs.gradle.org/current/userguide/build_cache.html), [D8](https://developer.android.com/tools/d8), [ART JIT](https://source.android.com/docs/core/runtime/jit-compiler). |
| Native startup compatibility | Add the requested 16 KB compatibility cross-reference, including native SDKs and validation, without saying every Android 15 device has 16 KB pages. [Android guide](https://developer.android.com/guide/practices/page-sizes). |
| Kotlin collections/lateinit/constants/lazy/volatile | Correct read-only versus immutable, allow top-level lateinit, distinguish stale inlined constants from linkage breakage, describe JVM lazy's volatile fast path and volatile visibility/ordering instead of cache bypass. [Collections](https://kotlinlang.org/docs/collections-overview.html), [properties](https://kotlinlang.org/docs/properties.html), [JLS binary constants](https://docs.oracle.com/javase/specs/jls/se17/html/jls-13.html#jls-13.4.9), [Kotlin 2.4.21 lazy source](https://raw.githubusercontent.com/JetBrains/kotlin/v2.4.21/libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt), [Volatile contract](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.concurrent/-volatile/). |
| crossinline | Clarify wrapped invocation versus storing the function value itself; noinline is the storage case. [Inline functions](https://kotlinlang.org/docs/inline-functions.html#non-local-jump-expressions). |

## Reports not adopted verbatim

The current WebView chapter already identifies a sandboxed renderer process. The current KMP decision matrix already allows shared ViewModels; the remaining false iOS claim was actually in Recomposition and State and is corrected there. The current Swift chapters already describe Kotlin 2.4 Alpha Swift export, Flow-to-AsyncSequence mapping and its default dispatcher caveat; [official Swift export documentation](https://kotlinlang.org/docs/native-swift-export.html) confirms those features. They were not rewritten based on the report's vague reminder.

The SharedFlow tryEmit bullets already have their default-unbuffered qualification. [The API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-mutable-shared-flow/try-emit.html) supports that scoped explanation. A conditional LaunchedEffect(Unit) is not automatically a bug; replacing keys blindly would not prove a delivery guarantee. The two-mode heading is corrected, without inventing a Channel mode and promising lossless navigation. General Kotlin Playground embedding remains an optional feature, not a technical correction.

## Validation and limits

The exact corrected service Flow is extracted from the approved replacement, compiled and run with Kotlin 2.4.21, coroutines 1.11.0 and JDK 17. Focused checks cover its emissions, invalid-context rejection, exact scheduler endpoints, no-subscriber/replay SharedFlow behavior, finite Flow testing without Turbine, top-level/local lateinit and a negative compiler check for delegated smart casts. All passed. Framework-dependent Android/Compose/Room/Hilt snippets were checked against their APIs and source; they were not compiled as a complete Android app. Application fragments still require their named surrounding types and imports.

The website build verifies source hashes, exact-once replacement matching and all 125 pages against the approved corrected token streams. Its corrected-unit count is 15,568; the earlier 15,572 baseline was before these intentional replacements. The source Markdown snapshot remains unchanged in the website checkout. Source docs gates and all 15 checker unit tests pass. Diagram and browser reruns and PR/publication results are recorded below when complete. This is not a declaration that every older phase finding or every historic correction proposal has been closed.

## Changed chapter inventory

| Chapter | Replacements |
|---|---:|
| `android/architecture/activity.md` | 4 |
| `android/architecture/modularization-strategies.md` | 1 |
| `android/architecture/mvvm-vs-mvi.md` | 2 |
| `android/architecture/process-death-and-state-restoration.md` | 1 |
| `android/architecture/savedstatehandle.md` | 1 |
| `android/architecture/viewmodel.md` | 1 |
| `android/build-tooling/gradle-and-build-systems.md` | 2 |
| `android/compose/modifiers-and-layout.md` | 1 |
| `android/compose/recomposition-and-state.md` | 1 |
| `android/compose/side-effects.md` | 1 |
| `android/compose/stability.md` | 15 |
| `android/concurrency/battery-optimizations.md` | 2 |
| `android/concurrency/services.md` | 1 |
| `android/concurrency/shared-flow-and-state-flow.md` | 2 |
| `android/concurrency/threads-and-looper.md` | 1 |
| `android/concurrency/workmanager.md` | 3 |
| `android/data-and-di/components.md` | 6 |
| `android/data-and-di/dependency-injection.md` | 3 |
| `android/data-and-di/repository-source-of-truth.md` | 2 |
| `android/data-and-di/room.md` | 4 |
| `android/networking-and-security/graphql.md` | 1 |
| `android/networking-and-security/ktor-vs-retrofit.md` | 1 |
| `android/networking-and-security/retrofit-and-okhttp.md` | 1 |
| `android/os-internals/art-and-dalvik.md` | 2 |
| `android/os-internals/the-zygote.md` | 1 |
| `android/performance/anrs.md` | 5 |
| `android/performance/startup.md` | 1 |
| `android/testing/unit-testing.md` | 7 |
| `kotlin/compiler-features/inline-functions.md` | 1 |
| `kotlin/language-core/variables.md` | 10 |
| `kotlin/runtime-and-jvm/memory-model.md` | 2 |

## Completed verification results

The complete browser sweep passed 125 pages, 1,750 layouts, 8,880 illustrated-state checks and 1,808 full-scene states. A final self-review changed the Apollo correction to expose its response wrapper, preserving intermediate data/error contracts; the focused GraphQL rerun passed and is recorded separately. Integrated results are in `verified-browser-validation.json`, with raw sweep and recheck files retained. Binder's 448 checks, all 13 motion checks and all 69 interaction/responsive checks passed. Focused compiler/runtime output is in `verified-kotlin-tests.txt`.

The website and original source branch were compared programmatically: all 31 corrected chapter texts match before the source PR's additional reference lists. Evidence: `verified-source-alignment.json`. [Source PR #57](https://github.com/swarnsingh/android-staff-engineer-playbook/pull/57), commit `3b5c7f7`, passed [GitHub documentation and diagram CI](https://github.com/swarnsingh/android-staff-engineer-playbook/actions/runs/40467761090). It remains available for review and is not merged. The original repository remains private. The website remains public and uses its existing PR #1 and Pages workflow.
