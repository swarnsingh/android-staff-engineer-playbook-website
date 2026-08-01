# API Contracts: GraphQL vs REST

> Mobile lives on a 16 ms frame budget, a 4G radio that costs battery to wake, and an unreliable connection. The API contract determines whether the UI renders in 200 ms or 2 seconds. GraphQL vs REST isn't a religion — it's a tradeoff between client power and HTTP caching, between schema enforcement and SDK independence, between a single round-trip and a CDN edge cache. Staff-level mastery means picking deliberately per screen, not per company.

---

## Three Axes (Don't Conflate Them)

This file covers **API shape / query language** only. Two related but independent choices:

| Axis | What it decides | Where covered |
|---|---|---|
| **API shape** (this file) | How requests are structured: REST resources vs GraphQL queries vs gRPC RPC | Below |
| **Wire format** | How bytes are encoded: JSON vs Protobuf vs FlatBuffers | [`data-formats.md`](data-formats.md) |
| **Transport** | How bytes move: HTTP/1.1, HTTP/2, HTTP/3, gRPC streams, WebSocket | [`transport-protocols.md`](transport-protocols.md) |

You can have any combination — JSON-over-REST (most common), JSON-over-GraphQL (typical), Protobuf-over-gRPC (microservices), JSON-over-HTTP/2 (most modern stacks). Picking GraphQL vs REST doesn't auto-pick a wire format.

A short note on **gRPC**: it's REST's strongest competitor when type safety + performance matter more than browser-cache friendliness. gRPC uses Protobuf over HTTP/2; clients get strongly-typed stubs; payloads are small and fast to parse. For server-to-server and KMP-shared logic, it's often the right choice. For Android-to-backend, the lack of browser/CDN tooling and the steeper ops learning curve keep most teams on REST or GraphQL. Deep dive in [`data-formats.md`](data-formats.md) and [`transport-protocols.md`](transport-protocols.md).

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

The mobile app downloads ~4 KB to use ~200 bytes. The Moshi adapter still allocates 40 fields; the GC churns; the radio stays on longer.

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

Two hundred bytes. Two field allocations. Zero waste.

### REST's answer: sparse fieldsets

REST isn't powerless against over-fetching. The JSON:API spec and most modern REST stacks support `?fields=id,name,avatar`:

```http
GET /users/123?fields=id,display_name,avatar_url
```

Plus `?include=posts,comments` for related resources. Many teams ship REST APIs with these and get 80% of GraphQL's payload efficiency. The remaining 20% (deeply nested queries, conditional includes) is where GraphQL pulls ahead.

---

## The N+1 Problem and Round-Trip Cost

Profile screen needs: user info + recent posts + comment counts.

REST forces multiple round-trips:

```http
GET /users/123
GET /users/123/posts?limit=5
GET /users/123/posts/<id>/comments/count   ← repeated for each post
```

On a 4G radio with ~80 ms RTT and a cold connection, that's easily 2–3 seconds before the screen renders.

GraphQL collapses to one round-trip:

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

One TCP+TLS connection, one HTTP/2 stream, one parse. The radio modem turns on once.

### REST's answer: BFF (Backend-for-Frontend)

A common pattern: a thin server-side aggregator exposes per-screen endpoints (`GET /screens/profile-with-posts/123`). The mobile team owns the BFF; calls are tailored. This delivers GraphQL's "one round-trip" benefit while keeping HTTP caching intact. See [`bff-pattern.md`](bff-pattern.md).

The tradeoff: BFF needs server work for every new screen; GraphQL doesn't.

---

## The Caching Tradeoff

This is where REST has an edge that GraphQL can never fully match.

REST's caching ecosystem is **free** because the API maps to HTTP semantics:

| Layer | Caches a REST `GET /users/123` | Caches a `POST /graphql` |
|---|---|---|
| Browser / OkHttp | Yes (Cache-Control header) | No (POST excluded by default) |
| CDN edge (Cloudflare, Fastly) | Yes | Only with custom routing rules |
| Reverse proxy (Nginx, Varnish) | Yes | No |
| ETag / If-None-Match | Native | Custom |
| 304 Not Modified | Native | Custom |

If your app fetches a million times a day, REST's caching means the origin server sees 10,000 requests; GraphQL's `/graphql` POST sees 1,000,000 requests.

### GraphQL's answer: persisted queries

Modern GraphQL clients support **persisted (a.k.a. safelisted) queries**:

1. At build time, every `.graphql` file gets a hash (SHA-256 of the query body).
2. The client sends the hash + variables instead of the full query.
3. The server looks up the query by hash from a pre-registered list.
4. The server responds; CDN can cache by `(hash, variables)`.

```http
GET /graphql?query_hash=a3f7…&variables=%7B%22id%22%3A%22123%22%7D
```

Two benefits beyond caching:

- **CDN-cacheable.** It's now a `GET` with a unique URL.
- **Security.** Clients can't construct arbitrary queries; the surface is fixed. Critical at scale — without this, attackers can write deeply nested queries that overwhelm your servers.
- **GraphQL persisted queries:** By storing the actual query strings on the server and referencing them strictly by their hashes from the client, the payload sizes are drastically minimized over the wire, optimizing bandwidth for mobile environments.

Apollo Kotlin supports this via build-time code generation.

### Apollo Normalized Cache (client side)

Where REST has HTTP caching, Apollo has a **normalized cache** on the client:

```kotlin
val apolloClient = ApolloClient.Builder()
    .serverUrl("https://api.example.com/graphql")
    .normalizedCache(SqlNormalizedCacheFactory(context, "apollo.db"))
    .build()
```

Apollo parses every response, identifies objects by their `__typename` + `id`, and stores them keyed by `User:123`. Subsequent queries asking for `User:123` (even from a different screen) reuse the cached object. Updates to `displayName` from one mutation auto-propagate to every Composable observing that field — anywhere in the app.

This is closer to a *database* than to an HTTP cache. Powerful and the right answer for offline-first GraphQL.

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
# schema.graphqls (pulled from the server via introspection)
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

The Apollo KSP plugin generates `UserProfileQuery.Data.User` with non-null `displayName` and nullable `avatarUrl` — directly from the server's introspected schema. **No drift possible** — the build fails if the server's schema doesn't satisfy the query.

```kotlin
plugins {
    id("com.apollographql.apollo3") version "4.0.0"
}

apollo {
    service("api") {
        packageName.set("com.example.api")
        schemaFiles.from(file("src/main/graphql/schema.graphqls"))
    }
}
```

GraphQL's schema-first nature is its strongest selling point after over-fetching. Build time fails if the API contract changes underneath you.

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

The cache updates → every Composable observing the post recomposes → the UI feels instant. If the server fails, the cache rolls back and the UI re-renders the prior state.

REST equivalent: you implement the same flow manually (update local state, send request, revert on failure). Apollo bakes it into the cache layer.

---

## Subscriptions (Real-Time)

GraphQL supports subscriptions over WebSocket:

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

REST has no native equivalent. You'd reach for [SSE](sse-vs-websockets.md), WebSockets, or polling. See [`push-vs-poll-vs-sse-vs-websockets.md`](push-vs-poll-vs-sse-vs-websockets.md).

If your app has heavy real-time needs *and* you've already committed to GraphQL, subscriptions are a nice consistency win. If real-time is incidental, REST + SSE is usually simpler.

---

## Error Handling Differences

### REST

HTTP status code carries the error class:

- `200`/`201` — success.
- `400` — client error (validation).
- `401`/`403` — auth.
- `404` — not found.
- `429` — rate-limited.
- `5xx` — server error.

Body usually contains a structured error payload:

```json
{ "error": { "code": "VALIDATION_FAILED", "message": "Email is invalid" } }
```

### GraphQL

The HTTP status is *almost always* `200`, even on errors. The response body carries the errors:

```json
{
  "data": null,
  "errors": [
    { "message": "User not found", "extensions": { "code": "NOT_FOUND" } }
  ]
}
```

Apollo Kotlin exposes errors as `ApolloException` subtypes plus the `errors` field on the response. You have to check `data == null || errors.isNotEmpty()` explicitly.

Some queries can be **partial successes**: `data` populated for the fields that succeeded, `errors` array for the ones that failed. REST has no equivalent — it's all-or-nothing per endpoint.

---

## Versioning

### REST — URL or media-type versioning

`/api/v1/users/123` → `/api/v2/users/123`. Clean break per major version. Easy to roll out gradually.

### GraphQL — additive evolution

GraphQL has no version. You add fields, deprecate old ones with `@deprecated(reason: "...")`, remove them eventually:

```graphql
type User {
  id: ID!
  displayName: String!
  fullName: String @deprecated(reason: "Use displayName")
}
```

Clients on old query strings keep working as long as the deprecated fields exist. Reduces release coordination but increases schema-sprawl over time.

For mobile, "no version" does not mean "no lifecycle." A released Android app may contain persisted query hashes for months or years. If the server removes a deprecated field while an old app still sends a safelisted query that selects it, that old app now has a production outage.

Treat GraphQL schema evolution like mobile API evolution:

| Practice | Why it matters on Android |
|---|---|
| Persisted query inventory by app version | Shows which old clients still depend on each field |
| Deprecation window tied to active installs | Removal waits for real adoption, not release-date optimism |
| CI schema diff against shipped queries | Prevents server merges that break old Android builds |
| Generic UI fallback for GraphQL errors | GraphQL can return HTTP 200 with partial `data` and `errors` |
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
        .watch()                                              // live updates from cache
        .map { response ->
            when {
                response.hasErrors() -> ProfileState.Error(response.errors!!.first().message)
                response.data?.user == null -> ProfileState.Empty
                else -> ProfileState.Success(response.data!!.user.toUiModel())
            }
        }
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), ProfileState.Loading)
}
```

`watch()` re-emits whenever the cache updates — from another query, a mutation, or a subscription. Compose + Flow + Apollo cache = a screen that auto-updates without manual invalidation. This is the "live UI" pattern that's nearly impossible to replicate cleanly in REST.

---

## When Each Wins

| Scenario | Pick |
|---|---|
| Public API consumed by browsers + CDN-heavy | REST |
| Many independent screen-specific queries against a complex graph | GraphQL |
| Internal microservice-to-microservice | gRPC + Protobuf (not in this file's scope) |
| Mobile-only app aggregating 3–5 backend services | GraphQL or BFF + REST |
| Massive static catalog (product listings) | REST + CDN |
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
| 4 KB JSON on a simple profile fetch | REST over-fetching | Sparse fieldsets (`?fields=...`) or GraphQL |
| 3-second cold-start time on a screen | N+1 REST round trips | BFF endpoint or GraphQL single query |
| GraphQL request rate-limited / rejected by CDN | All POSTs hit origin | Persisted queries → GET → CDN cacheable |
| Mobile attacker writes a query that fetches 1 GB | No persisted-query enforcement | Allow only safelisted queries in prod |
| Apollo cache shows stale data after another screen mutated | `fetchPolicy` wrong or missing `__typename` | Use `FetchPolicy.NetworkFirst` or ensure schema includes `id` fields |
| Build fails after server-side schema change | Apollo Kotlin schema out of sync | Re-run introspection: `./gradlew downloadApolloSchemaFromIntrospection` |
| Apollo always returns `null` for some fields | Field selection forgot to include them | Add explicit field selections; GraphQL never returns unselected fields |
| OkHttp cache hit rate dropped | Server changed `Cache-Control` or response varies on something unexpected | Inspect headers; check `Vary` and ETag |
| REST endpoint accidentally returns `null` instead of `false` | Loose typing on server | Generate Kotlin types from OpenAPI; enforce non-null in schema |
| GraphQL response carries 200 but errors present | Forgot to check `response.errors` | Always check `hasErrors()` before reading `data` |
| Mutation rolled back but UI shows optimistic state | Cache update bug or wrong `__typename` | Verify cache normalization; restart Apollo client to reset |
| Persisted query fails — "unknown query hash" | Hash list out of sync between client and server | Regenerate at build time; deploy together |
| Apollo subscription drops connection on 4G | WebSocket idle timeout from mobile carrier | Implement keepalive ping; reconnect with exponential backoff |
| API contracts drift silently between mobile and backend | OpenAPI hand-maintained, never validated | Contract testing (Pact); CI runs introspection diff |

---

## Common Pitfalls

- **Switching to GraphQL "for performance."** GraphQL's perf wins come from over-fetching reduction + round-trip consolidation. If your screens already use sparse fieldsets and a BFF, the perf delta is small. Don't migrate for vibes.
- **Allowing arbitrary client queries in production.** Persistent queries are not optional at scale. Without them, a single attacker can write a query that joins every table in your DB.
- **GraphQL without normalized cache.** You've kept the over-fetching cost reduction but lost the offline-first + real-time benefits. Always pair Apollo with `SqlNormalizedCacheFactory`.
- **Forgetting `__typename` in mutation results.** Without `__typename`, Apollo can't normalize the response → cache doesn't update → UI stays stale.
- **Mixing REST and GraphQL on the same screen.** Possible but doubles cognitive load. Pick one per screen.
- **Hand-coding types from OpenAPI.** Code-gen at build time. If your team rejects code-gen, your types will drift.
- **Treating GraphQL `errors` as soft warnings.** A response with `data: null` and `errors: [...]` is a hard failure, not a warning. Branch UI accordingly.
- **Using GraphQL for cacheable static content.** A product catalog that doesn't change for hours per user belongs behind a REST endpoint + CDN, not a GraphQL query.
- **No build-time schema validation.** Apollo can validate every `.graphql` file at build time against the schema. Enable it. Stops bad queries from shipping.

---

## Probing Questions

1. Walk through the over-fetching problem with a concrete payload. Show how GraphQL collapses 4 KB to 200 bytes.
2. Why does REST get HTTP caching "for free" while GraphQL doesn't? What's the consequence at 1M requests/day?
3. Explain persisted queries. What two problems do they solve?
4. Apollo normalized cache vs OkHttp HTTP cache — what's the conceptual difference?
5. Your API contract drifts between server and Android. Compare how OpenAPI + REST vs Apollo + GraphQL detect this.
6. Walk through optimistic updates in Apollo Kotlin. What happens on success vs failure?
7. Real-time updates: GraphQL subscriptions vs REST + SSE. When pick each?
8. A team wants to switch from REST to GraphQL for "performance." Walk through the audit you'd run first.
9. Error handling: REST uses HTTP status codes; GraphQL returns 200 with `errors`. Why? What's the practical implication for the Android client?
10. Versioning: `/api/v2/users` vs schema deprecation. Compare the lifecycle costs of each.
11. A new feature needs data from 5 microservices on one screen. REST + BFF or GraphQL? Justify.
12. You're building an offline-first app with live UI updates. Walk through the Apollo + Flow + Compose pattern that delivers it.
13. Where does gRPC fit in this picture? Why isn't it usually picked for Android-to-backend calls?

---

## Answer Key

1. **Walk through the over-fetching problem with a concrete payload. Show how GraphQL collapses 4 KB to 200 bytes.**
   A REST profile fetch might return 40 fields (address, marketing_opt_in) totaling 4KB, even if the UI only needs `displayName` and `avatarUrl`. A GraphQL query explicitly requests only those two fields, and the server returns exactly 200 bytes, avoiding massive string allocation and parsing.
2. **Why does REST get HTTP caching "for free" while GraphQL doesn't? What's the consequence at 1M requests/day?**
   REST relies on HTTP `GET` requests, which CDNs, proxies, and OkHttp natively cache via `Cache-Control` headers. GraphQL uses `POST`, which is not cached by default. At 1M requests/day, REST offloads traffic to the edge, while GraphQL forces all 1M requests to hit the origin server.
3. **Explain persisted queries. What two problems do they solve?**
   Persisted queries replace the full GraphQL query string with a pre-registered hash. They solve caching by allowing clients to send `GET` requests with the hash, and they solve security by preventing attackers from executing arbitrary or excessively deep queries.
4. **Apollo normalized cache vs OkHttp HTTP cache — what's the conceptual difference?**
   OkHttp caches raw network responses by URL (HTTP cache). Apollo's normalized cache breaks down the JSON response and stores individual objects by `__typename` + `id`, acting like a local database where updating a user's name automatically updates all screens showing that user.
5. **Your API contract drifts between server and Android. Compare how OpenAPI + REST vs Apollo + GraphQL detect this.**
   OpenAPI specs are often manually maintained, allowing silent drift between backend code and client expectations that manifest as runtime crashes. Apollo reads the live server schema via introspection and generates Kotlin types at compile time; if the server contract breaks, the Android build fails immediately.
6. **Walk through optimistic updates in Apollo Kotlin. What happens on success vs failure?**
   The client instantly writes the expected mutation result (e.g., `likeCount + 1`) to the local Apollo cache, triggering immediate UI recomposition. If the network request succeeds, the cache is confirmed; if it fails, Apollo automatically rolls back the cache and the UI reverts.
7. **Real-time updates: GraphQL subscriptions vs REST + SSE. When pick each?**
   Use GraphQL subscriptions if the app is already heavily invested in the Apollo ecosystem and requires bidirectional WebSocket management. Use REST + SSE if the app only needs simple, one-way real-time updates and wants to leverage standard HTTP infrastructure.
8. **A team wants to switch from REST to GraphQL for "performance." Walk through the audit you'd run first.**
   Audit if the app actually suffers from massive over-fetching or N+1 round trips. If they already use sparse fieldsets (`?fields=`) and a BFF, the performance delta is negligible. Migrating just for "vibes" introduces massive caching and security complexities.
9. **Error handling: REST uses HTTP status codes; GraphQL returns 200 with `errors`. Why? What's the practical implication for the Android client?**
   GraphQL returns 200 because a query can partially succeed (e.g., profile loads, but related posts fail). The client must manually check `response.hasErrors()` because a 200 OK does not guarantee business logic success, unlike REST where a 4xx/5xx explicitly flags failure.
10. **Versioning: `/api/v2/users` vs schema deprecation. Compare the lifecycle costs of each.**
    REST's `/v2` allows a clean break but forces coordinated API migrations. GraphQL's field deprecation allows continuous, additive evolution without breaking endpoints, but requires strict telemetry (persisted query tracking) to know when an old Android client finally stops requesting a deprecated field.
11. **A new feature needs data from 5 microservices on one screen. REST + BFF or GraphQL? Justify.**
    If the mobile team wants to orchestrate the exact payload shape and the backend exposes a unified Graph, use GraphQL. If the backend doesn't have GraphQL, or if the payload needs custom server-side error mapping/business logic specific to mobile, build a REST + BFF.
12. **You're building an offline-first app with live UI updates. Walk through the Apollo + Flow + Compose pattern that delivers it.**
    The ViewModel executes a GraphQL query and calls `.watch().toFlow()`. The Composable collects this StateFlow. Any local mutation or incoming subscription updates the Apollo normalized cache, which automatically triggers `.watch()` to emit a new state, recomposing the UI instantly.
13. **Where does gRPC fit in this picture? Why isn't it usually picked for Android-to-backend calls?**
    gRPC provides typed, binary RPCs over HTTP/2 via Protobuf. It is avoided for Android-to-backend because it lacks native browser/CDN caching, proxy debugging is extremely difficult (unreadable binary), and the tooling (protoc, OkHttp workarounds) is much heavier than REST or GraphQL.

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
