# Computer Science: Trees (Applied to Mobile)

## The Theory
A Tree is an undirected graph in which any two vertices are connected by exactly one path. It is fundamentally hierarchical data, starting from a single Root node and branching out to Leaf nodes.

## Staff-Level Application in Mobile

### 1. UI Hierarchies (The DOM & View Tree)
Every UI framework on Android (XML `Views` or Jetpack `Compose`) is a Tree.
-   **XML:** The `DecorView` is the root. `LinearLayouts` are branches. `TextViews` are leaves. When the OS needs to draw the screen, it executes a **Depth-First Search (DFS)** traversal (`onMeasure`, `onLayout`, `onDraw`). If your tree is 20 levels deep (nested `LinearLayouts` inside `ConstraintLayouts`), the `O(N)` traversal time exceeds the 16ms frame budget, causing UI Jank.
-   **Compose:** Recomposition optimizes this by mapping the Compose tree to a Slot Table (a flat array). When state changes, Compose can surgically update a leaf node without traversing the entire tree, provided the state is correctly hoisted.

### 2. Merkle Trees (Offline Sync)
When syncing a massive SQLite database between the mobile device and the cloud, transferring all the data is impossible.
We use a **Merkle Tree (Hash Tree)**.
1.  Every row in the local DB is hashed (Leaf nodes).
2.  Pairs of row hashes are combined and hashed together to form parent nodes.
3.  This repeats until a single **Root Hash** is generated for the entire database.
4.  The mobile app sends only the Root Hash to the backend. If it matches the backend's Root Hash, the DBs are identical (`O(1)` sync time).
5.  If they differ, the backend sends its tree down. The client traverses the tree to find exactly which branch differs, narrowing it down to the exact row that needs syncing in `O(log N)` time. (This is how Git works).

### 3. Abstract Syntax Trees (Static Analysis)
When configuring a CI/CD pipeline, a Staff engineer writes custom `Detekt` or `Android Lint` rules.
The compiler parses the Kotlin code into an **Abstract Syntax Tree (AST)**.
To ban a specific function call (e.g., `SharedPreferences.apply()`), you write a Lint rule that visits the nodes of the AST. When it finds a `MethodInvocation` node with the name "apply", it fails the build.

## Common Pitfalls
-   **Deep vs Wide Trees:** In UI development, wide trees (many children under one parent, like `ConstraintLayout`) are significantly cheaper to render than deep trees (deeply nested `LinearLayouts`), because traversal overhead is exponential in Android's measure pass.
-   **Memory Leaks:** If a child node holds a strong reference to its parent node (or the `Activity` context) after the parent has been logically destroyed, the entire tree is kept in memory. This is the root cause of 90% of Android memory leaks.
