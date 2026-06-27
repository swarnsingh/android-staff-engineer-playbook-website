# System Design: Search (Typeahead / Autocomplete)

## The Prompt

*"Design the Global Search feature for a massive E-Commerce app (like Amazon). As the user types into the search bar, the app must show instant autocomplete suggestions ('lap' -> 'laptop', 'lapel pin'). The results must be lightning-fast, and the app must not accidentally DDoS the backend or show stale data."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Typeahead / Autocomplete: Show suggestions *while* the user types.
- Full Search: Show the actual product list when the user hits 'Enter'.
- Offline Support: Minimal (can show recent searches), but real search requires a network.

### Non-Functional Requirements (NFRs)
- **Latency (Priority 0):** Autocomplete suggestions must appear in < 100ms. If it takes 1 second, the user will have already finished typing the word.
- **Server Load (Priority 1):** We cannot fire an HTTP request for every single keystroke of 100 million users. The backend API Gateway will melt.
- **Data Consistency (Race Conditions):** If I type 'S' (Request A) and then 'H' (Request B), Request B might return from the server *before* Request A. The UI must not show results for 'S' after the user has typed 'SH'.

## 2. High-Level Architecture

The Search architecture is an exercise in **Stream Throttling**. The user's keystrokes are a hyper-fast stream of data that must be filtered and delayed before hitting the network.

```mermaid
graph TD
    Input[Search EditText] -->|Keystroke Stream| VM[ViewModel]
    
    subgraph Stream Processing (Coroutines/Flow)
        VM -->|Debounce (300ms)| Debouncer
        Debouncer -->|Filter Empty| Filter
        Filter -->|Distinct Until Changed| Distinct
    end
    
    Distinct -->|Cleaned Query| Network[Search API]
    Network -->|Results| VM
    
    subgraph Backend
        Network --> Redis[(Redis Cache)]
        Redis -- Miss --> ElasticSearch[(ElasticSearch Index)]
    end
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Debouncing (Protecting the Server)
*Interviewer:* "A user types 'M', 'A', 'C'. They type 3 keys in 100 milliseconds. Your app fires 3 HTTP requests: `/search?q=m`, `/search?q=ma`, `/search?q=mac`. You just tripled your AWS bill. Fix it."

**Staff Answer:**
"I will apply a **Debounce** operator to the keystroke stream using Kotlin Flows.
```kotlin
val searchQuery = MutableStateFlow("")

searchQuery
    .debounce(300L) // Wait 300ms after the LAST keystroke before continuing
    .filter { it.isNotBlank() } // Don't search for empty strings
    .distinctUntilChanged() // If user types 'A', deletes it, types 'A' within 300ms, ignore it
    .flatMapLatest { query -> 
        api.search(query) // Fire network request
    }
```
If the user types 'M', 'A', 'C' rapidly, the 300ms timer resets on every key. The app only fires ONE network request for 'mac' after the user pauses typing for 300ms. This reduces server load by 80%."

### Flow 2: The Race Condition (`flatMapLatest`)
*Interviewer:* "The user types 'P'. Request A is sent. It hits a slow backend pod and takes 2 seconds. The user types 'I' (forming 'PI'). Request B is sent. It hits a fast pod and takes 50ms. Request B returns, showing 'Pizza'. Then Request A returns, overwriting the UI with 'Pants'. The user searched for 'PI' but sees results for 'P'. Fix it."

**Staff Answer:**
"This is a classic Out-Of-Order execution bug. 
In RxJava, we solve this with `switchMap`. In Kotlin Coroutines, we use **`flatMapLatest`**.
When the user types 'PI' and Request B is initiated, `flatMapLatest` instantly **cancels** the ongoing Coroutine Job for Request A. The `OkHttp` socket for Request A is severed. Request A's results will never reach the UI. The UI is guaranteed to only show the results of the most recent query."

### Flow 3: The Caching Layer (Latency)
*Interviewer:* "Even with Debounce, the API takes 200ms. We want it faster. Users often search for the same things. How do we drop latency to 0ms?"

**Staff Answer:**
"We implement an aggressive, short-lived **L1 Memory Cache** on the device.
When the user searches for 'mac', we save the JSON response in a local `LruCache<String, List<Result>>` (Key: 'mac').
If the user deletes a letter (backspaces to 'ma') and then types 'c' again (forming 'mac'), the `ViewModel` checks the LruCache first. It finds 'mac', completely skips the network request, and updates the UI in 0 milliseconds."

## 4. The Backend Constraint (Why ElasticSearch?)

A Staff Mobile Engineer must understand *why* the backend is built a certain way to design the mobile client correctly.

If the backend team tries to implement Global Search using a standard SQL database (`SELECT * FROM products WHERE name LIKE '%mac%'`), the query will take 5 seconds on a 10-million row table. `LIKE` queries cannot use standard B-Tree indexes effectively.

The backend MUST use an Inverted Index engine like **ElasticSearch** or **Apache Solr**. These engines break words into tokens and map them instantly to document IDs, providing <20ms search times. The mobile engineer should explicitly confirm with the interviewer that the backend is using a proper search engine, otherwise, the 100ms latency NFR is impossible.

## 5. Failure Modes & Bottlenecks

### Bottleneck: Keyboard Thrashing
*Interviewer:* "The user taps the search bar. The keyboard slides up. The `RecyclerView` is resized. The UI stutters massively. Why?"

**Staff Answer:**
"Keyboard animations are notoriously heavy in Android. If the `RecyclerView` is recalculating its layout while the keyboard is animating up, you drop frames.
**The Fix:** I will use `WindowInsetsCompat` to detect the keyboard animation. I will defer any heavy UI updates (like rendering the search history list) until *after* the keyboard animation completes, ensuring 60fps smoothness."

### Bottleneck: Stale Cache Data
*Interviewer:* "You cached 'macbook' in your `LruCache`. The price is $1000. Tomorrow, the price drops to $900. The user searches 'macbook' again and sees $1000. They buy it, and are charged $900. They are confused."

**Staff Answer:**
"Typeahead/Autocomplete results should strictly be for *Navigation*, not for *Transaction*. The autocomplete JSON payload should only contain the `id`, `name`, and an `icon`. It should NOT contain volatile data like `price` or `inventory_count`. 
When the user clicks the autocomplete suggestion, it navigates to the Product Detail Screen, which makes a fresh, un-cached `GET /products/{id}` request to fetch the real-time price."

## 6. Probing Questions (For Practice)

1.  Explain why firing an HTTP request for every single keystroke is considered a catastrophic failure in System Design for a massive application.
2.  Describe how the `debounce` operator works mathematically, and why 300ms is a common standard for human typing speeds.
3.  Walk through the Race Condition where an older network request returns *after* a newer network request. How does `flatMapLatest` (or `switchMap`) permanently prevent this?
4.  Why is an LruCache (Memory Cache) appropriate for caching search results during a single app session, rather than a SQLite database (Disk Cache)?
5.  Explain the architectural difference between a standard SQL database (using `LIKE '%query%'`) and an Inverted Index (like ElasticSearch) regarding search latency.
6.  Describe the "Stale Cache" problem. Why must the JSON payload for Autocomplete suggestions exclude highly volatile data like Prices or Inventory counts?
7.  How does the `distinctUntilChanged` operator protect the network if a user rapidly types a character and then immediately deletes it?
8.  Why is the Android Soft Keyboard animation a major source of UI Jank on search screens, and how do you mitigate it?
9.  Explain the tradeoff between a short Debounce time (e.g., 50ms) and a long Debounce time (e.g., 600ms) regarding User Experience vs Server Load.
10. If an application requires offline search capabilities (e.g., a dictionary app), how does the architecture shift from querying a backend ElasticSearch to querying a local device database?

## Further Reading

- [`flow.md`](../android/architecture/flow.md) — The deep dive into Kotlin Flow operators like `debounce` and `flatMapLatest`.
- [`jank.md`](../android/performance/jank.md) — How the keyboard animation causes dropped frames.
- [`caching.md`](../engineering-fundamentals/caching.md) — The fundamental rules of LruCache implementation.
