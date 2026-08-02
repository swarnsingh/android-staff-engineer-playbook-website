# Rate Limiting

> Rate limiting restricts operations over an interval. Backends enforce quotas and overload policy; mobile clients may also shape requests to protect product correctness, energy, data use, and UX. Search debouncing, duplicate-submit protection, and handling `HTTP 429 Too Many Requests` are distinct mechanisms whose scope depends on the operation and server contract.

---

## Overview

There are two sides to Rate Limiting in a mobile architecture:
1. **Server-Side Enforcement:** A backend can return `429`, optionally with `Retry-After`. The client applies the hint to the correct rate-limit bucket and retries only under its safety, deadline, and attempt policy.
2. **Client-Side Throttling (Debounce/Throttle):** The Android app intentionally delays or drops user input to prevent generating excessive network requests in the first place.

---

## 1. Client-Side Throttling (Coroutines & Flow)

The most common rate-limiting scenario on mobile is a "Search-as-you-type" feature. If the user types "S - T - A - F - F" in 500 milliseconds, you do not want to fire 5 separate API calls. 

We use Kotlin `Flow` operators to rate-limit the input.

### Debounce
`debounce` waits for a period of *silence* before emitting the latest value. If the user keeps typing, the timer resets.

```kotlin
// In the ViewModel
private val _searchQuery = MutableStateFlow("")
val searchQuery = _searchQuery.asStateFlow()

val searchResults = _searchQuery
    .debounce(300L) // Wait for 300ms of silence
    .filter { it.length >= 3 } // Don't search for 1 or 2 characters
    .distinctUntilChanged() // Don't search if the query hasn't actually changed
    .flatMapLatest { query ->
        // Cancels the previous API call if a new one starts
        api.search(query) 
    }
    .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5000), emptyList())
```
**Staff Insight:** `flatMapLatest` cancels collection of the previous inner flow when a new query arrives. It can reduce obsolete work when the networking layer cooperates with cancellation, but it is not a server rate-limit guarantee and brief overlap may occur while cancellation propagates.

### Throttle (Sample)
If you are tracking a user's location via GPS, you might receive updates every 10 milliseconds. You only want to send an update to the server once every 5 seconds. `sample` (throttling) emits the latest value at fixed intervals, regardless of silence.

```kotlin
val locationUpdates = gpsTracker.locationFlow
    .sample(5000L) // Take the latest location every 5 seconds
    .onEach { location ->
        api.sendLocation(location)
    }
```

---

## 2. Handling Server-Side Rate Limits (HTTP 429)

When a client exceeds a server's applicable request policy, the server may return `HTTP 429 Too Many Requests`; other overload, quota, or gateway policies can surface different responses.

An API may include `Retry-After` as either delay-seconds or an HTTP-date. Preserve the server's embargo for the affected bucket. If that time exceeds the client's automatic-retry budget, surface or abandon the retry instead of shortening the embargo.

### The OkHttp Interceptor Solution

Centralize `429` handling at the appropriate client, host, or API scope rather than making every ViewModel parse it independently. The retry policy still needs request safety, deadlines, cancellation, and domain-specific rate-limit boundaries.

```kotlin
fun interface HttpDateParser {
    // Production implementations accept IMF-fixdate plus the obsolete RFC 850
    // and asctime forms that HTTP recipients are required to recognize.
    fun parseEpochMillis(value: String): Long?
}

class RateLimitException(
    val bucket: String,
    val retryAtElapsedRealtimeMillis: Long,
) : IOException("Rate-limited bucket: $bucket")

class RateLimitInterceptor(
    private val httpDateParser: HttpDateParser,
) : Interceptor {
    // This example scopes a bucket by origin. If the API publishes a finer
    // route, user, resource, or quota-bucket key, use that identity instead.
    private val limitEndByOrigin = ConcurrentHashMap<String, AtomicLong>()

    private fun delayMillis(value: String?, nowEpochMillis: Long): Long {
        val rawValue = value?.trim()
        val delayDigits = rawValue?.takeIf { candidate ->
            candidate.isNotEmpty() && candidate.all { it in '0'..'9' }
        }
        if (delayDigits != null) {
            val normalizedDigits = delayDigits.trimStart('0').ifEmpty { "0" }
            // A syntactically valid value beyond Long range represents a wait
            // longer than this process can schedule, so preserve the embargo
            // by saturating instead of using the invalid-header fallback.
            val delaySeconds = normalizedDigits.toLongOrNull() ?: Long.MAX_VALUE
            if (delaySeconds == 0L) return 0L
            return if (delaySeconds > Long.MAX_VALUE / 1_000L) {
                Long.MAX_VALUE
            } else {
                delaySeconds * 1_000L
            }
        }

        val httpDateMillis = rawValue?.let(httpDateParser::parseEpochMillis)
        return if (httpDateMillis != null) {
            if (httpDateMillis <= nowEpochMillis) 0L
            else httpDateMillis - nowEpochMillis
        } else {
            60_000L // Local first-delay policy for an absent/invalid header.
        }
    }

    private fun addDelay(baseMillis: Long, delayMillis: Long): Long {
        return if (delayMillis > Long.MAX_VALUE - baseMillis) {
            Long.MAX_VALUE
        } else {
            baseMillis + delayMillis
        }
    }

    private fun preserveLongestDeadline(origin: String, incoming: Long): Long {
        // putIfAbsent and compareAndSet work on older Android API levels; this
        // avoids relying on API-24 ConcurrentMap/AtomicLong convenience methods.
        val candidate = AtomicLong(0L)
        val deadline = limitEndByOrigin.putIfAbsent(origin, candidate) ?: candidate

        while (true) {
            val current = deadline.get()
            if (current >= incoming) return current
            if (deadline.compareAndSet(current, incoming)) return incoming
        }
    }

    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        val origin = request.url.run { "$scheme://$host:$port" }
        val nowMillis = android.os.SystemClock.elapsedRealtime()
        val currentDeadline = limitEndByOrigin[origin]?.get() ?: 0L

        // 1. Pre-check only the bucket associated with this request.
        if (nowMillis < currentDeadline) {
            throw RateLimitException(origin, currentDeadline)
        }

        val response = chain.proceed(request)

        // 2. Post-check: Did the server tell us to back off?
        if (response.code == 429) {
            val nowEpochMillis = System.currentTimeMillis()
            val nowElapsedMillis = android.os.SystemClock.elapsedRealtime()
            val deadlineMillis = addDelay(
                nowElapsedMillis,
                delayMillis(response.header("Retry-After"), nowEpochMillis),
            )
            // Concurrent responses must not shorten an existing longer delay.
            val appliedDeadline = preserveLongestDeadline(origin, deadlineMillis)
            // Close the response body to prevent leaks before throwing
            response.close()
            throw RateLimitException(origin, appliedDeadline)
        }

        return response
    }
}
```

### UX Fallback
Map `RateLimitException` separately from generic connectivity failures so a generic retry interceptor does not immediately replay it. Use its monotonic deadline only for in-process comparisons and derive the remaining duration for UI. Disable controls whose requests map to the affected bucket; this origin-scoped sample may cover several actions, so use a finer server-published bucket identity when action-level isolation is required. If timing should not be exposed, use a nonnumeric “Try again later” message.

---

## 3. UI Rate Limiting (Disabling Interactions)

Some UI operations need duplicate-submission protection. A payment action, for example, may receive several taps before its visible state updates.

For a non-idempotent or mutually exclusive operation, transition state atomically and disable or otherwise guard the relevant control while the operation is active. Repeatable actions may use a different interaction policy.

```kotlin
@Composable
fun CheckoutButton(
    uiState: CheckoutUiState,
    onSubmit: () -> Unit
) {
    // 1. Visual indication of loading
    // 2. Physical disablement of the button
    Button(
        onClick = onSubmit,
        enabled = uiState !is CheckoutUiState.Loading 
    ) {
        if (uiState is CheckoutUiState.Loading) {
            CircularProgressIndicator()
        } else {
            Text("Submit Payment")
        }
    }
}
```

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **Global 429 Lockout** | Using a single global interceptor to block *all* network traffic when an image CDN returns a 429, preventing the user from using the core API. | Implement domain-specific rate limits. Keep a map of `[Domain -> LockoutTime]` in the interceptor, so hitting a limit on `images.example.com` doesn't block `api.example.com`. |
| **Missing or invalid `Retry-After`** | The client immediately repeats an otherwise eligible request. | This interceptor records a bounded first bucket embargo. A separate retry scheduler owns attempt count and capped exponential backoff with jitter for later replay-safe attempts; it still enforces deadlines and cancellation. |
| **Double Clicks bypassing UI** | A button is disabled during `Loading`, but the ViewModel takes 50ms to transition from `Idle` to `Loading`. The user clicks twice in 20ms. | Use a fast-path local boolean flag or a click-debouncer at the View layer (e.g., a custom `Modifier.debouncedClick` in Compose) to ignore clicks within 300ms of each other. |

---

## 5. Common Pitfalls

### Pitfall 1: Retrying a 429 Immediately
A generic retry interceptor can turn one `429 Too Many Requests` into several immediate requests, worsening overload and extending a server-side lockout.

*Fix:* Treat `429` as a retryable response only under an explicit policy. Honor `Retry-After` when present; otherwise let a retry scheduler apply capped exponential backoff with jitter across later attempts. Retry only when the operation is safe to repeat, the request deadline and attempt budget allow it, and cancellation has not occurred. Queue durable background work locally and reschedule it; foreground UI may expose a retry action rather than blocking the thread. RFC 6585 permits a `429` response to include `Retry-After`; it does not require either unconditional automatic retry or manual-only retry.

### Pitfall 2: Silent Dropping via `sample`
If `sample(5000L)` is the only consumer of three critical events emitted inside one window, intermediate values are not forwarded by that sampled flow. Without a separate durable event store or delivery path, those events are lost to this analytics pipeline.
*Fix:* Do not rate-limit critical data by dropping. Persist events first, then use an explicit size/time-window accumulator (or a verified batching operator) that emits `List<Event>` and flushes remainders. `buffer()` can decouple producer and consumer but does not itself create batches.

---

## Probing Questions

1.  **Token Bucket Algorithm:** A common backend rate-limiting algorithm is the "Token Bucket". If the backend uses this, how does it differ from a fixed-window rate limit (e.g., 100 requests per minute), and how might the Android client experience bursts of traffic differently?
2.  **Concurrency:** If concurrent `429` responses for one bucket contain different deadlines, why is an atomic `set()` insufficient, and how does atomic max/CAS prevent a shorter response from reducing the active delay?
3.  **Flow Operators:** What is the mechanical difference between `debounce`, `sample`, and `throttleFirst` (often found in RxJava)? Which one is best for preventing double-clicks on a "Buy" button?
4.  **Batching:** You need to track user scroll positions in a massive list for analytics. Firing an API call per pixel is impossible. Using Kotlin Flows, write pseudo-code to batch these scroll events into arrays of 50 events, and emit the batch to the network layer.
5.  **Offline Queues:** If the app receives a 429 with a Retry-After of 1 hour, what should the app do with critical background data (like WorkManager sync operations) during that hour? How do you instruct WorkManager to respect a dynamic 1-hour delay?

## Answer Key

1. **Token Bucket Algorithm: A common backend rate-limiting algorithm is the "Token Bucket". If the backend uses this, how does it differ from a fixed-window rate limit (e.g., 100 requests per minute), and how might the Android client experience bursts of traffic differently?**
   A fixed-window resets strictly at the top of the minute, which can cause sudden spikes. A token bucket gradually refills tokens; it allows short, rapid bursts of traffic (up to the bucket's capacity) and then smoothly throttles subsequent requests until tokens replenish.
2. **If concurrent `429` responses for one bucket contain different deadlines, why is an atomic `set()` insufficient, and how does atomic max/CAS prevent a shorter response from reducing the active delay?**
   Separate atomic writes are not torn, but last-writer-wins can replace a longer deadline with a shorter one. An `accumulateAndGet(maxOf)` or compare-and-set loop preserves the maximum deadline atomically for that bucket; deriving limited state from that one value avoids a separate flag/time race.
3. **Flow Operators: What is the mechanical difference between `debounce`, `sample`, and `throttleFirst` (often found in RxJava)? Which one is best for preventing double-clicks on a "Buy" button?**
   `debounce` waits for silence before emitting; `sample` emits the most recent value at fixed intervals; `throttleFirst` emits immediately, then ignores subsequent events for a duration. `throttleFirst` (or a custom click-debouncer) is best for preventing double-clicks.
4. **Batching: You need to track user scroll positions in a massive list for analytics. Firing an API call per pixel is impossible. Using Kotlin Flows, write pseudo-code to batch these scroll events into arrays of 50 events, and emit the batch to the network layer.**
   Use a verified batching operator or an explicit accumulator that emits at 50 items, flushes a partial batch on its time/lifecycle boundary, and persists data that must survive process death. Pseudo-code: `scrollFlow.batch(size = 50, maxWait = 5.seconds).onEach { batch -> outbox.enqueue(batch) }.launchIn(scope)`. `buffer()` may provide backpressure capacity around this pipeline but does not form arrays.
5. **Offline Queues: If the app receives a 429 with a Retry-After of 1 hour, what should the app do with critical background data (like WorkManager sync operations) during that hour? How do you instruct WorkManager to respect a dynamic 1-hour delay?**
   Persist the payload, bucket, attempt state, and a durable epoch deadline or original server retry metadata—not the in-process `elapsedRealtime()` absolute value, which resets on reboot. On restore, derive a nonnegative delay from the durable value (with a conservative policy if wall-clock trust matters), build and enqueue/replace a unique `OneTimeWorkRequest` with `setInitialDelay`, and return promptly rather than sleeping inside a worker. Use `Result.retry()` only when its configured backoff matches the server/client policy.

## Further Reading

- [`../patterns/circuit-breaker.md`](../patterns/circuit-breaker.md) — How rate limiting relates to full circuit tripping.
- [`../patterns/retry.md`](../patterns/retry.md) — How bounded retry, idempotency, deadlines, backoff, and jitter interact.
- [RFC 6585 §4: 429 Too Many Requests](https://www.rfc-editor.org/rfc/rfc6585.html#section-4) — The status code and optional `Retry-After` guidance.
- [RFC 9110 §10.2.3: Retry-After](https://www.rfc-editor.org/rfc/rfc9110.html#section-10.2.3) — Header semantics.
- [`../android/architecture/flow.md`](../android/architecture/flow.md) — Deep dive into the Coroutine Flow operators (`debounce`, `sample`, `flatMapLatest`).
- [`api-design-for-mobile.md`](api-design-for-mobile.md) — Designing APIs to accept batched payloads to avoid rate limits entirely.
