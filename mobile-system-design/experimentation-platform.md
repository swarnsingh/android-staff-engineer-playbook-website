# Experimentation Platform (Beyond A/B)

> A 45-60 minute mobile system-design walkthrough for an experimentation platform that goes beyond fixed A/B (multi-armed bandits, interleaving, sequential testing) — from the mobile client's perspective. Built on top of `feature-flags-and-remote-config.md` and `a-b-testing-infrastructure.md`.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design an experimentation platform — go beyond fixed A/B."
> **Candidate:** "Multi-armed bandits (MAB) shift traffic to better-performing variants in real time. Interleaving is for ranking experiments. Sequential testing changes how we decide to stop. From the mobile client side, MAB is the interesting integration. I'll deep-dive the MAB client."

### Functional Requirements
- **Fixed A/B** support (the previous file).
- **Multi-armed bandits**: server adapts traffic by performance.
- **Reward reporting**: client signals success per arm.
- **Sticky assignment within the user-session** even as bandits shift.
- **Eligibility filters** (only ship a variant to users who qualify).

### Non-Functional Requirements
- **Fast assignment** — no extra network hop.
- **Reward must be attributable** to the exposed arm.
- **Privacy-aware** — reward signals scrub PII.
- **Auditable** — every assignment + reward traceable.
- **Resilient** — falls back to fixed A/B if bandit service is down.

### Out of Scope
- Bandit algorithm internals (Thompson sampling, UCB, ε-greedy) — server's domain
- Interleaving experiments (for search/feed ranking, specialist)
- Sequential analysis statistics (server)
- Causal inference / observational studies
- Marketing campaign optimization

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Bandit algorithm policies (single per experiment)? | API shape |
| Reward latency (immediate vs delayed)? | Buffer + late-attribution |
| Sample budget per arm? | Convergence rate |
| Cross-platform parity? | Server-side assignment |
| Default if bandit service down? | Fall back to control or last-known winner |
| Reward signals (click, conversion, retention)? | Capture latency |
| Bandit rebalance cadence? | Sticky session enforcement |

> **Candidate:** "Per-experiment Thompson sampling, conversion rewards within 30 min of exposure, server-side assignment, fall back to fixed A/B on bandit failure, cross-platform consistent."

---

## 3. High-Level Diagram (~10 min)

```
   Client requests flags ──► /v1/flags
                                  │
                                  ▼
                  Server: for experiment X, ask BanditService
                                  │
                                  ▼
                  Bandit returns variant (probabilistic, per current posterior)
                                  │
                                  ▼
                  /v1/flags response: variant + assignmentId
                                  │
                                  ▼
   Client: variant cached + exposure logged
                                  │
                                  ▼
   User performs reward action → /v1/experiments/reward
                                  │
                                  ▼
                          BanditService updates posterior
                                  │
                                  ▼
                  Next assignment for similar users adjusts
```

**Components:**
- **`BanditClient`** — talks to flag service + reward endpoint.
- **`AssignmentTracker`** — pairs (assignmentId, exposureSession) for reward attribution.
- **`RewardSink`** — buffers reward events; sends through analytics path.
- **Server-side Bandit Service** — black box; runs the algorithm.

---

## 4. API Contract

### Flag response (bandit-aware)

```json
{
  "flags": {
    "onboarding_variant": {
      "type": "variant",
      "value": "C",
      "experimentId": "exp_onboarding_v7",
      "assignmentId": "asg_8f7a",       // unique to this assignment
      "policy": "bandit_thompson"
    }
  }
}
```

### Reward report

```http
POST /v1/experiments/reward
{
  "assignmentId": "asg_8f7a",
  "experimentId": "exp_onboarding_v7",
  "rewardType": "onboarding_completed",
  "rewardValue": 1.0,
  "ts": ...
}
```

### Fallback flag (if bandit service down)

```json
{
  "flags": {
    "onboarding_variant": { "type": "variant", "value": "control",
                            "experimentId": "exp_onboarding_v7",
                            "policy": "fallback_control" }
  }
}
```

---

## 5. Mobile App Architecture

### Module structure

```
:lib:experiments               ← (from a-b-testing-infrastructure)
:lib:bandits
    bandits-api                ← reward typed accessors
    bandits-core               ← AssignmentTracker, RewardSink
```

### Layered diagram

```
   FlagSet has assignmentId per bandit experiment
        │
        ▼
   Caller: Experiments.onboarding.variant
        │
        ▼
   AssignmentTracker.record(experimentId, assignmentId, sessionId)
        │
        ▼
   Caller (later): Experiments.onboarding.recordReward(type, value)
        │
        ▼
   RewardSink.enqueue(reward)
        │
        ▼
   Analytics path → POST /v1/experiments/reward
```

### Key class signatures

```kotlin
class BanditExperiment<T : Variant>(
    id: String,
    flagKey: String,
    default: T,
    variants: List<T>,
) : Experiment<T>(...) {
    fun recordReward(type: String, value: Double = 1.0)
}

class AssignmentTracker {
    fun record(experimentId: String, assignmentId: String, sessionId: String)
    fun assignmentFor(experimentId: String): AssignmentSnapshot?
}

data class AssignmentSnapshot(
    val experimentId: String, val assignmentId: String,
    val sessionId: String, val ts: Long
)
```

---

## 6. Local Storage

```kotlin
@Entity(tableName = "bandit_assignments")
data class AssignmentEntity(
    @PrimaryKey val key: String,           // "$experimentId|$sessionId"
    val experimentId: String, val assignmentId: String,
    val sessionId: String, val ts: Long
)

@Entity(tableName = "bandit_rewards")
data class RewardEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val assignmentId: String, val experimentId: String,
    val rewardType: String, val rewardValue: Double, val ts: Long
)
```

Assignments are kept for reward window (e.g., 24h). Rewards are buffered like analytics events and flushed via the same worker.

---

## 7. Deep Dive: Bandit Client (~15 min)

> *I'd pick this as the deep dive because the MAB client looks like A/B but the reward attribution is where everything gets subtle: which arm gets credit, when, and how to avoid leaking signal from delayed conversions.*

### Assignment

Server returns the variant + `assignmentId` per fetch. The `assignmentId` is unique per assignment instance (not stable across sessions like A/B). This is important: a bandit may give a user variant `A` today and variant `B` next month as the algorithm explores.

> **Trade-off:** within a session, we still want stickiness (the user shouldn't see the home screen in variant `A` and the checkout screen in variant `B`). The client enforces stickiness at session boundary.

### Sticky-within-session policy

```kotlin
class BanditExperimentImpl<T : Variant>(...) : BanditExperiment<T>(...) {

    private val sessionAssignments = ConcurrentHashMap<String, AssignmentSnapshot>()

    override val variant: T
        get() {
            val sessionId = currentSessionId()
            // Use the assignment recorded at session start
            val existing = sessionAssignments[sessionId]
            if (existing != null) return resolveVariant(existing.assignmentId)
            // First read this session: snapshot current server assignment
            val raw = flags.value.variantFor(flagKey)
            val snap = AssignmentSnapshot(
                experimentId = id,
                assignmentId = raw?.assignmentId ?: "fallback",
                sessionId = sessionId,
                ts = clock.now()
            )
            sessionAssignments[sessionId] = snap
            assignmentTracker.record(id, snap.assignmentId, sessionId)
            exposureSink.log(id, raw?.value?.toString() ?: default.name, isInExperiment = raw != null)
            return raw?.let { pickVariant(it) } ?: default
        }
}
```

> The first read locks the assignment for the session. Subsequent reads within the session return the same variant, even if the server rebalances mid-session.

### Reward reporting

```kotlin
override fun recordReward(type: String, value: Double) {
    val sessionId = currentSessionId()
    val snap = sessionAssignments[sessionId]
        ?: assignmentTracker.assignmentFor(id)                // late attribution (within window)
        ?: return                                              // user wasn't in this experiment

    rewardSink.enqueue(RewardEntity(
        assignmentId = snap.assignmentId,
        experimentId = id,
        rewardType = type, rewardValue = value,
        ts = clock.now()
    ))
}
```

### Reward attribution window

A user is exposed to variant `C` at 10:00. They convert at 10:32. The reward should attribute to the 10:00 assignment, not whatever variant they'd be in at 10:32.

```kotlin
class AssignmentTracker @Inject constructor(private val dao: AssignmentDao) {
    fun assignmentFor(experimentId: String): AssignmentSnapshot? = runBlocking {
        val recent = dao.recentFor(experimentId, since = clock.now() - REWARD_WINDOW_MS)
        recent?.toSnapshot()
    }
}
```

`REWARD_WINDOW_MS` = 24h typically. Older than that and we conservatively drop the reward signal.

### Reward sink (durable, batched)

```kotlin
class RewardSink @Inject constructor(
    private val rewardDao: RewardDao,
    private val workManager: WorkManager,
) {
    suspend fun enqueue(reward: RewardEntity) {
        rewardDao.insert(reward)
        workManager.enqueueUniqueWork("reward-flush", KEEP, rewardFlushWork())
    }
}

@HiltWorker
class RewardFlushWorker @AssistedInject constructor(...) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val batch = rewardDao.take(100)
        return runCatching { api.reportRewards(batch.toWire()) }
            .fold(
                onSuccess = { rewardDao.delete(batch.map { it.id }); Result.success() },
                onFailure = { Result.retry() }
            )
    }
}
```

### Eligibility filtering

Some variants are only valid for some users (e.g., a premium-only feature variant). The flag service applies the filter server-side and either omits the variant or returns control.

Client-side post-filter (rare, for late-known eligibility):

```kotlin
val variant: T
    get() {
        val candidate = super.variant
        return if (!eligibility.check(candidate)) {
            sessionAssignments.remove(currentSessionId())
            default
        } else candidate
    }
```

### Failure modes

| What breaks | Behavior |
|---|---|
| Bandit service down | Server returns control with `policy: fallback_control` |
| Reward sent for unknown `assignmentId` | Server-side dedup/drop |
| User exposed, never converts | No reward — bandit interprets as no signal (or as a 0 reward depending on contract) |
| Late conversion (> window) | Drop client-side; report a `late_conversion` diagnostic |
| User in holdout | Skip bandit entirely; default arm; no reward attribution |
| Session boundary mid-flow | Don't re-assign mid-flow; sticky-within-session preserves |

---

## 8. Trade-offs

### Bandit assignment

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Server-side per request** | Algorithm-driven, central | Network round-trip on each fetch | Pick this |
| Server pre-computed cohort | No real-time adaptation | Stale | Skip for MAB |
| Client-side bandit | Latency-friendly | Diverges from server, hard to debug | Skip |

### Sticky-within-session

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Session-locked assignment** | Coherent UX | Slower convergence | Pick this |
| Per-screen assignment | Faster convergence | Confusing UX, often invalid | Skip |
| Sticky across sessions | Closer to A/B; loses adaptivity | Defeats bandits | Use only for slow-changing arms |

### Reward latency

| Option | Verdict |
|---|---|
| **Immediate reward** (within session) | Easiest; preferred when possible |
| **Delayed reward** (within 24h) | Pick — keep `AssignmentTracker` for window |
| Multi-day rewards | Server-side join; not client's problem |

### Reward signal

| Option | Verdict |
|---|---|
| **Boolean conversion** | Pick when simple (clicked / didn't) |
| Scalar value (revenue) | Pick when value matters |
| Latency-based | Possible; tricky to interpret |
| Implicit (dwell time) | Useful but noisy |

### Fallback

| Option | Verdict |
|---|---|
| **Control variant on bandit failure** | Pick — safest |
| Last-known winner | OK if known and acceptable to ship |
| Crash | Don't |

---

## 9. Major Concerns

- **Session stickiness.** A user must not see arm A on screen 1 and arm B on screen 2. Lock on first read.
- **Reward leakage.** A reward fired after user switched arms (e.g., due to logout/login) must not attribute incorrectly. Use `assignmentId` as the key.
- **Privacy.** Reward types shouldn't reveal PII. Use category labels (e.g., `purchase_completed`, not `purchased_xyz_product`).
- **Late conversions.** Set a window (24h-7d) past which rewards are dropped. Otherwise opportunistic conversions reward whichever arm is current.
- **Bandit convergence.** Need a minimum sample per arm before traffic shifts heavily. Server enforces; client just consumes.
- **Cross-platform consistency.** Same user on iOS and Android should not be in different arms of the same bandit. Server keys by user id, not device.
- **Holdout interaction.** Bandits live within the layered experimentation system. Holdout users always get control.
- **Debugging.** Without sticky-within-session, debugging is nearly impossible. Engineers can't reproduce.
- **Algorithm leakage.** Don't expose `policy: thompson` to users in dashboards; could be confusing.

---

## 10. Follow-up Questions

> **Q: User opens the app, app fetches flags (variant C), user converts in 5 minutes — what happens?**
> AssignmentTracker had recorded `(experimentId, assignmentId=asg_8f7a, sessionId=s_111)`. The reward event sends `assignmentId=asg_8f7a`. Server credits C's posterior with +1 reward. The next user might be more likely to see C if Thompson sampling boosts it.

> **Q: User opens the app while offline — what variant do they get?**
> The cached flag snapshot from last fetch. If that included a variant for this experiment, they see it (sticky). If not, control. No bandit signal is sent until reconnect.

> **Q: Why not let the client run the bandit algorithm?**
> Cross-platform consistency (the same user across iOS and Android), centralized algorithm changes, and server-side has the global posterior view that no single client can have.

> **Q: How is a 7-day rolling reward window handled?**
> AssignmentTracker keeps assignments in Room for 7 days. Reward events look up by `experimentId`. After 7 days, attempts return null and the reward is dropped (with a diagnostic logged).

> **Q: A reward fires twice (network retry) — how is dedup handled?**
> Each reward has an autogenerated id. Worker drops by id on successful upload. Server also dedups on `(assignmentId, rewardType, ts)` within seconds-level grain.

> **Q: How is this tested?**
> Fake `FlagsRepository` that returns scripted assignments. Fake `RewardSink`. Property test: same `(experimentId, sessionId)` always returns same variant; first read sets it; second read reads from cache.

---

## 11. Out of Scope (defended)

- **Algorithm internals** (Thompson, UCB, ε-greedy) — server-side; vendor or in-house data science.
- **Interleaving** — ranking-specific; specialist.
- **Sequential testing** — analysis methodology.
- **Causal inference** — observational studies, separate problem.
- **Server admin** — non-mobile.

---

## 12. Further Reading

- [Microsoft — Multi-Armed Bandits at scale](https://exp-platform.com/) — research and patterns.
- [Spotify — Recommending music via bandits](https://engineering.atspotify.com/) — practitioner blog.
- [Statsig — bandit experimentation guide](https://docs.statsig.com/) — vendor docs.
- [Vowpal Wabbit — Contextual bandits](https://vowpalwabbit.org/) — open-source algorithm reference.
- [Cassidy Williams — Sequential testing primer](https://posthog.com/blog) — accessible intro.

---

> **Closing in the interview:** "Bandit client was my deep dive because sticky-within-session + reward attribution is where most bugs live. Happy to dig into eligibility filtering, layered bandits, or the late-conversion handling next."
