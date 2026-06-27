# Career: Performance Reviews & The Promotion Packet

## The Theory
In a perfect world, a Senior Engineer writes brilliant code, their manager notices it, and they are automatically promoted to Staff Engineer. 
In the real world, this never happens. A promotion to Staff is a formal business transaction. It requires a "Promotion Packet"—a documented body of evidence proving to a committee of Directors (who likely have never met you) that you are already operating at the Staff level and providing organizational impact.

## Staff-Level Application in Mobile

### 1. The Brag Document (The Hype File)
You cannot remember what you did 9 months ago. If you wait until performance review season to write your self-evaluation, you will forget 80% of your impact.
-   **The Mechanism:** Create a private Google Doc or markdown file today. Call it your "Brag Document."
-   **The Routine:** Every Friday afternoon, spend 10 minutes writing down what you accomplished that week.
-   **What to Record:**
    -   *Not:* "I closed 5 JIRA tickets." (Senior level).
    -   *Record:* "I noticed the network module was causing memory leaks. I wrote an RFC, convinced the iOS team to align with our schema, and mentored a Mid-Level engineer to implement the fix. This reduced OOM crashes globally by 12%." (Staff level impact).
    -   Record links to major PRs, RFCs you authored, and screenshots of Slack messages where other engineers thanked you for your help.

### 2. Managing Up (Aligning with your EM)
Your Engineering Manager (EM) is your sponsor, but they cannot advocate for you if they don't know what you want.
-   **The Promotion Conversation:** Do not wait for your EM to bring up a promotion. You must initiate it. "My goal is to reach Staff Engineer within the next 18 months. What are the specific gaps between my current performance and the Staff rubric, and how can we find projects that allow me to demonstrate those skills?"
-   **The Rubric Check:** Review the company's official engineering ladder together. If the rubric states a Staff engineer "Drives cross-team initiatives," and you are currently only fixing bugs on the Login screen, you and your EM need to actively hunt for a cross-team project for you to lead.

### 3. Writing the Promotion Packet (The Impact Argument)
When it is time for the formal promotion review, you must write your self-evaluation. This is not a list of tasks; it is an argument for your impact.
-   **The STAR Method:** Use the Situation, Task, Action, Result framework.
    -   *Situation:* The app build time was 15 minutes, destroying velocity.
    -   *Task:* I needed to reduce this to under 5 minutes.
    -   *Action:* I wrote a modularization strategy, convinced three feature teams to adopt it, and implemented a Remote Build Cache.
    -   *Result:* P90 build times dropped to 3 minutes, saving an estimated $200k in engineering hours annually.
-   **Business Metrics over Technical Jargon:** The Director reviewing your packet doesn't care that you used Kotlin Coroutines `SharedFlow`. They care that you reduced the crash rate, which increased user retention, which drove revenue. Translate technical wins into business value.

### 4. The "No" and How to Handle It
If you submit your packet and are denied the promotion to Staff, how you react defines your true seniority.
-   **The Junior Reaction:** Throwing a tantrum, threatening to quit, or accusing the committee of bias.
-   **The Staff Reaction:** Asking for the specific, actionable feedback from the committee. "The committee felt you didn't have enough impact outside of the Android team." You take that feedback, you pivot your focus to a cross-platform (Android/iOS/Backend) API standardization project, and you build an undeniable case for the next cycle.

## Common Pitfalls
-   **The Silent Martyr:** Believing that if you just work hard enough and fix enough bugs quietly, you will be rewarded. Visibility is crucial. You must present your work at All-Hands meetings, write blog posts on the internal engineering wiki, and publicly credit the engineers who helped you.
-   **The Competitor:** Viewing other Senior engineers as rivals for a limited number of Staff positions. If you sabotage a peer to make yourself look better, you immediately fail the Staff rubric for "Lifting the Organization." You are evaluated against the rubric, not against a quota. Helping your peers succeed is the fastest way to prove you are operating at the Staff level.
