# callbackFlow bridge audit

Reviewed on 25 October 2026. Read the entire original callbackFlow and Bridging Callbacks chapter. Its canonical Markdown is unchanged. Seven guarded website replacements are recorded in `website/content/corrections-callbacks.json`; they preserve the callback bridge, buffering, sharing, Android examples, lifecycle guidance, tests, and review checklist.

## Corrections

1. The two-collector example now starts both collections concurrently. Sequential collection of the first long-lived flow would never reach the second call.
2. Registration and cleanup guidance states the external API's thread and concurrency requirements. callbackFlow makes channel operations thread-safe; it does not make arbitrary SDK registration/unregistration thread-safe.
3. channelFlow is described as cold, like callbackFlow; there is no comparative “colder” contract.
4. The sensor example handles absent hardware by closing with an explicit failure and returning, rather than waiting forever without a registration.
5. It also checks the Boolean registration result and reports registration failure.
6. The cleanup test uses runCurrent before emission to start backgroundScope collection, then processes the immediate event and uses cancelAndJoin to wait for cleanup. advanceUntilIdle is not a substitute for deliberately starting background-only work.
7. The EditText bridge runs its upstream registration/read/cleanup on Main.immediate, following the Android View threading contract regardless of downstream collection context.

## Sources and verification limits

Checked the official [callbackFlow contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-core/kotlinx.coroutines.flow/callback-flow.html), [backgroundScope scheduling contract](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/-test-scope/background-scope.html), [SensorManager API](https://developer.android.com/reference/android/hardware/SensorManager), and [Android thread rules](https://developer.android.com/guide/components/processes-and-threads#Threads). The edited test still assumes the app-provided FakeLocationSource from the example; this audit did not compile or execute its Android-specific test fixture. SDK callback threading, cancellation races, permissions, and hardware absence need integration tests in an actual application. No device behavior or zero-error guarantee is claimed.
