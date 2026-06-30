# Adapter Pattern

> The Adapter pattern converts the interface of a class into another interface the clients expect. In Android, the most famous (and misunderstood) implementation is the `RecyclerView.Adapter`. A Staff engineer understands that the Adapter pattern isn't just a UI concept—it is the architectural boundary that protects your core domain logic from third-party SDKs, legacy APIs, and system frameworks. Whether adapting a JSON payload to a UI state, or adapting a legacy XML layout to Jetpack Compose, the Adapter pattern is the ultimate anti-corruption layer.

---

## Overview

When you have two incompatible interfaces that need to work together, you build an adapter. You don't rewrite the core library to match the client, and you don't rewrite the client to match the library. You put a middleman in between.

In Android, this happens in two main forms:
1. **Structural Adapters:** Bridging domain models to UI frameworks (e.g., `RecyclerView.Adapter`).
2. **Architectural Adapters (Ports & Adapters):** Shielding the domain from external dependencies (e.g., bridging a third-party Analytics SDK to an internal `AnalyticsLogger` interface).

---

## 1. The Core Android Implementation: RecyclerView.Adapter

The `RecyclerView` is an incredibly complex UI component that knows how to recycle memory, calculate layout passes, and animate scrolling. But it knows *nothing* about your business logic. 

The `RecyclerView.Adapter` is a literal implementation of the Gang of Four pattern. It adapts your `List<User>` (the Adaptee) into `ViewHolders` (the Target Interface) that the `RecyclerView` (the Client) understands.

```kotlin
// The Domain Model (Adaptee)
data class User(val id: String, val name: String, val avatarUrl: String)

// The Adapter
class UserAdapter : ListAdapter<User, UserAdapter.UserViewHolder>(UserDiffCallback()) {

    // Target Interface: Creating the View
    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): UserViewHolder {
        val binding = ItemUserBinding.inflate(LayoutInflater.from(parent.context), parent, false)
        return UserViewHolder(binding)
    }

    // Target Interface: Binding the Data
    override fun onBindViewHolder(holder: UserViewHolder, position: Int) {
        val user = getItem(position)
        holder.bind(user) // Adapting domain data to the UI widgets
    }

    class UserViewHolder(private val binding: ItemUserBinding) : RecyclerView.ViewHolder(binding.root) {
        fun bind(user: User) {
            binding.userName.text = user.name
            binding.userAvatar.load(user.avatarUrl)
        }
    }
}
```

### The Compose Revolution
Jetpack Compose effectively eliminates the `RecyclerView.Adapter` class, replacing it with the `items()` DSL in `LazyColumn`. However, the *concept* of adapting domain data to UI remains—it's just done functionally.

```kotlin
LazyColumn {
    // The "Adapter" is now just a mapping function
    items(users, key = { it.id }) { user ->
        UserRow(user)
    }
}
```

---

## 2. Architectural Adapters: The Anti-Corruption Layer

A Staff engineer uses Adapters to build **Anti-Corruption Layers**. If your company decides to switch from Mixpanel to Firebase Analytics, you should not have to rewrite 500 ViewModels.

**Bad Approach (Tight Coupling):**
```kotlin
class CheckoutViewModel {
    fun onCheckoutComplete(cartTotal: Double) {
        // Tied directly to a 3rd party SDK
        FirebaseAnalytics.getInstance(context).logEvent("checkout", bundleOf("total" to cartTotal))
    }
}
```

**Good Approach (The Adapter Pattern):**

1. Define the interface your app *wants* (The Target).
```kotlin
interface AnalyticsTracker {
    fun trackEvent(eventName: String, properties: Map<String, Any>)
}
```

2. Build the Adapter.
```kotlin
class FirebaseAnalyticsAdapter(
    private val firebaseAnalytics: FirebaseAnalytics
) : AnalyticsTracker {
    
    override fun trackEvent(eventName: String, properties: Map<String, Any>) {
        // Adapt the generic map to the specific Bundle Firebase expects
        val bundle = Bundle().apply {
            properties.forEach { (key, value) ->
                when (value) {
                    is String -> putString(key, value)
                    is Int -> putInt(key, value)
                    is Double -> putDouble(key, value)
                }
            }
        }
        firebaseAnalytics.logEvent(eventName, bundle)
    }
}
```

3. Inject the interface into your ViewModel.
```kotlin
class CheckoutViewModel(private val tracker: AnalyticsTracker) {
    fun onCheckoutComplete(cartTotal: Double) {
        tracker.trackEvent("checkout", mapOf("total" to cartTotal))
    }
}
```
If you ever switch to Mixpanel, you write a `MixpanelAdapter`, swap it in your DI module, and zero ViewModels change.

---

## 3. UI Framework Adapters (Interop)

When migrating a massive app to Jetpack Compose, you cannot rewrite everything at once. You must adapt existing XML Views into Compose, and Compose into existing XML Views. Google provides official Adapters for this.

**Adapting XML to Compose (`AndroidView`):**
```kotlin
@Composable
fun MapScreen() {
    // AndroidView is an Adapter bridging the legacy View system to Compose
    AndroidView(
        factory = { context ->
            MapView(context).apply {
                // Initialize map
            }
        },
        update = { mapView ->
            // Update map when Compose state changes
        }
    )
}
```

**Adapting Compose to XML (`ComposeView`):**
```xml
<!-- In your legacy XML layout -->
<androidx.compose.ui.platform.ComposeView
    android:id="@+id/compose_container"
    android:layout_width="match_parent"
    android:layout_height="wrap_content" />
```
```kotlin
// In your Fragment
binding.composeContainer.setContent {
    MyModernComposable()
}
```

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The Fat Adapter** | Putting business logic (API calls, complex calculations) inside a `RecyclerView.Adapter`. | The Adapter should only format and bind data. Pass click events up to the ViewModel via callbacks/lambdas. |
| **Leaking Implementations** | An architectural Adapter throws an SDK-specific exception (e.g., `FirebaseNetworkException`), forcing the client to catch the specific exception. | The Adapter must catch third-party exceptions and map them to domain-specific exceptions (e.g., `AnalyticsException`). |
| **Performance Overhead** | Creating a new Adapter object for every list item, or doing heavy formatting inside `onBindViewHolder`. | Pre-format data in the ViewModel before passing it to the adapter. Adapters should be O(1) assignment operations. |

---

## 5. Common Pitfalls

### Pitfall 1: Adapting Two-Way Binding
When bridging an old UI component that relies on mutable two-way binding (like an `EditText` with a `TextWatcher`) to a modern Unidirectional Data Flow architecture, the Adapter can easily cause infinite loops. The user types -> UI sends event to ViewModel -> ViewModel updates State -> State pushes back to UI -> UI updates `EditText` -> `TextWatcher` fires again.
*Fix:* The Adapter must check for equality before applying state. `if (editText.text.toString() != newState) editText.setText(newState)`.

### Pitfall 2: Using the Wrong Adapter Type
Writing a custom `RecyclerView.Adapter` and calling `notifyDataSetChanged()` when the list changes. This causes the entire list to re-render, destroying animations and killing scroll performance.
*Fix:* Always use `ListAdapter` with `DiffUtil`. `ListAdapter` acts as a specialized adapter that calculates differences on a background thread and dispatches precise update events (`notifyItemInserted`, etc.).

---

## Probing Questions

1.  **DiffUtil Mechanics:** In a `ListAdapter`, `DiffUtil.ItemCallback` requires you to implement `areItemsTheSame` and `areContentsTheSame`. What is the specific architectural distinction between these two methods, and what happens to the RecyclerView if you implement them incorrectly?
2.  **Compose Under the Hood:** The `AndroidView` composable acts as an adapter. How does it handle the Android View lifecycle (e.g., attachment to the window) within the Compose composition lifecycle?
3.  **Ports & Adapters (Hexagonal):** In the Hexagonal Architecture pattern, what is the difference between a "Driving" adapter (e.g., a REST controller or UI) and a "Driven" adapter (e.g., a database implementation)?
4.  **Memory Leaks:** If you pass an `Activity` reference into a `RecyclerView.Adapter` to handle click events, you risk a memory leak if the Adapter outlives the Activity. How do you safely route click events from an Adapter back to the UI controller without leaking context?
5.  **Multiplatform:** You are building a Kotlin Multiplatform app. You have a `commonMain` interface `PlatformLogger`. You write an `IosLoggerAdapter` and an `AndroidLoggerAdapter`. Where and how are these adapters injected into the shared code graph?

## Further Reading

- [`../android/architecture/modularization-strategies.md`](../android/architecture/modularization-strategies.md) — How architectural adapters enable swapping modules.
- [`../android/compose/compose-runtime.md`](../android/compose/compose-runtime.md) — How Compose replaces traditional UI adapters with pure functions.
- [`factory.md`](factory.md) — Creating instances of adapters dynamically based on configuration.
