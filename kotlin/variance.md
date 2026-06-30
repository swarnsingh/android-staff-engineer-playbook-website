# Variance (Covariance and Contravariance)

> Variance answers one question: if `Dog : Animal`, what's the relationship between `Container<Dog>` and `Container<Animal>`? Get this wrong and you ship a `ClassCastException`. Get it right and your APIs flex without sacrificing type safety. Staff-level mastery means knowing when to declare `out T` / `in T` on your own generic types, when to use use-site projections, why `MutableList<T>` is intentionally invariant, and how `Nothing` powers the sealed `Resource<out T>` idiom.

---

## The Big Idea in One Sentence

**`out T` (covariance):** "I only *produce* T. Subtype relationship preserved."
**`in T` (contravariance):** "I only *consume* T. Subtype relationship reversed."
**No modifier (invariance):** "I both produce and consume T. No subtype relationship."

```kotlin
open class Animal
class Dog : Animal()

// Covariance: Producer<Dog> can be used as Producer<Animal>
interface Producer<out T> { fun produce(): T }

// Contravariance: Consumer<Animal> can be used as Consumer<Dog>
interface Consumer<in T> { fun consume(item: T) }

// Invariance: Box<Dog> and Box<Animal> are unrelated
class Box<T>(var item: T)
```

---

## Why It Matters

Without variance, you couldn't pass a `List<Dog>` to a function expecting `List<Animal>` — the type system would treat them as utterly unrelated types. Without it, every generic API would force callers to copy their data into the exact required type, or use unsafe casts, or simply not be reusable at all.

The Kotlin stdlib uses variance everywhere:

- `List<out T>` — read-only collections are covariant.
- `Comparator<in T>` — comparators are contravariant.
- `Flow<out T>` — coroutine flows are covariant in their emission type.
- `Function1<in P, out R>` — function types are contravariant in params, covariant in return.
- `Iterator<out T>`, `Iterable<out T>`, `Sequence<out T>` — all covariant.
- `MutableList<T>` — **intentionally invariant**, because writing breaks the chain.

---

## The Java Arrays Catastrophe (Why This Matters)

Java made arrays covariant by default. The result:

```java
Dog[] dogs = new Dog[10];
Animal[] animals = dogs;          // Java allows this — arrays are covariant
animals[0] = new Cat();           // Cat is-an Animal — Java allows the assignment
// CRASH at runtime: ArrayStoreException
```

The JVM has to add a runtime check on every array write to detect this. Generics were designed differently: **invariant by default**, with explicit opt-in to variance.

```kotlin
val dogs: MutableList<Dog> = mutableListOf()
val animals: MutableList<Animal> = dogs    // ❌ Compile error
// would have allowed animals.add(Cat()), corrupting dogs
```

Kotlin's compile-time enforcement makes the runtime check unnecessary — bugs caught before the app ships.

---

## First Principles

1. **Position matters.** A type parameter can appear in *input* position (function parameter type) or *output* position (return type, property type).
2. **`out T` allows the parameter only in output positions.** Reading is safe; writing is forbidden.
3. **`in T` allows the parameter only in input positions.** Writing is safe; reading is forbidden.
4. **Invariance is the default.** No subtype relationship between `Foo<Dog>` and `Foo<Animal>`.
5. **`Nothing` is the universal subtype.** `Resource<Nothing>` is assignable to `Resource<T>` for any `T`. This makes terminal states (`Loading`, `Error`) work in generic sealed hierarchies.

---

## Mental Model — Vending Machines and Trash Cans

| | Vending machine | Trash can |
|---|---|---|
| Type | Producer | Consumer |
| Variance | `out` (covariance) | `in` (contravariance) |
| Direction | Things come **out** | Things go **in** |
| Substitution | Doritos-machine works where a snack-machine is needed (subtype → supertype) | A general electronics dumpster works where a laptop dumpster is needed (supertype → subtype) |

Mnemonic — **PECS** (from Java): **P**roducer **E**xtends → `out` ; **C**onsumer **S**uper → `in`.

---

## Covariance (`out T`) — Producers

```kotlin
interface Source<out T> {
    fun next(): T
    // fun add(item: T)   ❌ compile error — T in input position
}

class DogSource : Source<Dog> {
    override fun next(): Dog = Dog()
}

val dogSource: Source<Dog> = DogSource()
val animalSource: Source<Animal> = dogSource    // ✅ legal because of `out`
val a: Animal = animalSource.next()             // Dog returned, used as Animal
```

It's mathematically safe: every `Dog` IS-A `Animal`, so a `Source<Dog>` is a valid `Source<Animal>` *for reading*. There's nothing to break because you can't write to it.

### Real stdlib: `List<out E>`

```kotlin
public interface List<out E> : Collection<E> {
    public operator fun get(index: Int): E   // E in output position ✅
    public fun indexOf(element: @UnsafeVariance E): Int   // ⚠ see below
}
```

You can pass a `List<Dog>` to a function expecting `List<Animal>` — completely safe. You cannot do this with `MutableList`.

`@UnsafeVariance` lets `indexOf(element: E)` use `E` in input position even though `List` is `out`. It's safe here because `indexOf` doesn't store the element, only reads existing items to compare. App-level code should avoid `@UnsafeVariance` — it's a stdlib escape hatch.

---

## Contravariance (`in T`) — Consumers

```kotlin
interface Sink<in T> {
    fun accept(item: T)
    // fun emit(): T     ❌ compile error — T in output position
}

val animalSink: Sink<Animal> = object : Sink<Animal> {
    override fun accept(item: Animal) { /* logs anything */ }
}
val dogSink: Sink<Dog> = animalSink    // ✅ legal because of `in`
dogSink.accept(Dog())                  // safe — Animal sink can absorb Dogs
```

Subtype relationship is **reversed**: `Sink<Animal>` is a subtype of `Sink<Dog>` even though `Animal` is a supertype of `Dog`. Because the sink only consumes, a general consumer works wherever a specific one is needed.

### Real stdlib: `Comparator<in T>`

```kotlin
val animalComparator: Comparator<Animal> = compareBy { it.name }
val dogComparator: Comparator<Dog> = animalComparator    // ✅ legal
listOf(Dog(), Dog()).sortedWith(dogComparator)
```

A `Comparator<Animal>` knows how to compare any two animals, so it certainly knows how to compare two dogs. Contravariance makes this fact a compile-time fact.

---

## Function Types — Variance Built-In

Kotlin function types are contravariant in their parameters and covariant in their return:

```kotlin
// Function1<P, R> is actually Function1<in P, out R>
val f: (Animal) -> Number = { a -> a.legs }
val g: (Dog) -> Int = f                          // ✅ legal: P (Dog) <: P (Animal); R (Int) <: R (Number)
val n: Int = g(Dog())
```

Reading rules:
- A `(Animal) -> X` works wherever a `(Dog) -> X` is wanted — contravariant in parameter (`in`).
- A `(X) -> Int` works wherever a `(X) -> Number` is wanted — covariant in return (`out`).

This is what makes the entire functional-style Kotlin work cleanly. You almost never think about it directly, but it's why `listOf(Dog()).map(animalNameFn)` compiles.

---

## Invariance — When You Need Both Read and Write

`MutableList<T>` cannot be `out` because you can write into it. It cannot be `in` because you can read from it. Therefore it must be invariant.

```kotlin
class Box<T>(var item: T) {
    fun get(): T = item        // out position
    fun set(value: T) { item = value }   // in position
}
// Cannot mark as in or out — uses T in both positions
```

This is the right default. If you try to be clever and mark `Box<out T>`, the compiler stops you because `set(value: T)` violates the contract.

---

## Use-Site Variance (Wildcards)

Sometimes the declaration is invariant, but **at a specific use site** you only read or only write. Use-site projection lets you opt in at the call:

```kotlin
fun copyAnimals(from: MutableList<out Animal>, to: MutableList<in Animal>) {
    for (item in from) to.add(item)
}

val dogs: MutableList<Dog> = mutableListOf(Dog(), Dog())
val animals: MutableList<Any> = mutableListOf()
copyAnimals(dogs, animals)   // ✅ legal
```

- `MutableList<out Animal>` — within this function, treat the list as read-only `Animal`.
- `MutableList<in Animal>` — within this function, treat the list as write-only with `Animal` minimum.

This is exactly Java's `? extends Animal` (`out`) and `? super Animal` (`in`).

| You want to | Use |
|---|---|
| Read from a list inside a function, accept any subtype | `List<out Animal>` (already default for List) |
| Write to a list inside a function, accept any supertype | `MutableList<in Animal>` |
| Both read and write | `MutableList<Animal>` (invariant) |

---

## Declaration-Site vs Use-Site Variance

| | Declaration-site | Use-site |
|---|---|---|
| Where declared | On the class itself: `class Foo<out T>` | At a function parameter: `fun bar(x: Foo<out T>)` |
| Scope | Class-wide rule for every use of `Foo<T>` | Local rule for that one parameter |
| Visibility | Document of intent (this class is always covariant) | Per-call decision |
| When to use | When the class naturally is a producer/consumer | When the class is invariant but you can be more specific locally |
| Kotlin uses | Kotlin's primary mechanism (preferred) | Java compatibility / one-off projections |

Kotlin prefers declaration-site. Java only has use-site (`? extends T`, `? super T`). When Kotlin code goes through to Java, variance becomes use-site wildcards.

---

## `Nothing` — The Universal Subtype + Variance

`Nothing` is the bottom of the type hierarchy — a subtype of every other type. Combined with covariance, it creates the **single-instance terminal** idiom for sealed hierarchies:

```kotlin
sealed interface Resource<out T> {
    data object Loading : Resource<Nothing>
    data class Success<T>(val data: T) : Resource<T>
    data class Failure(val error: Throwable) : Resource<Nothing>
}

val loading: Resource<User> = Resource.Loading    // ✅ Resource<Nothing> is Resource<User>
val failure: Resource<Cart> = Resource.Failure(IOException())   // ✅ same
```

`Loading` doesn't need to know what `T` is — it's a single shared instance. Because `Resource` is `out T`, and `Nothing : T` for every `T`, `Resource<Nothing>` is assignable everywhere.

You'd be unable to write this idiomatically without:
- Covariance (`out T`) on the sealed interface.
- `Nothing` as the terminal type parameter.

This pattern shows up in `kotlin.Result<T>`, every `ApiResponse<T>` you write, and most `Either<L, R>` libraries.

---

## When You Must Be Invariant

- The class has **mutable state** that holds a `T` and is both read and written — `MutableList<T>`, `MutableSet<T>`, `Box<T>`.
- The class **consumes and produces** the same `T` — like a cache (`Cache<K, V>` where `V` is both put and got).

If you try to add `out` to such a class, the compiler stops you because writing breaks the safety guarantee.

---

## Real Android Patterns

### `Flow<out T>` — covariant emissions

```kotlin
val userFlow: Flow<User> = ...
val anyFlow: Flow<Any> = userFlow    // ✅ legal
```

Collectors only receive `T`, never emit — perfect for `out`.

### Listener-style consumers — contravariant

```kotlin
interface OnItemClickListener<in T> {
    fun onClick(item: T)
}

val animalListener: OnItemClickListener<Animal> = ...
recyclerView.onClickListener = animalListener as OnItemClickListener<Dog>   // ✅ legal
```

A listener for "anything" can listen for dogs specifically. Use `in` here.

### `LiveData<T>` — invariant (a missed opportunity)

`androidx.lifecycle.LiveData<T>` is invariant. This means you cannot assign `LiveData<Dog>` to `LiveData<Animal>` directly — annoying. The reason: `MutableLiveData<T>` writes; the design choice was to keep the API consistent. Use `.map { it as Animal }` or switch to `Flow<out T>` which is covariant.

### Custom `Result` types

```kotlin
sealed interface ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>
    data class Error(val code: Int) : ApiResult<Nothing>
    data object Cancelled : ApiResult<Nothing>
}
```

Now `ApiResult<User>` can hold a `Success<User>`, an `Error`, or `Cancelled` — and your `when` branches work cleanly.

### `Repository<in T>` for inserts

```kotlin
interface Saver<in T> {
    suspend fun save(item: T)
}

val animalSaver: Saver<Animal> = ...
val dogSaver: Saver<Dog> = animalSaver    // ✅ a general-animal saver can save a dog
```

Useful when one repository accepts a generic hierarchy.

---

## Java Interop — Variance Crosses the Boundary

When Kotlin compiles to JVM bytecode, declaration-site variance becomes use-site wildcards on the Java side:

| Kotlin | Java |
|---|---|
| `List<out T>` returned | `List<? extends T>` |
| `Sink<in T>` parameter | `Sink<? super T>` |
| `(Animal) -> Int` (`Function1<in Animal, out Int>`) | `Function1<? super Animal, ? extends Integer>` |

Java consumers get verbose signatures. If you're shipping a Kotlin SDK to Java consumers, you can suppress:

```kotlin
@JvmSuppressWildcards
fun process(list: List<Animal>): List<Result> = ...
// Java sees: List<Animal>, List<Result>  (no wildcards)
```

And in the other direction, force a wildcard:

```kotlin
fun produce(): List<@JvmWildcard Animal> = ...
// Java sees: List<? extends Animal>
```

This is the kind of detail you discover when your Java consumers complain about cluttered signatures. See [`../platform-engineering/library-versioning.md`](../platform-engineering/library-versioning.md) and `generics.md` for SDK API discipline.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Compile error: "Type mismatch" passing `List<Dog>` to `List<Animal>` param | List declared without `out` (custom list) | Use stdlib `List` (already `out E`) or add `out` if read-only |
| Compile error: "Out-projected type" on `MutableList<out Animal>` write | Tried to `add` to a use-site `out` projection | Either accept invariant `MutableList<T>` or use read-only |
| Compile error on your own `class Box<out T>` | `T` appears in `in` (parameter) position | Either remove `out`, or refactor to not consume `T` |
| `@UnsafeVariance` warning ignored | Reading source that violates declared variance | Don't suppress in app code; use only in stdlib-style code |
| Java consumers see ugly `? extends T` everywhere | Default Kotlin variance leaks to Java | `@JvmSuppressWildcards` on SDK surface |
| `Resource<Nothing>` assignment fails | Sealed parent is invariant | Add `out T` to the sealed parent |
| Listener type incompatible | `OnClick<T>` invariant | Mark as `in T` |
| Cannot assign `LiveData<Dog>` to `LiveData<Animal>` | LiveData is invariant | `Transformations.map(it) { it as Animal }` or switch to `Flow<out T>` |
| Confusing variance inheritance | Subclass changes variance | Subclass cannot widen variance; can only narrow / preserve |
| `Comparator<Dog>` not accepted for sorting `List<Animal>` (rare) | Contravariance direction confused | Comparator is `in T`; an `Animal` comparator works for Dogs, not the reverse |
| Test fails because mocked Flow is wrong type | Mocking a covariant type by emitting subtypes | Cast at the mock construction or use stable type |
| Compose Composable parameter rejects generic subtype | Compose Composables can't be inline-generic in some scenarios | Sometimes refactor to a concrete type at the surface |

---

## Staff Engineer Lens

When reviewing variance choices, I look for:

1. **Generic class only used as a producer** — should be `out T`. Missed opportunity for reuse if invariant.
2. **Generic class only used as a consumer (listener, sink, saver)** — should be `in T`. Same.
3. **`@UnsafeVariance` in app code** — auto-reject unless there's a stdlib-style proof. Usually wrong.
4. **Sealed hierarchy without `out T`** — you've blocked the `Resource<Nothing>` idiom. Add it.
5. **Function type signatures unnecessarily complex** — sometimes a custom interface is clearer than `(A) -> B` deeply nested in generics.
6. **Java consumer complaints about wildcard noise** — `@JvmSuppressWildcards` at the SDK boundary.
7. **`as` casts to bridge variance** — usually means the declaration site got variance wrong. Fix the declaration.
8. **A `MutableSomething<out T>` attempt** — explain why this is structurally impossible and refactor.

---

## Common Misconceptions

- **"Variance is about input vs output of the program."** No — it's about input vs output positions of `T` in the generic class's API.
- **"`out` means I can write to it."** Backwards. `out` means read-only — the type comes *out*.
- **"`in` means I can read from it."** Backwards. `in` means write-only — the type goes *in*.
- **"Covariance is unsafe (like Java arrays)."** Java arrays were unsafe because the *write* check happened at runtime. Kotlin variance makes the unsafe operations *not compile* — totally safe.
- **"I should just mark every generic class as `out` to be flexible."** Doing so forbids any `T`-in-input-position function. Pick deliberately.
- **"`out` and `in` are equivalent to Java's `extends` and `super`."** Sort of — but Kotlin lets you declare it once on the class (declaration-site), where Java forces you to repeat it at every use (use-site).
- **"Variance is rare in real code."** It's everywhere — every `Flow`, every `List`, every comparator, every coroutine builder. You just usually don't think about it.

---

## Probing Questions

1. Explain why `Dog[]` is a `Animal[]` in Java but `Box<Dog>` is *not* a `Box<Animal>` in Kotlin by default. What problem does the latter prevent?
2. Walk through what `out T` allows and forbids in a class body. Same for `in T`.
3. Why is `List<out E>` valid but `MutableList<out E>` impossible?
4. Real example: you have `class Saver<T> { fun save(item: T) }`. Should it be `Saver<in T>`, `Saver<out T>`, or neither? Why?
5. Walk through how `Resource<Nothing>` becomes assignable to `Resource<User>` via `out T` + `Nothing` being the bottom type.
6. The function type `(Animal) -> Int` — what variance does each parameter have, and why?
7. Comparator: `Comparator<in T>`. Why is `Comparator<Animal>` a valid `Comparator<Dog>`?
8. When would you need use-site variance (`MutableList<out Number>`) instead of declaration-site?
9. Java sees Kotlin's `out T` as `? extends T`. Why might this annoy Java consumers of your Kotlin SDK, and how do you fix it?
10. `@UnsafeVariance` — what does it do, and why should app developers avoid it while stdlib authors use it?
11. PECS mnemonic — give a concrete example of each rule using Android-relevant types.
12. Can a subclass widen variance compared to its parent class? Tighten? Why?
13. `LiveData<T>` is invariant; `Flow<out T>` is covariant. Why might that be, given they both deliver values to observers?

---

## Further Reading

- [`generics.md`](generics.md) — type erasure, bounded generics, foundation for variance.
- [`sealed-classes.md`](sealed-classes.md) — `out T` + `Nothing` idiom in sealed hierarchies.
- [`reified-types.md`](reified-types.md) — type info at runtime for generic / variant operations.
- [`inline-functions.md`](inline-functions.md) — why `reified` requires inline.
- [`coroutines.md`](coroutines.md) — `Flow<out T>` covariance in practice.
- [`null-safety.md`](null-safety.md) — `Result<T>` and bounded null safety.
- [`../platform-engineering/library-versioning.md`](../platform-engineering/library-versioning.md) — `@JvmSuppressWildcards` for clean Java consumer APIs.
- [Kotlin Docs — Generics: variance](https://kotlinlang.org/docs/generics.html#variance) — official reference.
- [Roman Elizarov — "Generic variance"](https://elizarov.medium.com/) — design notes from Kotlin's language lead.
- [Java Generics FAQ — Wildcards](https://www.angelikalanger.com/GenericsFAQ/JavaGenericsFAQ.html) — the deep JVM-side reference.
- [PECS — Joshua Bloch's Effective Java Item 31](https://www.amazon.com/Effective-Java-Joshua-Bloch/dp/0134685997) — the canonical Producer/Consumer treatment.
