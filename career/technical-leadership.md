# Career: Technical Leadership

> Leadership without management. You lead through code, architecture, RFCs, and influence — not through HR authority. A Staff Engineer is a Technical Leader; an Engineering Manager is a People Leader. Sometimes the same person; usually not.

---

## Leadership ≠ Management

| Management (EM) | Technical Leadership (Staff) |
|---|---|
| 1:1s, comp planning, PIPs, hiring | Architecture, RFCs, code, mentorship |
| Career growth conversations | Career growth *via* sponsoring opportunities |
| Shielding the team from org politics | Engaging in org politics for technical outcomes |
| Headcount, budgets, ratios | Tech-debt budgets, error budgets, performance budgets |
| Owns *who* and *when* | Owns *what* and *how* |
| Authority: organizational | Authority: earned through demonstrated judgment |

A healthy team has both. A team with strong EM and weak Tech Leader ships features without architectural coherence; a team with strong Tech Leader and weak EM produces beautiful architecture nobody is accountable to deliver.

You do not need direct reports to be a Technical Leader.

---

## Where The Power Comes From (Without Authority)

A Staff engineer cannot fire anyone. Cannot deny PTO. Cannot allocate budget. So how does anything get done?

### Demonstrated technical judgment

Every load-bearing technical decision you make right (or wrong) compounds. After two years of Staff-level decisions that consistently *worked*, peers default to your judgment on hard problems. After two years of Staff-level decisions that consistently *failed*, they don't — regardless of your title.

This is the hardest currency to earn and the easiest to spend down. One bad RFC nobody reads (because your last three RFCs over-architected the problem) takes a year to recover from.

### Visible mentorship

When the engineers you sponsor get promoted, peers want to work with you. When you publicly credit others for their wins, they reciprocate when you need help. When you stay late helping a junior debug, that junior becomes a Senior who advocates for your RFCs five years later.

### Owning the unowned

The org has dozens of broken things nobody owns. Pick one; fix it; document it. Now you have credibility to propose the fix for the next one. Stack five such wins, and you can propose anything.

### Writing things down

The engineer who writes the architecture doc *is* the architect. The engineer who writes the runbook *is* the on-call lead. The engineer who writes the hiring rubric *defines* the team's bar. Writing converts your opinion into the team's reality.

---

## Setting Engineering Culture

Culture is what the team *tolerates*. The Staff engineer is one of the small group of people who set what gets tolerated.

### Examples in practice

| Cultural signal | What it says about the team |
|---|---|
| PRs land with 0 tests | The team doesn't believe tests pay back |
| PRs require 2 approvals from CODEOWNERS | The team values consensus over speed |
| Crash-rate gating blocks the rollout | The team prioritizes user experience over launch dates |
| Post-mortems are blameless and rigorous | The team learns from incidents |
| Post-mortems become finger-pointing | The team will hide future incidents |
| RFCs are the default for non-trivial work | Architectural decisions are deliberate |
| "We can do this Slack-DM" decisions | Decisions are made by the loudest voice |

### How a Staff engineer shifts culture

1. **Hold the line on PRs.** When you review, reject PRs that don't meet the bar. Explain why. Suggest the fix. This is uncomfortable; it's the job.
2. **Automate the standards in CI.** Detekt, Lint, Spotless, ktlint, JaCoCo coverage gates, Macrobenchmark perf gates, Crash-rate auto-halt. The CI is the durable enforcer; your reviews are the calibration.
3. **Write the post-mortem template.** Make blameless analysis the default. Lead by example: write yours rigorously, especially the ones where you made the mistake.
4. **Document the decision process.** RFCs in a folder; ADRs in another folder. Make it impossible for a new engineer to argue "we never decided that."
5. **Show up at hiring.** The bar you set in interviews is the bar you'll work with for years.
6. **Public credit, private criticism.** Public praise costs nothing; never criticize publicly.

---

## The Tech Lead vs The Staff Engineer

In many orgs, a Senior engineer becomes the **Tech Lead** (TL) of a squad. The TL is delivery-focused: shipping the team's roadmap on time. A Staff engineer operates *above* the TL layer.

| Role | Scope | Primary metric |
|---|---|---|
| TL (Senior in TL role) | One squad's roadmap | On-time delivery; team velocity |
| Staff | Multiple squads / org | Capability, leverage, durability |
| Senior Staff / Principal | Entire mobile platform | Strategy: where will we be in 3 years? |

Concrete example:

- **TL question:** "How do we implement the checkout flow by Friday?"
- **Staff question:** "Why does it take the checkout squad 3 weeks to build a feature that takes the feed squad 1 week? It's the lack of a shared networking layer. I'll build that layer."

The Staff engineer's value is *capability creation*. Every Staff-shipped piece of infrastructure or pattern should let multiple squads ship faster.

---

## Glue Work As Leadership

Tanya Reilly: "The work that holds the team together but isn't anyone's job."

Glue work examples in mobile:

- Catching that iOS and Android log analytics events with slightly-different schemas. Calling a meeting; writing an RFC; aligning both platforms.
- Realizing the on-call rotation has no runbook. Writing it; testing it with a new joiner.
- Two adjacent teams are independently solving the same problem. Connecting them; building the leverage.
- Recruiting needs a calibrated Staff Mobile interview loop. Writing the rubric; training interviewers; sponsoring candidates.
- Engineering blog has been dormant; nobody is sharing learnings publicly. Restarting it; soliciting drafts.

Glue work is invisible by default. Two things make it visible-enough to count:

1. **Document the work in writing.** RFCs, runbooks, blog posts, hiring rubrics. The artifact is the evidence.
2. **Surface impact in business terms.** "I aligned the analytics schema across platforms; the data team estimates this recovered ~30% of previously-corrupt event data." That's a sentence the EM can put in your packet.

The danger: spending 100% of your time on glue work and burning out. Reilly's rule: cap glue work at ~20% of your time. The other 80% is high-leverage engineering. Glue is the lubricant, not the engine.

---

## Technical Strategy (The Multi-Year Horizon)

A Senior solves today's problem. A Staff solves next year's.

### Concrete example: modularization

**Senior framing:** "Build times are slow. Let me tweak Gradle flags this week to save 2 minutes."

**Staff framing:** "Build times are slow *now*. Hiring projections show the team going from 20 to 80 engineers in 18 months. The monolith will collapse. I'll write a 12-month modularization roadmap, secure EM buy-in, and start with the first module this quarter so we have concrete proof-of-concept data by H2."

Both engineers' work is useful. The Senior fix is faster ROI on a smaller scope. The Staff fix sets the org up for survival.

### How to develop strategic thinking

1. **Read your org's roadmap.** What features ship next year? What does the architecture need to be to support them?
2. **Read hiring projections.** Team-size growth changes which architectures collapse.
3. **Talk to peer Staff engineers in adjacent orgs.** What are *they* designing for? What do *they* see as inevitable?
4. **Track industry direction.** What's Compose Multiplatform shipping in 6 months? What's KMP maturity at? What's the new Android API level adding?
5. **Write speculative one-pagers.** "If we're going to need offline-first across all features in 2 years, what does the architecture look like? What's the first step we'd need to take today?"

Most of these one-pagers never ship as RFCs. The exercise is what matters — you're building the muscle of *seeing ahead*.

---

## Sponsoring vs Mentoring

- **Mentor** advises. "Here's how I'd approach that. Here's a useful book."
- **Sponsor** *uses their authority* to put the mentee in the room. "I told the VP you should present at the all-hands. Here's prep time."

Mentorship costs little; sponsorship costs reputation capital. Staff engineers spend that capital deliberately.

### How to sponsor effectively

1. **Identify high-potential engineers** in your org who don't yet have visibility. (Often women, underrepresented groups, junior engineers.)
2. **Recommend them for stretch projects.** "I think Priya is ready to lead the next cross-team RFC. I'll back her up if she needs me."
3. **Recommend them for visibility moments.** "Have Priya present the modularization update at all-hands instead of me."
4. **Recommend them in promotion discussions.** Your support of a peer's promotion can tilt the committee.
5. **Pull them into adjacent conversations.** "Priya should be in the room when we discuss the API contract; she'll own this surface next quarter."

Sponsorship is where Staff engineers' influence becomes generational. The engineers you sponsor today become the Staff engineers you work with in 3 years.

---

## Anti-Patterns

- **The Dictator.** Dictating choices without building anything. "We're moving to MVI; just do it." Engineers tune you out. Lead by example: write the first prototype, then ask the team to adopt the pattern.
- **The Architecture Astronaut.** All UML, no code. Decisions look elegant on paper, fail on the compiler. Stay 30-40% hands-on.
- **Abandoning code.** Stops coding entirely; technical skills atrophy; can't accurately assess risk. The team stops trusting your judgment.
- **Doing your EM's job.** Slipping into people management because no EM is available. Noble; destroys your bandwidth. Lobby for the hire.
- **Glue-work-only.** Doing 100% lubrication, 0% engine. Burns out within a year; doesn't ship anything you can put in a packet.
- **The single-context expert.** Knows the codebase in obsessive detail; knows nothing about the iOS app, the BFF, or the data team's needs. Can't make cross-team trade-offs.
- **Avoiding politics.** Refusing to engage in stakeholder management. Decisions get made without you in the room; you complain about them later.
- **Public criticism.** Calling out an engineer's bad PR in a 30-person Slack channel. Costs you sponsorship capital with everyone watching.
- **Withholding credit.** Taking sole credit for cross-team work. Burns the relationships you depend on for the *next* cross-team work.

---

## Probing Questions

1. What's the difference between Technical Leadership and Engineering Management?
2. Why can't you be a Technical Leader on authority alone?
3. Give an example of "owning the unowned." What's the smallest version that still demonstrates leadership?
4. What's the difference between mentorship and sponsorship? Why is sponsorship harder?
5. How do you set engineering culture if you can't fire anyone?
6. Why is glue work undervalued? How do you make yours visible?
7. What's the time horizon a Staff engineer should optimize for? How is it different from a Senior's?
8. How do you stay hands-on with code while taking on more meetings, mentorship, and writing?

---

## Further Reading

- [`scope-and-ambiguity.md`](scope-and-ambiguity.md) — what Staff scope feels like.
- [`writing-rfcs.md`](writing-rfcs.md) — the leadership artifact.
- [`senior-to-staff-progression.md`](senior-to-staff-progression.md) — the paradigm shift.
- [`../leadership/influence-without-authority.md`](../leadership/influence-without-authority.md) — the muscle for technical leadership.
- [`../leadership/technical-mentorship.md`](../leadership/technical-mentorship.md) — how mentorship becomes leadership.
- [Tanya Reilly — "Being Glue"](https://noidea.dog/glue) — the canonical talk.
- [Charity Majors — "The Engineer/Manager Pendulum"](https://charity.wtf/2017/05/11/the-engineer-manager-pendulum/) — why these are different jobs.
- [Lara Hogan — "Influence Maps"](https://larahogan.me/blog/influence-maps/) — practical tool for navigating org influence.
