# ADR 007: Hilt vs Manual DI (Dependency Injection)

## Context
The Android application relies on Dependency Injection (DI) to provide instances of Repositories, ViewModels, and Network Clients to the UI. Historically, the project used **Dagger 2**.

While Dagger 2 is incredibly powerful and provides compile-time safety, it has become a severe pain point:
1.  **Steep Learning Curve:** New engineers spend weeks understanding `@Component`, `@Subcomponent`, `@Module`, and `@Binds`.
2.  **Boilerplate:** Connecting an Android `Activity` or `Fragment` to the Dagger graph requires writing tedious, repetitive injection boilerplate (`AndroidInjection.inject(this)`).
3.  **ViewModel Injection:** Providing dependencies to `ViewModel`s requires complex multibinding factories (`ViewModelProvider.Factory`), which is arguably the most confusing part of standard Dagger 2 on Android.

The engineering team is evaluating whether to migrate to **Hilt** (Google's opinionated wrapper over Dagger), **Koin** (a Kotlin Service Locator), or fallback to **Manual DI**.

## Alternatives Considered

### 1. Manual DI (Pure Kotlin)
-   **Pros:** Zero third-party library dependencies. Zero build-time code generation overhead. The most transparent flow of dependencies possible.
-   **Cons:** Does not scale. Manually instantiating a deep dependency tree with 50 singletons inside the `Application` class becomes a massive, unmaintainable file. Scoping dependencies to specific lifecycles (e.g., clearing a user repository when they log out) requires manual memory management, which is highly prone to leaks.

### 2. Koin
-   **Pros:** Extremely low boilerplate. 100% Kotlin. No annotation processing (`kapt`/`ksp`), which drastically improves build times compared to Dagger.
-   **Cons:** It is a Service Locator, not true Dependency Injection. It resolves dependencies at *runtime*. If a dependency is missing, the app crashes at runtime (`InstanceCreationException`) instead of failing the CI build. This is unacceptable for a Staff-level architecture where compile-time safety is paramount.

### 3. Hilt
-   **Pros:** 
    -   **Compile-Time Safety:** Retains the mathematical guarantee of Dagger 2 (if it compiles, the graph is complete).
    -   **Zero Android Boilerplate:** Solves the ViewModel and Activity injection nightmare with simple annotations (`@HiltViewModel`, `@AndroidEntryPoint`).
    -   **Standardized Scopes:** Provides built-in predefined components (`SingletonComponent`, `ViewModelComponent`) that automatically tie into the Android Lifecycle.
-   **Cons:** Uses annotation processing. Adds to the build time overhead. Imposes strict rules on module structure that might clash with esoteric legacy Dagger setups.

## Decision
We will migrate the dependency injection framework to **Hilt**.

1.  **Standardization:** All ViewModels must be annotated with `@HiltViewModel`. Custom `ViewModelFactory` implementations are banned.
2.  **Entry Points:** All Activities and Fragments that require injection must use `@AndroidEntryPoint`.
3.  **Module Scoping:** Engineers must strictly adhere to Hilt's predefined scopes. Using `@Singleton` for dependencies that should be scoped to a user session (e.g., `UserDataRepository`) is forbidden, as it leads to data leaks when a different user logs in on the same device. (Such dependencies should be scoped to a custom component or handled manually if Hilt's predefined scopes do not fit).
4.  **Testing:** Hilt will be used in the instrumented testing layer (`@HiltAndroidTest`) to allow easily swapping production network modules with mock local modules during UI testing.

## Consequences
-   **Positive:** Developer velocity will increase drastically, especially for junior engineers who no longer need to write Dagger boilerplate.
-   **Positive:** The `ViewModel` injection process becomes trivial.
-   **Positive:** We retain the absolute compile-time safety of the Dagger 2 compiler.
-   **Negative:** **Build Times.** Because Hilt relies on KSP/KAPT (Kotlin Symbol Processing), the build time will remain slower than a pure Koin or Manual DI solution. We accept this trade-off in exchange for compile-time safety.
-   **Negative:** Migrating existing legacy Dagger `Subcomponents` into the Hilt hierarchy will require a dedicated refactoring phase, as Hilt's monolithic component structure is less flexible than raw Dagger.
