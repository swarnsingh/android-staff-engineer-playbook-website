# Shared Domain Boundaries in KMP

## Overview

The best shared KMP code is boring domain code with explicit platform edges. The worst shared KMP code is a platform abstraction layer that hides Android and iOS differences until production.

Shared domain boundaries define what lives in `commonMain`, what stays platform-specific, and how the two communicate.

## Why It Matters

Boundary quality — not sharing percentage — decides whether KMP pays off or becomes the codebase everyone routes around:

- **A leaked platform type is permanent.** Once `Context` or a lifecycle type appears in a shared API, every consumer on every platform inherits it; unwinding it means breaking the shared API for both apps at once.
- **Bad boundaries surface late.** A shared module compiles happily against a wrong abstraction for months; the cost appears when iOS implements the interface and discovers it encodes Android assumptions (a `suspend fun` that Android calls from a lifecycle scope but iOS has no natural scope for; an error type that only maps cleanly to Retrofit).
- **The boundary is the team contract.** `commonMain` is co-owned by Android and iOS engineers. What's allowed inside it decides whether iOS engineers review shared PRs as peers or treat the shared module as an upstream vendor they file tickets against.

The Staff-level insight: KMP fails socially before it fails technically, and the social failure starts at a boundary that made one platform a second-class citizen.

## Mental Model

Think of `commonMain` as an **embassy on neutral ground**.

- Inside the embassy, only the shared treaty language is spoken: domain concepts, pure logic, declared interfaces.
- Each country (Android, iOS) sends ambassadors (adapter implementations) who translate the treaty into local law (Keystore vs Keychain, WorkManager vs BGTaskScheduler).
- The embassy never issues instructions in one country's local law — the moment a treaty document says "as implemented by Android's WorkManager," the other country can no longer honor it.
- Escape hatches are diplomatic exceptions: declared openly in the treaty (`PlatformCapabilities`), never smuggled.

If you can't explain a shared API to an iOS engineer without saying an Android class name, it isn't treaty language yet.

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

Note what makes `SecureTokenStore` a *good* boundary interface: it is defined by what the **domain needs** (read, write, clear a token), not by wrapping what either platform offers. The anti-pattern is the "platform mirror" interface — `interface KeystoreWrapper` with methods shaped like Android's Keystore API — which forces iOS to emulate Android semantics on top of Keychain. Domain-shaped interfaces stay small; platform-mirror interfaces grow a method per platform quirk.

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

Two reasons this is non-negotiable rather than stylistic:

1. **Swift interop:** Kotlin exceptions do not surface as typed Swift errors — a shared API that "documents" behavior via thrown platform exceptions is undocumented on iOS. Sealed result/error types at least survive the boundary as inspectable types; exception hierarchies don't. See [`tooling/swift-interop.md`](tooling/swift-interop.md).
2. **Exhaustiveness — with a Swift caveat:** a sealed error type gives *Kotlin* callers compile-time exhaustiveness. Swift callers through the default Objective-C export get **no exhaustive `switch`** — a new error case added in Kotlin silently falls through Swift's `else` branch (see [`tooling/swift-interop.md`](tooling/swift-interop.md), "Sealed Classes → No Exhaustive switch"). Closing that gap requires SKIE or generated Swift wrappers; until then, every sealed type change is a *manual* iOS review item, which is still far better than `catch (e: Exception)` — the type carries the cases even when the compiler can't enforce them.

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

The asymmetry that makes this rule matter: Android callers have natural structured-concurrency owners (`viewModelScope`, `lifecycleScope`); iOS callers consuming the API from Swift do not. A shared class that spawns its own scope has decided cancellation policy for a platform whose lifecycle it cannot see — work leaks on iOS are the standard result.

Exposing `suspend fun` and `Flow` keeps cancellation in the hands of whoever owns the lifecycle — **for Kotlin callers**. Swift callers get no such guarantee for free: the default Kotlin/Native async bridge does **not** propagate Swift's `Task.cancel()` into the Kotlin coroutine, and cancelling a `Flow` collection means managing the collected `Job` yourself (see [`tooling/swift-interop.md`](tooling/swift-interop.md), "suspend fun → Broken Cancellation"). In practice the iOS side needs SKIE or a thin hand-written bridge that ties collection jobs to the Swift owner's lifetime. The boundary rule still holds — the shared class must not own scopes — but on iOS, *someone* must, explicitly, in the adapter layer.

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

The capabilities pattern beats `expect/actual` for behavioral differences: `expect/actual` says "both platforms do this, differently"; capabilities say "platforms differ in *whether and how much*" — which is the truth for background execution, integrity attestation, and permission UX. Shared logic branches on declared capability, and the branch is testable in `commonTest` by constructing capability values, no platform required.

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

## Production Example

**The offline outbox that almost forked.**

A team shares their offline sync engine ([`../../mobile-system-design/offline-sync.md`](../../mobile-system-design/offline-sync.md)) via KMP. First design: the shared module owns scheduling — a `SyncScheduler` interface shaped exactly like WorkManager (`enqueueUniqueWork`, constraint objects, backoff policies). Android's adapter is a one-line delegation. The iOS adapter becomes a 700-line emulation of WorkManager semantics on BGTaskScheduler — which iOS cannot actually honor (iOS grants background time opportunistically; there is no guaranteed unique-work queue). iOS ships a subtly broken emulation, sync reliability diverges by platform, and the iOS team proposes forking the sync engine entirely.

The redesign moved the boundary: shared code owns *what to sync* (outbox state machine, batching, retry/idempotency rules — all pure and testable), and each platform owns *when to run* (WorkManager on Android, BGTaskScheduler + foreground opportunities on iOS), reporting back through a two-method interface (`requestSyncSoon()`, `onSyncWindow(budget)`). Shared line count went *down*; shared correctness and iOS trust went up. The lesson: **share the decision logic, never the platform's job.**

## Tradeoffs

- **Sharing more vs owing more:** every type in `commonMain` is API surface owed to two platforms, reviewable by two teams, constrained by Swift interop. Share the pieces with real duplicated logic (validation, sync rules, state machines) — not everything that *could* compile in common.
- **Domain interfaces vs adapter count:** domain-shaped interfaces mean each platform writes a real adapter (more platform code) instead of one-line delegations to a mirrored API (less platform code, wrong abstraction). Pay the adapter tax; it's the price of both platforms being first-class.
- **Capabilities vs least-common-denominator:** designing to the intersection of platform abilities makes the shared module simple and both apps worse. Capabilities keep the shared module honest about differences at the cost of branching logic — branching that would otherwise live, undocumented, in each app.

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

## Probing Questions

1.  How do you tell a domain-shaped interface from a platform-mirror interface in review? Give the smell for each.
2.  Why must shared code expose sealed domain errors instead of exceptions — what specifically breaks on the Swift side if it doesn't?
3.  A shared class creates its own `CoroutineScope`. Whose lifecycle is it implicitly claiming to know, and what goes wrong on iOS?
4.  Background sync must be shared across Android and iOS. Which parts do you put in `commonMain`, which stay platform-side, and where exactly is the interface between them?
5.  When do you reach for `PlatformCapabilities` instead of `expect/actual`, and how do you test capability-dependent logic without a device?
6.  An iOS engineer says the shared module "feels like an Android library we're forced to use." What boundary defects would you audit for first?

## Further Reading

- [`kmp-decision-matrix.md`](kmp-decision-matrix.md) - what to share.
- [`foundations/architecture-and-module-boundaries.md`](foundations/architecture-and-module-boundaries.md) - module boundaries.
- [`production/concurrency-and-memory.md`](production/concurrency-and-memory.md) - coroutine and memory behavior.
- [`tooling/swift-interop.md`](tooling/swift-interop.md) - Swift API constraints.
- [`../../mobile-system-design/offline-sync.md`](../../mobile-system-design/offline-sync.md) - the sync engine boundary example in full.
