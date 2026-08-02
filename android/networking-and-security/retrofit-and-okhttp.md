# Retrofit and OkHttp

## Overview

`OkHttp` and `Retrofit`, both from Square, are established choices in Android networking.

While Junior developers use these libraries to simply fetch JSON from a server, a Staff Engineer understands the deep architectural split between the two. `OkHttp` is the low-level HTTP client (handling sockets, connection pooling, and caching), while `Retrofit` is the high-level declarative wrapper (handling URL routing, serialization, and coroutine integration).

Understanding how to manipulate the `OkHttp` interceptor chain is critical for building resilient apps that gracefully handle authentication token refresh, offline caching, and massive file uploads.

## Why It Matters

Mobile networks are hostile. Users walk onto elevators, drive through tunnels, and connect to captive Wi-Fi portals (like Starbucks) that intercept HTTPS traffic.

If a networking layer treats every failure as a crash, the experience is brittle. Centralize shared HTTP concerns such as authentication and cache policy, but retry only transient failures under a bounded policy when the operation and body are safe to replay. Honor cancellation, deadlines, backoff, and server hints; offline behavior depends on deliberately cached or persisted data.

## Historical Context

Before OkHttp became common, Android applications often used `HttpURLConnection` or Apache HTTP Client and had to account for platform-version behavior and lower-level HTTP details. Historical Android releases included connection-reuse defects that libraries and applications worked around.

Square built `OkHttp` to bypass these OS bugs by bundling a complete, heavily-tested HTTP client directly into the app APK. 

Square later built Retrofit as a declarative API layer over OkHttp. Compared with hand-built URLs and ad hoc parsing, generated request mappings and converter boundaries can reduce construction and decoding mistakes, though contracts still require tests and error handling.

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
        AppInt --> Cache[HTTP Cache: Disk entries and validators]
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

For challenge-based token renewal, an OkHttp `Authenticator` can centralize one bounded refresh and follow-up attempt. The repository still receives failure when refresh is unavailable, rejected, cancelled, or exceeds its deadline.

```kotlin
class TokenAuthenticator(
    private val tokenStorage: TokenStorage,
    // Built on a dedicated client with no TokenAuthenticator, so refresh 401s
    // cannot recursively invoke this authenticator.
    private val refreshApi: AuthApi,
) : Authenticator {

    override fun authenticate(route: Route?, response: Response): Request? {
        // Count authentication challenges, not redirects in the prior chain.
        val challengeCount = generateSequence(response) { it.priorResponse }
            .count { it.code == 401 }
        if (challengeCount >= 2) {
            return null
        }

        val failedAuthorization = response.request.header("Authorization")

        // 2. authenticate() runs synchronously on this call's execution thread.
        // Serialize refresh and re-read storage so queued 401s reuse the token
        // produced by the first refresh instead of refreshing again.
        synchronized(this) {
            val currentToken = tokenStorage.getToken()
            val currentAuthorization = currentToken?.let { "Bearer $it" }
            if (currentAuthorization != null && currentAuthorization != failedAuthorization) {
                return response.request.newBuilder()
                    .header("Authorization", currentAuthorization)
                    .build()
            }

            // The dedicated refresh API returns null for an unsuccessful or
            // unauthenticated refresh; bound its call timeout separately.
            val newToken = refreshApi.refreshTokenSynchronouslyOrNull()
                ?: return null
            tokenStorage.saveToken(newToken)
            
            // 3. Retry the failed request with the new token
            return response.request.newBuilder()
                .header("Authorization", "Bearer $newToken")
                .build()
        }
    }
}

// In DI, the refreshApi uses a client without this authenticator.
val refreshClient = baseClient.newBuilder()
    .authenticator(Authenticator.NONE)
    .build()
val refreshApi = buildRefreshApi(refreshClient)
val okHttpClient = baseClient.newBuilder()
    .authenticator(TokenAuthenticator(storage, refreshApi))
    .build()
```

## Tradeoffs

**Moshi vs Gson vs Kotlin Serialization**

Choosing the `Converter` for Retrofit is a critical architectural decision.

- **Gson:** The legacy Google library. 
    - *Tradeoffs:* Reflection-based mappings can bypass Kotlin constructor/nullability expectations unless suitable adapters and tests are used. Existing Gson systems may remain viable, but new Kotlin models should make null, default, and unknown-value behavior explicit.
- **Moshi:** Built by Square (the creators of Retrofit).
    - *Pros:* Kotlin-aware adapters and code generation can enforce declared constructor/nullability behavior without reflection for generated models.
    - *Tradeoffs:* Adapter setup, defaults, qualifiers, and performance depend on configuration and schema.
- **Kotlinx Serialization:** The official JetBrains library.
    - *Pros:* Compiler-plugin-generated serializers and Kotlin Multiplatform support.
    - *Tradeoffs:* Its JSON configuration rejects unknown keys by default, and annotation/configuration choices become part of the wire contract. Benchmark representative models rather than assuming a universal speed ranking.

## Failure Modes

- **The DI Circular Dependency Loop:**
  If your `TokenAuthenticator` injects your `Retrofit` instance (to make the refresh call), and your `Retrofit` instance injects your `OkHttpClient` (which requires the `TokenAuthenticator`), you have a circular dependency loop. Dagger/Hilt will refuse to compile.
  *(Fix: Build the refresh API on a dedicated bounded client with no token authenticator, then inject that API into the authenticated client. `Lazy`/`Provider` can defer a construction cycle but does not prevent runtime authenticator recursion if both APIs share the same authenticated client.)*
- **Reading the Interceptor Body Twice:**
  ```kotlin
  val bodyString = response.body?.string() // 1. Read the stream
  Log.d("API", bodyString)
  return response // 2. Pass to Retrofit
  ```
  *(Fix: In OkHttp, the response body is a one-time-use byte stream. If you call `.string()`, the stream is consumed and closed. When Retrofit tries to read it to parse the JSON, it crashes with `IllegalStateException: closed`. You must `peek()` the body or clone the buffer for logging).*
- **Leaking response-body resources:**
  If you download a large file (`@Streaming`) but fail to close its `ResponseBody`, the response does not promptly release its stream/socket resources. That may prevent connection reuse or consume HTTP/2 stream capacity until cleanup occurs. Repeated leaks increase connection churn and may eventually hit file-descriptor, dispatcher, peer, or network limits. The default connection-pool setting of five refers to **idle** connections, not a five-request maximum, so there is no universal “five leaks and every request hangs” threshold.

## Staff Engineer Thinking

When reviewing the Network layer, a Staff engineer focuses on resilience and global configurations:

1.  **Timeouts:** Review connect, read, write, and whole-call deadlines against the operation and supported network cohorts. Defaults and appropriate values vary by OkHttp version, request type, UX, and backend budget; verify behavior with fault tests.
2.  **Mocking via interceptors:** An interceptor-backed fake can exercise URL paths, verbs, converters, and response handling. Interface fakes are faster and more focused for domain tests; choose the boundary that matches the behavior under test.
3.  **Global Error Handling:** ViewModels should not be writing `if (e is UnknownHostException)` to detect offline states. I prefer an Interceptor that catches raw socket exceptions and throws a custom `NoInternetException`, which is then globally mapped into a User-Facing Error State by the BaseViewModel or Repository.

## Common Misconceptions

- **"A raw Retrofit `Call<T>` is entirely synchronous."** A raw call supports asynchronous `enqueue()` and blocking `execute()`. The blocking form must not run on the main thread; a Retrofit `suspend` service method uses OkHttp's asynchronous execution path.
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
9.  If you use `@Streaming` to download a large response, what ownership step prevents socket, file-descriptor, and response-body resource leaks?
10. Describe how you could use an `OkHttp` Interceptor to implement a complete "Offline First" mock backend for your Android application.

## Answer Key

1. **What is the architectural distinction between `OkHttp` and `Retrofit`? Why did Square separate them?**
   `OkHttp` is the low-level engine handling TCP sockets, HTTP multiplexing, and caching. `Retrofit` is a high-level API for declarative URL routing and serialization. They were separated to follow the single responsibility principle and allow each layer to be highly optimized and composable.
2. **Explain the "Chain of Responsibility" pattern as it applies to `OkHttp` Interceptors.**
   Each interceptor can inspect, modify, or rewrite a request before passing it to `chain.proceed()`, and then process the response when it returns. It delegates execution step-by-step to the network boundary and back.
3. **What is the difference between an Application Interceptor and a Network Interceptor?**
   Application Interceptors run first, intercepting the original call, ideal for auth headers and app-level logging. Network Interceptors run last, seeing exactly what is sent/received over the wire (including redirects and caching headers).
4. **Why is Gson considered dangerous to use with Kotlin Data Classes, and what library should you use instead?**
   Gson uses reflection and ignores Kotlin null-safety rules, potentially instantiating non-null fields as `null` if they are missing in JSON. Use Moshi or kotlinx.serialization instead.
5. **If you write an Interceptor to log the JSON response body using `response.body()?.string()`, why will your application crash when Retrofit attempts to parse the object?**
   `response.body()?.string()` consumes and closes the one-time-use byte stream. Retrofit will crash with an `IllegalStateException` when trying to read the already-closed stream.
6. **Describe how you would implement a transparent OAuth Token Refresh mechanism without putting `try/catch` logic inside your ViewModels or Repositories.**
   Use an OkHttp `Authenticator`, which runs synchronously on the call's execution thread after an authentication challenge. Coalesce refreshes: inside a bounded single-flight/mutex, re-read storage and reuse a credential changed since the failed request; only the first caller refreshes. Return a follow-up request with the new credential, cap follow-ups, and return `null` when recovery is unsafe or fails.
7. **What is a Circular Dependency, and how does it commonly occur when setting up an `OkHttp` Authenticator with Dependency Injection (Hilt)?**
   It occurs when the authenticator needs a Retrofit refresh API, that Retrofit needs the authenticated OkHttp client, and the client needs the authenticator. Build the refresh API on a separate bounded client without this authenticator. `Lazy`/`Provider` can defer construction but does not prevent runtime recursion when refresh uses the same authenticated client.
8. **Why is it unnecessary to wrap a Retrofit `suspend` function inside a `withContext(Dispatchers.IO)` block?**
   Retrofit's Coroutine integration automatically offloads the network call to a background thread natively through OkHttp's asynchronous execution.
9. **If you use `@Streaming` to download a large response, what ownership step prevents socket, file-descriptor, and response-body resource leaks?**
   Close the `ResponseBody`, preferably with `use { ... }`. OkHttp may reuse the connection when the protocol and body state permit; otherwise closing promptly releases or discards the underlying resources. There is no fixed five-leak pool-capacity threshold.
10. **Describe how you could use an `OkHttp` Interceptor to implement a complete "Offline First" mock backend for your Android application.**
   Write a MockInterceptor that intercepts requests, checks the URL path or method, and returns a crafted `Response` containing hardcoded JSON using `ResponseBody.create()` without ever calling `chain.proceed()` to the real network.

## Further Reading

- [`dependency-injection.md`](../data-and-di/dependency-injection.md) — How we provide singletons of Retrofit via Hilt.
- [`coroutines-under-the-hood.md`](../concurrency/coroutines-under-the-hood.md) — How Retrofit automatically bridges `Call<T>` into Coroutine State Machines.
- [OkHttp Interceptor API](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/Interceptor.kt)
- [OkHttp `ResponseBody`](https://square.github.io/okhttp/5.x/okhttp/okhttp3/-response-body/index.html) — Closing response bodies and resource ownership.
- [OkHttp `ConnectionPool`](https://square.github.io/okhttp/5.x/okhttp/okhttp3/-connection-pool/index.html) — Idle-connection configuration.
