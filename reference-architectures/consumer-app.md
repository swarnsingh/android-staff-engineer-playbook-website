# Blueprint: The Consumer App (B2C)

## 1. Architectural Signature
A Consumer App (e.g., Spotify, Duolingo, Tinder) is optimized for **Growth, Engagement, and Acquisition**. 
The architecture prioritizes a frictionless onboarding experience, rapid UI iterations (A/B testing), and psychological stickiness. Data consistency (CAP theorem) is secondary; it is acceptable if a user's "Like" takes 5 seconds to sync to the server, as long as the UI feels instantaneous (Optimistic Updates).

**Core Trade-off:** UX Fluidity & Analytics > Absolute Data Consistency.

## 2. Component Blueprint

### Presentation Layer (The Funnel)
- **Framework:** Jetpack Compose (mandatory for UI velocity).
- **Pattern:** MVI (Model-View-Intent). State must be unidirectional to handle complex, asynchronous animations and loading states without flickering.
- **Onboarding:** The 'First 5 Minutes' are sacred. The architecture must support **Anonymous Sessions**; users must be able to explore the app without creating an account.
- **Deep Linking:** Aggressive implementation of Android App Links. Marketing emails must transition the user directly into the core loop of the app, bypassing the Home screen entirely.

### Domain Layer (The Engagement Engine)
- **A/B Testing SDK:** (e.g., LaunchDarkly, Firebase Remote Config). The Domain layer must constantly query feature flags to determine which variant of a Use Case to execute.
- **Gamification Mechanics:** Local state machines tracking streaks, points, or badges.
- **Push Notification Router:** A dedicated module to handle FCM Data Payloads, categorized by channels (e.g., "Re-engagement", "Social Activity").

### Data Layer (Optimistic & Event-Driven)
- **Local Persistence:** Room (SQLite) acting as the Single Source of Truth.
- **Network Strategy:** **Optimistic Updates**. When a user "Likes" a post, the Data layer immediately updates the local Room DB (triggering UI refresh) and fires the API request in the background. If the API fails, it silently reverts the local state or queues it for retry.
- **Telemetry Pipeline:** A massive, high-throughput pipeline for Analytics events (Mixpanel, Amplitude). Every swipe, scroll, and click is buffered locally and batched to the server to feed the Data Science models.

## 3. Infrastructure & DevOps
- **Release Cadence:** Weekly Release Train. High velocity is required for continuous experimentation.
- **App Size:** Must be kept small (< 30MB) using App Bundles. High app size directly correlates with high abandonment rates during acquisition campaigns in emerging markets.
- **Crash Gating:** Aggressive. A crash in the onboarding funnel costs real marketing dollars (Cost Per Acquisition - CPA).

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The "Cold Start" Drop-off
*Problem:* The app takes 4 seconds to load because it initializes 15 different analytics, marketing, and crash-reporting SDKs synchronously. Users abandon the app before seeing the first screen.
*Solution:* **The Dependency DAG**. Triage SDKs into Critical (Crashlytics, DI), Async (Analytics, DB), and Lazy (Marketing, Ads) phases. Use `IdleHandler` to initialize Lazy SDKs only when the CPU is completely free.

### Bottleneck 2: The A/B Test Flicker
*Problem:* The app fetches an A/B test configuration from the network on startup. The UI renders the "Blue Button", the network response arrives 500ms later, and the UI suddenly repaints to the "Red Button". This destroys trust.
*Solution:* **Client-Side Hashing & Session Stickiness**. A/B tests must be evaluated synchronously using deterministic hashing (MurmurHash). If remote config is used, updates must be deferred to the *next* app session to guarantee UI stability during the current session.

### Bottleneck 3: The Anonymous to Authenticated Migration
*Problem:* A user plays a game anonymously for 3 days, earning 500 coins. On day 4, they create an account. The backend creates a new User ID with 0 coins. The user loses their progress and uninstalls.
*Solution:* **Identity Stitching Architecture**. The local DB must tag all data with a `device_id`. When the user finally authenticates, the API payload must include a `merge_data_from_device_id` flag. The backend stitches the anonymous history into the new authenticated profile, and returns the merged state to the client.

## 5. Summary of Technologies
- **UI:** Compose, MVI, Lottie (Animations), Navigation Component.
- **Data:** Room, Retrofit, Kotlin Coroutines/Flow.
- **Telemetry:** Firebase Analytics, Crashlytics, LaunchDarkly/Split.io.
- **Background:** WorkManager (for analytics batching and silent syncs).

## Further Reading
- [`app-startup.md`](../mobile-system-design/app-startup.md)
- [`a-b-testing-infrastructure.md`](../mobile-system-design/a-b-testing-infrastructure.md)
- [`analytics-sdk.md`](../mobile-system-design/analytics-sdk.md)
