# Rate Limiting

> Rate Limiting restricts the number of operations that can be performed in a given timeframe. While backends enforce rate limits to protect databases from DDoS attacks, a Staff engineer builds **Client-Side Rate Limiting** to protect the user's battery, data plan, and UI experience. Whether it's debouncing a fast-typing user in a search bar, or gracefully handling an `HTTP 429 Too Many Requests` response from a struggling backend, client-side rate limiting is a mandatory defensive mechanism on mobile.

---

## Overview

There are two sides to Rate Limiting in a mobile architecture:
1. **Server-Side Enforcement:** The backend returns an `HTTP 429` error, often with a `Retry-After` header. The Android client must parse this and halt requests.
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
**Staff Insight:** `flatMapLatest` is a form of concurrency rate-limiting. It ensures that only one network request is being processed at a time for this specific flow, instantly cancelling any inflight request if the user types again.

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

If the Android app spams the server (or if the server lowers its global rate limits during a traffic spike), the server will return an `HTTP 429 Too Many Requests`.

Well-designed APIs include a `Retry-After` header indicating how many seconds the client must wait before trying again.

### The OkHttp Interceptor Solution

You must build a global OkHttp Interceptor to handle this gracefully, rather than relying on every ViewModel to parse 429 errors manually.

```kotlin
class RateLimitInterceptor : Interceptor {
    
    // Thread-safe flag to block all outgoing requests globally
    private val isRateLimited = AtomicBoolean(false)
    private var limitEndTime = AtomicLong(0)

    override fun intercept(chain: Interceptor.Chain): Response {
        // 1. Pre-check: Are we currently locked out?
        if (isRateLimited.get() && System.currentTimeMillis() < limitEndTime.get()) {
            throw IOException("Client-side rate limit enforced. Try again later.")
        } else {
            isRateLimited.set(false) // Lockout expired
        }

        val request = chain.request()
        val response = chain.proceed(request)

        // 2. Post-check: Did the server tell us to back off?
        if (response.code == 429) {
            val retryAfterSeconds = response.header("Retry-After")?.toLongOrNull() ?: 60L // Default 1 min
            
            // Lock the client
            limitEndTime.set(System.currentTimeMillis() + (retryAfterSeconds * 1000))
            isRateLimited.set(true)
            
            // Close the response body to prevent leaks before throwing
            response.close()
            throw RateLimitException("Server returned 429. Locked for $retryAfterSeconds seconds.")
        }

        return response
    }
}
```

### UX Fallback
When this interceptor throws a `RateLimitException`, the Retrofit call in your Repository fails. Your ViewModel must catch this specific exception and display a clear UI message: *"Our servers are currently overwhelmed. Please wait 1 minute."* (And optionally disable the submit button until the timer expires).

---

## 3. UI Rate Limiting (Disabling Interactions)

Beyond network flows, rate limiting must be applied to UI interactions. A frustrated user might tap the "Submit Payment" button 15 times in 2 seconds.

While `debounce` works on streams, UI components should be explicitly disabled during critical operations.

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
| **Missing `Retry-After`** | The backend returns a 429 but doesn't include the header. The app assumes it can retry immediately, creating an infinite loop of 429s. | The client must enforce a default, aggressive exponential backoff (e.g., 60 seconds) if the server omits the header. |
| **Double Clicks bypassing UI** | A button is disabled during `Loading`, but the ViewModel takes 50ms to transition from `Idle` to `Loading`. The user clicks twice in 20ms. | Use a fast-path local boolean flag or a click-debouncer at the View layer (e.g., a custom `Modifier.debouncedClick` in Compose) to ignore clicks within 300ms of each other. |

---

## 5. Common Pitfalls

### Pitfall 1: Retrying a 429 Automatically
If you combine an OkHttp Retry Interceptor with a Rate Limit interceptor, the Retry Interceptor might see the 429 and immediately retry the request 3 times. This will instantly get your app permanently banned by the backend's WAF (Web Application Firewall) or Cloudflare layer.
*Fix:* **Never automatically retry a 429.** A 429 means "stop talking to me." The request should fail, propagate to the UI, and the user must manually initiate the action later.

### Pitfall 2: Silent Dropping via `sample`
If you use `sample(5000L)` on a flow of critical analytics events (like "Purchase Completed"), and three events fire in 5 seconds, `sample` will drop the first two completely. They are lost forever.
*Fix:* Do not rate-limit critical data via dropping. Use a `buffer` or `batch` operator to collect all events over 5 seconds, and send them in a single array payload to the server.

---

## Probing Questions

1.  **Token Bucket Algorithm:** A common backend rate-limiting algorithm is the "Token Bucket". If the backend uses this, how does it differ from a fixed-window rate limit (e.g., 100 requests per minute), and how might the Android client experience bursts of traffic differently?
2.  **Concurrency:** In the OkHttp Interceptor example above, `AtomicBoolean` and `AtomicLong` are used. If 5 coroutines make a request simultaneously and all 5 receive a 429 response at the exact same millisecond, what race conditions exist when setting the `limitEndTime`, and how does `AtomicLong` solve it?
3.  **Flow Operators:** What is the mechanical difference between `debounce`, `sample`, and `throttleFirst` (often found in RxJava)? Which one is best for preventing double-clicks on a "Buy" button?
4.  **Batching:** You need to track user scroll positions in a massive list for analytics. Firing an API call per pixel is impossible. Using Kotlin Flows, write pseudo-code to batch these scroll events into arrays of 50 events, and emit the batch to the network layer.
5.  **Offline Queues:** If the app receives a 429 with a Retry-After of 1 hour, what should the app do with critical background data (like WorkManager sync operations) during that hour? How do you instruct WorkManager to respect a dynamic 1-hour delay?

## Further Reading

- [`../patterns/circuit-breaker.md`](../patterns/circuit-breaker.md) — How rate limiting relates to full circuit tripping.
- [`../patterns/retry.md`](../patterns/retry.md) — Why 429 errors must be explicitly excluded from retry logic.
- [`../android/architecture/flow.md`](../android/architecture/flow.md) — Deep dive into the Coroutine Flow operators (`debounce`, `sample`, `flatMapLatest`).
- [`api-design-for-mobile.md`](api-design-for-mobile.md) — Designing APIs to accept batched payloads to avoid rate limits entirely.
