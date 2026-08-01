# Coroutines Debugging and Profiling

## Overview

Coroutine bugs rarely look like syntax bugs. They look like stuck loading spinners, cancelled work that still writes to disk, slow collectors that block emitters, hidden dispatcher starvation, or crashes reported far from the coroutine that caused them.

Debugging coroutines requires two views at once:

- The structured-concurrency tree: which scope owns this work?
- The runtime execution view: which dispatcher, thread, queue, and suspension point is involved?

## The Debugging Model

Every coroutine has:

- A `Job` that defines lifecycle and parent/child cancellation.
- A `CoroutineContext` with dispatcher, name, exception handler, and other elements.
- A state: active, suspended, cancelling, cancelled, or completed.
- A continuation stack that may not look like a normal blocking stack trace.

When production behavior is confusing, ask:

1. Who launched this coroutine?
2. What cancels it?
3. Which dispatcher executes each expensive section?
4. Where can it suspend?
5. Where do exceptions go?
6. Is the code cancellation cooperative?

## Name Important Coroutines

`CoroutineName` is cheap and pays for itself in logs, debug dumps, and trace analysis.

```kotlin
viewModelScope.launch(CoroutineName("Profile/loadProfile")) {
    loadProfile(userId)
}
```

For repeated work, include stable domain identifiers, not raw PII.

```kotlin
syncScope.launch(CoroutineName("Outbox/upload/${operation.type}")) {
    uploader.upload(operation)
}
```

Good names describe ownership and purpose:

- `Checkout/submitOrder`
- `Outbox/drain`
- `Feed/pagingRefresh`
- `Location/shareGps`

Bad names describe implementation:

- `Coroutine1`
- `IO job`
- `launch block`

## Log Cancellation Correctly

`CancellationException` is a control-flow signal. It should normally be rethrown and not reported as a crash.

```kotlin
try {
    repository.refresh()
} catch (e: CancellationException) {
    throw e
} catch (e: IOException) {
    _state.update { it.copy(error = ErrorState.Network) }
}
```

This is especially important with broad `catch (Throwable)` or `runCatching`, because both catch cancellation.

```kotlin
val result = runCatching {
    repository.refresh()
}.onFailure { error ->
    if (error is CancellationException) throw error
}
```

If cancellation is swallowed, parent scopes believe work completed normally while child work may have skipped cleanup or hidden an aborted operation.

## Understand Coroutine Stack Traces

Suspending functions split execution into continuations. A crash stack may show generated continuation frames and may not include the original launcher line.

Improve trace quality by:

- Naming coroutines.
- Keeping launch sites small and meaningful.
- Avoiding huge inline lambdas inside `launch`.
- Converting domain failures to explicit state near the boundary.
- Rethrowing cancellation.

```kotlin
fun refresh() {
    viewModelScope.launch(CoroutineName("Inbox/refresh")) {
        refreshInbox()
    }
}

private suspend fun refreshInbox() {
    _state.update { it.copy(isRefreshing = true) }
    try {
        repository.refreshInbox()
    } finally {
        _state.update { it.copy(isRefreshing = false) }
    }
}
```

Small named functions make stack traces and traces readable.

## Debug Probes and Coroutine Dumps

On JVM targets, `kotlinx-coroutines-debug` can install debug probes that track active coroutines and dump coroutine stacks.

```kotlin
DebugProbes.install()
DebugProbes.dumpCoroutines()
```

Use this in local debug tooling, test diagnostics, or internal debug screens. Do not leave unrestricted coroutine dumps in production because coroutine names and stacks can contain sensitive business context.

The JVM debug agent can also enrich thread names with coroutine ids and names:

```text
-Dkotlinx.coroutines.debug
```

This is most useful in local JVM tests and debug builds.

## Android Studio and Runtime Profiling

Use the Android Studio profiler and Perfetto when the symptom is performance, not logical correctness.

Look for:

- Main thread slices blocked by heavy mapping or JSON parsing.
- Excessive dispatching between Main, IO, and Default.
- Long-running `Dispatchers.Default` work competing with Compose or image work.
- Network or database work accidentally running from Main collectors.
- Repeated upstream restarts after every lifecycle transition.
- Hot flows with active upstream work while the UI is stopped.

Staff-level debugging means correlating coroutine ownership with device-level cost. A Flow pipeline that is "correct" but restarts GPS or network polling on every collector is still a production bug.

## Dispatcher Starvation

Coroutine code can starve dispatchers even without blocking every thread.

### CPU work on IO

```kotlin
withContext(Dispatchers.IO) {
    hugeJsonPayload.decodeAndNormalize()
}
```

`Dispatchers.IO` is for blocking IO. CPU-heavy parsing should usually run on `Dispatchers.Default` or a limited dispatcher.

### Blocking work on Default

```kotlin
withContext(Dispatchers.Default) {
    legacyBlockingClient.execute()
}
```

Blocking calls on `Default` steal CPU workers. Use an IO dispatcher or wrap the blocking API at the edge.

### Main-immediate reentrancy surprises

`Dispatchers.Main.immediate` can run immediately when already on Main. That can be useful for UI state updates, but it can also create surprising reentrancy if a state update triggers code that expected to run later.

Use it intentionally, not as a default optimization.

## Flow-Specific Debugging

### Add temporary lifecycle probes

```kotlin
repository.observeFeed()
    .onStart { logger.debug("feed upstream start") }
    .onEach { logger.debug("feed emission id=${it.id}") }
    .onCompletion { cause ->
        logger.debug("feed upstream complete cause=$cause")
    }
```

Remove noisy logs after diagnosis or gate them behind debug builds.

### Locate the hot boundary

When upstream work restarts unexpectedly, find every `stateIn`, `shareIn`, and collector.

```text
DAO Flow -> Repository map -> ViewModel stateIn -> UI collect
```

If the repository uses `shareIn(applicationScope)`, upstream may keep running even when no screen is visible. If no one uses `shareIn`, multiple collectors may duplicate expensive work.

### Check `SharingStarted`

`SharingStarted.WhileSubscribed(5_000)` prevents quick UI transitions from tearing down upstream immediately. `Eagerly` starts work without a subscriber. `Lazily` starts once and may keep replay forever. These are operational choices, not style preferences.

## Deadlocks and Hangs

### `runBlocking` on Main

```kotlin
fun onClick() {
    runBlocking {
        repository.refresh()
    }
}
```

This blocks the Main thread and can deadlock if the suspended work needs Main to resume. In Android app code, `runBlocking` belongs almost nowhere outside narrow test or bridge code.

### Waiting for a hot flow to complete

```kotlin
val states = viewModel.uiState.toList()
```

`StateFlow` and long-lived `SharedFlow` never complete normally. Use `first`, Turbine, or explicit cancellation.

### Swallowed cancellation in cleanup

```kotlin
finally {
    uploadFinalMetric() // suspends and can be cancelled immediately
}
```

If cleanup must run after cancellation, use `NonCancellable` sparingly and keep it bounded.

```kotlin
finally {
    withContext(NonCancellable) {
        withTimeout(1_000) {
            uploadFinalMetric()
        }
    }
}
```

## Production Observability

Expose metrics that answer ownership and cost questions:

- Active sync jobs by type.
- Queue depth for outbox or channel workers.
- Coroutine retry counts by operation.
- Cancellation counts by screen or feature.
- Flow upstream start/stop counts.
- Dispatcher latency for critical work queues.
- Long Main thread sections around collectors.

Do not log every emission of high-volume flows in production. Prefer counters, histograms, and sampled diagnostics.

When emitting structured logs, use `MDCContext` (from `kotlinx-coroutines-slf4j`) to restore a captured Mapped Diagnostic Context (MDC) across suspension points. Populate request and user fields before capturing the context. Later `MDC.put` mutations are not tracked automatically and can be lost after suspension, so explicitly capture a new `MDCContext` after updates when those fields must propagate.

## Testing for Debuggability

Tests should prove cancellation and ownership, not only happy-path values.

```kotlin
@Test
fun refreshCancelsWhenViewModelClears() = runTest {
    val repository = FakeRepository(
        refreshBlock = { awaitCancellation() }
    )
    val viewModel = InboxViewModel(repository, dispatcher = testDispatcher)

    viewModel.refresh()
    assertTrue(repository.refreshStarted)

    viewModel.clearForTest()
    advanceUntilIdle()

    assertTrue(repository.refreshCancelled)
}
```

If a coroutine is important enough to debug in production, it is important enough to test cancellation in isolation.

## Staff Engineer Review Checklist

- Are important coroutines named?
- Are launch sites small enough to diagnose?
- Does every broad catch rethrow `CancellationException`?
- Is `runBlocking` absent from Android app paths?
- Are dispatcher choices tied to blocking IO, CPU work, or Main updates?
- Is `flowOn` placed at ownership boundaries?
- Are hot flows scoped to the correct lifecycle?
- Do tests prove cancellation and cleanup?
- Are coroutine metrics useful without leaking sensitive data?
- Is debug-only instrumentation kept out of release behavior?

## Further Reading

- [`coroutines.md`](coroutines.md) - structured concurrency and exception propagation.
- [`flow-operators-and-backpressure.md`](flow-operators-and-backpressure.md) - operator-level cancellation and buffering.
- [`test-dispatchers-virtual-time.md`](test-dispatchers-virtual-time.md) - deterministic tests.
- [Kotlin coroutine debugging docs](https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html#debugging-coroutines-and-threads)
- [kotlinx-coroutines-debug API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-debug/)
