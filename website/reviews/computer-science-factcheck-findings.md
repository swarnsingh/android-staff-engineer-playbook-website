# Computer Science fact-check: findings in the original chapters

**29 October 2026.** A full fact-check of the 12 Computer Science chapters, requested by the owner before the data-structures interview round. Every chapter was read in full. Claims about APIs, platform behaviour, history, numbers and code were checked against official documentation, specifications, source code or arithmetic. The sources are listed per finding.

**Owner decision, 29 October 2026: all 44 corrections approved.** They are applied on the website from `website/content/corrections-computer-science.json`; the original Markdown is unchanged. The machine-readable proposals, with exact original and replacement text, are in [`computer-science-factcheck-2026-10-29.json`](computer-science-factcheck-2026-10-29.json). Each `old` string was checked to occur exactly once in its chapter, so an approved row can move into a corrections file unchanged, with `status` set to `approved` and a `validation` note added.

Finding CSS01 supersedes SC1 in [the teaching-layer findings](computer-science-teaching-findings.md).

## Summary

| Chapter | High | Medium | Low |
|---|---:|---:|---:|
| Hashing | 7 | 2 | 2 |
| Trees | 4 | 3 | 2 |
| Graphs | 0 | 4 | 4 |
| System Complexity | 4 | 6 | 3 |
| Arrays and Strings | 0 | 1 | 0 |
| Sorting and Searching | 0 | 0 | 1 |
| Heaps and Priority Queues | 0 | 0 | 1 |

Big-O, Linked Lists, Recursion and Backtracking, Dynamic Programming, and Greedy and Intervals had no factual errors. Their claims and code matched the standard definitions; small simplifications (for example, quoting subset generation as O(2^n) rather than O(n·2^n) including copies) were left alone as conventional.

**Severity.** *High*: wrong in a way that would mislead an interview answer or a production decision. *Medium*: inaccurate, or a code bug in an example. *Low*: imprecise wording, or a wrong label or number that does not change the lesson.

## Findings

| ID | Severity | Chapter | Problem | Evidence |
|---|---|---|---|---|
| CSH01 | high | Hashing | String.hashCode is specified and deterministic; JEP 180 replaced the alternative hashing with tree bins. | [source](https://openjdk.org/jeps/180); [source](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/lang/String.html#hashCode()) |
| CSH02 | high | Hashing | The JDK does not use randomized seeds for String keys. | [source](https://openjdk.org/jeps/180) |
| CSH03 | high | Hashing | 2^256 is about 1.16 × 10^77, which is below common atom-count estimates. | Arithmetic: 2^256 = 1.158 × 10^77 |
| CSH04 | high | Hashing | The birthday bound concerns set size (about 2^16), not the probability for a single pair (2^-32). | Birthday problem: n ≈ 1.1774 × sqrt(2^32) ≈ 77,163 for a 50% chance |
| CSH05 | high | Hashing | OkHttp pins hash the Subject Public Key Info, not the whole certificate. | [source](https://github.com/square/okhttp/blob/master/okhttp/src/commonJvmAndroid/kotlin/okhttp3/CertificatePinner.kt) |
| CSH06 | high | Hashing | Verification runs at install time, and Android 12 changed the fallback from a chooser to the default browser. | [source](https://developer.android.com/training/app-links/verify-android-applinks); [source](https://developer.android.com/about/versions/12/behavior-changes-all) |
| CSH07 | high | Hashing | Git documents that its hardened SHA-1 is not vulnerable to SHAttered. | [source](https://git-scm.com/docs/hash-function-transition) |
| CSH08 | medium | Hashing | TREEIFY_THRESHOLD is 8 and MIN_TREEIFY_CAPACITY is 64; ordering within tree bins relies on Comparable keys. | [source](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java) |
| CSH09 | medium | Hashing | The official guidance describes position-based default keys and the Bundle constraint; it does not describe a hash-keyed slot table. | [source](https://developer.android.com/develop/ui/compose/lists) |
| CSH10 | low | Hashing | The values are MD5 digests; the second one was not the MD5 of "hellp". | Computed with md5 on macOS |
| CSH11 | low | Hashing | With the default load factor a HashMap never reaches 99% load. | [source](https://github.com/openjdk/jdk/blob/master/src/java.base/share/classes/java/util/HashMap.java) |
| CST01 | high | Trees | `--amend` replaces only the latest commit, which has no later commits. | [source](https://git-scm.com/docs/git-commit) |
| CST02 | high | Trees | Bitcoin never used SHA-1. | [source](https://git-scm.com/docs/hash-function-transition); [source](https://bitcoin.org/bitcoin.pdf) |
| CST03 | high | Trees | Layout runs on request, not every frame; Hierarchy Viewer is deprecated. | [source](https://developer.android.com/topic/performance/rendering/optimizing-view-hierarchies); [source](https://developer.android.com/reference/android/view/View) |
| CST04 | high | Trees | The shown code walks the whole matching subtree. | Code inspection of the chapter's Trie.wordsWithPrefix |
| CST05 | medium | Trees | Recursion depth equals tree height, not node count. | log2(100,000) ≈ 16.6 |
| CST06 | medium | Trees | Same depth-versus-size correction as CST05. | log2(100,000) ≈ 16.6 |
| CST07 | medium | Trees | B-tree insertion keeps all leaves at the same depth; there is no lagging rebalancing. | [source](https://www.sqlite.org/fileformat2.html); [source](https://www.sqlite.org/eqp.html) |
| CST08 | low | Trees | No logarithmic bound is documented. | [source](https://developer.android.com/develop/ui/compose/lifecycle) |
| CST09 | low | Trees | Read cost scales with the number of levels, not the log of it. | [source](https://github.com/facebook/rocksdb/wiki/RocksDB-Overview) |
| CSG01 | medium | Graphs | Dagger wiring is generated at compile time; the O(n²) claim has no source. | [source](https://dagger.dev/dev-guide/) |
| CSG02 | medium | Graphs | Cross-project parallelism needs org.gradle.parallel or the configuration cache. | [source](https://docs.gradle.org/current/userguide/performance.html#parallel_execution) |
| CSG03 | medium | Graphs | The quoted message is not what Gradle prints; Gradle reports a task cycle. | [source](https://docs.gradle.org/current/userguide/build_lifecycle.html) |
| CSG04 | medium | Graphs | LinkedIn documents its own graph database, LIquid. | [source](https://engineering.linkedin.com/blog/2020/liquid-the-soul-of-a-new-graph-database-part-1) |
| CSG05 | low | Graphs | The scandal broke in 2018. | [source](https://en.wikipedia.org/wiki/Facebook%E2%80%93Cambridge_Analytica_data_scandal) |
| CSG06 | low | Graphs | Recomposition counts are a Layout Inspector feature. | [source](https://developer.android.com/develop/ui/compose/tooling/layout-inspector) |
| CSG07 | low | Graphs | The diagram shows four edges. | Diagram inspection |
| CSG08 | low | Graphs | Nodes outside the cycle can still be emitted; the code already checks the output size. | Code inspection |
| CSS01 | high | System Complexity | The sentence states a ratio and contradicts it, with no source. | Internal consistency |
| CSS02 | high | System Complexity | Accelerate measures delivery performance, not code complexity or output. | [source](https://dora.dev/research/); [source](https://itrevolution.com/product/accelerate/) |
| CSS03 | medium | System Complexity | No source for an exponential relationship. | Same basis as CSS01 |
| CSS04 | high | System Complexity | The Cognitive Complexity specification ignores try/finally and adds the current nesting level. | [source](https://www.sonarsource.com/docs/CognitiveComplexity.pdf) |
| CSS05 | medium | System Complexity | Per the specification, lambdas raise nesting. | [source](https://www.sonarsource.com/docs/CognitiveComplexity.pdf) |
| CSS06 | high | System Complexity | Stability is a property of parameter types. | [source](https://developer.android.com/develop/ui/compose/performance/stability) |
| CSS07 | medium | System Complexity | Skipping depends on stability or strong skipping. | [source](https://developer.android.com/develop/ui/compose/performance/stability/strongskipping) |
| CSS08 | medium | System Complexity | A full file path never equals a fragment such as "/feature/checkout/", so the test checked no files and always passed. | Code inspection; https://docs.konsist.lemonappdev.com/ |
| CSS09 | medium | System Complexity | Same path-comparison bug as CSS08. | Code inspection |
| CSS10 | medium | System Complexity | Detekt has no coupling task or metric. | [source](https://detekt.dev/docs/rules/complexity) |
| CSS11 | low | System Complexity | There is no built-in moduleDependencies task. | [source](https://docs.gradle.org/current/userguide/viewing_debugging_dependencies.html) |
| CSS12 | low | System Complexity | Current defaults: allowedComplexity 14, LargeClass allowedLines 600 (per class). | [source](https://detekt.dev/docs/rules/complexity) |
| CSS13 | low | System Complexity | Three decision points plus one is 4. | Count of decision points |
| CSA01 | medium | Arrays and Strings | The default mutation policy is structuralEqualityPolicy (==). | [source](https://github.com/androidx/androidx/blob/androidx-main/compose/runtime/runtime/src/commonMain/kotlin/androidx/compose/runtime/SnapshotState.kt) |
| CSO01 | low | Sorting and Searching | Binary search works with duplicates; lowerBound and upperBound in this chapter rely on that. | Chapter's own lowerBound/upperBound |
| CSP01 | low | Heaps and Priority Queues | TreeMap and TreeSet are available on the JVM and Android. | [source](https://docs.oracle.com/en/java/javase/21/docs/api/java.base/java/util/TreeMap.html) |

## Not changed

- Unsourced performance figures that cannot be checked either way, such as "MurmurHash3 is roughly 2-4x faster than `String.hashCode()`" or Floyd–Warshall being practical "only for V < ~500". They are worth softening in a later editorial pass, but they are not demonstrably wrong.
- Opinions and recommendations, such as preferring BLAKE3 for new code or the module-depth guidance.
