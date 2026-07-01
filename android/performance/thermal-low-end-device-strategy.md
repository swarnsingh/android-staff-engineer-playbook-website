# Thermal and Low-End Device Strategy

## Overview

Performance is not a single number on one fast device. Android apps run under heat, low battery, poor signal, limited RAM, old storage, background restrictions, and vendor-specific scheduling.

A Staff engineer designs graceful degradation: the app should reduce work before the OS or hardware does it brutally.

## Device Constraints

| Constraint | Symptom | Design response |
|---|---|---|
| Thermal throttling | CPU/GPU slows, frames miss deadlines | reduce effects, pause prefetch, lower quality |
| Low RAM | LMKs, warm-start misses, OOM | smaller caches, paging, restore state |
| Slow storage | startup stalls, database latency | async init, smaller reads, WAL hygiene |
| Poor CPU | slow JSON/image work | move off Main, simplify transforms, precompute |
| Poor GPU | animation jank, texture upload stalls | reduce overdraw, image size, animation complexity |
| Poor signal | retry storms, battery drain | backoff, batch, offline-first |
| Battery saver | deferred background work | respect constraints, reduce freshness |

## Thermal Status

Android exposes thermal status through `PowerManager` on API 29+.

```kotlin
class ThermalMonitor(
    context: Context,
    private val onStatus: (Int) -> Unit
) {
    private val powerManager = context.getSystemService(PowerManager::class.java)
    private val listener = PowerManager.OnThermalStatusChangedListener { status ->
        onStatus(status)
    }

    @RequiresApi(29)
    fun start(executor: Executor) {
        onStatus(powerManager.currentThermalStatus)
        powerManager.addThermalStatusListener(executor, listener)
    }

    @RequiresApi(29)
    fun stop() {
        powerManager.removeThermalStatusListener(listener)
    }
}
```

Thermal statuses include:

| Status | Meaning | App response |
|---|---|---|
| `NONE` | No throttling | Normal quality |
| `LIGHT` | Light throttling, UX not impacted | Avoid speculative work |
| `MODERATE` | Moderate throttling | Reduce prefetch/animations |
| `SEVERE` | UX largely impacted | Lower quality, pause nonessential work |
| `CRITICAL` | Platform has done everything to reduce power | Stop heavy work |
| `EMERGENCY` | Key components shutting down | Preserve state, stop |
| `SHUTDOWN` | Need shutdown immediately | Persist minimal state |

## Graceful Degradation Matrix

| Feature | Normal | Degraded |
|---|---|---|
| Image feed | high-res thumbnails, prefetch next page | smaller thumbnails, no prefetch |
| Video preview | autoplay muted previews | click-to-play thumbnails |
| Maps | frequent marker updates | lower update frequency, cluster |
| Search | instant suggestions | debounce longer, fewer suggestions |
| Sync | opportunistic background refresh | user-triggered only |
| Animations | full motion | reduced motion/simple transitions |
| Analytics | near-real-time flush | larger batches, delayed flush |

Degradation should be reversible and visible only when it improves UX.

## Low-End Device Budgets

Set budgets by supported device tier:

| Budget | Example |
|---|---|
| Cold start | p95 under agreed threshold on low-end device |
| Scroll | no frozen frames in primary feed |
| Memory | cache cap based on RAM class |
| Network | no background polling loop |
| Disk | first screen avoids large synchronous reads |
| Image | max decoded pixels per cell |
| CPU | no long JSON/crypto work on Main |

Use `ActivityManager.isLowRamDevice` and memory class to tune caches.

```kotlin
val activityManager = context.getSystemService(ActivityManager::class.java)
val memoryClassMb = activityManager.memoryClass
val lowRam = activityManager.isLowRamDevice

val imageCachePercent = if (lowRam) 0.10 else 0.20
```

## App Startup on Low-End Devices

Low-end startup problems often come from:

- DI graph construction.
- ContentProvider initialization.
- Synchronous disk reads.
- Reflection and class loading.
- Database open and migrations.
- First Compose composition doing too much.
- Image/font/resource work before first frame.

Strategy:

- Defer non-critical initialization.
- Use App Startup intentionally.
- Keep first screen state small.
- Move expensive mapping out of composition.
- Measure with Baseline Profiles and startup benchmarks.
- Verify `reportFullyDrawn` represents useful content.

## Low Memory Strategy

When memory is tight:

- Shrink image caches.
- Avoid retaining offscreen screen graphs.
- Use Paging for large lists.
- Release camera/media resources aggressively.
- Store recoverable state in `SavedStateHandle` or durable storage.
- Avoid large in-memory offline queues.

Do not "fix" LMK by pinning foreground services. That trades memory reliability for battery and policy risk.

## Thermal-Aware Work Scheduling

Pause or downgrade:

- Image prefetch.
- ML inference.
- Video processing.
- Large sync batches.
- Database compaction.
- Expensive animations.
- Background indexing.

Keep:

- User-critical state persistence.
- Foreground interaction handling.
- Safety/security operations.
- Small durable writes needed to avoid data loss.

Thermal policy should live in a shared capability object, not scattered `if (hot)` checks.

```kotlin
data class DevicePerformancePolicy(
    val allowPrefetch: Boolean,
    val maxImagePixels: Int,
    val animationQuality: AnimationQuality,
    val syncBatchSize: Int
)
```

## Observability

Track:

- Thermal status distribution during sessions.
- Device RAM class and low-RAM flag.
- Startup and jank by device tier.
- LMK rate by version and device.
- Cache hit/miss and eviction rates.
- Image decode size and failures.
- Background work deferred due to constraints.
- Battery saver and metered network behavior.

Without segmentation, averages hide the users who most need performance work.

## Test Matrix

Minimum practical matrix:

- Low-RAM physical device.
- Mid-tier high-volume device.
- High-refresh flagship.
- Tablet/foldable for adaptive UI.
- Poor network simulation.
- Battery saver mode.
- Thermal stress run for long sessions.
- Font scale and accessibility settings.

Run long enough to expose heat and memory churn. A 30-second happy path does not validate a 20-minute session.

## Staff Engineer Review Checklist

- Are device tiers defined from real user distribution?
- Are performance budgets tier-specific?
- Does the app observe or infer thermal pressure where relevant?
- Can expensive features degrade gracefully?
- Are caches tuned by memory class/low-RAM status?
- Are LMKs monitored and tied to ownership?
- Are startup and scroll benchmarks run on low-end hardware?
- Does process death restoration protect user progress?
- Are background jobs constrained under battery saver and poor network?
- Is degradation product-approved, not accidental?

## Further Reading

- [Android API: PowerManager thermal status](https://developer.android.com/reference/android/os/PowerManager#THERMAL_STATUS_SEVERE)
- [Android Developers: Low memory killers](https://developer.android.com/topic/performance/vitals/lmk)
- [Android Developers: Macrobenchmark](https://developer.android.com/topic/performance/benchmarking/macrobenchmark-overview)
- [`macrobenchmark-and-perfetto.md`](macrobenchmark-and-perfetto.md) - benchmark workflow.
- [`native-memory-bitmaps.md`](native-memory-bitmaps.md) - image/native memory constraints.
