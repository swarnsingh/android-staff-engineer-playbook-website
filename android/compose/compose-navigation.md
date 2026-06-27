# Compose Navigation

## Overview

In Jetpack Compose, the concept of "Navigation" has been completely rewritten. We no longer navigate between physical `Activity` or `Fragment` classes. We navigate between **pure Kotlin functions**.

A Staff Engineer understands that Navigation in Compose is ultimately just State Management. The screen the user sees is simply a reflection of a `String` (the route) stored in a Back Stack. However, building a robust, type-safe navigation graph that supports deep linking, argument passing, and nested graphs requires deep architectural rigor to avoid the notorious "String Parsing" trap that plagued early versions of Compose Navigation.

## Why It Matters

In the legacy XML system, navigating to a new screen meant executing an `Intent` or a `FragmentTransaction`. The OS handled the Back Stack natively. Arguments were passed using a `Bundle` (a key-value map). If you tried to extract an `Int` but the previous screen passed a `String`, the app crashed at runtime.

Compose Navigation initially tried to emulate web development. You navigated to `"profile/123"`. This meant developers were manually concatenating strings and parsing them back out. It was incredibly brittle.

Modern Compose Navigation (built upon Jetpack Navigation 2.8+) introduced **Type-Safe Navigation** using Kotlin Serialization. Instead of navigating to a string, you navigate to a strongly-typed Kotlin Data Class or Object. This guarantees compile-time safety across the entire application graph.

## Historical Context

- **Pre-2018 (Intents/Fragments):** Complete chaos. Developers wrote manual `FragmentManager` transactions. Process Death resulted in massive bugs because the Fragment back stack was difficult to serialize properly.
- **Navigation Component (XML Era):** Google released the Jetpack Navigation component with a visual graph editor (`nav_graph.xml`). It generated SafeArgs classes, providing excellent type safety.
- **Compose Navigation v1 (String Routes):** Google threw away the XML graph and moved to a pure Kotlin DSL. However, they abandoned SafeArgs. Navigation became string-based (`navController.navigate("details/${userId}")`). The community hated it.
- **Compose Navigation v2.8+ (Type-Safe):** Google fixed the problem by integrating `kotlinx.serialization`. We are back to complete compile-time safety, but entirely in pure Kotlin without XML.

## First Principles

1.  **`NavController`:** The central API. It tracks the back stack, manages the state of the current route, and executes the navigation commands.
2.  **`NavHost`:** The physical container in your UI. It acts as a window that swaps out the `@Composable` functions based on the current state of the `NavController`.
3.  **The Graph (DSL):** A lambda block passed to the `NavHost` where you define every possible screen and how they connect.
4.  **Route (Serializable):** A Kotlin `data class` or `object` that uniquely identifies a destination and holds any arguments required by that destination.

## Mental Model

Think of Compose Navigation as a **Television Set**.
- The **`NavHost`** is the physical TV screen on your wall.
- The **Graph** is the Channel Guide (Channel 1 is News, Channel 2 is Sports).
- The **`NavController`** is the Remote Control.
- The **Route** is the specific Channel Number you punch into the remote.

When you punch a new channel into the remote (`navController.navigate(SportsChannel(gameId = 5))`), the TV screen (`NavHost`) instantly swaps the picture from the News Composable to the Sports Composable. 

## Internal Mechanics

### 1. Defining the Routes (Type Safety)

You define your entire application map using standard Kotlin classes annotated with `@Serializable`.

```kotlin
// A screen with no arguments
@Serializable
object Home

// A screen that requires an ID
@Serializable
data class Profile(val userId: String)

// A screen with optional arguments
@Serializable
data class Search(val query: String? = null)
```

### 2. Building the Graph

In your `MainActivity` (or top-level App Composable), you create the `NavController` and bind it to the `NavHost`.

```kotlin
@Composable
fun MyApp() {
    // 1. Create the Remote Control
    val navController = rememberNavController()

    // 2. Create the TV Screen and hand it the Remote Control
    NavHost(
        navController = navController,
        startDestination = Home // The initial channel
    ) {
        // 3. Define the Channel Guide
        composable<Home> { 
            HomeScreen(
                onNavigateToProfile = { id -> 
                    // Type-Safe Navigation!
                    navController.navigate(Profile(userId = id)) 
                }
            ) 
        }

        composable<Profile> { backStackEntry ->
            // 4. Extract the arguments type-safely!
            val profileRoute: Profile = backStackEntry.toRoute()
            ProfileScreen(userId = profileRoute.userId)
        }
    }
}
```

## Architecture

```mermaid
graph TD
    subgraph Routes
        R1[object Home]
        R2[data class Profile]
    end
    
    subgraph Navigation Layer
        NC[NavController]
        NH[NavHost]
    end
    
    subgraph UI Layer
        HomeScrn[Home Composable]
        ProfScrn[Profile Composable]
    end
    
    R1 -.-> NH
    R2 -.-> NH
    
    HomeScrn -->|navController.navigate(Profile)| NC
    NC -->|Swaps Content| NH
    NH -->|Renders| ProfScrn
```

## Production Example

**Nested Graphs and Bottom Navigation**

A Staff Engineer architects large applications using Nested Graphs. If your app has a Bottom Navigation Bar with 3 tabs (Home, Search, Settings), and the "Home" tab has a deep flow of 5 screens, those 5 screens belong in a Nested Graph.

```kotlin
// The Route for the entire nested graph
@Serializable
object HomeGraph

@Composable
fun MainGraph(navController: NavHostController) {
    NavHost(navController, startDestination = HomeGraph) {
        
        // NESTED GRAPH
        navigation<HomeGraph>(startDestination = HomeFeed) {
            composable<HomeFeed> { FeedScreen(...) }
            composable<ArticleDetails> { ArticleScreen(...) }
            composable<AuthorProfile> { AuthorScreen(...) }
        }
        
        // OTHER TABS
        composable<SearchTab> { SearchScreen(...) }
        composable<SettingsTab> { SettingsScreen(...) }
    }
}
```

## Tradeoffs

**Single Activity vs Multiple Activities**

- **Single Activity (The Compose Way):**
    - *Pros:* Phenomenally fast navigation (no OS-level window transitions). Shared elements (like a music player bar) persist seamlessly across all screens.
    - *Cons:* The entire app runs in a single process context. If a deep screen consumes too much memory, the OS kills the *entire* app, not just that specific screen.
- **Multiple Activities (The Legacy Way):**
    - *Pros:* Each Activity acts as a physical boundary. If you launch a camera Activity, the OS can destroy the underlying MainActivity to free up RAM, and restore it perfectly later.
    - *Cons:* Extremely slow visual transitions. Passing massive data objects between Activities via Intents is dangerous and prone to `TransactionTooLargeException`.

*Staff Note:* Jetpack Compose demands a Single-Activity Architecture. You should only spin up a secondary `Activity` if you are interacting with external apps (like launching the system Camera, or handling an external Share Intent).

## Failure Modes

- **The `ViewModel` Lifecycle Trap:**
  ```kotlin
  composable<Profile> {
      // BAD: If Profile navigates to Details, and then Back to Profile, 
      // this ViewModel is kept alive in memory the entire time!
      val viewModel = hiltViewModel<ProfileViewModel>() 
  }
  ```
  If you use `hiltViewModel()` inside a `NavHost` composable block, the ViewModel is scoped to the `NavBackStackEntry`. It will survive as long as that screen is anywhere in the back stack.
  *(Fix: This is actually the intended behavior, but developers often mistake it for "Activity Scoped". If you need a ViewModel to be shared across 5 screens in a nested graph, you must extract the `NavBackStackEntry` of the parent `navigation` graph and scope the ViewModel to that specific parent entry).*
- **Passing Massive Objects:**
  ```kotlin
  @Serializable
  data class Details(val user: User) // User contains 5MB of high-res image data
  ```
  If you pass a massive data class as a navigation argument, Compose Serialization will serialize the entire 5MB object into a String and push it into the OS Back Stack. The app will crash with an Intent size limit exception.
  *(Fix: Navigation arguments should strictly be IDs (`val userId: String`). The destination screen's ViewModel uses that ID to fetch the full object from a Local Database [Room] or the Network).*
- **The "Pop Up To" Back Stack Explosion:**
  If a user logs out of the app, you navigate them to the `LoginScreen`. If you don't clear the back stack, pressing the Android Back Button on the Login Screen will take them back into the app!
  *(Fix: Use `popUpTo(0) { inclusive = true }` to mathematically obliterate the entire back stack during critical transitions like Log In / Log Out).*

## Staff Engineer Thinking

When reviewing Navigation code, a Staff engineer focuses on State Hoisting and Decoupling.

1.  **No `NavController` in the UI:** I actively reject PRs where a developer passes `NavController` deep into the UI tree (`fun ProfileScreen(navController: NavController)`). This makes the `ProfileScreen` impossible to preview via `@Preview`, impossible to unit test without mocking the entire navigation framework, and locks the screen to that specific navigation implementation.
2.  **Event Callbacks:** I enforce that Screens only emit events. `fun ProfileScreen(onNavigateToSettings: () -> Unit)`. The top-level `NavHost` handles the actual `navController.navigate()` call. This perfectly decouples the UI from the Routing logic.
3.  **Deep Linking:** I ensure every major route in the app is annotated with a `deepLinks` parameter. If Marketing wants to send out a push notification or an email blast linking to a specific product sale, the `NavHost` must be able to intercept the URL and instantly jump to that specific nested `@Composable` with the back stack correctly synthesized.

## Common Misconceptions

- **"Compose Navigation is slower than Fragment Navigation."** False. It is significantly faster. Fragments required the Android `FragmentManager` to execute massive reflection-based transaction commits on the Main Thread. Compose Navigation simply swaps a boolean flag in a state variable, causing an instant recomposition of the UI tree.
- **"I don't need Compose Navigation, I can just use a simple `if/else` block."** You can use `if (currentScreen == "Home") HomeScreen()`, but you completely lose OS integration. The Android Back Button won't work. Deep linking won't work. ViewModel scoping tied to the back stack won't work. Do not reinvent the wheel.

## Probing Questions

1.  What is the fundamental architectural difference between navigating via `Intent`/`Activity` and navigating in Jetpack Compose?
2.  Explain why passing a large, complex Data Class (like a downloaded `User` object) as a Navigation argument is a critical architectural failure.
3.  How did the introduction of `kotlinx.serialization` in Compose Navigation 2.8 solve the "String Parsing" problem of earlier versions?
4.  Why is it an architectural anti-pattern to pass the `NavController` directly into your deep `@Composable` UI screens? What should you do instead?
5.  If a user taps "Log Out", describe the exact `navController.navigate` configuration required to ensure they cannot press the physical Android back button to return to their private dashboard.
6.  How does a `NavHost` physically map the Android OS Back Button to the Compose internal state machine?
7.  If you have a 4-step Checkout flow (Cart -> Shipping -> Payment -> Confirm), explain why wrapping those 4 routes in a Nested `navigation` graph is superior to keeping them in the main global graph.
8.  How is the lifecycle of a `ViewModel` (created via `hiltViewModel()`) tied to the `NavBackStackEntry`?
9.  Describe how you would configure a `deepLink` in the `NavHost` to allow a user clicking a URL in an email to open your app directly to a specific product screen.
10. In a Single-Activity Architecture powered by Compose Navigation, what is the primary risk of a severe memory leak occurring deep inside a nested screen?

## Further Reading

- [`recomposition-and-state.md`](recomposition-and-state.md) — How the `NavHost` utilizes State to swap the screens instantly.
- [`dependency-injection.md`](../data-and-di/dependency-injection.md) — How `hiltViewModel()` scopes ViewModels to the Navigation Back Stack.
- [Android Developers: Type Safety in Compose Navigation](https://developer.android.com/guide/navigation/design/type-safety)
