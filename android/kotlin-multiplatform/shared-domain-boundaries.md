# Shared Domain Boundaries in KMP

## Overview

The best shared KMP code is boring domain code with explicit platform edges. The worst shared KMP code is a platform abstraction layer that hides Android and iOS differences until production.

Shared domain boundaries define what lives in `commonMain`, what stays platform-specific, and how the two communicate.

## Boundary Rule

`commonMain` should know about:

- Domain concepts.
- Use case orchestration.
- Pure validation.
- Serialization contracts.
- Repository interfaces.
- Time/random/id abstractions.
- Error models.

`commonMain` should not know about:

- Android `Context`.
- iOS `UIViewController`.
- Lifecycle owners.
- Platform permissions.
- Notification channels.
- Keychain/Keystore details.
- WorkManager/BGTaskScheduler details.
- UI navigation controllers.

## Dependency Direction

```text
Android/iOS platform adapters
        ↓
Shared domain interfaces
        ↓
Shared pure domain logic
```

The shared domain defines interfaces. Platforms implement them.

```kotlin
interface SecureTokenStore {
    suspend fun readAccessToken(): String?
    suspend fun writeAccessToken(token: String)
    suspend fun clear()
}

class RefreshSessionUseCase(
    private val tokenStore: SecureTokenStore,
    private val api: SessionApi
) {
    suspend fun refresh(): SessionResult { ... }
}
```

Android implementation uses Keystore/Encrypted storage. iOS implementation uses Keychain. The shared use case does not know either detail.

## Error Boundaries

Shared code should expose domain errors, not platform exceptions.

```kotlin
sealed interface CheckoutError {
    data object Offline : CheckoutError
    data object PaymentDeclined : CheckoutError
    data object CartChanged : CheckoutError
    data class Unknown(val debugMessage: String?) : CheckoutError
}
```

Do not expose:

- `IOException`
- `NSError`
- Retrofit exceptions
- Ktor engine exceptions
- SQL exceptions

Map platform/library failures at the adapter boundary.

## Time, IDs, Randomness

Inject boundary services for nondeterministic inputs.

```kotlin
interface Clock {
    fun now(): Instant
}

interface IdGenerator {
    fun newId(): String
}
```

This makes shared tests deterministic and prevents platform APIs from leaking into domain code.

## Coroutine Boundaries

Shared code can use coroutines, but it should not expose internal scopes.

Good:

```kotlin
class CartUseCase(
    private val repository: CartRepository
) {
    fun observeCart(): Flow<CartState> = repository.observeCart()

    suspend fun addItem(item: CartItem) {
        repository.addItem(item)
    }
}
```

Risky:

```kotlin
class CartUseCase {
    val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
}
```

Scope ownership belongs to the platform or an explicitly documented shared lifecycle owner.

## Platform Escape Hatches

Every shared abstraction needs a way to let platforms be platforms.

Examples:

- Android may use WorkManager; iOS may use BGTaskScheduler.
- Android may use Play Integrity; iOS may use App Attest.
- Android may show notification permission UI differently from iOS.
- Android may support background location differently.

Design with feature capabilities:

```kotlin
data class PlatformCapabilities(
    val supportsBackgroundRefresh: Boolean,
    val supportsStrongDeviceIntegrity: Boolean,
    val maxBackgroundUploadBytes: Long
)
```

Avoid pretending the platforms are the same when they are not.

## Shared State Machines

State machines are often excellent shared candidates.

```kotlin
sealed interface UploadState {
    data object Idle : UploadState
    data class Queued(val count: Int) : UploadState
    data class Uploading(val progress: Float) : UploadState
    data class Failed(val canRetry: Boolean) : UploadState
}
```

Platforms render state differently, but the transition rules can be shared and tested.

## Testing Boundary Contracts

Shared tests should prove:

- Pure domain rules.
- Error mapping.
- Retry/idempotency logic.
- State machine transitions.
- Serialization compatibility.
- Time and ID behavior through fakes.

Platform tests should prove:

- Keystore/Keychain behavior.
- Permission flows.
- Background schedulers.
- Network engine configuration.
- Crash symbolication and logging.
- Swift/Kotlin API ergonomics.

## Staff Engineer Review Checklist

- Does `commonMain` avoid platform UI/lifecycle/security objects?
- Are interfaces defined by domain needs, not platform wrappers?
- Are platform exceptions mapped to domain errors?
- Are time/ID/randomness injected?
- Are coroutine scopes owned explicitly?
- Are platform escape hatches designed?
- Are shared state machines deterministic and tested?
- Is Swift API shape reviewed?
- Are platform adapters thin and replaceable?
- Does shared code reduce duplication without erasing platform truth?

## Further Reading

- [`kmp-decision-matrix.md`](kmp-decision-matrix.md) - what to share.
- [`foundations/architecture-and-module-boundaries.md`](foundations/architecture-and-module-boundaries.md) - module boundaries.
- [`production/concurrency-and-memory.md`](production/concurrency-and-memory.md) - coroutine and memory behavior.
- [`tooling/swift-interop.md`](tooling/swift-interop.md) - Swift API constraints.
