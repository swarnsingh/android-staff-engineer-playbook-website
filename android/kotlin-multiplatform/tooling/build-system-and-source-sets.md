# KMP Build System & Source Sets

> The Kotlin Multiplatform Gradle Plugin is the single most complex Gradle plugin you will ever configure. It orchestrates multiple compiler backends (JVM bytecode, LLVM native code, JavaScript), manages a hierarchical tree of source sets, resolves platform-specific dependencies, and produces binaries for drastically different runtimes — all in a single `build.gradle.kts`. Understanding every section of this file is non-negotiable for a Staff KMP engineer.

---

## Overview

A standard Android module uses the `com.android.library` or `com.android.application` plugin. It compiles Kotlin to JVM bytecode, packages it into an `.aar` or `.apk`, and you're done.

A KMP module uses `org.jetbrains.kotlin.multiplatform`. It compiles the *same source code* to multiple backends simultaneously. The Gradle plugin must:

1. Set up source set directories (`commonMain`, `androidMain`, `iosMain`, etc.).
2. Resolve dependencies per source set (a dependency in `commonMain` must have published artifacts for *all* declared targets).
3. Configure the Kotlin/Native compiler to produce Apple Frameworks.
4. Hook into Android Gradle Plugin for the Android target.
5. Generate Xcode-compatible build tasks.

---

## The Complete `build.gradle.kts` Anatomy

Here is a production-grade shared module configuration with inline commentary:

```kotlin
// shared/build.gradle.kts

plugins {
    alias(libs.plugins.kotlinMultiplatform)  // org.jetbrains.kotlin.multiplatform
    alias(libs.plugins.androidLibrary)        // com.android.library (for the Android target)
    alias(libs.plugins.kotlinSerialization)    // kotlinx-serialization compiler plugin
    alias(libs.plugins.sqldelight)            // SQLDelight code generation
    id("co.touchlab.skie") version "0.9.0"   // SKIE Swift enhancement
}

kotlin {
    // =========================================================
    // 1. ANDROID TARGET
    // =========================================================
    androidTarget {
        compilations.all {
            kotlinOptions {
                jvmTarget = "17"  // Must match your Android project's JDK
            }
        }
    }

    // =========================================================
    // 2. iOS TARGETS (Three separate compilation targets)
    // =========================================================
    //
    // Why three?
    //   - iosArm64():            Physical iPhone/iPad (ARM64 chip)
    //   - iosX64():              iOS Simulator on Intel Macs (x86_64)
    //   - iosSimulatorArm64():   iOS Simulator on Apple Silicon (M1/M2/M3/M4)
    //
    // If you forget iosSimulatorArm64(), your M-series Mac cannot
    // run the iOS simulator at all.
    //
    listOf(
        iosX64(),
        iosArm64(),
        iosSimulatorArm64()
    ).forEach { iosTarget ->
        iosTarget.binaries.framework {
            baseName = "SharedCode"
            isStatic = true   // Static linking — one fewer .dylib to manage

            // Export dependencies so Swift can see their types in headers
            // Without this, Swift gets opaque types it can't use
            export(libs.kotlinx.coroutines.core)
        }
    }

    // =========================================================
    // 3. OPTIONAL: Desktop/Server JVM target
    // =========================================================
    // jvm()  // Uncomment if you want to share code with a Ktor server

    // =========================================================
    // 4. SOURCE SET DEPENDENCY GRAPH
    // =========================================================
    sourceSets {
        // --- COMMON (All platforms) ---
        commonMain.dependencies {
            implementation(libs.kotlinx.coroutines.core)
            implementation(libs.kotlinx.serialization.json)
            implementation(libs.ktor.client.core)
            implementation(libs.ktor.client.content.negotiation)
            implementation(libs.ktor.serialization.kotlinx.json)
            implementation(libs.koin.core)
            implementation(libs.kotlinx.datetime)
        }

        commonTest.dependencies {
            implementation(libs.kotlin.test)              // NOT JUnit!
            implementation(libs.kotlinx.coroutines.test)
        }

        // --- ANDROID ---
        androidMain.dependencies {
            implementation(libs.ktor.client.okhttp)       // OkHttp engine
            implementation(libs.sqldelight.android.driver) // AndroidSqliteDriver
            implementation(libs.koin.android)
        }

        // --- iOS ---
        // The KMP plugin auto-creates iosMain as a shared intermediate
        // source set. You do NOT need to create iosX64Main, iosArm64Main,
        // etc. separately — they all inherit from iosMain.
        iosMain.dependencies {
            implementation(libs.ktor.client.darwin)        // NSURLSession engine
            implementation(libs.sqldelight.native.driver)  // NativeSqliteDriver
        }
    }
}

// =========================================================
// 5. ANDROID BLOCK (Required when using androidTarget)
// =========================================================
android {
    namespace = "com.example.shared"
    compileSdk = 34
    defaultConfig {
        minSdk = 26
    }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
```

---

## Source Set Resolution — How Dependencies Actually Work

### The Dependency Resolution Chain

When you put `implementation(libs.kotlinx.coroutines.core)` in `commonMain`, how does Gradle know which `.jar` or `.klib` to download?

**Answer:** Every KMP library publishes a **Gradle Metadata file** (`.module`) alongside its artifacts. This metadata file declares which platform variants exist:

```json
{
  "variants": [
    { "name": "jvmApiElements", "files": ["kotlinx-coroutines-core-jvm-1.8.0.jar"] },
    { "name": "iosArm64ApiElements", "files": ["kotlinx-coroutines-core-iosarm64-1.8.0.klib"] },
    { "name": "iosSimulatorArm64ApiElements", "files": ["kotlinx-coroutines-core-iossimulatorarm64-1.8.0.klib"] },
    { "name": "iosX64ApiElements", "files": ["kotlinx-coroutines-core-iosx64-1.8.0.klib"] }
  ]
}
```

When Gradle resolves the dependency for `commonMain`:
1. It downloads the `.module` metadata.
2. For each declared target in your project (Android, iosArm64, iosSimulatorArm64, iosX64), it verifies a matching variant exists.
3. If a variant is missing (e.g., the library doesn't publish `iosArm64`), the build fails immediately with: `Could not resolve kotlinx-coroutines-core for target iosArm64`.
4. During compilation, the correct platform-specific artifact is used.

### The `.klib` Format

On the JVM, Kotlin libraries are `.jar` files (Java Archives containing `.class` bytecode).
On Kotlin/Native, libraries are `.klib` files (Kotlin Libraries containing serialized IR). The `.klib` is not machine code — it is an intermediate format that the LLVM backend converts to native ARM64/x86_64 during the final link phase.

```text
JVM:    .kt  →  [Kotlin/JVM compiler]  →  .class  →  packaged into .jar
Native: .kt  →  [Kotlin/Native compiler] → .klib IR → [LLVM] → .o → linked into .framework
```

---

## Version Catalogs (`libs.versions.toml`)

A Staff-level KMP project uses Gradle Version Catalogs to centralize all dependency versions. The catalog must handle both shared and platform-specific libraries.

```toml
# gradle/libs.versions.toml

[versions]
kotlin = "2.0.20"
coroutines = "1.8.1"
ktor = "2.3.12"
sqldelight = "2.0.2"
koin = "3.5.6"
skie = "0.9.0"
compose-multiplatform = "1.6.11"

[libraries]
kotlinx-coroutines-core = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-core", version.ref = "coroutines" }
kotlinx-coroutines-test = { module = "org.jetbrains.kotlinx:kotlinx-coroutines-test", version.ref = "coroutines" }
kotlinx-serialization-json = { module = "org.jetbrains.kotlinx:kotlinx-serialization-json", version = "1.7.1" }
kotlinx-datetime = { module = "org.jetbrains.kotlinx:kotlinx-datetime", version = "0.6.0" }

# Ktor
ktor-client-core = { module = "io.ktor:ktor-client-core", version.ref = "ktor" }
ktor-client-okhttp = { module = "io.ktor:ktor-client-okhttp", version.ref = "ktor" }
ktor-client-darwin = { module = "io.ktor:ktor-client-darwin", version.ref = "ktor" }
ktor-client-content-negotiation = { module = "io.ktor:ktor-client-content-negotiation", version.ref = "ktor" }
ktor-serialization-kotlinx-json = { module = "io.ktor:ktor-serialization-kotlinx-json", version.ref = "ktor" }

# SQLDelight
sqldelight-android-driver = { module = "app.cash.sqldelight:android-driver", version.ref = "sqldelight" }
sqldelight-native-driver = { module = "app.cash.sqldelight:native-driver", version.ref = "sqldelight" }

# DI
koin-core = { module = "io.insert-koin:koin-core", version.ref = "koin" }
koin-android = { module = "io.insert-koin:koin-android", version.ref = "koin" }

# Testing
kotlin-test = { module = "org.jetbrains.kotlin:kotlin-test", version.ref = "kotlin" }

[plugins]
kotlinMultiplatform = { id = "org.jetbrains.kotlin.multiplatform", version.ref = "kotlin" }
androidLibrary = { id = "com.android.library", version = "8.5.0" }
kotlinSerialization = { id = "org.jetbrains.kotlin.plugin.serialization", version.ref = "kotlin" }
sqldelight = { id = "app.cash.sqldelight", version.ref = "sqldelight" }
```

---

## The `iosMain` Intermediate Source Set (Apple Silicon Deep Dive)

### The Historical Problem

Before the KMP plugin introduced automatic intermediate source sets, every iOS target was isolated:

```text
OLD (Pre-2023):
  commonMain
       ├── iosX64Main        (Intel simulator)
       ├── iosArm64Main      (Physical device)
       └── iosSimulatorArm64Main  (Apple Silicon simulator)
```

If you wrote a Kotlin file in `iosArm64Main` to wrap `NSDate`, you had to **copy** that exact same file into `iosX64Main` and `iosSimulatorArm64Main`. Three copies of the same code. Every change = three files to update.

### The Modern Solution

The KMP plugin now automatically creates `iosMain` as a shared parent:

```text
MODERN (Kotlin 1.9+):
  commonMain
       └── iosMain           (shared iOS code — write once)
             ├── iosX64Main
             ├── iosArm64Main
             └── iosSimulatorArm64Main
```

You write all iOS-specific code in `iosMain`. The leaf source sets (`iosX64Main`, `iosArm64Main`, `iosSimulatorArm64Main`) are almost always empty — they exist only for the rare case where you need architecture-specific behavior (e.g., different SIMD optimizations for x86 vs ARM64).

### Why iosArm64 ≠ iosSimulatorArm64

Both are ARM64 instruction sets. Why are they separate?

**The Simulator is not a real iOS device.** It runs as a macOS process in a sandboxed environment. The system libraries are macOS libraries (compiled for the simulator), not real iOS libraries. The ABI (Application Binary Interface), dynamic linker paths, and available system calls differ:

| | Physical Device (iosArm64) | Simulator on Apple Silicon (iosSimulatorArm64) |
|---|---|---|
| CPU Architecture | ARM64 | ARM64 |
| OS | iOS | macOS (simulated iOS) |
| System Libraries | iOS SDK dylibs | Simulator SDK dylibs |
| Available APIs | All hardware APIs | No GPS, no NFC, no Bluetooth |
| ABI | Mach-O for iOS | Mach-O for simulator |
| Code Signing | Required (provisioning profile) | Not required |

If you tried to link a binary compiled for `iosArm64` into the simulator, it would crash immediately because the dynamic linker can't find the iOS system libraries on the macOS filesystem.

---

## The `binaries.framework` Block

The `framework` block controls how the final iOS Framework is produced.

```kotlin
iosTarget.binaries.framework {
    baseName = "SharedCode"         // Name of the .framework directory
    isStatic = true                 // Static vs Dynamic linking
    
    // Transitivity: make sub-module types visible to Swift
    export(project(":core:core-model"))
    
    // Compiler flags for LLVM optimization
    freeCompilerArgs += listOf(
        "-Xallocator=mimalloc",    // Use mimalloc allocator (faster than default)
        "-opt-in=kotlinx.cinterop.ExperimentalForeignApi"
    )
}
```

### Static vs Dynamic Linking

| | `isStatic = true` | `isStatic = false` |
|---|---|---|
| **Output** | `.a` static archive inside `.framework` | `.dylib` inside `.framework` |
| **App launch time** | Faster (everything pre-linked at build time) | Slower (dynamic linker resolves at runtime) |
| **Binary size** | Slightly larger (dead code not stripped by dyld) | Slightly smaller |
| **Framework embedding** | No embedding required | Must embed in Xcode "Frameworks" |
| **Apple recommendation** | ✅ Preferred for small frameworks | For very large shared libs |

**Staff Rule:** Use `isStatic = true` for KMP frameworks unless your framework exceeds ~50MB, at which point dynamic linking allows the OS to lazy-load sections.

### The `export()` Function

By default, only types *directly* declared in the shared module are visible in the generated Objective-C header. If your shared module depends on `core-model` (which defines `data class User`), and your ViewModel returns a `StateFlow<User>`, Swift won't be able to access `User`'s properties unless you `export(project(":core:core-model"))`.

Without export:
```swift
let user = viewModel.state.value  // Type: KotlinBase (opaque!)
// user.name → COMPILE ERROR: no member 'name'
```

With export:
```swift
let user = viewModel.state.value  // Type: User
print(user.name)  // ✅ Works
```

---

## Gradle Convention Plugins for KMP

In a multi-module KMP project, you do not want to copy the 80-line `build.gradle.kts` configuration into every module. You write a Gradle Convention Plugin.

```kotlin
// build-logic/convention/src/main/kotlin/KmpLibraryConventionPlugin.kt

class KmpLibraryConventionPlugin : Plugin<Project> {
    override fun apply(target: Project) = with(target) {
        with(pluginManager) {
            apply("org.jetbrains.kotlin.multiplatform")
            apply("com.android.library")
        }

        extensions.configure<KotlinMultiplatformExtension> {
            androidTarget {
                compilations.all {
                    kotlinOptions { jvmTarget = "17" }
                }
            }

            listOf(iosX64(), iosArm64(), iosSimulatorArm64()).forEach {
                it.binaries.framework {
                    baseName = project.name
                    isStatic = true
                }
            }

            sourceSets {
                commonMain.dependencies {
                    implementation(libs.findLibrary("kotlinx.coroutines.core").get())
                }
                commonTest.dependencies {
                    implementation(libs.findLibrary("kotlin.test").get())
                }
            }
        }

        extensions.configure<LibraryExtension> {
            namespace = "com.example.${project.name.replace("-", ".")}"
            compileSdk = 34
            defaultConfig { minSdk = 26 }
        }
    }
}
```

Now, every feature module's `build.gradle.kts` is just:

```kotlin
plugins {
    id("kmp-library-convention")
}

kotlin {
    sourceSets {
        commonMain.dependencies {
            implementation(project(":core:core-network"))
        }
    }
}
```

---

## Common Pitfalls

### 1. The "Unresolved reference" IDE Phantom
Android Studio sometimes shows red squiggles in `commonMain` files even when the code compiles fine from CLI. This happens because the IDE defaults to resolving against the Android target, and certain Kotlin/Native APIs (`platform.Foundation.*`) are only visible when the IDE switches to the iOS source set context.

**Fix:** In Android Studio, use the source set switcher in the bottom toolbar to switch between `commonMain [android]` and `commonMain [iosArm64]`.

### 2. The Missing `android` Block
If you declare `androidTarget()` in the `kotlin` block but forget the `android { ... }` block at the bottom of the file, you'll get a cryptic error: `Android Gradle plugin requires compileSdk to be set`. The KMP plugin does not automatically configure the Android block.

### 3. Dependency Conflicts Between Targets
If `androidMain` uses OkHttp 4.12.0 and `commonMain` pulls in a transitive Ktor dependency that wants OkHttp 4.11.0, Gradle will resolve this conflict *only* for the Android target. The iOS target doesn't use OkHttp at all. But your lockfile may show confusing version mismatches.

**Fix:** Use `./gradlew :shared:dependencies --configuration commonMainApi` to inspect the resolved dependency graph per source set.

---

## Probing Questions

1.  **Source Set Resolution:** You add `implementation("com.squareup.okhttp3:okhttp:4.12.0")` to `commonMain.dependencies`. What error do you get, and why? How does Gradle's metadata resolution determine that OkHttp is JVM-only?
2.  **Static vs Dynamic:** Your KMP shared framework is 8MB. Apple requires apps under 200MB over cellular. Should you use static or dynamic linking? What changes if the framework grows to 60MB?
3.  **The iosSimulatorArm64 Question:** A junior developer removes `iosSimulatorArm64()` from the target list because "it's the same architecture as iosArm64." The project compiles, but the simulator crashes on launch. Explain exactly what went wrong at the linker level.
4.  **Convention Plugin Design:** You have 12 KMP feature modules. Five of them also use SQLDelight. How do you design your convention plugin hierarchy to avoid applying the SQLDelight plugin to all 12 modules?
5.  **The `export()` Problem:** Your `shared` module depends on `core-model` and `core-network`. You forget to `export(project(":core-model"))`. What exact symptom does the iOS team see in Xcode, and how do they report the bug to you?

## Further Reading

- [`overview-and-k1-vs-k2.md`](../foundations/overview-and-k1-vs-k2.md) — The K2 compiler that processes this Gradle configuration.
- [`ios-distribution.md`](ios-distribution.md) — How the `framework {}` block output is consumed by Xcode via SPM or CocoaPods.
- [`../../build-tooling/convention-plugins.md`](../../build-tooling/convention-plugins.md) — The Android convention plugin patterns that extend to KMP.
- [`../../build-tooling/gradle-and-build-systems.md`](../../build-tooling/gradle-and-build-systems.md) — Deep dive into Gradle's task graph and configuration avoidance.
