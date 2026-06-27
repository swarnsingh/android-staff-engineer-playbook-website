# API Design for Mobile

## Overview

A Junior Engineer consumes whatever REST API the backend team provides, ignoring the fact that it requires 14 round-trips to render a single screen, and assumes "the network is reliable."

A Staff Engineer understands that standard REST API design principles (Hypermedia, HATEOAS, strict Resource orientation) were built for Desktop Web Browsers on wired fiber-optic connections. Mobile networks are high-latency, packet-loss-prone environments. Designing an API for mobile requires violating pure REST principles in favor of pragmatism, payload reduction, and state synchronization.

## Why It Matters

Consider a classic REST API for a social media app:
1. `GET /users/123` (Get user profile)
2. `GET /users/123/posts` (Get IDs of user's posts)
3. `GET /posts/991` (Get Post 991)
4. `GET /posts/992` (Get Post 992)

If a user is on a train switching cellular towers, their phone takes 500ms just to establish a TLS connection. The N+1 query problem shown above will take 4-5 seconds to execute on mobile, compared to 50ms on a desktop. The user will see a loading spinner for 5 seconds, assume the app is broken, and uninstall it. 

Mobile APIs must be designed to minimize TCP round-trips above all else.

## Historical Context

- **SOAP / XML (Pre-2010):** Massive, strict, heavily typed XML contracts. Required massive parsing overhead on early CPUs.
- **Pure REST (2010-2015):** The era of strict Resource-based routing (`GET /authors/1/books/2`). It forced mobile apps to make chaining network calls, leading to the N+1 problem.
- **Pragmatic Mobile REST (2015-Present):** Backend teams realized mobile needed specialized endpoints. Introduction of `?include=` query parameters to fetch relations in a single call, and [Backend-For-Frontend (BFF)](bff-pattern.md) patterns.
- **GraphQL (Present):** The ultimate solution to REST limitations, allowing the client to specify exactly the shape of the graph it wants in one trip. (See [GraphQL](../android/networking-and-security/graphql.md)).

## First Principles

1.  **Latency vs Bandwidth:** Bandwidth is how much data fits in the pipe (e.g., 4G is wide). Latency is how long it takes for a drop of water to travel through the pipe. Mobile networks have terrible latency. *Minimizing round-trips is vastly more important than minimizing JSON size.*
2.  **Idempotency:** A network call is idempotent if making the exact same call 5 times has the exact same result on the server as making it once. (Crucial for Mobile Retries).
3.  **Partial Responses:** Allowing the client to ask the server to strip out useless JSON fields to save parsing time and battery.
4.  **Versioning:** Mobile apps cannot be force-updated easily. An API must support multiple versions simultaneously for years.

## Mental Model

Think of designing a Mobile API like **Ordering at a Drive-Thru**.
- **Pure REST:** You pull up to the window. You ask for a Burger. The cashier hands you a burger. You pull around the building, wait in line again, and ask for Fries. You pull around again, wait in line, and ask for a Coke. (Too many round trips).
- **Mobile API:** You pull up to the window and say "I want Meal #4". The cashier hands you a box containing a Burger, Fries, and a Coke all at once. (One round trip, aggregated data).

## Internal Mechanics

### 1. Eliminating the N+1 Problem (Compound Documents)

If the UI requires a User and their recent Posts, the API must return it in a single HTTP request.

```http
// Pragmatic REST using query expansion
GET /api/v1/users/123?include=posts,followers

// Response
{
  "id": "123",
  "name": "Jane",
  "posts": [
    { "id": "991", "text": "Hello" }
  ],
  "followers": 50
}
```

This violates strict REST (which dictates that `/users/` should only return User primitives), but it saves 500ms of latency and completely eliminates the risk of the first network call succeeding but the second call failing due to a tunnel dropout.

### 2. Idempotency Keys (Handling the Tunnel Dropout)

A user taps "Submit Order". The Android app sends a `POST /checkout`. The server receives it, charges the credit card, and sends the `HTTP 200 OK` response.
*But the user drove into a tunnel right as the server replied.*
The Android app throws a `SocketTimeoutException`. The app thinks the order failed. The user taps "Submit Order" again. They are charged twice.

A Staff Engineer mandates **Idempotency Keys** for all state-mutating APIs.

```kotlin
// Android App generates a unique UUID for this specific button press
val idempotencyKey = UUID.randomUUID().toString()

val request = Request.Builder()
    .url("https://api.com/checkout")
    .addHeader("Idempotency-Key", idempotencyKey)
    .post(body)
    .build()
```

When the user taps "Submit" the second time (due to the timeout), the app sends the *exact same UUID*. The backend database sees the UUID, realizes it already charged the card, skips the billing phase, and just returns the previous `HTTP 200 OK`. 

### 3. Sparse Fieldsets (Partial Responses)

If a `Product` object contains 100 fields, but the search list UI only needs `id`, `name`, and `price`, the mobile app should not pay the battery/CPU cost of parsing 97 unused fields.

```http
// The Client dictates the payload shape
GET /api/v1/products?fields=id,name,price

// Response
{
  "data": [
    { "id": "1", "name": "Laptop", "price": 999.00 }
  ]
}
```

*(Staff Note: This is exactly what GraphQL does natively, but if your company is stuck on REST, Sparse Fieldsets are mandatory for mobile performance).*

## Tradeoffs

**Strict Versioning vs API Evolution**

- **URL Versioning (`/v1/users`, `/v2/users`):**
    - *Pros:* Extremely explicit. The Android client knows exactly what JSON shape it will receive.
    - *Cons:* The backend team hates maintaining `v1`, `v2`, and `v3` codebases simultaneously. They will eventually deprecate `v1`. When they do, users on 3-year-old Android devices whose phones cannot update to the new APK will experience a fatal app crash.
- **API Evolution (GraphQL / Add-Only REST):**
    - *Pros:* You never version the URL. You only ever *add* new fields. You never delete or rename old fields. Old apps continue to work forever.
    - *Cons:* The backend database models become littered with legacy fields (`firstName`, `new_first_name`, `firstNameV3`). 

*Staff Decision:* For mobile, API Evolution is vastly superior to URL Versioning. Because you cannot force a user to update an Android app, URL Versioning is a ticking time bomb.

## Failure Modes

- **The Massive Payload Freeze:**
  The backend team returns a 2MB JSON array of 10,000 items in a single API call. When Android's `Gson` or `Moshi` attempts to parse a 2MB string into 10,000 Kotlin objects on a mid-range phone, the CPU locks up for 3 seconds, causing severe [Jank](../android/performance/jank.md), and often triggering an `OutOfMemoryError`.
  *(Fix: The API MUST implement [Pagination](../mobile-system-design/pagination.md). The backend should never return more than 20-50 items per request).*
- **Assuming Sequential Execution:**
  A developer fires `POST /uploadImage` and `POST /updateProfile` simultaneously, assuming the server will process the image first. The network routes the packets differently, the profile updates first, fails because the image doesn't exist, and crashes.
  *(Fix: APIs should support batching, or the client must strictly chain dependent calls, absorbing the latency hit).*

## Staff Engineer Thinking

When reviewing an API Contract (Swagger/OpenAPI spec) proposed by the backend team, a Staff engineer fights for the mobile client.

1.  **Enforce UI-Driven Payloads:** If I see an API contract that looks exactly like the backend SQL database schema, I reject it. The API should look like the Android UI. If the UI needs a pre-calculated "Time since posted" (e.g., "5 mins ago"), the backend should calculate it and send it. Do not send `2024-10-01T12:00:00Z` and force 10 million Android phones to run DateTime math 60 times a second.
2.  **Status Codes vs Business Errors:** Standard REST uses HTTP 404 for "Not Found". But what if the HTTP call hit a proxy that returned 404? Did the Proxy fail, or did the API fail? I ensure that HTTP 200 is used for successful *network* transit, and the JSON payload contains a strict `business_error_code` (e.g., `USER_NOT_FOUND_104`) so the Android app can differentiate between a network failure and a logic failure.
3.  **Deprecation Horizons:** I monitor the analytics of our oldest app versions. If the backend team wants to drop an old API field, I query the APM to prove that 4% of our revenue still comes from users on Android 8 running a 4-year-old APK. The field stays.

## Common Misconceptions

- **"REST means one resource per endpoint."** In an academic computer science paper, yes. In a production mobile environment, adhering to this rule will destroy your app's performance. Pragmatic mobile APIs group resources to save TCP handshakes.
- **"GZIP solves payload size problems."** GZIP compresses the JSON over the network, saving bandwidth. However, the Android phone still has to decompress it back into a massive String in RAM, and then parse that massive String into Kotlin objects. GZIP does not save CPU or Memory. Only sending less data saves CPU.

## Probing Questions

1.  Explain why minimizing network latency (round-trips) is significantly more critical for a mobile application than minimizing total bandwidth payload size.
2.  What is the "N+1 Query Problem" in REST API design, and how does the concept of "Compound Documents" (`?include=`) solve it for mobile clients?
3.  Describe the specific edge-case scenario where an Android device loses cellular connection *after* an API processes a payment, and how an Idempotency Key prevents double-billing.
4.  Why is URL versioning (`/v1/api`) inherently dangerous for mobile applications compared to web applications?
5.  What are "Sparse Fieldsets", and how do they protect a mobile device's CPU and battery?
6.  Explain the architectural anti-pattern of forcing a mobile client to perform heavy mathematical calculations (e.g., aggregating 50 prices into a Total) instead of doing it on the backend.
7.  If a backend API returns a 5MB JSON payload, why does GZIP compression fail to protect the Android device from `OutOfMemoryError`s during parsing?
8.  Describe why a Staff Engineer might advocate for HTTP 200 OK responses that contain explicit "Business Error Codes" in the JSON body, rather than relying solely on HTTP 4xx/5xx status codes.
9.  How does the Backend-For-Frontend (BFF) pattern act as a physical manifestation of Mobile API Design principles?
10. What is the fundamental difference in API contract design between an endpoint that returns a literal Database Row versus an endpoint that returns a UI State Object?

## Further Reading

- [`bff-pattern.md`](bff-pattern.md) — The cloud architecture used to implement these mobile-specific API designs.
- [`graphql.md`](../android/networking-and-security/graphql.md) — A query language that natively solves Over-fetching and N+1 routing.
- [`idempotency.md`](../distributed-systems/idempotency.md) — Deep dive into the distributed systems math behind Idempotency Keys.
