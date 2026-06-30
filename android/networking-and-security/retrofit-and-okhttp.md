# Retrofit and OkHttp

## Overview

In the Android ecosystem, networking is completely dominated by two libraries from Square: `OkHttp` and `Retrofit`. 

While Junior developers use these libraries to simply fetch JSON from a server, a Staff Engineer understands the deep architectural split between the two. `OkHttp` is the low-level HTTP client (handling sockets, connection pooling, and caching), while `Retrofit` is the high-level declarative wrapper (handling URL routing, serialization, and coroutine integration).

Understanding how to manipulate the `OkHttp` interceptor chain is critical for building resilient apps that gracefully handle authentication token refresh, offline caching, and massive file uploads.

## Why It Matters

Mobile networks are hostile. Users walk onto elevators, drive through tunnels, and connect to captive Wi-Fi portals (like Starbucks) that intercept HTTPS traffic.

If your networking layer simply calls `api.getData()` and crashes when it fails, the UX is terrible. A Staff-level architecture uses `OkHttp` interceptors to automatically retry failed requests, attach Bearer tokens, transparently refresh expired tokens via an `Authenticator`, and cache responses so the app loads instantly even in Airplane mode.

## Historical Context

Before `OkHttp`, developers used `HttpURLConnection` (built into Java) or the Apache HTTP Client. These were famously terrible. `HttpURLConnection` had a bug on Android 2.2 where calling `close()` on a readable input stream poisoned the connection pool, forcing developers to write OS-version-specific hacks.

Square built `OkHttp` to bypass these OS bugs by bundling a complete, heavily-tested HTTP client directly into the app APK. 

Later, Square built `Retrofit` on top of `OkHttp`. Before Retrofit, developers had to manually parse JSON strings and manually build URL strings with `?query=` parameters, which was incredibly brittle and led to constant `NullPointerExceptions` and Malformed URL errors.

## First Principles

1.  **`OkHttp` (The Engine):** Responsible for making the physical TCP/TLS connection to the server. It manages connection pooling, HTTP/2 multiplexing, and GZIP compression.
2.  **`Retrofit` (The Steering Wheel):** Responsible for translating a Kotlin interface (`@GET("/users")`) into a raw `okhttp3.Request` object, and translating the raw `okhttp3.Response` back into Kotlin Data Classes using a Converter (like Moshi or Gson).
3.  **Interceptors:** A powerful middleware pattern in `OkHttp` that allows you to inspect, modify, or completely rewrite requests and responses before they hit the network.
4.  **Converters:** Pluggable factories in `Retrofit` that handle serialization (JSON to Kotlin).
5.  **CallAdapters:** Pluggable factories in `Retrofit` that adapt the execution model (e.g., adapting a raw `Call<T>` into a `suspend` function or a `Flow<T>`).

## Mental Model

Think of networking as **Shipping a Package**.
- **Retrofit:** The Front Desk clerk. You hand them a Kotlin object. They translate it into a standard cardboard box (Serialization), write the address on it (Routing), and hand it to the delivery driver.
- **OkHttp:** The Delivery Driver. They get in the truck, choose the fastest highway (Connection Pooling), stop at toll booths (Interceptors), physically drive to the destination (TCP Socket), and bring the response box back.

## Internal Mechanics

### The Interceptor Chain

The most powerful feature of `OkHttp` is the Interceptor chain. It is an implementation of the Chain of Responsibility pattern.

```kotlin
// A standard OkHttp Interceptor
class AuthInterceptor : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        // 1. Get the original request
        val originalRequest = chain.request()

        // 2. Modify it (Add Auth Header)
        val newRequest = originalRequest.newBuilder()
            .addHeader("Authorization", "Bearer $token")
            .build()

        // 3. Pass it down the chain to the actual network
        val response = chain.proceed(newRequest)

        // 4. (Optional) Inspect the response before returning it to Retrofit
        return response
    }
}
```

There are two types of Interceptors:
1.  **Application Interceptors:** The first thing to run. Best for adding headers (like Auth) or logging the exact request the app made.
2.  **Network Interceptors:** The last thing to run before hitting the wire. They see exactly what is sent over the network (including injected headers like `Accept-Encoding: gzip` added automatically by OkHttp). Best for inspecting caching and redirect behavior.

## Architecture

```mermaid
graph TD
    subgraph "Retrofit Layer"
        API[Kotlin @GET Interface] -->|Serialization| Moshi[Moshi Converter]
        Moshi -->|Generates| Req[OkHttp Request]
    end
    
    subgraph "OkHttp Interceptor Chain"
        Req --> AppInt[Application Interceptor: Logging/Auth]
        AppInt --> Cache[Cache Interceptor: Checks local DB]
        Cache --> NetInt[Network Interceptor: GZIP/Stetho]
    end
    
    subgraph "The Internet"
        NetInt -->|TCP/TLS| Server[(Backend Server)]
    end
    
    Server -.->|JSON Response| NetInt
```

## Production Example

**The Authenticator (Token Refresh)**

A classic Junior mistake is handling Token Refresh inside the ViewModel or Repository using `try/catch(401)`. 

A Staff Engineer implements this inside `OkHttp` using an `Authenticator`. This handles the refresh entirely transparently. The Repository doesn't even know it happened.

```kotlin
class TokenAuthenticator(
    private val tokenStorage: TokenStorage,
    private val authApi: Provider<AuthApi> // Lazy provider to prevent circular DI loops
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        // 1. If the failed request already tried to use a new token, give up to prevent infinite loops.
        if (response.request.header("Authorization") != null && response.code == 401 && response.priorResponse != null) {
            return null // Returns null to signal failure
        }

        // 2. Synchronously refresh the token. 
        // OkHttp calls this on a background thread automatically.
        // We use a synchronized block in case 5 concurrent API calls all hit 401 at the same time.
        synchronized(this) {
            val newToken = authApi.get().refreshTokenSynchronously()
            tokenStorage.saveToken(newToken)
            
            // 3. Retry the failed request with the new token
            return response.request.newBuilder()
                .header("Authorization", "Bearer $newToken")
                .build()
        }
    }
}

// In your Hilt DI Module:
val okHttpClient = OkHttpClient.Builder()
    .authenticator(TokenAuthenticator(storage, apiProvider))
    .build()
```

## Tradeoffs

**Moshi vs Gson vs Kotlin Serialization**

Choosing the `Converter` for Retrofit is a critical architectural decision.

- **Gson:** The legacy Google library. 
    - *Cons:* Uses heavy Reflection. Horribly breaks Kotlin null-safety. If the JSON is missing a field, Gson will instantiate your Data Class with `null` values even if your Kotlin property is declared as `val name: String` (non-null). Do not use in modern apps.
- **Moshi:** Built by Square (the creators of Retrofit).
    - *Pros:* Fully respects Kotlin nullability. Extremely fast. Supports codegen (no reflection). 
    - *Cons:* The standard choice for the last 5 years, but increasingly being replaced by Kotlinx.
- **Kotlinx Serialization:** The official JetBrains library.
    - *Pros:* Natively integrated into the Kotlin compiler. Supports KMP (Kotlin Multiplatform). Extremely fast. 
    - *Cons:* Slightly stricter parsing rules out-of-the-box (e.g., throws exceptions on unknown JSON keys unless explicitly configured).

## Failure Modes

- **The DI Circular Dependency Loop:**
  If your `TokenAuthenticator` injects your `Retrofit` instance (to make the refresh call), and your `Retrofit` instance injects your `OkHttpClient` (which requires the `TokenAuthenticator`), you have a circular dependency loop. Dagger/Hilt will refuse to compile.
  *(Fix: Inject a `Lazy<AuthApi>` or `Provider<AuthApi>` into the Authenticator so the dependency is deferred until runtime).*
- **Reading the Interceptor Body Twice:**
  ```kotlin
  val bodyString = response.body?.string() // 1. Read the stream
  Log.d("API", bodyString)
  return response // 2. Pass to Retrofit
  ```
  *(Fix: In OkHttp, the response body is a one-time-use byte stream. If you call `.string()`, the stream is consumed and closed. When Retrofit tries to read it to parse the JSON, it crashes with `IllegalStateException: closed`. You must `peek()` the body or clone the buffer for logging).*
- **Connection Pool Exhaustion:**
  If you download a massive file (`@Streaming`) but forget to explicitly close the `ResponseBody` in your Repository, the TCP connection is never returned to the `OkHttp` connection pool. After ~5 leaked calls, the pool is exhausted and all future network requests will hang indefinitely.

## Staff Engineer Thinking

When reviewing the Network layer, a Staff engineer focuses on resilience and global configurations:

1.  **Timeouts:** I verify that `connectTimeout`, `readTimeout`, and `writeTimeout` are explicitly configured on the `OkHttpClient`. The defaults (10 seconds) are often too short for rural users on 3G, but too long for snappy UI feedback.
2.  **Mocking via Interceptors:** For UI testing or early feature development before the Backend is ready, I encourage teams to write a `MockInterceptor` that intercepts specific URLs and returns hardcoded JSON strings. This is vastly superior to mocking the Retrofit Interface with Mockito, because the Interceptor actually validates that your URL paths and HTTP verbs are correct.
3.  **Global Error Handling:** ViewModels should not be writing `if (e is UnknownHostException)` to detect offline states. I prefer an Interceptor that catches raw socket exceptions and throws a custom `NoInternetException`, which is then globally mapped into a User-Facing Error State by the BaseViewModel or Repository.

## Common Misconceptions

- **"Retrofit executes network calls on the background thread automatically."** Retrofit 2.6+ inherently supports Kotlin Coroutines. If you define a method as `suspend fun getUser()`, Retrofit will shift the execution to a background thread natively. However, if you return a raw `Call<User>`, it is entirely synchronous and will crash the app if you call `.execute()` on the Main Thread.
- **"I need to add `Dispatchers.IO` when calling Retrofit suspend functions."** False. Retrofit's Coroutine CallAdapter internally routes the HTTP request to OkHttp's asynchronous dispatcher. Wrapping a Retrofit `suspend` function in `withContext(Dispatchers.IO)` is redundant and adds unnecessary context-switching overhead.

## Probing Questions

1.  What is the architectural distinction between `OkHttp` and `Retrofit`? Why did Square separate them?
2.  Explain the "Chain of Responsibility" pattern as it applies to `OkHttp` Interceptors.
3.  What is the difference between an Application Interceptor and a Network Interceptor?
4.  Why is Gson considered dangerous to use with Kotlin Data Classes, and what library should you use instead?
5.  If you write an Interceptor to log the JSON response body using `response.body()?.string()`, why will your application crash when Retrofit attempts to parse the object?
6.  Describe how you would implement a transparent OAuth Token Refresh mechanism without putting `try/catch` logic inside your ViewModels or Repositories.
7.  What is a Circular Dependency, and how does it commonly occur when setting up an `OkHttp` Authenticator with Dependency Injection (Hilt)?
8.  Why is it unnecessary to wrap a Retrofit `suspend` function inside a `withContext(Dispatchers.IO)` block?
9.  If you use the `@Streaming` annotation in Retrofit to download a 500MB video, what critical step must you take in your Repository to prevent exhausting the OkHttp Connection Pool?
10. Describe how you could use an `OkHttp` Interceptor to implement a complete "Offline First" mock backend for your Android application.

## Further Reading

- [`dependency-injection.md`](../data-and-di/dependency-injection.md) — How we provide singletons of Retrofit via Hilt.
- [`coroutines-under-the-hood.md`](../concurrency/coroutines-under-the-hood.md) — How Retrofit automatically bridges `Call<T>` into Coroutine State Machines.
- [OkHttp Interceptors Documentation](https://square.github.io/okhttp/features/interceptors/)
