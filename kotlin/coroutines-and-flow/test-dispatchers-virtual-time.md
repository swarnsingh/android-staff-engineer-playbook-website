# Test Dispatchers and Virtual Time

## Overview

Coroutine tests should be deterministic. A test that sleeps for real time, races a real dispatcher, or depends on machine speed is not testing coroutine logic; it is negotiating with the scheduler.

`kotlinx-coroutines-test` gives you:

- `runTest` for a structured test scope.
- `TestCoroutineScheduler` for virtual time.
- `StandardTestDispatcher` for queued, deterministic execution.
- `UnconfinedTestDispatcher` for eager execution in narrow cases.
- `backgroundScope` for long-lived work that should be cancelled at test end.

## Why It Matters

Android coroutine code often has:

- Debounce windows.
- Retry delays.
- Timeout behavior.
- `viewModelScope` jobs.
- Flow pipelines that never complete.
- Main dispatcher state updates.
- Work that should cancel when a screen disappears.

Without virtual time, those tests become slow, flaky, or incomplete.

## `runTest`

`runTest` creates a `TestScope` and runs the test with virtual time.

```kotlin
@Test
fun retriesAfterDelay() = runTest {
    val attempts = mutableListOf<Int>()

    retryingOperation(
        onAttempt = { attempts += it },
        delayBetweenAttempts = 1.minutes
    )

    advanceTimeBy(1.minutes)
    advanceUntilIdle()

    assertEquals(listOf(1, 2), attempts)
}
```

`delay(1.minutes)` does not sleep for one real minute. The scheduler advances instantly when the test tells it to.

## The Test Scheduler

All test dispatchers in one test should share the same scheduler.

```kotlin
@Test
fun usesOneScheduler() = runTest {
    val io = StandardTestDispatcher(testScheduler)
    val default = StandardTestDispatcher(testScheduler)

    val repository = Repository(
        ioDispatcher = io,
        defaultDispatcher = default
    )
}
```

If each dispatcher creates its own scheduler, `advanceUntilIdle()` may advance one queue while another queue remains stuck.

## `StandardTestDispatcher`

`StandardTestDispatcher` queues work until the test thread yields control through `runCurrent`, `advanceTimeBy`, or `advanceUntilIdle`.

```kotlin
@Test
fun standardDispatcherIsQueued() = runTest {
    var value = 0

    launch(StandardTestDispatcher(testScheduler)) {
        value = 1
    }

    assertEquals(0, value)
    runCurrent()
    assertEquals(1, value)
}
```

Use it by default. It exposes missing yields and ordering assumptions.

## `UnconfinedTestDispatcher`

`UnconfinedTestDispatcher` starts work eagerly on the current thread until the first suspension.

```kotlin
@Test
fun unconfinedStartsEagerly() = runTest {
    var started = false

    launch(UnconfinedTestDispatcher(testScheduler)) {
        started = true
        delay(1_000)
    }

    assertTrue(started)
}
```

Use it when eager startup makes the test simpler, especially for collecting flows before triggering emissions. Do not use it to hide ordering problems that exist in production.

## Advancing Time

| API | Meaning | Typical use |
|---|---|---|
| `runCurrent()` | Run tasks scheduled for the current virtual time | Start queued coroutines |
| `advanceTimeBy(duration)` | Move virtual time forward | Test debounce, delay, retry |
| `advanceUntilIdle()` | Run until no queued work remains | Flush finite async work |

Subtle point: after advancing exactly to a scheduled boundary, use `runCurrent()` or `advanceUntilIdle()` to execute tasks scheduled at that new time.

```kotlin
advanceTimeBy(300)
runCurrent()
```

This prevents off-by-one scheduler assumptions in debounce and timeout tests.

## Main Dispatcher Rule

ViewModels usually launch on `Dispatchers.Main` through `viewModelScope`. Unit tests must replace Main.

```kotlin
@OptIn(ExperimentalCoroutinesApi::class)
class MainDispatcherRule(
    val dispatcher: TestDispatcher = StandardTestDispatcher()
) : TestWatcher() {
    override fun starting(description: Description) {
        Dispatchers.setMain(dispatcher)
    }

    override fun finished(description: Description) {
        Dispatchers.resetMain()
    }
}
```

Usage:

```kotlin
@get:Rule
val mainDispatcherRule = MainDispatcherRule()

@Test
fun loadsProfile() = runTest {
    val viewModel = ProfileViewModel(repository)

    viewModel.load()
    advanceUntilIdle()

    assertEquals(ProfileUiState.Content, viewModel.uiState.value)
}
```

If the rule's dispatcher and `runTest` use different schedulers, pass the scheduler explicitly when creating dependencies:

```kotlin
val ioDispatcher = StandardTestDispatcher(testScheduler)
```

## Dispatcher Injection

Production code should not hard-code dispatchers deep inside business logic.

```kotlin
class UserRepository(
    private val api: UserApi,
    private val ioDispatcher: CoroutineDispatcher
) {
    suspend fun loadUser(id: UserId): User =
        withContext(ioDispatcher) {
            api.getUser(id)
        }
}
```

Test:

```kotlin
@Test
fun loadUserUsesVirtualScheduler() = runTest {
    val repository = UserRepository(
        api = fakeApi,
        ioDispatcher = StandardTestDispatcher(testScheduler)
    )

    val deferred = async { repository.loadUser(UserId("1")) }
    advanceUntilIdle()

    assertEquals(expectedUser, deferred.await())
}
```

Hard-coded `Dispatchers.IO` forces the test onto a real dispatcher and makes virtual time incomplete.

## Flow Testing

### Finite flows

```kotlin
@Test
fun emitsMappedUsers() = runTest {
    val users = repository.observeUsers()
        .take(2)
        .toList()

    assertEquals(listOf(first, second), users)
}
```

Use `take(n)` for finite assertions. A hot flow may never complete.

### Hot flows

Use Turbine or explicit collection in `backgroundScope`.

```kotlin
@Test
fun emitsUiState() = runTest {
    viewModel.uiState.test {
        assertEquals(UiState.Loading, awaitItem())

        repository.emit(User("Asha"))

        assertEquals(UiState.Content("Asha"), awaitItem())
        cancelAndIgnoreRemainingEvents()
    }
}
```

### Manual collection

```kotlin
@Test
fun collectsHotFlowManually() = runTest {
    val states = mutableListOf<UiState>()

    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        viewModel.uiState.toList(states)
    }

    repository.emit(User("Asha"))
    advanceUntilIdle()

    assertEquals(UiState.Content("Asha"), states.last())
}
```

`backgroundScope` is cancelled automatically when `runTest` finishes, which prevents never-ending hot-flow collectors from hanging the test.

## Testing Debounce

```kotlin
@Test
fun searchIsDebounced() = runTest {
    val queries = MutableSharedFlow<String>()
    val searches = mutableListOf<String>()

    backgroundScope.launch(UnconfinedTestDispatcher(testScheduler)) {
        queries
            .debounce(300.milliseconds)
            .collect { searches += it }
    }

    queries.emit("a")
    advanceTimeBy(299.milliseconds)
    runCurrent()
    assertTrue(searches.isEmpty())

    advanceTimeBy(1.milliseconds)
    runCurrent()
    assertEquals(listOf("a"), searches)
}
```

No `Thread.sleep`. No real 300 ms delay.

## Testing Cancellation

Cancellation behavior is a first-class requirement.

```kotlin
@Test
fun oldSearchIsCancelledWhenNewQueryArrives() = runTest {
    val cancelledQueries = mutableListOf<String>()

    val results = queryFlow
        .flatMapLatest { query ->
            flow {
                try {
                    awaitCancellation()
                } finally {
                    cancelledQueries += query
                }
            }
        }

    backgroundScope.launch { results.collect() }

    queryFlow.emit("old")
    queryFlow.emit("new")
    advanceUntilIdle()

    assertEquals(listOf("old"), cancelledQueries)
}
```

This kind of test catches accidental replacement of `flatMapLatest` with `flatMapMerge` or `map`.

## Common Failure Modes

### Real dispatcher in test

```kotlin
withContext(Dispatchers.IO) {
    delay(10_000)
}
```

Virtual time will not control this if `Dispatchers.IO` is not injected.

### Forgetting to start collectors

With `StandardTestDispatcher`, a collector launched in the background may not start until you call `runCurrent()`.

```kotlin
backgroundScope.launch {
    flow.collect { values += it }
}
runCurrent()
```

Or use `UnconfinedTestDispatcher(testScheduler)` for collectors that must subscribe immediately before emissions.

### Waiting for a hot flow to complete

```kotlin
viewModel.uiState.toList()
```

This hangs because `StateFlow` never completes. Use Turbine, `first`, `take`, or `backgroundScope`.

### Testing implementation details

Avoid asserting that a specific dispatcher method was called. Assert observable behavior:

- UI state changes.
- Work is cancelled.
- Retry delay is respected.
- Callback is unregistered.
- Outbox row transitions state.

## Staff Engineer Review Checklist

- Does every coroutine test use `runTest`?
- Do all injected test dispatchers share `testScheduler`?
- Is `Dispatchers.Main` replaced for ViewModel tests?
- Are production dispatchers injectable?
- Are hot flows collected with Turbine, `take`, `first`, or `backgroundScope`?
- Are timing operators tested with virtual time?
- Are collectors started before emissions?
- Do cancellation tests prove cleanup, not just values?
- Are real sleeps absent from unit tests?
- Does the test fail if cancellation or backpressure semantics change?

## Further Reading

- [`coroutines.md`](coroutines.md) - coroutine foundations.
- [`flow-operators-and-backpressure.md`](flow-operators-and-backpressure.md) - operators that require virtual-time tests.
- [`coroutines-debugging-and-profiling.md`](coroutines-debugging-and-profiling.md) - diagnosing runtime behavior.
- [kotlinx-coroutines-test API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/)
- [Turbine](https://github.com/cashapp/turbine)
