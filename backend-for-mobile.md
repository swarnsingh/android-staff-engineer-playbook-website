# Backend for Mobile

## Purpose

The contract between mobile clients and the services they call — BFFs, transport protocols, push vs poll.

## Why It Matters

Mobile clients have different needs than web clients: battery, intermittent connectivity, payload size, old app versions, and store-mediated rollouts. The BFF pattern and mobile-specific API design exist because generic backend interfaces do not serve mobile well.

## Learning Order

BFF pattern and API design first (the shape), then transport protocols (the wire), then push-vs-poll and rate limiting (the operational concerns).

## Topics

- [BFF Pattern](backend-for-mobile/bff-pattern.md)
- [API Design for Mobile](backend-for-mobile/api-design-for-mobile.md)
- [Transport Protocols (REST / gRPC / GraphQL)](backend-for-mobile/transport-protocols.md)
- [GraphQL vs REST](backend-for-mobile/graphql-vs-rest.md)
- [Push vs Poll vs SSE vs WebSockets](backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md)
- [SSE vs WebSockets](backend-for-mobile/sse-vs-websockets.md)
- [Rate Limiting](backend-for-mobile/rate-limiting.md)
- [Data Formats (JSON / Protobuf)](backend-for-mobile/data-formats.md)
