# Release Engineering: Play Store Internals

> What Play Console actually shows you, the difference between Vitals' view and your crash reporter's view, how Play distributes updates, and the dashboards a release manager needs to live in.

---

## 1. The Play Console Surface Area

| Section | What it tells you | When you look at it |
|---|---|---|
| **Production / Testing tracks** | Current rollout status, % adopted, halt button | Every promotion |
| **Statistics — Installs** | Daily installs, uninstalls, by country / device / version | Weekly review |
| **Statistics — Acquisition** | Source of installs (organic, search, referrer) | Marketing/Growth |
| **Quality — Android Vitals** | Crash rate, ANR rate, slow start, slow render | During rollout, daily after |
| **Quality — Pre-launch reports** | Crawler-based automated tests on real devices | After every Internal upload |
| **Quality — Reach and devices** | Per-device-class adoption, fragmentation | Quarterly |
| **App content** | Privacy policy, data safety, target audience | Compliance |
| **Setup → App integrity** | Signing keys, Play Integrity setup | Setup only |
| **Pricing & distribution** | Countries, pricing, in-app products | Per-launch |

The interesting ones for releng are **Production tracks**, **Vitals**, and **Reach and devices**. Vitals is the source of truth for crash decisions because it's what Play itself uses to decide whether to deprioritize your app in Search.

---

## 2. Vitals vs Crashlytics — Why Different Numbers

| Source | Methodology | Reach |
|---|---|---|
| **Android Vitals** | GMS-instrumented; data from Play Services on every Play-installed device | Every Play-installed device with GMS |
| **Crashlytics** | SDK in your APK; reports when your app code initializes | Devices that successfully ran your app |

They differ because:
- Vitals counts a crash on app start before Crashlytics initializes. (Your SDK was DOA.)
- Crashlytics counts crashes Vitals misses (e.g., custom non-fatal logs).
- Vitals' user base = all Play users; Crashlytics' = users whose app ran long enough to init.
- Vitals shows ANRs that Crashlytics misses (system-detected vs in-process detected).

For **promote/halt decisions**, use Vitals. For **issue grouping and stack traces during triage**, use Crashlytics or Sentry.

---

## 3. Reach And Devices Dashboard

The most useful undervalued tool. Shows your install base broken down by:
- API level (Android version)
- RAM tier
- Screen size & density
- ABI (32-bit / 64-bit)
- OEM (Samsung, Xiaomi, Pixel, ...)
- Country
- Language

```
API Level
  API 26 (Android 8.0):   2.3%
  API 28 (Android 9.0):   8.1%
  API 29 (Android 10):    11.4%
  API 30 (Android 11):    18.7%
  API 31 (Android 12):    14.2%
  API 33 (Android 13):    21.8%
  API 34 (Android 14):    18.1%
  API 35 (Android 15):    5.4%

OEM
  Samsung:    42%
  Xiaomi:     11%
  Pixel:      8%
  OPPO:       7%
  Vivo:       5%
  Other:      27%
```

Use this when:
- Setting `minSdk`. Don't drop API 26 if 2.3% is meaningful.
- Investigating a "only on Samsung Galaxy A" bug — what's the Samsung share?
- Sizing test coverage: if 11% are Xiaomi, you owe them an FTL run.

Available via the same Play Developer Reporting API:

```python
# scripts/reach_breakdown.py
def reach_by_dimension(dimension: str) -> dict:
    body = {
        "timelineSpec": {"aggregationPeriod": "DAILY", "startTime": ..., "endTime": ...},
        "metrics": ["activeUsers"],
        "dimensions": [dimension],
    }
    resp = service.vitals().anrrate().query(
        name=f"apps/{PACKAGE}/anrRateMetricSet", body=body
    ).execute()
    return {row['dimensions'][0]['value']: int(row['metrics'][0]['decimalValue']['value'])
            for row in resp['rows']}
```

---

## 4. Pre-Launch Report

When you upload to any track, Play runs the APK against a fleet of physical devices for ~30 minutes. Automated crawler clicks through the UI. Returns:

- Crashes (with stack traces).
- ANRs.
- Performance issues.
- Security vulnerabilities (basic scan).
- Accessibility issues (basic).

Doesn't replace your own testing but catches obvious smokes — particularly useful for OEM-specific crashes you couldn't reproduce.

You can disable pre-launch reports on Internal track if they slow your iteration; keep them on for Alpha and above.

---

## 5. How Play Distributes Updates

Play doesn't push updates immediately; it adopts a slow schedule:

- **Internal track**: instant (seconds to minutes).
- **Alpha/Beta**: usually within 1-2 hours of upload.
- **Production at X%**: distributed over 24-48 hours; user fraction is a probability, not an immediate switch.

Per-device factors:
- Wi-Fi vs cellular. Default settings only auto-update on Wi-Fi.
- App in use. Play tends to update at idle.
- Battery state. Low battery delays.
- Time of day. User's local night-time often.
- Device idleness. Idle devices get updates faster.

This means "10% rollout" doesn't snap to 10% in 10 seconds. It ramps over a day.

In-App Updates API gives you control:

```kotlin
class InAppUpdateChecker @Inject constructor(@ApplicationContext ctx: Context) {
    private val manager = AppUpdateManagerFactory.create(ctx)

    suspend fun checkAndPrompt(activity: ComponentActivity) {
        val info = manager.appUpdateInfo.await()
        when {
            info.updateAvailability() != UpdateAvailability.UPDATE_AVAILABLE -> return
            info.updatePriority() >= 4 && info.isUpdateTypeAllowed(IMMEDIATE) -> {
                manager.startUpdateFlowForResult(info, IMMEDIATE, activity, REQ_IMMEDIATE)
            }
            info.updatePriority() >= 2 && info.isUpdateTypeAllowed(FLEXIBLE) -> {
                manager.startUpdateFlowForResult(info, FLEXIBLE, activity, REQ_FLEXIBLE)
            }
        }
    }
}
```

`updatePriority()` is the `updatePriority` you set in Triple-T `play { }`. The app reads it; you decide blocking vs background download.

---

## 6. Play's Distribution Throttles

If your release is "bad" (crash rate spikes, install error rate spikes), Play silently slows the distribution. You'll see:
- Adoption rate plateauing well below target.
- Play Console showing "distribution paused" or "issues detected."
- Vitals showing the regression.

Play's distribution throttling is a safety net; don't rely on it. Detect via your own crash gate first.

---

## 7. Country-Specific Distribution

Play Console lets you target specific countries during staged rollout:

```
Track: production
  Global rollout: 5%
  Per-country override:
    NZ:  50%       (low-volume canary)
    AU:  20%       (English-speaking, similar device mix)
    IN:  0%        (postponed pending OEM fix)
```

Useful when a known regression affects a specific region. CI can't currently set per-country overrides via the API for staged rollouts — must be done in Console UI, which means it's a manual button.

---

## 8. Device Catalog Exclusions

Play Console → Setup → Advanced settings → Device catalog.

Exclude specific device models from receiving the app entirely or from receiving updates:
- Galaxy S10 (model SM-G973) — exclude this release due to known SoC bug.
- Xiaomi POCO M3 — exclude due to insufficient testing coverage.

```
Per-app excluded devices:
  - Samsung SM-G973F (Galaxy S10)         — known SoC bug, exclude until v2.0.3
  - Xiaomi M2010J19SG (POCO M3)            — exclude pending QA coverage
```

Last-resort tool. Customers on excluded devices stay on whatever version they had, with no path forward until you re-include. Document and unblock.

---

## 9. The "Suddenly Crashing in India on Samsung A11 Android 11" Cohort

Your Vitals breakdown reveals it. Crashlytics doesn't (your app crashed before init). Steps:

1. **Vitals: Crash rate by device.** Filter `country=IN`. Find Samsung A11 spiking.
2. **Vitals: Crash details.** Stack trace from Play's instrumentation. Often points to OEM-modified libraries.
3. **Cohort kill switch.** Disable the offending feature for `deviceModel matches 'SM-A11*'` via the variant kill flag (see `kill-switches.md`).
4. **Forensic on a real device.** Buy a Samsung A11 or rent one through FTL. Reproduce.
5. **Fix or block.** Either fix in next release, or use Play Device Catalog exclusion temporarily.

This pattern — Vitals reveals it, kill-switch contains it, real-device reproduces it, fix ships — is the entire reason for the dashboards and tooling.

---

## 10. Common Pitfalls

- **Trusting Crashlytics's "0 crashes" while Vitals reports 12%.** Your app died before init. Add a `Thread.UncaughtExceptionHandler` to catch boot-time crashes.
- **Not checking Vitals during rollout.** "We don't have any reports!" doesn't mean what you think.
- **Ignoring pre-launch reports.** Free 30-minute crawler coverage on real devices. Costs you nothing.
- **Promoting to 100% before reviewing per-country breakdowns.** Globally fine; emerging market specifically broken.
- **Excluding devices and forgetting.** Excluded devices accumulate. Quarterly review.
- **Treating the rollout fraction as instantaneous.** Ramps over 24-48h; expect a soak time.
- **Setting `updatePriority` to 5 for non-critical releases.** Trains users to dismiss the update dialog.
- **Not using a Slack alert when Play auto-pauses distribution.** Buried in Console.
- **Forgetting Play has separate "review for compliance" workflows.** Policy violations can hold a release for weeks.
- **Trusting the Play Console UI for ground truth.** Dashboards lag by hours. Use the API for hot-path automation.

---

## 11. Useful Play Developer API Endpoints

```
# Status of current production release
GET https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/edits/{editId}/tracks/production

# Vitals
GET https://playdeveloperreporting.googleapis.com/v1beta1/apps/{packageName}/crashRateMetricSet:query
GET https://playdeveloperreporting.googleapis.com/v1beta1/apps/{packageName}/anrRateMetricSet:query

# Reviews
GET https://androidpublisher.googleapis.com/androidpublisher/v3/applications/{packageName}/reviews

# Install statistics
GET https://playdeveloperreporting.googleapis.com/v1beta1/apps/{packageName}/installCountMetricSet:query
```

OAuth scopes:
- `https://www.googleapis.com/auth/androidpublisher` — Console operations (releases, listings, in-app products).
- `https://www.googleapis.com/auth/playdeveloperreporting` — Reporting (Vitals, install metrics, reviews).

---

## 12. Further Reading

- [Play Console help](https://support.google.com/googleplay/android-developer/) — official.
- [Play Developer API](https://developers.google.com/android-publisher) — automation.
- [Play Developer Reporting API](https://developers.google.com/play/developer/reporting) — Vitals + install metrics.
- [Android Vitals](https://developer.android.com/topic/performance/vitals) — what they measure and thresholds.
- [In-app Updates](https://developer.android.com/guide/playcore/in-app-updates) — priority-driven update prompts.

---

> **In short:** Vitals is the source of truth Play itself uses; learn the dashboards; automate the reads via Play Developer Reporting API; treat Crashlytics as triage and Vitals as gate. Use Reach & Devices for `minSdk` decisions. Don't be surprised by 24-48h ramp times.
