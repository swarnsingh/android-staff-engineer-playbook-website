# News Feed (Instagram / Twitter-style)

> A 45-60 minute mobile system-design walkthrough for a social feed client (Android-first). Feed ranking, fan-out, and the ML pipeline are server concerns — the bulk of this file is how the *Android app* renders, paginates, and stays responsive over a slow network.

---

## 1. Gathering Requirements (~5 min)

> **Interviewer:** "Design a news feed like Instagram."
> **Candidate:** "I'll keep the backend at one diagram — the interesting work for a mobile engineer is paging, scroll, video, and offline behavior. Want me to start there?"

### Functional Requirements
- **Infinite scroll** of mixed posts (image, short video, text).
- **Pull-to-refresh** to show new posts.
- **Like / comment count** updates optimistically.
- **Open a post** in a detail screen and come back without losing scroll position.
- **Background prefetch** of the next page over Wi-Fi.

### Non-Functional Requirements
- **Smooth scroll** at 90/120 Hz — no jank, no frame drops on a mid-range device.
- **Offline tolerance** — last seen feed renders from cache; "Tap to retry" if the network is dead.
- **Data-saver mode** — disable autoplay, low-quality images on cellular.
- **Battery** — no decoded video off-screen; release players aggressively.

### Out of Scope
- Authoring / upload flow
- DMs, stories, reels recommendations carousel
- Ad-serving SDK integration
- Recommendation model training (the ranker is a black box that returns a sorted list of postIds)
- Content moderation / takedown UX

---

## 2. Clarifying Questions (~3 min)

| Question | Why it matters |
|---|---|
| DAU / median sessions per day? | Cache size, prefetch policy |
| Median post type (image-heavy vs text)? | ExoPlayer pool size, Coil disk budget |
| Geography (cellular cost)? | Data-saver default, image quality tier |
| Android API floor? | `setExpedited`, predictive back, Compose strong-skipping |
| Avg images per post? | Carousel pagination, prefetch radius |
| Should likes work offline? | Outbox for engagement events |
| Real-time "new posts available" banner? | FCM data push vs polling |
| Personalised order or chronological? | Cache eviction strategy (personalised = short TTL) |

> **Candidate:** "Assuming 50M DAU, mostly image + 6-15s video, mixed networks, Android 9+, personalised ranking, ~30 min median session."

---

## 3. High-Level Diagram (~10 min)

```
            ┌────────────────┐
            │  Android Client│
            │   (this talk)  │
            └────────┬───────┘
                     │ HTTPS + (optional) WSS for "new posts" hint
                     ▼
       ┌──────────────────────────┐
       │       BFF / Feed API     │
       │ (paginates, hydrates)    │
       └──┬─────────┬────────┬────┘
          │         │        │
     ┌────▼───┐ ┌──▼───┐ ┌──▼───┐
     │Ranking │ │ CDN  │ │ Push │
     │  + ML  │ │media │ │ FCM  │
     └────────┘ └──────┘ └──────┘
```

**Server components (named, not designed):**
- **Feed API (BFF)** — accepts `cursor`, returns hydrated posts ready for render.
- **Ranking + ML** — picks postIds in order. Treated as a black box.
- **CDN** — serves images / HLS video segments with edge caching.
- **Push (FCM)** — fires a low-bandwidth "new posts available" hint when desired.

> The rest of the file is what the Android app does with `/v1/feed?cursor=…`.

---

## 4. API Contract

### Feed page (cursor-paginated)

```json
GET /v1/feed?cursor=eyJvIjozMH0=&limit=15
200 OK
{
  "items": [
    { "id": "p_991", "author": { "id": "u_7", "name": "sam", "avatar": "https://cdn/…" },
      "media": [{ "type": "image", "url": "https://cdn/…", "blurhash": "L6P…", "w": 1080, "h": 1350 }],
      "text": "…", "likeCount": 41, "commentCount": 3,
      "likedByMe": false, "createdAt": 1750000000 }
  ],
  "nextCursor": "eyJvIjo0NX0="
}
```

### Engagement (optimistic, idempotent)

| Method | Path | Use |
|---|---|---|
| `POST` | `/v1/posts/{id}/like` | Idempotent (state, not increment) |
| `DELETE` | `/v1/posts/{id}/like` | Idempotent unlike |
| `POST` | `/v1/posts/{id}/comments` | `Idempotency-Key` header (UUID) |

### "New posts available" FCM payload

```json
{ "type": "feed.new", "count": "3" }   // hint only; client decides whether to show banner
```

> **Wire-level rule:** the server returns *render-ready* objects. The client should not need to JOIN, re-rank, or hydrate. That's the BFF's job.

---

## 5. Mobile App Architecture (~10 min)

### Module structure

```
:app
:feature:feed              ← list screen
:feature:post-detail
:core:network              ← Ktor 3 / OkHttp + Retrofit
:core:database             ← Room 2.7+, Paging 3 LOCAL store
:core:media                ← Coil 3, Media3 (ExoPlayer)
:core:work                 ← engagement Outbox worker
:domain:feed
:data:feed                 ← FeedRepository + RemoteMediator
```

### Layered diagram

```
   Compose UI ──► FeedViewModel ──► FeedRepository
                                       │
                                       ├─► Pager(Paging 3) ─► RemoteMediator ─► /v1/feed
                                       ├─► Room (cache, page anchors)
                                       └─► EngagementOutbox ─► WorkManager
```

### Key class signatures

```kotlin
interface FeedRepository {
    fun feed(): Flow<PagingData<Post>>
    suspend fun toggleLike(id: String, liked: Boolean)
    fun newPostsAvailable(): Flow<Int>   // from FCM hint
}

@HiltViewModel
class FeedViewModel @Inject constructor(
    private val repo: FeedRepository,
    savedState: SavedStateHandle,
) : ViewModel() {
    val feed: Flow<PagingData<PostUi>> = repo.feed().map(::toUi).cachedIn(viewModelScope)
    val firstVisible = savedState.getStateFlow("firstVisible", 0)
    val newPostsBadge: StateFlow<Int>
}
```

---

## 6. Local Storage (Room as cache, not source of truth for feed order)

```kotlin
@Entity(tableName = "feed_posts")
data class PostEntity(
    @PrimaryKey val id: String,
    val authorId: String, val text: String?,
    val mediaJson: String,      // serialized via kotlinx.serialization
    val likeCount: Int, val likedByMe: Boolean,
    val commentCount: Int, val createdAt: Long,
    val pageIndex: Int          // for RemoteMediator
)
```

> Feed order is **server-truth** (it's personalised), so we cache by `pageIndex` not by `createdAt`. On `REFRESH` the mediator clears and refetches. Likes are cached locally and reconciled against the server response on next fetch.

---

## 7. Deep Dive: Feed Scroll & Pagination (~15 min)

> *I'd pick this as the deep dive because it covers Paging 3 + RemoteMediator, scroll restoration across process death, optimistic likes, lifecycle-aware video, image prefetch, and the "new posts available" pattern — most of the interesting client decisions in one feature.*

### Paging 3 + RemoteMediator

```kotlin
@OptIn(ExperimentalPagingApi::class)
class FeedRemoteMediator(
    private val api: FeedApi,
    private val db: AppDatabase,
) : RemoteMediator<Int, PostEntity>() {
    override suspend fun load(
        loadType: LoadType,
        state: PagingState<Int, PostEntity>,
    ): MediatorResult = try {
        val cursor = when (loadType) {
            LoadType.REFRESH -> null
            LoadType.PREPEND -> return MediatorResult.Success(endOfPaginationReached = true)
            LoadType.APPEND  -> state.lastItemOrNull()?.let { /* derive cursor */ } ?: return MediatorResult.Success(true)
        }
        val resp = api.feed(cursor, limit = PAGE_SIZE)
        db.withTransaction {
            if (loadType == LoadType.REFRESH) db.feedDao().clear()
            db.feedDao().insert(resp.items.toEntities(loadType))
        }
        MediatorResult.Success(endOfPaginationReached = resp.nextCursor == null)
    } catch (t: Throwable) { MediatorResult.Error(t) }
}
```

### Compose UI

```kotlin
@Composable
fun FeedScreen(vm: FeedViewModel = hiltViewModel()) {
    val items = vm.feed.collectAsLazyPagingItems()
    val state = rememberLazyListState(initialFirstVisibleItemIndex = vm.firstVisible.collectAsStateWithLifecycle().value)
    LazyColumn(state = state) {
        items(items.itemCount, key = items.itemKey { it.id }) { i ->
            items[i]?.let { PostCard(it, onLike = { vm.toggleLike(it.id, !it.likedByMe) }) }
        }
        item { if (items.loadState.append is LoadState.Loading) FeedSpinner() }
    }
    LaunchedEffect(state) {
        snapshotFlow { state.firstVisibleItemIndex }.collect { vm.onScroll(it) }
    }
}
```

### Lifecycle-aware video (Media3)

| Concern | Approach |
|---|---|
| Off-screen autoplay | `LifecycleEventEffect(ON_STOP) { player.pause() }` + visibility detector |
| Player pool | 2-3 `ExoPlayer`s reused, not one per card |
| Audio focus | Muted autoplay; unmute only on tap |
| Pre-buffer | `setLoadControl` with small `bufferForPlayback` so scroll is responsive |
| Release | `DisposableEffect { onDispose { player.release() } }` on the post composable |

### Scroll restoration across process death

`savedState.getStateFlow("firstVisible", 0)` persists the index. On restore, `rememberLazyListState(initialFirstVisibleItemIndex = …)` rebuilds the list. Paging 3's `cachedIn(viewModelScope)` keeps pages alive across config changes; for process death the `Pager` re-fetches the cursor for the visible page.

### Optimistic likes

```kotlin
suspend fun toggleLike(id: String, liked: Boolean) {
    db.feedDao().setLiked(id, liked, deltaCount = if (liked) +1 else -1)  // optimistic
    engagementOutbox.enqueue(EngagementOp.Like(id, liked))                // durable
}
```

`EngagementOutboxWorker` is a `@HiltWorker` with `setExpedited`, retries on 5xx, drops on 4xx. On reconcile, the next feed fetch overwrites local counts with server truth.

### Image prefetch

Coil 3 with an `ImageLoader.execute(ImageRequest)` for `state.firstVisibleItemIndex + 2..+6` on a low-priority dispatcher. Cancelled when the user scrolls back.

### "New posts available" banner

FCM data message → `WorkManager` increments a `newPostsBadge` `StateFlow`. The banner is a Compose composable; tap → `items.refresh()` + scroll to top.

---

## 8. Trade-offs

### Pagination strategy

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **Cursor + Paging 3 + RemoteMediator** | Stable, handles inserts, cached | More wiring | Pick this |
| Offset pagination | Trivial | Breaks when feed shifts (personalised) | Skip |
| Load-all | Trivial | OOM | Skip |
| Manual `LazyColumn` paging | No deps | Reinvents Paging 3 | Skip |

### Local cache

| Option | Use |
|---|---|
| **Room** | Page anchors, post bodies, like state |
| DataStore | User prefs (data-saver toggle, autoplay) |
| Disk (Coil/Media3) | Image / video segments |
| MemoryCache (Coil) | Last 25% of heap for decoded bitmaps |

### Image loader

| Option | Verdict |
|---|---|
| **Coil 3** | Pick — KMP-ready, Compose-native, Kotlin-first |
| Glide | Battle-tested but Java-first, no native Compose |
| Picasso | Unmaintained |
| Fresco | Heavy, native memory; only if you need bitmap streaming |

### Video player

| Option | Verdict |
|---|---|
| **Media3 (ExoPlayer)** | Pick — official, DASH/HLS, surface abstraction |
| `MediaPlayer` | Limited; no adaptive streaming |
| Web `VideoView` in WebView | Latency, no pre-buffer control |

### "New posts" hint transport

| Option | Verdict |
|---|---|
| **FCM data push** | Pick — battery-friendly, server-pushed |
| WebSocket | Overkill for a count |
| Polling | Wastes battery and quota |

---

## 9. Major Concerns

- **Jank.** Decoded bitmap memory dominates; cap Coil at 25% heap. Compose `key { post.id }` prevents recomposition on scroll. Use `derivedStateOf` for "is at top" so the FAB doesn't recompose every frame.
- **Battery.** No auto-playing video off-screen. `Media3` player pool capped at 2-3. Foreground discipline — drop the WebSocket "new posts" channel when backgrounded.
- **Cellular data.** Data-saver default on metered networks (`ConnectivityManager.isActiveNetworkMetered`). Lower image quality variant requested from CDN.
- **Process death.** Scroll index in `SavedStateHandle`. Page cursor re-derived from the visible page on restore. Pager's in-memory cache is rebuilt.
- **Memory leaks.** `ExoPlayer.release()` in `DisposableEffect`. No `Activity` held by ViewModels or repos.
- **Cold start.** Show a skeleton from Room while `RemoteMediator` refreshes. No spinner on first paint.
- **Errors.** `LoadState.Error` → inline retry chip, not a full-screen error. Empty state when `items.itemCount == 0` and not loading.
- **Accessibility.** `Modifier.semantics` per post; `LazyColumn` announces position. Honor "reduce motion" by disabling autoplay.

---

## 10. Follow-up Questions

> **Q: How do you avoid showing the same post twice across pagination?**
> The mediator dedupes by `id` (PK). Server should also stabilise cursor over a session — if the ranker reshuffles mid-session you'd see dupes. Mitigation: server returns a `sessionId` baked into the cursor.

> **Q: What if a post is deleted between page fetches?**
> Server returns a tombstone in the next page or omits it. Client filters `deleted == true` in the DAO query. UI animates removal via `AnimatedItem`.

> **Q: How do likes reconcile if the worker is offline for hours?**
> The Outbox is durable in Room. On reconnect, the worker drains in order. If server state diverges (someone unliked from web), the next feed fetch wins.

> **Q: How do you measure scroll jank?**
> `JankStats` (Jetpack) reports janky frames per session. Macrobenchmark + `BaselineProfile` for cold/warm start budgets. In-house dashboard tracks p95 frame time per device tier.

> **Q: How would you support a "for you" vs "following" toggle?**
> Two `Pager`s, one per tab. Tab state in `SavedStateHandle`. Each has its own Room key namespace. Switching tabs flips the `Flow<PagingData>` source — Compose handles it.

> **Q: Ads injection on the client?**
> Server returns ad slots inline (with a `type: "ad"` discriminator) so the client never has to interleave. Client just renders whatever the BFF gives it.

---

## 11. Out of Scope (defended)

- **Post upload** — separate flow with camera, media compression, resumable upload. ~30 min on its own.
- **Comments thread / replies** — UI is a separate screen with its own pagination.
- **Live video** — entirely different stack (RTMP ingest, low-latency HLS, chat overlay).
- **Stories** — short-form, separate cache eviction (24h TTL).
- **Recommendation model internals** — server's black box; we consume sorted IDs.

---

## 12. Further Reading

- [weeeBox/mobile-system-design](https://github.com/weeeBox/mobile-system-design) — reference format.
- [Android Developers — Paging 3 library](https://developer.android.com/topic/libraries/architecture/paging/v3-overview) — official guide + RemoteMediator.
- [Coil 3 documentation](https://coil-kt.github.io/coil/) — Compose-first, KMP-ready image loader.
- [Media3 (ExoPlayer) docs](https://developer.android.com/media/media3) — player pooling and lifecycle.
- [Now in Android sample](https://github.com/android/nowinandroid) — production-grade Compose feed with Paging.

---

> **Closing in the interview:** "Send-flow equivalent for a feed is the page-and-render loop — I picked that. Happy to deep-dive into video pooling, FCM ranking-update hints, or the data-saver tier logic next."
