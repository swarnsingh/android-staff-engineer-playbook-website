# Backend For Mobile: structure plan

Planning baseline: approved source `fb8354edb079e901edf18710ca9388a124712a5b` (source PRs #76–#80). Order below is the exact guided tree-index order, not filename order. This plan precedes teaching-layer drafting. Only Delivery Semantics is implemented in this milestone; all other entries are conversion plans awaiting later topic ownership and approval.

Each chapter retains its complete original text, code, tables, diagrams, operational sections and existing questions/answers in order. The coverage field names the chapter-specific mechanisms that must remain understandable; it is not permission to drop other original sections. Original Mermaid sources get designed FigureMaps when converted. New figures use shared role tokens, labelled relationships, explicit boundaries and captions stating the point. Motion is optional; listed traces are manual candidates, not promised animations. No new prediction questions, decision-card interactions or answer hiding are approved. Source links below are the primary authorities to consult at conversion, not a claim that every linked page or integration has been tested.

The content layer supplies content and component selection only. Layout and behaviour remain in the shared design system. Official requirements and product status must be rechecked at conversion, especially Security and Release policy chapters. The accompanying inventory records exact Git-object hashes and section/diagram counts; planning reads do not synchronize whole trees.

## 1. Backend-for-Mobile (BFF) Pattern

- **Opening problem:** One screen fans out to several services and optional data breaks the whole screen.
- **Narrative route:** Compare device orchestration with a BFF; follow required and optional upstreams into a stable client contract.
- **Preserved coverage / internals:** Native/client and Ktor fragments, cancellation of optional work, contract ownership, SDUI and failure tradeoffs.
- **Figures / step-throughs:** Client/BFF/upstream boundary map; optional timeout trace.
- **Production / staff decisions:** Keep business truth in domain services; budget latency and own schema compatibility.
- **Prerequisites:** Distributed Systems through mobile contracts.
- **Official sources:** [learn.microsoft.com](https://learn.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends).

## 2. API Design for Mobile

- **Opening problem:** An old app version receives a valid server response it cannot interpret.
- **Narrative route:** Begin with radio/round-trip constraints; shape payloads; evolve fields and negotiate capabilities.
- **Preserved coverage / internals:** Under/overfetching, defensive parsing, result envelopes, canonical response contract, negative capability tests and governance.
- **Figures / step-throughs:** Old/new client contract map; static compatibility matrix.
- **Production / staff decisions:** Agree required vs optional fields and long-tail client support; choose REST/BFF/GraphQL by evidence.
- **Prerequisites:** BFF pattern; delivery and idempotency.
- **Official sources:** [google.aip.dev](https://google.aip.dev/180).

## 3. Data Formats (JSON, Protobuf, FlatBuffers)

- **Opening problem:** A small schema edit changes the meaning of an old client default.
- **Narrative route:** Compare wire representations through one payload migration; show presence, defaults and unknown values.
- **Preserved coverage / internals:** JSON adapters/streaming, Protobuf field evolution, FlatBuffers access costs, null/default migration and shrinking.
- **Figures / step-throughs:** Wire-field ownership map; old/new reader table.
- **Production / staff decisions:** Choose format by payload/access/evolution costs and test cross-version pairs.
- **Prerequisites:** API design and schema evolution.
- **Official sources:** [protobuf.dev](https://protobuf.dev/programming-guides/proto3/); [flatbuffers.dev](https://flatbuffers.dev/).

## 4. Transport Protocols (HTTP/2, HTTP/3, gRPC)

- **Opening problem:** A reconnect changes the network while several requests or a stream are active.
- **Narrative route:** Separate API shape, encoding and transport; inspect multiplexing/migration, then application reconnect.
- **Preserved coverage / internals:** HTTP/2, HTTP/3, QUIC, gRPC, protobuf, streaming resume semantics and mobile defaults.
- **Figures / step-throughs:** Connection/stream map; reconnect trace with app cursor.
- **Production / staff decisions:** Set deadlines and resume contracts; transport recovery does not recover business state.
- **Prerequisites:** Data formats; delivery semantics.
- **Official sources:** [www.rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9113); [www.rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9000); [grpc.io](https://grpc.io/docs/guides/).

## 5. API Contracts: GraphQL vs REST

- **Opening problem:** The screen needs less data and fewer calls, but cached responses are valuable.
- **Narrative route:** Separate query interface, orchestration and transport; compare one screen under both contracts.
- **Preserved coverage / internals:** Sparse fieldsets/BFF, request fan-out, HTTP vs normalized caches, persisted operations, type safety, mutations, errors and evolution.
- **Figures / step-throughs:** Static request/cache ownership comparison; optimistic result trace if needed.
- **Production / staff decisions:** Evaluate schema governance, complexity controls, compatibility and operational cost.
- **Prerequisites:** API design and data formats.
- **Official sources:** [spec.graphql.org](https://spec.graphql.org/); [www.apollographql.com](https://www.apollographql.com/docs/kotlin/caching/normalized-cache).

## 6. Real-Time Data (Push vs Poll vs SSE vs WebSockets)

- **Opening problem:** A backgrounded app must eventually catch up without a permanently open connection.
- **Narrative route:** Begin with freshness/lifecycle needs; compare wakeup hints and foreground streams; restore continuity from authoritative state.
- **Preserved coverage / internals:** Polling, FCM, SSE, WebSockets, battery/lifecycle boundaries, data/notification handling and shared continuity contract.
- **Figures / step-throughs:** OS/app/server boundary map; hint-loss to cursor-reconciliation trace.
- **Production / staff decisions:** Choose foreground vs background contracts and acceptable staleness, not a transport popularity ranking.
- **Prerequisites:** Delivery semantics; Android background execution.
- **Official sources:** [firebase.google.com](https://firebase.google.com/docs/cloud-messaging/customize-messages/setting-message-lifespan); [html.spec.whatwg.org](https://html.spec.whatwg.org/multipage/server-sent-events.html).

## 7. Real-Time Data: SSE vs WebSockets

- **Opening problem:** A live screen reconnects and must determine what it missed.
- **Narrative route:** Compare directionality and protocols; then handle resume identity, server retention and full reset.
- **Preserved coverage / internals:** OkHttp fragments, Last-Event-ID scope, reconnection, background boundaries, mobile cost and multiplexing constraints.
- **Figures / step-throughs:** Static duplex comparison; manual expired-cursor reset trace.
- **Production / staff decisions:** Own replay retention and authorization on reconnect; select bidirectionality only when required.
- **Prerequisites:** Broad push/poll comparison and transport protocols.
- **Official sources:** [html.spec.whatwg.org](https://html.spec.whatwg.org/multipage/server-sent-events.html); [www.rfc-editor.org](https://www.rfc-editor.org/rfc/rfc6455).

## 8. Rate Limiting

- **Opening problem:** Search requests queue faster than results remain useful, then the server returns 429.
- **Narrative route:** Separate UI pacing, in-flight ownership and server admission; parse retry guidance and show a useful fallback.
- **Preserved coverage / internals:** Debounce/sample, latest-query result ownership, Retry-After handling, interceptor constraints and UI throttling.
- **Figures / step-throughs:** Request ownership map; manual stale-search-result trace.
- **Production / staff decisions:** Use retry budgets and cancellation; do not treat local pacing as server authorization.
- **Prerequisites:** API design; coroutines and cancellation.
- **Official sources:** [www.rfc-editor.org](https://www.rfc-editor.org/rfc/rfc6585#section-4); [www.rfc-editor.org](https://www.rfc-editor.org/rfc/rfc9110#section-10.2.3).
