# NetworkCallback, Metered Networks, VPNs, and Captive Portals

## Overview

Network state is dynamic and advisory. Android can tell you what the system currently knows about connectivity, but that does not prove your API request will succeed.

A Staff engineer treats network state as policy input, not as a replacement for request-level error handling.

## Core Concepts

| Concept | Meaning | Product impact |
|---|---|---|
| Network | A specific connectivity path managed by Android | Wi-Fi, cellular, VPN, satellite, etc. |
| NetworkCapabilities | What that network can do | Internet, validation, metering, captive portal, VPN |
| LinkProperties | DNS, proxy, routes, interface info | Debugging and enterprise networking |
| Default network | Network used by most app traffic | Can change while app runs |
| Validated network | System verified internet reachability | Better signal than "connected" |
| Metered network | User/provider treats data as costly | Avoid large background sync |
| Captive portal | Network requires login before internet | Show recovery, do not spin retries |
| VPN | Traffic may be routed through private network | Transport labels can be misleading |

## Observing Network Changes

```kotlin
class NetworkMonitor(
    private val connectivityManager: ConnectivityManager
) {
    fun observe(): Flow<NetworkStatus> = callbackFlow {
        val callback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                trySend(currentStatus())
            }

            override fun onCapabilitiesChanged(
                network: Network,
                capabilities: NetworkCapabilities
            ) {
                trySend(capabilities.toStatus())
            }

            override fun onLost(network: Network) {
                trySend(currentStatus())
            }
        }

        connectivityManager.registerDefaultNetworkCallback(callback)
        trySend(currentStatus())

        awaitClose {
            connectivityManager.unregisterNetworkCallback(callback)
        }
    }.distinctUntilChanged()
}
```

Use `callbackFlow` so registration is tied to collection and cleanup.

## Capabilities to Check

```kotlin
data class NetworkStatus(
    val hasInternetCapability: Boolean,
    val isValidated: Boolean,
    val isMetered: Boolean,
    val isCaptivePortal: Boolean,
    val isVpn: Boolean
)

fun NetworkCapabilities.toStatus(): NetworkStatus =
    NetworkStatus(
        hasInternetCapability = hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET),
        isValidated = hasCapability(NetworkCapabilities.NET_CAPABILITY_VALIDATED),
        isMetered = !hasCapability(NetworkCapabilities.NET_CAPABILITY_NOT_METERED),
        isCaptivePortal = hasCapability(NetworkCapabilities.NET_CAPABILITY_CAPTIVE_PORTAL),
        isVpn = hasTransport(NetworkCapabilities.TRANSPORT_VPN)
    )
```

Important nuance:

- `NET_CAPABILITY_INTERNET` means the network is configured for internet, not that your backend is reachable.
- `NET_CAPABILITY_VALIDATED` is stronger because Android verified connectivity.
- Captive portals can have a network but block ordinary traffic.
- VPN transport can obscure the underlying physical cost and routing behavior.

## Policy Decisions

| Condition | Good behavior |
|---|---|
| No validated internet | Show offline state, queue durable writes |
| Captive portal | Surface login/retry affordance; pause background retries |
| Metered network | Avoid large media sync unless user opted in |
| VPN | Do not block by default; handle enterprise/proxy failures gracefully |
| Constrained/low bandwidth | Reduce image/video prefetch and batch sync |
| Network changes mid-request | Let request fail/retry through normal policy |

Network policy should influence work, not hide errors.

## WorkManager Constraints

For durable background work:

```kotlin
val constraints = Constraints.Builder()
    .setRequiredNetworkType(NetworkType.CONNECTED)
    .setRequiresBatteryNotLow(true)
    .build()
```

Use `UNMETERED` for large, non-urgent work:

```kotlin
Constraints.Builder()
    .setRequiredNetworkType(NetworkType.UNMETERED)
    .build()
```

Do not implement a forever loop waiting for network inside a coroutine. Persist the work and let the scheduler run it under constraints.

## Request-Level Reality

Even on a validated network:

- DNS can fail.
- TLS can fail.
- Backend can be down.
- Captive portal detection can be stale.
- Enterprise proxy can block your endpoint.
- VPN can route differently.
- Network can disappear after the callback.

Every network call still needs timeout, error classification, retry policy, and user-facing state.

```kotlin
sealed interface NetworkFailure {
    data object Offline : NetworkFailure
    data object Timeout : NetworkFailure
    data object Tls : NetworkFailure
    data object Unauthorized : NetworkFailure
    data class Http(val code: Int) : NetworkFailure
    data class Unknown(val cause: Throwable) : NetworkFailure
}
```

## Captive Portal UX

Captive portal failures often look like:

- HTTP 200 with login HTML instead of JSON.
- TLS failures.
- Redirects to portal login.
- System marks network as captive.

App behavior:

- Avoid destructive retries.
- Keep cached data visible.
- Queue writes.
- Offer "Open network login" through system settings/browser where appropriate.
- Explain that the network requires sign-in, not that the app is broken.

## VPN and Enterprise Networks

VPNs can introduce:

- Split tunneling.
- Private DNS.
- Certificate interception.
- Blocked endpoints.
- Different latency and MTU behavior.

Do not block VPN users by default. Many enterprise users require VPN. Instead:

- Log network capability context in diagnostics.
- Keep TLS errors clear.
- Avoid certificate pinning mistakes unless threat model justifies it.
- Provide support tooling that captures sanitized connection diagnostics.

## Observability

Track:

- Request failures by network capability state.
- Metered vs unmetered bytes.
- Captive portal detection around failures.
- Retry counts by endpoint.
- WorkManager constraint delays.
- Queue age while offline.
- VPN-associated failures if privacy policy allows coarse metadata.

Never log SSIDs, IP addresses, tokens, or full URLs with PII without a privacy review.

## Staff Engineer Review Checklist

- Is network state used as policy input, not truth?
- Does the app check `VALIDATED`, not only `INTERNET`?
- Are metered networks respected for large background work?
- Does captive portal state stop retry storms?
- Are VPNs supported without fragile transport assumptions?
- Are request failures still handled independently?
- Are durable writes queued before network starts?
- Are WorkManager constraints used for background work?
- Are diagnostics privacy-safe?
- Can telemetry distinguish offline, captive, timeout, TLS, and backend errors?

## Further Reading

- [Android Developers: Read network state](https://developer.android.com/develop/connectivity/network-ops/reading-network-state)
- [Android Developers: Manage network usage](https://developer.android.com/develop/connectivity/network-ops/manage-network-usage)
- [Android Developers: Monitor connectivity status and connection metering](https://developer.android.com/develop/connectivity/network-ops/reading-network-state)
- [`../performance/network-radio-wakeups.md`](../performance/network-radio-wakeups.md) - radio and battery cost.
- [`../concurrency/workmanager.md`](../concurrency/workmanager.md) - scheduled durable work.
