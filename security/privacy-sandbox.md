# Privacy Sandbox on Android: What It Was, Why It Died, What Replaces It

Privacy Sandbox on Android was Google's multi-year program to rebuild mobile advertising without cross-app identifiers. **As of October 17, 2025 it is deprecated**: Attribution Reporting, Protected Audience, Topics, SDK Runtime, On-Device Personalization, and Protected App Signals are all scheduled for phaseout, and the equivalent Chrome APIs were retired alongside them.

Why keep a file about a dead platform in a staff-level playbook? Three reasons. Interviewers still ask about it (often without knowing it's dead — correcting them gracefully is a signal). Its architecture ideas keep resurfacing in other systems. And its failure is the best recent case study of a question staff engineers face constantly: *when do you bet your roadmap on a platform initiative?*

---

## 1. What Privacy Sandbox on Android Was

Announced in early 2022, the program promised to replace the advertising ID (GAID) and cross-app tracking with on-device, privacy-preserving primitives:

- **Topics API** — the device locally inferred coarse interest categories from app usage; ad SDKs could read a few topics without learning app-level history.
- **Attribution Reporting API** — conversion measurement (did the ad drive the install/purchase?) computed with event-level and aggregate reports, with noise and delay instead of a per-user identifier joining ad click to conversion.
- **Protected Audience (née FLEDGE)** — remarketing via on-device auctions: the "audience list" lived on the device, and ad selection ran locally, so membership never left the phone.
- **SDK Runtime** — the most architecturally interesting piece for app engineers: third-party ad SDKs would run in a separate sandboxed process with restricted permissions, instead of inheriting your app's entire permission set and address space.
- **Protected App Signals / On-Device Personalization** — later additions for app-install ads and personalization with device-local data.

The unifying idea: move computation to the data (on-device auctions, local topic inference, aggregated noisy reporting) instead of moving data to the computation (server-side identity graphs).

## 2. Why It Died

- **Adoption never came.** Ad tech ran on GAID and had little incentive to rebuild on APIs that were strictly less capable, especially while GAID remained available. Sandbox APIs were additive, so the ecosystem waited — and a two-sided market that waits, dies.
- **Regulators boxed it in.** The UK CMA supervised the Chrome side because deprecating third-party cookies while owning the largest ad business is a competition problem; US antitrust rulings in 2025 against Google's ad-tech business made unilateral platform changes to ad infrastructure even harder to push through.
- **The forcing function disappeared.** In April 2025 Google abandoned third-party-cookie deprecation in Chrome. Once the web side kept cookies, the Android side lost its "the identifier is going away, migrate now" story — and in October 2025 both were wound down.

What survived is telling: the pieces that improve login and reduce cross-site tracking without restructuring the ads business (on Chrome: CHIPS, FedCM, Storage Access API, partitioning). The pieces that required the ad industry to rebuild itself did not.

## 3. What Android Privacy Actually Looks Like Now

With the Sandbox gone, the working privacy model for app engineers is the one that was already in force, and it is enforced by **policy and platform hardening**, not by new ad APIs:

- **GAID with user control.** The advertising ID persists, but users can delete it (it zeroes out), and Play policy requires declared, consented use. iOS's ATT remains the stricter comparison point.
- **Play Data safety + policy enforcement.** Your public contract about data collection, sharing, and deletion. Wrong answers are a policy strike, and your SDK vendors' behavior is *your* declaration — you own what they collect.
- **Regulatory floor.** GDPR/CCPA consent, data-residency, and deletion obligations do the heavy lifting the Sandbox was supposed to make unnecessary — covered in [Privacy, GDPR & Data Residency](privacy-gdpr-data-residency.md).
- **SDK governance without SDK Runtime.** The sandbox that would have isolated ad SDKs is phased out, so third-party SDK risk management stays organizational: an SDK inventory, network-egress review, permission budget, and kill switches per SDK (see [Kill Switches](../release-engineering/kill-switches.md)). Every third-party SDK still runs with your full app's permissions and process access. Treat that as your threat model.
- **On-device computation as a privacy pattern lives on** — just not as an ads API. Private Compute Core still hosts platform features, and [on-device AI](../mobile-system-design/on-device-ai.md) inference via AICore is now the mainstream "move compute to the data" story.

## 4. The Staff-Level Lesson: Platform Bets

If your team spent 2023–2025 integrating Attribution Reporting, that work is now write-off. The generalizable heuristics:

1. **Watch the incentives, not the announcements.** Privacy Sandbox required the ad ecosystem to adopt weaker tools while stronger ones remained legal and available. When a migration depends on counterparties acting against their interest, discount the roadmap heavily.
2. **Distinguish "deprecation-backed" from "aspiration-backed" platform changes.** Scoped-storage and background-execution limits shipped because Google could unilaterally enforce them at the OS level. Sandbox adoption was voluntary. Enforced changes happen; voluntary re-architectures usually don't.
3. **Wrap, don't weld.** Teams that integrated Sandbox APIs behind their own measurement abstraction lost an adapter; teams that welded event schemas to Attribution Reporting semantics lost a pipeline. The [strategy pattern for vendor boundaries](../android/observability/mobile-apm-and-rum.md) applies to platform APIs too.
4. **Regulatory supervision is a schedule risk multiplier.** Any platform change that a competition authority reviews line-by-line will slip, repeatedly. Plan optionality, not dates.

## 5. Interview Framing

If asked "how would you design privacy-preserving ad measurement on Android?" — the honest 2026 answer starts with the fact that the platform primitives for it were retired, then reasons from first principles: aggregate over individual (differential-privacy-style noise on cohort metrics), on-device joins where possible, shortest-path consent, and server-side enforcement of retention. You'll cover everything the Sandbox tried to do, while demonstrating you know what actually shipped and what didn't.

## Further Reading

- [Privacy Sandbox feature status](https://privacysandbox.google.com/overview/status) — the authoritative phaseout list, updated October 17, 2025
- [Privacy Sandbox on Android (archived docs)](https://developers.google.com/admob/android/privacy/sandbox) — retained for reference
- [Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) — the declaration that now carries the enforcement weight
