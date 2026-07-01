# SharedFlow and StateFlow

## Overview

`StateFlow` and `SharedFlow` are Kotlin's main hot-flow primitives. They are both always-live stream objects, but they solve different problems:

- `StateFlow` models current state.
- `SharedFlow` broadcasts values to active subscribers with configurable replay and buffering.

The practical Android question is not "which one is newer?" It is: what delivery contract does this feature need under rotation, backgrounding, slow collectors, process death, and multiple subscribers?

## Decision Matrix

| Need | Use | Why | Avoid |
|---|---|---|---|
| Current screen state | `StateFlow<UiState>` | Always has a value and replays latest to new collectors | `SharedFlow` with replay as fake state |
| Derived UI state from repository Flow | `stateIn(viewModelScope, ...)` | Converts cold stream to hot state at ViewModel boundary | Hot repository state unless it is an intentional cache |
| Broadcast app updates to many active collectors | `SharedFlow<T>` | One emission can reach many subscribers | `Channel`, because normal channels are point-to-point |
| One worker should receive each item | `Channel<T>` | Queue/point-to-point semantics | `SharedFlow`, because every subscriber may see the value |
| Latest-only high-frequency values | `StateFlow` or conflated stream | Old values are stale | Lossless queues that grow under pressure |
| Critical business progress | Durable state/outbox | Survives process death and backgrounding | In-memory flow events |
| Ephemeral UI effect where loss is acceptable | `Channel` or carefully configured `SharedFlow` | Contract is explicit and scoped | Treating it as reliable delivery |
| Callback/listener API | `callbackFlow` | Registration tied to collection and cancellation | Manually managed global listeners |

## Mental Model

`StateFlow` is an observable variable.

- It always has a current value.
- A new collector immediately receives the current value.
- Setting an equal value does not emit a new value.
- Slow collectors skip intermediate updates and receive the latest.

`SharedFlow` is a broadcast hub.

- It may have no initial value.
- It can replay zero or more past values to new collectors.
- It does not conflate equal values.
- Its buffering and suspension behavior depend on configuration and subscriber speed.

`Channel` is a queue.

- A normal channel value is consumed by one receiver.
- It is useful for work distribution and point-to-point handoff.
- It is not a broadcast primitive.

## StateFlow Deep Dive

### Current value and initial value

`MutableStateFlow` requires an initial value.

```kotlin
private val _state = MutableStateFlow(ProfileUiState.Loading)
val state: StateFlow<ProfileUiState> = _state.asStateFlow()
```

That requirement is a feature, not ceremony. A UI can always render something.

```kotlin
@Composable
fun ProfileRoute(viewModel: ProfileViewModel) {
    val state by viewModel.state.collectAsStateWithLifecycle()
    ProfileScreen(state)
}
```

### Atomic updates

Prefer `update { }` for state transitions based on the previous value.

```kotlin
_state.update { current ->
    current.copy(
        isLoading = false,
        profile = profile
    )
}
```

This is atomic and safe when multiple coroutines update the same `MutableStateFlow`. Avoid read-modify-write patterns for concurrent updates:

```kotlin
// Risky under concurrency
_state.value = _state.value.copy(count = _state.value.count + 1)

// Better
_state.update { it.copy(count = it.count + 1) }
```

### Equality conflation

`StateFlow` uses equality to suppress duplicate emissions. If `newValue == oldValue`, collectors are not notified.

This is ideal for UI state. Re-rendering the same state is wasted work.

It becomes a bug when state contains mutable objects.

```kotlin
data class CartState(val items: List<Item>)

val mutableItems = _state.value.items as MutableList<Item>
mutableItems.add(newItem)
_state.value = _state.value.copy(items = mutableItems)
```

If the old and new state compare equal because the same list instance was mutated, the UI may not update. Use immutable data and create new collections.

```kotlin
_state.update { current ->
    current.copy(items = current.items + newItem)
}
```

### StateFlow as a special SharedFlow

Conceptually, `StateFlow` behaves like a `SharedFlow` configured with:

- `replay = 1`
- latest-value replacement
- equality-based `distinctUntilChanged`
- a synchronous `.value` property

But do not treat it as just "SharedFlow with replay 1." `StateFlow` has a stronger state contract:

- It always has an initial value.
- It exposes `.value`.
- It conflates equal values.
- It does not support `resetReplayCache`.

### Combining StateFlows

Use `combine` for derived state.

```kotlin
val uiState: StateFlow<HomeUiState> =
    combine(user, notifications, connectivity) { user, notifications, connectivity ->
        HomeUiState(
            user = user,
            unreadCount = notifications.count { !it.read },
            offline = !connectivity.isOnline
        )
    }.stateIn(
        scope = viewModelScope,
        started = SharingStarted.WhileSubscribed(5_000),
        initialValue = HomeUiState.Loading
    )
```

`combine` emits after each upstream has emitted at least once, then emits whenever any upstream changes.

## SharedFlow Deep Dive

### Replay cache

`replay` controls how many past values a new subscriber receives.

```kotlin
private val _prices = MutableSharedFlow<Price>(replay = 5)
val prices: SharedFlow<Price> = _prices.asSharedFlow()
```

A new collector immediately receives up to five cached prices, then live prices.

Inspecting replay:

```kotlin
val cached: List<Price> = _prices.replayCache
```

Resetting replay:

```kotlin
_prices.resetReplayCache()
```

Use `resetReplayCache` carefully. It only exists on `MutableSharedFlow`, and it changes what future subscribers see. Active subscribers are not "un-emitted."

### Extra buffer capacity

`extraBufferCapacity` lets slow active subscribers lag behind without suspending emitters immediately.

```kotlin
private val _gps = MutableSharedFlow<Location>(
    replay = 1,
    extraBufferCapacity = 16,
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)
```

The contract here is explicit: keep the latest location for new subscribers, tolerate short bursts, and drop old values when the consumer cannot keep up.

### No-subscriber behavior

This is the detail that breaks many Android event implementations.

For `MutableSharedFlow`:

- If there are no subscribers, only `replay` values are stored.
- `extraBufferCapacity` does not store values for future subscribers by itself.
- Buffer overflow strategy is not triggered without at least one slow subscriber.
- A default `MutableSharedFlow()` has `replay = 0` and no buffer, so values emitted with no subscribers are lost immediately.

```kotlin
val events = MutableSharedFlow<String>()

events.emit("Navigate") // returns immediately if there are no subscribers
// No replay, no subscriber, value is gone.
```

### `emit` vs `tryEmit`

| API | Suspends? | Success meaning | Dangerous misconception |
|---|---:|---|---|
| `emit(value)` | Yes | Value accepted according to flow config | "It always waits for a future subscriber" |
| `tryEmit(value)` | No | Value accepted immediately | "true means a subscriber received it" |

For a default unbuffered `MutableSharedFlow()`:

- `emit` suspends until all active subscribers receive the value.
- If there are no subscribers, `emit` returns immediately and the value is lost.
- `tryEmit` succeeds only when there are no subscribers, and in that case the value is immediately lost.

That last bullet surprises people. `tryEmit(true)` does not mean "delivered." It means "accepted by the configured SharedFlow without suspension."

### `subscriptionCount`

`MutableSharedFlow.subscriptionCount` is a `StateFlow<Int>` with the number of active collectors.

```kotlin
locationUpdates.subscriptionCount
    .map { count -> count > 0 }
    .distinctUntilChanged()
    .onEach { active ->
        if (active) gps.start() else gps.stop()
    }
    .launchIn(appScope)
```

Use it for resource management, metrics, or debugging. Do not use it as a correctness gate for critical event delivery because subscribers can appear or disappear immediately after the check.

### SharedFlow never completes

`SharedFlow.collect` never completes normally. It also cannot be closed like a channel. If a shared stream needs to represent completion or failure, materialize that as data:

```kotlin
sealed interface SyncSignal {
    data object Started : SyncSignal
    data class Progress(val percent: Int) : SyncSignal
    data class Failed(val cause: SyncFailure) : SyncSignal
    data object Complete : SyncSignal
}
```

## `stateIn` and `shareIn`

Cold flows become hot with `stateIn` or `shareIn`.

```kotlin
val uiState: StateFlow<ProfileUiState> =
    repository.observeProfile()
        .map(ProfileUiState::Content)
        .catch { emit(ProfileUiState.Error) }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = ProfileUiState.Loading
        )
```

```kotlin
val livePrices: SharedFlow<Price> =
    repository.observePrices()
        .shareIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            replay = 1
        )
```

### SharingStarted strategies

| Strategy | Behavior | Use when | Risk |
|---|---|---|---|
| `Eagerly` | Starts upstream immediately | App-wide singleton cache, metrics stream | Wastes work if nobody needs it |
| `Lazily` | Starts when first subscriber appears, then keeps running | Warm cache after first use | Can keep work alive longer than expected |
| `WhileSubscribed()` | Starts with subscribers, stops without subscribers | UI-bound streams | May restart frequently |
| `WhileSubscribed(5_000)` | Delays stop after last subscriber | Android rotation/navigation gaps | Timeout must match expected lifecycle gaps |
| `WhileSubscribed(stopTimeoutMillis, replayExpirationMillis)` | Separately controls upstream stop and replay reset | Sensitive/stale replay data | Incorrect replay expiration causes stale or missing UI |

For Android ViewModels, `SharingStarted.WhileSubscribed(5_000)` is a strong default for UI state derived from cold streams. It avoids restarting upstream work during quick configuration changes.

Use `replayExpirationMillis = 0` when replayed data must be reset as soon as the stream stops:

```kotlin
SharingStarted.WhileSubscribed(
    stopTimeoutMillis = 5_000,
    replayExpirationMillis = 0
)
```

For `stateIn`, replay reset returns to the original `initialValue`. For `shareIn`, replay reset clears the replay cache.

## Lifecycle-Safe Collection

In Compose:

```kotlin
val state by viewModel.uiState.collectAsStateWithLifecycle()
```

For one-off collection in Compose, use `LaunchedEffect` and lifecycle-aware flow collection when needed.

```kotlin
LaunchedEffect(viewModel) {
    viewModel.effects.collect { effect ->
        when (effect) {
            is UiEffect.ShowToast -> snackbarHostState.showSnackbar(effect.message)
        }
    }
}
```

In Views/Fragments:

```kotlin
viewLifecycleOwner.lifecycleScope.launch {
    viewLifecycleOwner.repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            render(state)
        }
    }
}
```

Do not collect a UI flow with plain `lifecycleScope.launch { collect { } }` from a Fragment view. The collector can outlive the view and keep doing work while stopped.

## The Single-Event Problem

The common anti-pattern:

```kotlin
private val _events = MutableSharedFlow<UiEvent>()
val events = _events.asSharedFlow()

fun onLoginSuccess() {
    viewModelScope.launch {
        _events.emit(UiEvent.NavigateHome)
    }
}
```

If the UI is stopped when the event is emitted, the default `SharedFlow` has no subscriber and no replay. The navigation event is lost.

Adding `replay = 1` creates a different bug: a new collector may receive old navigation after rotation or after returning to the screen unless the replay cache is reset carefully.

## Event-as-State Pattern

For effects the user must see, model pending work as state with stable IDs.

```kotlin
data class UiMessage(
    val id: String,
    val text: String
)

data class LoginUiState(
    val isLoading: Boolean = false,
    val pendingMessages: List<UiMessage> = emptyList(),
    val destination: Destination? = null
)
```

ViewModel:

```kotlin
fun onLoginFailed(error: LoginError) {
    _state.update { current ->
        current.copy(
            isLoading = false,
            pendingMessages = current.pendingMessages + UiMessage(
                id = newMessageId(),
                text = error.userMessage
            )
        )
    }
}

fun onMessageShown(id: String) {
    _state.update { current ->
        current.copy(
            pendingMessages = current.pendingMessages.filterNot { it.id == id }
        )
    }
}
```

`newMessageId()` can be backed by any app-approved unique ID strategy. The important part is that each pending message has a stable identity for Compose effects and explicit consumption.

Compose:

```kotlin
val message = state.pendingMessages.firstOrNull()

LaunchedEffect(message?.id) {
    if (message != null) {
        snackbarHostState.showSnackbar(message.text)
        viewModel.onMessageShown(message.id)
    }
}
```

This survives rotation because the pending message is part of state. It avoids replay cache hacks because consumption is explicit.

For navigation, prefer durable screen state:

```kotlin
if (state.destination == Destination.Home) {
    LaunchedEffect(Unit) {
        navController.navigate("home") {
            popUpTo("login") { inclusive = true }
        }
        viewModel.onNavigationHandled()
    }
}
```

If navigation represents critical business progress, persist the underlying progress, not just an in-memory event.

## When SharedFlow Effects Are Acceptable

`SharedFlow` can still be fine for ephemeral effects when loss is acceptable and documented.

Examples:

- Debug toasts.
- Haptic pulse while a visible control is pressed.
- Analytics/debug stream for currently visible developer tooling.
- Non-critical UI animation cues.

Make the contract explicit:

```kotlin
private val _effects = MutableSharedFlow<UiEffect>(
    replay = 0,
    extraBufferCapacity = 1,
    onBufferOverflow = BufferOverflow.DROP_OLDEST
)
val effects = _effects.asSharedFlow()

fun pulse() {
    _effects.tryEmit(UiEffect.HapticPulse)
}
```

This says: keep at most one pending effect for slow active collectors; drop old effects; do not replay to future collectors.

## Testing

### StateFlow value assertions

```kotlin
@Test
fun incrementsAtomically() = runTest {
    val viewModel = CounterViewModel()

    coroutineScope {
        repeat(100) {
            launch { viewModel.increment() }
        }
    }

    assertEquals(100, viewModel.state.value.count)
}
```

The implementation should use `_state.update { }`, not read-modify-write.

### Testing StateFlow emissions with Turbine

```kotlin
@Test
fun emitsLoadingThenContent() = runTest {
    viewModel.uiState.test {
        assertEquals(ProfileUiState.Loading, awaitItem())

        repository.emit(Profile("Asha"))

        assertEquals(ProfileUiState.Content("Asha"), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Testing SharedFlow no-subscriber behavior

```kotlin
@Test
fun defaultSharedFlowDropsWithoutSubscribers() = runTest {
    val events = MutableSharedFlow<String>()

    events.emit("lost")

    events.test {
        expectNoEvents()
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Testing lifecycle-sensitive event-as-state

```kotlin
@Test
fun messageStaysPendingUntilConsumed() = runTest {
    viewModel.onLoginFailed(LoginError.Network)

    val message = viewModel.state.value.pendingMessages.single()
    assertEquals("Network unavailable", message.text)

    viewModel.onMessageShown(message.id)

    assertTrue(viewModel.state.value.pendingMessages.isEmpty())
}
```

## KMP and Kotlin 2.4 Note

Kotlin 2.4 Swift export can export `kotlinx.coroutines` Flow APIs to Swift as `AsyncSequence` with type information preserved. That improves the KMP story for `StateFlow` and `SharedFlow`, but it does not change the semantics described above:

- `StateFlow` is still current state.
- `SharedFlow` is still broadcast with replay/buffer rules.
- The Swift collector must still be cancelled with Swift task lifecycle.
- Exported Flow collection uses Kotlin coroutine dispatching under the hood; switch dispatchers in Kotlin when Main confinement is required.

Treat Swift export as an interop surface, not as a semantic adapter that makes event delivery reliable.

## Staff Engineer Review Checklist

- Is the primitive chosen from a delivery contract, not taste?
- Does UI state use `StateFlow` and immutable state objects?
- Are state transitions based on previous state using `update { }`?
- Are one-off critical effects modeled as state or durable progress?
- If `SharedFlow` is used, are `replay`, `extraBufferCapacity`, and `onBufferOverflow` justified?
- Does the team understand no-subscriber behavior?
- Are `tryEmit` results handled when drops matter?
- Is `subscriptionCount` used only for resource management, not correctness?
- Is `stateIn`/`shareIn` scoped to the right owner?
- Does `SharingStarted` match lifecycle and resource cost?
- Are hot-flow tests finite through Turbine, `first`, `take`, or explicit cancellation?

## Common Misconceptions

- "`SharedFlow` is for one-off events." Incomplete. It is a configurable broadcast flow. Whether it is safe for an event depends on loss, replay, lifecycle, and consumption semantics.
- "`tryEmit` true means delivered." False. It means accepted without suspension by the configured flow.
- "`replay = 1` makes SharedFlow a StateFlow." False. It lacks `.value`, initial value, and equality conflation.
- "`StateFlow` cannot represent errors." False. State can include error fields, pending messages, and retry affordances.
- "A repository must never return `StateFlow`." Too absolute. It should not accidentally create immortal caches, but app-wide state holders may intentionally expose hot state if lifecycle and memory are designed.

## Probing Questions

1. What happens when `emit` is called on a default `MutableSharedFlow` with zero subscribers?
2. Why can `tryEmit` return true while no active collector receives the value?
3. Why is `MutableStateFlow.update { }` safer than assigning `_state.value = _state.value.copy(...)` under concurrency?
4. How does equality conflation interact with mutable lists inside data classes?
5. What is the difference between replay cache and extra buffer capacity?
6. When would `resetReplayCache` be appropriate?
7. How does `WhileSubscribed(5_000)` change behavior during rotation?
8. Why is `replay = 1` dangerous for navigation events?
9. When is a `Channel` more correct than a `SharedFlow`?
10. What changes when a Flow is exported to Swift `AsyncSequence` in Kotlin 2.4, and what does not change?

## Further Reading

- [`../architecture/flow.md`](../architecture/flow.md) - Cold vs hot Flow foundations.
- [`../../kotlin/flow-operators-and-backpressure.md`](../../kotlin/flow-operators-and-backpressure.md) - Flow operator semantics.
- [`../../kotlin/channels-and-select.md`](../../kotlin/channels-and-select.md) - Channels and point-to-point delivery.
- [`../../kotlin/test-dispatchers-virtual-time.md`](../../kotlin/test-dispatchers-virtual-time.md) - Testing hot flows.
- [Android Developers: StateFlow and SharedFlow](https://developer.android.com/kotlin/flow/stateflow-and-sharedflow)
- [Kotlin API: StateFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-state-flow/)
- [Kotlin API: SharedFlow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-shared-flow/)
- [Kotlin API: SharingStarted](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-sharing-started/)
