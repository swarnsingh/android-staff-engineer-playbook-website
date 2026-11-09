# Concurrency & The Kotlin/Native Memory Model

> Concurrency in KMP is the single most dangerous topic for production stability. On Android, coroutines run on JVM threads managed by ART's garbage collector. On iOS, coroutines run on native threads managed by Kotlin/Native's own GC — a completely separate memory management system that coexists with Swift's ARC. If you don't understand the dual-GC architecture and the historical evolution of the K/Native memory model, you will ship apps that leak memory, deadlock on the iOS main thread, or crash with `ConcurrentModificationException` on release day.

---

## Overview

The Kotlin/Native memory model went through three distinct eras. Understanding all three is necessary because you will encounter legacy code from each era, and because the current model's design decisions only make sense in the context of what came before.

---

## 1. Era 1: Thread Confinement (2017-2022) — The Dark Ages

### The Rule
Kotlin/Native 1.0 through 1.6 enforced a strict rule:

> **Mutable objects cannot be shared between threads. If you want to pass an object to another thread, you must freeze it first.**

"Freezing" an object made it deeply immutable — the entire object graph became read-only. Any attempt to mutate a frozen object threw `InvalidMutabilityException` and crashed the app.

### Why This Existed
Kotlin/Native didn't have a concurrent garbage collector. If two threads modified the same object simultaneously, the reference counting system (similar to Swift's ARC) would corrupt the reference count, leading to use-after-free crashes or memory leaks. JetBrains chose to prevent this entirely at the language level.

### What This Looked Like in Practice

```kotlin
// Era 1 code — DO NOT WRITE THIS IN MODERN KMP

data class User(var name: String, var email: String)

fun brokenExample() {
    val user = User("Alice", "alice@example.com")
    
    // Freeze the user so it can cross thread boundaries
    user.freeze()
    
    CoroutineScope(Dispatchers.Default).launch {
        // This crash is INTENTIONAL — you cannot mutate a frozen object
        user.name = "Bob"  // 💥 InvalidMutabilityException
    }
}
```

### The Aftermath
This model was so painful that many early KMP adopters abandoned the platform entirely. Common complaints:
- Any object passed to a coroutine background thread was auto-frozen.
- Shared mutable-state patterns required careful thread/freeze ownership under the legacy manager; this did not make every ViewModel design impossible.
- `AtomicReference<T>` was the only way to hold mutable state across threads — ugly, error-prone, and unfamiliar to Android engineers.

**Migration:** Freeze-related APIs identify legacy constraints, but AtomicReference is also a current synchronization tool. An atomic reference can safely publish immutable snapshots; it does not make a mutable list's internal operations atomic.

---

## 2. Era 2: The New Memory Model (Kotlin 1.7.20+) — The Fix

### What Changed
Kotlin 1.7.20, released on 29 September 2022, made the new Native memory manager the default. The key changes:

1. **No more freezing.** Objects can be shared between threads freely, just like on the JVM.
2. **A new concurrent Garbage Collector.** The GC can now trace and collect objects that are referenced by multiple threads simultaneously.
3. **Thread-local policy:** SharedImmutable is obsolete under the new manager and can be removed. ThreadLocal is not marked deprecated in the current API; retain it only for an intentional thread-local contract.

### How the New GC Works

The Kotlin/Native GC uses a **tracing garbage collector** with concurrent marking:

```mermaid
sequenceDiagram
    participant A as Thread A
    participant B as Thread B
    participant GC as GC thread
    A->>A: Create User and set name to Alice
    A-->>B: Share reference to user
    B->>B: Set email through its reference
    GC->>GC: Mark phase: walk roots
    GC->>GC: Mark user reachable
    GC->>GC: Sweep unreachable objects
    Note over A,GC: User remains allocated because it is reachable
```

**Comparison with JVM collectors:** both Kotlin/Native and JVM collectors use safepoints and barriers as implementation tools. The current Kotlin/Native collector is non-generational concurrent mark-and-sweep; application threads can participate in marking and short stop-the-world phases still exist. Do not use "Native has barriers, JVM has safepoints" as the distinction.

### GC Configuration

You can tune the K/Native GC via `gradle.properties`:

```properties
# Current default is concurrent mark-and-sweep (CMS).
# Use PMCS only as a measured fallback when diagnosing a CMS regression.
kotlin.native.binary.gc=pmcs

# Disable allocator paging only after profiling memory behavior.
kotlin.native.binary.pagedAllocator=false

# Emit Apple-platform GC safepoints to Instruments.
kotlin.native.binary.enableSafepointSignposts=true
```

Allocator selection such as mimalloc is a compiler option (`-Xallocator=mimalloc`), not the obsolete `kotlin.native.allocator` property. These knobs evolve; verify them against the Kotlin/Native memory-manager documentation for the Kotlin version you ship.

**Staff Rule:** Do not tune the GC unless you have profiled a specific memory problem. The defaults are well-chosen for typical mobile apps.

---

## 3. The Dual-GC Architecture (The Real Danger)

An iOS app running KMP has **two garbage collection systems running simultaneously**:

```mermaid
flowchart LR
    subgraph process["iOS app process"]
        swift["Swift / Objective-C<br/>ARC<br/>deterministic, immediate deallocation<br/>cycles can leak"]
        kotlin["Kotlin/Native<br/>tracing mark-and-sweep GC<br/>batched, non-deterministic collection<br/>cycles are collectable"]
        swift <-->|"interop bridge<br/>cross-boundary references can leak"| kotlin
    end
```

### Cross-Boundary Reference Leaks

When Swift holds a reference to a Kotlin object:
- Swift ARC increments its own reference count for the Kotlin object.
- The Kotlin GC sees this as an external root — it will NOT collect the Kotlin object until Swift releases it.

When Kotlin holds a reference to a Swift object:
- Kotlin retains the bridged Swift object through a strong reference, which is released according to GC/ARC interop lifetime.
- Swift ARC thinks the Swift object is still in use and won't deallocate it.

**The Leak Scenario:**
```kotlin
// Kotlin code
class KotlinViewModel {
    // This holds a strong reference to whatever Swift passes in
    var onStateChange: ((String) -> Unit)? = null
    
    fun start() {
        viewModelScope.launch {
            while (true) {
                delay(1000)
                onStateChange?.invoke("tick")
            }
        }
    }
}
```

```swift
// Swift code — THIS LEAKS!
class SwiftViewController: UIViewController {
    let viewModel = KotlinViewModel()
    
    override func viewDidLoad() {
        super.viewDidLoad()
        
        // Passing `self` into Kotlin creates a strong cross-boundary reference
        viewModel.onStateChange = { [self] state in
            self.label.text = state
            // `self` (UIViewController) is captured by the Kotlin closure
            // Kotlin GC holds `self` → ARC thinks VC is still alive
            // VC is never deallocated, even after user navigates away
        }
        viewModel.start()
    }
}
```

**The Fix:**
```swift
// Use [weak self] to prevent the strong cross-boundary reference
viewModel.onStateChange = { [weak self] state in
    self?.label.text = state
}
```

---

## 4. Coroutine Dispatchers on iOS

### Dispatchers.Main (The iOS Main Thread)

On iOS, `Dispatchers.Main` maps to Apple's **Main Dispatch Queue** (GCD). This is the same queue that SwiftUI and UIKit use for UI updates.

```kotlin
// This is safe — updates happen on the iOS main thread
viewModelScope.launch(Dispatchers.Main) {
    _state.value = UiState.Loading  // ✅ Safe for UI observation
    val data = withContext(Dispatchers.IO) {
        api.fetchData()  // Background thread
    }
    _state.value = UiState.Success(data)  // ✅ Back on main thread
}
```

### Dispatchers.IO on iOS

As of `kotlinx-coroutines` 1.7.0, `Dispatchers.IO` is available on Kotlin/Native. It creates a background thread pool.

**Apple dispatchers:** The Darwin Default implementation uses a GCD global queue, not a fixed Kotlin pool sized to CPU count. Blocking/CPU pressure can delay work; starvation is not itself a deadlock. Choose a dispatcher and bound concurrency for the actual workload.

**After 1.7.0:** `Dispatchers.IO` exists on Native with an elastic thread pool (similar to JVM), so I/O-bound operations can scale independently of CPU-bound work.

### Dispatchers.Default Behavior Differences

| Property | JVM (Android) | Native (iOS) |
|---|---|---|
| Default scheduling | JVM scheduler implementation | GCD global queue on Darwin; do not infer a fixed per-task native thread |
| Thread lifetime | Runtime-managed | GCD/runtime-managed on Darwin; no thread creation/destruction guarantee per coroutine |
| Thread creation cost | ~1ms (JVM reuses) | ~5-10ms (OS-level thread creation) |
| Stack size per thread | 512KB-1MB configurable | 512KB (Apple default) |

**Implication:** If your coroutine code rapidly creates and cancels thousands of short-lived tasks on `Dispatchers.Default`, iOS will pay a higher penalty than Android because Native threads are more expensive to create/destroy.

---

## 5. `StateFlow` Observation Across the Bridge

The most common concurrency pattern in KMP is emitting state from a shared ViewModel and observing it in Swift:

```kotlin
// commonMain — The Kotlin side
class ProfileViewModel {
    private val _state = MutableStateFlow(ProfileState())
    val state: StateFlow<ProfileState> = _state.asStateFlow()
    
    fun loadProfile(userId: String) {
        viewModelScope.launch {
            _state.update { it.copy(isLoading = true) }
            
            val result = withContext(Dispatchers.IO) {
                repository.getProfile(userId)
            }
            
            _state.update { it.copy(isLoading = false, profile = result) }
        }
    }
}
```

### Without SKIE (Manual Collection)

A manual bridge must provide a real Kotlin cancellation handle. For example, the following application-owned bridge exposes a typed callback and owns its collection scope:

```kotlin
class ProfileStateBridge(private val state: StateFlow<ProfileState>) {
    fun observe(onState: (ProfileState) -> Unit): StateObservation {
        val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main)
        scope.launch { state.collect { onState(it) } }
        return StateObservation(scope)
    }
}
class StateObservation internal constructor(private val scope: CoroutineScope) {
    fun close() { scope.cancel() }
}
```

The Swift owner retains StateObservation while visible and calls close on disappearance, not only in deinit. Keep UI publication on MainActor and avoid a strong callback cycle (for example with a weak capture). Publishing from a background context violates SwiftUI's contract; it is not a universal guaranteed-crash diagnostic. The exported Swift names depend on the selected export path, so inspect the generated interface instead of assuming a FlowCollector.collect helper exists.

### With Kotlin 2.4 Swift Export

```swift
struct ProfileScreen: View {
    let viewModel = ProfileViewModel()
    @State private var state = ProfileState.companion.initial
    
    var body: some View {
        VStack {
            if state.isLoading {
                ProgressView()
            } else if let profile = state.profile {
                Text(profile.name)
            }
        }
        .task {
            do {
                // Kotlin 2.4 Swift Export exposes StateFlow/Flow
                // as Swift AsyncSequence via asAsyncSequence().
                // .task automatically cancels when the View disappears,
                // which cancels the Kotlin collection job through the bridge.
                for try await newState in viewModel.state.asAsyncSequence() {
                    self.state = newState
                }
            } catch is CancellationError {
                // Normal SwiftUI view-disappearance cancellation.
            } catch {
                // Surface as state or telemetry in production code.
            }
        }
        .onAppear {
            viewModel.loadProfile(userId: "123")
        }
    }
}
```

**What the AsyncSequence bridge does internally:**
1. Exposes the Kotlin `Flow`/`StateFlow` as a Swift `AsyncSequence`.
2. Starts a Kotlin coroutine that calls `Flow.collect`.
3. When Swift's `Task` is cancelled (e.g., View disappears), the bridge cancels the Kotlin collection job.
4. The Kotlin coroutine throws `CancellationException`, which unwinds the coroutine stack and releases references.

For SKIE, the generated Flow wrapper is itself an AsyncSequence: iterate viewModel.state directly. The example above is specifically Swift export's asAsyncSequence API. Select one export path, verify its generated types and cancellation behavior, and keep SwiftUI state publication on MainActor. Swift export remains Alpha in Kotlin 2.4.

```kotlin
suspend fun loadProfileOnMain(): Profile =
    withContext(Dispatchers.Main) {
        repository.loadProfile()
    }
```

---

## Common Pitfalls

### 1. The `GlobalScope` Leak
```kotlin
// BAD — This coroutine NEVER gets cancelled
GlobalScope.launch {
    while (true) {
        delay(1000)
        analytics.track("heartbeat")
    }
}
```
GlobalScope lacks the screen/feature ownership needed on either platform. Android task removal does not universally kill the process, and suspended iOS apps do not execute indefinitely. Cancel owned scopes and release callbacks when the feature ends.

### 2. The Main Thread Deadlock
```kotlin
// DANGEROUS on iOS
runBlocking(Dispatchers.Main) {
    val data = api.fetchData()  // This suspends...
}
// runBlocking BLOCKS the Main thread while waiting for fetchData()
// fetchData() needs to resume on Main thread (to update StateFlow)
// → DEADLOCK: Main thread is blocked, waiting for work that needs Main thread
```

### 3. The `Dispatchers.Main.immediate` Assumption
On Darwin the current implementation compares CFRunLoopGetCurrent with CFRunLoopGetMain. Do not infer a pre-UIApplicationMain failure from a different API; avoid runBlocking(Main) and test the actual initialization path.

---

## Probing Questions

1.  **Legacy Migration:** You inherit a KMP codebase that uses `AtomicReference<MutableList<User>>` to share state between threads. This was written for the old memory model. How do you refactor this for the new memory model?
2.  **Dual-GC Leak:** Draw the reference graph for the `SwiftViewController → KotlinViewModel → closure → SwiftViewController` leak scenario. Which GC system (ARC or K/Native) would need to break the cycle, and why can't it?
3.  **Dispatcher Starvation:** Your KMP app on iOS has 8 concurrent `Dispatchers.Default` coroutines doing CPU-heavy image processing. A 9th coroutine needs to run a 5ms database query. What happens, and how do you fix it?
4.  **StateFlow Collection:** Without SKIE, trace the exact sequence of events when a SwiftUI `View` disappears while a Kotlin `StateFlow` is being collected via a manual `FlowCollector`. What object is leaked if `close()` isn't called?
5.  **GC Tuning:** Your KMP app on iOS shows 15ms GC pauses in Instruments. These pauses cause dropped frames in a scrolling list. What K/Native GC configuration options are available, and what tradeoff does each represent?

## Answer Key

1. Use StateFlow/serialized mutations or an atomic immutable snapshot according to the contract. AtomicReference remains legitimate; atomically replacing a reference does not protect mutations inside the referenced list.
2. Swift retains the Kotlin object, Kotlin retains the closure, and the closure retains Swift. ARC cannot see through Kotlin GC ownership and Kotlin GC cannot release an externally retained Swift object; explicitly break the closure/reference cycle.
3. CPU-bound work can occupy the Default pool and delay the short query. Bound image parallelism, move blocking database calls to an appropriate dispatcher, and prioritize/partition workloads instead of launching unbounded jobs.
4. Manual bridging continues until its collection job is cancelled. If `close()` is omitted, the collector/bridge and captured Swift view model can remain reachable after the view disappears.
5. Kotlin 2.4 uses concurrent mark-and-sweep by default; pmcs is a documented fallback. Measure pauses, throughput and memory on target devices before selecting supported GC/allocator options for the pinned compiler.

## Further Reading

- [`swift-interop.md`](../tooling/swift-interop.md) — How SKIE bridges Kotlin `Job` cancellation to Swift `Task` cancellation.
- [`../../kotlin/coroutines-and-flow/coroutines.md`](../../../kotlin/coroutines-and-flow/coroutines.md) — Deep dive into Job hierarchies, SupervisorJob, and cancellation propagation.
- [`../../kotlin/runtime-and-jvm/memory-model.md`](../../../kotlin/runtime-and-jvm/memory-model.md) — The JVM memory model (compare with the K/Native GC described here).
- [Kotlin/Native memory management](https://kotlinlang.org/docs/native-memory-manager.html) — current collector behavior and supported binary options.
- [Swift/Objective-C ARC integration](https://kotlinlang.org/docs/native-arc-integration.html) — cross-runtime lifecycle and retain-cycle behavior.
- [`testing-and-mocking.md`](testing-and-mocking.md) — How to test concurrent code in `commonTest` across both runtimes.

### Official verification references

- [Primary documentation or owning implementation](https://developer.android.com/guide/components/activities/process-lifecycle)
- [Primary documentation or owning implementation](https://github.com/Kotlin/kotlinx.coroutines/blob/master/kotlinx-coroutines-core/nativeDarwin/src/Dispatchers.kt)
- [Primary documentation or owning implementation](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.native.concurrent/-thread-local/)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/native-migration-guide.html)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/native-objc-interop.html)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/native-swift-export.html)
- [Primary documentation or owning implementation](https://skie.touchlab.co/features/flows)
