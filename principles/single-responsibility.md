# Single Responsibility Principle (SRP)

## Overview

The Single Responsibility Principle (the 'S' in SOLID) states that a module, class, or function should have **only one reason to change**.

It does *not* mean a class should only do one thing. It means the class should be responsible to only one actor or stakeholder. A class with three methods answering to one stakeholder is healthier than a class with one method answering to three.

## Why It Matters

Every "reason to change" attached to a unit of code is a future merge conflict, a future regression surface, and a future reviewer who has to understand the whole file to change a corner of it.

- **Change amplification.** When UI, networking, and persistence live in one class, a payload rename forces you to reopen — and re-test — rendering code that had nothing to do with it.
- **Team contention.** Reasons-to-change map to *teams*. A file that designers, backend integrators, and infra engineers all edit becomes the highest-conflict, highest-defect file in the repo. Ownership boundaries follow responsibility boundaries.
- **Testability.** A class with one reason to change has one axis to fake. A god object needs a network stack, a database, and a UI harness just to test a boolean flip.

At Staff level, SRP stops being a code-review nitpick and becomes an organizational design tool: you shape modules so that the teams who change things for different reasons don't share files.

## First Principles

1.  **A "responsibility" is a stakeholder, not a verb.** Ask "who requests changes to this code?" — not "how many things does it do?"
2.  **Reasons to change are discovered over time.** Code that looks cohesive today reveals its seams when two stakeholders pull it in different directions. The second divergent change request is the signal to split.
3.  **Cohesion is the counterweight.** Things that always change together belong together. SRP splits by *stakeholder*, not by line count.

## Mental Model

Think of a class as an **employee with exactly one manager**.

- An employee reporting to one manager gets coherent instructions and can be evaluated against one goal.
- An employee reporting to three managers (design, backend, product) receives conflicting orders, context-switches constantly, and every performance review is a negotiation between departments.
- SRP is the org-chart rule applied to code: every unit reports to exactly one stakeholder. When two managers keep giving the same employee orders, you split the role.

## Staff-Level Application in Mobile

### 1. The "God Object" Activity

The classic Android violation is the 3,000-line `MainActivity.kt`.

- **The violation:** the Activity renders UI, makes network requests, parses JSON, and saves data to SharedPreferences.
- **The reasons to change:**
    1. The designer wants to change the button color (UI).
    2. The backend team changes the JSON payload (networking).
    3. The product manager wants different caching (storage).
- **The fix:** split by stakeholder. The Activity (or composable) renders. The [ViewModel](../android/architecture/viewmodel.md) holds state. The [Repository](../patterns/repository.md) fetches data. The serializer parses payloads.

### 2. SRP at the Module Level

Staff engineers apply SRP to entire Gradle modules, because modules are the unit of ownership, build parallelism, and API enforcement:

- **`data`** changes when schemas or network APIs change — owned by the platform/data team.
- **`domain`** changes when business rules change ("users must now be 18+ to register") — owned by the feature team.
- **`ui`** changes when design changes — owned by the feature/design-system collaboration.

The payoff compounds: migrate REST → GraphQL and only `data` modules change; the `domain` and `ui` trees don't even rebuild. See [modularization-strategies](../android/architecture/modularization-strategies.md).

### 3. The Danger of "Reusability"

Engineers often violate SRP in pursuit of DRY.

- **The scenario:** `UserDTO` from the `/login` endpoint has `email` and `passwordHash`. The profile UI also needs a user model showing `email`.
- **The violation:** reusing `UserDTO` for both the network layer and the UI layer to save typing.
- **The consequence:** six months later the UI team adds `firstName` to `UserDTO` for display. The deserializer now expects `firstName` in the `/login` response. When the backend doesn't send it, parsing behavior changes underneath a login flow nobody meant to touch.
- **The Staff pattern:** network models and UI models have *different reasons to change* — they belong to different stakeholders. Even when the classes look identical today, keep `NetworkUser` and `UiUser` separate and map between them. **Duplication is cheaper than the wrong abstraction.**

### 4. SRP in Compose

The same principle, new syntax:

- A composable that reads `ViewModel` state, formats currency, *and* fires analytics has three stakeholders.
- Split: stateless composable (design), state holder (feature logic), analytics decorator at the call site (data team).
- Symptom to watch for in review: a `@Composable` whose parameter list mixes domain objects, formatting config, and logging callbacks.

## Production Example

A payments team owns `CheckoutViewModel`. Over a year it accretes: price formatting (locale team files bugs against it), retry policy for the payment API (infra team tunes it), and an A/B flag branch (growth team edits it). Three teams now edit one file; merge conflicts and "unrelated" regressions follow — the growth team's flag change once broke retry behavior in a way none of their tests could catch.

The Staff-level fix wasn't cleverer code — it was redrawing ownership: `PriceFormatter` (locale team), `PaymentRetryPolicy` (infra, in a shared module with its own tests), and an experimentation wrapper at the DI layer (growth). Each unit gained a single manager; cross-team regressions stopped being possible by construction.

## Tradeoffs

- **SRP vs. locality.** Every split adds a file hop. For code with one stakeholder and stable behavior, inlining is fine — SRP is a response to *divergent change pressure*, not a mandate to pre-shatter everything.
- **SRP vs. speed of first draft.** The god object is genuinely faster to write on day one. The principle pays off from the second divergent change onward — which is why prototypes may skip it, and products must not.
- **When to split: on the second stakeholder, not the fifth.** Waiting until the file is unmanageable means untangling a year of interleaved changes; splitting speculatively means abstractions with one caller. The second *divergent* change request is the calibrated trigger.

## Failure Modes

- **Micro-fragmentation.** Splitting into thousands of 5-line classes until a button click that saves a boolean spans 15 files. If understanding one behavior requires a file-hopping expedition, readability has been destroyed in SRP's name. Cohesion — things that change together stay together — is equal in rank, not subordinate.
- **Splitting by layer instead of by stakeholder.** Mechanically creating `Manager`/`Helper`/`Util` classes redistributes lines, not responsibilities. `UserHelper` with formatting, validation, and caching methods has three reasons to change no matter how small it is.
- **The shared "common" module.** A `:common` module every team dumps into is the god object reborn at module scale — every team's changes rebuild everyone, and no one owns it. Split commons by stakeholder too (`:common:design`, `:common:networking`).

## Probing Questions

1.  "One reason to change" — a reason for *whom*? Walk through how you'd identify the stakeholders of a class you're reviewing.
2.  A teammate defends a 2,500-line ViewModel as "cohesive — it's all checkout logic." How do you evaluate whether that's true?
3.  When is duplicating a data class the *right* call, and what future change makes the duplication pay for itself?
4.  How does SRP at the Gradle-module level affect build times, code ownership, and API review?
5.  What symptoms in a git log (not the code itself) tell you a file violates SRP?
6.  Where is the line between SRP and micro-fragmentation, and which heuristic do you use to stop splitting?

## Further Reading

- [`coupling-vs-cohesion.md`](../engineering-fundamentals/coupling-vs-cohesion.md) — the mechanics underneath this principle.
- [`composition-over-inheritance.md`](composition-over-inheritance.md) — the structural tool that makes splits cheap.
- [`optimize-for-change.md`](optimize-for-change.md) — the parent heuristic: design for the changes that are coming.
- [`../android/architecture/modularization-strategies.md`](../android/architecture/modularization-strategies.md) — SRP applied at module scale.
- [`../patterns/repository.md`](../patterns/repository.md) — the standard stakeholder split for data access.
