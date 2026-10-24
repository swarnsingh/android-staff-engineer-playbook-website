# Runtime, JVM interop, and Kotlin 2.4 technical audit

Reviewed on 25 October 2026. This is an authoring report, not learner-facing prose.

Read all four source chapters: `kotlin/runtime-and-jvm/bytecode.md`, `jvm-interop.md`, `memory-model.md`, and `kotlin/version-updates/kotlin-2-4-update.md`. The website overlay contains 44 exact, unique replacements. Canonical Markdown was not edited; every existing topic, heading, and question remains in the source.

## Evidence

Current [Kotlin 2.4.0 release notes](https://kotlinlang.org/docs/whatsnew24.html) and [Swift export documentation](https://kotlinlang.org/docs/native-swift-export.html) support the release chapter's major assertions: stable context parameters with experimental exceptions, explicit backing fields, annotation targeting, UUID API with generation exceptions, sorted-order checks, Java 26 targeting, Gradle 9.5 compatibility, Alpha Swift export, typed Flow-to-AsyncSequence export, and default dispatcher. No correction to that chapter was necessary from these checks. Its API examples are illustrative fragments; an Android/KMP project was not built.

Compiled a minimal probe with local Kotlin/JVM 2.2.21 and OpenJDK 17.0.19, inspected it with javap, and attempted Java subclassing with javac. Results:

- Top-level internal `greet` is public `greet(String)`; internal member `greet` is `greet$audit(String)`.
- `List<Box<Number>>` return signature contains no extends wildcards.
- An overload with defaulted parameters before/after a required parameter gains `(Int, String)` and `(String)` overloads.
- Named object methods belong to `TelemetryClient`, not the file facade.
- Same-package Java subclassing of the shown sealed class fails because its constructor is private.
- Nullable `Any?.toString()` returns the text `null`.
- Boxing the small integer 5 reuses a wrapper in this run; nullable representation does not prove fresh allocation.
- Eager map visits the complete source before terminal lookup. The standard collection contract confirms map/filter create intermediates while firstOrNull creates no third collection.

These observations are compiler/runtime-specific checks, not evidence that all bytecode shapes are universal. Probe files and raw command output were temporary local verification artifacts.

## Corrections

The overlay fixes Java-facing call sites, top-level/member visibility lowering, wildcard return signatures, required Java Unit returns, default-parameter ABI promises, value-class boxed/unboxed terminology, sealed hierarchy restrictions, nullable-toString behaviour, the javap classpath command, generated data-class methods, eager collection allocation counting, and DEX/runtime optimisation boundaries.

The memory corrections address references stored in heap objects, boxing/cache-dependent allocation counts, the missing fourth reference-strength answer, phantom reachability, Android 8 versus Android 10 collector chronology, bitmap storage history, UI callback ownership, profiler instance-count heuristics, and the distinction between RSS and managed-heap accounting. They also identify JEP 197 as code-cache material rather than heap-GC guidance.

Every correction has primary-source links in `website/content/corrections-runtime.json`. These are minimal overlays applied by the site build; source drift should fail the exact-match check rather than silently discard text.

## Limits

No Android SDK app, R8 build, physical-device profiler, Swift export integration, or Kotlin 2.4 compilation was run in this audit. Historical instruction offsets, runtime timing values, library dependency versions, unprovided app APIs, and workload-specific performance claims are not certified by a source read. Recommendations require context; this audit does not establish an error-free guarantee for all source content or every supported platform.
