# Computer Science: Graphs (Applied to Mobile)

## The Theory
A Graph is a set of nodes (vertices) connected by links (edges). Unlike a Tree, a Graph can have cycles (A connects to B, B connects to C, C connects to A). Graphs can be directed (A -> B) or undirected (A <-> B).

## Staff-Level Application in Mobile

### 1. The Build System (DAGs)
The most important graph in Android development is the **Directed Acyclic Graph (DAG)**.
-   **Gradle:** When you hit "Build", Gradle parses your 50 modules. Module A depends on B. B depends on C and D. Gradle constructs a DAG. Because it is *acyclic* (no circular dependencies allowed), Gradle can perform a **Topological Sort** to figure out the exact order in which to compile modules. Furthermore, it analyzes the branches of the DAG to determine which modules can be compiled in parallel.
-   **Dagger/Hilt:** Dependency Injection frameworks parse your `@Inject` annotations and build a massive DAG of your object factory requirements at compile time.

### 2. Navigation Graphs
Jetpack Navigation explicitly models your app's screens as a Graph. 
-   The screens are Nodes.
-   The Actions (`navigate(R.id.action_A_to_B)`) are directed Edges.
Understanding the Navigation Graph prevents back-stack corruption (e.g., handling cyclical flows like A -> B -> C -> A without creating infinite memory stacks by using `popUpTo`).

### 3. Routing (Dijkstra's / A* Algorithms)
In Ride-Hailing or Map applications, the road network is a weighted, directed graph.
When a user requests a ride, the mobile app does not usually run Dijkstra's algorithm (it's too CPU intensive for a massive city grid). Instead, the server runs it and returns the polyline.
However, in **Offline-First Mapping** scenarios (where the user has downloaded a region), the mobile client *must* execute A* Search locally to find the shortest path between the GPS node and the Destination node based on road weights (speed limits, distance).

## Common Pitfalls
-   **Circular Dependencies (The Cycle):** The most catastrophic failure in a DAG architecture. If Module A depends on Module B, and someone accidentally makes Module B depend on Module A, the graph becomes cyclic. Gradle will instantly fail the build, because it is mathematically impossible to resolve a compilation order.
-   **Graph Depth vs Memory:** In Dependency Injection, extremely deep graphs (an object that requires 50 layers of nested dependencies to instantiate) dramatically slow down the app startup time on the Main Thread. Staff engineers use `@Lazy` or `@Provider` to defer the instantiation of heavy branches of the DI graph until they are actually needed.
