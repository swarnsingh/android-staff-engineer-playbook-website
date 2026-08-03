# API Design for Mobile

> A mobile phone operates on battery power, traverses variable Wi-Fi and cellular paths, and may run an older app version. Mobile API design therefore considers round trips, payload size, caching, compression, parsing cost, compatibility, and failure recovery against measured product requirements.
>
> **Canonical owner:** the shared mobile API contract—error layers, compatibility, deprecation, supported client cohorts, and contract governance—lives here. [`graphql-vs-rest.md`](graphql-vs-rest.md) compares API shapes; [`../android/networking-and-security/graphql.md`](../android/networking-and-security/graphql.md) applies this contract with Apollo Kotlin.

---

## Overview

When backend engineers design APIs, they typically optimize for RESTful purity, microservice boundaries, and database normalization. When mobile engineers consume APIs, they optimize for **user experience**. 

If a screen requires data from the `Users`, `Inventory`, and `Pricing` services, parallel requests may still pay separate scheduling, headers, server work, and failure handling. The impact depends on protocol reuse, request dependencies, payloads, network, and rendering architecture; measure it before introducing aggregation.

---

## 1. The Physical Constraints of Mobile

### The Cellular Radio State Machine
Cellular networks use Radio Resource Control (RRC) states, and data activity can affect radio energy. Promotion time, connected-state behavior, discontinuous reception, and idle timers vary by radio technology, carrier, modem, signal, device, and concurrent traffic; a fixed wake/tail timeline is not a portable application guarantee.

**The anti-pattern:** Polling at a fixed high frequency regardless of lifecycle or change rate can add radio and server work.
**Possible responses:** Batch compatible work, use cache validators and adaptive cadence, use FCM as a best-effort invalidation hint, or maintain SSE/WebSocket streams while the product lifecycle justifies them. Measure each option; persistent streams also have heartbeat and infrastructure costs.

### Bandwidth and Latency
- **Dependent latency accumulates.** Sequential requests cannot overlap their dependencies; actual elapsed time includes connection reuse, protocol, server processing, and transfer—not simply ping multiplied by request count.
- **Payload size matters.** A large response can increase transfer, parsing, memory, and deadline pressure, but size alone does not determine whether OkHttp raises a timeout.

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
With only these endpoints and no batching, embedding, or cache hits, rendering 20 posts with distinct uncached authors requires up to **21 application requests**. The experience depends on concurrency, connection reuse, cache state, payloads, and network; the contract nevertheless creates avoidable fan-out.

### Over-Fetching
The backend tries to solve the above by sending everything.
```kotlin
interface SocialApi {
    @GET("api/v1/posts?include=author,comments,likes,history")
    suspend fun getFeed(): List<PostWithEverything>
}
```
If this endpoint returns substantially more data than the screen uses, transfer, parsing, and allocation costs grow. Parsing on a background dispatcher does not directly block the main thread, but CPU contention, publication work, allocation pressure, or main-thread transformation can still affect frames; profile the actual response.

### The Mobile Solution: Payload Shaping
Mobile APIs should provide a bounded shape that supports the screen without unnecessary fan-out or payload. Common approaches include:
1. **GraphQL:** The Android app selects fields for an operation through a client such as Apollo Kotlin; pagination, server fields, errors, and resolver behavior still affect the result.
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

### Canonical response and evolution contract

Keep four layers distinct for every API style:

| Layer | Examples | Client responsibility |
|---|---|---|
| Transport | DNS, TLS, timeout, cancellation, offline | Classify retryability without inventing a domain outcome |
| HTTP exchange | Status, headers, negotiated media type, cache validators | Preserve protocol metadata and parse only when the representation is valid |
| API execution | GraphQL request/validation/execution errors; REST/BFF envelope or batch-member failures | Interpret the style-specific payload, including partial results where defined |
| Domain outcome | Insufficient funds, item unavailable, stale version | Map stable machine-readable codes to product behavior and retain a generic fallback |

An HTTP success status is not proof of domain success, and a non-2xx response does not by itself explain the domain outcome. For GraphQL-over-HTTP, evaluate the HTTP exchange together with `data`, `errors`, and negotiated response semantics; partial `data` is usable only under an explicit product policy. REST/BFF contracts can also define partial batch or aggregate results, so “REST is all-or-nothing” is not a safe model.

Schema/build validation protects only operations checked against that schema. It does not protect already-shipped binaries. Preserve supported operations and semantics for the published client cohort, inventory persisted or safelisted operations by app version, deprecate before removal, and remove a field only after telemetry and policy show that no supported client depends on it. Additive fields, enum values, nullability changes, and new error codes still require compatibility tests and defensive client behavior.

---

## 3. Core Android Example: Defensive Parsing and Result Envelopes

Backend teams deploy continuously. Mobile apps are shipped as static binaries (APKs/AABs) that users may never update. Within the published supported-client window, forward compatibility is a release requirement rather than an optional decoder preference.

### 1. Ignore Unknown Keys
If the backend adds a new `"badge_tier"` field to the JSON, older versions of the app must not crash.
- **Moshi:** Generated and reflective adapters ignore unknown object properties by default unless a stricter custom policy or adapter changes that behavior.
- **Kotlinx Serialization JSON:** The default `Json` configuration rejects unknown keys; set `ignoreUnknownKeys = true` globally or use the supported per-class mechanism when forward-compatible additive fields are expected.

```kotlin
val json = Json { ignoreUnknownKeys = true }
```

### 2. Enum Fallbacks
If the backend adds a new enum value (for example, `Status.ARCHIVED`), an older client's behavior depends on its serializer and fallback policy: decoding may fail, return an unknown representation, or invoke a configured fallback.
```kotlin
// Defensive Kotlin definition
enum class Status {
    ACTIVE,
    INACTIVE,
    UNKNOWN; // Use a fallback when the wire contract is expected to evolve additively.
}
```

### 3. The Sealed Result Envelope
Standard HTTP status codes (404, 500) are not enough for mobile. Mobile needs business-logic error handling. Wrap API responses in a typed `Result` envelope.

```kotlin
sealed interface NetworkResult<out T> {
    data class Success<T>(val data: T) : NetworkResult<T>
    
    data class BusinessError(
        val code: String, // e.g., "INSUFFICIENT_FUNDS"
    ) : NetworkResult<Nothing>
    
    data class HttpError(val code: Int) : NetworkResult<Nothing>

    data class ProtocolError(
        val reason: String,
        val cause: Throwable? = null,
    ) : NetworkResult<Nothing>
    
    data class IOError(val exception: IOException) : NetworkResult<Nothing> // No network
}
```

In your Repository:
```kotlin
suspend fun fetchProfile(): NetworkResult<Profile> {
    return try {
        val response = api.getProfile()
        val body = response.body()
        when {
            response.isSuccessful && body != null ->
                NetworkResult.Success(body)

            response.isSuccessful ->
                NetworkResult.ProtocolError("Successful response had no profile body")

            else -> {
                // A non-2xx status is an HTTP outcome. Promote it to a domain
                // outcome only when the representation matches the reviewed
                // machine-readable error contract.
                val domainError = response.errorBody()?.use(::parseBusinessErrorOrNull)
                if (domainError != null) {
                    NetworkResult.BusinessError(domainError.code)
                } else {
                    NetworkResult.HttpError(response.code())
                }
            }
        }
    } catch (e: SerializationException) {
        NetworkResult.ProtocolError("Profile representation did not match the contract", e)
    } catch (e: IOException) {
        NetworkResult.IOError(e) // Connectivity, DNS, TLS, or stream I/O.
    }
}
```

`SerializationException` is illustrative for Kotlinx Serialization; catch the converter's specific decoding exception when using Moshi or another stack. Cancellation must retain the coroutine/client library's documented behavior rather than being translated into a generic offline result.

---

## 4. Versioning Strategy for Mobile

When a web app updates its API, the frontend is deployed simultaneously. When a mobile app updates its API, it creates a new version, but v1.0, v1.1, and v1.2 are all still running in the wild.

### Strategies
1. **URI Versioning:** `api.example.com/v1/users` -> `api.example.com/v2/users`. Safest for major breaking changes.
2. **Header Versioning:** `Accept: application/vnd.example.v2+json`. Cleaner URLs, but harder to cache via CDNs.
3. **GraphQL:** Prefer additive evolution and deprecate fields before removal, but do not claim that GraphQL is “unversioned” or that fields can never be deleted. Define supported client cohorts, observe persisted-query and field usage, preserve semantics during the compatibility window, and remove a field only after the published support policy says no supported client depends on it. Even additive changes require validation because clients may make unsafe assumptions.
4. **API Versioning Strategies (Mobile Context):** Within the supported-client compatibility window, prefer additive evolution. Breaking changes or removals require a new negotiated contract or completion of the published deprecation/support policy; a forced upgrade is a risk decision, not a substitute for contract governance.

### The startup handshake

A startup policy handshake can be useful when one launch needs a coordinated compatibility decision across minimum-version policy, capabilities, schema/storage support, or kill switches. It adds an availability and caching dependency, so a smaller API may instead negotiate capabilities on individual requests, use ordinary remote configuration, or rely on a published server compatibility window. When a handshake is chosen, treat it as a versioned contract rather than only a force-upgrade check.

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
| **Battery Drain** | Frequent polling of an endpoint for status updates. | Evaluate an appropriately scoped stream or best-effort FCM invalidation hint, then reconcile durable server state. Background delivery and socket lifetime remain policy- and lifecycle-dependent. |
| **Old-client breakage** | Backend removed or changed a field still used by an old app. | Keep additive wire changes, run old-client contract tests, gate new shapes behind capabilities. |
| **Handshake outage lockout** | App treats missing policy as `FORCE_UPGRADE`. | Cache last policy; first launch defaults to minimal safe mode; never fail closed unless security requires it. |
| **Feature flag mismatch** | Server enables a feature for clients that do not support its response shape. | Flag rollout must include app version, capability, schema version, API level, and backend cohort gates. |

---

## 6. Common Pitfalls

### Pitfall 1: Trusting the Backend's Nullability
Backend sends: `{"name": null}` while the Kotlin model declares `val name: String`. Some reflection-based Gson mappings can construct an object containing a Java `null`, deferring failure until later use; exact behavior depends on adapters and configuration.
*Fix:* Use a Kotlin-aware generated or reflection adapter with explicit nullability behavior, such as properly configured Moshi or Kotlinx Serialization, and test malformed or legacy payloads. Catch decoding failures at the repository boundary and map them to an observable error state.

### Pitfall 2: Treating HTTP 200 as "Success"
Many enterprise backends (especially legacy ones) return `HTTP 200 OK` for everything, with the error embedded in the JSON: `{"status": "error", "code": 500}`.
*Fix:* Correct the server contract when possible. Otherwise preserve the HTTP status and parse the legacy envelope in a converter or repository mapper into a typed `BusinessError`. Synthesizing a transport `5xx` can trigger incorrect retry/monitoring behavior, and an interceptor that consumes the one-shot body must rebuild it safely.

### Pitfall 3: Using app version as the only API switch
`versionCode` is useful for support policy, but it is a weak behavior signal. Hotfixes, staged rollouts, regional builds, white-label apps, and backports break the assumption that "version X always has feature Y."

*Fix:* send explicit capabilities in the handshake and use version only for lifecycle policy: deprecation banners, minimum supported versions, and force-update thresholds.

---

## Probing Questions

1.  **Push vs polling:** Why can an OS/Play-services-managed FCM channel avoid periodic app polling, and which delivery/background limits prevent treating a push as a guaranteed app wake-up?
2.  **Retry ownership:** Which transient-failure classification belongs in shared HTTP infrastructure, and when must retry remain in a repository/outbox workflow?
3.  **Null Safety Boundary:** Explain exactly how `Moshi` differs from `Gson` when encountering a null JSON value mapped to a non-null Kotlin property. How does Kotlinx Serialization handle this same scenario?
4.  **GraphQL vs REST:** How can REST+BFF and GraphQL each minimize request count for a screen, and what HTTP/application-cache tradeoffs remain?
5.  **Force Upgrade:** Walk through the architecture of a Force Upgrade system. How do you ensure the `/config` endpoint itself doesn't become a single point of failure that prevents the app from opening when the server is down?
6.  **Capability Negotiation:** Why is `versionCode >= 412010` a weaker backend switch than `supportsFeedV2=true`? Give a hotfix or backport scenario where version-based switching fails.
7.  **Old Client Contract Testing:** Design a CI test that proves a six-month-old Android client can still parse today's backend response.

## Answer Key

1. **Why can an OS/Play-services-managed FCM channel avoid periodic app polling, and which delivery/background limits prevent treating a push as a guaranteed app wake-up?**
   Shared platform messaging infrastructure can receive a server hint without each app scheduling its own polling wakeups. Data-message delivery remains best-effort and depends on priority, Doze, app state, device policy, and possible deprioritization; use it to trigger bounded work and reconciliation, not as durable state. On Android 13+, `POST_NOTIFICATIONS` separately governs display of non-exempt notifications, not whether a data message can reach `FirebaseMessagingService`.
2. **Which transient-failure classification belongs in shared HTTP infrastructure, and when must retry remain in a repository/outbox workflow?**
   Shared infrastructure can classify transport/server hints and apply a common bounded policy, but it may retry only replay-safe/idempotent operations with explicit attempt, deadline, cancellation, and jitter rules. Domain commands, durable writes, or non-replayable bodies need repository/outbox ownership and idempotency semantics.
3. **Explain exactly how `Moshi` differs from `Gson` when encountering a null JSON value mapped to a non-null Kotlin property. How does Kotlinx Serialization handle this same scenario?**
   Some reflection-based Gson mappings can construct an object containing Java `null` and defer failure until use; adapters can change that behavior. Properly configured Moshi Kotlin adapters and Kotlinx Serialization normally reject an explicit `null` for a required non-null property at decoding, subject to custom adapters/serializers and declared defaults. Test the chosen configuration at the repository boundary.
4. **How can REST+BFF and GraphQL each minimize request count for a screen, and what HTTP/application-cache tradeoffs remain?**
   Either style can serve the screen in one or several requests depending on endpoint shape, batching, cache state, and query splitting. REST/BFF responses often map naturally to URL/HTTP caches; GraphQL commonly uses normalized application caching, while GET queries or persisted/APQ hashes can also participate in HTTP/CDN caching.
5. **Walk through the architecture of a Force Upgrade system. How do you ensure the `/config` endpoint itself doesn't become a single point of failure that prevents the app from opening when the server is down?**
   If the product chooses a startup policy endpoint, cache a valid prior policy with explicit expiry, ship a safe bootstrap default, authenticate the response, and define unavailable/stale behavior that does not accidentally lock out supported clients. Security emergencies may require a different fail-safe posture. Simpler products can avoid a mandatory startup dependency and enforce compatibility at ordinary request boundaries.
6. **Why is `versionCode >= 412010` a weaker backend switch than `supportsFeedV2=true`? Give a hotfix or backport scenario where version-based switching fails.**
   Version codes are linear, but features can be backported to older branches or staggered via staged rollouts. Relying on `versionCode` breaks when a hotfix build lacks the feature but has a higher version code; `supportsFeedV2=true` explicitly checks for the capability.
7. **Design a CI test that proves a six-month-old Android client can still parse today's backend response.**
   Store an old version of the client's API models and parser logic in the codebase. Write a test that feeds the current backend's JSON payload into the legacy parser and asserts that it successfully deserializes without throwing unknown key or missing field exceptions.

## Further Reading

- [`bff-pattern.md`](bff-pattern.md) — How to fix over-fetching by building a middleware API tailored for the Android app.
- [`data-formats.md`](data-formats.md) — The performance differences between JSON, Protocol Buffers, and FlatBuffers on mobile.
- [`../mobile-system-design/versioning-and-backward-compatibility.md`](../mobile-system-design/versioning-and-backward-compatibility.md) — Full mobile version lifecycle: deprecation, schema migration, and force-update policy.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — Deep dive into configuring OkHttp for mobile constraints.
- [`../android/networking-and-security/ktor-vs-retrofit.md`](../android/networking-and-security/ktor-vs-retrofit.md) — Modern networking alternatives for Kotlin Multiplatform.
- [`graphql-vs-rest.md`](graphql-vs-rest.md) — decision comparison that applies this contract to API shape.
- [`../android/networking-and-security/graphql.md`](../android/networking-and-security/graphql.md) — Apollo Kotlin application of this contract.
- [GraphQL specification: Field deprecation](https://spec.graphql.org/October2021/#sec-Field-Deprecation) — Schema deprecation semantics.
- [GraphQL specification: Validation](https://spec.graphql.org/October2021/#sec-Validation) — Executable-document validation against a schema.
