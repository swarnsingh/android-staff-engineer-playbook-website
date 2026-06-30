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

---

## 1. The Mobile Orchestration Problem

### The Native Android Implementation (Without BFF)
If the Android app has to do the orchestration, the ViewModel or Repository looks like this:

```kotlin
// BAD: Orchestration on the mobile client
suspend fun fetchHomeScreenData(): HomeState {
    return coroutineScope {
        // Launch 4 simultaneous network requests over a mobile radio
        val profileDeferred = async { userApi.getProfile() }
        val inventoryDeferred = async { inventoryApi.getProducts() }
        val promosDeferred = async { promoApi.getBanners() }
        val cartDeferred = async { cartApi.getCartCount() }
        
        try {
            // Wait for the SLOWEST request to finish
            HomeState.Success(
                profile = profileDeferred.await(),
                inventory = inventoryDeferred.await(),
                promos = promosDeferred.await(),
                cartCount = cartDeferred.await()
            )
        } catch (e: Exception) {
            // If ANY request fails, the entire screen fails!
            HomeState.Error
        }
    }
}
```

**Why this fails on mobile:**
1. **Radio Wakeup:** Making 4 requests keeps the cellular radio active longer.
2. **Head-of-Line Blocking:** HTTP/2 helps, but multiple massive JSON payloads competing for bandwidth will stutter.
3. **Over-fetching:** The `userApi` returns 50 fields, but the Home screen only needs `avatarUrl` and `firstName`. The Android CPU wastes time parsing data it throws away.
4. **Partial Failure:** Handling partial failures (e.g. promos fail, but inventory succeeds) on the client requires complex, stateful logic in the ViewModel.

---

## 2. The BFF Implementation

With a BFF, the backend team (or often, the mobile team themselves using Kotlin/Ktor or Node.js) builds an endpoint specifically for the Android Home Screen.

### The BFF Server Logic (e.g., Ktor)
```kotlin
// Server-side BFF logic (running in AWS/GCP)
get("/android/v1/home") {
    // These calls happen over 10Gbps internal data center network
    // Latency is <5ms
    val profile = internalUserClient.getProfile(userId)
    val inventory = internalInventoryClient.getProducts()
    val promos = try {
        internalPromoClient.getBanners()
    } catch (e: Exception) {
        emptyList() // Server handles partial failure gracefully!
    }
    
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
The mobile code collapses into a single, clean network call.

```kotlin
// GOOD: Client simply consumes the BFF payload
suspend fun fetchHomeScreenData(): HomeState {
    return try {
        // ONE request, shaped perfectly for the UI
        val response = bffApi.getHomeScreen() 
        HomeState.Success(response)
    } catch (e: Exception) {
        HomeState.Error
    }
}
```

---

## 3. Server-Driven UI (SDUI)

The ultimate evolution of the BFF pattern is **Server-Driven UI**. 

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
The Android app acts as a "dumb renderer" that loops over the components sent by the BFF.

```kotlin
@Composable
fun SduiScreen(components: List<SduiComponent>) {
    LazyColumn {
        items(components) { component ->
            when (component.type) {
                "HeroBanner" -> HeroBannerUI(component.data)
                "HorizontalCarousel" -> CarouselUI(component.data)
                "TextHeader" -> HeaderUI(component.data)
                else -> { /* Ignore unknown components (forward compatibility!) */ }
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

## Further Reading

- [`api-design-for-mobile.md`](api-design-for-mobile.md) — The physical mobile constraints that make BFFs necessary.
- [`graphql-vs-rest.md`](graphql-vs-rest.md) — How GraphQL offers an alternative to dedicated BFF servers.
- [`../android/architecture/state-management.md`](../android/architecture/state-management.md) — How to model the BFF's response into a Jetpack Compose `UiState`.
