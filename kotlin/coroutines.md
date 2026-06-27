# Coroutines

## Overview

Coroutines are Kotlin's solution for asynchronous, non-blocking programming. Instead of dealing with Callbacks, Futures, or RxJava streams, Coroutines allow you to write asynchronous code (like making a network request) in a sequential, top-to-bottom style that looks exactly like normal, synchronous code.

At the core, a Coroutine is "lightweight thread"—a unit of work that can be paused (suspended) and resumed later without blocking the underlying operating system thread.

## Why It Matters

Android has a strict rule: You cannot do heavy work (Network, Database) on the Main (UI) Thread, or the app will freeze. You also cannot update the UI from a Background Thread, or the app will crash.

Historically, this required passing data back and forth between threads using interfaces (Callback Hell). Coroutines solve this by allowing the compiler to handle the thread-jumping invisibly. You can request data on a background thread and immediately assign it to the UI on the next line of code.

## Historical Context

Concurrency in Java was built on OS Threads (`java.lang.Thread`). Threads are incredibly heavy. Creating a thread takes massive memory (1MB stack space) and CPU time. You cannot create 10,000 threads.

RxJava was introduced as an alternative, pushing events through functional streams. It was powerful but incredibly difficult to learn, resulting in unreadable stack traces. 

Kotlin Coroutines use "Continuation-Passing Style" (CPS), an academic computer science concept from the 1970s. The Kotlin compiler breaks your code into a state machine, allowing millions of coroutines to run concurrently on just a handful of OS threads.

## First Principles

1.  **Suspend:** The magic keyword. A `suspend` function can pause the execution of the current coroutine, freeing up the underlying thread to do other work, and resume later when the result is ready.
2.  **Dispatchers:** The thread pools. They determine *where* the coroutine runs. `Dispatchers.Main` (UI), `Dispatchers.IO` (Network/Disk), `Dispatchers.Default` (Heavy CPU math).
3.  **Structured Concurrency:** Coroutines must be launched inside a `CoroutineScope`. If the scope is cancelled (e.g., the user closes the screen), all running coroutines inside it are instantly cancelled, preventing memory leaks and wasted network calls.

## Mental Model

Think of a chef in a kitchen (The Thread).
- **Blocking (Java Threads):** The chef puts a pizza in the oven, and then stands in front of the oven staring at it for 20 minutes. No other work gets done. If you want a salad made, you have to hire a second chef (A second Thread).
- **Suspending (Coroutines):** The chef puts the pizza in the oven, sets a timer (Suspends), and walks away to chop vegetables for a salad. When the timer goes off, the chef Resumes the pizza task. One chef (Thread) is doing the work of many.

## Internal Mechanics

How does `suspend` actually work without blocking the thread? 

### The State Machine

```kotlin
suspend fun fetchUserAndShow() {
    println("Start")                    // State 0
    val user = api.fetchUser()          // Suspend point
    println("Name: ${user.name}")       // State 1
}
```

When the compiler sees the `suspend` keyword, it rewrites the function. It generates a massive `switch` statement (a State Machine) and injects a hidden parameter called a `Continuation`.

*Decompiled Concept:*
```java
// What the JVM actually executes
Object fetchUserAndShow(Continuation cont) {
    StateMachine sm = (StateMachine) cont;
    switch(sm.label) {
        case 0:
            System.out.println("Start");
            sm.label = 1;
            // The thread is returned to the pool!
            return api.fetchUser(sm); 
        case 1:
            User user = (User) sm.result;
            System.out.println("Name: " + user.name);
            return Unit;
    }
}
```
When `fetchUser` is called, the function literally returns early, freeing the thread. When the network call finishes, it calls `fetchUserAndShow` *again*, but passes in `label = 1`, allowing it to jump straight to the second half of the function.

## Architecture

```mermaid
graph TD
    subgraph Coroutine Scope (e.g. viewModelScope)
        Scope --> Launch[launch]
        
        Launch -->|Thread: Main| UI[Show Loading Spinner]
        
        UI -->|withContext: IO| Net[Suspend: Fetch API]
        
        Net -.->|Thread Freed| Free[Main Thread handles user scrolling]
        Net -.->|API Returns| Resume
        
        Resume[Resume on Main] -->|Thread: Main| UpdateUI[Show Data]
    end
```

## Production Example

**The Golden Path (Android ViewModel)**

This is the standard pattern for modern Android development. 

```kotlin
class ProfileViewModel(private val api: Api) : ViewModel() {

    private val _uiState = MutableStateFlow<String>("Loading")
    val uiState = _uiState.asStateFlow()

    fun loadProfile() {
        // 1. Structured Concurrency: Ties the coroutine to the ViewModel's lifecycle
        viewModelScope.launch {
            try {
                // 2. Main Thread: Safe to update UI
                _uiState.value = "Fetching..." 
                
                // 3. Suspend & Thread Jump: Move to IO pool, free the Main thread
                val data = withContext(Dispatchers.IO) {
                    api.getUser() 
                }
                
                // 4. Resume: Automatically back on Main Thread!
                _uiState.value = data.name 
                
            } catch (e: Exception) {
                // CancellationExceptions are handled transparently
                _uiState.value = "Error"
            }
        }
    }
}
```

## Tradeoffs

**Advantages**
- **Readability:** Asynchronous code reads linearly. No `flatMap` or `.then()` nesting.
- **Resource Efficiency:** You can launch 100,000 coroutines without running out of memory. Try that with Threads and your app will crash instantly (OOM).
- **Memory Safety:** Structured Concurrency guarantees that when a ViewModel dies, all its pending network requests are killed instantly.

**Disadvantages**
- **The "Color" Problem:** A `suspend` function can only be called from another `suspend` function or a Coroutine Builder (`launch`). If you have a massive legacy Java codebase, bridging the gap between non-suspend Java and suspend Kotlin is painful.
- **Testing:** Testing coroutines requires manipulating virtual time (`TestCoroutineScheduler`) to fast-forward through `delay()` calls. If configured incorrectly, tests will be flaky or hang forever.
- **Exception Handling is Bizarre:** If a child coroutine throws an Exception, it immediately cancels its parent, which cancels all other siblings. Trying to use a `try/catch` around a `launch` block does not work. You must use `CoroutineExceptionHandler` or `supervisorScope`.

## Failure Modes

- **Blocking the Main Thread inside a Coroutine:**
  ```kotlin
  viewModelScope.launch {
      // BAD: This runs on Dispatchers.Main by default.
      // Thread.sleep() BLOCKS the thread, it does NOT suspend.
      // The app will freeze and ANR.
      Thread.sleep(5000) 
      
      // GOOD: delay() SUSPENDS the coroutine, freeing the Main thread.
      delay(5000)
  }
  ```
- **The GlobalScope Leak:**
  ```kotlin
  // DISASTER: This coroutine lives until the app process is killed.
  // If the user navigates away, this keeps downloading data in the background,
  // draining battery and leaking memory.
  GlobalScope.launch {
      downloadMassiveFile()
  }
  ```
  *(Fix: Always use lifecycle-aware scopes like `viewModelScope` or `lifecycleScope`).*
- **Swallowing CancellationException:**
  ```kotlin
  try {
      delay(5000)
  } catch (e: Exception) {
      // BAD: You just caught the CancellationException!
      // When the ViewModel dies, it tries to cancel this coroutine, 
      // but you caught the signal and ignored it. The coroutine will continue running as a zombie.
      Log.e("Error", e.message)
  }
  ```
  *(Fix: Always `catch (e: IOException)` specifically, or rethrow `CancellationException`).*

## Staff Engineer Thinking

When reviewing concurrency, a Staff engineer focuses on execution boundaries:

1.  **Who controls the Dispatcher?** I enforce that all `suspend` functions must be "main-safe." A repository function `suspend fun getUsers()` must internally wrap its work in `withContext(Dispatchers.IO)`. The ViewModel should NEVER have to specify `Dispatchers.IO` when calling a repository. This is called *Dispatcher Injection*.
2.  **Are we using Supervisor Jobs?** If a ViewModel launches three independent network calls (`async { }`), and one fails, the default behavior is to cancel the other two. I ask: "Is this the intended business logic?" Usually, it's not. I will enforce `supervisorScope` to isolate the failures.
3.  **The StateFlow Pivot:** I push teams away from using `LiveData` (which is deeply tied to the Android OS framework) to pure Kotlin `StateFlow` and `SharedFlow`. This allows our domain and data layers to be completely independent of Android, making them unit testable on a standard JVM.

## Common Misconceptions

- **"Coroutines are just Threads."** No. Multiple coroutines can run on a single thread. A coroutine is a state machine managed by the Kotlin library; a thread is a resource managed by the Operating System.
- **"Coroutines make my code run faster."** False. A network request takes 200ms whether you use Threads, RxJava, or Coroutines. Coroutines just make your app use *fewer resources* (memory/CPU) while waiting for that 200ms to pass.

## Probing Questions

1.  Explain the fundamental difference between `Thread.sleep()` and `delay()` in Kotlin.
2.  What is "Structured Concurrency" and how does it prevent memory leaks in Android ViewModels?
3.  Describe the "State Machine" mechanism the Kotlin compiler generates when it encounters the `suspend` keyword.
4.  Why is it an architectural anti-pattern for a ViewModel to pass `Dispatchers.IO` when calling a Repository `suspend` function? (Main-Safety).
5.  What is a `CancellationException`, and why is it dangerous to write a generic `catch (e: Exception)` block inside a coroutine?
6.  Explain the difference between `launch` and `async`. When would you use one over the other?
7.  Why did the Android community largely abandon RxJava in favor of Kotlin Coroutines?
8.  If you have three concurrent `async` tasks running inside a standard `coroutineScope`, what happens to tasks B and C if task A throws an exception? How do you change this behavior?
9.  Why is `GlobalScope.launch` considered highly dangerous in Android development?
10. How does a Coroutine "suspend" its execution without blocking the underlying OS Thread? Where does the thread go?

## Further Reading

- [`generics.md`](generics.md) — The foundation for understanding how `Continuation<T>` works.
- [`../observability/tracing.md`](../observability/tracing.md) — How to track performance across asynchronous coroutine boundaries.
- [Kotlin Docs: Coroutines Basics](https://kotlinlang.org/docs/coroutines-basics.html)
