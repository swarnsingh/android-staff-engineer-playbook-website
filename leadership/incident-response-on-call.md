# Leadership: Incident Response & On-Call (The Firefight)

## The Theory
At the Staff level, you are no longer just writing code; you are responsible for the stability of the entire system. When the Android app crashes for 500,000 users during a Black Friday sale, panic ensues. A Staff Engineer's job is to impose order on chaos, halt the bleeding, and ensure the organization learns from the failure without pointing fingers.

## Staff-Level Application in Mobile

### 1. The On-Call Rotation (PagerDuty)
On-call is not a punishment; it is the fundamental feedback loop that forces engineering teams to build resilient software. If a team builds a flaky architecture, they feel the pain directly at 3:00 AM.
-   **The Triage:** When a PagerDuty alert fires, the on-call engineer has 15 minutes to acknowledge it. Their primary goal is *not* to find the root cause and write a 500-line bug fix. Their primary goal is **Mitigation**.
-   **Mitigation over Resolution:** If the new Checkout flow is crashing, the Staff response is to toggle the Remote Config Feature Flag back to `false`, instantly routing users to the legacy, stable Checkout flow. The bleeding stops in 2 minutes. The root cause analysis (Resolution) can happen at 10:00 AM on Monday during normal working hours.

### 2. The Incident Commander (IC) Role
During a SEV-1 (Severity 1) incident, multiple teams are involved (Mobile, Backend, DevOps, Customer Support). If everyone is shouting in a Slack channel, nothing gets fixed.
-   A Staff Engineer often acts as the **Incident Commander**.
-   The IC does *not* look at code. The IC does *not* query logs.
-   The IC coordinates the humans. They assign roles (e.g., "Sarah, investigate the API gateway logs. John, prepare the rollback binary."). They enforce communication discipline ("Keep the main Slack channel clear of chatter; use threads for investigation."). They communicate status updates to executive stakeholders so the engineers can focus on the fix.

### 3. The Blameless Post-Mortem (COE)
Once the fire is out, a Correction of Errors (COE) or Post-Mortem document must be written. A Staff Engineer champions the **Blameless** culture.
-   **The Anti-Pattern:** "Bob merged a bad PR that crashed the app. Bob needs to be more careful." This teaches engineers to hide their mistakes and breeds fear.
-   **The Staff Pattern:** "A PR bypassed the automated UI tests because the CI runner was misconfigured. Why did the CI runner misconfigure? Why didn't the staging rollout catch the crash before 100% production? We will implement a new Detekt rule to catch this automatically." We blame the *system*, not the human.

### 4. The 5 Whys
During the Post-Mortem, use the "5 Whys" technique to drill past the superficial symptom down to the systemic root cause.
1.  *Why did the app crash?* Because a `NullPointerException` occurred in the Checkout ViewModel.
2.  *Why was the data null?* Because the backend returned a null `shipping_address` field.
3.  *Why did the app crash when the backend returned null?* Because the Retrofit data model declared `shipping_address` as a non-null `String` instead of `String?`.
4.  *Why did the mobile model diverge from the backend reality?* Because the teams do not share a unified OpenAPI (Swagger) schema.
5.  *Why don't we have a unified schema?* **Root Cause:** We lack an automated contract testing pipeline. **Action Item:** Integrate GraphQL or OpenAPI generation into the CI build by Q3.

## Common Pitfalls
-   **Alert Fatigue:** If PagerDuty pages the team 10 times a week for non-actionable events (e.g., "CPU usage spiked to 80% for 2 minutes but recovered automatically"), engineers will start ignoring the pager. Staff engineers ruthlessly delete alerts that do not require immediate human intervention. Alerts should only fire for user-facing impact (e.g., "Checkout conversion dropped by 15%").
-   **The Hero Complex:** A Staff engineer who constantly jumps in at 3:00 AM, fixes the bug single-handedly, and saves the day without documenting the process or training others is a massive single point of failure. True leadership is building playbooks (runbooks) so that a junior engineer can resolve the SEV-1 without waking you up.
