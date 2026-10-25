# Android Phase 6 — structure before authoring

Defined 2026-10-25, before creating this phase's three blends. Originals stay byte-identical; the added layer explains a testing decision, not a second copy of the chapter. Each page gets three Q&A checkpoints and a step-through mechanism. Original diagrams stay available. No correction is approved by this work.

| Chapter | Opening problem and learning sequence | Mechanism / visual | Production and staff destination |
|---|---|---|---|
| Testing strategy | A merge gate is slow and no longer trusted → identify escaped risk → choose the cheapest sufficient evidence → manage failure signals | Risk-to-test evidence map; failed run → bounded investigation → classification → accountable quarantine → repair | Feedback latency, release risk, ownership and contracts; policy numbers are examples |
| Unit testing | A cart rule breaks only with a particular input → expose dependencies → drive a fake → observe a public outcome → keep integration at a separate seam | Fake repository request/response trace; inputs, subject and observable contract | Deterministic state and interaction assertions, maintenance cost; disputed scheduler passages stay under review |
| UI testing | A button looks correct but its action is disconnected → distinguish pixels, semantics and callback → test the smallest observable UI contract → add platform integration when required | Click-to-callback trace; semantic / visual / platform evidence map | State-driven component tests, reviewed visual baselines and representative device coverage |

## Sources actually read

- All three original chapters in full, including code, tables and Answer Keys.
- Jaewoong Eum, *Manifest Android Interview* (PDF metadata creation 2025-06-16): **PDF pages 448–451 only**, printed pages 445–448, read in full for state-driven Compose interaction, semantic queries and bounded waits. This is secondary framing, not an API contract. The book's broad synchronization claims were not adopted.
- [Android coroutine testing](https://developer.android.com/kotlin/coroutines/test), [advanceTimeBy API](https://kotlinlang.org/api/kotlinx.coroutines/kotlinx-coroutines-test/kotlinx.coroutines.test/advance-time-by.html), [JUnit 5.11.4 lifecycle and nested tests](https://docs.junit.org/5.11.4/user-guide/index.html#writing-tests-nested).
- [Compose synchronization](https://developer.android.com/develop/ui/compose/testing/synchronization), [Hilt testing](https://developer.android.com/training/dependency-injection/hilt-testing), [Compose accessibility testing](https://developer.android.com/develop/ui/compose/accessibility/testing), [semantics merging](https://developer.android.com/develop/ui/compose/accessibility/merging-clearing), [Paparazzi's task contract](https://github.com/cashapp/paparazzi#tasks).

## Review boundary

Findings go in `android-phase6-findings.md`; neutral notices precede every affected H2. No pending scheduler, lifecycle, test-host or accessibility API correction is taught as a settled replacement in the blend. Each chapter keeps its own order and all original units. Author checks cover markers and animation JSON, not Android compilation, devices or browser fidelity. Independent review and integrated preservation/browser checks remain separate gates.
