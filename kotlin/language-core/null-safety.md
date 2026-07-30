# Null Safety

> Tony Hoare called the null reference his "billion-dollar mistake." Android's #1 historical crash class is `NullPointerException`. Kotlin moves null detection from runtime to compile time by baking nullability into the type system. Knowing the operators isn't enough at staff level — you need to know the Android boundaries where the type system breaks down (Java interop, JSON, ViewBinding, reflection), and how to seal those leaks.

---

## Overview

In Java, *any* object reference can silently be `null`. In Kotlin, `String` and `String?` are different types. The compiler refuses to compile anything that could blow up:

```kotlin
val name: String = "Alice"      // never null
val maybe: String? = readLine()  // may be null
name.length                      // ✅ compiles
maybe.length                     // ❌ compile error: "Only safe (?.) or non-null asserted (!!.) calls allowed"
```

The result: an entire class of crash is eliminated **before the code even runs**.

---

## Why It Matters (Android Context)

Pre-Kotlin Android code was full of:

```java
if (user != null && user.getAddress() != null && user.getAddress().getCity() != null) {
    textView.setText(user.getAddress().getCity());
}
```

Defensive walls everywhere. Easy to forget one. NPE in production. Crashlytics filled with `NullPointerException at ProfileActivity.onCreate(line 47)`.

Kotlin makes the type system carry the burden. The compiler refuses to let you forget.

---

## First Principles

1. **Types carry nullability.** `T` and `T?` are distinct. No implicit conversion from `T?` to `T`.
2. **Compiler enforces handling.** Every nullable access requires explicit handling.
3. **Opt-in danger.** `!!` is the explicit "trust me, throw NPE if I'm wrong" escape hatch.

---

## Mental Model — Sealed vs Locked Boxes

- **Java box** — labeled "Shoes." You reach in blindly. Sometimes shoes; sometimes a rat trap (`null`). You learn to always poke with a stick first.
- **Kotlin transparent box** (`Shoes`) — you see shoes; just grab them.
- **Kotlin locked box** (`Shoes?`) — you must unlock (null-check) before reaching in.

---

## The Operators — When to Use What

| Operator | Reads as | Returns null when… | Use when |
|---|---|---|---|
| `?.` (safe call) | "if non-null, call" | Receiver is null | Chain calls through possibly-null receivers |
| `?:` (Elvis) | "or else" | Left-hand is null | Provide a default value |
| `!!` (not-null assert) | "or throw NPE" | Never (throws if null) | You can prove non-null but compiler can't |
| `?.let { }` | "if non-null, do" | Receiver is null | Run a block on the value if it exists |
| `requireNotNull(x)` | "or throw IAE" | Never (throws) | Validate input at boundaries |
| `checkNotNull(x)` | "or throw ISE" | Never (throws) | Validate internal invariants |
| `x.orEmpty()` | "or empty" | Never | Treat nullable collections/strings as empty |

### The `?.` + `?:` combo is the workhorse

```kotlin
data class UserResponse(val profile: Profile?)
data class Profile(val address: Address?)
data class Address(val city: String?)

// 20 lines of Java collapse to 1 line:
val city: String = response.profile?.address?.city ?: "Unknown City"
```

Each `?.` short-circuits the chain to `null` if anything is missing. The `?:` provides a final fallback. The variable is non-null `String` — no further checks needed downstream.

### `?.let { }` for non-null branches

```kotlin
viewModel.user?.let { user ->
    tvName.text = user.name
    tvEmail.text = user.email
    // 'user' is non-null inside this block
}
```

Use `let` when you need:
- The receiver as a different name (`it` or rename to `user`).
- Multiple operations on a non-null value.
- A different return type than the receiver.

Pair with `?:` for an "else" branch:

```kotlin
viewModel.user?.let { showProfile(it) } ?: showLogin()
```

### `requireNotNull` and `checkNotNull` over `!!`

These give you a *named* exception with a *message*. `!!` gives you `NullPointerException at line 47` with no context.

```kotlin
// Bad
val userId = arguments?.getString("user_id")!!

// Better — input validation at the boundary
val userId = requireNotNull(arguments?.getString("user_id")) {
    "ProfileFragment must be created with user_id argument"
}
```

When this fires, the crash report says exactly what went wrong, who's expected to provide it, and where.

---

## `lateinit` vs `by lazy` vs Nullable

Three options when a non-null property can't be initialized at construction. Pick by use case:

| | `lateinit var x: String` | `val x: String by lazy { ... }` | `var x: String? = null` |
|---|---|---|---|
| Initialized | Manually before first use | Lazily on first read | At declaration |
| Reassignable | Yes (`var`) | No (`val`) | Yes |
| Access before init | `UninitializedPropertyAccessException` | Block runs | Returns `null` |
| Thread-safe | No | Yes by default (LazyThreadSafetyMode.SYNCHRONIZED) | No |
| Works with | `var` only; not primitives | `val` only | Anything |
| Use case | DI (`@Inject`), Android lifecycle (`onCreate`), tests | Expensive immutable derived value | Truly optional state |

### Typical Android `lateinit` usage

```kotlin
@AndroidEntryPoint
class MainActivity : AppCompatActivity() {
    @Inject lateinit var analytics: Analytics      // Hilt fills it in
    private lateinit var binding: ActivityMainBinding   // View binding set in onCreate

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)
        analytics.track("screen.main")  // both lateinits are now valid
    }
}
```

### `by lazy` for expensive derived values

```kotlin
class MapHelper(private val context: Context) {
    val markerIcon: BitmapDescriptor by lazy {
        BitmapDescriptorFactory.fromResource(R.drawable.pin)
    }
}
```

`markerIcon` is computed once on first access, cached forever. Thread-safe by default.

### `Delegates.notNull<T>()` — the lateinit equivalent for primitives

```kotlin
var userAge: Int by Delegates.notNull()
```

`lateinit` doesn't work with primitives (`Int`, `Boolean`, etc.). `Delegates.notNull<T>()` plugs the gap.

---

## Smart Casts — When the Compiler Auto-Narrows

```kotlin
fun process(name: String?) {
    if (name != null) {
        println(name.length)   // smart-cast to String inside the if
    }
}
```

Inside the `if`, the compiler knows `name` cannot be null. No `?.` or `!!` needed.

### When smart cast fails

```kotlin
class User {
    var name: String? = null

    fun process() {
        if (name != null) {
            println(name.length)
            //      ^^^^ ERROR: Smart cast to 'String' is impossible,
            //           because 'name' is a mutable property that could
            //           have been changed by another thread.
        }
    }
}
```

**Reason:** Another thread could null `name` between the check and the access. Compiler refuses.

**Fixes:**

```kotlin
// 1. Local val (most idiomatic)
val n = name
if (n != null) {
    println(n.length)
}

// 2. ?.let
name?.let { println(it.length) }

// 3. Make it immutable
val name: String? = ...
```

Same problem with:
- Open / abstract properties (overrides may have side effects).
- Properties with custom getters (could return different values on each call).
- Properties in another module (the compiler can't see the implementation).

---

## Platform Types — The Java Boundary Hole

When Kotlin calls Java code that lacks `@Nullable` / `@NonNull` annotations, the compiler doesn't know if a value can be null. It creates a **platform type**, shown as `String!`:

```java
// Java
public class LegacyApi {
    public String getName() { return name; }   // no @Nullable / @NonNull
}
```

```kotlin
// Kotlin
val name = LegacyApi().getName()   // type is `String!` — null-safety disabled
println(name.length)                // compiles, runtime NPE if name was null
```

`String!` means "either `String` or `String?`, you decide." The compiler stops protecting you.

### Defenses

**1. Wrap Java APIs at the boundary:**

```kotlin
// Anti-corruption layer
class LegacyApiWrapper(private val legacy: LegacyApi) {
    fun getName(): String? = legacy.name   // explicit nullable
}
```

**2. Use `@Nullable` / `@NonNull` annotations in Java sources** if you own them. Kotlin will then enforce.

**3. Treat all platform types as nullable** unless documented otherwise. Defensive `?.` and `?:` are cheap.

**4. JSpecify / JetBrains annotations** — for libraries that ship `package-info.java` with `@NullMarked`, Kotlin gets accurate nullability for free.

---

## Reflection-Based Libraries Can Lie

`Gson` (and any reflection-based deserializer) can violate Kotlin's null safety:

```kotlin
data class User(val name: String, val age: Int)

// Server returns: { "age": 25 }   ← name missing!
val user = Gson().fromJson(json, User::class.java)
// user.name is now null, but type system thinks it's String
println(user.name.length)   // NPE — and your "non-null String" was a lie
```

Gson uses `Unsafe` allocation: it constructs the object **without calling the constructor**, then injects fields by reflection. Constructor checks (`Intrinsics.checkNotNullParameter`) never run.

**Fix:** use Moshi or kotlinx.serialization — both honor Kotlin nullability and refuse to deserialize missing non-null fields:

```kotlin
@JsonClass(generateAdapter = true)
data class User(val name: String, val age: Int)

Moshi.Builder().build().adapter(User::class.java).fromJson(json)
// JsonDataException: Required value 'name' missing at $.name
```

---

## How Kotlin Enforces Null Safety at the JVM Boundary

The JVM has no concept of null-safe types. `String` and `String?` both compile to `java.lang.String`. Then how does Kotlin enforce non-null?

**Intrinsics** — compiler-inserted runtime checks.

```kotlin
fun printName(name: String) {
    println(name.length)
}
```

Compiles to (roughly):

```java
public static final void printName(@NotNull String name) {
    Intrinsics.checkNotNullParameter(name, "name");   // inserted by compiler
    System.out.println(name.length());
}
```

If a Java caller passes `null`, the function fails **at the boundary** with a clear message ("Parameter specified as non-null is null: ..., name"), rather than crashing deep inside business logic.

Likewise, when you call a Kotlin function returning a non-null type from Java, the return is checked.

---

## Real Android NPE Traps

| Source | Why nullable | Pattern |
|---|---|---|
| `findViewById<T>(R.id.x)` | View might not exist in current layout | Prefer ViewBinding |
| `intent.getStringExtra("key")` | Extra might not be present | `?: error("key required")` or `requireNotNull` |
| `arguments?.getString("key")` | Fragment without args | Validate in `newInstance()` factory |
| `Bundle.getString("key")` | Key missing or wrong type | Validate at boundary |
| `binding` after `onDestroyView` | View destroyed but ref kept | Set `_binding = null` in `onDestroyView()` |
| `getActivity()` / `requireActivity()` | Fragment detached | Use `requireActivity()` (throws clearly) |
| `getContext()` | Same | Use `requireContext()` |
| `SharedPreferences.getString(key, null)` | Default returns null | Provide non-null default |
| `Cursor.getString(idx)` | Column NULL | Check `isNull(idx)` |
| `JSONObject.optString(key)` | Returns `"null"` (string!) when missing | Use Moshi/kotlinx instead |
| `LiveData.value` | No value emitted yet | Treat as nullable |
| `StateFlow.value` | None — always has a value | Non-null |
| Compose `LocalContext.current` | Has a default `error()` | OK in @Composable scope |

### ViewBinding lifecycle pattern

```kotlin
class CartFragment : Fragment() {
    private var _binding: FragmentCartBinding? = null
    private val binding get() = _binding!!   // valid only between onCreateView and onDestroyView

    override fun onCreateView(
        inflater: LayoutInflater, container: ViewGroup?, state: Bundle?,
    ): View {
        _binding = FragmentCartBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onDestroyView() {
        _binding = null    // release view ref to avoid leak
        super.onDestroyView()
    }
}
```

The `!!` here is intentional and safe — `binding` is only accessed between `onCreateView` and `onDestroyView`, where `_binding` is guaranteed non-null.

---

## Don't Use `null` for Errors — Use `Result` or Sealed

`fun pay(): String?` is ambiguous. Does `null` mean:

- Network timed out?
- Card declined?
- User cancelled?
- Already paid?

You lose information.

**Better:**

```kotlin
sealed interface PaymentResult {
    data class Success(val transactionId: String) : PaymentResult
    data object NetworkTimeout : PaymentResult
    data class Declined(val reason: String) : PaymentResult
    data object UserCancelled : PaymentResult
}

fun pay(): PaymentResult { /* ... */ }

when (val result = pay()) {
    is PaymentResult.Success -> showReceipt(result.transactionId)
    PaymentResult.NetworkTimeout -> showRetry()
    is PaymentResult.Declined -> showReason(result.reason)
    PaymentResult.UserCancelled -> goBack()
}
```

The `when` is exhaustive (compiler enforces). Every error path is visible. See [`sealed-classes.md`](sealed-classes.md).

Or use Kotlin's `Result<T>`:

```kotlin
suspend fun pay(): Result<String> = runCatching { api.pay() }

pay()
    .onSuccess { showReceipt(it) }
    .onFailure { showError(it.message) }
```

Use `Result` when failure is opaque (just an exception); use sealed when failure has structure.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Crash: `UninitializedPropertyAccessException` | Access `lateinit var` before init | Initialize in `onCreate` / before first use; or `isInitialized` check |
| Crash: `NullPointerException` despite Kotlin code | `!!` on a value that was null | Replace with `?.let`, `?:`, or `requireNotNull` with message |
| Compile error: "Smart cast impossible" on mutable property | `var` could change concurrently | Local `val` copy, or `?.let` |
| Production NPE in JSON parsing | Gson reflection bypass | Switch to Moshi/kotlinx.serialization |
| Mystery NPE inside Java library call | Platform type returned null | Treat all Java returns as `T?` until proven otherwise |
| Crash on fragment recreation | Accessed binding after `onDestroyView` | Set `_binding = null` in `onDestroyView` |
| `intent.getStringExtra("user")` returns null | Caller didn't pass extra | Validate at boundary with `requireNotNull` |
| Compose recomposition crashes after rotation | `lateinit` UI state | Move state into ViewModel/SavedStateHandle |
| `if (x != null) x.foo()` doesn't compile | `x` is mutable property | `x?.foo()` or assign to local val |
| Logs show `null` everywhere | `null` used as error state | Replace with sealed/`Result` |

---

## Staff Engineer Lens

When reviewing nullability, I look at:

1. **Every `!!` is a question.** Reject PRs containing `!!` unless there's a comment that makes the invariant explicit and obvious. Often `requireNotNull(x) { "why" }` is clearer.
2. **`null` as error state.** If a function returns `T?` and the null means "something went wrong," push to model the error explicitly (sealed/`Result`).
3. **Boundary discipline.** Java APIs return platform types (`T!`). Wrap them in an anti-corruption layer that returns explicit `T?` or `T`, so the rest of the codebase stays honest.
4. **Reflection libs.** Gson and similar can lie about types. Move to Moshi/kotlinx.serialization.
5. **`lateinit` discipline.** A class with five `lateinit var`s has re-invented Java's null problem. Either inject them or refactor.
6. **Smart-cast workarounds.** A `?.let` everywhere is fine, but if you see the same `val tmp = x; if (tmp != null)` pattern repeatedly, the underlying class needs immutability or a redesign.

---

## Common Misconceptions

- **"Kotlin apps never NPE."** False. NPE sources: `!!`, platform types from Java, Gson reflection, custom unsafe code.
- **"The JVM treats `String?` differently."** False. Both are `java.lang.String` in bytecode. Null safety is a compile-time enforcement plus runtime `Intrinsics` at boundaries.
- **"`lateinit` makes a property non-null forever."** False. Accessing before init throws. It's "I'll initialize before use" — your contract, not the compiler's.
- **"`!!` is fine if I'm sure."** If you can prove it, the type system should be able to. Refactor instead.
- **"Returning `null` is a clean way to signal error."** Not at staff level. Sealed types make every failure mode named and exhaustive.

---

## Probing Questions

1. What is a Kotlin "platform type" (`String!`)? When do you encounter it, and how do you defend against it?
2. Walk through what bytecode the compiler generates for a `fun greet(name: String)` function. What runtime check does it insert?
3. Why does smart cast fail on a `var` property? Show three ways to work around it.
4. `lateinit` vs `by lazy` vs `var x: String? = null` — when do you pick each?
5. You have a fragment that crashes intermittently with `NullPointerException` accessing `binding.tvName`. What's the most likely cause?
6. Why is using `null` as a return value to indicate an error a code smell at a staff-engineer level? What's the alternative?
7. Walk through how Gson can produce a Kotlin object with a `null` value in a non-null `String` field. How do you prevent it?
8. Give a legitimate use case for `!!`. Give an illegitimate one and the refactor.
9. `requireNotNull` vs `checkNotNull` vs `!!` — when do you use each?
10. A Java library returns `User getUser()` with no annotations. Walk through the wrapper pattern you'd build.
11. ViewBinding lifecycle: why do you set `_binding = null` in `onDestroyView`? What goes wrong if you don't?
12. You have a `SharedFlow<Result<User>>`. Compare this against `StateFlow<User?>`. Which is right when?

## Answer Key

1. **What is a Kotlin "platform type" (`String!`)? When do you encounter it, and how do you defend against it?**
   A platform type (`String!`) occurs when Kotlin calls Java code that lacks `@Nullable`/`@NonNull` annotations. The compiler suspends null-safety checks because it doesn't know if the value can be null. You defend against it by treating all unannotated Java returns as nullable (`T?`), adding annotations to the Java code if possible, or wrapping the Java API in a strict Kotlin anti-corruption layer.
2. **Walk through what bytecode the compiler generates for a `fun greet(name: String)` function. What runtime check does it insert?**
   The compiler generates a public static/instance method with a non-null signature. At the very beginning of the method body, it inserts a call to `Intrinsics.checkNotNullParameter(name, "name")`. If a Java caller bypasses the compiler and passes `null`, this intrinsic immediately throws an `IllegalArgumentException` at the boundary.
3. **Why does smart cast fail on a `var` property? Show three ways to work around it.**
   Smart cast fails on a `var` property because a concurrent thread could mutate the property to `null` between the `!= null` check and the actual usage. Workarounds: 1) Assign to a local `val` first (`val n = name; if (n != null) n.length`); 2) Use the safe call and let (`name?.let { it.length }`); 3) Change the property declaration from `var` to `val` if it's meant to be immutable.
4. **`lateinit` vs `by lazy` vs `var x: String? = null` — when do you pick each?**
   Pick `lateinit` for non-null `var` properties that must be initialized outside the constructor (e.g., DI via `@Inject`, Android `onCreate`). Pick `by lazy` for read-only `val` properties that are expensive to compute and should only be evaluated on their first access. Pick `var x: String? = null` when the absence of a value is a valid, ongoing state of the object.
5. **You have a fragment that crashes intermittently with `NullPointerException` accessing `binding.tvName`. What's the most likely cause?**
   The most likely cause is accessing the `binding` property after `onDestroyView` has been called (e.g., in a delayed coroutine or callback). The ViewBinding pattern sets `_binding = null` in `onDestroyView`, so the forced unwrap (`get() = _binding!!`) throws an NPE when accessed outside the view's active lifecycle.
6. **Why is using `null` as a return value to indicate an error a code smell at a staff-engineer level? What's the alternative?**
   `null` is ambiguous—it doesn't communicate *why* an operation failed (e.g., network timeout vs. unauthorized vs. local error), leading to lossy error handling. The alternative is to return a `sealed interface` representing explicit success/failure states, or `Result<T>` if the error is an opaque exception.
7. **Walk through how Gson can produce a Kotlin object with a `null` value in a non-null `String` field. How do you prevent it?**
   Gson deserializes objects using `Unsafe` allocation, bypassing the class constructor entirely, and then sets fields via reflection. Since the constructor never runs, Kotlin's non-null intrinsic checks are bypassed. If the JSON omits a field, the field remains uninitialized (`null`), violating the type system. Prevent this by using Moshi or `kotlinx.serialization`.
8. **Give a legitimate use case for `!!`. Give an illegitimate one and the refactor.**
   A legitimate use case is inside a Fragment's ViewBinding getter (`val binding get() = _binding!!`), where you strictly control the lifecycle and guarantee it's accessed only between `onCreateView` and `onDestroyView`. An illegitimate use is `intent.getStringExtra("id")!!`, which crashes if the extra is missing. Refactor it to `requireNotNull(intent.getStringExtra("id")) { "Activity requires 'id' extra" }`.
9. **`requireNotNull` vs `checkNotNull` vs `!!` — when do you use each?**
   Use `requireNotNull` when validating arguments or inputs crossing a public boundary (throws `IllegalArgumentException` with a custom message). Use `checkNotNull` when validating internal state or invariants that should never be null if the class is behaving correctly (throws `IllegalStateException`). Avoid `!!` unless you are doing something so localized (like ViewBinding) that a message isn't necessary.
10. **A Java library returns `User getUser()` with no annotations. Walk through the wrapper pattern you'd build.**
    You create a Kotlin anti-corruption layer: `class SafeUserRepo(private val javaRepo: JavaRepo) { fun getUser(): User? = javaRepo.getUser() }`. By explicitly marking the return as `User?`, you force all Kotlin consumers to perform null checks, neutralizing the danger of the platform type.
11. **ViewBinding lifecycle: why do you set `_binding = null` in `onDestroyView`? What goes wrong if you don't?**
    A Fragment instance can outlive its View hierarchy (e.g., when placed on the back stack). The `_binding` holds a strong reference to the entire View tree. If you don't set it to `null` in `onDestroyView`, the Fragment keeps the Views (and associated Bitmaps/Contexts) in memory, causing a massive memory leak until the Fragment itself is destroyed.
12. **You have a `SharedFlow<Result<User>>`. Compare this against `StateFlow<User?>`. Which is right when?**
    `SharedFlow<Result<User>>` models discrete events or commands (e.g., "A login attempt succeeded or failed") where multiple emissions are important and there isn't a single ongoing state. `StateFlow<User?>` models continuous state (e.g., "Who is currently logged in, or null if nobody is") where only the latest value matters and UI components need to react to changes in that state.

---

## Further Reading

- [`sealed-classes.md`](sealed-classes.md) — modeling explicit error states instead of `T?`.
- [`data-classes.md`](data-classes.md) — immutability supports smart casts.
- [`delegation.md`](delegation.md) — `by lazy`, `Delegates.notNull`, `Delegates.observable`.
- [`coroutines.md`](../coroutines-and-flow/coroutines.md) — `Result<T>` in suspend functions.
- [`../principles/make-invalid-states-impossible.md`](../../principles/make-invalid-states-impossible.md) — null-safety as one example of this principle.
- [`../android/architecture/viewmodel.md`](../../android/architecture/viewmodel.md) — state holders and nullability of UI state.
- [Kotlin Docs — Null safety](https://kotlinlang.org/docs/null-safety.html) — official reference.
- [Tony Hoare — "Null References: The Billion Dollar Mistake"](https://www.infoq.com/presentations/Null-References-The-Billion-Dollar-Mistake-Tony-Hoare/) — the apology that started it all.
- [Roman Elizarov — "Dealing with absence of value"](https://elizarov.medium.com/dealing-with-absence-of-value-307b80534903) — Kotlin lead engineer's take.
- [JSpecify](https://jspecify.dev/) — standard nullness annotations for Java/Kotlin interop.
