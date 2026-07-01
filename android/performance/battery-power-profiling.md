# Battery and Power Profiling

## Overview

Battery performance is not just "background work." It is the total cost of CPU, screen, radio, GPS, wake locks, sensors, jobs, alarms, foreground services, and retries over time.

A Staff engineer treats power as a production budget. The goal is to understand which user journeys and background behaviors keep hardware active, then reduce or batch that work without breaking product guarantees.

## Measurement Stack

| Tool | Use for | Notes |
|---|---|---|
| Power Profiler | Local power exploration in Android Studio | Good first pass for CPU/radio/sensor clues |
| System tracing/Perfetto | Correlating work with frames, CPU, jobs, wakeups | Preferred modern trace workflow |
| Macrobenchmark power metrics | Repeatable journey-level power checks | Useful in regression suites |
| Batterystats | Framework battery accounting dump | Still useful for device-level evidence |
| Battery Historian | HTML visualization over Batterystats | No longer actively maintained; use when it helps |
| Android vitals | Field signals: wake locks, wakeups, network, battery | Production monitoring, not root cause alone |

Official Android guidance now warns that Battery Historian is no longer actively maintained, so prefer system tracing, Macrobenchmark power metrics, or Power Profiler when possible. Historian remains useful for reading older workflows and broad device timelines.

## What Drains Battery

| Cost center | Typical cause | Better design |
|---|---|---|
| CPU | tight loops, JSON parsing, encryption, image work | batch, cache, move off Main, reduce work |
| Radio | frequent small requests, polling, retries | batch, push, backoff, cache, opportunistic sync |
| GPS | high accuracy updates when coarse is enough | lower priority, geofencing, lifecycle-aware collection |
| Wake locks | manual locks around long work | WorkManager, foreground service only when user-visible |
| Alarms | frequent exact wakeups | inexact windows, WorkManager, server-side aggregation |
| Sensors | high-frequency sampling | sample, conflate, stop on lifecycle |
| Screen/GPU | animations, bright video, high refresh | pause, reduce effects, dark surfaces where appropriate |

## Profiling Protocol

1. Define the scenario.
2. Charge device enough to avoid low-battery throttling.
3. Reset or isolate battery stats.
4. Run the scenario on battery, disconnected from USB.
5. Capture trace/bugreport.
6. Compare against a baseline build.
7. Segment findings by device/network state.

Example scenarios:

- App idle for 30 minutes after login.
- Background sync with 100 pending operations.
- Turn-by-turn tracking for 20 minutes.
- Feed refresh over cellular with poor signal.
- Media upload retry while app is backgrounded.

## Batterystats Workflow

```bash
adb shell dumpsys batterystats --reset
# disconnect USB, run scenario on battery, reconnect
adb shell dumpsys batterystats > batterystats.txt
adb bugreport bugreport.zip
```

Review:

- Wake locks.
- JobScheduler activity.
- Alarm wakeups.
- Mobile radio active time.
- GPS/sensor activity.
- Foreground service duration.
- App process state during work.

## Wake Locks

Manual wake locks are a last resort. They are easy to leak and hard to reason about.

Prefer:

- WorkManager for deferrable guaranteed work.
- Foreground service only for user-visible ongoing work.
- ExoPlayer/media APIs for media use cases.
- Location APIs with lifecycle and priority controls.

If a wake lock is unavoidable:

- Use the narrowest scope.
- Set a timeout.
- Release in `finally`.
- Add metrics around acquisition duration.
- Review Android vitals for excessive/stuck wake locks.

```kotlin
val wakeLock = powerManager.newWakeLock(
    PowerManager.PARTIAL_WAKE_LOCK,
    "App:CriticalUpload"
)

try {
    wakeLock.acquire(30_000)
    uploadCriticalFile()
} finally {
    if (wakeLock.isHeld) wakeLock.release()
}
```

Most apps should not need this code.

## Jobs, Alarms, and Sync

Battery-friendly background work is:

- Batched.
- Constraint-aware.
- Idempotent.
- Retry-bounded.
- Cancelable.
- Observable.

Use WorkManager constraints:

```kotlin
val constraints = Constraints.Builder()
    .setRequiredNetworkType(NetworkType.UNMETERED)
    .setRequiresBatteryNotLow(true)
    .build()
```

Do not use exact alarms for routine sync. Exact alarms wake the device at precise times and should be reserved for user-visible, time-critical behavior.

## Location and Sensors

Location is one of the easiest ways to create silent battery damage.

Staff-level questions:

- Does the feature need high accuracy?
- Does it need updates while backgrounded?
- Can it use geofencing instead of continuous GPS?
- Can updates stop when UI is not visible?
- Can old updates be conflated?
- Is there a maximum session duration?

For sensor streams, sample and conflate when only latest values matter.

## Power Budgets

Create product budgets:

| Feature | Budget example |
|---|---|
| Idle logged-in app | No wake locks, no periodic network more often than agreed interval |
| Chat sync | Push-first, bounded fallback polling, no exact alarms |
| Location sharing | Foreground notification, session timeout, adaptive accuracy |
| Upload queue | Wi-Fi/charging preference for large media, resumable chunks |
| Feed refresh | User-triggered or opportunistic, backoff on failure |

Budgets turn battery into an architecture constraint instead of a late bug.

## Field Monitoring

Monitor:

- Excessive wake locks.
- Stuck partial wake locks.
- Excessive wakeups.
- Excessive background network usage.
- Excessive background Wi-Fi scans.
- Foreground service duration.
- Job retry counts.
- Sync queue depth and age.

Android vitals can surface several of these issues at scale. Pair those signals with app telemetry so you can identify which feature caused the behavior.

## Staff Engineer Review Checklist

- Is the work user-visible, deferrable, or durable background work?
- Can it be batched with other work?
- Are retries bounded with exponential backoff?
- Does it respect battery-not-low and unmetered constraints when appropriate?
- Are GPS/sensor sessions scoped and time-limited?
- Are wake locks absent or heavily justified?
- Are foreground services tied to visible user value?
- Does offline work survive process death without spinning?
- Is battery measured on real devices and poor networks?
- Are Android vitals and app telemetry connected to ownership?

## Further Reading

- [Android Developers: Profile battery usage with Batterystats and Battery Historian](https://developer.android.com/topic/performance/power/setup-battery-historian)
- [Android Developers: Analyze power use with Battery Historian](https://developer.android.com/topic/performance/power/battery-historian)
- [Android Developers: System tracing overview](https://developer.android.com/topic/performance/tracing)
- [`../concurrency/battery-optimizations.md`](../concurrency/battery-optimizations.md) - Doze and App Standby.
- [`network-radio-wakeups.md`](network-radio-wakeups.md) - radio-specific battery cost.
