# Real-Time Data: SSE vs WebSockets

> **Decision:** this chapter compares SSE with WebSockets once the broader transport-selection process has narrowed the choice to a persistent stream. Canonical polling, FCM, lifecycle, retry, and reconciliation mechanics live in [`push-vs-poll-vs-sse-vs-websockets.md`](push-vs-poll-vs-sse-vs-websockets.md).
>
> Real-time on mobile is a lifecycle and continuity decision before it is a protocol decision. Pick per feature and workload; neither an open stream nor a push message is an authoritative event log.

---

## Decision Scope

Use the canonical [four-way comparison](push-vs-poll-vs-sse-vs-websockets.md) first. Continue here only when the experience needs a long-lived stream while its explicit feature/process owner is active.

| Choose | When | Reconsider when |
|---|---|---|
| **SSE** | Updates are server-to-client, text events fit, and upstream commands can use ordinary requests | The client needs frequent bidirectional control, binary frames, or one shared duplex protocol |
| **WebSocket** | Both sides send frequently, a framed duplex channel fits, or binary messages matter | Traffic is almost entirely downstream and HTTP-stream infrastructure materially simplifies operation |

In either case, specify authentication refresh, replay/reconciliation, backpressure, lifecycle ownership, heartbeat policy, and connection-state UX before selecting a client library.

---

## SSE (Server-Sent Events)

Plain HTTP `GET` that the server holds open, streaming `data: ...` lines:

```
event: stock_update
data: {"symbol":"AAPL","price":150.32}

event: stock_update
data: {"symbol":"GOOG","price":2900.10}
```

### OkHttp implementation

```kotlin
val client = OkHttpClient.Builder()
    .readTimeout(0, TimeUnit.MILLISECONDS)   // stream lifetime is owned elsewhere
    .build()

val request = Request.Builder()
    .url("https://api.example.com/ticker")
    .header("Accept", "text/event-stream")
    .build()

EventSources.createFactory(client).newEventSource(
    request,
    object : EventSourceListener() {
        override fun onOpen(es: EventSource, response: Response) { /* ... */ }

        override fun onEvent(es: EventSource, id: String?, type: String?, data: String) {
            // Parse JSON; deliver to ViewModel
        }

        override fun onFailure(es: EventSource, t: Throwable?, r: Response?) {
            // Reconnect with backoff (see below)
        }

        override fun onClosed(es: EventSource) {
            // Server closed normally
        }
    },
)
```

### Built-in resume semantics: `Last-Event-ID`

If the server gives each event an `id:`, browser `EventSource` reconnection uses the SSE-defined `Last-Event-ID` carrier. An Android OkHttp SSE integration does **not** automatically provide the browser's complete reconnect/resume behavior: cache the last accepted ID, append `Last-Event-ID` to the next request, and handle retention gaps and duplicates explicitly.

### Pros / Cons

**Pros:**
- Uses an HTTP response stream and can share supported HTTP/2 infrastructure; proxy buffering and idle policy still need validation.
- Many server frameworks provide SSE response primitives.
- Standard event IDs and `Last-Event-ID` reduce custom replay-protocol surface.
- Text/UTF-8 only — easy to debug in Charles Proxy.

**Cons:**
- One-way (server → client). You still need a separate `POST` for client-to-server.
- No binary support — Base64 your bytes if you must.
- Some legacy load balancers cut connections after N seconds (configure timeout properly).

---

## WebSockets

Full-duplex framed connection, commonly negotiated with an HTTP/1.1 upgrade; HTTP/2 support depends on the client, server, and intermediaries.

### OkHttp implementation

```kotlin
val client = OkHttpClient.Builder()
    .pingInterval(measuredPingInterval, TimeUnit.SECONDS) // only after validating idle policy
    .build()

val request = Request.Builder().url("wss://api.example.com/socket").build()

val listener = object : WebSocketListener() {
    override fun onOpen(ws: WebSocket, response: Response) {
        ws.send("""{"type":"auth","token":"$jwt"}""")
    }
    override fun onMessage(ws: WebSocket, text: String) { /* handle JSON */ }
    override fun onMessage(ws: WebSocket, bytes: ByteString) { /* handle binary */ }
    override fun onFailure(ws: WebSocket, t: Throwable, r: Response?) {
        reconnect()
    }
    override fun onClosing(ws: WebSocket, code: Int, reason: String) {
        ws.close(NORMAL_CLOSURE_STATUS, null)
    }
}

val webSocket = client.newWebSocket(request, listener)
```

### Pros / Cons

**Pros:**
- Bidirectional — client can stream up as easily as receive down.
- Binary support — voice, video frames, game state.
- Low overhead per message (no HTTP headers per frame).

**Cons:**
- WebSocket messages do not use ordinary HTTP response caching; gateways and intermediaries must support the negotiated WebSocket transport.
- Custom protocol on top — you invent your own message envelope.
- Reconnection is entirely your problem.
- Heartbeat policy must match measured server, NAT, carrier, and intermediary idle behavior; OkHttp does not send pings unless configured.

---

## Relationship to Background Delivery

FCM is a best-effort notification or invalidation channel, not a durable continuation of either stream. When no foreground feature/process owner needs the connection, close or suspend it according to product policy and use platform push only as a hint to reconcile authoritative state. Multi-window, picture-in-picture, calls, foreground services, and navigation between activities mean `Activity.onStop()` is not a universal boundary. See the [canonical lifecycle and FCM model](push-vs-poll-vs-sse-vs-websockets.md#2-the-battery-cost-of-websockets).

---

## Focused Decision

Default to SSE for a downstream-only text event stream when the Android client and intermediaries support the required authentication, buffering, timeout, and replay behavior. Choose WebSocket when the same connection must carry material upstream traffic, binary frames, or a domain protocol that benefits from duplex messaging. Reverse either choice when measurements or infrastructure constraints invalidate those assumptions.

---

## Reconnection: The Hard Part

Use the canonical [shared continuity contract](push-vs-poll-vs-sse-vs-websockets.md#shared-continuity-contract): bounded exponential backoff with jitter, server hints, a stable-session reset rule, durable replay/reconciliation, and deduplication.

The protocol-specific difference is the resume token. SSE defines event IDs and the `Last-Event-ID` request header, but an Android OkHttp SSE integration still needs explicit storage, reconnect, and gap policy. WebSocket defines no equivalent application replay contract; design a cursor/event ID and catch-up API when continuity matters.

---

## Mobile Cost Boundary

Data activity can add radio promotion and tail energy, but the magnitude varies by radio technology, carrier, modem, signal, device, batching, concurrent traffic, and heartbeat interval. Measure representative sessions. Own the stream at the narrowest feature/process lifecycle that meets the product requirement, multiplex compatible traffic when that reduces total connections, and use a foreground service only when the user-visible ongoing task and current platform policy justify one.

---

## Connection Multiplexing When Boundaries Align

If chat, live map, and notifications share lifecycle, authorization, service ownership, protocol, and fault-isolation requirements, a `ConnectionManager` can multiplex them. Keep separate connections when those boundaries differ:

```kotlin
@Singleton
class ConnectionManager @Inject constructor(
    private val client: OkHttpClient,
    private val authProvider: AuthProvider,
) {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private var socket: WebSocket? = null
    private val events = MutableSharedFlow<ServerEvent>(replay = 0, extraBufferCapacity = 64)

    val chat: Flow<ChatEvent> = events.filterIsInstance()
    val locations: Flow<LocationEvent> = events.filterIsInstance()
    val notifications: Flow<NotificationEvent> = events.filterIsInstance()

    fun connect() {
        val request = Request.Builder()
            .url("wss://api.example.com/multiplex")
            .header("Authorization", "Bearer ${authProvider.token}")
            .build()
        socket = client.newWebSocket(request, ConnListener())
    }

    fun disconnect() = socket?.close(1000, null)

    private inner class ConnListener : WebSocketListener() {
        override fun onMessage(ws: WebSocket, text: String) {
            scope.launch {
                events.emit(parseEvent(text))   // sealed type discriminator
            }
        }
        // ... onFailure → reconnection logic ...
    }
}
```

Server side sends a discriminator in each frame:

```json
{ "type": "chat", "room": "r1", "text": "hi" }
{ "type": "location", "tripId": "t9", "lat": 37.7, "lng": -122.4 }
{ "type": "notification", "title": "New offer" }
```

Each feature filters the multiplexed flow. One socket, one measured heartbeat policy, and one reconnect path can be simpler than independent feature connections when their lifecycle and security boundaries align.

---

## Server Side Concerns

These don't usually live in app code, but staff engineers must know them:

- **Routing state.** Sticky routing is necessary only when connection/session state cannot be recovered from shared infrastructure or the connection-owning node. Prefer stateless/shared routing where practical.
- **Connection budgets.** Capacity-plan gateway, file-descriptor, memory, fan-out, and client limits using measurements from the selected stack.
- **Proxy timeouts.** Discover the deployed intermediary idle policies, then configure heartbeat and reconnect behavior from evidence rather than a universal interval.
- **TLS termination.** WebSocket Secure (`wss://`) and HTTPS-SSE both terminate TLS at the load balancer. Check your LB config supports it.
- **Auth refresh.** When token TTL is shorter than a valid session, define whether the client reauthenticates in-stream or reconnects with a new token, and make failure explicit.

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Unexpected energy use while inactive | Stream outlives its product owner or sends unnecessary traffic | Fix lifecycle ownership; measure heartbeat and batching; use push only as a best-effort hint |
| Socket disconnects near an intermediary timeout | Load balancer or proxy idle policy | Align the deployed idle timeout and a measured heartbeat/liveness policy |
| Messages lost during reconnect | No durable resume/reconciliation contract | SSE: persist event ID and explicitly send `Last-Event-ID`; WS: define cursor/replay or fetch authoritative state |
| Thundering herd on reconnect | No jitter | Add `Random.nextLong(0, base/2)` to backoff |
| Socket survives but no messages flow | Intermediary idle policy or half-open path | Detect liveness under an explicit timeout; align any Ping/Pong cadence with measured network and server policy |
| `wss://` fails on captive WiFi | Hotspot redirects HTTPS for sign-in | Detect via probe URL; show "sign in to WiFi" |
| Continuity breaks while app is inactive | Lifecycle, Doze, process death, or network policy interrupted the stream | Reconcile from a durable cursor/state when the owning experience resumes |
| App crashes after rotation | Listener leaked Activity | Lifecycle-aware service or ViewModel-scoped manager |
| Race: two sockets open after reconnect | New `connect()` called before old socket closed | Single source of truth — `ConnectionManager` with state |
| SSE stream returns garbled UTF-8 | Server sent bytes mid-character | SSE spec requires UTF-8; server-side bug |
| Auth expires mid-stream | Token TTL shorter than session | In-stream refresh protocol; reconnect with new JWT |
| User sees stale messages after long inactivity | Client treated stream/push delivery as authoritative | Refresh or replay from the server under the product freshness policy |
| Multi-tab / multi-device chaos | Same user has chat open on phone + tablet | Server-side session tracking with idempotency keys per send |
| Stream fails only on some networks | Captive portal, proxy, TLS inspection, or intermediary policy | Keep TLS validation enabled; reproduce with approved test tooling and inspect the failing boundary |

---

## Common Pitfalls

- **One socket per feature by default.** Independent streams multiply lifecycle, authentication, and reconnect work. Multiplex only when feature ownership, authorization, and failure isolation are compatible.
- **Unbounded synchronized reconnects.** A fleet can delay recovery by retrying in lockstep. Apply bounded attempts, server hints, backoff, and jitter appropriate to the operation.
- **No durable event ID/cursor.** Reconnect can create a gap. Persist and send SSE's `Last-Event-ID` explicitly on Android, or define an equivalent WebSocket replay/reconciliation contract.
- **WebSocket for one-way data without a reason.** SSE may fit a downstream text stream more directly, but validate client support, authentication, proxy buffering, and operations before deciding.
- **Implicit lifecycle ownership.** A connection tied mechanically to one activity can outlive or underlive the product experience. Name the feature/process owner and its foreground-service exceptions.
- **Universal heartbeat interval.** Too-frequent traffic can waste energy; no heartbeat can miss silent intermediary closure. Measure the deployed path and choose an explicit liveness policy.
- **Hand-rolled reconnection on every feature.** Centralize compatible policy in a tested connection boundary while preserving feature-specific replay and authorization rules.
- **Treating FCM as guaranteed delivery.** It is best-effort. Use it as an invalidation hint when delivery/background policy permits work, and reconcile authoritative state independently.
- **TLS misconfiguration.** Use `wss://`/HTTPS, validate the platform trust configuration, and adopt certificate pinning only with an operationally safe rotation/recovery policy.

---

## Probing Questions

1. Compare the battery cost of polling every 30 s vs holding an open WebSocket. Why is polling sometimes cheaper than you'd guess?
2. Walk through what happens when an Android device enters Doze mode and your app has a WebSocket open.
3. What does SSE standardize with `Last-Event-ID`, and what continuity work remains on Android?
4. Your app has Chat, Live Map, and Notifications — three persistent connections. When would you multiplex them, and when should they remain isolated?
5. Reconnection with exponential backoff and jitter — explain how it reduces synchronized load after an outage and which caps/reset rules remain necessary.
6. Compare SSE, WebSocket, and a media transport for a stock ticker, chat app, voice call, and collaborative document editor.
7. Walk through an FCM "tickle then fetch" pattern and the cases where a user-visible ongoing stream may still be justified.
8. Your WebSocket auth token expires every hour but sessions last days. Design the refresh protocol.
9. Load balancer kills your socket every 60 s. How do you detect and prevent this?
10. SSE vs polling with ETag — when is each cheaper?
11. WebSocket connection multiplexer with sealed-class events — show the rough class design.
12. A user's phone shows a chat notification but the app never opened that conversation in the foreground. How did the notification arrive? Walk through.

---

## Answer Key

1. **Compare the battery cost of polling every 30 s vs holding an open WebSocket. Why is polling sometimes cheaper than you'd guess?**
   Neither has a universal energy ordering. Polling may be cheaper when a lifecycle-bound, cache-validated cadence batches with other traffic and leaves long idle periods; a quiet stream may be cheaper when updates are frequent. Compare measured radio activity, heartbeat cadence, payloads, update rate, and server cost.
2. **Walk through what happens when an Android device enters Doze mode and your app has a WebSocket open.**
   Network access and process execution can become discontinuous, so the stream may stall or close. The client follows its lifecycle/retry policy rather than looping aggressively, then reconciles authoritative state when the owning experience resumes; FCM remains best-effort, not a guaranteed wake-up.
3. **What does SSE standardize with `Last-Event-ID`, and what continuity work remains on Android?**
   SSE standardizes the event ID and `Last-Event-ID` carrier, reducing protocol design work. The Android client must still persist the last accepted ID, send it on reconnect, handle retention gaps, and deduplicate; WebSocket requires an equivalent application contract.
4. **Your app has Chat, Live Map, and Notifications — three persistent connections. When would you multiplex them, and when should they remain isolated?**
   A shared connection can reduce duplicate lifecycle, authentication, heartbeat, and reconnect machinery when the features have compatible ownership, authorization, delivery, and failure-isolation requirements. Keep them isolated when security boundaries, protocols, service ownership, release cadence, or fault containment differ.
5. **Reconnection with exponential backoff and jitter — explain how it reduces synchronized load after an outage and which caps/reset rules remain necessary.**
   Each failed attempt increases a bounded delay and adds randomness, spreading a fleet across a time window instead of one instant. Cap attempts and total deadline, honor server hints, stop when the owner is inactive, and reset the attempt window only after a sufficiently stable session; backoff reduces synchronization but cannot guarantee server recovery.
6. **Compare SSE, WebSocket, and a media transport for a stock ticker, chat app, voice call, and collaborative document editor.**
   A downstream text ticker often fits SSE. Interactive chat or collaborative editing can fit WebSocket when a duplex application protocol is useful. Voice media normally needs a transport such as WebRTC that addresses real-time media, NAT traversal, loss, jitter, and congestion control; WebSocket may still carry signaling or control messages.
7. **Walk through an FCM "tickle then fetch" pattern and the cases where a user-visible ongoing stream may still be justified.**
   FCM can deliver a best-effort notification/invalidation hint through shared platform infrastructure. When delivery and background policy permit, the client performs bounded work or reconciles later; it never assumes a wake-up or durable event delivery. This often avoids an app-owned inactive stream, but the product must measure its own latency and energy tradeoff.
8. **Your WebSocket auth token expires every hour but sessions last days. Design the refresh protocol.**
   Implement an in-stream refresh protocol where the server sends an `auth_refresh_required` event shortly before expiration. The client silently fetches a new JWT and sends an `auth` frame up the WebSocket to re-authenticate without dropping the connection.
9. **Load balancer kills your socket every 60 s. How do you detect and prevent this?**
   Correlate client disconnect telemetry with gateway idle policy and network captures. Then align the gateway timeout and a measured heartbeat/liveness policy; do not hard-code an interval until the deployed intermediaries and mobile cost are known.
10. **SSE vs polling with ETag — when is each cheaper?**
    SSE can reduce repeated requests when updates are frequent and low latency matters. Conditional polling can be cheaper and operationally simpler when updates are rare and a longer freshness interval is acceptable. Compare measured request/heartbeat traffic, radio activity, connection capacity, cache-hit rate, and lifecycle duration.
11. **WebSocket connection multiplexer with sealed-class events — show the rough class design.**
    For compatible features, a `ConnectionManager` can own the `WebSocket` and expose `Flow<ServerEvent>`. A sealed event hierarchy routes validated envelopes to feature flows, while the manager owns connection state and each feature retains authorization, cursor, deduplication, and reconciliation policy.
12. **A user's phone shows a chat notification but the app never opened that conversation in the foreground. How did the notification arrive? Walk through.**
    The server may have sent an FCM notification payload that the SDK displayed, or a data/mixed message may have reached app code under current app/device/priority policy. The exact callback and display path depends on payload type, app state, permission, delegation, and platform policy; the app reconciles durable message state independently.

## Further Reading

- [`push-vs-poll-vs-sse-vs-websockets.md`](push-vs-poll-vs-sse-vs-websockets.md) — canonical transport, lifecycle, retry, and reconciliation mechanics.
- [`graphql-vs-rest.md`](graphql-vs-rest.md) — GraphQL subscriptions live on WebSocket.
- [`transport-protocols.md`](transport-protocols.md) — HTTP/2 multiplexing and SSE.
- [`rate-limiting.md`](rate-limiting.md) — protecting socket endpoints from reconnect storms.
- [`bff-pattern.md`](bff-pattern.md) — BFF as the multiplex aggregator.
- [`../android/concurrency/battery-optimizations.md`](../android/concurrency/battery-optimizations.md) — radio states and Doze.
- [`../android/concurrency/workmanager.md`](../android/concurrency/workmanager.md) — background work alternatives.
- [`../android/concurrency/services.md`](../android/concurrency/services.md) — foreground service for persistent connections.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — OkHttp configuration.
- [`../distributed-systems/lww-vs-crdt.md`](../distributed-systems/lww-vs-crdt.md) — conflict resolution for live state.
- [OkHttp WebSocket API](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/WebSocket.kt) — official reference.
- [OkHttp SSE module](https://github.com/square/okhttp/tree/master/okhttp-sse) — official.
- [FCM HTTP v1 API](https://firebase.google.com/docs/cloud-messaging) — server side.
- [FCM message priority](https://firebase.google.com/docs/cloud-messaging/android/message-priority) — background processing and delivery constraints.
- [WHATWG — Server-Sent Events spec](https://html.spec.whatwg.org/multipage/server-sent-events.html) — protocol details.
- [RFC 6455 — WebSocket Protocol](https://www.rfc-editor.org/rfc/rfc6455.html) — framing, control frames, and optional Ping/Pong behavior.
- [Android network access optimization](https://developer.android.com/develop/connectivity/network-ops/network-access-optimization) — radio and batching considerations.
- [Discord — How Discord scaled to 11M users on 5 servers](https://discord.com/blog/how-discord-handles-two-and-half-million-concurrent-voice-users-using-webrtc) — multiplex architectures.
