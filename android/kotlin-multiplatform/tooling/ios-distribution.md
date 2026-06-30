# iOS Distribution: How Xcode Consumes Kotlin

> Kotlin/Native compiles your shared code to ARM64 machine code, packages it inside an Apple Framework, and generates an Objective-C header that bridges the Kotlin types to Swift. Understanding the entire pipeline — from `./gradlew assembleXCFramework` to the moment Swift calls `import SharedCode` — is essential for a Staff engineer managing cross-platform teams.

---

## Overview

When the Kotlin/Native compiler finishes processing your `commonMain` + `iosMain` code, it produces:
1. **Object files** (`.o`) — compiled ARM64 machine code for every Kotlin function.
2. **An Objective-C header** (`.h`) — type declarations that map Kotlin classes to Objective-C classes (which Swift can import).
3. **A module map** — tells Xcode how to import the framework as a Swift module.

These are packaged into an **Apple Framework** — a structured directory that Xcode understands natively.

---

## The `.framework` vs `.xcframework` Distinction

### The Problem with `.framework`

A single `.framework` contains a binary compiled for exactly **one** target architecture + platform combination:

```text
SharedCode.framework/              ← This is for iosArm64 ONLY
 ├── Headers/
 │    └── SharedCode.h             ← Objective-C header
 ├── Modules/
 │    └── module.modulemap         ← Swift module map
 ├── SharedCode                    ← ARM64 binary (static archive or dylib)
 └── Info.plist
```

If you hand this framework to an iOS engineer and they try to run the app on the Simulator (which needs `iosSimulatorArm64`), it will crash immediately:

```
ld: building for 'iOS-simulator', but linking in object file built for 'iOS'
```

### The Solution: `.xcframework`

An XCFramework is Apple's official multi-architecture wrapper. It bundles multiple `.framework` directories:

```text
SharedCode.xcframework/
 ├── Info.plist                                ← Describes all contained platforms
 ├── ios-arm64/                                ← Physical devices
 │    └── SharedCode.framework/
 │         ├── Headers/SharedCode.h
 │         └── SharedCode (ARM64 binary)
 ├── ios-arm64_x86_64-simulator/              ← Simulators (both architectures)
 │    └── SharedCode.framework/
 │         ├── Headers/SharedCode.h
 │         └── SharedCode (fat binary: ARM64 + x86_64)
 └── macos-arm64_x86_64/                      ← macOS (if targeting desktop)
      └── SharedCode.framework/
```

When Xcode builds the app, it reads the `Info.plist`, determines the active build destination (physical device vs simulator), and automatically selects the correct inner `.framework`.

### Generating the XCFramework

```kotlin
// In build.gradle.kts
kotlin {
    listOf(iosX64(), iosArm64(), iosSimulatorArm64()).forEach {
        it.binaries.framework {
            baseName = "SharedCode"
            isStatic = true
        }
    }
}
```

Then run:
```bash
./gradlew :shared:assembleSharedCodeXCFramework
```

This generates `build/XCFrameworks/release/SharedCode.xcframework/` containing all three architectures.

---

## The Three Distribution Methods (In Depth)

### Method A: CocoaPods Plugin

**How it works:** JetBrains provides a `kotlin("native.cocoapods")` Gradle plugin. It generates a `.podspec` file alongside the framework binaries. The iOS app's `Podfile` references the shared module as a local pod.

```kotlin
// shared/build.gradle.kts
kotlin {
    cocoapods {
        summary = "Shared KMP module"
        homepage = "https://example.com"
        version = "1.0"
        ios.deploymentTarget = "15.0"
        
        framework {
            baseName = "SharedCode"
            isStatic = true
        }
    }
}
```

```ruby
# iosApp/Podfile
target 'iosApp' do
  use_frameworks!
  pod 'SharedCode', :path => '../shared'
end
```

**The CocoaPods Build Flow:**

```text
iOS engineer runs: pod install
  └── CocoaPods reads the .podspec
       └── .podspec points to a Gradle build script
            └── Xcode's "Build Phases" gains a Run Script phase
                 └── Run Script executes: ./gradlew :shared:syncFramework
                      └── Kotlin/Native compiles → produces .framework
                           └── CocoaPods copies .framework into Pods/
```

**Why CocoaPods is problematic:**
1. **Build time coupling:** Every time the iOS engineer hits CMD+R in Xcode, the Gradle daemon boots and recompiles the Kotlin code. On a cold build, this adds 30-90 seconds.
2. **JDK requirement:** Every iOS team member must install the JDK, Gradle, and often Android Studio to resolve build issues.
3. **CocoaPods deprecation:** Apple stopped investing in CocoaPods years ago. The community has moved to SPM. Major libraries (Firebase, Alamofire) now recommend SPM.
4. **Flaky integration:** The Gradle ↔ CocoaPods bridge breaks on Xcode version updates with alarming regularity.

### Method B: Swift Package Manager (SPM)

**The Architecture:**
Unlike CocoaPods, SPM consumes *pre-built* binaries. The iOS team never runs Gradle. The flow is:

```text
CI Server (macOS):
  ./gradlew :shared:assembleXCFramework
  → Zip the .xcframework
  → Upload to GitHub Releases / S3 / Artifactory
  → Update Package.swift with new URL + SHA256 checksum
  → Commit and push Package.swift

iOS Engineer's Xcode:
  File → Add Package Dependency → Enter the Package.swift repo URL
  → SPM downloads the .xcframework.zip
  → SPM verifies the SHA256 checksum
  → SPM unpacks and links the framework
  → import SharedCode   ← Just works!
```

**The `Package.swift` file:**

```swift
// swift-tools-version: 5.9

import PackageDescription

let package = Package(
    name: "SharedCode",
    platforms: [.iOS(.v15)],
    products: [
        .library(
            name: "SharedCode",
            targets: ["SharedCode"]
        ),
    ],
    targets: [
        .binaryTarget(
            name: "SharedCode",
            url: "https://github.com/your-org/shared-kmp/releases/download/v1.2.3/SharedCode.xcframework.zip",
            checksum: "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"
        ),
    ]
)
```

**Why SPM is the Staff recommendation:**
1. **Zero Gradle knowledge required for iOS.** They paste a URL in Xcode. Done.
2. **Incremental downloads.** SPM caches the framework. It only re-downloads when the checksum changes.
3. **Native to Xcode.** No third-party tooling (CocoaPods is Ruby-based and frequently breaks).
4. **Deterministic builds.** The SHA256 checksum guarantees the iOS team gets the exact binary that CI produced.

**The KMMBridge Automation:**
Writing the CI script to zip, upload, compute checksums, and update `Package.swift` is tedious. **KMMBridge** (by Touchlab) is a Gradle plugin that automates the entire pipeline:

```kotlin
// shared/build.gradle.kts
plugins {
    id("co.touchlab.kmmbridge") version "0.6.1"
}

kmmbridge {
    mavenPublishArtifacts()  // or githubReleaseArtifacts()
    spm()
}
```

With this, `./gradlew kmmBridgePublish` handles everything — XCFramework generation, SPM `Package.swift` update, and artifact upload.

### Method C: Direct Xcode Integration (Monorepo)

**When to use:** When Android and iOS live in the same Git repository and you want the iOS team to always have the absolute latest Kotlin code without waiting for a CI publish cycle.

**Setup:** You add a "Run Script" Build Phase to the Xcode project:

```bash
# Xcode Build Phase → Run Script
cd "$SRCROOT/.."
./gradlew :shared:embedAndSignAppleFrameworkForXcode \
    -Pkotlin.native.cocoapods.platform=$PLATFORM_NAME \
    -Pkotlin.native.cocoapods.archs="$ARCHS" \
    -Pkotlin.native.cocoapods.configuration="$CONFIGURATION"
```

**Pros:**
- The iOS engineer hits CMD+R and gets the latest Kotlin code compiled and linked.
- Perfect for debugging — Xcode can step through Kotlin code (with the LLDB plugin).
- No artifact hosting infrastructure required.

**Cons:**
- Every Xcode build triggers a Gradle invocation (~15-30s overhead even for incremental builds).
- iOS team must install JDK 17+ and Gradle.
- The Xcode "clean build" takes 2-3 minutes instead of 30 seconds.
- IDE fighting: two build systems (Gradle + Xcode) running simultaneously, competing for CPU and disk I/O.

### Distribution Method Decision Matrix

| Factor | CocoaPods | SPM | Direct Xcode |
|---|---|---|---|
| **iOS team needs JDK?** | Yes | No | Yes |
| **Build time impact on iOS** | High (Gradle runs on every build) | None (pre-built binary) | High |
| **CI infrastructure required?** | Minimal | Yes (macOS runner, artifact hosting) | None |
| **Debugging Kotlin from Xcode** | Possible (breakpoints) | Not possible (pre-built) | Best (full source-level) |
| **Ideal for** | Legacy teams already on CocoaPods | Production teams, polyrepo | Monorepo, early development |
| **Apple ecosystem alignment** | ❌ Deprecated | ✅ Native | ⚠️ Non-standard |

---

## The Generated Objective-C Header (Deep Dive)

When Kotlin/Native produces the framework, it generates a `.h` file that maps every public Kotlin declaration to Objective-C. Understanding this mapping is critical for debugging "why does my Swift code see a weird type?"

### Mapping Rules

| Kotlin | Objective-C | Swift (bridged) |
|---|---|---|
| `class User` | `@interface SharedCodeUser : SharedCodeBase` | `class User : KotlinBase` |
| `data class User` | Same as `class` (no special treatment) | Same — `.copy()` exists but is ugly |
| `sealed class Result` | `@interface SharedCodeResult : SharedCodeBase` | Regular class (no exhaustive switch!) |
| `enum class Color` | `SharedCodeColor` (each entry is a `companion` property) | Accessible but not a Swift enum |
| `interface Repository` | `@protocol SharedCodeRepository` | Swift protocol |
| `suspend fun fetch()` | Completion handler pattern | `async throws` function |
| `fun process(x: Int = 5)` | `- (void)processX:(int32_t)x` (default LOST) | Must pass `x` explicitly |
| `String` | `NSString *` | `String` |
| `Int` | `int32_t` | `Int32` (not `Int`!) |
| `Long` | `int64_t` | `Int64` |
| `Boolean` | `BOOL` | `Bool` |
| `List<String>` | `NSArray<NSString *> *` | `[String]` |
| `Map<String, Int>` | `NSDictionary<NSString *, SharedCodeInt *> *` | Ugly generic dictionary |
| `Unit` (return type) | `void` | `Void` |
| `Nothing` | Not representable | Not representable |
| `Throwable` | `NSError *` | `Error` |

### The `@ObjCName` Annotation

By default, every Kotlin class gets prefixed with the module name in Objective-C. `class User` becomes `SharedCodeUser` in Swift. This is ugly.

```kotlin
@ObjCName("User")  // Override the generated Objective-C name
class User(val name: String)
```

Now Swift sees `User` directly, not `SharedCodeUser`.

---

## Probing Questions

1.  **XCFramework Internals:** Explain the directory structure of a `.xcframework` and why it contains separate directories for `ios-arm64` and `ios-arm64_x86_64-simulator`. Why can't they share a single ARM64 binary?
2.  **SPM Checksum:** If your CI pipeline uploads a new `.xcframework.zip` but forgets to update the SHA256 checksum in `Package.swift`, what exact error does the iOS engineer see in Xcode? Why is this security measure important?
3.  **Distribution Decision:** Your team has 8 Android engineers and 3 iOS engineers. The iOS team is hostile to installing the JDK. You're in a polyrepo setup. Which distribution method do you choose, and why do the other two fail?
4.  **Header Generation:** Your Kotlin code defines `sealed class NetworkResult { data class Success(...) : NetworkResult(); data class Error(...) : NetworkResult() }`. Without SKIE, what does the generated Objective-C header look like? Why can't Swift do an exhaustive `switch` on it?
5.  **The `export()` Problem:** Your `shared` module depends on `core-model` which defines `data class Product`. Your ViewModel returns `StateFlow<List<Product>>`. You forget to `export(project(":core:core-model"))` in the `framework {}` block. What symptom does the iOS team report, and what does the Objective-C header show instead of `Product`?

## Further Reading

- [`swift-interop.md`](swift-interop.md) — Deep dive into the Objective-C bridge limitations shown in the header mapping table above.
- [`build-system-and-source-sets.md`](build-system-and-source-sets.md) — The `framework {}` block configuration that drives framework generation.
- [`ci-cd-for-kmp.md`](ci-cd-for-kmp.md) — Automating the SPM pipeline (XCFramework → zip → upload → Package.swift update).
- [`overview-and-k1-vs-k2.md`](overview-and-k1-vs-k2.md) — How K2's Direct Swift Export will eventually replace the Objective-C header entirely.
