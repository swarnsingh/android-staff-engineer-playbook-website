# Platform Engineering: Build Graph Scaling & Profiling

## The Theory
As an Android codebase scales from 10 modules to 200 modules, build times inevitably degrade. A 10-minute local build time destroys developer flow state, limits engineers to just 6 compiles an hour, and burns millions of dollars in wasted salary organization-wide.
A Platform Engineer recognizes that the build system (Gradle) is just another massive, distributed software system. It has bottlenecks, memory leaks, and inefficient dependency chains (the Build Graph) that must be rigorously profiled and optimized.

## Staff-Level Application in Mobile

### 1. The Build Graph (DAG) Bottleneck
Gradle executes tasks based on a Directed Acyclic Graph (DAG). If Module C depends on Module B, and Module B depends on Module A, the graph is a straight line (`A -> B -> C`).
-   **The Problem (Sequential Execution):** If a developer changes code in Module A, Gradle must recompile A. Then it *must wait* for A to finish before it can start recompiling B. Then it waits for B to finish before starting C. This is sequential, blocking execution. It does not matter if the developer has a 16-core MacBook Pro; 15 of those cores are sitting idle waiting for the bottleneck.
-   **The Solution (Flattening the Graph):** A Platform Engineer analyzes the graph and restructures dependencies to maximize width (parallelism) rather than depth. If Module B doesn't actually need Module A's code to compile, but is just passing it along to C, the dependency is broken. The goal is to allow Gradle to compile A, B, and C simultaneously on 3 separate CPU cores.

### 2. Remote Build Cache (The Force Multiplier)
Even with a flat graph, compiling 200 modules from scratch on a clean build takes time.
-   **The Junior Approach:** Every developer compiles every module locally on their machine. If Alice compiles `:feature:login`, and then Bob pulls `main` and compiles `:feature:login`, Bob's laptop wastes 2 minutes doing the exact same mathematical computations Alice's laptop just did.
-   **The Staff Approach (Remote Caching):** The Platform team deploys a Gradle Remote Build Cache server (or uses Develocity/Gradle Enterprise).
    -   When the CI server compiles `:feature:login` on the `main` branch, it calculates the hash of the source files. It compiles the bytecode and uploads the output to the remote cache, keyed by the hash.
    -   When Bob pulls `main` and hits "Build", his local Gradle calculates the hash of his local `:feature:login` files. It asks the Remote Cache, "Do you have the compiled output for this hash?"
    -   The Remote Cache says "Yes," and downloads the pre-compiled bytecode instantly. Bob's local machine does zero compilation. A 10-minute clean build drops to 30 seconds (network download time).

### 3. Build Profiling (Data-Driven Optimization)
You cannot fix what you cannot measure. Guessing why the build is slow is an anti-pattern.
-   **The `--scan` Flag:** Platform Engineers rely heavily on Gradle Build Scans. This generates a comprehensive web report of the entire build lifecycle.
-   **What to look for:**
    -   **Garbage Collection Time:** If the scan shows the JVM spent 30% of the build time doing Garbage Collection, the Gradle Daemon is starving for RAM. The Platform team updates the central `gradle.properties` to increase `org.gradle.jvmargs=-Xmx8g`.
    -   **Task Configuration Avoidance:** If the "Configuration" phase takes 45 seconds before any compilation even begins, a rogue Gradle plugin is doing heavy I/O (like reading files) during configuration, rather than deferring it to the execution phase. The Platform team must rewrite or ban the offending plugin.
    -   **Cache Misses:** If the Remote Cache is enabled but the scan shows a 10% hit rate, something is breaking the cache keys (e.g., a plugin embedding absolute file paths or absolute timestamps into generated code).

### 4. Configuration Caching
Gradle 7+ introduced Configuration Caching, arguably the most impactful build optimization in years.
-   **The Theory:** Gradle spends significant time (often 10-20 seconds) just reading all the `build.gradle` files and figuring out the DAG *before* it does any work.
-   **The Feature:** Configuration Caching serializes that DAG to disk. On the next build, if no `build.gradle` files have changed, Gradle skips the configuration phase entirely and jumps straight to execution.
-   **The Platform Challenge:** Many legacy, third-party Gradle plugins use APIs that are incompatible with Configuration Caching (e.g., trying to read project state during execution). The Platform team must identify, upgrade, or rip out these incompatible plugins to unlock the feature for the organization.

## Common Pitfalls
-   **`api` vs `implementation` Leakage:** The most common cause of sequential build bottlenecks. If Module A uses `api project(':module_b')`, any change to Module B forces Module A (and everything that depends on A) to recompile. Enforcing the use of `implementation` creates ABI (Application Binary Interface) boundaries, meaning changes to the internal implementation of B do *not* force A to recompile.
-   **Ignoring Annotation Processors:** KAPT (Kotlin Annotation Processing Tool) runs before the Kotlin compiler. It is notoriously slow and breaks incremental compilation in older versions. Platform teams must aggressively migrate the organization from KAPT to KSP (Kotlin Symbol Processing) to halve annotation processing times.
