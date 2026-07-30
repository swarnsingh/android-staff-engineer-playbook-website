# Generics

> Generics are how Android avoids 17 copies of `ArrayList`. `Result<T>`, `ViewModelFactory<T>`, `RecyclerView.Adapter<T : ViewHolder>`, `LazyColumn { items<T>(...) }` — every Android architectural primitive is generic. Staff-level mastery is knowing the JVM's type-erasure rules, when `reified` is the workaround, and how variance (`in`/`out`) interacts with generic hierarchies — because the moment you write `Result<Success>` and try to assign it to `Result<Outcome>`, you're in deep water.

---

## Overview

A generic type parameter is a placeholder for a type. The compiler enforces consistency at compile time:

```kotlin
class Box<T>(val item: T)

val intBox: Box<Int> = Box(42)
val strBox: Box<String> = Box("hi")

intBox.item.length    // ❌ compile error — Int has no .length
strBox.item.length    // ✅ smart-typed as String
```

The mental model: `<T>` is "for any T, here is the contract."

---

## Why It Matters (Android Context)

Pre-generics Java collections held raw `Object`:

```java
ArrayList list = new ArrayList();
list.add("hello");
list.add(42);
String s = (String) list.get(1);   // ClassCastException at runtime
```

Generics shifted this risk from runtime to compile time. Modern Android relies on this everywhere:

- `RecyclerView.Adapter<VH : ViewHolder>` — your VH type flows through every call.
- `StateFlow<T>` — emissions and collectors agree on type.
- `Repository<User>` — pluggable data sources.
- `Result<T>` / `ApiResponse<T>` — typed success/error envelopes.
- `Comparator<T>` — sortable collections.
- `Class<T>` / `KClass<T>` — type tokens for serialization.

A weak grasp of generics turns into runtime crashes that look like "this can't happen."

---

## First Principles

1. **Type parameters are compile-time only.** The JVM doesn't see them at runtime — that's type erasure.
2. **Bounded generics restrict.** `<T : Comparable<T>>` says "T must be comparable to itself."
3. **`where` clauses combine bounds.** `<T> where T : A, T : B`.
4. **Variance** (`in`/`out`) controls how generic parameters interact with inheritance — covered in [`variance.md`](variance.md).
5. **`reified`** + `inline` is Kotlin's escape from JVM erasure.

---

## Generic Functions

```kotlin
fun <T> singletonList(item: T): List<T> = listOf(item)

fun <T : Comparable<T>> max(a: T, b: T): T = if (a > b) a else b

fun <T> List<T>.swapInPlace(i: Int, j: Int): MutableList<T> {
    val mutable = this.toMutableList()
    val tmp = mutable[i]; mutable[i] = mutable[j]; mutable[j] = tmp
    return mutable
}
```

Type parameters declared before the function name. Used in parameter types, return type, and (in extension functions) the receiver.

### Multiple parameters

```kotlin
fun <K, V> mapOf(vararg pairs: Pair<K, V>): Map<K, V> = ...
fun <K, V, R> Map<K, V>.mapValues(transform: (V) -> R): Map<K, R> = ...
```

By convention: `T`, `R` for return, `E` for element, `K`/`V` for key/value.

---

## Bounded Generics

### Upper bound

```kotlin
class JsonParser<T : Any>             // T cannot be nullable
class Repo<T : Entity>                // T must extend Entity
fun <T : Number> sum(list: List<T>)   // T must extend Number
```

Without the bound, the compiler defaults to `T : Any?` — including nullable.

### `where` clause for multiple bounds

```kotlin
fun <T> validate(value: T): Boolean
    where T : Comparable<T>,
          T : CharSequence
{
    return value.length > 0 && value > "minimum"
}
```

Multiple constraints, all must hold.

### Common Android upper bounds

| Bound | Use case |
|---|---|
| `T : Any` | Exclude null; required for type-token reflection |
| `T : Comparable<T>` | Sortable items |
| `T : Number` | Numeric collections |
| `T : Parcelable` | Items that survive process death |
| `VH : RecyclerView.ViewHolder` | RecyclerView adapters |
| `T : ViewModel` | Generic ViewModel factories |
| `T : Activity` | Type-safe `Intent` builders |

---

## Type Erasure — The Core Constraint

Kotlin runs on the JVM. The JVM erases generic types in bytecode. **At runtime, `List<String>` and `List<Int>` are the same class.**

```kotlin
val strList = listOf("a", "b")
val intList = listOf(1, 2)

println(strList::class.java)    // class kotlin.collections.EmptyList
println(intList::class.java)    // class kotlin.collections.EmptyList (same!)
strList::class.java == intList::class.java   // true
```

### What you CAN'T do because of erasure

```kotlin
fun checkType(x: Any) {
    if (x is List<String>) { ... }   // ❌ compile error: erased
}

inline fun <T> create(): T {
    return T()                       // ❌ compile error: erased
}

fun <T> classOf(): Class<T> {
    return T::class.java             // ❌ compile error: erased
}
```

### What you CAN do

```kotlin
if (x is List<*>) { ... }                       // ✅ star projection
val s = x as? String ?: return                  // ✅ casting concrete types
inline fun <reified T> classOf(): Class<T> =    // ✅ reified
    T::class.java
```

### Star projection (`*`)

When you don't know or don't care what `T` is at runtime:

```kotlin
fun describe(list: List<*>) {
    println("size=${list.size}")
    val first = list.firstOrNull()    // type is Any?
    // can read as Any?, cannot safely write
}
```

`List<*>` is like `List<out Any?>` for reads, `List<in Nothing>` for writes — i.e., read-as-`Any?`, can't write at all.

---

## `reified` — Escaping Erasure with `inline`

`inline` functions are copy-pasted at every call site. The compiler can preserve the type parameter because there are no longer "uses" of `T` — only specific specialized calls.

```kotlin
inline fun <reified T> Gson.fromJson(json: String): T =
    fromJson(json, T::class.java)

val user: User = gson.fromJson("""{"id": 1}""")    // T is known concretely
```

Without `reified`, you'd write:

```kotlin
fun <T> Gson.fromJson(json: String, clazz: Class<T>): T = ...
val user: User = gson.fromJson(json, User::class.java)    // verbose
```

### When `reified` works

- The function **must be `inline`** — the compiler needs to copy the body into the call site.
- You can use `T::class`, `T::class.java`, `is T`, `as T` inside the body.

### When `reified` doesn't work

- Lambda parameters can't easily be reified.
- You can't store a reified `T` as a field — only use it locally.
- Recursion across reified functions has limits.

### Why this matters in Android

```kotlin
// Generic Intent builder
inline fun <reified A : Activity> Context.start(
    builder: Intent.() -> Unit = {}
) {
    val intent = Intent(this, A::class.java).apply(builder)
    startActivity(intent)
}

// Call site
context.start<DetailActivity> {
    putExtra("id", productId)
}

// Generic ViewModel factory
inline fun <reified VM : ViewModel> Fragment.viewModelFactory(
    noinline create: () -> VM
): Lazy<VM> = viewModels {
    object : ViewModelProvider.Factory {
        override fun <T : ViewModel> create(modelClass: Class<T>): T {
            @Suppress("UNCHECKED_CAST")
            return create() as T
        }
    }
}
```

`reified` makes the call sites elegant. Without it, every caller would pass `VM::class.java` manually.

---

## Type Tokens — The Reflection Workaround

If you need *generic-of-generic* type info at runtime (`List<User>` not just `List`), even `reified` isn't enough. You need a type token.

```kotlin
// Moshi
val type = Types.newParameterizedType(List::class.java, User::class.java)
val adapter = moshi.adapter<List<User>>(type)

// Gson (less safe)
val type = object : TypeToken<List<User>>() {}.type
val users: List<User> = gson.fromJson(json, type)
```

`object : TypeToken<List<User>>() {}` is the anonymous-subclass trick: by extending `TypeToken<T>`, the generic parameter is captured in the class file's `Signature` attribute, which reflection can read at runtime.

---

## Variance — `in`, `out`, and Why `List<Dog>` Isn't `List<Animal>`

Without explicit variance, generic types are **invariant**. `Producer<Dog>` and `Producer<Animal>` are unrelated, even if `Dog : Animal`.

```kotlin
open class Animal
class Dog : Animal()

val dogs: MutableList<Dog> = mutableListOf()
val animals: MutableList<Animal> = dogs    // ❌ compile error
```

Why? Because if it compiled, you could do `animals.add(Cat())` — corrupting `dogs`.

### `out T` (covariance) — for producers

```kotlin
interface Source<out T> {
    fun next(): T
}

val dogSource: Source<Dog> = ...
val animalSource: Source<Animal> = dogSource    // ✅ OK with `out`
```

`out T` means "T only appears in *output* (return) positions." Safe to read; can't write.

### `in T` (contravariance) — for consumers

```kotlin
interface Sink<in T> {
    fun accept(item: T)
}

val animalSink: Sink<Animal> = ...
val dogSink: Sink<Dog> = animalSink    // ✅ OK with `in`
```

`in T` means "T only appears in *input* (parameter) positions." Safe to write; can't read.

### Real-world examples

- `List<out T>` — read-only, covariant.
- `MutableList<T>` — read and write, invariant.
- `Comparator<in T>` — `Comparator<Animal>` works as `Comparator<Dog>`.
- `Flow<out T>` — covariant; collector receives `T`.
- `Function1<in P, out R>` — `(Animal) -> Number` works as `(Dog) -> Int`.

Full deep dive in [`variance.md`](variance.md).

---

## Generic Constraints — Use-Site Projections

If the *declaration* doesn't specify variance, you can apply it at the use site:

```kotlin
// MutableList is invariant by declaration.
// At use site, we read out without writing in:
fun copy(from: MutableList<out Number>, to: MutableList<Number>) {
    for (item in from) to.add(item)
    // from.add(...)    ← compile error: 'out' position
}
```

This is Java's `? extends T` / `? super T` syntax in disguise.

---

## Common Android Patterns

### Generic ApiResponse / Resource

```kotlin
sealed interface Resource<out T> {
    data object Loading : Resource<Nothing>
    data class Success<T>(val data: T) : Resource<T>
    data class Failure(val error: Throwable) : Resource<Nothing>
}

suspend fun <T> safeApi(call: suspend () -> T): Resource<T> = try {
    Resource.Success(call())
} catch (e: Exception) {
    if (e is CancellationException) throw e
    Resource.Failure(e)
}

// Usage
val userR: Resource<User> = safeApi { api.getUser() }
```

### RecyclerView adapters

```kotlin
abstract class BaseAdapter<T, VH : RecyclerView.ViewHolder>(
    diffCallback: DiffUtil.ItemCallback<T>,
) : ListAdapter<T, VH>(diffCallback)

class CartAdapter : BaseAdapter<CartItem, CartViewHolder>(CartDiff) {
    override fun onBindViewHolder(holder: CartViewHolder, position: Int) {
        holder.bind(getItem(position))
    }
}
```

`<T, VH : ViewHolder>` enforces matched item + holder types.

### Compose generic Composables

```kotlin
@Composable
fun <T> LazyList(
    items: List<T>,
    key: (T) -> Any,
    content: @Composable (T) -> Unit
) {
    LazyColumn {
        items(items, key = key) { content(it) }
    }
}

LazyList(products, key = { it.id }) { ProductRow(it) }
```

The `key = (T) -> Any` callback is generic — caller decides what stable identity looks like.

### Hilt assisted-inject with generics

```kotlin
@HiltViewModel(assistedFactory = DetailViewModel.Factory::class)
class DetailViewModel @AssistedInject constructor(
    @Assisted val productId: String,
    private val repo: ProductRepo,
) : ViewModel() {
    @AssistedFactory
    interface Factory {
        fun create(productId: String): DetailViewModel
    }
}

// Composable
val factory = EntryPointAccessors.fromActivity<DetailEntryPoint>(activity)
val vm: DetailViewModel = viewModel(factory = ...) { factory.create(id) }
```

### Service locators / DI containers

```kotlin
inline fun <reified T : Any> ServiceLocator.get(): T {
    return registry[T::class.java] as T
        ?: error("Service ${T::class.java.simpleName} not registered")
}

val analytics: Analytics = locator.get()
```

---

## Java Interop — `@JvmSuppressWildcards` and Friends

Kotlin's variance generates Java wildcards when crossing the interop boundary. Sometimes you need to suppress them:

```kotlin
// Kotlin signature: List<out T>
// Java sees: List<? extends T>  ← wildcard from `out`

@JvmSuppressWildcards
fun process(list: List<Animal>) { ... }
// Java now sees: List<Animal>  (no wildcard)

fun produce(): List<@JvmWildcard Animal> = ...
// Forces a wildcard even when Kotlin wouldn't
```

Mostly relevant when shipping a Kotlin SDK that needs clean Java consumption. See `library-versioning.md` for SDK API concerns.

---

## `@UnsafeVariance` — The Escape Hatch

```kotlin
interface Producer<out T> {
    fun produce(): T
    fun consume(@UnsafeVariance item: T): Unit   // ← T in 'in' position
}
```

Tells the compiler "trust me, I know this looks variance-unsafe, but it's OK in my implementation." Use sparingly. The standard library uses this for `List.contains(element: @UnsafeVariance E): Boolean`.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `ClassCastException` from unchecked cast | `as` cast of erased generic | Use `reified` or pass a `Class<T>` explicitly |
| `is List<String>` fails to compile | Erasure | `is List<*>` then check element types manually |
| Cannot instantiate `T()` inside generic class | Erasure — `T::class.java` unavailable | Pass a `Class<T>` constructor arg or use `reified` (which needs `inline`) |
| Shadowed type parameter | `fun <T> bar(item: T)` inside `class Foo<T>` | Remove the inner `<T>` or rename |
| `MutableList<Dog>` not assignable to `MutableList<Animal>` | Invariance is correct | Use `MutableList<out Animal>` (read-only) or copy |
| Gson silently returns `List<LinkedTreeMap>` instead of `List<User>` | Type token lost | Use Moshi (compile-time codegen) or `TypeToken` |
| Java consumer gets verbose wildcard signatures | Default `out` becomes `? extends T` in bytecode | `@JvmSuppressWildcards` on the API |
| `inline fun` becomes huge | Body copied at every call site | Smaller body; or extract non-inline helpers |
| Hilt fails to inject generic type | Erasure — Dagger sees raw `Repo`, not `Repo<User>` | Use `@Qualifier` or non-generic wrapper |
| `reified` doesn't work | Forgot `inline` | Add `inline` and re-`reified` |
| Compose recomposes more than expected with generic stable type | Inferred unstable | Annotate the generic class `@Immutable` |
| `Bundle` extras with generics | Erasure | Use Parcelize + sealed wrappers, or kotlinx serialization |

---

## Staff Engineer Lens

When reviewing generics, I look for:

1. **Unbounded `<T>` where `<T : Any>` is correct.** A nullable type parameter is rarely intended; the bound forces nullability into a separate `T?` decision.
2. **Generic class with `T::class.java` inside non-`reified` non-`inline` context.** Won't compile — but I've seen PRs that tried. Push to `reified` + `inline`.
3. **`@Suppress("UNCHECKED_CAST")` without justification.** Each one is a runtime crash possibility. Either fix or document why it's safe.
4. **Five-parameter generic functions.** `<A, B, C, D, E>` is a code smell. Usually means too many concerns crammed into one function.
5. **"Generics everywhere" syndrome.** A class only used with `String` doesn't need to be `class X<T>`. Rule of Three: stay concrete until three real generic uses appear.
6. **`Class<*>` API.** Use `KClass<*>` or `KClass<out Foo>` to be Kotlin-idiomatic and let the compiler help.
7. **Star projection where covariance would work.** `List<*>` is read-as-`Any?`. If you can refactor to `List<out T>` and read as `T`, do so.
8. **Java interop wildcards leaking through SDK boundary.** `@JvmSuppressWildcards` on the public API surface.

---

## Common Misconceptions

- **"Generics make the app larger or slower."** False on JVM. Type erasure means zero runtime cost. (C++ templates do bloat; the JVM does not.)
- **"`List<Dog>` is a `List<Animal>` because Dog is an Animal."** **False — that's invariance.** Variance (`in`/`out`) is opt-in.
- **"`reified` works on any generic function."** Only on `inline` functions.
- **"`<T : Any?>` is the same as `<T>`."** True for bounds, false in practice — `<T : Any>` (no `?`) excludes null.
- **"I can use `T::class.java` in a non-inline generic class."** No. Erasure prevents it. Pass `Class<T>` as a constructor arg.
- **"`List<*>` and `List<Any?>` are the same."** `List<*>` is read-only at the element type; `List<Any?>` accepts any input. Subtle but important.
- **"All generic functions should be `reified`."** No. Reified forces inline; inline bloats bytecode if the body is large.

---

## Probing Questions

1. Walk through what bytecode the JVM sees for `List<String>` vs `List<Int>`. Why are they identical, and what does the IDE actually check?
2. Why does `if (x is List<String>)` fail to compile? How do you check at runtime if `x` is a list of strings?
3. Write a `reified` extension that deserializes JSON to `T`. Why does it have to be `inline`?
4. Explain the `<T : Any>` constraint. When is `<T>` (no bound) wrong?
5. You need `Class<T>` inside a non-inline generic class. What's the workaround?
6. Why is `MutableList<Dog>` not assignable to `MutableList<Animal>` even though `Dog : Animal`? How does `out` fix it for read-only cases?
7. The `@Suppress("UNCHECKED_CAST")` warning — when is it dangerous and when is it acceptable?
8. Explain `<T> where T : Comparable<T>, T : Iterable<T>`. What does each bound contribute?
9. Walk through how `object : TypeToken<List<User>>() {}` captures the generic at runtime when normal erasure would lose it.
10. `inline fun <reified T> Context.start(...)` for starting an Activity — what does this gain over passing `T::class.java`?
11. Hilt fails to inject `Repo<User>` because Dagger sees the raw type. How do you work around it?
12. Compose generic `LazyList<T>` — what makes the inferred stability *correct* vs *wrong* for the parameter `T`?

## Answer Key

1. **Walk through what bytecode the JVM sees for `List<String>` vs `List<Int>`. Why are they identical, and what does the IDE actually check?**
   The JVM sees both as the raw type `java.util.List` due to type erasure; the generic parameters are stripped at compilation. The IDE and compiler check the type safety at compile time using the generic metadata, ensuring you only add `String`s to the first and `Int`s to the second, and inserting implicit casts when retrieving items.
2. **Why does `if (x is List<String>)` fail to compile? How do you check at runtime if `x` is a list of strings?**
   It fails because the `<String>` type argument is erased at runtime, so the JVM cannot verify if the list contains strings. You can check `if (x is List<*>)` to verify it's a list, but you must manually iterate and check the type of its elements (`x.all { it is String }`) to verify its contents.
3. **Write a `reified` extension that deserializes JSON to `T`. Why does it have to be `inline`?**
   `inline fun <reified T> fromJson(json: String): T = gson.fromJson(json, T::class.java)`. It must be `inline` because the compiler needs to copy the function body to every call site. By doing so, it can replace `T::class.java` with the actual concrete type used at that specific call site, bypassing runtime type erasure.
4. **Explain the `<T : Any>` constraint. When is `<T>` (no bound) wrong?**
   `<T : Any>` sets the upper bound of `T` to the non-nullable `Any`, ensuring `T` can never be a nullable type. Without it, the default bound is `<T : Any?>`, which allows nulls. Using unbounded `<T>` is wrong when your generic class or function cannot safely handle null values or requires a non-null type for reflection.
5. **You need `Class<T>` inside a non-inline generic class. What's the workaround?**
   You must require the caller to pass the `Class<T>` explicitly as a constructor parameter, storing it as a field for runtime use.
6. **Why is `MutableList<Dog>` not assignable to `MutableList<Animal>` even though `Dog : Animal`? How does `out` fix it for read-only cases?**
   `MutableList` is invariant because allowing the assignment would let you write an `Animal` (like a `Cat`) into a list that is supposed to only hold `Dog`s, corrupting it. Using `out Animal` (covariance) makes the list read-only; since you can only extract `Animal`s and cannot insert anything, it's safe to assign `List<Dog>` to `List<out Animal>`.
7. **The `@Suppress("UNCHECKED_CAST")` warning — when is it dangerous and when is it acceptable?**
   It is dangerous when the cast might fail at runtime due to type erasure (e.g., casting a raw `List` to `List<User>`), leading to a `ClassCastException` later when reading an element. It is acceptable when you can logically prove the cast is safe (e.g., inside a `ViewModelProvider.Factory` where you checked the class type, or when using type tokens).
8. **Explain `<T> where T : Comparable<T>, T : Iterable<T>`. What does each bound contribute?**
   This `where` clause requires `T` to satisfy *both* bounds simultaneously. `T` must be comparable to itself (allowing sorting or comparisons) AND `T` must be iterable (allowing it to be looped over in a `for` loop).
9. **Walk through how `object : TypeToken<List<User>>() {}` captures the generic at runtime when normal erasure would lose it.**
   Creating an anonymous subclass of `TypeToken` causes the Java compiler to embed the specific generic superclass signature (`TypeToken<List<User>>`) into the compiled `.class` file's metadata. At runtime, the `TypeToken` base class uses reflection (`getClass().getGenericSuperclass()`) to read this preserved metadata, bypassing standard instance-level type erasure.
10. **`inline fun <reified T> Context.start(...)` for starting an Activity — what does this gain over passing `T::class.java`?**
    It dramatically cleans up the call site. Instead of writing `start(DetailActivity::class.java)`, the caller simply writes `start<DetailActivity>()`, which is more idiomatic and concise, especially in DSLs.
11. **Hilt fails to inject `Repo<User>` because Dagger sees the raw type. How do you work around it?**
    You can use `@Qualifier` annotations to differentiate the bindings, or wrap the generic type in a concrete non-generic class (e.g., `class UserRepo @Inject constructor(...) : Repo<User>`), which Dagger can easily identify and inject.
12. **Compose generic `LazyList<T>` — what makes the inferred stability *correct* vs *wrong* for the parameter `T`?**
    If `T` is an interface or from an external module, Compose compiler assumes it is Unstable, causing unnecessary recompositions. If you know `T` is actually immutable or stable, the inferred instability is "wrong" for performance. You fix it by annotating the generic class representing `T` with `@Immutable` / `@Stable`, or by wrapping it in a stable container.

---

## Further Reading

- [`variance.md`](variance.md) — `in`/`out` deep dive.
- [`reified-types.md`](../compiler-features/reified-types.md) — `reified` mechanics in depth.
- [`inline-functions.md`](../compiler-features/inline-functions.md) — `inline` rules that enable `reified`.
- [`sealed-classes.md`](../language-core/sealed-classes.md) — generic sealed hierarchies (`Resource<out T>`).
- [`data-classes.md`](../language-core/data-classes.md) — generic data classes (`Pair<A, B>`).
- [`null-safety.md`](../language-core/null-safety.md) — `<T : Any>` for non-null type params.
- [`../android/architecture/viewmodel.md`](../../android/architecture/viewmodel.md) — generic ViewModel factories.
- [`../platform-engineering/library-versioning.md`](../../platform-engineering/library-versioning.md) — `@JvmSuppressWildcards` and Java consumer concerns.
- [Kotlin Docs — Generics](https://kotlinlang.org/docs/generics.html) — official reference.
- [Roman Elizarov — "Generic variance"](https://elizarov.medium.com/) — Kotlin language team's design notes.
- [Java Generics FAQ — Angelika Langer](https://www.angelikalanger.com/GenericsFAQ/JavaGenericsFAQ.html) — encyclopedic JVM-side reference.
- [Effective Java Items 26–32](https://www.amazon.com/Effective-Java-Joshua-Bloch/dp/0134685997) — Bloch's chapter on generics.
