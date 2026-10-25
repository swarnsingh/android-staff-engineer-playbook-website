# Corrections With Edits: Exact Text

Exact proposed wording for the 23 rows of [`corrections-triage.md`](corrections-triage.md) marked **Approve with edit**, including the three new findings (F17, BY8, K1). Nothing here is approved or applied. The original Markdown is never edited: an approved correction replaces the text only on the website, with a visible marker.

**How to approve:** name the IDs you approve. Each approved ID then goes into `website/content/corrections-*.json` with `"status": "approved"`, using exactly the original and replacement shown here. Rows marked "Approve" (without edit) in the triage use Codex's proposed text unchanged and are not repeated here.

**Checked:**
- Each original text below occurs exactly once in its chapter at the line shown, and no two replacements overlap, so all 23 can be applied together.
- With all 24 replacements across 23 IDs applied in a temporary build, every page renders and the preservation check passes (3,521 units, 0 problems). 17 replacements get an inline highlight; the other 7 (a table row and code) are shown by their section's correction note. The temporary file was removed afterwards.
- CH4, C24 and K1 were compiled and run exactly as they would read in the chapter; see each entry.
- The machine-readable copy is [`corrections-with-edits.json`](corrections-with-edits.json), with the same `path`/`old`/`new` fields as the corrections files.

| ID | Chapter | Section | Line |
|---|---|---|---|
| [V8](#v8) | Variables | Tradeoffs | 512 |
| [V12](#v12) | Variables | Failure Modes | 528 |
| [V15](#v15) | Variables | `lateinit` for view-model injection | 438 |
| [N1](#n1) | Null Safety | How Kotlin Enforces Null Safety at the JVM Boundary | 314 |
| [N7](#n7) | Null Safety | Reflection-Based Libraries Can Lie | 277 |
| [N8](#n8) | Null Safety | Answer Key | 478 |
| [F5](#f5) | Functions | What a lambda compiles to | 248 |
| [F17](#f17) | Functions | Function references vs lambdas at the bytecode level | 290 |
| [D2](#d2) | Data Classes | Inheritance Restrictions | 245 |
| [D9](#d9) | Data Classes | Why It Matters (Android Context) | 38 |
| [VA2](#va2) | Value Classes | 2. Boxing: the Rule That Decides Whether You Got the Performance | 46 |
| [SE6](#se6) | Sealed Classes and Interfaces | SDK and Public API Considerations | 422 |
| [GE9](#ge9) | Generics | Common Misconceptions | 486 |
| [RE4](#re4) | Reified Types | Probing Questions | 183 |
| [RE5](#re5) | Reified Types | Answer Key | 197 |
| [C18](#c18) | Coroutines | The main-safety contract | 137 |
| [C24](#c24) | Coroutines | Scope = lifetime owner | 179 |
| [C40](#c40) | Coroutines | `runTest` — virtual time for unit tests | 472 |
| [C56](#c56) | Coroutines | Answer Key | 580 |
| [CH4](#ch4) | Channels and Select | Actor-Style State Ownership | 185 |
| [JV12](#jv12) | JVM Interop | Calling Android SDK Java from Kotlin: platform types in action | 452 |
| [BY8](#by8) | Kotlin: Bytecode and Decompilation | Property access | 123 |
| [K1](#k1) | Kotlin 2.4 Update for Android and KMP | Explicit backing fields are Stable | 50 |

## V8

- **Chapter:** Variables (`kotlin/language-core/variables.md`)
- **Original says:** `by lazy` synchronizes on every read
- **Reason:** After initialization, it reads a volatile field without locking
- **Evidence:** Current `SynchronizedLazyImpl` source
- **Sources:** <https://github.com/JetBrains/kotlin/blob/v2.2.21/libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt>

**Original** (section "Tradeoffs", line 512):

````markdown
- Con: small overhead per access (synchronization, even after init in SYNCHRONIZED mode); not usable on `var`; the block can't be cancelled or reset.
````

**Replacement:**

````markdown
- Con: delegate access has a small overhead; on the JVM, `SYNCHRONIZED` reads a volatile field after initialization instead of locking. Not usable on `var`; the standard lazy delegate cannot be reset and does not support coroutine cancellation.
````

## V12

- **Chapter:** Variables (`kotlin/language-core/variables.md`)
- **Original says:** `val A = B + 1; val B = A * 2` can deadlock or NPE; fix with `by lazy`
- **Reason:** In one file the compiler rejects it; across files it silently reads 0; lazy does not fix a cycle
- **Evidence:** Run: compile error in one file; `A=1 B=2` across two files
- **Sources:** <https://docs.oracle.com/javase/specs/jls/se17/html/jls-12.html#jls-12.4.2>, <https://github.com/JetBrains/kotlin/blob/v2.2.21/libraries/stdlib/jvm/src/kotlin/util/LazyJVM.kt>

**Original** (section "Failure Modes", line 528):

````markdown
**Top-level `val` circular dependency.** `val A = B + 1` and `val B = A * 2` at top level can deadlock or NPE during class loading. Mitigation: use `by lazy` to break the cycle.
````

**Replacement:**

````markdown
**Top-level `val` circular dependency.** In one file, the compiler rejects `val A = B + 1` before `B` is initialized. Split across files, it compiles and one value silently reads `0`; with several threads, class initialization can deadlock. Remove the cycle. `by lazy` only moves it: two lazies that read each other overflow the stack.
````

## V15

- **Chapter:** Variables (`kotlin/language-core/variables.md`)
- **Original says:** Hilt sets the field in `…KeyModule_BindUseInstance`
- **Reason:** Field injection happens in `onAttach`
- **Evidence:** Hilt docs: injected on the first `onAttach`
- **Sources:** <https://dagger.dev/hilt/android-entry-point.html>

**Original** (section "`lateinit` for view-model injection", line 438):

````markdown
Hilt sets `imageLoader` in the generated `Fragment_HiltModules$KeyModule_BindUseInstance` code before `onViewCreated` runs.
````

**Replacement:**

````markdown
Hilt injects the Fragment's fields in `onAttach`, before this `onViewCreated` use.
````

## N1

- **Chapter:** Null Safety (`kotlin/language-core/null-safety.md`)
- **Original says:** A Kotlin function returning a non-null type has its return checked when called from Java
- **Reason:** Kotlin adds no return check; checks run on parameters and on Java values Kotlin uses as non-null
- **Evidence:** `javap`: `title()` is just `ldc "x"; areturn`
- **Sources:** <https://kotlinlang.org/docs/java-interop.html#null-safety-and-platform-types>

**Original** (section "How Kotlin Enforces Null Safety at the JVM Boundary", line 314):

````markdown
Likewise, when you call a Kotlin function returning a non-null type from Java, the return is checked.
````

**Replacement:**

````markdown
There is no matching check on return values. Kotlin's compiler already guarantees a non-null return, and the generated `@NotNull` only informs Java tools. Checks run the other way: when Kotlin uses a Java value as non-null.
````

## N7

- **Chapter:** Null Safety (`kotlin/language-core/null-safety.md`)
- **Original says:** Gson allocates with `Unsafe`, skipping the constructor
- **Reason:** Only when there is no no-args constructor, which is the usual Kotlin data class
- **Evidence:** Gson troubleshooting guide
- **Sources:** <https://google.github.io/gson/Troubleshooting.html#default-field-values-not-present-after-deserialization>

**Original** (section "Reflection-Based Libraries Can Lie", line 277):

````markdown
Gson uses `Unsafe` allocation: it constructs the object **without calling the constructor**, then injects fields by reflection. Constructor checks (`Intrinsics.checkNotNullParameter`) never run.
````

**Replacement:**

````markdown
For a class without a no-args constructor, which includes a typical Kotlin data class, Gson falls back to `Unsafe` allocation: it creates the object **without calling the constructor**, then sets fields by reflection. The constructor's `Intrinsics.checkNotNullParameter` checks never run.
````

## N8

- **Chapter:** Null Safety (`kotlin/language-core/null-safety.md`)
- **Original says:** Same claim, in the Answer Key
- **Reason:** Same, and Moshi validates only with a Kotlin-aware adapter
- **Evidence:** Same
- **Sources:** <https://google.github.io/gson/Troubleshooting.html#default-field-values-not-present-after-deserialization>

**Original** (section "Answer Key", line 478):

````markdown
Gson deserializes objects using `Unsafe` allocation, bypassing the class constructor entirely, and then sets fields via reflection. Since the constructor never runs, Kotlin's non-null intrinsic checks are bypassed. If the JSON omits a field, the field remains uninitialized (`null`), violating the type system. Prevent this by using Moshi or `kotlinx.serialization`.
````

**Replacement:**

````markdown
Gson creates a Kotlin class without a no-args constructor through `Unsafe` allocation, bypassing the constructor, then sets fields by reflection. The non-null checks never run, so a field missing from the JSON stays `null` despite its non-null type. Prevent this with `kotlinx.serialization` or Moshi with its Kotlin adapter (codegen or `KotlinJsonAdapterFactory`), which reject the missing field.
````

## F5

- **Chapter:** Functions (`kotlin/language-core/functions.md`)
- **Original says:** `prefix` is captured by reference; every call allocates
- **Reason:** It is a `val`, so its value is copied; the per-evaluation allocation is right for a capturing lambda
- **Evidence:** Run: capturing lambda is a new object each time
- **Sources:** <https://kotlinlang.org/docs/whatsnew20.html#generation-of-lambda-functions-using-invokedynamic>

**Original** (section "What a lambda compiles to", line 248):

````markdown
3. **Captured variables become fields.** `prefix` is captured by reference and stored in the anonymous class instance. Every call to `greetAll` allocates a new instance.
````

**Replacement:**

````markdown
3. **Captured values are stored in the function object.** `prefix` is a `val`, so its value is copied in. Because the lambda captures, each evaluation creates a new function object. A non-capturing lambda is created once and reused.
````

## F17

- **Chapter:** Functions (`kotlin/language-core/functions.md`)
- **Original says:** `::isEven` compiles to one cached class when passed to `filter`
- **Reason:** `filter` is `inline`, so no class or object is created
- **Evidence:** `javap`, as in F6
- **Note:** F6 (approved as proposed) replaces the next paragraph about the wrapper lambda; together they say both forms are inlined.

**Original** (section "Function references vs lambdas at the bytecode level", line 290):

````markdown
The function reference compiles to a *single* generated class that implements `Function1<Int, Boolean>` and calls `isEven`. The class is cached — every use of `::isEven` references the same singleton.
````

**Replacement:**

````markdown
`filter` is `inline`, so neither form creates a function object: both compile into a loop that calls `isEven` directly. The difference matters only for non-inline parameters, where a non-capturing reference or lambda is created once and reused.
````

## D2

- **Chapter:** Data Classes (`kotlin/language-core/data-classes.md`)
- **Original says:** Table: data classes cannot extend other classes
- **Reason:** They can extend `open`, `abstract` or `sealed` classes; they cannot be extended
- **Evidence:** Run: `data class Sub(…) : Base(name)` compiles and runs
- **Sources:** <https://kotlinlang.org/docs/data-classes.html>
- **Changed from the triage text:** The triage text repeated "Be extended by another class", which the table already has in its third row; the right-hand cell now names the restriction this row is about.

**Original** (section "Inheritance Restrictions", line 245):

````markdown
| Implement interfaces | Extend other classes (`open class`, `abstract class`) |
````

**Replacement:**

````markdown
| Implement interfaces; extend an `open`, `abstract` or `sealed` class | Extend another data class (data classes are final) |
````

## D9

- **Chapter:** Data Classes (`kotlin/language-core/data-classes.md`)
- **Original says:** Compose skips recomposition when state `equals` the previous state
- **Reason:** Only stable parameters use `equals`; unstable ones are compared by instance
- **Evidence:** Strong skipping docs
- **Sources:** <https://developer.android.com/develop/ui/compose/performance/stability/strongskipping>

**Original** (section "Why It Matters (Android Context)", line 38):

````markdown
- **Jetpack Compose** skips recomposition when state `equals` the previous state.
````

**Replacement:**

````markdown
- **Jetpack Compose** can skip a composable whose parameters are unchanged: stable parameters are compared with `equals`, unstable ones by instance.
````

## VA2

- **Chapter:** Value Classes (`kotlin/language-core/value-classes.md`)
- **Original says:** `List<UserId>` allocates one wrapper per element
- **Reason:** Elements are stored boxed, but a box is made where a value enters generic code, not per slot; one box can fill several slots
- **Evidence:** Run: two `add(id)` calls give two boxes; `fun <T> twice(x: T) = listOf(x, x)` gives one box in both slots
- **Sources:** <https://kotlinlang.org/docs/inline-classes.html>

**Original** (section "2. Boxing: the Rule That Decides Whether You Got the Performance", line 46):

````markdown
- **Collections box.** `List<UserId>` allocates one wrapper per element. For a hot path holding millions of wrapped longs, that's the same cost as not using primitives — use primitive arrays or rethink the type at the boundary.
````

**Replacement:**

````markdown
- **Collections box.** `List<UserId>` stores each element as a `UserId` box, not as a raw `long`. Usually that means one allocation each time a value enters the list or other generic code, so millions of wrapped longs cost about what boxed `Long`s cost — use primitive arrays (`LongArray`) or rethink the type at the boundary, and measure before deciding.
````

## SE6

- **Chapter:** Sealed Classes and Interfaces (`kotlin/language-core/sealed-classes.md`)
- **Original says:** With an `Unknown` case, a new type "downgrades to `Unknown`" instead of crashing or breaking builds
- **Reason:** Holds for old clients whose parser maps unknown values; adding the subclass still breaks consumers' builds when they upgrade
- **Evidence:** Sealed classes docs; exhaustiveness as in SE3
- **Sources:** <https://kotlinlang.org/docs/sealed-classes.html>, <https://kotlinlang.org/docs/api-guidelines-backward-compatibility.html>

**Original** (section "SDK and Public API Considerations", line 422):

````markdown
Now adding a new method type in the next minor version downgrades to `Unknown` for old clients, instead of crashing or breaking their build.
````

**Replacement:**

````markdown
Now, when the server starts sending a new payment type, old clients whose parser maps unrecognised values to `Unknown` show a fallback instead of crashing. Adding the new subclass to the SDK still breaks exhaustive `when`s when consumers upgrade, so it remains a source-breaking change.
````

## GE9

- **Chapter:** Generics (`kotlin/type-system/generics.md`)
- **Original says:** Generics have zero runtime cost on the JVM
- **Reason:** No code bloat, but primitives are boxed and casts are inserted
- **Evidence:** Same
- **Sources:** <https://kotlinlang.org/docs/generics.html>, <https://kotlinlang.org/docs/whatsnew20.html#generation-of-lambda-functions-using-invokedynamic>

**Original** (section "Common Misconceptions", line 486):

````markdown
- **"Generics make the app larger or slower."** False on JVM. Type erasure means zero runtime cost. (C++ templates do bloat; the JVM does not.)
````

**Replacement:**

````markdown
- **"Generics make the app larger or slower."** Mostly false on the JVM: erasure means one class serves every type argument, so there is no code bloat (unlike C++ templates). It is not completely free: primitive type arguments are boxed (`List<Int>` holds `Integer` objects) and the compiler inserts casts.
````

## RE4

- **Chapter:** Reified Types (`kotlin/compiler-features/reified-types.md`)
- **Original says:** Question: why is `reified` "mathematically impossible" without `inline`?
- **Reason:** "Mathematically impossible" overstates it; other languages pass type information at runtime
- **Evidence:** —
- **Sources:** <https://kotlinlang.org/docs/inline-functions.html>

**Original** (section "Probing Questions", line 183):

````markdown
2.  Why is the `reified` keyword mathematically impossible to implement without also using the `inline` keyword?
````

**Replacement:**

````markdown
2.  Why does Kotlin allow `reified` only on `inline` functions?
````

## RE5

- **Chapter:** Reified Types (`kotlin/compiler-features/reified-types.md`)
- **Original says:** Answer to the same question
- **Reason:** The answer is right; only the question line needs the same fix
- **Evidence:** —
- **Sources:** <https://kotlinlang.org/docs/inline-functions.html>, <https://kotlinlang.org/api/core/kotlin-stdlib/kotlin.reflect/type-of.html>
- **Note:** Only the question line changes; the original answer below it stays.

**Original** (section "Answer Key", line 197):

````markdown
2. **Why is the `reified` keyword mathematically impossible to implement without also using the `inline` keyword?**
````

**Replacement:**

````markdown
2. **Why does Kotlin allow `reified` only on `inline` functions?**
````

## C18

- **Chapter:** Coroutines (`kotlin/coroutines-and-flow/coroutines.md`)
- **Original says:** Calls the hard-coded `Dispatchers.IO` example "Dispatcher injection"
- **Reason:** Hard-coding is not injection
- **Evidence:** —
- **Sources:** <https://developer.android.com/kotlin/coroutines/coroutines-best-practices>

**Original** (section "The main-safety contract", line 137):

````markdown
Now no caller anywhere thinks about threading. The repository owns its own main-safety. This is **Dispatcher injection** — and in practice you inject a `CoroutineDispatcher` rather than reference `Dispatchers.IO` directly so tests can substitute a `TestDispatcher`.
````

**Replacement:**

````markdown
Now no caller anywhere thinks about threading. The repository owns its own main-safety. In practice you also **inject** the `CoroutineDispatcher` instead of referencing `Dispatchers.IO` directly, so tests can substitute a `TestDispatcher`.
````

## C24

- **Chapter:** Coroutines (`kotlin/coroutines-and-flow/coroutines.md`)
- **Original says:** `Repo` scope built on `Job()`
- **Reason:** After one failed save, the scope is cancelled and every later save silently never runs. `SupervisorJob` alone fixes that but an uncaught failure still crashes an Android app
- **Evidence:** Run: with `Job()`, the second `launch` is cancelled; with `SupervisorJob()`, the scope stays active but the `IOException` reaches the thread's uncaught handler
- **Sources:** <https://developer.android.com/kotlin/coroutines/coroutines-best-practices>
- **Note:** The whole code block is replaced; `IOException` comes from `java.io`, as elsewhere in the chapter.
- **Replacement checked:** Compiled and run with a body that throws `IOException` on the first save: the failure is caught, the scope stays active, and the second save prints `saved`.

**Original** (section "Scope = lifetime owner", line 179):

````markdown
```kotlin
class Repo {
    private val scope = CoroutineScope(Job() + Dispatchers.IO)

    fun save(data: Data) {
        scope.launch { /* runs on IO */ }
    }

    fun close() {
        scope.cancel()   // every in-flight save cancels
    }
}
```
````

**Replacement:**

````markdown
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
````

## C40

- **Chapter:** Coroutines (`kotlin/coroutines-and-flow/coroutines.md`)
- **Original says:** `runTest` builds a `ViewModel` without replacing `Dispatchers.Main`; passes `dispatcher =`
- **Reason:** `viewModelScope` needs `Dispatchers.setMain` in JVM tests; the parameter is named `ioDispatcher`
- **Evidence:** Android coroutine testing docs
- **Sources:** <https://developer.android.com/kotlin/coroutines/test>
- **Replacement checked:** Not compiled here: it needs the chapter's `CartViewModel`, JUnit 4 and Android `ViewModel`. `MainDispatcherRule` is defined in the Test Dispatchers chapter; `ioDispatcher` is the constructor parameter of the chapter's `CartViewModel`.

**Original** (section "`runTest` — virtual time for unit tests", line 472):

````markdown
```kotlin
@Test
fun cartCheckout() = runTest {
    val viewModel = CartViewModel(repo, dispatcher = StandardTestDispatcher(testScheduler))
    viewModel.checkout()
    advanceUntilIdle()      // run all pending coroutines without real waiting
    assertEquals(Success, viewModel.state.value)
}
```
````

**Replacement:**

````markdown
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
````

## C56

- **Chapter:** Coroutines (`kotlin/coroutines-and-flow/coroutines.md`)
- **Original says:** Answer Key: blocking calls "monopolize the 4 cores while waiting"
- **Reason:** They occupy threads, not cores
- **Evidence:** Same as C16
- **Sources:** <https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-dispatchers/-i-o.html>

**Original** (section "Answer Key", line 580):

````markdown
so it allows up to 64 threads. If you run 10 IO calls on `Default`, they monopolize the 4 cores while waiting, blocking the 10 CPU tasks and taking ~1800ms. On `IO`, all 10 wait concurrently, leaving `Default` free for CPU work, taking ~800ms.
````

**Replacement:**

````markdown
so it allows up to 64 threads. If you run 10 blocking calls on `Default`, they occupy all 4 `Default` threads while waiting, delaying the 10 CPU tasks: ~1800 ms. On `IO`, all 10 wait concurrently, leaving `Default` free for CPU work: ~800 ms.
````

## CH4

- **Chapter:** Channels and Select (`kotlin/coroutines-and-flow/channels-and-select.md`)
- **Section:** Actor-Style State Ownership
- **Reason:** The worker must release active and undelivered checkout replies and reject submissions after shutdown, including cancellation before startup. An active caller receives CartStoppedException on actor shutdown, while its own cancellation remains CancellationException. A service-local timeout or cancellation fails only that request with CheckoutRequestCancelledException when the worker remains active; unexpected failures still stop the worker and follow the owner's reporting policy. When submit() returns a result, forward it without a post-call cancellation check. Cancellation or failure before receipt delivery can leave the outcome unknown; use idempotency or reconcile server state before retrying.
- **Sources:** <https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-coroutine-start/-d-e-f-a-u-l-t/>, <https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-job/invoke-on-completion.html>, <https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/>, <https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/ensure-active.html>, <https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-send-channel/send.html>
- **Scope:** Replace the complete `CartActor` class. The command types and public method signatures remain the same; shutdown is now a normal `CartStoppedException` for active callers. The replacement also declares two exception types. The enclosing file needs `java.io.IOException` and the coroutine/channel imports.
- **Regression checks:** `website/scripts/check_kotlin_examples.py` compiles this exact proposal with the chapter's command types. It checks expected failure/recovery, shutdown while processing, buffered and suspended senders, cancellation before startup, and construction with an already-cancelled owner. It also checks a service-local timeout followed by recovery, active callers displaying shutdown errors, caller-owned cancellation, and a checkout that commits while its owner shuts down. Unexpected worker failures retain the owner's uncaught-error policy.
- **Ownership:** Accepted commands belong to the actor's owner. Cancelling a caller waiting for a reply does not roll back a command that was already accepted. This in-memory example provides no durability promise.

**Original** (Actor-Style State Ownership):

````kotlin
class CartActor(
    scope: CoroutineScope,
    private val checkout: CheckoutService
) {
    private val commands = Channel<CartCommand>(capacity = Channel.BUFFERED)

    init {
        scope.launch {
            var items = emptyList<Item>()
            for (command in commands) {
                when (command) {
                    is CartCommand.Add -> items = items + command.item
                    is CartCommand.Remove -> items = items.filterNot { it.id == command.id }
                    is CartCommand.Checkout -> {
                        command.replyTo.complete(checkout.submit(items))
                    }
                }
            }
        }
    }

    suspend fun add(item: Item) {
        commands.send(CartCommand.Add(item))
    }

    suspend fun checkout(): CheckoutResult {
        val reply = CompletableDeferred<CheckoutResult>()
        commands.send(CartCommand.Checkout(reply))
        return reply.await()
    }
}
````

**Replacement:**

````kotlin
class CartStoppedException(cause: Throwable? = null) :
    IllegalStateException("CartActor stopped", cause)

class CheckoutRequestCancelledException(cause: CancellationException) :
    IllegalStateException("Checkout was cancelled while its actor remained active", cause)

class CartActor(
    scope: CoroutineScope,
    private val checkout: CheckoutService
) {
    private val commands = Channel<CartCommand>(
        capacity = Channel.BUFFERED,
        onUndeliveredElement = { command ->
            if (command is CartCommand.Checkout) {
                command.replyTo.completeExceptionally(CartStoppedException())
            }
        }
    )

    init {
        val worker = scope.launch {
            var items = emptyList<Item>()
            for (command in commands) {
                when (command) {
                    is CartCommand.Add -> items = items + command.item
                    is CartCommand.Remove -> items = items.filterNot { it.id == command.id }
                    is CartCommand.Checkout -> {
                        try {
                            currentCoroutineContext().ensureActive()
                            val result = checkout.submit(items)
                            // A finished checkout keeps its result, even if shutdown began meanwhile.
                            command.replyTo.complete(result)
                        } catch (error: CancellationException) {
                            try {
                                currentCoroutineContext().ensureActive()
                            } catch (stopped: CancellationException) {
                                // Owner/worker shutdown is an ordinary error to an active caller.
                                command.replyTo.completeExceptionally(CartStoppedException(stopped))
                                throw stopped
                            }
                            // A service-local timeout did not cancel the worker. Fail one request.
                            command.replyTo.completeExceptionally(CheckoutRequestCancelledException(error))
                        } catch (error: IOException) {
                            command.replyTo.completeExceptionally(error)
                        } catch (error: Throwable) {
                            command.replyTo.completeExceptionally(error)
                            throw error // Preserve the owner's unexpected-failure policy.
                        }
                    }
                }
            }
        }
        worker.invokeOnCompletion { cause ->
            // Runs even when cancellation prevented the worker body from starting.
            val stopped = CancellationException("CartActor stopped")
            if (cause != null) stopped.initCause(cause)
            commands.cancel(stopped)
        }
    }

    private suspend fun send(command: CartCommand) {
        currentCoroutineContext().ensureActive()
        try {
            commands.send(command)
        } catch (error: CancellationException) {
            // Preserve this caller's own cancellation; translate cancellation of the channel.
            currentCoroutineContext().ensureActive()
            throw CartStoppedException(error)
        }
    }

    suspend fun add(item: Item) {
        send(CartCommand.Add(item))
    }

    suspend fun checkout(): CheckoutResult {
        val reply = CompletableDeferred<CheckoutResult>()
        send(CartCommand.Checkout(reply))
        return reply.await()
    }
}
````

## JV12

- **Chapter:** JVM Interop (`kotlin/runtime-and-jvm/jvm-interop.md`)
- **Original says:** Comment: "`.toString()` on `Any!` is fine … CRASHES if tag is null"
- **Reason:** Calling `toString()` on a platform-typed null crashes. Codex's text says it safely returns "null", which is also wrong
- **Evidence:** `javap`: `invokevirtual Object.toString`; run: `NullPointerException`
- **Sources:** <https://kotlinlang.org/api/core/kotlin-stdlib/kotlin/to-string.html>

**Original** (section "Calling Android SDK Java from Kotlin: platform types in action", line 452):

````markdown
// CRASHES at runtime if tag is null:
val tagStr: String = view.tag.toString()       // .toString() on Any! is fine, but if you assign to non-null String and tag is null...
````

**Replacement:**

````markdown
// CRASHES at runtime if tag is null: on a platform type, toString() calls Object.toString() directly
val tagStr: String = view.tag.toString()
````

## BY8

- **Chapter:** Kotlin: Bytecode and Decompilation (`kotlin/runtime-and-jvm/bytecode.md`)
- **Original says:** Listing shows `greeting()` reading `name` through `invokevirtual getName()`
- **Reason:** Inside the class, Kotlin reads the field directly
- **Evidence:** `javap`: `greeting()` uses `getfield name`
- **Note:** Two replacements in the same listing and its observations. The instruction stays 3 bytes long, so later offsets are unchanged.

**Original** (section "Property access", line 123):

````markdown
    13: invokevirtual #7 // Method getName:()Ljava/lang/String;
````

**Replacement:**

````markdown
    13: getfield     #2 // Field name:Ljava/lang/String;
````

**Original** (section "Property access", line 130):

````markdown
1. `val name` becomes a **field** (`getfield`) **plus** a getter method. Accessing `user.name` from Kotlin calls `getName()`, not the field directly.
````

**Replacement:**

````markdown
1. `val name` becomes a **field** plus a getter method. Code inside `User` reads the field directly (`getfield`); code in other classes calls `getName()`.
````

## K1

- **Chapter:** Kotlin 2.4 Update for Android and KMP (`kotlin/version-updates/kotlin-2-4-update.md`)
- **Original says:** `var token: String?` with `field = null` and `private set`
- **Reason:** Does not compile: explicit backing fields are `val`-only
- **Evidence:** Compiler: "only 'val' properties with explicit backing fields are supported"
- **Replacement checked:** Compiled and run (Kotlin 2.4.21): `token=abc`; callers see a `StateFlow` backed by the `MutableStateFlow`.

**Original** (section "Explicit backing fields are Stable", line 50):

````markdown
class Session {
    var token: String?
        field = null
        private set

    fun authenticate(newToken: String) {
        token = newToken
    }
}
````

**Replacement:**

````markdown
class Session {
    val token: StateFlow<String?>
        field = MutableStateFlow<String?>(null)

    fun authenticate(newToken: String) {
        token.value = newToken   // inside the class, token is the MutableStateFlow
    }
}
````
