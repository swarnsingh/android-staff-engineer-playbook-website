# Retry Pattern

> The Retry pattern enables an application to handle transient failures by transparently retrying a failed operation. On mobile networks, transient failures (packet loss, cell tower handoffs) are guaranteed. A Staff engineer implements retries in two distinct layers: **Fast Retries** (via OkHttp interceptors for split-second blips) and **Durable Retries** (via WorkManager for prolonged offline periods). Crucially, you must understand Exponential Backoff, Jitter, and Idempotency to prevent your retries from destroying the backend infrastructure.

---

## Overview

Mobile devices are inherently disconnected. When an API call fails, it might be a transient service outage or a permanent request/configuration error, or it might be because the user drove under a bridge for 2 seconds (transient).

If you fail immediately on a transient error, the user experiences a frustrating, flaky app. If you retry aggressively, you drain the battery and DDOS your own backend. 

---

## 1. Fast Retries: The HTTP Layer (OkHttp)

Fast retries are designed to catch momentary network blips. They execute immediately in memory while the user is actively staring at a loading spinner.

### Built-in OkHttp Retries
By default, OkHttp silently recovers from certain connection failures (e.g., unreachable IP addresses, stale connection pools).
```kotlin
val client = OkHttpClient.Builder()
    .retryOnConnectionFailure(true) // Enabled by default, but good to know
    .build()
```

### Custom Exponential Backoff Interceptor

OkHttp can perform narrowly defined HTTP follow-ups as well as connection recovery; for example, its implementation can follow a 503 with `Retry-After: 0`. It is incorrect to assume it never handles 503. Test the combined transport/application attempt budget for the version you ship.

For a bounded application retry of a safe read, use suspending delay rather than sleeping an OkHttp dispatcher thread:

```kotlin
// Fragment: read must be a replay-safe read that fully consumes its response.
// The caller classifies transient transport failures; do not use for writes.
suspend fun <T> retrySafeRead(
    maxAttempts: Int = 3,
    shouldRetry: (IOException) -> Boolean,
    read: suspend () -> T,
): T {
    require(maxAttempts in 1..5)
    repeat(maxAttempts) { attempt ->
        try {
            return read()
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (failure: IOException) {
            if (attempt == maxAttempts - 1 || !shouldRetry(failure)) throw failure
        }
        val capMs = minOf(2_000L, 250L * (1L shl attempt))
        delay(Random.nextLong(capMs + 1)) // Full jitter; capped example budget.
    }
    error("Unreachable")
}
```

The caller owns cancellation and the total deadline (for example, `withTimeout` around a cancellation-cooperative Retrofit call). HTTP errors, `Retry-After`, authentication recovery and breaker-open results need endpoint-specific classification; this helper deliberately does not retry them. If implementing retries in an application interceptor, close only a response being discarded, return the final response open, and never blindly replay one-shot/duplex bodies or unsafe mutations.

## 2. Durable Retries: The Command Layer (WorkManager)

Fast retries fail if the user enters airplane mode for 2 hours. If the user tried to upload a photo, in-memory retry progress is lost when the process is terminated; it is not inherently a crash caused by the retry loop.

For these operations, we use **Durable Retries** via WorkManager. WorkManager persists the retry state to an SQLite database.

```kotlin
// Example UploadApi policy: these statuses are retryable for the same saved
// operation/payload. This is not a rule for every endpoint or HTTP failure.
fun retryableUploadStatus(status: Int): Boolean = status in setOf(408, 429, 500, 502, 503, 504)
```

```kotlin
// Fragment: inject UploadApi and UploadOperations with a WorkerFactory.
class UploadWorker(
    appContext: Context,
    params: WorkerParameters,
    private val api: UploadApi,
    private val operations: UploadOperations,
) : CoroutineWorker(appContext, params) {
    override suspend fun doWork(): Result {
        val id = inputData.getString("UPLOAD_ID") ?: return Result.failure()
        val operation = operations.load(id) ?: return Result.failure()
        operation.terminalResult?.let { return it }
        suspend fun fail(reason: String): Result {
            operations.markFailed(id, reason)
            return Result.failure()
        }
        if (runAttemptCount >= 4) return fail("Retry budget exhausted")
        if (!operations.retryIsDue(id)) return Result.retry()
        try {
            // fileId resolves to the retained app-private image; the key is persisted.
            api.uploadPhoto(operation.fileId, operation.idempotencyKey)
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (failure: HttpException) {
            if (!retryableUploadStatus(failure.code())) return fail("HTTP ${failure.code()}")
            operations.deferRetry(id, failure.response()?.headers()?.get("Retry-After"))
            return Result.retry()
        } catch (failure: IOException) {
            return Result.retry()
        }
        operations.markSucceeded(id) // Storage errors are not transport retries.
        return Result.success()
    }
}
```

`UploadOperations` is an application-owned, main-safe durable store, not a WorkManager API. `load` returns the saved file ID, immutable idempotency key and a terminal WorkManager result reconstructed from persisted status; `markFailed` commits a visible failure reason. `deferRetry` parses the endpoint's supported `Retry-After` delta-seconds or HTTP-date into a persisted not-before time; `retryIsDue` checks it before another request. Invalid or absent hints use the configured backoff. Returning `Result.retry()` alone does not implement `Retry-After`. Deferral runs count toward this example's four-run budget and can end in explicit failure; applications allowing long server delays should budget actual persisted send attempts instead. Cancellation leaves the record available for reconciliation. A local failure does not prove that no remote effect occurred; retain the identity for outcome reconciliation.

Set the network constraint and backoff, then enqueue under the saved operation's unique name:
```kotlin
// operation.id identifies an already committed upload with a retained image/key.
val uploadWorkRequest = OneTimeWorkRequestBuilder<UploadWorker>()
    .setInputData(workDataOf("UPLOAD_ID" to operation.id))
    .setConstraints(
        Constraints.Builder()
            .setRequiredNetworkType(NetworkType.CONNECTED)
            .build()
    )
    .setBackoffCriteria(
        BackoffPolicy.EXPONENTIAL, // 10s, 20s, 40s, 80s...
        WorkRequest.MIN_BACKOFF_MILLIS, // Starts at 10 seconds
        TimeUnit.MILLISECONDS
    )
    .build()

WorkManager.getInstance(context).enqueueUniqueWork(
    "upload:${operation.id}",
    ExistingWorkPolicy.KEEP,
    uploadWorkRequest,
)
```

If the backoff delay elapses while the device is offline, the work still waits for the network constraint. `KEEP` retains any unfinished work with the same name. See [Command](command.md#issuing-the-command) for how to await the enqueue result and recover a saved operation if enqueue was interrupted.

---

## 3. The Danger of Retries: Idempotency

**Retrying a non-idempotent operation is a catastrophic bug.**

Imagine a `POST /api/v1/checkout` endpoint.
1. The Android app sends the POST request.
2. The server charges the user's credit card successfully.
3. The server sends the `200 OK` response back to the phone.
4. *The user's cellular connection drops before the phone receives the response.*
5. The Android app hits an `IOException` (timeout).
6. The OkHttp Retry Interceptor blindly resends the `POST /checkout` request.
7. The user is charged a second time.

**The Fix:**
Retry only when the method and endpoint contract make repetition safe. PUT is idempotent by HTTP semantics, but POST/PATCH often need an explicit server deduplication contract. For keyed operations, persist one key with the logical operation before its first send; retries must not generate a new key. A header alone does not provide deduplication.

```kotlin
val request = originalRequest.newBuilder()
    .header("Idempotency-Key", persistedOperation.idempotencyKey)
    .build()
```
The server atomically associates the key, authenticated operation/payload and effect/outcome, and defines retention. An unchanged retry may then recover the prior outcome; it is not universally a cached 200, and retrying after the deduplication window can be a new operation.

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The Thundering Herd** | The backend goes down for 5 minutes. 100,000 apps all hit an exponential backoff timer that resolves at the exact same second, DDOSing the server when it reboots. | Add randomized **Jitter**, such as full jitter, to spread retries over time; choose and measure the policy for the workload. |
| **Battery Drain** | Configuring WorkManager with a `LINEAR` backoff of 10 seconds for an endpoint that is permanently dead. | Choose bounded attempts, deadlines and a backoff policy from the operation contract. WorkManager exposes `runAttemptCount`; it has no generic `maxRetries` builder setting. |
| **Silent Failures in UI** | The OkHttp interceptor blocks the thread for 8 seconds retrying in the background. The UI shows a frozen loading spinner, and the user force-kills the app. | Set strict read/write timeouts in OkHttp. A network call (including all retries) should either succeed or fail within a UX-acceptable timeframe (e.g., 10 seconds total). |

---

## 5. Common Pitfalls

### Pitfall 1: Retrying HTTP 4xx Errors
If an API returns `400 Bad Request` or `401 Unauthorized`, retrying it will change nothing. The payload is malformed or the token is dead. It will just fail again instantly.
*Fix:* Classify the endpoint and failure: 408/429 may be retryable, a 401 may need bounded auth recovery, and some I/O/TLS or 5xx failures are not transient. Respect `Retry-After` and stop on cancellation or a breaker-open signal.

### Pitfall 2: Confusing Retry with Circuit Breaker
A Retry pattern *adds* load to a struggling server. A Circuit Breaker *removes* load from a struggling server.
*Fix:* Retries and breakers are optional, independently justified policies. Their order determines whether the breaker counts logical operations or each attempt. The retry predicate must explicitly exclude breaker-open results; interceptor order alone does not stop retries.

---

## Probing Questions

1.  **WorkManager Constraints:** If a WorkManager task returns `Result.retry()`, but you also specified `Constraints.setRequiredNetworkType(NetworkType.CONNECTED)`, what happens if the device is offline when the exponential backoff timer hits?
2.  **OkHttp Internals:** OkHttp's `Interceptor.Chain.proceed()` is called multiple times in a retry loop. What happens if the `RequestBody` is a one-shot stream (like streaming a large file from disk)? How does OkHttp know if the body can be consumed twice?
3.  **GraphQL Retries:** GraphQL typically returns HTTP 200 OK even if the query failed, embedding the errors in the JSON payload. How do you implement a generic Retry Interceptor for a GraphQL client?
4.  **Jitter Algorithms:** Describe the difference between "Full Jitter" and "Equal Jitter". Which one provides a better distribution of load for a recovering backend system?
5.  **Coroutines:** Instead of OkHttp interceptors, you can implement retries at the Kotlin Flow layer using the `retryWhen { cause, attempt -> }` operator. What are the architectural tradeoffs of retrying in the Domain layer (Flow) versus the Data layer (OkHttp)?

## Answer Key

1. **WorkManager Constraints: If a WorkManager task returns `Result.retry()`, but you also specified `Constraints.setRequiredNetworkType(NetworkType.CONNECTED)`, what happens if the device is offline when the exponential backoff timer hits?**
   WorkManager will wait. The backoff timer determines the *earliest* time the work can run. If constraints are not met at that time, execution is delayed until the device regains connectivity.
2. **OkHttp Internals: What happens if the `RequestBody` is a one-shot stream? How does OkHttp know if the body can be consumed twice?**
   OkHttp checks `RequestBody.isOneShot()`. If it returns `true` (e.g., a streaming request), OkHttp will not retry the request automatically because the stream cannot be rewound. A manual retry may send empty/partial data or fail according to the body implementation; it is not guaranteed to throw. Custom interceptors must enforce replay safety themselves.
3. **GraphQL Retries: How do you implement a generic Retry Interceptor for a GraphQL client?**
   GraphQL can return 200 with partial data/errors, or non-200 for transport/request failures. A network interceptor could inspect bytes, but a GraphQL-aware layer can preserve partial data, error paths and mutation replay rules. Classify the failure there rather than retrying every response containing errors.
4. **Jitter Algorithms: Describe the difference between "Full Jitter" and "Equal Jitter".**
   Full Jitter picks a random value between 0 and the current backoff maximum (`random(0, backoff)`). Equal Jitter uses half the backoff plus a random value between 0 and half the backoff (`backoff/2 + random(0, backoff/2)`). Equal Jitter enforces a half-cap minimum delay. Neither is universally best; AWS's cited contention experiment found Full Jitter did less work than Equal Jitter. Evaluate latency and load under the actual workload.
5. **Coroutines: What are the architectural tradeoffs of retrying in the Domain layer (Flow) versus the Data layer (OkHttp)?**
   Retrying in the Data layer (OkHttp) is centralized, transparent to the UI, and great for standard network blips. Retrying in the Domain layer (Flow) allows for business-logic-aware retries (e.g., prompting the user, refreshing tokens, or falling back to a cache), but scatters retry logic across multiple Use Cases.

## Further Reading

- [`circuit-breaker.md`](circuit-breaker.md) — The protective layer that must accompany any aggressive retry strategy.
- [`command.md`](command.md) — How WorkManager encapsulates the retry payload safely.
- [`../distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — Deep dive into the backend mechanics of `Idempotency-Key`.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Where to place the retry interceptor in the OkHttp chain.
- [HTTP idempotent methods and automatic retry](https://www.rfc-editor.org/rfc/rfc9110.html#section-9.2.2)
- [OkHttp actual follow-up implementation](https://raw.githubusercontent.com/square/okhttp/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/internal/http/RetryAndFollowUpInterceptor.kt)
- [AWS original Full/Equal Jitter comparison](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
- [WorkManager attempts, constraints and backoff](https://developer.android.com/develop/background-work/background-tasks/persistent/getting-started/define-work)
- [WorkManager unique work and KEEP](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work#conflict-resolution)
- [GraphQL over HTTP status semantics](https://graphql.github.io/graphql-over-http/draft/#sec-Status-Codes)
- [Coroutine cancellation semantics](https://kotlinlang.org/docs/cancellation-and-timeouts.html)
- [Retrofit suspending body calls throw HttpException for HTTP errors](https://raw.githubusercontent.com/square/retrofit/trunk/retrofit/src/main/java/retrofit2/KotlinExtensions.kt)
- [HTTP Retry-After delay/date semantics](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3)
