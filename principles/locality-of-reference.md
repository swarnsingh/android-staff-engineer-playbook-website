# Principles: Locality of Reference (Spatial & Temporal)

## The Theory
Locality of Reference is a principle originating from CPU cache design, stating that a processor tends to access the same set of memory locations repetitively over a short period.
-   **Temporal Locality:** If a memory location is accessed, it is likely to be accessed again soon.
-   **Spatial Locality:** If a memory location is accessed, memory locations near it are likely to be accessed soon.

In software architecture, we apply this concept to code organization: **Code that changes together, should live together.**

## Staff-Level Application in Mobile

### 1. Package by Feature vs Package by Layer
The most visible application of Spatial Locality in Android is how you organize your packages and modules.
-   **Package by Layer (Low Locality):**
    ```text
    com.company.app
    ├── ui/ (Contains LoginScreen, CheckoutScreen, ProfileScreen)
    ├── viewmodels/ (Contains LoginViewModel, CheckoutViewModel)
    └── data/ (Contains LoginRepository, CheckoutRepository)
    ```
    If you need to build a new feature for the Login flow, you have to jump across three completely different directories. The files related to "Login" are spatially distant.
-   **Package by Feature (High Locality):**
    ```text
    com.company.app
    ├── login/ (Contains LoginScreen, LoginViewModel, LoginRepository)
    ├── checkout/ (Contains CheckoutScreen, CheckoutViewModel, CheckoutRepository)
    ```
    Now, everything related to the Login feature lives in one place. When an engineer works on Login, their cognitive load is localized to a single folder. This is the foundation of modern Android modularization.

### 2. State Locality (Jetpack Compose)
In UI architecture, state should live as close as possible to the component that uses it.
-   **Low Locality (Hoisting too high):** You put a `TextField` input string in a global `AppState` object at the very top of your app architecture, just because you might need it for a final submit button 5 screens later. Every time the user types a character, the entire app state tree recomposes.
-   **High Locality:** The `TextField` state lives exactly inside the local Composable that renders the text field. The state is only hoisted up to the `ViewModel` when the user actually hits "Submit". Keeping state local prevents unnecessary recompositions and memory leaks.

### 3. Temporal Locality in Execution (CPU Cache Misses)
While less common to optimize manually in modern Kotlin, Staff Engineers working on ultra-high-performance SDKs (e.g., video rendering, game engines via NDK) must respect actual CPU memory locality.
-   **The Problem:** Iterating over an `Array<Object>` in Kotlin involves reading memory locations scattered randomly across the heap (because arrays of objects are just arrays of pointers). This causes CPU Cache Misses, which are extremely slow.
-   **The Solution:** Using primitive arrays (`IntArray`, `FloatArray`) or specific flattened data structures where the data is laid out contiguously in physical RAM, maximizing the CPU's Spatial Locality optimizations.

## Common Pitfalls
-   **The "Core" Module Dump:** Creating a `:core` or `:common` module and using it as a dumping ground for any class that is used by more than one feature. This violates Locality of Reference because completely unrelated concepts (e.g., a String formatter and a Network interceptor) are forced to live next to each other. "Core" modules should be strictly partitioned by domain.
