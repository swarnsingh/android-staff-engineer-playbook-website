# ADR 005: GraphQL vs REST for the Mobile API Gateway

## Context
The Android application has grown to interface with 15 different backend microservices. Currently, the app uses standard **REST APIs** (via Retrofit).

This architecture is causing three significant bottlenecks on mobile:
1.  **Over-fetching (Payload Bloat):** To render the Home Feed, the app calls `GET /users/me`. The backend returns a 50KB JSON payload containing the user's entire history, settings, and addresses, even though the UI only needs the `avatar_url` and `first_name` (1KB). This wastes bandwidth, battery, and JSON parsing time.
2.  **Under-fetching (The Waterfall Problem):** To render a Post with its Author and Comments, the app makes 3 sequential requests: `GET /post/1`, then `GET /users/{author_id}`, then `GET /comments?postId=1`. On a slow 3G network (200ms latency), this waterfall results in a 600ms minimum delay before the UI can render.
3.  **BFF (Backend-For-Frontend) Maintenance:** To solve the above, the Backend team creates custom endpoints for every mobile screen (e.g., `GET /mobile/home-feed-aggregated`). This tightly couples the backend to the UI layout, requiring a backend deployment every time the mobile team adds a new field to the screen.

The engineering team is evaluating whether to migrate the primary mobile communication layer to **GraphQL** (via Apollo Android).

## Alternatives Considered

### 1. REST with Aggregation (BFF)
-   **Pros:** Well-understood by all engineers. Excellent support for standard HTTP caching (CDNs).
-   **Cons:** Requires constant coordination between mobile and backend teams to build and maintain bespoke endpoints for every UI variation. Doesn't fundamentally solve over-fetching unless the backend maintains multiple versions of the same payload.

### 2. GraphQL
-   **Pros:** 
    -   **Declarative Data Fetching:** The client requests exactly the fields it needs, and nothing more.
    -   **Single Request:** Resolves the waterfall problem by allowing the client to fetch nested relations (Post -> Author -> Comments) in a single round-trip.
    -   **Type Safety:** The GraphQL schema automatically generates strongly-typed Kotlin data models (via Apollo), eliminating `NullPointerException`s caused by undocumented REST API changes.
-   **Cons:** 
    -   **Caching Complexity:** Standard HTTP caching at the CDN level is broken because GraphQL uses `POST` requests and the URL path is always `/graphql`.
    -   **N+1 Problem:** If the backend resolvers are poorly written, a single GraphQL query from mobile can cause the backend to execute 1,000 SQL queries.
    -   **Learning Curve:** Requires adopting Apollo Android and learning GraphQL query syntax.

## Decision
We will migrate the primary Mobile API Gateway to **GraphQL**, replacing Retrofit with the Apollo Android client.

1.  **Read-Heavy Feeds:** All complex, read-heavy screens (Home Feed, Profile, Search) will transition to GraphQL to eliminate the Waterfall problem and reduce payload bloat.
2.  **Apollo Code Generation:** We will rely exclusively on Apollo's code generation to create Kotlin models from `.graphql` files. Manual parsing of JSON objects is deprecated.
3.  **Exceptions (REST Remains):** Binary uploads (Video/Image uploads) and highly cacheable static assets will continue to use REST.
4.  **Backend Implementation:** The backend will implement a Federated GraphQL API Gateway that sits in front of the existing REST microservices, meaning the core backend services do not need to be rewritten immediately.

## Consequences
-   **Positive:** Mobile bandwidth consumption will decrease significantly due to the elimination of over-fetching.
-   **Positive:** Mobile engineering velocity will increase, as UI developers can add new data fields to their screens by modifying a client-side query, rather than filing a Jira ticket for the backend team.
-   **Positive:** Retrofit's runtime JSON parsing errors will be replaced by Apollo's compile-time type checking.
-   **Negative:** We lose the ability to use simple Edge CDNs (like Cloudflare) to cache API responses based on URLs. The backend must implement robust caching logic (e.g., Apollo Federation / Redis caching on the Gateway) to absorb the load.
-   **Negative:** The APK size will slightly increase due to the inclusion of the Apollo runtime.
