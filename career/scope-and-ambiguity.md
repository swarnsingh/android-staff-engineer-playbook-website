# Career: Scope and Ambiguity

## The Theory
The defining characteristic of engineering levels is how much ambiguity they can process, and the blast radius of their decisions (Scope).
-   **Junior:** Needs low ambiguity (a ticket with exact steps) and has low scope (a single button).
-   **Mid-Level:** Needs moderate ambiguity (a ticket with a goal, but no steps) and has medium scope (a single screen).
-   **Senior:** Can handle high ambiguity (a 3-sentence feature request) and has large scope (an entire module or feature flow).
-   **Staff:** Operates in total ambiguity ("The app feels slow, fix it") and has organizational scope (impacting every developer and every user).

## Staff-Level Application in Mobile

### 1. Navigating Total Ambiguity
When a business leader says, "Our Android app crashes too much, fix it," there is no JIRA ticket, no API contract, and no clear definition of "done." A Staff Engineer must map this ambiguous territory.
-   **Phase 1: Defining the Metric.** "Crashes too much" is an emotion. A Staff Engineer translates this into math. They analyze Crashlytics and determine the current "Crash-Free Session" rate is 98.5%. They define a concrete goal: "Achieve a 99.9% Crash-Free Session rate."
-   **Phase 2: Root Cause Analysis.** They don't just start fixing random NullPointerExceptions. They look for systemic patterns. They discover 40% of crashes are `OutOfMemoryErrors` caused by the image loading pipeline, and 30% are caused by a specific third-party ad SDK.
-   **Phase 3: The Strategy.** They write an RFC proposing replacing Glide with Coil (configured with strict memory limits) and removing the ad SDK in favor of a more stable vendor.

### 2. Expanding Your Scope
Scope is not granted; it is taken. You cannot ask your manager for "more scope." You must identify organizational problems and start fixing them.
-   **The Mobile Monolith:** You notice build times are 15 minutes. No one has asked you to fix it. A Senior Engineer might complain about it on Slack. A Staff Engineer initiates a cross-team guild, writes a modularization strategy, and starts breaking out the first core module in their spare time to prove it works. They have just expanded their scope to impact the entire mobile org.
-   **Cross-Functional Impact:** Expanding scope means working outside the IDE. It means sitting with the Product Manager to explain *why* building the offline mode is technically impossible given the current API design, and negotiating a simpler "cached read" mode instead. You are shaping the product, not just the code.

### 3. The "Saying No" Superpower
As your scope expands, everyone will want your time. Feature teams will ask you to review every PR. Product managers will ask you to estimate every roadmap item.
-   A Junior engineer says yes to everything and burns out.
-   A Staff engineer rigorously guards their time. They know that saying "Yes" to reviewing a trivial UI PR means saying "No" to finalizing the database migration architecture.
-   **Delegation & Systems:** When asked to do a repetitive task (e.g., "Can you manually generate the release notes for this week's build?"), a Staff engineer does it *once*, writes a Bash script to automate it, and hands the script to the release team. They use systems to say no.

## Common Pitfalls
-   **Scope Creep in Architecture:** Operating in high ambiguity makes it tempting to try and solve every problem at once. If you are tasked with modularizing the app to improve build times, do not simultaneously try to rewrite the entire UI in Compose. A Staff Engineer ruthlessly scopes down complex projects into small, deliverable milestones to maintain momentum.
-   **The "Not My Job" Mentality:** If the iOS app is crashing because the backend deployed a broken API response, a Senior Android engineer might say, "My Android code handles the null safely, it's an iOS/Backend problem." A Staff Engineer realizes the company is losing money and jumps into the incident channel to help coordinate a rollback, regardless of platform boundaries. The boundary of a Staff Engineer's job is the success of the product.
