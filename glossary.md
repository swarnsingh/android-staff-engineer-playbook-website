# Glossary

## Purpose
A centralized dictionary for terms used across the `android-staff-engineer-bible`. When an acronym or specialized term is used in a canonical file, it should ideally be defined here so readers have a quick reference without losing context.

## Terms

### A-C
-   **AAR (Android Archive):** The binary distribution format for Android libraries. Contains compiled bytecode, resources, and an AndroidManifest.
-   **ANR (Application Not Responding):** An error triggered by the Android OS when the Main (UI) thread is blocked for too long (typically 5 seconds).
-   **BFF (Backend for Frontend):** An architectural pattern where a dedicated backend service is created specifically to format and aggregate data for a single frontend client (e.g., a Mobile app), rather than a general-purpose API.
-   **BOM (Bill of Materials):** A special Maven POM file that defines a set of library versions that are guaranteed to work together, allowing consumers to omit explicit version numbers.
-   **CAP Theorem:** A distributed systems principle stating that a system can only guarantee two out of three characteristics: Consistency, Availability, and Partition Tolerance.
-   **CI/CD (Continuous Integration / Continuous Deployment):** The automated pipeline for building, testing, and distributing software to users or QA.

### D-F
-   **DAG (Directed Acyclic Graph):** A graph data structure with no loops. Used extensively in Gradle task execution and dependency resolution.
-   **DI (Dependency Injection):** A design pattern where an object receives its dependencies from an external source rather than creating them itself. Promotes testability and decoupling.
-   **Feature Flag (Remote Config):** A server-side toggle that allows enabling or disabling a feature in the client application without requiring an app store update.

### G-I
-   **GraphQL:** A query language for APIs that allows clients to request exactly the data they need, mitigating over-fetching and under-fetching.
-   **Idempotency:** A property of an operation where applying it multiple times yields the same result as applying it once. Critical for safe network retries (e.g., payment processing).
-   **IDP (Internal Developer Platform):** A suite of tools, paved roads, and self-service infrastructure built by Platform Engineering teams to accelerate product engineers.

### J-L
-   **Jank:** Visible stuttering or dropped frames in a UI, typically caused by the Main thread taking longer than 16ms to render a frame.
-   **JWT (JSON Web Token):** A compact, URL-safe means of representing claims to be transferred between two parties. Commonly used for stateless authentication.
-   **Locality of Reference:** The principle that data accessed together should be stored together. Applies to memory layout and codebase modularization.

### M-O
-   **MITM (Man-in-the-Middle):** An attack where an adversary intercepts and potentially alters communication between two parties (e.g., an app and its backend).
-   **NFR (Non-Functional Requirement):** System requirements that dictate *how* the system should perform, rather than *what* it should do (e.g., latency, security, scalability).
-   **Observability:** A measure of how well the internal states of a system can be inferred from knowledge of its external outputs (Logs, Metrics, Traces).

### P-R
-   **Pagination:** The process of dividing a large dataset into smaller, discrete chunks (pages) for efficient network transfer and memory usage.
-   **RFC (Request for Comments):** A design document written by an engineer proposing a technical architecture, circulated for peer review before implementation begins.
-   **R8:** Google's compiler that shrinks, obfuscates, and optimizes Android bytecode.

### S-U
-   **SLI / SLO / SLA:** 
    -   *SLI (Indicator):* A specific metric (e.g., Crash-Free Sessions).
    -   *SLO (Objective):* The target value for the SLI (e.g., 99.9% Crash-Free).
    -   *SLA (Agreement):* The business contract dictating what happens if the SLO is missed.
-   **SRP (Single Responsibility Principle):** The heuristic that a module or class should have only one reason to change.
-   **UDF (Unidirectional Data Flow):** An architectural pattern where state flows down (from ViewModel to UI) and events flow up (from UI to ViewModel).

### V-Z
-   **Version Catalog:** A Gradle feature that centralizes dependency coordinates and versions into a single TOML file.

---
*Note: This glossary is a living document. Add terms as new canonical files introduce complex jargon.*
