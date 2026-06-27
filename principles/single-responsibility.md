# Principles: Single Responsibility Principle (SRP)

## The Theory
The Single Responsibility Principle (the 'S' in SOLID) states that a module, class, or function should have only one reason to change. 
It does *not* mean a class should only do one thing. It means that the class should be responsible to only one actor or stakeholder.

## Staff-Level Application in Mobile

### 1. The "God Object" Activity
The most classic violation of SRP in Android is the 3,000-line `MainActivity.kt`.
-   **The Violation:** The Activity handles UI rendering, makes network requests, parses JSON, and saves data to SharedPreferences.
-   **The Reasons to Change:** 
    1. The designer wants to change the button color (UI).
    2. The backend team changes the JSON payload (Networking).
    3. The product manager wants to cache data differently (Storage).
-   **The Fix:** Split the responsibilities. The `Activity` (or Compose file) only renders UI. The `ViewModel` holds state. The `Repository` fetches data. The `Retrofit Service` parses JSON.

### 2. SRP at the Module Level (Clean Architecture)
Staff engineers apply SRP not just to classes, but to entire Gradle modules.
-   **The `data` module:** Responsible for fetching and persisting data. It should only change if the database schema or network APIs change.
-   **The `domain` module:** Responsible for core business logic (Use Cases/Interactors). It should only change if the fundamental rules of the business change (e.g., "Users must now be 18+ to register").
-   **The `ui` module:** Responsible for displaying pixels. It should only change if the design changes.
-   **The Benefit:** If the company decides to migrate from REST to GraphQL, only the `data` module changes. The `domain` and `ui` modules remain completely untouched because their single responsibilities were not violated.

### 3. The Danger of "Reusability"
Junior engineers often violate SRP in the pursuit of DRY (Don't Repeat Yourself).
-   **The Scenario:** You have a `UserDTO` returned from the `/login` endpoint. It has an `email` and `passwordHash`. You also need a `UserProfile` model for the UI that shows the `email`.
-   **The Violation:** To save typing, the engineer uses the exact same `UserDTO` data class for both the network layer and the UI layer.
-   **The Consequence:** Six months later, the UI team wants to display the user's `firstName`. They add `firstName` to `UserDTO`. Now the network parser expects a `firstName` field in the `/login` response. If it's missing, the app crashes.
-   **The Staff Pattern:** The Network model and the UI model have *different reasons to change*. They belong to different stakeholders. Even if the classes look identical today, a Staff engineer creates two separate classes (`NetworkUser` and `UiUser`) and maps between them. Duplication is cheaper than the wrong abstraction.

## Common Pitfalls
-   **Micro-Fragmentation:** Taking SRP to the extreme by splitting code into thousands of 5-line classes. If you have to open 15 files just to understand how a button click saves a boolean to a database, you have destroyed readability. Cohesion (things that change together should stay together) is just as important as decoupling.
