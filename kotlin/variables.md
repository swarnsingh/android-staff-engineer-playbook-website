# Kotlin: Variables (Immutability & State)

## The Theory
In Kotlin, variables are strictly differentiated between mutable (`var`) and read-only (`val`). This seemingly simple syntactic choice is the foundation of Kotlin's functional programming paradigm and its safety guarantees regarding concurrent state.

## Staff-Level Application in Mobile

### 1. `val` is Read-Only, not Immutable
A critical distinction that trips up mid-level engineers: `val` does *not* mean immutable. It means the reference cannot be reassigned.
```kotlin
// The reference 'list' cannot point to a new list object.
val list = mutableListOf(1, 2, 3)

// But the underlying data structure IS mutable.
list.add(4) // This compiles and mutates the state.
```
-   **The Staff Implication:** To achieve true immutability (which is required for safe Coroutine execution across multiple threads), you must use read-only references pointing to immutable data structures (e.g., `val list = listOf(1, 2, 3)`).

### 2. Backing Properties (The State Hoisting Pattern)
When exposing state from a ViewModel to a Compose UI, you must prevent the UI from mutating the state directly.
-   **The Pattern:** You use a private mutable variable (the backing property) and expose a public read-only variable.
```kotlin
class LoginViewModel : ViewModel() {
    // Private Mutable State (Only the ViewModel can modify this)
    private val _uiState = MutableStateFlow<LoginState>(LoginState.Loading)
    
    // Public Read-Only State (The UI observes this, but cannot call .value = x)
    val uiState: StateFlow<LoginState> = _uiState.asStateFlow()
}
```
This strictly enforces the Unidirectional Data Flow (UDF) architecture.

### 3. `lateinit var` vs `lazy`
Both defer initialization, but they have entirely different performance and safety profiles.
-   **`lateinit var`:** A promise to the compiler that you will initialize the variable later (usually in an Android lifecycle method like `onCreate`). 
    -   *Danger:* If you access it before initialization, the app crashes with an `UninitializedPropertyAccessException`. It also forces the variable to be a mutable `var`.
-   **`val x by lazy { ... }`:** Thread-safe (by default), deferred initialization. The code block is executed only the first time `x` is accessed.
    -   *Staff Application:* Use `lazy` for heavy objects (like Database initializations or parsing large JSON files) that might not be needed immediately on app startup. This shaves milliseconds off the Main Thread startup time.

## Common Pitfalls
-   **Leaking Mutability:**
    ```kotlin
    class UserProfile {
        val permissions: MutableList<String> = mutableListOf("READ")
    }
    ```
    Even though `permissions` is a `val`, any class that has a reference to `UserProfile` can call `profile.permissions.add("ADMIN")`. You have leaked mutability and destroyed the integrity of your domain model. Always expose `List`, not `MutableList`.
