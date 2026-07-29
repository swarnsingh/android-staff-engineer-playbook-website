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

## Guided Reading Sequence

Prerequisite: understand one production system well enough to name its user journeys and failures. Learn signals first, then reliability framing, then human response.

1. [Logging](observability/logging.md)
2. [Structured Logging](observability/structured-logging.md)
3. [Metrics](observability/metrics.md)
4. [Tracing](observability/tracing.md)
5. [Distributed Tracing](observability/distributed-tracing.md) — canonical; `distributed-systems/` cross-references.
6. [SLIs](observability/slis.md)
7. [SLOs](observability/slos.md)
8. [Error Budgets](observability/error-budgets.md)
9. [Alerting](observability/alerting.md)
10. [Dashboards](observability/dashboards.md)

**Next:** apply the signals in [Release Engineering](release-engineering.md) and Android's application-specific observability topics.

## Application Files

Android-specific implementations live under `android/observability/` and are sequenced in [Android Phase 7](android.md#phase-7-performance-and-android-observability). Those application files link back here.
