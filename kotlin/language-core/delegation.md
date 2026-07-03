# Delegation

> Delegation in Kotlin is how you do "composition over inheritance" without writing 30 lines of forwarding boilerplate. It's also how you wire up almost every modern Android idiom: `by viewModels()`, `by activityViewModels()`, `by remember`, `by mutableStateOf`, `by lazy`. Understanding `by` at staff level means knowing the *runtime cost* (allocations, thread-safety modes), the *traps* (delegating to a `var`, blocking I/O hidden inside a property), and the *full Android delegate vocabulary*.

---

## Overview

Delegation is a structural pattern: instead of doing the work itself, an object hands the work to another object — the **delegate**. Kotlin makes this a first-class language feature via the `by` keyword.

Two forms:

| Form | Syntax | What it does |
|---|---|---|
| **Class delegation** | `class Wrapper : Logger by realLogger` | Auto-forwards every `Logger` method to `realLogger` |
| **Property delegation** | `val x: T by SomeDelegate()` | Hooks `get` (and optionally `set`) to a delegate object |

```kotlin
// Class delegation
class TimestampedLogger(real: Logger) : Logger by real {
    override fun log(msg: String) = real.log("${now()} $msg")
}

// Property delegation
val heavyDb: Db by lazy { Room.databaseBuilder(...).build() }
```

---

## Why It Matters (Android Context)

**Why composition over inheritance?** Joshua Bloch, *Effective Java* Item 18: subclassing concrete classes couples your code to their implementation. Java updates `ArrayList`'s internal logic — your `LoggingArrayList` breaks. Composition avoids this, but Java forces you to write the forwarding methods by hand. Kotlin's `by` eliminates the boilerplate.

**Android specifics.** Property delegation is everywhere in modern Android:

- `by viewModels()` — gets a ViewModel scoped to the Fragment/Activity.
- `by activityViewModels()` — gets a ViewModel scoped to the host Activity.
- `by hiltNavGraphViewModels(R.id.graph)` — scoped to a nav graph.
- `by remember { mutableStateOf(...) }` — Compose state holder.
- `var name by rememberSaveable { mutableStateOf("") }` — persists across config change.
- Hilt's `@Inject lateinit var`, Compose's `LocalContext.current`, navArgs() — delegation under the hood.

Knowing the delegate vocabulary is required to read Android code fluently.

---

## First Principles

1. **`by` for interfaces only** (class delegation). You cannot `class Dog : Animal by Mammal()` if `Animal` is abstract.
2. **Delegate must implement `getValue` / `setValue` operators** (property delegation). Easiest path: implement `ReadOnlyProperty<T, V>` or `ReadWriteProperty<T, V>`.
3. **Property delegation rewrites bytecode** — a hidden `xxx$delegate` field holds the delegate; reads route through it.
4. **The delegate reference is captured at init time** — changing it later doesn't change the routing (huge trap; see below).

---

## Class Delegation

### The pattern

```kotlin
interface Logger {
    fun log(msg: String)
    fun flush()
}

class FileLogger(private val file: File) : Logger {
    override fun log(msg: String) = file.appendText("$msg\n")
    override fun flush() = file.flush()
}

class TimestampedLogger(private val real: Logger) : Logger by real {
    override fun log(msg: String) = real.log("${nowIso()} $msg")
    // flush() is auto-forwarded to `real`
}
```

The compiler generates a synthetic `flush()` on `TimestampedLogger` that just calls `real.flush()`. You can override any method you want (like `log`) and get the rest for free.

### When to use it

- You want to **wrap** a service (add logging, retries, validation) without subclassing.
- You want to **mix in** multiple behaviors from interfaces.
- You want to avoid the Fragile Base Class problem.

### Mixin via multiple delegates

```kotlin
interface Cache<K, V> { fun get(key: K): V?; fun put(key: K, value: V) }
interface Logger { fun log(msg: String) }

class CachingService<K, V>(
    cache: Cache<K, V>,
    logger: Logger,
) : Cache<K, V> by cache, Logger by logger
```

`CachingService` is now both a Cache and a Logger, with zero boilerplate. Pure composition.

### Diamond / overlap gotcha

If two delegated interfaces have the same method, the compiler forces you to disambiguate:

```kotlin
interface A { fun ping() }
interface B { fun ping() }

class Both(a: A, b: B) : A by a, B by b {
    override fun ping() {
        // must override explicitly when both have the same signature
        a.ping(); b.ping()
    }
}
```

### Trap: delegating to a `var`

```kotlin
// BAD
class Screen(var tracker: Analytics) : Analytics by tracker

val s = Screen(Firebase())
s.tracker = Mixpanel()
s.logEvent(...)   // still calls Firebase! The delegate reference was captured at init
```

The compiler captures the *value* of `tracker` at construction time into the hidden delegate field. Reassigning `tracker` doesn't update the routing. **Always use `val` for delegate parameters.**

If you actually need dynamic re-binding, don't use `by`. Write a manual forwarder:

```kotlin
class Screen(var tracker: Analytics) : Analytics {
    override fun logEvent(name: String) = tracker.logEvent(name)
}
```

---

## Property Delegation

### Built-in delegates

| Delegate | Use case | Notes |
|---|---|---|
| `by lazy { }` | Expensive immutable init | Computed on first read; cached |
| `by Delegates.observable(initial) { ... }` | Side-effect on every set | Fires *after* assignment |
| `by Delegates.vetoable(initial) { ... }` | Conditionally allow set | Returns `Boolean`; rejects if `false` |
| `by Delegates.notNull<T>()` | Non-null `var` for primitives | Throws if read before init (like `lateinit`) |
| `by map` / `by mutableMap` | Property reads pull from `Map<String, Any?>` | Useful for dynamic objects |

### `by lazy` modes

The default `lazy { }` is thread-safe — uses `LazyThreadSafetyMode.SYNCHRONIZED`. For UI code that's always single-threaded, the synchronization is wasted work.

```kotlin
val a by lazy { compute() }                                  // SYNCHRONIZED (default)
val b by lazy(LazyThreadSafetyMode.PUBLICATION) { compute() } // may compute multiple times across threads but only one wins
val c by lazy(LazyThreadSafetyMode.NONE) { compute() }       // no sync; only safe on single thread
```

| Mode | Thread-safe | Cost | When to use |
|---|---|---|---|
| `SYNCHRONIZED` | Yes (`@Volatile` + `synchronized`) | Highest | Multi-thread access; default |
| `PUBLICATION` | "Safely published" — multiple threads may compute, but only one's result is used | Medium | Idempotent expensive computation called rarely |
| `NONE` | No | Lowest | Single-threaded contexts (UI thread); microbenchmarks |

A common Android pattern: properties on a ViewModel or Activity accessed only from the Main thread can use `NONE` for free perf:

```kotlin
val analytics by lazy(LazyThreadSafetyMode.NONE) { buildAnalytics() }
```

But measure first — the savings are real but small.

### `Delegates.observable` example

```kotlin
class FormViewModel {
    var name: String by Delegates.observable("") { _, old, new ->
        if (old != new) validate()
    }
}
```

Every time `name` is set, `validate()` runs *after* the assignment.

### `Delegates.vetoable` example

```kotlin
var positive: Int by Delegates.vetoable(0) { _, _, new ->
    new >= 0   // reject negatives
}

positive = 5    // OK; positive == 5
positive = -1   // rejected; positive still == 5
```

### `by map` example

```kotlin
class User(map: Map<String, Any?>) {
    val name: String  by map
    val age: Int      by map
}

val u = User(mapOf("name" to "Alice", "age" to 30))
u.name   // "Alice"
```

Useful when reading JSON into a flat object without writing a `data class` (rare in modern Android — prefer Moshi).

---

## Writing a Custom Delegate

The clean way is to implement `ReadOnlyProperty<T, V>` (for `val`) or `ReadWriteProperty<T, V>` (for `var`):

```kotlin
class Preference(
    private val prefs: SharedPreferences,
    private val key: String,
    private val defaultValue: String,
) : ReadWriteProperty<Any?, String> {

    override fun getValue(thisRef: Any?, property: KProperty<*>): String =
        prefs.getString(key, defaultValue) ?: defaultValue

    override fun setValue(thisRef: Any?, property: KProperty<*>, value: String) {
        prefs.edit { putString(key, value) }
    }
}

class Settings(prefs: SharedPreferences) {
    var theme: String by Preference(prefs, "theme", "system")
    var locale: String by Preference(prefs, "locale", "en")
}
```

Reading `settings.theme` triggers `getValue`; writing it triggers `setValue`. **But:** every read hits disk synchronously — see the failure mode below.

You can also write raw `operator fun getValue` / `setValue` without implementing the interface — works the same, but the interface form is clearer and IDE-discoverable.

### `provideDelegate` for one-time setup

If your delegate needs `KProperty` info at init time (e.g., to register the property name with a system), implement `provideDelegate`:

```kotlin
class Required<T>(private val source: Map<String, Any?>) : ReadOnlyProperty<Any?, T> {
    private lateinit var value: T

    operator fun provideDelegate(
        thisRef: Any?, property: KProperty<*>,
    ): ReadOnlyProperty<Any?, T> {
        @Suppress("UNCHECKED_CAST")
        value = (source[property.name]
            ?: error("Missing required: ${property.name}")) as T
        return this
    }

    override fun getValue(thisRef: Any?, property: KProperty<*>): T = value
}
```

`provideDelegate` is invoked once at property initialization (with the `KProperty` already available) and returns the actual delegate. This is how you do bind-once validation, registration, or expensive per-property setup.

---

## Android Property Delegates Worth Knowing

### `by viewModels()`

```kotlin
class CartFragment : Fragment() {
    private val vm: CartViewModel by viewModels()
}
```

What this does:

- Reads from the Fragment's `ViewModelStore`.
- On first read, creates a `CartViewModel` via the default factory.
- Caches it; subsequent reads (after rotation, etc.) return the same instance.
- Cleared when the Fragment is destroyed for real (not on rotation).

Under the hood: it's a property delegate whose `getValue` calls `ViewModelProvider(this).get(CartViewModel::class.java)`.

### `by activityViewModels()`

Like `viewModels()`, but scoped to the host Activity. Two fragments in the same activity get the **same** instance — the standard pattern for sharing state.

### `by hiltNavGraphViewModels(R.id.graph)`

Scoped to a nav-graph entry. ViewModel survives across all destinations within the graph but is cleared when the graph itself leaves the back stack.

### `by remember { mutableStateOf(initial) }` (Compose)

```kotlin
@Composable
fun Counter() {
    var count by remember { mutableStateOf(0) }
    Button(onClick = { count++ }) { Text("$count") }
}
```

Two delegates stacked:

- `remember { ... }` caches the value across recompositions.
- `by mutableStateOf(...)` is the property delegate — `getValue` reads `.value`, `setValue` writes `.value` and triggers recomposition.

### `by rememberSaveable { mutableStateOf("") }`

Same as `remember`, but the value is restored after process death via `SavedStateHandle`.

### `by argument()`, `by navArgs()`

```kotlin
class DetailFragment : Fragment() {
    private val args: DetailFragmentArgs by navArgs()
}
```

Reads typed arguments from the Fragment's `Bundle` via Safe Args generated code.

---

## How the Compiler Actually Implements This

```kotlin
class C {
    val name: String by lazy { "Alice" }
}
```

Becomes roughly:

```kotlin
class C {
    private val name$delegate: Lazy<String> = lazy { "Alice" }
    val name: String
        get() = name$delegate.getValue(this, this::name)
}
```

For `var`:

```kotlin
class C {
    var name: String by Preference(prefs, "name", "")
}
// becomes
class C {
    private val name$delegate = Preference(prefs, "name", "")
    var name: String
        get() = name$delegate.getValue(this, this::name)
        set(value) { name$delegate.setValue(this, this::name, value) }
}
```

Each delegated property allocates **one extra object** (the `Lazy` wrapper, or your `Preference` instance). Not free — see the perf note.

---

## Performance Notes

| Pattern | Allocation per use | Use sparingly when |
|---|---|---|
| `by lazy { 5 }` for a primitive | One `Lazy` wrapper per instance | Hot constructor paths, list items |
| `by lazy { ... }` in `RecyclerView.ViewHolder` | × number of holders | Initialize eagerly instead |
| `Delegates.observable` | One wrapper + listener invocation per set | Frequent setter (60 fps) |
| Custom delegate with `provideDelegate` | One delegate per property at init | Always fine (one-time cost) |
| Class delegation | Zero extra runtime cost vs manual forwarders | Always fine |

In a `RecyclerView.ViewHolder`, allocating a `Lazy<T>` per item across thousands of items adds up. A direct assignment is faster:

```kotlin
// SLOWER (per ViewHolder)
private val title: TextView by lazy { itemView.findViewById(R.id.title) }

// FASTER
private val title: TextView = itemView.findViewById(R.id.title)
```

(Better still: ViewBinding eliminates the question.)

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Delegated method calls stale instance | Delegated to a `var`; instance was reassigned | Use `val`; or manual forwarder if dynamic re-bind is needed |
| `ConcurrentModificationException` on `lazy` initialization | Default `SYNCHRONIZED` mode + reentrant access from same thread | Restructure to avoid re-entrance; or use `PUBLICATION` |
| UI jank when reading a property | Custom delegate does blocking I/O on the getter | Move I/O to a suspend function; name explicitly |
| `IllegalArgumentException: Class is missing` after rotation | `by viewModels()` used without proper factory for constructor args | Provide a `ViewModelProvider.Factory` or use Hilt's `by hiltViewModel()` |
| Two Fragments don't share state | Used `by viewModels()` instead of `by activityViewModels()` | Scope correctly |
| Compose recomposes infinitely | `by mutableStateOf` used inside `remember` block reading it back | Move read out of the side-effect closure |
| `lateinit` won't compile for `Int` | `lateinit` doesn't support primitives | Use `Delegates.notNull<Int>()` |
| `UninitializedPropertyAccessException` on `Delegates.notNull` | Property read before being set | Initialize before first read; or use `lateinit`-style alternative |
| Memory leak in singleton `by lazy { Application }` | Held context reference for app lifetime | Pass `Application` context, not `Activity`; or scope the delegate |
| Custom delegate name doesn't match property name | Forgot `provideDelegate` to capture `KProperty` | Implement `provideDelegate` to wire name |

---

## Staff Engineer Lens

When reviewing delegation usage, I look for:

1. **`BaseViewModel` / `BaseFragment` / `BaseActivity`.** Inheritance is fragile. Push to interface + class delegation. Most "base" classes are 2-3 cross-cutting concerns that should be composed in.
2. **Custom delegate with hidden I/O.** A custom `by Preference(...)` that reads disk every time the property is accessed is a UI-jank bomb. Either move to coroutines, cache, or name explicitly (`preferencesSync` not `preferences`).
3. **`by lazy` for cheap values.** `val x by lazy { 5 }` allocates a `Lazy` wrapper to defer a trivial computation. Push for direct assignment.
4. **`by lazy` in ViewHolders / hot paths.** Adds N allocations for N items. Eager-init or use binding.
5. **`by viewModels()` vs `by activityViewModels()` confusion.** Shared state across fragments needs activity scope. Misuse causes mysterious state-reset bugs on tab switch.
6. **Compose state without `remember`.** A bare `var x by mutableStateOf(0)` inside a Composable resets every recomposition. Almost always wants `remember { mutableStateOf(0) }`.
7. **Class delegation with a `var` source.** Captures the initial reference; reassign is silently ignored. Force `val` or manual forwarder.
8. **Diamond ambiguity** — when two delegated interfaces share a method, ensure the override is intentional, not "first one wins."

---

## Common Misconceptions

- **"Delegation replaces inheritance."** No. Inheritance is for "is-a"; delegation is for "has-a." A `Car` *has* an engine; it isn't one.
- **"You can delegate to an abstract class."** False. Class delegation only works with interfaces. Abstract classes can't be the delegation target.
- **"`by lazy` is free."** It allocates a `Lazy<T>` wrapper. Cheap, but × thousands of instances adds up.
- **"`by lazy` is thread-safe so I can use it anywhere."** True by default — but the synchronization isn't free, and there are modes (PUBLICATION, NONE) for hot paths.
- **"`Delegates.observable` fires before assignment."** No. After. The callback receives both old and new; the value is already set when called.
- **"`by viewModels()` creates a new ViewModel on every call."** No. The delegate returns the cached instance from the `ViewModelStore` after the first read.
- **"The delegate object is shared across instances."** False (for normal property delegates) — each instance of the containing class gets its own delegate object via `xxx$delegate`. Only `object`-typed delegates share state.

---

## Probing Questions

1. Walk through what the compiler generates for `val name: String by lazy { "Alice" }`. Where does the value live? When does the lambda run?
2. What are the three `LazyThreadSafetyMode` options? When would you choose each one?
3. You have a class implementing two interfaces via class delegation, and both interfaces have a method `fun ping()`. What does the compiler force you to do?
4. Why is `class Screen(var tracker: Analytics) : Analytics by tracker` a bug? Walk through the failure scenario.
5. Custom delegate: implement `ReadWriteProperty<Any?, String>` for a SharedPreferences-backed string. What's the perf concern in production?
6. Compare `by viewModels()` vs `by activityViewModels()` vs `by hiltNavGraphViewModels()`. When do you pick each?
7. Why does `by lazy { 5 }` for a single `Int` field harm performance vs `val x = 5`?
8. Why does the `by` keyword (class delegation) only work with interfaces, not abstract classes?
9. In Compose, what's the difference between `var x by mutableStateOf(0)` inside vs outside a `remember { }` block?
10. Walk through how `provideDelegate` differs from a normal delegate. When do you need it?
11. `var theme by Delegates.observable("light") { _, old, new -> ... }` — does the callback fire before or after the assignment? How do you reject a value instead?
12. Why does `lateinit` not work with `Int`? What's the delegation-based alternative?

---

## Further Reading

- [`null-safety.md`](null-safety.md) — `lateinit` vs `by lazy` vs nullable choice.
- [`data-classes.md`](data-classes.md) — when you want value semantics, not delegation.
- [`coroutines.md`](../coroutines-and-flow/coroutines.md) — async patterns instead of hiding I/O behind property delegates.
- [`../android/architecture/viewmodel.md`](../../android/architecture/viewmodel.md) — `by viewModels()` mechanics.
- [`../android/compose/recomposition-and-state.md`](../../android/compose/recomposition-and-state.md) — `by remember { mutableStateOf(...) }` deep dive.
- [`../android/data-and-di/dependency-injection.md`](../../android/data-and-di/dependency-injection.md) — Hilt-injected `lateinit var` vs delegated properties.
- [`../principles/composition-over-inheritance.md`](../../principles/composition-over-inheritance.md) — the design philosophy delegation serves.
- [Kotlin Docs — Delegation](https://kotlinlang.org/docs/delegation.html) — class delegation reference.
- [Kotlin Docs — Delegated properties](https://kotlinlang.org/docs/delegated-properties.html) — property delegation reference.
- [Effective Java Item 18](https://www.amazon.com/Effective-Java-Joshua-Bloch/dp/0134685997) — "Favor composition over inheritance" — the canonical argument.
- [Roman Elizarov — "Delegates and property delegates"](https://elizarov.medium.com/) — Kotlin lead engineer's notes on the design.
