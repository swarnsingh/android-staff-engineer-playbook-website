# Retry Pattern

> The Retry pattern enables an application to handle transient failures by transparently retrying a failed operation. On mobile networks, transient failures (packet loss, cell tower handoffs) are guaranteed. A Staff engineer implements retries in two distinct layers: **Fast Retries** (via OkHttp interceptors for split-second blips) and **Durable Retries** (via WorkManager for prolonged offline periods). Crucially, you must understand Exponential Backoff, Jitter, and Idempotency to prevent your retries from destroying the backend infrastructure.

---

## Overview

Mobile devices are inherently disconnected. When an API call fails, it might be because the server is down (fatal), or it might be because the user drove under a bridge for 2 seconds (transient).

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
OkHttp's built-in retry does not handle HTTP 503 (Service Unavailable) or 504 (Gateway Timeout) errors. We implement a custom interceptor with **Exponential Backoff** (waiting longer between each attempt) and **Jitter** (adding randomness to prevent thundering herds).

```kotlin
class RetryInterceptor(private val maxRetries: Int = 3) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        var response: Response? = null
        var tryCount = 0
        
        while (tryCount < maxRetries) {
            try {
                response = chain.proceed(request)
                
                // If success or a client error (4xx), return immediately. No need to retry.
                if (response.isSuccessful || response.code in 400..499) {
                    return response
                }
                
                // If 5xx (Server Error), close the response body to prevent leaks before retrying
                response.close()
                
            } catch (e: IOException) {
                // SocketTimeout or Connection drop. We will retry.
            }
            
            tryCount++
            if (tryCount < maxRetries) {
                // Exponential Backoff with Jitter: 1s, 2s, 4s + random ms
                val backoff = 1000L * (2.0.pow(tryCount - 1)).toLong()
                val jitter = (Math.random() * 500).toLong()
                Thread.sleep(backoff + jitter)
            }
        }
        
        // If we exhausted retries and still have a response, return the last failure
        // Otherwise, throw an IOException indicating ultimate network failure
        return response ?: throw IOException("Failed after $maxRetries retries")
    }
}
```

---

## 2. Durable Retries: The Command Layer (WorkManager)

Fast retries fail if the user enters airplane mode for 2 hours. If the user tried to upload a photo, an in-memory OkHttp retry loop will crash when the Android OS kills the app in the background.

For these operations, we use **Durable Retries** via WorkManager. WorkManager persists the retry state to an SQLite database.

```kotlin
class UploadWorker(appContext: Context, params: WorkerParameters) :
    CoroutineWorker(appContext, params) {

    override suspend fun doWork(): Result {
        return try {
            api.uploadPhoto(inputData.getString("URI")!!)
            Result.success()
        } catch (e: IOException) {
            // Tells WorkManager to use its built-in Backoff Policy
            Result.retry()
        } catch (e: HttpException) {
            if (e.code() >= 500) Result.retry() else Result.failure() // Don't retry 400 Bad Request
        }
    }
}
```

You configure the backoff policy when enqueuing the work:
```kotlin
val uploadWorkRequest = OneTimeWorkRequestBuilder<UploadWorker>()
    .setBackoffCriteria(
        BackoffPolicy.EXPONENTIAL, // 10s, 20s, 40s, 80s...
        WorkRequest.MIN_BACKOFF_MILLIS, // Starts at 10 seconds
        TimeUnit.MILLISECONDS
    )
    .build()
```

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
Any API that creates or mutates data (`POST`, `PATCH`, `PUT`) must be designed idempotently if it is going to be retried. The Android client must generate a unique `Idempotency-Key` (a UUID) and send it as an HTTP header.

```kotlin
val request = originalRequest.newBuilder()
    .header("Idempotency-Key", UUID.randomUUID().toString())
    .build()
```
When the server receives the retry, it sees the same UUID, realizes it already charged the card, and simply returns the cached `200 OK` response without double-charging.

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The Thundering Herd** | The backend goes down for 5 minutes. 100,000 apps all hit an exponential backoff timer that resolves at the exact same second, DDOSing the server when it reboots. | Always add **Jitter** (a random offset like +/- 10%) to your backoff calculations so retries spread out over time. |
| **Battery Drain** | Configuring WorkManager with a `LINEAR` backoff of 10 seconds for an endpoint that is permanently dead. | Always use `EXPONENTIAL` backoff, and set a hard maximum on `maxRetries`. |
| **Silent Failures in UI** | The OkHttp interceptor blocks the thread for 8 seconds retrying in the background. The UI shows a frozen loading spinner, and the user force-kills the app. | Set strict read/write timeouts in OkHttp. A network call (including all retries) should either succeed or fail within a UX-acceptable timeframe (e.g., 10 seconds total). |

---

## 5. Common Pitfalls

### Pitfall 1: Retrying HTTP 4xx Errors
If an API returns `400 Bad Request` or `401 Unauthorized`, retrying it will change nothing. The payload is malformed or the token is dead. It will just fail again instantly.
*Fix:* Only retry on `IOException` (network drop) or HTTP `5xx` (server-side struggle).

### Pitfall 2: Confusing Retry with Circuit Breaker
A Retry pattern *adds* load to a struggling server. A Circuit Breaker *removes* load from a struggling server.
*Fix:* They must be used together. The Circuit Breaker interceptor must sit *below* the Retry interceptor. If the breaker trips, it throws an immediate exception, short-circuiting the Retry loop and failing fast.

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
   OkHttp checks `RequestBody.isOneShot()`. If it returns `true` (e.g., a streaming request), OkHttp will not retry the request automatically because the stream cannot be rewound. Attempting to manually consume a one-shot stream twice in an interceptor will throw an exception.
3. **GraphQL Retries: How do you implement a generic Retry Interceptor for a GraphQL client?**
   Since GraphQL returns HTTP 200, an OkHttp interceptor is ineffective because it only sees the HTTP status. You must implement the retry logic at the GraphQL client layer (e.g., Apollo's retry interceptors) where the JSON payload can be inspected for network or server errors.
4. **Jitter Algorithms: Describe the difference between "Full Jitter" and "Equal Jitter".**
   Full Jitter picks a random value between 0 and the current backoff maximum (`random(0, backoff)`). Equal Jitter uses half the backoff plus a random value between 0 and half the backoff (`backoff/2 + random(0, backoff/2)`). Equal Jitter prevents very short retries, ensuring a more stable, wider distribution of load.
5. **Coroutines: What are the architectural tradeoffs of retrying in the Domain layer (Flow) versus the Data layer (OkHttp)?**
   Retrying in the Data layer (OkHttp) is centralized, transparent to the UI, and great for standard network blips. Retrying in the Domain layer (Flow) allows for business-logic-aware retries (e.g., prompting the user, refreshing tokens, or falling back to a cache), but scatters retry logic across multiple Use Cases.

## Further Reading

- [`circuit-breaker.md`](circuit-breaker.md) — The protective layer that must accompany any aggressive retry strategy.
- [`command.md`](command.md) — How WorkManager encapsulates the retry payload safely.
- [`../distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — Deep dive into the backend mechanics of `Idempotency-Key`.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Where to place the retry interceptor in the OkHttp chain.
