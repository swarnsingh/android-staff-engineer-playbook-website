# Leadership: Escalation and Decision Making

> When to push a decision *down* (let the team decide), *across* (peer-debate it), or *up* (escalate to the EM/Director). Escalation badly done burns trust; escalation done well unblocks the org. The Staff engineer's discipline is knowing the difference and executing the routing without drama.

---

## The Decision Routing Question

Every important technical decision has a *right level* to be decided at. Get this wrong and one of two failure modes:

- **Under-routed.** The team decides something that should have gone to the Director. Six months later, the Director discovers it and unwinds the work.
- **Over-routed.** Every minor architectural choice gets escalated to the VP. The VP loses confidence in the team; the team becomes paralyzed waiting for sign-off.

The Staff engineer's job is to route correctly. The framework:

| Decision type | Where it should be decided |
|---|---|
| Library choice within one module | The IC working on the module |
| Cross-module architectural pattern | Tech leads of the affected teams |
| New top-level dependency for the app | Staff + Tech leads (RFC) |
| Investing 3+ engineer-weeks of capacity | EM + Staff |
| Investing > 1 engineer-quarter | Director + EM + Staff |
| Breaking an external API contract | Cross-org leadership + Product |
| Hiring decisions | EM (Staff advises) |
| Going on-call rotation policy | EM + Tech leads |
| Security boundary changes | InfoSec + Staff + EM |
| Strategic platform direction | VP + Staff senior leadership |

---

## The DACI Framework

For each non-trivial decision, name four roles:

| Role | What they do |
|---|---|
| **D — Driver** | Owns the decision process. Schedules, writes the RFC, ensures the decision *happens*. |
| **A — Approver** | Says yes or no. Usually 1 person (max 2). |
| **C — Contributors** | Provide input. Have weight in shaping the decision. Multiple. |
| **I — Informed** | Need to know the outcome but don't have to weigh in. |

DACI is the antidote to "everyone in this meeting has an opinion and we can't decide." If you can't name the **A** in a single sentence, you don't have a decision-making structure — you have a discussion.

### Staff engineer's role in DACI

- Most often the **Driver** for cross-team technical decisions.
- The **Approver** for architectural choices within their scope.
- A **Contributor** for adjacent-team decisions.
- An **Informed** for product/business decisions where the architecture is downstream.

Naming the right roles up-front saves weeks of friction.

---

## When To Escalate (And When Not To)

### Escalate when:

- **A peer disagreement is blocking progress and you've tried to resolve it directly.** Escalation forces a decision; it doesn't decide for you.
- **The decision needs authority you don't have.** Headcount allocation, vendor contracts, cross-org coordination.
- **A timeline is slipping for systemic reasons** (the BFF team is overloaded; the iOS team rejected the contract). The EM/Director can re-prioritize across teams.
- **A security or compliance risk** that the team can't fix at its level.
- **Cultural breakage** (a peer team consistently merges without tests; you've raised it; nothing changes).
- **A pattern is repeating** (this is the third time the same kind of bug shipped; the system needs to change).

### Don't escalate when:

- **You haven't tried to resolve it directly.** Going around your peers to their manager destroys peer relationships.
- **You're losing an argument and want a parent to overrule.** The Director will see this; you'll lose credibility.
- **The decision is genuinely yours to make.** Escalating decisions you own makes you look indecisive.
- **You're escalating a person, not a problem.** "Bob is hard to work with" without specifics is character assassination, not escalation.
- **No specific ask.** "I want to escalate that things feel off." Escalation requires a yes/no question.

---

## The Escalation Template

When you do escalate, do it in writing first. Verbal escalations get misremembered.

```
Subject: Escalation: <one-sentence summary>

Context (2-3 sentences):
What's happening, who's involved, what's already been tried.

Decision needed:
Specific yes/no question. "Should we delay the launch by 2 weeks to address
the security finding, or ship as-is with a follow-up in v4.3?"

What I've tried:
- 2026-06-12: 1:1 with backend lead; no agreement.
- 2026-06-15: design review meeting; no resolution.

Recommendation:
What I would do if I had authority. Reasoning in 3-5 bullet points.

Cost of delay:
What happens if this isn't decided by <date>. "Each week of delay costs
about 50 user-weeks of impact on the metric."

Stakeholders:
- D: <Driver>
- A: <Approver — usually the recipient of this email>
- C: <Contributors>
- I: <Informed>
```

The recipient reads this in 90 seconds, makes a decision in their next 1:1 with you, and the path forward is clear. Escalation done well is *fast*.

---

## Disagree-And-Commit

Once a decision is made (at the right level, with the right input), the disagreeing parties commit fully. They do not:

- Re-litigate the decision in Slack the next day.
- Tell juniors "I disagreed with this but I was overruled."
- Drag their feet on implementation.

They do:

- State their disagreement clearly during the decision.
- Argue forcefully; lose; commit; execute as if it was their choice.
- If new information emerges, re-open the decision via the normal channel (RFC, escalation), not via passive resistance.

The Staff engineer's discipline is making the commitment *visible*. After a decision goes against you:

> Public Slack: "We're going with X. I argued for Y; the team and I weighed the trade-offs; X is the right call given the constraints. Here's how I'm helping execute it: [link to PR / RFC]."

This signals to juniors that disagreement is healthy *and* that healthy teams converge.

---

## The "Type 1 vs Type 2" Framework (Bezos)

Two kinds of decisions:

- **Type 1 (one-way doors).** Hard or impossible to reverse. Switching databases. Choosing a vendor with a 3-year contract. Adopting a different language for the entire codebase. Demands rigor, multiple alternatives, ADR, sign-off, time.
- **Type 2 (two-way doors).** Easy to reverse. Trying a new naming convention. A small experimental feature. A new test framework on one module. Decide fast; reverse if wrong.

Most teams over-rigor Type 2 decisions and under-rigor Type 1 decisions.

### The Staff engineer's contribution

- Recognize the type. Many "Type 1" decisions are actually Type 2 in disguise (the database can be migrated; the vendor can be switched at renewal). Many "Type 2" decisions are actually Type 1 (the naming convention will leak across the codebase and be impossible to revert).
- Match the process to the type. Type 1 gets RFC + ADR + sign-off. Type 2 gets a Slack message + try it.
- Decline to over-process Type 2 decisions, even when others want to. The team's velocity depends on it.

### Architecture governance triggers

Some decisions should automatically enter the RFC/design-review path.

| Trigger | Required process |
|---|---|
| New top-level dependency or vendor | 1-pager or RFC + platform/security review |
| New cross-team API contract | RFC + contract-test plan |
| New persistence/sync protocol | RFC + migration/rollback plan |
| Security/privacy boundary change | RFC + InfoSec/legal review |
| Build/release pipeline change | RFC or ADR + releng approval |
| Deprecating a shared module/API | ADR + migration/deprecation plan |
| Decision consumes more than one team for a quarter | Director-visible 1-pager + RFC |

This is governance without a committee for every choice. The trigger list lets teams move fast locally while routing high-blast-radius decisions deliberately.

---

## Disagreeing With Your Manager

Eventually you'll disagree with your EM or Director on something that matters. Three options:

1. **Disagree privately, commit publicly.** Most common path. State your disagreement in your 1:1; commit fully in public; revisit if you have new data.
2. **Disagree publicly, professionally.** "I want to flag for the team that I've raised concerns about X; the EM and I have discussed; we've decided to proceed with X for these reasons. I want everyone to understand the trade-offs." This is *appropriate* when the disagreement is substantive and the team needs to know what's at stake.
3. **Escalate above your manager.** Last resort. Only for serious issues (safety, ethics, irrecoverable strategic mistake). Use the formal escalation template. Burns trust with your EM; sometimes worth it.

Never: silent resistance, smug "I told you so" after the fact, recruiting allies to undermine the decision.

---

## Difficult Conversations: Templates

### "I disagree with this decision"

> "I want to push back on X. The reasoning I see is [their reasoning]; my concern is [your counter]. Specifically: [evidence]. I'm not asking to overturn the decision — I want to make sure the trade-off is explicit. If we still want to proceed, here's what I'd do to mitigate [concern]."

### "We need to escalate"

> "I think this needs to go to [name]. We've discussed for [time]; the disagreement is at the level of [authority / org alignment / risk]; it's appropriate for [name] to make the call. I'll draft the escalation note today; do you want to co-author or review?"

### "I think you're wrong about [important thing]"

> "Can I push back on something? I think the direction we're taking on X is wrong because [specific reason]. I might be missing context — what am I not seeing?"

### "I committed but I still think we should change course"

> "Two weeks ago I committed to X. Since then, we've seen [new data]. I want to re-open the decision. Here's what I'd propose: [new direction]."

---

## Anti-Patterns

- **The Loud Escalator.** Escalating every disagreement, often skipping levels. Within a year, the Director's filter is "ignore them."
- **The Silent Resister.** Disagrees in their head; never says anything; passive-aggressively resists implementation. Worst kind of leader.
- **The Backroom Dealmaker.** "I talked to the Director and we agreed..." done outside the normal decision process. Peer trust evaporates.
- **The Over-Processor.** RFCs for every choice, including Type 2 trivialities. Team loses velocity; nobody contributes to RFCs anymore.
- **The Under-Processor.** Big architectural decisions made in Slack DMs by 2 people. Surface 6 months later; whole team affected; no documentation.
- **The Re-Litigator.** Decision was made; they keep re-opening it in every meeting. Disagree and commit, or move on.
- **The Triangulator.** "Did Bob actually agree to this?" — fishing for political allies instead of having the direct conversation.
- **The Decision Avoider.** Punts every decision to "let's revisit next week." Decisions get made by default (often badly).
- **The Single-Point-of-Failure.** Decisions only get made when the Staff engineer is in the room. Team can't function without them. Failed leadership.

---

## Probing Questions

1. How do you decide whether a decision belongs to you, your peer, your EM, or your Director?
2. Give an example of a decision where escalating made things better. Where it made things worse.
3. What's the difference between disagreeing professionally and disagreeing destructively?
4. How do you tell whether a decision is Type 1 (one-way door) or Type 2 (two-way door)?
5. The team votes 4-2 against your proposal. You think they're wrong. What do you do?
6. Your EM is making a strategic call you think is wrong. Walk through how you'd handle it.
7. You've committed to a decision; new data suggests it was wrong. How do you re-open it without losing credibility?
8. What's the failure mode of a Staff engineer who escalates too readily? Too rarely?

---

## Further Reading

- [`influence-without-authority.md`](influence-without-authority.md) — the muscle that lets you decide without title power.
- [`running-a-design-review.md`](running-a-design-review.md) — where DACI roles get exercised.
- [`incident-response-on-call.md`](incident-response-on-call.md) — escalation in the heat of an incident.
- [`../career/writing-rfcs.md`](../career/writing-rfcs.md) — the artifact that records the decision.
- [Atlassian — DACI Decision Framework](https://www.atlassian.com/team-playbook/plays/daci) — practical template.
- [Lara Hogan — "Disagree and Commit"](https://larahogan.me/blog/) — how to do it well.
- [Amazon's 2015 shareholder letter](https://ir.aboutamazon.com/files/doc_financials/annual/2015-Letter-to-Shareholders.PDF) — the primary source for the Type 1 / Type 2 framing.
