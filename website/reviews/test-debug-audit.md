# Coroutine testing and debugging audit

Reviewed 25 October 2026. Read both source chapters completely: `kotlin/coroutines-and-flow/test-dispatchers-virtual-time.md` and `coroutines-debugging-and-profiling.md`. The site overlay contains 14 exact, unique corrections. Canonical Markdown was not changed.

## Confirmed corrections

- `advanceUntilIdle` stops advancing when only `backgroundScope` tasks remain; it is not a way to drain an indefinitely running background collector. The manual collector now uses `runCurrent`.
- The latest-search cancellation example now creates its SharedFlow, uses an explicit `flow<Unit>` type, subscribes before emission, starts the old operation, and processes replacement/cleanup before asserting. Replay-zero emissions are no longer lost before subscription.
- ViewModel cancellation testing defines its dispatcher, replaces Main, shares the scheduler, starts queued work before asserting, and restores Main in finally. App-defined fakes and the nonstandard `clearForTest` hook are labelled as prerequisites.
- `runTest` can advance virtual time automatically as well as explicitly. A noncompleting foreground flow is subject to the test timeout.
- Unconfined eager-entry guarantees and Main scheduler adoption are described with their scope.
- Job lifecycle versus suspended execution, swallowed cancellation versus cancelled Job state, and debug-property versus DebugProbes instrumentation are distinguished.
- The JVM `main @coroutine#2` name is explained as an OS thread plus coroutine id.
- Bounded suspending cleanup now states cooperative-timeout and exception-masking limits.

## Executed evidence

Compiled and ran standalone verification probes with Kotlin/JVM 2.2.21, OpenJDK 17.0.19, and kotlinx-coroutines-core/test JVM 1.10.2 from Maven Central. They passed these assertions:

1. The revised latest-search test records exactly the old query's cleanup before asserting, while the new query is cancelled by test teardown.
2. A queued background-scope collector remains unstarted after `advanceUntilIdle` with no foreground work, then starts after `runCurrent`.
3. Catching a cancellation exception allows the next ordinary statement to execute with `isActive == false`; the Job still ends cancelled.

This tests focused scheduling/cancellation semantics, not an Android ViewModel binary or the entire original example set. The library version is a stated verification environment, not a recommendation to pin production to it.

## Primary sources

- [backgroundScope contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-scope/background-scope.html).
- [UnconfinedTestDispatcher contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-unconfined-test-dispatcher.html).
- [Android coroutine testing guide](https://developer.android.com/kotlin/coroutines/test).
- [Coroutine test API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/).
- [Job lifecycle API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines/-job/).
- [Coroutine debug mode](https://kotlinlang.org/docs/coroutine-context-and-dispatchers.html#debugging-coroutines-and-threads).
- [DebugProbes instrumentation](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-debug/kotlinx.coroutines.debug/-debug-probes/).

## Limits

The Android fragments require app-specific classes, fixtures, dependencies, and imports. They were reviewed against Main/ownership contracts; they were not compiled as an Android application. Perfetto, Android debugger integration, JVM dynamic-attach support, Turbine integration, and device behaviour were not exercised. This is evidence for the listed corrections, not an absolute absence-of-errors certification.
