# Platform Engineering: Design Systems Architecture

## The Theory
If 10 different product teams build 10 different UI screens, you will end up with 15 different shades of blue, 8 different button corner radii, and a disjointed user experience. Worse, when the company rebrands, it takes 6 months of engineering time to hunt down every hardcoded hex color in the codebase.
A **Design System** solves this by establishing a shared vocabulary (Design Tokens) between Designers (Figma) and Engineers (Code), implemented as a centralized UI component library.

## Staff-Level Application in Mobile

### 1. Design Tokens (The Vocabulary)
A Staff Engineer does not allow developers to hardcode `#0052CC` or use generic names like `blue_light`.
-   **The Architecture:** The platform team implements a multi-tiered token system.
    -   **Global Tokens (Primitives):** Raw values. `color_blue_500 = #0052CC`.
    -   **Semantic Tokens (Intent):** Maps primitives to meaning. `color_primary_action = color_blue_500`.
    -   **Component Tokens (Specific):** Maps semantics to specific components. `button_primary_background = color_primary_action`.
-   **The Benefit:** If the company rebrands to Red, you update `color_primary_action = color_red_500` in exactly *one* place, and every button, text link, and icon in the entire app updates instantly. Furthermore, this architecture natively supports Dark Mode without writing `if (isDark)` logic in your UI code; you simply define a second Semantic Token map for the dark theme.

### 2. The Shared UI Component Library (The Module)
The Design System must be isolated into its own highly strictly governed module (e.g., `:core:design-system`).
-   **Strict Encapsulation:** Product feature modules (like `:feature:checkout`) are *banned* from depending on raw Android UI widgets (`android.widget.Button` or standard Compose `Button`). They are only allowed to depend on the `:core:design-system` module and must use the custom `CompanyButton` component.
-   **Enforcement:** Staff Engineers use Lint rules to fail the CI build if a developer imports a raw UI primitive instead of the Design System component.

### 3. Jetpack Compose Integration
Compose was built specifically to empower Design Systems.
-   **`CompositionLocal`:** Instead of passing theme parameters down through 20 layers of Composables, the Design System provides a custom `CompanyTheme` object. Under the hood, it uses `staticCompositionLocalOf` to make the colors, typography, and spacing universally accessible to any child Composable via `CompanyTheme.colors.primaryAction`.
-   **Slot APIs:** To keep components flexible without creating a `CompanyButton` with 45 different boolean parameters (`hasIcon`, `isTrailingIcon`, `isLoading`), the Design System exposes **Slot APIs**. The component defines the structural container (padding, background, ripple), but allows the caller to pass in a generic `@Composable` lambda to fill the "slot" (the content of the button).

### 4. Figma to Code Automation (The Holy Grail)
A truly mature Platform Team automates the translation from Design to Code.
-   The design team maintains the "Source of Truth" for Tokens in Figma (using Figma Variables or Tokens Studio).
-   When a designer updates a color, a GitHub Action is triggered.
-   A script parses the Figma API JSON response, generates the Kotlin data classes containing the new Compose Color definitions, opens a Pull Request on the Android repository, and assigns the Platform Team to review it. The engineers never manually type hex codes again.

## Common Pitfalls
-   **The Rigid System (The Tyranny of Design):** If the Design System is too rigid and doesn't provide enough Slot APIs or override capabilities, feature teams will just build their own rogue components to hit their deadlines. A Design System must be flexible enough to accommodate edge cases while maintaining the core brand identity.
-   **Breaking Changes:** The Design System module is a dependency for every other module in the app. If you change the method signature of `CompanyButton`, you break 50 feature modules simultaneously. The Platform Team must treat the Design System as a public API, employing deprecation cycles (`@Deprecated`) and providing automated migration scripts (Structural Search and Replace) for the feature teams.
