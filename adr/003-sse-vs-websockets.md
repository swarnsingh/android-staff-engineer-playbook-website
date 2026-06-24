# ADR 003 — SSE vs WebSockets for AirBridge Progress Streams

**Status:** Accepted
**Date:** *TODO: actual decision date*
**Deciders:** *TODO: actual deciders*

---

## Context

AirBridge's upload pipeline (see [`../airbridge/upload-state-machine.md`](../airbridge/upload-state-machine.md)) needs server-driven progress updates pushed to the mobile client during the `Uploading` state. Updates include per-chunk acknowledgments, server-side processing milestones, and final completion. The client never needs to *push* progress upstream; the client already knows what it has uploaded. The data flow is strictly one-way: server → client.

The pipeline already uses POST-per-chunk for the upload itself (see [`002-post-vs-websockets.md`](002-post-vs-websockets.md)). Progress transport is a separate decision because progress arrives during the upload, on a different channel than the chunk PUTs themselves.

The relevant constraints:

- **Direction:** server-push only. No client-to-server messaging on this channel.
- **Cadence:** sporadic. A small upload may emit 3 progress events; a large one, hundreds.
- **Reliability:** lost messages are recoverable. The client can always re-derive progress from the server by polling the upload's state endpoint. Progress is a UX optimization, not a correctness mechanism.
- **Connection lifetime:** seconds to tens of minutes — the duration of an upload.
- **Mobile constraints:** background restrictions, battery, NAT timeouts (typically 60-300s on mobile carrier networks).

---

## Problem

What transport should carry server → client progress updates during an active upload?

---

## Alternatives

### Polling

Client polls a `GET /uploads/{id}/status` endpoint every N seconds.

- **Pros:** trivial; no special server infrastructure; survives all proxies and network conditions; no long-lived connection to manage.
- **Cons:** wasted requests when nothing has changed; latency floor of `N`; battery cost on mobile from periodic radio wake-ups; doesn't scale well as upload count grows.

### Long polling

Client sends a request; server holds it open until progress is available or a timeout elapses, then responds. Client immediately re-sends.

- **Pros:** lower latency than polling; works through almost any proxy; HTTP semantics throughout.
- **Cons:** half the complexity of a real streaming protocol with most of the operational cost; awkward error handling; doesn't actually escape connection management; less standard tooling than the other options.

### Server-Sent Events (SSE)

A long-lived HTTP response with `Content-Type: text/event-stream`. Server writes events as text frames; client parses them with `EventSource` (or, on Android, an OkHttp event-source extension).

- **Pros:** built on plain HTTP/1.1 or HTTP/2 — passes through any HTTP-aware proxy and works with existing auth (cookies, bearer tokens, mTLS) without special handling; one-way fits the actual data flow; the standard supports automatic reconnect with `Last-Event-ID`; trivial server implementation (just hold a response open and write).
- **Cons:** one direction only — useless if the channel ever needs to carry client → server messages; some legacy proxies buffer responses and break the streaming property; older Android HTTP stacks had no native client (modern OkHttp does).

### WebSockets

A full-duplex protocol that begins life as HTTP, then upgrades. Both directions are open after the handshake.

- **Pros:** full-duplex; broad library support; well understood; the obvious default for "real-time" use cases.
- **Cons:** full-duplex is *unnecessary* for our actual data flow; the upgrade handshake doesn't traverse all proxies cleanly; auth on the upgrade is fiddlier than HTTP-native; ping/pong heartbeats and reconnection logic must be implemented by the application (the spec doesn't define automatic resume); fragmentation handling adds code complexity; some carrier middleboxes close idle WebSocket connections aggressively.

---

## Decision

**SSE.**

The data flow is one-way (server → client), and SSE matches one-way push exactly. WebSockets would buy us bidirectional capability we don't need, in exchange for handshake complexity, auth fiddliness, more application-level reconnect logic, and worse behavior through aggressive middleboxes.

---

## Consequences

**Positive**

- Auth is plain HTTP — the same bearer tokens used for chunk PUTs work for the progress stream. No separate auth flow.
- Automatic resume on disconnect via the `Last-Event-ID` header, with no application code. The client picks up where it left off when the connection re-establishes.
- Server implementation is trivial: hold an HTTP response open and write `data: ...\n\n` frames.
- Operational tooling (HTTP logs, tracing, request IDs) works out of the box.
- One transport (HTTP) end-to-end. No special protocol upgrade for ops to reason about.

**Negative**

- If a future requirement adds client → server messaging on this channel (e.g., "pause from another device"), SSE cannot carry it. We will need a second channel (likely a POST endpoint).
- Some legacy proxies (typically corporate/captive environments) buffer responses. In those environments, the stream degrades to chunked polling. Mitigation: a periodic SSE comment frame as a keep-alive forces flush behavior on most middleboxes.
- The `EventSource` browser API is irrelevant — we're on Android. We depend on OkHttp's event-source support, which adds a small dependency surface.

---

## Tradeoffs

We accept:

- Loss of full-duplex on this channel. If progress-stream-the-channel ever needs to carry upstream messages, we add a second channel rather than re-platform.
- Dependency on OkHttp's event-source library for the client implementation.
- Some carrier networks may close the stream at NAT timeouts (~60-300s). SSE's auto-reconnect handles this transparently, but reconnection still incurs latency. For very long uploads, the client will reconnect multiple times.

We give up:

- The option to use a single WebSocket connection as a multi-purpose realtime channel. Other real-time features (chat, presence, etc.) — should they appear — would need their own transport decision; we are not committing the project to SSE for everything.

---

## Future Revisit Conditions

Re-open this decision if any of the following becomes true:

- A new requirement adds client → server messaging on the progress channel and we end up running an SSE channel *and* a second upload channel for messaging. At that point, collapsing both into a single WebSocket may be simpler.
- The repo grows to include multiple real-time features (presence, collaborative editing, live notifications) such that running one WebSocket for everything beats per-feature SSE streams.
- Observed reconnection rate in production exceeds *TODO: threshold* — implying that SSE's HTTP-layer reconnect is masking a problem we should address at the transport layer instead.

---

## Related

- [`002-post-vs-websockets.md`](002-post-vs-websockets.md) — the upload transport decision; explains why uploads use POST per chunk rather than a single long-lived connection.
- [`../airbridge/upload-state-machine.md`](../airbridge/upload-state-machine.md) — the consumer of this decision.
- [`../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md`](../backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md) — canonical comparison of all four transports.
