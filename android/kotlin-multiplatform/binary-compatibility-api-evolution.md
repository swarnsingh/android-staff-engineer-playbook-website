# Binary Compatibility and API Evolution

## Overview

KMP shared modules become platform libraries. Once Android and iOS teams compile against them, changing public APIs can break source compatibility, binary compatibility, behavioral compatibility, or Swift interop.

A Staff engineer treats shared APIs like product contracts.

## Compatibility Types

| Compatibility | Meaning | Example break |
|---|---|---|
| Source | Existing source code still compiles | Removing a function parameter default or renaming a type |
| Binary | Previously compiled clients still run with new library | Changing JVM method signature or return type |
| Behavioral | Same inputs keep same semantics | Changing retry behavior or error mapping |
| Swift API | Swift call sites remain ergonomic and stable | Changing generated names, nullability, or exported type shape |
| Serialization | Stored/network payloads remain readable | Renaming enum values without migration |

Source-compatible changes can still break binary compatibility.

## Public API Rules

For shared modules:

- Enable explicit API mode for published modules.
- Specify public return types explicitly.
- Keep public DTOs small and stable.
- Avoid leaking library-specific exceptions.
- Avoid exposing mutable collections.
- Avoid public `data class` for long-lived binary APIs unless you accept constructor/copy compatibility costs.
- Prefer factory functions or builders for evolvable models.
- Keep experimental APIs behind opt-in annotations.

```kotlin
public class CheckoutResult private constructor(
    public val receiptId: String,
    public val total: Money
) {
    public companion object {
        public fun success(receiptId: String, total: Money): CheckoutResult =
            CheckoutResult(receiptId, total)
    }
}
```

This is more verbose than a data class, but easier to evolve.

## Default Arguments Are Not Free

Adding a parameter with a default value can still break binary compatibility for already compiled Kotlin/JVM clients.

Risky:

```kotlin
fun fetchUser(id: String): User

// Later
fun fetchUser(id: String, forceRefresh: Boolean = false): User
```

Safer:

```kotlin
fun fetchUser(id: String): User
fun fetchUser(id: String, forceRefresh: Boolean): User
```

For JVM APIs, `@JvmOverloads` helps Java callers but does not automatically preserve Kotlin binary compatibility for existing compiled Kotlin callers.

## Data Class API Trap

Data classes generate:

- Constructor.
- `copy`.
- `componentN`.
- `equals/hashCode`.

Adding or reordering properties can break binary or behavioral compatibility.

For internal models, data classes are great. For published shared APIs consumed by multiple apps or platforms, use them deliberately.

## Sealed Hierarchy Evolution

Adding a new sealed subtype can break exhaustive `when` handling at source level and can surprise Swift wrappers.

Policy:

- Add new cases in minor versions only when consumers are prepared.
- Provide an `Unknown` or `Other` case for server-driven states when appropriate.
- Document whether callers must handle future cases.
- Add Swift examples for exhaustive handling.

```kotlin
sealed interface PaymentStatus {
    data object Pending : PaymentStatus
    data object Complete : PaymentStatus
    data class Failed(val reason: FailureReason) : PaymentStatus
    data class Unknown(val raw: String) : PaymentStatus
}
```

## Binary Compatibility Validation

Kotlin provides binary compatibility validation support through tooling that dumps public API and compares changes in CI.

Workflow:

1. Enable explicit API mode.
2. Generate API dump.
3. Commit API files.
4. Run API check in CI.
5. Review API diff like a schema migration.
6. Update API dump only after approving the compatibility impact.

CI should block accidental public API changes.

## KLib and Multiplatform Nuance

Multiplatform libraries produce metadata and native artifacts. Compatibility is not only JVM bytecode.

Review:

- Common metadata API.
- JVM binary API.
- Native/Swift exported API.
- Serialization schema.
- Gradle module coordinates.
- Source set visibility.

Swift export is Alpha in Kotlin 2.4, so generated Swift API shape may still change. Treat exported Swift APIs as reviewed artifacts, not incidental build output.

## Deprecation Cycle

Use a staged deprecation policy:

```kotlin
@Deprecated(
    message = "Use submitOrder(request) so idempotency is explicit.",
    replaceWith = ReplaceWith("submitOrder(OrderRequest.from(order))"),
    level = DeprecationLevel.WARNING
)
fun submitOrder(order: Order): Receipt
```

Typical cycle:

1. Add replacement.
2. Deprecate old API as warning.
3. Migrate internal consumers.
4. Raise to error in a later release.
5. Hide/remove only at a major version or agreed breaking window.

## Behavioral Compatibility

API checks do not catch behavior changes.

Examples:

- Retry count changes from 1 to 5.
- Error `Offline` becomes `Unknown`.
- Flow stops replaying latest value.
- Cache freshness window changes.
- Serialization default changes.
- Clock/timezone interpretation changes.

Protect behavior with contract tests.

```kotlin
@Test
fun timeoutMapsToExpectedFailure() {
    val failure = mapper.map(SocketTimeoutException())
    assertEquals(NetworkFailure.Timeout, failure)
}
```

## Versioning and Release Notes

Every shared module release should state:

- Added APIs.
- Deprecated APIs.
- Removed APIs.
- Behavioral changes.
- Serialization/schema changes.
- Minimum Kotlin/AGP/Xcode versions.
- Migration steps.
- Rollback notes.

For internal shared modules, this can be a changelog entry in the repo. The point is not ceremony; it is helping platform teams upgrade safely.

## Staff Engineer Review Checklist

- Is explicit API mode enabled for shared/public modules?
- Are public return types explicit?
- Are binary compatibility checks in CI?
- Are Swift exported APIs reviewed?
- Are data classes avoided or accepted deliberately at boundaries?
- Are default-argument API changes handled with overloads?
- Are sealed hierarchy additions documented?
- Are serialization changes versioned and tested?
- Is deprecation staged across releases?
- Do contract tests protect behavior, not only signatures?

## Further Reading

- [Kotlin: Backward compatibility guidelines](https://kotlinlang.org/docs/api-guidelines-backward-compatibility.html)
- [Kotlin Swift export documentation](https://kotlinlang.org/docs/native-swift-export.html)
- [`kmp-decision-matrix.md`](kmp-decision-matrix.md) - selecting shared module scope.
- [`shared-domain-boundaries.md`](shared-domain-boundaries.md) - API boundary ownership.
- [`tooling/swift-interop.md`](tooling/swift-interop.md) - generated Swift API constraints.
