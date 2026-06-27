# Platform Design: Analytics SDK

## The Prompt

*"Design an Analytics SDK (like Mixpanel, Amplitude, or Firebase Analytics) for a global E-Commerce app. The SDK must track user behavior (clicks, screen views, purchases) perfectly, ensuring no events are lost even if the user is in a subway tunnel. It must also handle user identity merging when an anonymous user logs in."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Log custom events with properties (e.g., `Event: "Added to Cart", ProductId: "123"`).
- Persist events offline and upload when the network returns.
- Identity resolution (stitching an anonymous device ID to a known User ID).

### Non-Functional Requirements (NFRs)
- **Data Integrity (Priority 0):** Zero dropped events. The company calculates Revenue based on these events.
- **Battery/Network:** Zero impact on app performance. Must not block the Main Thread or drain the battery with constant HTTP requests.
- **Privacy:** Must strictly adhere to GDPR/CCPA regulations regarding user tracking and deletion.

## 2. High-Level Architecture (The Pipeline)

An Analytics SDK is essentially a high-throughput, fault-tolerant message queue embedded in a mobile phone.

```mermaid
graph TD
    App[Host App] -->|track("Click")| API[SDK API]
    
    API -->|1. Async Enqueue| Ingest[Memory Queue]
    Ingest -->|2. Flush to Disk| SQLite[(SQLite DB)]
    
    subgraph Background Upload Engine
        WM[WorkManager] -->|3. Read Batch| SQLite
        WM -->|4. Compress (GZIP)| Payload[JSON Payload]
        Payload -->|5. HTTP POST| Server[Analytics Ingestion Backend]
    end
    
    Server -->|6. ACK (200 OK)| WM
    WM -->|7. Delete from DB| SQLite
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Preventing Main Thread Freezes (The Memory Queue)
*Interviewer:* "The host developer calls `Analytics.track('Scroll')` 60 times a second inside a `RecyclerView`. If you write to SQLite directly, the UI drops frames. How do you optimize the ingest?"

**Staff Answer:**
"The public API `track()` must be mathematically non-blocking.
1. When `track()` is called, the event is immediately pushed into an in-memory `ConcurrentLinkedQueue` (or a Kotlin `Channel`). This takes microseconds. `track()` returns instantly.
2. A dedicated background thread (the Flusher Thread) continuously drains the queue.
3. The Flusher Thread batches the events in RAM (e.g., waiting for 50 events or 1 second) and then executes a single bulk `INSERT` into SQLite. This eliminates the I/O bottleneck entirely."

### Flow 2: The Upload Strategy (Batching & Backoff)
*Interviewer:* "You have 10,000 events in SQLite. When exactly do you send them to the server?"

**Staff Answer:**
"We trigger the upload based on three specific lifecycle heuristics to protect battery and network:
1.  **Count Threshold:** When the SQLite database accumulates 50 unsent events.
2.  **Time Threshold:** Every 30 seconds, regardless of event count.
3.  **App Backgrounding:** When the Android OS signals `onStop()` (the user left the app), we immediately flush all remaining events to disk and fire a final upload request.
If the upload fails (e.g., HTTP 500 or No Network), we employ **Exponential Backoff**. We wait 2s, 4s, 8s, 16s before retrying. If we hit the maximum backoff, we cancel the job and let `WorkManager` handle it when the OS detects a stable network connection."

### Flow 3: Identity Stitching (The Anonymous User)
*Interviewer:* "A user downloads the app, browses 5 items, and adds 1 to the cart anonymously. Then they tap 'Log In'. How do you ensure the backend knows those 6 anonymous actions belong to the now-logged-in user?"

**Staff Answer:**
"This is Identity Resolution, and it relies on two distinct IDs.
1.  **Device ID (Anonymous):** Upon installation, the SDK generates a random UUID (e.g., `Device-XYZ`). Every event is tagged with this ID.
2.  **User ID (Known):** When the user logs in, the host app calls `Analytics.setUserId("User-99")`.
3.  **The Stitching Event:** The SDK instantly fires a special event to the backend: `$identify(old_id: "Device-XYZ", new_id: "User-99")`.
4.  From that point forward, all new events are tagged with `User-99`. The Backend database receives the `$identify` event and retroactively merges all previous `Device-XYZ` events into `User-99`'s profile, preserving the complete funnel."

## 4. Failure Modes & Bottlenecks

### Bottleneck: Database Bloat (The Infinite Tunnel)
*Interviewer:* "The user's phone has no network for 3 weeks. They use your offline app every day. The SQLite database accumulates 5 million events. The app runs out of storage space and crashes."

**Staff Answer:**
"The Analytics SDK must have a **Hard Cap** on disk usage to protect the host device.
1. I will set a hard limit (e.g., 50 Megabytes or 100,000 events).
2. When the limit is reached, the SQLite database must switch to an **Eviction Policy (FIFO)**.
3. When a new event arrives, the oldest event in the database is permanently deleted. We sacrifice old data to protect the host application's stability and prevent `DiskFull` OS crashes."

### Bottleneck: Payload Saturation (The 413 Error)
*Interviewer:* "You read 10,000 events from SQLite and send them in a 10 Megabyte JSON payload. The backend API Gateway rejects it with `HTTP 413 Payload Too Large`. The SDK keeps retrying. It's stuck forever."

**Staff Answer:**
"The batch upload must respect the backend's ingestion limits.
1. We chunk the SQLite read query into strict payload limits (e.g., maximum 500 events or 1MB per HTTP request).
2. We iterate through the database, sending multiple 1MB chunks sequentially.
3. If the backend returns a `413`, the SDK must implement a **Binary Backoff** strategy: split the batch in half (250 events) and try again. This ensures that a single excessively large event string (e.g., a massive JSON property) does not poison the entire queue."

## 5. Staff Engineer Thinking: GDPR & CCPA Compliance

A Junior engineer logs everything. A Staff engineer knows that logging the wrong thing results in a $50 Million fine.

1.  **PII Scrubbing:** The SDK must never automatically capture text fields (e.g., scraping `EditText` values), because it might capture passwords or credit card numbers.
2.  **The Nuclear Button (Delete Data):** Under GDPR, a user has the "Right to be Forgotten". The SDK API must expose a method: `Analytics.reset()`. When called, the SDK must immediately and synchronously `DELETE FROM events` in the SQLite database, clear the SharedPreferences Device ID, and stop tracking completely until explicitly opted back in.
3.  **Consent Gating:** In the EU, tracking cannot begin until the user taps 'Accept' on a cookie/tracking banner. The SDK must start in a dormant state (`isTrackingEnabled = false`) and only activate when the host app explicitly unlocks it.

## 6. Probing Questions (For Practice)

1.  Explain why calling `Analytics.track()` must be mathematically non-blocking, and how an in-memory queue prevents Main Thread UI stuttering.
2.  Describe the three lifecycle heuristics (Count, Time, App Backgrounding) used to trigger a batch upload to the backend.
3.  How does the SDK use a `$identify` event to solve the "Identity Stitching" problem when an anonymous user finally logs in?
4.  Why is Exponential Backoff absolutely mandatory when the backend Analytics Server returns an HTTP 500 error?
5.  Explain the "Database Bloat" problem during long offline periods. How does a FIFO eviction policy protect the host device from crashing?
6.  Describe the strategy for handling an `HTTP 413 Payload Too Large` rejection. How does chunking the SQLite read prevent the queue from getting permanently stuck?
7.  Why must an Analytics SDK strictly avoid Auto-Capturing user input from `EditText` fields? What compliance laws dictate this?
8.  Explain the required behavior of the `Analytics.reset()` function under GDPR requirements (The Right to be Forgotten).
9.  Why must batched JSON payloads be compressed using GZIP before transmission over the cellular network?
10. If the host application is forcefully killed by the Android OS (Process Death), how does the SQLite database guarantee that pending events in the memory queue are not permanently lost? (Trick question: They *are* lost if not flushed to disk fast enough; discuss the tradeoff between disk I/O speed and data loss risk).

## Further Reading

- [`telemetry-sdk.md`](telemetry-sdk.md) — How the batching and transmission engines overlap with Crash reporting.
- [`time-and-clocks.md`](../engineering-fundamentals/time-and-clocks.md) — Why offline events must use elapsed realtime to prevent timestamp distortion.
- [`security-and-privacy.md`](../mobile-system-design/security-and-privacy.md) — Deep dive into PII compliance.
