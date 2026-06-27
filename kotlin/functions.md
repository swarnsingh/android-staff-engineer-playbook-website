# Kotlin: Functions (First-Class Citizens)

## The Theory
In Java (prior to Java 8), functions were bound to classes. They were methods. In Kotlin, functions are "First-Class Citizens." This means a function can be stored in a variable, passed as an argument to another function, or returned from another function. This enables Functional Programming (FP) paradigms.

## Staff-Level Application in Mobile

### 1. Higher-Order Functions (Callbacks vs Lambdas)
A Higher-Order Function is a function that takes another function as a parameter.
-   **The Java/Legacy Way (Interfaces):** In Android, click listeners were traditionally implemented using anonymous interface implementations.
    ```kotlin
    button.setOnClickListener(object : View.OnClickListener {
        override fun onClick(v: View) {
            submitData()
        }
    })
    ```
-   **The Kotlin Way (Lambdas):** Because functions can be passed directly, Kotlin eliminates the boilerplate.
    ```kotlin
    button.setOnClickListener { submitData() }
    ```
-   **Architectural Implication:** Jetpack Compose is built entirely on Higher-Order functions. A `Button` composable takes an `onClick: () -> Unit` parameter. State hoisting relies on passing these function references down the UI tree.

### 2. The `inline` Keyword (Performance Tuning)
When you pass a lambda to a Higher-Order function, Kotlin generates a background anonymous class (e.g., `Function1`) and allocates it on the heap. If you do this inside a loop running 10,000 times, you allocate 10,000 objects, triggering the Garbage Collector and causing UI Jank.
-   **The Solution:** The `inline` keyword.
    ```kotlin
    inline fun measureTime(block: () -> Unit) {
        val start = System.currentTimeMillis()
        block()
        println("Time: ${System.currentTimeMillis() - start}")
    }
    ```
-   **Under the Hood:** The compiler literally takes the bytecode of the `block` lambda and pastes it directly into the call site. No anonymous objects are created. Zero memory allocation overhead.
-   **Staff Warning:** Do *not* `inline` massive functions. Because it pastes the bytecode, inlining a 500-line function across 20 different call sites will exponentially bloat the size of your APK (Dalvik Executable size). Only inline small, frequently called utility functions with lambdas.

### 3. Scope Functions (`let`, `apply`, `run`, `with`, `also`)
Scope functions execute a block of code within the context of an object.
-   **`let`:** Used primarily for null-checks and transforming data. `user?.let { db.save(it.id) }`
-   **`apply`:** Used for configuring objects. It returns the object itself.
    ```kotlin
    val intent = Intent().apply {
        action = Intent.ACTION_VIEW
        data = Uri.parse("https://google.com")
    }
    ```
-   **The Danger:** Nesting scope functions (`user.let { it.address?.apply { ... } }`) destroys readability. A Staff Engineer enforces strict Lint rules prohibiting the nesting of scope functions to maintain a readable codebase.

## Common Pitfalls
-   **Crossinline and Noinline:** When writing advanced `inline` functions, you must understand `crossinline` (preventing non-local returns) and `noinline` (when you need to store the lambda in a variable rather than inlining it). Misunderstanding these will lead to obscure compiler errors.
