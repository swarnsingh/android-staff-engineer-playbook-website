# API Contracts: GraphQL vs REST

> Mobile API shape affects request count, transferred bytes, parsing, cache behavior, backend fan-out, and failure handling. GraphQL and REST can each be shaped well or poorly; choose from measured screen contracts, operational ownership, compatibility, and cache requirements rather than adopting one style company-wide by default.
>
> **Decision:** canonical response/error layers and compatibility governance live in [`api-design-for-mobile.md`](api-design-for-mobile.md#canonical-response-and-evolution-contract). Apollo Kotlin implementation lives in [`../android/networking-and-security/graphql.md`](../android/networking-and-security/graphql.md). This chapter compares API shapes without redefining those contracts.

---

## Three Axes (Don't Conflate Them)

This file covers **API shape / query language** only. Two related but independent choices:

| Axis | What it decides | Where covered |
|---|---|---|
| **API shape** (this file) | How requests are structured: REST resources vs GraphQL queries vs gRPC RPC | Below |
| **Wire format** | How bytes are encoded: JSON vs Protobuf vs FlatBuffers | [`data-formats.md`](data-formats.md) |
| **Transport** | How bytes move: HTTP/1.1, HTTP/2, HTTP/3, gRPC streams, WebSocket | [`transport-protocols.md`](transport-protocols.md) |

You can have any combination — JSON-over-REST (most common), JSON-over-GraphQL (typical), Protobuf-over-gRPC (microservices), JSON-over-HTTP/2 (most modern stacks). Picking GraphQL vs REST doesn't auto-pick a wire format.

A short note on **gRPC**: it combines generated RPC stubs with Protobuf and commonly HTTP/2. It can fit typed internal APIs or mobile clients when the infrastructure, streaming model, debugging, proxy, and compatibility requirements justify it. REST or GraphQL may fit better when standard HTTP caching, browser interoperability, or existing operational tooling dominates. Deep dive in [`data-formats.md`](data-formats.md) and [`transport-protocols.md`](transport-protocols.md).

---

## The Mobile Problem: Over-fetching

A "User Profile Header" needs `displayName` and `avatarUrl`. REST returns this:

```json
// GET /api/v1/users/123
{
  "id": "123",
  "display_name": "Swaransingh",
  "avatar_url": "https://cdn.../avatar.png",
  "email": "user@example.com",
  "phone": "+1234567890",
  "address": { "street": "...", "city": "...", "country": "..." },
  "subscription_tier": "PREMIUM",
  "last_login_ip": "...",
  "marketing_opt_in": false,
  // ... 40 more fields
}
```

In this illustrative representation, the wire payload is about 4 KB while the screen needs roughly 200 bytes. A decoder can skip fields absent from its model, so it does not necessarily allocate every field; transfer, tokenization, and any modeled values still have measurable cost.

**GraphQL flips the paradigm** — the client declares exactly which fields it wants:

```graphql
query UserProfileHeader($id: ID!) {
  user(id: $id) {
    displayName
    avatarUrl
  }
}
```

Response:

```json
{ "data": { "user": { "displayName": "Swaransingh", "avatarUrl": "..." } } }
```

For this example the response is much smaller, although envelope, headers, compression, pagination, and resolver work still contribute cost.

### REST's answer: sparse fieldsets

REST can also avoid over-fetching. JSON:API defines sparse fieldsets, and an API can expose an equivalent projection explicitly:

```http
GET /users/123?fields=id,display_name,avatar_url
```

An API may also define relationship inclusion such as `?include=posts,comments`. Whether this matches GraphQL's payload efficiency depends on the resource contract, nesting, authorization, cache keys, and the actual screens; measure both shapes rather than assuming a fixed percentage.

---

## Client Request Fan-out and Round-Trip Cost

Profile screen needs: user info + recent posts + comment counts.

This particular resource contract requires several application requests:

```http
GET /users/123
GET /users/123/posts?limit=5
GET /users/123/posts/<id>/comments/count   ← repeated for each post
```

Those requests may execute sequentially or concurrently and may reuse an existing connection. Their latency depends on cache state, radio/network path, server work, prioritization, and dependency ordering.

One GraphQL operation can request the same screen shape in one application exchange:

```graphql
query UserProfile($id: ID!) {
  user(id: $id) {
    displayName
    avatarUrl
    recentPosts(limit: 5) {
      title
      thumbnailUrl
      commentCount
    }
  }
}
```

This removes client-visible request fan-out when the server can execute the operation efficiently. It does not imply a new TCP/TLS connection, one backend lookup, or one radio promotion: connection reuse, resolver fan-out, batching, and current radio state remain separate concerns.

### REST's answer: BFF (Backend-for-Frontend)

A common pattern: a thin server-side aggregator exposes per-screen endpoints (`GET /screens/profile-with-posts/123`). The mobile team owns the BFF; calls are tailored. This can provide one application request while retaining ordinary HTTP-cache semantics when the response, authorization, validators, and directives make it cacheable. See [`bff-pattern.md`](bff-pattern.md).

The tradeoff: a screen-shaped BFF may require endpoint work as screens evolve. GraphQL shifts that work into schema and resolver evolution, query governance, and server-side fan-out rather than eliminating it.

---

## The Caching Tradeoff

Resource-oriented `GET` contracts often map more directly to shared HTTP caches. GraphQL query caching depends on request method, operation identity, variables, authorization, response directives, and intermediary support.

The common defaults differ, but neither style receives correct caching without an explicit contract:

| Layer | Caches a REST `GET /users/123` | Caches a `POST /graphql` |
|---|---|---|
| Browser / OkHttp | Eligible `GET` responses can be cached when directives permit | `POST` is commonly not cached; query-over-GET can be eligible |
| CDN edge (Cloudflare, Fastly) | Resource URL, authorization, `Vary`, and directives define the key | Operation/hash, variables, authorization, and directives must define the key |
| Reverse proxy (Nginx, Varnish) | Standard HTTP caching can apply | Support depends on method and configured operation-aware policy |
| ETag / If-None-Match | Available when the server emits validators | Available to a cacheable GraphQL-over-HTTP `GET` representation when implemented |
| 304 Not Modified | Available for conditional requests | Available when the GraphQL `GET` contract and intermediary support validators |

At the same request volume, origin load depends on cache eligibility, hit rate, authorization partitioning, invalidation, operation shape, and whether GraphQL queries use `POST` or cacheable `GET`; the API label alone does not determine the result.

### Persisted operations and safelisting

GraphQL deployments can persist operation documents and, separately, enforce a safelist. A persisted-operation protocol lets the client identify a stored document; a safelist rejects operations outside an approved set. Automatic persisted queries (APQ) may register a previously unknown document at runtime, so APQ is not by itself a security allowlist.

1. The build or operation-registry pipeline derives an operation identifier, commonly a SHA-256 hash of a canonical operation document.
2. The client sends the hash + variables instead of the full query.
3. The server looks up the query by hash from a pre-registered list.
4. A `GET` representation can be cached when the variables, authorization partition, headers, and response directives form a safe key.

```http
GET /graphql?query_hash=a3f7…&variables=%7B%22id%22%3A%22123%22%7D
```

Potential benefits:

- **HTTP-cache participation.** A persisted operation sent as `GET` can use a stable operation/variables key when policy permits.
- **Bounded accepted operation surface.** A safelist can reject unregistered operations, while authorization, resolver limits, depth/complexity controls, and rate limits remain necessary.
- **Smaller request documents.** Sending an identifier instead of the complete operation can reduce request bytes; variables, headers, and response payload still dominate some workloads.

Apollo Kotlin can generate operation manifests/identifiers as part of its Gradle compiler workflow; the server or router still needs the matching registration and enforcement policy.

### Apollo Normalized Cache (client side)

Where REST has HTTP caching, Apollo has a **normalized cache** on the client:

```kotlin
val apolloClient = ApolloClient.Builder()
    .serverUrl("https://api.example.com/graphql")
    .normalizedCache(SqlNormalizedCacheFactory(context, "apollo.db"))
    .build()
```

Apollo parses responses and normalizes objects when the client has a configured stable cache-key policy (often a type plus key fields such as `id`). Objects without a usable key remain embedded/path-associated records. A write re-emits affected watchers only when it targets the same normalized record and includes or explicitly updates the selected fields.

This is closer to an application data store than to an HTTP response cache. It can support offline-first GraphQL when cache identity, persistence, conflict, freshness, privacy, and migration policy are defined.

---

## Type Safety: Schema-First Wins (Both Sides)

Both REST and GraphQL can be type-safe; the question is whether your team treats the contract as code.

### REST + OpenAPI

```yaml
# openapi.yaml
paths:
  /users/{id}:
    get:
      parameters:
        - name: id
          in: path
          required: true
          schema: { type: string }
      responses:
        '200':
          content:
            application/json:
              schema: { $ref: '#/components/schemas/User' }
```

Run [openapi-generator](https://openapi-generator.tech/) or [Kiota](https://learn.microsoft.com/en-us/openapi/kiota/) → Kotlin code is generated. Types match the server.

The honesty problem: **OpenAPI is often maintained by hand**, and drift between server and spec is silent. Apps crash from "fields the server changed."

### GraphQL + Apollo Kotlin

```graphql
# schema.graphqls (reviewed and pinned for reproducible builds)
type User {
  id: ID!
  displayName: String!
  avatarUrl: String
}
```

```kotlin
// .graphql file in your Android project
query UserProfile($id: ID!) {
  user(id: $id) { displayName avatarUrl }
}
```

The Apollo Gradle plugin invokes Apollo's compiler/code generation to validate the checked operation against the schema input pinned to that build and generate `UserProfileQuery.Data.User` with non-null `displayName` and nullable `avatarUrl`. The schema may come from a reviewed registry export, introspection snapshot, or source file; code generation does not read the live server implicitly. It catches incompatibility for operations and schema checked together, not drift affecting already-shipped clients.

```kotlin
plugins {
    alias(libs.plugins.apollo)
}

apollo {
    service("api") {
        packageName.set("com.example.api")
        schemaFiles.from(file("src/main/graphql/schema.graphqls"))
    }
}
```

The pinned schema makes operation compatibility reproducible for a build. Server CI must separately validate proposed schema changes against supported shipped/persisted operations before deployment.

---

## Mutations and Optimistic Updates

REST: any `POST/PUT/PATCH/DELETE` is a mutation. The body shape is up to you.

GraphQL: explicit mutation type:

```graphql
mutation LikePost($postId: ID!) {
  likePost(postId: $postId) {
    id
    likeCount
    likedByMe
  }
}
```

Apollo Kotlin supports **optimistic updates** — write the expected result to the cache immediately, then reconcile with the server response:

```kotlin
apolloClient.mutation(LikePostMutation(postId = "1"))
    .optimisticUpdates(
        LikePostMutation.Data(
            likePost = LikePostMutation.LikePost(
                id = "1",
                likeCount = post.likeCount + 1,
                likedByMe = true,
            )
        )
    )
    .execute()
```

When cache identity and selected fields align, the optimistic layer can notify affected watchers before the network result. Apollo replaces that layer with the server result or removes it when execution fails; the application still maps the failure and reconciles any server-side effect that may have occurred.

REST clients can implement the same optimistic state machine in a repository/local store. Apollo's normalized cache supplies an integrated optimistic layer, but identity, domain reconciliation, and user-visible failure policy remain application decisions.

---

## Subscriptions (Real-Time)

GraphQL defines subscription operations; WebSocket is a common transport, with exact protocol and lifecycle behavior chosen by the client/server stack:

```graphql
subscription OnNewComment($postId: ID!) {
  commentAdded(postId: $postId) { id author text }
}
```

```kotlin
apolloClient.subscription(OnNewCommentSubscription(postId = "1"))
    .toFlow()
    .collect { response -> /* ... */ }
```

A REST-shaped API can pair ordinary requests with [SSE](sse-vs-websockets.md), WebSockets, or polling. See [`push-vs-poll-vs-sse-vs-websockets.md`](push-vs-poll-vs-sse-vs-websockets.md).

If the app already governs GraphQL operations and the subscription transport meets continuity and lifecycle needs, subscriptions can preserve one schema/tooling model. A separate SSE/WebSocket/polling path may be simpler when real-time is narrow or owned independently.

---

## Error Handling Differences

Both styles have transport, HTTP, API-execution, and domain layers. The canonical model is in [API Design for Mobile](api-design-for-mobile.md#canonical-response-and-evolution-contract); the decision difference is the shape of the API-execution payload.

- A REST/BFF endpoint commonly uses HTTP status plus a structured representation, but status alone does not encode a domain outcome. Batch or aggregate endpoints can define partial member results.
- A GraphQL-over-HTTP client evaluates the negotiated HTTP response together with `data`, `errors`, and extensions. Request, validation, execution, parsing, and transport failures do not all have one status-code rule.
- A GraphQL operation can return usable partial `data` alongside `errors`. The repository applies an explicit product policy per operation instead of treating every non-empty `errors` list identically.

For example, a well-formed GraphQL response may contain:

```json
{
  "data": null,
  "errors": [
    { "message": "User not found", "extensions": { "code": "NOT_FOUND" } }
  ]
}
```

Apollo Kotlin exposes response data and GraphQL errors separately from transport/parsing failures. Map all layers at the repository boundary, preserve partial data only when the screen contract permits it, and retain stable machine-readable domain codes plus a generic fallback.

---

## Versioning

### REST — URL or media-type versioning

`/api/v1/users/123` → `/api/v2/users/123`. Clean break per major version. Easy to roll out gradually.

### GraphQL — schema evolution without a required URL version

GraphQL schemas often evolve in place: add fields, deprecate old ones with `@deprecated(reason: "...")`, and remove them only under a published compatibility/support policy:

```graphql
type User {
  id: ID!
  displayName: String!
  fullName: String @deprecated(reason: "Use displayName")
}
```

Clients on old operation strings keep working only while selected fields and their semantics remain compatible. In-place evolution can reduce endpoint migration work but does not remove contract lifecycle or release coordination.

For mobile, "no version" does not mean "no lifecycle." A released Android app may contain persisted query hashes for months or years. If the server removes a deprecated field while an old app still sends a safelisted query that selects it, that old app now has a production outage.

Treat GraphQL schema evolution like mobile API evolution:

| Practice | Why it matters on Android |
|---|---|
| Persisted query inventory by app version | Shows which old clients still depend on each field |
| Deprecation window tied to active installs | Removal waits for real adoption, not release-date optimism |
| CI schema diff against shipped queries | Prevents server merges that break old Android builds |
| Generic UI fallback for GraphQL errors | New domain/execution errors must not make old clients unusable; partial `data` follows operation policy |
| Complexity and depth limits | Protects the backend from expensive queries, even from buggy clients |

GraphQL helps mobile move faster only when the schema is governed as a contract. Without query safelisting, schema diffs, and app-version telemetry, it simply moves breakage from URL versions to field selection.

---

## Real-World Apollo + Compose + Flow Pattern

```kotlin
class ProfileViewModel @Inject constructor(
    private val apolloClient: ApolloClient,
) : ViewModel() {
    val profile: StateFlow<ProfileState> = apolloClient
        .query(UserProfileQuery(id = "123"))
        .watch()
        .map { response ->
            // This screen explicitly permits partial content when `user` is
            // present. Map GraphQL error codes to bounded UI warnings; do not
            // expose raw server messages directly.
            val user = response.data?.user
            val warnings = response.errors.orEmpty().mapNotNull(::toProfileWarning)
            when {
                user != null -> ProfileState.Content(user.toUiModel(), warnings)
                response.hasErrors() -> ProfileState.Error(mapProfileFailure(response.errors.orEmpty()))
                else -> ProfileState.Empty
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ProfileState.Loading)
}
```

`watch()` can emit the configured fetch-policy result and later cache changes that affect the watched operation's records and selected fields. Writes from another query, mutation, subscription, or explicit cache update therefore re-emit only when cache identity and field dependencies align. A REST client can provide the same UI contract by observing a repository-owned database/store; Apollo reduces custom normalized-cache plumbing rather than creating a uniquely possible pattern.

---

## When Each Wins

| Scenario | Pick |
|---|---|
| Public API consumed by browsers + CDN-heavy | REST |
| Many independent screen-specific queries against a complex graph | GraphQL |
| Internal microservice-to-microservice | gRPC + Protobuf (not in this file's scope) |
| Mobile-only app aggregating 3–5 backend services | GraphQL or BFF + REST |
| Large, mostly static catalog (product listings) | REST + CDN |
| Live-updating UI (likes, comments, presence) | GraphQL + subscriptions, or REST + SSE/WebSocket |
| Public SDK serving unknown clients | REST (universal toolchain) |
| Backend team won't add fields fast enough for your screens | GraphQL (mobile team self-serves from the schema) |
| Need offline-first with mutation optimism | GraphQL + Apollo normalized cache |
| Team is small and REST infrastructure already mature | REST |

Most apps end up with a hybrid: REST for static/large payloads (catalog, images), GraphQL for screen-specific data fetches. That's fine.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Measured profile payload contains many unused fields | Resource representation is broader than the screen | Sparse fieldsets, a screen-shaped BFF, or GraphQL field selection |
| Measured screen latency is dominated by dependent client requests | Contract exposes client-visible request fan-out | Batch/include fields, add a BFF operation, or use a bounded GraphQL operation |
| GraphQL query cannot participate in the intended CDN policy | Operation uses an ineligible method/key or unsafe authorization partition | Define persisted query-over-GET, variables, directives, and authorization-aware cache keys where safe |
| Unregistered or expensive operation reaches resolvers | Accepted-operation, authorization, complexity, or rate controls are incomplete | Safelist where appropriate and enforce authorization, resolver, depth/complexity, and rate budgets |
| Apollo cache shows stale data after another screen mutated | Records do not share a configured key, or the write omitted selected fields | Verify cache-key policy and perform an explicit cache update/refetch when normalization cannot connect the records |
| Build fails after a reviewed schema update | A checked operation is incompatible with the pinned schema | Review the schema diff and operation; do not refresh mutable introspection merely to make CI pass |
| A selected Apollo field is unexpectedly `null` | The server returned null or an execution error, the partial response omitted the value, or the cache/fetch result lacks it | Inspect `data` and `errors`, schema nullability, the operation selection, fetch policy, cache identity, and the screen's partial-data policy |
| OkHttp cache hit rate dropped | Server changed `Cache-Control` or response varies on something unexpected | Inspect headers; check `Vary` and ETag |
| REST endpoint accidentally returns `null` instead of `false` | Loose typing on server | Generate Kotlin types from OpenAPI; enforce non-null in schema |
| GraphQL response carries 200 with errors | Client treated status as the complete outcome | Evaluate `data` and `errors` together; preserve partial data only under the operation's product policy |
| Mutation reconciliation leaves stale optimistic state | Optimistic write/reconciliation or cache-key policy is incomplete | Test success, GraphQL-error, transport-failure, and cancellation paths; repair or explicitly evict/update the affected records |
| Persisted query fails — "unknown query hash" | Hash list out of sync between client and server | Regenerate at build time; deploy together |
| Apollo subscription drops on particular networks | Lifecycle, server/intermediary idle policy, or network transition | Correlate the boundary; use measured liveness policy, bounded reconnect, and authoritative reconciliation |
| API contracts drift silently between mobile and backend | Schema artifacts and shipped operations are not governed together | Validate reviewed schema changes against checked and shipped/persisted operations plus supported client cohorts |

---

## Common Pitfalls

- **Switching to GraphQL "for performance."** Its benefit depends on current over-fetching, client request fan-out, caching, parsing, and resolver behavior. Compare representative GraphQL operations with sparse REST or a BFF before accepting migration and governance cost.
- **Allowing arbitrary unbounded client queries without a threat model.** Safelisted/persisted operations can reduce the accepted operation surface, but the server still needs authorization, resolver safeguards, and complexity/rate limits for every registered operation.
- **Assuming every GraphQL screen needs a normalized cache.** Adopt it when identity, offline, shared-record, or watcher requirements justify its lifecycle and privacy cost; a network-only operation can be the simpler correct contract.
- **Assuming `__typename` alone guarantees cache updates.** Configure stable key fields and ensure mutation/subscription writes include or explicitly update the fields observed by affected queries.
- **Mixing REST and GraphQL on one screen without ownership.** A hybrid can be valid, but define cache, loading, partial-failure, cancellation, retry, and observability policy across both clients.
- **Treating generation as proof of server compatibility.** Generate clients from a reviewed OpenAPI or GraphQL artifact, validate provider implementation and proposed changes in CI, and test supported shipped-client contracts. Generation alone does not prove the deployed server matches the artifact.
- **Treating GraphQL `errors` as soft warnings.** A response with `data: null` and `errors: [...]` is a hard failure, not a warning. Branch UI accordingly.
- **Ignoring shared-cache economics for static content.** A REST resource often maps directly to CDN caching, while a GraphQL persisted query-over-GET can also be cacheable when variables, authorization, and directives form a safe key. Choose from measured hit rate and operational simplicity.
- **No reproducible operation validation.** Configure Apollo's Gradle compiler to validate checked `.graphql` operations against a reviewed pinned schema. This blocks incompatible operations in that build; it does not protect shipped binaries from later server changes.

---

## Probing Questions

1. Walk through over-fetching with an illustrative payload. Which measurements show whether GraphQL, sparse fields, or a BFF improves it?
2. Compare HTTP-cache eligibility for a REST `GET`, a GraphQL `POST`, and a persisted GraphQL query sent as `GET`. What determines origin load?
3. Explain persisted operations and safelisting. Which payload, caching, and accepted-operation problems can they address?
4. Apollo normalized cache vs OkHttp HTTP cache — what's the conceptual difference?
5. Your API contract drifts between server and Android. Compare how OpenAPI + REST vs Apollo + GraphQL detect this.
6. Walk through optimistic updates in Apollo Kotlin. What happens on success vs failure?
7. Real-time updates: GraphQL subscriptions vs REST + SSE. When pick each?
8. A team wants to switch from REST to GraphQL for "performance." Walk through the audit you'd run first.
9. Error handling: how do transport, HTTP, API-execution, and domain outcomes differ for REST/BFF and GraphQL, including partial results?
10. Versioning: `/api/v2/users` vs schema deprecation. Compare the lifecycle costs of each.
11. A new feature needs data from 5 microservices on one screen. REST + BFF or GraphQL? Justify.
12. You're building an offline-first app with live UI updates. Walk through the Apollo + Flow + Compose pattern that delivers it.
13. Where does gRPC fit in this picture? Which mobile, infrastructure, caching, streaming, and tooling constraints favor or disfavor it?

---

## Answer Key

1. **Walk through over-fetching with an illustrative payload. Which measurements show whether GraphQL, sparse fields, or a BFF improves it?**
   In an illustrative measurement, a fixed REST representation may contain 4 KB across 40 fields while one screen selects two fields totaling about 200 bytes. GraphQL can reduce that payload when resolver and transport overhead do not offset the saving; measure the actual serialized, compressed, parsed response rather than treating those numbers as a platform constant.
2. **Compare HTTP-cache eligibility for a REST `GET`, a GraphQL `POST`, and a persisted GraphQL query sent as `GET`. What determines origin load?**
   Neither style gets useful caching for free. Cacheable REST `GET` responses often map directly to standard HTTP caches when validators and directives permit. GraphQL commonly uses `POST`, while persisted/APQ `GET` operations can also use HTTP/CDN caching. Origin load depends on eligibility, keys, directives, invalidation, hit rate, and query shape.
3. **Explain persisted operations and safelisting. Which payload, caching, and accepted-operation problems can they address?**
   A persisted-operation protocol lets the client send an identifier for a stored operation, reducing request-document bytes and potentially providing a stable query-over-`GET` cache key. Safelisting is the separate enforcement decision to reject operations outside an approved set. APQ that accepts runtime registration is useful persistence but is not an allowlist. Neither mechanism authorizes fields or bounds resolver cost, so authorization, complexity, resolver, and rate controls remain necessary.
4. **Apollo normalized cache vs OkHttp HTTP cache — what's the conceptual difference?**
   OkHttp caches eligible HTTP representations using request/cache metadata. Apollo's normalized cache stores operation fields as records under configured cache keys; writes can notify affected watchers when identity and selected fields align. It is an optional application data cache, not automatic HTTP caching.
5. **Your API contract drifts between server and Android. Compare how OpenAPI + REST vs Apollo + GraphQL detect this.**
   Either style needs a reviewed, reproducible contract artifact and CI validation. Apollo validates checked operations against the schema pinned to that build; OpenAPI generators can do the same for REST. Neither protects already-shipped binaries, so server CI must also validate changes against supported client operations/contracts.
6. **Walk through optimistic updates in Apollo Kotlin. What happens on success vs failure?**
   When the operation supplies optimistic data, Apollo publishes the optimistic record to affected watchers before the network result. The real result replaces it; on failure the optimistic layer is removed. The application still maps the failure and reconciles any related domain/server side effects.
7. **Real-time updates: GraphQL subscriptions vs REST + SSE. When pick each?**
   Prefer GraphQL subscriptions when the schema, Apollo operation model, and selected subscription transport already fit the product's lifecycle and continuity contract. Prefer SSE for a downstream text stream when ordinary HTTP infrastructure and separate request commands are simpler. Either option still needs authentication refresh, replay/reconciliation, bounded reconnect, and lifecycle ownership.
8. **A team wants to switch from REST to GraphQL for "performance." Walk through the audit you'd run first.**
   Measure request count, compressed payload, cache hit rate, parse cost, resolver/fan-out cost, latency distribution, and failure behavior for representative screens. Compare GraphQL with sparse REST or a BFF, and include migration, governance, caching, and security cost; the result depends on the current contract rather than the API label.
9. **How do transport, HTTP, API-execution, and domain outcomes differ for REST/BFF and GraphQL, including partial results?**
   Both styles require all four layers. HTTP status describes the exchange, not the complete domain outcome. GraphQL-over-HTTP evaluates status/media type with `data` and `errors`; REST/BFF evaluates status with its representation and may define partial batch/aggregate results. The repository maps each layer and preserves partial data only under an explicit screen contract.
10. **Versioning: `/api/v2/users` vs schema deprecation. Compare the lifecycle costs of each.**
    A `/v2` endpoint can isolate a breaking contract while requiring migration and parallel support. In-place GraphQL deprecation can avoid a new URL, but selected fields and semantics must remain compatible through the supported-client window. Both need usage evidence, published support policy, server validation against shipped clients, and an eventual removal plan.
11. **A new feature needs data from 5 microservices on one screen. REST + BFF or GraphQL? Justify.**
    Either can aggregate behind one mobile operation. A governed graph favors GraphQL when several clients need flexible selections and resolver ownership is mature. A BFF favors explicit screen contracts and mobile-owned orchestration/fallbacks. Compare fan-out, partial failure, caching, authorization, ownership, and compatibility rather than choosing from service count alone.
12. **You're building an offline-first app with live UI updates. Walk through the Apollo + Flow + Compose pattern that delivers it.**
    The ViewModel watches a query as a Flow and exposes mapped UI state. Cache writes from a mutation, subscription, or refetch notify the watcher when configured record identity and selected fields overlap; Compose then renders the emitted state. Offline persistence, conflict, freshness, and error policy remain application-owned.
13. **Where does gRPC fit in this picture? Which mobile, infrastructure, caching, streaming, and tooling constraints favor or disfavor it?**
    gRPC provides generated Protobuf RPC contracts and streaming over supported HTTP/2 infrastructure. It can fit controlled clients that value typed RPCs, compact messages, or streaming. Standard browser/CDN caching, text-level inspection, intermediary compatibility, schema evolution, generated-code workflow, and mobile binary/runtime cost may favor another shape. Measure the selected implementation rather than treating gRPC as categorically unsuitable for Android.

## Further Reading

- [`api-design-for-mobile.md`](api-design-for-mobile.md) — practical mobile-API design across both styles.
- [`bff-pattern.md`](bff-pattern.md) — REST's answer to per-screen data needs.
- [`data-formats.md`](data-formats.md) — wire-format choice (JSON, Protobuf, FlatBuffers).
- [`transport-protocols.md`](transport-protocols.md) — HTTP/2, HTTP/3, gRPC at the transport level.
- [`push-vs-poll-vs-sse-vs-websockets.md`](push-vs-poll-vs-sse-vs-websockets.md) — real-time alternatives.
- [`sse-vs-websockets.md`](sse-vs-websockets.md) — REST-friendly real-time.
- [`rate-limiting.md`](rate-limiting.md) — protecting GraphQL surface from depth-bomb queries.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — REST client canonical.
- [`../android/networking-and-security/graphql.md`](../android/networking-and-security/graphql.md) — Apollo Kotlin canonical.
- [`../distributed-systems/lww-vs-crdt.md`](../distributed-systems/lww-vs-crdt.md) — conflict resolution for offline GraphQL mutations.
- [Apollo Kotlin docs](https://www.apollographql.com/docs/kotlin) — official.
- [GraphQL spec](https://spec.graphql.org/) — the source.
- [OpenAPI](https://swagger.io/specification/) — REST schema-first.
- [JSON:API](https://jsonapi.org/) — REST conventions for sparse fieldsets, includes, errors.
- [Persisted queries — Apollo docs](https://www.apollographql.com/docs/router/configuration/persisted-queries/) — security + caching deep dive.
