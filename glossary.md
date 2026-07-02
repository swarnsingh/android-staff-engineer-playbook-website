# Glossary

## Purpose

A centralized dictionary for terms used across the `android-staff-engineer-playbook`. When an acronym or specialized term is used in a canonical file, it should ideally be defined here so readers have a quick reference without losing context.

## Terms

### A-C

- **AAR (Android Archive):** The binary distribution format for Android libraries. Contains compiled bytecode, resources, and an AndroidManifest.
- **ANR (Application Not Responding):** An Android watchdog failure triggered when an app component does not respond within a system timeout. Input dispatch is commonly around 5 seconds; broadcasts, services, and content providers have different thresholds.
- **BFF (Backend for Frontend):** An architectural pattern where a dedicated backend service formats and aggregates data for a specific frontend client, such as a mobile app, rather than exposing only a general-purpose API.
- **BOM (Bill of Materials):** A special Maven POM file that defines a set of library versions that are expected to work together, allowing consumers to omit explicit version numbers.
- **CAP Theorem:** A distributed systems principle stating that during a network partition, a distributed system must choose between consistency and availability for the affected operation. Partition tolerance is not optional in real distributed systems.
- **CI/CD (Continuous Integration / Continuous Delivery or Deployment):** The automated pipeline for building, testing, and distributing software to users or QA.

### D-F

- **DAG (Directed Acyclic Graph):** A graph data structure with no cycles. Used extensively in Gradle task execution and dependency resolution.
- **DI (Dependency Injection):** A design pattern where an object receives its dependencies from an external source rather than creating them itself. Promotes testability and decoupling.
- **Feature Flag (Remote Config):** A server-controlled toggle that allows enabling, disabling, or changing client behavior without requiring an app store update.

### G-I

- **GraphQL:** A query language for APIs that allows clients to request exactly the data they need, mitigating over-fetching and under-fetching.
- **Idempotency:** A property of an operation where applying it multiple times yields the same durable effect as applying it once. Critical for safe network retries, especially payments and offline sync.
- **IDP (Internal Developer Platform):** A suite of tools, paved roads, and self-service infrastructure built by platform engineering teams to accelerate product engineers.

### J-L

- **Jank:** Visible stuttering or dropped frames in a UI, typically caused by work missing the display frame deadline. A 60 Hz display has about 16.7 ms per frame; higher refresh rates have smaller budgets.
- **JWT (JSON Web Token):** A compact, URL-safe way to represent claims transferred between two parties. Commonly used for stateless authentication.
- **Locality of Reference:** The principle that data accessed together should be stored together. Applies to memory layout, cache behavior, and codebase modularization.

### M-O

- **MITM (Man-in-the-Middle):** An attack where an adversary intercepts and potentially alters communication between two parties, such as an app and its backend.
- **NFR (Non-Functional Requirement):** A system quality requirement that defines *how well* the system must behave, such as latency, security, availability, accessibility, or scalability.
- **Observability:** The ability to infer internal system state from external signals such as logs, metrics, traces, crash reports, and user-impacting indicators.

### P-R

- **Pagination:** The process of dividing a large dataset into smaller chunks for efficient network transfer, database queries, rendering, and memory usage.
- **RFC (Request for Comments):** A design document proposing a technical direction, circulated for review before implementation begins.
- **R8:** Google's Android code shrinker, optimizer, obfuscator, and dexer used in modern Android release builds.

### S-U

- **SLI / SLO / SLA:**
  - **SLI (Indicator):** A specific metric, such as crash-free sessions.
  - **SLO (Objective):** The target value for an SLI, such as 99.9% crash-free sessions.
  - **SLA (Agreement):** The external or business agreement that defines consequences if a service target is missed.
- **SRP (Single Responsibility Principle):** The heuristic that a module or class should have one primary reason to change.
- **UDF (Unidirectional Data Flow):** An architectural pattern where state flows down from state holder to UI and events flow up from UI to state holder.

### V-Z

- **Version Catalog:** A Gradle feature that centralizes dependency coordinates and versions, usually in a `libs.versions.toml` file.

---
*Note: This glossary is a living document. Add terms as new canonical files introduce complex jargon.*
