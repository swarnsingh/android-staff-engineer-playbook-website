# Retry Pattern

## Overview

The Retry pattern enables an application to handle transient failures by transparently retrying a failed operation. In mobile development, where network connections drop in elevators and APIs sporadically timeout, it is the most fundamental mechanism for providing a seamless user experience.

## Why It Exists

Mobile networks are inherently hostile. A 503 Service Unavailable, an `UnknownHostException` during a tunnel handover, or a simple timeout are expected daily occurrences. If you surface an error to the user the *first* time a request fails, your app will feel broken. Retrying hides the volatility of the network from the user.

## Historical Context

A core resilience engineering pattern. In the era of Java `Thread.sleep()`, implementing asynchronous retry logic with backoff was a complex web of callbacks and timers. Today, Kotlin Coroutines have reduced advanced retry logic (with exponential backoff and jitter) to a few lines of highly readable, non-blocking code.

## First Principles

1.  **Idempotency:** You can only safely retry an operation if executing it multiple times has the same effect as executing it once. (You don't want to charge a credit card three times).
2.  **Backoff:** Immediate retries usually fail for the same reason the first attempt failed. You must wait.
3.  **Jitter:** If 10,000 devices lose connection and regain it simultaneously, you must randomize their retry delays to avoid a thundering herd.

## Mental Model

Think of trying to unlock a sticky door. 
- You turn the key, it doesn't work (Attempt 1). 
- You don't instantly violently shake the handle. You jiggle it slightly, pause, and try again (Attempt 2 - linear backoff). 
- If it still doesn't work, you step back, look at the lock, apply some WD-40, and try again (Attempt 3 - exponential backoff). 
- If the door is bricked up (a 404 Not Found), you stop trying entirely.

## Internal Mechanics

A robust Retry implementation requires three components: the loop, the delay (backoff), and the condition (should we retry?).

### The Kotlin Coroutine Implementation

```kotlin
/**
 * Retries the given [block] up to [times] times.
 * Applies exponential backoff with jitter.
 */
suspend fun <T> retryWithBackoff(
    times: Int = 3,
    initialDelayMs: Long = 1000,
    maxDelayMs: Long = 10_000,
    factor: Double = 2.0,
    block: suspend () -> T
): T {
    var currentDelay = initialDelayMs
    repeat(times - 1) { attempt ->
        try {
            return block() // If successful, exit the function immediately
        } catch (e: Exception) {
            // Check if the error is transient. Don't retry 404s or 401s.
            if (!e.isTransient()) {
                throw e
            }
            
            // Log the retry
            println("Attempt ${attempt + 1} failed. Retrying in ${currentDelay}ms")
        }
        
        // Wait before the next attempt
        delay(currentDelay)
        
        // Calculate the next delay: Exponential + Jitter
        // Jitter is a random +/- 20% variance
        val nextDelay = (currentDelay * factor).toLong()
        val jitter = (nextDelay * 0.2 * Math.random()).toLong() - (nextDelay * 0.1).toLong()
        currentDelay = (nextDelay + jitter).coerceAtMost(maxDelayMs)
    }
    
    // Final attempt outside the loop so the exception bubbles up naturally
    return block() 
}

// Extension to determine retryability
fun Exception.isTransient(): Boolean {
    return this is IOException || 
           (this is HttpException && this.code() in 500..599)
}
```

## Architecture

```mermaid
flowchart TD
    Start[Start Operation] --> Attempt{Attempt < Max?}
    Attempt -->|Yes| Execute[Execute Block]
    Attempt -->|No| Fail[Throw Exception]
    
    Execute --> Success{Success?}
    Success -->|Yes| Return[Return Result]
    Success -->|No| CheckError{Is Error\nTransient?}
    
    CheckError -->|No| Fail
    CheckError -->|Yes| Backoff[Calculate Delay\n(Backoff + Jitter)]
    Backoff --> Sleep[Wait (delay)]
    Sleep --> Attempt
```

## Production Example

In OkHttp, the `RetryAndFollowUpInterceptor` is built-in, but it mostly handles connection failures and redirects, not application-level 5xx retries with backoff. You usually write a custom Interceptor or wrap your Repository calls.

```kotlin
class ResilientUserRepository(private val api: UserApi) {

    suspend fun fetchUserProfile(userId: String): UserProfile {
        // Wrap the raw API call in the retry logic
        return retryWithBackoff(times = 3, initialDelayMs = 500) {
            api.getUser(userId)
        }
    }
}
```

For background tasks, `WorkManager` handles retry natively. You just return `Result.retry()` and configure the WorkRequest:

```kotlin
val workRequest = OneTimeWorkRequestBuilder<SyncWorker>()
    .setBackoffCriteria(
        BackoffPolicy.EXPONENTIAL, 
        WorkRequest.MIN_BACKOFF_MILLIS, // 10 seconds
        TimeUnit.MILLISECONDS
    )
    .build()
```

## Tradeoffs

**Advantages**
- **User Experience:** Dramatically reduces the number of error screens shown to users.
- **Resilience:** Gracefully handles the chaos of mobile networks.

**Disadvantages**
- **Latency Masking:** If an API is consistently failing and succeeding on the 3rd attempt, the user waits 5 seconds for data. The Retry pattern hides this server degradation from your crash reporting (unless you explicitly log retries).
- **Resource Amplification:** If your app makes 5 requests on startup, and they all fail and retry 3 times, your app just made 15 requests, potentially exacerbating the server issue.

## Failure Modes

- **Retrying Non-Idempotent Operations:** Wrapping `POST /checkout` in a generic retry block. If the first request succeeds on the server but the response drops on the way back, the retry will charge the user a second time. (Fix: Implement Idempotency Keys).
- **The Missing Jitter:** Implementing exponential backoff (`delay = 2^attempt`) without randomness. If a popular backend service goes down, 100,000 devices fail at `T=0`. They all retry exactly at `T=2`, bringing the recovering server down again. They all retry exactly at `T=4`, etc. Jitter smears the load.
- **Infinite Loops:** Using a `while(true)` loop for retries without a maximum attempt cap or a maximum duration cap.
- **Retrying Fatal Errors:** Retrying a 401 Unauthorized or a 400 Bad Request. The server told you exactly why it failed; trying the exact same request again is a waste of resources.

## Staff Engineer Thinking

When reviewing resilience code, a Staff engineer focuses on the systemic impact:

1.  **Is it combined with a Circuit Breaker?** Retry without a Circuit Breaker is dangerous. If the server is definitively dead, Retrying 3 times with exponential backoff just wastes battery and blocks the UI thread/coroutine for 10 seconds before finally surfacing the error. The Circuit Breaker should wrap the Retry.
2.  **Are we logging retries?** A successful operation on the 3rd retry is a success to the user, but a failure to the platform. If we don't log `retry_count` in our telemetry, we are blind to degrading backend performance.
3.  **Is the backoff configured correctly?** A 10-second initial backoff on a UI-blocking fetch is terrible UX. A 100ms backoff on a background sync is too aggressive. Backoff policies must be context-aware.

## Common Misconceptions

- **"RxJava `retryWhen` is better than Coroutines."** They solve the same problem. Coroutines are generally preferred now because a simple `try/catch` inside a `repeat` loop is significantly easier to read and debug than a complex reactive chain of `Observable.timer` and `flatMap`.
- **"I don't need retry if I have offline caching."** False. Offline caching serves stale data. You still need to retry the network request to get fresh data to update the cache.

## Probing Questions

1.  Explain why "Jitter" is just as important as "Exponential Backoff".
2.  What is Idempotency, and why is it a strict prerequisite for applying the Retry pattern to a POST/PUT request?
3.  Write the pseudo-code for a Coroutine retry function that gives up early if it receives an `IllegalArgumentException`.
4.  If you are using both a Circuit Breaker and a Retry pattern, which one should wrap the other? Why?
5.  How does Android's `WorkManager` handle retries internally? What happens if the device is rebooted during a backoff period?
6.  Why is it an anti-pattern to retry a 404 (Not Found) HTTP response?
7.  What is the "Thundering Herd" problem, and how does the Retry pattern (if implemented poorly) cause it?
8.  How do you ensure that a long-running retry loop doesn't leak memory if the user navigates away from the screen? (Hint: Coroutine cancellation).
9.  Should you surface "Retrying..." to the UI, or keep it completely transparent to the user? Defend your UX choice.
10. How do you distinguish between a network failure (where retry makes sense) and a server-side crash (where retry might not make sense) in OkHttp?

## Further Reading

- [`circuit-breaker.md`](circuit-breaker.md) — The complementary pattern. Retry protects the user; Circuit Breaker protects the system.
- [`../distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — Mandatory reading before applying retries to mutating requests.
- AWS Architecture Blog: [Exponential Backoff And Jitter](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/)
