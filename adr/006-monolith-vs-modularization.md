# ADR 006: Monolith vs Modularization

## Context
The Android repository currently consists of a single `:app` module (a Monolith) containing 500,000 lines of code.

As the team has grown to 30 engineers, this architecture is failing in three critical ways:
1.  **Build Times:** A clean build takes 12 minutes. An incremental build (changing one line of code) takes 4 minutes because the Gradle execution must evaluate and recompile the entire monolithic dependency graph.
2.  **Code Ownership:** There are no physical boundaries between features. A developer working on the `Checkout` feature can easily (and accidentally) instantiate classes from the `Profile` feature, creating a spaghetti dependency graph that makes refactoring impossible.
3.  **Merge Conflicts:** 30 engineers working in the same module leads to constant merge conflicts, especially in central files like `build.gradle` or navigation graphs.

The engineering team is proposing a transition to a **Multi-Module Architecture**.

## Alternatives Considered

### 1. Monolith (Status Quo)
-   **Pros:** Extremely simple setup. No cross-module dependency management required. Easy to onboard junior engineers.
-   **Cons:** Unsustainable build times. Impossible to enforce architectural boundaries. Blocks the adoption of Dynamic Feature Modules (App Bundles).

### 2. Feature-Based Modularization (Vertical Slicing)
-   **Description:** Splitting the app into feature-specific modules (`:feature:login`, `:feature:checkout`, `:feature:feed`), which all depend on a shared `:core` module.
-   **Pros:** Isolates features, allowing teams to own their specific modules. Gradle can compile `:login` and `:checkout` in parallel.
-   **Cons:** Prone to circular dependencies if `:checkout` needs to navigate to `:login`. Often leads to a bloated `:core` module that becomes a mini-monolith itself.

### 3. Clean Architecture Modularization (Horizontal Slicing)
-   **Description:** Splitting the app strictly by architectural layers (`:domain`, `:data`, `:presentation`).
-   **Pros:** Enforces strict Clean Architecture rules (e.g., `:domain` cannot know about Android classes).
-   **Cons:** Modifying a single feature requires touching 3 different modules, increasing cognitive load and context switching. Does not solve the parallel compilation issue well, as `:presentation` will always depend on `:domain`, forcing sequential builds.

## Decision
We will adopt a hybrid **Feature-First, Layer-Second Modularization Strategy**.

1.  **Strict Feature Modules:** The app will be divided into independent feature modules (e.g., `:feature:home`, `:feature:cart`).
2.  **No Feature-to-Feature Dependencies:** A feature module is strictly forbidden from depending on another feature module. This mathematically eliminates circular dependencies and guarantees maximum parallel compilation in Gradle.
3.  **Navigation via Deep Links/Interfaces:** If `:cart` needs to navigate to `:home`, it must use an implicit deep link (Jetpack Navigation) or a generic interface defined in the `:core:navigation` module, rather than explicitly importing the `:home` module.
4.  **Core Utility Modules:** Shared infrastructure will be broken into highly specific core modules (`:core:network`, `:core:design-system`, `:core:analytics`). A giant, catch-all `:core` module is banned.
5.  **Domain/Data Split (Optional):** Within a complex feature module, the team *may* choose to sub-modularize into `:feature:cart:domain` and `:feature:cart:ui` if the business logic requires strict isolation, but this is not mandated globally.

## Consequences
-   **Positive:** **Build Speed.** Because feature modules do not depend on each other, modifying `:cart` means Gradle *only* recompiles `:cart` and the `:app` shell. Incremental build times should drop from 4 minutes to under 30 seconds.
-   **Positive:** **Boundary Enforcement.** We can use the Kotlin `internal` visibility modifier to hide implementation details within a module. The `CheckoutRepositoryImpl` cannot be accessed by the `Profile` feature, enforcing strict encapsulation.
-   **Positive:** Paves the way for Android App Bundles and Dynamic Feature Modules (downloading features on demand).
-   **Negative:** **Dependency Management Overhead.** We must adopt a `libs.versions.toml` (Version Catalog) to centrally manage Gradle dependencies across 50+ modules to prevent version conflicts.
-   **Negative:** **Initial Refactoring Cost.** Untangling the existing monolith to extract the first feature module will be a massive undertaking, likely requiring a dedicated "Platform Team" effort for several weeks.
