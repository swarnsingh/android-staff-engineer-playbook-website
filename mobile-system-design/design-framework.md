# Mobile System Design Framework

## Overview

A Junior Engineer approaches a System Design problem by immediately drawing boxes for `Retrofit`, `Room`, and `Jetpack Compose`. They jump straight into implementation details before understanding the scale or constraints of the system.

A Staff Engineer understands that System Design is not about writing code; it is about **managing tradeoffs under strict constraints**. Before a single architectural box is drawn, you must extract the exact requirements, calculate the boundaries of the system, and establish the structural framework.

The **Mobile System Design Framework** (often referred to as the "RADIO" framework or similar variants) is a structured, repeatable methodology for breaking down massive, ambiguous problems (e.g., "Design WhatsApp") into solvable technical decisions.

## Why It Matters

If you are asked to "Design a Photo Sharing App," the correct architecture depends entirely on context:
- Is this for 100 photographers sharing massive 50MB RAW files?
- Is this for 1 billion teenagers sharing 50KB heavily compressed JPEGs?
- Is this for doctors sharing X-Rays in a hospital with no cellular service?

If you jump to "I'll use Glide to load the images," you have failed. The framework forces you to ask the right questions so you solve the correct problem.

## The Framework (RADIO)

The canonical framework for tackling any Mobile System Design problem consists of 5 phases:

1.  **R**equirements & Clarification
2.  **A**rchitecture (High Level)
3.  **D**ata Model & API
4.  **I**nterfaces & UI State
5.  **O**ptimization & Deep Dives (NFRs)

---

### Phase 1: Requirements & Clarification (5-10 mins)

The goal here is to shrink the infinite scope of "Design WhatsApp" down to a Minimum Viable Product (MVP) that can be discussed in 45 minutes.

#### Functional Requirements (What does it do?)
- *You:* "Does the chat app support group chats, or just 1-on-1?"
- *Interviewer:* "Just 1-on-1 for now."
- *You:* "Does it support sending photos and videos, or just text?"
- *Interviewer:* "Text and photos."
- *You:* "Are read receipts required?"
- *Interviewer:* "Yes."

#### Non-Functional Requirements / NFRs (How well does it do it?)
This is where Staff Engineers shine. You must define the physical constraints. (See [Non-Functional Requirements](non-functional-requirements.md)).
- *You:* "Does this app need to work fully offline (e.g., drafting messages on an airplane)?"
- *You:* "What is the expected latency for a message delivery? Sub-100ms, or is 2 seconds acceptable?"
- *You:* "Are we targeting global emerging markets (low-end devices, 3G) or just flagship 5G devices?"

*Staff Artifact:* Write down exactly 3-4 bullet points. "We are designing a 1-on-1 text/photo chat app, with offline queuing, targeting 100ms latency on 4G networks."

---

### Phase 2: High-Level Architecture (10 mins)

Draw the massive structural blocks. Do not mention `RxJava` or `Coroutines`. Think in physical boundaries.

1.  **The Client:** The Android App.
2.  **The Network Boundary:** The API Gateway, [Load Balancers](../distributed-systems/cap-theorem.md), or [BFF (Backend-For-Frontend)](../backend-for-mobile/bff-pattern.md).
3.  **The Transports:** How does data cross the boundary? Are we using [REST, WebSockets, or Server-Sent Events](../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md)?
4.  **The Backend Services:** Identify the necessary microservices (e.g., `AuthService`, `ChatService`, `MediaStorageService`).
5.  **The CDN (Content Delivery Network):** Where do photos live?

*Example output:* "The Android client will use a WebSocket connection to the `ChatService` for real-time text, and standard HTTP REST multipart uploads to an S3 bucket via the `MediaService` for photos. The CDN will distribute the photos globally."

---

### Phase 3: Data Model & API Contract (10-15 mins)

Now you design the exact shape of the data moving through the system and resting on the device.

#### 1. Local Storage (SQLite / Room)
Design the Entity-Relationship (ER) diagram for the local cache.
- `UserTable`: `id`, `name`, `avatar_url`
- `MessageTable`: `id`, `sender_id`, `recipient_id`, `text`, `timestamp`, `sync_status (PENDING, SENT, FAILED)`

#### 2. The API Contract
Design the exact JSON or Protobuf payload. Focus heavily on [Idempotency](../distributed-systems/idempotency.md) and [Pagination](../mobile-system-design/pagination.md).

```json
// POST /messages
{
  "idempotency_key": "UUID-123",
  "recipient_id": "991",
  "payload_type": "TEXT",
  "content": "Hello World"
}
```

*Staff Check:* Did you remember to add `sync_status` to your local database? If not, how will you show the user a red exclamation mark when the network fails? Did you use an `idempotency_key` in your API? If not, the user will send duplicate messages when they drive into a tunnel.

---

### Phase 4: Interfaces & UI State (5 mins)

Connect the Data to the Screen using modern Android architectural patterns (MVVM/MVI, Unidirectional Data Flow).

- **The Repository:** Acts as the Single Source of Truth. It merges the WebSocket stream and the Room database.
- **The ViewModel:** Exposes a `StateFlow<ChatUiState>`.
- **The UI:** Jetpack Compose function that blindly renders the `ChatUiState`.

```kotlin
sealed class ChatUiState {
    object Loading : ChatUiState()
    data class Success(val messages: List<MessageUI>) : ChatUiState()
    data class Error(val reason: String) : ChatUiState()
}
```

---

### Phase 5: Optimization & Deep Dives (10 mins)

This is the most critical phase for a Staff Engineer. The Interviewer will point to a box on your diagram and say, "Break this." You must identify the bottlenecks and propose solutions.

- **Bottleneck:** "If a user receives 10,000 messages in a massive group chat, your `RecyclerView` will stutter when Room emits the new list."
- **Staff Solution:** "I will implement `Paging 3` to only load 50 messages into RAM at a time. I will use `DiffUtil` on a background thread to calculate the delta."
- **Bottleneck:** "If the user is on a slow 3G network, uploading a 10MB photo will fail 90% of the time."
- **Staff Solution:** "I will use Android's `WorkManager` for background execution with network constraints. Before uploading, I will compress the Bitmap to WebP format, reducing it to 500KB. If it fails, `WorkManager` will handle the Exponential Backoff."

## Tradeoffs

**Perfect Architecture vs Time to Market**

During a System Design discussion, you must constantly weigh perfection against reality.

- *Perfection:* "We will use gRPC Bidirectional Streams for chat, backed by a CRDT (Conflict-Free Replicated Data Type) database for perfect offline sync resolution."
- *Reality:* "While CRDTs are mathematically perfect, they are incredibly complex to implement. Given our 3-month timeline, we will use a standard 'Last-Write-Wins' timestamp resolution in SQLite and WebSockets. We accept a 0.1% edge-case conflict rate to hit our launch date."

*Staff Decision:* A Staff Engineer knows the complex theoretical solutions, but often recommends the pragmatic, simpler solution, explicitly stating the tradeoffs they are accepting.

## Failure Modes

- **The Solution Searching for a Problem:**
  A developer says, "I will use Kotlin Multiplatform, GraphQL, and Realm." The interviewer asks, "Why?" The developer replies, "Because they are modern." 
  *(Failure: You have failed the interview. Technologies are chosen to solve specific problems defined in Phase 1. If you don't define the constraints, you cannot justify the technology).*
- **Ignoring the Network:**
  Designing a system that assumes every API call returns `HTTP 200 OK` in 50ms.
  *(Failure: You must actively design for `SocketTimeoutException`, HTTP 500s, and 3G packet loss. This means local caching, optimistic UI updates, and retry queues are mandatory).*
- **Boiling the Ocean:**
  Trying to design the entire microservice backend architecture (Kubernetes scaling, Cassandra partitioning) when applying for a Mobile role.
  *(Failure: While you must understand the API boundary and basic server concepts like Load Balancing, your primary focus must remain on the client-side constraints: Battery, RAM, OS Lifecycles, and SQLite).*

## Staff Engineer Thinking

When I enter a System Design discussion, my primary weapon is the word **"Why."**

1.  **Challenge the Prompt:** If asked to design a "Video Streaming App," I immediately ask, "Is it live-streaming (Twitch) or Video-on-Demand (Netflix)?" The entire architecture (HLS vs WebRTC) pivots on this answer.
2.  **State the Invariants:** I verbally lock in my assumptions. "I am assuming users will have spotty network connections. Therefore, I am designing this as an Offline-First application with a local SQLite cache as the absolute Single Source of Truth."
3.  **The "What If" Game:** I pre-emptively attack my own design. "My current API design works for 1,000 friends. However, if a user has 1,000,000 friends, this JSON payload will cause an `OutOfMemoryError` on parse. To fix this, I would need to introduce cursor-based pagination here."

## Probing Questions

1.  Explain why jumping straight to choosing libraries (e.g., Retrofit vs Ktor) is a failure of the System Design framework.
2.  What is the difference between a Functional Requirement and a Non-Functional Requirement (NFR) in the context of mobile applications?
3.  During Phase 2 (High-Level Architecture), why is it critical to explicitly define the boundaries between the Client, the Transport Layer, and the Server?
4.  Why must an Entity-Relationship (ER) diagram for a local SQLite database include synchronization state columns (e.g., `sync_status`) in addition to the standard business data?
5.  Explain the concept of an "Optimistic UI Update" and how it masks network latency in a Chat application.
6.  If an interviewer asks you to design a system for uploading massive 4K videos, why is Android's `WorkManager` a better choice than a standard Kotlin Coroutine?
7.  Describe a scenario where choosing a "mathematically perfect" architecture (like CRDTs) might be the wrong engineering decision.
8.  How do you prevent a massive list of data (e.g., 50,000 chat messages) from causing UI stuttering and OutOfMemory errors on an Android device?
9.  Why is it crucial to clarify the target demographic's network quality (e.g., 5G in Seoul vs 3G in rural India) during the Requirements phase?
10. Describe the "Single Source of Truth" pattern when merging real-time WebSocket data with historical data loaded from a REST API.

## Further Reading

- [`non-functional-requirements.md`](non-functional-requirements.md) — Deep dive into the constraints (Battery, CPU, Network) that shape every mobile design.
- [`offline-first-app.md`](../reference-architectures/offline-first-app.md) — The reference architecture that implements the "Single Source of Truth" local caching pattern.
- [`idempotency.md`](../distributed-systems/idempotency.md) — The mathematical proof required for safe network retries.
