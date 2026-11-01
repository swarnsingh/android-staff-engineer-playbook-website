# Server-Driven UI (SDUI)

> A platform-design walkthrough for a server-driven UI system: the server decides *what* renders on a screen; the client owns *how* it renders. This is the idea behind Airbnb's Ghost Platform and Lyft's Bikes and Scooters screens — and the standard answer to "how do we ship UI changes without waiting for app releases and Play review?"

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a system where the server controls the app's screens."
> **Candidate:** "Let me scope which *kind* of server-driven we're building — the term covers everything from remote config to shipping a full interpreter."

### Functional Requirements

- **Server-composed screens** — the backend returns an ordered list of typed UI sections with data and actions; the client renders them with native components.
- **Same-day UI changes** — reorder sections, change copy, insert a new banner on existing component types without an app release.
- **New component rollout** — introduce a *new* component type to old app versions safely (they must degrade gracefully, not crash).
- **Interaction handling** — taps, form inputs, and impressions route through server-declared actions (navigate, mutate, open deep link).
- **Per-user/per-market composition** — screens vary by user segment, experiment bucket, and locale.

### Non-Functional Requirements

- **Render latency:** cached screen renders instantly; network-fresh screen p95 < 800ms.
- **Crash safety:** a malformed or unknown payload must *never* crash the app — worst case is a skipped section or a fallback screen.
- **Offline:** last-fetched screen renders offline; actions queue or disable explicitly.
- **Accessibility & theming parity:** server-driven screens meet the same a11y bar as native screens — semantics ship in the schema, not as an afterthought.
- **Observability:** every render, fallback, and unknown-component event is measurable per app version.

### Out of Scope (defended)

- Shipping executable logic (JS/Lua interpreters, Compose-runtime-over-the-wire) — that's a different risk class (app-store policy, security, debugging) and a different design.
- Server-driven *navigation graph* redesign (we handle per-screen composition; full flow orchestration is a follow-up).
- The CMS/authoring tool that product teams use to compose screens (we design the contract it must emit).
- Web rendering (same schema can serve web, but we design the Android client).

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| How dynamic is "dynamic"? Copy/order changes, or new layouts weekly? | Decides schema generality vs simplicity |
| Who authors screens — engineers, PMs via CMS, ML ranking? | Drives validation strictness and preview tooling |
| Min supported app version / update lag? | Old binaries live 1-2+ years; forward compatibility is the core problem |
| One team or many teams contributing components? | Registry governance, naming, review process |
| Is the screen personalized per request? | Cache strategy: shared CDN cache vs per-user payloads |
| Existing design system? | Components map 1:1 to design-system components or SDUI fragments into pixel-level primitives |

> **Candidate:** "I'll assume: a design-system-backed component vocabulary (~30 types), PM-authored composition via a backend tool, apps up to 18 months old in the wild, personalized screens, 10M DAU."

---

## 3. High-Level Diagram (~10 min)

```mermaid
flowchart LR
    subgraph Client[Android client]
        Loader["Screen loader"] --> Cache["Validated payload cache"] --> Renderer["Native component registry / renderer"] --> Actions["Allowlisted action router"]
    end
    subgraph Backend[Backend]
        Compose["Screen composition service"] --> Registry["Versioned schema registry"]
        Data["Data + experimentation + personalization"] --> Compose
    end
    Loader <-->|"versioned HTTPS payload"| Compose
```

The server composes only schemas and actions the installed client advertises; the client validates, renders native components, and safely falls back for unknown types rather than executing arbitrary server code.

**Server-side (named, not designed):** a screen-composition BFF assembles sections from data services, filtered by the requesting app's **supported schema version and component set**; the component registry is the shared contract both sides build against. Airbnb's Ghost Platform does exactly this over a single shared GraphQL schema for web/iOS/Android.

---

## 4. API Contract

### Screen payload

```json
{
  "schemaVersion": 3,
  "screenId": "home",
  "ttlSeconds": 900,
  "cacheKey": "home|us|exp_home_v4:B",    // from the server, so the client needn't know its experiment bucket
  "cacheScope": "user",                   // "user" for personal payloads; "shared" only for non-personal ones
  "sections": [
    {
      "id": "promo-banner-1",
      "type": "Banner",
      "typeVersion": 2,
      "props": {
        "title": "Summer sale",
        "imageUrl": "https://cdn.example.com/x.webp",
        "a11yLabel": "Summer sale. Up to 40 percent off."
      },
      "action": { "type": "deeplink", "uri": "app://sale/summer" },
      "fallback": { "behavior": "skip" },
      "analytics": { "impressionId": "imp_8821" }
    },
    {
      "id": "listing-carousel-1",
      "type": "Carousel",
      "typeVersion": 1,
      "props": { "items": [ { "...": "..." } ] },
      "fallback": {
        "behavior": "replaceWith", "type": "ListSection", "typeVersion": 1,
        "props": { "items": [ { "...": "..." } ] }      // complete and valid for the replacement type
      }
    }
  ]
}
```

### Version negotiation (request)

```http
GET /v1/screens/home
X-SDUI-Schema-Version: 3
X-SDUI-Components: Banner:2,Carousel:1,ListSection:1,Grid:1
```

The client declares what it can render; the server composes only from that set (or attaches fallbacks). This single design decision is what makes 18-month-old binaries safe.

### The contract rules

- **Components are data, not code.** `props` are typed values validated against the registry schema — never templates or expressions to evaluate.
- **Actions are an enum, not a script.** `deeplink | navigate | mutate | dismiss | openSheet` — each handled by native code.
- **An allowed action type doesn't authorize its contents.** The router parses each URI and checks its scheme and full host against an allowlist, and destinations against a registered list. `mutate` names a registered operation with validated arguments. The server still authorizes every mutation, and a queued one carries an idempotency key.
- **Every section carries a fallback policy** (`skip`, `replaceWith`, or `useNativeDefault`). A `replaceWith` carries its own valid props.
- **Payloads are bounded.** Limits on size, section count, nesting depth and fallback-chain length are checked before rendering, so malformed content can't exhaust the client.
- **`a11y` fields are required** in the schema for any component with user-facing text or imagery — validated at authoring time, not left to client guesswork.

---

## 5. Mobile App Architecture

### Module structure

```
:core:sdui:schema        // payload models + parser (tolerant reader)
:core:sdui:renderer      // section list -> Compose, component registry
:core:sdui:actions       // action router (navigation, mutations)
:core:designsystem       // the native components SDUI maps onto
:feature:home            // hosts an SDUI screen with native chrome
```

### Key class signatures

```kotlin
// Registry: the client's declared vocabulary
interface ComponentRegistry {
    fun rendererFor(type: String, typeVersion: Int): SectionRenderer?
    fun supported(): Map<String, Int>          // sent in X-SDUI-Components
}

interface SectionRenderer {
    @Composable fun Render(section: Section, dispatch: (Action) -> Unit)
}

// Tolerant parsing: unknown fields ignored, unknown sections preserved
sealed interface ParsedSection {
    data class Known(val section: Section) : ParsedSection
    data class Unknown(val type: String, val fallback: Fallback?) : ParsedSection
}

class SduiScreenViewModel(
    private val loader: ScreenLoader,          // cache-then-network
    private val registry: ComponentRegistry,
) : ViewModel() { /* exposes StateFlow<SduiScreenState> */ }
```

The renderer maps section types onto **design-system components** — SDUI composes the design system; it does not bypass it. This keeps theming, a11y semantics, and interaction states native and consistent (see [`../platform-engineering/design-systems-architecture.md`](../platform-engineering/design-systems-architecture.md)).

## 6. Local Storage

One table, keyed by owner + screen + the server's cache key:

```sql
CREATE TABLE sdui_screens (
  owner_id TEXT NOT NULL,         -- signed-in account; a fixed value only for "shared" payloads
  screen_id TEXT NOT NULL,
  cache_key TEXT NOT NULL,        -- returned by the server
  payload BLOB NOT NULL,          -- raw JSON, re-parsed on read
  schema_version INTEGER NOT NULL,
  fetched_at INTEGER NOT NULL,
  ttl_seconds INTEGER NOT NULL,
  payload_hash TEXT NOT NULL,
  PRIMARY KEY (owner_id, screen_id, cache_key)
);

CREATE TABLE sdui_render_attempts (     -- one row per render; see the crash quarantine below
  attempt_id TEXT PRIMARY KEY,
  payload_hash TEXT NOT NULL,
  launch_id TEXT NOT NULL,              -- changes every process start
  started_at INTEGER NOT NULL
);
```

A segment key alone would let users in the same segment read each other's personal payload, and a second person signing in offline would see the first person's home screen. So reads filter by `owner_id`, and sign-out deletes that account's rows.

Store the **raw payload**, not parsed models — a client update with a newer parser can re-read old cached payloads, and parse failures fall back exactly like network failures.

## 7. Deep Dive: Versioning & Forward Compatibility (~15 min)

The hard problem: **the server evolves weekly; binaries in the field are frozen for months.**

Four layers of defense:

1. **Tolerant reader.** The parser ignores unknown fields, treats missing optionals as defaults, and turns unknown section types into `ParsedSection.Unknown` instead of throwing. A parse error in one section never poisons the screen.
2. **Capability negotiation.** The client declares `type:typeVersion` pairs; the server never sends a component the binary can't render *without* a fallback the binary can.
3. **Server-declared fallbacks.** For gradual rollout of a new component, the payload carries `replaceWith` fallbacks expressed in old vocabulary. The authoring tool refuses to publish a screen whose fallback chain doesn't bottom out in components supported by the minimum live app version.
4. **Validate before composing.** Parsing isn't enough. A renderer that throws during composition can't be caught by `try`/`catch` around a composable call, and `LazyColumn` requires unique keys, so two sections with the same `id` can break the whole list. An authoring bug like that passes a schema check. So validation runs on the parsed list before any composition: unique IDs (drop later duplicates and count them), required props present, limits respected. The authoring tool runs the same check before publishing.

```kotlin
fun render(parsed: List<ParsedSection>): List<@Composable () -> Unit> =
    validate(parsed).mapNotNull { p ->
        when (p) {
            is ParsedSection.Known ->
                registry.rendererFor(p.section.type, p.section.typeVersion)
                    ?.let { r -> { r.Render(p.section, ::dispatch) } }
                    ?: fallbackOf(p.section.fallback)      // known type, too-new version
            is ParsedSection.Unknown -> fallbackOf(p.fallback)
        }
    }
// fallbackOf: skip -> null; replaceWith -> render substitute; useNativeDefault -> native section
// validate: dedupes IDs and enforces limits; a fallback chain stops at the depth limit
```

**Crash quarantine.** "Never crash" needs a last line of defense, because a cached payload that crashes would crash on every launch. Before composing, a render inserts its own attempt row; after its first frame, it deletes only that row. A shared counter wouldn't work: one screen's success would clear another's pending attempt, and two screens rendering at once could look like crashes.

Only unfinished attempts from an **earlier** `launch_id` count as evidence, since a live attempt in this process hasn't failed. With two or more for a `payload_hash`, skip that payload and load fresh or show the native fallback screen.

Checking doesn't delete that evidence, or a crash loop would never reach the threshold. Launch A crashes and leaves one row. Launch B finds one, retries, crashes and leaves a second. Launch C finds two and shows the fallback, and keeps skipping that hash on later launches because the rows remain. Evidence clears in only two ways: a first frame for that hash succeeds, which removes its rows from earlier launches, or the payload is replaced or evicted, which removes rows for the old hash. A rendering screen's own pending row from this launch is never touched, so two screens can't clear each other. A process killed for other reasons before its first frame also counts, so a rare false quarantine is possible; it costs one fresh load.

This protects the first frame only. A lazy section that crashes when scrolled into view happens after the row is gone, so crash reports carry `screenId`, `payload_hash` and the section `type`, which feed the server's per-screen kill switch.

**Failure-mode table for this cycle:**

| Failure | Behavior | Signal |
|---|---|---|
| Unknown component type | Apply fallback (skip/replace) | `sdui_unknown_component{type, appVersion}` counter |
| Known type, newer `typeVersion` | Same as unknown | same counter, `reason=version` |
| Malformed props (schema mismatch) | Drop section, keep screen | `sdui_parse_error` with section id |
| Duplicate section `id` | Keep the first; drop later ones | `sdui_duplicate_id` |
| Payload over a size, depth or fallback limit | Drop the section, or treat the whole payload as malformed | `sdui_limit_exceeded` |
| Whole payload malformed | Serve cached payload; else native fallback screen | `sdui_screen_fallback` |
| Renderer crashes on a cached payload's first frame | Quarantine it on next launch; load fresh or native fallback | `sdui_payload_quarantined` |
| Lazy section crashes after the first frame | Not quarantined automatically; crash reports identify it, and the server kill switch stops it | crash rate by `payload_hash` |
| Action type unknown | No-op + log (never crash) | `sdui_unknown_action` |
| Action URI or operation not allowlisted | Refuse + log | `sdui_action_rejected` |

The observability requirement is structural: **unknown-component rate per app version** is the metric that tells the authoring side when a fallback chain is wrong — alert on it like a crash rate ([`../observability/metrics.md`](../observability/metrics.md)).

## 8. Trade-offs

| Axis | Native screens | SDUI (this design) | Shipping an interpreter (JS/DSL) |
|---|---|---|---|
| UI iteration speed | App release + rollout | Server deploy | Server deploy |
| New *behavior* | App release | App release (actions are enum) | Server deploy — and that's the problem |
| Crash risk from remote change | None | Low (fallbacks) | High (arbitrary logic) |
| Store policy risk | None | Low — payloads are data | Real: dynamic code raises review/policy questions |
| Debuggability | Full | Medium (payload + version matrix) | Poor (which script version did the user have?) |
| A11y/theming consistency | Native | Native (via design system) | Re-implemented per component |
| Cost | Per-feature | Platform team + registry governance | Platform team + language/runtime team |

The honest framing: SDUI moves iteration speed from "release-bound" to "deploy-bound" **for composition and content** while deliberately keeping *behavior* release-bound. Teams that need behavior-level dynamism are choosing the third column and should price its risks explicitly.

## 9. Major Concerns

- **Testing matrix explosion** — every payload shape × every live app version. Mitigate: contract tests generated from the registry; a "min-supported-version renderer" CI job that renders every published screen with the oldest binary's component set.
- **The registry becomes the bottleneck** — one team gate-keeping component additions recreates the release train socially. Mitigate: paved-road contribution process with schema linting, not human review for every prop.
- **Analytics drift** — server-composed screens must emit impressions/taps consistently; put `impressionId` in the schema so the server identifies the content, and add a client-generated render ID, because a cached payload replays the same `impressionId` on every render ([`analytics-sdk.md`](analytics-sdk.md)).
- **Performance** — deep section lists are still `LazyColumn` items with stable keys (`section.id`); payload-driven UI doesn't exempt you from [stability discipline](../android/compose/stability.md).
- **Offline UX honesty** — a stale cached screen with a dead promo is worse than a generic screen; TTL + "content may be outdated" states are product decisions to force early.

## 10. Follow-up Questions (anticipate)

- "How would you A/B test two screen compositions?" → the composition service consumes the experimentation platform ([`experimentation-platform.md`](experimentation-platform.md)); the server includes the bucket in `cacheKey`, so caches don't cross-contaminate and the client never computes it.
- "How do forms work — isn't input state behavior?" → input components own local state natively; submission is a `mutate` action with a typed payload; validation rules ship as data (regex/required/ranges), complex validation stays server-side.
- "How do you handle SDUI state management for interactive components?" → Components maintain ephemeral state (like text input or toggle state) locally in a state holder keyed by `section.id`, since two same-type sections would otherwise share one ViewModel. That state is aggregated and dispatched as a unified payload upon a designated submit action, keeping the server stateless during interaction.
- "Could this drive the whole app?" → chrome (tabs, auth, settings) stays native; SDUI earns its keep on high-iteration surfaces (home, search results, checkout upsells) — large platforms such as Airbnb's show it can cover many surfaces, but expect to build authoring, preview, and observability tooling to match.

## 11. Out of Scope (defended earlier, restated)

Interpreter-based dynamism, server-driven navigation graphs, the authoring CMS, and multi-platform web rendering — each is its own design with its own failure modes.

## 12. Further Reading

- [A Deep Dive into Airbnb's Server-Driven UI System](https://medium.com/airbnb-engineering/a-deep-dive-into-airbnbs-server-driven-ui-system-842244c5f5) — the Ghost Platform: sections, single GraphQL schema, cross-platform frameworks.
- [InfoQ summary of Airbnb's SDUI platform](https://www.infoq.com/news/2021/07/airbnb-server-driven-ui/) — condensed architecture overview.
- [The journey to server-driven UI at Lyft Bikes and Scooters](https://eng.lyft.com/the-journey-to-server-driven-ui-at-lyft-bikes-and-scooters-c19264a0378e) — a smaller, surface-scoped rollout.
- [Unsafe URI loading](https://developer.android.com/privacy-and-security/risks/unsafe-uri-loading) — validating schemes and hosts.
- [`feature-flags-and-remote-config.md`](feature-flags-and-remote-config.md) — the simpler sibling: values, not composition.
- [`versioning-and-backward-compatibility.md`](versioning-and-backward-compatibility.md) — the canonical version-negotiation treatment.
- [`../backend-for-mobile/bff-pattern.md`](../backend-for-mobile/bff-pattern.md) — the composition service is a BFF specialization.
- [`../platform-engineering/design-systems-architecture.md`](../platform-engineering/design-systems-architecture.md) — the component vocabulary SDUI composes.
