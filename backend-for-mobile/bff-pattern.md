# Backend-for-Mobile (BFF) Pattern

> A Backend-for-Frontend (BFF) is a middleware server built specifically to serve a single client (e.g., the Android app). In a microservices architecture, forcing the mobile app to aggregate data from 5 different services drains the battery, blocks the UI with multiple loading states, and compounds latency. A Staff engineer recognizes that orchestration belongs on the server. The BFF pattern shifts the burden of multiple network calls, data filtering, and payload shaping from the underpowered mobile device to a high-speed data center.

---

## Overview

Historically, backends exposed generic, "one-size-fits-all" APIs. The Web app, the Android app, and the iOS app all consumed the exact same `/api/v1/users` endpoint.

As microservices took over, the Android app had to start acting like a database aggregator. To render the "Home" screen, the app had to call:
1. `AuthService` (to get permissions)
2. `UserService` (to get the profile)
3. `InventoryService` (to get product lists)
4. `RecommendationService` (to get personalized ads)

This is the **Orchestration Problem**. Doing this on a mobile device over a 3G connection is an architectural disaster.

The **BFF Pattern** solves this by placing a dedicated server (the Android BFF) between the mobile app and the microservices. The Android app makes *one* call to the BFF. The BFF makes the 4 internal calls over high-speed data center fiber, aggregates the result into a single, perfectly shaped JSON object, and sends it back to the phone.

At Staff level, a BFF is also a **compatibility boundary**. Backend microservices can rename fields, split services, or change internal error models without forcing the Android app to change immediately. The BFF owns the mobile contract: old app versions, fallback payloads, feature capability checks, semantic error envelopes, and partial-success behavior.

---

## 1. The Mobile Orchestration Problem

### The Native Android Implementation (Without BFF)
If the Android app has to do the orchestration, the ViewModel or Repository looks like this:

```kotlin
// BAD: Orchestration on the mobile client
suspend fun fetchHomeScreenData(): HomeState = try {
    coroutineScope {
        val profile = async { userApi.getProfile() }
        val inventory = async { inventoryApi.getProducts() }
        val promos = async { promoApi.getBanners() }
        val cart = async { cartApi.getCartCount() }
        HomeState.Success(profile.await(), inventory.await(), promos.await(), cart.await())
    }
} catch (e: CancellationException) {
    throw e
} catch (e: HttpException) {
    HomeState.Error
} catch (e: SerializationException) {
    HomeState.Error
} catch (e: IOException) {
    HomeState.Error
}
```

This all-required example deliberately fails the screen if one call fails. The catch surrounds `coroutineScope`: catching only `await()` inside it cannot recover a scope already cancelled by a failed child. Production code also classifies HTTP/decoding failures from its chosen client.

**Costs to measure on mobile:**
1. **Radio Wakeup:** Several concurrent requests may share connection and radio activity; extra work can increase energy, but request count is not a radio-wakeup count.
2. **Head-of-Line Blocking:** Competing payloads can increase transfer/decoding pressure; distinguish TCP head-of-line blocking from CPU or bandwidth contention.
3. **Over-fetching:** The `userApi` returns 50 fields, but the Home screen only needs `avatarUrl` and `firstName`. Unknown fields may be skipped without allocating their model values, although bytes and tokenization still cost work.
4. **Partial Failure:** Handling partial failures (e.g. promos fail, but inventory succeeds) on the client requires complex, stateful logic in the ViewModel.

---

## 2. The BFF Implementation

With a BFF, the backend team (or often, the mobile team themselves using Kotlin/Ktor or Node.js) builds an endpoint specifically for the Android Home Screen.

### Contract ownership

The BFF must be versioned and operated like a product API, not like throwaway glue code.

| Responsibility | Staff-level expectation |
|---|---|
| Old app support | Keep N-2/N-3 response shapes working, or document the explicit sunset policy |
| Capabilities | Gate new fields, component types, and actions behind client capabilities |
| Partial failures | Convert microservice failures into stable mobile UI states |
| Observability | Tag logs, traces, and SLIs by app version, endpoint, capability, and upstream dependency |
| Rollback | A backend rollback must not require an app rollback, because app rollback is usually impossible |

This is why ownership matters. If the mobile organization owns the BFF, Android engineers can evolve the screen contract with the same care they apply to client code. If a central backend team owns it, the team needs an explicit API review path, service-level objectives, and a deprecation policy for mobile contracts.

### Optional Upstream Boundary

This server example uses Ktor with `expectSuccess = true` and content negotiation. Its adapter surfaces status failures as `ResponseException`, converter failures as `ContentConvertException` (or a direct `SerializationException`), and transport failures as `IOException`. Only the optional promo dependency gets a fallback; required dependencies still fail the response through the BFF's reviewed error mapper.

```kotlin
suspend fun <T> optionalUpstream(load: suspend () -> List<T>): List<T> = try {
    load()
} catch (e: CancellationException) {
    throw e
} catch (e: ResponseException) {
    emptyList()
} catch (e: ContentConvertException) {
    emptyList()
} catch (e: SerializationException) {
    emptyList()
} catch (e: IOException) {
    emptyList()
}
```

The exception imports are `io.ktor.client.plugins.ResponseException`, `io.ktor.serialization.ContentConvertException`, `kotlinx.serialization.SerializationException`, `java.io.IOException`, and `kotlinx.coroutines.CancellationException`; another client needs its own error classification. Never turn cancellation, authentication for required data, or arbitrary programming errors into an apparently healthy complete response. A richer product can expose unavailable section metadata instead of an empty list.

### The BFF Server Logic (e.g., Ktor)
```kotlin
// Server-side BFF logic (running in AWS/GCP)
get("/android/v1/home") {
    // Upstream latency and deadlines are deployment-specific; measure them.
    val profile = internalUserClient.getProfile(userId)
    val inventory = internalInventoryClient.getProducts()
    val promos = optionalUpstream { internalPromoClient.getBanners() }

    // Shape the payload strictly for the Android UI
    val response = AndroidHomeResponse(
        greeting = "Hello, ${profile.firstName}",
        avatarUrl = profile.avatarUrl,
        items = inventory.map { it.toAndroidItem() },
        banners = promos.map { it.toAndroidBanner() }
    )

    call.respond(response)
}
```

### The Android Client Logic (With BFF)
The mobile code makes one call. These Android examples use Retrofit with a Kotlinx Serialization converter: handle `HttpException` and `SerializationException` as well as I/O failure, while cancellation propagates.

```kotlin
// GOOD: Client simply consumes the BFF payload
suspend fun fetchHomeScreenData(): HomeState {
    return try {
        // ONE request, shaped perfectly for the UI
        val response = bffApi.getHomeScreen()
        HomeState.Success(response)
    } catch (e: CancellationException) {
        throw e
    } catch (e: HttpException) {
        HomeState.Error
    } catch (e: SerializationException) {
        HomeState.Error
    } catch (e: IOException) {
        HomeState.Error
    }
}
```

---

## 3. Server-Driven UI (SDUI)

A BFF can support **Server-Driven UI**, but neither pattern requires the other.

If the BFF is already aggregating data specifically for the Android screen, why not have the BFF dictate *how* the screen should be laid out? This allows you to redesign the app's layout without shipping a new APK to the Play Store.

### The BFF SDUI Payload
```json
{
  "screenId": "home_feed",
  "components": [
    {
      "type": "HeroBanner",
      "data": { "imageUrl": "...", "title": "Summer Sale" }
    },
    {
      "type": "HorizontalCarousel",
      "data": {
        "items": [
          { "id": "1", "name": "Shoes", "price": "$99" }
        ]
      }
    }
  ]
}
```

### The Android Compose Implementation
The client validates supported components and owns accessibility, local state and safe actions. Required unknown components must trigger a supported fallback, not silently disappear.

```kotlin
@Composable
fun SduiScreen(components: List<SduiComponent>) {
    LazyColumn {
        items(components) { component ->
            when (component.type) {
                "HeroBanner" -> HeroBannerUI(component.data)
                "HorizontalCarousel" -> CarouselUI(component.data)
                "TextHeader" -> HeaderUI(component.data)
                else -> { /* Only optional components may be skipped; required ones need fallback. */ }
            }
        }
    }
}
```
**Staff Insight:** SDUI is incredibly powerful but extremely hard to maintain. Versioning components, handling animations, and managing local state (like text input fields) across server-driven architectures require massive engineering investment (e.g., Airbnb's Ghost Platform).

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The "God Endpoint"** | The BFF Home endpoint grows out of control, eventually downloading 5MB of data and taking 3 seconds to aggregate on the server. | Paginate the BFF, or split the BFF into logical UI zones (e.g., one call for the header, one for the feed). |
| **Logic Duplication** | The Android BFF and the iOS BFF have 95% identical aggregation logic, leading to bugs when a core microservice changes. | Extract shared orchestration logic into a common backend library, or use GraphQL as a unified BFF layer. |
| **BFF Bottleneck** | The mobile team has to wait for backend engineers to update the BFF before they can build the UI feature. | The Mobile team should *own* the BFF. Write the BFF in Kotlin (Ktor) or Node/TypeScript so mobile engineers can submit PRs to it. |

---

## 5. Common Pitfalls

### Pitfall 1: Leaking Internal Microservice Errors
If the internal `InventoryService` returns a `503 Service Unavailable`, the BFF must not simply forward the `503` to the mobile app. The mobile app doesn't know what "InventoryService" is.
*Fix:* The BFF must catch internal errors and either return a partial success (e.g., UI loads without inventory) or translate the error into a semantic mobile error envelope (e.g., `{"error": "CART_UNAVAILABLE"}`).

### Pitfall 2: Using the BFF as a Business Logic Layer
The BFF is an *orchestration* and *presentation* layer. It should not calculate taxes, verify passwords, or update database records.
*Fix:* If you are writing SQL queries or complex state machines in the BFF, you have created a Monolith. Push business logic down to the domain microservices.

---

## Probing Questions

1.  **GraphQL vs BFF:** GraphQL allows the client to define exactly the payload it wants, solving the over-fetching problem. In what scenarios is a dedicated Kotlin/Ktor BFF superior to exposing a single GraphQL endpoint to the mobile app?
2.  **Partial Failure:** The Android Home screen relies on a BFF that calls 5 microservices. Service #4 (Recommendations) goes down. Design the exact JSON response the BFF should return to the Android app, and explain how the Android `UiState` should model this partial failure.
3.  **Ownership:** According to Conway's Law, architectures reflect organizational structures. If the Backend team owns the BFF, what friction occurs during a mobile feature launch? How does having the Android team write the BFF in Kotlin change this dynamic?
4.  **Server-Driven UI:** In an SDUI architecture, how do you handle local, instantaneous state changes? For example, the user types into a Search Bar. Does every keystroke go to the BFF to re-render the components, or do you mix local state with SDUI?
5.  **Caching:** In a microservice architecture, caching happens at the database layer. In a BFF architecture, where should caching happen? Does the Android app cache the final BFF response, or does the BFF cache the individual microservice responses? What are the tradeoffs?

## Answer Key

1. **GraphQL vs BFF: GraphQL allows the client to define exactly the payload it wants, solving the over-fetching problem. In what scenarios is a dedicated Kotlin/Ktor BFF superior to exposing a single GraphQL endpoint to the mobile app?**
   A BFF is superior when mobile apps require complex server-side orchestration, custom fallback logic on partial failures, or when incorporating Server-Driven UI (SDUI). It also limits client-side complexity compared to managing Apollo/GraphQL caching, especially if the mobile team owns the BFF code.
2. **Partial Failure: The Android Home screen relies on a BFF that calls 5 microservices. Service #4 (Recommendations) goes down. Design the exact JSON response the BFF should return to the Android app, and explain how the Android `UiState` should model this partial failure.**
   The JSON should return success for available data and omit or provide a fallback for recommendations: `{"profile": {...}, "inventory": [...], "recommendations": []}`. The `UiState` models this by displaying the loaded content and hiding the recommendation section (or showing a localized "retry" UI), rather than throwing a global error.
3. **Ownership: According to Conway's Law, architectures reflect organizational structures. If the Backend team owns the BFF, what friction occurs during a mobile feature launch? How does having the Android team write the BFF in Kotlin change this dynamic?**
   If Backend owns the BFF, mobile feature launches are blocked by backend release cycles, API reviews, and differing priorities. If Android owns the BFF (e.g., in Kotlin/Ktor), they can iterate on the API contract in tandem with the UI, removing the bottleneck.
4. **Server-Driven UI: In an SDUI architecture, how do you handle local, instantaneous state changes? For example, the user types into a Search Bar. Does every keystroke go to the BFF to re-render the components, or do you mix local state with SDUI?**
   SDUI dictates layout and initial state, but local instantaneous interactions (like typing, dragging, or local validation) must be handled by the client's local state management (e.g., Compose `MutableState`). The client only sends the final action (e.g., "Submit Search") back to the BFF.
5. **Caching: In a microservice architecture, caching happens at the database layer. In a BFF architecture, where should caching happen? Does the Android app cache the final BFF response, or does the BFF cache the individual microservice responses? What are the tradeoffs?**
   Caching should ideally happen at both layers depending on volatility. The BFF caches slow microservice responses (e.g., static inventory) via Redis to reduce backend load. The Android app caches the final BFF response (via HTTP headers) to enable offline launch and instant UI rendering.

## Further Reading

- [Ktor HTTP response validation](https://ktor.io/docs/client-response-validation.html).
- [Retrofit HTTP exception source](https://github.com/square/retrofit/blob/trunk/retrofit/src/main/java/retrofit2/HttpException.java).

- [Kotlin coroutine exception propagation](https://kotlinlang.org/docs/exception-handling.html).
- [Structured concurrent calls](https://kotlinlang.org/docs/composing-suspending-functions.html).

- [`api-design-for-mobile.md`](api-design-for-mobile.md) — The physical mobile constraints that make BFFs necessary.
- [`graphql-vs-rest.md`](graphql-vs-rest.md) — How GraphQL offers an alternative to dedicated BFF servers.
- [`../android/architecture/state-management.md`](../android/architecture/state-management.md) — How to model the BFF's response into a Jetpack Compose `UiState`.
