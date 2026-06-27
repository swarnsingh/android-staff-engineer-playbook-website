# Learning Paths

This repository is massive. Reading it linearly from `android.md` to `security.md` is a recipe for burnout.
Instead, use these curated learning paths based on your immediate goals.

---

## Path 1: The "I have a System Design Interview next week" Sprint
If you need to quickly ramp up on how to design mobile systems at scale, focus entirely on the application of architecture and distributed systems.

1.  **Start with the Framework:** [Mobile System Design Framework](mobile-system-design.md)
2.  **Understand the Backend Constraints:**
    *   [API Design for Mobile](backend-for-mobile/api-design-for-mobile.md)
    *   [Transport Protocols](backend-for-mobile/transport-protocols.md)
3.  **Master the Hard Constraints (The "Gotchas"):**
    *   [Offline Sync](mobile-system-design/offline-sync.md) (The hardest problem in mobile)
    *   [Pagination](mobile-system-design/pagination.md)
    *   [Image Loading](mobile-system-design/image-loading.md)
4.  **Review the Blueprints:** Read the [Reference Architectures](reference-architectures.md) to see how the pieces fit together into a cohesive app.

---

## Path 2: The "Senior to Staff" Promotion Track
If you are already a strong technical Senior engineer and want to understand the *scope* and *impact* required for Staff.

1.  **The Mindset Shift:**
    *   [Senior to Staff Progression](career/senior-to-staff-progression.md)
    *   [Scope and Ambiguity](career/scope-and-ambiguity.md)
2.  **Building Leverage (Platform Engineering):**
    *   [Internal Developer Platforms](platform-engineering/internal-developer-platforms.md)
    *   [Build Graph Scaling](platform-engineering/build-graph-scaling.md)
3.  **Communication & Leadership:**
    *   [Writing Technical Documents (RFCs)](career/writing-rfcs.md)
    *   [Incident Response & On-Call](leadership/incident-response-on-call.md)
    *   [Influence Without Authority](leadership/influence-without-authority.md)

---

## Path 3: The Android Performance & Internals Deep Dive
If you want to become the resident expert on why the app is crashing, freezing, or draining the battery.

1.  **The Engine (Kotlin & OS):**
    *   [Kotlin Bytecode](kotlin/bytecode.md)
    *   [ART & Dalvik](android/os-internals/art-and-dalvik.md)
    *   [The Binder](android/os-internals/the-binder.md)
2.  **Concurrency:**
    *   [Coroutines Under the Hood](android/concurrency/coroutines-under-the-hood.md)
    *   [Threads and Looper](android/concurrency/threads-and-looper.md)
3.  **Performance Bottlenecks:**
    *   [Jank & Rendering](android/performance/jank.md)
    *   [ANRs](android/performance/anrs.md)
    *   [Memory Management & Leaks](android/performance/memory-management-and-leaks.md)
4.  **Measurement (Observability):**
    *   [SLIs, SLOs, and SLAs](observability/slis.md)
    *   [Crash Monitoring](android/observability/crash-monitoring.md)

---

## Path 4: The "Foundations First" Academic Track
If you have time and want to build a bulletproof mental model of software engineering from the ground up, independent of the Android framework.

1.  **Computer Science & Complexity:**
    *   [System Complexity](computer-science/system-complexity.md)
    *   [Big-O](engineering-fundamentals/complexity-analysis.md)
2.  **Engineering Fundamentals:**
    *   [State Machines](engineering-fundamentals/state-machines.md)
    *   [Idempotency](distributed-systems/idempotency.md)
    *   [Time & Clocks](engineering-fundamentals/time-and-clocks.md)
3.  **Principles:** Read the entire [Principles](principles.md) tree, starting with *Single Responsibility* and ending with *Optimize for Change*.
