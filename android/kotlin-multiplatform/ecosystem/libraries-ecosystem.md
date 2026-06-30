# KMP Libraries & The Ecosystem Shift

> When transitioning to Kotlin Multiplatform, an Android engineer faces an immediate culture shock: every JVM library you've relied on for years — Retrofit, OkHttp, Room, Hilt, Moshi, Gson — cannot exist in `commonMain`. They depend on `java.io`, `java.net`, Java reflection, or Android SDK classes that Kotlin/Native's LLVM backend cannot compile. A Staff engineer must know the exact failure mode for every blocked library and the KMP-native replacement stack.

---

## Overview

The fundamental constraint of KMP `commonMain` is:

> **If a library depends on any `java.*` or `android.*` class, it cannot be used in `commonMain`.**

This includes libraries that are "100% Kotlin" but internally use JVM platform APIs. For example, OkHttp is written entirely in Kotlin, but its HTTP engine calls `java.net.Socket`, `java.io.InputStream`, and `javax.net.ssl.SSLSocketFactory` — all JVM-only.

---

## Why Each Major Android Library Fails

### Retrofit
```text
Failure reason: Retrofit uses Java dynamic proxies (java.lang.reflect.Proxy)
to generate API interface implementations at runtime.
Kotlin/Native has NO java.lang.reflect package.
```

### OkHttp
```text
Failure reason: OkHttp's transport layer uses java.net.Socket, java.io.OutputStream,
and javax.net.ssl.SSLContext for TLS. These are JVM-specific I/O primitives.
Kotlin/Native uses POSIX sockets via C-interop or NSURLSession on Apple platforms.
```

### Room
```text
Failure reason: Room depends on android.database.sqlite.SQLiteOpenHelper,
which is part of the Android framework (not available on iOS).
Room also uses KSP/KAPT annotation processing to generate DAO implementations
that extend Android-specific classes.
```

### Hilt / Dagger
```text
Failure reason: Dagger generates Java source code via KAPT/KSP.
The generated code uses javax.inject annotations and Java class references
that have no equivalent in Kotlin/Native.
Furthermore, Dagger's component graph is wired via JVM reflection at compile time.
```

### Moshi / Gson
```text
Failure reason: Both rely on java.lang.reflect for runtime JSON parsing.
Moshi's codegen (KSP) generates JVM-specific adapter code.
Gson uses java.lang.reflect.Field to read/write object fields.
Kotlin/Native has no java.lang.reflect.
```

### Timber
```text
Failure reason: Timber's Tree abstraction uses android.util.Log internally.
android.util.Log is part of the Android framework SDK.
```

---

## The Canonical KMP Replacement Stack

| Domain | Legacy Android (JVM) | KMP Replacement (`commonMain`) | Key Difference |
|:---|:---|:---|:---|
| **HTTP Client** | Retrofit + OkHttp | **Ktor Client** | Imperative DSL vs declarative annotations |
| **JSON Serialization** | Moshi / Gson | **kotlinx-serialization** | Compiler plugin (no reflection) vs runtime reflection |
| **Relational Database** | Room | **SQLDelight** | Write SQL → generate Kotlin vs Write Kotlin → generate SQL |
| **Key-Value Store** | SharedPreferences / DataStore | **Multiplatform Settings** / **DataStore KMP** | `NSUserDefaults` on iOS vs custom file on iOS |
| **Dependency Injection** | Dagger / Hilt | **Koin** / **kotlin-inject** | Runtime service locator vs compile-time codegen |
| **Date/Time** | `java.time` / JodaTime | **kotlinx-datetime** | Wraps `java.time` on JVM, `NSDate` on iOS |
| **Concurrency** | RxJava / Threads | **kotlinx-coroutines** | Already KMP-native since 1.6.0 |
| **Logging** | Timber | **Kermit** (Touchlab) / **Napier** | `android.util.Log` on Android, `NSLog` on iOS |
| **Image Loading** | Coil / Glide | **Coil 3** (KMP) / **Kamel** | Coil 3 has experimental KMP support |
| **Cryptography** | `java.security` / Tink | **Diglol Crypto** / platform `expect/actual` | Wraps CommonCrypto on iOS |
| **Paging** | Jetpack Paging 3 | **Cash App Multiplatform Paging** | Fork of Paging 3 with KMP targets |
| **Testing** | JUnit / MockK | **kotlin-test** / **MocKMP** / **Mockative** | JUnit is JVM-only; kotlin-test is multiplatform |

---

## Deep Dive: kotlinx-serialization vs Moshi

This is the most common migration a team faces. Let's compare them in depth.

### Moshi (JVM-only)

```kotlin
// 1. Define a data class with Moshi annotations
@JsonClass(generateAdapter = true)
data class User(
    @Json(name = "user_id") val id: String,
    @Json(name = "full_name") val name: String,
    val email: String,
    val isActive: Boolean = true  // Default works
)

// 2. Create a Moshi instance
val moshi = Moshi.Builder()
    .add(KotlinJsonAdapterFactory())  // Uses reflection!
    .build()

// 3. Parse JSON
val adapter = moshi.adapter(User::class.java)
val user = adapter.fromJson(jsonString)
```

**How Moshi works:** KSP/KAPT generates a `UserJsonAdapter` class that knows how to read/write each field. The generated code uses `JsonReader` and `JsonWriter` which call `java.io.BufferedSource` under the hood. None of this compiles on Kotlin/Native.

### kotlinx-serialization (KMP-native)

```kotlin
// 1. Define a data class with @Serializable
@Serializable
data class User(
    @SerialName("user_id") val id: String,
    @SerialName("full_name") val name: String,
    val email: String,
    val isActive: Boolean = true  // Default works
)

// 2. Create a Json instance (no reflection!)
val json = Json { 
    ignoreUnknownKeys = true
    isLenient = true
    encodeDefaults = false
    prettyPrint = false
}

// 3. Parse JSON — identical code on Android AND iOS
val user: User = json.decodeFromString(jsonString)
val jsonOutput: String = json.encodeToString(user)
```

**How kotlinx-serialization works:** The `@Serializable` annotation triggers a **Kotlin Compiler Plugin** (not KSP/KAPT). The plugin generates a `User.Companion.serializer()` function at compile time. This function uses the Kotlin compiler's knowledge of the class structure — no reflection needed. The generated code is pure Kotlin with zero JVM dependencies, so it compiles identically on JVM, Native, JS, and Wasm.

### Migration Complexity

| Aspect | Moshi → kotlinx-serialization |
|---|---|
| Annotation rename | `@Json(name = "x")` → `@SerialName("x")` |
| Adapter creation | Delete all `Moshi.Builder()` code |
| Custom adapters | Rewrite as `KSerializer<T>` implementations |
| Polymorphic JSON | `@JsonClass(generator = "sealed:type")` → `@Serializable` + `@SerialName` on sealed subclasses |
| Retrofit integration | Replace `MoshiConverterFactory` with `KotlinxSerializationConverterFactory` |
| Ktor integration | Ktor natively supports kotlinx-serialization — just install `ContentNegotiation` plugin |

---

## Evaluating Unknown KMP Libraries (Staff Heuristic)

Before adding any new dependency to a KMP project, run it through this checklist:

### 1. Does it publish KMP targets?
Check the library's Maven Central page. A KMP library publishes multiple artifacts:
```
com.example:my-lib-jvm:1.0.0        ← JVM artifact
com.example:my-lib-iosarm64:1.0.0   ← iOS ARM64 artifact
com.example:my-lib-iosx64:1.0.0     ← iOS x64 artifact
com.example:my-lib:1.0.0            ← Gradle Metadata (the orchestrator)
```

If you only see `-jvm`, the library is JVM-only and cannot be used in `commonMain`.

### 2. How large is the iOS binary impact?
Every KMP library adds to the `.xcframework` size. Libraries with deep generic hierarchies or extensive inline functions can cause LLVM to generate massive amounts of machine code.

**Measurement:**
```bash
# Before adding the library
ls -lh build/bin/iosArm64/releaseFramework/SharedCode.framework/SharedCode
# → 4.2 MB

# After adding the library
ls -lh build/bin/iosArm64/releaseFramework/SharedCode.framework/SharedCode
# → 5.8 MB  (1.6 MB increase — is this acceptable?)
```

### 3. Is it actively maintained for all targets?
Some libraries publish KMP targets but only test on JVM. Check their CI configuration:
- Does CI run `iosSimulatorArm64Test`?
- Are there iOS-specific issues in the GitHub tracker?
- When was the last release?

### 4. Does it use `expect/actual` or pure Kotlin?
- **Pure Kotlin (e.g., kotlinx-serialization):** Identical behavior on all platforms.
- **`expect/actual` wrapper (e.g., Multiplatform Settings):** Wraps `SharedPreferences` on Android and `NSUserDefaults` on iOS. Behavioral differences are possible (e.g., `NSUserDefaults` is backed by plist XML, SharedPreferences by XML, DataStore by protobuf).

### 5. Does it block future Wasm support?
If you plan to add a Kotlin/Wasm target (for Compose Web), check if the library publishes `wasmJs` artifacts. Adding a library that doesn't support Wasm to `commonMain` will block your entire Wasm migration later.

---

## The "androidMain Escape Hatch" Pattern

Sometimes you genuinely need a JVM library (like Firebase Crashlytics) alongside your KMP shared code. The pattern is:

```kotlin
// commonMain — define the interface
interface CrashReporter {
    fun recordException(throwable: Throwable)
    fun setUserId(id: String)
    fun log(message: String)
}

// androidMain — use Firebase Crashlytics (JVM library)
class FirebaseCrashReporter : CrashReporter {
    override fun recordException(throwable: Throwable) {
        FirebaseCrashlytics.getInstance().recordException(throwable)
    }
    override fun setUserId(id: String) {
        FirebaseCrashlytics.getInstance().setUserId(id)
    }
    override fun log(message: String) {
        FirebaseCrashlytics.getInstance().log(message)
    }
}

// iosMain — use Sentry (available via CocoaPods C-interop)
class SentryCrashReporter : CrashReporter {
    override fun recordException(throwable: Throwable) {
        SentrySDK.captureException(throwable.asNSException())
    }
    override fun setUserId(id: String) {
        SentrySDK.setUser(SentryUser().apply { this.userId = id })
    }
    override fun log(message: String) {
        SentrySDK.addBreadcrumb(SentryBreadcrumb(level: .info, message: message))
    }
}
```

Your `commonMain` business logic calls `crashReporter.recordException(e)` without knowing (or caring) whether the underlying implementation is Firebase or Sentry.

---

## Probing Questions

1.  **OkHttp Paradox:** OkHttp is written 100% in Kotlin. Why can't it be used in `commonMain`? What specific JVM packages does it import that don't exist in Kotlin/Native?
2.  **Serialization Internals:** Explain how `kotlinx-serialization`'s compiler plugin approach avoids Java reflection. What does the generated `User.Companion.serializer()` function actually produce at the IR level?
3.  **Binary Size:** You add `kotlinx-datetime` to `commonMain`. On JVM it wraps `java.time` (zero binary impact). On Kotlin/Native, it must ship its own IANA timezone database. How does this affect iOS binary size, and how can you mitigate it?
4.  **Library Evaluation:** Your team wants to add `com.jakewharton.threetenabp:threetenabp:1.4.6` to `commonMain` for date handling. Walk through the evaluation heuristic. What do you discover, and what do you recommend instead?
5.  **The Wasm Trap:** You've built a successful KMP app sharing logic between Android and iOS. Product now wants a web version using Kotlin/Wasm. One of your `commonMain` dependencies doesn't publish a `wasmJs` artifact. What are your options?

## Further Reading

- [`networking-with-ktor.md`](networking-with-ktor.md) — Deep dive into the Ktor Client (the Retrofit replacement).
- [`persistence.md`](persistence.md) — Deep dive into SQLDelight (the Room replacement) and Multiplatform Settings.
- [`dependency-injection.md`](dependency-injection.md) — Koin as the Hilt/Dagger replacement, with the "androidMain Escape Hatch" pattern.
- [`build-system-and-source-sets.md`](../tooling/build-system-and-source-sets.md) — How Gradle resolves KMP library artifacts via `.module` metadata.
