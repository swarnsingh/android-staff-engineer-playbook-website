# Swift Interop, SKIE, and Swift Export

> The #1 reason iOS teams reject KMP is not the shared logic — it's the *API surface*. When a Kotlin `sealed class` becomes an un-exhaustive Objective-C class hierarchy, when a `StateFlow` becomes an opaque generic that SwiftUI can't observe, when default arguments vanish — the iOS engineer rightfully declares the API unusable. A Staff engineer must understand every translation failure in the Objective-C bridge and know how to fix each one, either with SKIE or architectural wrappers.

---

## Overview

Kotlin/Native does not compile to Swift. It compiles to native machine code and exposes the public API surface via an **Objective-C header** (`.h`). Swift then imports this header through the standard Objective-C-to-Swift bridge that Apple provides.

This architecture means every Kotlin type must first be representable in Objective-C, and then Objective-C must be representable in Swift. Any Kotlin feature that has no Objective-C equivalent is **lost in translation**.

```text
Kotlin Source → Kotlin/Native Compiler → ARM64 machine code
                                       → Objective-C header (.h)
                                                ↓
Swift sees the Objective-C header → Swift bridge → usable in SwiftUI
```

---

## The Translation Failures (Comprehensive)

### 1. Sealed Classes → No Exhaustive `switch`

**In Kotlin:**
```kotlin
sealed class NetworkResult {
    data class Success(val data: String) : NetworkResult()
    data class Error(val code: Int, val message: String) : NetworkResult()
    data object Loading : NetworkResult()
}
```

**What Objective-C generates:**
```objc
__attribute__((objc_subclassing_restricted))
@interface SharedCodeNetworkResultSuccess : SharedCodeNetworkResult
@property (readonly) NSString *data;
@end

__attribute__((objc_subclassing_restricted))
@interface SharedCodeNetworkResultError : SharedCodeNetworkResult
@property (readonly) int32_t code;
@property (readonly) NSString *message;
@end

// Loading is just a property on the companion object — not a real subclass
```

**What Swift sees:**
```swift
func handle(result: NetworkResult) {
    // NO exhaustive switch! Swift doesn't know this is sealed.
    // Must use `if let` chains or add a `default:` case.
    if let success = result as? NetworkResultSuccess {
        print(success.data)
    } else if let error = result as? NetworkResultError {
        print(error.message)
    } else {
        // What is this? Loading? Something else?
        // Swift has NO compiler guarantee that you've handled all cases.
    }
}
```

**The real danger:** If a Kotlin engineer adds a new `data class Timeout : NetworkResult()`, the Swift code silently falls through to the `else` branch. No compiler warning. Silent bug in production.

### 2. `suspend fun` → Broken Cancellation

**In Kotlin:**
```kotlin
class UserRepository {
    suspend fun fetchUser(id: String): User {
        return httpClient.get("users/$id").body()
    }
}
```

**What Swift sees:**
```swift
// Swift correctly translates this to async/throws
func fetchUser(id: String) async throws -> User
```

This looks perfect, but there's a critical bug: **cancellation doesn't propagate**.

```swift
// Swift code
let task = Task {
    let user = try await repository.fetchUser(id: "123")
    updateUI(user)
}

// Later, user navigates away:
task.cancel()

// PROBLEM: The Swift Task is cancelled, but the Kotlin coroutine
// inside fetchUser() continues running! The network request is
// NOT cancelled. The response is fetched, deserialized, and then
// discarded. Battery and bandwidth wasted.
```

**Why:** Swift's `Task.cancel()` sets a cancellation flag on the Swift `Task`. But the Kotlin coroutine is managed by a separate `Job` hierarchy. The Objective-C bridge does not wire Swift's cancellation flag to Kotlin's `Job.cancel()`. They are two independent cancellation systems.

### 3. `StateFlow` → Opaque Generic (No SwiftUI Observation)

**In Kotlin:**
```kotlin
class CheckoutViewModel {
    private val _state = MutableStateFlow(CheckoutState())
    val state: StateFlow<CheckoutState> = _state.asStateFlow()
}
```

**What Swift sees:**
```swift
// state is of type Kotlinx_coroutines_coreStateFlow
// This is a generic Objective-C class. SwiftUI cannot observe it.

// This DOES NOT WORK:
struct CheckoutScreen: View {
    @StateObject var viewModel = CheckoutViewModel()  // ❌ Not ObservableObject
    
    var body: some View {
        Text(viewModel.state.value.totalPrice)  // ❌ value is untyped KotlinBase
    }
}
```

**The manual wrapper (without SKIE):**
To make this work, the iOS engineer must write a bridging class for every single ViewModel:

```swift
@MainActor
class CheckoutViewModelWrapper: ObservableObject {
    private let kotlinVM = CheckoutViewModel()
    @Published var state = CheckoutState.companion.initial
    private var job: Kotlinx_coroutines_coreJob? = nil
    
    init() {
        // Manually subscribe to the StateFlow using Kotlin's collect
        job = FlowUtilsKt.collect(kotlinVM.state) { [weak self] newState in
            guard let self = self, let state = newState as? CheckoutState else { return }
            DispatchQueue.main.async {
                self.state = state
            }
        }
    }
    
    deinit {
        job?.cancel(cause: nil)  // If you forget this → memory leak!
    }
}
```

This is 25 lines of fragile boilerplate for **every single ViewModel**. In a large app with 30 ViewModels, this becomes 750 lines of pure bridge code. iOS engineers rightfully hate this.

### 4. Default Arguments → Vanished

**In Kotlin:**
```kotlin
fun search(
    query: String,
    limit: Int = 20,
    offset: Int = 0,
    includeInactive: Boolean = false
)
```

**What Swift sees:**
```swift
// ALL parameters are required — no defaults!
func search(query: String, limit: Int32, offset: Int32, includeInactive: Bool)

// iOS engineer must write:
repository.search(query: "shoes", limit: 20, offset: 0, includeInactive: false)
// Instead of the ergonomic:
repository.search(query: "shoes")  // ❌ ERROR: Missing arguments
```

### 5. Kotlin Generics → Type Erasure

**In Kotlin:**
```kotlin
class DataResult<T>(val data: T, val metadata: Map<String, Any>)
```

**What Swift sees:**
```swift
// T is erased to Any (KotlinBase in Objective-C)
class DataResult : KotlinBase {
    var data: Any { get }  // Not T! Just Any.
    // iOS engineer must cast: let user = result.data as! User
}
```

### 6. Kotlin `object` → Singleton with `.shared`

**In Kotlin:**
```kotlin
object Analytics {
    fun track(event: String) { /* ... */ }
}
```

**What Swift sees:**
```swift
// Access via .shared (Objective-C singleton pattern)
Analytics.shared.track(event: "checkout_started")
// NOT Analytics.track(event:) — the .shared is mandatory
```

---

## SKIE (Swift Kotlin Interface Enhancer)

**SKIE** (by Touchlab) is a Kotlin compiler plugin that intercepts the framework generation process. Instead of only producing an Objective-C header, SKIE **also generates native Swift wrapper code** that fixes every translation failure above.

### Setup

```kotlin
// shared/build.gradle.kts
plugins {
    id("co.touchlab.skie") version "0.9.0"
}

skie {
    features {
        // Enable all fixes
        enableSwiftUIObservingPreview = true
    }
}
```

### What SKIE Fixes (With Before/After Code)

#### Fix 1: Exhaustive Sealed Classes

SKIE generates a native Swift enum that mirrors the Kotlin sealed class:

```swift
// WITH SKIE — Exhaustive switch!
switch onEnum(of: result) {
case .success(let success):
    print(success.data)
case .error(let error):
    print(error.message)
case .loading:
    print("Loading...")
}
// If Kotlin adds a new subclass → Swift compiler error! ✅
```

#### Fix 2: Coroutine Cancellation Propagation

SKIE bridges Swift `Task` cancellation to Kotlin `Job` cancellation:

```swift
// WITH SKIE
let task = Task {
    let user = try await repository.fetchUser(id: "123")
    updateUI(user)
}

task.cancel()
// ✅ The Kotlin coroutine's Job is ALSO cancelled.
// ✅ The network request is aborted.
// ✅ No wasted battery or bandwidth.
```

#### Fix 3: StateFlow → AsyncSequence

SKIE converts `StateFlow` to Swift's native `AsyncSequence`, which SwiftUI can observe directly:

```swift
// WITH SKIE — No wrapper class needed!
struct CheckoutScreen: View {
    let viewModel = CheckoutViewModel()
    @State private var state = CheckoutState.companion.initial
    
    var body: some View {
        VStack {
            Text(state.totalPrice.description)
        }
        .task {
            // StateFlow is now an AsyncSequence!
            for await newState in viewModel.state {
                self.state = newState
            }
            // When the View disappears, .task cancels automatically,
            // which cancels the Kotlin Job. Zero leaks.
        }
    }
}
```

#### Fix 4: Default Arguments Restored

```swift
// WITH SKIE
repository.search(query: "shoes")  // ✅ limit=20, offset=0, includeInactive=false
repository.search(query: "shoes", limit: 50)  // ✅ offset=0, includeInactive=false
```

### SKIE Under the Hood

SKIE operates at the **Kotlin compiler backend** level:

```text
Kotlin Source
    ↓
[K2 Frontend (FIR)]
    ↓
[Kotlin/Native Backend]
    ↓
[SKIE Plugin intercepts here]
    ├── Generates standard .h header (for compatibility)
    └── ALSO generates .swift files:
         ├── Sealed class → Swift enum wrapper
         ├── StateFlow → AsyncSequence adapter
         ├── suspend fun → proper async cancellation bridge
         └── Default args → overloaded Swift functions
    ↓
[Final .xcframework contains both .h AND .swift]
```

The generated Swift files are compiled directly into the framework binary. The iOS engineer doesn't see them — they just see a clean, idiomatic Swift API.

### SKIE Performance Considerations

SKIE adds to the framework compilation time:
- **Small project (20 public Kotlin classes):** +2-3 seconds
- **Large project (200+ public Kotlin classes):** +10-15 seconds
- **Binary size impact:** +50-200 KB per sealed class wrapper

For CI pipelines, this is negligible. For local development with Direct Xcode Integration, it's noticeable but acceptable.

---

## Swift Export in Kotlin 2.4

Kotlin 2.4 promotes Swift export to **Alpha**. Instead of exposing Kotlin only through Objective-C headers, the compiler can generate Swift-facing modules so Swift code can call Kotlin APIs more idiomatically.

This changes the recommendation. Swift export is no longer just future theory, and Flow interop is no longer only available through third-party adapters. However, Alpha still means incomplete behavior and possible breaking changes, so production teams need a deliberate migration plan.

### Architecture Comparison

```text
Objective-C bridge:
  Kotlin → Obj-C Header → Swift Bridge → Swift Code

Swift export:
  Kotlin → Swift Module (.swiftmodule) → Swift Code

What's eliminated:
  - Obj-C header generation
  - Swift-to-Obj-C bridge overhead
  - Many Objective-C bridge limitations around naming, nullability, async APIs, and Flow interop
```

### What Swift Export Enables

| Feature | Objective-C bridge | Kotlin 2.4 Swift export |
|---|---|---|
| Module shape | One framework with Objective-C naming artifacts | Swift modules with module naming and package preservation options |
| Nullability | Boxed primitives for nullable values | Better Swift nullability for primitives |
| Overloads | Often awkward or renamed | Supported more directly |
| `suspend fun` | Completion-handler style bridge | Swift `async` counterpart |
| `Flow<T>` | Opaque without wrappers/adapters | Exported as Swift `AsyncSequence` via `asAsyncSequence()` |
| Type aliases | Usually erased through bridge | Preserved in Swift |
| Generic types | Often erased or awkward | Still limited; generic type parameters are generally type-erased to upper bounds |
| Swift inheritance | Not a natural fit | Cross-language inheritance is still unsupported |

### Flow Export to `AsyncSequence`

Kotlin 2.4 can export public APIs that use `kotlinx.coroutines.flow.Flow` while preserving the element type.

```kotlin
// Kotlin
fun observeMessages(): Flow<Message> = repository.observeMessages()
```

```swift
// Swift
Task {
    do {
        for try await message in shared.observeMessages().asAsyncSequence() {
            self.messages.append(message)
        }
    } catch is CancellationError {
        // Normal task cancellation.
    } catch {
        // Surface as state or telemetry.
    }
}
```

Important operational details:

- Flow export is enabled by default for Swift export.
- Swift sees the stream as `AsyncSequence`, which fits Swift structured concurrency.
- By default, exported suspend functions and `asAsyncSequence()` run Kotlin code on `Dispatchers.Default`.
- If Main confinement is required, switch dispatcher in Kotlin with `withContext(Dispatchers.Main)`.
- Swift task cancellation must still cancel the collection; the interop layer does not make event delivery durable.

### Staff Recommendation

Use a two-track strategy:

1. Keep SKIE or explicit wrappers for production modules where you already depend on stable generated Swift APIs.
2. Evaluate Kotlin 2.4 Swift export in a sample or non-critical module, especially for shared Flow APIs and suspend functions.
3. Design public KMP APIs as if Swift engineers are first-class consumers: stable names, simple DTOs, explicit errors, no leaked internal coroutine types.
4. Do not expose important one-off UI events as `SharedFlow` just because Swift can now collect Flow. The StateFlow/SharedFlow delivery semantics are unchanged across the bridge.

---

## Common Pitfalls

### 1. SKIE Version Conflicts
SKIE must match your Kotlin version exactly. If you upgrade Kotlin from 2.0.10 to 2.0.20 without upgrading SKIE, the build will fail with cryptic compiler plugin errors. Always check the SKIE compatibility matrix before upgrading Kotlin.

### 2. The `@HiddenFromObjC` Escape Hatch
If you have internal implementation details that shouldn't appear in the Objective-C header (and thus shouldn't be visible to Swift), annotate them:

```kotlin
@HiddenFromObjC
internal class InternalCache { /* ... */ }
```

### 3. The `KotlinInt` vs Swift `Int` Trap
Kotlin `Int` maps to Objective-C `int32_t`, which becomes Swift `Int32` — NOT Swift `Int` (which is `Int64` on 64-bit platforms). This causes subtle type mismatch errors in Swift:

```swift
let count: Int = viewModel.itemCount  // ❌ ERROR: Cannot convert Int32 to Int
let count: Int = Int(viewModel.itemCount)  // ✅ Must explicitly widen
```

### 4. The `suspend` + `@Throws` Requirement
If a `suspend fun` throws a checked exception in Kotlin, you must annotate it with `@Throws` for the error to be visible in Swift:

```kotlin
@Throws(NetworkException::class, CancellationException::class)
suspend fun fetchUser(id: String): User
```

Without `@Throws`, Swift's `try` won't catch the exception — it will crash the app.

---

## Probing Questions

1.  **Cancellation Mechanics:** Trace the exact execution path when a Swift `Task` is cancelled while a Kotlin `suspend fun` is in progress. Without SKIE, what happens to the Kotlin `Job`? With SKIE, what C-interop mechanism does SKIE use to bridge the two cancellation systems?
2.  **Sealed Class Safety:** Your Kotlin `sealed class PaymentResult` has 3 subclasses. Without SKIE, the iOS team uses a `switch` with a `default:` case. A Kotlin engineer adds a 4th subclass. What happens on the iOS side? With SKIE, what happens?
3.  **StateFlow Collection Lifecycle:** Using SKIE or Kotlin 2.4 Swift export's `AsyncSequence` bridge, explain exactly what happens to the Kotlin `StateFlow` collector when a SwiftUI `View` disappears. Who cancels the collector? What mechanism prevents a memory leak of the ViewModel?
4.  **Type Mapping:** A Kotlin function returns `Map<String, List<Pair<Int, Boolean>>>`. What does the Objective-C header look like? What does Swift see? Why is this a sign of poor API design for the KMP boundary?
5.  **Swift Export vs SKIE:** In Kotlin 2.4, which problems does Swift export solve directly, which limitations still remain, and where would you keep SKIE or explicit wrappers for production stability?

## Further Reading

- [`ios-distribution.md`](ios-distribution.md) — How the SKIE-enhanced framework is packaged into an `.xcframework`.
- [`concurrency-and-memory.md`](../production/concurrency-and-memory.md) — The K/Native memory model and how it interacts with Swift ARC during StateFlow collection.
- [`overview-and-k1-vs-k2.md`](../foundations/overview-and-k1-vs-k2.md) — How K2's architecture enables Swift export.
- [`architecture-and-module-boundaries.md`](../foundations/architecture-and-module-boundaries.md) — Designing the KMP API surface to be "Swift-friendly" from the start.
