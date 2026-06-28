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
- [SavedStateHandle](android/architecture/savedstatehandle.md)
- [Process Death & State Restoration](android/architecture/process-death-and-state-restoration.md)
- [Structured Concurrency](android/architecture/structured-concurrency.md)
- [Flow](android/architecture/flow.md)

### Compose

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
- [ANRs](android/performance/anrs.md)
- [Baseline Profiles](android/performance/baseline-profiles.md)
- [Memory Management & Leaks](android/performance/memory-management-and-leaks.md)
- [App Size & R8](android/performance/app-size-and-r8.md)

### Data & DI

- [Room](android/data-and-di/room.md)
- [Paging](android/data-and-di/paging.md)
- [DataStore](android/data-and-di/datastore.md)
- [Dependency Injection (Hilt)](android/data-and-di/dependency-injection.md)

### Networking & Security

- [Retrofit & OkHttp](android/networking-and-security/retrofit-and-okhttp.md)
- [GraphQL](android/networking-and-security/graphql.md)
- [Security & Keystore](android/networking-and-security/security-and-keystore.md)

### System Internals

- [Binder](android/os-internals/the-binder.md)
- [Zygote](android/os-internals/the-zygote.md)
- [ART & Dalvik](android/os-internals/art-and-dalvik.md)
- [Gradle & Build Systems](android/os-internals/gradle-and-build-systems.md)

### Observability (Application Files)

Canonical observability concepts live in [`observability/`](observability.md). These are the Android-specific implementations.

- [New Relic](android/observability/new-relic.md)
- [Crash Monitoring](android/observability/crash-monitoring.md)
- [Logging](android/observability/logging.md)

### Cross-References (Topics Owned Elsewhere)

- App Bundles & Dynamic Feature Delivery → [`release-engineering/app-bundles.md`](release-engineering/app-bundles.md)
- App Startup → [`mobile-system-design/app-startup.md`](mobile-system-design/app-startup.md)
- Performance horizontal view → [`mobile-system-design/performance.md`](mobile-system-design/performance.md)
