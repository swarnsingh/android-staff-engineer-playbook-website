# Factory Pattern

> The Factory pattern encapsulates the instantiation logic of objects. In modern Android, pure dependency injection frameworks (like Hilt and Koin) handle 95% of object creation, effectively acting as massive, automated Abstract Factories. However, a Staff engineer knows exactly when DI falls short and explicit Factories are required: specifically, when objects require **runtime arguments** (like navigation IDs) to be constructed. The canonical Android examples are `ViewModelProvider.Factory` and Hilt's `@AssistedInject`.

---

## Overview

If you sprinkle `new Object()` (or just `Object()` in Kotlin) throughout your business logic, your classes become tightly coupled to concrete implementations, making them impossible to mock during unit testing.

The Factory pattern moves the `new` keyword behind an interface or a dedicated class.

There are three main flavors:
1. **Simple Factory:** A static method or class that returns instances based on a parameter (e.g., `ButtonFactory.create("primary")`).
2. **Factory Method:** A base class defines an abstract method for creation, which subclasses implement (e.g., `Fragment.onCreateView`).
3. **Abstract Factory:** An interface for creating families of related objects (e.g., `DarkThemeUIFactory` vs `LightThemeUIFactory`).

---

## 1. The Core Android Problem: ViewModel Creation

In Android, the OS destroys and recreates `Activities` and `Fragments` constantly (e.g., during screen rotation). 
If you create a `ViewModel` yourself (`val vm = UserViewModel()`), it will be destroyed and recreated on rotation, losing all state.

To survive rotation, the `ViewModel` must be created and cached by the Android system's `ViewModelStore`. But the system doesn't know how to pass dependencies (like a Repository) into your ViewModel's constructor. 

This is the exact problem the **Factory Pattern** solves in Android.

### The Standard `ViewModelProvider.Factory`
```kotlin
// 1. The Concrete Class we want to build
class UserViewModel(
    private val repository: UserRepository,
    private val userId: String // A runtime argument!
) : ViewModel() { ... }

// 2. The Factory
class UserViewModelFactory(
    private val repository: UserRepository,
    private val userId: String
) : ViewModelProvider.Factory {
    
    @Suppress("UNCHECKED_CAST")
    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        if (modelClass.isAssignableFrom(UserViewModel::class.java)) {
            // The Factory encapsulates the 'new' keyword
            return UserViewModel(repository, userId) as T
        }
        throw IllegalArgumentException("Unknown ViewModel class")
    }
}

// 3. Usage in a Fragment
class UserFragment : Fragment() {
    private val viewModel: UserViewModel by viewModels {
        UserViewModelFactory(MyApp.repository, arguments?.getString("user_id")!!)
    }
}
```

---

## 2. Modern Android: Assisted Injection (Dynamic Factories)

Writing manual `ViewModelProvider.Factory` boilerplate for 50 ViewModels is tedious. Modern DI frameworks like Dagger/Hilt automate this. 

But DI frameworks only know about **compile-time** dependencies (like Repositories). They do not know about **runtime** dependencies (like a `userId` clicked in a RecyclerView).

To merge compile-time DI with runtime arguments, we use **Assisted Injection**, which generates a Factory under the hood.

```kotlin
// 1. Mark the ViewModel for Assisted Injection
@HiltViewModel(assistedFactory = UserViewModel.UserViewModelFactory::class)
class UserViewModel @AssistedInject constructor(
    private val repository: UserRepository, // Provided by Hilt DI
    @Assisted private val userId: String    // Provided at runtime by the Factory
) : ViewModel() {

    // 2. Define the Factory Interface (Hilt generates the implementation!)
    @AssistedFactory
    interface UserViewModelFactory {
        fun create(userId: String): UserViewModel
    }
}
```

Usage in Jetpack Compose:
```kotlin
@Composable
fun UserScreen(userId: String) {
    // We use the Hilt generated factory to inject the runtime 'userId'
    val viewModel = hiltViewModel<UserViewModel, UserViewModel.UserViewModelFactory> { factory ->
        factory.create(userId)
    }
}
```
This is the pinnacle of the Factory pattern on Android: the framework generates the Factory boilerplate, cleanly merging static dependencies and dynamic runtime arguments.

---

## 3. The Simple Factory: DTO Parsing and Polymorphism

APIs often return polymorphic JSON arrays (e.g., a social feed containing `ImagePost`, `TextPost`, and `VideoPost`). The UI needs to render different components based on the type.

A Simple Factory handles this instantiation perfectly.

```kotlin
// The Domain Models
sealed interface FeedItem
data class ImageItem(val url: String) : FeedItem
data class TextItem(val text: String) : FeedItem
data class UnknownItem(val type: String) : FeedItem

// The Factory
object FeedItemFactory {
    fun create(json: JsonObject): FeedItem {
        return when (val type = json.getString("type")) {
            "image" -> ImageItem(json.getString("url"))
            "text" -> TextItem(json.getString("text"))
            else -> UnknownItem(type) // Defensive fallback!
        }
    }
}
```
*Note: In modern Android, libraries like Moshi or Kotlinx.Serialization handle this via Polymorphic adapters, which are essentially automated reflection-based Factories.*

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **The God Factory** | A single `ObjectFactory` class that knows how to instantiate every object in the app, becoming a 5,000-line bottleneck. | Group factories by feature or domain (e.g., `BillingFactory`, `AuthFactory`). Or better, use a DI framework (Hilt/Koin). |
| **Factory Passing (Service Locator Anti-Pattern)** | Passing a Factory object deep down the call stack just in case a leaf node needs to instantiate something. | Use Dependency Injection to provide fully constructed objects to the leaf nodes, rather than passing the means of construction. |
| **Leaking Android Context** | A singleton Factory requires a `Context` to create objects, and holds a strong reference to an `Activity`. | If a Factory needs Context, inject the `ApplicationContext`, never an `Activity` context, to prevent memory leaks. |

---

## 5. Common Pitfalls

### Pitfall 1: Over-Engineering with Abstract Factories
Creating an `AbstractWidgetFactory` interface with `AndroidWidgetFactory` and `IosWidgetFactory` implementations inside a pure Android app "just in case we need it."
*Fix:* YAGNI (You Aren't Gonna Need It). If you aren't currently building a cross-platform system, use a Simple Factory or direct DI. Only introduce Abstract Factories when you have multiple *active* variants of a product family.

### Pitfall 2: Static Factory Methods hiding I/O
```kotlin
class ConfigManager private constructor(val config: Config) {
    companion object {
        // BAD: Factory method does disk I/O!
        fun create(context: Context): ConfigManager {
            val json = File(context.filesDir, "config.json").readText()
            return ConfigManager(parse(json))
        }
    }
}
```
If you call `ConfigManager.create()` on the Main Thread, the app crashes with an ANR (Application Not Responding). 
*Fix:* Factory methods should be fast, CPU-only instantiations. I/O should be handled asynchronously and passed into the constructor/factory.

---

## Probing Questions

1.  **DI vs Factory:** What is the specific architectural threshold where you stop using Dagger/Hilt to provide an object and start writing a custom Factory? (Hint: Think about object lifecycles and runtime data).
2.  **FragmentFactory:** Historically, Fragments had to have an empty, no-argument constructor so the OS could recreate them. In modern Android, we have `FragmentFactory`. How does `FragmentFactory` work, and how does it allow Constructor Injection for Fragments?
3.  **AssistedInject Internals:** Under the hood, Hilt generates a class when you use `@AssistedInject`. What does the constructor of that generated Factory class look like, and how does it get the non-assisted dependencies (like the Repository)?
4.  **Testing:** You have a class that needs to create 10 `NetworkRequest` objects in a `while` loop based on user input. Should you inject the 10 objects (DI), or inject a `NetworkRequestFactory`? How does this choice impact your ability to write unit tests for the loop?
5.  **Companion Objects:** Kotlin does not have `static` methods. Instead, we use `companion object { fun create(): MyClass }`. Is a companion object a Simple Factory? What are the memory and inheritance tradeoffs of using `companion object` compared to a dedicated `MyClassFactory` interface?

## Answer Key

1. **DI vs Factory:**
   Dagger/Hilt handles compile-time dependencies. A custom Factory is required when object instantiation depends on runtime arguments (like navigation IDs or user input) that DI frameworks cannot know about during compilation.
2. **FragmentFactory:**
   `FragmentFactory` hooks into the FragmentManager's instantiation process. Instead of reflection on a no-arg constructor, it calls `instantiate(classLoader, className)`, allowing you to provide a custom factory that passes constructor arguments (like Repositories) into your Fragments.
3. **AssistedInject Internals:**
   The generated Factory class receives the compile-time dependencies in its constructor via standard injection. Its `create()` method takes the runtime arguments (the `@Assisted` parameters) and combines both to instantiate the target ViewModel.
4. **Testing:**
   You should inject a `NetworkRequestFactory`. If you inject 10 objects directly, the loop is hard-coded to a limit. Injecting a Factory allows the loop to instantiate an arbitrary number of requests dynamically, and during testing, you can mock the Factory to return mock requests.
5. **Companion Objects:**
   A `companion object` can function as a Simple Factory. However, unlike a dedicated Factory interface, it cannot be easily mocked or substituted via polymorphism for testing, and it couples the instantiation logic directly to the class definition.

## Further Reading

- [`../android/data-and-di/dependency-injection.md`](../android/data-and-di/dependency-injection.md) — How DI frameworks act as the ultimate application-wide factory.
- [`../android/architecture/viewmodel.md`](../android/architecture/viewmodel.md) — Deep dive into the ViewModel lifecycle and why the Factory is strictly required.
- [`builder.md`](builder.md) — Contrast the Factory (which returns polymorphic types) with the Builder (which constructs complex configurations of a single type).
