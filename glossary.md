# Glossary

## Purpose

A centralized dictionary for terms used across the `android-staff-engineer-playbook`. When an acronym or specialized term is used in a canonical file, it should ideally be defined here so readers have a quick reference without losing context.

## Terms

### 0-9

- **16 KB Page Size:** The larger memory-page configuration on modern ARM64 Android devices. Since November 2025, Google Play requires apps targeting Android 15+ to ship 16 KB-compatible native libraries (ELF segments aligned to 2^14). See [`release-engineering/16kb-page-sizes.md`](release-engineering/16kb-page-sizes.md).

### A-C

- **AAR (Android Archive):** The binary distribution format for Android libraries. Contains compiled bytecode, resources, and an AndroidManifest.
- **AICore:** The Android system service that hosts, updates, and runs Gemini Nano on device with hardware acceleration and platform safety filters. Apps reach it through the ML Kit GenAI APIs. See [`mobile-system-design/on-device-ai.md`](mobile-system-design/on-device-ai.md).
- **ANR (Application Not Responding):** An Android watchdog failure triggered when an app component does not respond within a system timeout. Input dispatch is commonly around 5 seconds; broadcasts, services, and content providers have different thresholds.
- **BFF (Backend for Frontend):** An architectural pattern where a dedicated backend service formats and aggregates data for a specific frontend client, such as a mobile app, rather than exposing only a general-purpose API.
- **BOM (Bill of Materials):** A special Maven POM file that defines a set of library versions that are expected to work together, allowing consumers to omit explicit version numbers.
- **CAP Theorem:** A distributed systems principle stating that during a network partition, a distributed system must choose between consistency and availability for the affected operation. Partition tolerance is not optional in real distributed systems.
- **CI/CD (Continuous Integration / Continuous Delivery or Deployment):** The automated pipeline for building, testing, and distributing software to users or QA.

### D-F

- **DAG (Directed Acyclic Graph):** A graph data structure with no cycles. Used extensively in Gradle task execution and dependency resolution.
- **DI (Dependency Injection):** A design pattern where an object receives its dependencies from an external source rather than creating them itself. Promotes testability and decoupling.
- **Entitlement:** The server-side record that a user has paid for (and still holds) access to a product — the thing your backend owns in a Play Billing integration, distinct from the purchase itself, which Google owns. See [`mobile-system-design/play-billing-and-subscriptions.md`](mobile-system-design/play-billing-and-subscriptions.md).
- **Feature Flag (Remote Config):** A server-controlled toggle that allows enabling, disabling, or changing client behavior without requiring an app store update.

### G-I

- **Glance:** The Jetpack framework for building home-screen app widgets (and Wear widgets) with Compose syntax that is translated to RemoteViews — not real Compose, and not interoperable with it. See [`android/compose/form-factors-matrix.md`](android/compose/form-factors-matrix.md).
- **GMD (Gradle Managed Devices):** Gradle-provisioned, headless emulators (including stripped-down ATD images) declared in build config, giving CI a reproducible device matrix. See [`android/testing/testing-strategy.md`](android/testing/testing-strategy.md).
- **Grace Period / Account Hold:** The two involuntary-churn stages of a Play subscription after a failed renewal payment: during grace the user keeps access while Google retries; on hold, access is revoked but the subscription is still recoverable. See [`mobile-system-design/play-billing-and-subscriptions.md`](mobile-system-design/play-billing-and-subscriptions.md).
- **GraphQL:** A query language for APIs that allows clients to request exactly the data they need, mitigating over-fetching and under-fetching.
- **Idempotency:** A property of an operation where applying it multiple times yields the same durable effect as applying it once. Critical for safe network retries, especially payments and offline sync.
- **IDP (Internal Developer Platform):** A suite of tools, paved roads, and self-service infrastructure built by platform engineering teams to accelerate product engineers.

### J-L

- **Jank:** Visible stuttering or dropped frames in a UI, typically caused by work missing the display frame deadline. A 60 Hz display has about 16.7 ms per frame; higher refresh rates have smaller budgets.
- **JWT (JSON Web Token):** A compact, URL-safe way to represent claims transferred between two parties. Commonly used for stateless authentication.
- **Lint Baseline:** A recorded snapshot of existing lint violations that grandfathers old code while holding new code to the rule — the mechanism behind severity-ratchet rollouts. See [`platform-engineering/custom-lint-and-static-analysis.md`](platform-engineering/custom-lint-and-static-analysis.md).
- **LiteRT:** Google's on-device ML runtime, the renamed TensorFlow Lite (`.tflite` models converted from TensorFlow, PyTorch, or JAX) with GPU/NPU acceleration. See [`mobile-system-design/on-device-ai.md`](mobile-system-design/on-device-ai.md).
- **Locality of Reference:** The principle that data accessed together should be stored together. Applies to memory layout, cache behavior, and codebase modularization.

### M-O

- **MITM (Man-in-the-Middle):** An attack where an adversary intercepts and potentially alters communication between two parties, such as an app and its backend.
- **NFR (Non-Functional Requirement):** A system quality requirement that defines *how well* the system must behave, such as latency, security, availability, accessibility, or scalability.
- **Observability:** The ability to infer internal system state from external signals such as logs, metrics, traces, crash reports, and user-impacting indicators.

### P-R

- **Pagination:** The process of dividing a large dataset into smaller chunks for efficient network transfer, database queries, rendering, and memory usage.
- **Replacement Mode:** The Play Billing policy chosen when a user switches subscription plans, controlling when the change takes effect and how remaining value is credited (time proration, prorated charge, full price, deferred, etc.). See [`mobile-system-design/play-billing-and-subscriptions.md`](mobile-system-design/play-billing-and-subscriptions.md).
- **RFC (Request for Comments):** A design document proposing a technical direction, circulated for review before implementation begins.
- **RTDN (Real-Time Developer Notifications):** Google Play's Pub/Sub push telling your backend that a purchase or subscription changed state. A trigger only — the actual state must be fetched from the Play Developer API. See [`mobile-system-design/play-billing-and-subscriptions.md`](mobile-system-design/play-billing-and-subscriptions.md).
- **R8:** Google's Android code shrinker, optimizer, obfuscator, and dexer used in modern Android release builds.

### S-U

- **SLI / SLO / SLA:**
  - **SLI (Indicator):** A specific metric, such as crash-free sessions.
  - **SLO (Objective):** The target value for an SLI, such as 99.9% crash-free sessions.
  - **SLA (Agreement):** The external or business agreement that defines consequences if a service target is missed.
- **SDUI (Server-Driven UI):** An architecture where the server sends a declarative description of screen structure and content, and the client renders it from a local component vocabulary — moving UI iteration off the release train. See [`mobile-system-design/server-driven-ui.md`](mobile-system-design/server-driven-ui.md).
- **SRP (Single Responsibility Principle):** The heuristic that a module or class should have one primary reason to change.
- **Strong Skipping:** The Compose compiler mode that makes composables with unstable parameters skippable by comparing those parameters with instance equality (`===`) and auto-memoizing lambdas. See [`android/compose/stability.md`](android/compose/stability.md).
- **UAST (Unified Abstract Syntax Tree):** The language-agnostic AST that Android Lint detectors analyze so a single rule covers both Kotlin and Java sources. See [`platform-engineering/custom-lint-and-static-analysis.md`](platform-engineering/custom-lint-and-static-analysis.md).
- **UDF (Unidirectional Data Flow):** An architectural pattern where state flows down from state holder to UI and events flow up from UI to state holder.

### V-Z

- **Value Class:** A Kotlin class wrapping a single value into a distinct compile-time type that is usually inlined away at runtime — boxed whenever used as a nullable, generic, or supertype. See [`kotlin/language-core/value-classes.md`](kotlin/language-core/value-classes.md).
- **Version Catalog:** A Gradle feature that centralizes dependency coordinates and versions, usually in a `libs.versions.toml` file.
- **ViewCompositionStrategy:** The policy controlling when a `ComposeView`'s composition is disposed; choosing the wrong one (notably the pooling-aware default inside fragments) silently resets Compose state. See [`android/compose/view-interop-and-migration.md`](android/compose/view-interop-and-migration.md).
- **W3C Trace Context:** The standard HTTP headers (`traceparent`, `tracestate`) that propagate a distributed trace across service and vendor boundaries. See [`android/observability/mobile-apm-and-rum.md`](android/observability/mobile-apm-and-rum.md).
- **Widevine L1 / L3:** The hardware-backed (L1) and software (L3) DRM security levels; content licensors typically gate HD/UHD playback on L1, so L3 fallback implies capping resolution. See [`android/media/media3-player-architecture.md`](android/media/media3-player-architecture.md).

---
*Note: This glossary is a living document. Add terms as new canonical files introduce complex jargon.*
