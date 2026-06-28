# Career: Performance Reviews & The Promotion Packet

> In a perfect world, brilliant code is noticed and you're promoted. In the real world, you write a packet. Promotion to Staff is a documented business case to a committee that has likely never met you. The packet is the artifact; everything else (the brag doc, the EM alignment, the project hunting) is in service of producing it.

---

## The Promotion Truth

- Promotions are made by committees, not by your manager alone. Your EM is your *sponsor*; the committee is the *decision-maker*.
- Committees evaluate against a rubric. Your packet is the evidence that you've been operating against that rubric *for at least two cycles*.
- You can't be promoted on a single brilliant project. You can be promoted on a consistent pattern.
- Most denials are not about technical ability; they're about *insufficient evidence of the right kind of impact*. Often the work was done, the case wasn't made.

The Senior-to-Staff jump is the hardest because the rubric shifts from "great IC work" to "great work that lifts the organization." Until you internalize that shift, you'll be doing senior work and waiting to be discovered.

---

## The Brag Document

You will not remember what you did in February when you write your H2 review in October. You will undercount your impact by 50-70% from memory. The brag document fixes this.

### The format

```markdown
# 2026 Brag Doc — <Your Name>

## Q1 (Jan-Mar)

### January
- **2026-01-08:** Modularization RFC published. 11 inline comments addressed; approved by 2 tech leads and EM. Link: <RFC URL>.
- **2026-01-15:** Mentored Priya through her first cross-team API contract. She landed it 2 weeks later; her EM thanked me in 1:1. Slack screenshot saved.
- **2026-01-22:** Tracked down OEM-specific crash on Xiaomi POCO M3. Fix landed in v4.2.0; Crashlytics shows 90% reduction in OOM on that device class. Dashboard link saved.

### February
- **2026-02-03:** Drove the kickoff for the offline-first redesign across mobile + backend. Wrote the alignment doc; ran two design reviews; both teams agreed on the contract. Doc link saved.
...

## Q2 (Apr-Jun)
...
```

### The discipline

- **Every Friday afternoon, 10 minutes.** Block it on your calendar. Treat it as inviolable.
- **Capture screenshots and links** the moment they happen. Slack messages get archived; PRs get closed; dashboards get deleted. Save them now.
- **Distinguish three categories** as you write:
  - **Senior work:** "Closed 23 JIRA tickets," "Fixed the login bug," "Implemented the feature spec." Necessary but not promotion-worthy on its own.
  - **Staff-aspiring work:** "Wrote an RFC that 8 engineers across 3 teams reviewed and adopted," "Mentored 2 engineers through a complex migration," "Identified a systemic issue, proposed a fix, drove adoption."
  - **Cross-org work:** "Partnered with iOS lead to standardize the API contract format," "Spoke at the engineering all-hands about modularization," "Hired 1 Senior engineer; brought 2 candidates through the loop."

By Q3, you'll have a year of evidence sorted into the rubric categories. The packet writes itself.

---

## Managing Up

Your EM is your sponsor. Sponsors need ammunition and alignment.

### The promotion conversation (own the initiation)

Most EMs don't bring up promotion until you do. They have 6-12 reports; they're not tracking the rungs ladder-by-ladder for you. *You initiate.*

Template for the first conversation:

> "I want to set Staff as my goal for the next 12-18 months. I'd like to:
> 1. Walk through the rubric together to agree on where I am and where the gaps are.
> 2. Identify 1-2 projects in the next 2 quarters that would let me build the missing evidence.
> 3. Establish a quarterly checkpoint so we're aligned before review season."

This frames it as a *partnership* (you're asking for their help, not for the promotion itself), gives them ammunition (specific projects to hunt for), and creates rhythm (checkpoints prevent surprises).

### The rubric check

Almost every company has an engineering ladder (Google L4/L5/L6, Meta E5/E6, etc.). The rubric is usually a 1-3 page document listing dimensions (technical scope, leadership, communication, mentorship, business impact) and what "meets" looks like at each level.

In your 1:1 with your EM, walk through it dimension-by-dimension:

| Dimension | Senior bar (your current) | Staff bar | Gap |
|---|---|---|---|
| Technical scope | Owns a feature or subsystem | Owns a cross-team architecture | "I'm running 1 cross-team initiative; need a second." |
| Leadership | Mentors 1-2 engineers | Mentors others to mentor | "I should sponsor someone leading their first mentee." |
| Communication | Writes RFCs, drives reviews | Sets the bar for RFCs in the org | "My RFCs are good; I should be running RFC workshops." |
| Business impact | Ships features on time | Ships work that moves a top-line metric | "Need to tie my modularization work to engineer productivity dollars." |

Now you have a concrete project list and a measurable gap.

### Quarterly checkpoints

Each quarter:
1. Pull the brag doc.
2. Walk through it with your EM.
3. Tag each entry as Senior / Staff-aspiring / Cross-org.
4. Agree: am I trending? What do I need more of next quarter?
5. Update the project hunt.

This is calendar work, not heroics. Promotions happen because of consistent quarterly checkpoints, not because of brilliant Q3.

---

## The Promotion Packet

When it's time, the packet is your closing argument. The structure varies by company; the substance is universal.

### Standard sections

```markdown
# Promotion Packet: <Name> — Senior → Staff Engineer

## Self-Summary (1 paragraph)

The thesis. One paragraph that, if a Director read only this, would communicate
your impact. "In the past 18 months I've led three cross-team initiatives that
collectively reduced cold start by 40%, eliminated a class of OOM crashes
affecting 0.4% of sessions, and modularized the build to drop p90 CI time from
22 minutes to 6 minutes. I've sponsored 3 engineers through stretch projects,
two of whom were promoted, and I've represented the Android team in the
company's mobile API council."

## Impact (the bulk of the packet)

For each major initiative, use the STAR format:

### Initiative 1: Modularization

**Situation:** Build times had crept from 8 min (2024) to 22 min (2026). Engineers were context-switching during the CI wait, costing ~9h/day across the org.

**Task:** Reduce build time without halting feature development.

**Action:** I led the modularization RFC (link); aligned with 3 feature teams on the sequencing; extracted 4 core modules in 6 weeks; introduced Gradle Remote Build Cache (Develocity). I documented patterns and ran a workshop for the 3 feature-team leads to extract their modules.

**Result:** P90 build time: 22 min → 6 min. P50 incremental build: 6 min → 1.4 min. Internal survey shows 87% of engineers report meaningful productivity improvement.

**Impact in business terms:** Recovered ~7 engineer-hours/day across the org. At fully-loaded cost, ~$1.4M annualized productivity recovery.

### Initiative 2: ...

### Initiative 3: ...

## Cross-Functional Impact

- Mentoring: <names and outcomes>
- Hiring: <interviews, decisions influenced>
- Industry/external: <talks, blog posts, OSS contributions>
- Org-wide: <RFCs adopted, processes you established>

## Rubric Self-Assessment

A table mapping the rubric dimensions to specific examples in the packet.

| Dimension | Evidence |
|---|---|
| Technical scope | Initiative 1 (multi-team architecture); Initiative 3 (platform library used by 4 teams) |
| Leadership | Mentored 3; sponsored 2; ran the RFC workshop |
| ... | ... |

## Peer / Sponsor Feedback

Quotes from peers, dotted-line stakeholders, and engineers you've worked with closely. Get these *before* you submit the packet; ask them what specifically they observed.

## Appendix

Links: RFCs, PRs, dashboards, recorded talks. Make it easy for the committee to verify.
```

### What committees actually look for

- **Pattern, not peak.** Three Staff-shaped initiatives over 18 months beats one heroic project.
- **Verifiable evidence.** Links to RFCs, PRs, before/after dashboards. Adjectives without numbers lose to numbers without adjectives.
- **Business framing.** Translate "we modularized" into "we recovered $1.4M of engineer productivity."
- **Cross-team breadth.** Staff is measured on impact *outside* your team. If all your evidence is intra-team, you're being promoted to a stronger Senior, not to Staff.
- **Sponsor diversity.** A packet with feedback from just your direct EM is weaker than one with feedback from a peer EM, an iOS lead, a Product Manager, and a Director.

### What kills packets

- "We were the first team to..." — no measurable outcome.
- "I'd estimate..." — no actual measurement; the reader doesn't trust it.
- Long lists of Senior-level wins; no Staff-level wins.
- Heavy on architecture; light on people impact.
- No mention of any failure or any lesson learned. Maturity-signal absent.

---

## Handling "No"

Most Staff promotions are denied at least once. The denial is data, not a verdict.

### The Junior reaction

- Anger at the committee.
- Quietly job-hunting.
- Asking your EM "what about now?" every 6 weeks.
- Concluding that the system is rigged.

This locks you out of the next cycle.

### The Staff reaction

1. **Ask the committee (via your EM) for the specific gap.** Not "you weren't strong enough" but "the committee felt your impact was concentrated in one team; they wanted more evidence of organizational reach."
2. **Validate the gap.** Sometimes the feedback is wrong; sometimes you have evidence the committee didn't see. Push back via your EM if so.
3. **Adjust the project hunt.** If the gap is "cross-team," your next 6 months are about taking on a cross-team initiative.
4. **Recalibrate the timeline.** Two more brag-doc cycles, then re-submit.
5. **Don't job-hop just because of the denial.** Job-hopping for a title at another company often resets you to the bar at that company. The promotion you earn at your current company is more durable.

A "no" with feedback you can act on is a *plan*, not a rejection. Most successful Staff promotions reference the previous denial in the resubmission ("To address the feedback from the H1 cycle, I led the cross-platform API standardization...").

---

## Common Anti-Patterns

- **The Silent Martyr.** "If I just work hard, I'll be noticed." Visibility is part of the job. Present at all-hands. Write engineering blog posts. Take credit publicly.
- **The Competitor.** Viewing peer Seniors as rivals for a promotion slot. There's no slot — Staff is a bar, not a quota. Tearing down peers fails the "lifts others" criterion.
- **The Heroics Trap.** A single 6-week sprint that saved the launch is a Senior story. Sustained Staff-level work over 18 months is a Staff story. Heroics burn you out and skew your packet.
- **The Vague Brag Doc.** "Worked on cool stuff" entries. Useless 6 months later.
- **Sandbagging your own work.** Underselling impact because you're modest. The committee can't infer what you don't write.
- **Inflating your own work.** Claiming credit for things you contributed to but didn't lead. The committee verifies; inflation costs you credibility for years.
- **Surprised at review time.** No quarterly checkpoints with your EM; you submit a packet they haven't co-developed; they can't defend it. The packet must be a *partnership*.
- **Treating Staff as a title, not a role.** Some people just want the title. The committee can smell it. Staff is more responsibility, not just more pay.
- **Asking for promotion before you're consistently operating at the next level.** Two cycles of Staff-level work is the minimum. You must already be doing the job before you ask for the title.

---

## Probing Questions

1. Why is the Senior-to-Staff jump harder than Mid-to-Senior?
2. What's the difference between "I shipped Feature X" and "I drove an organizational improvement that incidentally produced Feature X"?
3. How would you start a brag document if you're 18 months in and haven't kept one?
4. Your EM is supportive but doesn't know how to find you Staff-shaped projects. How do you help?
5. What's the failure mode of optimizing for the *promotion* instead of optimizing for *Staff-level impact*?
6. Why is peer/sponsor feedback in the packet important? What kinds of quotes carry weight?
7. You're denied. What's the first conversation you have with your EM?
8. When is the right time to leave for another company instead of waiting for the next cycle?

---

## Further Reading

- [`scope-and-ambiguity.md`](scope-and-ambiguity.md) — what Staff-shaped work looks like.
- [`senior-to-staff-progression.md`](senior-to-staff-progression.md) — what shifts at the rung jump.
- [`technical-leadership.md`](technical-leadership.md) — the leadership dimension that gets packet evidence.
- [`writing-rfcs.md`](writing-rfcs.md) — the artifact that becomes packet evidence.
- [Will Larson — "Staff Engineer"](https://staffeng.com/book) — the canonical reference.
- [Julia Evans — "Get your work recognized: write a brag document"](https://jvns.ca/blog/brag-documents/) — the technique's origin.
- [Tanya Reilly — "The Staff Engineer's Path"](https://www.oreilly.com/library/view/the-staff-engineers/9781098118723/) — the chapter on packets is excellent.
