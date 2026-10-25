# Android Phase 1: possible errors in the original chapters

Found while writing the teaching layer for Android Phase 1 (the nine chapters under `android/architecture/` listed in Phase 1 of `android.md`). These are **findings for the owner's review**, not approved corrections. Nothing here is applied: the original Markdown is unchanged and no entry exists in `content/corrections-*.json`.

On the website, each finding is shown as an **Under review** note placed before the section that contains it. The note says the passage is under review, but the website does not print a replacement text next to the original. The teaching layer avoids restating these claims.

Sources were checked on 2026-10-25.

| ID | Chapter, section | Original says | Problem | Evidence |
|---|---|---|---|---|
| A1 | Activity, Internal Mechanics: The Lifecycle (and Answer Key 1) | Opening split-screen mode is an example of `onPause()` without `onStop()` | Since Android 10, all activities visible in multi-window mode stay `RESUMED` (multi-resume); split-screen no longer pauses the other visible app | [Multi-window support](https://developer.android.com/develop/ui/views/layout/support-multi-window-mode): "Android 10 (API level 29) and higher versions support multi-resume—all activities remain in the RESUMED state" |
| VM1 | ViewModel, Internal Mechanics | The Activity hands the `ViewModelStore` "to the OS", and the new Activity asks the OS for it back | The retained non-configuration instance stays in the app process; nothing is handed to the system. The chapter's own Answer Key 1 says this correctly | androidx `ComponentActivity.onRetainNonConfigurationInstance()` / `lastNonConfigurationInstance`; the store is cleared on `ON_DESTROY` only when `!isChangingConfigurations` |
| SSH1 | SavedStateHandle, Tradeoffs | "`TransactionTooLargeException` limits (1MB across the *entire* OS IPC system)" | The 1MB Binder transaction buffer is per process, shared by that process's in-flight transactions; Android recommends keeping saved state under 50KB | [Parcelables and Bundles](https://developer.android.com/guide/components/activities/parcelables-and-bundles) |
| PD1 | Process Death, Tradeoffs | "IPC limit of 1MB total across all apps" | Same as SSH1: the limit is per process | Same as SSH1 |
| PD2 | Process Death, Staff Engineer Thinking, point 1 | Test process-death survival with "Don't keep activities" or by killing the process | "Don't keep activities" destroys activities but keeps the process, so it tests activity recreation, not process death. The chapter's own Answer Key 3 says so | Answer Key 3 of the same chapter; `adb shell am kill <package>` on a backgrounded app is the process-death path |
| MV1 | MVVM vs MVI, Compose Integration, point 2 | Avoid `{ vm.processIntent(it) }` because it "allocates a new lambda each composition" | Since Kotlin 2.0.20, Compose strong skipping is on by default and remembers lambdas inside composables, keyed on their captures | [Strong skipping mode](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping) |
| MV2 | MVVM vs MVI, Failure Modes, row 1 | "Toast re-fires after rotation → Move to `Channel<Effect>`" | Conflicts with the chapter's own state-first rule ("UI Events" section) and Android's UI events guidance for actions whose loss matters; the matching row in State Management says "Clear/advance UI state after the UI handles it" | [UI events](https://developer.android.com/topic/architecture/ui-layer/events) |
| SM1 | State Management, `SavedStateHandle` — Process-Death Survival | The OS kills your app for memory reasons "(Doze, low memory, …)" | Doze defers background CPU and network work to save power; it is not a memory-reclaim mechanism | [Doze and App Standby](https://developer.android.com/training/monitoring-device-state/doze-standby) |
| SM2 | State Management, Real Android Patterns 1, 2 and 5 | `@HiltViewModel class FeedViewModel(repo: FeedRepository)` (and `CheckoutViewModel`, `CheckoutWizardViewModel`) without `@Inject` | Hilt requires the `@HiltViewModel` class to have an `@Inject`-annotated constructor; these examples do not compile with Hilt | [Hilt and Jetpack integrations](https://developer.android.com/training/dependency-injection/hilt-jetpack) |
| SM3 | State Management, Failure Modes | Fix: "`MutableSharedFlow.update`" | `update { }` is an extension on `MutableStateFlow`; `MutableSharedFlow` has no `update` | kotlinx.coroutines API reference for `MutableStateFlow.update` |
| MO1 | Modularization Strategies, Type-Safe Navigation Across Modules | "Compose Navigation 2.7+ supports type-safe routes" | Type-safe routes arrived in Navigation 2.8.0; the Navigation chapter in this phase already says 2.8 | [Navigation releases](https://developer.android.com/jetpack/androidx/releases/navigation) (2.8.0) |
| MO2 | Modularization Strategies, Failure Modes | "`internal` classes accessible from another module — cause: modules in same package" | Kotlin `internal` is visible within one module regardless of package, so sharing a package does not expose it to another Kotlin module | [Kotlin visibility modifiers](https://kotlinlang.org/docs/visibility-modifiers.html#modules) |

## Smaller notes (not flagged on the pages)

- **Activity, mental model and diagram:** both say "a dialog" pauses the activity. Android's documentation groups "a new activity or dialog" together. The teaching layer uses the runtime permission prompt, which is a separate activity, as its paused-but-visible example.
- **State Management, UDF diagram:** the edge from the repository to the ViewModel is labelled `Flow.collectAsState`, which is a Compose API. The redrawn diagram uses `stateIn(viewModelScope, …)`, matching the chapter's own code.
- **Activity, Historical Context:** "It caused massive jank" is an overstatement, but it is not a technical error.

## How to approve

Approve findings by ID. For each approved finding, the exact original text and replacement would be written as an entry in a new `content/corrections-android.json`, following the existing approval format, and the matching Under review note would then be removed.
