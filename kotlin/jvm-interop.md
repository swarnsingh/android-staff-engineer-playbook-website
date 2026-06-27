# JVM Interop

## Overview

Kotlin compiles to JVM bytecode and shares the runtime with Java. Within one Android module you can have Kotlin files calling Java files calling Kotlin files calling back into Java, all linked together at the bytecode level. This **bidirectional interop** is what made Kotlin adoptable in 2017 — teams could rewrite one file at a time without forking their codebases.

But the two languages have features the other doesn't. Kotlin has nullability in the type system; Java doesn't. Kotlin has default arguments; Java doesn't. Kotlin has `internal`, `inline`, properties, top-level functions, `object` singletons, sealed classes, and value classes; the JVM has none of these natively. The Kotlin compiler bridges the gap by **lowering** Kotlin features into JVM-compatible constructs and exposing **interop knobs** (a family of `@Jvm*` annotations) that let you tune what Java callers see.

This file explains how every Kotlin construct appears to a Java caller, how Java's lack of nullability bleeds into Kotlin as **platform types**, and which annotations and patterns Staff engineers use to design APIs that are ergonomic in both languages.

---

## Why It Exists

Kotlin's adoption strategy was "no rewrites required." A team with 500,000 lines of Java could add a `build.gradle` line and start writing new files in Kotlin tomorrow. For that to work, three things had to be true:

1. **Calling Java from Kotlin must feel natural.** A Java method returning a `String` should be callable from Kotlin as if it were a Kotlin function. But what's the Kotlin type — `String` or `String?`? Java doesn't say. The compromise is **platform types**, denoted `String!`, which behave as either at the cost of disabling null safety.
2. **Calling Kotlin from Java must produce a sane API.** Kotlin features that don't exist in Java (default arguments, top-level functions, `object` singletons) must be projected into bytecode shapes Java can call. The defaults are usually fine; when they're not, `@Jvm*` annotations give you a knob.
3. **The combined codebase must run on one JVM with one classloader.** No two-language runtime, no FFI bridge. Java sees Kotlin classes the same way it sees Java classes.

The hidden cost is mostly Kotlin-side: the language has to maintain awareness of Java's looseness everywhere it touches Java types. The most common production bug from this is a Kotlin variable typed as a non-null `String` that receives null from Java at runtime, crashing with `NullPointerException` — not Kotlin's fault, but the cost of pretending Java is null-safe.

---

## Historical Context

1. **Kotlin 0.x (2011–2015).** JetBrains designed Kotlin alongside their largely Java codebase (IntelliJ IDEA). Interop was a primary design constraint from day one.
2. **Kotlin 1.0 (2016).** Stable interop with Java 6+. Platform types, `@Jvm*` annotations, top-level functions as `XxxKt` classes, `object` singletons via `INSTANCE` field.
3. **Android Studio 3.0 (2017).** Google announced first-party Kotlin support for Android. Kotlin became the recommended language in 2019.
4. **Kotlin 1.3 (2018).** Added Java 8 default method support, letting Kotlin interfaces project default implementations as real Java 8 defaults (with `@JvmDefault`).
5. **Kotlin 1.5+ (2021–).** Value classes (`@JvmInline`), sealed interfaces, improved Java records interop.
6. **Kotlin/JVM 2.x (2024+).** Refinements to inline value class boxing, kotlin.Result interop, refined nullability inference from JSpecify annotations.

The arc: from minimal-viable-interop (just call each other) to designed-interop (Kotlin can expose a clean Java-facing API by default, with annotations for the cases where the default isn't right).

---

## First Principles

### 1. Calling Java from Kotlin: Platform Types

When Kotlin calls a Java method that returns `String`, the compiler doesn't know if the return value can be null. Java says nothing about nullability unless annotated.

```kotlin
// Suppose this Java method exists:
// public class UserDao { public String findById(long id) { ... } }

val name = UserDao().findById(42)  // What's the type of `name`?
```

The Kotlin type is `String!` — a **platform type**. You can use it as `String` *or* as `String?`, and Kotlin won't complain at compile time. If you treat it as `String` and the Java method returns null at runtime, you get a `NullPointerException` (or more precisely, an `IllegalStateException` from the intrinsics null check) at the point you assigned it to a non-null variable.

The convention is to **declare an explicit Kotlin type** at the boundary:

```kotlin
val name: String? = UserDao().findById(42)   // forces handling
val name: String = UserDao().findById(42)    // claims non-null; will crash if Java returns null
```

If the Java code has `@Nullable` or `@NotNull` annotations (from JSpecify, JetBrains annotations, javax, Android Support, or Spring), Kotlin reads them and produces proper `String?` or `String` types. Always annotate Java boundaries crossing into Kotlin.

### 2. Calling Kotlin from Java: Mapping Kotlin features

A Kotlin file is compiled into one or more JVM classes. Here's how each major feature maps:

| Kotlin construct | JVM artifact | Java caller writes |
|---|---|---|
| `class Foo` | `class Foo` | `new Foo()` |
| `object Singleton` | `class Singleton` with static `INSTANCE` field | `Singleton.INSTANCE.doThing()` |
| `companion object` of `Foo` | nested class `Foo$Companion` with `Companion` field on `Foo` | `Foo.Companion.doThing()` |
| top-level `fun bar()` in `Util.kt` | `class UtilKt` with static `bar()` | `UtilKt.bar()` |
| top-level `val X: Int = 10` | `class UtilKt` with static `getX()` (and field) | `UtilKt.getX()` |
| `val x: Int` property on `Foo` | private field `x`, public `getX()` | `foo.getX()` |
| `var x: Int` property on `Foo` | private field `x`, public `getX()`, `setX()` | `foo.getX()`, `foo.setX(5)` |
| `fun greet(name: String = "world")` | one method `greet(String)`; default value only available from Kotlin | `foo.greet("world")` — Java must always pass |
| `inline fun` | regular method; `inline` is a Kotlin-side optimization | callable but not inlined when called from Java |
| `internal fun bar()` | public method with mangled name `bar$module_name()` | callable but the mangled name is awkward |
| sealed class | abstract class with package-private constructor | extendable only from same package — Java can extend, but Kotlin won't recognize new subtypes in `when` |

### 3. The `@Jvm*` annotation family

Five annotations cover 95% of interop tuning:

- `@JvmStatic` — promote a companion object method to a real Java `static` method.
- `@JvmOverloads` — generate overloaded methods for Java callers when using default arguments.
- `@JvmField` — expose a property as a public field (no getter/setter generation).
- `@JvmName("...")` — rename the JVM-visible method (used to escape name clashes or polish Java naming).
- `@JvmSuppressWildcards` / `@JvmWildcard` — control how generic variance is projected to Java's wildcard generics.

Each is a *boundary* tool. They affect Java visibility, never Kotlin.

### 4. `internal` is a Kotlin concept, not a JVM one

The JVM has four visibilities: `public`, `protected`, `private`, package-private (default). It has no concept of "module."

When you write `internal fun greet()`, Kotlin compiles it as `public` bytecode but **mangles the name** to include the module name:

```kotlin
internal fun greet(name: String) = "Hello, $name"
```

In bytecode: `public static String greet$mymodule_debug(String name)`.

From Kotlin in the same module, you write `greet("Ana")`. From any other Kotlin module or from Java, the function is invisible *by convention* (the IDE hides it), but callable *by name*. A determined Java caller can invoke `UtilKt.greet$mymodule_debug("Ana")`. `internal` is **compiler-enforced encapsulation**, not a runtime security boundary.

### 5. Default arguments are Kotlin-only

```kotlin
fun connect(host: String, port: Int = 80, useTls: Boolean = false) { ... }
```

Compiles to a single method `connect(String host, int port, boolean useTls)`. Kotlin callers can omit `port` and `useTls`; the compiler generates a *synthetic helper* `connect$default(String, int, boolean, int mask, Object marker)` that takes a bitmask indicating which arguments are present and fills in defaults.

Java callers see only the main `connect(String, int, boolean)` — no defaults. To get Java-callable overloads, add `@JvmOverloads`:

```kotlin
@JvmOverloads
fun connect(host: String, port: Int = 80, useTls: Boolean = false) { ... }
```

The compiler now also emits:

```java
public static void connect(String host, int port) { connect(host, port, false); }
public static void connect(String host) { connect(host, 80, false); }
```

`@JvmOverloads` only generates overloads for trailing parameters — Java still can't skip middle arguments.

---

## Mental Model

Think of Kotlin as a **second language layered over the JVM**, with its own type system, its own visibility rules, and its own optimizations. Bytecode is the lingua franca. When designing a Kotlin API:

- **What does Java see?** Mentally decompile your declaration. Is the method name reasonable? Is the parameter list usable without default arguments?
- **What does Kotlin see?** Are there hidden helpers (`$default`, `Companion`, `INSTANCE`)? Are they leaking into autocomplete or stack traces?
- **Where's the boundary?** Annotate Java code with `@Nullable`/`@NotNull` (JSpecify is the modern choice). At Kotlin boundaries calling Java, always declare types explicitly.

The boundary is where most bugs live. Internal-to-Kotlin code rarely surprises you; the surprises happen at the seam.

---

## Internal Mechanics

### How a top-level function becomes a Java class

```kotlin
// File: TextUtils.kt
package com.example

fun titleCase(s: String): String = s.replaceFirstChar { it.uppercase() }
```

Compiled to:

```java
// Class: com.example.TextUtilsKt
public final class TextUtilsKt {
    @NotNull
    public static final String titleCase(@NotNull String s) {
        Intrinsics.checkNotNullParameter(s, "s");
        // ...
    }
}
```

The Java class name is the file name + `Kt`. To rename, add a file-level annotation:

```kotlin
@file:JvmName("Strings")
package com.example

fun titleCase(s: String): String = ...
```

Now Java callers write `Strings.titleCase("hello")`. Use `@JvmMultifileClass` to merge functions from multiple files into one Java class.

### How `object` singletons work

```kotlin
object SessionManager {
    fun current(): Session? = ...
}
```

Compiled to:

```java
public final class SessionManager {
    public static final SessionManager INSTANCE;
    @Nullable
    public final Session current() { ... }
    private SessionManager() { ... }
    static { INSTANCE = new SessionManager(); }
}
```

The class has a private constructor and a public static `INSTANCE` field initialized in `<clinit>`. From Kotlin: `SessionManager.current()`. From Java: `SessionManager.INSTANCE.current()`.

To get a clean Java API, mark the methods `@JvmStatic`:

```kotlin
object SessionManager {
    @JvmStatic
    fun current(): Session? = ...
}
```

Now both can be called as a true static: `SessionManager.current()` from Java as well.

### How companion objects work

```kotlin
class Config {
    companion object {
        fun load(): Config = ...
    }
}
```

Compiled to:

```java
public final class Config {
    public static final Companion Companion = new Companion();
    public static final class Companion {
        @NotNull
        public final Config load() { ... }
    }
}
```

From Java: `Config.Companion.load()`. To clean it up, add `@JvmStatic` (and optionally `@JvmField` if exposing a property):

```kotlin
class Config {
    companion object {
        @JvmStatic
        fun load(): Config = ...

        @JvmField
        val MAX_SIZE = 1024
    }
}
```

Now Java sees `Config.load()` and `Config.MAX_SIZE` — clean, idiomatic Java.

### How properties become getters and setters

```kotlin
class User {
    val id: Long = 0
    var name: String = ""
    var isActive: Boolean = false
}
```

Compiled to:

```java
public final class User {
    private final long id = 0L;
    @NotNull private String name = "";
    private boolean isActive = false;

    public final long getId() { return id; }
    @NotNull public final String getName() { return name; }
    public final void setName(@NotNull String name) { ... }
    public final boolean isActive() { return isActive; }       // note: Boolean getter named `isX`, not `getIsX`
    public final void setActive(boolean active) { ... }
}
```

Boolean properties starting with `is` get a getter named the same as the property (`isActive()`), not `getIsActive()`. This matches the JavaBeans convention.

To expose a property as a raw field (no getter/setter):

```kotlin
class User {
    @JvmField val id: Long = 0
}
```

Java now sees `public final long id;` directly. Use sparingly — it loses encapsulation.

### `lateinit var` and `const val`

```kotlin
class MyService {
    lateinit var connection: Connection      // initialized later, throws if accessed before
    companion object {
        const val MAX_RETRIES = 3            // compile-time constant
    }
}
```

`lateinit` compiles to a `var` with a null backing field; access compiles to a check that throws `UninitializedPropertyAccessException` if null. Only works for non-null, non-primitive types.

`const val` (only on `object`, `companion object`, or top-level) becomes a Java `public static final` constant inlined at every call site. Required for use in Java annotations (which need true compile-time constants).

### Generics: declaration-site vs use-site

Kotlin's `out T` and `in T` declare variance at the class. Java uses wildcards (`? extends T`, `? super T`) at the use site. The compiler bridges this automatically; usually you don't think about it. When you do:

```kotlin
class Box<out T>(val value: T)

// In a Kotlin function returning a Box, the Java signature shows wildcards:
fun makeBoxes(): List<Box<Number>>
// Java sees: List<? extends Box<? extends Number>>
```

The `? extends` wildcards may surprise Java callers. To suppress them, use `@JvmSuppressWildcards`. To force them, use `@JvmWildcard`. The default is usually fine; tune only when interop breaks.

### Exceptions: Kotlin doesn't have checked exceptions

Kotlin treats all exceptions as unchecked. Java code calling a Kotlin function that throws `IOException` isn't forced to catch or declare it. To preserve Java's checked-exception API for Kotlin functions:

```kotlin
@Throws(IOException::class)
fun readConfig(): Config = File("config").readText().let { parse(it) }
```

`@Throws` adds a `throws IOException` clause to the Java bytecode signature, restoring Java's static check.

---

## Architecture

```mermaid
flowchart TB
    subgraph KT["Kotlin source"]
        KFun["fun greet(n: String = \"world\")"]
        KObj["object Singleton"]
        KComp["companion object"]
        KProp["val name: String"]
        KInt["internal fun"]
    end

    subgraph Bytecode["JVM bytecode"]
        Static["static method (mangled if internal)"]
        Inst["class with INSTANCE field"]
        CompCls["nested Companion class"]
        Getter["private field + public getter"]
    end

    subgraph Java["Java caller experience"]
        JStatic["UtilKt.greet(\"world\")"]
        JInst["Singleton.INSTANCE.doThing()"]
        JComp["Foo.Companion.doThing()"]
        JGet["user.getName()"]
    end

    KFun --> Static --> JStatic
    KObj --> Inst --> JInst
    KComp --> CompCls --> JComp
    KProp --> Getter --> JGet
    KInt --> Static
```

Each Kotlin construct has a deterministic JVM lowering. Knowing the mapping lets you predict the Java-facing API without compiling.

---

## Production Example

### A Kotlin-first SDK that supports Java consumers

```kotlin
// File: Telemetry.kt
@file:JvmName("Telemetry")
package com.example.sdk

object TelemetryClient {
    @JvmStatic
    @JvmOverloads
    fun event(name: String, properties: Map<String, Any> = emptyMap()) { ... }

    @JvmStatic
    fun flush(): Boolean { ... }

    @JvmField
    val SDK_VERSION = "1.2.3"
}
```

What this gives Java callers:

```java
Telemetry.event("user_signed_in");
Telemetry.event("checkout", Map.of("amount", 99.99));
boolean ok = Telemetry.flush();
String v = Telemetry.SDK_VERSION;
```

Without the annotations, Java callers would write:

```java
TelemetryKt.TelemetryClient.INSTANCE.event("user_signed_in", Collections.emptyMap());
boolean ok = TelemetryKt.TelemetryClient.INSTANCE.flush();
String v = TelemetryKt.TelemetryClient.INSTANCE.SDK_VERSION;  // would actually be getSDK_VERSION()
```

The annotations cost six lines of source and save every Java caller the boilerplate forever.

### Wrapping a Java callback API in suspend functions

```kotlin
suspend fun OkHttpClient.awaitResponse(request: Request): Response =
    suspendCancellableCoroutine { cont ->
        val call = newCall(request)
        call.enqueue(object : Callback {
            override fun onResponse(call: Call, response: Response) {
                cont.resume(response) { _, _, _ -> response.close() }
            }
            override fun onFailure(call: Call, e: IOException) {
                cont.resumeWithException(e)
            }
        })
        cont.invokeOnCancellation { call.cancel() }
    }
```

This is the prevailing pattern: a Kotlin extension on a Java class produces a `suspend` function callers can use idiomatically. Java callers can still use OkHttp directly with callbacks; Kotlin callers get the suspend version. Both coexist.

---

## Android Example

### Calling Android SDK Java from Kotlin: platform types in action

```kotlin
val context: Context = activity.applicationContext  // type is Context (not Context!) since SDK is annotated
val tag = view.tag                                   // type is Any! — view.getTag() returns Object with no annotation
val children = (view as ViewGroup).children          // KTX extension, returns Sequence<View>
```

`view.getTag()` returns `Object` from Java with no `@Nullable` or `@NonNull` annotation, so Kotlin types it as `Any!`. Treating the result as non-null without checking will crash if the tag wasn't set.

```kotlin
// SAFE:
val tag = view.tag as? String                  // null-safe cast

// CRASHES at runtime if tag is null:
val tagStr: String = view.tag.toString()       // .toString() on Any! is fine, but if you assign to non-null String and tag is null...
```

Modern Android SDK is well-annotated with `@Nullable`/`@NonNull`, so most platform types collapse to real `T?` or `T`. Older or sparsely-annotated libraries (especially internal libraries) leak platform types into your code.

### Designing a Kotlin SDK called from Java

```kotlin
class ImageLoader private constructor(private val context: Context) {
    @JvmOverloads
    fun load(
        url: String,
        placeholder: Int = R.drawable.placeholder,
        listener: ((Result<Bitmap>) -> Unit)? = null
    ) { ... }

    companion object {
        @JvmStatic
        fun with(context: Context): ImageLoader = ImageLoader(context)
    }
}
```

Java callers:

```java
ImageLoader.with(context).load("https://...");
ImageLoader.with(context).load("https://...", R.drawable.custom_placeholder);
ImageLoader.with(context).load("https://...", R.drawable.custom_placeholder, result -> { ... });
```

Lambda parameter (`((Result<Bitmap>) -> Unit)?`) compiles to a `Function1<Result<Bitmap>, Unit>` interface — Java callers can pass `null` or a lambda (Java 8+ SAM conversion handles function types automatically).

---

## Tradeoffs

**Advantages**

- **Incremental migration.** A team can adopt Kotlin file-by-file without disrupting the build or rewriting working Java.
- **Zero runtime overhead.** Interop is compile-time; there's no bridge layer or marshalling cost.
- **Shared ecosystem.** Every Java library — Retrofit, OkHttp, Room, Gson, Firebase SDKs — is callable from Kotlin as-is, often more cleanly than from Java thanks to extensions.
- **Designed knobs.** `@Jvm*` annotations let you ship one source file with two clean APIs (Kotlin and Java).

**Disadvantages**

- **Platform types disable null safety.** Every Java boundary is a potential NPE source. Annotating Java code or declaring explicit Kotlin types is the only defense.
- **Some Kotlin features have no Java equivalent.** Default arguments, named arguments, `inline`, and `internal` either don't exist or behave differently when called from Java.
- **Hidden synthetic methods clutter Java APIs.** `Companion` fields, `$default` helpers, mangled `internal` names show up in Java autocomplete and stack traces.
- **Annotations are easy to forget.** A missing `@JvmStatic` or `@JvmOverloads` quietly produces a worse Java API; nothing breaks, but the Java side gets harder to use.
- **Java callers can't take advantage of `value class`.** Inline value classes box back to their underlying type when crossing into Java, losing the type-safety benefit at the interop boundary.

**When not to lean on interop heavily**

- For a pure-Kotlin library with no Java consumers, don't sprinkle `@JvmStatic`/`@JvmOverloads`/`@JvmField` everywhere — they only matter if Java will call.
- For a library that's primarily Java-consumed, consider keeping the API surface in Java (or using a thin Java facade) — you'll spend less time fighting annotations than designing two APIs at once.

---

## Failure Modes

**Platform-type NPE at the boundary.** A Java method returns null; Kotlin treats it as non-null; Kotlin code crashes. Mitigation: annotate Java with `@Nullable`/`@NotNull` (JSpecify is the modern standard for new code), or declare explicit Kotlin types at the boundary.

**Default-argument call from Java.** A library author adds a new default parameter; Java callers' code doesn't break, but the parameter is now mandatory for Java. Mitigation: add `@JvmOverloads` to public Kotlin APIs that take default arguments.

**`internal` accidentally exposed via reflection.** A Java caller uses reflection to invoke a mangled `internal` method. Not a Kotlin bug, but surprising. Mitigation: don't rely on `internal` for security; use module boundaries and access tokens for sensitive APIs.

**Companion `INSTANCE` boilerplate.** Java callers without `@JvmStatic` write `MyClass.Companion.method()`. Mitigation: add `@JvmStatic` to public companion methods.

**Top-level function file rename.** Renaming `Util.kt` to `Strings.kt` changes the Java class from `UtilKt` to `StringsKt`. Java callers (and reflection-using code, ProGuard rules) break. Mitigation: add `@file:JvmName("Util")` to pin the class name regardless of file name.

**`@JvmField` on a `val` that you later want to make a property with a getter.** Removing `@JvmField` is a binary-incompatible change for Java callers. Mitigation: don't `@JvmField` until you're sure the property won't need a getter.

**Boolean property naming.** A `val hasFoo: Boolean` compiles to `getHasFoo()`. A `val isFoo: Boolean` compiles to `isFoo()`. Inconsistent boolean naming surprises Java callers. Mitigation: pick a prefix convention (`is`, `has`, `can`) and stick to it.

**Sealed class extension from Java.** Java can extend a Kotlin sealed class within the same package, but the Kotlin compiler then doesn't know about the new subtype. `when` becomes non-exhaustive at runtime. Mitigation: don't expose sealed classes for cross-language inheritance; use closed `interface` for cross-language and `sealed` only for Kotlin internals.

---

## Performance Considerations

- **Property access is a method call.** A Kotlin `val x` is a `getX()` method; in tight Java loops this can matter. JIT inlines aggressively after warmup, so usually negligible.
- **`@JvmField` removes the getter overhead.** For hot paths accessed from Java, exposing a property as a field shaves a method call. Trade off for the loss of encapsulation.
- **Companion object access goes through a static field.** `Foo.Companion` is a single static reference; no per-call allocation.
- **Default arguments require a synthetic helper.** `connect(host)` (omitting defaults) is two calls: `connect$default(...)` and the real `connect(...)`. Tiny but real overhead.
- **Inline functions don't inline when called from Java.** Java calls them as ordinary methods; the inlining benefit is Kotlin-only.
- **Reified generics aren't visible to Java.** A function `inline fun <reified T> get(): T` exposes no usable method to Java (the type parameter is erased at the call boundary). Provide a non-reified overload taking `Class<T>` for Java consumers.

---

## Reliability Considerations

- **Annotate every Java public API with `@Nullable` / `@NotNull`.** JSpecify is the modern standard (used by Android, AndroidX, and Google libraries). Without annotations, Kotlin produces platform types and you've moved null-safety enforcement out of the compiler and into runtime.
- **Use `@Throws` for Kotlin functions thrown from Java try/catch.** Without it, Java callers don't know to catch `IOException`.
- **Treat platform types as guilty until proven innocent.** When in doubt, declare an explicit `String?` at the boundary and handle null.
- **Don't rename `JvmName`-annotated symbols casually.** Renaming a `@JvmName` annotation is a binary-incompatible change. Document `@JvmName` choices in API design docs.

---

## Security Considerations

- **`internal` is not a security boundary.** Reflection from Java can call mangled-name functions. Don't gate security-sensitive operations on `internal` visibility.
- **`@JvmField` exposes mutable fields.** A `@JvmField var token: String` lets any caller (Kotlin or Java) write directly, bypassing any setter validation you might add later. Avoid for mutable state.
- **Platform types can hide tainted data.** A `String!` from a Java method might be unsanitized user input; treat boundary data as untrusted regardless of Java's annotations.
- **Be wary of `companion object` factories returning sensitive resources.** They survive across the entire process; if they hold a network connection or unencrypted token, it persists.

---

## Observability

- **Stack traces show Kotlin compiler artifacts.** A `NullPointerException` in a Kotlin function called from Java may show `Intrinsics.checkNotNullParameter` at the top of the stack — that's the runtime null check Kotlin generated at the parameter. The actual bug is usually one frame down (the Java caller passing null).
- **Mangled `internal` names in stack traces.** A frame like `Foo.bar$mymodule_debug` means the called function was `internal`. Recognize the mangling.
- **`Companion` and `$default` frames** indicate companion-object access or default-argument resolution. Usually benign.

---

## Staff Engineer Thinking

**Treat the Java API as a first-class design surface for SDKs.** If your Kotlin library has Java consumers, write three example Java call sites for each public function during code review. If those examples are ugly, add `@Jvm*` annotations until they're not.

**Standardize on JSpecify or JetBrains annotations for the team's Java code.** A repo-wide lint rule that requires `@Nullable` / `@NotNull` on public Java APIs eliminates 80% of platform-type bugs. Pair it with a Detekt rule rejecting bare assignment of platform types to non-nullable Kotlin types.

**Document the interop contract.** When a Kotlin file is intentionally Java-facing, put a comment at the top: `// Public API — Java callers depend on this. Don't change @JvmName, don't add default-args without @JvmOverloads.` Saves PR roundtrips.

**Audit `@JvmField` aggressively.** It's the only annotation that becomes a binary-compatibility commitment to mutable state. Most uses should be `val` (read-only) — and ideally `const val` or a `@JvmStatic` getter.

**Migrate away from companion `INSTANCE` for public APIs.** New SDK design should default to top-level functions with `@file:JvmName(...)`. Companion objects are useful for class-scoped factories; for module-scoped utilities, top-level is simpler.

**Watch for sealed-class interop gotchas.** If a sealed class is part of your public API and Java extends it (legally, within the same package), runtime `when` exhaustiveness assumptions break. Either keep sealed types fully internal or use `interface` for cross-language extensibility.

**Prefer composition over inheritance at the interop boundary.** Java is more comfortable composing — calling a Kotlin method that returns a configured object — than inheriting from a Kotlin class with default-argument constructors and named parameters. Design factories, not abstract bases, for Java consumers.

---

## Common Misconceptions

**"Kotlin and Java code can't coexist in the same module."** They can — the same `src/main/kotlin/` and `src/main/java/` directories produce one combined classpath.

**"Java callers see Kotlin features automatically."** They don't. Default arguments, named arguments, `inline`, `reified`, value classes — Java sees only what compiles to bytecode they can call. Annotations bridge the gap.

**"`internal` is hidden from Java."** It's *mangled*, not hidden. Reflection or knowing the mangled name reveals it.

**"Platform types only appear with old, unannotated Java code."** Any unannotated Java method produces platform types — including freshly-written internal Java in your own codebase. Annotation discipline matters.

**"`@JvmStatic` makes a method static in Kotlin too."** It changes how Java sees the method but Kotlin callers see no difference. `@JvmStatic` is a Java-only signal.

**"Top-level Kotlin functions are static methods in `Filename.kt` class."** Almost — it's `FilenameKt`, with the `Kt` suffix. Use `@file:JvmName` to drop the suffix.

**"You can call `inline fun` and get the inlined version from Java."** No. Java calls it as an ordinary method. Inlining is Kotlin-side.

**"Kotlin's `data class` is the same as Java records."** Similar but not identical. `data class` predates records (Java 14+) and has methods (`copy`, `componentN`) records don't. Records' canonical constructor is final; `data class` allows mutable `var` properties.

---

## Probing Questions

1. A Java method `String findUser(long id)` returns null. A Kotlin caller writes `val name: String = userDao.findUser(42)`. Walk through what happens and where the crash occurs.
2. Compile `object Logger { fun log(s: String) { ... } }` to bytecode. What's the Java call site to invoke `log`?
3. What's the difference between `@JvmStatic` on a companion object method and `@JvmField` on a companion object property?
4. A Kotlin function `fun connect(host: String, port: Int = 80)`. Show the JVM bytecode method signature with and without `@JvmOverloads`.
5. Why does `internal fun foo()` show up in Java reflection if `internal` is supposed to be module-private?
6. Decompile a `data class User(val name: String, var age: Int)` and list every method the compiler generated.
7. What does `@file:JvmName("Strings")` do, and why would you use it instead of just naming the file `Strings.kt`?
8. A Kotlin extension `fun String.titleCase()` lives in `StringExt.kt`. How does a Java caller invoke it?
9. Explain why `@Throws(IOException::class)` is necessary even though Kotlin doesn't have checked exceptions.
10. You have a Kotlin library with `value class UserId(val raw: Long)`. A Java caller wants to pass a `UserId`. What does the Java signature actually accept, and what's the type-safety implication?

---

## Further Reading

In this repository:

- [`null-safety.md`](null-safety.md) — platform types, intrinsics, `lateinit`, `!!` operator.
- [`bytecode.md`](bytecode.md) — how Kotlin features compile to JVM constructs; decompiled examples.
- [`extensions.md`](extensions.md) — extensions as static methods callable from Java via the file-class.
- [`data-classes.md`](data-classes.md) — how data classes interop with Java (and records).
- [`sealed-classes.md`](sealed-classes.md) — sealed-class interop nuances.
- [`functions.md`](functions.md) — function types, `fun interface` for cross-language callbacks.

External:

- Kotlin Documentation: [Java to Kotlin interop](https://kotlinlang.org/docs/java-to-kotlin-interop.html) — canonical reference for Java-calling-Kotlin.
- Kotlin Documentation: [Calling Java from Kotlin](https://kotlinlang.org/docs/java-interop.html) — calling Java APIs idiomatically from Kotlin.
- JSpecify project: [jspecify.dev](https://jspecify.dev/) — the modern unified standard for Java nullness annotations.
- Roman Elizarov, *"Designing Kotlin APIs for use from Java"* (KotlinConf 2019) — annotation guidance and patterns.
- Jake Wharton, *"Public API challenges in Kotlin"* (KotlinConf 2018) — managing binary compatibility across Kotlin/Java boundaries.
- *Effective Kotlin* by Marcin Moskała — Item 38: "Consider providing a Java-friendly API."
