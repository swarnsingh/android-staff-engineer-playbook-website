# Strategy Pattern

## Overview

The Strategy pattern defines a family of algorithms, encapsulates each one, and makes them interchangeable. Strategy lets the algorithm vary independently from the clients that use it. In modern mobile development, it's the primary mechanism for replacing large `if/else` or `when` blocks with polymorphism, enabling clean composition and testing.

## Why It Exists

Business rules change dynamically. How an app sorts a list, calculates a discount, caches data, or authenticates a user often depends on the current state, user preferences, or server config. If a class hardcodes all variations using `when` statements, it becomes a massive, unmaintainable "God Object" that violates the Open/Closed Principle. The Strategy pattern extracts the "how" into separate, interchangeable classes (or functions).

## Historical Context

One of the original GoF behavioral patterns. Historically implemented using deep class hierarchies and interfaces. In modern Kotlin, the Strategy pattern is often drastically simplified: because functions are first-class citizens, a Strategy is frequently just a higher-order function (`(A) -> B`) rather than a dedicated interface and class implementation.

## First Principles

1.  **Favor Composition over Inheritance:** Don't subclass `Checkout` into `CreditCardCheckout` and `PaypalCheckout`. Instead, compose a generic `Checkout` class with a `PaymentStrategy`.
2.  **Open/Closed Principle:** You should be able to add a new pricing algorithm (e.g., "Holiday Discount") without touching the core `Cart` calculation code.
3.  **Encapsulate What Varies:** Identify the aspects of your application that vary and separate them from what stays the same.

## Mental Model

Think of a navigation app (like Google Maps). The core goal is "route from A to B". However, the *strategy* for calculating that route varies wildly based on the user's choice: driving, walking, cycling, or transit. The map rendering engine doesn't care how the route was calculated; it just takes the list of coordinates and draws a line. The routing algorithm is the Strategy.

## Internal Mechanics

### 1. The Classic Interface Approach

Best when the strategy requires multiple methods or internal state.

```kotlin
// 1. The Strategy Interface
interface CacheStrategy {
    fun get(key: String): ByteArray?
    fun put(key: String, data: ByteArray)
}

// 2. Concrete Strategies
class MemoryCacheStrategy : CacheStrategy {
    private val cache = LruCache<String, ByteArray>(1024 * 1024)
    override fun get(key: String) = cache.get(key)
    override fun put(key: String, data: ByteArray) { cache.put(key, data) }
}

class DiskCacheStrategy(private val fileDir: File) : CacheStrategy {
    override fun get(key: String) = File(fileDir, key).takeIf { it.exists() }?.readBytes()
    override fun put(key: String, data: ByteArray) { File(fileDir, key).writeBytes(data) }
}

// 3. The Context
class ImageLoader(
    // The Context is composed with a Strategy
    private val cacheStrategy: CacheStrategy 
) {
    fun loadImage(url: String) {
        val cached = cacheStrategy.get(url)
        if (cached != null) return render(cached)
        
        val networkData = fetchFromNetwork(url)
        cacheStrategy.put(url, networkData)
        render(networkData)
    }
}
```

### 2. The Modern Functional Approach

When the strategy is a single operation, use Kotlin's higher-order functions. No interfaces required.

```kotlin
// The Context takes a function as the Strategy
class OrderProcessor(
    private val calculateDiscount: (Order) -> Double
) {
    fun process(order: Order) {
        val finalPrice = order.total - calculateDiscount(order)
        charge(finalPrice)
    }
}

// The Strategies are just functions
val noDiscount: (Order) -> Double = { 0.0 }
val employeeDiscount: (Order) -> Double = { it.total * 0.20 }
val vipDiscount: (Order) -> Double = { order -> if (order.total > 100) 25.0 else 0.0 }

// Usage
val processor = OrderProcessor(calculateDiscount = vipDiscount)
```

### 3. The DI-Injected Strategy (The Staff Approach)

In modern Android architecture, Strategies are almost always injected via Dagger/Hilt. This is incredibly powerful for things like Sorters, Filters, or Authenticators.

```kotlin
// 1. The Strategy Interface
interface FeedSorter {
    fun sort(items: List<FeedItem>): List<FeedItem>
}

// 2. Concrete Strategies (Injected with their own dependencies!)
class ChronologicalSorter @Inject constructor() : FeedSorter {
    override fun sort(items: List<FeedItem>) = items.sortedByDescending { it.timestamp }
}

class AlgorithmicSorter @Inject constructor(
    private val userPreferences: UserPreferences // Strategy declares its own dependencies!
) : FeedSorter {
    override fun sort(items: List<FeedItem>): List<FeedItem> {
        val favoriteTopics = userPreferences.getTopics()
        return items.sortedByDescending { favoriteTopics.contains(it.topic) }
    }
}

// 3. The Context (ViewModel)
@HiltViewModel
class FeedViewModel @Inject constructor(
    private val repository: FeedRepository,
    // Inject a Map of Strategies using Hilt Multibinding
    private val sorters: Map<String, @JvmSuppressWildcards FeedSorter>
) : ViewModel() {
    
    private val _uiState = MutableStateFlow<List<FeedItem>>(emptyList())
    
    fun changeSortMethod(method: String) {
        val items = repository.getCurrentFeed()
        val strategy = sorters[method] ?: sorters["chronological"]!!
        _uiState.value = strategy.sort(items)
    }
}
```
This is the true power of the Strategy pattern: `AlgorithmicSorter` requires a `UserPreferences` database, while `ChronologicalSorter` does not. Because they are injected via DI, the `FeedViewModel` never has to know about `UserPreferences`.

## Architecture

```mermaid
flowchart TD
    Context[Context] -->|Delegates algorithm to| StrategyInterface[Strategy Interface]
    StrategyInterface <.. ConcreteA[Concrete Strategy A]
    StrategyInterface <.. ConcreteB[Concrete Strategy B]
    StrategyInterface <.. ConcreteC[Concrete Strategy C]
    
    classDef core fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef strat fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    
    class Context core;
    class StrategyInterface,ConcreteA,ConcreteB,ConcreteC strat;
```

## Production Example

In a complex video streaming app, the policy for determining video quality isn't static. It changes based on network conditions, user settings, and battery life.

```kotlin
interface BitrateSelectionStrategy {
    fun selectBitrate(networkBandwidth: Int, batteryLevel: Float): Int
}

class AutoBitrateStrategy : BitrateSelectionStrategy {
    override fun selectBitrate(bandwidth: Int, battery: Float): Int {
        if (battery < 0.15f) return 480 // Save power
        return when {
            bandwidth > 10_000 -> 1080
            bandwidth > 5_000 -> 720
            else -> 480
        }
    }
}

class DataSaverBitrateStrategy : BitrateSelectionStrategy {
    override fun selectBitrate(bandwidth: Int, battery: Float) = 360 // Always low
}
```
When the user toggles "Data Saver Mode" in settings, the app simply swaps the `BitrateSelectionStrategy` instance in the video player context. The video player core logic remains untouched.

## Android Example

The Android framework uses Strategy extensively. The clearest example is `RecyclerView.LayoutManager`.

A `RecyclerView` (the Context) knows how to recycle views and handle touch events, but it has no idea how to position items on the screen. It delegates positioning entirely to the `LayoutManager` (the Strategy).

```kotlin
// Strategy A: Linear layout
recyclerView.layoutManager = LinearLayoutManager(context)

// Strategy B: Grid layout
recyclerView.layoutManager = GridLayoutManager(context, 2)

// Strategy C: Staggered grid
recyclerView.layoutManager = StaggeredGridLayoutManager(2, VERTICAL)
```
You can radically change the look and behavior of the list without modifying the `RecyclerView` class or your `Adapter`.

## Tradeoffs

**Advantages**
- **Clean Code:** Eliminates massive, hard-to-read conditional statements (`if/else` or `when`).
- **Testability:** Strategies can be unit tested in complete isolation. The Context can be tested using a mock strategy.
- **Runtime Swapping:** Strategies can be swapped at runtime based on user actions or server configuration.

**Disadvantages**
- **Class Explosion:** Can lead to a proliferation of tiny classes if overused for trivial variations.
- **Client Burden:** The client creating the Context often needs to know about the different strategies and decide which one to inject. (This is usually mitigated by combining Strategy with a Factory).

## Failure Modes

- **The Fat Strategy:** A strategy interface that has too many methods. If a strategy forces concrete implementations to leave methods blank or throw `NotImplementedError`, the interface violates the Interface Segregation Principle.
- **Strategy vs. State Confusion:** The State pattern and Strategy pattern look identical structurally (a Context delegating to an Interface). But the intent is different: Strategies are swapped externally by the client; States swap themselves internally based on transitions.
- **Over-engineering:** Using a full interface/class Strategy for a simple mathematical variation where a higher-order function or a simple `enum` would suffice.

## Staff Engineer Thinking

When reviewing PRs with Strategies, a Staff engineer focuses on the boundary:

1.  **Is the Context truly agnostic?** If the Context has to check `if (strategy is DataSaverStrategy) { ... }`, the abstraction has failed. The Strategy interface must encapsulate the differences completely.
2.  **How is data passed?** Does the Context pass *all* its internal data to the Strategy, breaking encapsulation? Or does the Strategy take a callback to ask the Context for data only when needed?
3.  **Is the instantiation deferred?** If the Strategies are stateless, they should be Singletons or static functions to avoid unnecessary allocation during hot loops (like inside a `RecyclerView` scroll or frame rendering).

## Common Misconceptions

- **"Enums are just as good."** Enums are great for simple variations, but if each enum case requires complex dependencies (e.g., one payment method needs a database connection, another needs a network client), an Enum becomes a bloated God Object. Strategies allow each algorithm to declare its own specific dependencies.
- **"It's just Dependency Injection."** DI is the *mechanism* used to deliver the Strategy to the Context, but the Strategy *Pattern* is the architectural decision to encapsulate varying algorithms.

## Probing Questions

1.  How would you refactor a `when` statement with 10 branches into a Strategy pattern?
2.  When should you use a Kotlin higher-order function instead of an interface for a Strategy?
3.  How does the Strategy pattern help adhere to the Open/Closed Principle?
4.  Explain the structural similarity and semantic difference between the Strategy pattern and the State pattern.
5.  If a Strategy needs to interact back with the Context, how should that communication be designed?
6.  How do you manage dependencies required by specific Concrete Strategies if the Context shouldn't know about them? (Hint: Factories/DI).
7.  Can multiple Strategies be composed together? Give an example.
8.  Why is `RecyclerView.LayoutManager` considered a Strategy pattern?
9.  What is the performance cost of using Strategy via interfaces in Kotlin, and how can `inline` functions mitigate it in functional strategies?
10. If an algorithm variation only requires changing a single primitive value (like a timeout duration), is the Strategy pattern appropriate?

## Further Reading

- [`factory.md`](factory.md) — Factories are typically responsible for instantiating and injecting the correct Strategy.
- [`state.md`](state.md) — The behavioral cousin to Strategy; understand the difference in intent.
- Refactoring Guru: [Strategy Pattern](https://refactoring.guru/design-patterns/strategy)
