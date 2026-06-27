# Leadership: Technical Mentorship (Scaling Yourself)

## The Theory
A Senior Engineer's impact is measured by the code they write. A Staff Engineer's impact is measured by the code *the organization* writes. 
You cannot scale yourself by working 80 hours a week and writing all the critical path code. You scale yourself by elevating the baseline competency of every engineer around you. This is achieved through deliberate Technical Mentorship.

## Staff-Level Application in Mobile

### 1. The Code Review as a Mentorship Tool
Code Reviews (PRs) are the highest-leverage mentorship opportunity, provided they are done correctly.
-   **The Anti-Pattern (The Nitpicker):** Leaving 40 comments on a junior engineer's PR about variable naming, spacing, and minor Kotlin idioms. This destroys morale and teaches them nothing about architecture.
-   **The Staff Pattern (The Architect):** A Staff Engineer uses automated tooling (Detekt/ktlint) to handle the formatting nits. In the PR review, they focus exclusively on structural flaws: "This ViewModel is holding a strong reference to the Activity context, which will cause a memory leak on rotation. Let's look at how to hoist this state or use the Application context instead."
-   **The Socratic Method:** Do not just post the solution code. Ask questions. "What happens to this Coroutine if the user presses the back button while the network request is still pending?" Guide them to find the bug themselves.

### 2. Pair Programming and Debugging
When a mid-level engineer is stuck on a critical bug for 2 days, a Staff engineer steps in.
-   **The Anti-Pattern:** You take their laptop, fix the bug in 5 minutes because you know the legacy codebase intimately, commit the code, and walk away. You solved the bug, but you created a dependency.
-   **The Staff Pattern:** You sit next to them (or jump on a screen share) and say, "Drive." You tell them what commands to type. You teach them *how* to use the Android Studio Memory Profiler to find the leak, or how to write a custom SQL query to inspect the Room database. You teach them the methodology of debugging, not just the solution.

### 3. Creating "Force Multipliers"
Mentorship isn't just 1-on-1 conversations. It is creating systemic resources that mentor engineers while you sleep.
-   **Reference Architectures:** Writing the canonical "How we build features here" document (like this very repository).
-   **Internal Tech Talks:** Hosting a monthly 30-minute session on a specific topic (e.g., "Deep Dive into Jetpack Compose Recomposition under the hood").
-   **Custom Lint Rules:** If you keep explaining the same architectural rule in PRs (e.g., "Don't use `GlobalScope.launch`"), write a custom Android Lint rule that catches it in the IDE. The compiler becomes the mentor.

### 4. Sponsorship vs Mentorship
Understand the difference between mentoring and sponsoring.
-   **Mentorship:** Giving advice, teaching technical concepts, and helping someone improve their skills (e.g., teaching them RxJava to Coroutines migration).
-   **Sponsorship:** Using your political capital to elevate someone else. (e.g., Telling the Engineering Manager: "Sarah has been doing incredible work on the UI layer. I think she is ready to lead the massive Dark Mode migration project. I will shadow her, but she should be the lead.") A Staff Engineer must actively sponsor high-performing engineers to help them reach the Senior level.

## Common Pitfalls
-   **The Gatekeeper:** Using your vast knowledge of the codebase to shoot down other people's ideas to protect your own perceived importance. A true Staff Engineer strives to make themselves obsolete on their current project so they can move on to the next massive organizational challenge.
-   **Ignoring the Mid-Levels:** It is easy to mentor eager junior engineers. It is harder, but vastly more important, to mentor the solid "Mid-Level" engineers. Moving a Mid-Level engineer to a Senior Engineer provides the highest ROI for the company, as they become autonomous problem solvers.
