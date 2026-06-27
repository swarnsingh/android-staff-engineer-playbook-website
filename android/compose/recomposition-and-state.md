# Recomposition and State

## Overview

Jetpack Compose represents a massive paradigm shift in Android development, moving from an Imperative UI system (`View` subclasses mutated via `findViewById`) to a Declarative UI system (pure Kotlin functions that transform State into UI).

A Staff Engineer understands that Compose is not just a UI framework; it is fundamentally a **State Management Compiler**. The `@Composable` annotation alters how the Kotlin compiler handles functions, injecting a hidden `Composer` object that tracks every single piece of state read within that function. When the state changes, Compose "Recomposes" (re-executes) only the functions that read that specific state.

## Why It Matters

In the legacy XML system, the UI stored its own state. A `TextView` inherently knew its own text. If you wanted to change it, you imperatively commanded it: `textView.text = "Hello"`. This led to catastrophic synchronization bugs where the ViewModel thought the user was logged out, but the `TextView` still displayed "Welcome Back" because the developer forgot to manually update the View.

Compose enforces **Unidirectional Data Flow (UDF)**. The UI stores *zero* state. It simply reflects the State provided by the ViewModel. If the state changes, the UI redraws itself automatically. However, if you misunderstand how Compose detects these state changes, you will trigger infinite loops or massive frame drops (Jank).

## Historical Context

- **Pre-2020 (XML):** Deeply nested XML files parsed at runtime using Reflection (`LayoutInflater`). Slow, bloated, and state was scattered across `Activity.kt` and the `View` instances.
- **React/Flutter:** The web and cross-platform communities proved that Declarative UI was vastly superior for developer velocity and bug reduction. 
- **Jetpack Compose (2021):** Google's answer. Built entirely from scratch. Unlike React (which uses a Virtual DOM to diff changes), Compose uses a Positional Memoization compiler plugin. It tracks exactly which line of code generated which UI node, allowing for insanely fast, targeted updates without a Virtual DOM overhead.

## First Principles

1.  **State:** Any value that can change over time.
2.  **`MutableState<T>`:** Compose's observable data holder. If a `@Composable` reads a `State` object, it subscribes to it.
3.  **Composition:** The initial execution of your `@Composable` functions. It builds the UI tree.
4.  **Recomposition:** The re-execution of specific `@Composable` functions when the State they read changes.
5.  **Smart Recomposition:** Compose actively attempts to *skip* recomposing functions if it mathematically proves their inputs have not changed.

## Mental Model

Think of Compose as a **Fast-Food Kitchen Screen**.
- The Kitchen Screen (UI) is dumb. It only shows what the Cashier Register (State) tells it to show.
- When an order changes from "Pending" to "Cooking", the Register updates its State.
- The Kitchen Screen doesn't recreate the entire list of 50 orders. It looks at the exact row for Order #12 and changes the color to Green (Smart Recomposition).

## Internal Mechanics

### The Magic of the Compiler Plugin

When you annotate a function with `@Composable`, the Kotlin compiler completely rewrites it.

```kotlin
// Your Code:
@Composable
fun Greeting(name: String) {
    Text(text = "Hello $name")
}

// What the Compiler generates (Conceptually):
fun Greeting(name: String, $composer: Composer, $changed: Int) {
    $composer.startRestartGroup(123)
    // Compose checks if 'name' changed since the last execution
    if ($changed or $composer.changed(name)) {
        Text("Hello $name", $composer)
    } else {
        $composer.skipToGroupEnd() // SMART SKIP!
    }
    $composer.endRestartGroup()?.updateScope { 
        Greeting(name, it, $changed) 
    }
}
```
If `name` hasn't changed, the entire execution of `Text()` is physically skipped. 

### `remember` vs `State`

```kotlin
@Composable
fun Counter() {
    // 1. Just a variable. Recomposition resets it to 0. Useless.
    var count = 0 
    
    // 2. Remembered, but not State. Compose doesn't know when it changes. 
    // The UI will never update.
    var count2 = remember { 0 } 
    
    // 3. The Correct Way. 
    // 'remember' survives recomposition.
    // 'mutableStateOf' tells Compose to redraw when it changes.
    var count3 by remember { mutableStateOf(0) } 
    
    Button(onClick = { count3++ }) {
        Text("Count is $count3")
    }
}
```

## Architecture

```mermaid
graph TD
    subgraph ViewModel
        State[StateFlow]
    end
    
    subgraph UI Layer
        Screen[Screen Composable]
        Button[Button Composable]
    end
    
    State -.->|collectAsState()| Screen
    Screen -->|Passes State| Button
    Button -->|User Clicks| Event[Intent]
    Event -->|Mutates| State
```
*Unidirectional Data Flow: State flows down, Events flow up.*

## Production Example

**State Hoisting**

A Staff Engineer enforces "State Hoisting". A component should not manage its own internal state if that state is relevant to the rest of the application.

```kotlin
// BAD: The CustomTextField is "Stateful". 
// The parent screen cannot read the text, clear the text, or validate it.
@Composable
fun StatefulTextField() {
    var text by remember { mutableStateOf("") }
    TextField(value = text, onValueChange = { text = it })
}

// GOOD: The CustomTextField is "Stateless".
// The state is hoisted up to the caller (The Screen or ViewModel).
@Composable
fun StatelessTextField(
    text: String, // State flows in
    onTextChanged: (String) -> Unit // Events flow out
) {
    TextField(value = text, onValueChange = onTextChanged)
}

// Usage in the Parent
@Composable
fun LoginScreen(viewModel: LoginViewModel) {
    val text by viewModel.emailFlow.collectAsState()
    StatelessTextField(text = text, onTextChanged = viewModel::onEmailChanged)
}
```

## Tradeoffs

**`StateFlow` vs `LiveData` vs Compose `State`**

In the ViewModel, how should we hold state?

- **`LiveData`:** Deprecated. It is tied to the Android OS lifecycle (which is good for XML), but it lacks the rich transformation operators of Kotlin Flow. It also only runs on the Main Thread.
- **Compose `MutableState` in ViewModel:** Some developers put `var text by mutableStateOf("")` directly in the ViewModel. 
    - *Pros:* No need to call `collectAsState()` in the UI. 
    - *Cons:* It permanently ties your ViewModel to the Compose framework dependency (`androidx.compose.runtime`). You cannot share this ViewModel with a KMP iOS app.
- **`StateFlow`:** The industry standard.
    - *Pros:* Pure Kotlin. Cross-platform. Thread-safe. Rich operators (`map`, `combine`).
    - *Cons:* You must explicitly convert it to Compose state in the UI using `collectAsStateWithLifecycle()`.

## Failure Modes

- **The List Mutation Trap:**
  ```kotlin
  val items = remember { mutableStateListOf("A", "B") }
  // OR
  var list by remember { mutableStateOf(listOf("A", "B")) }
  ```
  If you use a standard `ArrayList` and call `list.add("C")`, Compose will not recompose. Compose only checks if the *reference* to the object changed. `list` is still pointing to the exact same memory address. 
  *(Fix: You must use `mutableStateListOf` which triggers Compose internally, OR create a brand new list: `list = list + "C"`).*
- **Unstable Classes (The Jank Generator):**
  As discussed in [Jank](../performance/jank.md), if you pass a class into a Composable, Compose tries to determine if it is "Stable." If it contains a `var`, or a `List` interface (which might be a mutable `ArrayList`), Compose marks it Unstable. If a parameter is Unstable, Compose **will never skip** recomposition of that function, destroying your frame rate.
  *(Fix: Annotate data classes with `@Immutable`, or use `kotlinx.collections.immutable.PersistentList`).*
- **Infinite Recomposition Loops:**
  ```kotlin
  @Composable
  fun InfiniteLoop() {
      var count by remember { mutableStateOf(0) }
      // DISASTER: We mutate state directly in the composition phase!
      count++ 
      Text("Count: $count")
  }
  ```
  1. Compose runs `InfiniteLoop`. 
  2. `count` becomes 1. 
  3. Because `count` changed, Compose says "I need to recompose `InfiniteLoop`." 
  4. It runs again. `count` becomes 2. 
  5. Repeat infinitely until the app crashes or freezes.
  *(Fix: State must only be mutated in callbacks (`onClick`) or Side Effects (`LaunchedEffect`)).*

## Staff Engineer Thinking

When reviewing Compose architecture, a Staff engineer focuses relentlessly on Recomposition boundaries.

1.  **Layout Inspector:** I use the Android Studio Layout Inspector and turn on "Recomposition Counts." If I scroll a list and see the recomposition count of the `TopAppBar` rocketing up to 500, we have a massive state read leak. The scroll state is being read too high in the tree.
2.  **`derivedStateOf`:** If a ViewModel exposes a list of 100 items, and the UI needs to show a "Scroll to Top" button only when the user scrolls past item 5, junior developers will read `listState.firstVisibleItemIndex > 5` directly in the composition. This causes recomposition on *every single pixel scrolled*. I enforce the use of `remember { derivedStateOf { listState.firstVisibleItemIndex > 5 } }`, which coalesces the rapid stream of index changes into a single boolean state change.
3.  **UI State Data Classes:** I reject PRs where a ViewModel exposes 15 different `StateFlow` variables (`isLoading`, `isError`, `data`, `title`). A screen should observe exactly ONE `data class UiState(...)`. This prevents tearing (the UI observing `data` but not yet seeing `isLoading = false`).

## Common Misconceptions

- **"Compose is slower than XML because it recreates the UI constantly."** False. Compose doesn't "recreate" UI elements; it traverses an existing tree in memory and updates the specific node parameters. It is significantly faster than XML `findViewById` traversals, *if* your recompositions are properly scoped.
- **"I don't need ViewModels anymore, I can just use `remember`."** False. State inside `remember` dies if the configuration changes (device rotation) or if the Composable is removed from the screen (navigating away). ViewModels survive configuration changes.

## Probing Questions

1.  What is the fundamental difference between an Imperative UI framework (like XML/Views) and a Declarative UI framework (like Compose) regarding State?
2.  Explain the concept of "Smart Recomposition" and how the Compose compiler achieves it.
3.  Why does assigning a value to a standard variable (`var count = 0`) inside a `@Composable` fail to update the UI when the variable changes?
4.  Describe the difference between `remember { }` and `mutableStateOf()`. Why do you usually need both together?
5.  What is "State Hoisting," and why is it critical for building reusable, testable Compose components?
6.  If you add an item to a standard Kotlin `ArrayList` that is wrapped in a `mutableStateOf`, why does the UI fail to recompose?
7.  What does it mean for a class to be marked as "Unstable" by the Compose compiler, and what is the severe performance penalty?
8.  Explain how mutating a `MutableState` value directly inside the body of a `@Composable` function (outside of a callback) creates an infinite loop.
9.  Why is `StateFlow` generally preferred over putting `MutableState` directly inside a `ViewModel`?
10. How does the `derivedStateOf` function help prevent unnecessary recompositions when dealing with rapidly changing values like scroll positions?

## Further Reading

- [`jank.md`](../performance/jank.md) — How Unstable classes and bad state reads cause dropped frames.
- [`side-effects.md`](side-effects.md) — How to safely execute non-composable code (like Snackbar popups) from within the Compose state machine.
- [Android Developers: State and Jetpack Compose](https://developer.android.com/jetpack/compose/state)
