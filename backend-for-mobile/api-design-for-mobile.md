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

### Staff Decision: REST, BFF, GraphQL, or Hybrid

At Staff level, the question is not "which API style is modern?" The question is: which contract lets old app versions keep working while backend teams keep shipping?

| Shape | Best when | Staff-level risk |
|---|---|---|
| REST resources | Stable domain objects, CDN-heavy reads, public API consumers | Mobile screens may under-fetch or over-fetch unless endpoints support sparse fields/includes |
| REST + BFF | Mobile screens aggregate several services or need server-owned fallback logic | BFF can become a god endpoint or a release bottleneck if ownership is unclear |
| GraphQL | Screens need flexible field selection across a rich graph | Without persisted queries, schema governance, and depth limits, the client can create server blast radius |
| Hybrid | Static/catalog reads fit REST, personalized screens fit GraphQL or BFF | Mixing styles per screen increases cache, error, auth, and observability complexity |

A BFF is often the right compatibility boundary when mobile release cycles are slower than backend deploy cycles. The app talks to a small set of mobile-shaped contracts; the BFF absorbs microservice churn, translates partial failures into mobile UI states, and gates response shapes by capabilities.

GraphQL is powerful when product teams need query flexibility, but production mobile GraphQL should be treated as a governed contract, not arbitrary client SQL over HTTP. Use persisted or safelisted queries, schema checks in CI, explicit deprecation windows, depth/complexity limits, and generated models through Apollo Kotlin. If old apps have a persisted query hash in the wild, removing the field behind that query is a breaking mobile change even if the GraphQL schema no longer has numeric versions.

The practical Staff rule: pick one data shape per screen, own its lifecycle, and define how it fails. A checkout screen may deserve REST + BFF for deterministic cache headers and semantic error envelopes. A social feed may deserve GraphQL with normalized caching. A product catalog may stay REST because CDN behavior matters more than field-level flexibility.

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

### The startup handshake

Every serious mobile API needs a startup handshake. It is not only a force-upgrade check. It is the server-client compatibility contract for this app launch.

```http
POST /v1/handshake
X-App-Version: 4.12.1
X-Version-Code: 412010
X-Platform: android
X-Api-Level: 35
X-Device-Class: low_ram

{
  "supportedCapabilities": [
    "feed.v2",
    "checkout.wallet",
    "profile.avatar_webp"
  ],
  "localSchemaVersion": 42
}
```

```json
{
  "policy": {
    "status": "ok",
    "minSupportedVersionCode": 410000,
    "forceUpdateBelow": 408000,
    "message": null
  },
  "serverCapabilities": {
    "feed": "v2",
    "checkout": "legacy",
    "avatarFormat": "webp"
  },
  "disabledFeatures": ["checkout.wallet"],
  "schemaPolicy": {
    "minReadableLocalSchema": 39,
    "outboxProtocol": 3
  }
}
```

The app caches the last successful handshake and uses it during offline launch. If the handshake endpoint is down on first install, default to the safest minimal feature set, not a lockout screen. A force-upgrade path that depends on a single flaky endpoint can turn a backend outage into a total app outage.

### Capability negotiation, not version guessing

Do not make backend code guess behavior from `versionCode` alone:

```kotlin
// Bad: version numbers become folklore.
if (appVersion >= 412010) {
    return FeedV2Response(...)
}
```

Prefer explicit capabilities:

```kotlin
data class ClientCapabilities(
    val supportsFeedV2: Boolean,
    val supportsWebpAvatars: Boolean,
    val outboxProtocol: Int,
)

fun feedResponseFor(c: ClientCapabilities): FeedResponse =
    if (c.supportsFeedV2) feedV2() else feedV1Compatible()
```

Version still matters for deprecation policy. Capabilities matter for behavior. This separation prevents accidental breakage when a hotfix backports one feature but not another.

### Compatibility contract

For every public mobile endpoint, document:

| Contract | Rule |
|---|---|
| Request fields | New optional request fields must be ignored by older servers or rejected with typed errors |
| Response fields | New response fields are optional to old clients |
| Enums | New enum values require `UNKNOWN` fallback behavior |
| Required fields | Never make an optional response field required without a new endpoint or negotiated capability |
| Semantics | Never change what an existing field means; add a new field |
| Errors | New business errors require a generic fallback UI |
| Pagination | Cursor format is opaque; clients never parse it |
| Idempotency | Mutation retries reuse the same key across process death |

### Negative capability testing

The Staff-level test is not "does the current app work with the current backend?" It is "does the current backend still work with old app contracts?"

```kotlin
@Test
fun feedV1Client_canReadFeedAfterBackendAddsBadges() = runTest {
    val oldClient = ContractClient(
        capabilities = setOf("feed.v1"),
        parser = FeedV1Parser(ignoreUnknownKeys = true)
    )

    fakeServer.enable("feed.badge_tier")

    val feed = oldClient.getFeed()

    assertThat(feed.items).isNotEmpty()
    assertThat(feed.items.first().title).isNotBlank()
}
```

Run these in CI against captured fixtures for N-3 or N-5 app versions. Mobile compatibility is a regression surface, just like unit tests.

---

## API Governance for Mobile

Mobile API governance is the system that prevents backend velocity from breaking old app binaries.

Minimum governance:

- Endpoint owner.
- Supported app version window.
- Capability gates.
- Request/response schema tests.
- Deprecation dates.
- Rollback plan.
- Dashboard for old-client traffic.
- Contract test fixtures for old apps.

### Schema change rules

| Change | Safe? | Rule |
|---|---|---|
| Add optional response field | Usually | Old clients must ignore unknown keys |
| Add required response field | Breaking | Use new endpoint or capability gate |
| Rename field | Breaking | Add new field, deprecate old field later |
| Change field meaning | Breaking | Add new semantic field |
| Add enum value | Risky | Clients need `UNKNOWN` fallback |
| Remove enum value | Risky | Old stored values and analytics may still reference it |
| Change pagination cursor shape | Safe only if opaque | Clients must never parse cursors |
| Add business error code | Safe only with generic fallback | Old clients need unknown-error UI |

### Persisted GraphQL queries

For mobile GraphQL, use persisted or safelisted queries.

Why:

- Prevents arbitrary expensive client queries.
- Lets backend know which app versions use which fields.
- Enables schema checks against real mobile operations.
- Improves CDN/cache behavior for query hashes.
- Makes deprecation measurable.

Governance rule: a GraphQL field is not removable until persisted-query traffic from supported app versions no longer references it.

### Negative capability matrix

Every backend feature rollout should test:

| Client capability | Backend feature | Expected behavior |
|---|---|---|
| absent | new field | ignored or omitted |
| absent | new enum | parsed as `UNKNOWN` |
| absent | new endpoint shape | old endpoint still works |
| old outbox protocol | new mutation protocol | server returns compatible response |
| old pagination | new ranking backend | cursor remains opaque and valid |

Negative capability tests are the antidote to "it works on the latest app."

---

## 5. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **JSON Parse Crash** | Backend added a new field, or changed an `Int` to a `String`, or sent a new Enum value. | Strict defensive parsing (ignore unknown keys, fallback enums). Write integration tests using real backend payload samples. |
| **Silent Token Expiration** | API returns 401, but the app doesn't handle it globally, resulting in empty screens. | Use an OkHttp `Authenticator` or `Interceptor` to automatically refresh tokens or trigger a logout event globally. |
| **Cellular Timeout** | Retrofit's default timeout (10s) is too short for large payloads on 3G, or too long for interactive searches. | Configure custom timeouts per endpoint (using OkHttp interceptors with custom headers) or tune the global OkHttp timeouts. |
| **Battery Drain** | Frequent polling of an endpoint for status updates. | Replace with Server-Sent Events (SSE), WebSockets, or FCM push notifications that wake the app only when state changes. |
| **Old-client breakage** | Backend removed or changed a field still used by an old app. | Keep additive wire changes, run old-client contract tests, gate new shapes behind capabilities. |
| **Handshake outage lockout** | App treats missing policy as `FORCE_UPGRADE`. | Cache last policy; first launch defaults to minimal safe mode; never fail closed unless security requires it. |
| **Feature flag mismatch** | Server enables a feature for clients that do not support its response shape. | Flag rollout must include app version, capability, schema version, API level, and backend cohort gates. |

---

## 6. Common Pitfalls

### Pitfall 1: Trusting the Backend's Nullability
Backend sends: `{"name": null}`. Your Kotlin data class says: `val name: String`. Retrofit uses Gson, which uses reflection to bypass Kotlin's null safety, injecting a Java `null` into your non-null Kotlin `String`. Your app crashes later with a `NullPointerException`.
*Fix:* Use `Moshi` or `Kotlinx Serialization`. They enforce Kotlin's null safety at the boundary and will fail the parsing immediately, allowing you to catch the exception and show an error state, rather than crashing the app randomly later.

### Pitfall 2: Treating HTTP 200 as "Success"
Many enterprise backends (especially legacy ones) return `HTTP 200 OK` for everything, with the error embedded in the JSON: `{"status": "error", "code": 500}`.
*Fix:* If you can't fix the backend, write a custom OkHttp `Interceptor` that intercepts the response, parses the status field, and rewrites the HTTP code to 500 before Retrofit sees it. This keeps your Repository layer clean.

### Pitfall 3: Using app version as the only API switch
`versionCode` is useful for support policy, but it is a weak behavior signal. Hotfixes, staged rollouts, regional builds, white-label apps, and backports break the assumption that "version X always has feature Y."

*Fix:* send explicit capabilities in the handshake and use version only for lifecycle policy: deprecation banners, minimum supported versions, and force-update thresholds.

---

## Probing Questions

1.  **Radio Wakeup:** Explain the specific mechanism by which FCM (Firebase Cloud Messaging) "wakes up" an Android device. Why is it vastly more battery-efficient than the app running an AlarmManager to ping the server every 15 minutes?
2.  **OkHttp Interceptors:** You want to implement an automatic retry mechanism for 503 Server Unavailable errors with exponential backoff. Do you put this logic in the Retrofit interface, the Repository, or an OkHttp Interceptor? Why?
3.  **Null Safety Boundary:** Explain exactly how `Moshi` differs from `Gson` when encountering a null JSON value mapped to a non-null Kotlin property. How does Kotlinx Serialization handle this same scenario?
4.  **GraphQL vs REST:** If a screen needs User Profile, Latest Order, and Cart Count, how many HTTP requests does REST typically require vs GraphQL? What are the caching disadvantages of GraphQL on the mobile client side?
5.  **Force Upgrade:** Walk through the architecture of a Force Upgrade system. How do you ensure the `/config` endpoint itself doesn't become a single point of failure that prevents the app from opening when the server is down?
6.  **Capability Negotiation:** Why is `versionCode >= 412010` a weaker backend switch than `supportsFeedV2=true`? Give a hotfix or backport scenario where version-based switching fails.
7.  **Old Client Contract Testing:** Design a CI test that proves a six-month-old Android client can still parse today's backend response.

## Further Reading

- [`bff-pattern.md`](bff-pattern.md) — How to fix over-fetching by building a middleware API tailored for the Android app.
- [`data-formats.md`](data-formats.md) — The performance differences between JSON, Protocol Buffers, and FlatBuffers on mobile.
- [`../mobile-system-design/versioning-and-backward-compatibility.md`](../mobile-system-design/versioning-and-backward-compatibility.md) — Full mobile version lifecycle: deprecation, schema migration, and force-update policy.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Deep dive into configuring OkHttp for mobile constraints.
- [`../android/networking-and-security/ktor-vs-retrofit.md`](../android/networking-and-security/ktor-vs-retrofit.md) — Modern networking alternatives for Kotlin Multiplatform.
