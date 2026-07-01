# KMP Observability and Crash Symbolication

## Overview

KMP production readiness is not only "the shared code compiles on iOS." It must be observable and debuggable when it fails in the hands of real users.

Shared code can crash on Android, crash on iOS through Kotlin/Native, throw errors across Swift interop, or create behavioral defects that look platform-specific. Staff engineers design the observability path before the rollout.

## Observability Goals

For every shared module, you should know:

- Which app version and shared module version is running.
- Which platform target failed.
- Which shared feature path was active.
- Whether the failure originated in shared Kotlin, platform adapter, backend, or interop.
- Whether symbolication/deobfuscation can resolve stack traces.
- Whether logs/traces preserve correlation IDs across platforms.

## Version Attribution

Expose a shared build identity.

```kotlin
data class SharedBuildInfo(
    val versionName: String,
    val gitSha: String,
    val schemaVersion: Int,
    val apiSurfaceVersion: String
)
```

Attach it to:

- Crash reports.
- Structured logs.
- Analytics diagnostics.
- Support bundles.
- Sync metadata when relevant.

This prevents "Android is on shared code v12 but iOS is on v10" confusion.

## Error Taxonomy

Shared code should report domain failures separately from crashes.

```kotlin
sealed interface SharedFailure {
    data object Offline : SharedFailure
    data object Unauthorized : SharedFailure
    data class Backend(val code: Int) : SharedFailure
    data class Serialization(val schema: String) : SharedFailure
    data class Unexpected(val category: String) : SharedFailure
}
```

Map unexpected exceptions to crash reporting. Map expected failures to state and telemetry.

## Android Crash Path

Android shared Kotlin code is usually visible in JVM stack traces after R8 mapping is uploaded.

Checklist:

- Upload R8/ProGuard mapping files for every release.
- Keep module names and package names meaningful.
- Preserve useful exception messages without PII.
- Add custom keys for shared module version and feature path.
- Keep obfuscation rules for serialized models and reflection-based libraries.

## iOS Crash Path

Kotlin/Native crashes and Swift interop failures need symbolication support.

Production checklist:

- Archive dSYMs for every iOS build containing the shared framework.
- Upload dSYMs to crash tooling.
- Preserve the exact shared framework build artifact for release analysis.
- Record Kotlin compiler version and shared module git SHA.
- Test a synthetic crash from shared code in an internal build and confirm symbolication.

Without this, iOS crash reports can collapse into opaque native frames.

## Structured Logging

Use a shared logging facade with platform implementations.

```kotlin
interface SharedLogger {
    fun event(name: String, attributes: Map<String, String> = emptyMap())
    fun warn(name: String, attributes: Map<String, String> = emptyMap())
    fun error(name: String, throwable: Throwable, attributes: Map<String, String> = emptyMap())
}
```

Shared code emits stable event names. Platforms decide where logs go.

Rules:

- No tokens, emails, full URLs, or raw payloads.
- Use stable keys.
- Include feature path and operation ID.
- Sample high-volume logs.
- Keep user-facing failures separate from debug logs.

## Trace Correlation

Distributed mobile failures cross layers:

```text
tap -> shared use case -> platform network engine -> backend -> local cache -> UI state
```

Use correlation IDs:

- Client request ID for writes.
- Sync operation ID.
- Trace ID from backend when available.
- Outbox operation ID.

Attach these IDs to logs and crash breadcrumbs on both Android and iOS.

## Flow and Coroutine Observability

For shared Flow APIs:

- Log subscription start/stop only for important streams.
- Track cancellation separately from failure.
- Surface collection errors to Swift callers clearly.
- Avoid infinite silent retries.
- Add timeout and retry metrics by operation.

Swift `AsyncSequence` collection should catch cancellation and errors explicitly.

```swift
Task {
    do {
        for try await state in viewModel.state.asAsyncSequence() {
            render(state)
        }
    } catch is CancellationError {
        // Normal lifecycle cancellation.
    } catch {
        crashReporter.record(error)
    }
}
```

## Privacy and Support Bundles

Diagnostics must be useful without becoming a data leak.

Allowed by default:

- App version.
- Shared module version.
- Platform target.
- Feature name.
- Operation ID.
- Error category.
- Network capability summary.

Requires privacy review:

- URLs with query parameters.
- Request/response bodies.
- User identifiers.
- Location.
- Device identifiers.
- Raw database rows.

## Rollout Gates

Before enabling a shared module broadly:

- Synthetic Android crash deobfuscates.
- Synthetic iOS crash symbolicates.
- Shared version appears in crash tools.
- Expected domain failures appear as non-fatal telemetry, not crashes.
- Swift collection errors are handled.
- Logs include operation IDs.
- Support team has a diagnostic runbook.

## Staff Engineer Review Checklist

- Is shared build identity attached to crash/log events?
- Are Android R8 mappings and iOS dSYMs uploaded?
- Has symbolication been tested with synthetic crashes?
- Are expected failures modeled separately from crashes?
- Are shared logs privacy-safe and stable?
- Are correlation IDs propagated across platform and backend?
- Are coroutine cancellations not reported as crashes?
- Are Flow/AsyncSequence errors handled on Swift side?
- Is observability included in rollout gates?
- Is ownership clear when a shared module fails in one platform app?

## Further Reading

- [`tooling/ios-distribution.md`](tooling/ios-distribution.md) - framework packaging and release artifacts.
- [`tooling/swift-interop.md`](tooling/swift-interop.md) - Swift collection and interop behavior.
- [`production/ci-cd-for-kmp.md`](production/ci-cd-for-kmp.md) - KMP CI/CD.
- [`../observability/crash-monitoring.md`](../observability/crash-monitoring.md) - Android crash monitoring.
- [Kotlin Swift export documentation](https://kotlinlang.org/docs/native-swift-export.html)
