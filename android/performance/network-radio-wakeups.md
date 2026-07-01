# Network Radio Wakeups

## Overview

Mobile networking is not only bandwidth and latency. Every network decision can wake radios, keep CPUs active, trigger retries, burn battery, and fail under changing connectivity.

The expensive pattern is frequent small network work: polling, chatty retries, analytics trickles, tiny sync jobs, and background refresh loops that prevent the device from resting.

## First Principles

| Constraint | Why it matters |
|---|---|
| Radio tail energy | Cellular radios can remain in a higher-power state after a transfer |
| Poor signal | More retransmission, slower transfers, higher power |
| Metered networks | User may pay with money, quota, or battery |
| Captive portals | Network exists but cannot reach public internet |
| VPNs | Transport type can hide underlying cost and behavior |
| Doze/App Standby | Background work is deferred and batched |
| Process death | In-memory retry loops disappear or duplicate |

## Polling vs Push vs Sync

| Pattern | Use when | Radio risk |
|---|---|---|
| Push notification | Server knows when data changes | Low if payload is small and not abused |
| Opportunistic sync | Freshness can wait | Low when batched with constraints |
| Bounded polling | Server cannot push and UX needs freshness | Medium; needs interval/backoff/session scope |
| WebSocket | Foreground real-time session | High if kept alive in background |
| SSE | Foreground server-to-client stream | High if kept alive outside visible session |
| Exact alarm + network | User-visible time-critical event | Very high; justify carefully |

Polling every few seconds in the background is almost never acceptable.

## Connectivity State

Use `ConnectivityManager.NetworkCallback` for dynamic state instead of polling synchronous APIs.

```kotlin
class NetworkMonitor(
    private val connectivityManager: ConnectivityManager
) {
    fun start(callback: ConnectivityManager.NetworkCallback) {
        connectivityManager.registerDefaultNetworkCallback(callback)
    }

    fun stop(callback: ConnectivityManager.NetworkCallback) {
        connectivityManager.unregisterNetworkCallback(callback)
    }
}
```

Capabilities matter more than transport names.

```kotlin
fun NetworkCapabilities.toNetworkPolicy(): NetworkPolicy {
    val validated = hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED)
    val unmetered = hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED)
    val captive = hasCapability(NetworkCapabilities.NET_CAPABILITY_CAPTIVE_PORTAL)

    return NetworkPolicy(
        canReachInternet = validated && !captive,
        allowLargeSync = validated && unmetered
    )
}
```

Do not assume Wi-Fi is unmetered or faster than cellular. Query capabilities and bandwidth estimates.

## Batching

Batch small work:

- Analytics events.
- Read receipts.
- Offline mutations.
- Device state pings.
- Cache refreshes.

Bad:

```text
event -> immediate POST
event -> immediate POST
event -> immediate POST
```

Better:

```text
events -> durable queue -> batch upload with max age/size/network constraints
```

Batch policy should define:

- Maximum batch size.
- Maximum event age.
- Flush trigger for foreground user-visible actions.
- Network and battery constraints.
- Idempotency key or sequence number.

## Retry Policy

Network retries are a battery policy.

```kotlin
fun retryDelay(attempt: Int): Duration {
    val base = 2.0.pow(attempt.coerceAtMost(6)).seconds
    val jitter = Random.nextLong(0, 1_000).milliseconds
    return base + jitter
}
```

Rules:

- Retry only idempotent reads/writes or writes with idempotency keys.
- Use exponential backoff with jitter.
- Stop retrying when the app is backgrounded unless work is delegated to WorkManager.
- Respect server `Retry-After`.
- Do not let every app launch restart a storm of failed uploads.

## Foreground vs Background Network

Foreground:

- User is waiting.
- Lower latency matters.
- More aggressive networking is acceptable.
- Still avoid waste and retry storms.

Background:

- User is not watching.
- Batch and defer.
- Use constraints.
- Prefer push or WorkManager.
- Persist state before starting network.

For long-running transfers, foreground service is appropriate only when the user clearly benefits and sees the ongoing work.

## WebSockets and Keepalives

WebSockets are correct for active, foreground, bidirectional sessions:

- Live collaboration.
- Ride tracking while trip is active.
- Active chat screen.
- Trading/dispatch dashboards.

Failure modes:

- Keeping sockets alive in background.
- Aggressive ping intervals.
- Reconnecting immediately in poor signal.
- Sending every local state change as its own packet.
- Treating socket delivery as durable business state.

Use REST sync or push fallback for background freshness.

## Observability

Track:

- Requests per foreground minute and background hour.
- Bytes sent/received by feature.
- Retry attempts by endpoint.
- Network wakeup-like work units by feature.
- Batch size and age.
- Time spent on cellular vs unmetered.
- Upload queue depth and oldest item age.
- WebSocket reconnect count and session duration.

Segment by:

- Network capability: validated, metered, captive.
- App state: foreground/background.
- Battery saver.
- Device tier.
- Country/region if network quality differs.

## Staff Engineer Review Checklist

- Is the freshness requirement explicit?
- Can push replace polling?
- Is polling bounded to a visible session?
- Are background transfers batched and constraint-aware?
- Are retries idempotent, jittered, and capped?
- Are metered and captive networks handled?
- Are sockets closed when the product session ends?
- Are analytics and read receipts batched?
- Does offline work use a durable queue?
- Can telemetry identify the feature responsible for radio cost?

## Further Reading

- [Android Developers: Read network state](https://developer.android.com/develop/connectivity/network-ops/reading-network-state)
- [Android Developers: Optimize network access](https://developer.android.com/develop/connectivity/network-ops/network-access-optimization)
- [Android Developers: Analyze power use with Battery Historian](https://developer.android.com/topic/performance/power/battery-historian)
- [`battery-power-profiling.md`](battery-power-profiling.md) - power measurement workflow.
- [`../../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md`](../../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md) - transport tradeoffs.
