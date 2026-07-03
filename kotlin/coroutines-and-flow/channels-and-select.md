# Channels and Select

## Overview

A `Channel<T>` is a coroutine-aware queue. It lets one coroutine send values while another coroutine receives them. Unlike `Flow`, a channel is not a declarative pipeline. It is a live communication primitive with ownership, capacity, cancellation, and backpressure semantics.

Use channels when you need a point-to-point handoff between coroutines. Use Flow when you need a stream that can be transformed, collected, and scoped as part of a reactive data pipeline.

## Why It Matters

Channels are powerful enough to build actors, event loops, worker queues, fan-out pipelines, debouncers, and callback bridges. They are also easy to misuse. A channel can leak producers, drop values, block senders, or hide failures if the team treats it like a general-purpose event bus.

A Staff engineer should be able to answer:

- Who owns the channel?
- Who closes it?
- What happens when the receiver is slow?
- Are values allowed to be dropped?
- Is delivery point-to-point or broadcast?
- Does cancellation release every sender, receiver, and external listener?

## First Principles

### Channel is a queue, not a broadcast stream

Each element sent to a normal channel is received by one receiver. If three coroutines call `receive`, one value goes to one coroutine. This is the opposite of `SharedFlow`, where one emission can be observed by all active subscribers.

```kotlin
val channel = Channel<JobRequest>()

repeat(4) { workerId ->
    launch {
        for (request in channel) {
            process(workerId, request)
        }
    }
}

requests.forEach { channel.send(it) }
channel.close()
```

This is a work queue. It is not a UI state holder, not a navigation mechanism by default, and not a replacement for `StateFlow`.

### Send and receive suspend instead of blocking threads

`send` suspends when the channel cannot accept a value. `receive` suspends when the channel has no value. Suspension preserves threads, but it still holds coroutine resources and can stall business logic if capacity is chosen carelessly.

```kotlin
val channel = Channel<String>() // rendezvous: no buffer

launch {
    channel.send("A") // suspends until a receiver is ready
}

launch {
    val value = channel.receive()
}
```

## Channel Capacities

| Capacity | Behavior | Use when | Main risk |
|---|---|---|---|
| `Channel.RENDEZVOUS` or `0` | Sender and receiver meet directly | You need strict handoff/backpressure | Sender stalls if receiver is late |
| `Channel.BUFFERED` | Uses default buffered capacity | You need normal producer/consumer decoupling | Default capacity can hide pressure |
| `Channel.CONFLATED` | Keeps only latest value | Only the most recent value matters | Intermediate values are lost |
| `Channel.UNLIMITED` | Sender never suspends for capacity | Bursts are bounded elsewhere | Memory can grow until process death |
| Explicit `Channel(n)` | Keeps up to `n` queued values | You know the burst size | Wrong size creates stalls or drops |

### Rendezvous channel

A rendezvous channel is the safest mental model because it makes backpressure visible.

```kotlin
val handoff = Channel<Frame>(capacity = Channel.RENDEZVOUS)

producerScope.launch {
    camera.frames.collect { frame ->
        handoff.send(frame) // waits for encoder
    }
}

consumerScope.launch {
    for (frame in handoff) {
        encoder.encode(frame)
    }
}
```

This is correct when every frame must be processed and the producer should slow down if the consumer cannot keep up. It is wrong for GPS or sensor streams where old values become stale quickly.

### Conflated channel

A conflated channel is appropriate when newer values supersede older values.

```kotlin
val latestLocation = Channel<Location>(Channel.CONFLATED)

locationCallback = { location ->
    latestLocation.trySend(location)
}

for (location in latestLocation) {
    renderMarker(location)
}
```

The contract is explicit: the UI does not need every historical coordinate. It needs the newest coordinate it can render.

### Unlimited channel

`Channel.UNLIMITED` should be treated like a production incident waiting for a trigger unless the upstream is already bounded.

```kotlin
// Dangerous for user-generated, network, sensor, or retry traffic.
val analytics = Channel<AnalyticsEvent>(Channel.UNLIMITED)
```

If the network is offline and the app keeps queuing events in memory, the process can run out of memory. Durable outbox storage is the right primitive for important offline work.

## Closing and Cancellation

Closing a channel means no more values will be sent. Receivers can still drain already-buffered values.

```kotlin
val channel = Channel<Int>(capacity = 16)

launch {
    try {
        repeat(100) { channel.send(it) }
    } finally {
        channel.close()
    }
}

launch {
    for (value in channel) {
        consume(value)
    }
}
```

Cancellation is stronger than closing. Cancelling a channel aborts waiting senders/receivers and discards buffered values.

```kotlin
override fun onCleared() {
    uploadQueue.cancel()
}
```

Ownership rule: the coroutine or object that creates the channel must define its lifecycle. Passing a mutable channel across layers without an owner makes leaks and half-closed pipelines likely.

## `send`, `trySend`, `receive`, and `receiveCatching`

| API | Suspends? | Use for | Watch out |
|---|---:|---|---|
| `send(value)` | Yes | Backpressured delivery | Can suspend forever if no receiver appears |
| `trySend(value)` | No | Callbacks or best-effort sends | Must inspect `ChannelResult` |
| `receive()` | Yes | Required next value | Throws when channel closes |
| `receiveCatching()` | Yes | Graceful close handling | Still suspends until value or close |

Callback code should normally use `trySend` and inspect the result because most callback APIs cannot suspend.

```kotlin
fun onLocation(location: Location) {
    val result = locations.trySend(location)
    if (result.isFailure) {
        metrics.increment("location_drop")
    }
}
```

## Actor-Style State Ownership

An actor is a coroutine that owns mutable state and receives commands through a channel. This can be useful when state updates must be serialized without exposing locks.

```kotlin
sealed interface CartCommand {
    data class Add(val item: Item) : CartCommand
    data class Remove(val id: ItemId) : CartCommand
    data class Checkout(val replyTo: CompletableDeferred<CheckoutResult>) : CartCommand
}

class CartActor(
    scope: CoroutineScope,
    private val checkout: CheckoutService
) {
    private val commands = Channel<CartCommand>(capacity = Channel.BUFFERED)

    init {
        scope.launch {
            var items = emptyList<Item>()
            for (command in commands) {
                when (command) {
                    is CartCommand.Add -> items = items + command.item
                    is CartCommand.Remove -> items = items.filterNot { it.id == command.id }
                    is CartCommand.Checkout -> {
                        command.replyTo.complete(checkout.submit(items))
                    }
                }
            }
        }
    }

    suspend fun add(item: Item) {
        commands.send(CartCommand.Add(item))
    }

    suspend fun checkout(): CheckoutResult {
        val reply = CompletableDeferred<CheckoutResult>()
        commands.send(CartCommand.Checkout(reply))
        return reply.await()
    }
}
```

This is appropriate when serialized mutation is the central requirement. It is overkill for ordinary ViewModel state where `MutableStateFlow.update { }` is simpler and more transparent.

## `select`

`select` waits for whichever suspending operation becomes available first. It is useful when a coroutine must react to multiple channels, timeouts, or deferred results.

```kotlin
suspend fun nextUiMessage(
    network: ReceiveChannel<Message>,
    local: ReceiveChannel<Message>
): Message = select {
    network.onReceiveCatching { result ->
        result.getOrNull() ?: Message.NetworkClosed
    }
    local.onReceiveCatching { result ->
        result.getOrNull() ?: Message.LocalClosed
    }
}
```

Common `select` use cases:

- Race cache and network results.
- Merge priority and normal work queues.
- Stop a worker when a control channel receives a shutdown signal.
- Implement timeouts or heartbeats around channel receives.

Prefer higher-level Flow operators when you are only transforming streams. Reach for `select` when the control flow itself depends on multiple suspending sources.

## Channel vs Flow vs SharedFlow vs StateFlow

| Need | Preferred primitive | Why |
|---|---|---|
| Current UI state | `StateFlow` | Always has a value and replays latest state |
| Database observation | Cold `Flow` from DAO/repository | Runs only when collected and composes with operators |
| Broadcast updates to many subscribers | `SharedFlow` | One emission can reach many active collectors |
| Work queue where one worker handles each item | `Channel` | Point-to-point delivery |
| Latest-only handoff | Conflated `Channel` or `StateFlow` | Choose channel for queue handoff, StateFlow for observable state |
| Callback bridge | `callbackFlow` | Owns listener registration and cancellation |
| Durable offline command | Database outbox + WorkManager | Process death must not lose the command |

## Android Failure Modes

### Channel used for navigation events

```kotlin
private val events = Channel<UiEvent>(Channel.BUFFERED)
val eventsFlow = events.receiveAsFlow()
```

This can be acceptable for ephemeral UI effects if the team explicitly accepts that events are tied to a single active collector and are lost when the ViewModel dies. It is not acceptable for critical navigation or business progress. For critical progress, write durable state and let the UI render from that state.

### Producer outlives consumer

```kotlin
class Repository {
    private val queue = Channel<Work>(Channel.UNLIMITED)

    fun submit(work: Work) {
        applicationScope.launch { queue.send(work) }
    }
}
```

If there is no active worker, `UNLIMITED` hides the bug until memory grows. If the channel is scoped to an application singleton, it can also keep references alive far longer than expected.

### Exceptions disappear

If a worker catches exceptions and continues, the sender may believe work succeeded even though it failed.

```kotlin
for (work in queue) {
    runCatching { upload(work) }
        .onFailure { error -> logger.warn(error) }
}
```

For important work, send an acknowledgement, persist state transitions, or use WorkManager with an outbox.

## Testing Channels

Prefer testing the public API rather than asserting internal channel mechanics.

```kotlin
@Test
fun workerProcessesQueuedItems() = runTest {
    val processed = mutableListOf<Int>()
    val worker = QueueWorker(
        scope = backgroundScope,
        process = { processed += it }
    )

    worker.enqueue(1)
    worker.enqueue(2)

    advanceUntilIdle()

    assertEquals(listOf(1, 2), processed)
}
```

When the channel itself is public, use `receiveCatching` to avoid brittle close exceptions.

```kotlin
val result = channel.receiveCatching()
assertEquals(expected, result.getOrThrow())
```

## Staff Engineer Review Checklist

- Is this point-to-point work delivery, or should it be a broadcast/state stream?
- Is capacity explicit and justified?
- What happens when the consumer is slower than the producer?
- Is `UNLIMITED` backed by a hard upstream bound?
- Who closes or cancels the channel?
- Do senders learn about processing failure, or only enqueue success?
- Is the channel scoped to a lifecycle that matches the data it carries?
- Would a database outbox survive process death better?

## Further Reading

- [`flow-operators-and-backpressure.md`](flow-operators-and-backpressure.md) - Flow operator and buffering semantics.
- [`callbackflow-and-bridging-callbacks.md`](callbackflow-and-bridging-callbacks.md) - Callback-safe channel creation.
- [`../android/concurrency/shared-flow-and-state-flow.md`](../../android/concurrency/shared-flow-and-state-flow.md) - Hot-flow decision guide.
- [Kotlin API: Channel](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.channels/-channel/)
- [Kotlin API: select](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.selects/select.html)
