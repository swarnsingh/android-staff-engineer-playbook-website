# ViewModel

## Overview

The `ViewModel` is the most ubiquitous architectural component in modern Android development. Its primary responsibility is to act as a **State Holder** for the UI, surviving Configuration Changes (like screen rotations) to prevent data loss.

It separates the chaotic, OS-driven lifecycle of the UI controller (Activity/Fragment) from the clean, pure Kotlin business logic of your application. The UI observes the ViewModel; the ViewModel exposes state and receives events.

## Why It Matters

Before 2017, Android developers struggled massively with screen rotations. When you rotate an Android phone, the OS destroys the Activity and recreates it. If you were in the middle of fetching a 5MB JSON payload over the network, that request would be orphaned, memory would leak, and the new Activity would trigger a redundant network request.

Developers used horrible hacks like `onRetainNonConfigurationInstance()` or retained headless Fragments to save their data. The Jetpack `ViewModel` was introduced to solve this specific problem elegantly and safely.

## Historical Context

It is critical to distinguish between the **Jetpack ViewModel** and the **MVVM ViewModel** (invented by Microsoft in 2005).

- **Microsoft's MVVM:** A design pattern relying heavily on *Data Binding*. The ViewModel exposes properties, and the XML View binds to them directly.
- **Jetpack ViewModel:** An Android OS lifecycle wrapper. It is simply an object that the `ViewModelStore` keeps alive across rotations.

While Jetpack ViewModels *can* be used in an MVVM architecture, they are increasingly used in **MVI (Model-View-Intent)** or **Unidirectional Data Flow (UDF)** architectures, especially with Jetpack Compose, where XML Data Binding does not exist.

## First Principles

1.  **The `ViewModelStore`:** ViewModels don't exist in a vacuum. They live inside a `ViewModelStore`. The `ViewModelStoreOwner` (usually an Activity or a Navigation Graph) holds this store.
2.  **Configuration Change Survival:** When the OS destroys an Activity for rotation, it *retains* the `ViewModelStore` in memory. When the new Activity is created, it grabs the old store, recovering the exact same ViewModel instances.
3.  **No OS Awareness:** A ViewModel should be a pure Kotlin class. It must *never* hold a reference to an `Activity`, `Fragment`, `View`, or Android `Context`. If it does, you will cause a massive memory leak.

## Mental Model

Think of the `Activity` as a **Television Screen** and the `ViewModel` as the **Cable Box**.

- If you unplug the TV to move it across the room (Configuration Change), the TV goes black. But the Cable Box stays plugged into the wall, still streaming the channel, still holding the state.
- When you plug the TV back in, you just connect the HDMI cable (Observation), and the show instantly resumes exactly where it was.
- However, if the power company cuts power to your entire house (System-Initiated Process Death), the Cable Box turns off too. (This is why you still need [SavedStateHandle](savedstatehandle.md)).

## Internal Mechanics

How does the `ViewModelStoreOwner` actually keep the ViewModel alive when the Activity is destroyed?

If you look at the source code of `ComponentActivity.java`, you'll see a method called `onRetainNonConfigurationInstance()`. 

```java
// Simplified ComponentActivity source code
public final Object onRetainNonConfigurationInstance() {
    // ...
    NonConfigurationInstances nci = new NonConfigurationInstances();
    // IT SAVES THE VIEWMODELSTORE HERE!
    nci.viewModelStore = mViewModelStore; 
    return nci;
}
```

The Android OS explicitly allows an Activity to pass *one* object to the OS before it is destroyed for a configuration change. Jetpack uses this loophole to hand the entire `ViewModelStore` to the OS. When the new Activity boots up, it asks the OS, "Hey, do you have my NonConfigurationInstance?" and gets the store back.

### The `onCleared()` Callback

When the Activity is *actually* finishing (e.g., the user presses the Back button to exit the screen permanently), the Activity will clear the `ViewModelStore`. 

The store iterates through all its ViewModels and calls their `onCleared()` method. This is where the ViewModel cancels its `viewModelScope` coroutines to stop background work.

## Architecture

```mermaid
graph TD
    subgraph View Layer (Survives Milliseconds)
        Act[Activity / Fragment / Compose UI]
    end
    
    subgraph State Layer (Survives Rotation)
        VM[ViewModel]
        State["StateFlow<UiState>"]
        VM --> State
    end
    
    subgraph Domain/Data Layer (Survives App Lifecycle)
        Repo[Repository]
    end
    
    Act -- 1. Sends Events (e.g. onClick) --> VM
    VM -- 2. Fetches Data --> Repo
    Repo -- 3. Emits Data --> VM
    VM -- 4. Mutates State --> State
    State -- 5. UI Observes State --> Act
```

## Production Example

**The UDF State Holder**

A Staff-level ViewModel does not expose 15 different `LiveData` objects. It exposes a single, immutable stream of UI State.

```kotlin
// The Immutable State
data class ProfileUiState(
    val isLoading: Boolean = false,
    val username: String = "",
    val error: String? = null
)

@HiltViewModel
class ProfileViewModel @Inject constructor(
    private val repository: UserRepository
) : ViewModel() {

    // Internal mutable state
    private val _uiState = MutableStateFlow(ProfileUiState())
    // Public immutable state
    val uiState: StateFlow<ProfileUiState> = _uiState.asStateFlow()

    init {
        // Load initial data
        loadUser()
    }

    // Public intent/event handler
    fun refresh() {
        loadUser()
    }

    private fun loadUser() {
        // viewModelScope is automatically cancelled in onCleared()
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            try {
                val user = repository.fetchUser()
                _uiState.update { it.copy(isLoading = false, username = user.name) }
            } catch (e: Exception) {
                _uiState.update { it.copy(isLoading = false, error = e.message) }
            }
        }
    }
}
```

## Tradeoffs

**ViewModel vs Standard Class**

Why not just use a regular Kotlin `class` for your business logic?
- If you use a regular class inside an `Activity`, it dies when the Activity rotates. You lose all state.
- If you use a regular class inside a global `Singleton` (e.g., injected via Dagger `@Singleton`), it survives rotation, but it *never dies*. The memory is leaked forever until the app process is killed.
- **The ViewModel Tradeoff:** It hits the perfect middle ground. It survives rotation, but it automatically dies (calls `onCleared()`) the exact moment the user is permanently finished with the screen. 

## Failure Modes

- **The Context Leak:**
  ```kotlin
  // DISASTER
  class BadViewModel(private val context: Context) : ViewModel() {
      // You just leaked the Activity context. When the phone rotates, 
      // the old Activity cannot be garbage collected because the ViewModel 
      // outlives it and holds a hard reference to it.
  }
  ```
  *(Fix: A ViewModel must never import `android.*` packages, except for `AndroidViewModel` which safely holds the `ApplicationContext` if absolutely necessary).*
- **Assuming Survival of Process Death:** Developers test their app by rotating the phone. The ViewModel survives. They assume the app is bulletproof. They put the app in the background, the LMK kills the process, the app restores, the ViewModel is completely blank, and the app crashes. *(Fix: All transient UI input must be backed by a [SavedStateHandle](savedstatehandle.md)).*
- **Initializing Data in Compose via `LaunchedEffect`:** A massive anti-pattern is triggering the ViewModel's initial data load from the UI using `LaunchedEffect`. The UI should just observe state. The ViewModel should load its own initial data in its `init {}` block or via lazy observation.

## Staff Engineer Thinking

When reviewing ViewModel architectures, a Staff engineer focuses on purity and flow:

1.  **Is the ViewModel Platform Agnostic?** A great ViewModel can be tested purely on the JVM (JUnit) without Robolectric. If the ViewModel requires Android dependencies (`Context`, `LocationManager`, `SensorManager`), those dependencies must be abstracted behind Kotlin Interfaces in the Domain layer.
2.  **Is it truly Unidirectional?** I will reject PRs where the ViewModel "calls a method" on the View (e.g., `view.showToast()`). The ViewModel must only mutate state (`_uiState.value = newState`). The View observes that state and decides to show the Toast.
3.  **ViewModel Scoping:** If a checkout flow requires 4 different screens, we should not pass huge objects via Navigation arguments. I will suggest scoping a single `CheckoutViewModel` to the *Navigation Graph*, allowing all 4 screens to effortlessly share the exact same ViewModel instance in memory.

## Common Misconceptions

- **"ViewModels are for business logic."** While they often contain UI-level logic (formatting a date, validating a password length), deep *Business Logic* (how to calculate tax on a shopping cart) belongs in a Repository or a Domain Use Case. The ViewModel is just a middleman.
- **"I should use `AndroidViewModel` to get a Context."** Avoid `AndroidViewModel` at all costs. It makes unit testing incredibly difficult. If you need a Context (e.g., to read a String resource), pass the resource ID (an `Int`) to the UI, and let the UI (which already has a Context) resolve the string.

## Probing Questions

1.  Explain exactly how the Android OS manages to keep the `ViewModel` instance alive in memory during a screen rotation while the `Activity` is completely destroyed.
2.  What is the architectural difference between Microsoft's original MVVM pattern and the Jetpack ViewModel approach used with Jetpack Compose?
3.  Describe the catastrophic memory leak that occurs when a `ViewModel` holds a hard reference to a `View` or an `Activity` context.
4.  Why is a `ViewModel` an insufficient solution for handling System-Initiated Process Death? What other Jetpack component must be used?
5.  What is `viewModelScope`, and what happens to the coroutines launched inside it when the user presses the Back button to exit the screen?
6.  Explain the concept of "Unidirectional Data Flow" (UDF) and how a ViewModel implements it using `StateFlow`.
7.  Why is it an anti-pattern to trigger a ViewModel's initial data load (e.g., `viewModel.fetchUsers()`) from a `LaunchedEffect` inside a Jetpack Compose screen?
8.  How can multiple Fragments or Compose screens share the exact same instance of a `ViewModel`? What dictates the "scope" of that ViewModel?
9.  If you absolutely need to access an Android system service (like `LocationManager`) to feed data to your ViewModel, how should you architect that without polluting the ViewModel with Android dependencies?
10. Describe the specific condition that triggers the `ViewModel.onCleared()` callback.

## Further Reading

- [`activity.md`](activity.md) — The lifecycle controller that owns the ViewModel.
- [`savedstatehandle.md`](savedstatehandle.md) — How to make the ViewModel survive true Process Death.
- [`flow.md`](flow.md) — The reactive streams used inside the ViewModel to expose state.
