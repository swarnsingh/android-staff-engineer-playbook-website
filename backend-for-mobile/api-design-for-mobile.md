# API Design for Mobile

> A mobile phone is not a server in a data center. It operates on battery power, communicates over unreliable cellular networks with high latency, and runs app versions that may be three years old. A Staff engineer knows that an API designed for a web browser will destroy a mobile app's performance. Designing APIs for mobile requires minimizing request counts (radio wakeups), aggressively compressing payloads, and building defensive parsing strategies to handle unexpected schema changes from the backend.

---

## Overview

When backend engineers design APIs, they typically optimize for RESTful purity, microservice boundaries, and database normalization. When mobile engineers consume APIs, they optimize for **user experience**. 

If a screen requires data from the `Users` microservice, the `Inventory` microservice, and the `Pricing` microservice, a web browser can make three parallel requests quickly over a fast Wi-Fi connection. A mobile app doing this on a 3G cell tower will experience compounding latency, battery drain, and UI stutter.

---

## 1. The Physical Constraints of Mobile

### The Cellular Radio State Machine
Mobile devices use Radio Resource Control (RRC) to manage the cellular modem. To save battery, the modem sleeps. 
When an app makes an HTTP request:
1. The modem wakes up (takes ~1-2 seconds, consuming high power).
2. The request is sent and received (high power).
3. The modem stays in a "tail state" for 5-15 seconds expecting more data (medium power).
4. The modem goes back to sleep (low power).

**The Anti-Pattern:** Polling an API every 10 seconds. The modem never leaves the high/medium power state. The battery will drain in hours.
**The Solution:** Batch requests, use Push Notifications (FCM) to wake the app, or use Server-Sent Events (SSE) / WebSockets for continuous streams.

### Bandwidth and Latency
- **Latency is compounding.** If you make sequential requests (Auth -> Get User -> Get Permissions), a 200ms ping means the user waits 600ms just for network transit.
- **Payload size matters.** A 5MB JSON payload (over-fetching) on a slow connection will cause OkHttp `SocketTimeoutException`s.

---

## 2. Core Android Example: Retrofit and the Over/Under-Fetching Problem

### Under-Fetching (The N+1 Problem)
The backend provides pure REST resources.
```kotlin
// Android Retrofit Definition
interface SocialApi {
    @GET("api/v1/posts")
    suspend fun getFeed(): List<Post> // Returns just post IDs and Text

    @GET("api/v1/users/{id}")
    suspend fun getUserProfile(@Path("id") userId: String): User
}
```
To render a feed of 20 posts with author avatars, the Android app must make **21 HTTP requests** (1 for the feed, 20 for the users). This will destroy the user experience on cellular networks.

### Over-Fetching
The backend tries to solve the above by sending everything.
```kotlin
interface SocialApi {
    @GET("api/v1/posts?include=author,comments,likes,history")
    suspend fun getFeed(): List<PostWithEverything>
}
```
Now the Android app downloads 3MB of JSON for a screen that only displays 140 characters of text and a tiny avatar. The JSON parsing alone (using Moshi or Gson) will block the background thread and trigger a GC pause, causing UI jank.

### The Mobile Solution: Payload Shaping
Mobile APIs should return exactly what the screen needs, nothing more. This is achieved via:
1. **GraphQL:** The Android app defines the exact schema it wants via Apollo Kotlin.
2. **Backend-For-Mobile (BFF):** A middleware server aggregates the microservices and returns a custom JSON object tailored for the specific Android screen. (See `bff-pattern.md`).

---

## 3. Core Android Example: Defensive Parsing and Result Envelopes

Backend teams deploy continuously. Mobile apps are shipped as static binaries (APKs/AABs) that users may never update. **Forward compatibility is mandatory.**

### 1. Ignore Unknown Keys
If the backend adds a new `"badge_tier"` field to the JSON, older versions of the app must not crash.
- **Retrofit/Moshi:** Fails by default on unknown keys if using certain adapters. Must be explicitly configured to ignore them.
- **Kotlinx Serialization:** Fails by default! You must set `ignoreUnknownKeys = true`.

```kotlin
val json = Json { ignoreUnknownKeys = true }
```

### 2. Enum Fallbacks
If the backend adds a new enum value (e.g., `Status.ARCHIVED`), older apps that only know `ACTIVE` and `INACTIVE` will crash during deserialization.
```kotlin
// Defensive Kotlin definition
enum class Status {
    ACTIVE,
    INACTIVE,
    UNKNOWN; // Always include a fallback!
}
```

### 3. The Sealed Result Envelope
Standard HTTP status codes (404, 500) are not enough for mobile. Mobile needs business-logic error handling. Wrap API responses in a typed `Result` envelope.

```kotlin
sealed interface NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>
    
    data class BusinessError(
        val code: String, // e.g., "INSUFFICIENT_FUNDS"
        val userMessage: String // e.g., "Your balance is too low."
    ) : NetworkResult<Nothing>
    
    data class HttpError(val code: Int) : NetworkResult<Nothing>
    
    data class IOError(val exception: IOException) : NetworkResult<Nothing> // No network
}
```

In your Repository:
```kotlin
suspend fun fetchProfile(): NetworkResult<Profile> {
    return try {
        val response = api.getProfile()
        if (response.isSuccessful) {
            NetworkResult.Success(response.body()!!)
        } else {
            // Parse custom error JSON from the backend
            val errorBody = parseErrorJson(response.errorBody())
            NetworkResult.BusinessError(errorBody.code, errorBody.message)
        }
    } catch (e: IOException) {
        NetworkResult.IOError(e) // Airplane mode
    }
}
```

---

## 4. Versioning Strategy for Mobile

When a web app updates its API, the frontend is deployed simultaneously. When a mobile app updates its API, it creates a new version, but v1.0, v1.1, and v1.2 are all still running in the wild.

### Strategies
1. **URI Versioning:** `api.example.com/v1/users` -> `api.example.com/v2/users`. Safest for major breaking changes.
2. **Header Versioning:** `Accept: application/vnd.example.v2+json`. Cleaner URLs, but harder to cache via CDNs.
3. **GraphQL:** No versions. Add new fields, never delete old fields. Deprecate fields in the schema so new client builds get warnings.

**The Force Upgrade Check:**
Every mobile app MUST hit a `/config` or `/handshake` endpoint on startup. If the backend determines the client version is too old to safely function, it returns a `FORCE_UPGRADE` flag, and the app locks the user out until they visit the Play Store.

---

## 5. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **JSON Parse Crash** | Backend added a new field, or changed an `Int` to a `String`, or sent a new Enum value. | Strict defensive parsing (ignore unknown keys, fallback enums). Write integration tests using real backend payload samples. |
| **Silent Token Expiration** | API returns 401, but the app doesn't handle it globally, resulting in empty screens. | Use an OkHttp `Authenticator` or `Interceptor` to automatically refresh tokens or trigger a logout event globally. |
| **Cellular Timeout** | Retrofit's default timeout (10s) is too short for large payloads on 3G, or too long for interactive searches. | Configure custom timeouts per endpoint (using OkHttp interceptors with custom headers) or tune the global OkHttp timeouts. |
| **Battery Drain** | Frequent polling of an endpoint for status updates. | Replace with Server-Sent Events (SSE), WebSockets, or FCM push notifications that wake the app only when state changes. |

---

## 6. Common Pitfalls

### Pitfall 1: Trusting the Backend's Nullability
Backend sends: `{"name": null}`. Your Kotlin data class says: `val name: String`. Retrofit uses Gson, which uses reflection to bypass Kotlin's null safety, injecting a Java `null` into your non-null Kotlin `String`. Your app crashes later with a `NullPointerException`.
*Fix:* Use `Moshi` or `Kotlinx Serialization`. They enforce Kotlin's null safety at the boundary and will fail the parsing immediately, allowing you to catch the exception and show an error state, rather than crashing the app randomly later.

### Pitfall 2: Treating HTTP 200 as "Success"
Many enterprise backends (especially legacy ones) return `HTTP 200 OK` for everything, with the error embedded in the JSON: `{"status": "error", "code": 500}`.
*Fix:* If you can't fix the backend, write a custom OkHttp `Interceptor` that intercepts the response, parses the status field, and rewrites the HTTP code to 500 before Retrofit sees it. This keeps your Repository layer clean.

---

## Probing Questions

1.  **Radio Wakeup:** Explain the specific mechanism by which FCM (Firebase Cloud Messaging) "wakes up" an Android device. Why is it vastly more battery-efficient than the app running an AlarmManager to ping the server every 15 minutes?
2.  **OkHttp Interceptors:** You want to implement an automatic retry mechanism for 503 Server Unavailable errors with exponential backoff. Do you put this logic in the Retrofit interface, the Repository, or an OkHttp Interceptor? Why?
3.  **Null Safety Boundary:** Explain exactly how `Moshi` differs from `Gson` when encountering a null JSON value mapped to a non-null Kotlin property. How does Kotlinx Serialization handle this same scenario?
4.  **GraphQL vs REST:** If a screen needs User Profile, Latest Order, and Cart Count, how many HTTP requests does REST typically require vs GraphQL? What are the caching disadvantages of GraphQL on the mobile client side?
5.  **Force Upgrade:** Walk through the architecture of a Force Upgrade system. How do you ensure the `/config` endpoint itself doesn't become a single point of failure that prevents the app from opening when the server is down?

## Further Reading

- [`bff-pattern.md`](bff-pattern.md) — How to fix over-fetching by building a middleware API tailored for the Android app.
- [`data-formats.md`](data-formats.md) — The performance differences between JSON, Protocol Buffers, and FlatBuffers on mobile.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Deep dive into configuring OkHttp for mobile constraints.
- [`../android/networking-and-security/ktor-vs-retrofit.md`](../android/networking-and-security/ktor-vs-retrofit.md) — Modern networking alternatives for Kotlin Multiplatform.
