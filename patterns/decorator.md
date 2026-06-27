# Decorator Pattern

## Overview

The Decorator pattern attaches additional responsibilities to an object dynamically. Decorators provide a flexible alternative to subclassing for extending functionality. In modern Android, it is the primary mechanism for wrapping existing classes with transversal concerns like logging, caching, or timing, without altering the underlying class's code.

## Why It Exists

Imagine an `ImageDownloader` class. You realize you need to log how long downloads take. You could modify `ImageDownloader` directly (violating the Open/Closed Principle). Later, you need to add memory caching. If you subclass it (`CachedImageDownloader`), and then need a version that both caches *and* logs, you end up with a combinatorial explosion of subclasses (`LoggingCachedImageDownloader`).

The Decorator solves this by wrapping the original object in a new object that shares the same interface, allowing you to stack behaviors infinitely at runtime.

## Historical Context

One of the original GoF structural patterns. Traditionally implemented by having the Decorator class implement the target Interface *and* hold a reference to an instance of that Interface. In Kotlin, class delegation (`by`) makes the Decorator pattern incredibly terse and powerful, removing the need for manual method forwarding.

## First Principles

1.  **Composition over Inheritance:** Instead of inheriting behavior from a superclass, you compose behavior by wrapping objects inside other objects.
2.  **Interface Adherence:** The decorator *must* implement the exact same interface as the object it decorates. To the client, a decorated object looks identical to a naked object.
3.  **Transversal Separation:** Core business logic stays in the base class; transversal concerns (metrics, caching, retries) move to the decorators.

## Mental Model

Think of a picture frame. The photograph itself is the base component. You can add a matte (Decorator 1) to give it a border. You can add glass (Decorator 2) to protect it. You can add a wooden frame (Decorator 3) to hang it. The core object is always the photograph, but you've added new properties and behaviors by wrapping it in layers. Crucially, the wall doesn't care if it's hanging a naked photo or a framed one; it just needs a hook.

## Internal Mechanics

### 1. The Classic (Manual) Implementation

```kotlin
// The Component Interface
interface NetworkClient {
    fun fetch(url: String): String
}

// The Concrete Component
class BasicNetworkClient : NetworkClient {
    override fun fetch(url: String): String {
        Thread.sleep(500) // Simulate work
        return "Data from $url"
    }
}

// The Decorator
class LoggingNetworkClient(
    private val delegate: NetworkClient // Holds reference to the interface
) : NetworkClient { // Implements the same interface

    override fun fetch(url: String): String {
        println("Starting fetch for $url")
        val startTime = System.currentTimeMillis()
        
        // Delegate the actual work
        val result = delegate.fetch(url)
        
        println("Completed in ${System.currentTimeMillis() - startTime}ms")
        return result
    }
}
```

### 2. The Kotlin Way (Class Delegation)

Kotlin's `by` keyword automatically forwards all interface methods to the delegate, meaning you only need to override the methods you actually want to decorate.

```kotlin
interface Repository {
    fun get(id: String): Data
    fun delete(id: String)
    fun update(id: String, data: Data)
}

// We only want to decorate 'get' to add caching. 
// Kotlin handles forwarding 'delete' and 'update' to the delegate automatically.
class CachingRepository(
    private val delegate: Repository,
    private val cache: LruCache<String, Data>
) : Repository by delegate { // <--- Magic happens here

    override fun get(id: String): Data {
        return cache.get(id) ?: delegate.get(id).also { cache.put(id, it) }
    }
}
```

## Architecture

```mermaid
flowchart TD
    Client[Client Code] -->|calls| Interface[Component Interface]
    
    subgraph Layers
        Dec2[Logging Decorator] -->|wraps| Dec1
        Dec1[Caching Decorator] -->|wraps| Base
        Base[Concrete Component]
    end
    
    Interface <.. Dec2
    Interface <.. Dec1
    Interface <.. Base
    
    classDef core fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef wrapper fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    
    class Client,Interface,Base core;
    class Dec1,Dec2 wrapper;
```

## Production Example

The most prominent and powerful example of the Decorator pattern in Android is **OkHttp Interceptors**. 

An Interceptor is a functional decorator. It receives a `Chain`, inspects the Request (before), calls `chain.proceed()` (delegation), and inspects the Response (after).

```kotlin
class GzipRequestInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val originalRequest = chain.request()
        
        // Decorate before: Add header and compress body
        val compressedRequest = originalRequest.newBuilder()
            .header("Content-Encoding", "gzip")
            .method(originalRequest.method, gzip(originalRequest.body))
            .build()
            
        // Delegate to the next decorator in the chain
        return chain.proceed(compressedRequest)
    }
}
```
You can stack an `AuthInterceptor`, a `LoggingInterceptor`, and a `GzipInterceptor`. They all decorate the network call without modifying the core HTTP engine.

## Android Example

The Android View system uses decorators, notably in `ContextWrapper`. 

When you create an `Activity`, it inherits from `ContextThemeWrapper`, which inherits from `ContextWrapper`, which implements `Context`. The `ContextWrapper` holds a "base context" and delegates all calls to it, allowing the framework to dynamically wrap contexts with new themes or configurations without subclassing every possible system service.

```java
// Simplified Android Open Source Project (AOSP) code
public class ContextWrapper extends Context {
    Context mBase; // The delegate

    public ContextWrapper(Context base) {
        mBase = base;
    }

    @Override
    public Object getSystemService(String name) {
        return mBase.getSystemService(name); // Forwarding
    }
}
```

## Tradeoffs

**Advantages**
- **Single Responsibility Principle:** You can divide a monolithic class that handles network, caching, and logging into three distinct classes.
- **Open/Closed Principle:** You can add new behavior without changing existing code.
- **Runtime Flexibility:** You can compose decorators dynamically. (e.g., Only add the `LoggingDecorator` if `BuildConfig.DEBUG` is true).

**Disadvantages**
- **Many Tiny Objects:** Can result in a system with lots of small objects that look similar, making it hard to debug.
- **Order Dependency:** The order in which decorators are stacked matters heavily. Putting a `CachingDecorator` *outside* a `LoggingDecorator` means cache hits won't be logged.
- **Object Identity:** `decorator == baseObject` is false. If client code relies on checking object identity or casting to specific concrete types (`if (client is BasicNetworkClient)`), the decorator breaks the code.

## Failure Modes

- **The Fat Interface Trap:** If the interface being decorated has 50 methods, manually implementing a Decorator in Java is a nightmare of forwarding boilerplate. (Kotlin's `by` keyword mitigates this).
- **The Semi-Transparent Decorator:** A decorator that adds new public methods not found in the base interface. If the client calls these new methods, they are now coupled to the *Decorator*, not the *Interface*, defeating the purpose of the pattern.
- **State Corruption:** If a decorator maintains internal state that duplicates or conflicts with the base component's state, data corruption occurs. Decorators should generally be stateless, focusing purely on behavior interception.

## Staff Engineer Thinking

When reviewing PRs with Decorators, a Staff engineer asks:

1.  **Does this belong in a Decorator or the Base Class?** If the new behavior is fundamental to the object's identity (e.g., calculating a cryptographic signature for a specific payment gateway), it belongs in the base class or a Strategy. If it's a transversal concern (logging, retrying), use a Decorator.
2.  **Is the stacking order safe?** Are we injecting a list of decorators via Dagger? Is the order deterministic? 
3.  **Are we breaking Object Identity?** Does the app rely on event buses or callbacks where the `this` reference is passed around? A decorated object passing `this` to a subscriber passes the *base* object, not the *decorator*, causing the subscriber to bypass the decorators on subsequent calls.

## Common Misconceptions

- **"Decorator and Proxy are the same."** Structurally, they are nearly identical (a wrapper holding a delegate). The difference is *intent*. A **Proxy** controls access to an object (e.g., lazy loading, access control, remote proxy). A **Decorator** adds behavior to an object.
- **"Kotlin Extension Functions replace Decorators."** False. Extension functions are resolved statically. They cannot intercept or wrap existing virtual method calls inside an interface.

## Probing Questions

1.  How does Kotlin's `by` keyword simplify the Decorator pattern?
2.  Explain the difference between the Decorator pattern and the Proxy pattern.
3.  If you stack a `RetryDecorator`, a `LoggingDecorator`, and a `CachingDecorator` on a network client, what is the optimal order and why?
4.  Why is the Decorator pattern considered an alternative to subclassing? What specific problem does it solve?
5.  How do OkHttp Interceptors implement the Decorator pattern? Why is it structured as a "Chain" rather than nested objects?
6.  What happens if client code tries to downcast a decorated object to its concrete base class implementation?
7.  How does the Decorator pattern adhere to the Open/Closed Principle?
8.  Can a Decorator dynamically remove behavior from an object? How?
9.  If a base object registers itself (`this`) as a listener with a system service, what problem occurs when that object is decorated?
10. How would you test a `RetryDecorator` without actually hitting a network?

## Further Reading

- [`adapter.md`](adapter.md) — Adapters change the interface; Decorators keep the same interface.
- [`retry.md`](retry.md) and [`circuit-breaker.md`](circuit-breaker.md) — Resilience patterns are almost always implemented as Decorators.
