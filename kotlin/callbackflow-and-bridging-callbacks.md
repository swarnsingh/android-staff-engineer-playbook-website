# callbackFlow and Bridging Callbacks

## Overview

`callbackFlow` converts callback-based APIs into a cold `Flow`. It is the correct primitive when the source API pushes values through listeners, observers, sensors, sockets, or platform callbacks that you must register and unregister.

The key idea: collection owns registration. Cancellation owns cleanup.

```kotlin
fun LocationClient.locations(): Flow<Location> = callbackFlow {
    val callback = object : LocationCallback {
        override fun onLocationResult(result: LocationResult) {
            result.lastLocation?.let { location ->
                trySend(location)
            }
        }
    }

    requestLocationUpdates(callback)

    awaitClose {
        removeLocationUpdates(callback)
    }
}
```

No collector, no callback registration. Collector cancelled, callback removed.

## Why It Matters

Android is full of callback APIs:

- Location updates
- Sensors
- Bluetooth scans
- Camera callbacks
- Text watchers
- Connectivity callbacks
- Firebase listeners
- WebSocket callbacks

Bridging these APIs incorrectly causes some of the hardest production bugs: listeners keep running after screens close, duplicate callbacks register after rotation, callback threads update UI state directly, or producer bursts overwhelm the app.

## `callbackFlow` Contract

`callbackFlow` gives the block a `ProducerScope<T>`. That scope is backed by a channel.

Inside the block you can:

- Register the external listener.
- Send values with `trySend`, `trySendBlocking`, or `send` from coroutines.
- Close the flow when the external source completes.
- Use `awaitClose` to unregister the listener on cancellation or close.

```kotlin
fun observeConnectivity(context: Context): Flow<NetworkStatus> = callbackFlow {
    val manager = context.getSystemService(ConnectivityManager::class.java)

    val callback = object : ConnectivityManager.NetworkCallback() {
        override fun onAvailable(network: Network) {
            trySend(NetworkStatus.Available)
        }

        override fun onLost(network: Network) {
            trySend(NetworkStatus.Unavailable)
        }
    }

    manager.registerDefaultNetworkCallback(callback)

    awaitClose {
        manager.unregisterNetworkCallback(callback)
    }
}
```

If the block returns without closing the channel or calling `awaitClose`, `callbackFlow` treats it as a bug because the listener could leak.

## `trySend` vs `send` vs `trySendBlocking`

| API | Use when | Avoid when |
|---|---|---|
| `trySend(value)` | Callback cannot suspend; dropping/failure can be handled | Value is mandatory and failure is ignored |
| `send(value)` | You are already in a coroutine and can suspend | Platform callback is synchronous/non-suspending |
| `trySendBlocking(value)` | Blocking bridge is unavoidable and callback expects backpressure | Callback is on Main, binder, sensor, or high-frequency threads |

Most Android callbacks should use `trySend`.

```kotlin
val result = trySend(event)
if (result.isFailure) {
    metrics.increment("callback_event_dropped")
}
```

Never call a suspending `send` directly from a platform callback unless the callback itself is running in a coroutine you control.

## Buffering

`callbackFlow` uses a channel internally. Configure buffering with Flow operators after the builder.

```kotlin
fun LocationClient.locations(): Flow<Location> =
    callbackFlow {
        val callback = locationCallback { location ->
            trySend(location)
        }

        requestLocationUpdates(callback)
        awaitClose { removeLocationUpdates(callback) }
    }
        .buffer(capacity = Channel.CONFLATED)
```

The buffer is part of the API contract:

- `Channel.CONFLATED`: only latest value matters, common for location and sensors.
- Small explicit buffer: short bursts matter, but not unbounded memory.
- Rendezvous/no buffer: producer should slow down, rarely possible with external callbacks.
- Unlimited buffer: almost never safe on mobile.

## Coldness and Duplicate Registration

Every collection of a cold `callbackFlow` registers a new callback.

```kotlin
val locations = locationClient.locations()

// Two collectors means two callback registrations.
locations.collect { renderMap(it) }
locations.collect { logDebug(it) }
```

If the source should be shared, convert it once at the correct owner boundary.

```kotlin
class LocationRepository(
    appScope: CoroutineScope,
    private val client: LocationClient
) {
    val locations: SharedFlow<Location> =
        client.locations()
            .shareIn(
                scope = appScope,
                started = SharingStarted.WhileSubscribed(
                    stopTimeoutMillis = 5_000
                ),
                replay = 1
            )
}
```

Use `appScope` only when app-wide sharing is intentional. Screen-specific streams should usually be shared in the ViewModel.

## `channelFlow` vs `callbackFlow`

| Builder | Use when | Example |
|---|---|---|
| `callbackFlow` | One external callback/listener source | Location listener, Firebase listener |
| `channelFlow` | You need to launch multiple child coroutines and send concurrently | Merge network polling plus local invalidation |
| `flow` | Sequential suspend code is enough | Load cache, then network |

`channelFlow` is colder and structured like Flow, but it permits concurrent sends from child coroutines.

```kotlin
fun mergedUpdates(): Flow<Update> = channelFlow {
    launch {
        localInvalidations.collect { send(Update.Local(it)) }
    }

    launch {
        remoteSocket.messages.collect { send(Update.Remote(it)) }
    }
}
```

Do not use `channelFlow` only because it feels advanced. It introduces concurrency; use it when you need concurrency.

## Error and Completion Semantics

External APIs often have explicit completion or failure callbacks. Materialize them correctly.

```kotlin
fun Query.snapshots(): Flow<QuerySnapshot> = callbackFlow {
    val registration = addSnapshotListener { snapshot, error ->
        when {
            error != null -> close(error)
            snapshot != null -> trySend(snapshot)
        }
    }

    awaitClose { registration.remove() }
}
```

If the stream should continue after recoverable errors, emit an explicit state instead of closing.

```kotlin
sealed interface SyncEvent {
    data class Data(val items: List<Item>) : SyncEvent
    data class RecoverableError(val message: String) : SyncEvent
}
```

Closing a Flow ends collection. Emitting error state lets the UI continue observing.

## Android Examples

### Text changes

```kotlin
fun EditText.textChanges(): Flow<String> = callbackFlow {
    val watcher = object : TextWatcher {
        override fun afterTextChanged(s: Editable?) {
            trySend(s?.toString().orEmpty())
        }

        override fun beforeTextChanged(s: CharSequence?, start: Int, count: Int, after: Int) = Unit
        override fun onTextChanged(s: CharSequence?, start: Int, before: Int, count: Int) = Unit
    }

    addTextChangedListener(watcher)
    trySend(text?.toString().orEmpty())

    awaitClose {
        removeTextChangedListener(watcher)
    }
}
```

This stream is view-owned. Do not expose it from a repository because it holds a View reference.

### Firebase-style listener

```kotlin
fun DocumentReference.observeUser(): Flow<UserDocument> = callbackFlow {
    val registration = addSnapshotListener { snapshot, error ->
        when {
            error != null -> close(error)
            snapshot != null && snapshot.exists() -> {
                val user = snapshot.toObject(UserDocument::class.java)
                if (user != null) trySend(user)
            }
        }
    }

    awaitClose { registration.remove() }
}
```

Add `.retryWhen` outside only if the SDK does not already retry and the read is safe to retry.

### Sensor stream

```kotlin
data class AccelerometerReading(
    val x: Float,
    val y: Float,
    val z: Float
)

fun SensorManager.accelerometer(): Flow<AccelerometerReading> = callbackFlow {
    val sensor = getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
    val listener = object : SensorEventListener {
        override fun onSensorChanged(event: SensorEvent) {
            trySend(
                AccelerometerReading(
                    x = event.values[0],
                    y = event.values[1],
                    z = event.values[2]
                )
            )
        }

        override fun onAccuracyChanged(sensor: Sensor?, accuracy: Int) = Unit
    }

    registerListener(listener, sensor, SensorManager.SENSOR_DELAY_GAME)

    awaitClose {
        unregisterListener(listener)
    }
}.conflate()
```

Do not pass mutable platform-owned `SensorEvent` instances downstream. Copy the values you need because the framework may reuse objects.

## Lifecycle Collection

`callbackFlow` cleanup only runs when the collecting coroutine is cancelled or the flow completes. Android UI must collect with lifecycle-aware APIs.

```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.locations.collect { location ->
            render(location)
        }
    }
}
```

In Compose:

```kotlin
val state by viewModel.uiState.collectAsStateWithLifecycle()
```

If the UI uses plain `lifecycleScope.launch { flow.collect { } }`, the callback can keep running while the screen is stopped.

## Testing Callback Bridges

Use fake callback sources and verify cleanup.

```kotlin
@Test
fun listenerIsRemovedWhenCollectionIsCancelled() = runTest {
    val source = FakeLocationSource()
    val values = mutableListOf<Location>()

    val job = backgroundScope.launch {
        source.locations().collect { values += it }
    }

    source.emit(Location("test"))
    advanceUntilIdle()

    assertEquals(1, source.listenerCount)
    job.cancel()
    advanceUntilIdle()
    assertEquals(0, source.listenerCount)
}
```

With Turbine:

```kotlin
@Test
fun emitsCallbacks() = runTest {
    val source = FakeLocationSource()

    source.locations().test {
        source.emit(Location("test"))
        assertEquals("test", awaitItem().provider)
        cancelAndIgnoreRemainingEvents()
    }
}
```

## Staff Engineer Review Checklist

- Does registration happen inside collection, not at object construction?
- Does `awaitClose` unregister every listener, callback, or subscription?
- Is `trySend` failure handled or intentionally ignored?
- Is buffer capacity explicit for bursty sources?
- Are high-frequency streams conflated or sampled when only latest data matters?
- Is mutable platform-owned data copied before emission?
- Are multiple collectors intentionally creating multiple registrations?
- If shared, is `shareIn` scoped to the right owner?
- Are errors modeled as terminal failures or recoverable state deliberately?
- Does lifecycle collection actually cancel the callback when UI is stopped?

## Further Reading

- [`channels-and-select.md`](channels-and-select.md) - channel capacity and ownership.
- [`flow-operators-and-backpressure.md`](flow-operators-and-backpressure.md) - buffering and cancellation operators.
- [`../android/concurrency/shared-flow-and-state-flow.md`](../android/concurrency/shared-flow-and-state-flow.md) - hot-flow selection.
- [Kotlin API: callbackFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html)
- [Android Developers: Kotlin flows on Android](https://developer.android.com/kotlin/flow)
