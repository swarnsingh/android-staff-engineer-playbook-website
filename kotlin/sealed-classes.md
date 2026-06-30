# Sealed Classes and Interfaces

> Sealed types are how you make invalid states impossible in modern Android. Every `UiState`, every `NetworkResult`, every navigation route in a well-architected Compose app sits in a sealed hierarchy. Staff-level mastery means knowing when sealed beats enum, when it beats interface, when it beats data class with nullable fields, and the traps (else branches, polymorphic JSON, SDK evolution) that turn the safety net into a footgun.

---

## Overview

A `sealed class` or `sealed interface` is a closed type hierarchy. You declare it like a regular type, but only subclasses defined in the same module (and same package since Kotlin 1.7) can extend it. The compiler knows the exhaustive list of subclasses at compile time, which unlocks:

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
4. **Module-local.** Subclasses must live in the same module (Kotlin 1.5+) and same package (Kotlin 1.7+) as the parent.

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

Exhaustiveness is enforced only when `when` is used as an **expression** (its result is used) — or when the language flag for "exhaustive when statements" is enabled.

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

Kotlin 1.7+ added the `-Xenable-exhaustive-when-statements` opt-in to enforce on statements too. Worth turning on.

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
- `out T` makes the type **covariant** — a `Resource<Admin>` can be used where `Resource<User>` is expected (see [`variance.md`](variance.md)).
- `Loading` and `Failure` parametrize on `Nothing` — `Resource<Nothing>` is assignable to `Resource<T>` for any `T`. This is the standard ADT idiom.

### `Result<T>` — Kotlin's built-in

```kotlin
suspend fun loadUser(id: String): Result<User> = runCatching {
    api.getUser(id)
}

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

Now adding a new method type in the next minor version downgrades to `Unknown` for old clients, instead of crashing or breaking their build.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| New subclass added; build still passes | `else ->` in a `when` | Remove `else`; use expression context |
| `when` not enforced exhaustive | Used as statement, Kotlin < 1.7 default | Use as expression; or `.let { }`; or enable exhaustive-statement flag |
| `IllegalStateException: Polymorphic` on JSON parse | Sealed without polymorphic adapter | kotlinx `@SerialName` discriminator or Moshi `PolymorphicJsonAdapterFactory` |
| Refactor breaks 50 files | Added a case to a widely-used sealed | Often intentional; otherwise carve a narrower hierarchy |
| Sealed leaks DB entity to UI | Same sealed type used across layers | Split: domain `Result` + UI `UiState`, mapped between layers |
| `data class Loading()` allocates per state | Should be `data object` | Convert to `data object` |
| Subclass not found at runtime | Subclass in different module | Move to the same module as the parent (Kotlin 1.5+ requires this) |
| Cannot inherit data class from another sealed | Data class restrictions | Use regular class, or restructure |
| `when` over a generic sealed loses type info | Generic `Result<Nothing>` for terminal cases | Use `Result<Nothing>` + `out T` covariance |
| SDK consumers' code breaks on minor version | Added a sealed case in a public API | Either MAJOR bump or include `Unknown` escape hatch |

---

## Staff Engineer Lens

When reviewing sealed-type usage, I look for:

1. **Boolean-and-nullable state.** `data class State(val isLoading: Boolean, val data: X?, val error: String?)` is always wrong — paradoxes are representable. Push to sealed.
2. **`else` in `when` over sealed.** Auto-flag. The whole point of sealed is exhaustiveness. Removing it bypasses the safety net.
3. **Enum with mismatched fields.** `enum class Status { OK, ERR }` paired with `errorMsg: String?` — sealed instead.
4. **Sealed leaking across layers.** A `sealed interface CartResult` returned from the data layer reused as the UI state is a coupling smell. Map between layers.
5. **`data class` instead of `data object` for stateless cases.** Wasteful allocation per state emission. Convert to object.
6. **Public SDK sealed without escape hatch.** Adding a case is a MAJOR break; include `Unknown` or document the cadence.
7. **Polymorphic JSON without explicit discriminator.** Reflection libs guess wrong. Set the discriminator yourself.
8. **Missing `key = { it.id() }` on `LazyColumn`** with a sealed `FeedItem`. Compose can't diff items by type alone; needs stable keys.

---

## Common Misconceptions

- **"Sealed classes are just enums."** False. Enum cases are singletons of the *same* class. Sealed subclasses are *different* classes, each with their own fields and behavior.
- **"Sealed types make `when` exhaustive everywhere."** Only as expressions (or with the explicit `-Xenable-exhaustive-when-statements` flag). Statements aren't enforced by default.
- **"All subclasses must be nested inside the sealed type."** False. They must be in the same package (Kotlin 1.7+) and same module (1.5+). Top-level subclasses are fine.
- **"Sealed = bad for SDKs."** Not always — but adding a case is a major-version event. Plan accordingly or include `Unknown`.
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

---

## Further Reading

- [`data-classes.md`](data-classes.md) — the structures that fill sealed branches.
- [`null-safety.md`](null-safety.md) — `Result`/sealed as alternatives to nullable returns.
- [`generics.md`](generics.md) — generic sealed hierarchies (`Resource<out T>`).
- [`variance.md`](variance.md) — `out T` covariance for `Resource<Nothing>` assignability.
- [`coroutines.md`](coroutines.md) — modeling success/failure of suspend operations.
- [`../patterns/state.md`](../patterns/state.md) — the state-pattern that sealed types enable.
- [`../principles/make-invalid-states-impossible.md`](../principles/make-invalid-states-impossible.md) — design principle sealed types deliver.
- [`../android/architecture/viewmodel.md`](../android/architecture/viewmodel.md) — sealed `UiState` flowing from ViewModel.
- [Kotlin Docs — Sealed classes](https://kotlinlang.org/docs/sealed-classes.html) — official reference.
- [Roman Elizarov — "Sealed classes"](https://elizarov.medium.com/) — design notes from the language team.
- [Jake Wharton — "Modeling Retrofit responses with sealed classes and coroutines"](https://github.com/JakeWharton) — practical patterns.
- [Arrow — `Either<L, R>`](https://arrow-kt.io/) — functional alternative for typed errors.
