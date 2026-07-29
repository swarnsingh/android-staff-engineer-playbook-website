# Backend for Mobile

## Purpose

The contract between mobile clients and the services they call — BFFs, transport protocols, push vs poll.

## Why It Matters

Mobile clients have different needs than web clients: battery, intermittent connectivity, payload size, old app versions, and store-mediated rollouts. The BFF pattern and mobile-specific API design exist because generic backend interfaces do not serve mobile well.

## What This Folder Helps You Do

- Design API contracts that survive slow app upgrades, old client versions, retries, partial rollout, and backend schema evolution.
- Choose between REST, GraphQL, gRPC, SSE, WebSockets, push, polling, and BFF orchestration with mobile constraints in mind.
- Reason about payload size, radio wakeups, cacheability, rate limits, idempotency keys, pagination, and offline recovery from the client side of the contract.
- Partner with backend teams from a Staff position: make compatibility guarantees explicit, define failure envelopes, and prevent backend velocity from becoming mobile fragility.

## Guided Reading Sequence

Prerequisite: [Distributed Systems](distributed-systems.md), through delivery semantics and mobile consistency contracts. Read API shape before transport and operational choices.

1. [BFF Pattern](backend-for-mobile/bff-pattern.md)
2. [API Design for Mobile](backend-for-mobile/api-design-for-mobile.md)
3. [Data Formats (JSON / Protobuf)](backend-for-mobile/data-formats.md)
4. [Transport Protocols (REST / gRPC / GraphQL)](backend-for-mobile/transport-protocols.md)
5. [GraphQL vs REST](backend-for-mobile/graphql-vs-rest.md)
6. [Push vs Poll vs SSE vs WebSockets](backend-for-mobile/push-vs-poll-vs-sse-vs-websockets.md)
7. [SSE vs WebSockets](backend-for-mobile/sse-vs-websockets.md)
8. [Rate Limiting](backend-for-mobile/rate-limiting.md)

**Next:** continue to [Mobile System Design](mobile-system-design.md).
