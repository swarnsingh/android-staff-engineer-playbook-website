# Ktor vs Retrofit+OkHttp — Android Networking Decision

> Retrofit with OkHttp is an established Android stack; Ktor adds a multiplatform client API and selectable platform engines. Choose from platform targets, protocol and serialization needs, operational evidence, team capability, ecosystem constraints, and migration cost—not novelty or a universal winner.

---

> [!NOTE]
> **Kotlin Multiplatform Deep Dive:** For a comprehensive guide on using Ktor across Android and iOS within a shared KMP module, including engine selection and cross-platform patterns, see [`../kotlin-multiplatform/ecosystem/networking-with-ktor.md`](../kotlin-multiplatform/ecosystem/networking-with-ktor.md).

---

## TL;DR

| Need | Pick |
|---|---|
| Android-only app, no KMP plans | **Retrofit + OkHttp** |
| KMP app (Android + iOS shared logic) | **Ktor** |
| Brand-new app, fast iteration, willing to bet on KMP later | **Ktor** |
| Mature app on Retrofit, no KMP need | **Stay on Retrofit** |
| You need the largest plugin ecosystem and OkHttp's specific connection-pool tuning | **Retrofit + OkHttp** |
| You want one client API across Android, iOS, Desktop, Web | **Ktor** |
| Strict binary-size budget | Measure both release variants with the required converters/plugins and selected engine |
| Easy WebSocket + SSE + HTTP in one client | **Ktor** |

Retrofit + OkHttp remains a strong Android-focused default; KMP-shared networking makes Ktor's multiplatform client model compelling. Both choices are valid when they match the actual boundary and operational needs.

---

## Architecture at a Glance

### Retrofit + OkHttp

```mermaid
graph LR
  Your[Your code] --> Iface["Retrofit interface<br/>@GET / @POST"]
  Iface --> Conv["Converter<br/>Moshi / kotlinx.serialization"]
  Conv --> OkHttp["OkHttpClient<br/>connection pool + interceptors"]
  OkHttp --> Socket[TLS socket]
```

Two layers:
- **Retrofit** — declarative API interface, code-generated implementation, response converters.
- **OkHttp** — actual HTTP/2/3 client, connection pool, interceptor chain.

You can use OkHttp alone (for raw HTTP), but rarely Retrofit alone. They're sold separately, designed to compose.

### Ktor Client

```mermaid
graph LR
  Your[Your code] --> Client[HttpClient]
  Client --> Plugins["Plugins<br/>Auth, Logging, Retry, etc."]
  Plugins --> Engine["Engine<br/>OkHttp / CIO / Darwin / JS"]
  Engine --> Socket[TLS socket]
```

Three concepts:
- **`HttpClient`** — the high-level API.
- **Engine** — pluggable; Android projects commonly select OkHttp, CIO, or the Android engine.
- **Plugins** — install via `install(Logging) { ... }`, similar to Express middleware.

Ktor is one client API with selectable engines. Pass an engine to `HttpClient(engine)`, or let `HttpClient()` choose from the engine dependencies available to that source set.

---

## Declarative vs Imperative

### Retrofit — declarative

```kotlin
interface UserApi {
    @GET("/users/{id}")
    suspend fun getUser(@Path("id") id: String): User

    @POST("/users")
    suspend fun createUser(@Body user: NewUser): User

    @GET("/users")
    suspend fun listUsers(@Query("page") page: Int = 0): PagedUsers
}

val api: UserApi = retrofit.create(UserApi::class.java)
val user = api.getUser("u_123")
```

Annotations describe each call. Retrofit's code generator (or proxy) creates the implementation. Type-safe; refactor-safe; concise.

### Ktor — imperative

```kotlin
val user: User = client.get("https://api.example.com/users/u_123").body()

val created: User = client.post("https://api.example.com/users") {
    contentType(ContentType.Application.Json)
    setBody(NewUser(name = "Alice"))
}.body()

val pages: PagedUsers = client.get("https://api.example.com/users") {
    parameter("page", 0)
}.body()
```

Direct calls. Each request is a function call returning a `HttpResponse`. Body deserialization via `body()`.

The tradeoff:
- Retrofit forces an API surface — you define the shape once, callers use it. Refactoring is mechanical.
- Ktor is more flexible — you can construct dynamic URLs and bodies inline, but a 50-endpoint app becomes 50 free-floating call sites without convention.

Most teams wrap Ktor in interface-like API classes to recover Retrofit's structure:

```kotlin
class UserApi(private val client: HttpClient) {
    suspend fun getUser(id: String): User = client.get("/users/$id").body()
    suspend fun createUser(user: NewUser): User = client.post("/users") { setBody(user) }.body()
}
```

Now it looks like Retrofit again, just hand-written.

---

## Interceptors vs Plugins

The mechanism for cross-cutting concerns (auth, logging, retry, caching).

### OkHttp interceptor chain

```kotlin
val client = OkHttpClient.Builder()
    .addInterceptor(LoggingInterceptor())
    .addInterceptor(AuthInterceptor(tokenProvider))
    .addInterceptor(RetryInterceptor(maxAttempts = 3))
    .authenticator(TokenRefreshAuthenticator(tokenProvider))
    .build()

class AuthInterceptor(private val tokens: TokenProvider) : Interceptor {
    override fun intercept(chain: Interceptor.Chain): Response {
        val token = tokens.current() ?: return chain.proceed(chain.request())
        val req = chain.request().newBuilder()
            .header("Authorization", "Bearer $token")
            .build()
        return chain.proceed(req)
    }
}
```

OkHttp has two chains: **application interceptors** (top of stack, see your code's request shape) and **network interceptors** (bottom, see actual wire-level request after retries / redirects). The split matters for logging.

Special case: `Authenticator` handles 401 → refresh → retry automatically. Tightly coupled to OkHttp's retry policy.

### Ktor plugins

```kotlin
val client = HttpClient(OkHttp) {
    install(Logging) {
        logger = Logger.SIMPLE
        level = LogLevel.HEADERS
    }
    install(ContentNegotiation) {
        json(Json { ignoreUnknownKeys = true })
    }
    install(Auth) {
        bearer {
            loadTokens { BearerTokens(tokens.access, tokens.refresh) }
            refreshTokens {
                val newTokens = refreshTokenApi.refresh(oldTokens?.refreshToken)
                BearerTokens(newTokens.access, newTokens.refresh)
            }
        }
    }
    install(HttpRequestRetry) {
        retryOnServerErrors(maxRetries = 3)
        exponentialDelay()
    }
}
```

Plugins are first-class. The DSL is cleaner. Many plugins ship with Ktor (`Auth`, `Logging`, `ContentNegotiation`, `HttpTimeout`, `HttpRequestRetry`, `HttpCache`, `Resources`, `WebSockets`).

### Equivalence and gotchas

Pattern | OkHttp interceptor | Ktor plugin
---|---|---
Bearer token attach | `AuthInterceptor` | `Auth.bearer { loadTokens }` |
Token refresh on 401 | `Authenticator` | `Auth.bearer { refreshTokens }` |
Request logging | `HttpLoggingInterceptor` | `install(Logging)` |
Response caching | `Cache` + `CACHE_CONTROL` header | `install(HttpCache)` |
Timeouts | `OkHttpClient.Builder().connectTimeout(...)` | `install(HttpTimeout) { ... }` |
Retry on 5xx | Custom interceptor | `install(HttpRequestRetry)` |
Custom headers per call | Per-call via `Request.Builder` | Inline in `client.get { headers { } }` |
Response decompression | Built-in | `install(ContentEncoding)` |

Both ecosystems can do everything. Ktor's plugin DSL is more discoverable; OkHttp's interceptor API is more battle-tested.

---

## KMP — The Decisive Factor

This is where Retrofit can't compete.

### Retrofit

```kotlin
// JVM-only. Cannot compile for iosX64, iosArm64, jsBrowser, mingwX64.
val retrofit = Retrofit.Builder()
    .baseUrl("https://api.example.com/")
    .build()
```

Retrofit uses reflection and dynamic proxies that don't exist on Native or JS targets. It's Android/JVM only.

### Ktor

```kotlin
// commonMain
expect class HttpClientFactory {
    fun create(): HttpClient
}

class UserApi(private val client: HttpClient) {
    suspend fun getUser(id: String): User = client.get("/users/$id").body()
}

// androidMain
actual class HttpClientFactory {
    actual fun create(): HttpClient = HttpClient(OkHttp) { /* ... */ }
}

// iosMain
actual class HttpClientFactory {
    actual fun create(): HttpClient = HttpClient(Darwin) { /* ... */ }
}
```

`UserApi` is in `commonMain` — shared across Android, iOS, Desktop. Each platform plugs in its own engine.

If a KMP app shares HTTP code, Ktor is a common option because its API lives in common source sets and delegates to platform engines. Compare it with other maintained multiplatform clients or a project-owned boundary; Retrofit itself remains JVM/Android-oriented.

---

## Engines on Android

Ktor requires a client engine dependency. `OkHttp` is a common Android choice when its transport behavior and API-level floor fit the product:

```kotlin
val client = HttpClient(OkHttp) {
    engine {
        config { /* native OkHttpClient.Builder */ }
    }
}
```

Inside that `config { }` block, you have the full OkHttp builder API. So Ktor on Android is "Ktor's API + OkHttp's reliability."

Alternative engines:
- **`CIO`** — Ktor's coroutine-based engine. Official Ktor documentation lists Android 7.0+ support, with Java API desugaring required for older Android versions; it currently supports HTTP/1.x rather than HTTP/2.
- **`Android`** — the supported `io.ktor:ktor-client-android:$ktor_version` artifact, backed by `HttpURLConnection`. It currently lacks HTTP/2 and WebSocket support.

**Contextual default:** Evaluate the OkHttp engine first for an Android application already standardized on OkHttp behavior. Choose another engine only from explicit platform floors, protocol needs, proxy/TLS requirements, footprint measurements, and operational evidence.

When a Retrofit+OkHttp application selects Ktor's OkHttp engine, the migration replaces Retrofit's API layer while retaining OkHttp as the transport engine. Selecting CIO or the Android engine changes that transport choice as well.

---

## Serialization

### Retrofit

Plug in a converter factory:

```kotlin
.addConverterFactory(MoshiConverterFactory.create(moshi))
.addConverterFactory(KotlinSerializationConverter(Json))
```

Multiple converters per Retrofit instance.

### Ktor

Install ContentNegotiation:

```kotlin
install(ContentNegotiation) {
    json(Json {
        ignoreUnknownKeys = true
        coerceInputValues = true
    })
    // Could also register XML, ProtoBuf, CBOR adapters
}
```

Both work with kotlinx.serialization. Both work with Moshi. The mechanics differ but the result is the same: `response.body<User>()` works.

For shared KMP models, `kotlinx.serialization` is a common default because it supports Kotlin multiplatform. Moshi is JVM-oriented; other formats or platform adapters remain possible when their target and maintenance constraints fit.

---

## WebSocket and SSE Integration

### OkHttp / Retrofit

WebSocket is OkHttp-native:

```kotlin
client.newWebSocket(request, listener)
```

Retrofit doesn't model WebSockets — you drop to OkHttp for them.

Retrofit does not model SSE; the OkHttp SSE module can be used alongside it:

```kotlin
EventSources.createFactory(client).newEventSource(request, listener)
```

Two libraries; two APIs.

### Ktor

Both are first-class:

```kotlin
val client = HttpClient(OkHttp) { install(WebSockets); install(SSE) }

// WebSocket
client.webSocket("wss://api.example.com/chat") {
    while (isActive) {
        when (val frame = incoming.receive()) {
            is Frame.Text -> println(frame.readText())
            else -> { }
        }
    }
}

// SSE
client.serverSentEventsSession("https://api.example.com/ticker").apply {
    incoming.collect { event -> println(event.data) }
}
```

Ktor can expose HTTP, WebSocket, and SSE through one client API. Whether that is simpler than Retrofit plus OkHttp modules depends on existing abstractions, lifecycle policy, and the selected engine/plugins.

---

## Binary Size and Method Count

There is no portable stack delta: versions, engine, converters/plugins, desugaring, min SDK, ABIs, resources, consumer rules, and R8 optimization all change the result. Measure release artifacts for the two complete configurations with the same app code and toolchain.

Record at least the signed download/install size by ABI, DEX method/reference change, mapping/configuration, and the exact dependency graph. Remove unused plugins/dependencies and keep rules only when runtime behavior requires them—`-keep` rules preserve code and can reduce shrinking.

---

## Error Handling

### Retrofit

Two main patterns:

```kotlin
// Pattern A: Response<T> for known errors
@GET("/users/{id}")
suspend fun getUser(@Path("id") id: String): Response<User>

val response = api.getUser(id)
if (response.isSuccessful) {
    val user = response.body()!!
} else {
    when (response.code()) {
        404 -> /* not found */
        401 -> /* unauthorized */
    }
}
```

```kotlin
// Pattern B: throw HttpException via NetworkResult wrapper
suspend fun <T> safe(call: suspend () -> T): NetworkResult<T> = try {
    NetworkResult.Success(call())
} catch (e: HttpException) {
    NetworkResult.HttpError(e.code(), e.message())
} catch (e: IOException) {
    NetworkResult.NetworkError
}
```

### Ktor

```kotlin
val response = client.get("/users/$id")
when (response.status.value) {
    in 200..299 -> response.body<User>()
    404 -> /* not found */
    in 500..599 -> /* server error */
}
```

Or via `expectSuccess = true`:

```kotlin
val client = HttpClient(OkHttp) {
    expectSuccess = true   // 4xx/5xx throw RedirectResponseException, ClientRequestException, ServerResponseException
}

try {
    val user: User = client.get("/users/$id").body()
} catch (e: ClientRequestException) {
    // 4xx
}
```

Both ecosystems support both patterns. Ktor's typed exceptions (`ClientRequestException` for 4xx, `ServerResponseException` for 5xx) are slightly cleaner than Retrofit's generic `HttpException`.

---

## Testing

### Retrofit

[OkHttp `MockWebServer`](https://github.com/square/okhttp/tree/master/mockwebserver) is the standard:

```kotlin
val server = MockWebServer()
server.start()
server.enqueue(MockResponse().setBody("""{"id":"u1","name":"Alice"}"""))

val retrofit = Retrofit.Builder().baseUrl(server.url("/")).build()
val api = retrofit.create(UserApi::class.java)
val user = api.getUser("u1")
```

Real OkHttp client makes real HTTP calls to localhost. Battle-tested; works with Retrofit and Ktor (Android engine).

### Ktor

Two approaches.

**`MockEngine`** — Ktor-native, no real HTTP:

```kotlin
val mockEngine = MockEngine { request ->
    respond(
        content = """{"id":"u1","name":"Alice"}""",
        status = HttpStatusCode.OK,
        headers = headersOf(HttpHeaders.ContentType, "application/json"),
    )
}
val client = HttpClient(mockEngine) {
    install(ContentNegotiation) { json() }
}
val user: User = client.get("/users/u1").body()
```

Faster than MockWebServer; KMP-compatible.

**`MockWebServer`** also works with Ktor's OkHttp engine — same as Retrofit.

`MockEngine` is the portable Ktor common-test option. Interface fakes are also portable, while platform test source sets can use loopback servers or engine-specific tools such as MockWebServer on JVM/Android.

---

## Coroutine Cancellation

Both stacks integrate cleanly with structured concurrency:

```kotlin
viewModelScope.launch {
    val user = api.getUser("u_123")    // suspends
}
```

When the scope cancels, a correctly integrated suspending call should stop delivering a result and cancel the in-flight request/stream. The engine decides whether to reset one HTTP/2 stream, close a socket, or retain a healthy pooled connection for reuse. Test cancellation, resource cleanup, callback suppression, and connection reuse on the selected versions.

One subtle difference: Ktor's WebSocket session is more naturally bound to coroutine scope (`client.webSocket { ... }` is a suspend function whose body is the session lifetime). OkHttp's WebSocket has a callback API requiring manual cleanup. Net win for Ktor in real-time scenarios.

---

## Migration Patterns

### From Retrofit to Ktor

Mostly a wrap-with-adapter exercise:

```kotlin
// Step 1: Keep Retrofit interface, build a Ktor-backed implementation
interface UserApi {
    suspend fun getUser(id: String): User
}

class KtorUserApi(private val client: HttpClient) : UserApi {
    override suspend fun getUser(id: String): User = client.get("/users/$id").body()
}

// Step 2: Swap the DI binding
@Provides
fun provideUserApi(client: HttpClient): UserApi = KtorUserApi(client)
```

Endpoints migrate one at a time. After all endpoints are migrated, remove Retrofit.

Estimate from a representative slice that includes authentication, streaming, error mapping, serialization, caching, observability, tests, and rollout. Endpoint count alone does not predict migration effort.

### From Ktor to Retrofit

The same boundary-and-adapter approach can support a reverse migration when Android-only ecosystem or operational requirements justify it.

---

## When Each Wins (Concrete Scenarios)

| Scenario | Pick | Why |
|---|---|---|
| Android-only consumer app, 30 endpoints | Retrofit + OkHttp | Largest ecosystem; battle-tested; less code per call |
| KMP cross-platform business logic | Ktor | Retrofit can't compile to iOS |
| Brand-new SDK shipped to Android consumers | Retrofit + OkHttp | Larger ecosystem; familiar to consuming apps |
| Backend-shared client library targeting JVM + Android | Ktor | One client, two platforms |
| App with heavy real-time (chat, live trading) | Ktor | Unified WebSocket + SSE + HTTP API |
| App with strict APK size limits | Retrofit + OkHttp | Smaller method count + bytecode |
| New team, no legacy code, KMP optional later | Ktor | Migration to KMP later is free |
| Existing Retrofit codebase, no KMP plans | Stay on Retrofit | Migration cost > benefits |
| OkHttp-specific tuning needed (connection pool sizes, TLS-specific quirks) | Retrofit + OkHttp | Direct OkHttp access; Ktor still allows but adds a layer |
| Want one library for HTTP/WebSocket/SSE | Ktor | Three protocols in one client |

---

## Production Patterns

### Pattern 1: Ktor with cached OkHttp tuning

```kotlin
val client = HttpClient(OkHttp) {
    engine {
        config {
            connectTimeout(15, TimeUnit.SECONDS)
            readTimeout(15, TimeUnit.SECONDS)
            connectionPool(ConnectionPool(maxIdleConnections = 10, keepAliveDuration = 5, TimeUnit.MINUTES))
            cache(Cache(File(context.cacheDir, "http-cache"), 10 * 1024 * 1024))
        }
    }
    install(Logging) { level = LogLevel.HEADERS }
    install(ContentNegotiation) { json() }
    install(Auth) {
        bearer {
            loadTokens { BearerTokens(authStore.access, authStore.refresh) }
            refreshTokens { /* call auth API */ }
        }
    }
    install(HttpRequestRetry) {
        retryOnServerErrors(maxRetries = 3)
        exponentialDelay()
    }
    install(HttpTimeout) {
        requestTimeoutMillis = 30_000
    }
}
```

### Pattern 2: Retrofit with full OkHttp interceptor chain

```kotlin
val okHttp = OkHttpClient.Builder()
    .connectTimeout(15, TimeUnit.SECONDS)
    .readTimeout(15, TimeUnit.SECONDS)
    .cache(Cache(File(context.cacheDir, "http-cache"), 10 * 1024 * 1024))
    .addInterceptor(LoggingInterceptor())
    .addInterceptor(AuthInterceptor(authStore))
    .authenticator(TokenRefreshAuthenticator(authStore, refreshApi))
    .addInterceptor(RetryInterceptor(maxAttempts = 3))
    .build()

val retrofit = Retrofit.Builder()
    .baseUrl("https://api.example.com/")
    .client(okHttp)
    .addConverterFactory(MoshiConverterFactory.create(moshi))
    .build()

val api = retrofit.create(UserApi::class.java)
```

### Pattern 3: KMP API wrapper (Ktor)

```kotlin
// commonMain
class ApiClient(private val client: HttpClient) {
    suspend fun getUser(id: String): User = client.get("/users/$id").body()
    suspend fun listOrders(userId: String): List<Order> = 
        client.get("/users/$userId/orders").body()
}

// commonMain (Repository)
class UserRepository(private val api: ApiClient) {
    suspend fun load(id: String): User = api.getUser(id)
}

// androidMain + iosMain — different HttpClient providers, same Repository
```

Same `UserRepository` runs on iOS, Android, JVM, and JS. Retrofit can't do this.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Ktor migration painful for 50+ endpoints | Lift-and-shift instead of incremental wrap-adapter | Wrap Retrofit interface; migrate endpoint-at-a-time |
| Ktor `body<T>()` returns malformed object | `ignoreUnknownKeys = true` masks schema mismatch | Use `coerceInputValues = false`; explicit field validation |
| OkHttp `Authenticator` competes with Ktor's `Auth` plugin | Both attached; double-refresh | Pick one layer — Auth plugin OR OkHttp Authenticator |
| `HttpRequestRetry` retries on 401 | Plugin retries before Auth refresh | Configure: `retryIf { request, response -> response.status.value !in 400..499 }` |
| Different engines on Android vs iOS for KMP | OkHttp on Android, Darwin on iOS | Expected; test on both |
| Release artifact exceeds its size budget after a stack change | Engine, plugins, converters, transitive dependencies, or keep rules changed | Compare reproducible release artifacts and dependency/R8 reports; remove only unused components |
| Parsing contributes to frame latency | Deserialization or mapping executes on a frame-sensitive path | Profile the selected engine/converter and move owned CPU work to an appropriate dispatcher when needed |
| Tests pass with MockEngine, fail in prod | MockEngine doesn't simulate timeouts | Add `delay()` in mock; or test with MockWebServer |
| Converter accepts an invalid/underspecified payload | Model and converter policy do not enforce required semantics | Validate critical fields and test missing/null/unknown values against provider fixtures |
| Scope cancellation still delivers a result or leaks work | Adapter/engine/version integration does not propagate cancellation as expected | Test the maintained selected versions and fix the integration; do not infer behavior from a major-version label |
| Ktor connection leak | Forgot to use `use { }` for streaming responses | `client.prepareGet(url).execute { response -> ... }` |
| Retrofit/Kotlin integration fails after a toolchain update | Unsupported or incompatible library/compiler combination | Check the maintained release compatibility notes and upgrade through a tested dependency change |
| Bearer token attached to refresh-token request | `Auth` plugin's refresh endpoint also intercepted | Use a separate HttpClient for refresh; or exclude path from Auth |

---

## Common Pitfalls

- **Migrating without a measured objective.** KMP sharing, protocol support, testability, engine behavior, or a common client API can justify Ktor; a working Retrofit stack can remain the lower-risk choice. Write the decision and success measures first.
- **Choosing a Ktor engine by reputation alone.** Verify Android/API floors, protocol and proxy/TLS support, cancellation, streaming, footprint, and behavior on representative network cohorts.
- **Unowned long-term coexistence.** Retrofit and Ktor can coexist during migration or for distinct boundaries, but duplicate auth, caching, pools, telemetry, and policy need owners and an exit/steady-state decision.
- **Trusting `ignoreUnknownKeys = true` blindly.** Hides bugs. Validate explicitly for critical fields.
- **Not testing the auth-refresh path.** Token expiry happens in production; tests should cover the refresh flow.
- **Defining endpoints inline everywhere with Ktor.** Without a wrapper class, you have 50 free-floating call sites. Adopt a Retrofit-like API class convention.
- **One client per call site.** Reuse compatible clients/engines and pools. Separate clients can still be appropriate for different trust material, proxies, authentication, engine configuration, or lifecycle boundaries.
- **Cache without `Cache-Control` validation.** Cached responses can be stale; tune per-endpoint.
- **No coroutine cancellation testing.** Network calls should cancel cleanly when the user navigates away.

---

## Probing Questions

1. Walk through what each layer does in `your code → Retrofit → OkHttp → socket`.
2. Walk through the same for `your code → Ktor → engine → socket`.
3. KMP — why can't Retrofit compile to iOS? What does Ktor do differently?
4. Compare OkHttp interceptor chain vs Ktor plugin model. Strengths of each?
5. You inherit a Retrofit codebase; the team wants KMP. Walk through your migration plan.
6. Bearer token refresh on 401 — implement in both OkHttp `Authenticator` and Ktor `Auth.bearer.refreshTokens`. Compare.
7. Design a reproducible release-artifact comparison for Ktor and Retrofit. Which inputs and outputs must be recorded?
8. Mock testing: `MockWebServer` vs Ktor's `MockEngine`. Pick each.
9. WebSocket + SSE + HTTP in one app — which stack creates the simpler owned boundary for this product, and how would you prove it?
10. Coroutine cancellation: prove a `viewModelScope.cancel()` actually cancels an in-flight HTTP request.
11. Both stacks have an `Auth` story. When does it accidentally retry the refresh endpoint itself? How to prevent?
12. A team wants Ktor "to be modern." No KMP plans. Walk through your code-review pushback.

---

## Answer Key

1. **Walk through what each layer does in `your code → Retrofit → OkHttp → socket`.**
   Your code defines a declarative interface. Retrofit converts the call parameters into an OkHttp Request and delegates. OkHttp handles connection pooling, interceptors, and TCP/TLS via sockets, then returns the response which Retrofit deserializes.
2. **Walk through the same for `your code → Ktor → engine → socket`.**
   Your code calls the Ktor `HttpClient` imperatively. The client passes the request through its configured plugins (auth, logging), then hands it to a platform engine (like OkHttp on Android or Darwin on iOS) which manages the raw socket connections.
3. **KMP — why can't Retrofit compile to iOS? What does Ktor do differently?**
   Retrofit relies on JVM reflection and dynamic proxies which are incompatible with iOS (Kotlin/Native). Ktor uses platform-agnostic abstractions (`commonMain`) and delegates HTTP execution to actual platform-specific engines.
4. **Compare OkHttp interceptor chain vs Ktor plugin model. Strengths of each?**
   OkHttp interceptors are a straightforward chain of responsibility, well-tested and native to the engine. Ktor plugins provide a broader, richer DSL for configuring things like WebSockets, Retries, and Auth, working uniformly across multiple platforms.
5. **You inherit a Retrofit codebase; the team wants KMP. Walk through your migration plan.**
   Wrap the existing Retrofit interfaces with Ktor-backed implementations via adapters. Migrate endpoint by endpoint, injecting the new Ktor wrapper, until Retrofit can be safely removed.
6. **Bearer token refresh on 401 — implement in both OkHttp `Authenticator` and Ktor `Auth.bearer.refreshTokens`. Compare.**
   OkHttp uses `Authenticator` which triggers on a 401 and synchronously generates a new Request. Ktor's `Auth` plugin uses a DSL to define `loadTokens` and `refreshTokens`, which feels more declarative but can easily conflict if mixed with an underlying OkHttp Authenticator.
7. **Design a reproducible release-artifact comparison for Ktor and Retrofit. Which inputs and outputs must be recorded?**
   Build equivalent minified release variants with pinned library/toolchain versions, engine, converters/plugins, min SDK, ABIs, keep rules, and app code. Compare signed download/install size, DEX references, dependency/R8 reports, startup/runtime measurements, and the product's size budget rather than reusing a universal delta.
8. **Mock testing: `MockWebServer` vs Ktor's `MockEngine`. Pick each.**
   Use `MockWebServer` for JVM-only integration tests that need real HTTP loopback. Use `MockEngine` for KMP tests since it mocks the engine directly in memory and compiles natively for all platforms.
9. **WebSocket + SSE + HTTP in one app — which stack creates the simpler owned boundary for this product, and how would you prove it?**
   Ktor offers one plugin/client model; Retrofit plus OkHttp uses declarative HTTP APIs with OkHttp WebSocket/SSE modules. Compare lifecycle, cancellation, auth, replay, telemetry, test fixtures, engine needs, team support, and measured code/size rather than deciding from API aesthetics alone.
10. **Coroutine cancellation: prove a `viewModelScope.cancel()` actually cancels an in-flight HTTP request.**
   Hold a test response open, cancel the owning job, assert prompt coroutine cancellation and no later delivery, and inspect server/engine events for request or stream cancellation. Do not require the pooled TCP connection to close: an implementation may retain a healthy connection for reuse.
11. **Both stacks have an `Auth` story. When does it accidentally retry the refresh endpoint itself? How to prevent?**
   This happens if the token refresh request itself is routed through the same client/interceptor handling auth, causing an infinite 401 loop. Prevent it by using a separate un-intercepted client for the refresh call.
12. **A team wants Ktor "to be modern." No KMP plans. Walk through your code-review pushback.**
   Ask for the concrete problem, alternatives, representative spike, migration/rollback plan, ownership, and measurable success criteria. KMP is one possible benefit, not the only one; reject a migration whose demonstrated value does not exceed its compatibility, learning, artifact, and operational cost.

## Further Reading

- [`retrofit-and-okhttp.md`](retrofit-and-okhttp.md) — Retrofit + OkHttp deep dive.
- [`graphql.md`](graphql.md) — Apollo Kotlin (separate alternative).
- [`security-and-keystore.md`](security-and-keystore.md) — certificate pinning on each stack.
- [`../data-and-di/hilt-vs-koin-vs-manual-di.md`](../data-and-di/hilt-vs-koin-vs-manual-di.md) — providing the HTTP client.
- [`../../backend-for-mobile/graphql-vs-rest.md`](../../backend-for-mobile/graphql-vs-rest.md) — REST vs GraphQL axis (orthogonal to this decision).
- [`../../backend-for-mobile/transport-protocols.md`](../../backend-for-mobile/transport-protocols.md) — HTTP/2 / HTTP/3 / gRPC at the transport layer.
- [`../../backend-for-mobile/sse-vs-websockets.md`](../../backend-for-mobile/sse-vs-websockets.md) — real-time protocols.
- [`../../platform-engineering/library-versioning.md`](../../platform-engineering/library-versioning.md) — versioning shared HTTP clients.
- [`../../kotlin/coroutines-and-flow/coroutines.md`](../../kotlin/coroutines-and-flow/coroutines.md) — coroutine cancellation semantics.
- [Ktor client documentation](https://ktor.io/docs/getting-started-ktor-client.html) — official.
- [Ktor client engines](https://ktor.io/docs/client-engines.html) — supported engines, dependency-driven selection, platform floors, and protocol capabilities.
- [Ktor Android engine API](https://api.ktor.io/ktor-client-android/io.ktor.client.engine.android/-android/index.html) — current `HttpURLConnection`-backed engine contract.
- [Ktor releases](https://ktor.io/docs/releases.html) — current stable and supported release lines.
- [Retrofit repository and documentation](https://github.com/square/retrofit) — official.
- [OkHttp repository and documentation](https://github.com/square/okhttp) — official.
- [Ktor + KMP guide](https://kotlinlang.org/docs/multiplatform-mobile-ktor-sqldelight.html) — KMP integration.
- [Roman Elizarov — Network architecture in KMP apps](https://elizarov.medium.com/) — design patterns.
