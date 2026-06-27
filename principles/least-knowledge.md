# Principles: Principle of Least Knowledge (Law of Demeter)

## The Theory
The Principle of Least Knowledge (often formalized as the Law of Demeter) states that a unit of code should only talk to its immediate friends and should have no knowledge of the internal structure of the objects it manipulates.
Informally: **"Don't talk to strangers."**

If object `A` needs something from object `C`, and `A` only knows about `B`, `A` should ask `B` to get the information, rather than `A` reaching through `B` to grab `C`.
```kotlin
// VIOLATION of Least Knowledge
val zipCode = user.address.getZipCode()

// ADHERENCE to Least Knowledge
val zipCode = user.getZipCode() // User class internally delegates to Address
```

## Staff-Level Application in Mobile

### 1. Mitigating the Blast Radius of Refactoring
Why is `user.address.getZipCode()` bad? Because the caller now depends on *two* contracts: the `User` class and the `Address` class.
-   **The Problem:** If the backend team changes the data model so that a user can have *multiple* addresses (e.g., shipping vs billing), the `Address` property on `User` becomes `List<Address>`.
-   **The Blast Radius:** Every single file in the Android app that called `user.address.getZipCode()` is now broken and won't compile. A simple backend change causes a massive client-side refactor.
-   **The Staff Solution:** If you followed the Law of Demeter and exposed `user.getPrimaryZipCode()`, you only have to update the internal implementation of the `User` class. The rest of the app compiles perfectly. You have isolated the change.

### 2. Dependency Injection (DI) and the Service Locator Anti-Pattern
The most common violation of Least Knowledge in Android is the Service Locator pattern (or passing the entire DI graph to a class).
-   **The Violation:**
    ```kotlin
    class CheckoutViewModel(val appContainer: AppContainer) {
        fun checkout() {
            // Reaching into the container to find a stranger
            val api = appContainer.networkModule.paymentApi 
            api.charge()
        }
    }
    ```
    This `ViewModel` knows too much. It knows about the `AppContainer`, it knows the container has a `networkModule`, and it knows the module has a `paymentApi`. This class is impossible to unit test without mocking the entire universe.
-   **The Adherence (Constructor Injection):**
    ```kotlin
    class CheckoutViewModel(val paymentApi: PaymentApi) {
        fun checkout() {
            paymentApi.charge()
        }
    }
    ```
    The `ViewModel` only knows about the exact interface it needs (`PaymentApi`). It is ignorant of how that API was created or where it came from.

### 3. Jetpack Compose: State Hoisting
In declarative UI, the Principle of Least Knowledge manifests as State Hoisting and passing callbacks instead of ViewModels.
-   **The Violation:** Passing a whole `CheckoutViewModel` down 5 layers deep to a `SubmitButton` Composable. The button now "knows" about the entire ViewModel, making the button completely un-reusable in other screens.
-   **The Adherence:** The `SubmitButton` only knows about the raw data it needs to render (`isEnabled: Boolean`), and it receives a callback to execute when clicked (`onClick: () -> Unit`). It has zero knowledge of the ViewModel or the screen's broader architecture.

## Common Pitfalls
-   **The Wrapper Explosion:** A dogmatic adherence to the Law of Demeter can lead to hundreds of meaningless wrapper methods (e.g., adding `user.getStreet()`, `user.getCity()`, `user.getState()`). A Staff Engineer is pragmatic: if `Address` is a stable Value Object that is highly unlikely to change structurally, it is perfectly acceptable to expose it directly (`val address: Address`). The principle is about minimizing risk, not absolute purity.
