# Observability

## Purpose

The canonical home for observability. Previously this was smuggled into the Android, distributed-systems, platform-engineering, and leadership trees — exactly the duplication the canonical-owner rule exists to kill. New Relic, crash monitoring, and distributed-tracing topics elsewhere now *link here* instead of re-explaining.

## Why It Matters

You cannot operate a system you cannot see. SLOs and error budgets are how Staff engineers make reliability tradeoffs explicit instead of implicit.

## What This Folder Helps You Do

- Design telemetry that explains user impact instead of only collecting raw logs, metrics, traces, and dashboards.
- Define SLIs, SLOs, error budgets, alerts, and release dashboards that help teams make better rollout and reliability decisions.
- Connect mobile symptoms to backend causes through trace propagation, sampling, correlation IDs, crash signals, and performance cohorts.
- Avoid observability traps: noisy alerts, PII leakage, unbounded logging cost, vanity dashboards, and metrics that cannot drive action.

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

Android-specific implementations live under `android/observability/` and are listed in [`android.md`](android.md#observability-application-files). Those are application files that link back here.
