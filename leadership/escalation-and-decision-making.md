# Leadership: Escalation and Decision Making

## The Theory
Organizations paralyze themselves when engineers cannot agree on a path forward. Two senior engineers might debate for weeks over whether to use RxJava or Kotlin Coroutines, grinding feature delivery to a halt. A Staff Engineer's responsibility is to unblock the organization by forcing a decision, and knowing when to escalate when a technical dispute threatens the business.

## Staff-Level Application in Mobile

### 1. The "Disagree and Commit" Framework
Consensus is a trap. You will rarely get 100% of engineers to agree on a major architectural change. If you wait for consensus, you will never ship.
-   **The Mechanism:** When a debate (e.g., in a Design Review) goes in circles, a Staff Engineer must synthesize the arguments, acknowledge the validity of the opposing side, and make a binding decision.
-   **The Communication:** "I understand the concerns about Hilt's compile-time overhead. Those are valid. However, given our goal to reduce onboarding time for junior engineers and enforce compile-time safety, we are moving forward with Hilt. I need everyone to disagree and commit to this path so we can hit our Q3 deliverables."
-   Once the decision is made, the engineers who opposed it must actively work to make it successful. Sabotaging the decision to prove "I told you so" is a toxic trait that Staff engineers must actively stamp out.

### 2. When to Escalate (The Escalation Matrix)
A Staff Engineer should handle 95% of technical disputes locally. Escalating to the Director of Engineering or CTO is a failure of local leadership if done prematurely, but a failure of business stewardship if done too late.
-   **Do NOT Escalate:** Debates over library choices, code formatting, or minor refactoring priorities. Handle these with an RFC and an ADR.
-   **DO Escalate:** 
    -   **Cross-Functional Deadlocks:** The Mobile team needs a new GraphQL endpoint. The Backend team refuses to build it because it's not on their roadmap. The mobile feature is blocked. You must escalate to Engineering Management to realign the roadmap priorities.
    -   **Security/Compliance Risks:** Product Management demands you ship a feature that you know violates GDPR (e.g., logging PII to a third-party SDK without consent) because they want to hit a revenue target. This is a non-negotiable escalation to Legal and the VP of Engineering.

### 3. How to Escalate (The Executive Summary)
When you do escalate to a Director or VP, do not send them a 5-page Slack message detailing the intricacies of the Android lifecycle. They do not care.
-   **The Format:**
    1.  **The Impact:** "If we do X, we will delay the Q4 release by 3 weeks, costing $500k in projected revenue."
    2.  **The Options:** "Option A (Backend builds the API) takes 2 weeks. Option B (Mobile mocks the data locally) takes 3 days but creates massive technical debt."
    3.  **The Recommendation:** "I strongly recommend Option A, as Option B will cause data consistency bugs in production."
-   Provide the business context, the technical options, and a clear, firm recommendation. Let the executive make the final call based on business risk.

### 4. Reversible vs Irreversible Decisions (One-Way Doors)
Amazon classifies decisions as "One-Way Doors" (irreversible) and "Two-Way Doors" (reversible).
-   **Two-Way Doors (Reversible):** Changing the color of a button, or swapping the JSON parsing library from Moshi to Kotlinx.Serialization in a single module. **Action:** Move fast, don't ask for permission, don't require an RFC. If it fails, revert the PR.
-   **One-Way Doors (Irreversible):** Choosing React Native over Native Kotlin for the next major app rewrite. Migrating the core database from Room to Realm. **Action:** Move slowly. Require a formal RFC, intense design reviews, and multiple prototypes. These decisions bind the company for years and require deliberate, escalated consensus.

## Common Pitfalls
-   **The Spineless Compromise:** Two engineers argue about architecture. To keep the peace, you propose a "hybrid" solution that incorporates half of Idea A and half of Idea B. The result is an overly complex, Frankenstein architecture that fails at both. A Staff Engineer must have the courage to pick a winner and let the other person be disappointed.
-   **Weaponized Escalation:** Using escalation as a threat to force junior engineers to comply with your technical opinions. Escalation should be a tool for systemic alignment, not a bludgeon for personal arguments.
