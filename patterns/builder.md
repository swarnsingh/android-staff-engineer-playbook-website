# Builder Pattern

## Overview

The Builder pattern separates the construction of a complex object from its representation, allowing the same construction process to create different representations. In modern Kotlin, the traditional Java-style Builder pattern is largely obsolete due to named arguments and default parameters. However, the *concept* survives in DSLs (Domain-Specific Languages) and for configuring highly complex library clients.

## Why It Exists

If an object requires 10 parameters to construct, but 8 of them are optional, a constructor becomes unwieldy. 
`User("John", "Doe", null, null, 25, null, true, false)` is unreadable. This is known as the "Telescoping Constructor Anti-pattern." The Builder solves this by allowing step-by-step initialization with readable, chainable methods, ultimately invoking a `build()` method to validate and instantiate the object.

## Historical Context

A GoF creational pattern. In Java, this pattern was absolutely mandatory for any class with more than 3-4 properties. Tools like AutoValue and Lombok existed almost entirely to generate Builders. When Kotlin introduced named arguments and default parameters, 95% of the use cases for the GoF Builder vanished overnight. Today, you only build manual Builders for specific API-design reasons.

## First Principles

1.  **Immutability:** The final object produced by the Builder must be completely immutable.
2.  **Step-by-Step Construction:** Construction happens over time, not instantly.
3.  **Validation at the Edge:** The `build()` method is the gatekeeper. It ensures that the accumulated state is valid before yielding the object.

## Mental Model

Think of ordering a custom sandwich at a deli. You don't hand the cashier a completed specification sheet all at once. You walk down the line: "I want wheat bread. Turkey. No cheese. Add lettuce and tomato. Light mayo." The sandwich (the complex object) is constructed step-by-step. The final "wrap it up" action is the `build()` call, and once wrapped, the sandwich cannot be changed.

## Internal Mechanics

### 1. The Kotlin Way (Data Classes - The 95% Solution)

Do not write a Builder for this. Use Kotlin's language features.

```kotlin
// Define the class with defaults
data class NetworkConfig(
    val url: String,
    val timeoutMs: Long = 30_000,
    val retries: Int = 3,
    val useTls: Boolean = true
)

// Callers use named arguments. No Builder class needed.
val config = NetworkConfig(
    url = "https://api.example.com",
    retries = 5 // timeoutMs and useTls use defaults
)

// "Copying" acts as a functional builder for mutations
val updatedConfig = config.copy(timeoutMs = 60_000)
```

### 2. The Type-Safe Builder (Kotlin DSL)

When configuring complex, nested hierarchies (like UI layouts, HTML, or Gradle scripts), Kotlin's type-safe builders (DSLs) provide a massive ergonomics upgrade over traditional chainable builders.

```kotlin
// The target class
class Notification(val title: String, val body: String, val priority: Int)

// The Builder
class NotificationBuilder {
    var title: String = ""
    var body: String = ""
    var priority: Int = 0

    fun build(): Notification {
        require(title.isNotEmpty()) { "Title is required" }
        return Notification(title, body, priority)
    }
}

// The DSL entry point
fun notification(block: NotificationBuilder.() -> Unit): Notification {
    return NotificationBuilder().apply(block).build()
}

// Usage
val myNotif = notification {
    title = "System Update"
    body = "Please reboot your device."
    priority = 1
}
```

## Architecture

```mermaid
flowchart LR
    Client[Client Code] -->|1. creates| Builder[Builder]
    Client -->|2. chains setters| Builder
    Client -->|3. calls build| Builder
    Builder -->|4. instantiates & validates| Product[Complex Product]
    Builder -->|5. returns| Product
    
    classDef core fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef external fill:#f8d7da,stroke:#dc3545,stroke-width:2px;
    
    class Client core;
    class Builder,Product external;
```

## Production Example

When wrapping complex third-party SDKs (like OkHttp, Retrofit, or Room), the Builder pattern is used to construct heavy client instances that require extensive configuration before they can be used.

```kotlin
// Real-world OkHttp example
val client = OkHttpClient.Builder()
    .connectTimeout(10, TimeUnit.SECONDS)
    .readTimeout(10, TimeUnit.SECONDS)
    .addInterceptor(AuthInterceptor())
    .addNetworkInterceptor(LoggingInterceptor())
    .cache(Cache(File(context.cacheDir, "http_cache"), 10L * 1024 * 1024))
    .build() // Validates all inputs and creates the heavy OkHttpClient instance
```
The resulting `OkHttpClient` is thread-safe and immutable. The configuration cannot be changed once `build()` is called.

## Android Example

The Android framework uses Builders extensively, particularly for objects passed to system services across IPC (Inter-Process Communication) boundaries.

- `NotificationCompat.Builder` (The most famous example)
- `AlertDialog.Builder`
- `JobInfo.Builder`

```kotlin
// Android Notification
val notification = NotificationCompat.Builder(context, CHANNEL_ID)
    .setSmallIcon(R.drawable.ic_notification)
    .setContentTitle("New Message")
    .setContentText("You have 1 unread message.")
    .setPriority(NotificationCompat.PRIORITY_HIGH)
    .setAutoCancel(true)
    .build()
```
The Builder acts as a facade, hiding the immense complexity of supporting notifications across 15 years of different Android OS versions.

## Tradeoffs

**Advantages**
- **Encapsulation of Validation:** The `build()` method guarantees that an object is only created if it is internally consistent (e.g., `startDate` is before `endDate`).
- **Immutability:** Allows for the construction of deeply immutable objects that have complex initialization requirements.
- **Fluent API:** Method chaining (`.withX().withY()`) makes configuration highly readable.

**Disadvantages**
- **Boilerplate:** In Java, writing a Builder doubles the lines of code for a class. In Kotlin, it's usually entirely unnecessary.
- **Statefulness:** The Builder itself is highly stateful and mutable during construction. It is almost never thread-safe.

## Failure Modes

- **The Useless Kotlin Builder:** Writing a traditional Builder class in Kotlin for a simple data container instead of using `data class` with default parameters. This is a classic "writing Java in Kotlin" code smell.
- **Mutable Products:** A Builder that creates a mutable object defeats the primary purpose of the pattern. The product should have `val` properties, not `var`.
- **Validation in the Constructor:** If the actual Product class does the validation in its `init` block instead of the Builder's `build()` method, the Builder is just useless indirection.

## Staff Engineer Thinking

When reviewing a PR that introduces a new Builder, a Staff engineer asks:

1.  **Is this necessary in Kotlin?** If the class has 8 optional parameters and no complex cross-validation logic, delete the Builder and use a `data class`.
2.  **Does it prevent invalid states?** Does `build()` throw an `IllegalStateException` if `useTls = true` but `certificate` is null? If it doesn't, the Builder isn't doing its job.
3.  **Are we building a DSL?** If the configuration is deeply nested (e.g., configuring an analytics schema with nested events and parameters), a Kotlin Type-Safe Builder (DSL) with receiver blocks (`@DslMarker`) is the correct architectural choice.

## Common Misconceptions

- **"Factory and Builder are the same."** No. A Factory usually creates an object in one step (you call `create()` and get the object). A Builder creates an object in multiple steps (you call 5 setters, then call `build()`).
- **"Builders are just for reducing constructor parameters."** That was the Java excuse. The *architectural* purpose of a Builder is to construct a complex, immutable object where the components have interdependencies that must be validated together.

## Probing Questions

1.  Why has the classic GoF Builder pattern largely disappeared in Kotlin codebases?
2.  Explain the concept of a "Telescoping Constructor" and how Builders solve it.
3.  How do you ensure a Builder itself is not accidentally reused after `build()` is called?
4.  What is a Kotlin Type-Safe Builder (DSL), and how does it differ from a traditional method-chaining Builder?
5.  Why does `NotificationCompat.Builder` exist in the Android framework? (Hint: backwards compatibility).
6.  If you have an object that requires asynchronous data fetching to be constructed, should the Builder handle the async work?
7.  How does the Builder pattern relate to the concept of Immutability?
8.  What is the purpose of the `@DslMarker` annotation in Kotlin?
9.  In a multi-module architecture, can the Builder reside in a different module than the Product implementation? How?
10. Describe a scenario in a modern Android app where you would explicitly choose to write a manual Builder over using a `data class`.

## Further Reading

- [`factory.md`](factory.md) — The single-step creational cousin to the multi-step Builder.
- [`../principles/make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md) — The core philosophical reason for using the `build()` method as a validation gate.
- Kotlin Docs: [Type-Safe Builders](https://kotlinlang.org/docs/type-safe-builders.html)
