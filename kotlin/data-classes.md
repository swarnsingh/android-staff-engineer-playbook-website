# Data Classes

> Data classes are the workhorse of every modern Android UI. Every `UiState`, every Room entity, every API DTO. Used well, they give you mathematical equality, immutable state, and Compose perf for free. Used badly, they tank Compose recompositions, break `HashSet` invariants, and ship 35-property "god states" that nobody can maintain. Staff-level usage is about knowing precisely when to reach for them — and when **not** to.

---

## Overview

A `data class` is a Kotlin class whose primary purpose is carrying state. The compiler auto-generates the methods that Java forced you to write by hand:

| Generated method | What it does |
|---|---|
| `equals(other)` | Value equality — compares each primary-constructor property |
| `hashCode()` | Value hash — consistent with `equals` |
| `toString()` | `User(id=1, name=Alice)` — pretty printing |
| `copy(...)` | Creates a new instance with selectively overridden properties |
| `componentN()` | One per property — enables destructuring |

```kotlin
data class User(val id: String, val name: String)

val a = User("1", "Alice")
val b = User("1", "Alice")
a == b          // true (value equality)
a.toString()    // User(id=1, name=Alice)
val older = a.copy(name = "Alex")   // structural update
val (id, name) = a                  // destructuring
```

---

## Why It Matters (Android Context)

The Java equivalent was 50 lines of boilerplate. Worse, if you forgot to override `equals`/`hashCode`, putting two "equal" `User` objects in a `HashSet` would store both — silent bug.

Modern Android relies on `equals` everywhere:

- **Jetpack Compose** skips recomposition when state `equals` the previous state.
- **`StateFlow.value = newState`** emits only if `newState != oldState`.
- **DiffUtil** (RecyclerView) animates list changes based on `equals`.
- **`HashMap` / `Set` / Room entity caching** all rely on a correct `equals`/`hashCode` pair.

A wrong (or missing) `equals` silently destroys UI performance and correctness.

---

## First Principles

1. **State, not behavior.** A data class holding 30 lines of business logic is a smell. Move logic out.
2. **Immutability by default.** Use `val`, not `var`. Updates happen via `copy(...)`.
3. **Primary constructor is the contract.** Only properties in the primary constructor participate in `equals`, `hashCode`, `toString`, `copy`, and `componentN`.

---

## How the Compiler Generates Each Method

### `equals` + `hashCode`

```kotlin
data class Point(val x: Int, val y: Int)
```

Roughly equivalent to:

```kotlin
override fun equals(other: Any?): Boolean {
    if (this === other) return true
    if (other !is Point) return false
    if (x != other.x) return false
    if (y != other.y) return false
    return true
}

override fun hashCode(): Int {
    var result = x.hashCode()
    result = 31 * result + y.hashCode()
    return result
}
```

The two methods are generated **together** and stay in sync. Critical contract:
- `a == b` ⇒ `a.hashCode() == b.hashCode()`.
- If you override one manually, you must override the other; the compiler stops generating both.

### `copy`

```kotlin
fun copy(x: Int = this.x, y: Int = this.y): Point = Point(x, y)
```

It's a shallow copy. Nested mutable objects are *shared*, not duplicated (this is a common bug — see Pitfalls).

### `componentN` and destructuring

```kotlin
operator fun component1(): Int = x
operator fun component2(): Int = y

val (a, b) = Point(3, 4)
// → val a = point.component1(); val b = point.component2()
```

Position-based, **not** name-based. We'll see why this matters.

### `toString`

```kotlin
override fun toString(): String = "Point(x=$x, y=$y)"
```

Cleaner Logcat output for free.

---

## When `data class` Is the Right Choice

| Use case | Right tool | Why |
|---|---|---|
| UI state (`HomeUiState`) | `data class` | Compose recomposition relies on `equals` |
| API/DTO objects | `data class` | Easy to deserialize + compare |
| Room `@Entity` | `data class` | Equality semantics + Kotlin idioms |
| Value objects (`Money`, `Email`) | `data class` or `value class` | Value semantics |
| MVI state nodes | `data class` (often nested under a sealed parent) | Exhaustive `when` + immutable updates |
| Compose params bundle | `data class` (with `@Stable`/`@Immutable` if needed) | Stability for skipping |

## When `data class` Is the **Wrong** Choice

| Use case | Better tool | Why data class fails |
|---|---|---|
| Database identity (`UserEntity`) | Regular class with explicit `equals` on `id` | Value equality on all fields collapses two distinct rows with same fields |
| Public SDK API surface | Regular class | Adding/removing a property is a binary-compatibility break |
| Classes with significant logic | Regular class | Mixing data + behavior violates SRP |
| Singletons / service objects | `object` | No state to carry; data class generates wasted methods |
| Inheritance hierarchy root | `sealed class` / regular `open class` | Data classes can't be `open` or extended |
| Anything with `ByteArray` / `Array<T>` | Regular class with manual `equals` | Default `equals` on Array uses reference, breaks contract |

---

## The Six Most Common Pitfalls

### 1. Body properties are ignored

```kotlin
data class User(val id: String) {
    var name: String = ""    // NOT in primary constructor
}

val a = User("1").apply { name = "Alice" }
val b = User("1").apply { name = "Bob" }

a == b   // TRUE — name is ignored!
```

**Fix:** put every property that defines identity/value in the primary constructor.

### 2. `var` in a data class

```kotlin
data class CartItem(val id: String, var qty: Int)

val set = hashSetOf<CartItem>()
val item = CartItem("a", 1)
set.add(item)
item.qty = 2          // mutated AFTER insertion
set.contains(item)    // false! HashSet looked up by old hashCode
```

The object is now "lost" in the set. Same trap with HashMap keys. **Fix:** always use `val`. Update by `set.remove(item); set.add(item.copy(qty = 2))`.

### 3. Shallow `copy()` with mutable collections

```kotlin
data class Cart(val items: MutableList<String>)

val original = Cart(mutableListOf("a", "b"))
val updated = original.copy()
updated.items.add("c")

original.items   // [a, b, c] — also changed!
```

`copy()` is a shallow copy — both objects share the same `MutableList`. **Fix:**

```kotlin
data class Cart(val items: List<String>)   // immutable List type

val original = Cart(listOf("a", "b"))
val updated = original.copy(items = original.items + "c")
```

### 4. Arrays don't equal by content

```kotlin
data class Payload(val bytes: ByteArray)

Payload(byteArrayOf(1, 2)) == Payload(byteArrayOf(1, 2))   // false!
```

`Array.equals` compares references. The generated `equals` uses `Array.equals`. **Fix:** either use `List<Byte>` (slower but correct) or override `equals`/`hashCode` manually with `contentEquals()`/`contentHashCode()`.

### 5. Destructuring with same-typed properties

```kotlin
data class LatLng(val lat: Double, val lng: Double)

val (lng, lat) = getLocation()   // ← named lng first by mistake
// component1() = lat, but we assigned it to a variable named `lng`
```

Destructuring is **positional**, not nominal. Compiler doesn't care what you name the variables. With same-typed fields, this is a silent disaster. **Fix:** access properties by name (`val loc = getLocation(); loc.lat, loc.lng`) when fields share types.

### 6. Massive `copy()` in a hot path

```kotlin
data class HomeUiState(
    val user: User,
    val cart: Cart,
    val recommendations: List<Product>,
    val banners: List<Banner>,
    // ... 30 more fields
)

// Every frame:
_state.value = _state.value.copy(scrollPos = newPos)
```

A 30-property `copy()` is fine occasionally, but 60×/sec on the main thread allocates 60 throwaway objects/sec. GC pressure + jank.

**Fix:** split god states into composed sub-states:

```kotlin
data class HomeUiState(
    val content: ContentState,
    val transient: TransientState,    // scroll position, focus, etc.
)
// then update only the slice that changed
```

---

## Inheritance Restrictions

| Allowed | Not allowed |
|---|---|
| Implement interfaces | Extend other classes (`open class`, `abstract class`) |
| Be inside a sealed hierarchy | Be `open`, `abstract`, `sealed`, or `inner` |
| Have a companion object | Be extended by another class |

```kotlin
// ✅ data class inside a sealed hierarchy
sealed interface UiState
data class Success(val data: List<Item>) : UiState
data class Error(val message: String) : UiState
data object Loading : UiState

// ❌ won't compile
open data class Base(val x: Int)
data class Sub(val x: Int, val y: Int) : Base(x)
```

This restriction exists because inheritance breaks the value-equality contract: a `Sub("a", 1)` and `Base("a")` couldn't both be "equal."

---

## Equals/HashCode Contract

A correct `equals` must be:

| Property | Means | Why it matters |
|---|---|---|
| **Reflexive** | `a == a` | Trivial, but breaks if you return `false` on identity |
| **Symmetric** | `a == b` ⇒ `b == a` | HashMap / HashSet contracts rely on this |
| **Transitive** | `a == b` and `b == c` ⇒ `a == c` | Breaks lookups otherwise |
| **Consistent** | Repeated calls give same result if neither changes | Mutation invalidates HashMap |
| **Non-null** | `a != null` always for non-null `a` | Standard Kotlin guarantee |

`hashCode` must obey: **if `a == b`, then `a.hashCode() == b.hashCode()`.**

The reverse is **not** required — two unequal objects can share a hashCode (collision).

Data classes get all of this for free as long as you use `val` and primary-constructor properties.

---

## Compose Stability and Data Classes

Compose decides whether to skip recomposition by checking whether function parameters are **stable**. A parameter is stable if:

1. Its type is a primitive (`Int`, `String`, `Boolean`, etc.), OR
2. Its class is annotated `@Stable` / `@Immutable`, OR
3. It's a `data class` with all-`val` properties of stable types.

```kotlin
@Immutable
data class User(val id: String, val name: String)   // stable
// Compose will skip recomposition when the same User is passed
```

### Things that make a data class **unstable**

```kotlin
data class User(val id: String, var name: String)
// var → unstable → Compose can't trust value equality
```

```kotlin
data class User(val id: String, val tags: List<String>)
// kotlin.collections.List is not @Stable in Compose (mutable contract)
// → unstable in Compose's eyes
```

Two fixes for the second case:

1. Annotate the class explicitly:
   ```kotlin
   @Immutable
   data class User(val id: String, val tags: List<String>)
   ```
   You promise Compose this is immutable. If you lie, you get stale UI.

2. Use a guaranteed-immutable collection:
   ```kotlin
   import kotlinx.collections.immutable.ImmutableList
   data class User(val id: String, val tags: ImmutableList<String>)
   ```
   See [`../android/compose/stability.md`](../android/compose/stability.md) for the `@Stable` / `@Immutable` deep dive.

### Why this matters in production

A complex screen with an unstable `UiState` will recompose every emission instead of skipping unchanged sub-trees. On a 60Hz display, you have 16ms per frame; unnecessary recomposition burns it fast. Stability isn't pedantry — it's the difference between a smooth screen and a janky one.

---

## Data Classes in Common Android Patterns

### MVI / UDF — sealed parent + data class children

```kotlin
sealed interface CartUiState {
    data object Loading : CartUiState
    data class Success(val items: List<CartItem>, val total: Money) : CartUiState
    data class Error(val message: String, val retryable: Boolean) : CartUiState
}

class CartViewModel : ViewModel() {
    private val _state = MutableStateFlow<CartUiState>(CartUiState.Loading)
    val state: StateFlow<CartUiState> = _state.asStateFlow()

    fun retry() {
        viewModelScope.launch {
            _state.value = CartUiState.Loading
            try {
                val items = repo.getCart()
                _state.value = CartUiState.Success(items, computeTotal(items))
            } catch (e: IOException) {
                _state.value = CartUiState.Error(e.message.orEmpty(), retryable = true)
            }
        }
    }
}
```

Exhaustive `when` on the Composable side. See [`sealed-classes.md`](sealed-classes.md).

### Room entity

```kotlin
@Entity(tableName = "users")
data class UserEntity(
    @PrimaryKey val id: String,
    val name: String,
    val email: String,
    @ColumnInfo(name = "created_at") val createdAt: Long,
)

@Dao
interface UserDao {
    @Query("SELECT * FROM users WHERE id = :id")
    suspend fun findById(id: String): UserEntity?

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun upsert(user: UserEntity)
}
```

Note: for entities representing **rows in a database**, the value-equality semantics of a data class can be misleading — two rows with the same fields are still different rows. Choose intentionally; if identity matters, override `equals` to compare on `id` only or use a regular class.

### Network DTO with Moshi

```kotlin
@JsonClass(generateAdapter = true)
data class UserDto(
    @Json(name = "user_id") val id: String,
    val name: String,
    val email: String?,
)
```

Moshi (preferred over Gson — see [`null-safety.md`](null-safety.md)) honors Kotlin nullability and uses the constructor, so non-null fields stay non-null.

### Compose parameters

```kotlin
@Composable
fun ProductRow(product: Product, onAdd: (Product) -> Unit) { /* ... */ }

@Stable
data class Product(val id: String, val name: String, val priceCents: Int)
```

If `ProductRow` is in a `LazyColumn`, stable params + stable lambda `onAdd` let Compose skip recomposition for rows whose product didn't change.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| `HashSet.contains(x)` returns false after mutation | `var` in data class, hashCode changed | All-`val`; update via `copy` + re-insert |
| Two equal-looking objects compare false | `ByteArray` / `Array<T>` field | Use `List<Byte>` or override `equals`/`hashCode` |
| Compose recomposes the whole tree on every emission | Unstable data class (`var`, `List`) | `@Immutable`, or use `kotlinx.collections.immutable` |
| `LazyColumn` doesn't animate item moves | Items don't have stable identity for `key` | Provide `key = { it.id }` |
| Memory leak: items pile up in cart list across copies | Shared `MutableList` inside data class | Switch to `List<T>`; use `+ element` |
| Two same-typed fields silently swapped after refactor | Destructuring positional, fields reordered | Access by name; or compiler warning "Component name mismatch" (Kotlin 1.9+) |
| `User(id=1) != User(id=1)` after JSON parse | Body property holding extra state | All identity props in primary constructor |
| Random crash: `IllegalStateException: companion default value …` | Adding a new non-default field to a public data class | SDK-style data classes need `@JvmOverloads`-style defaults or use a Builder |
| Logs spam `User(id=…, name=…, email=…, …)` with PII | `toString` includes sensitive fields | Override `toString` manually or mark fields as redacted (`@Sensitive`) |
| `60 fps drop to 30 fps` after adding state field | God-state `copy()` allocates large object each frame | Split into composed sub-states |

---

## Staff Engineer Lens

When reviewing a data class PR, I check for:

1. **`ByteArray` / `Array<T>` fields** — auto-reject. The default `equals` is broken for arrays. Force `List` or manual override.
2. **`var` properties** — auto-reject unless there's a specific justification. Mutation breaks `HashMap`/`HashSet` and Compose skipping.
3. **Body properties** — push everything that defines identity to the primary constructor.
4. **God states** (>10 properties) — push to split.
5. **Public-API data classes in SDKs** — flag binary-compat risk. Adding a property is a breaking change for Java consumers who positional-construct. Force builders or `@JvmOverloads` if needed.
6. **Destructuring on same-typed fields** — warn; require named access.
7. **`Sensitive PII in `toString`** — call out for redaction.
8. **Stability annotations missing** when used in Compose — push for `@Immutable`/`@Stable`.

---

## Common Misconceptions

- **"Every class should be a data class."** No. Data classes are for *carrying state*. Services and singletons aren't.
- **"Data classes are just POJOs."** They're immutable value types with auto-generated structural equality. POJOs are mutable bean-style containers.
- **"`copy()` is a deep copy."** It's shallow. Nested mutable state is shared. Switch to immutable types or `copy()` recursively.
- **"`var` is fine if I'm careful."** It silently corrupts `HashSet`/`HashMap`/Compose. There is no safe `var` in a data class.
- **"Data classes can't have business logic."** They can have functions; they shouldn't be the *primary location* of business logic. A short `fun totalCents(): Int` is fine; a 40-line validation method isn't.
- **"Two equal data classes have the same hashCode (always)."** True if you used the generated `hashCode`. If you overrode `equals` without overriding `hashCode`, you've broken the contract.

---

## Probing Questions

1. List the 5 methods the compiler generates for a `data class`. What does each enable?
2. A `HashSet<User>` contains `User("1", "Alice")`. The application mutates `user.name = "Alex"`. Does `contains` still find it? Why or why not?
3. Why does putting a `ByteArray` in a data class break structural equality?
4. Walk through the silent bug when destructuring `data class LatLng(val lat: Double, val lng: Double)` as `val (lng, lat) = location`.
5. What happens to Compose recomposition if your `UiState` data class contains a `List<Item>` and you don't annotate it `@Immutable`?
6. Why is using `var` inside a data class an architectural smell that breaks `HashMap`?
7. `data class Cart(val items: List<String>)` — calling `.copy()` produces an independent list, true or false? Walk through.
8. Compare a `data class` Room entity with one written as a normal class. When does identity-equality matter more than value-equality?
9. Your SDK publishes `data class Config(val timeout: Int)`. The next minor version adds `val retries: Int`. What breaks for Java consumers?
10. Why are data classes forbidden from being `open` or extending another class?
11. Compare `data class` vs `value class` (inline class). When is each the right choice?
12. A team's `data class HomeUiState` has 35 properties. What questions do you ask before they go further?

---

## Further Reading

- [`null-safety.md`](null-safety.md) — nullable properties inside data classes.
- [`sealed-classes.md`](sealed-classes.md) — sealed parents + data class children pattern.
- [`delegation.md`](delegation.md) — `by lazy` for expensive derived properties on a data class.
- [`variance.md`](variance.md) — generic data classes (`Result<out T>`, `Either<L, R>`).
- [`../android/compose/stability.md`](../android/compose/stability.md) — `@Stable` / `@Immutable` deep dive.
- [`../android/compose/recomposition-and-state.md`](../android/compose/recomposition-and-state.md) — how Compose uses `equals` to skip work.
- [`../android/data-and-di/room.md`](../android/data-and-di/room.md) — data class as `@Entity`.
- [`../principles/make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md) — immutable value types as the foundation.
- [Kotlin Docs — Data classes](https://kotlinlang.org/docs/data-classes.html) — official reference.
- [JEP 395: Records](https://openjdk.org/jeps/395) — Java's equivalent feature; useful for comparison.
- [Jake Wharton — "Public API challenges in Kotlin"](https://jakewharton.com/public-api-challenges-in-kotlin/) — binary compatibility of data classes.
