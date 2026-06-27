# Mobile System Design Framework (Interview Approach)

> A meta-file: how to approach any mobile system design interview using the 12-section structure used throughout this folder. Inspired by [weeeBox/mobile-system-design](https://github.com/weeeBox/mobile-system-design) but tuned for Android-first interviews.

---

## 1. The 45-60 Minute Interview Structure

| Phase | Duration | What you do | What's being assessed |
|---|---|---|---|
| Introductions | 2-5 min | Brief background, set scope | Communication style |
| Requirements | 5-7 min | Functional, non-functional, out-of-scope | Scoping; restraint |
| Clarifying questions | 3-5 min | Ask the interviewer key questions | Curiosity; awareness of unknowns |
| High-level diagram | 8-10 min | One server-side sketch + paragraph | Big-picture understanding |
| Mobile architecture | 10-15 min | Modules, layers, key types | Mobile expertise |
| Deep dive | 15-20 min | One feature with code-level detail | Depth on hard problem |
| Trade-offs + concerns | 5-10 min | Tables, key tensions | Tradeoff awareness |
| Wrap | 2-5 min | Out-of-scope defended, follow-ups suggested | Self-awareness; signaling |

**Rule of thumb:** if you're 25 minutes in and haven't started coding/deep-diving, you're over-scoping.

---

## 2. The 12-Section Template

This is the structure every file in this folder follows. Use it as your interview playbook:

1. **Gathering Requirements**
2. **Clarifying Questions**
3. **High-Level Diagram** (one ASCII or sketch + one paragraph naming services)
4. **API Contract** (endpoints, JSON shape, idempotency mechanism)
5. **Mobile App Architecture** (module structure + layered diagram + class signatures)
6. **Local Storage** (one entity shown; rest summarised)
7. **Deep Dive: ONE Feature** (code only for the interesting parts)
8. **Trade-offs** (comparison tables, not paragraphs)
9. **Major Concerns** (bullets with one-sentence rationale)
10. **Follow-up Questions** (anticipate what the interviewer asks next)
11. **Out of Scope (defended)** (what you cut and why)
12. **Further Reading** (3-5 links)

---

## 3. Section-by-Section Playbook

### 1. Gathering Requirements

> "Before I draw anything, let me agree on scope so I don't drift into a 3-hour answer."

- **3-5 functional requirements** — the core happy-path features.
- **3-4 non-functional requirements** — see `non-functional-requirements.md` for the menu.
- **Explicit "out of scope"** — list 4-6 things you're cutting and why.

Tone: confident scoping, not feature dumping. If the interviewer wants more, they'll pull it back in.

### 2. Clarifying Questions

> "A few questions before I commit to an architecture."

Pick the 3-5 most architecturally-load-bearing questions:

- **Scale** (DAU, peak, geography) → drives transport choice, cache sizing.
- **Real-time vs eventual** → drives WS vs polling.
- **Offline expectations** → drives Room SSOT decisions.
- **API floor** → drives WorkManager features.
- **Cross-platform** → drives wire format / shared definitions.

End by stating assumptions: "I'll assume X, Y, Z."

### 3. High-Level Diagram

**ONE** ASCII or whiteboard diagram. Name the server-side components in a paragraph. Don't design the server.

```
            ┌────────────────┐
            │  Android Client│
            │   (this talk)  │
            └────────┬───────┘
                     │ WSS / HTTPS
                     ▼
       ┌──────────────────────────┐
       │       BFF / Gateway      │
       └──┬──────────┬──────┬─────┘
          │          │      │
       services... (black box)
```

### 4. API Contract

JSON example payloads. Endpoint table. Idempotency mechanism. The "contract between us and the server."

```json
POST /v1/<resource>
Idempotency-Key: ...
{ ... }
```

### 5. Mobile App Architecture

- Module tree (multi-module Gradle).
- Layered diagram (UI → ViewModel → Repository → Data).
- Key interface signatures (not implementations).

```kotlin
interface Repository {
    fun observeFoo(): Flow<Foo>
    suspend fun doBar(...)
}
```

### 6. Local Storage

ONE entity shown in full. Mention the rest exist. SQLCipher / EncryptedSharedPrefs if data is sensitive.

### 7. Deep Dive: ONE Feature

**Pick the most representative feature.** Cover with code snippets only for the interesting parts (state machine, lifecycle, idempotency). Use:

- Sequence diagrams or numbered steps.
- 1-2 Kotlin snippets focused on the trick.
- A failure-mode table.

The deep dive is what differentiates senior from junior — depth on one thing > shallow on many.

### 8. Trade-offs

Tables. Not paragraphs.

| Option | Pros | Cons | Verdict |
|---|---|---|---|

The "Verdict" column shows you can decide.

### 9. Major Concerns

Bullets with 1-2 sentence rationale each. Pick 6-10 mobile-specific concerns: battery, process death, OEM kill, Doze, memory, schema migration, etc.

### 10. Follow-up Questions

Anticipate what the interviewer would push on. Format:

> **Q: How does X handle Y?**
> [1-paragraph answer]

This shows you've thought one layer deeper.

### 11. Out of Scope (defended)

For each cut item, one-line justification:

- **Group chats** — fan-out, per-member receipts; ~1 hour on its own.
- **E2EE protocol math** — integrate `libsignal-client` SDK as a black box.

### 12. Further Reading

3-5 links. Mix of official Android docs, open-source samples, and one industry blog post.

---

## 4. Common Mistakes (and how to avoid them)

| Mistake | Symptom | Fix |
|---|---|---|
| Over-scoping | "I'd build X, Y, Z, also AR mode, also..." | Practice cutting scope; explicit out-of-scope list |
| Designing the backend | Long Kafka/Cassandra explanations | Backend = black box; one HLD + paragraph |
| Show-off code | Full Kotlin classes everywhere | Class signatures + 1-2 snippets for the trick only |
| Forgetting NFRs | Only happy-path | Use the NFR checklist (`non-functional-requirements.md`) |
| Skipping trade-offs | "We'll use Room" | Comparison tables: "Why Room over X, Y" |
| No deep dive | Shallow on everything | Pick one feature and go deep; signal you have more |
| No process death story | Forgets `SavedStateHandle`, durable queues | Add to every interview answer |
| No OEM-kill mention | Forgets Xiaomi/OPPO | Mention in major concerns |
| No testing story | Skips `JankStats`, `Macrobenchmark` | Show observability + CI gates |
| Defensive about cuts | "I can't do that in 45 min" | Confident scoping: "Out of scope here because..." |

---

## 5. Signals You're Doing Well

- You **state assumptions** before drawing.
- You **separate** functional from non-functional.
- You **mention process death** without prompting.
- You **draw one diagram**, not five.
- You **defer** to libraries (`Coil 3`, `Media3`, `libsignal SDK`).
- You **trade off explicitly** ("Cursor pagination over offset because...").
- You **anticipate follow-ups** ("If you ask about X, my answer is Y").
- You **defend cuts** ("Group chats are out of scope because...").
- You're **comfortable saying "I don't know"** for genuinely unknown things.

---

## 6. Sample Opening

> "Let me start by agreeing on scope. The product is X — I'll focus on the Y feature, scoping out Z because it's a separate hour-long design. For non-functional: I'll prioritise offline tolerance, process-death resilience, and battery, because those are usually where mobile designs fail. I'll plan to draw a single HLD, then go deeper on the mobile architecture, then deep-dive the send/receive (or equivalent) flow because that's where most of the interesting decisions live. Sound good? Let me ask a few clarifying questions first."

This sets:
- Scope discipline
- NFR awareness
- Plan for the next 45 minutes
- Invitation for collaboration

---

## 7. What to Default To (the libraries you'll mention)

| Concern | Default library |
|---|---|
| UI | Jetpack Compose |
| Compose state | `collectAsStateWithLifecycle` |
| Navigation | Compose Navigation |
| DI | Hilt |
| Network | OkHttp + Retrofit (or Ktor 3 if KMP) |
| WebSocket | OkHttp WebSocket |
| Persistence | Room 2.7+ |
| Encrypted persistence | EncryptedSharedPrefs or DataStore + Tink |
| DB encryption | SQLCipher |
| Image loading | Coil 3 |
| Video | Media3 (ExoPlayer) |
| Background work | WorkManager 2.10+ |
| Pagination | Paging 3 + RemoteMediator |
| Location | FusedLocationProvider |
| Push | FirebaseMessaging |
| JSON | kotlinx.serialization |
| Concurrency | Coroutines + Flow |
| Logging | Timber or stdlib |
| Crash | Crashlytics or Sentry |
| Perf | `JankStats`, `Macrobenchmark`, Baseline Profile |
| E2EE | libsignal SDK (as a black box) |
| Maps | Google Maps SDK / Mapbox |
| Auth | AppAuth (OAuth + PKCE) |

State these confidently; if the interviewer pushes, defend the choice with tradeoffs.

---

## 8. Practice Recommendations

1. **Pick one file in this folder per week.** Read it. Talk through it out loud as if you're in the interview.
2. **Whiteboard the HLD from memory.** If you can't draw it without referring to the file, you don't know it yet.
3. **Time yourself.** 45 minutes per file end-to-end. Slow down if you're rushing; speed up if you're padding.
4. **Pair with someone.** Have them probe with the "Follow-up Questions" section.
5. **Reverse the deep dive.** What if the interviewer picks a different feature to deep-dive? Practice 2-3 deep dives per problem.

---

## 9. Further Reading

- [weeeBox/mobile-system-design](https://github.com/weeeBox/mobile-system-design) — the reference framework this folder is modeled on.
- [Common interview mistakes](https://github.com/weeeBox/mobile-system-design/blob/master/common-interview-mistakes.md) — anti-patterns to avoid.
- [Now in Android sample](https://github.com/android/nowinandroid) — production-grade Android architecture.
- [Android Developers — Architecture guide](https://developer.android.com/topic/architecture) — official UI/Domain/Data layering.
- [System Design Interview — Vol 2](https://www.amazon.com/System-Design-Interview-Insiders-Guide/dp/1736049119) — Alex Xu (server-side; useful for the HLD muscle).

---

> **In short:** the framework is requirements → questions → HLD → API → mobile architecture → storage → ONE deep dive → tradeoffs → concerns → follow-ups → out-of-scope → further reading. Pace yourself, scope aggressively, go deep on one thing, signal you have more.
