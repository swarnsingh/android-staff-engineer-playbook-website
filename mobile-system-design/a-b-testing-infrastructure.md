# A/B Testing Infrastructure

> A 45-60 minute mobile system-design walkthrough for the *mobile client side* of an A/B testing system: variant assignment, exposure logging, metric capture, statistical pitfalls to avoid on mobile. Built on top of flags (`feature-flags-and-remote-config.md`); a richer platform is the next file (`experimentation-platform.md`).

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design A/B testing infrastructure for an Android app."
> **Candidate:** "The interesting client problems are: consistent variant assignment per user, exposure logging that powers the analysis, and capturing the right metrics with the right context. I'll deep-dive assignment + exposure."

### Functional Requirements
- **Assign each user to a variant** (control, A, B...) for each experiment.
- **Stable assignment** — same user, same variant, across sessions.
- **Lazy exposure logging** — fire when the user actually sees the variant.
- **Metric tagging** — link analytics events to experiments.
- **Holdouts** — opt-out a slice of users from all experiments.

### Non-Functional Requirements
- **Consistent across devices** for the same user.
- **No PII leakage** in assignment or exposure.
- **Doesn't slow startup**.
- **Survives offline** — defaults to control if unknown.
- **Auditable** — exposure events form the truth for analysis.

### Out of Scope
- Statistical analysis (server / dashboard team)
- Multi-armed bandits (see `experimentation-platform.md`)
- Server-side experiment definition UI
- Interleaving / ranking experiments (specialist)
- Power calculation tools

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Server-evaluated or client-evaluated? | Network round-trip vs cold-start latency |
| Sticky bucketing scope (user, device, session)? | Assignment policy |
| Hold-out group needed? | Always-control slice |
| Concurrent experiments per user? | Layer / namespace design |
| Sample-ratio mismatch (SRM) detection? | Analysis side, but client must log accurately |
| Cross-platform parity? | Same user on iOS sees same variant |
| Min sample size considerations? | Affects rollout speed but not architecture |

> **Candidate:** "Server-evaluated primary, sticky by user id, 5% holdout, layered experiments, cross-platform parity, no SRM detection client-side (server does it)."

---

## 3. High-Level Diagram (~10 min)

```
   Client: Flags fetch  ──► /v1/flags
                                │
                                ▼
                  Server: evaluate variant for each experiment
                                │
                                ▼
                  /v1/flags response includes variant per experiment
                                │
                                ▼
            Client: variant cached in FlagSet
                                │
                                ▼
            Caller: Experiment.variant("ab_checkout_color")
                                │
                                ▼
            ExposureSink.log(experiment, variant)  ← only once per session
                                │
                                ▼
            Analytics events tagged with active experiments

   Server consumer: exposure events + downstream metrics → analysis
```

**Components:**
- **`ExperimentRegistry`** — typed accessors per experiment.
- **`ExposureSink`** — debounced per-session logger.
- **`MetricTagger`** — adds active experiments to every analytics event.
- **`Holdout`** — kicks a deterministic slice out of all experiments.

---

## 4. API Contract

### Flag response (variant-aware)

```json
GET /v1/flags?...
{
  "flags": {
    "ab_checkout_color": { "type": "variant", "value": "B",
                            "experimentId": "exp_checkout_color_v3",
                            "isInExperiment": true }
  }
}
```

### Exposure event (sent through analytics SDK)

```json
{
  "event": "experiment_exposure",
  "experimentId": "exp_checkout_color_v3",
  "variant": "B",
  "isInExperiment": true,
  "ts": ...
}
```

### Other analytics events (auto-tagged with active variants)

```json
{
  "event": "purchase_completed",
  "props": { "amount": 4999 },
  "experiments": {
    "exp_checkout_color_v3": "B",
    "exp_button_size_v2": "control"
  }
}
```

---

## 5. Mobile App Architecture

### Module structure

```
:lib:experiments
    experiments-api     ← Experiment, Variant, typed accessors
    experiments-core    ← ExposureSink, MetricTagger, Holdout
:lib:flags              ← (dependency)
:lib:analytics          ← (dependency, for event piping)
```

### Layered diagram

```
   FlagSet (from flags lib)
        │
        ▼
   ExperimentRegistry
        │
        ▼
   Caller: Experiments.checkoutColor.variant
        │
        ▼
   ExposureSink (lazy, once per (experiment, session))
        │
        ▼
   Analytics emits experiment_exposure event
        │
        ▼
   MetricTagger attaches active variants to every other event
```

### Key class signatures

```kotlin
class Experiment<T : Variant>(
    val id: String,
    val flagKey: String,
    val default: T,
    private val variants: List<T>,
) {
    val variant: T               // returns active variant; logs exposure
    val isInExperiment: Boolean  // false if user is in holdout
}

object Experiments {
    val checkoutColor = variantExperiment(
        id = "exp_checkout_color_v3",
        flagKey = "ab_checkout_color",
        default = CheckoutColor.Control,
        values = CheckoutColor.entries
    )
}

class ExposureSink {
    fun log(experimentId: String, variant: String, isInExperiment: Boolean)
}
```

---

## 6. Local Storage

Already covered by `feature-flags-and-remote-config.md`'s DataStore snapshot. Experiments don't need their own store; they read through the FlagSet.

For exposure deduplication within a session:

```kotlin
class SessionExposureCache {
    private val emitted = ConcurrentHashMap.newKeySet<String>()    // "experimentId|sessionId"
    fun shouldEmit(experimentId: String, sessionId: String): Boolean =
        emitted.add("$experimentId|$sessionId")
}
```

In-memory only — sessions are short-lived.

---

## 7. Deep Dive: Assignment + Exposure (~15 min)

> *I'd pick this as the deep dive because correct assignment + correct exposure is what makes the experiment trustworthy. Get either wrong and the analysis is garbage even if the math is fine.*

### Assignment

Assignment happens server-side (in `/v1/flags` response). The client just consumes the variant. For client-side fallback (server omitted the variant for any reason), sticky bucketing:

```kotlin
fun fallbackBucket(experimentId: String, userId: String, variants: List<String>): String {
    val hash = Hashing.sha256().hashString("$experimentId|$userId", Charsets.UTF_8).asLong()
    val bucket = ((hash % variants.size) + variants.size) % variants.size
    return variants[bucket.toInt()]
}
```

Same `(experimentId, userId)` always lands on the same bucket. Different experiments use the same user but different keys, so users in B for one experiment aren't biased to B for another.

### Holdout

A "holdout" experiment that excludes a deterministic slice (e.g., 5%) from all experiments. Implementation:

```kotlin
class Holdout @Inject constructor(private val userId: () -> String) {
    private val holdoutBucket = lazy {
        Hashing.sha256().hashString("holdout|${userId()}", Charsets.UTF_8).asLong().mod(100)
    }

    fun isInHoldout(): Boolean = holdoutBucket.value < HOLDOUT_PERCENT  // e.g., 5
}
```

For users in the holdout, `Experiment.variant` always returns `default`. They're never logged as in any experiment. The holdout exists so the team has a control group for long-term feature stacking effects.

### Exposure logging

```kotlin
class ExperimentImpl<T : Variant>(...) {
    val variant: T
        get() {
            val raw = flags.value.variantFor(flagKey)
            val isInHoldout = holdout.isInHoldout()
            val resolved = if (isInHoldout) default else (raw?.let(::pickVariant) ?: default)
            exposureSink.log(id, resolved.name, !isInHoldout)
            return resolved
        }
}

class ExposureSink @Inject constructor(
    private val sessionId: () -> String,
    private val analytics: AnalyticsClient,
    private val cache: SessionExposureCache,
) {
    fun log(experimentId: String, variant: String, isInExperiment: Boolean) {
        if (!cache.shouldEmit(experimentId, sessionId())) return
        analytics.track(AnalyticsEvent(
            name = "experiment_exposure",
            properties = mapOf(
                "experimentId" to experimentId,
                "variant" to variant,
                "isInExperiment" to isInExperiment
            ),
            category = Category.DIAGNOSTIC
        ))
    }
}
```

> **Why lazy?** If the user never sees the variant (e.g., the experiment is on a screen they never visit), they shouldn't count as exposed. Analysis only includes users who were exposed.

### Metric tagging

Every analytics event automatically includes active variants the user has been exposed to:

```kotlin
class ExperimentMetricInterceptor @Inject constructor(
    private val activeExperiments: () -> Map<String, String>
) : EventInterceptor {
    override suspend fun intercept(event: AnalyticsEvent, ctx: EventContext): AnalyticsEvent {
        return event.copy(
            properties = event.properties + mapOf("experiments" to activeExperiments())
        )
    }
}
```

`activeExperiments()` returns `Map<experimentId, variant>` for all experiments the user has been exposed to in the current session.

> **Note:** only experiments the user has *been exposed to* are tagged — not all defined experiments. This avoids polluting events with variants the user never saw.

### Layered experiments

To run many concurrent experiments without interaction effects, group them into "layers". Within a layer, each user gets one experiment (mutually exclusive). Across layers, experiments are independent.

```kotlin
class Layer(val id: String, val experiments: List<Experiment<*>>) {
    fun assign(userId: String): Experiment<*> {
        val bucket = Hashing.sha256().hashString("layer|$id|$userId", Charsets.UTF_8).asLong()
            .mod(experiments.size.toLong()).toInt()
        return experiments[bucket]
    }
}
```

### Failure modes

| What breaks | Behavior |
|---|---|
| Server didn't include variant | Sticky bucketing fallback |
| User in holdout | Always control; no exposure |
| `userId` not yet known (pre-login) | Use `anonId` for bucketing; re-evaluate after login |
| Two experiments contradict | Layer them; document the interaction |
| Exposure not fired | User excluded from analysis (correct behaviour) |
| Variant changes between sessions | Don't allow — sticky bucketing prevents |

---

## 8. Trade-offs

### Assignment site

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Server-evaluated** | Central, consistent, can adapt | Network round-trip | Pick this |
| **Client-evaluated** | Offline-safe | Drift between platforms, harder to update | Fallback only |
| **Hybrid (server primary, client fallback)** | Best of both | More code paths | Default |

### Bucketing key

| Option | Verdict |
|---|---|
| **User id (sticky cross-device)** | Pick — cross-platform parity |
| Device id | Bad — users switch devices |
| Anon id (pre-login) | Pick for unauthenticated state; migrate on login |
| Session id | Bad — flips every session |

### Exposure model

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Lazy** (log on read) | Accurate "was exposed" set | Risk of missing exposures if accessed via reflection | Pick this |
| Eager (log on fetch) | Simpler | Counts users who never saw it | Skip |
| Manual | Caller-driven | Easy to forget | Skip |

### Concurrent experiments

| Option | Verdict |
|---|---|
| **Layered (one experiment per layer)** | Pick — no interaction effects |
| Unlayered (independent buckets) | OK if experiments don't interact |
| Single-experiment-at-a-time | Slow rollout |

### Holdout

| Option | Verdict |
|---|---|
| **5% holdout per layer / global** | Pick — measures aggregate effect of experimentation |
| No holdout | Loses ability to measure cumulative drift |
| 50% holdout | Slows experimentation; sample-size-limited |

---

## 9. Major Concerns

- **Don't break stickiness.** Same user → same variant. If you change the assignment algorithm, you re-randomize everyone and old experiments become invalid.
- **Lazy exposure.** Only log when read. Eager logging inflates exposure counts with users who never saw the variant.
- **Default = control.** When the network fails or the flag is missing, return control. Never return a treatment by accident.
- **Privacy.** No PII in `experimentId` or variant names. They show up in logs and dashboards.
- **Cross-platform parity.** iOS, Android, web should agree for the same user. Server-side evaluation enforces this.
- **Sample ratio mismatch.** If the client-side filter excludes a different share per arm (e.g., feature only triggers on Android), SRM check on the server flags it. The client must log honestly.
- **Holdout management.** Document who's in the holdout. Don't auto-exclude critical paths (like login).
- **Long-tail experiments.** Decide on a sunset policy. Old experiments stuck in "control vs B" forever pollute every event.
- **Session correctness.** Use `ProcessLifecycleOwner` for session boundaries (not Activity callbacks).

---

## 10. Follow-up Questions

> **Q: How do you handle a user who upgrades the app mid-experiment?**
> Sticky bucketing is by user id, not version. If the new version adds a new variant, the user's `(experimentId, userId)` hash deterministically places them. Old version users with old buckets aren't reshuffled.

> **Q: An experiment is wrong and shipping bad behavior — how to kill it?**
> Two options: (1) update the flag definition to force "control" for everyone (live-apply policy); (2) end the experiment in the dashboard and let server return control. Option 1 propagates faster.

> **Q: How do you avoid "experiment fatigue" in analytics?**
> Auto-tagging adds only *active* experiments to events (those the user was exposed to). Experiments cleaned up after launch removed from active set automatically.

> **Q: How do you debug "why am I in variant B"?**
> Debug overlay shows: `userId`, all active experiments + variants, holdout status, source (server / fallback / default). Optionally a developer override.

> **Q: How is the assignment algorithm tested?**
> Property-based tests: same `(experimentId, userId)` → same variant 100% of the time. Different `userId`s → balanced distribution (chi-squared at 5%).

> **Q: How do you measure exposure events themselves are trustworthy?**
> Server logs flag fetches AND exposure events. If exposure count >> flag fetch count, something is wrong. SRM detection compares variant counts to expected split.

---

## 11. Out of Scope (defended)

- **Statistical analysis** — server / data team.
- **Multi-armed bandits** — see `experimentation-platform.md`.
- **Server admin UI** — non-mobile.
- **Power calculation** — separate tooling.
- **Reverse experiments / sequential analysis** — analysis-side methodology.

---

## 12. Further Reading

- [GrowthBook documentation](https://docs.growthbook.io/) — open-source experimentation implementation reference.
- [Statsig documentation](https://docs.statsig.com/welcome) — current experimentation and feature-gating entry point.
- [Microsoft — Trustworthy Online Controlled Experiments](https://exp-platform.com/) — research papers.
- [Spotify — feature flags layered experiments](https://engineering.atspotify.com/) — blog on layering at scale.
- [Airbnb — Experimentation platform principles](https://medium.com/airbnb-engineering/) — practitioner perspective.

---

> **Closing in the interview:** "I anchored on assignment + exposure because that's the contract with the analyst. Happy to dig into layered experiments, sample-ratio detection, or how holdouts interact with launches next."
