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
-   **Breadcrumb Tracking:** Funnel user interactions and lifecycle events from both iOS and Android into a shared KMP logger, then use platform adapters to route a bounded, redacted subset into the breadcrumb API of each crash SDK (for example, Crashlytics or Sentry). A shared log sink alone does not attach events to a crash report; the explicit adapters create the interwoven timeline of native UI events and shared business-logic state changes.

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
2. **Serialization:** kotlinx.serialization supplies consumer R8 rules. Add narrow extra rules only for documented cases such as named companion objects or independent reflection; test the optimized release configuration rather than blanket @Keep on every serializable model.
3.  **Meaningful Messages:** Preserve useful exception messages without embedding PII.

---

## 5. The iOS Crash Path (dSYMs and Kotlin/Native)

iOS observability is the hardest aspect of KMP. Without strict configuration, an unhandled Kotlin exception on iOS will crash the app, and the stack trace will show a useless `konan::abort()` or opaque memory addresses.

### Apple dSYMs and UUID Matching
For crash tools to map memory addresses back to your Kotlin source code, they need the **dSYM (Debug Symbol)** file.
1. Inspect the selected Kotlin/Native linkage and debug-info configuration; a separately loaded dynamic framework and statically linked code do not necessarily produce the same symbol packaging.
2.  **UUID Matching:** The generated binary and the dSYM share a unique UUID. **If the UUIDs do not match perfectly, symbolication fails.**
3. Preserve and upload symbols for the binaries actually loaded in the release. Dynamic framework images need matching framework symbols; statically linked code may be represented in the final app binary's debug information. Inspect archive contents, linkage and UUIDs rather than requiring a separate framework dSYM for every XCFramework.

### Kotlin/Native Crash Bridges
By default, standard iOS crash reporters (which attach to Objective-C/Swift exception handlers) cannot cleanly catch Kotlin/Native unhandled exceptions before the process aborts.

To fix this, you must use a crash bridge (such as the widely standard **CrashKiOS** by Touchlab, or native integrations if your observability vendor supports Kotlin/Native directly). These bridges hook into the Kotlin/Native unhandled exception hook (`setUnhandledExceptionHook`) and cleanly pass the Kotlin stack trace to the iOS crash reporter before termination.

---

## 6. Flow, Cancellation, and Swift-Facing Errors

Concurrency failures behave differently across platforms.

### Cancellation is Not a Crash
A coroutine cancelled by its parent (e.g., a ViewModel clearing) throws a `CancellationException`.
*   **Android:** The JVM treats this as a normal lifecycle event. It is swallowed by the coroutine machinery.
* **iOS:** A bridge such as SKIE propagates cancellation between Swift async and Kotlin suspend and can surface CancellationError. Plain Objective-C callback export with Swift async syntax does not by itself establish that cancellation propagation.

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

Use explicit domain failures for a controlled error contract. Plain Objective-C export does not make Kotlin sealed classes exhaustive Swift enums; use a documented wrapper such as SKIE onEnum(of:) or the selected export path's actual generated API. Test cancellation and application errors separately.

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
2. Are debug symbols retained for the actual app/framework images and verified against the release UUIDs and linkage?
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

1. Verify symbols against the actual loaded images, linkage and release UUIDs; missing separate framework symbols is one possible cause, not universal for static linkage. Also inspect whether the Kotlin exception details reach the crash reporter before the native abort signal.
2. The shared code is catching a broad `Exception` (which includes `CancellationException`) and logging it as an error or crash before swallowing it. Coroutine cancellation is a normal lifecycle event; `CancellationException` must always be caught and rethrown (or handled via `suspend` mechanisms) to avoid false-positive error spam and breaking structured concurrency.
3. Generate a stable Correlation ID (like a UUID) in the shared code before the request. Log it locally. Then, inject it into the Ktor HTTP request headers (e.g., using W3C Trace Context `traceparent` or a custom `X-Request-ID`). When the backend logs the 500 error, it must include that header, allowing seamless correlation across the boundary.
4. The shared code should expose a `SharedBuildInfo` struct containing the exact Git SHA and version of the KMP module at compile time. This struct should be attached as a custom key to all crash reports. Inspecting the custom keys of the new crash will immediately reveal if the iOS app bundled the old or new SHA.
5. You must execute a synthetic-crash verification. Build a release iOS app using the new XCFramework distribution, trigger a deliberate exception originating in shared Kotlin code, and check the crash reporting dashboard. If the stack trace correctly symbolicates to the exact Kotlin file and line number, the dSYM mapping and distribution pipeline are intact.

---

## Official Sources and Further Reading

- [Kotlin/Native iOS Crash Symbolication (Touchlab CrashKiOS)](https://github.com/touchlab/CrashKiOS)
- [Apple Documentation: Adding standard dSYMs](https://developer.apple.com/documentation/xcode/building-your-app-to-include-debugging-information)
- [SKIE: Swift Kotlin Interface Enhancer](https://skie.touchlab.co/)
- [Android Developers: R8 and mapping files](https://developer.android.com/tools/retrace)
- [Kotlin Coroutines: Cancellation and Exceptions](https://kotlinlang.org/docs/exception-handling.html)

### Official verification references

- [Primary documentation or owning implementation](https://developer.apple.com/videos/play/wwdc2021/10211/)
- [Primary documentation or owning implementation](https://github.com/Kotlin/kotlinx.serialization/blob/master/README.md)
- [Primary documentation or owning implementation](https://kotlinlang.org/docs/native-objc-interop.html)
- [Primary documentation or owning implementation](https://skie.touchlab.co/features/suspend)
