# Career: Scope and Ambiguity

> The defining characteristic of engineering levels is *how much ambiguity you can process* and the *blast radius* of your decisions. Junior engineers need precise tickets and own buttons; Staff engineers operate in "the app feels slow, fix it" and shape the org.

---

## The Ambiguity-Scope Ladder

| Level | Ambiguity tolerated | Typical scope | Decision blast radius |
|---|---|---|---|
| Junior | Low. Needs a ticket with steps. | One button, one screen task. | A bug in their code blocks one user flow. |
| Mid | Moderate. Ticket with a goal. | One screen, one feature flow. | A bug breaks a feature for some users. |
| Senior | High. 3-sentence feature request. | An entire feature, a module, a subsystem. | A bad call slows their team for a quarter. |
| **Staff** | **Total.** "The app feels slow." | **Multiple teams, the whole platform.** | **A bad call sets the org back a year.** |
| Principal | Strategic. "Where will mobile platforms be in 3 years?" | The company. | Defines what success means. |

The promotion criterion at each step: *can you operate one rung up* — handle one rung more ambiguity, ship work with one rung more blast radius. You don't get promoted by becoming a better Senior; you get promoted by acting Staff for two quarters.

---

## Navigating Total Ambiguity

Total ambiguity sounds like:

> "The app feels slow."
> "Our crash rate is too high."
> "We should think about modularizing the app."
> "Engagement has plateaued."

These are *prompts*, not specifications. A Staff engineer's first move is to translate them into something the team can actually work on.

### The 4-Phase Framework

#### Phase 1: Define what "done" looks like in numbers

The prompt is an emotion. Your first job is to translate it to math.

> Prompt: "The app feels slow."
>
> Translation: "Cold start TTID at p95 on mid-tier devices is 2.4s; users in tier-3 markets see 3.8s. Target: < 1.5s on mid-tier within 2 quarters."

Numbers are non-negotiable. Without them, the project drifts.

#### Phase 2: Diagnose, don't fix

Resist the urge to start coding. Spend 1-2 weeks gathering data:

- Pull Crashlytics, Vitals, internal RUM. Build a per-tier, per-OEM, per-country breakdown.
- Run Macrobenchmark. Run Perfetto traces on a real low-tier device.
- Talk to 3-5 engineers in different feature teams. The slow surface is rarely where you'd guess.

You'll often find the problem is *not* what the prompt-giver thought it was. The "the app feels slow" prompt becomes "the home screen's image-loading SDK does synchronous main-thread decode on the cold path."

#### Phase 3: Write the strategy doc (RFC)

Now write the RFC. The diagnosis becomes the Context section; the proposed fix becomes the Solution. The RFC is how you take the ambiguity from your head into the org's shared understanding.

See [`writing-rfcs.md`](writing-rfcs.md).

#### Phase 4: Sequence and ship

Break the strategy into 2-4 week milestones, each independently deliverable. Land them with crash-rate-gated rollouts. Each milestone produces a measurable improvement on the success metric.

If you can't sequence, you're not done diagnosing.

---

## Expanding Scope

**Scope isn't granted. It's taken.** You can't ask your manager for "more scope." You identify problems no one is fixing, propose to fix them, and quietly start.

### The "no one is fixing this" pattern

1. Notice the problem. Build times have crept from 8 min to 22 min over a year. Senior engineers complain on Slack; no one owns it.
2. Quantify it. "22 min × 30 PRs/day × 100 devs = ~9 hours/day lost across the org. At fully-loaded cost, that's $X/year."
3. Sketch a fix. Modularization, build cache, KSP migration, parallel test sharding.
4. Get a green light. Don't ask for a roadmap slot; ask for permission to spend 20% of your time investigating. Bring the data.
5. Land a small win. Reduce build time by 10% via one concrete change in three weeks. Now you have credibility for the bigger investment.
6. Propose the bigger investment via RFC. Get headcount allocated by named contributors from multiple teams.

You just expanded your scope from "the team you're on" to "the mobile platform org." This is the playbook.

### The dual-class superpower: cross-functional reach

Expanding scope inside engineering is necessary but not sufficient. The other axis is *cross-functional*:

- Sit with Product Managers to explain *why* the proposed offline mode is technically impossible given the current API design. Negotiate a "cached read" alternative.
- Help recruiting build a fair Staff Mobile hiring loop. The bar you set affects the team you'll have for years.
- Join the Customer Support sync once a month. The top crash classes and the top user complaints don't always overlap.
- Coach the Director of Engineering through a tech-stack decision they're not technical enough to evaluate alone.

Each of these is scope, even though none of it shows up in `git log --author`.

---

## Saying No

The cost of saying yes to something is saying no to everything else you could be doing in that time. As a Junior, the cost is small (you have one thing to do anyway). As a Staff, the cost is enormous (there are 50 things competing for your attention, and only one or two will move the org meaningfully).

### A working framework for saying no

| Ask | Default response | When you DO say yes |
|---|---|---|
| Review a 50-line UI PR | "Could a teammate review? Tag me if there's an architectural concern." | When it's in the architecture you own and a misstep will spread. |
| Estimate a Product feature you don't know | "I can spend 1 hour with the spec and give a rough order of magnitude." | When the team's actual estimator is unavailable AND the decision blocks a roadmap. |
| Join a recurring meeting | "I'll attend the first 4 to understand the context; then I'll send a delegate." | When the meeting is where your scope is being defined. |
| 1:1 with a Junior who wants mentorship | "Happy to. 30 min monthly, with a specific topic each time." | Default yes — but bounded. |
| Lead a new initiative | "Show me the data on impact and timeline; I'll respond by Friday." | When it serves the strategy you're already executing. |
| "Quick question?" in Slack | Answer in async, with the answer documented in the team wiki | If documenting the answer once removes the next 5 asks |

### The "saying no" toolkit

- **Delegate via systems.** When asked to do a repetitive thing (generate release notes, audit dependency versions), do it *once*, write a script, hand the script over. Now you've said no to the recurring ask while saying yes to it being done.
- **Coach instead of doing.** When a Senior asks you to design their feature, send them a draft template and offer to review the *first* version, not the last. They learn; you don't become their thinking-prosthetic.
- **Decline with context.** "I can't take this on because I'm finishing the modularization milestone by end of quarter. If it's blocking, here's who I'd recommend." A bare "no" creates animosity; a contextual no is professional.
- **The 24-hour rule.** For ambiguous asks, wait 24 hours before committing. Reconsider with fresh eyes. You'll say no to 60% of the things you would have said yes to in the moment.

---

## Case Studies

### Case 1: "Our app crashes too much"

**Prompt** (VP of Eng): "Crashes are unacceptable. Fix it."

**Junior response:** open Crashlytics, fix the top crashing issue. Ship. Move on.

**Staff response:**

1. Pull 90 days of Crashlytics + Vitals + Play Console. Cluster by tier, country, OEM, app version.
2. Discover 60% of crashes are `OutOfMemoryError` concentrated on Android 9 + 4GB RAM + Asia/LATAM.
3. Identify root cause: an image-loading SDK without a memory cap.
4. Write RFC: replace SDK; cap memory cache at 25% of heap.
5. Stage rollout with crash-rate gate.
6. Outcome: crash-free rate goes from 98.5% to 99.7% in 6 weeks. Documented the work; published to the engineering blog.

The Staff response made the work *systemic*. The result: future engineers know how to investigate similar problems; the SDK choice is documented in an ADR; the rollout discipline becomes the team's default.

### Case 2: "We need to modularize"

**Prompt** (EM): "Build times are killing us. Modularize the app."

**Junior response:** start ripping the app into 50 modules; quickly hit circular dependency hell; deliver nothing.

**Staff response:**

1. Measure. Current state: monolith, 22 min CI build, 6 min incremental.
2. Diagnose. 80% of incremental time is in one module (`:app`) that touches everything.
3. Strategy: extract `:core:` modules first (no UI deps); leave `:feature:` modules for phase 2; never break `:app` into pieces (it's the binary).
4. Write RFC; get sign-off on the sequencing.
5. Land phase 1: 4 `:core:` modules in 6 weeks. Build time drops from 22 min to 14 min.
6. Hand off phase 2 (feature extraction) to feature teams with a template + office-hour support.

The Staff response *scaled the work*. Not "I'll modularize the app"; rather, "I'll create the conditions where every team modularizes their feature."

### Case 3: "Why is iOS launching before Android?"

**Prompt** (CTO): "Why does iOS always launch features first?"

**Junior response:** "Because iOS team is bigger / better resourced."

**Staff response:**

1. Investigate. Find that 60% of "iOS first" cases are due to Android engineers waiting on backend changes the iOS team negotiated faster.
2. Realize the real problem is *contract definition velocity*, not Android execution speed.
3. Propose: every cross-platform feature starts with a shared API contract RFC, written by mobile + backend together at kickoff. Both platforms work in parallel against the contract.
4. Pilot on 3 features; measure time-to-launch.
5. After a quarter of data, present back: Android launches alongside iOS in 4 of 5 cases.

The CTO heard "Android is slow." The Staff response found "the contract step is the bottleneck."

---

## Anti-Patterns

- **Solving the prompt verbatim.** "The app feels slow" doesn't mean "find the slow code." It means "you have permission to redefine the problem until it's solvable."
- **Boil-the-ocean strategies.** Proposing to "rewrite the entire app in Compose" because cold start is slow. Scope down.
- **The "if I just had more headcount" trap.** Sometimes true, but more often a sign you haven't sequenced the work into something deliverable with current resources.
- **Owning everything; being expert in nothing.** Spreading across 12 initiatives = none get finished. Pick 1-2 large bets per quarter.
- **Confusing visibility with impact.** Speaking at conferences is visibility. Reducing crash rate by 1pp for 100M users is impact. The first sometimes follows the second; the second never follows the first.
- **Refusing to scope down.** "If I can't fix the *whole* problem, I won't start." The bigger the problem, the more important it is to find the smallest deliverable wedge.
- **Ambiguity as an excuse for inaction.** Total ambiguity isn't a license to wait for clarification; it's the *job*. Define your own brief.
- **Ambiguity burnout.** Constantly living in unstructured problem spaces without resolving them into executable work will burn you out. You manage ambiguity burnout by rigorously defining the "done" state, creating intermediate milestones, and handing well-defined work over to execution teams before moving to the next ambiguous problem.
- **Not-my-job mentality.** If iOS is crashing because backend deployed a bad API and Android works fine, a Staff engineer still joins the incident — the company loses money either way. The Staff job's boundary is *the product's success*, not the platform's.

---

## Probing Questions

1. Give an example of a prompt with total ambiguity. How would you spend the first two weeks?
2. Why is scope something you take, not something you ask for? How do you take it without overstepping?
3. What's the difference between visibility (talks, blog posts) and impact (measurable change)? When do they correlate?
4. You're asked to review every PR for a feature team. What's the cost of saying yes? Of saying no?
5. How do you decide between fixing the top crash (high local impact) vs writing the RFC for the next architectural cycle (high systemic impact)?
6. Describe a time you redefined a problem so it became solvable. What did the prompt actually need?
7. How do you tell a Director "no" when they're pressuring you to commit?
8. What does it look like when a Staff engineer expands scope poorly? (Hint: drama, burnt-out reports, work nobody asked for, missed actual deliverables.)

---

## Answer Key

1. **Give an example of a prompt with total ambiguity. How would you spend the first two weeks?**
   "The app feels slow." The first two weeks should be spent defining "done" with math (e.g., Target cold start < 1.5s) and diagnosing the root cause by pulling traces and analytics rather than blindly writing code.
2. **Why is scope something you take, not something you ask for? How do you take it without overstepping?**
   Scope is taken because management rarely assigns unstructured, cross-team problems. You take it without overstepping by diagnosing an unowned problem, quantifying its cost, proposing a fix via RFC, and earning buy-in incrementally through small wins.
3. **What's the difference between visibility (talks, blog posts) and impact (measurable change)? When do they correlate?**
   Impact fundamentally improves the product or engineering metrics (e.g., reducing OOMs by 20%), whereas visibility simply broadcasts your presence. They correlate when visibility is used as a vehicle to scale impact, such as using a blog post to drive org-wide adoption of a new pattern.
4. **You're asked to review every PR for a feature team. What's the cost of saying yes? Of saying no?**
   The cost of saying yes is dedicating all your bandwidth to micro-level execution, blocking your ability to drive systemic architectural work. The cost of saying no is potentially missing a bad design early on, which is why you must delegate via CI automation and selectively review only architectural boundaries.
5. **How do you decide between fixing the top crash (high local impact) vs writing the RFC for the next architectural cycle (high systemic impact)?**
   You prioritize based on business risk and leverage. If the crash is actively bleeding revenue or blocking users, it must be addressed first. Otherwise, the RFC provides higher long-term leverage by preventing entire classes of future issues.
6. **Describe a time you redefined a problem so it became solvable. What did the prompt actually need?**
   When told "iOS always launches features first," the prompt actually needed a faster cross-platform API contract phase, not faster Android execution. Redefining it to require upfront, joint API RFCs removed the blocker and solved the discrepancy.
7. **How do you tell a Director "no" when they're pressuring you to commit?**
   Use a contextual "no" paired with trade-offs. Example: "I can't take this on because I am fully committed to landing the modularization milestone by the end of Q3. If this new priority supersedes it, we will need to delay modularization to Q4."
8. **What does it look like when a Staff engineer expands scope poorly? (Hint: drama, burnt-out reports, work nobody asked for, missed actual deliverables.)**
   Poor scope expansion results in half-finished initiatives, over-architected systems disconnected from actual business needs, micromanaged engineers, and failure to deliver on the original core responsibilities.

---

## Further Reading

- [`writing-rfcs.md`](writing-rfcs.md) — the document that makes scope real.
- [`senior-to-staff-progression.md`](senior-to-staff-progression.md) — what changes between rungs.
- [`technical-leadership.md`](technical-leadership.md) — how technical work becomes leadership.
- [Tanya Reilly — "The Staff Engineer's Path"](https://www.oreilly.com/library/view/the-staff-engineers/9781098118723/) — the canonical book on this exact transition.
- [Will Larson — "Staff Engineer: Leadership Beyond the Management Track"](https://staffeng.com/) — the reference website.
- [`leadership/influence-without-authority.md`](../leadership/influence-without-authority.md) — the muscle that makes scope expansion work.
