# Kotlin Multiplatform: Overview & The K2 Compiler

> Kotlin Multiplatform (KMP) lets you write business logic once in Kotlin and compile it to JVM bytecode for Android *and* LLVM native machine code for iOS — no virtual machine on iOS, no JavaScript bridge, no JSON-over-bridge marshalling. Understanding the compiler pipeline, the `expect`/`actual` contract mechanism, and the K2 revolution is the foundation of every other KMP topic.

---

## Overview

Kotlin is not "an Android language." It is a **frontend language with pluggable backend targets**. When you write a `.kt` file, the Kotlin compiler frontend parses it into an intermediate representation. Then a *backend* translates that IR into a platform-specific output:

| Backend | Output | Runtime | Use Case |
|---|---|---|---|
| Kotlin/JVM | `.class` bytecode in `.jar` | JVM (Android ART, server JVMs) | Android apps, Spring servers |
| Kotlin/Native | LLVM IR → native ARM64/x86 machine code | No VM — bare metal | iOS, macOS, Linux, Windows |
| Kotlin/JS | JavaScript source | Browser V8 / Node.js | Web frontends |
| Kotlin/Wasm | WebAssembly binary | Browser Wasm runtime | Experimental web targets |

When you write KMP code in `commonMain`, the compiler frontend validates it against the **Kotlin Standard Library common subset** — no `java.io.File`, no `android.content.Context`, no `platform.Foundation.NSURL`. Those exist only in platform-specific source sets.

### KMP vs React Native vs Flutter — The Architectural Difference

Understanding *why* KMP is different is a Staff-level interview topic:

```text
┌──────────────────────────────────────────────────────────────┐
│ React Native                                                 │
│ ┌──────────┐    JSON Bridge    ┌──────────────────┐          │
│ │ JS Thread|  ───────────────  │ Native UI Thread │          │
│ └──────────┘   (serialization  └──────────────────┘          │
│                 overhead)                                    │
├──────────────────────────────────────────────────────────────┤
│ Flutter                                                      │
│ ┌──────────┐    Dart VM       ┌──────────────────┐           │
│ │ Dart Code│ ──────────────   │ Skia Canvas (own │           │
│ └──────────┘   (GC pauses)    │ rendering, no    │           │
│                               │ native UIKit)    │           |
|                               └──────────────────┘           │
├──────────────────────────────────────────────────────────────┤
│ KMP                                                          │
│ ┌──────────┐    Direct call   ┌──────────────────┐           │
│ │ Kotlin   │ ──────────────   │ Native ARM64 code│           │
│ │ Source   |   (compiled to   │ (same as Swift   │           │
│ └──────────┘   machine code)  │ output)          │           |
|                               └──────────────────┘           │
└──────────────────────────────────────────────────────────────┘
```

**React Native** marshals data as JSON between a JavaScript thread and the native thread. Every function call crossing the bridge pays a serialization tax. This is why complex animations stutter.

**Flutter** compiles Dart to native code but draws *all* UI using its own Skia canvas — it does not use UIKit at all. The UI looks identical on both platforms but doesn't respect iOS-specific conventions (e.g., the back-swipe gesture).

**KMP** compiles Kotlin to the *exact same ARM64 machine code* that Swift compiles to. There is no bridge, no serialization, no VM. The compiled Kotlin function executes at native speed, directly callable from Swift via an Objective-C header. The UI remains fully native (Jetpack Compose on Android, SwiftUI on iOS).

---

## The `expect` / `actual` Mechanism

KMP's core language-level tool for platform abstraction is `expect`/`actual`. It is resolved entirely at **compile time** — the compiler replaces every `expect` declaration with the matching `actual` implementation for the current target, then continues compilation as if the `expect` never existed.

### The Problem It Solves

You need a UUID in `commonMain`. You cannot use `java.util.UUID` (JVM-only) or `platform.Foundation.NSUUID` (iOS-only). You need a compile-time guarantee that every platform *will* provide an implementation.

### Step 1: The Contract (`commonMain`)

```kotlin
// shared/src/commonMain/kotlin/com/example/Platform.kt
package com.example

/**
 * Platform-specific metadata. Every target MUST provide an [actual] implementation.
 * If any target is missing an [actual], the project will not compile.
 */
expect class Platform() {
    val osName: String
    val osVersion: String
    fun generateUUID(): String
}

// You can also expect top-level functions and properties:
expect fun currentTimeMillis(): Long
```

### Step 2: The Android Implementation (`androidMain`)

```kotlin
// shared/src/androidMain/kotlin/com/example/Platform.android.kt
package com.example

import android.os.Build
import java.util.UUID

actual class Platform actual constructor() {
    actual val osName: String = "Android ${Build.VERSION.SDK_INT}"
    actual val osVersion: String = Build.VERSION.RELEASE

    actual fun generateUUID(): String = UUID.randomUUID().toString()
}

actual fun currentTimeMillis(): Long = System.currentTimeMillis()
```

### Step 3: The iOS Implementation (`iosMain`)

```kotlin
// shared/src/iosMain/kotlin/com/example/Platform.ios.kt
package com.example

import platform.UIKit.UIDevice
import platform.Foundation.NSUUID
import platform.Foundation.NSDate
import platform.Foundation.timeIntervalSince1970

actual class Platform actual constructor() {
    actual val osName: String = UIDevice.currentDevice.systemName
    actual val osVersion: String = UIDevice.currentDevice.systemVersion

    actual fun generateUUID(): String = NSUUID().UUIDString()
}

actual fun currentTimeMillis(): Long =
    (NSDate().timeIntervalSince1970 * 1000).toLong()
```

### What You Can `expect`

| Declaration | Example | Notes |
|---|---|---|
| `expect class` | `expect class Platform()` | Must match constructor signature exactly |
| `expect fun` | `expect fun log(msg: String)` | Top-level function |
| `expect val` / `var` | `expect val isDebug: Boolean` | Top-level property |
| `expect object` | `expect object Analytics` | Singleton |
| `expect annotation` | `expect annotation class Parcelize()` | Used for Android Parcelable |
| `expect interface` | ❌ Not allowed | Use regular interfaces instead |

### When `expect`/`actual` Is Wrong

`expect`/`actual` is a **compile-time** mechanism — every target *must* provide an `actual`, or the build fails. This is extremely rigid:

```kotlin
// BAD: You just created a maintenance burden for every new target
expect class DatabaseDriver()          // Now you MUST write actuals for JVM, iOS, JS, Wasm...
expect class HttpEngine()              // Same problem
expect class AnalyticsTracker()        // Same problem
expect class CrashReporter()           // 50 expect classes = unmaintainable
```

**Staff Rule:** Use `expect`/`actual` only for **thin, primitive wrappers** (UUID, time, logging). For everything else (networking, database, analytics), use **interfaces + Dependency Injection** (Koin). With DI, the platform-specific implementation is injected at runtime — you can add new targets or swap implementations without touching `commonMain` at all.

```kotlin
// GOOD: Interface in commonMain, implementations injected via Koin
interface DatabaseDriver {
    fun execute(sql: String)
}

// In androidMain: class AndroidDriver(context: Context) : DatabaseDriver { ... }
// In iosMain:     class IOSDriver : DatabaseDriver { ... }
// In Koin module: single<DatabaseDriver> { AndroidDriver(get()) }
```

The difference matters in interviews:
- `expect`/`actual` = **compile-time polymorphism**, enforced by the compiler.
- `interface` + DI = **runtime polymorphism**, enforced by the DI graph.

---

## The K2 Compiler Revolution

Kotlin Multiplatform existed since 2017 but was marked "Alpha" for six years. The technical reason: the K1 compiler's architecture was fundamentally hostile to multiplatform compilation. K2 (default since Kotlin 2.0, released May 2024) is a complete rewrite of the compiler frontend.

### The K1 Problem (Technical Detail)

K1 used a **multi-pass resolution** architecture. For every source set in the hierarchy (`commonMain` → `appleMain` → `iosArm64Main`), K1 would:

1. Parse all files in the source set.
2. Resolve all type references against the source set's dependencies.
3. Check for `expect`/`actual` matching.
4. Generate the IR (Intermediate Representation).

For a project with `commonMain`, `androidMain`, `iosX64Main`, `iosArm64Main`, `iosSimulatorArm64Main`, and `appleMain`, K1 would run these passes **six times** — once for each leaf target. Many of these passes redundantly re-analyzed the exact same `commonMain` code.

**Concrete Impact:** A mid-sized KMP project (~200 files in `commonMain`) took 45-90 seconds for a clean build on K1. Incremental builds after touching a single file in `commonMain` often took 15-20 seconds because K1 couldn't efficiently determine which targets were affected.

### The K2 Solution: FIR (Frontend Intermediate Representation)

K2 introduces a **unified resolution** architecture. The new pipeline:

```text
K1 Pipeline (old):
  Source → [Parse] → [Resolve per-target] × N targets → [IR] → [Backend]
  
K2 Pipeline (new):
  Source → [Parse] → [FIR (unified resolve)] → [IR] → [Backend per-target]
```

The FIR phase resolves types and checks `expect`/`actual` contracts **once**, producing a single intermediate representation. Only the final backend code generation (JVM bytecode, LLVM IR) is duplicated per target.

**K2 Improvements — Concrete Numbers:**

| Metric | K1 | K2 | Improvement |
|---|---|---|---|
| Clean build (200-file KMP project) | ~60s | ~30s | **2x** |
| Incremental build (1 file changed in commonMain) | ~18s | ~5s | **3.6x** |
| IDE syntax highlighting lag | Frequent red squiggles | Rare | Qualitative |
| Smart casts across `expect`/`actual` | Broken in complex cases | Works | Critical for sealed classes |

### K2 and Smart Casts (The Subtle Win)

K1 couldn't propagate smart casts across `expect`/`actual` boundaries. This caused real pain:

```kotlin
// commonMain
expect sealed class NetworkResult
expect class Success(data: String) : NetworkResult
expect class Failure(error: Throwable) : NetworkResult

fun handle(result: NetworkResult) {
    when (result) {
        is Success -> println(result.data)   // K1: ERROR — cannot smart-cast
        is Failure -> println(result.error)  // K1: ERROR — cannot smart-cast
    }
}
```

K1 would fail because it couldn't prove exhaustiveness of a `when` block over an `expect sealed class` — it didn't know if the `actual` implementations on each platform might add extra subclasses. K2's unified FIR resolves this correctly.

### K2 and Swift Export

The K1 compiler could only generate Objective-C headers (`.h` files) for iOS consumption. Swift had to go through the Objective-C bridge, losing `sealed class` exhaustiveness, default arguments, coroutine cancellation, and more.

K2's architecture enables Kotlin's newer **Swift export** pipeline. In Kotlin 2.4, Swift export is Alpha. Instead of exposing Kotlin only through Objective-C headers, the compiler can generate Swift-facing modules with cleaner package/module structure and better Swift concurrency interop.

What it improves today:

- Kotlin packages and modules can map more cleanly to Swift modules.
- Kotlin type aliases can be preserved.
- Nullable primitive types map more naturally.
- Overloads are easier to call from Swift.
- `suspend fun` exports as Swift `async`.
- `kotlinx.coroutines` Flow exports as Swift `AsyncSequence`.

It is still Alpha and incomplete. Generic type parameters are still erased to upper bounds, cross-language inheritance is unsupported, and teams must review the generated Swift API before treating it as a production contract.

---

## Hierarchical Project Structure

A modern KMP project uses a hierarchy to share code between *similar* platforms without duplicating `actual` implementations.

### The Full Hierarchy

```text
shared/
 └── src/
      ├── commonMain/             ← Pure Kotlin (zero platform APIs)
      │    └── kotlin/
      │         ├── domain/       ← Use cases, entities
      │         ├── data/         ← Repository interfaces
      │         └── presentation/ ← ViewModels (StateFlow)
      │
      ├── androidMain/            ← Full Android SDK access
      │    └── kotlin/
      │         └── Platform.android.kt
      │
      ├── appleMain/              ← Shared Apple code (Foundation, Darwin)
      │    └── kotlin/
      │         └── DateFormatter.apple.kt  ← NSDateFormatter
      │
      ├── iosMain/                ← UIKit-specific (inherits appleMain)
      │    └── kotlin/
      │         └── Platform.ios.kt
      │
      ├── macosMain/              ← AppKit-specific (inherits appleMain)
      │    └── kotlin/
      │         └── Platform.macos.kt
      │
      ├── jvmMain/                ← Server-side JVM (Spring, Ktor server)
      │    └── kotlin/
      │         └── Platform.jvm.kt
      │
      ├── commonTest/             ← Tests shared across all targets
      ├── androidUnitTest/        ← Android-specific tests (Robolectric)
      └── iosTest/                ← iOS simulator tests
```

### Why `appleMain` Exists

Without `appleMain`, you would have to duplicate Apple-specific `actual` implementations in both `iosMain` and `macosMain`:

```kotlin
// WITHOUT appleMain — duplicated code in iosMain AND macosMain
actual fun formatDate(epochMillis: Long): String {
    val date = NSDate(timeIntervalSince1970 = epochMillis / 1000.0)
    val formatter = NSDateFormatter()
    formatter.dateFormat = "yyyy-MM-dd"
    return formatter.stringFromDate(date)
}
```

With `appleMain`, you write this `actual` once, and both `iosMain` and `macosMain` inherit it automatically. The Kotlin compiler resolves the hierarchy at compile time — `iosMain` "sees" all declarations from `appleMain` and `commonMain`.

### Custom Intermediate Source Sets

You can create arbitrary intermediate source sets for unusual sharing patterns:

```kotlin
// build.gradle.kts
kotlin {
    sourceSets {
        // Create a custom intermediate source set for "non-JVM" targets
        val nonJvmMain by creating {
            dependsOn(commonMain)
        }
        iosMain { dependsOn(nonJvmMain) }
        jsMain { dependsOn(nonJvmMain) }
        // Now iosMain and jsMain share code that Android doesn't see
    }
}
```

---

## Common Pitfalls

### 1. The "It works on Android" Trap
You write and test everything in Android Studio. It compiles, tests pass, ship it. Then the iOS build fails because you accidentally imported `java.net.URL` in a `commonMain` file. Android Studio's syntax highlighting does not always catch JVM-only imports in `commonMain` when the IDE is in "Android" mode.

**Fix:** Always run `./gradlew :shared:iosSimulatorArm64Test` locally before pushing. Better yet, configure a pre-commit hook.

### 2. The `lateinit` Crash on Native
Kotlin/Native handles `lateinit` differently than the JVM. On the JVM, accessing an uninitialized `lateinit var` throws `UninitializedPropertyAccessException`. On Kotlin/Native, the behavior is the same in modern versions, but older versions would segfault silently.

**Fix:** Prefer `lazy` or nullable types with explicit null checks over `lateinit` in `commonMain`.

### 3. The Coroutine Dispatcher Mismatch
`Dispatchers.IO` behaves differently across platforms. On JVM, it's a 64-thread elastic pool. On Kotlin/Native (pre-1.7.0), it didn't exist at all — `Dispatchers.Default` was used as a fallback.

**Fix:** Always use `kotlinx-coroutines` version 1.7.0+ in KMP projects, which provides `Dispatchers.IO` on all platforms.

---

## Probing Questions

1.  **Compiler Architecture:** Walk through what happens when you run `./gradlew :shared:linkReleaseFrameworkIosArm64`. What compiler phases execute, what intermediate representations are produced, and what is the final output artifact?
2.  **`expect`/`actual` vs Interfaces:** You have a `CrashReporter` that sends crashes to Firebase on Android and Sentry on iOS. Should you use `expect class CrashReporter` or `interface CrashReporter` with DI? Justify your answer with concrete tradeoffs (compile-time safety, testability, adding a Wasm target later).
3.  **K2 FIR Unification:** Explain why K1's per-target resolution caused quadratic build time growth as targets were added, and how K2's FIR reduces this to linear.
4.  **Hierarchical Source Sets:** Your project supports iOS, macOS, and tvOS. You need to call `AVFoundation` APIs that exist on all three Apple platforms. Where do you put the code — in `iosMain`, `appleMain`, or a custom source set? What happens if `tvOS` doesn't support a specific `AVFoundation` API that the other two do?
5.  **The "It works on Android" trap:** Your `commonMain` code uses `String.format("%.2f", price)`. This compiles and works on Android. What happens on iOS, and why?

## Further Reading

- [`architecture-and-module-boundaries.md`](architecture-and-module-boundaries.md) — How to decide what goes in `commonMain` vs the native apps.
- [`build-system-and-source-sets.md`](../tooling/build-system-and-source-sets.md) — The Gradle configuration that defines the source set hierarchy.
- [`ios-distribution.md`](../tooling/ios-distribution.md) — How the Kotlin/Native output (the `.xcframework`) is consumed by Xcode.
- [`concurrency-and-memory.md`](../production/concurrency-and-memory.md) — How the JVM GC and the Kotlin/Native GC differ fundamentally.
- [`swift-interop.md`](../tooling/swift-interop.md) — Objective-C bridge limitations and the Kotlin 2.4 Swift export path.
