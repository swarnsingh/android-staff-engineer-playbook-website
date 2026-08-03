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

1. [Telemetry Taxonomy and Signal Selection](observability/telemetry-taxonomy.md) — canonical decision matrix for product events, operational metrics, exceptions, logs, traces, breadcrumbs, privacy, sampling, retention, and deletion.
2. [Logging](observability/logging.md)
3. [Structured Logging](observability/structured-logging.md)
4. [Metrics](observability/metrics.md)
5. [Tracing](observability/tracing.md) — canonical mechanics for traces, spans, in-process context, and sampling.
6. [Distributed Tracing](observability/distributed-tracing.md) — applies those mechanics to wire propagation, ingress trust, and cross-system correlation; `distributed-systems/` cross-references.
7. [SLIs](observability/slis.md)
8. [SLOs](observability/slos.md)
9. [Error Budgets](observability/error-budgets.md)
10. [Alerting](observability/alerting.md)
11. [Dashboards](observability/dashboards.md)

**Next:** apply the signals in [Release Engineering](release-engineering.md) and Android's application-specific observability topics.

## Application Files

Android-specific implementations live under `android/observability/` and are sequenced in [Android Phase 7](android.md#phase-7-performance-and-android-observability). Those application files link back here.
