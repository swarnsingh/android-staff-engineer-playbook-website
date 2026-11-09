# Sealed Classes and Interfaces

> Sealed types are how you make invalid states impossible in modern Android. Every `UiState`, every `NetworkResult`, every navigation route in a well-architected Compose app sits in a sealed hierarchy. Staff-level mastery means knowing when sealed beats enum, when it beats interface, when it beats data class with nullable fields, and the traps (else branches, polymorphic JSON, SDK evolution) that turn the safety net into a footgun.

---

## Overview

A `sealed class` or `sealed interface` is a closed type hierarchy. You declare it like a regular type, but only subclasses defined in the same module and package for direct subclasses (package/module-wide subclasses have been supported since Kotlin 1.5) can extend it. The compiler knows the exhaustive list of subclasses at compile time, which unlocks:

- **Exhaustive `when`** — no `else` branch required; compiler errors if you miss a case.
- **Smart casts** — inside `is Success ->` the variable is narrowed to `Success`.
- **Algebraic Data Type (ADT) modeling** — express "this value is one of N specific shapes."

```kotlin
sealed interface NetworkResult {
    data class Success(val json: String) : NetworkResult
    data class Error(val code: Int) : NetworkResult
    data object Loading : NetworkResult
}
```

Add a new `data object Cancelled : NetworkResult` six months later, and every `when` over `NetworkResult` in the codebase fails to compile until you handle it. **Refactoring becomes a guided process instead of a guessing game.**

---

## Why It Matters (Android Context)

Pre-sealed-types, UI state looked like:

```kotlin
data class HomeState(
    val isLoading: Boolean,
    val data: List<Item>?,
    val error: String?,
)
```

How many "valid" combinations? Eight (2 × 2 × 2). How many actually exist? Three. The other five are paradoxes — "loading + error + data" doesn't mean anything. The compiler can't help you avoid representing them.

```kotlin
sealed interface HomeState {
    data object Loading : HomeState
    data class Success(val data: List<Item>) : HomeState
    data class Error(val message: String) : HomeState
}
```

Three states. Three. No paradoxes possible. Compiler enforces handling each branch. UI code becomes trivially correct.

---

## First Principles

1. **Closed hierarchy.** Compiler knows every subclass. No surprises at runtime.
2. **Exhaustiveness.** `when` over a sealed type is checked for completeness.
3. **Smart casts.** No need for `?.` or `as` inside type-narrowed branches.
4. **Direct-subclass boundary.** Direct subclasses must be in the same module and package; an open indirect branch can permit outside extensions.

---

## When to Reach For Sealed — vs Alternatives

| Use case | Right tool | Why |
|---|---|---|
| Fixed set of values, same data shape | `enum class` | Lighter; values are singletons |
| Fixed set of *shapes*, each with different data | `sealed class` / `sealed interface` | Type per branch |
| Open polymorphism (3rd-party extension) | `interface` (not sealed) | Sealed forbids outside subclasses |
| Reusable behavior up the hierarchy | `abstract class` | Sealed class is fine too if hierarchy is closed |
| Combine multiple categorizations | `sealed interface` × `sealed interface` | Multi-interface intersection |
| Variant of a generic state | `sealed class Resource<T>` | Generic ADTs |

### sealed vs enum — concrete decision

```kotlin
// Enum — when each case has identical structure
enum class Role { ADMIN, EDITOR, VIEWER }

// Sealed — when each case has different structure
sealed interface PaymentMethod {
    data class CreditCard(val last4: String, val brand: String) : PaymentMethod
    data class UpiId(val handle: String) : PaymentMethod
    data class Wallet(val provider: String, val balance: Long) : PaymentMethod
    data object Cash : PaymentMethod
}
```

If you find yourself with an enum + multiple nullable fields where the nullability depends on the enum, you needed sealed.

### sealed class vs sealed interface

| | `sealed class` | `sealed interface` |
|---|---|---|
| Available since | Kotlin 1.0 | Kotlin 1.5 |
| Constructor | Has one | None |
| State on the parent | Yes (`val timestamp: Long`) | No |
| Multiple inheritance | Single parent | Subclass can implement multiple |
| Default for new code | Only if shared state | **Preferred** |

```kotlin
// Class — share `id` across all subclasses
sealed class UiEvent(open val timestamp: Long) {
    data class Click(val buttonId: String, override val timestamp: Long) : UiEvent(timestamp)
    data class Swipe(val direction: Direction, override val timestamp: Long) : UiEvent(timestamp)
}

// Interface — multiple categorizations
sealed interface Trackable
sealed interface UserAction : Trackable
sealed interface SystemEvent : Trackable
data object AppLaunched : SystemEvent
data class ButtonClicked(val id: String) : UserAction
```

`sealed interface` is preferred when you don't need shared state — it's more flexible and composable.

---

## Exhaustive `when` — the Headline Feature

```kotlin
fun render(state: HomeState) = when (state) {
    HomeState.Loading -> showSpinner()
    is HomeState.Success -> showItems(state.data)
    is HomeState.Error -> showError(state.message)
}
```

**No `else` branch.** Compiler checks every subclass is covered.

### `when` as expression vs statement

For sealed, enum, and Boolean subjects, Kotlin 1.7+ checks exhaustiveness for both expressions and statements. Older language versions had different statement rules.

```kotlin
// Expression — compiler enforces exhaustiveness
val message: String = when (state) {
    HomeState.Loading -> "..."
    is HomeState.Success -> "ok"
    is HomeState.Error -> "fail"
}

// Statement (Kotlin <1.7 default) — exhaustiveness NOT enforced
when (state) {
    HomeState.Loading -> showSpinner()
    is HomeState.Success -> showItems(state.data)
    // missing Error — compiles silently in older Kotlin!
}
```

**Forcing exhaustiveness on statements** — assign to `Unit` or use the `.exhaustive` idiom:

```kotlin
when (state) {
    HomeState.Loading -> showSpinner()
    is HomeState.Success -> showItems(state.data)
    is HomeState.Error -> showError(state.message)
}.let { }   // forces expression context
```

In Kotlin 1.7+ these sealed-subject statements are exhaustive by default; the historical expression-context workaround is unnecessary.

### Smart casts inside branches

```kotlin
when (state) {
    HomeState.Loading -> Unit
    is HomeState.Success -> {
        // state is smart-cast to Success
        showItems(state.data)   // .data accessed without cast
    }
    is HomeState.Error -> {
        // state is smart-cast to Error
        showError(state.message)
    }
}
```

The `is` check both filters and narrows. No `as Success` required.

---

## Generic Sealed Hierarchies

For reusable result types, parametrize the sealed hierarchy:

```kotlin
sealed interface Resource<out T> {
    data object Loading : Resource<Nothing>
    data class Success<out T>(val data: T) : Resource<T>
    data class Failure(val error: Throwable) : Resource<Nothing>
}

// Usage
val userResource: Resource<User> = repo.getUser()
val cartResource: Resource<List<CartItem>> = repo.getCart()
```

Two important details:
- `out T` makes the type **covariant** — a `Resource<Admin>` can be used where `Resource<User>` is expected (see [`variance.md`](../type-system/variance.md)).
- `Loading` and `Failure` parametrize on `Nothing` — `Resource<Nothing>` is assignable to `Resource<T>` for any `T`. This is the standard ADT idiom.

### `Result<T>` — Kotlin's built-in

```kotlin
suspend fun loadUser(id: String): Result<User> = runCatching {
    api.getUser(id)
}.onFailure { if (it is kotlinx.coroutines.CancellationException) throw it }

loadUser(id)
    .onSuccess { showProfile(it) }
    .onFailure { showError(it.message) }
```

`kotlin.Result` is a built-in success/failure wrapper. Two caveats:

- It's an `inline value class` — efficient at runtime.
- It uses `Throwable` for failure — fine for opaque errors, lossy for structured errors. For structured failures, write your own sealed type.

### Arrow's `Either<L, R>`

For functional-style codebases:

```kotlin
suspend fun loadUser(id: String): Either<UserError, User>
```

`Left` is the failure case, `Right` is success. Composable via `bind`, `flatMap`, etc. Most Android teams don't reach for this until error-handling complexity demands it.

---

## Real Android Patterns

### 1. Unidirectional Data Flow UI State

```kotlin
sealed interface CartUiState {
    data object Loading : CartUiState
    data class Success(val items: List<CartItem>, val total: Money) : CartUiState
    data class Error(val message: String, val retryable: Boolean) : CartUiState
}

class CartViewModel : ViewModel() {
    private val _state = MutableStateFlow<CartUiState>(CartUiState.Loading)
    val state: StateFlow<CartUiState> = _state.asStateFlow()

    fun load() {
        viewModelScope.launch {
            _state.value = CartUiState.Loading
            _state.value = try {
                CartUiState.Success(repo.getCart(), computeTotal())
            } catch (e: IOException) {
                CartUiState.Error(e.message.orEmpty(), retryable = true)
            }
        }
    }
}

@Composable
fun CartScreen(vm: CartViewModel) {
    val state by vm.state.collectAsStateWithLifecycle()
    when (val s = state) {
        CartUiState.Loading      -> Spinner()
        is CartUiState.Success   -> CartList(s.items, s.total)
        is CartUiState.Error     -> ErrorBanner(s.message, retryable = s.retryable)
    }
}
```

### 2. Network responses with structured errors

```kotlin
sealed interface ApiResult<out T> {
    data class Success<T>(val data: T) : ApiResult<T>
    data class HttpError(val code: Int, val body: String?) : ApiResult<Nothing>
    data object NetworkError : ApiResult<Nothing>
    data object Timeout : ApiResult<Nothing>
    data class Unknown(val cause: Throwable) : ApiResult<Nothing>
}

suspend fun <T> safeApi(call: suspend () -> T): ApiResult<T> = try {
    ApiResult.Success(call())
} catch (e: HttpException) {
    ApiResult.HttpError(e.code(), e.response()?.errorBody()?.string())
} catch (e: SocketTimeoutException) {
    ApiResult.Timeout
} catch (e: IOException) {
    ApiResult.NetworkError
} catch (e: Throwable) {
    if (e is CancellationException) throw e
    ApiResult.Unknown(e)
}
```

Every consumer of `ApiResult<T>` is forced by the compiler to handle each error case.

### 3. Compose Navigation routes (Kotlin 1.9+)

```kotlin
sealed interface Screen {
    @Serializable data object Home : Screen
    @Serializable data class Profile(val userId: String) : Screen
    @Serializable data class Order(val orderId: String, val tab: Tab = Tab.Details) : Screen
}

NavHost(navController, startDestination = Screen.Home) {
    composable<Screen.Home> { HomeScreen(navController) }
    composable<Screen.Profile> { backStackEntry ->
        val args: Screen.Profile = backStackEntry.toRoute()
        ProfileScreen(args.userId)
    }
    composable<Screen.Order> { backStackEntry ->
        val args: Screen.Order = backStackEntry.toRoute()
        OrderScreen(args.orderId, args.tab)
    }
}
```

Type-safe routes — no string deeplink keys. The compiler checks every navigation target.

### 4. RecyclerView/`LazyColumn` heterogeneous items

```kotlin
sealed interface FeedItem {
    data class Header(val title: String) : FeedItem
    data class Post(val id: String, val text: String) : FeedItem
    data class Ad(val campaignId: String) : FeedItem
    data object Divider : FeedItem
}

LazyColumn {
    items(feed, key = { it.id() }) { item ->
        when (item) {
            is FeedItem.Header -> HeaderRow(item.title)
            is FeedItem.Post   -> PostRow(item.id, item.text)
            is FeedItem.Ad     -> AdRow(item.campaignId)
            FeedItem.Divider   -> Divider()
        }
    }
}
```

### 5. Type-state pattern (compile-time state machines)

```kotlin
sealed interface ConnectionState
data object Disconnected : ConnectionState
data class Connecting(val attempt: Int) : ConnectionState
data class Connected(val sessionId: String) : ConnectionState

class Connection(private var state: ConnectionState = Disconnected) {
    fun connect(): Connection { state = Connecting(1); /* … */; return this }
    fun send(msg: String) {
        require(state is Connected) { "Must be connected; was $state" }
        // send
    }
}
```

A more advanced variant uses generic phantom types so the *type* of `Connection` changes as transitions happen — `send` only exists on `Connection<Connected>`. Powerful for SDKs; usually overkill for app code.

---

## Polymorphic Serialization

Reflection-based JSON parsers can't know which subclass to instantiate when reading a sealed type. You need polymorphic adapters.

### kotlinx.serialization — first-class support

```kotlin
@Serializable
sealed interface ApiResponse {
    @Serializable @SerialName("success")
    data class Success(val data: String) : ApiResponse

    @Serializable @SerialName("error")
    data class Error(val message: String) : ApiResponse
}

val json = Json { ignoreUnknownKeys = true; classDiscriminator = "type" }
val r = json.decodeFromString<ApiResponse>("""{"type":"success","data":"ok"}""")
```

The `classDiscriminator` field (here `"type"`) tells the parser which subclass to construct. With Moshi, you do this manually via `PolymorphicJsonAdapterFactory`.

### Moshi

```kotlin
val moshi = Moshi.Builder()
    .add(
        PolymorphicJsonAdapterFactory.of(ApiResponse::class.java, "type")
            .withSubtype(ApiResponse.Success::class.java, "success")
            .withSubtype(ApiResponse.Error::class.java, "error")
    )
    .build()
```

**Gson** has poor support — switch to Moshi or kotlinx for sealed deserialization.

---

## SDK and Public API Considerations

If you publish a sealed type as a public SDK API, you've locked yourself out of adding *new* subclasses in a minor release. Adding a new case will break consumers' `when` exhaustiveness checks — a major-version event.

| Scenario | Choice |
|---|---|
| Internal app code | Sealed — adding cases is what you want |
| Public SDK to consumers you control | Sealed with major-version cadence |
| Public SDK to unknown consumers | Open `interface` + private impls, or sealed with a documented "Unknown" fallback case |

A common compromise: include an `Unknown` case in your sealed type:

```kotlin
public sealed interface PaymentMethod {
    public data class Card(val last4: String) : PaymentMethod
    public data class UpiId(val handle: String) : PaymentMethod
    public data class Unknown(val raw: Map<String, Any?>) : PaymentMethod
}
```

Now, when the server starts sending a new payment type, old clients whose parser maps unrecognised values to `Unknown` show a fallback instead of crashing. Adding the new subclass to the SDK still breaks exhaustive `when`s when consumers upgrade, so it remains a source-breaking change.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| New subclass added; build still passes | `else ->` in a `when` | Remove `else`; use expression context |
| Sealed-subject statement is not exhaustive | Older Kotlin language mode | Use expression context there; Kotlin 1.7+ checks these statements by default |
| `IllegalStateException: Polymorphic` on JSON parse | Sealed without polymorphic adapter | kotlinx `@SerialName` discriminator or Moshi `PolymorphicJsonAdapterFactory` |
| Refactor breaks 50 files | Added a case to a widely-used sealed | Often intentional; otherwise carve a narrower hierarchy |
| Sealed leaks DB entity to UI | Same sealed type used across layers | Split: domain `Result` + UI `UiState`, mapped between layers |
| `data class Loading()` allocates per state | Should be `data object` | Convert to `data object` |
| Subclass not found at runtime | Subclass in different module | Move to the same module as the parent (Kotlin 1.5+ requires this) |
| Cannot inherit from a data class | Data classes are final | Use an eligible ordinary/sealed superclass; data classes may extend it |
| `when` over a generic sealed loses type info | Generic `Result<Nothing>` for terminal cases | Use `Result<Nothing>` + `out T` covariance |
| SDK consumers' code breaks on minor version | Added a sealed subclass | Treat exhaustiveness as a source-compatibility promise; Unknown only helps with explicit wire fallback mapping |

---

## Staff Engineer Lens

When reviewing sealed-type usage, I look for:

1. **Boolean-and-nullable state.** `data class State(val isLoading: Boolean, val data: X?, val error: String?)` is always wrong — paradoxes are representable. Push to sealed.
2. **`else` in `when` over sealed.** Auto-flag. Explicit branches preserve exhaustiveness feedback. Adding an else bypasses that feedback.
3. **Enum with mismatched fields.** `enum class Status { OK, ERR }` paired with `errorMsg: String?` — sealed instead.
4. **Sealed leaking across layers.** A `sealed interface CartResult` returned from the data layer reused as the UI state is a coupling smell. Map between layers.
5. **`data class` instead of `data object` for stateless cases.** Wasteful allocation per state emission. Convert to object.
6. **Public SDK sealed evolution.** Adding a direct case affects exhaustive callers; plan compatibility. An Unknown wire-value fallback does not make arbitrary new subclasses compatible.
7. **Polymorphic JSON without explicit discriminator.** Reflection libs guess wrong. Set the discriminator yourself.
8. **Missing `key = { it.id() }` on `LazyColumn`** with a sealed `FeedItem`. Compose can't diff items by type alone; needs stable keys.

---

## Common Misconceptions

- **"Sealed classes are just enums."** False. Enum cases are singletons of the *same* class. Sealed subclasses are *different* classes, each with their own fields and behavior.
- **"Sealed types make every branch safe."** Kotlin 1.7+ enforces exhaustiveness for sealed-subject statements and expressions, but an `else` still hides omitted specific cases.
- **"All subclasses must be nested inside the sealed type."** False. Direct subclasses can be top-level in the same package/module. Indirect subclasses follow the openness of their direct parent.
- **"Sealed = bad for SDKs."** Not always, but adding a subclass can break exhaustive consumers. Plan the compatibility contract; Unknown only handles data that a parser explicitly maps to it.
- **"You can extend a sealed type if you really need to."** False. The compiler refuses. That's the point.
- **"Sealed types are slower because of all the `is` checks."** Negligible. The JIT compiles each `is` check to a single instanceof; far cheaper than the bugs it prevents.

---

## Probing Questions

1. Walk through three real-world signals that an `enum class` should be a `sealed interface`.
2. When does Kotlin enforce exhaustiveness on a `when` over a sealed type, and when doesn't it?
3. Why is `else ->` in a `when` over a sealed type considered an anti-pattern? Walk through what it costs.
4. Compare `sealed class` vs `sealed interface`. Why is `sealed interface` the modern preference?
5. Your `data class HomeState(val isLoading: Boolean, val data: List<Item>?, val error: String?)` has 8 combinations but only 3 valid. Refactor it.
6. You ship `sealed interface PaymentMethod` as a public SDK. Six months later, marketing demands you add `CryptoWallet`. What just broke?
7. Why does Gson struggle with sealed-class deserialization and how do you fix it (Moshi or kotlinx)?
8. Walk through how `out T` (covariance) interacts with a generic `Resource<T>` to make `Resource<Nothing>` assignable everywhere.
9. Compare `kotlin.Result<T>` with a custom `sealed interface ApiResult<T>`. When do you reach for each?
10. Type-state pattern: explain how phantom generic types + sealed states can make `Connection.send()` only compile when connected.
11. You have `sealed interface Screen` for Compose navigation. What's the SDK / version concern when adding a new screen?
12. Multi-module: which module must the subclasses live in relative to the sealed parent? (Kotlin 1.5+, 1.7+)
13. Compare `data object` vs `object` vs `data class()` for stateless sealed branches. Which do you pick and why?

## Answer Key

1. **Walk through three real-world signals that an `enum class` should be a `sealed interface`.**
   1) The cases need to hold different types of data (e.g., a `Success` case holds a payload, while an `Error` case holds an exception). 2) The cases need different shapes or fields entirely. 3) You need multiple instances of the same case with different state (enums are singletons).
2. **When does Kotlin enforce exhaustiveness on a `when` over a sealed type, and when doesn't it?**
   Kotlin 1.7+ enforces exhaustiveness for sealed-subject expressions and statements. Before 1.7, non-exhaustive statements could compile (with migration warnings in 1.6); expressions already required coverage.
3. **Why is `else ->` in a `when` over a sealed type considered an anti-pattern? Walk through what it costs.**
   `else ->` bypasses the compiler's exhaustiveness check. If a new subclass is added to the sealed hierarchy later, the compiler will not flag the missing case in the `when` block. It will silently fall into the `else` branch, hiding potential bugs and making refactoring brittle.
4. **Compare `sealed class` vs `sealed interface`. Why is `sealed interface` the modern preference?**
   A `sealed class` can have constructors and hold shared state, but restricts subclasses to single inheritance. A `sealed interface` cannot hold state, but allows a single subclass to implement multiple sealed interfaces (multi-categorization) and doesn't consume the single class inheritance slot. It's the modern preference because most ADTs don't need shared state in the parent.
5. **Your `data class HomeState(val isLoading: Boolean, val data: List<Item>?, val error: String?)` has 8 combinations but only 3 valid. Refactor it.**
   `sealed interface HomeState { data object Loading : HomeState; data class Success(val data: List<Item>) : HomeState; data class Error(val message: String) : HomeState }`
6. **You ship `sealed interface PaymentMethod` as a public SDK. Six months later, marketing demands you add `CryptoWallet`. What just broke?**
   Every consumer of your SDK who wrote an exhaustive `when` block over `PaymentMethod` will suddenly face a compilation error upon upgrading to the new minor version, because their `when` is no longer exhaustive. This forces a breaking API change (major version bump).
7. **Why does Gson struggle with sealed-class deserialization and how do you fix it (Moshi or kotlinx)?**
   Gson relies heavily on reflection and lacks built-in support for polymorphic deserialization based on a discriminator field (e.g., `"type": "success"`). To fix it, use `kotlinx.serialization` with `@SerialName` and a configured `classDiscriminator`, or Moshi with a `PolymorphicJsonAdapterFactory`.
8. **Walk through how `out T` (covariance) interacts with a generic `Resource<T>` to make `Resource<Nothing>` assignable everywhere.**
   `Nothing` is a subtype of every type in Kotlin. By defining the sealed class as `Resource<out T>`, we declare that a `Resource` of a subtype can be assigned to a `Resource` of a supertype. Therefore, `Resource<Nothing>` is a subtype of `Resource<User>`, allowing singletons like `object Loading : Resource<Nothing>` to be assigned to any typed `Resource` variable.
9. **Compare `kotlin.Result<T>` with a custom `sealed interface ApiResult<T>`. When do you reach for each?**
   Reach for `kotlin.Result<T>` for generic operations where failure is simply represented by a `Throwable` and performance (via inline value classes) is critical. Reach for a custom `sealed interface ApiResult<T>` when you need structured, domain-specific error cases (e.g., `HttpError`, `NetworkError`) that force callers to handle distinct failure modes differently.
10. **Type-state pattern: explain how phantom generic types + sealed states can make `Connection.send()` only compile when connected.**
    By parameterizing the class (e.g., `class Connection<State>`), you can define methods as extensions or member functions bound to a specific state type: `fun Connection<Connected>.send()`. The `send` method physically won't exist on a variable typed as `Connection<Disconnected>`, making invalid state calls uncompilable.
11. **You have `sealed interface Screen` for Compose navigation. What's the SDK / version concern when adding a new screen?**
    If `Screen` is exposed to external modules or an SDK, adding a new screen breaks exhaustive `when` statements in the consuming code. If it's internal app code, it's safe and desirable to get those compile errors.
12. **Multi-module: which module must the subclasses live in relative to the sealed parent? (Kotlin 1.5+, 1.7+)**
    Direct subclasses must be in the same package and module. Kotlin 1.5 enabled this package/module-wide arrangement; older sealed-class rules were more restrictive. Multiplatform source-set rules also apply.
13. **Compare `data object` vs `object` vs `data class()` for stateless sealed branches. Which do you pick and why?**
    Use object for a singleton, or data object for generated readable toString/value-style object semantics. An empty `data class()` does not compile: data classes require a primary-constructor property. Data objects were experimental in Kotlin 1.7.20, previewed in 1.8.20 and became stable in 1.9.0.

---

## Further Reading

- [`data-classes.md`](data-classes.md) — the structures that fill sealed branches.
- [`null-safety.md`](null-safety.md) — `Result`/sealed as alternatives to nullable returns.
- [`generics.md`](../type-system/generics.md) — generic sealed hierarchies (`Resource<out T>`).
- [`variance.md`](../type-system/variance.md) — `out T` covariance for `Resource<Nothing>` assignability.
- [`coroutines.md`](../coroutines-and-flow/coroutines.md) — modeling success/failure of suspend operations.
- [`../patterns/state.md`](../../patterns/state.md) — the state-pattern that sealed types enable.
- [`../principles/make-invalid-states-impossible.md`](../../principles/make-invalid-states-impossible.md) — design principle sealed types deliver.
- [`../android/architecture/viewmodel.md`](../../android/architecture/viewmodel.md) — sealed `UiState` flowing from ViewModel.
- [Kotlin Docs — Sealed classes](https://kotlinlang.org/docs/sealed-classes.html) — official reference.
- [Kotlin docs — Sealed classes and interfaces](https://kotlinlang.org/docs/sealed-classes.html) — official language reference.
- [Jaewoong Eum — "Modeling Retrofit Responses With Sealed Classes and Coroutines"](https://getstream.io/blog/modeling-retrofit-responses/) — practical patterns.
- [Arrow — `Either<L, R>`](https://arrow-kt.io/) — functional alternative for typed errors.

### Official verification references

- [Primary documentation or owning implementation](https://developer.android.com/kotlin/coroutines/coroutines-best-practices#exceptions)
- [Primary documentation or owning implementation](https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/run-catching.html)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/api-guidelines-backward-compatibility.html)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/compatibility-guide-17.html#make-when-statements-with-enum-sealed-and-boolean-subjects-exhaustive-by-default)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/data-classes.html)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/sealed-classes.html#use-sealed-classes-with-when-expression)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/whatsnew15.html#sealed-interfaces)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/whatsnew19.html#stable-data-objects-for-symmetry-with-data-classes)
