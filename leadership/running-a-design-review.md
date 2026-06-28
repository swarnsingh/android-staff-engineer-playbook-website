# Leadership: Running a Design Review

> The design review is where RFCs go from "draft someone wrote alone" to "decision the team owns." A good design review surfaces non-obvious problems in 45 minutes; a bad one wastes the time of 8 people and produces no decision. The Staff engineer's job is to *facilitate* the review, not to defend the proposal.

---

## Why Design Reviews Exist

Every non-trivial architectural decision has multiple right answers and many wrong ones. You can't tell which is which by yourself — your brain is the one that built the proposal. Other brains will see things you can't.

A design review trades meeting time for decision quality. The cheap path (skip the review, ship the design, discover problems in production) costs orders of magnitude more than the 45 minutes.

The Staff engineer often *runs* the review, even when they're not the RFC author. The author is too close to the proposal to facilitate fairly.

---

## Async vs Synchronous

Most of the review should be **async**. The synchronous meeting is for the unresolved 10%.

| Phase | Time | What happens |
|---|---|---|
| **Async draft** | Author writes draft | RFC posted in folder + Slack channel; status DRAFT |
| **Async comments** | 3-5 business days | Reviewers comment inline; author replies and revises |
| **Sync meeting** | 45-60 min | Discuss unresolved threads only; make decisions |
| **Async wrap-up** | 1-2 days | Author updates RFC with meeting outcomes; status APPROVED |

If 90% of comments can be resolved async, the meeting is for the hard 10%. If everyone shows up to the meeting having not read the RFC, you're doing it wrong. *Cancel the meeting* until people have read it.

---

## Before The Meeting: The Pre-Review Checklist

The Staff engineer (as facilitator) ensures:

- [ ] RFC posted at least 3 business days before the meeting.
- [ ] Posted to the right Slack channel + the right reviewers tagged.
- [ ] Reviewers know it's their *job* to read it before the meeting.
- [ ] Author has responded to all async comments (resolved or escalated to the meeting).
- [ ] Agenda for the meeting is published 24h before: "Open thread 1: X. Open thread 2: Y. Decision needed: Z."
- [ ] DACI roles are clear: who's Driver, Approver, Contributors, Informed (see [`escalation-and-decision-making.md`](escalation-and-decision-making.md)).
- [ ] If the Approver can't make the meeting, *postpone* — there's no point in a review without the decision-maker.

If any of these are missing, push back on the author. Better to delay a week than to run a useless meeting.

---

## During The Meeting: The Facilitator's Toolkit

### Open with the agenda

> "We have 45 minutes. Today's open threads are 1, 2, 3. By the end of this meeting we want a decision on whether to proceed with X. The Approver is <name>. Author is <name>; everyone else is a Contributor or Informed. Let's start with thread 1."

This sets expectations. People know what success looks like. The author isn't ambushed; the Approver isn't asked to make a surprise decision.

### Time-box ruthlessly

If a thread has been discussed for 10 minutes and isn't converging, *park it*:

> "We've spent 10 min on this; we're not converging. Let me note this as an open thread; let's continue async after the meeting. <Author>, please add a paragraph to the RFC summarizing the discussion and the open question."

A meeting that produces 3 decisions and 2 parked threads is more useful than one that produces 0 decisions and 5 discussed threads.

### Surface the silent

The loudest reviewer dominates by default. The facilitator counters:

> "We've heard from <loud reviewer>; <quiet reviewer>, what's your take? You've worked on a similar problem before."

Make space for the quiet. They often have the most-considered views.

### Re-route when the conversation drifts

> "We've drifted into bikeshedding on naming. Let me park that — naming is a follow-up decision for the implementer. Back to the architectural question: <restate>."

Bikeshedding kills design reviews. The facilitator's job is to keep the conversation on the highest-value question.

### Force the decision

If the conversation has reached natural resolution:

> "Sounds like we're aligned on X. <Approver>, do you want to confirm: we're going with X. Are there any blocking concerns?"

A design review without a decision is a discussion. Force the decision before time runs out, even if "the decision is: defer for 2 weeks pending more data."

---

## The Three Outcomes Of A Design Review

Every review should end in one of three states:

1. **APPROVED.** Author proceeds; status APPROVED on the RFC. Approver and key reviewers sign.
2. **NEEDS REVISION.** Approver is willing to approve after specific changes; author revises and re-circulates async.
3. **REJECTED / RECONSIDER.** Approver is not approving in the current form; either back to the drawing board or escalated.

If you end without one of these, you have a fourth (bad) state: **AMBIGUOUS**. Author doesn't know what to do; another meeting is needed; the proposal stalls. Avoid this at all costs.

---

## After The Meeting: The Wrap-Up

Within 24 hours:

- Author updates the RFC with the meeting's decisions and open threads.
- Author posts in the Slack channel: "Design review complete. Decision: X. Open threads parked for async: Y, Z. Status: <APPROVED / NEEDS REVISION / REJECTED>. Thanks <attendees>."
- If APPROVED: author writes an ADR if the decision is Type 1 (one-way door, see [`escalation-and-decision-making.md`](escalation-and-decision-making.md)).
- If NEEDS REVISION: author commits to a re-circulation date.
- Facilitator (if different from author) writes a 1-paragraph "lessons learned" note for the team: "What worked in this review? What should we do differently next time?"

The post-meeting wrap-up makes the meeting's value durable.

---

## Common Review Anti-Patterns

### From the author's side

- **Defending instead of listening.** A reviewer raises a concern; author immediately argues against it. The reviewer feels unheard; future reviews from them are perfunctory.
- **The "I already considered that" deflection.** Even if you did, the reviewer didn't see your consideration. Walk through it again.
- **Surprise scope changes mid-meeting.** "Actually, I also want to discuss Y." NO — Y goes to a separate review.
- **Skipping the alternatives section.** Reviewers must understand what you rejected and why.
- **Showing up without having read your own RFC.** Sounds absurd; happens. Always re-read your own RFC the morning of the review.

### From the reviewer's side

- **Showing up unprepared.** Hasn't read the RFC; asks questions answered in section 2. Cost: the rest of the meeting wasted.
- **The bikeshedder.** Spending 20 minutes on what to name the variable while the actual architecture goes undiscussed.
- **The "what about X?" hostage-taker.** Every meeting, a new tangential concern that prevents the decision. Force them to bound their concerns.
- **The silent disagree-and-don't-commit.** Says nothing in the meeting; complains in Slack the next day. Address it directly: "I'd rather hear concerns now than next week."
- **The veto from on high.** A senior reviewer who shows up only to issue a no without engaging. Address it: "Can you walk us through what would need to change for you to approve?"

### From the facilitator's side

- **Letting the loudest reviewer dominate.** Quiet reviewers tune out.
- **Not enforcing the agenda.** Meeting drifts; nothing decided.
- **Not time-boxing.** 90-min meeting that should have been 45.
- **Not forcing a decision.** Meeting ends in "let's think about it more."
- **Defending the author instead of facilitating.** The author should defend themselves; the facilitator stays neutral.

---

## Variations By RFC Type

| RFC type | Review intensity | Typical attendees | Duration |
|---|---|---|---|
| New module / small feature | Light (async only often) | Author + 1-2 reviewers | — |
| Cross-team architectural change | Standard async + sync | Author + 4-6 reviewers (incl. peer team leads) | 45 min |
| Platform-level change | Heavy | Author + 6-10 reviewers (incl. multiple teams) | 60-90 min |
| Vendor / dependency decision | Standard + procurement | Author + tech leads + EM + procurement | 45 min |
| Security / compliance | Heavy | Author + 3-5 + InfoSec + EM | 60 min |

Match the review intensity to the decision's blast radius. Don't run a 60-minute meeting for a single-module decision; don't run a 30-minute meeting for an architectural one.

---

## Hosting Recurring Design Reviews

For teams that ship many RFCs (most healthy mobile teams), running a recurring "RFC Review" meeting is more efficient than scheduling per-RFC:

- Weekly or biweekly, 60 min.
- Async queue of RFCs (everyone reads in the week before).
- Live meeting walks through 2-3 RFCs; 15-20 min each.
- Facilitator rotates.

This trades scheduling friction for cadence. The team gets used to the rhythm; RFCs don't pile up; junior engineers get exposure to design discussions even if they're not the author.

---

## Probing Questions

1. Why is async review usually more valuable than the sync meeting?
2. What's the right time-box for a design review? When would you go longer or shorter?
3. As facilitator, how do you handle a reviewer who hasn't read the RFC?
4. The Approver can't attend the scheduled meeting. What do you do?
5. The author keeps defending instead of listening. How do you intervene without humiliating them?
6. The meeting ends with no decision. What's the cost? How do you avoid it next time?
7. A senior reviewer vetoes the proposal but won't explain why. How do you handle it?
8. Walk through what you'd do in the first 5 minutes of a design review you're facilitating.

---

## Further Reading

- [`escalation-and-decision-making.md`](escalation-and-decision-making.md) — DACI roles in the review.
- [`influence-without-authority.md`](influence-without-authority.md) — pre-review relationship building.
- [`technical-mentorship.md`](technical-mentorship.md) — letting a junior facilitate as practice.
- [`../career/writing-rfcs.md`](../career/writing-rfcs.md) — what gets reviewed.
- [Google eng-practices — Design Doc Reviews](https://google.github.io/eng-practices/) — practical examples.
- [Lara Hogan — Resilient Management](https://larahogan.me/blog/) — meeting facilitation patterns.
- [Stripe — Working Backwards from Decisions](https://stripe.com/blog/) — decision-process patterns.
