# Observability

## Purpose

The canonical home for observability. Previously this was smuggled into the Android, distributed-systems, platform-engineering, and leadership trees — exactly the duplication the canonical-owner rule exists to kill. New Relic, crash monitoring, and distributed-tracing topics elsewhere now *link here* instead of re-explaining.

## Why It Matters

You cannot operate a system you cannot see. SLOs and error budgets are how Staff engineers make reliability tradeoffs explicit instead of implicit.

## Learning Order

Logging and structured logging first (the lowest layer), then metrics and tracing (the middle), then SLIs/SLOs/error budgets (the framing), then alerting and dashboards (how it reaches humans).

## Topics

- [Logging](observability/logging.md)
- [Structured Logging](observability/structured-logging.md)
- [Metrics](observability/metrics.md)
- [Tracing](observability/tracing.md)
- [Distributed Tracing](observability/distributed-tracing.md) — canonical; `distributed-systems/` cross-references
- [SLIs](observability/slis.md)
- [SLOs](observability/slos.md)
- [Error Budgets](observability/error-budgets.md)
- [Alerting](observability/alerting.md)
- [Dashboards](observability/dashboards.md)

## Application Files

[`android/observability/`](observability.md) holds the Android-specific implementations (New Relic, crash monitoring, logging). Those are application files that link back here.
