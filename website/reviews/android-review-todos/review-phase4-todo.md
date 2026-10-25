# Phase 4 independent review: disposition

The independent reviewer found teaching-layer problems and additional original claims needing owner review. All listed teaching-layer fixes below are now applied locally. Original source corrections remain unapproved and unapplied.

- MX2's compiler-rejection statement is held outside active content until approval. The StateFlow checkpoint no longer calls its internals lock-free.
- Services now names OS and target-SDK prerequisites, avoids process-survival guarantees, and qualifies expedited scheduling with quota/load and OutOfQuotaPolicy.
- The suspendCoroutine checkpoint distinguishes a cancelled Job, a suspension still waiting for callback, and listener cleanup that depends on the wrapper/API.
- Doze wording accounts for non-exempt apps and non-exhaustive exceptions; the diagram no longer says every app is subject to identical restrictions.
- Threads/Looper no longer describes Handler as the only crossing API, or every Main.immediate execution as a queued message.
- Flow's short subscriber-gap animation says upstream does not restart; it does not promise no database invalidations or queries. The introduction describes a common cold-to-hot architecture, not a rule that all repository sources must be cold.
- Structured concurrency now calls cancellation cooperative, and SC1 distinguishes bare Go goroutines from scoped errgroup patterns.
- Original findings FL1–FL4, SV2, WM1–WM2, MX3 and BO2–BO5 are numbered with evidence and notes before each affected section. BO1 now covers Answer Key 4 as well.

Validation: the pure Kotlin Flow map/catch shape fails compilation exactly as FL4 describes (Kotlin 2.4.21, coroutines 1.11.0). All nine Phase 4 blends parse, their marker targets exist and their stepper JSON is valid; all original Android hashes remain unchanged. Integrated build and browser checks belong to the coordinator after shared edits settle. Android framework code was not compiled, and real-device behaviour was not measured.

## Scope of the independent review

The reviewer read all nine Phase 4 chapters and their teaching files: structured concurrency, Flow, coroutine internals, Threads/Looper, SharedFlow/StateFlow, Mutex/synchronisation, Services, WorkManager and battery optimisation. The review was independent of the original author. It checked contract claims against the Kotlin API references and Android developer documentation, and used small pure-Kotlin probes for the Flow type-narrowing error and suspendCoroutine cancellation state. It did not compile Android framework examples or run physical devices.

The coordinator's follow-up inspected the resulting captions, checkpoint answers and original-finding notes. Source preservation, H2 marker resolution and animation JSON validation complement that technical review; they do not establish foreground-service eligibility, notification permission, Doze behaviour or device-specific scheduling. Those examples remain subject to their stated OS/target conditions. The integrated browser report records whether generated pages load their diagrams, initialise animation controls and fit the tested widths; it is separate from any runtime claim about an Android app.
