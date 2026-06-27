# Blueprint: The Social Media App (Infinite Feed Scale)

## 1. Architectural Signature
A Social Media App (e.g., Twitter, Instagram, TikTok) is optimized for **Infinite Pagination, Media Caching, and Asynchronous Write Operations**.
The architecture prioritizes the illusion of instant speed. When a user uploads a 4K video or a large image, they cannot be blocked from browsing their feed while it uploads. The app is fundamentally an offline-capable read cache coupled with a robust background write queue.

**Core Trade-off:** Eventual Consistency & Local Caching > Synchronous Writes.

## 2. Component Blueprint

### Presentation Layer (The Infinite Feed)
- **Framework:** Jetpack Compose. `LazyColumn` or `HorizontalPager` (for TikTok-style feeds) are pushed to their absolute limits.
- **View Recycling:** Unforgiving optimization of Recomposition. Complex nested Composables must use `derivedStateOf` and `remember` to prevent the entire feed from stuttering when a single "Like" button is pressed.
- **Media Playback:** ExoPlayer integration. The UI must proactively prepare the *next* video in the feed before it scrolls into view, ensuring a 0ms buffer delay when the user swipes.

### Domain Layer (The Fanout)
- **Background Upload Manager:** A dedicated module wrapping `WorkManager` (or a Foreground Service for massive video files). It handles chunked video uploads, exponential backoff, and UI progress reporting independently of the Activity lifecycle.
- **Pagination Engine:** Implements the Android `Paging 3` library to seamlessly stitch together network data and local database data.

### Data Layer (The Remote Mediator)
- **Local Persistence:** Room Database acts as the *Single Source of Truth* (SSOT).
- **Network Strategy:** **The Paging3 RemoteMediator Pattern**. 
  1. The UI observes a Flow directly from the Room Database.
  2. When the user scrolls to the bottom, the DB triggers the `RemoteMediator`.
  3. The Mediator fetches the next page of JSON from the network.
  4. The Mediator inserts the JSON into the Room Database.
  5. The UI automatically updates because it is observing the DB. The UI never talks to the network directly.
- **Image Pipeline:** Aggressive pre-fetching. The app downloads thumbnail images for posts that are 5 items below the current scroll position, ensuring they are hot in memory when the user scrolls down.

## 3. Infrastructure & DevOps
- **Release Cadence:** Highly iterative, A/B test driven.
- **Telemetry:** Deep focus on "Jank" (Dropped Frames). A social feed must scroll at 60 FPS (or 120 FPS on modern displays). The CI pipeline must run Macrobenchmark tests to ensure no PR introduces UI thread contention.

## 4. Scaling Bottlenecks & Staff Solutions

### Bottleneck 1: The "Like" Button Desync (Thundering Herd)
*Problem:* The user likes a post. The app fires an HTTP POST. The backend is under heavy load (e.g., during the Super Bowl) and returns an HTTP 503 error. The app removes the "Like" from the screen. The user taps it again angrily.
*Solution:* **Optimistic UI & Background Event Sourcing**.
1. When the user taps "Like", the UI instantly animates to the "Liked" state (Optimistic Update).
2. The UI inserts a `LikeAction(postId=123, status=PENDING)` into a local Room table.
3. A background process (WorkManager) detects the `PENDING` row and attempts the HTTP POST.
4. If the server returns 503, the WorkManager schedules a retry for 5 minutes later using exponential backoff.
5. The UI remains "Liked" based on the local DB state, entirely shielding the user from the backend failure. (This is how Twitter handles massive traffic spikes).

### Bottleneck 2: Database Size Explosion (The Cache Eviction)
*Problem:* The user scrolls past 10,000 tweets over a week. The Room Database grows to 500MB. The device runs out of storage, and SQLite queries become slow.
*Solution:* **The LRU (Least Recently Used) Cache Eviction Policy**.
The local Database is a cache, not a permanent archive.
1. The app must implement a scheduled background job (or a trigger on startup).
2. It executes a query to delete all posts older than 48 hours, *unless* they are explicitly bookmarked or belong to an active draft.
3. It vacuums the SQLite database to reclaim the physical disk space.

### Bottleneck 3: The Video Pre-Fetch Memory Leak
*Problem:* To make the TikTok-style swipe seamless, the app uses ExoPlayer to pre-buffer the next 3 videos in memory. The user swipes rapidly 20 times. The app crashes with an OOM (Out Of Memory) error because 20 ExoPlayer instances are silently buffering in the background.
*Solution:* **ExoPlayer Pooling & strict Lifecycle Hooks**.
1. The app must never create 20 `ExoPlayer` instances. It creates a **Pool** of exactly 3 instances.
2. Player 0 plays the current video. Player 1 pre-buffers the next video. Player 2 pre-buffers the previous video (in case the user swipes up).
3. When the user swipes down, Player 1 becomes the active player. Player 0 is stopped, reset, and immediately reassigned to pre-buffer the *new* next video.
4. Strict Compose `DisposableEffect` blocks ensure that when a video leaves the viewport by more than 1 index, its resources are aggressively released.

## 5. Summary of Technologies
- **UI:** Compose, `LazyColumn`, `derivedStateOf`.
- **Media:** ExoPlayer (Pooled), Coil (Pre-fetching).
- **Data:** Paging 3, Room, RemoteMediator.
- **Background:** WorkManager (for robust uploads and optimistic updates).

## Further Reading
- [`news-feed.md`](../mobile-system-design/news-feed.md) (The system design interview blueprint).
- [`caching-library.md`](../mobile-system-design/caching-library.md) (Deep dive into LRU memory limits).
- [`jank.md`](../android/performance/jank.md) (How to guarantee 60 FPS scrolling in a heavy feed).
