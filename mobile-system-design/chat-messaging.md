# System Design: Chat / Messaging (WhatsApp / Telegram)

## The Prompt

*"Design a 1-on-1 Chat application like WhatsApp. Users must be able to send text messages and images, see 'Read Receipts' (the double blue ticks), and the app must support offline queuing if the user is in a subway tunnel. Target latency for message delivery is under 200ms."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- 1-on-1 text messaging and image sharing.
- Message status indicators: Sent, Delivered, Read.
- Offline support (draft messages in airplane mode, send automatically when connected).

### Non-Functional Requirements (NFRs)
- **Latency (Priority 0):** < 200ms message delivery. (This mandates persistent connections, banning HTTP Polling).
- **Scale:** 10 Million Daily Active Users (DAU).
- **Data Integrity:** No lost messages. Exact message ordering is critical.
- **Battery:** The app cannot keep a WebSocket alive when in the background.

## 2. High-Level Architecture

The core of a chat application is the **Persistent Connection**. You cannot use standard REST (Request-Response) for real-time latency.

```mermaid
graph TD
    ClientA[Android Client A] <-->|WebSocket| ChatSvc[Chat Service / Gateway]
    ClientB[Android Client B] <-->|WebSocket| ChatSvc
    ClientC[Android Client C (Background)] <--|FCM Push| PushSvc[Push Notification Service]
    
    ChatSvc -->|Message Stream| Kafka[Kafka / Message Broker]
    Kafka --> PushSvc
    Kafka --> DB[(Cassandra / Chat DB)]
    
    ClientA -->|HTTP POST| MediaSvc[Media Service]
    MediaSvc --> S3[(AWS S3)]
```

*Staff Note:* The separation of the `ChatSvc` (Text) and the `MediaSvc` (Images) is mandatory. WebSockets are terrible for uploading 5MB image files. Text flows over WebSockets; Images flow over standard HTTP REST.

## 3. Data Model & API

### The Local Database (Room)

To achieve the "Offline" requirement and the "Instantly Fast" requirement, the app must implement the **Single Source of Truth** pattern. The UI reads *only* from Room.

```kotlin
@Entity(tableName = "messages")
data class MessageEntity(
    @PrimaryKey val id: String, // Client-generated UUID
    val chatId: String,
    val text: String,
    val senderId: String,
    val timestamp: Long,
    val status: MessageStatus // PENDING, SENT, DELIVERED, READ
)

enum class MessageStatus { PENDING, SENT, DELIVERED, READ }
```

### The API (WebSocket Payload)

We design the JSON payload moving across the WebSocket.

```json
// Outgoing Message (Client A -> Server)
{
  "type": "MESSAGE_SEND",
  "idempotency_key": "uuid-123", // CRITICAL
  "recipient_id": "user-99",
  "text": "Hello"
}

// Incoming Event (Server -> Client A)
{
  "type": "MESSAGE_STATUS_UPDATE",
  "message_id": "uuid-123",
  "status": "DELIVERED"
}
```

## 4. The Core Flows (Deep Dive)

### Flow 1: Sending a Text Message (The Happy Path)
1. User types "Hello" and hits Send.
2. The UI creates a `MessageEntity` with `id = UUID`, `status = PENDING`.
3. It saves it to Room.
4. The UI reacts instantly (Optimistic UI) and shows the message with a little clock icon 🕒.
5. A background Coroutine attempts to send the JSON over the active WebSocket.
6. The Server receives it, saves it to Cassandra, routes it to the recipient, and replies `MESSAGE_ACK`.
7. The Client receives `ACK`, updates Room to `status = SENT`. The UI instantly updates to a single checkmark ✔️.

### Flow 2: The Subway Tunnel (Offline Queuing)
1. User enters a tunnel (No Network). Hits Send.
2. Message saves to Room (`PENDING`). UI shows 🕒.
3. WebSocket fails.
4. The app enqueues a `WorkManager` job.
5. *Wait 10 minutes...*
6. User exits tunnel. Network returns.
7. `WorkManager` wakes up, pulls all `PENDING` messages from Room, opens an HTTP connection, and pushes them to the server. (We use HTTP here as a fallback because the WebSocket might take a few seconds to re-establish).

### Flow 3: Sending an Image
1. User selects a 5MB image.
2. The app compresses the image to a 200KB WebP on a background thread.
3. The app makes an HTTP `POST /media` request to the Media Service (NOT the WebSocket).
4. The Media Service stores it in S3 and returns a CDN URL: `https://cdn.chat.com/img123.webp`.
5. The app takes the URL and sends it over the WebSocket as a standard text message payload: `{"type": "IMAGE", "url": "https..."}`.

## 5. Failure Modes & Bottlenecks

### Bottleneck: The WebSocket Reconnection Storm
*Interviewer:* "Your load balancer crashes. 5 million active WebSockets drop simultaneously. They all try to reconnect. Your server melts. How do you fix this?"

**Staff Answer:**
"This is the **Thundering Herd** problem. 
I will implement **Exponential Backoff with Jitter** on the Android client. When the WebSocket drops, the client waits 1 second + a random variance (e.g., +/- 500ms). If it fails again, it waits 2 seconds + variance. This randomly smears the 5 million reconnection attempts across a 60-second window, allowing the Load Balancer to recover."

### Bottleneck: Battery Drain
*Interviewer:* "Users are complaining your app drains 15% battery overnight while they sleep. Why?"

**Staff Answer:**
"We are keeping the WebSocket alive while the app is in the background. A WebSocket requires a 'Ping' every 30 seconds to prevent the cellular ISP from dropping the idle connection. This forces the cellular radio to stay awake, draining the battery.
**The Fix:** I will implement the **Hybrid Approach**. When the Android `Activity` reaches `onStop()` (background), I will immediately disconnect the WebSocket. I will rely entirely on Firebase Cloud Messaging (FCM) 'Data Pushes' to wake the app up when a new message arrives. When the user opens the app again (`onStart`), I will re-establish the WebSocket and perform a REST `/sync` call to catch up on missed messages."

### Bottleneck: Message Duplication
*Interviewer:* "Client A sends a message. The Server receives it and saves it. But before the Server can send the ACK back, Client A drives into a tunnel and disconnects. Client A thinks the message failed. They reconnect and send it again. Client B receives the message twice."

**Staff Answer:**
"This is why the `idempotency_key` (Client-generated UUID) is mandatory. 
When Client A reconnects and retries, it sends the exact same UUID. The backend database (Cassandra) performs an `INSERT ... IF NOT EXISTS` or an `UPSERT` using the UUID as the Primary Key. The database realizes it already has this message, ignores the duplicate, and just sends back the missing ACK. Client B never sees a duplicate."

## 6. Probing Questions (For Practice)

1.  Explain why WebSockets are the preferred transport protocol for text chat over HTTP Polling or Server-Sent Events (SSE).
2.  Describe the "Thundering Herd" problem and explicitly how "Jitter" solves it during a mass disconnection event.
3.  Why is it an architectural failure to send a 5MB Image byte array directly through a WebSocket connection? Describe the correct multi-transport architecture.
4.  Explain the concept of an "Optimistic UI Update" and how the local Room database makes it possible.
5.  What is an Idempotency Key, and exactly how does it prevent Client B from receiving duplicate messages when Client A experiences a network dropout?
6.  Describe the battery implications of holding a WebSocket open in the background, and the "Hybrid Approach" involving FCM Push Notifications used to solve it.
7.  If a user goes offline, types 10 messages, and comes back online, why might a Staff Engineer use Android's `WorkManager` instead of just waiting for the WebSocket to reconnect?
8.  Explain how the "Read Receipt" (double blue ticks) feature works. Who generates the "READ" event, and how does it route back to the original sender?
9.  Why must the `id` of a message be generated on the Android client (UUID) rather than waiting for the backend relational database to assign an auto-incrementing integer ID?
10. If the application is required to support End-to-End Encryption (E2EE) like WhatsApp, how does this change the architectural responsibility of the Chat Service backend?

## Further Reading

- [`push-vs-poll-vs-sse-vs-websockets.md`](../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md) — The deep dive into transport protocols and battery drain.
- [`offline-sync.md`](offline-sync.md) — The foundation of the Single Source of Truth database architecture.
- [`idempotency.md`](../distributed-systems/idempotency.md) — The math behind preventing duplicate messages.
