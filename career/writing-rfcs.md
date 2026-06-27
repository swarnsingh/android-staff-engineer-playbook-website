# Career: Writing Technical Documents (RFCs, ADRs, PRDs)

## The Theory
The defining transition from Senior to Staff Engineer is shifting from communicating with *code* to communicating with *prose*. 
Code is read sequentially by compilers. Prose is read asynchronously by humans with varying contexts (Product Managers, CTOs, Junior Engineers). If a Staff Engineer cannot write a compelling, structured argument in a technical document, they cannot scale their influence, and their brilliant architectural ideas will never be built.

## Staff-Level Application in Mobile

### 1. The RFC (Request for Comments) / Design Doc
The RFC is the blueprint for the future. You write an RFC *before* you write the code.
-   **The Audience:** The Engineering Manager (who needs to approve the time), the Tech Leads (who need to agree on the architecture), and the Junior Engineers (who need to understand the 'why').
-   **The Structure:**
    1.  **Title & Status:** (e.g., "RFC 42: Migrating from SharedPreferences to DataStore [DRAFT]").
    2.  **Context & Problem:** Explain the current pain point with data. "SharedPreferences is causing 500 ANRs per day on the Main Thread."
    3.  **Proposed Solution:** "We will migrate to Proto DataStore. Here is the schema. Here is the migration path."
    4.  **Alternatives Considered:** "Why not Room? Overkill for simple key-value pairs." (This is the most critical section to preempt arguments).
    5.  **Rollout Plan:** "We will dual-write for 2 weeks, then switch the read path, behind a Feature Flag."
-   **The Goal:** The goal is *not* to prove you are smart. The goal is to surface hidden edge cases by inviting peer review before you waste 3 weeks writing the wrong code.

### 2. The ADR (Architecture Decision Record)
The ADR is the history book. You write an ADR *after* an RFC has been debated and a decision has been made.
-   **The Audience:** The engineer who joins the company 2 years from now and asks, "Why on earth did we build it this way?"
-   **The Structure (Usually based on Michael Nygard's template):**
    1.  **Title:** "ADR 004: Room vs DataStore".
    2.  **Context:** The debate that happened.
    3.  **Decision:** The binding outcome.
    4.  **Consequences:** The good and the bad. "Good: No more ANRs. Bad: We have to learn Protobuf syntax."
-   **The Goal:** ADRs live directly in the Git repository (`/adr/` folder). They capture the context of the decision at a specific point in time, preventing the team from endlessly relitigating old arguments.

### 3. The 1-Pager / Tech Spec
A 1-Pager is a heavily compressed RFC used for smaller features or to secure executive buy-in before investing time in a full 10-page RFC.
-   **The Audience:** Directors and VPs of Engineering.
-   **The Structure:** Bullet points. High-level architecture diagram. Estimated engineering weeks (T-Shirt sizing: S, M, L).
-   **The Goal:** To get a quick "Yes" or "No" on strategic direction. "Should we investigate migrating our build system to Bazel?" If the VP says "No, we don't have the bandwidth this year," you just saved yourself 2 weeks of writing an RFC.

### 4. Writing for the Audience
A Staff Engineer must context-switch their writing style based on the reader.
-   **When writing for Engineers:** Be extremely precise. Use exact class names, link to specific lines of code in GitHub, and provide concrete JSON payload examples.
-   **When writing for Product/Management:** Zoom out. Translate technical debt into business risk. Do not say, "We need to update to Kotlin 1.9 because of the new inline value class features." Say, "We need to update to Kotlin 1.9 to maintain compatibility with our third-party SDKs; if we don't, we will be unable to process payments by Q4."

## Common Pitfalls
-   **The Novelist:** Writing a 25-page RFC with dense, unformatted paragraphs. Engineers will skim it, miss critical details, and approve it blindly just to get it off their desk. Use bullet points, bold text, diagrams (Mermaid.js), and short sentences.
-   **Designing in Secret:** Writing the RFC alone in a dark room for 3 weeks and then dropping it on the team as a "finished" document. They will reject it because they feel no ownership. Write the RFC in the open. Tag engineers in comments while it's still a messy draft: *"Hey @Alice, does this API contract look right to you?"*
-   **Ignoring the "Alternatives":** Presenting only one solution as if it's the magical cure to all problems. If you don't list the downsides of your own proposal, people will assume you haven't thought deeply enough about the problem.
