# KMP Observability and Crash Symbolication

> Shared code compiling on iOS is only half the contract. A production Kotlin Multiplatform rollout is not complete until shared failures can be correlated across boundaries, and both Android and iOS crashes resolve into readable Kotlin source frames in your telemetry tools.

---

## Why This Matters

When a mobile application fails in production, the root cause could be a platform-specific bug, a backend incident, or a defect in shared Kotlin logic. If KMP observability is poor, staff engineers spend days playing ping-pong between Android and iOS teams, trying to prove whose code actually failed.

A strong KMP observability architecture guarantees:

1.  **Attribution:** The exact version of the shared code is attached to every crash and log.
2.  **Correlation:** Trace IDs travel from the user's tap, through the shared module, to the backend, and back.
3.  **Symbolication:** Stack traces on both Android (via R8) and iOS (via dSYMs) resolve back to Kotlin line numbers, avoiding opaque `konan::abort()` native frames.
4.  **Separation:** Expected domain failures (e.g., HTTP 401) are tracked as telemetry, while actual unhandled exceptions are routed to crash reporting.

---

## 1. Version Attribution and Build Identity

Do not assume the host application version maps perfectly to the shared code version, especially if the KMP module is distributed as a binary XCFramework or Maven artifact rather than a monorepo source dependency.

Expose a deterministic build identity from your shared code:

```kotlin
// commonMain
data class SharedBuildInfo(
    val versionName: String,
    val gitSha: String,
    val compilerVersion: String,
    val apiSchemaVersion: Int
)

expect fun getSharedBuildInfo(): SharedBuildInfo
```

Attach this payload to:
-   Crash report custom keys (e.g., Crashlytics keys).
-   Structured analytical events.
-   Support bundles and feedback emails.
-   HTTP `User-Agent` or custom tracing headers.

This immediately answers: *"Is this iOS crash happening because they are running a three-week-old shared binary?"*

---

## 2. Trace Correlation

Distributed failures cross multiple layers:
`Swift UI -> KMP Use Case -> Ktor Engine -> Backend -> KMP Database -> Swift UI`

To debug this effectively, inject and pass stable **Correlation IDs**.

-   **Client Request ID:** Generated at the UI/ViewModel layer before invoking the shared use case.
-   **W3C Trace Context / B3 Headers:** Ensure Ktor passes standard distributed tracing headers (e.g., `traceparent`) to the backend.
-   **Sync/Job ID:** For offline-first sync loops, generate an ID when the loop wakes up and attach it to all logs emitted during that pass.

When an error occurs, log the `Client Request ID` alongside the exception. If a backend request fails, the backend's `Trace ID` must be returned to the client and included in the telemetry event.

---

## 3. Error Taxonomy and Privacy

A shared module must explicitly separate expected domain failures from unexpected crashes.

```kotlin
sealed interface DomainFailure {
    data object Offline : DomainFailure
    data object Unauthorized : DomainFailure
    data class BackendError(val code: Int, val traceId: String) : DomainFailure
    data class SerializationMismatch(val modelName: String) : DomainFailure
}
```

**Rule:** Never throw an exception for a `DomainFailure`. Return it as a `Result<T>` or a sealed type.

**Rule:** Map unexpected conditions (e.g., `IllegalStateException`) to your crash reporter.

### Privacy-Safe Telemetry

Diagnostics must be useful without becoming a data leak. KMP modules operate at the data layer, making them highly susceptible to logging PII (Personally Identifiable Information).

*   **Allowed by default:** App version, feature name, operation ID, error category (e.g., `SerializationMismatch`), network transport type.
*   **Requires privacy review:** Raw URLs with query parameters, request/response bodies, user identifiers, raw database rows.

---

## 4. The Android Crash Path (R8 and Retrace)

On Android, shared Kotlin code runs natively on the JVM/ART. Crashes will surface as standard Java `Throwable` stack traces.

The primary observability risk is **R8 Obfuscation**.
1.  **Mapping Uploads:** Ensure your CI pipeline automatically uploads the R8 `mapping.txt` file to your crash reporting tool (e.g., Firebase Crashlytics) for every release build.
2.  **Serialization:** Ensure Kotlinx Serialization models or classes accessed via reflection are protected by `@Keep` annotations or explicit ProGuard rules, otherwise obfuscation will cause runtime `SerializationException` crashes.
3.  **Meaningful Messages:** Preserve useful exception messages without embedding PII.

---

## 5. The iOS Crash Path (dSYMs and Kotlin/Native)

iOS observability is the hardest aspect of KMP. Without strict configuration, an unhandled Kotlin exception on iOS will crash the app, and the stack trace will show a useless `konan::abort()` or opaque memory addresses.

### Apple dSYMs and UUID Matching
For crash tools to map memory addresses back to your Kotlin source code, they need the **dSYM (Debug Symbol)** file.
1.  When Kotlin/Native compiles the Apple framework, it generates a `.dSYM` bundle.
2.  **UUID Matching:** The generated binary and the dSYM share a unique UUID. **If the UUIDs do not match perfectly, symbolication fails.**
3.  If you distribute the KMP module as an XCFramework, the host iOS app's build process *must* preserve and upload the shared framework's dSYMs to the crash reporter alongside the app's own dSYMs.

### Kotlin/Native Crash Bridges
By default, standard iOS crash reporters (which attach to Objective-C/Swift exception handlers) cannot cleanly catch Kotlin/Native unhandled exceptions before the process aborts.

To fix this, you must use a crash bridge (such as the widely standard **CrashKiOS** by Touchlab, or native integrations if your observability vendor supports Kotlin/Native directly). These bridges hook into the Kotlin/Native unhandled exception hook (`setUnhandledExceptionHook`) and cleanly pass the Kotlin stack trace to the iOS crash reporter before termination.

---

## 6. Flow, Cancellation, and Swift-Facing Errors

Concurrency failures behave differently across platforms.

### Cancellation is Not a Crash
A coroutine cancelled by its parent (e.g., a ViewModel clearing) throws a `CancellationException`.
*   **Android:** The JVM treats this as a normal lifecycle event. It is swallowed by the coroutine machinery.
*   **iOS:** If an `async` Swift function bridged to a Kotlin `suspend` function is cancelled, Swift receives a `CancellationError`.

**Rule:** Never blindly catch `Exception` or `Throwable` in shared code and report it to your crash tracker without rethrowing `CancellationException`. Doing so will flood your telemetry with false-positive crashes every time a user navigates away from a loading screen.

```kotlin
// WRONG
try {
    api.fetch()
} catch (e: Exception) {
    logger.error("Fetch failed", e) // False positives on cancellation!
}

// RIGHT
try {
    api.fetch()
} catch (e: CancellationException) {
    throw e // Let structured concurrency handle it
} catch (e: Exception) {
    logger.error("Fetch failed", e)
}
```

### Projecting Errors to Swift
When a `suspend` function fails, the `@Throws(ExceptionClass::class)` annotation converts only the explicitly listed exception classes (and their subclasses) into Swift `Error`s that can be caught with `do/catch`. Undeclared Kotlin exceptions can still terminate the iOS process.

For `Flow` and async functions, relying heavily on unchecked exceptions across the boundary is risky. While tools like **SKIE** supply sealed wrappers and async/Flow conveniences, they do not automatically convert arbitrary Kotlin exception hierarchies into typed Swift `Error` enums. Instead of exceptions, prefer returning explicit `Result<T>` or a sealed `DomainFailure` class so iOS engineers can write exhaustive `switch` statements over shared domain errors safely without risking an uncatchable crash.

---

## 7. Synthetic-Crash Verification

You cannot assume symbolication works just because a CI script passed. Toolchain updates, Xcode version bumps, or Gradle plugin changes routinely break dSYM packaging.

**The Release Gate:**
Before merging a major architecture change or bumping KMP versions, add a hidden developer menu button that throws a synthetic exception in shared Kotlin code:
```kotlin
fun forceSharedCrash() {
    throw IllegalStateException("Synthetic KMP crash for symbolication testing")
}
```
1.  Deploy a release-type build to Android and iOS devices.
2.  Trigger the crash.
3.  Verify in your production crash dashboard that the exact file name and line number in `commonMain` are visible for both platforms.

---

## Review Checklist

1.  Is a deterministic shared build SHA attached to crash events on both platforms?
2.  Are iOS dSYMs for the shared framework definitively extracted and uploaded to the crash reporter?
3.  Is a Kotlin/Native crash bridge (like CrashKiOS) configured to prevent `konan::abort()` blind spots?
4.  Do shared logs safely omit PII while retaining stable correlation IDs?
5.  Are coroutine cancellations explicitly ignored by error reporting?
6.  Has a synthetic crash been verified end-to-end on a release build for both platforms?

---

## Probing Questions

1. **iOS Blind Spots:** An iOS app using your KMP framework crashes frequently, but the crash reporter only shows `konan::abort()` at the top of the stack trace. What two missing configurations are likely causing this?
2. **Cancellation Noise:** Your telemetry dashboard is suddenly flooded with thousands of "crashes" from a shared network repository, but users are not reporting app terminations. What coroutine concept was likely mishandled?
3. **Trace Continuity:** A user taps "Checkout" on iOS, the shared KMP module makes a Ktor request, and the backend returns a 500 error. How should you instrument the shared code so the backend team can find the exact request in their logs?
4. **Build Attribution:** A bug in a shared Kotlin formatting function was fixed last week. The iOS team claims they released the fix, but the crash is still occurring in production. How can observability definitively prove whether the iOS app was built with the fixed KMP binary?
5. **Release Verification:** Your team just migrated from Cocoapods to XCFrameworks for KMP distribution. How do you definitively prove that iOS crash observability wasn't broken by the migration?

## Answer Key

1. First, the Apple dSYM files for the KMP framework are likely not being uploaded to the crash reporter, preventing memory addresses from mapping to source files. Second, the app lacks a Kotlin/Native unhandled exception hook bridge (like CrashKiOS), meaning the crash reporter is catching the native abort signal rather than the underlying Kotlin exception string and stack trace.
2. The shared code is catching a broad `Exception` (which includes `CancellationException`) and logging it as an error or crash before swallowing it. Coroutine cancellation is a normal lifecycle event; `CancellationException` must always be caught and rethrown (or handled via `suspend` mechanisms) to avoid false-positive error spam and breaking structured concurrency.
3. Generate a stable Correlation ID (like a UUID) in the shared code before the request. Log it locally. Then, inject it into the Ktor HTTP request headers (e.g., using W3C Trace Context `traceparent` or a custom `X-Request-ID`). When the backend logs the 500 error, it must include that header, allowing seamless correlation across the boundary.
4. The shared code should expose a `SharedBuildInfo` struct containing the exact Git SHA and version of the KMP module at compile time. This struct should be attached as a custom key to all crash reports. Inspecting the custom keys of the new crash will immediately reveal if the iOS app bundled the old or new SHA.
5. You must execute a synthetic-crash verification. Build a release iOS app using the new XCFramework distribution, trigger a deliberate exception originating in shared Kotlin code, and check the crash reporting dashboard. If the stack trace correctly symbolicates to the exact Kotlin file and line number, the dSYM mapping and distribution pipeline are intact.

---

## Official Sources and Further Reading

- [Kotlin/Native iOS Crash Symbolication (Touchlab CrashKiOS)](https://github.com/touchlab/CrashKiOS)
- [Apple Documentation: Adding standard dSYMs](https://developer.apple.com/documentation/xcode/building-your-app-to-include-debugging-information)
- [SKIE: Swift Kotlin Interface Enhancer](https://skie.touchlab.co/)
- [Android Developers: R8 and mapping files](https://developer.android.com/studio/build/shrink-code#decode-stack-trace)
- [Kotlin Coroutines: Cancellation and Exceptions](https://kotlinlang.org/docs/exception-handling.html)
