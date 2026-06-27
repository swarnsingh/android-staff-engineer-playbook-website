# Rate Limiting (HTTP 429)

## Overview

A Junior Engineer writes a `while(true)` loop to retry a failed network request, assuming the network just had a temporary hiccup.

A Staff Engineer understands that if 1 million app instances all run a `while(true)` retry loop simultaneously, they will launch a Distributed Denial of Service (DDoS) attack against their own company's servers, bringing down the entire backend infrastructure and costing the company millions of dollars.

**Rate Limiting** is the defensive mechanism backend servers use to protect themselves from malicious actors and poorly written mobile apps. A mobile application must be meticulously designed to respect Rate Limits (`HTTP 429 Too Many Requests`), implement Exponential Backoff, and utilize Jitter to prevent accidental self-DDoS.

## Why It Matters

Imagine a highly anticipated product drop (e.g., concert tickets). 500,000 users open the Android app at exactly 12:00 PM. 
They all hit `GET /tickets`.
The backend database cannot handle 500,000 queries a second. The API Gateway detects the surge and instantly Rate Limits 490,000 of the users, returning `HTTP 429`.

- **Bad App Design:** The 490,000 apps see a failure, immediately retry at 12:00:01 PM. The server returns 429 again. The apps retry at 12:00:02 PM. The Load Balancer melts.
- **Staff App Design:** The 490,000 apps read the `Retry-After: 30` header in the HTTP 429 response. They wait exactly 30 seconds. Furthermore, they add "Jitter", so 10,000 apps retry at 30s, 10,000 at 31s, 10,000 at 32s, smoothing out the massive spike into a manageable wave.

## Historical Context

- **The Slashdot Effect / Reddit Hug of Death:** In the early 2000s, if a popular website linked to a small website, the sudden influx of traffic would crash the small server.
- **Throttling vs Rate Limiting:** Throttling slows down the speed of the response (giving you bytes slower). Rate Limiting outright rejects the request (giving you an error).
- **HTTP 429 (2012):** RFC 6585 officially introduced the `429 Too Many Requests` status code. Before this, servers incorrectly used `503 Service Unavailable` or `400 Bad Request`.

## First Principles

1.  **Rate Limit (HTTP 429):** The server explicitly rejecting a request because the client has sent too many in a given timeframe (e.g., Max 100 requests per minute).
2.  **`Retry-After` Header:** An HTTP header sent alongside the 429 response, telling the client exactly how many seconds to wait before trying again.
3.  **Exponential Backoff:** If the server doesn't provide a `Retry-After` header, the client must guess. It waits 1s, then 2s, then 4s, then 8s, up to a maximum limit.
4.  **Jitter:** Adding a random mathematical variance to the backoff time (e.g., waiting 4.2 seconds instead of exactly 4.0 seconds) to prevent thousands of clients from retrying at the exact same millisecond.

## Mental Model

Think of Rate Limiting as a **Bouncer at an Exclusive Club**.
- **The Limit:** The club can only hold 100 people.
- **Rate Limiting (HTTP 429):** You walk up to the door. The Bouncer puts his hand up and says, "We are full."
- **Retry-After:** The Bouncer adds, "Wait in line for 10 minutes, then ask me again."
- **Exponential Backoff:** If the Bouncer doesn't give you a time, you ask. He says no. You wait 1 minute. Ask again. He says no. You wait 2 minutes. Ask again. You wait 4 minutes.
- **Jitter:** Instead of the entire line of 50 people asking the bouncer at the exact same second (overwhelming him), everyone agrees to wait a random amount of seconds between asks.

## Internal Mechanics

### 1. The HTTP 429 Response

When an API Gateway (like AWS API Gateway, Cloudflare, or NGINX) rate-limits a client, it usually includes headers indicating the current status of the client's "Token Bucket."

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1672531200
Retry-After: 45

{
  "error": "Rate limit exceeded. Try again in 45 seconds."
}
```

The Mobile App's network interceptor must catch this specific status code globally.

### 2. Global OkHttp Interceptor for 429

A Staff Engineer does not write retry logic in every single `ViewModel`. They write it once, at the absolute lowest network layer: the `OkHttp Interceptor`.

```kotlin
class RateLimitInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        var request = chain.request()
        var response = chain.proceed(request)
        var tryCount = 0
        val maxRetries = 3

        while (response.code == 429 && tryCount < maxRetries) {
            tryCount++
            
            // 1. Check if server told us exactly how long to wait
            val retryAfterSeconds = response.header("Retry-After")?.toLongOrNull()
            
            // 2. Calculate sleep time: Use Retry-After, OR Exponential Backoff with Jitter
            val sleepMs = if (retryAfterSeconds != null) {
                retryAfterSeconds * 1000L
            } else {
                val exponentialMs = (2.0.pow(tryCount) * 1000).toLong() // 2s, 4s, 8s
                val jitter = Random.nextLong(-500, 500) // +/- 500ms
                exponentialMs + jitter
            }

            // 3. Pause the thread (OkHttp background thread, NOT the UI thread)
            Thread.sleep(sleepMs)
            
            // 4. Close the failed response and try again
            response.close() 
            response = chain.proceed(request)
        }

        return response
    }
}
```

## Tradeoffs

**Silent Retry vs UI Feedback**

- **Silent Retry (The Interceptor):**
    - *Pros:* The UI code (ViewModel) is completely unaware the network is failing. It just thinks the request is taking a long time (e.g., 5 seconds instead of 1 second). Clean architecture.
    - *Cons:* If the `Retry-After` header dictates a 60-second wait, the user will stare at a spinning loading circle for 60 seconds. They will assume the app is frozen and force-close it.
- **UI Feedback (Failing Fast):**
    - *Pros:* The Interceptor immediately returns the 429 to the UI. The UI displays a Snackbar: *"Server busy. Try again in 60 seconds."* The user understands what is happening.
    - *Cons:* You have to write HTTP 429 handling logic in every single ViewModel.

*Staff Decision:* Hybrid approach. The `OkHttp` interceptor silently handles small retries (e.g., `< 3 seconds`). If the calculated backoff exceeds 3 seconds, or the max retry count is hit, the Interceptor throws a custom `RateLimitException`. The global UI error handler catches this exception and displays the Snackbar to the user.

## Failure Modes

- **The Accidental DDoS (Thundering Herd):**
  If 100,000 users are rate-limited simultaneously, and your exponential backoff algorithm does *not* include Jitter, all 100,000 apps will sleep for exactly 2.0 seconds, and then all 100,000 apps will hit the server at the exact same millisecond.
  *(Fix: The `jitter` calculation `Random.nextLong(-500, 500)` ensures the 100,000 requests are smeared smoothly across a 1-second window, protecting the server).*
- **Retry Amplification:**
  Microservice A calls Microservice B. Microservice B is overloaded and returns 429. Microservice A retries 3 times. Meanwhile, the Android App called Microservice A, saw a timeout, and retried 3 times. 
  3 Android retries * 3 Microservice A retries = 9 requests hitting Microservice B. If the user taps the button 3 times, that's 27 requests. 
  *(Fix: Mobile apps must limit global retries to 1 or 2 maximum. Do not rely heavily on client-side retries; fix the scaling issue on the backend).*

## Staff Engineer Thinking

When reviewing network resilience, a Staff engineer focuses on protecting the backend infrastructure.

1.  **Idempotency is Mandatory for Retries:** If an interceptor automatically retries a `POST /checkout` request, it is mathematically possible that the first request *succeeded* on the server, but the 429 was generated by a reverse proxy *returning* the response. If the client retries, the user is charged twice. I mandate [Idempotency Keys](api-design-for-mobile.md) for all mutating endpoints before allowing an automated retry interceptor to be merged.
2.  **Differentiating 429 vs 500:** A 429 means "The server is healthy, but you are too loud." A 500/502/503 means "The server is on fire." Exponential backoff with Jitter works for both, but the `Retry-After` header is usually only present on a 429. I ensure our networking layer treats 503s with extreme caution (larger backoffs) to avoid kicking a server while it is down.
3.  **Circuit Breaker Pattern:** If the server is returning 429s or 500s continuously, the app should stop trying entirely. I implement a Client-Side [Circuit Breaker](../patterns/circuit-breaker.md). If 5 requests fail in a row, the circuit "opens." For the next 60 seconds, any network request made by the UI instantly fails locally without ever hitting the radio antenna, saving battery and server load.

## Common Misconceptions

- **"If the server returns an error, try again immediately."** This is the single most destructive misconception in mobile development. Immediate retries cause cascading infrastructure failures.
- **"Rate limiting is only for malicious bots."** False. A poorly written Android app that accidentally gets stuck in an infinite loop while syncing a database will generate bot-level traffic. Rate limiting protects the API from your own bugs.

## Probing Questions

1.  Explain the fundamental difference between Throttling (slowing down a response) and Rate Limiting (HTTP 429).
2.  Why is an HTTP 429 response accompanied by a `Retry-After` header considered a "polite" rejection by an API Gateway?
3.  Describe the "Thundering Herd" problem, and exactly how adding a random "Jitter" variable to an Exponential Backoff algorithm prevents it.
4.  Why is it dangerous to implement an automated retry loop for a `POST /transfer_funds` API call without implementing an Idempotency Key?
5.  Explain the architectural tradeoff between handling a 429 silently inside an `OkHttp Interceptor` versus bubbling the 429 up to the UI/ViewModel.
6.  How does a "Retry Amplification" cascade occur when a mobile app, an API Gateway, and a backend microservice all implement their own retry logic simultaneously?
7.  If an API Gateway returns an HTTP 503 (Service Unavailable) instead of a 429, how should a mobile client adjust its retry behavior?
8.  Describe how a Client-Side "Circuit Breaker" pattern protects both the Android device's battery and the backend server during a prolonged outage.
9.  Why might a Staff Engineer mandate a maximum limit (e.g., 3) on the number of automated retries an application is allowed to perform for a single user action?
10. If 500,000 users open an application at the exact same second to buy concert tickets, why is the backend architecture solely reliant on the mobile app's correct implementation of backoff/jitter to survive?

## Further Reading

- [`circuit-breaker.md`](../patterns/circuit-breaker.md) — The pattern used to halt all network traffic when a server is completely unresponsive.
- [`api-design-for-mobile.md`](api-design-for-mobile.md) — How Idempotency Keys ensure that automated retries don't duplicate transactions.
- [`retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — The layer where the `Interceptor` handles the Exponential Backoff loop.
