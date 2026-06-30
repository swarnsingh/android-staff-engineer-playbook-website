# Real-Time Data: SSE vs WebSockets (and Polling, and FCM)

> Real-time on mobile is a battery decision before it's a protocol decision. Every persistent connection keeps the radio in a higher power state; every reconnect spins it up. WebSockets and SSE are not the only options — polling and FCM are real, often better, alternatives. Staff-level mastery is picking the right tool *per feature*, not per app, and architecting a single shared connection that multiplexes every real-time need.

---

## The Four Real-Time Options

| Option | Direction | Connection lifetime | Battery cost | Best for |
|---|---|---|---|---|
| **Polling** (HTTP GET in a loop) | Client pulls | Short, repeated | Low–Medium (depending on interval) | Low-urgency data, < 1 update/min |
| **Long polling** (HTTP GET held open) | Server → client (response holds) | Up to a minute per cycle | Medium | Backwards compatibility with HTTP/1.1 stacks |
| **SSE** (Server-Sent Events) | Server → client | Persistent | Medium | Notifications, scores, stock prices, server-driven UI |
| **WebSocket** | Bidirectional | Persistent | Medium–High | Chat, gaming, collaborative editing, voice |
| **FCM** (Firebase Cloud Messaging) | Push to client | App can be killed | Near zero (OS-multiplexed) | "Wake me up when something happens" |

Most apps think they need WebSockets but actually want a mix: FCM for off-process wakeups, polling for cheap status, and SSE or WebSockets only when active and needed. The pragmatic rule: **don't open a persistent socket unless the app is in the foreground and the user is actively viewing real-time data**.

---

## Polling — Underrated for Many Use Cases

```kotlin
class PollingService(private val api: Api, private val scope: CoroutineScope) {
    fun startPolling(intervalMs: Long = 30_000) = scope.launch {
        while (isActive) {
            try {
                val data = api.getLatest()
                _state.value = data
            } catch (e: IOException) { /* skip, retry next tick */ }
            delay(intervalMs)
        }
    }
}
```

**Pros:**
- Standard HTTP — works through every firewall, proxy, CDN.
- Predictable battery cost (one request per interval).
- Trivial to cache (each response is a normal `GET`).
- No reconnection logic. The "reconnect" *is* the next request.
- Easy to back off (`delay(intervalMs * 2)` after failure).

**Cons:**
- Latency = ~half the polling interval on average.
- N polls × M users = wasted server cycles if most polls return "no change."
- Doesn't scale to "real-time" feel below 5-second intervals.

When polling works: cart count badge, "you have N unread messages," server-side feature flag refresh, profile-data freshness. Anything where a 30-second delay is invisible to users.

### ETag-based conditional polling

```http
GET /messages/count
If-None-Match: "v3-abc123"
→ 304 Not Modified   (server saved bytes + GC pressure on client)
```

OkHttp handles this automatically with response cache. Drops 90%+ of polling cost for endpoints where the data changes rarely.

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
    .readTimeout(0, TimeUnit.MILLISECONDS)   // critical — don't time out the stream
    .pingInterval(30, TimeUnit.SECONDS)
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

If the server gives each event an `id:`, the SSE specification dictates that on reconnect the client automatically sends `Last-Event-ID: <last>`. The server resumes from there. **Android Note:** While this is a killer feature of the web specification, OkHttp's SSE implementation *does not* automatically track or append this header for you. You must manually cache the last seen ID and append `Last-Event-ID` to your reconnection request headers.

### Pros / Cons

**Pros:**
- Standard HTTP. Plays nicely with HTTP/2 multiplexing, proxies, CDNs.
- One-line server implementation in most frameworks.
- Automatic resume via `Last-Event-ID`.
- Text/UTF-8 only — easy to debug in Charles Proxy.

**Cons:**
- One-way (server → client). You still need a separate `POST` for client-to-server.
- No binary support — Base64 your bytes if you must.
- Some legacy load balancers cut connections after N seconds (configure timeout properly).

---

## WebSockets

Full-duplex, persistent TCP connection after a one-time HTTP upgrade handshake.

### OkHttp implementation

```kotlin
val client = OkHttpClient.Builder()
    .pingInterval(20, TimeUnit.SECONDS)   // ping/pong keepalive
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
- After the upgrade, it stops being HTTP. CDN caching is impossible.
- Custom protocol on top — you invent your own message envelope.
- Reconnection is entirely your problem.
- Heartbeats are mandatory or proxies kill the connection.

---

## FCM — The Battery-Free Option

Firebase Cloud Messaging is the **only way** to deliver a message to your app while it's not running. The OS holds a single multiplexed connection to Google's servers; your app is woken when relevant.

```kotlin
class AppFcmService : FirebaseMessagingService() {
    override fun onMessageReceived(message: RemoteMessage) {
        val type = message.data["type"]
        when (type) {
            "new_message" -> showMessageNotification(message.data)
            "trip_update" -> updateActiveTrip(message.data)
        }
    }

    override fun onNewToken(token: String) {
        sendTokenToServer(token)
    }
}
```

**Battery cost: effectively zero on top of what the OS already pays.** FCM rides one socket shared across every Google-Play-using app on the device.

### Use FCM when

- The user must be notified **even when the app is closed**.
- The message rate is low (< 100 per device per day).
- A small payload (~4 KB max) suffices to convey the event (often you just send "refresh now" and the app fetches the details).

### Use FCM as the *backbone*, layered with WebSocket/SSE for active sessions

The mature pattern:

- App background → only FCM listens.
- User opens the app → connect WebSocket/SSE for low-latency live updates.
- App backgrounded again → close the live socket; rely on FCM.

This costs almost nothing in the background and gets sub-second latency in the foreground.

---

## The Decision Tree

```
Do I need to push events to a backgrounded / killed app?
├── Yes → FCM (no other option works reliably on Android)
└── No → app is in foreground
    ├── Need bidirectional with binary or sub-100ms latency? → WebSocket
    ├── Server-to-client only, can do POST for upstream? → SSE
    └── Updates every 30s+ are fine? → Polling with ETag
```

Then pair them: FCM for wakeups + SSE/WebSocket for active sessions + polling for "barely real-time" status data. Layered.

---

## Reconnection: The Hard Part

A real-world reconnect loop with exponential backoff + jitter + cap:

```kotlin
class ResilientWebSocket(
    private val client: OkHttpClient,
    private val request: Request,
    private val onMessage: (String) -> Unit,
) {
    private var attempt = 0
    private var current: WebSocket? = null
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)

    fun start() = connect()

    private fun connect() {
        current = client.newWebSocket(request, object : WebSocketListener() {
            override fun onOpen(ws: WebSocket, response: Response) {
                attempt = 0    // reset backoff on success
            }
            override fun onMessage(ws: WebSocket, text: String) = onMessage(text)
            override fun onFailure(ws: WebSocket, t: Throwable, r: Response?) {
                scheduleReconnect()
            }
            override fun onClosing(ws: WebSocket, code: Int, reason: String) {
                ws.close(NORMAL_CLOSURE_STATUS, null)
                scheduleReconnect()
            }
        })
    }

    private fun scheduleReconnect() {
        val base = (1L shl attempt.coerceAtMost(6)) * 1_000   // 1s, 2s, 4s, ..., 64s
        val jitter = Random.nextLong(0, base / 2)              // avoid thundering herd
        attempt++
        scope.launch {
            delay(base + jitter)
            if (isActive) connect()
        }
    }

    fun stop() {
        scope.cancel()
        current?.close(NORMAL_CLOSURE_STATUS, "client stop")
    }

    companion object { private const val NORMAL_CLOSURE_STATUS = 1000 }
}
```

Three things to get right:

- **Exponential backoff** so a bad server doesn't get hammered.
- **Jitter** so 10,000 clients reconnecting at once don't all hit the server in the same millisecond.
- **Reset on success** — first connection after recovery shouldn't penalize the next failure.

SSE needs the same pattern. `EventSource` doesn't auto-reconnect on Android (the W3C browser spec does; OkHttp's port doesn't).

---

## The Battery Reality

Android's cellular radio has three power states:

| State | Power | Time to leave |
|---|---|---|
| Idle (deep) | ~5 mW | 1–2 s to wake |
| Low Power (FACH/CELL_PCH) | ~50 mW | 0 |
| Active (DCH) | ~500 mW | 0 |

When you open any persistent connection (WebSocket, SSE, long-poll), the radio sits in **Active** until traffic stops; then drops to **Low Power** after a "tail time" (~5–10 s); then to Idle after another ~30 s.

A WebSocket sending ping every 20 seconds keeps the radio in **Low Power** indefinitely. **Battery drains even if the app is doing nothing.**

### Mitigations

1. **Close the socket when the app backgrounds.** Use lifecycle observers.
2. **Multiplex.** One socket for all features, not one per feature.
3. **Lengthen pings.** 60-second pings are usually enough; check what your load balancer tolerates.
4. **Fall back to FCM** for background updates.
5. **Doze-mode awareness.** When the device enters Doze, network access is denied; your socket will fail. Don't reconnect immediately — wait until the device leaves Doze or use a high-priority FCM.

### Foreground service for persistent connections

If the app *must* keep a connection alive while backgrounded (rare — usually a sign the design is wrong), wrap it in a `Service` with `startForeground` and a notification. The OS won't kill it, but the user sees an ongoing notification and the radio stays active. Suitable for: a delivery driver's app while on a trip, a video call. Not suitable for: chat (use FCM-driven notification + reconnect on open).

---

## Connection Multiplexing — One Socket To Rule Them All

If your app has a chat feature, a live map, and a notifications drawer, **do not open three sockets**. Build a `ConnectionManager`:

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

Each feature filters the multiplexed flow. One socket; one set of heartbeats; one reconnect path.

---

## Server Side Concerns

These don't usually live in app code, but staff engineers must know them:

- **Sticky sessions.** Long-lived connections must terminate on the same backend node for the session lifetime. Load balancers need `ip_hash` or cookie-based stickiness.
- **Max connections per origin.** Browsers limit ~6 per origin; Android doesn't have the same cap but cellular networks impose their own. Multiplex.
- **Proxy timeouts.** AWS ALB defaults to 60s idle timeout. Set your ping interval to less than that.
- **TLS termination.** WebSocket Secure (`wss://`) and HTTPS-SSE both terminate TLS at the load balancer. Check your LB config supports it.
- **Connection caps.** Each open socket costs ~50 KB of server RAM. 100k concurrent users = 5 GB. Plan capacity.
- **Auth refresh.** A 24-hour open socket on a 1-hour token? You need a refresh-in-stream protocol (server sends `auth_refresh_required`, client reconnects with new token).

---

## Failure Modes

| Symptom | Cause | Fix |
|---|---|---|
| Battery drain even when app idle | Persistent socket with frequent pings | Multiplex; fall back to FCM in background |
| Socket disconnects every ~60s | Load balancer idle timeout | Lower ping interval below LB timeout |
| Messages lost during reconnect | No resume protocol | SSE: `Last-Event-ID`; WS: server-side message queue + replay token |
| Thundering herd on reconnect | No jitter | Add `Random.nextLong(0, base/2)` to backoff |
| Socket survives but no messages flow | Idle timeout closed by ISP/NAT silently | Ping/pong on a shorter interval; detect with timeout |
| `wss://` fails on captive WiFi | Hotspot redirects HTTPS for sign-in | Detect via probe URL; show "sign in to WiFi" |
| Doze mode kills socket | Device entered Doze | Don't reconnect immediately; wait for `ACTION_DEVICE_IDLE_MODE_CHANGED` |
| FCM message dropped | Too many low-priority messages | Use `priority: high` sparingly; rely on tickle-then-fetch pattern |
| App crashes after rotation | Listener leaked Activity | Lifecycle-aware service or ViewModel-scoped manager |
| Race: two sockets open after reconnect | New `connect()` called before old socket closed | Single source of truth — `ConnectionManager` with state |
| SSE stream returns garbled UTF-8 | Server sent bytes mid-character | SSE spec requires UTF-8; server-side bug |
| Auth expires mid-stream | Token TTL shorter than session | In-stream refresh protocol; reconnect with new JWT |
| User sees stale messages after long background | Polling never ran while backgrounded | FCM "tickle" + foreground refresh |
| Multi-tab / multi-device chaos | Same user has chat open on phone + tablet | Server-side session tracking with idempotency keys per send |
| Carrier MITM corrupts frames | Some carriers mangle bytes in headers | Use TLS only; investigate via test-only TLS-inspection proxy |

---

## Common Pitfalls

- **One socket per feature.** Costs N× battery; complicates auth refresh. Multiplex.
- **No reconnect backoff.** Outage → 10k clients hammer your server in a loop. Always exponential + jitter.
- **No `Last-Event-ID` (or equivalent).** Reconnect = lost messages. Either SSE's built-in or a custom replay protocol over WebSocket.
- **WebSocket for one-way data.** Adds complexity (custom envelope, manual reconnect) without benefit. SSE is simpler.
- **Persistent connection while backgrounded.** Wakelocks, battery drain, foreground-service requirement post-O. Almost always wrong; use FCM.
- **Polling at 1-second intervals.** "Real-time enough" for the PM, "battery murder" for the user. Push the use case to FCM + open-on-app-foreground.
- **No heartbeat.** Connections silently die behind NATs; you don't notice for minutes. Always send pings.
- **Hand-rolled reconnection on every feature.** Centralize in `ConnectionManager`.
- **Treating FCM as guaranteed delivery.** It isn't. FCM is best-effort. Use as a "tickle" — wake the app, let the app fetch authoritative state.
- **TLS misconfiguration.** `ws://` instead of `wss://`. Always TLS; pin the cert; check captive-portal behavior.

---

## Probing Questions

1. Compare the battery cost of polling every 30 s vs holding an open WebSocket. Why is polling sometimes cheaper than you'd guess?
2. Walk through what happens when an Android device enters Doze mode and your app has a WebSocket open.
3. Why is SSE's `Last-Event-ID` header a killer feature compared to rolling your own resume protocol on WebSocket?
4. Your app has Chat, Live Map, and Notifications — three persistent connections. Walk through how you'd refactor to one.
5. Reconnection with exponential backoff and jitter — walk through the math for 10,000 clients reconnecting after a 30 s outage.
6. Compare WebSocket vs SSE for: stock ticker, chat app, voice call, collaborative document editing. Pick each and justify.
7. FCM as the backbone: walk through the "tickle then fetch" pattern and why it's superior to keeping a socket open in the background.
8. Your WebSocket auth token expires every hour but sessions last days. Design the refresh protocol.
9. Load balancer kills your socket every 60 s. How do you detect and prevent this?
10. SSE vs polling with ETag — when is each cheaper?
11. WebSocket connection multiplexer with sealed-class events — show the rough class design.
12. A user's phone shows a chat notification but the app never opened that conversation in the foreground. How did the notification arrive? Walk through.

---

## Further Reading

- [`push-vs-poll-vs-sse-vs-websockets.md`](push-vs-poll-vs-sse-vs-websockets.md) — broader real-time comparison.
- [`graphql-vs-rest.md`](graphql-vs-rest.md) — GraphQL subscriptions live on WebSocket.
- [`transport-protocols.md`](transport-protocols.md) — HTTP/2 multiplexing and SSE.
- [`rate-limiting.md`](rate-limiting.md) — protecting socket endpoints from reconnect storms.
- [`bff-pattern.md`](bff-pattern.md) — BFF as the multiplex aggregator.
- [`../android/concurrency/battery-optimizations.md`](../android/concurrency/battery-optimizations.md) — radio states and Doze.
- [`../android/concurrency/workmanager.md`](../android/concurrency/workmanager.md) — background work alternatives.
- [`../android/concurrency/services.md`](../android/concurrency/services.md) — foreground service for persistent connections.
- [`../android/networking-and-security/retrofit-and-okhttp.md`](../android/networking-and-security/retrofit-and-okhttp.md) — OkHttp configuration.
- [`../distributed-systems/lww-vs-crdt.md`](../distributed-systems/lww-vs-crdt.md) — conflict resolution for live state.
- [OkHttp WebSockets docs](https://square.github.io/okhttp/4.x/okhttp/okhttp3/-web-socket/) — official reference.
- [OkHttp SSE module](https://github.com/square/okhttp/tree/master/okhttp-sse) — official.
- [FCM HTTP v1 API](https://firebase.google.com/docs/cloud-messaging) — server side.
- [WHATWG — Server-Sent Events spec](https://html.spec.whatwg.org/multipage/server-sent-events.html) — protocol details.
- [Discord — How Discord scaled to 11M users on 5 servers](https://discord.com/blog/how-discord-handles-two-and-half-million-concurrent-voice-users-using-webrtc) — multiplex architectures.
