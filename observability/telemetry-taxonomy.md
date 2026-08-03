# Telemetry Taxonomy and Signal Selection

## Overview

Telemetry is evidence emitted by a running system. **Analytics, logs, metrics, traces, exception reports, and crash breadcrumbs are not interchangeable destinations.** Each answers a different question, has a different cost model, and needs an explicit owner, privacy classification, retention policy, and deletion path.

This chapter owns the repository's signal-selection vocabulary. Application chapters should link here when deciding where an event belongs and then describe only their platform-specific implementation.

## Why It Matters

Sending every handled exception to a crash reporter buries actionable defects. Sending operational failures to product analytics distorts funnels. Logging every evaluation of a high-cardinality value creates cost and privacy risk without necessarily producing an alert or diagnosis.

The selection question is therefore not "Which SDK is already installed?" It is:

> Which engineering or product decision will this evidence support, at what aggregation level, and under which data-governance constraints?

## Canonical Signal-Selection Matrix

| Signal | Primary question | Example | Default shape | Cardinality and sampling | Expected action |
|---|---|---|---|---|---|
| **Product event** | Which product action, outcome, assignment, or defined exposure occurred? | Checkout submitted; onboarding completed; experiment exposure | Versioned event with bounded business dimensions | Keep dimensions bounded; sample only when analysis remains statistically valid | Product or experiment decision |
| **Operational metric** | How often, how long, or how much? | Sync success rate; request-latency histogram; queue depth | Counter, gauge, or histogram aggregated over a population | Attribute sets must be bounded; do not use raw user, request, URL, or exception text as labels | Dashboard, SLO, capacity decision, or alert |
| **Exception report** | Which actionable defect or violated invariant produced this stack and context? | Parser invariant failure after a schema rollout | Grouped throwable plus bounded diagnostic context | Group, rate-limit, and sample repeated reports; expected environmental outcomes usually do not need one report per occurrence | Defect triage with an owner |
| **Structured diagnostic event or log** | What happened in one execution context? | Sync attempt rejected because authentication expired | Timestamped schema or message with severity and correlation fields | Sample high-volume events; control message size and field cardinality | Investigation, audit where authorized, or metric derivation |
| **Trace and span** | Where did time or failure propagate through a request or workflow? | Checkout client span linked to gateway and payment spans | Trace/span IDs, timing, status, and bounded attributes | Head- or tail-sample by an explicit policy; never put secrets or unrestricted payloads in attributes | Latency and dependency diagnosis |
| **Crash or performance breadcrumb** | What bounded context helps explain a later report? | Last approved screen category; sync state transition | Small ordered context attached to another report | Strict count/size limit; redact and sample before attachment | Enrich the parent crash, exception, or performance report |

An **operational event** is not automatically a seventh storage destination. It is an occurrence such as `sync_failed` or `token_refresh_rejected` that should be represented as an operational metric, a sampled structured diagnostic event, an exception report, or more than one of those only when each representation supports a named decision.

Vendor products often accept multiple signals. A Crashlytics breadcrumb is still a breadcrumb, not product analytics; a Datadog event can still be a log or metric input; an analytics SDK does not turn an operational timeout into a product event.

## Selection Procedure

For each proposed signal:

1. **Name the decision and owner.** If no team will alert, investigate, measure a product outcome, or make a capacity/reliability decision from it, do not collect it by default.
2. **Choose the lowest-cost sufficient shape.** Prefer an aggregated metric for a fleet-wide rate, an exception report for an actionable stack, and a sampled trace for causal latency.
3. **Bound dimensions.** Enumerated app version, endpoint template, result category, and network class are usually safer than raw URL, arbitrary error text, request ID as a metric label, or stable user ID.
4. **Set sampling and rate limits before launch.** State whether sampling is deterministic, random, head-based, tail-based, or adaptive and how analysis compensates for it.
5. **Classify the data.** Document purpose, consent or other collection basis where applicable, access, regional handling, retention, and deletion. Hashing an identifier does not automatically make it anonymous.
6. **Test the operational path.** Verify schema validation, redaction, sampling, offline buffering, quota behavior, and deletion—not only that an SDK call succeeds.

## Decision Examples

| Situation | Preferred signal | Why |
|---|---|---|
| Routine timeout rate by endpoint template and network class | Operational metric, optionally sampled diagnostic events | The population rate drives action; one exception per timeout creates noise |
| New parser exception after an API rollout | Grouped exception report plus release/endpoint dimensions | The stack and rollout context identify an actionable defect |
| User taps "Buy" and receives confirmation | Product events for the intent and outcome | The events answer a funnel/product question |
| Checkout is slow across mobile and backend | Sampled distributed trace plus latency metrics | Metrics show magnitude; traces locate the delay |
| Last screen before a crash | Bounded breadcrumb attached to the crash | It is diagnostic context, not a standalone business event |
| Feature-flag exposure for an experiment | Versioned product exposure event, once per defined exposure unit | Logging every flag lookup overcounts exposure and creates avoidable volume |

## Privacy, Retention, and Deletion

Telemetry must be minimized at the call site because downstream redaction can fail and copies may exist in queues, exports, backups, and incident artifacts.

At minimum, every signal family should document:

- allowed and prohibited fields;
- whether stable or pseudonymous identifiers are permitted;
- access roles and auditability;
- on-device and server-side buffering limits;
- retention by environment and signal class;
- deletion behavior across the primary store and supported exports;
- regional routing or residency requirements where applicable;
- behavior when collection consent or policy changes.

This matrix is repository engineering policy, not a universal legal conclusion. Product, privacy, security, and legal owners determine the applicable collection basis and controls for a product and jurisdiction.

## Failure Modes

- **Destination by convenience:** The installed analytics SDK becomes the sink for crashes, retries, and debug strings. The resulting schema answers no coherent question.
- **Exception-per-occurrence:** Expected network or device outcomes exhaust non-fatal quotas and obscure violated invariants.
- **Identifier as metric label:** A user, request, URL, or free-form error value creates unbounded time series and cost.
- **Unsampled high-volume traces:** Instrumentation produces more storage and device/network overhead than the diagnostic value justifies.
- **Breadcrumb as event stream:** A crash-context buffer is queried as if it were a complete product or audit history even though it is bounded and sampled.
- **Collection without deletion:** The primary vendor honors deletion but warehouse exports and incident copies retain the same data indefinitely.

## Staff Engineer Thinking

- Treat telemetry schemas as versioned APIs with owners and compatibility review.
- Budget signal volume, on-device work, network use, storage, and query cost before rollout.
- Keep product measurement and operational diagnosis joinable only through approved, minimized correlation fields.
- Review dashboards and alerts together with the instrumentation that feeds them; collection without a decision path is inventory, not observability.
- Revisit sampling, retention, and field allowlists when a feature, threat model, vendor, or consent state changes.

## Probing Questions

1. A handled timeout occurs 50,000 times a day. When should it be a metric, sampled diagnostic event, or exception report?
2. Why is a raw user ID unsafe as a metric label even when access to the dashboard is restricted?
3. What is the difference between a product event and an operational event with the same name?
4. When do a latency metric and a distributed trace complement rather than duplicate each other?
5. Which controls must be verified when telemetry collection is disabled or a deletion request is processed?

## Answer Key

1. Use a bounded metric when the population rate is the decision input, sampled diagnostics when representative context helps investigation, and a grouped exception report when a specific stack or invariant is actionable. Do not emit all three per occurrence without separate owners and purposes.
2. Metric systems create a time series per unique attribute set, so user IDs create unbounded cardinality and can also constitute personal or profiling data. Use bounded cohorts for metrics and an approved, sampled diagnostic path when individual correlation is necessary.
3. A product event records an intentional action or outcome for product analysis. An operational event records system behavior for reliability or diagnosis. Similar wording does not make their schemas, retention, sampling, or owners interchangeable.
4. A metric shows the size and distribution of a latency problem; a sampled trace shows where time was spent in particular executions. Either can exist alone, but together they support detection and diagnosis.
5. Verify client-side gating, queued and in-flight data, vendor storage, exports, backups, retention expiry, and the documented deletion workflow. An SDK flag alone does not prove all copies were removed.

## Further Reading

- [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) — canonical logs, metrics, traces, and baggage concepts.
- [OpenTelemetry metrics](https://opentelemetry.io/docs/concepts/signals/metrics/) — instruments, aggregation, and attribute considerations.
- [W3C Trace Context](https://www.w3.org/TR/trace-context/) — interoperable trace propagation.
- [Android app data and files](https://developer.android.com/privacy-and-security/about) — platform privacy and security entry point.
- [NIST Privacy Framework](https://www.nist.gov/privacy-framework) — risk-based privacy governance and data-processing controls.
- [`../android/observability/crash-monitoring.md`](../android/observability/crash-monitoring.md) — Android exception-reporting application.
- [`../android/observability/logging.md`](../android/observability/logging.md) — Android device and release logging application.
