# Delegation

## Overview

Delegation is a structural design pattern where an object, instead of performing a task itself, hands that task off to a helper object (the delegate). Kotlin elevates this pattern to a first-class language feature via the `by` keyword, allowing you to implement "Composition over Inheritance" with zero boilerplate.

There are two primary types of delegation in Kotlin: **Class Delegation** and **Property Delegation**.

## Why It Matters

**The Problem with Inheritance:**
If you want to create a special type of `List` that logs every time an item is added, the traditional Java approach is to inherit from `ArrayList`. However, inheriting from concrete classes tightly couples your code to the internal implementation of `ArrayList`. If `ArrayList` changes its internal logic in a future Java update, your subclass might break (the "Fragile Base Class" problem).

**The Solution:**
Composition. You create a class that *contains* an `ArrayList`, and you manually forward every single method call (`get`, `size`, `remove`) to that inner list. This is mathematically sound, but incredibly tedious. Kotlin's `by` keyword does this manual forwarding for you automatically at compile time.

## Historical Context

"Favor Composition over Inheritance" is Item 18 in Joshua Bloch's legendary book *Effective Java*. While everyone agreed with the philosophy, developers often ignored it because writing 20 forwarding methods by hand was exhausting. Inheritance was just a single `extends` keyword. Kotlin recognized this friction and introduced the `by` keyword to make Composition as easy as Inheritance.

## First Principles

1.  **The `by` Keyword:** This is the magic. It tells the compiler, "For any interface methods I don't implement myself, forward them to this object."
2.  **Interfaces Only (Class Delegation):** Kotlin can only automatically delegate methods defined in an `interface`. You cannot delegate to a concrete class instance directly.
3.  **Getter/Setter Hijacking (Property Delegation):** Property delegation intercepts the `get()` and `set()` calls of a specific variable, allowing you to extract complex logic (like lazy initialization or database syncing) out of the property and into a reusable delegate class.

## Mental Model

Think of a CEO and an Executive Assistant.
- **Inheritance:** The CEO tries to be the Assistant, the Accountant, and the Janitor all at once. If the rules of accounting change, the CEO breaks.
- **Delegation:** The CEO (the wrapper class) is asked for a financial report. The CEO immediately turns around and asks the Accountant (the delegate) for the report, and then hands it back to you. The CEO doesn't know *how* the math was done; they just forwarded the request.

## Internal Mechanics

### 1. Class Delegation

```kotlin
// The Interface
interface AnalyticsLogger {
    fun logEvent(name: String)
}

// The Concrete Delegate (The Accountant)
class FirebaseLogger : AnalyticsLogger {
    override fun logEvent(name: String) = println("Firebase: $name")
}

// The Wrapper (The CEO)
// "I implement AnalyticsLogger, but I'm delegating all the work to 'logger'"
class PaymentProcessor(logger: AnalyticsLogger) : AnalyticsLogger by logger {
    
    fun process() {
        println("Processing payment...")
        logEvent("payment_success") // Automatically forwarded to 'logger'
    }
}
```

*Under the hood:* The `kotlinc` compiler generates bytecode for `PaymentProcessor` that contains a hidden `logEvent` method. Inside that method, it writes `logger.logEvent(name)`. It writes the boilerplate for you.

### 2. Property Delegation

Property delegation intercepts the memory access of a variable.

```kotlin
// 1. Lazy Delegation (The most common)
// The memory allocation doesn't happen until the variable is called for the first time.
val heavyDatabase by lazy { Room.databaseBuilder(...) }

// 2. Observable Delegation
// Intercepts the setter and fires a callback whenever the value changes.
var username: String by Delegates.observable("<no name>") { prop, old, new ->
    println("$old -> $new")
}
```

*Under the hood:* When you write `val user by lazy { ... }`, the compiler actually creates a hidden variable (e.g., `user$delegate`). When you call `user`, the compiler rewrites the bytecode to call `user$delegate.getValue()`.

## Production Example

**The ViewModel State Delegate**

In Jetpack Compose, managing state in a ViewModel often requires two variables: a private `MutableStateFlow` (which can be modified) and a public `StateFlow` (which is read-only). This is tedious.

Property delegation can hide this.

```kotlin
// A custom delegate that manages the Mutable/Read-Only split
class UiStateDelegate<T>(initialState: T) {
    private val _state = MutableStateFlow(initialState)
    val state: StateFlow<T> = _state.asStateFlow()

    operator fun getValue(thisRef: Any?, property: KProperty<*>): StateFlow<T> {
        return state
    }

    fun update(mutate: (T) -> T) {
        _state.value = mutate(_state.value)
    }
}

// In the ViewModel:
class ProfileViewModel : ViewModel() {
    // 1 line of code instead of 3!
    val uiState by UiStateDelegate(ProfileState())
}
```

## Tradeoffs

**Advantages**
- **Shatters Inheritance:** Allows you to build highly modular, decoupled architectures without deep inheritance trees.
- **Reusability:** Property delegates (`lazy`, `observable`, SharedPreferences delegates) extract complex memory/storage management into single, reusable lines of code.

**Disadvantages**
- **The "Magic" Factor:** Heavy use of custom property delegates can make code very hard to read for junior developers. If `val user = "Alice"` actually triggers a blocking network call under the hood because of a custom `by` delegate, you have hidden critical performance implications.
- **Allocation Overhead:** Property delegates create hidden objects. `val x by lazy { 5 }` allocates a `Lazy` object wrapper. In a tight loop or a RecyclerView, allocating thousands of hidden delegate objects will cause Garbage Collection churn.

## Failure Modes

- **Delegating to `var` parameters:**
  ```kotlin
  // BAD: The delegate is a 'var'. 
  class Screen(var tracker: Analytics) : Analytics by tracker
  
  val myTracker = Firebase()
  val screen = Screen(myTracker)
  
  // If I change the tracker later...
  screen.tracker = Mixpanel() 
  // BUG: The delegation is permanently locked to the INITIAL 'myTracker'. 
  // It will NOT forward calls to Mixpanel!
  ```
  *(Fix: The compiler captures the delegate instance at initialization time. Changing the reference later does not update the delegation routing. Always use `val` for delegate parameters).*
- **Hidden Blocking Calls:** Creating a property delegate `var userToken by EncryptedSharedPreferences()`. Every time the developer reads `userToken`, the app performs synchronous disk I/O, dropping frames on the UI thread. *(Fix: Property delegates should be fast memory access. Disk/Network logic should be explicitly called via suspend functions, not hidden behind variable assignment).*

## Staff Engineer Thinking

When reviewing code, a Staff engineer looks for Composition opportunities:

1.  **Is this a "BaseViewModel"?** If I see a PR introducing `BaseViewModel`, `BaseFragment`, or `BaseActivity`, I immediately request a refactor. Inheritance is a rigid, single-parent constraint. I will demand the developer extract the common logic into an interface and use Class Delegation to compose the behaviors together.
2.  **Are we abusing `lazy`?** `lazy` is great for heavy initialization. But if I see `val name by lazy { "Alice" }`, I know the developer doesn't understand the memory allocation cost of the `Lazy` wrapper. I will enforce raw assignments for cheap primitives.
3.  **Is the magic hidden?** If a custom property delegate accesses the network or database, I require it to be named explicitly to warn the caller. `val config by RemoteConfigDelegate()` is better than `val config by get()`.

## Common Misconceptions

- **"Delegation replaces inheritance."** No. Inheritance is for "Is-A" relationships (A `Dog` Is-A `Animal`). Delegation is for "Has-A" relationships (A `Car` Has-A `Engine`). Delegation forces you to model your domain correctly.
- **"I can delegate to an Abstract Class."** False. The `by` keyword for class delegation *only* works with Interfaces. You cannot write `class Dog : Animal by Mammal()` if `Animal` is an abstract class.

## Probing Questions

1.  What is the difference between "Class Delegation" and "Property Delegation" in Kotlin?
2.  Explain the "Fragile Base Class" problem in Java and how Kotlin's `by` keyword solves it by encouraging Composition.
3.  Why can you only use the `by` keyword for Class Delegation with an `interface` and not an `abstract class`?
4.  Under the hood, what bytecode does the Kotlin compiler generate when you use `val name by lazy { "Alice" }`?
5.  Why is it dangerous to use a `var` as the target of Class Delegation (e.g., `class A(var b: B) : Interface by b`)?
6.  Describe a scenario where using a custom Property Delegate to read from SharedPreferences could cause UI jank (dropped frames).
7.  How does Class Delegation allow you to eliminate deep inheritance hierarchies like `BaseViewModel` or `BaseActivity`?
8.  What is the `observable` property delegate in Kotlin, and how might it be used in a UI architecture?
9.  Why does using `by lazy` for a simple primitive (like an `Int`) actually decrease performance compared to a standard assignment?
10. If you declare a custom Property Delegate, what are the names of the two operator functions you must implement? (Hint: `getValue` and `setValue`).

## Further Reading

- [`make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md) — Using delegation to strictly control state mutation.
- [`../principles/composition-over-inheritance.md`](../principles/composition-over-inheritance.md) — The architectural pattern powered by delegation.
