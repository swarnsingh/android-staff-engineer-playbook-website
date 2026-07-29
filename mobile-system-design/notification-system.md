# Notification System (End-to-End)

> A 45-60 minute mobile system-design walkthrough for an end-to-end notification system: the parts that decide *what* to send, *who* to send to, *when*, and how preferences propagate. The Android client receive pipeline is the previous file (`push-notifications.md`); this one focuses on the *system*.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a notification system for an app like Uber or Instagram."
> **Candidate:** "There are three layers: triggers (what causes a notification), routing (which channels, which devices), and preferences (user opt-outs, do-not-disturb, frequency caps). I'll deep-dive routing + preferences."

### Functional Requirements
- **Triggers**: domain events (order shipped, comment received, low balance) emit notifications.
- **Channels**: push, in-app, email, SMS — pluggable.
- **User preferences**: per-channel, per-category opt-in/out.
- **Frequency caps**: don't spam (e.g., max 3 promos/day).
- **Localization**: render in user's language at delivery time.

### Non-Functional Requirements
- **Don't lose triggers** under bursts (Black Friday).
- **Honour preferences** before delivery.
- **Mobile-side**: respect channel mute, lock-screen visibility, quiet hours.
- **Observable**: every step from trigger to render is traced.
- **Compliance**: GDPR opt-out, CAN-SPAM unsubscribe link.

### Out of Scope
- Marketing campaign UI (Braze/Iterable cover this)
- A/B testing of notification copy (see `a-b-testing-infrastructure.md`)
- Server-side delivery infra at hyperscale (Kafka topics, sharding)
- iOS / web push transports (slot-in components)
- Anti-spam ML model design

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| Volume per day (10k vs 10M)? | Worker count, queue sizing |
| User-facing preference granularity? | Schema complexity |
| Transactional vs marketing mix? | Different paths, different SLAs |
| Do we render templates server-side or client-side? | Payload size, localization strategy |
| Channels in scope (push only or also email/SMS)? | Adapter count |
| Frequency caps per category or per channel? | Throttle scope |
| Quiet hours configurable? | Per-user time-zone logic |

> **Candidate:** "Mid-scale (1M DAU), push + email + in-app inbox, mostly transactional, server-side templates, per-category opt-out + global quiet hours, Android 9+ on the client."

---

## 3. High-Level Diagram (~10 min)

```
      Domain events (Order, Chat, Account)
                       │
                       ▼
               Notification Service
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Preferences    Template        Frequency
     Service       Renderer         Capper
                       │
                       ▼
                Channel Routers
                       │
        ┌──────┬───────┼───────┬──────┐
        ▼      ▼       ▼       ▼      ▼
       FCM   APNs    Email    SMS    Inbox
                       │
                 (client receives)
```

**Server components (named, not designed):**
- **Notification Service** — receives triggers, orchestrates routing.
- **Preferences Service** — user opt-ins per category + channel.
- **Template Renderer** — locale + variable substitution.
- **Frequency Capper** — throttle per user/category/channel.
- **Channel Routers** — push, email, SMS adapters.

> The Android client is one consumer of FCM; the system above is what *decides* whether to send.

---

## 4. API Contract

### Trigger (internal service → notif service)

```json
POST /v1/notifications
{
  "userId": "u_42",
  "category": "order_shipped",
  "templateId": "order_shipped_v3",
  "variables": { "orderId": "o_99", "carrier": "DHL", "trackingUrl": "https://..." },
  "channels": ["push", "email", "inbox"],
  "priority": "transactional",
  "deduplicationKey": "order_shipped_o_99"
}
```

### Preferences (client → preferences service)

```http
GET /v1/me/preferences
{
  "categories": {
    "promo":          { "push": false, "email": true,  "inbox": true },
    "order_update":   { "push": true,  "email": true,  "inbox": true },
    "chat_dm":        { "push": true,  "email": false, "inbox": true },
    "account_security": { "push": true, "email": true, "inbox": true }  // not toggleable
  },
  "quietHours": { "start": "22:00", "end": "07:00", "tz": "Asia/Kolkata" }
}

PATCH /v1/me/preferences
{ "categories": { "promo": { "push": false } } }
```

### Inbox (client → API)

```http
GET /v1/me/inbox?cursor=…&limit=30
GET /v1/me/inbox/unread-count
POST /v1/me/inbox/{id}/read
```

### FCM payload (push channel)

```json
{
  "data": {
    "type": "order_shipped",
    "templateId": "order_shipped_v3",
    "title": "Your order has shipped",
    "body": "Your DHL package is on the way.",
    "deepLink": "myapp://orders/o_99",
    "inboxId": "n_555"
  }
}
```

---

## 5. Mobile App Architecture (client view)

### Module structure

```
:app
:feature:inbox             ← in-app notifications screen
:feature:settings          ← preferences UI
:core:notifications        ← from push-notifications.md
:core:work                 ← inbox sync workers
:data:preferences          ← preferences repo
:data:inbox                ← inbox repo (Room mirror)
```

### Layered diagram

```
   PushDispatcher ──► InboxRepository ──► Room (inbox_items)
                            │
                            ▼
                    Compose Inbox screen
                            │
                    "Mark all read" → REST PATCH
```

### Key class signatures (client)

```kotlin
interface PreferencesRepository {
    fun preferences(): Flow<Preferences>
    suspend fun setCategoryChannel(category: String, channel: Channel, enabled: Boolean)
    suspend fun setQuietHours(start: LocalTime, end: LocalTime)
}

interface InboxRepository {
    fun unreadCount(): Flow<Int>
    fun items(): Flow<PagingData<InboxItem>>
    suspend fun markRead(id: String)
}
```

---

## 6. Local Storage

```kotlin
@Entity(tableName = "preferences")
data class PreferenceRow(
    @PrimaryKey val key: String,         // e.g., "promo.push"
    val value: String,                   // "true"/"false"/"22:00"
    val updatedAt: Long, val dirty: Boolean
)

@Entity(tableName = "inbox_items")       // mirrors server inbox
data class InboxItem(
    @PrimaryKey val id: String, val category: String,
    val title: String, val body: String,
    val deepLink: String?, val receivedAt: Long, val readAt: Long?
)
```

Preferences sync uses the same outbox pattern as `offline-sync.md`. Inbox is a cache; server is the truth for read state and ordering.

---

## 7. Deep Dive: Routing + Preferences (~15 min)

> *I'd pick this as the deep dive because routing + preferences is where notification systems fail in subtle ways: wrong channel, wrong language, double sends, sends during quiet hours.*

### Routing pipeline (server-side, conceptually)

```
Trigger
  │
  ▼
1. Dedupe by deduplicationKey (idempotency)
  │
  ▼
2. Lookup user prefs + locale + timezone
  │
  ▼
3. For each requested channel:
     a. Channel enabled for category? (prefs)
     b. Frequency cap not hit? (capper)
     c. Quiet hours allow? (or category is "must-deliver")
     d. Render template in user's locale
     e. Hand to channel router
  │
  ▼
4. Channel router (push: build FCM data payload)
  │
  ▼
5. Persist in inbox (always, regardless of push success)
```

### Idempotency

The `deduplicationKey` is the only thing standing between a duplicate trigger and a duplicate ping. Service stores `(key, sentAt)` for a TTL window; second trigger with the same key is a no-op.

### Preferences resolution

```
Effective(category, channel) =
    prefs.get(category, channel)
    ?? defaultsForCategory(category, channel)
    ?? false
```

Defaults come from a server-side config:

```yaml
order_update:
  push: true
  email: true
  inbox: true
chat_dm:
  push: true
  email: false
  inbox: true
promo:
  push: false   # opt-in
  email: true
  inbox: true
account_security:
  must_deliver: true   # override; not user-toggleable
```

### Frequency capper

| Scope | Example |
|---|---|
| Per-user, per-category, per-day | "max 3 promos/day" |
| Per-user, per-channel, per-hour | "max 5 push/hour" |
| Per-conversation | Chat collapses to last message during a fast burst |
| Global emergency override | Account-security bypasses all caps |

Capper is a token-bucket store keyed by `(userId, scope)`. Sliding window in Redis or similar.

### Quiet hours

```
isQuiet(now, prefs):
    let userNow = now in prefs.tz
    let quietRange = prefs.quietHours
    return userNow in quietRange
```

**During quiet hours:**
- Transactional (`order_update`): deliver (may suppress sound at OS via channel importance).
- Promotional: defer until end of quiet hours (queue).
- Account security: always deliver.

### Client-side preferences UI

```kotlin
@Composable
fun NotificationSettingsScreen(vm: NotificationSettingsViewModel) {
    val prefs by vm.preferences.collectAsStateWithLifecycle()
    LazyColumn {
        items(prefs.categories) { (cat, channels) ->
            CategoryRow(cat) {
                Switch(checked = channels.push,
                    onCheckedChange = { vm.toggle(cat, Channel.PUSH, it) })
                Switch(checked = channels.email,
                    onCheckedChange = { vm.toggle(cat, Channel.EMAIL, it) })
            }
        }
        item { QuietHoursRow(prefs.quietHours, vm::setQuietHours) }
    }
}
```

Toggling writes locally first (`dirty=true`), syncs in the background. Server confirms via `PATCH`.

### Client-side delivery suppression

Even with server-side prefs, the client double-checks:
- If channel importance was lowered by the user post-config, the OS handles silence.
- If category opt-out toggled offline, push that already arrived is still inserted into the inbox; the OS notification is suppressed via `NotificationManagerCompat.areNotificationsEnabled()` short-circuit.

### Inbox sync

```kotlin
@HiltWorker
class InboxSyncWorker @AssistedInject constructor(...) : CoroutineWorker(ctx, params) {
    override suspend fun doWork(): Result {
        val resp = api.fetchInbox(since = lastToken)
        db.withTransaction {
            resp.items.forEach { inboxDao.upsert(it.toEntity()) }
            tokenStore.lastInboxToken = resp.nextToken
        }
        return Result.success()
    }
}
```

Triggered: on FCM hint, on app foreground, on periodic 30-min schedule.

### Failure modes

| What breaks | Behavior |
|---|---|
| Duplicate trigger from upstream service | Dedup key drops it |
| Email channel down | Continue with push + inbox; mark email pending; retry |
| FCM rejects payload size | Truncate body, drop large fields; keep deep link |
| User offline for days | Inbox grows server-side; on next sync, client paginates |
| Preferences out of sync | Client preference is sent on next change; server is the truth |
| Template renderer fails | Log + fallback to plain text from `body` |

---

## 8. Trade-offs

### Where templates live

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Server-side render** | Locale + variables centralized; A/B easy | Larger payloads | Pick this |
| Client-side render | Smaller payloads; resilient to server change | Localization redundant on every client; templates harder to A/B | Skip for new |
| Hybrid (server fills, client tweaks) | Flexibility | Two places to debug | Use sparingly |

### Trigger fan-out

| Option | Verdict |
|---|---|
| **Domain event → notification service** | Pick — decoupled |
| Direct API call from service A to send notification | Tight coupling, hard to test |
| Cron / batch | Use only for explicit campaign jobs |

### Inbox modeling

| Option | Verdict |
|---|---|
| **Server inbox, mirrored to Room** | Pick — multi-device read state |
| Local-only inbox | Lost on uninstall, no multi-device |
| No inbox (push only) | Bad UX; misses are permanent |

### Preferences storage

| Option | Verdict |
|---|---|
| **Server preferences, mirrored locally** | Pick — survives device change |
| Local-only preferences | Lost on uninstall, no multi-device |
| OS-managed only (channel importance) | Coarse-grained, no category abstraction |

### Frequency cap store

| Option | Verdict |
|---|---|
| **Redis (token bucket per scope)** | Pick — fast, server-side |
| Database | Slower, harder to time-window |
| In-memory | Lost on restart |

---

## 9. Major Concerns

- **Idempotency.** Dedup keys on triggers. Server tracks `(key, sentAt)` for the TTL.
- **Localization.** Server-rendered with `Accept-Language`; falls back to user profile locale; falls back to `en`.
- **Multi-device.** A user with 3 devices needs the notification on all 3, but the inbox is shared. Read state syncs across devices via the server inbox.
- **Compliance.** Promotional channels are opt-in by default (CAN-SPAM, GDPR). Account-security is non-toggleable and explained in the UI.
- **Quiet hours edge cases.** Time-zone changes (user travels), DST transitions, midnight wrap. Use server-side resolution; store `tz` per user.
- **Burst protection.** Capper protects users; circuit breaker protects upstream when push provider is rate-limiting.
- **Observability.** Every step (trigger received, prefs resolved, channel routed, transport accepted, client received, user tapped) emits a trace event keyed by notification id.
- **Data minimisation.** Don't put PII or sensitive content in notification body; just summary + deep link.

---

## 10. Follow-up Questions

> **Q: User has 3 devices; should they get 3 push notifications?**
> Yes (one per device token). Reads sync across devices through the inbox — dismissing on one device updates the server inbox; the others see the updated read state on next sync.

> **Q: Marketing wants to send a campaign at 9am local time per user — how?**
> Capper + scheduler. Triggers are enqueued ahead of time; a scheduler dispatches at `userLocalNow == 09:00`. Easy with a per-user `nextEligibleAt` field.

> **Q: How is a notification deleted if the underlying event is cancelled (e.g., order cancelled)?**
> Send a follow-up `cancel` trigger with the same deep link; client removes the notification by tag (`notificationManager.cancel(tag, id)`).

> **Q: Why dual-write to inbox and push?**
> Push can be lost (OEM kills, no network, off). Inbox is the system of record from the user's POV. The push is a real-time hint; the inbox is the truth.

> **Q: What about "smart" muting (don't send if user is actively in the app)?**
> The dispatcher checks foreground state (covered in `push-notifications.md`); for chat notifications, suppress system notification while the conversation is on screen.

> **Q: How would A/B tests on copy work?**
> Trigger carries `experimentId`; server template renderer picks the variant; exposure event logs which variant. See `a-b-testing-infrastructure.md`.

---

## 11. Out of Scope (defended)

- **Marketing campaign authoring UI** — Braze / Iterable level.
- **Server-side fan-out at hyperscale** — Kafka topics, sharding strategies are backend territory.
- **iOS / web push** — channel adapters; pattern same as FCM.
- **Anti-spam ML** — would gate the capper; independent.
- **Email / SMS deliverability** — separate vendor problem.

---

## 12. Further Reading

- [Android Developers — Notifications overview](https://developer.android.com/develop/ui/views/notifications) — channels, importance, runtime permission.
- [Firebase Cloud Messaging — message types](https://firebase.google.com/docs/cloud-messaging/customize-messages/set-message-type) — notification and data payload behavior.
- [Iterable engineering — Designing a notification platform](https://iterable.com/blog/) — vendor perspective on triggers and routing.
- [GDPR — push notifications](https://gdpr.eu/) — consent and opt-in framing.
- [Don't kill my app](https://dontkillmyapp.com/) — OEM impact on actual delivery rates.

---

> **Closing in the interview:** "Routing + preferences was the deep dive because that's the system's job. Happy to talk through scheduling, the capper internals, or the inbox sync race conditions next."
