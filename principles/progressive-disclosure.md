# Principles: Progressive Disclosure

## The Theory
Progressive Disclosure is originally a UI/UX principle: do not overwhelm the user with 50 configuration toggles on the first screen. Show them the essential information first, and provide an "Advanced" button to reveal the complexity only when they ask for it.
In software architecture, this principle applies to API design and module boundaries: **Expose a simple, default interface for 90% of use cases, but provide extension points for the 10% of complex use cases.**

## Staff-Level Application in Mobile

### 1. API Design for Internal Libraries (SDKs)
When a Platform team builds a logging library, they must balance simplicity with power.
-   **The Anti-Pattern (Too Complex):**
    ```kotlin
    // The consumer is forced to configure 5 parameters just to log a string.
    Logger.log(
        message = "App Started",
        level = LogLevel.INFO,
        destination = Destination.CONSOLE_AND_FILE,
        timestampFormat = "yyyy-MM-dd",
        bufferSize = 1024
    )
    ```
-   **The Application of Progressive Disclosure:**
    ```kotlin
    // 90% of the time, the engineer just wants this:
    Logger.info("App Started")

    // But for the 10% of advanced use cases, the API allows deep configuration via DSL:
    Logger.log {
        message = "App Started"
        level = LogLevel.DEBUG
        destinations = listOf(FileDestination(maxSize = 2048))
    }
    ```
    The complexity is hidden behind default parameters or builder patterns, allowing a junior engineer to use the library instantly, while empowering a senior engineer to customize it deeply.

### 2. Jetpack Compose: The Modifier Pattern
Google's Jetpack Compose heavily utilizes Progressive Disclosure.
-   A `Text()` composable takes a simple `String`.
-   If you want to add padding, a click listener, a background color, and a custom semantics label, you do not pass 4 new boolean parameters into the `Text()` function.
-   You pass a single `Modifier` object. The `Modifier` chain progressively discloses infinite layout complexity without cluttering the base API of the UI component.

### 3. Architecture: The Facade Pattern
Progressive Disclosure at the architectural level is achieved via the Facade Pattern.
-   **The Subsystem:** You have a complex Bluetooth Low Energy (BLE) scanning subsystem consisting of `BleScanner`, `GattClient`, `DeviceFilter`, and `PermissionManager`.
-   **The Facade:** You do not expose all 4 classes to the UI layer. You create a single `BluetoothService` interface (The Facade). The UI calls `BluetoothService.connect(deviceId)`. The Facade handles the internal orchestration. The complexity of the BLE spec is progressively hidden from the UI developers.

## Common Pitfalls
-   **The "God Function":** Creating a function with 15 optional parameters in Kotlin (`fun doThing(a=1, b=2, c=3... z=26)`). While technically hiding complexity via default arguments, it makes the function signature unreadable in the IDE. Complex configuration should be extracted into a dedicated Configuration object (Data Class) or a Builder DSL.
