# System Design: Pagination

## The Prompt

*"Design the data loading mechanism for a social media feed like Instagram or a massive E-commerce search result. The backend database has 10 million items. The Android client must display them in an infinite scrolling list without crashing the app, running out of memory, or showing duplicate items."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Infinite scrolling list.
- Pull-to-refresh to get the latest items.
- Handle insertion/deletion of items mid-scroll.

### Non-Functional Requirements (NFRs)
- **Memory (RAM) Limit:** The app cannot hold 10,000 items in memory. It will trigger an `OutOfMemoryError` (OOM).
- **Performance (Jank):** Scrolling must maintain 60fps. Database queries and JSON parsing must occur on background threads.
- **Data Integrity:** No duplicated items and no skipped items, even if the underlying database is constantly changing.

## 2. High-Level Architecture (The Paging Layer)

A Junior engineer downloads 500 items into a giant `List<Item>`, puts it in a `RecyclerView`, and hopes for the best.
A Staff engineer builds a **Paging Pipeline** connecting the Network, the Disk (Room), and the UI in chunks.

```mermaid
graph TD
    UI[Jetpack Compose / RecyclerView] <-->|Observe Flow<PagingData>| Repo[Paging Repository]
    
    subgraph Paging Boundary (Paging 3)
        Repo -->|1. Query Page| DB[(Room DB)]
        Repo -->|2. Trigger Load| RemoteMediator[RemoteMediator]
    end
    
    RemoteMediator -->|3. Fetch Next Page| Network[Backend API]
    Network -->|4. Save to Disk| DB
```

*Staff Architecture:* The UI never talks to the Network. The UI asks Room for Page 1. When the user scrolls near the bottom, the `RemoteMediator` detects it, fetches Page 2 from the Network, saves it to Room, and Room automatically emits the new items to the UI.

## 3. The API Contract: Offset vs Cursor

This is the most critical decision in Pagination design.

### The Junior Way: Offset/Limit Pagination
```http
GET /feed?offset=0&limit=20   // Page 1
GET /feed?offset=20&limit=20  // Page 2
```
**The Flaw (The Duplicate Problem):**
1. User loads Page 1 (Items 1-20).
2. While the user is reading, someone posts a *new* item at the top of the feed (Item 0).
3. All items shift down by 1 in the database.
4. User scrolls down and requests Page 2 (`offset=20`).
5. Because everything shifted down, the item that used to be at index 19 is now at index 20. The server returns Item 19 again. The user sees a duplicate item in their feed.

### The Staff Way: Cursor Pagination
A Cursor is a unique, immutable pointer to a specific row in the database.
```http
GET /feed?limit=20                  // Page 1 (Returns items + next_cursor="xyz")
GET /feed?limit=20&after="xyz"      // Page 2
```
**The Solution:**
Even if 50 new items are inserted at the top of the feed, the `after="xyz"` cursor still points to the exact same item. The database just fetches the 20 items immediately following "xyz". No duplicates, no skipped items.

## 4. Internal Mechanics: Android Paging 3

Google's `Paging 3` library is the industry standard for handling the extreme complexity of asynchronous chunk loading.

### 1. PagingSource
The component that knows how to load chunks of data from a single source (usually Room). It handles the `load(params)` function and returns `LoadResult.Page` containing the data, the `prevKey`, and the `nextKey`.

### 2. RemoteMediator
The architectural bridge used in an **Offline-First** design. It listens to the `PagingSource` (Room). When Room runs out of data (e.g., the user scrolled to the end of the cached data), the `RemoteMediator` fires a network request, fetches the next JSON chunk, and saves it into Room.

### 3. PagingData & cachedIn
The `ViewModel` exposes a `Flow<PagingData<Item>>`. 
*Staff Rule:* You MUST call `.cachedIn(viewModelScope)` on this Flow. If the user rotates the phone (Activity recreation), the `PagingData` is held in memory by the ViewModel, preventing a redundant network request and a reset of the scroll position.

## 5. Failure Modes & Bottlenecks

### Bottleneck: The Memory Leak (Infinite Scroll)
*Interviewer:* "The user scrolls down 10,000 items. Your `PagingSource` keeps appending chunks to the Flow. The UI is now holding 10,000 items in RAM. The app crashes with OOM. How do you prevent this?"

**Staff Answer:**
"Paging 3 supports **Page Dropping** (Max Size). 
When I configure the `Pager`, I set `maxSize = 100`. As the user scrolls down and loads Page 4, the Paging library automatically *drops* Page 1 from memory. If the user scrolls back up, it re-fetches Page 1 from the local Room database. This caps the memory footprint strictly to the `maxSize`, mathematically preventing OOMs regardless of infinite scrolling."

### Bottleneck: Database Tombstones
*Interviewer:* "Users are swiping to delete items from the feed. You issue `DELETE` statements in Room. After a week, the app gets incredibly slow when scrolling."

**Staff Answer:**
"When you delete items in SQLite, it leaves 'Tombstones' (empty spaces). If a user deletes 5,000 items, and you query `SELECT * FROM items LIMIT 20 OFFSET 5000`, SQLite has to scan past 5,000 tombstones before finding active data. 
**The Fix:** I must implement a Database Vacuuming strategy, or rely strictly on Cursor-based pagination in SQLite (querying by indexed IDs) rather than `OFFSET`, ensuring read times remain `O(1)` regardless of deleted rows."

### Bottleneck: The Spinner Flash
*Interviewer:* "When the user scrolls to the bottom, they see a loading spinner for 500ms before the next items appear. It breaks the illusion of an infinite feed."

**Staff Answer:**
"We must configure the **Prefetch Distance**. 
In the `PagingConfig`, I will set `prefetchDistance = 10` (if `pageSize = 20`). 
When the user scrolls and reaches the 10th item from the bottom of the list, the Paging library will silently trigger the network request for the *next* page in the background. By the time the user's thumb actually reaches the bottom, the data is already in Room and rendered, completely eliminating the loading spinner."

## 6. Staff Engineer Thinking: Tradeoffs

1.  **Offset vs Cursor Constraints:** I always advocate for Cursor pagination. However, if the Product Manager says "Users must be able to jump directly to Page 50," Cursor pagination fails (you can only go to the *next* page, you cannot skip). In that specific case, I must fallback to Offset pagination and accept the risk of duplicates, explicitly stating the tradeoff.
2.  **Pull-to-Refresh vs Caching:** If a user pulls to refresh, what happens to the cached data? A naive approach deletes the entire Room table and re-fetches. This causes a massive white flash on the UI. A Staff approach uses a Diffing algorithm (like `RemoteMediator` handling `REFRESH` load types) to upsert the new items at the top of the cache, allowing `DiffUtil` to smoothly animate the new items in without clearing the screen.

## 7. Probing Questions (For Practice)

1.  Explain the fundamental flaw of Offset/Limit pagination in a highly active feed (like Twitter) and how it causes duplicate items on the client.
2.  Describe how Cursor pagination solves the duplication problem using an immutable database pointer.
3.  Why is an Offline-First pagination architecture (using a `RemoteMediator` and a Local Database) superior to paginating directly from the Network?
4.  Explain the concept of "Page Dropping" (`maxSize`) and how it mathematically prevents OutOfMemory (OOM) errors during infinite scrolling.
5.  What is "Prefetch Distance," and how does it create the illusion of an infinitely loading list without loading spinners?
6.  Describe the severe UI bug that occurs if a developer forgets to call `.cachedIn(viewModelScope)` on a `PagingData` Flow and the user rotates their phone.
7.  If a Product Requirement mandates that a user can "Jump directly to Page 100," why must an engineering team abandon Cursor Pagination?
8.  Explain the performance impact of SQLite "Tombstones" when using `OFFSET` queries in a local Room database after thousands of items have been deleted.
9.  How does `DiffUtil` (or Compose's lazy list diffing) work in conjunction with Paging to prevent UI flashes when new data arrives?
10. If the backend API changes the sorting order of the feed (e.g., from Chronological to Algorithmic), how does this break Cursor pagination if the cursor was previously based on a timestamp?

## Further Reading

- [`jank.md`](../android/performance/jank.md) — How massive lists cause UI stuttering if not paginated.
- [`offline-first-app.md`](../reference-architectures/offline-first-app.md) — The reference architecture for the `RemoteMediator` pattern.
- [`memory-management-and-leaks.md`](../android/performance/memory-management-and-leaks.md) — Why holding 10,000 objects in a `List` causes OOMs.
