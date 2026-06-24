# AirBridge

## Definition

A cross-platform file-transfer and data-sync system that performs large, resumable uploads from mobile clients to backend storage. Key technical characteristics: deterministic resume across process death and network failure, a multi-state upload pipeline (`Idle → Discovering → Preparing → Uploading → Paused → Retrying → Completed → Failed`), SSE-based server-driven progress streams, and an idempotency-and-consistency model guaranteeing no duplicate work after partial failures.

> *TODO: scale numbers — uploads/day, median and p95 payload sizes, concurrency limits, end-to-end latency targets.*

## Role In This Repo

AirBridge is an **anchor system**, not a portfolio project. It is the worked example that grounds abstract concepts in [networking](backend-for-mobile.md), [distributed systems](distributed-systems.md), [security](security.md), [state machines](engineering-fundamentals.md), [release engineering](release-engineering.md), [observability](observability.md), and [reference architectures](reference-architectures.md).

When a canonical topic gets too abstract, an AirBridge application file ties it to a real system.

## Application Files

Application files in [`airbridge/`](airbridge/) — each links back to its canonical owner and never redefines concepts.

- [`airbridge/deterministic-resume.md`](airbridge/deterministic-resume.md) — applies idempotency + consistency
- [`airbridge/upload-state-machine.md`](airbridge/upload-state-machine.md) — applies state machines

## Related ADRs

Decisions captured in [`adr/`](adr/) that shaped AirBridge:

- [`adr/002-post-vs-websockets.md`](adr/002-post-vs-websockets.md)
- [`adr/003-sse-vs-websockets.md`](adr/003-sse-vs-websockets.md)
