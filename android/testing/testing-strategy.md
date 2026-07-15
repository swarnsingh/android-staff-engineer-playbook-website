# Testing Strategy at Scale

## Overview

[`unit-testing.md`](unit-testing.md) and [`ui-testing.md`](ui-testing.md) cover how to write good tests and which tools to use. This file covers the layer above: how a 50–500-engineer Android org decides **what to test where, what it costs, who owns a failure, and how CI turns tests into a merge gate that engineers trust** — the difference between a test suite and a testing *system*.

The canonical split: the pyramid tiers and their mechanics live in [`unit-testing.md`](unit-testing.md#the-test-pyramid-android-edition); UI-test tool selection and flake policy for UI tests live in [`ui-testing.md`](ui-testing.md#ui-test-governance-at-scale). This file owns the economics, the CI topology, and the organizational machinery.

## Why It Matters

At small scale, testing strategy is a style question. At org scale it becomes an economics problem with compounding failure modes:

- A suite whose PR gate takes 40 minutes changes *how people work*: batched commits, fewer refactors, pressure to skip tests.
- A 2% flake rate on a 1,000-test suite means the average full run contains ~20 false failures — engineers learn to re-run without reading, and the suite stops catching real regressions **while still costing full price**.
- Every tier decision multiplies across the org: moving a class of checks from emulator to JVM saves minutes × thousands of runs × years.

Staff engineers own this system the way they own production reliability — with budgets, SLOs, and explicit ownership, not aspirations.

## First Principles

1.  **A test's value is information per unit cost.** Cost = write + run-time × frequency + maintenance + flake-triage. A slow, flaky E2E test that catches what a ViewModel test would catch has negative value.
2.  **Trust is the product.** The moment engineers stop believing a red build means a real bug, the suite's value collapses to zero regardless of coverage numbers.
3.  **Every test has exactly one owner.** A failure with no owner is a failure that gets muted.
4.  **Determinism is designed, not hoped for.** Flakes come from unowned time, network, ordering, and shared state ([`../../principles/determinism.md`](../../principles/determinism.md)) — each is an injectable seam.

## Mental Model

Run the test suite like an **airport security system**.

- **Layered screening:** cheap, fast checks screen everyone (JVM tests on every PR); expensive checks (full-device E2E) screen selectively (main branch, nightly, release candidates). Screening every passenger with the most expensive machine bankrupts the airport and creates six-hour queues.
- **False alarms are the enemy of security, not just throughput:** if the scanner beeps on every belt buckle, agents start waving people through. That's a flaky suite — the *alarm fatigue*, not the missed threat, is what kills the system.
- **Lanes have SLOs:** the airport publishes queue times and staffs to them. Your PR gate has a latency budget someone defends.

## The Tier Portfolio and Its Economics

The tiers themselves are defined in [`unit-testing.md`](unit-testing.md#the-test-pyramid-android-edition); at strategy level, what matters is their cost profile and *placement*:

| Tier | Runs on | Cost/run | Flake source | Belongs in |
|---|---|---|---|---|
| JVM unit (JUnit, Turbine) | Every PR, pre-merge | Seconds | ~None if deterministic | PR gate |
| JVM Android (Robolectric, Paparazzi screenshots) | Every PR | Seconds–minutes | Low | PR gate |
| Instrumented (Gradle Managed Devices/ATD emulators) | Main branch per-merge; affected-module subset on PR | Minutes | Medium | Merge gate / main |
| Real-device lab (Firebase Test Lab, device farms) | Nightly + release branch | Tens of minutes | High (hardware, OEM) | Nightly / release |
| Full E2E journeys | Nightly + release candidates | High | Highest | Release qualification |

Placement rules that keep the system honest:

- **The PR gate is a latency budget first.** Pick a number (e.g., p95 ≤ 15 min) and treat regressions like production latency regressions. Everything that doesn't fit moves down the topology, not into the gate.
- **Affected-module test selection** (build-graph-aware: only test what a change can reach) is the single highest-leverage CI optimization in a modularized app — it's why modularization is a *testing* strategy, not just a build strategy ([`../../platform-engineering/build-graph-scaling.md`](../../platform-engineering/build-graph-scaling.md)).
- **Push checks down-tier aggressively.** Every check should run on the cheapest tier that can catch its failure class: screenshot diffs on JVM (Paparazzi) not devices; navigation logic in Robolectric not E2E; business logic in plain JUnit, always.

## Flakiness as a System, Not a Nuisance

### The machinery

1.  **Detect:** CI records every test's pass/fail history. A test that fails then passes on retry *with no code change* is a flake event — tracked per test, per module, per owner.
2.  **Quarantine:** tests crossing a flake threshold (e.g., >0.5% over 7 days) are automatically moved out of the blocking gate into a quarantine lane — they still run, they don't block merges, and a ticket is filed on the owning team.
3.  **Fix or delete within SLO:** quarantine has a time limit (e.g., 14 days). A test nobody fixes in two weeks is a test nobody values — delete it ([`../../principles/prefer-deletion.md`](../../principles/prefer-deletion.md)).
4.  **Report:** flake rate is a first-class engineering metric on the same dashboard as crash rate.

### Retry policy — the honest version

Blanket auto-retry ("run everything up to 3×") is the most common and most corrosive policy: it converts flakes into invisible latency, hides real race conditions (a test failing 40% of the time passes 78% of runs under 3 retries), and removes the pressure that gets flakes fixed.

The defensible policy: **retry only quarantine-lane tests; blocking-lane failures are real until proven otherwise.** If the org insists on retries in the blocking lane, every retried-then-passed run must still count as a flake event feeding the quarantine system — retries may mask a failure for a merge, never for the metrics.

### Attribution

Flaky tests get fixed when exactly one team is on the hook. Ownership maps from module → team (CODEOWNERS); shared/E2E journeys have named owning teams, not "QA." The quarantine bot files tickets against that owner with the failure history attached — no human triage step, because unowned triage queues rot.

## CI Topology

```
PR opened ──► PR gate (budget: ~15 min)
│              • lint + detekt + api-check
│              • JVM unit + Robolectric + Paparazzi (affected modules)
│              • instrumented smoke subset (ATD, affected modules)
▼
Merge queue ──► per-merge on main
│              • full JVM suite
│              • instrumented suite on Gradle Managed Devices (sharded)
▼
Nightly ──────► real-device matrix (Test Lab: OEM × API spread)
│              • full E2E journeys
│              • performance/macrobenchmark suites
▼
Release branch ► release qualification
               • full matrix + monkey/stress + screenshot full-diff
```

- **Merge queue** (batching merges and testing the *combined* result) prevents the "two green PRs, red main" problem that otherwise burns the platform team's mornings.
- **Device strategy:** Gradle Managed Devices with ATD images are the modern default for CI emulators — AGP provisions/tears down devices, ATD images strip non-test services for lower CPU/memory, snapshots cut startup, and sharding is one `gradle.properties` entry (`android.experimental.androidTest.numManagedDeviceShards=<n>` — note it provisions shards × devices in the group, so budget CI resources accordingly). Note ATD's documented limit: hardware-rendering-dependent screenshot tests aren't supported — another reason screenshot testing belongs on JVM. Real-device labs cover what emulators can't: OEM skins, thermal behavior, real cameras/radios.
- **Caching is strategy:** Gradle build cache + test-result caching means unchanged modules genuinely skip their tests. This only works if tests are hermetic — a test that reads the network or the clock silently defeats caching correctness.

## Contract Tests Against the BFF

The mobile-specific gap in most pyramids: your integration tests mock the backend, the backend's tests mock you, and the wire contract drifts until production finds it.

- **Consumer-driven contracts:** the app publishes the requests it makes and the response shapes it depends on (generated from the same serialization models the app ships). Backend CI replays them against the real BFF implementation; a breaking change fails *their* build before it ships.
- The cheap version that captures 80% of the value: schema-validate recorded fixtures against the BFF's OpenAPI/GraphQL schema in *both* CIs, and version the fixtures with the API ([`../../backend-for-mobile/api-design-for-mobile.md`](../../backend-for-mobile/api-design-for-mobile.md), [`../../mobile-system-design/versioning-and-backward-compatibility.md`](../../mobile-system-design/versioning-and-backward-compatibility.md)).
- What this buys: your E2E tier stops being the only place client/server drift is caught, so it can shrink to true journey validation.

## Metrics That Govern the System

| Metric | Target shape | Why |
|---|---|---|
| PR gate p95 latency | Budgeted (e.g., ≤15 min), alarmed | It's the org's inner-loop tax |
| Blocking-lane flake rate | <0.1%, trending | Trust in red builds |
| Quarantine dwell time | p90 < SLO (14 days) | Quarantine must not be a landfill |
| Time-to-detection by tier | Most regressions caught at JVM tier | Validates down-tier pushing |
| Escaped defects (prod bugs with no failing test) | Reviewed monthly | The only true measure of suite value |

The last one matters most and is measured least: every incident review asks "which tier *should* have caught this, and what's the cheapest test that would have?" — that question, asked consistently, is what evolves the portfolio.

## Failure Modes

- **The gate that grew.** Every incident adds "one more check" to the PR gate; two years later it's 50 minutes and everyone batches commits. *(Fix: the latency budget is constitutional — new checks displace old ones or run post-merge.)*
- **Retry-driven decay.** Auto-retry hides a growing race-condition population until a release week where nothing reproduces and everything fails. *(Fix: retries always emit flake events; quarantine SLO enforced.)*
- **Coverage theater.** A mandated "80% coverage" produces thousands of assertion-free tests that execute code without checking it — cost without information. *(Fix: govern by escaped defects and mutation-testing spot checks, not line coverage.)*
- **The unowned E2E suite.** "QA owns the journeys" means nobody fixes them; they rot, get muted, and the org discovers at incident time that the muted test covered the broken flow. *(Fix: journey tests have feature-team owners; muting requires the same rigor as deleting.)*
- **Emulator monoculture.** Everything green on ATDs; crash spike on one OEM's Android 14 skin the emulator can't reproduce. *(Fix: nightly real-device matrix weighted by your actual user base's device distribution, not by what the lab happens to have.)*

## Staff Engineer Thinking

1.  **Publish the strategy as a table, not a doctrine.** One page: failure class → tier → owner → runs-when. Every "should this be an E2E test?" debate resolves against the table instead of taste.
2.  **Treat CI capacity like production capacity.** Sharding, device fleets, and cache hit rates get the same dashboards and budgeting as server fleets — because they gate every engineer's day.
3.  **Make the fast path the paved path.** If writing a JVM test for a new screen is harder than writing an instrumented one, engineers will do the expensive thing. Invest in fixtures, fakes, and screenshot-test scaffolding until the cheap tier is also the easy tier.
4.  **Audit the suite like you audit dependencies.** Yearly: which tests have never failed meaningfully? Which failure class has no tier? What does a minute of PR gate cost the org in engineer-hours, and what did it catch this quarter?

## Probing Questions

1.  Your PR gate is at 35 minutes and the org wants a new set of instrumented checks added. Walk through your decision framework.
2.  Design the flake-quarantine pipeline: detection signal, threshold, what changes for a quarantined test, and the exit paths.
3.  Why does blanket auto-retry corrode a test system even though it makes builds greener? When is retry defensible?
4.  Where do contract tests against the BFF sit in the pyramid, and what do they let you remove from the E2E tier?
5.  What's your device strategy — what runs on ATD emulators vs real devices, and what data decides the real-device matrix?
6.  Line coverage is 85% and production bugs keep escaping. What do you measure instead, and how do you re-aim the suite?

## Further Reading

- [`unit-testing.md`](unit-testing.md) — the pyramid tiers, coroutine/Flow testing mechanics, contract-vs-mock detail.
- [`ui-testing.md`](ui-testing.md) — Compose/Robolectric/Paparazzi selection, UI-flake policy, semantics.
- [`../../platform-engineering/build-graph-scaling.md`](../../platform-engineering/build-graph-scaling.md) — affected-module selection and build caching.
- [`../../platform-engineering/internal-developer-platforms.md`](../../platform-engineering/internal-developer-platforms.md) — the platform team that runs this system.
- [`../../principles/determinism.md`](../../principles/determinism.md) — the root cause of every flake.
- [Gradle Managed Devices](https://developer.android.com/studio/test/gradle-managed-devices) — ATD images, snapshots, sharding (verified source for the CI-device claims here).
- [Firebase Test Lab](https://firebase.google.com/docs/test-lab) — real-device matrix testing.
