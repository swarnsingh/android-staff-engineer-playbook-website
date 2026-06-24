# Android

## Purpose

The Android platform, top to bottom — from app architecture down to Binder IPC. This is the most depth-heavy tree in the repo because Android is where the work actually happens.

## Why It Matters

Operating at Staff Mobile Platform Engineer level means understanding Android not as a collection of APIs but as a system with constraints (process death, doze, battery, ANRs) that shape every design decision above it.

## Learning Order

Architecture and lifecycle first (you cannot reason about anything else without these), then Compose (the modern UI system), then concurrency, then performance and operations. Build systems and internals come last — they sharpen everything that came before.

## Topics

### Architecture

- [Activity](android/activity.md)
- [Fragment](android/fragment.md)
- [ViewModel](android/viewmodel.md)
- [Navigation](android/navigation.md)
- [SavedStateHandle](android/savedstatehandle.md)
- [Process Death & State Restoration](android/process-death-and-state-restoration.md)

### Compose

- [Compose Runtime](android/compose-runtime.md)
- [Recomposition](android/recomposition.md)
- [Stability](android/stability.md)
- [Snapshot System](android/snapshot-system.md)
- [Side Effects](android/side-effects.md)
- [State Management](android/state-management.md)

### Concurrency

- [Coroutines](android/coroutines.md) — application file; canonical is [`kotlin/coroutines.md`](kotlin/coroutines.md)
- [Structured Concurrency](android/structured-concurrency.md)
- [Flow](android/flow.md)
- [SharedFlow](android/shared-flow.md)
- [StateFlow](android/state-flow.md)

### Performance

- [Jank](android/jank.md)
- [ANRs](android/anrs.md)
- [Baseline Profiles](android/baseline-profiles.md)
- [Startup](android/startup.md)
- [Rendering](android/rendering.md)
- [Memory Management & Leak Detection](android/memory-management-and-leak-detection.md)

### Lifecycle & Background Execution

- [WorkManager & Background Execution Constraints](android/workmanager-and-background-execution-constraints.md)
- [Doze, App Standby & Battery Optimization](android/doze-app-standby-and-battery-optimization.md)

### Data

- [Room](android/room.md)
- [Paging](android/paging.md)
- [DataStore](android/datastore.md)

### Dependency Injection

- [Hilt](android/hilt.md)
- [Scopes](android/scopes.md)
- [Components](android/components.md)

### Networking

- [Retrofit](android/retrofit.md)
- [OkHttp](android/okhttp.md)
- [GraphQL](android/graphql.md)

### Testing

- [Unit Testing](android/unit-testing.md)
- [UI Testing](android/ui-testing.md)
- [Journey Testing](android/journey-testing.md)

### Build Systems

- [Gradle](android/gradle.md)
- [KSP](android/ksp.md)
- [Convention Plugins](android/convention-plugins.md)
- [Multi-module](android/multi-module.md)
- [R8 / ProGuard](android/r8-proguard.md)
- [App Bundles & Dynamic Feature Delivery](android/app-bundles.md) — stub; canonical is [`release-engineering/app-bundles.md`](release-engineering/app-bundles.md)

### System Internals

- [Binder & IPC](android/binder-and-ipc.md)

### Observability (Application Files)

Canonical observability concepts live in [`observability/`](observability.md). These are the Android-specific implementations.

- [New Relic](android/observability/new-relic.md)
- [Crash Monitoring](android/observability/crash-monitoring.md)
- [Logging](android/observability/logging.md)
