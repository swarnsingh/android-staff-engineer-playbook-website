# State Pattern

## Overview

The State pattern allows an object to alter its behavior when its internal state changes. The object will appear to change its class. In modern Android, it is the fundamental pattern for modeling robust UI screens (UDF/MVI) and managing complex, multi-step operations without relying on fragile boolean flags.

*Note: This file covers the structural **implementation** of the State Pattern. For the underlying mechanics of State Machines, see [`engineering-fundamentals/state-machines.md`](../engineering-fundamentals/state-machines.md).*

## Why It Exists

An object whose behavior changes based on state usually ends up with methods filled with `if (isLoading) { ... } else if (isError) { ... } else { ... }`. When a new state is added, every method must be updated. The State pattern solves this by extracting each state's behavior into a dedicated class. The main object (the Context) simply delegates work to the current State object. 

## Historical Context

A GoF behavioral pattern. Originally implemented via a Context class holding a reference to a `State` interface, where state transitions often involved states instantiating other states. In modern Kotlin, **Sealed Classes / Sealed Interfaces** have completely revolutionized this pattern, replacing runtime polymorphism with compile-time exhaustive pattern matching. 

## First Principles

1.  **Encapsulate State-Specific Behavior:** Put all behavior associated with a particular state into one object.
2.  **Make Invalid States Impossible:** By defining discrete states, you eliminate the possibility of contradictory configurations (e.g., `isLoading = true` AND `isError = true`). See [`principles/make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md).
3.  **Explicit Transitions:** State changes aren't accidents of data mutation; they are explicit transitions from one well-defined state to another.

## Mental Model

Think of a smartphone screen. When the screen is "Locked", swiping right opens the camera. When the screen is "Unlocked", swiping right moves to the next home screen. The phone (Context) doesn't run a giant `if(locked)` check on every swipe; it just passes the swipe event to the current `ScreenState` object, and the state knows what to do.

## Internal Mechanics

### 1. The Classic (GoF) Approach

Useful when state transitions require complex business logic or dependency injection.

```kotlin
// The Context
class AudioPlayer {
    var state: PlayerState = StoppedState(this) // Initial state
    
    fun play() { state.onPlay() }
    fun stop() { state.onStop() }
}

// The State Interface
interface PlayerState {
    fun onPlay()
    fun onStop()
}

// Concrete States
class StoppedState(private val player: AudioPlayer) : PlayerState {
    override fun onPlay() {
        println("Starting playback")
        player.state = PlayingState(player) // State transition
    }
    override fun onStop() = println("Already stopped")
}

class PlayingState(private val player: AudioPlayer) : PlayerState {
    override fun onPlay() = println("Already playing")
    override fun onStop() {
        println("Stopping playback")
        player.state = StoppedState(player) // State transition
    }
}
```

### 2. The Modern Kotlin Approach (Sealed Classes / MVI)

In Android, the State pattern is predominantly used to model UI State. Here, the "State" doesn't usually contain methods (behavior); it acts as a rigid data structure, and the "Context" (a ViewModel or Reducer) uses `when` statements to determine behavior based on the current state. This is a functional interpretation of the pattern.

```kotlin
// The State Definition
sealed interface ScreenState {
    data object Loading : ScreenState
    data class Content(val items: List<String>) : ScreenState
    data class Error(val message: String) : ScreenState
}

// The Context (ViewModel)
class ScreenViewModel : ViewModel() {
    private val _state = MutableStateFlow<ScreenState>(ScreenState.Loading)
    val state = _state.asStateFlow()

    fun loadData() {
        // Transition: Loading -> Content or Error
        _state.value = ScreenState.Loading
        try {
            val data = fetch()
            _state.value = ScreenState.Content(data)
        } catch (e: Exception) {
            _state.value = ScreenState.Error(e.message ?: "Unknown error")
        }
    }
}
```
*Why is this better than the Classic approach for UI?* Because it separates State (data) from Behavior (ViewModel), making the State immutable and easily observable by Compose or Views.

## Architecture

```mermaid
flowchart TD
    Context[Context] -->|delegates request| StateInterface[State Interface]
    StateInterface <.. StateA[Concrete State A]
    StateInterface <.. StateB[Concrete State B]
    StateA -.->|triggers transition| Context
    
    classDef core fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef strat fill:#f8d7da,stroke:#dc3545,stroke-width:2px;
    
    class Context core;
    class StateInterface,StateA,StateB strat;
```

## Production Example

Consider a file uploader that must handle chunking, network drops, and retries. Using booleans (`isUploading`, `isPaused`, `hasError`) is a recipe for disaster.

```kotlin
sealed class UploadState {
    data object Idle : UploadState()
    data class Uploading(val bytesSent: Long, val totalBytes: Long) : UploadState()
    data class Paused(val reason: String) : UploadState()
    data class Error(val exception: Throwable, val canRetry: Boolean) : UploadState()
    data class Complete(val fileUrl: String) : UploadState()
}

class UploadManager {
    fun handleEvent(event: UploadEvent, currentState: UploadState): UploadState {
        // The power of exhaustive 'when'
        return when (currentState) {
            is UploadState.Idle -> {
                if (event is UploadEvent.Start) UploadState.Uploading(0, event.fileSize)
                else currentState
            }
            is UploadState.Uploading -> {
                when (event) {
                    is UploadEvent.ChunkSent -> UploadState.Uploading(event.newBytesSent, currentState.totalBytes)
                    is UploadEvent.NetworkLost -> UploadState.Paused("Waiting for connection")
                    else -> currentState
                }
            }
            // ... handles other states safely
        }
    }
}
```

## Android Example

Jetpack Compose UIs are fundamentally built around observing State patterns.

```kotlin
@Composable
fun UserProfileScreen(state: ProfileState) {
    // The UI acts as a dumb renderer of the current State class
    when (state) {
        is ProfileState.Loading -> CircularProgressIndicator()
        is ProfileState.Error -> ErrorBanner(state.message)
        is ProfileState.Success -> ProfileCard(state.user)
    }
}
```
Because `ProfileState` is a sealed interface, the compiler enforces that every possible state is handled by the UI.

## Tradeoffs

**Advantages**
- **Eliminates God-Conditionals:** Replaces complex `if/else` logic with discrete, focused objects or patterns.
- **Exhaustiveness:** Kotlin's sealed classes ensure that when a new state is added, the compiler flags every place in the app that needs to handle it.
- **Safety:** Eliminates invalid combinations of state variables.

**Disadvantages**
- **Boilerplate:** For very simple two-state systems (e.g., a simple on/off toggle switch), creating sealed classes is overkill compared to a single boolean.
- **Transition Complexity:** If states are allowed to mutate the Context directly (Classic pattern), tracing *how* the app got into a specific state can become difficult. (This is why UDF/MVI centralizes state transitions in a Reducer).

## Failure Modes

- **The Boolean Trap:** Modeling state with concurrent properties: `val isLoading: Boolean, val user: User?, val error: String?`. What does it mean if `isLoading` is true AND `error` is not null? The UI doesn't know. Use a Sealed Class instead.
- **State Explosion:** If a single sealed class has 50 variants, you probably have multiple orthogonal states (e.g., `AuthenticationState` and `NetworkConnectivityState`). They should be modeled as separate state machines that are combined by the observer.
- **God States:** A state that holds data irrelevant to its status. E.g., `Loading(val previousUser: User)`. If the data spans states, it belongs in the Context, not the State payload.

## Staff Engineer Thinking

When reviewing state management, a Staff engineer asks:

1.  **Can we make invalid states unrepresentable?** If I see `data class ViewState(val loading: Boolean, val data: List<Item>)`, I will ask the author to refactor it to a sealed class to prevent the `loading=true && data.isNotEmpty()` paradox.
2.  **Is this a Finite State Machine?** Do we explicitly define the valid transitions between states? Or can the system jump from `Idle` directly to `Complete` due to a race condition?
3.  **Where do side effects happen?** When we transition to `LoadingState`, who triggers the network request? Mixing state mutation logic with side-effect execution leads to untestable ViewModels.

## Common Misconceptions

- **"State and Strategy are the same."** Structurally, yes. But intentionally, no. **Strategy** is an algorithm swapped by the *client* to change how something is done. **State** is swapped *internally* by the context or the states themselves to react to lifecycle or events.
- **"Sealed Classes are just enums."** Enums represent a closed set of *values* (all instances are the same type). Sealed classes represent a closed set of *types* (each state can hold its own unique payload, e.g., `Error` holds an Exception, `Loading` holds nothing).

## Probing Questions

1.  How do Sealed Interfaces in Kotlin improve the implementation of the State pattern compared to traditional Java Interfaces?
2.  Explain the difference between the State pattern and the Strategy pattern. Provide an example of when to use each.
3.  What are the consequences of modeling a 3-state system (Loading, Success, Error) with two booleans?
4.  In the classic State pattern, should the State objects be responsible for transitioning to the next state, or should the Context do it?
5.  How does Unidirectional Data Flow (UDF) utilize the State pattern?
6.  If you have a screen that shows a list of items, but each item has an independent "liking" animation state, how do you model that? Does the whole screen state change?
7.  What is the "Reducer" concept in MVI, and how does it relate to state transitions?
8.  Why is immutability a critical requirement for State objects in modern Android UI development?
9.  If a state transition requires an asynchronous operation (like saving to a database), how do you prevent the state from changing again before the async operation completes?
10. Can a State object hold a reference to the Android `Context`? Why or why not?

## Further Reading

- [`engineering-fundamentals/state-machines.md`](../engineering-fundamentals/state-machines.md) — The theoretical mechanics of FSMs.
- [`strategy.md`](strategy.md) — The structural twin to the State pattern.
- [`principles/make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md) — The core principle behind why we use Sealed Classes.
