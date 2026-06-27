# Principles: Optimize for Change (Reversibility)

## The Theory
Software is not a bridge; it is never "finished." The only guarantee in software engineering is that requirements will change. 
Therefore, a superior architecture is not one that perfectly predicts the future (which is impossible). A superior architecture is one that makes future changes cheap and safe.

## Staff-Level Application in Mobile

### 1. The Strategy Pattern (Swappable Implementations)
If your app needs to process payments, a Junior engineer tightly couples the app to Stripe's SDK.
-   **The Cost of Change:** When the business decides to switch to Braintree to save 1% on transaction fees, the engineering team has to rewrite 50 files across the app, taking 3 months.
-   **Optimizing for Change:** A Staff Engineer defines an interface `interface PaymentProcessor { fun charge(amount: Int) }`. The app depends entirely on this interface. The implementation `StripeProcessorImpl` is injected via DI. When the business switches to Braintree, the engineer writes a new `BraintreeProcessorImpl`, swaps the DI binding in exactly one place, and the feature is done in 2 days.

### 2. Feature Flags (Reversibility)
Optimizing for change means acknowledging that some changes will be catastrophic failures in production. You must optimize for the ability to *reverse* the change instantly.
-   **The One-Way Door:** Releasing a massive UI rewrite by simply merging it into `main` and shipping an APK to the Play Store. If it crashes on Samsung devices, the only way to reverse the change is to write a hotfix, compile a new APK, submit it to Google, wait 48 hours for review, and hope users download the update.
-   **The Two-Way Door:** Releasing the UI rewrite behind a Remote Config Feature Flag. If it crashes, a Staff Engineer toggles the flag on the backend dashboard. The change is reversed globally in 30 seconds without a Play Store update.

### 3. Avoiding Premature Optimization (YAGNI)
You Aren't Gonna Need It (YAGNI) is the counter-balance to over-engineering.
-   **The Trap:** A developer builds a complex plugin architecture to support 15 different types of video players, "just in case" the product team asks for it next year.
-   **The Reality:** The product team never asks for it. The complex architecture makes the codebase harder to maintain and slower to compile.
-   **The Balance:** Optimize for change by keeping the code *simple* and *decoupled*. Do not build infrastructure for features that do not exist yet. Write code that is easy to delete.

## Common Pitfalls
-   **The "Clean Architecture" Dogma:** Forcing a 3-tier Clean Architecture (Data, Domain, Presentation) with 15 interfaces and mappers onto a simple "About Us" screen that displays static text. This violates YAGNI. It does not optimize for change; it optimizes for bureaucracy. A Staff Engineer knows when to apply heavy architecture and when a simple direct database call is sufficient.
