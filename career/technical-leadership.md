# Career: Technical Leadership

## The Theory
Leadership in software engineering is frequently confused with Management.
-   **Management** is about humans. It is 1-on-1s, compensation planning, performance improvement plans (PIPs), and shielding the team from organizational politics.
-   **Technical Leadership** is about systems. It is defining the architecture, setting the engineering culture, enforcing technical standards, and ensuring the software actually works at scale.
A Staff Engineer is a Technical Leader. You lead through code, architecture, and influence, not through HR authority.

## Staff-Level Application in Mobile

### 1. Defining the "Engineering Culture"
Culture is not Ping-Pong tables and free snacks. Engineering culture is defined by what you tolerate in the codebase.
-   **The PR Review as Culture:** If a team merges PRs with zero tests and unhandled Exceptions for 3 months, that is their culture. A Staff Engineer changes the culture by refusing to approve those PRs (holding the line) and automating the standards via CI gates (Detekt/Jacoco).
-   **The Post-Mortem Culture:** When a junior engineer breaks production, does the team scream at them, or do they write a blameless post-mortem analyzing the systemic failure of the deployment pipeline? A Staff Engineer actively shapes this response, transforming a culture of fear into a culture of continuous learning.

### 2. The Tech Lead (TL) vs The Staff Engineer
Often, a Senior Engineer operates as a "Tech Lead" for a specific squad (e.g., The Checkout Squad). The Staff Engineer operates above the squad level.
-   **The Tech Lead (Squad Level):** Focused on delivery. "How do we implement this specific feature by Friday? How do I unblock Alice on this bug?"
-   **The Staff Engineer (Org Level):** Focused on capability. "Why does it take the Checkout squad 3 weeks to build a feature? Because they lack a generic networking layer. I will build the generic networking layer so *every* squad can ship features in 1 week."

### 3. Leading Through "Glue Work"
Much of technical leadership is invisible work that keeps the machine running. Tanya Reilly famously coined this "Glue Work."
-   It is noticing that the iOS team and Android team are defining the analytics events slightly differently, leading to corrupt data for the Data Science team.
-   It is organizing a cross-platform meeting, writing an RFC for a unified JSON schema, and pushing the teams to adopt it.
-   No one asked you to do this. There was no JIRA ticket. But if you didn't do it, the company's analytics would be useless. That is Technical Leadership.

### 4. Technical Strategy (The 1-Year Horizon)
A Senior Engineer solves the problem of today. A Staff Engineer solves the problem of next year.
-   If you have a monolithic Android app, a Senior Engineer figures out how to compile it faster today by tweaking Gradle flags.
-   A Staff Engineer realizes that hiring projections show the team growing from 20 to 50 engineers in 12 months. The monolith will completely collapse under that weight. The Staff Engineer writes a 6-month roadmap for Modularization, secures buy-in from the Engineering Manager, and begins executing the first phase today.

## Common Pitfalls
-   **The Dictator:** Dictating technical choices from on high without writing code yourself. "We are moving to MVI because I read a blog post. Implement it." You will be ignored or resented. Technical leaders must lead by example, building the prototypes and fixing the bugs alongside the team.
-   **Abandoning the Code:** Assuming that because you are a "Leader," you should stop coding and only attend meetings. If you stop coding, your technical skills atrophy. You lose the ability to accurately assess technical risk. You must aggressively block out time (at least 30-40% of your week) for deep, focused engineering work.
-   **Managing People:** Slipping into the Engineering Manager role because the team currently lacks a good manager. You start doing 1-on-1s and managing PTO requests. While noble, this destroys your bandwidth for Technical Leadership. A Staff Engineer partners with the EM; they do not replace them.
