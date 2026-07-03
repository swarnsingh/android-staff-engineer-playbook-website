# Learning Paths

This repository is large enough that reading it linearly from `android.md` to `security.md` is a recipe for burnout. Use these paths based on the question you are trying to answer.

---

## Path 1: Mobile System Design Sprint

Use this when you need to design mobile systems under interview or architecture-review pressure.

1. **Start with the framework:** [Mobile System Design Framework](mobile-system-design/design-framework.md)
2. **Learn the mobile/backend contract:** [API Design for Mobile](backend-for-mobile/api-design-for-mobile.md), [Transport Protocols](backend-for-mobile/transport-protocols.md), and [Versioning & Backward Compatibility](mobile-system-design/versioning-and-backward-compatibility.md)
3. **Study the hard mobile constraints:** [Offline Sync](mobile-system-design/offline-sync.md), [Pagination](mobile-system-design/pagination.md), [Image Loading](mobile-system-design/image-loading.md), and [Push Notifications](mobile-system-design/push-notifications.md)
4. **Practice full designs:** [Ride-Hailing](mobile-system-design/ride-hailing.md), [Chat / Messaging](mobile-system-design/chat-messaging.md), [News Feed](mobile-system-design/news-feed.md), and [Payment Flow](mobile-system-design/payment-flow.md)
5. **Read the blueprints:** [Reference Architectures](reference-architectures.md) shows how the same tradeoffs become buildable systems.

---

## Path 2: Senior to Staff Track

Use this when you are already a strong Senior engineer and want to understand Staff-level scope, leverage, and decision quality.

1. **Calibrate the level change:** [Senior to Staff Progression](career/senior-to-staff-progression.md) and [Scope and Ambiguity](career/scope-and-ambiguity.md)
2. **Build leverage:** [Internal Developer Platforms](platform-engineering/internal-developer-platforms.md), [Build Graph Scaling](platform-engineering/build-graph-scaling.md), and [Design Systems Architecture](platform-engineering/design-systems-architecture.md)
3. **Lead through documents and reviews:** [Writing Technical Documents (RFCs)](career/writing-rfcs.md), [Running a Design Review](leadership/running-a-design-review.md), and [Escalation & Decision Making](leadership/escalation-and-decision-making.md)
4. **Operate production systems:** [Incident Response & On-Call](leadership/incident-response-on-call.md), [SLOs](observability/slos.md), [Alerting](observability/alerting.md), and [Release Strategy](release-engineering/release-strategy.md)
5. **Make risk visible:** [Security & Privacy](mobile-system-design/security-and-privacy.md), [Privacy, GDPR & Data Residency](security/privacy-gdpr-data-residency.md), and [Kill Switches](release-engineering/kill-switches.md)

---

## Path 3: Android Performance and Internals Deep Dive

Use this when you want to become the person who can explain crashes, freezes, memory pressure, startup regressions, and battery drain.

1. **Understand the runtime:** [ART & Dalvik](android/os-internals/art-and-dalvik.md), [Zygote](android/os-internals/the-zygote.md), [Binder](android/os-internals/the-binder.md), and [ActivityManager & Process Lifecycle](android/os-internals/activitymanager-process-lifecycle.md)
2. **Master concurrency:** [Coroutines](kotlin/coroutines-and-flow/coroutines.md), [Coroutines Under the Hood](android/concurrency/coroutines-under-the-hood.md), [SharedFlow & StateFlow](android/concurrency/shared-flow-and-state-flow.md), and [Threads & Looper](android/concurrency/threads-and-looper.md)
3. **Measure UI performance:** [Jank](android/performance/jank.md), [Rendering](android/performance/rendering.md), [Compose Performance Tooling](android/compose/compose-performance-tooling.md), and [Macrobenchmark & Perfetto](android/performance/macrobenchmark-and-perfetto.md)
4. **Control resource pressure:** [Memory Management & Leaks](android/performance/memory-management-and-leaks.md), [Native Memory & Bitmaps](android/performance/native-memory-bitmaps.md), [Battery & Power Profiling](android/performance/battery-power-profiling.md), and [Network Radio Wakeups](android/performance/network-radio-wakeups.md)
5. **Close the loop with observability:** [Crash Monitoring](android/observability/crash-monitoring.md), [SLIs](observability/slis.md), [SLOs](observability/slos.md), and [Dashboards](observability/dashboards.md)

---

## Path 4: Foundations First

Use this when you want the mental model underneath Android, Kotlin, distributed systems, and Staff-level architecture.

1. **Learn complexity and data structures:** [Complexity Analysis](engineering-fundamentals/complexity-analysis.md), [Arrays and Strings](computer-science/arrays-and-strings.md), [Hashing](computer-science/hashing.md), [Trees](computer-science/trees.md), and [Graphs](computer-science/graphs.md)
2. **Practice algorithmic patterns:** [Sorting and Searching](computer-science/sorting-and-searching.md), [Recursion and Backtracking](computer-science/recursion-backtracking.md), [Dynamic Programming](computer-science/dynamic-programming.md), and [Greedy Algorithms and Intervals](computer-science/greedy-and-intervals.md)
3. **Build system intuition:** [State Machines](engineering-fundamentals/state-machines.md), [Queues](engineering-fundamentals/queues.md), [Backpressure](engineering-fundamentals/backpressure.md), [Fault Tolerance](engineering-fundamentals/fault-tolerance.md), and [Time & Clocks](engineering-fundamentals/time-and-clocks.md)
4. **Connect to distributed reality:** [Idempotency](distributed-systems/idempotency.md), [Delivery Semantics](distributed-systems/delivery-semantics.md), [Consistency Models](distributed-systems/consistency-models.md), and [Mobile Client Consistency Contracts](distributed-systems/mobile-client-consistency-contracts.md)
5. **Finish with principles:** [Principles](principles.md) turns the mechanics into judgment.
