# Determinism

## Overview

Determinism is the principle that a given set of inputs will always, without exception, produce the exact same output and result in the exact same state. A deterministic system behaves predictably. A non-deterministic system produces random, flaky, or unpredictable behavior. In mobile engineering, striving for determinism is the only way to build testable and reliable software.

## Why It Matters

"It works on my machine" is the battle cry of a non-deterministic system. If a function works 99 times but crashes on the 100th time, it is a nightmare to debug. Non-determinism destroys developer confidence. It leads to flaky tests that the team eventually ignores. If tests are ignored, bugs slip into production, and the application's perceived quality plummets.

## Historical Context

In functional programming, determinism is strictly enforced: "Pure functions" have no side effects and rely solely on their arguments. In Object-Oriented programming, determinism was often sacrificed for convenience (e.g., using a global `Singleton` that holds hidden, changing state). The shift toward Unidirectional Data Flow (UDF) in Android is largely an attempt to wrestle non-deterministic UI states back under strict, deterministic control.

## First Principles

1.  **Same Input = Same Output:** The core mathematical definition. $f(x) = y$, always and forever.
2.  **No Hidden State:** A function's behavior must not depend on global variables, system time, or randomized variables that are not passed in as arguments.
3.  **No Side Effects:** A function should not secretly mutate something outside of its scope (like writing to a database or changing a global variable) while doing its primary job.

## Mental Model

Think of a basic calculator versus a slot machine.

- **Deterministic (The Calculator):** If you press `2 + 2`, the output is `4`. If you press it a million times, the output is always `4`. You can write a test for this with 100% confidence.
- **Non-Deterministic (The Slot Machine):** You pull the lever (the input). Sometimes you get three cherries. Sometimes you get three bells. The output relies on a hidden Random Number Generator (hidden state). You cannot write a predictable unit test for pulling the lever.

## Internal Mechanics

The most common sources of non-determinism in Android are Time, Concurrency (Threads), and Global State.

### 1. The Time Problem

Time is inherently non-deterministic because it is always moving forward.

**Bad (Non-Deterministic):**
```kotlin
fun isWeekend(): Boolean {
    // Hidden dependency on the system clock!
    val today = Calendar.getInstance().get(Calendar.DAY_OF_WEEK)
    return today == Calendar.SATURDAY || today == Calendar.SUNDAY
}

// How do you unit test this? The test will pass on Friday and fail on Saturday.
```

**Good (Deterministic):**
```kotlin
// Time is passed as an explicitly injected input.
fun isWeekend(clock: Clock): Boolean {
    val today = clock.now().dayOfWeek
    return today == DayOfWeek.SATURDAY || today == DayOfWeek.SUNDAY
}

// In the Unit Test, you pass a FakeClock frozen to a Tuesday.
// The test is 100% deterministic.
```

### 2. The Concurrency Problem

If Thread A and Thread B access a mutable variable at the same time, the result depends entirely on which thread the OS schedules first. This is a Race Condition.

**Bad (Non-Deterministic Race Condition):**
```kotlin
var counter = 0 // Shared mutable state

fun increment() {
    counter++ // Under the hood: read, add 1, write. 
}
// If two threads call increment() at the exact same millisecond, 
// the counter might only increase by 1.
```

**Good (Deterministic Thread Safety):**
```kotlin
val counter = AtomicInteger(0)

fun increment() {
    counter.incrementAndGet() // Atomic operation, thread-safe.
}
```

## Architecture

```mermaid
graph TD
    subgraph Pure Function (Deterministic)
        In1[Input Data] --> F1((Function))
        F1 --> Out1[Predictable Output]
    end
    
    subgraph Impure Function (Non-Deterministic)
        In2[Input Data] --> F2((Function))
        Time[Hidden State: System.currentTime] -.-> F2
        F2 --> Out2[Random Output]
        F2 -.-> SideEffect[Side Effect: Writes to DB]
    end
```

## Production Example

**Jetpack Compose**

Jetpack Compose relies on determinism to function. A `@Composable` function transforms State (Input) into UI (Output). 

If you put non-deterministic code inside a Composable, the UI will glitch.

```kotlin
// BAD: Non-Deterministic Composable
@Composable
fun Greeting(name: String) {
    // Math.random() is non-deterministic hidden state!
    val color = if (Math.random() > 0.5) Color.Red else Color.Blue
    
    Text(text = "Hello $name", color = color)
    // Every time the screen recomposes (e.g., during a scroll), 
    // the text will randomly flash red and blue.
}
```

Compose expects functions to be *Idempotent* (a form of determinism where executing it multiple times yields the same result) and *Side-effect free*.

## Tradeoffs

**Advantages**
- **Testability:** Deterministic code is trivial to test. You pass input A, you assert output B.
- **Debuggability:** If a bug occurs, you know exactly how to reproduce it. (Provide the same inputs).
- **Caching:** If $f(x)$ always equals $y$, you can compute it once, save $y$ in a cache, and never run the computation again (Memoization).

**Disadvantages**
- **Boilerplate:** To make things deterministic, you often have to inject dependencies (like `Clock` or `Random` generators) through constructors, which adds boilerplate compared to just calling `System.currentTimeMillis()`.
- **Not Everything is Deterministic:** Network calls and User Inputs are inherently non-deterministic. The architecture must carefully quarantine these operations at the edges of the system so the core business logic remains pure.

## Failure Modes

- **Flaky Tests:** The ultimate symptom of non-determinism. A test that fails 1 out of 10 times usually relies on Thread timing, System Time, or a shared database that isn't cleared between tests. *Flaky tests must be deleted or fixed immediately; they destroy trust in the CI pipeline.*
- **Global Singletons:** Using a global object like `UserManager.currentUser`. If one test logs in a user and forgets to log them out, the next test fails because the global state was mutated.
- **Unordered Collections:** Iterating over a `HashSet` or `HashMap`. The order of elements is not guaranteed. If your logic relies on the order, it will behave non-deterministically. (Fix: Use `LinkedHashSet` or sort the list first).

## Staff Engineer Thinking

When reviewing code or investigating flaky tests, a Staff engineer hunts for non-determinism:

1.  **Where does Time come from?** I ban direct calls to `System.currentTimeMillis()` or `LocalDate.now()` in business logic. They must be hidden behind an injectable `Clock` interface.
2.  **Are we relying on sorting?** If an API returns a list of items, and we just take `list[0]`, is the API guaranteed to sort them? If not, `list[0]` is non-deterministic. The client must sort the list explicitly before grabbing the first item.
3.  **Is the UI state reproducible?** If a user reports a crash, and they provide the exact JSON payload from the API that caused it, can I inject that JSON into my emulator and reproduce the exact crash? If the UI relies on complex hidden variables, I cannot.

## Common Misconceptions

- **"I don't need determinism if I don't write tests."** Tests just reveal the non-determinism. If you don't write tests, the non-determinism is still there, it's just your users experiencing the flaky, random crashes instead of your CI pipeline.
- **"Network calls are deterministic if the server is reliable."** False. A backhoe can cut a fiber optic cable outside your office. The network is the definition of non-determinism. You must handle the failure gracefully.

## Probing Questions

1.  What is a "Pure Function", and why is it desirable in software architecture?
2.  How does a hidden dependency on `System.currentTimeMillis()` destroy the testability of a function? How do you fix it?
3.  Explain why Race Conditions are considered non-deterministic.
4.  Why does Jetpack Compose require `@Composable` functions to be deterministic (idempotent and side-effect free)?
5.  What is a "Flaky Test", and what are the most common causes of them in Android?
6.  How does passing a Random Number Generator as an argument to a function (Dependency Injection) make the function more deterministic?
7.  Why is relying on the iteration order of a standard `HashMap` dangerous?
8.  If an API response can fail due to a network timeout, how do you architect the system so the core business logic remains deterministic?
9.  Explain the concept of "Memoization" and how it relies on determinism.
10. Give an example of how Global State (Singletons) introduces non-determinism into a test suite.

## Further Reading

- [`immutability.md`](../engineering-fundamentals/immutability.md) — Immutability removes shared mutable state, one of the primary causes of non-determinism.
- [`simplicity.md`](simplicity.md) — Simple code is easier to make deterministic.
- [Pure Functions (Wikipedia)](https://en.wikipedia.org/wiki/Pure_function)
