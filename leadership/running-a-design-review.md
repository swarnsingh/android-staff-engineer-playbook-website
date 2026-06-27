# Leadership: Running a Design Review (RFCs)

## The Theory
A Senior Engineer writes excellent code. A Staff Engineer ensures the *right* code is written before a single pull request is opened. The mechanism for this is the **Request for Comments (RFC)** or Technical Design Document, culminating in a formal Design Review meeting.
If 10 engineers start writing code without a unified architectural vision, they will build 10 incompatible micro-systems. The Design Review prevents this.

## Staff-Level Application in Mobile

### 1. The Anatomy of an RFC Document
A Staff Engineer does not write an RFC by simply pasting a UML diagram. The document must be structured to guide decision-making.
-   **Context & Problem Statement:** Why are we doing this? (e.g., "The current monolithic `api` module increases build times by 4 minutes per PR.")
-   **Goals & Non-Goals:** Explicitly stating what the project will *not* do is crucial to prevent scope creep.
-   **Proposed Solution:** The actual architecture. API contracts, data models, state flow.
-   **Alternatives Considered:** This is the most important section. A Staff Engineer must steelman the opposing arguments. Why *didn't* we choose Koin over Hilt? Documenting the rejected paths prevents the team from revisiting the same arguments 6 months later.
-   **Rollout & Rollback Plan:** How do we safely deploy this to 10 million users, and how do we revert it if it crashes?

### 2. Preparing for the Review
A Design Review meeting should never be a surprise.
-   **Pre-Reads:** The RFC document must be circulated at least 48 hours before the meeting. If you try to read a 10-page architecture document live on a Zoom call, the feedback will be superficial (grammar corrections) rather than structural (flaws in the database schema).
-   **Asynchronous Feedback First:** Encourage engineers to leave comments directly on the Google Doc or Confluence page before the meeting. The Staff author should resolve the simple disagreements asynchronously. The synchronous meeting is reserved *only* for the highly contested architectural trade-offs.

### 3. Facilitating the Meeting (The Staff Role)
When running the meeting, the Staff Engineer acts as a facilitator, not a dictator.
-   **Foster Psychological Safety:** If a junior engineer asks a seemingly simple question ("Why aren't we just using SharedPreferences?"), a Staff engineer does not shut them down. They use it as a teaching moment ("Great question. We considered that in the 'Alternatives' section, but because of the ANR risk on the main thread, we decided on DataStore.").
-   **Park the Bikeshedding:** Engineers love to argue about trivial details (e.g., naming conventions or folder structures)—this is called "Bikeshedding" (Parkinson's Law of Triviality). The Staff Engineer must ruthlessly identify these debates and "park" them. ("Let's take the naming of the DTO classes offline. We need to focus on the offline-sync conflict resolution strategy today.")
-   **Drive to Consensus (or Commit):** The goal of the meeting is a decision. If the room is split 50/50 on an architecture choice, the Staff Engineer must synthesize the arguments and make a binding decision, or use the "Disagree and Commit" framework to move the project forward.

### 4. The Output: The ADR
Once the Design Review is complete and the path is chosen, the final decision must be permanently recorded as an **Architecture Decision Record (ADR)** in the Git repository (see the `adr/` folder). This ensures the context of *why* the decision was made survives even if the original Staff Engineer leaves the company.

## Common Pitfalls
-   **The "Big Reveal":** Working on an architecture document in secret for 3 weeks and surprising the team in the meeting. The team will feel lack of ownership and will naturally resist the design. Build consensus iteratively by consulting key stakeholders *while* writing the document.
-   **Designing in the Meeting:** A Design Review is for *reviewing* a design, not *creating* one. If the meeting devolves into 5 engineers whiteboarding completely new architectures from scratch, the meeting has failed. The author must take the feedback offline, redesign the RFC, and schedule a follow-up.
