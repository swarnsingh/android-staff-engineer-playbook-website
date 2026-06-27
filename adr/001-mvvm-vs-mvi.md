# ADR 001: MVVM vs MVI Architecture

## Context
As the application scales in complexity, particularly with the introduction of Jetpack Compose, state management has become a critical bottleneck. The existing architecture predominantly uses **MVVM (Model-View-ViewModel)** with multiple `LiveData` or `StateFlow` streams representing different pieces of the UI state (e.g., `isLoading`, `userData`, `errorMessage`).

This approach has led to several issues:
1.  **State Desync (Impossible States):** Because `isLoading` and `userData` are independent streams, the UI occasionally renders impossible combinations (e.g., a loading spinner displaying simultaneously with a populated user list, or an error snackbar appearing on top of a success screen).
2.  **Concurrency Bugs:** When multiple asynchronous operations complete simultaneously, updating disparate streams leads to race conditions and "flickering" UIs.
3.  **Action Tracing:** Debugging user reports is difficult because mutations to the ViewModel state occur from scattered methods, making it hard to trace the exact sequence of events that led to a crash.

The engineering team is debating whether to standardize on a strict **MVI (Model-View-Intent)** architecture to resolve these issues, knowing that MVI introduces significant boilerplate.

## Alternatives Considered

### 1. MVVM (Status Quo)
-   **Pros:** Native to Android architecture components. Low learning curve for junior engineers. Extremely low boilerplate for simple screens.
-   **Cons:** Mutable state is scattered. UI is responsible for combining multiple streams, leading to complex `combine()` logic or `if/else` ladders in the View layer. Prone to illegal state combinations.

### 2. MVI (Model-View-Intent)
-   **Pros:** 
    -   **Single Source of Truth:** A single, immutable `State` data class represents the entire screen.
    -   **Unidirectional Data Flow (UDF):** The View only emits `Intents` (Events/Actions) to the ViewModel. The ViewModel is a pure state machine that reduces Intents into a new `State`.
    -   **Predictability:** Eliminates impossible states. If the data class defines `sealed class ScreenState { Loading, Success, Error }`, the UI can physically only be in one of those states.
-   **Cons:** 
    -   **Boilerplate:** Requires defining `Intent`, `State`, and `Effect` (Side-Effects) classes for every screen.
    -   **State Explosion:** For complex screens, updating a deeply nested data class requires cumbersome `copy()` commands.
    -   **Performance:** Creating a new immutable copy of the entire screen state on every minor update (e.g., typing a character in a text field) can cause excessive Garbage Collection or Recomposition overhead in Compose if not optimized.

## Decision
We will adopt a **Pragmatic MVI** approach, specifically tailored for Jetpack Compose, with the following constraints:

1.  **Single Immutable State:** All ViewModels must expose exactly one `StateFlow<ViewState>` representing the UI state. Multiple independent `StateFlows` (e.g., `loadingFlow`, `errorFlow`) are strictly forbidden.
2.  **Unidirectional Intents:** The UI must communicate with the ViewModel by dispatching discrete `Intent` or `Action` objects, rather than directly calling ViewModel methods (e.g., `viewModel.dispatch(UserAction.LoadData)` instead of `viewModel.loadData()`).
3.  **Separation of Side-Effects:** One-time events (e.g., showing a Snackbar, navigating to a new screen) must not be modeled as persistent State. They must be handled via a separate `SharedFlow<ViewEffect>` to prevent re-triggering the event on configuration changes (rotation).
4.  **Exceptions for High-Frequency Inputs:** To avoid the "State Explosion" and GC thrashing, extremely high-frequency UI events (like typing in a `TextField` or dragging a slider) may bypass the strict Intent/Reducer loop and update a localized, mutable Compose `State` variable directly within the UI layer, synchronizing with the ViewModel only on submission or debounced intervals.

## Consequences
-   **Positive:** The UI layer (Compose) becomes completely devoid of logic, acting as a pure function of the `ViewState`. Bugs related to impossible states (Loading + Error simultaneously) are mathematically eliminated.
-   **Positive:** Debugging is vastly simplified. We can log every `Intent` and the resulting `ViewState` transition, allowing us to perfectly replay user sessions.
-   **Negative:** Developers will complain about boilerplate. We must mitigate this by providing standardized Base classes (`BaseViewModel<State, Intent, Effect>`) and Android Studio Live Templates to automate the creation of the MVI triad.
-   **Negative:** The learning curve increases. We must invest in training to ensure engineers understand Reducers and pure functions.
