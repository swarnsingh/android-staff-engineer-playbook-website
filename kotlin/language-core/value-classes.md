# Value Classes

A value class wraps exactly one value in a new, distinct compile-time type that — in the best case — costs nothing at runtime:

```kotlin
@JvmInline
value class UserId(val raw: String)

@JvmInline
value class Millis(val value: Long) {
    init { require(value >= 0) }          // init blocks are allowed
    val seconds: Long get() = value / 1000 // properties without backing fields
}
```

The compiler inlines the underlying value where it can, so `fun load(id: UserId)` compiles to a method taking a `String` — the type safety exists at compile time and evaporates from the bytecode. This is the language's answer to *primitive obsession*: `load(userId, orderId)` can't be called with the arguments swapped, while `load(String, String)` silently can.

## 1. Value Class vs Type Alias vs Data Class

| | `value class UserId(val raw: String)` | `typealias UserId = String` | `data class UserId(val raw: String)` |
|---|---|---|---|
| New type (rejects raw `String`) | ✅ | ❌ — assignment-compatible both ways | ✅ |
| Runtime allocation | Usually none (see boxing) | None | Always an object |
| Use case | Domain primitives, units, handles | Shortening ugly generic signatures | Multi-field aggregates |

A type alias is documentation only — it provides zero type safety, and using it for domain identifiers gives a false sense of it. And the moment you need **two** fields, a value class is off the table: the single-property-in-primary-constructor rule is enforced by the compiler. `Money(amount, currency)` is a data class, full stop; as of Kotlin 2.x, Kotlin value classes still require exactly one underlying property.

## 2. Boxing: the Rule That Decides Whether You Got the Performance

The doc-level rule is exact: **a value class is boxed whenever it is used as another type.** Inlined as itself; boxed as anything more abstract:

```kotlin
@JvmInline value class Meters(val v: Double)

fun asItself(m: Meters) {}          // inlined: parameter is double
fun asNullable(m: Meters?) {}       // boxed: null needs a reference
fun <T> asGeneric(t: T) {}          // boxed: generic T
fun asAny(a: Any) {}                // boxed: supertype
interface Measure; // value class implementing Measure → boxed at the interface

val list = listOf(Meters(1.0))      // boxed: List<T> is generic
```

Consequences that matter at staff level:

- **Collections box.** `List<UserId>` allocates one wrapper per element. For a hot path holding millions of wrapped longs, that's the same cost as not using primitives — use primitive arrays or rethink the type at the boundary.
- **Equality across representations is safe** (boxing preserves `equals`), but *identity* is not — two boxes of the same value are different references. `===` on value classes is a bug pattern.
- Nullable wrapped types and generic-heavy code erode the benefit silently; the type safety remains, the zero-cost claim doesn't. Profile before assuming.

## 3. Mangling and Java Interop

Because `fun compute(x: UInt)` and `fun compute(x: Int)` would collide in bytecode (both take `int`), functions with value-class parameters get **mangled names** — a hyphen-plus-hash suffix (`compute-<hash>`). Hyphens are invalid in Java identifiers, which makes such functions *deliberately uncallable from Java*. In a mixed Kotlin/Java codebase or a published SDK this is an API-design decision, not a triviality:

```kotlin
@JvmName("computeMillis")           // opts out of mangling — callable from Java
fun compute(x: Millis) { }
```

Public API of libraries with Java consumers should either avoid value classes at the surface or `@JvmName` every entry point — and that choice is permanent per [binary-compatibility rules](../../android/kotlin-multiplatform/binary-compatibility-api-evolution.md), because switching between a value class and a regular class changes signatures and mangling.

The standard library's `UInt`, `ULong`, `Duration` are value classes — which is why they interop awkwardly with Java and why `Duration` in a public Java-facing API is a review flag.

## 4. Where They Earn Their Keep

- **Domain identifiers:** `UserId`, `OrderId`, `SessionToken` — the compile-time firewall against argument transposition, at zero cost in straight-line Kotlin code.
- **Units:** `Millis`, `Meters`, `Cents` — the `init { require(...) }` block gives you a validated construction point, and arithmetic extensions keep call sites readable.
- **Constrained strings:** `EmailAddress`, validated once at the boundary, trusted everywhere after — the type *is* the proof of validation.
- **Compose stability:** a value class is as stable as its underlying type, so wrapping a `String` or `Long` keeps parameters skippable (see [Stability](../../android/compose/stability.md)) while adding meaning.

They support interfaces (with boxing at that seam), delegation, secondary constructors, and member functions — enough to carry real domain behavior, not just naming.

## 5. Review Checklist

- Is the wrapped type actually confused-at-call-sites without it? (If nothing else takes a `String` nearby, the wrapper is ceremony.)
- Does this type cross a Java or serialization boundary? Decide the mangling/`@JvmName` and serializer story *now* — retrofits are binary-incompatible.
- Is it stored in bulk collections on a hot path? Measure the boxing.
- Does it need a second field? Then it was never a value class.

## Further Reading

- [Kotlin docs — Inline value classes](https://kotlinlang.org/docs/inline-classes.html) — boxing rules, mangling, restrictions
- [Data Classes](data-classes.md) — the multi-field alternative
- [Compose Stability](../../android/compose/stability.md) — how wrappers interact with skipping
