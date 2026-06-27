# Blueprint: The E-Commerce App (B2C Scale)

## 1. Architectural Signature
An E-Commerce App (e.g., Amazon, Nike, Shopify Consumer) is optimized for **Conversion Rate, Catalog Discovery, and Media Delivery**.
The architecture prioritizes blazing-fast image loading, deep linking attribution (for ad campaigns), and a frictionless checkout funnel. Network failures during catalog browsing are annoying; network failures during Checkout are catastrophic.

**Core Trade-off:** Image Quality & Caching vs App Size & Memory (OOMs).

## 2. Component Blueprint

### Presentation Layer (The Catalog)
- **Framework:** Jetpack Compose (ideal for dynamic feeds) combined with **Server-Driven UI (SDUI)**. Marketing needs to change the Homepage layout daily without an app release.
- **Image Pipeline:** A robust image loading library (Coil or Glide) configured with strict memory limits and a massive disk cache. 
- **Deep Linking:** The router must handle Android App Links, deferred deep links (Branch.io), and preserve the "Intent" (e.g., automatically applying a 10% discount code parsed from the URL) across the app installation gap.

### Domain Layer (The Cart & Recommendations)
- **A/B Testing Engine:** Heavy reliance on client-side deterministic hashing (MurmurHash) for rapid UI experiments without blocking the main thread.
- **Cart State Machine:** A localized state machine that handles optimistic updates for adding to the cart, but pessimistic validation during the final checkout phase.

### Data Layer (The Hybrid Cache)
- **Local Persistence:** Room (SQLite) is used heavily for caching the user's Cart, Wishlist, and browsing history.
- **Network Strategy:** `Stale-While-Revalidate`. When opening the Homepage, instantly render the cached JSON from disk (stale), while firing a background request to fetch the latest sales (revalidate), and cross-fading the UI when it arrives.
- **Analytics:** Extremely high fidelity. Every single product impression (when an image enters the viewport) is logged to calculate conversion metrics.

## 3. Infrastructure & DevOps
- **Release Cadence:** Weekly trains, but strictly driven by Feature Flags to decouple marketing campaigns from binary releases.
- **Kill Switches:** Mandatory for payment gateways. If Stripe goes down, the app must degrade to PayPal instantly via Remote Config.
- **App Size:** Strictly managed via App Bundles (dynamic feature modules for heavy/rare features like AR shoe fitting).

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The OutOfMemoryError (OOM) Bitmap Crash
*Problem:* The user scrolls rapidly through a list of 500 shoes. The app crashes with `java.lang.OutOfMemoryError`. The image loading library is trying to hold 500 high-resolution bitmaps in RAM simultaneously.
*Solution:* **The CDN Contract & Viewport Paging**.
1. The app must never request `shoe_original.jpg` (which might be 4MB).
2. The Backend must provide an Image CDN (like Cloudinary or Imgix).
3. The app requests a mathematically exact crop based on the device's screen density: `cdn.com/shoe.jpg?w=400&h=400&fm=webp`.
4. The Image Loader (Coil) uses a Memory Cache sized relative to the device's physical RAM (e.g., 15%), and a Disk Cache for the rest.
5. The Compose `LazyColumn` or `RecyclerView` aggressively recycles views/composables, forcing the Image Loader to drop references to bitmaps that have left the screen, allowing the Garbage Collector to reclaim them.

### Bottleneck 2: The Checkout Race Condition
*Problem:* The user has 1 item left in stock in their cart. They are on a slow 3G connection. They tap "Pay" three times rapidly in frustration. The app fires 3 concurrent API requests. The backend charges their credit card 3 times.
*Solution:* **Idempotency Keys**.
The Android app must generate a unique UUID (the Idempotency Key) at the start of the Checkout flow. Every time the user taps "Pay", the app attaches this exact same UUID in the HTTP Header: `Idempotency-Key: <UUID>`. The backend sees the first request, processes it, and saves the UUID to a cache. When the 2nd and 3rd requests arrive 50ms later, the backend sees the duplicate UUID, rejects the charge, and returns the cached "Success" response from the first request.

### Bottleneck 3: The Thundering Herd (Flash Sales)
*Problem:* Marketing sends a Push Notification to 10 million users for a "Flash Sale". 5 million users open the app at the exact same second. The API Gateway crashes.
*Solution:* **Push Notification Jitter & Edge Caching**.
1. The backend must "smear" the push delivery over 15 minutes.
2. The Android app must rely on HTTP `Cache-Control` headers. When 5 million users request `/api/homepage`, the request must be absorbed by a CDN (Cloudflare) at the Edge, never reaching the core origin servers.
3. If the backend *does* fail, the Android app must implement exponential backoff with jitter on its retries, preventing the app itself from DDoSing the recovering server.

## 5. Summary of Technologies
- **UI:** Compose, Server-Driven UI (SDUI), Coil/Glide.
- **Data:** Retrofit, Room, Branch.io (Deferred Deep Links).
- **Architecture:** MVI, Stale-While-Revalidate caching pattern.
- **Performance:** App Bundles, Idempotency Keys, Exponential Backoff.

## Further Reading
- [`app-bundles.md`](../release-engineering/app-bundles.md) (How to keep the app small).
- [`a-b-testing-infrastructure.md`](../mobile-system-design/a-b-testing-infrastructure.md) (Client-side evaluation).
- [`deep-links-and-universal-links.md`](../mobile-system-design/deep-links-and-universal-links.md) (Attribution and Branch.io).
