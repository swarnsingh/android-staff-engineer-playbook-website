# Leadership: Technical Mentorship (Scaling Yourself)

> A Staff engineer who writes brilliant code but doesn't develop others has a fixed ceiling — at best, one person's output forever. The Staff role is to *multiply yourself* through mentorship and sponsorship. The engineers you raise today are the Senior engineers you collaborate with in 3 years; the Staff engineers in 7.

---

## Mentor vs Sponsor

These get conflated; they're different:

| Mentor | Sponsor |
|---|---|
| Advises. Shares experience. Talks. | Acts. Uses authority. Decides. |
| "Here's how I'd approach that." | "I told the VP you should present at the all-hands." |
| Low cost; low risk. | Higher cost; spends reputation capital. |
| Helps the mentee *think* better. | Helps the mentee get *opportunities*. |
| Can mentor many people. | Sponsor a handful at a time. |

A Staff engineer does both. Mentor at scale; sponsor a few deliberately. Most engineers get plenty of mentorship and almost no sponsorship — sponsorship is the rarer, more valuable currency.

### Why sponsorship matters

Mentorship gives advice; sponsorship gives opportunities. An engineer who's been told "you'd be great as a Tech Lead" is mentored. An engineer whose Staff puts their name forward to lead a high-visibility cross-team initiative is *sponsored*.

The mentorship-only path produces engineers who feel encouraged but pass over for opportunities. The sponsorship path produces engineers who get the visibility, the scope, the reps that compound into the next promotion.

---

## How To Mentor Well

### The Lightweight Pattern

Most useful mentorship is *not* recurring 1:1s. It's targeted help on a specific problem.

Pattern:

1. Junior says "I'm stuck on X."
2. Mentor asks 3-4 diagnostic questions: "What have you tried? What did you expect to see vs what happened? What do you think the root cause might be?"
3. Mentor doesn't *solve* the problem; mentor frames *how to think about* the problem.
4. Junior tries the next step.
5. Mentor follows up next day: "How did it go?"

This costs the mentor 15 minutes and gives the junior the *skill* of debugging, not just the answer.

### The Recurring 1:1 Pattern

For deeper, longer-term mentorship — typically 1-2 mentees at any given time:

- 30-45 minutes, monthly.
- Mentee owns the agenda (sends 2-3 topics in advance).
- Mentor's role: ask better questions, share patterns, occasionally connect to people/opportunities.
- Document agreements ("By next session, you'll have written the first draft of the X RFC and asked Bob to review it").

### The "Show Your Work" Pattern

Most powerful pattern in a Staff engineer's repertoire. Instead of telling the mentee how to do something, do it in front of them and narrate:

- Pair-debug a hard bug for 30 minutes. Talk through your hypothesis-testing.
- Co-write an RFC. Show the structure as you draft.
- Walk through your screen during an incident: "I'm checking dashboards first, then logs, then..."

Watching a Staff engineer think is the single highest-leverage learning opportunity for a Senior or Mid. Don't hoard it.

---

## How To Sponsor Well

Sponsorship has steps:

### 1. Identify

Look for engineers in your org who:
- Have demonstrated technical chops on at least one solid project.
- Don't yet have the visibility their work warrants.
- Are often women, underrepresented groups, junior engineers, or quiet engineers — *those most likely to be overlooked by the default sponsorship pattern, which sponsors people who look like the sponsor.*

### 2. Build the relationship

You can't effectively sponsor someone you don't know. Spend 30-60 days mentoring before sponsoring. Understand their goals, their gaps, their next stretch.

### 3. Find the opportunity

The next time a stretch opportunity comes up — leading an RFC, presenting at all-hands, joining a cross-team review, owning an investigation — *recommend them by name*.

> Public Slack to the EM: "I think Priya would be the right person to lead the modularization RFC. She owned the X migration last quarter and has the architectural breadth. I'll back her up if she needs it."

### 4. Defend them publicly

If your sponsee struggles in the early stages, defend them publicly. Their setback is a story you can tell as growth ("Priya pushed back on my initial design; her instincts were right; we shipped a better solution"). Defending sponsored people compounds their reputation.

### 5. Step out of the way

The point of sponsorship is the sponsee earning *their own* credibility. After the first 2-3 sponsored opportunities, they should be operating independently. If you're still vouching for them year three, sponsorship didn't take.

### Pace

You can effectively sponsor 2-4 people at once. More than that, you can't deeply advocate; less than that, you're not exercising the muscle.

---

## The Mentorship Contract

For longer mentorships (3-12 months), make the agreement explicit:

```
# Mentorship Agreement: <Mentor> + <Mentee>

## Goal
What the mentee wants to achieve in this period. Specific and measurable.
Example: "Operate consistently at Senior-level scope on cross-team
features by end of Q3."

## Cadence
- Monthly 1:1, 45 min.
- Async Slack DM as needed for ad-hoc questions.

## Commitments
Mentor:
- Show up to 1:1s prepared (review agenda in advance).
- Connect mentee to opportunities/people.
- Provide candid feedback within 48h of asks.

Mentee:
- Send agenda 24h before each 1:1.
- Try concrete actions between sessions; report back.
- Drive own goals; mentor is a resource, not a substitute for ownership.

## Check-in
Quarterly: review goal progress, decide whether to continue.

## End conditions
- Goal achieved.
- Cadence stops being useful.
- Mentee outgrows the relationship (success!).
```

Making it explicit prevents drift (the relationship that never ends and never produces anything) and creates a clear exit (mutual graceful close, not awkward fade).

---

## Common Mentorship Mistakes

### From the mentor's side

- **Solving instead of teaching.** "Here's how to fix it: [code]." The mentee learns nothing about debugging.
- **Telling instead of asking.** "You should use a Mutex here." Better: "What's the concurrency model in this code?"
- **The lecture loop.** Mentor talks for 30 minutes, mentee listens. Mentee retains 10%.
- **Vague guidance.** "Be more strategic." Useless. Try: "Next time you write an RFC, structure it as a business case first; here's an example."
- **The 'find your own way' cop-out.** "I can't really tell you what to do; you have to figure it out." Sometimes useful; often just lazy mentorship.
- **Optimizing for the mentor's ego.** "Let me tell you about when I solved a similar problem at <famous company>." Not useful unless directly applicable.

### From the mentee's side

- **No agenda.** Showing up with nothing prepared. The mentor's time is finite; respect it.
- **Wanting answers, not skills.** "Just tell me what to do." Mentorship is about getting better, not getting answers.
- **Not following through.** Discusses an action in the 1:1; doesn't do it; shows up next month with the same problem.
- **Confiding too much.** A mentor is not a therapist; keep personal vents to other forums.
- **Skipping the work.** Asking the mentor to read your RFC without doing the deep reading themselves first.

---

## Mentoring At Scale

A Staff engineer can't have monthly 1:1s with 30 people. To scale mentorship:

### Office hours

Block 1-2 hours weekly. Anyone in the org can sign up for a 15-30 min slot. Topic-agnostic.

- Pros: low overhead; high reach; spontaneous learnings.
- Cons: less depth than ongoing 1:1s.

### Workshops

Spot a recurring question pattern in the org (e.g., "how do I write an RFC?"). Run a 60-min workshop. 15 engineers learn at once instead of 15 individual conversations.

### Recorded talks + written guides

Convert your most-asked-about topic into a recorded internal talk or written guide. Now your mentorship scales to anyone who reads/watches it.

### Internal engineering blog

Encourage juniors to write up their learnings as blog posts. Review their drafts. This is mentorship as *publishing* — and the artifacts become future onboarding material.

---

## Mentoring Up

You can mentor people more senior than you, too. A Staff engineer can mentor an EM on technical understanding; a junior Staff can mentor a senior Staff on a specific specialty.

The motion is the same: ask better questions, share patterns, occasionally suggest. The difference is *humility* — you're not the more-senior person; you're peers with complementary skills.

If you find yourself mentoring up, do it quietly. Don't make a show of it; the mentee may find it useful only if it doesn't feel like a status play.

---

## Mentoring Other Mentors

The most leveraged mentorship of all. Help Senior engineers learn to mentor.

Pattern:

- Pair them with their first mentee.
- Debrief monthly: how's the relationship going? What did you try? What worked?
- Share your own mentorship patterns.
- Sponsor them to lead workshops.

After 6-12 months, you've created a *mentor* who is now mentoring 1-2 of their own people. The org's mentorship capacity has grown without you doing more 1:1s.

This is how engineering cultures of learning scale. Without it, mentorship stays concentrated in the few willing Staff engineers; with it, the practice spreads.

---

## Anti-Patterns

- **The mentorship hoarder.** Has 8 mentees; gives shallow attention to each; helps none of them deeply.
- **The mentorship saint.** Spends 50% of their week on mentorship; falls behind on their own deliverables; eventually burns out and drops everyone.
- **The pet-project sponsor.** Sponsors only people who work on the sponsor's pet topics. Limits reach; signals favoritism.
- **The credit-stealing mentor.** Helps a junior land a big project; takes credit for it in their own packet. Burns the relationship permanently.
- **The "we should chat sometime" trap.** Casual offer of mentorship; never follows through. Junior feels dismissed.
- **The mentor as a therapist.** Letting mentorship become emotional support. Both parties get drained.
- **The unwilling mentor.** Forced to mentor by their EM; checks the box without engaging. Worse than no mentor at all.
- **The "I made it without a mentor" pride.** Refusing to mentor because "no one helped me; they should figure it out too." This is how toxic cultures perpetuate.

---

## Probing Questions

1. What's the difference between mentorship and sponsorship? Why does sponsorship compound more?
2. How do you mentor someone without solving their problems for them?
3. You have 4 hours a week for mentorship. How do you allocate them?
4. Who in your current org would you sponsor? Have you?
5. A mentee shows up to the third 1:1 with no agenda again. How do you address it?
6. Why is "find your own way" sometimes lazy mentorship?
7. How do you mentor someone more senior than you without it being awkward?
8. What's the failure mode of a Staff engineer who refuses to mentor?

---

## Answer Key

1. **What's the difference between mentorship and sponsorship? Why does sponsorship compound more?**
   Mentorship provides advice and perspective, whereas sponsorship provides specific opportunities by using the sponsor's capital to advocate. Sponsorship compounds more because it gives the sponsee visible reps that directly lead to career advancement.
2. **How do you mentor someone without solving their problems for them?**
   Ask diagnostic questions (e.g., "What have you tried?", "What do you think is the root cause?") to help them frame their thinking and guide their debugging process.
3. **You have 4 hours a week for mentorship. How do you allocate them?**
   Spend 1-2 hours on high-leverage 1:1 sponsorship for a couple of engineers, 1 hour on "Office Hours" for ad-hoc broad mentorship, and 1 hour on scaling knowledge via written artifacts or workshops.
4. **Who in your current org would you sponsor? Have you?**
   (Self-reflection) Look for engineers who do solid technical work but lack visibility, particularly those from underrepresented groups or those who are quiet, and actively recommend them for high-profile tasks.
5. **A mentee shows up to the third 1:1 with no agenda again. How do you address it?**
   Address it directly using the mentorship contract. Explain that your time is finite and their growth requires their ownership, gracefully ending or pausing the 1:1s until they are ready.
6. **Why is "find your own way" sometimes lazy mentorship?**
   While intended to build independence, it often provides zero framing or guidance, leaving the mentee completely stuck rather than teaching them the specific mental models they need.
7. **How do you mentor someone more senior than you without it being awkward?**
   Do it quietly and with humility. Focus on asking great questions, sharing domain-specific patterns where you have deep expertise, and acting as a peer with complementary skills.
8. **What's the failure mode of a Staff engineer who refuses to mentor?**
   They become a single point of failure and their impact is capped at their own individual output. The organization fails to grow its technical bench, and the Staff engineer eventually burns out.

## Further Reading

- [`influence-without-authority.md`](influence-without-authority.md) — sponsorship as influence-spending.
- [`../career/technical-leadership.md`](../career/technical-leadership.md) — mentorship as leadership.
- [`../career/senior-to-staff-progression.md`](../career/senior-to-staff-progression.md) — what to mentor people *toward*.
- [`running-a-design-review.md`](running-a-design-review.md) — mentorship in the review setting.
- [Lara Hogan — "Mentorship vs Sponsorship"](https://larahogan.me/blog/) — the canonical distinction.
- [Tanya Reilly — "Being Glue"](https://noidea.dog/glue) — mentorship as glue work.
- [Cate Huston — "DRI Your Support System"](https://cate.blog/2021/11/22/dri-your-support-system/) — practical mentoring and sponsorship distinctions.
- [Will Larson — "Sponsoring is more important than mentoring"](https://lethain.com/) — the case for sponsorship.
