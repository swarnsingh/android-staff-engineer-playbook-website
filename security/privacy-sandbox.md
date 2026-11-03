# Privacy Sandbox on Android: Architecture, Phaseout and Migration

Privacy Sandbox on Android was Google's multi-year program to rebuild mobile advertising without cross-app identifiers. Google's [feature status page](https://privacysandbox.google.com/overview/status), updated August 14, 2026, lists Attribution Reporting, Protected Audience, Topics, SDK Runtime, On-Device Personalization, and Protected App Signals as **scheduled for phaseout**. It lists several related Chrome advertising APIs for deprecation and removal too; that is a lifecycle plan, not a claim that all those APIs have already been removed. Other Chrome privacy features, including CHIPS, FedCM, and Storage Access, remain supported.

Why keep a file about a platform being phased out in a staff-level playbook? Three reasons. Interviewers still ask about it, and its changed status matters to an answer. Its architecture ideas keep resurfacing in other systems. Its lifecycle change also raises a planning question: how can a roadmap retain options when a platform dependency changes?

---

## 1. What Privacy Sandbox on Android Was

Announced in early 2022, the program promised to replace the advertising ID (GAID) and cross-app tracking with on-device, privacy-preserving primitives:

- **Topics API** — the device locally inferred coarse interest categories from app usage; ad SDKs could read a few topics without learning app-level history.
- **Attribution Reporting API** — conversion measurement (did the ad drive the install/purchase?) computed with event-level and aggregate reports, with noise and delay instead of a per-user identifier joining ad click to conversion.
- **Protected Audience (née FLEDGE)** — remarketing via on-device auctions: the "audience list" lived on the device, and ad selection ran locally, so membership never left the phone.
- **SDK Runtime** — the most architecturally interesting piece for app engineers: third-party ad SDKs would run in a separate sandboxed process with restricted permissions, instead of inheriting your app's entire permission set and address space.
- **Protected App Signals / On-Device Personalization** — later additions for app-install ads and personalization with device-local data.

The unifying idea: move computation to the data (on-device auctions, local topic inference, aggregated noisy reporting) instead of moving data to the computation (server-side identity graphs).

## 2. Status and Planning Implications

The official status list establishes the phaseout plan. It does not by itself establish a complete causal account of adoption, competition proceedings or commercial incentives. Treat those as hypotheses requiring separate evidence rather than settled reasons for Google's decision.

For planning, distinguish a scheduled phaseout from a removal already shipped on every supported device. Inventory dependencies, follow the individual API's release/deprecation notes and provide an adapter migration path. Existing privacy obligations do not disappear with an advertising API, and those APIs never replaced lawful-basis, transparency or deletion duties.

## 3. What Android Privacy Actually Looks Like Now

With these Sandbox ad APIs scheduled for phaseout, app engineers should rely on the privacy controls already in force, including **policy and platform hardening**:

- **GAID with user control.** The advertising ID persists, but users can delete it (it zeroes out), and Play policy requires declared, consented use. iOS's ATT remains the stricter comparison point.
- **Play Data safety + policy enforcement.** Your public contract about data collection, sharing, and deletion. Wrong answers are a policy strike, and your SDK vendors' behavior is *your* declaration — you own what they collect.
- **Regulatory floor.** Applicable lawful-basis, transparency, transfer, consumer-choice and deletion obligations remain independent of advertising API design — covered in [Privacy, GDPR & Data Residency](privacy-gdpr-data-residency.md).
- **SDK governance while SDK Runtime phases out.** Since [SDK Runtime is scheduled for phaseout](https://privacysandbox.google.com/overview/status#android), third-party SDK risk management still needs an SDK inventory, network-egress review, permission budget, and kill switches per SDK (see [Kill Switches](../release-engineering/kill-switches.md)). Review each SDK's actual process and permission model rather than assuming isolation.
- **On-device computation as a privacy pattern lives on** — just not as an ads API. Private Compute Core still hosts platform features, and [on-device AI](../mobile-system-design/on-device-ai.md) inference via AICore is now the mainstream "move compute to the data" story.

## 4. The Staff-Level Lesson: Platform Bets

If your team spent 2023–2025 integrating Attribution Reporting, the planned phaseout changes that investment's long-term value. The generalizable heuristics:

1. **Separate status from explanation.** A phaseout announcement is evidence of lifecycle change; it is not evidence that one commercial incentive or regulatory event caused it. Use official release/status notes to plan dependency work and label any causal analysis separately.
2. **Inventory exposure.** Record which features use each API, the supported device/client cohort, stored data and the removal/reset contract. A release date in one channel is not proof that every installation has lost the API.
3. **Wrap vendor boundaries.** Keep application event schemas and purpose controls separate from the advertising adapter. A migration can then replace the transport/measurement integration without quietly changing the meaning of stored events.
4. **Stage a measured migration.** Assign an owner, validate the replacement's privacy and behavior, observe coverage, then remove the old integration under a documented compatibility policy. These steps do not depend on an unproven explanation for the phaseout.

## 5. Interview Framing

If asked "how would you design privacy-preserving ad measurement on Android?" — the answer should start with the [current phaseout status](https://privacysandbox.google.com/overview/status) of the Sandbox ad APIs, then reason from first principles: aggregate over individual (differential-privacy-style noise on cohort metrics), on-device joins where possible, shortest-path consent, and server-side enforcement of retention. Explain which APIs remain available for the app's supported devices and timeline instead of describing them as already retired.

## Further Reading

- [Privacy Sandbox feature status](https://privacysandbox.google.com/overview/status) — the authoritative lifecycle list; check its latest update date
- [Privacy Sandbox on Android (archived docs)](https://developers.google.com/admob/android/privacy/sandbox) — retained for reference
- [Play Data safety](https://support.google.com/googleplay/android-developer/answer/10787469) — the declaration that now carries the enforcement weight
