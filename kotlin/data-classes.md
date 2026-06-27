# Data Classes

## Overview

A `data class` is a specialized Kotlin class designed solely to hold state (data). By adding the `data` modifier, the Kotlin compiler automatically generates the tedious boilerplate code that Java developers historically had to write by hand: `equals()`, `hashCode()`, `toString()`, `copy()`, and `componentN()` functions.

They are the fundamental building blocks of Unidirectional Data Flow (UDF) architectures and immutable state management in modern Android.

## Why It Matters

In Java, if you wanted a class to hold a `User` with an `id` and a `name`, you had to write ~50 lines of code. If you forgot to override `equals()` and `hashCode()`, and you put that `User` into a `HashSet`, your app would silently behave incorrectly because the default `equals()` compares memory addresses, not the actual data.

Kotlin `data classes` reduce this 50-line liability to a single line: `data class User(val id: String, val name: String)`. This guarantees mathematical correctness when comparing objects, which is an absolute requirement for UI frameworks like Jetpack Compose to function efficiently.

## Historical Context

Java was criticized for decades for its "Plain Old Java Object" (POJO) boilerplate. To fix this, developers used massive IDE generation tools (AutoValue) or controversial bytecode manipulation libraries (Lombok). Kotlin made data-holding classes a first-class language feature. (Java eventually copied this feature with Java 14 `Records`).

## First Principles

1.  **State over Behavior:** A `data class` is meant to carry data. If it has 5 properties and 10 complex business logic methods, it probably shouldn't be a data class.
2.  **Immutability:** While you *can* use `var` in a data class, you absolutely shouldn't. Data classes should use `val` exclusively to enforce [Immutability](../engineering-fundamentals/immutability.md).
3.  **Primary Constructor Only:** The compiler only uses properties declared in the *primary constructor* when generating `equals()`, `hashCode()`, and `toString()`.

## Mental Model

Think of a standard Java class as a custom-built vault. You can put things in it, but you have to write all the rules for how the vault opens, how it identifies itself, and how it prints its inventory.
Think of a Kotlin `data class` as a standardized shipping container. The compiler gives you the container, stamps a barcode on the side (`hashCode()`), prints the shipping manifest (`toString()`), and ensures that any two containers holding the exact same cargo are considered identical (`equals()`).

## Internal Mechanics

When you compile a `data class`, `kotlinc` generates several synthetic methods under the hood.

### 1. `equals()` and `hashCode()`

```kotlin
data class User(val name: String, val age: Int)

val u1 = User("Alice", 30)
val u2 = User("Alice", 30)

println(u1 == u2) // TRUE. In a normal class, this would be FALSE.
```
*Under the hood:* The compiler generates an `equals()` method that compares `u1.name == u2.name && u1.age == u2.age`. It generates a mathematically sound `hashCode()` combining both fields, allowing safe use in `HashMap` and `HashSet`.

### 2. `copy()`

Because data classes should be immutable (`val`), you need a way to change them. The `copy()` method creates a brand new instance with the exact same data, allowing you to selectively overwrite specific fields.

```kotlin
val nextYearUser = u1.copy(age = 31) // name is copied, age is overwritten.
```

### 3. Destructuring (`componentN()`)

The compiler generates `component1()`, `component2()`, etc., corresponding to the order of properties in the constructor. This allows destructuring declarations:

```kotlin
val (name, age) = u1
// Equivalent to:
// val name = u1.component1()
// val age = u1.component2()
```

## Architecture

```mermaid
graph TD
    subgraph The Compiler Magic
        DC[data class User(val id, val name)]
        
        DC -->|Generates| Eq[equals: Compares id and name]
        DC -->|Generates| Hash[hashCode: Hashes id and name]
        DC -->|Generates| TS[toString: User(id=.., name=..)]
        DC -->|Generates| Copy[copy: Creates new instance]
        DC -->|Generates| Comp[component1, component2]
    end
```

## Production Example

**Jetpack Compose Recomposition**

Compose relies entirely on `equals()` to know if it should redraw the screen. If the old state equals the new state, Compose skips drawing to save CPU.

```kotlin
// BAD: Normal class. '==' checks memory address. 
// Compose will ALWAYS redraw, even if the text didn't change, causing jank.
class ViewState(val text: String)

// GOOD: Data class. '==' checks the actual text string.
// Compose will SKIP redrawing if the text is the same.
data class ImmutableViewState(val text: String)

// In ViewModel
_state.value = _state.value.copy(text = "New Text")
```

## Tradeoffs

**Advantages**
- **Zero Boilerplate:** Clean, readable, mathematically sound code.
- **Compose Optimization:** Critical for UI performance.
- **Easy Debugging:** `toString()` automatically prints the entire state of the object cleanly into `logcat`.

**Disadvantages**
- **Method Count (Dex Limit):** Generating 5 methods for every single data class adds up. A massive app with thousands of data classes will bloat the APK size and method count slightly.
- **Inheritance Restrictions:** Data classes cannot be `abstract`, `open`, `sealed`, or `inner`. They cannot inherit from other data classes. (They *can* implement interfaces).
- **Array Traps:** If you put an `Array` inside a data class, the generated `equals()` and `hashCode()` will use the Array's reference (memory address), not its contents! This breaks the mathematical correctness. *(Fix: Use `List` instead, or write a custom `equals()`—which defeats the purpose of the data class).*

## Failure Modes

- **The Body Property Trap:**
  ```kotlin
  data class User(val id: String) {
      var name: String = "" // NOT IN PRIMARY CONSTRUCTOR
  }
  
  val u1 = User("1").apply { name = "Alice" }
  val u2 = User("1").apply { name = "Bob" }
  
  println(u1 == u2) // TRUE! 'name' is ignored by equals()!
  ```
  *(Fix: The compiler only uses properties in the primary constructor for `equals()`. Put all state in the constructor).*
- **Using `var` in a Data Class:** Data classes are designed for immutability. If you use `var`, you can mutate the object *after* placing it into a `HashSet`. The object's `hashCode()` will change, but the `HashSet` won't know. The object will be permanently "lost" inside the Set, causing memory leaks and logic bugs.
- **The Massive Deep Copy:** Calling `copy()` on a massive, deeply nested data class 60 times a second on the Main Thread. It creates massive Garbage Collection pressure and drops frames. *(Fix: Flatter data structures, or mutate locally before freezing).*

## Staff Engineer Thinking

When reviewing data classes, a Staff engineer asks:

1.  **Are there Arrays inside this data class?** I will immediately reject a PR with `data class Payload(val bytes: ByteArray)`. Arrays do not have value-based equality in Kotlin. I will require changing it to `List<Byte>` or overriding `equals()` and `hashCode()` manually using `contentEquals()`.
2.  **Is this a God Class disguised as data?** If a `data class` has 35 properties, the `copy()` method becomes incredibly expensive and the UI state becomes unmanageable. I will ask the developer to break it up into smaller composed data classes.
3.  **Are we abusing destructuring?** Returning a `data class Location(val lat: Double, val lng: Double)` is fine. But if a developer does `val (lng, lat) = getLocation()`, the compiler doesn't care about the names; it maps by position (`component1()`, `component2()`). The variables are now swapped, creating a silent, catastrophic bug. I enforce caution with destructuring identical types.

## Common Misconceptions

- **"Data classes are just POJOs."** No. POJOs are mutable containers. Data classes are mathematically verifiable, immutable value types.
- **"I should make every class a data class."** If a class has no state and only contains functions (e.g., `UserRepositoryImpl`), making it a `data class` just adds useless bloated methods (`copy`, `hashCode`) to the APK. Use a normal `class` or an `object`.

## Probing Questions

1.  What are the 5 synthetic methods generated by the Kotlin compiler when you use the `data` keyword?
2.  Why is it dangerous to define properties inside the body `{ ... }` of a data class rather than in the primary constructor?
3.  Explain how Jetpack Compose relies on the `equals()` method generated by data classes to optimize UI rendering.
4.  Why does putting a `ByteArray` or `Array<String>` inside a data class break its structural equality guarantees?
5.  What is the "Destructuring Trap" when a data class contains multiple properties of the exact same type (e.g., two `Double`s)?
6.  Explain why using `var` inside a data class completely breaks the contract of a `HashSet` or `HashMap` if the object is mutated after insertion.
7.  Why can't a `data class` inherit from another `data class`?
8.  How does the `copy()` method support Unidirectional Data Flow (UDF) architectures like Redux or MVI?
9.  If a class only has functions and no state properties, why is it an anti-pattern to mark it as a `data class`?
10. Can a `data class` implement an `interface`? Give an example of why you might want to do this.

## Further Reading

- [`null-safety.md`](null-safety.md) — How to safely handle optional fields inside a data class.
- [`sealed-classes.md`](sealed-classes.md) — How data classes are often grouped together to represent distinct states.
- [`../principles/make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md) — Using data classes (and value classes) to enforce domain rules.
