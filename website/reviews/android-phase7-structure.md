# Android Phase 7: structure before authoring

Plan written 2026-10-25, before Phase 7 blends. Scope: the fifteen chapters listed under Phase 7 in android.md. The original text, code and diagrams remain in source order and read-only. This plan adds labelled guides; disputed claims receive neutral section notes and are held separately until owner approval.

## Learning route

Start with a user-visible delay, locate its boundary, explain the responsible mechanism, choose evidence, then make a release decision. This is a diagnostic phase: stories differ by topic rather than forcing every topic into the same mechanism template. All numerical traces added here are explicitly illustrative unless a primary API contract states otherwise. No app measurements or benchmark wins are invented.

| Chapter | Beginner entry and narrative | Visual/controlled sequence | Production and staff boundary |
|---|---|---|---|
| Startup | Icon responds but feed is still empty: what has actually finished? | Two finish lines, TTID and useful content; launch evidence stepper | Critical-path ownership, compilation state, representative launch modes |
| Jank | Scroll catches for one frame although API calls are quick | Deadline investigation board; isolate running versus waiting CPU work | Trace a single slow interval, then confirm field cohort and benchmark |
| Rendering | Main thread looks quiet but the displayed frame is late | App recording, rendering and system presentation lanes; handoff sequence | Attribute the bottleneck before changing UI toolkit or GPU work |
| ANRs | Tap waits while another thread owns a lock | Wait-for chain; trace from waiter to owner | Component-specific evidence and mitigation; no one universal timeout |
| Memory/leaks | Every visit leaves another screen behind | Reachability path and retained-object lifecycle sequence | Separate retention, allocation churn and process pressure |
| Native memory/bitmaps | Kotlin heap is steady while image navigation kills the process | Pixel budget and process-memory buckets; decode-size decision | Software/native/graphics visibility, cache ownership and LMK evidence |
| App size/R8 | New SDK grows delivered download and release-only failure appears | Static-reachability boundary plus reflection edge; artifact inspection sequence | Exact-build mapping, scoped rules, device delivery size |
| Baseline Profiles | First journey pays runtime work that later journeys avoid | Rules → packaged artifact → ART verification → benchmark | Baseline versus Startup Profiles, installation uncertainty, measured ROI |
| Macrobenchmark/Perfetto | A red benchmark number alone does not explain a regression | Experiment controls and trace-reading decision board; causal investigation | Match compilation/build/device state, retain raw evidence, avoid noisy gates |
| Battery/power | App appears idle but keeps hardware busy | Activity/cost/attribution matrix; isolate power experiment sequence | Supported power measurement, comparable state, user-value budget |
| Radio wakeups | Many tiny background requests create work between useful events | Batch freshness boundary and retry lifecycle sequence | Durable queue, capped idempotent retries, measured radio behavior |
| Thermal/low-end | Smooth first minute becomes poor after a long session | Device pressure → reversible capability policy; recovery sequence | Cohort-specific budgets, hysteresis as policy, critical work preserved |
| Logging | A debug message is suppressed but its argument still runs | Call construction → policy → sink; lazy-gate sequence | Redaction before sinks, release-artifact verification and cost budget |
| Crash monitoring | A captured stack has no readable names or actionable owner | Capture, persistence, matching symbols, delivery and triage sequence | Coverage gaps, process termination classes, owner/runbook and privacy |
| Mobile APM/RUM | Server response is fast but checkout feels slow | Nested client/server boundaries and telemetry pipeline; trace correlation sequence | Coverage inventory, sampling bias, comparable journeys and SDK overhead |

## Composition and evidence

Each page gets a short problem-first opening, at least one designed visual and one controlled stepper where time/ownership changes matter, then a three-question checkpoint. Checkpoints use `:: check` and are routed to Q&A by the shared engine. Source-backed deeper guides are concise, especially on the six shorter chapters. Original diagrams remain visible through their original renderer; redraws are only added where they teach a useful faithful shape.

Primary evidence: Android Developers startup, App Startup, frame timelines/JankStats, ANR diagnosis, memory and bitmap guides, R8/keep rules, Baseline Profiles, Macrobenchmark, power profiling, network state and thermal APIs; Perfetto documentation; Firebase Crashlytics/Performance; Timber source; W3C Trace Context. Exact consulted links and unresolved original findings will be in android-phase7-findings.md. No Gradle/device profiling is run for authoring.

## Companion book actually consulted

Manifest Android Interview, Jaewoong Eum, supplied 2025-06-16 edition, 459 PDF pages. Initial full text reads: PDF 107–108 (printed 104–105, ART/Dalvik/DEX) and PDF 235–238 (printed 232–235, Baseline Profiles and transition to business logic). These are companion explanations, not current contracts: modern ART retains JIT, profile delivery/compilation is conditional, and fixed improvement percentages are not guarantees. Further fully read ranges will be recorded in the findings, separate from pages located only by keyword search.

## Exit checks

Validate all marker targets against actual H2s, parse every stepper JSON and node reference, verify three questions per page, compare source hashes before/after, inspect prose budget, then request independent review. Parent owns integrated build, preservation, browser/device-size sweeps and publication; do not claim those ran here. Proposed source corrections stay unapplied and have neutral notes before every affected H2, including repeated answer claims.
