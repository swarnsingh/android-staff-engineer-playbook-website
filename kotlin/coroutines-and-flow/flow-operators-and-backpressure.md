# Flow Operators and Backpressure

## Overview

Kotlin `Flow` is sequential by default. One value moves through the upstream block, each intermediate operator, and the terminal collector in order. Backpressure is built into that chain because `emit` suspends until downstream is ready.

That simple default is the reason Flow is safe. The advanced skill is knowing exactly when an operator changes that default by adding concurrency, buffering, cancellation, or a dispatcher boundary.

## First Principles

```kotlin
flow {
    emit(loadFromDisk())
}
    .map { entity -> entity.toDomain() }
    .filter { user -> user.isActive }
    .collect { user -> render(user) }
```

Without operators like `buffer`, `flowOn`, `flatMapMerge`, or `channelFlow`, this entire pipeline executes sequentially. The upstream producer does not outrun the collector. If `render` is slow, `emit` becomes slow too.

## Operator Categories

| Category | Operators | Staff-level question |
|---|---|---|
| Transform | `map`, `transform`, `mapNotNull` | Is this pure and cheap enough for the current dispatcher? |
| Filter | `filter`, `distinctUntilChanged`, `drop`, `take` | Are equality and termination semantics correct? |
| Side effect | `onEach`, `onStart`, `onCompletion` | Is the side effect idempotent and scoped? |
| Error | `catch`, `retry`, `retryWhen` | Which failures are caught, retried, or surfaced as state? |
| Context | `flowOn` | Which upstream work moves to another dispatcher? |
| Buffering | `buffer`, `conflate`, `collectLatest` | Is dropping, queueing, or cancellation acceptable? |
| Flattening | `flatMapLatest`, `flatMapMerge`, `flatMapConcat` | What happens to old work when a new input arrives? |
| Combining | `combine`, `zip`, `merge` | Do we need latest values, pairs, or interleaving? |
| Timing | `debounce`, `sample`, `timeout` | Is time virtualized in tests and explicit in product behavior? |
| Terminal | `collect`, `first`, `single`, `toList`, `launchIn` | Does the terminal operation match stream cardinality? |

## Transform Operators

### `map`

Use `map` for one-to-one transformation.

```kotlin
val uiState: Flow<ProfileUiState> =
    repository.observeProfile()
        .map { profile -> ProfileUiState.Content(profile.name) }
```

Keep `map` pure when possible. Network calls inside `map` create hidden latency and retry behavior. If transformation is expensive, move the upstream work with `flowOn` or use a dedicated use case.

### `transform`

Use `transform` when one input can emit zero, one, or many outputs.

```kotlin
val results = queryFlow.transform { query ->
    if (query.length < 3) {
        emit(SearchState.TooShort)
    } else {
        emit(SearchState.Loading)
        emit(SearchState.Results(search(query)))
    }
}
```

This is often clearer than combining `map`, `onStart`, and `emitAll` when a state machine is involved.

### `mapLatest`

`mapLatest` cancels the previous transform when a new upstream value arrives.

```kotlin
val suggestions = searchQuery
    .debounce(300)
    .mapLatest { query -> api.suggestions(query) }
```

This is correct for typeahead where old queries are obsolete. It is wrong for payments, uploads, writes, or analytics where previous work must finish.

### `transformLatest`

`transformLatest` provides advanced, suspending latest-value transformations. It behaves like `mapLatest` by cancelling previous transformations when a new value arrives, but allows emitting multiple values (or zero values) like `transform`.

## Error Operators

### `catch`

`catch` catches exceptions thrown upstream of its position. It does not catch exceptions thrown downstream in the collector.

```kotlin
repository.observeProfile()
    .map { it.toUi() }
    .catch { error ->
        emit(ProfileUiState.Error(error.userMessage()))
    }
    .collect { state ->
        render(state) // exceptions here are not caught above
    }
```

Operator placement matters. A `catch` before a risky `map` will not catch that `map`.

### `retryWhen`

Use `retryWhen` when retry policy depends on the failure and attempt count.

```kotlin
fun <T> Flow<T>.retryNetworkReads(): Flow<T> =
    retryWhen { cause, attempt ->
        val retryable = cause is IOException && attempt < 3
        if (retryable) delay(2.0.pow(attempt.toDouble()).seconds)
        retryable
    }
```

Do not retry non-idempotent writes blindly. A retrying Flow around `submitPayment()` can duplicate effects unless the backend has idempotency keys.

### `onCompletion`

`onCompletion` runs for normal completion, failure, and cancellation. Inspect the nullable cause.

```kotlin
flow
    .onCompletion { cause ->
        if (cause == null) metrics.increment("sync_complete")
    }
```

Cancellation is not an error. Avoid logging cancellation as a crash.

## Context with `flowOn`

`flowOn(dispatcher)` changes the context of upstream operators only.

```kotlin
val users = dao.observeUsers()
    .map { rows -> rows.map(UserRow::toDomain) }
    .flowOn(Dispatchers.Default)
    .map { users -> users.sortedBy { it.name } } // downstream context
```

Everything above `flowOn` runs on `Dispatchers.Default`. Everything below it runs in the collector's context unless another boundary is introduced.

Staff-level rule: do not sprinkle `flowOn` randomly. Each `flowOn` creates a concurrency boundary that can change cancellation timing, buffering, and stack traces. Put it at ownership boundaries:

- DAO/database adapter owns disk dispatcher needs.
- Repository owns network/disk mapping if it is expensive.
- ViewModel should not have to remember which upstream methods are safe on Main.

## Backpressure and Buffering

### Default backpressure

```kotlin
flow {
    repeat(1_000) {
        emit(it) // waits for collector
    }
}.collect { value ->
    delay(100)
    render(value)
}
```

The producer emits at the consumer's pace. This is safe but may be too slow when upstream and downstream could work concurrently.

### `buffer`

`buffer(n)` allows upstream to run ahead by `n` values.

```kotlin
repository.events()
    .buffer(capacity = 64)
    .collect { event -> upload(event) }
```

Use buffering when values are important and short bursts are expected. Size the buffer from a real burst budget, not vibes. If the buffer fills, the producer still suspends by default.

### `conflate`

`conflate` keeps the latest value and drops intermediate values when the collector is slow.

```kotlin
locationUpdates()
    .conflate()
    .collect { location -> renderMarker(location) }
```

This is correct for latest-only state like location, scroll position, and progress. It is wrong for ordered logs, audit events, payments, or chat messages.

### `collectLatest`

`collectLatest` cancels the previous collector block when a new value arrives.

```kotlin
queryFlow
    .debounce(300)
    .collectLatest { query ->
        render(api.search(query))
    }
```

The cancellation applies to the body of `collectLatest`. The body must be cancellation cooperative. If it calls a blocking API, the old work may continue on a thread even though the coroutine is cancelled.

## Flattening Operators

### `flatMapLatest`

Use for "new input makes old stream obsolete".

```kotlin
val results: Flow<List<Result>> = queryFlow
    .debounce(300)
    .distinctUntilChanged()
    .flatMapLatest { query ->
        repository.search(query)
    }
```

When `query` changes, collection of the old inner Flow is cancelled.

### `flatMapConcat`

Use when order matters and inner flows must run one after another.

```kotlin
val uploadResults = pendingUploads
    .flatMapConcat { upload -> uploadOne(upload) }
```

This preserves order but can create head-of-line blocking.

### `flatMapMerge`

Use when inner flows may run concurrently.

```kotlin
val thumbnails = imageIds
    .flatMapMerge(concurrency = 4) { id -> repository.thumbnail(id) }
```

Always set a concurrency limit. Unbounded fan-out is a production performance bug.

## Combining Operators

### `combine`

`combine` emits whenever any upstream emits after every upstream has emitted at least once.

```kotlin
val uiState = combine(user, settings, permissions) { user, settings, permissions ->
    HomeUiState(user, settings, permissions)
}
```

This is the default choice for UI state derived from multiple state holders.

### `zip`

`zip` pairs values by index.

```kotlin
val pairs = localIds.zip(remoteIds) { local, remote -> local to remote }
```

This is much rarer in UI. If one stream emits faster, it waits for the other. Do not use `zip` when you mean "latest of both".

### `merge`

`merge` interleaves emissions from multiple flows of the same type.

```kotlin
val refreshTriggers = merge(
    pullToRefreshClicks,
    retryClicks,
    appForegroundEvents
)
```

Use it for common event channels where order between sources is not semantically important.

## Timing Operators

### `debounce`

`debounce` waits for quiet time.

```kotlin
searchText
    .debounce(300.milliseconds)
    .distinctUntilChanged()
    .flatMapLatest(repository::search)
```

Good for search boxes. Bad for critical actions where every input must be handled.

### `sample`

`sample` emits the latest value at a fixed period.

```kotlin
dragPosition
    .sample(16.milliseconds)
    .collect { position -> render(position) }
```

Good for UI frame-like updates. Be explicit that intermediate values are dropped.

## Terminal Operators

| Operator | Use when | Risk |
|---|---|---|
| `collect` | You need every value until cancellation/completion | Never returns for hot flows |
| `first` | You need the first matching value | Hangs if no value arrives |
| `single` | Exactly one value must exist | Throws if zero or many |
| `toList` | Finite flow in tests or batch code | Never returns for hot flows |
| `launchIn(scope)` | You have already used `onEach` and want collection tied to a scope | Easy to hide lifecycle and error handling |

Never call `toList()` on a `StateFlow` or long-lived `SharedFlow` in production code. They never complete normally.

## Android Patterns

### UI state pipeline

```kotlin
val uiState: StateFlow<SearchUiState> =
    query
        .debounce(300.milliseconds)
        .distinctUntilChanged()
        .flatMapLatest { query ->
            if (query.length < 3) {
                flowOf(SearchUiState.Empty)
            } else {
                repository.search(query)
                    .map<SearchResult, SearchUiState>(SearchUiState::Results)
                    .onStart { emit(SearchUiState.Loading) }
                    .catch { emit(SearchUiState.Error) }
            }
        }
        .stateIn(
            scope = viewModelScope,
            started = SharingStarted.WhileSubscribed(5_000),
            initialValue = SearchUiState.Empty
        )
```

This pipeline makes cancellation semantics intentional: new query cancels old search, errors become UI state, and the cold pipeline becomes hot at the ViewModel boundary.

### Write pipeline

```kotlin
suspend fun submitOrder(order: Order) {
    repository.submitOrder(
        order = order,
        idempotencyKey = order.clientRequestId
    )
}
```

Do not hide non-idempotent writes behind `flatMapLatest`, `retryWhen`, or `collectLatest` unless cancellation and duplicate handling are designed with the backend.

## Testing Operator Semantics

Virtual time is mandatory for timing operators.

```kotlin
@Test
fun searchDebouncesTyping() = runTest {
    val queries = MutableSharedFlow<String>()
    val results = mutableListOf<String>()
    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        queries
            .debounce(300.milliseconds)
            .toList(results)
    }

    queries.emit("p")
    advanceTimeBy(299)
    assertTrue(results.isEmpty())

    advanceTimeBy(1)
    runCurrent()
    assertEquals(listOf("p"), results)
}
```

In production tests, prefer Turbine for Flow assertions and `runTest` for deterministic virtual time.

## Staff Engineer Review Checklist

- Does operator placement match the error and dispatcher boundaries?
- Are values queued, dropped, or cancelled intentionally?
- Are write operations protected by idempotency if retries/cancellation are involved?
- Does `flatMapLatest` cancel only work that is truly obsolete?
- Is every `flatMapMerge` concurrency-limited?
- Are timing operators tested with virtual time?
- Does a hot flow terminal operation ever wait for completion?
- Is every `flowOn` attached to a clear ownership boundary?

## Further Reading

- [`coroutines.md`](coroutines.md) - structured concurrency and cancellation.
- [`test-dispatchers-virtual-time.md`](test-dispatchers-virtual-time.md) - deterministic coroutine tests.
- [`../android/concurrency/shared-flow-and-state-flow.md`](../../android/concurrency/shared-flow-and-state-flow.md) - hot-flow selection.
- [Kotlin Flow guide](https://kotlinlang.org/docs/flow.html)
- [Kotlin API: Flow](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/-flow/)
