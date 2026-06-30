# Android

## Purpose

The Android platform, top to bottom — from app architecture down to Binder IPC. This is the most depth-heavy tree in the repo because Android is where the work actually happens.

## Why It Matters

Operating at Staff Mobile Platform Engineer level means understanding Android not as a collection of APIs but as a system with constraints (process death, doze, battery, ANRs) that shape every design decision above it.

## Learning Order

Architecture and lifecycle first (you cannot reason about anything else without these), then Compose (the modern UI system), then concurrency, then performance and operations. Build systems and internals come last — they sharpen everything that came before.

## Topics

### Architecture

- [Activity](android/architecture/activity.md)
- [Fragment](android/architecture/fragment.md)
- [ViewModel](android/architecture/viewmodel.md)
- [Navigation](android/architecture/navigation.md)
- [MVVM vs MVI](android/architecture/mvvm-vs-mvi.md)
- [Modularization Strategies](android/architecture/modularization-strategies.md)
- [SavedStateHandle](android/architecture/savedstatehandle.md)
- [Process Death & State Restoration](android/architecture/process-death-and-state-restoration.md)
- [Structured Concurrency](android/architecture/structured-concurrency.md)
- [Flow](android/architecture/flow.md)
- [State Management (patterns)](android/architecture/state-management.md)

### Compose

- [Compose Runtime](android/compose/compose-runtime.md)
- [Stability (`@Stable` / `@Immutable`)](android/compose/stability.md)
- [Snapshot System (MVCC for UI state)](android/compose/snapshot-system.md)
- [Compose Navigation](android/compose/compose-navigation.md)
- [Modifiers & Layout](android/compose/modifiers-and-layout.md)
- [Recomposition & State](android/compose/recomposition-and-state.md)
- [Side Effects](android/compose/side-effects.md)

### Concurrency

- Coroutines language mechanics: [`kotlin/coroutines.md`](kotlin/coroutines.md)
- [Coroutines Under the Hood](android/concurrency/coroutines-under-the-hood.md)
- [Threads & Looper](android/concurrency/threads-and-looper.md)
- [SharedFlow & StateFlow](android/concurrency/shared-flow-and-state-flow.md)
- [Synchronization & Mutex](android/concurrency/synchronization-and-mutex.md)
- [Services](android/concurrency/services.md)
- [WorkManager](android/concurrency/workmanager.md)
- [Battery Optimizations (Doze, App Standby)](android/concurrency/battery-optimizations.md)

### Performance

- [Jank](android/performance/jank.md)
- [Rendering (RenderThread, Skia)](android/performance/rendering.md)
- [Startup (Cold/Warm/Hot)](android/performance/startup.md)
- [ANRs](android/performance/anrs.md)
- [Baseline Profiles](android/performance/baseline-profiles.md)
- [Memory Management & Leaks](android/performance/memory-management-and-leaks.md)
- [App Size & R8](android/performance/app-size-and-r8.md)

### Data & DI

- [Room](android/data-and-di/room.md)
- [Paging](android/data-and-di/paging.md)
- [DataStore](android/data-and-di/datastore.md)
- [Room vs DataStore](android/data-and-di/room-vs-datastore.md)
- [Hilt vs Koin vs Manual DI](android/data-and-di/hilt-vs-koin-vs-manual-di.md)
- [Hilt Components](android/data-and-di/components.md)
- [Scopes (Hilt vs coroutine)](android/data-and-di/scopes.md)
- [Dependency Injection (Hilt)](android/data-and-di/dependency-injection.md)

### Networking & Security

- [Retrofit & OkHttp](android/networking-and-security/retrofit-and-okhttp.md)
- [Ktor vs Retrofit (decision)](android/networking-and-security/ktor-vs-retrofit.md)
- [GraphQL](android/networking-and-security/graphql.md)
- [Security & Keystore](android/networking-and-security/security-and-keystore.md)

### System Internals

- [Binder](android/os-internals/the-binder.md)
- [Zygote](android/os-internals/the-zygote.md)
- [ART & Dalvik](android/os-internals/art-and-dalvik.md)
- [Gradle & Build Systems](android/os-internals/gradle-and-build-systems.md)
- [KSP (Kotlin Symbol Processing)](android/os-internals/ksp.md)
- [Convention Plugins](android/os-internals/convention-plugins.md)
- [Multi-Module Project Structure](android/os-internals/multi-module.md)

### Testing

- [Unit Testing (JUnit, MockK, Turbine)](android/testing/unit-testing.md)
- [UI Testing (Compose, Robolectric, Paparazzi)](android/testing/ui-testing.md)

### Kotlin Multiplatform (KMP)

- [Overview & K1 vs K2](android/kotlin-multiplatform/foundations/overview-and-k1-vs-k2.md)
- [Architecture & Module Boundaries](android/kotlin-multiplatform/foundations/architecture-and-module-boundaries.md)
- [Build System & Source Sets](android/kotlin-multiplatform/tooling/build-system-and-source-sets.md)
- [iOS Distribution (XCFramework/SPM)](android/kotlin-multiplatform/tooling/ios-distribution.md)
- [Swift Interop & SKIE](android/kotlin-multiplatform/tooling/swift-interop.md)
- [Libraries Ecosystem](android/kotlin-multiplatform/ecosystem/libraries-ecosystem.md)
- [Networking with Ktor](android/kotlin-multiplatform/ecosystem/networking-with-ktor.md)
- [Persistence (SQLDelight/Realm)](android/kotlin-multiplatform/ecosystem/persistence.md)
- [Dependency Injection (Koin)](android/kotlin-multiplatform/ecosystem/dependency-injection.md)
- [Compose Multiplatform](android/kotlin-multiplatform/ui-sharing/compose-multiplatform.md)
- [Resource Sharing](android/kotlin-multiplatform/ui-sharing/resource-sharing.md)
- [Concurrency & Memory Model](android/kotlin-multiplatform/production/concurrency-and-memory.md)
- [Testing & Mocking](android/kotlin-multiplatform/production/testing-and-mocking.md)
- [CI/CD for KMP](android/kotlin-multiplatform/production/ci-cd-for-kmp.md)
- [Adoption & Migration](android/kotlin-multiplatform/production/adoption-and-migration.md)

### Observability (Application Files)

Canonical observability concepts live in [`observability/`](observability.md). These are the Android-specific implementations.

- [New Relic](android/observability/new-relic.md)
- [Crash Monitoring](android/observability/crash-monitoring.md)
- [Logging](android/observability/logging.md)

### Cross-References (Topics Owned Elsewhere)

- App Bundles & Dynamic Feature Delivery → [`release-engineering/app-bundles.md`](release-engineering/app-bundles.md)
- App Startup → [`mobile-system-design/app-startup.md`](mobile-system-design/app-startup.md)
- Performance horizontal view → [`mobile-system-design/performance.md`](mobile-system-design/performance.md)
