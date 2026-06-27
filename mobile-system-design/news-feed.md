# System Design: News Feed (Instagram / Twitter)

## The Prompt

*"Design the News Feed for a global social media application like Twitter or Instagram. The app must load the feed instantly on startup, support infinite scrolling of mixed media (text, images, video), allow users to 'Like' posts while offline, and seamlessly handle new incoming posts at the top of the feed."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Display a vertically scrolling feed of Posts (Text, Image, Video).
- Infinite scroll backwards in time.
- Pull-to-refresh to fetch newer posts.
- Users can Like/Unlike posts (even offline).

### Non-Functional Requirements (NFRs)
- **Latency (Priority 0):** The app must show the feed instantly (< 300ms) on cold start. (Mandates an Offline-First cache).
- **Smoothness:** Scrolling must never drop below 60 FPS, despite mixed media types.
- **Data Integrity:** Liking a post offline must eventually sync to the server without being overwritten by a stale network response.

## 2. High-Level Architecture

The News Feed is the ultimate test of the **Offline-First Paging Architecture**. It combines Pagination, Image Loading, and Optimistic UI updates into a single complex flow.

```mermaid
graph TD
    UI[Compose LazyColumn] <-->|Observe Flow| ViewModel
    
    subgraph Paging Layer (Single Source of Truth)
        ViewModel <-->|PagingData| Repo[Feed Repository]
        Repo <-->|Query| DB[(Room SQLite)]
        Repo -->|Trigger Load| RemoteMediator
    end
    
    subgraph Background Sync
        RemoteMediator -->|Fetch Next Page| API[Backend REST API]
        API -->|Insert| DB
        
        ActionWorker[Like/Unlike WorkManager] -->|POST /like| API
    end
```

## 3. Data Model & Components

### The Local Database (Room)

The Feed is not just a list of posts; it requires a complex relational model to handle offline Likes correctly.

```kotlin
@Entity(tableName = "feed_posts")
data class PostEntity(
    @PrimaryKey val id: String,
    val authorId: String,
    val textContent: String,
    val mediaUrl: String?,
    val mediaType: MediaType, // NONE, IMAGE, VIDEO
    val serverLikeCount: Int,
    val serverHasLiked: Boolean
)

// We store pending offline actions SEPARATELY.
@Entity(tableName = "pending_likes")
data class PendingLikeEntity(
    @PrimaryKey val postId: String,
    val isLiked: Boolean, // true = Like, false = Unlike
    val timestamp: Long
)
```

### The API (Cursor Pagination)

The backend MUST use Cursor pagination (usually based on a Cassandra `timeuuid` or SnowFlake ID). If it uses `offset/limit`, the feed will show duplicate posts when new items are injected at the top. (See [Pagination](pagination.md)).

```http
// Client requests the feed
GET /v1/feed?limit=20&cursor=1672531200000

// Response
{
  "next_cursor": "1672531000000",
  "posts": [ ... ]
}
```

## 4. The Core Flows (Deep Dive)

### Flow 1: Instant Cold Start
1. User opens the app.
2. The UI subscribes to `Flow<PagingData<PostEntity>>` from Room.
3. Room instantly emits the 20 posts currently sitting on the flash disk. The UI renders in < 100ms.
4. Concurrently, the `RemoteMediator` fires a `REFRESH` request to the network to check for newer posts.
5. If new posts exist, they are inserted at the top of the Room table.
6. Room automatically emits the new list. `DiffUtil` animates the new posts into the top of the feed smoothly.

### Flow 2: Optimistic Offline Liking (The Hard Part)
*Interviewer:* "The user is on an airplane. They 'Like' Post A. The post currently has 10 likes. You update the local DB so it shows 11 likes. 5 minutes later, they land. In that 5 minutes, 50 other people liked Post A. When your app syncs, how do you prevent the total count from resetting to 11?"

**Staff Answer:**
"We must separate the *Client State* from the *Server State*.
1. When the user taps 'Like' offline, I do NOT modify `serverLikeCount`.
2. I insert a row into the `pending_likes` table: `(postId="A", isLiked=true)`.
3. The UI observes a SQL View or a joined query: `SELECT serverLikeCount + (if pending_like=true then 1 else 0) as displayLikeCount`. The UI instantly shows 11 (Optimistic UI).
4. `WorkManager` attempts to push the `pending_like` to the backend.
5. The Backend processes it, and eventually returns a new feed payload where the real `serverLikeCount` is now 61.
6. The `RemoteMediator` saves the new post data to Room, and *deletes* the row from `pending_likes`.
7. The UI updates to show 61. There is no race condition because the client's local action and the server's absolute count are never merged mathematically on the client."

### Flow 3: Mixed Media Scrolling (Jank Prevention)
*Interviewer:* "Your feed has text, large images, and autoplaying videos. The user scrolls rapidly. The app drops to 15 FPS. Why?"

**Staff Answer:**
"This is caused by UI thread blocking and excessive garbage collection.
1. **Images:** I will use a library like Coil/Glide to ensure Bitmap decoding happens on `Dispatchers.IO` and utilizes memory pooling (`inBitmap`) to prevent GC thrashing. (See [Image Loading](image-loading.md)).
2. **Video:** `ExoPlayer` instances are incredibly heavy. We cannot instantiate an `ExoPlayer` for every video in the feed. I will use an **ExoPlayer Pool**. The app keeps exactly 1 (maybe 2) active `ExoPlayer` instances. When a video scrolls into the center 50% of the screen, it grabs the Player from the pool and attaches it to the `PlayerView`. When it scrolls out, it detaches it.
3. **View Types:** In a `RecyclerView`, I must explicitly define different `viewType` integers for Text-only, Image, and Video posts. This ensures the `RecyclerView` pools them separately. A Video view is never forced to bind a Text-only post, preventing massive layout hierarchy recalculations."

## 5. Failure Modes & Bottlenecks

### Bottleneck: The "Back to Top" Duplicate
*Interviewer:* "The user scrolls down 500 posts. They tap the 'Home' tab to jump to the top. The `RemoteMediator` fires a `REFRESH`. The backend returns the 20 newest posts. You insert them. Now the user has a gap in their feed between Post 20 and Post 500. If they scroll down, the app crashes or shows duplicates. Why?"

**Staff Answer:**
"This is the **Paging Gap Problem**. If you refresh the top of the feed while deeply scrolled, the cursor chain is broken. 
**The Fix:** When a `REFRESH` occurs (e.g., Pull-to-Refresh or Back-to-Top), the `RemoteMediator` must execute a **Clear and Replace** strategy. It must delete the *entire* cached feed in Room before inserting the 20 new posts. This resets the Paging state completely. The user will lose their position deep in the feed, but this is the standard expected behavior when returning to the top of Twitter or Instagram."

### Bottleneck: Video Bandwidth Exhaustion
*Interviewer:* "The user scrolls past 10 videos very quickly. The app initiates 10 video streams. The network is completely saturated. The images stop loading entirely."

**Staff Answer:**
"We must implement **Request Cancellation** tied to the UI lifecycle. 
When a video post is recycled (scrolls off-screen), the `onViewRecycled` callback must explicitly tell `ExoPlayer` to stop buffering and sever the HTTP connection. Furthermore, videos in the feed should not download the full MP4; the backend must provide HLS (HTTP Live Streaming) manifests, and the player should be configured to only buffer the first 3 seconds initially."

## 6. Staff Engineer Thinking: Backend Awareness

A Staff Mobile Engineer does not just accept whatever API the backend provides.

1.  **Fan-Out on Write vs Read:** If this is Twitter (celebrities with 100M followers), the backend uses Fan-Out on Write. When Justin Bieber tweets, the backend copies that tweet ID into 100 million Redis lists. When the Android app calls `GET /feed`, it is a lightning-fast `O(1)` read from Redis.
2.  **Edge Caching (CDN):** The JSON payload for a highly active public feed should be cacheable at the Edge (Cloudflare/Fastly). If the user isn't logged in, the mobile app should hit a CDN URL that serves the feed globally in <20ms, bypassing the core backend entirely.

## 7. Probing Questions (For Practice)

1.  Explain why an Offline-First architecture (Room DB as Single Source of Truth) is mandatory to achieve the <300ms cold start latency requirement for a News Feed.
2.  Describe the "Optimistic UI" pattern. How does separating the `pending_likes` table from the `feed_posts` table prevent data corruption during synchronization?
3.  Why is Cursor-based pagination (e.g., `after=timestamp`) absolutely required for a News Feed, and how does Offset/Limit pagination cause duplicate items?
4.  Explain the "ExoPlayer Pool" concept. Why is it an architectural failure to instantiate a new Video Player object for every video post in the feed?
5.  What is the "Paging Gap Problem"? Walk through why a Pull-to-Refresh action usually requires the mobile app to completely clear the local database cache.
6.  Describe how `DiffUtil` (or Compose's lazy diffing) prevents the entire screen from flashing white when new posts are injected at the top of the feed.
7.  How does failing to cancel HTTP requests in `onViewRecycled` lead to network saturation and image loading failures?
8.  Why is HLS (HTTP Live Streaming) preferred over standard MP4 downloads for autoplaying videos in an infinite scrolling feed?
9.  Explain the Backend "Fan-Out on Write" architecture and why a Staff Mobile Engineer must know if the backend is using it when designing the API contract.
10. If the app supports "Soft Deletes" (e.g., hiding a post from your own feed), how must the `RemoteMediator` handle these hidden posts when parsing a new page from the server?

## Further Reading

- [`pagination.md`](pagination.md) — The deep mechanics of Paging 3 and Cursors.
- [`offline-first-app.md`](../reference-architectures/offline-first-app.md) — The structural blueprint for the Single Source of Truth.
- [`jank.md`](../android/performance/jank.md) — How complex `RecyclerView` hierarchies destroy frame rates.
