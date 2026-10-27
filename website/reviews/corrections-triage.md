# Corrections Triage

**Approval update, 27 October 2026:** The owner explicitly requested the official-source fixes and source PR. Ten existing proposals in `corrections-language.json` are now approved and applied, alongside 76 targeted review replacements. [The verification report](OFFICIAL-CONTENT-VERIFICATION-2026-10-27.md) defines this subset. The older verdicts below remain review recommendations for the other proposals; they are not blanket approvals.


Codex proposed 292 corrections to the original chapters, stored in `website/content/corrections-*.json`. Application requires owner approval; the dated subset above now has that approval. Approved corrections appear on the website only, visibly marked; the original Markdown is never edited.

**Verdicts**

- **Approve:** the original is wrong or misleading, and the proposed text is right.
- **Approve with edit:** the original is wrong, but the proposed text needs the change shown.
- **Reject:** the original is fine, or the change is only rewording.

**Evidence** means the claim was compiled and run locally (Kotlin 2.4.21, kotlinx.coroutines 1.11.0, JDK 17), or checked against the current official source named.

To approve, mark the row. Approved rows get `"status": "approved"` in the JSON; "with edit" rows also get the amended text. The exact original and replacement for every "with edit" row is in [`corrections-with-edits.md`](corrections-with-edits.md).

## Overview

All 292 proposals are reviewed, plus 3 new errors found while checking (F17, BY8, K1). This table replaces Codex's earlier audit notes, which remain in git history.

| | Rows |
|---|---|
| Approve | 199 |
| Approve with edit | 23 (3 of them new findings) |
| Reject | 73 |
| **Total** | **295** |

The language, type-system and compiler chapters are mostly real errors. Coroutines and Flow have the most rejections: there, many proposals hedge statements that are correct as taught.

Some rows show that an example in the original does not compile or fails when run:
- **Do not compile:** GE1, DE2, DE9, K1.
- **Tests that fail:** CH7, CA6, TE4, CO6, C40.
- **Hang forever:** CH4, C24.

**Revised after Codex's review (2026-10-25).** Codex re-checked the triage and was right on these points, each reproduced locally:
- **CH4:** the first amended actor still left queued checkouts waiting forever when the owner's scope was cancelled. The new text fails them and closes the channel.
- **C24:** `SupervisorJob` keeps later saves alive, but an uncaught failure still crashes. The new text catches the expected failure.
- **VA2:** now approved with edit: boxing happens where a value enters generic code, so one box can fill several slots.
- **C21, C47:** now approved: `async` gives concurrency; parallelism depends on the dispatcher.
- **C32–C35, C58, C61:** now approved: only cancellable suspending calls throw after cancellation (`delay(0)` and `currentCoroutineContext()` return normally in a cancelled `finally`), `yield` need not suspend, and `NonCancellable` protects cleanup without guaranteeing it finishes.

Two proposals were themselves wrong, so they are rejected or replaced (Codex confirmed both):
- **E4:** the API 33 `Bundle.getParcelable` overload is unbounded.
- **JV12:** `toString()` on a platform-typed null crashes; it does not return "null".

## Variables — 16 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| V1 | A `val xs: List<Int>` is safe to share because `listOf(...)` is immutable | `listOf` returns a read-only view, not an immutable list | Approve | Run: `(listOf(1,2,3) as MutableList)[0] = 99` gives `[99, 2, 3]` |
| V2 | "To get full immutability, both must apply" | The objects inside must be immutable too | Approve | Follows from V1 |
| V3 | `List<T>` over `MutableList<T>` gives value-level immutability | Read-only and immutable are different contracts | Approve | Kotlin collections overview |
| V4 | `lateinit` is not allowed on top-level properties | It is allowed | Approve | Run: top-level `lateinit var` compiles and works |
| V5 | Full immutability: use `List`, `Map`, `Set`, data classes | Those types alone do not guarantee it | Approve | Follows from V1 |
| V6 | Reflection won't show `const val`s as ordinary fields | They are `public static final` fields | Approve | Run: reflection lists `public static final BASE_URL` |
| V7 | Changing a `const val` value is binary-incompatible | Old binaries keep the old value; linking does not break | Approve | Kotlin properties docs |
| V8 | `by lazy` synchronizes on every read | After initialization, it reads a volatile field without locking | Approve with edit | Current `SynchronizedLazyImpl` source |
| V9 | Same claim, in Performance Considerations | Same | Approve | Same |
| V10 | Same claim, in Common Misconceptions | Same | Approve | Same |
| V11 | Any change to a `const val` is binary-incompatible | Renaming or removing breaks linking; a value change gives stale values | Approve | Kotlin properties docs |
| V12 | `val A = B + 1; val B = A * 2` can deadlock or NPE; fix with `by lazy` | In one file the compiler rejects it; across files it silently reads 0; lazy does not fix a cycle | Approve with edit | Run: compile error in one file; `A=1 B=2` across two files |
| V13 | Fix the cycle with `by lazy` | Two lazies that read each other overflow the stack | Approve | Run: `StackOverflowError` |
| V14 | A 200 ms build on the main thread causes an ANR | 200 ms is jank; the input ANR threshold is 5 seconds | Approve | Android vitals ANR page |
| V15 | Hilt sets the field in `…KeyModule_BindUseInstance` | Field injection happens in `onAttach` | Approve with edit | Hilt docs: injected on the first `onAttach` |
| V16 | `Room.databaseBuilder(…, AppDatabase::class.java)` inside `object AppDatabase` | The builder needs the `RoomDatabase` subclass, not the holder object | Approve | Room docs |

**Amended text**

- **V8:** "Con: delegate access has a small overhead; on the JVM, `SYNCHRONIZED` reads a volatile field after initialization instead of locking. Not usable on `var`; the standard lazy delegate cannot be reset and does not support coroutine cancellation." This keeps the original's true point that lazy is not usable on `var`, which the proposed text dropped.
- **V12:** "**Top-level `val` circular dependency.** In one file, the compiler rejects `val A = B + 1` before `B` is initialized. Split across files, it compiles and one value silently reads `0`; with several threads, class initialization can deadlock. Remove the cycle. `by lazy` only moves it: two lazies that read each other overflow the stack."
- **V15:** "Hilt injects the Fragment's fields in `onAttach`, before this `onViewCreated` use."

**Summary:** 13 approve, 3 approve with edit, 0 reject.

## Null Safety — 8 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| N1 | A Kotlin function returning a non-null type has its return checked when called from Java | Kotlin adds no return check; checks run on parameters and on Java values Kotlin uses as non-null | Approve with edit | `javap`: `title()` is just `ldc "x"; areturn` |
| N2 | `optString(key)` returns `"null"` when the key is missing | A missing key gives `""`; only an explicit JSON `null` gives `"null"` | Approve | Android `JSONObject.optString` source |
| N3 | `StateFlow.value` is always non-null | It always has a value, but a `StateFlow<T?>` value can be null | Approve | StateFlow API docs |
| N4 | `runCatching { api.pay() }` in a suspend function | It also catches `CancellationException`, so cancellation is swallowed | Approve | Kotlin `runCatching` docs; Android coroutine best practices |
| N5 | `checkNotNullParameter` throws `IllegalArgumentException` | It throws `NullPointerException` | Approve | Run: `NullPointerException: Parameter specified as non-null is null` |
| N6 | Elvis `?:` returns null when the left side is null | It returns the right side then | Approve | Kotlin null-safety docs |
| N7 | Gson allocates with `Unsafe`, skipping the constructor | Only when there is no no-args constructor, which is the usual Kotlin data class | Approve with edit | Gson troubleshooting guide |
| N8 | Same claim, in the Answer Key | Same, and Moshi validates only with a Kotlin-aware adapter | Approve with edit | Same |

**Amended text**

- **N1:** "There is no matching check on return values. Kotlin's compiler already guarantees a non-null return, and the generated `@NotNull` only informs Java tools. Checks run the other way: when Kotlin uses a Java value as non-null."
- **N7:** "For a class without a no-args constructor, which includes a typical Kotlin data class, Gson falls back to `Unsafe` allocation: it creates the object **without calling the constructor**, then sets fields by reflection. The constructor's `Intrinsics.checkNotNullParameter` checks never run."
- **N8:** "Gson creates a Kotlin class without a no-args constructor through `Unsafe` allocation, bypassing the constructor, then sets fields by reflection. The non-null checks never run, so a field missing from the JSON stays `null` despite its non-null type. Prevent this with `kotlinx.serialization` or Moshi with its Kotlin adapter (codegen or `KotlinJsonAdapterFactory`), which reject the missing field."

**Summary:** 5 approve, 3 approve with edit, 0 reject.

## Functions — 16 proposed, 1 new

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| F1 | Every lambda you pass creates a `Function` instance | A non-capturing lambda is created once and reused | Approve | Run: non-capturing lambda is the same object every time |
| F2 | Function references are cheaper than lambdas, with no captured scope | `System.out::println` is bound and captures; neither form is cheaper in general | Approve | Run: bound reference is a new object each time |
| F3 | "Decompiled:" shows an anonymous `Function1` class | Since Kotlin 2.0 lambdas use `invokedynamic`; the listing is the old `-Xlambdas=class` shape | Approve | Kotlin 2.0 release notes; run: lambda class is `FnsKt$$Lambda$7/…` |
| F4 | A lambda is an anonymous class per call site | Not the default since 2.0 | Approve | Same |
| F5 | `prefix` is captured by reference; every call allocates | It is a `val`, so its value is copied; the per-evaluation allocation is right for a capturing lambda | Approve with edit | Run: capturing lambda is a new object each time |
| F6 | `filter { isEven(it) }` creates an anonymous class; the reference is cheaper | `filter` is `inline`: both forms become a loop that calls `isEven` directly | Approve | `javap`: two direct `invokestatic isEven`, no function objects |
| F7 | Diagram: each non-inline lambda call site allocates an anonymous class | Same as F1 and F4 | Approve | Same |
| F8 | Without `inline`, each lambda passed allocates a `FunctionN` | Same as F1 | Approve | Same |
| F9 | "Each non-inline lambda allocates a `FunctionN` object" | Same as F1 | Approve | Same |
| F10 | Function references are usually faster than lambdas | No general ordering; both non-capturing forms are reused | Approve | Run: unbound reference and non-capturing lambda both reused |
| F11 | Avoid function types when behaviour is configured at runtime; use an interface and DI | This is design guidance, not an error | Reject | — |
| F12 | A `launch { }` lambda captures everything in scope | It captures only what it uses, which can include `this` | Approve | Kotlin closures docs |
| F13 | `onClick` is re-invoked on later compositions; skipping relies on lambda identity | Event lambdas run on click; strong skipping remembers lambdas | Approve | Strong skipping docs: default since Kotlin 2.0.20 |
| F14 | Lambdas with mutable captures defeat skipping; CI should fail on unstable lambdas | Strong skipping remembers lambdas with unstable captures too | Approve | Same |
| F15 | An unstable `viewModel` capture makes a new lambda every recomposition | Not with strong skipping, which compares unstable captures by identity | Approve | Same |
| F16 | `obj::method` allocates a new object each time it is evaluated | The original is right at the bytecode level | Reject | Run: bound reference is a new object each time |
| F17 (new) | `::isEven` compiles to one cached class when passed to `filter` | `filter` is `inline`, so no class or object is created | Approve with edit | `javap`, as in F6 |

**Amended text**

- **F5:** "3. **Captured values are stored in the function object.** `prefix` is a `val`, so its value is copied in. Because the lambda captures, each evaluation creates a new function object. A non-capturing lambda is created once and reused."
- **F17** (replaces "The function reference compiles to a *single* generated class … the same singleton."): "`filter` is `inline`, so neither form creates a function object: both compile into a loop that calls `isEven` directly. The difference matters only for non-inline parameters, where a non-capturing reference or lambda is created once and reused."

**Summary:** 13 approve, 2 approve with edit (one of them new), 2 reject.

## Extensions — 11 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| E1 | An extension with a member's signature compiles silently | The compiler warns that the member shadows it | Approve | Compiler: `warning: this extension is shadowed by a member` |
| E2 | "The compiler issues no warning" | Same | Approve | Same |
| E3 | Resolution step 3: local functions that take the receiver as a parameter | `x.foo()` never resolves to `foo(x)` | Approve | Kotlin spec, calls with an explicit receiver |
| E4 | `inline fun <reified T> Bundle.getParcelableSafe` | The proposal says API 33 needs `T : Parcelable`, but that overload is unbounded `<T>` and the original compiles | Reject | AOSP `Bundle.java`; compiled both versions against `android.jar` (API 36) |
| E5 | No warning, so a library's new member safely takes precedence | There is a warning, and behaviour changes only when consumers recompile | Approve | Compiler warning, as in E1 |
| E6 | Extensions cannot be mocked or stubbed | MockK can mock them with `mockkStatic` | Approve | MockK docs |
| E7 | Mockito and MockK cannot intercept extensions | Same | Approve | Same |
| E8 | "Extensions cannot be mocked because they are static" | Same | Approve | Same |
| E9 | `internal` makes an extension package-private | `internal` means visible in the whole module | Approve | Kotlin visibility docs |
| E10 | Java calls an `internal` extension through a mangled name `foo$mymodule_debug` | Top-level `internal` functions are not mangled; only `internal` members are | Approve | `javap`: `public static … shout(String)`; member `memberInternal$main()` |
| E11 | Sequences are faster only when the chain has more than about 3 elements | There is no fixed threshold | Approve | Kotlin sequences docs |

**Summary:** 10 approve, 0 approve with edit, 1 reject.

## Data Classes — 16 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| D1 | Override `equals` or `hashCode` and the compiler stops generating both | It still generates the one you did not write | Approve | Run: data class overriding only `equals` still has a generated `hashCode` |
| D2 | Table: data classes cannot extend other classes | They can extend `open`, `abstract` or `sealed` classes; they cannot be extended | Approve with edit | Run: `data class Sub(…) : Base(name)` compiles and runs |
| D3 | The restriction exists because inheritance breaks equality | The real rule is that data classes are final; they may still extend a class | Approve | Same |
| D4 | Question: "Why are data classes forbidden from … extending another class?" | False premise | Approve | Same |
| D5 | Answer to the same question | Same | Approve | Same |
| D6 | `List<String>` comment: "immutable List type" | Read-only, not immutable | Approve | Same as V1 |
| D7 | Data classes are immutable value types | `var` properties are allowed; `val`s can hold mutable objects | Approve | Kotlin data classes docs |
| D8 | "There is no safe `var` in a data class" | Legal; the danger is mutating a key used in a hash collection | Approve | Kotlin data classes docs |
| D9 | Compose skips recomposition when state `equals` the previous state | Only stable parameters use `equals`; unstable ones are compared by instance | Approve with edit | Strong skipping docs |
| D10 | An unstable `UiState` recomposes on every emission | Strong skipping (default since Kotlin 2.0.20) still skips unchanged instances | Approve | Same |
| D11 | Unstable data class: "Compose recomposes the whole tree on every emission" | Same | Approve | Same |
| D12 | A `List` field makes every emission force a full recomposition | Same | Approve | Same |
| D13 | Review checklist: push for `@Immutable`/`@Stable` | They are promises; check inferred stability first | Approve | Same |
| D14 | Adding a field causes `IllegalStateException: companion default value …` | The real failure is `NoSuchMethodError` when a constructor or `copy` signature changes | Approve | Kotlin backward-compatibility guidelines |
| D15 | `@JvmOverloads` or a Builder preserves the old signature | Neither restores the old `copy` signature | Approve | Same |
| D16 | Kotlin 1.9+ warns "Component name mismatch" when destructured names are swapped | No warning by default | Approve | Compiler: `val (city, name) = Person(…)` compiles silently and swaps the values |

**Amended text**

- **D2** (table row): "| Implement interfaces; extend an `open`, `abstract` or `sealed` class | Extend another data class (data classes are final) |"
- **D9:** "**Jetpack Compose** can skip a composable whose parameters are unchanged: stable parameters are compared with `equals`, unstable ones by instance."

**Summary:** 14 approve, 2 approve with edit, 0 reject.

## Value Classes — 4 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| VA1 | "The doc-level rule is exact": boxed whenever used as another type | The docs call it a rule of thumb; `Name?` wrapping a `String` is not boxed | Approve | Docs: "As a rule of thumb"; `javap`: `takeName(String)` for a `Name?` parameter |
| VA2 | `List<UserId>` allocates one wrapper per element | Elements are stored boxed, but a box is made where a value enters generic code, not per slot; one box can fill several slots | Approve with edit | Run: two `add(id)` calls give two boxes; `fun <T> twice(x: T) = listOf(x, x)` gives one box in both slots |
| VA3 | `===` on value classes is a bug pattern | The compiler prohibits it | Approve | Compiler: "identity equality … is prohibited" |
| VA4 | Java-facing APIs: avoid value classes or `@JvmName` every entry point | `@JvmExposeBoxed` / `-Xjvm-expose-boxed` now exist (opt-in) | Approve | Kotlin "Calling Kotlin from Java" docs |

**Amended text**

- **VA2:** "- **Collections box.** `List<UserId>` stores each element as a `UserId` box, not as a raw `long`. Usually that means one allocation each time a value enters the list or other generic code, so millions of wrapped longs cost about what boxed `Long`s cost — use primitive arrays (`LongArray`) or rethink the type at the boundary, and measure before deciding."

**Summary:** 3 approve, 1 approve with edit, 0 reject.

## Sealed Classes — 17 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| SE1 | Same package since Kotlin 1.7 | The same-module, same-package rule arrived in 1.5 | Approve | Kotlin 1.5 release notes |
| SE2 | Same module (1.5+) and same package (1.7+) | Same; the rule also applies only to direct subclasses | Approve | Same; sealed classes docs |
| SE3 | Exhaustiveness is enforced only for `when` expressions | Since 1.7, statements on sealed, enum and Boolean subjects are checked too | Approve | Compiler: a statement missing a branch fails with "'when' expression must be exhaustive" |
| SE4 | 1.7 added an opt-in flag to check statements | It is the default since 1.7 | Approve | Same |
| SE5 | `runCatching { api.getUser(id) }` in a suspend function | Swallows `CancellationException` | Approve | Same as N4 |
| SE6 | With an `Unknown` case, a new type "downgrades to `Unknown`" instead of crashing or breaking builds | Holds for old clients whose parser maps unknown values; adding the subclass still breaks consumers' builds when they upgrade | Approve with edit | Sealed classes docs; exhaustiveness as in SE3 |
| SE7 | Troubleshooting: statements need expression form or a flag | Outdated since 1.7 | Approve | Same as SE3 |
| SE8 | "Cannot inherit data class from another sealed" | Data classes can extend sealed classes; data classes cannot be extended | Approve | Same as D2 |
| SE9 | An `Unknown` case avoids a major version bump | Same as SE6 | Approve | Same |
| SE10 | Review checklist: include `Unknown` | Same as SE6 | Approve | Same |
| SE11 | Exhaustiveness only for expressions or with a flag | Same as SE3 | Approve | Same |
| SE12 | Same package (1.7+) and same module (1.5+) | Same as SE1, and only direct subclasses | Approve | Same |
| SE13 | "Plan accordingly or include `Unknown`" | Same as SE6 | Approve | Same |
| SE14 | Answer Key: statements are checked only with a flag before 1.7 | Rewritten to state current behaviour first | Approve | Same as SE3 |
| SE15 | Module rule since 1.5, package rule since 1.7 | Same as SE1 | Approve | Same |
| SE16 | Empty `data class()` is wasteful; `data object` arrived in 1.8 | An empty data class does not compile; data objects previewed in 1.8.20 and became stable in 1.9 | Approve | Kotlin 1.9 release notes |
| SE17 | "Removing it bypasses the safety net," about `else` | Reads backwards: adding `else` bypasses it | Approve | Sealed classes docs |

**Amended text**

- **SE6:** "Now, when the server starts sending a new payment type, old clients whose parser maps unrecognised values to `Unknown` show a fallback instead of crashing. Adding the new subclass to the SDK still breaks exhaustive `when`s when consumers upgrade, so it remains a source-breaking change."

**Summary:** 16 approve, 1 approve with edit, 0 reject.

## Delegation — 10 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| DE1 | Hilt's `@Inject lateinit var` and `LocalContext.current` are delegation under the hood | Only `by navArgs()` is a delegate; the others are field injection and CompositionLocal | Approve | Kotlin delegated properties docs; CompositionLocal docs |
| DE2 | `class Required<T>` with `private lateinit var value: T` | Does not compile: `lateinit` needs a non-null bound | Approve | Compiler: "'lateinit' modifier is not allowed on properties of a type with nullable upper bound" |
| DE3 | Every read of the preference delegate hits disk | `SharedPreferences` reads an in-memory map after the first load | Approve | AOSP `SharedPreferencesImpl.getString`: `awaitLoadedLocked()` then `mMap.get(key)` |
| DE4 | `rememberSaveable` restores through `SavedStateHandle` | It uses the saved-instance-state registry; `SavedStateHandle` is separate | Approve | Compose state-saving docs |
| DE5 | Reentrant `lazy` access throws `ConcurrentModificationException` | It recurses until `StackOverflowError` | Approve | Run: two lazies reading each other give `StackOverflowError` |
| DE6 | `Delegates.notNull` throws `UninitializedPropertyAccessException` | It throws `IllegalStateException` | Approve | Run: `IllegalStateException: Property later should be initialized before get.` |
| DE7 | Answer Key: every read is a synchronous disk read | Same as DE3 | Approve | Same |
| DE8 | Review checklist: a preference delegate reads disk every time | Same as DE3 | Approve | Same |
| DE9 | `override fun flush() = file.flush()` on a `java.io.File` | `File` has no `flush()`; the example does not compile | Approve | `java.io.File` API |
| DE10 | "use Hilt's `by hiltViewModel()`" | `hiltViewModel()` is a Composable function, not a delegate | Approve | Android Hilt-Jetpack docs |

**Summary:** 10 approve, 0 approve with edit, 0 reject.

## Generics — 17 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| GE1 | `validate` compares `value > "minimum"` | Does not compile: `T` is expected, `String` given | Approve | Compiler: "argument type mismatch: actual type is 'String'" |
| GE2 | `listOf("a","b")::class.java` prints `EmptyList` | Both print `java.util.Arrays$ArrayList` | Approve | Run: `class java.util.Arrays$ArrayList` twice |
| GE3 | `(Animal) -> Number` works as `(Dog) -> Int` | Backwards for the return type: `(Animal) -> Int` works as `(Dog) -> Number` | Approve | Compiler rejects the original assignment |
| GE4 | `fun consume(@UnsafeVariance item: T)` | The annotation targets the type: `item: @UnsafeVariance T` | Approve | Compiler: "not applicable to target 'value parameter'"; corrected form compiles |
| GE5 | Heading: why `List<Dog>` isn't `List<Animal>` | Kotlin's `List` is covariant, so it is; `MutableList` is the invariant one | Approve | Kotlin generics docs |
| GE6 | Misconception: `List<Dog>` is not a `List<Animal>` | Same | Approve | Same |
| GE7 | `<T : Any?>` vs `<T>`: "false in practice" | They are the same; the original switches to `<T : Any>` midway | Approve | Kotlin generics docs |
| GE8 | `List<*>` is read-only, `List<Any?>` accepts any input | Neither read-only `List` can add; the difference is for `MutableList` | Approve | Same |
| GE9 | Generics have zero runtime cost on the JVM | No code bloat, but primitives are boxed and casts are inserted | Approve with edit | Same |
| GE10 | Fix for "cannot instantiate `T()`": pass a `Class<T>` or use `reified` | The original fix (reflection through a class token) is valid | Reject | — |
| GE11 | Dagger sees raw `Repo`, not `Repo<User>` | Dagger keys are full Java types, including type arguments; Kotlin wildcards are the usual mismatch | Approve | Dagger semantics: a key is "a pair of a Java type and an optional qualifier", with `Map<Integer, String>` as an example |
| GE12 | Question with the same premise | Same | Approve | Same |
| GE13 | Answer with the same premise | Same | Approve | Same |
| GE14 | Generic type unstable: annotate it `@Immutable` | A promise, not a fix; strong skipping changes the picture | Approve | Same as D10–D13 |
| GE15 | Answer: annotate `T`'s class `@Immutable` / `@Stable` | Same | Approve | Same |
| GE16 | `registry[…] as T ?: error(…)` | The cast runs first, so a miss throws before the error message | Approve | Run: `NullPointerException: null cannot be cast to non-null type Service`; compiler warns the Elvis is unreachable |
| GE17 | Even `reified` cannot give `List<User>` at runtime | `typeOf<T>()` can; only `T::class.java` cannot | Approve | Earlier run: `typeOf` gives `List<User>` |

**Amended text**

- **GE9:** "**"Generics make the app larger or slower."** Mostly false on the JVM: erasure means one class serves every type argument, so there is no code bloat (unlike C++ templates). It is not completely free: primitive type arguments are boxed (`List<Int>` holds `Integer` objects) and the compiler inserts casts."

**Summary:** 15 approve, 1 approve with edit, 1 reject.

## Variance — 10 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| VR1 | `val g: (Dog) -> Int = f` where `f: (Animal) -> Number` is legal | Rejected by the compiler | Approve | Compiler: "expected '(Dog) -> Int', actual '(Animal) -> Number'" |
| VR2 | Returned `List<out T>` appears in Java as `List<? extends T>` | Kotlin omits wildcards on return types | Approve | `javap`: return `List<Animal>`, parameter `List<? extends Animal>` |
| VR3 | Question: `MutableList<out E>` is impossible | Only as a declaration; as a use-site projection it is valid | Approve | Run: a `MutableList<out Animal>` reference works and can `clear()` |
| VR4 | Answer with the same premise | Same | Approve | Same |
| VR5 | Review checklist: `MutableSomething<out T>` is structurally impossible | Same | Approve | Same |
| VR6 | `LiveData` is invariant because `MutableLiveData` writes | `LiveData` is a Java class, so it has no declaration-site variance; `List`/`MutableList` show a mutable subtype does not force invariance | Approve | Kotlin generics docs; LiveData reference |
| VR7 | Answer with the same reason | Same | Approve | Same |
| VR8 | `MutableList<out Animal>` is read-only; `MutableList<in Animal>` is write-only | `clear()` still works on `out`; `in` can still be read, as `Any?` | Approve | Run: both observed |
| VR9 | A subclass cannot widen variance | The real rule is about type positions | Approve | Compiler: "'T' is declared as 'out' but occurs in 'invariant' position" for `class C<out T> : Box<T>`; `class Child<T> : Producer<T>` compiles |
| VR10 | Answer with the same rule | Same | Approve | Same |

**Summary:** 10 approve, 0 approve with edit, 0 reject.

## Inline Functions — 15 proposed

The `doMath { x, y -> x + y }` example passes a non-capturing lambda. On Kotlin 2.x it compiles to `invokedynamic` and the same object is reused on every call. The chapter's "new object per call → GC churn → jank" story does not hold for it.

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| IN1 | Every lambda allocates a new object on each execution; 60 a second freezes the UI | Non-capturing lambdas are reused; `filter` is already inline | Approve | `javap`: `invokedynamic` for the example; earlier run: non-capturing lambda is the same object |
| IN2 | "If you decompile … you will see" an anonymous class | That is old class-based output, not current | Approve | Same; Kotlin 2.0 release notes |
| IN3 | Label: "Decompiled Java (No Inline)" | Same | Approve | Same |
| IN4 | Comment: "The JVM instantiated a hidden object!" | Same | Approve | Same |
| IN5 | `calculate()` allocates a `Function2` on every call | Same | Approve | Same |
| IN6 | `new` + `dup` + `invokespecial` every invocation → jank | Not produced by this example | Approve | Same |
| IN7 | 8,000 stack operations vs 1,000 heap allocations | Invented counts | Approve | Same |
| IN8 | Without inlining, a `filter.map.sortedBy` chain would hit out-of-memory | Unsupported; inlining also does not remove the intermediate lists | Approve | Kotlin inline functions docs |
| IN9 | Inline functions cannot access `private` members | Only public-API inline functions; a private inline function can | Approve | Compiler: private inline reading a private field compiles; public inline calling a private function fails with "public-API inline function cannot access non-public-API function" |
| IN10 | Reject inline functions over 3–4 lines; they cause severe instruction-cache misses | No basis for a line threshold or the cache claim | Approve | Kotlin inline functions docs |
| IN11 | 50 lines in `.let { }` makes the caller's bytecode massive | Code at one call site is not duplicated by `let` | Approve | Same |
| IN12 | Answer Key: a new `Function` object per call | Same as IN1 | Approve | Same as IN1 |
| IN13 | Answer Key: without inlining, chains would crash with OOM | Same as IN8 | Approve | Same as IN8 |
| IN14 | Question: why can't inline functions access `private` members? | Same as IN9 | Approve | Same as IN9 |
| IN15 | Answer with the same premise | Same as IN9 | Approve | Same as IN9 |

**Summary:** 15 approve, 0 approve with edit, 0 reject.

## Reified Types — 7 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| RE1 | A reified type parameter "remains a real, queryable class at runtime" | The type is substituted at each call site; `T::class` has no type arguments, `typeOf<T>()` does | Approve | Earlier run: `T::class.java` gives `java.util.List`, `typeOf` gives `List<User>` |
| RE2 | "The function doesn't exist at runtime; only its specialised copies do" | The method is still emitted alongside the inlined copies | Approve | `javap`: `public static final <T> boolean isType(Object)` present |
| RE3 | Why `reified` needs `inline`: one shared body cannot keep `T` | The original explains Kotlin's mechanism correctly | Reject | — |
| RE4 | Question: why is `reified` "mathematically impossible" without `inline`? | "Mathematically impossible" overstates it; other languages pass type information at runtime | Approve with edit | — |
| RE5 | Answer to the same question | The answer is right; only the question line needs the same fix | Approve with edit | — |
| RE6 | Reified wrappers pass `T::class.java` to a private non-inline worker | A public inline function cannot call a private worker | Approve | Compiler: "public-API inline function cannot access non-public-API function" |
| RE7 | A class "lives on the heap", so it cannot be reified | Mixes up class definitions and instances; the rule is that only inline functions may declare `reified` | Approve | Kotlin inline functions docs |

**Amended text**

- **RE4:** "2. Why does Kotlin allow `reified` only on `inline` functions?"
- **RE5:** Replace only the question line with "2. **Why does Kotlin allow `reified` only on `inline` functions?**" and keep the original answer.

**Summary:** 4 approve, 2 approve with edit, 1 reject.

## Coroutines — 63 proposed

Most rejections here are hedges on statements that are correct as taught: "lightweight thread", "fire-and-forget", strong review rules such as "never `GlobalScope`". The approved rows are where the original is actually wrong, overstates a guarantee, or its example fails.

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| C1 | Tens of thousands of coroutines share a few threads | Correct; the Kotlin docs show 50,000 | Reject | — |
| C2 | Heavy work on Main freezes the app; UI updates off Main crash | Correct simplification for the opening problem | Reject | — |
| C3 | Every `suspend` function becomes a state machine | A function whose only suspend call is a tail call gets none | Approve | `javap`: `twoPoints` has a continuation class, `tailOnly` has none |
| C4 | Pseudocode `return api.fetchUser(sm)` | Loses the path where the call completes without suspending (`COROUTINE_SUSPENDED` check) | Approve | Kotlin spec, coroutines chapter |
| C5 | At suspension the function returns and the thread is freed | Correct | Reject | — |
| C6 | One app can have 50,000 coroutines in flight | Correct | Reject | — |
| C7 | A dispatcher decides which thread pool runs the coroutine | Simplification; "#1 cause" is rhetoric | Reject | — |
| C8 | `IO`: elastic pool, default 64 threads | Correct on Android (max(64, cores)) | Reject | — |
| C9 | `Default`: fixed pool = number of cores | At least two threads | Approve | `Dispatchers.Default` API docs |
| C10 | `Unconfined`: whatever thread resumed you | Correct after the first suspension | Reject | — |
| C11 | `Main.immediate` skips dispatch when already on Main | Correct | Reject | — |
| C12 | 10 API calls of 500 ms on `Default` vs `IO` | Holds only if the calls *block*; suspending calls would not occupy threads | Approve | Same reasoning as the chapter's dispatcher section |
| C13 | All 10 run on the IO pool concurrently | Correct once C12 says "blocking" | Reject | — |
| C14 | "Batched 4 × 4 × 2 = 3 batches" | The arithmetic is wrong: ceil(10 / 4) = 3 | Approve | Arithmetic |
| C15 | ~1800 ms total, 2.25× slower | Correct for the model | Reject | — |
| C16 | While IO threads wait, "the OS can schedule something else on the same physical thread" | It is the CPU core that gets reused, not the thread | Approve | `Dispatchers.IO` API docs |
| C17 | A main-safe repository does its own `withContext(IO)` | Fine for the blocking example shown | Reject | — |
| C18 | Calls the hard-coded `Dispatchers.IO` example "Dispatcher injection" | Hard-coding is not injection | Approve with edit | — |
| C19 | `launch` result: none (fire-and-forget) | Standard wording | Reject | — |
| C20 | `async` failure propagates to the parent and is held for `await()` | Correct | Reject | — |
| C21 | `async` comment: "starts in parallel" | `async` starts work concurrently; it runs in parallel only if the dispatcher has free threads | Approve | `async` API docs; overlapping waits can share one thread |
| C22 | "Parallel decomposition" | Standard wording | Reject | — |
| C23 | Await-only failures only for top-level or supervised `async` | Correct | Reject | — |
| C24 | `Repo` scope built on `Job()` | After one failed save, the scope is cancelled and every later save silently never runs. `SupervisorJob` alone fixes that but an uncaught failure still crashes an Android app | Approve with edit | Run: with `Job()`, the second `launch` is cancelled; with `SupervisorJob()`, the scope stays active but the `IOException` reaches the thread's uncaught handler |
| C25 | `scope.cancel()`: every coroutine inside dies | Simplification; the cancellation section explains cooperation | Reject | — |
| C26 | Table: `GlobalScope` has a `Job` | It has no Job (empty context) | Approve | `GlobalScope` API docs |
| C27 | `GlobalScope` is reserved for internals and tests | It is a delicate API with rare legitimate uses, not internal | Approve | Same |
| C28 | Cancelling a parent cancels children; siblings unaffected | Correct | Reject | — |
| C29 | Table: `viewModelScope.launch` "inherits `SupervisorJob`" | Each launch gets an ordinary `Job` whose parent is the supervisor | Approve | Kotlin exception-handling docs |
| C30 | `supervisorScope` example: if one fails, the others keep running | True, but the uncaught failure still crashes an Android app; the example needs local catches | Approve | Kotlin exception-handling docs |
| C31 | `SupervisorJob` is `Job` except siblings are not cancelled | Correct; C30 carries the caveat | Reject | — |
| C32 | kotlinx.coroutines suspend functions check for cancellation | Only cancellable operations do; `suspend` alone promises no check | Approve | Run: in a cancelled `finally`, `currentCoroutineContext()` and `delay(0)` return normally; `delay(10)` throws |
| C33 | `yield()` suspends briefly and checks cancellation | It checks cancellation but need not actually suspend | Approve | `yield` API docs |
| C34 | Suspending calls in `finally` fail immediately | Cancellable suspending calls do; others return normally | Approve | Same run as C32 |
| C35 | `NonCancellable` block "actually completes" | It is protected from cancellation; it still has to finish and can still fail | Approve | `NonCancellable` API docs |
| C36 | Adds a paragraph after the cleanup example | Addition, not a correction | Reject | — |
| C37 | Swallowing `CancellationException` makes a zombie that keeps running | It continues only to the next suspension point, which throws again | Approve | Run: code after the catch ran, then the next `delay` threw; job completed |
| C38 | Exception handler fires only at the top level, not for `async` | Correct for the standard case | Reject | — |
| C39 | `launchWhenStarted` only pauses | Correct | Reject | — |
| C40 | `runTest` builds a `ViewModel` without replacing `Dispatchers.Main`; passes `dispatcher =` | `viewModelScope` needs `Dispatchers.setMain` in JVM tests; the parameter is named `ioDispatcher` | Approve with edit | Android coroutine testing docs |
| C41 | "Inject a dispatcher into your ViewModel/repo" | Fine once C40 replaces Main | Reject | — |
| C42 | `CartViewModel` with an injected `ioDispatcher` | Valid design | Reject | — |
| C43 | Failure mode: `async { throw }` without `await` is swallowed | Under an ordinary parent it cancels the parent, as the chapter itself explains | Approve | Same as C20 |
| C44 | Real `Dispatchers.IO` in a test hangs forever | It runs in real time; `runTest` times out rather than hanging | Approve | Android coroutine testing docs |
| C45 | Network on Main because the repository did not switch | Fine for blocking clients | Reject | — |
| C46 | 200 ms JSON parse on `Dispatchers.IO` freezes the UI | Work on `IO` cannot freeze the main thread | Approve | Dispatcher model |
| C47 | Two `async`s started before `await` run in parallel | Same as C21 | Approve | Same as C21 |
| C48 | `runBlocking` in production is always wrong | Review rule, not a factual claim | Reject | — |
| C49 | "9 times out of 10" a generic catch swallows cancellation | Rhetoric | Reject | — |
| C50 | `GlobalScope.launch` is always wrong unless a daemon | Review rule | Reject | — |
| C51 | Link text says `android/concurrency/structured-concurrency.md` | The file is `android/architecture/structured-concurrency.md` | Approve | File system |
| C52 | `delay` returns the thread to the pool | Close enough | Reject | — |
| C53 | Answer Key: state machine description | Close enough; C4 fixes the pseudocode | Reject | — |
| C54 | Answer Key: the swallowed-cancellation zombie | Same as C37 | Approve | Same as C37 |
| C55 | A pure CPU loop never checks cancellation | Correct | Reject | — |
| C56 | Answer Key: blocking calls "monopolize the 4 cores while waiting" | They occupy threads, not cores | Approve with edit | Same as C16 |
| C57 | `supervisorScope`: second launch completes although the first crashed | Correct | Reject | — |
| C58 | Suspending calls in `finally` throw; fix with `NonCancellable` | Same as C34 and C35 | Approve | Same as C32 |
| C59 | `Default` pool equals core count | At least two | Approve | Same as C9 |
| C60 | Use `lifecycleScope` for work that must stop when the view dies | In a Fragment, use `viewLifecycleOwner.lifecycleScope`; the Fragment outlives its view | Approve | Android lifecycle-aware coroutines docs |
| C61 | `yield()` suspends briefly | Same as C33 | Approve | Same as C33 |
| C62 | Never use `runBlocking` in production Android code | Review rule | Reject | — |
| C63 | `Main`: never block; only quick work | That is the instruction, correctly given | Reject | — |

**Amended text**

- **C18:** "Now no caller anywhere thinks about threading. The repository owns its own main-safety. In practice you also **inject** the `CoroutineDispatcher` instead of referencing `Dispatchers.IO` directly, so tests can substitute a `TestDispatcher`."
- **C24:**
  ```kotlin
  class Repo {
      // SupervisorJob: one failed save must not cancel every later save.
      private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

      fun save(data: Data) {
          scope.launch {
              try {
                  /* runs on IO */
              } catch (e: IOException) {
                  // Expected failure: record it here. Anything unexpected still crashes,
                  // unless the scope gets a CoroutineExceptionHandler on purpose.
              }
          }
      }

      fun close() {
          scope.cancel()   // every in-flight save cancels
      }
  }
  ```
- **C40:**
  ```kotlin
  @get:Rule
  val mainDispatcherRule = MainDispatcherRule()   // replaces Dispatchers.Main; see the Test Dispatchers chapter

  @Test
  fun cartCheckout() = runTest {
      val viewModel = CartViewModel(repo, ioDispatcher = StandardTestDispatcher(testScheduler))
      viewModel.checkout()
      advanceUntilIdle()      // run all pending coroutines without real waiting
      assertEquals(Success, viewModel.state.value)
  }
  ```
- **C56:** "so it allows up to 64 threads. If you run 10 blocking calls on `Default`, they occupy all 4 `Default` threads while waiting, delaying the 10 CPU tasks: ~1800 ms. On `IO`, all 10 wait concurrently, leaving `Default` free for CPU work: ~800 ms."

**Summary:** 26 approve, 4 approve with edit, 33 reject.

## Channels and Select — 8 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| CH1 | `send` suspends when the channel cannot accept; `receive` when empty | Correct for the default channels taught here | Reject | — |
| CH2 | Closing means no more sends; receivers drain the buffer | Correct | Reject | — |
| CH3 | Rendezvous is right when every frame must be processed | Adds lifecycle guidance; the original is not wrong | Reject | — |
| CH4 | `CartActor` completes `replyTo` with `checkout.submit(items)` | If `submit` throws, the actor's loop dies and every `checkout()` caller waits forever. The same happens to queued callers when the owner's scope is cancelled, and the channel keeps accepting commands nobody will read | Approve with edit | Run: after one `IOException`, both calls still waiting after 500 ms. With the edit: the failed call fails, the next succeeds; after the owner is cancelled, the active and the queued checkout both fail with `CartActor stopped`, and a new `checkout()` fails at once |
| CH5 | Actor is right when serialized mutation is central | Goes with Codex's larger rewrite of CH4, which the smaller edit makes unnecessary | Reject | — |
| CH6 | Worker loop: `runCatching { upload(work) }` | Catches `CancellationException`, so the worker cannot be cancelled cleanly | Approve | Same as N4 |
| CH7 | Test: `advanceUntilIdle()` then assert both items processed | `advanceUntilIdle` does not run `backgroundScope` work; the list is empty | Approve | Run: `[]` after `advanceUntilIdle`, `[1, 2]` after `runCurrent` |
| CH8 | Use `receiveCatching` for public channels | Addition | Reject | — |

**Amended text**

- **CH4:** The exact complete-class replacement is in [the CH4 proposal](corrections-with-edits.md#ch4). A Job completion handler cancels the channel even if startup is prevented. Undelivered and executing requests fail with `CartStoppedException` for active callers; their own cancellation remains cancellation. A service-local timeout fails one request with `CheckoutRequestCancelledException` and leaves an active worker serving. Expected `IOException` also affects one request; unexpected failures stop the worker and retain the owner’s reporting policy. A checkout that finishes during shutdown still returns its result. If cancellation or failure happens before the receipt is delivered, the outcome is unknown; use idempotency or reconcile server state before retrying. Regression cases exercise these boundaries. No correction has been approved or applied.

**Summary:** 2 approve, 1 approve with edit, 5 reject.

## Flow Operators and Backpressure — 9 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| FL1 | Everything above `flowOn` runs on `Default` | Correct for the pipeline shown | Reject | — |
| FL2 | Each `flowOn` creates a concurrency boundary | Only when the dispatcher changes; adjacent operators fuse | Approve | `flowOn` API docs |
| FL3 | `buffer(n)` lets upstream run ahead by n values | Close enough | Reject | — |
| FL4 | `combine` emits whenever any upstream emits | Close enough for teaching | Reject | — |
| FL5 | `sample` emits the latest value at a fixed period | Close enough | Reject | — |
| FL6 | `collect` never returns for hot flows | True for `StateFlow`/`SharedFlow`, the hot flows the chapter means | Reject | — |
| FL7 | `first`: hangs if no value arrives | A completing flow without a match throws `NoSuchElementException` | Approve | `first` API docs |
| FL8 | `toList` never returns for hot flows | Same as FL6 | Reject | — |
| FL9 | Search pipeline summary | Addition about `WhileSubscribed` | Reject | — |

**Summary:** 2 approve, 0 approve with edit, 7 reject.

## callbackFlow and Bridging Callbacks — 7 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| CA1 | `locations.collect { … }` twice in a row: "two collectors" | The first `collect` never returns, so the second never starts | Approve | `callbackFlow` API docs |
| CA2 | "Collection owns registration. Cancellation owns cleanup." | Addition about thread contracts | Reject | — |
| CA3 | `channelFlow` is "colder" than `callbackFlow` | Both are cold; there is no "colder" | Approve | `channelFlow` API docs |
| CA4 | `getDefaultSensor(…)` used directly | Returns null on devices without the sensor; the flow then waits forever | Approve | `SensorManager.getDefaultSensor` reference |
| CA5 | `registerListener(…)` result ignored | Returns false on failure; same silent wait | Approve | `SensorManager.registerListener` reference |
| CA6 | Test emits, then `advanceUntilIdle()`, expects one listener | Collection in `backgroundScope` has not started, so the listener count is 0 and the test fails | Approve | Run: `listeners=0 values=[]`; Codex's version gives `listeners=1`, `values=[test]`, then 0 after cancel |
| CA7 | `EditText` callback flow without `flowOn(Main.immediate)` | Collected from the UI, it already runs on Main | Reject | — |

**Summary:** 5 approve, 0 approve with edit, 2 reject.

## Coroutines Debugging and Profiling — 7 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| CO1 | Job states include "suspended" | Not a Job state; a suspended coroutine's Job is active | Approve | `Job` API docs: New, Active, Completing, Cancelling, Cancelled, Completed |
| CO2 | Swallowed cancellation means child work "may have skipped cleanup" | `finally` still runs, and the Job stays cancelled | Approve | Run (C37): code continued, the next suspension threw, `finally` ran |
| CO3 | "The JVM debug agent" enriches thread names | That is the `kotlinx.coroutines.debug` property (debug mode), not the `DebugProbes` agent | Approve | Kotlin coroutine context and dispatchers docs, debugging section |
| CO4 | Thread-name debugging is most useful in local tests | Addition | Reject | — |
| CO5 | Use `NonCancellable` sparingly and bounded | Addition | Reject | — |
| CO6 | Cancellation test: `dispatcher = testDispatcher`, then asserts `refreshStarted` right away | `testDispatcher` is never defined, `Main` is not replaced, and queued work has not started when it asserts | Approve | Same pattern as CA6: `StandardTestDispatcher` work waits for `runCurrent()` |
| CO7 | Closing sentence | Addition | Reject | — |

**Summary:** 4 approve, 0 approve with edit, 3 reject.

## Test Dispatchers and Virtual Time — 7 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| TE1 | `UnconfinedTestDispatcher` starts work eagerly until the first suspension | Correct | Reject | — |
| TE2 | `backgroundScope` is cancelled when `runTest` ends | Correct | Reject | — |
| TE3 | Manual hot-flow test with an unconfined collector, then `advanceUntilIdle()` | Correct: the collector is unconfined and the ViewModel work is not background | Reject | — |
| TE4 | `flatMapLatest` cancellation test | Emits before the background collector subscribes, and `advanceUntilIdle()` never runs it; no query is cancelled | Approve | Run: `cancelled=[]` with both a `SharedFlow` and a `StateFlow` (test expects `[old]`) |
| TE5 | Collecting a `StateFlow` in the test "hangs" | `runTest` fails at its timeout rather than hanging forever | Approve | Same as C44 |
| TE6 | Virtual time advances "when the test tells it to" | Also advances automatically when the test is idle; minor | Reject | — |
| TE7 | Pass the scheduler explicitly when schedulers differ | Correct advice | Reject | — |

**Summary:** 2 approve, 0 approve with edit, 5 reject.

## Memory Model — 16 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| ME1 | All object references live on the stack or in registers | References in fields and arrays live on the heap | Approve | JVM specification, run-time data areas |
| ME2 | A `List<Int>` of 100k items is 100k+1 heap objects | An approximation that makes the right point | Reject | — |
| ME3 | Phantom references are cleared "even before finalize" | Phantom reachability comes after finalization; `get()` always returns null | Approve | `PhantomReference` API docs |
| ME4 | Concurrent generational GC from Android 8 | Concurrent Copying from Android 8; generational from Android 10 | Approve | AOSP: "CC extends to be a generational GC in Android 10 and higher" |
| ME5 | Dalvik had no Large Object Space; ART has one for bitmaps | Simplified comparison table; not clearly wrong | Reject | — |
| ME6 | ART introduced generational GC; bitmaps go to the LOS | Same chronology as ME4; bitmap pixels are native from Android 8 | Approve | AOSP GC docs; Android bitmap memory docs |
| ME7 | Bitmaps go to native memory with `Bitmap.Config.HARDWARE` | From Android 8 all bitmap pixels are native; hardware bitmaps use graphics memory | Approve | Android bitmap memory docs |
| ME8 | Fix the Activity's delayed callback with `viewModelScope` | Moves the Activity capture into a longer-lived owner, causing the leak it fixes | Approve | Android lifecycle-aware coroutines docs |
| ME9 | 5+ instances after a forced GC means a leak | Profiling heuristic | Reject | — |
| ME10 | "800 MB RSS but only 80 MB heap" | Illustration | Reject | — |
| ME11 | Bitmaps were in the Java heap before Oreo | True for every API level still relevant | Reject | — |
| ME12 | Boxing `5` allocates an `Integer` on the heap | The cached `Integer` is still a heap object | Reject | — |
| ME13 | Answer Key: 100,001 objects | Same as ME2 | Reject | — |
| ME14 | Answer Key: four reference strengths, but only three answered; weak refs "cleared immediately" | The phantom answer is missing | Approve | `WeakReference` / `PhantomReference` API docs |
| ME15 | `viewModelScope` cancels on clear and breaks the reference chain | Correct | Reject | — |
| ME16 | JEP 197 cited as generational GC background | JEP 197 is the segmented code cache | Approve | JEP 197 |

**Summary:** 8 approve, 0 approve with edit, 8 reject.

## JVM Interop — 21 proposed

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| JV1 | Java sees only `connect(String, int, boolean)` | Correct; `connect$default` is synthetic | Reject | — |
| JV2 | `@JvmOverloads` only covers trailing parameters | Correct for the chapter's example | Reject | — |
| JV3 | Java can extend a Kotlin sealed class in the same package | The constructor is private; Java cannot | Approve | `javac`: "Shape() has private access in Shape" |
| JV4 | `internal fun greet()` gets a mangled name | Only `internal` members are mangled; top-level functions are not | Approve | `javap`, as in E10 |
| JV5 | Bytecode `greet$mymodule_debug` for the top-level example | Same | Approve | Same |
| JV6 | The failure is "more precisely, an `IllegalStateException`" | It is a `NullPointerException` | Approve | Run: `NullPointerException: findById(...) must not be null` |
| JV7 | Java sees `List<? extends Box<? extends Number>>` for a return type | Return types get no wildcards | Approve | `javap`: return `List<Animal>`, parameter `List<? extends Animal>` |
| JV8 | With `@file:JvmName("Telemetry")`, Java calls `Telemetry.event(…)` | The functions are members of `object TelemetryClient`, so Java calls `TelemetryClient.event(…)` | Approve | Kotlin "Calling Kotlin from Java" docs |
| JV9 | Without annotations: `TelemetryKt.TelemetryClient.INSTANCE` | The object is not nested in the file class | Approve | Same |
| JV10 | `view.tag` is `Any!` | Correct | Reject | Compiled against `android.jar` (API 36): `val t: Any = view.tag` compiles, so it is a platform type |
| JV11 | `getTag()` has no nullability annotation | Correct | Reject | Same |
| JV12 | Comment: "`.toString()` on `Any!` is fine … CRASHES if tag is null" | Calling `toString()` on a platform-typed null crashes. Codex's text says it safely returns "null", which is also wrong | Approve with edit | `javap`: `invokevirtual Object.toString`; run: `NullPointerException` |
| JV13 | Java lambda `result -> { … }` for a Kotlin `(Result) -> Unit` | Must `return Unit.INSTANCE` | Approve | Kotlin "Calling Java from Kotlin" docs |
| JV14 | Java SAM conversion handles function types automatically | Same as JV13 | Approve | Same |
| JV15 | Adding a default parameter doesn't break Java, but it becomes mandatory | Contradicts itself: it does break Java callers | Approve | Kotlin "Calling Kotlin from Java" docs |
| JV16 | Java can extend a sealed class in the same package | Same as JV3 | Approve | Same as JV3 |
| JV17 | Same, in the Staff Lens | Same as JV3 | Approve | Same as JV3 |
| JV18 | Value classes "box back to their underlying type" in Java | Reversed: they appear unboxed, as the underlying type | Approve | Kotlin inline value classes docs |
| JV19 | Companion factories holding sensitive resources keep them for the process | Conditional ("if they hold"), so correct | Reject | — |
| JV20 | A record's canonical constructor is final | Constructors cannot be final; record classes and their fields are | Approve | Java records docs |
| JV21 | Answer Key: `internal` names are mangled | Same as JV4 | Approve | Same as JV4 |

**Amended text**

- **JV12:**
  ```kotlin
  // CRASHES at runtime if tag is null: on a platform type, toString() calls Object.toString() directly
  val tagStr: String = view.tag.toString()
  ```

**Summary:** 15 approve, 1 approve with edit, 5 reject.

## Bytecode — 7 proposed, 1 new

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| BY1 | `javap -c -p Foo.jar FooKt` | The jar must go in `-classpath` | Approve | `javap` manual |
| BY2 | A data class "generates 4 free methods" | It generates accessors, `componentN`, `copy`, `equals`, `hashCode`, `toString` | Approve | Kotlin data classes docs |
| BY3 | Every `val` in a data class is compared in `equals` | Only primary-constructor properties | Approve | Same |
| BY4 | Without `inline`, `calc()` constructs a `Function2` | A non-capturing lambda uses `invokedynamic` and is reused | Approve | Same as F1/F3 |
| BY5 | DEX is the same bytecode in a different encoding | A different instruction set | Approve | AOSP Dalvik bytecode docs |
| BY6 | The optimizations you care about happen before D8/R8 | R8 and ART do major optimization | Approve | Android app optimization docs |
| BY7 | `map.filter.firstOrNull` shows three calls and three lists | `map` and `filter` are inlined loops making two lists; `firstOrNull` makes none | Approve | Kotlin `firstOrNull` docs; same as F6 |
| BY8 (new) | Listing shows `greeting()` reading `name` through `invokevirtual getName()` | Inside the class, Kotlin reads the field directly | Approve with edit | `javap`: `greeting()` uses `getfield name` |

**Amended text**

- **BY8:** In the listing, replace `13: invokevirtual #7 // Method getName:()Ljava/lang/String;` with `13: getfield #2 // Field name:Ljava/lang/String;`. Replace observation 1 with: "`val name` becomes a **field** plus a getter method. Code inside `User` reads the field directly (`getfield`); code in other classes calls `getName()`."

**Summary:** 7 approve, 1 approve with edit (new), 0 reject.

## Kotlin 2.4 Update — 0 proposed, 1 new

| # | Original says | Problem | Verdict | Evidence |
|---|---|---|---|---|
| K1 (new) | `var token: String?` with `field = null` and `private set` | Does not compile: explicit backing fields are `val`-only | Approve with edit | Compiler: "only 'val' properties with explicit backing fields are supported" |

**Amended text**

- **K1:**
  ```kotlin
  class Session {
      val token: StateFlow<String?>
          field = MutableStateFlow<String?>(null)

      fun authenticate(newToken: String) {
          token.value = newToken   // inside the class, token is the MutableStateFlow
      }
  }
  ```
  Compiled and run with Kotlin 2.4.21: `token=abc`.

**Summary:** 1 approve with edit (new).
