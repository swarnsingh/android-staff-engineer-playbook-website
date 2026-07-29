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

Two reasons this is usually safer than exposing library exceptions:

1. **Swift interop:** on the default Objective-C export path, only exceptions listed by `@Throws` are converted to `NSError` for non-suspending functions; unexpected Kotlin exceptions terminate the program. A domain result makes expected failures explicit in the API instead of relying on a platform exception hierarchy.
2. **Exhaustiveness — with an export-path caveat:** a sealed error type gives Kotlin callers compile-time exhaustiveness. Swift callers through Objective-C export receive class-like representations and still need a fallback case. Kotlin 2.4's Alpha Swift export improves Swift-native mappings, but it is incomplete and should not be treated as a stable production contract. Review generated APIs and every added error case on iOS.

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

The asymmetry that makes this rule matter: Android callers have natural structured-concurrency owners (`viewModelScope`, `lifecycleScope`); a SwiftUI integration must deliberately connect shared work to a Swift owner. A shared class that silently spawns its own scope has chosen cancellation policy without seeing either platform lifecycle, which makes leaks and stale work more likely.

Exposing `suspend fun` and `Flow` lets Kotlin callers preserve structured ownership. Swift behavior depends on the export path:

- The default Objective-C export path exposes suspending functions through completion handlers (and an experimental Swift `async` import); `Flow` observation is not directly integrated with SwiftUI. A maintained adapter or a library such as SKIE/KMP-NativeCoroutines must connect jobs to the Swift owner's lifetime.
- Kotlin 2.4's Alpha Swift export maps suspending functions to `async` and flows to `AsyncSequence` with built-in concurrency support. Because the feature is Alpha, validate cancellation and generated API behavior with the exact Kotlin version before adopting it.

In both cases, lifecycle ownership must be explicit and tested rather than hidden inside a use case.

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

A team shares its offline sync engine ([`../../mobile-system-design/offline-sync.md`](../../mobile-system-design/offline-sync.md)) via KMP. First design: the shared module owns scheduling through a `SyncScheduler` interface shaped like WorkManager (`enqueueUniqueWork`, constraint objects, backoff policies). Android's adapter is nearly direct; the iOS adapter must emulate semantics that BGTaskScheduler does not promise because the system decides when background launch occurs. Reliability diverges by platform, and the iOS team proposes forking the sync engine.

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
2.  Why should shared code usually expose domain failures instead of library exceptions, and how do Objective-C export and Alpha Swift export change the Swift-side tradeoffs?
3.  A shared class creates its own `CoroutineScope`. Whose lifecycle is it implicitly claiming to know, and what goes wrong on iOS?
4.  Background sync must be shared across Android and iOS. Which parts do you put in `commonMain`, which stay platform-side, and where exactly is the interface between them?
5.  When do you reach for `PlatformCapabilities` instead of `expect/actual`, and how do you test capability-dependent logic without a device?
6.  An iOS engineer says the shared module "feels like an Android library we're forced to use." What boundary defects would you audit for first?

## Answer Key

1. A domain-shaped interface is named in the consumer's language and contains only operations the domain needs, such as `SecureTokenStore.readAccessToken()`. A platform mirror repeats one SDK's nouns, overloads, configuration objects, or lifecycle assumptions, such as `KeystoreWrapper.enqueueUniqueWork(...)`; the other platform must emulate foreign semantics. Review callers first, then make the smallest contract that satisfies them.
2. Map expected failures to domain values so callers get a documented, testable contract independent of Retrofit, Ktor, `NSError`, or a database driver. With Objective-C export, only `@Throws`-listed exceptions become `NSError` for non-suspending functions, unexpected exceptions can terminate the process, and sealed types are not exhaustively switchable in Swift. Alpha Swift export offers more Swift-native mappings but remains incomplete and version-sensitive. Keep unexpected programmer failures exceptional; do not convert every throwable into a business result.
3. It is implicitly claiming to know the lifetime of every Android and iOS consumer. A private long-lived scope can outlive a SwiftUI screen, retain objects, deliver stale state, or keep work running after navigation. Return suspending operations/flows or use an explicitly owned shared component; connect its cancellation to Android lifecycle/ViewModel ownership and to a deliberate Swift owner, then test disposal on both platforms.
4. Share outbox state, serialization, deduplication/idempotency, batching, retry decisions, and the operation that performs one bounded sync window. Keep WorkManager constraints/unique-work semantics on Android and BGTaskScheduler/foreground opportunities on iOS. A small domain-shaped port such as `requestSyncSoon()` plus a platform call into `runSyncWindow(budget)` crosses the boundary without pretending the schedulers are equivalent.
5. Use capabilities when availability or limits differ at runtime—background refresh, device integrity, or upload budgets—and shared policy genuinely needs to branch on them. Use `expect`/`actual` when each compiled target must supply a declaration with the same semantic contract. Test capability-dependent logic in `commonTest` by passing representative capability values, including unsupported and constrained cases.
6. Audit exported APIs for Android types/names, lifecycle and dispatcher assumptions, platform-mirror interfaces, leaked vendor exceptions, WorkManager-like scheduling contracts, forced Android UX/navigation, and APIs that generate poor Swift signatures. Then inspect ownership: whether iOS reviews shared API changes, has platform escape hatches, can test adapters independently, and can evolve its UI without waiting for Android-shaped abstractions.

## Further Reading

- [`kmp-decision-matrix.md`](kmp-decision-matrix.md) - what to share.
- [`foundations/architecture-and-module-boundaries.md`](foundations/architecture-and-module-boundaries.md) - module boundaries.
- [`production/concurrency-and-memory.md`](production/concurrency-and-memory.md) - coroutine and memory behavior.
- [`tooling/swift-interop.md`](tooling/swift-interop.md) - Swift API constraints.
- [`../../mobile-system-design/offline-sync.md`](../../mobile-system-design/offline-sync.md) - the sync engine boundary example in full.
- [Kotlin Multiplatform API guidelines](https://kotlinlang.org/docs/api-guidelines-build-for-multiplatform.html) - official guidance for common APIs and platform-specific behavior.
- [Swift/Objective-C interoperability](https://kotlinlang.org/docs/native-objc-interop.html) - stable export mappings and limitations.
- [Swift export](https://kotlinlang.org/docs/native-swift-export.html) - current Alpha Swift-native export behavior.
