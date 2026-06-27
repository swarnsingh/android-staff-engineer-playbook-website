# Computer Science: System Complexity (Applied to Mobile)

## The Theory
System Complexity (often evaluated via Big O notation or Cyclomatic Complexity) measures how a system's resource consumption (time, memory, or cognitive load) scales as the input size increases.

## Staff-Level Application in Mobile

### 1. Big O on the Main Thread (Time Complexity)
Mobile devices have hard constraints: 16 milliseconds to render a frame (60 FPS), and 5 seconds to respond to user input before an Application Not Responding (ANR) crash is triggered.
-   **O(N^2) Parsing:** A junior engineer writes a nested `forEach` loop to match 10,000 local contacts against 10,000 backend users. `10,000 * 10,000 = 100,000,000` operations. The UI freezes for 3 seconds.
-   **O(N) Optimization:** A Staff engineer converts the backend users into a `HashSet`. They iterate through the 10,000 local contacts once, performing an `O(1)` lookup against the set. `10,000` operations. The UI renders instantly.

### 2. Big O in Memory (Space Complexity)
Mobile devices have limited RAM, and the OS will ruthlessly kill background apps (and your foreground app) if memory pressure is too high.
-   **O(N) Memory Bloat:** An app fetches a list of 5,000 articles from the network and holds the entire JSON array in memory as Kotlin data classes to power a `RecyclerView`. This might consume 50MB of RAM.
-   **O(1) Pagination:** A Staff engineer uses `Paging 3`. The app only holds the 50 articles currently visible (and a small buffer) in RAM. As the user scrolls, old articles are garbage collected, and new ones are loaded from the Room database. The memory footprint remains constant (`O(1)` relative to the total dataset size), regardless of whether there are 5,000 or 5,000,000 articles.

### 3. Cyclomatic Complexity (Cognitive Load)
Cyclomatic Complexity measures the number of linearly independent paths through a program's source code (determined by `if`, `else`, `when`, `for` statements).
-   **The God Class:** A `CheckoutViewModel` with a cyclomatic complexity of 45 is impossible to unit test thoroughly. Every new boolean flag (`isGuest`, `hasDiscount`, `isInternational`) exponentially increases the number of test cases required to prove the code works.
-   **The Fix (Polymorphism & State Machines):** Staff engineers enforce SonarQube or Detekt rules that fail the build if a function's cyclomatic complexity exceeds 10. They refactor complex `if/else` ladders into Polymorphic classes or strict State Machines (MVI), reducing the cognitive load and making the system mathematically verifiable.

## Common Pitfalls
-   **Premature Optimization:** Do not spend 3 days rewriting an `O(N)` algorithm to `O(log N)` if `N` will never exceed 10 (e.g., iterating through a list of a user's 3 credit cards). Optimize for readability first, and only optimize for Big O when profiling (Traceview/Macrobenchmark) proves it is a bottleneck.
-   **Ignoring Hidden Complexity:** Calling `list.contains(item)` inside a `forEach` loop looks like `O(N)` code, but `list.contains()` is an `O(N)` operation itself, meaning the hidden complexity is `O(N^2)`. Always know the algorithmic complexity of the standard library functions you are calling.
