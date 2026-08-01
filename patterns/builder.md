# Builder Pattern

> The Builder pattern separates the construction of a complex object from its representation. In the Java era of Android, Builders were mandatory to avoid the "Telescoping Constructor" anti-pattern (e.g., `AlertDialog.Builder`, `NotificationCompat.Builder`). However, a Staff engineer knows that modern Kotlin renders classic Builders largely obsolete through **Named Arguments** and **Default Parameters**. Today, the Builder pattern survives in Android primarily through legacy Java SDKs, complex configuration objects (like `OkHttpClient.Builder`), and Kotlin's powerful **Type-Safe DSLs** (Domain-Specific Languages).

---

## Overview

When an object requires numerous parameters to initialize—especially when many are optional—passing them all into a single constructor becomes unreadable and prone to errors (passing the `width` integer into the `height` integer slot).

The Builder pattern solves this by providing a mutable step-by-step construction object. Once all parameters are set, you call `.build()` to generate an immutable instance of the final object.

---

## 1. The Classic Java Builder (Android SDK)

The Android SDK is written in Java and relies heavily on the classic Builder pattern. If you've written Android code, you've used these.

### Example: NotificationCompat.Builder
Constructing a notification requires dozens of optional parameters (icons, actions, styles, channels). A single constructor would be impossible to maintain.

```kotlin
val notification = NotificationCompat.Builder(context, CHANNEL_ID)
    .setSmallIcon(R.drawable.ic_notification)
    .setContentTitle("Staff Engineer Playbook")
    .setContentText("New chapter available!")
    .setPriority(NotificationCompat.PRIORITY_HIGH)
    .setAutoCancel(true)
    .setStyle(NotificationCompat.BigTextStyle().bigText("Longer text here..."))
    .build() // Returns the immutable Notification object
```

### Example: OkHttpClient.Builder
`OkHttpClient` has over 30 configuration options (timeouts, interceptors, authenticators). 

```kotlin
// The builder allows step-by-step configuration
val builder = OkHttpClient.Builder()
    .connectTimeout(10, TimeUnit.SECONDS)
    .readTimeout(30, TimeUnit.SECONDS)

// You can conditionally add configuration
if (BuildConfig.DEBUG) {
    builder.addInterceptor(HttpLoggingInterceptor())
}

// Finally, build the immutable client
val client = builder.build()
```
**Staff Insight:** `OkHttpClient` implements a brilliant variation of the Builder pattern: **`newBuilder()`**. Because `OkHttpClient` is immutable, if you need a client that shares the same connection pool but has a different timeout for a specific request, you can derive a new builder from the existing client:
```kotlin
val specificClient = client.newBuilder()
    .readTimeout(60, TimeUnit.SECONDS)
    .build()
```

---

## 2. Why Kotlin Killed the Classic Builder

If you are writing new Kotlin code, **do not write classic Builder classes.**

### The Telescoping Constructor Problem
In Java, if you had optional parameters, you had to write multiple constructors:
```java
public class User {
    public User(String id, String name) { ... }
    public User(String id, String name, String email) { ... }
    public User(String id, String name, String email, String avatar) { ... }
}
```

### The Kotlin Solution: Named + Default Parameters
Kotlin eliminates the need for Builder classes for data models completely.

```kotlin
// Define defaults in the constructor
data class User(
    val id: String,
    val name: String,
    val email: String? = null,
    val avatarUrl: String? = null,
    val isActive: Boolean = true
)

// Instantiate using named arguments (order doesn't matter, omits optional fields)
val user = User(
    id = "123",
    name = "Alice",
    avatarUrl = "https://example.com/avatar.png"
    // email and isActive use their default values
)
```

### The Data Class `copy()` Method (The Micro-Builder)
If you need to mutate an existing immutable object, Kotlin's `data class` provides a generated `copy()` method, which acts exactly like OkHttp's `newBuilder()`.

```kotlin
val updatedUser = user.copy(isActive = false)
```

---

## 3. The Modern Kotlin Builder: Type-Safe DSLs

While classic object Builders are dead in Kotlin, the pattern evolved into **Type-Safe Builders** (Domain-Specific Languages). This uses Kotlin's "lambdas with receivers" to create highly readable, declarative configuration blocks.

This is the exact technology that powers Jetpack Compose, the Ktor networking client, and Kotlin Gradle scripts (`build.gradle.kts`).

### Building a Custom DSL (Example: Analytics Event)

Instead of a Java Builder:
```kotlin
// Old Java-style Builder
val event = AnalyticsEvent.Builder("checkout")
    .addProperty("total", 99.99)
    .addProperty("currency", "USD")
    .build()
```

We build a Kotlin DSL:
```kotlin
// The resulting immutable object
data class AnalyticsEvent(
    val name: String,
    val properties: Map<String, Any>
)

// The DSL Builder Class
class AnalyticsEventBuilder(private val name: String) {
    private val properties = mutableMapOf<String, Any>()
    
    fun property(key: String, value: Any) {
        properties[key] = value
    }
    
    fun build(): AnalyticsEvent = AnalyticsEvent(name, properties)
}

// The Higher-Order Function (The DSL entry point)
inline fun analyticsEvent(name: String, block: AnalyticsEventBuilder.() -> Unit): AnalyticsEvent {
    val builder = AnalyticsEventBuilder(name)
    builder.block() // Execute the lambda against the builder receiver
    return builder.build()
}

// Modern Kotlin Usage
val event = analyticsEvent("checkout") {
    property("total", 99.99)
    property("currency", "USD")
    // Conditional logic inside the builder!
    if (isVipUser) {
        property("user_tier", "VIP")
    }
}
```

---

## 4. Jetpack Compose: The Ultimate UI Builder

Jetpack Compose is essentially a massive, highly optimized Type-Safe Builder for the UI tree. It replaces the old `LayoutInflater` (which parsed XML strings at runtime) with compile-time checked Kotlin code.

```kotlin
Column(
    modifier = Modifier.padding(16.dp)
) {
    Text("Title")
    if (showSubtitle) {
        Text("Subtitle")
    }
}
```
Under the hood, these functions emit nodes into a `SlotTable`—they are building the UI tree dynamically.

---

## 5. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **Builder Boilerplate** | Writing Java-style Builder classes in Kotlin for data models. | Delete the Builder. Use a Kotlin `data class` with default parameters and named arguments. |
| **Incomplete Object State** | Calling `.build()` before mandatory parameters are provided. | In a classic Builder, pass mandatory parameters into the Builder's constructor (e.g. `AlertDialog.Builder(context)`), and leave only optional parameters as builder methods. |
| **Mutable Leakage** | The Builder returns an object that can still be mutated, or passes a mutable collection into the final object. | The `.build()` method must return a strictly immutable object. If passing lists, use `.toList()` inside `build()` to create an immutable copy. |
| **DSL Scope Pollution** | In nested Kotlin DSLs, you accidentally call a method from the outer builder inside the inner builder. | Use the `@DslMarker` annotation to restrict scope resolution in nested lambdas. |

---

## 6. Common Pitfalls

### Pitfall 1: Passing Mutable Collections to a Builder
```kotlin
val tags = mutableListOf("android", "kotlin")
val post = Post.Builder().setTags(tags).build()

// Later...
tags.add("java") // This modifies the already-built 'post' object!
```
*Fix:* A Builder must ensure the object it creates is deeply immutable.
```kotlin
class Builder {
    fun setTags(tags: List<String>) = apply { this.tags = tags.toList() } // Defensive copy
}
```

### Pitfall 2: The God Builder
When a Builder has 50 methods, it often means the resulting object violates the Single Responsibility Principle. 
*Fix:* Group related configurations. Notice how `OkHttpClient.Builder` doesn't have `setCacheDirectory(File)`. Instead, it has `cache(Cache)`, forcing you to configure the `Cache` object separately before passing it to the main builder.

---

## Probing Questions

1.  **Immutability:** Explain the mechanical difference between OkHttp's `Request.Builder` and Retrofit's `@GET` annotations. Both ultimately construct HTTP requests. Why does Retrofit use reflection/proxies instead of exposing a Builder to the developer?
2.  **Kotlin Features:** How does the Kotlin compiler handle named arguments and default parameters at the JVM bytecode level? Does it generate a Builder class, or does it generate overloaded constructors (synthetic methods)?
3.  **DSL Mechanics:** Explain the concept of a "Lambda with Receiver" (`T.() -> Unit`). How does it change the `this` context inside the lambda block, and how does this enable DSLs?
4.  **DslMarker:** You are writing an HTML DSL (`html { body { div { } } }`). Without `@DslMarker`, a developer can legally call a `body { }` block inside a `div { }` block. How does the `@DslMarker` annotation prevent this at compile time?
5.  **Data Classes:** The `copy()` method of a Kotlin data class is often used as a lightweight builder. What is a "shallow copy" vs a "deep copy", and which one does the generated `copy()` method perform? What risk does this pose if your data class contains a `MutableList`?

## Answer Key

1. **Immutability: Why does Retrofit use reflection/proxies instead of exposing a Builder to the developer?**
   Retrofit uses dynamic proxies to construct HTTP requests declaratively via interfaces, abstracting away the boilerplate of manually building OkHttp `Request` objects. This allows developers to define the API contract cleanly, while Retrofit handles the repetitive translation internally.
2. **Kotlin Features: How does the Kotlin compiler handle named arguments and default parameters at the JVM bytecode level?**
   It generates a synthetic constructor with a bitmask parameter. The bitmask tracks which arguments were provided. Inside the constructor, it uses the bitmask to inject default values for missing arguments before calling the actual constructor, avoiding telescoping constructors.
3. **DSL Mechanics: Explain the concept of a "Lambda with Receiver" (`T.() -> Unit`).**
   A lambda with receiver injects an instance of type `T` into the lambda scope as `this`. It allows you to call methods and access properties of `T` directly without prefixing them, making the code read like a domain-specific configuration block.
4. **DslMarker: How does the `@DslMarker` annotation prevent scope pollution at compile time?**
   When multiple nested receivers share the same `@DslMarker` annotation, the Kotlin compiler restricts implicit `this` resolution to the nearest receiver. Attempting to call an outer receiver's method from inside an inner receiver without explicit qualification results in a compile-time error.
5. **Data Classes: What is a "shallow copy" vs a "deep copy", and which one does the generated `copy()` method perform?**
   A shallow copy duplicates the object's references, while a deep copy duplicates the references and the objects they point to. Kotlin's `copy()` performs a shallow copy. If a data class contains a `MutableList`, both the original and copied object will point to the same list, risking unintended mutations.

## Further Reading

- [`../android/compose/compose-runtime.md`](../android/compose/compose-runtime.md) — How Jetpack Compose uses DSLs to build the UI Slot Table.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Extensive use of the `OkHttpClient.Builder` for network configuration.
- [`factory.md`](factory.md) — How Builders compare to Factories for object creation.
