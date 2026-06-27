# Blueprint: The Merchant App (B2B)

## 1. Architectural Signature
A Merchant App (e.g., Square POS, Uber Eats Restaurant App, Shopify Admin) is an enterprise tool used by employees in a high-stress, fast-paced environment.
The architecture is optimized for **Reliability, Absolute Data Accuracy, and Hardware Integration**.
A/B testing is rare. "Delightful" animations are considered distractions. If the app crashes, the merchant loses money instantly. If the app loses network connectivity, it must still function (Offline-First).

**Core Trade-off:** Uptime & Data Accuracy > UI Velocity & Experimentation.

## 2. Component Blueprint

### Presentation Layer (The Utility)
- **Framework:** Compose or Views. The UI is dense, data-heavy, and utilitarian.
- **Pattern:** MVVM (Model-View-ViewModel). State management prioritizes exposing raw data streams over complex UI state machines.
- **Navigation:** Deep, hierarchical navigation. Less reliance on deep links, more reliance on stable internal routing and role-based access control (RBAC) in the UI.

### Domain Layer (The Business Rules)
- **Strict Validation:** Complex business logic executes on the client. (e.g., Calculating tax, verifying inventory levels before allowing a cart addition).
- **Offline Sync Engine:** A dedicated module responsible for queuing mutations (e.g., "Charge Card", "Accept Order") when offline, and synchronizing them sequentially when the network returns.
- **Hardware Abstraction Layer (HAL):** Interfaces defining interactions with Bluetooth printers, barcode scanners, or NFC payment terminals.

### Data Layer (Offline-First)
- **Local Persistence (Priority 0):** Room Database is mandatory. The app reads exclusively from the local DB. It never reads directly from the network.
- **Network Strategy:** **Pessimistic Updates (for critical actions)**. If a merchant charges a credit card, the app *must* wait for the network confirmation before updating the UI to "Success". Optimistic updates are banned for financial transactions.
- **Background Sync:** Heavy reliance on `WorkManager` for guaranteed background execution of the synchronization queue.

## 3. Infrastructure & DevOps
- **Release Cadence:** Slow and steady (e.g., bi-weekly or monthly). Merchants despise UI changes that disrupt their muscle memory.
- **Rollout Strategy:** Highly conservative. A 1% rollout might bake for 3 days before moving to 5%.
- **Telemetry:** Focuses on ANRs, crashes, and API latency rather than funnel conversion or "clicks".

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The Offline Consistency Paradox
*Problem:* A restaurant loses internet. A waiter takes an order on Tablet A. Another waiter takes an order on Tablet B. Both tablets come back online. Tablet A deleted an item that Tablet B modified.
*Solution:* **Vector Clocks or Conflict-Free Replicated Data Types (CRDTs)**. Simple "Last Write Wins" timestamp logic destroys merchant data. The architecture must implement a Sync Engine capable of deterministic conflict resolution, or rely on a backend designed to handle differential syncs.

### Bottleneck 2: Hardware Fragmentation (Bluetooth Hell)
*Problem:* The app needs to print receipts. There are 50 different receipt printers on the market. Hardcoding SDKs for all 50 bloats the app and causes dependency conflicts.
*Solution:* **The Plugin Architecture**. The core app defines a `PrinterInterface`. Specific printer SDKs are built as separate dynamic modules or even separate Android APKs that communicate with the core app via AIDL (Android Interface Definition Language).

### Bottleneck 3: Background OS Kills
*Problem:* The Merchant puts the tablet to sleep. A new "Uber Eats" order arrives via push notification. The app tries to ring an alarm, but Android Doze mode suppresses the network request and the alarm. The restaurant misses the order.
*Solution:* **High-Priority FCM & Foreground Services**. Transactional pushes must be marked `priority: high`. The app must immediately launch a `Foreground Service` (with an ongoing notification) to ring the alarm and keep the CPU awake until the merchant acknowledges the order.

## 5. Summary of Technologies
- **UI:** Compose/XML, MVVM.
- **Data:** Room (Heavy usage), Retrofit, Kotlin Flow.
- **Sync:** WorkManager, CRDTs (if decentralized).
- **Hardware:** Android Bluetooth Stack, NFC, AIDL (for IPC).

## Further Reading
- [`offline-sync.md`](../mobile-system-design/offline-sync.md)
- [`push-notifications.md`](../mobile-system-design/push-notifications.md) (Specifically Doze Mode & High Priority).
