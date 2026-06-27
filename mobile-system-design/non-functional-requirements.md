# Non-Functional Requirements (NFRs)

## Overview

A Junior Engineer is obsessed with Functional Requirements: *"Can the user upload a photo?"* *"Does the button turn green?"*

A Staff Engineer is obsessed with **Non-Functional Requirements (NFRs)**: *"Does the photo upload succeed if the user is on a 2G network?"* *"Does the app drain 10% of the battery in 5 minutes while uploading?"* *"Is the photo encrypted at rest?"*

Functional requirements define *what* the system does. Non-Functional Requirements define *how well* the system does it under constraints. In mobile engineering, the physical constraints (Battery, CPU, Network, Storage) are so severe that the NFRs completely dictate the architecture.

## Why It Matters

If you are asked to design Twitter/X for Android:
- **Functional Requirement:** A user can view a timeline of tweets.
- **Architecture 1:** Make a `GET /timeline` API call every time the app opens. (Works perfectly).
- **NFR Introduced:** The app must load the timeline instantly (< 100ms) even if the user opens it in a subway tunnel with zero network connection.
- **Architecture 2 (Forced by NFR):** The app must implement an Offline-First Room database, a background `WorkManager` synchronization job, and a Repository pattern that exposes a `Flow` from the local disk, hiding the network latency entirely.

The NFR forced the architecture to change from a simple 1-tier design to a complex 3-tier offline-first design.

## The Core Mobile NFRs

Every Mobile System Design interview and every major feature architecture review must explicitly define these NFRs before code is written.

### 1. Performance (Latency & Jank)
- **Metric:** Time to Interactive (TTI), Frame Rate (FPS), App Startup Time (Cold/Warm/Hot).
- **Questions:** Does this screen need to render at a strict 60fps? Does the API need to return in <200ms? How fast must the app open from a cold boot?
- **Architectural Impact:** Dictates the use of Baseline Profiles, local SQLite caching, Pagination (Paging 3), and View/Compose complexity.

### 2. Battery & Power Consumption
- **Metric:** Milliamp-hours (mAh) drained per hour of active use. Wake-locks acquired.
- **Questions:** Does this app require constant GPS tracking? Does it maintain a persistent WebSocket?
- **Architectural Impact:** Dictates the shift from WebSockets to Push Notifications (FCM). Dictates the shift from Polling to Server-Sent Events (SSE). Forces the batching of network requests to allow the cellular radio to sleep.

### 3. Network Resilience & Bandwidth
- **Metric:** Data consumed (MB/month). Success rate on 3G vs 5G.
- **Questions:** Are we targeting users in emerging markets with metered data plans? What happens when a network request fails halfway through?
- **Architectural Impact:** Dictates the use of Protocol Buffers (gRPC) over JSON. Dictates the use of `WorkManager` for guaranteed background execution with Exponential Backoff. Dictates the use of Idempotency Keys.

### 4. Storage & Memory (RAM) Footprint
- **Metric:** APK Download Size (MB). RAM allocated at peak usage. Local disk space consumed.
- **Questions:** Will this app be installed on $50 budget phones with 2GB of RAM and 16GB of storage? 
- **Architectural Impact:** Dictates the use of R8/ProGuard shrinking, dynamic feature delivery (App Bundles), caching eviction policies (LRU cache for images), and FlatBuffers for zero-copy parsing.

### 5. Security & Privacy
- **Metric:** Data encryption at rest/transit. GDPR/CCPA compliance.
- **Questions:** Does this app handle medical data (HIPAA) or credit cards (PCI-DSS)? 
- **Architectural Impact:** Dictates the use of the Android Keystore, EncryptedSharedPreferences, SQLCipher, Certificate Pinning, and strict PII removal from APM logging tools.

### 6. Accessibility (a11y)
- **Metric:** Screen reader compatibility, contrast ratios, tap target sizes.
- **Questions:** Can a blind user navigate the checkout flow using TalkBack?
- **Architectural Impact:** Dictates strict adherence to semantic UI trees in Jetpack Compose, content descriptions, and scalable font sizes (SP instead of DP).

## Mental Model

Think of Functional Requirements as the **Blueprint of a Car** (It has 4 wheels, an engine, and seats).

Think of Non-Functional Requirements as the **Laws of Physics and the Environment**.
- If the environment is a perfectly flat racetrack (Desktop Web), the car can be built entirely for speed, with slick tires and minimal suspension.
- If the environment is a rocky mountain in the middle of a blizzard (Mobile Networks and Battery Limits), that exact same car will crash instantly. You must redesign it with 4-wheel drive, snow chains, and a massive battery.

## Internal Mechanics

### Establishing the SLAs (Service Level Agreements)

A Staff Engineer does not say, "The app should be fast." They define mathematical SLAs.

*   "The P90 (90th percentile) Cold Start time must be < 1500ms."
*   "The Home Screen must hit 60fps rendering, allowing no more than 5 dropped frames (Jank) per minute of scrolling."
*   "The application must never consume more than 2% of the total device battery per hour in the background."

Once these mathematical NFRs are locked in, you set up your CI/CD pipelines and APM tools (New Relic / Firebase Performance) to alert you the exact second a Pull Request violates them.

## Tradeoffs

**The Triangle of Truth: Speed, Quality, Cost (Pick Two)**

NFRs constantly fight each other. You cannot have everything.

- **Offline Support vs Storage Space:** You want the app to work offline (Great NFR). So you download 500MB of data into a local Room database. The user's phone runs out of storage space and they uninstall the app (Failed NFR).
- **Security vs Battery:** You want absolute security, so you use a 4096-bit RSA key to encrypt every single database row locally. The CPU thrashes to encrypt/decrypt on every scroll event, the phone overheats, and the battery dies in 40 minutes.
- **Bandwidth vs Code Complexity:** You want to save user bandwidth, so you implement a complex Delta-Sync algorithm where the server only sends the exact bytes that changed. The backend takes 3 months to build, and the mobile code is a nightmare of conflict resolution. (Simple JSON would have taken 3 days).

*Staff Decision:* A Staff Engineer's primary job is negotiating these tradeoffs with Product Management. "If you want this feature to work fully offline, it will increase our APK size by 10MB and delay the launch by 2 months. Do we proceed?"

## Failure Modes

- **Testing Only on Emulators / Flagships:**
  Developing exclusively on a $1200 Pixel 8 Pro on a gigabit corporate Wi-Fi network.
  *(Failure: The app perfectly passes all Functional Requirements. The moment it launches in India on a $100 device with 2GB RAM on a 3G network, it crashes with OOM (Out of Memory) and SocketTimeouts. You failed the NFRs).*
- **The APM Blindspot:**
  You define strict NFRs for latency and crash rates, but you never actually implement New Relic or Firebase Performance Monitoring.
  *(Failure: If you don't measure the NFR in production, it does not exist. You are flying blind).*

## Staff Engineer Thinking

When reviewing an Architecture Document, I immediately skip the Functional section and look for the NFRs.

1.  **Define the Limits:** If an engineer proposes fetching a list of users, my first question is: "What is the maximum limit?" If they say "100", I say "Fine." If they say "100,000", I mandate Pagination and a Room database. NFRs dictate the solution.
2.  **Graceful Degradation:** The core philosophy of mobile NFRs. If the network goes from 5G to 2G, the app should not crash. It should gracefully degrade (e.g., stop downloading high-res images, switch to text-only mode). If the battery hits 10%, the app should gracefully stop background syncs.
3.  **The "5 Whys" for NFRs:** If a Product Manager says "We need real-time WebSockets for this feature," I ask why. "Because users need the data instantly." Why? "Because if the price of the item changes, they might buy at the wrong price." Okay, so the NFR is *Data Accuracy at Checkout*, not necessarily *Real-Time UI*. We can solve this with a much cheaper REST validation call at the moment of checkout, rather than a battery-draining WebSocket.

## Probing Questions

1.  Explain the fundamental difference between a Functional Requirement and a Non-Functional Requirement (NFR).
2.  Provide three examples of physical constraints unique to mobile devices that completely alter how a system is designed compared to a desktop web application.
3.  If an NFR states that an application must function in a "subway tunnel" (zero connectivity), how does this mandate a shift from a 1-tier to a 3-tier architecture?
4.  Describe the tradeoff between the NFR of "Battery Life" and the NFR of "Real-Time Data Freshness" when deciding between WebSockets and FCM Push Notifications.
5.  Why is it dangerous to define an NFR simply as "The app should be fast"? What is a better, mathematical way to define it?
6.  How does the NFR of "Storage Footprint" impact the decision of how aggressively a mobile app should cache images and JSON data offline?
7.  Explain the concept of "Graceful Degradation" regarding network bandwidth (e.g., moving from 5G to 2G).
8.  Why is testing a mobile application exclusively on a high-end flagship device considered an architectural failure regarding NFRs?
9.  If an application requires strict HIPAA compliance (Security NFR), how does this affect the implementation of local SQLite databases and `SharedPreferences`?
10. Describe how a Staff Engineer negotiates with Product Management when two NFRs (e.g., Offline Capabilities vs Time-to-Market) are in direct conflict.

## Further Reading

- [`design-framework.md`](design-framework.md) — Phase 1 of the System Design framework, where NFRs are explicitly negotiated.
- [`offline-first-app.md`](../reference-architectures/offline-first-app.md) — An entire architecture born from the NFR of "Network Resilience."
- [`performance/`](../android/performance/) — The entire section dedicated to tracking and mitigating Performance and Memory NFR violations.
