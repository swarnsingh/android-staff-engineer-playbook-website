# Release Engineering: Staged Rollouts

> Never ship to 100% of users at once. Use Play's staged rollout API to grow the audience gradually, monitor crash/ANR rate per stage, and pull the release if numbers degrade.

---

## 1. The Stage Model

```
v2.0.0 submitted
    │
    ▼
Internal Test Track (employees, 100%)
    │ (24h soak; engineers can use the app like users)
    ▼
Closed Test Track (alpha, ~500 trusted users)
    │ (3-7 days; rich crash/perf telemetry)
    ▼
Open Test Track (beta, opt-in users)
    │ (7 days)
    ▼
Production: 1% → 5% → 10% → 25% → 50% → 100%
    (24h between stages; auto-halt on regression)
```

A safer cadence costs a week of latency but turns a "30% crash rate disaster" into "we saw it at 1% and rolled back."

---

## 2. Promoting Between Stages With Triple-T

```kotlin
// app/build.gradle.kts
plugins {
    id("com.github.triplet.play") version "3.11.0"
}

play {
    serviceAccountCredentials.set(file(System.getenv("PLAY_SERVICE_ACCOUNT")))
    track.set("internal")
    defaultToAppBundles.set(true)
    releaseStatus.set(ReleaseStatus.COMPLETED)
    updatePriority.set(2)
    artifactDir.set(file("build/outputs/bundle/release"))
}
```

```bash
# Upload to internal
./gradlew :app:publishReleaseBundle --track=internal

# Promote internal → alpha
./gradlew :app:promoteArtifact --from-track=internal --promote-track=alpha

# Promote alpha → beta
./gradlew :app:promoteArtifact --from-track=alpha --promote-track=beta

# Production at 1% rollout (staged)
./gradlew :app:promoteArtifact \
    --from-track=beta \
    --promote-track=production \
    --release-status=inProgress \
    --user-fraction=0.01
```

The Play API supports incremental `userFraction`. Each promotion increases it.

---

## 3. Direct Play Developer API (When You Need More)

For automation outside Triple-T's coverage, use the Play Developer Publishing API directly. JWT-based service account auth:

```python
# scripts/promote.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import sys, json, os

SCOPES = ['https://www.googleapis.com/auth/androidpublisher']
PACKAGE = 'com.example.app'

def main(track: str, fraction: float):
    creds = service_account.Credentials.from_service_account_file(
        os.environ['PLAY_SERVICE_ACCOUNT'], scopes=SCOPES
    )
    service = build('androidpublisher', 'v3', credentials=creds)

    edits = service.edits()
    edit = edits.insert(packageName=PACKAGE, body={}).execute()
    edit_id = edit['id']

    current = edits.tracks().get(packageName=PACKAGE, editId=edit_id, track=track).execute()
    release = current['releases'][0]

    release['status'] = 'inProgress' if fraction < 1.0 else 'completed'
    release['userFraction'] = fraction if fraction < 1.0 else None

    edits.tracks().update(
        packageName=PACKAGE, editId=edit_id, track=track,
        body={'releases': [release]}
    ).execute()

    edits.commit(packageName=PACKAGE, editId=edit_id).execute()
    print(f"Promoted {track} to fraction={fraction}")

if __name__ == '__main__':
    main(sys.argv[1], float(sys.argv[2]))
```

```yaml
# .github/workflows/promote.yml
on:
  workflow_dispatch:
    inputs:
      track: { description: 'Track (production)', required: true, default: 'production' }
      fraction: { description: 'User fraction (0.01-1.0)', required: true, default: '0.05' }

jobs:
  promote:
    runs-on: ubuntu-latest
    environment: production-promote
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install google-api-python-client google-auth
      - run: python scripts/promote.py "${{ inputs.track }}" "${{ inputs.fraction }}"
        env:
          PLAY_SERVICE_ACCOUNT: ${{ secrets.PLAY_PUBLISHER_SA_JSON }}
```

Wrap in `environment: production-promote` so a separate set of reviewers must approve each promotion.

---

## 4. Halting A Bad Release

```python
# scripts/halt.py
release['status'] = 'halted'
# userFraction stays where it was; no new users get the update
# Existing affected users keep the broken version (a Play limitation)
```

When you halt:
- New users on the previous fraction stop receiving the new version.
- Users who already updated stay on the new version.

For users already on the bad release, kill switches (see `kill-switches.md`) disable the offending feature. Halting is the supply-side fix; kill switches are the demand-side fix.

### Halt runbook

Halting a rollout is a mitigation, not an incident close.

1. Halt the Play production release.
2. Freeze further promotions in CI.
3. Flip any relevant kill switch or backend fallback for already-updated users.
4. Pin the release dashboard to the affected `versionCode`.
5. Write the incident note: impact, affected cohorts, lever used, next checkpoint.
6. Decide whether the recovery path is resume, hotfix, backend rollback, or force update.

Do not resume because the graph "looks better" after the halt. Resume only after the affected cohort is stable for the agreed window and the root cause is understood.

---

## 5. Automated Stage Promotion With Crash-Rate Gates

```yaml
# .github/workflows/auto-promote.yml
on:
  schedule:
    - cron: '0 14 * * *'   # 14:00 UTC daily check

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Fetch current Play release status
        id: status
        run: python scripts/play_status.py > status.json
        env: { PLAY_SERVICE_ACCOUNT: ${{ secrets.PLAY_PUBLISHER_SA_JSON }} }

      - name: Read crash rate from Firebase Crashlytics
        id: crash
        run: python scripts/crashlytics_rate.py --version "$(jq -r .versionName status.json)" > crash.json
        env: { FIREBASE_SA: ${{ secrets.FIREBASE_SA_JSON }} }

      - name: Decide next fraction
        id: decide
        run: |
          rate=$(jq -r .crashFreeUsersPercent crash.json)
          baseline=$(jq -r .baselinePercent crash.json)
          delta=$(python -c "print($baseline - $rate)")
          if (( $(python -c "print(int($delta > 0.5))") )); then
            echo "action=halt" >> $GITHUB_OUTPUT
          elif (( $(python -c "print(int($delta < 0.1))") )); then
            current=$(jq -r .userFraction status.json)
            next=$(python -c "print(min(1.0, $current * 2))")
            echo "action=promote" >> $GITHUB_OUTPUT
            echo "fraction=$next" >> $GITHUB_OUTPUT
          else
            echo "action=hold" >> $GITHUB_OUTPUT
          fi

      - name: Apply decision
        run: |
          case "${{ steps.decide.outputs.action }}" in
            halt) python scripts/halt.py "production" ;;
            promote) python scripts/promote.py "production" "${{ steps.decide.outputs.fraction }}" ;;
            hold) echo "Holding; reviewing tomorrow" ;;
          esac
        env: { PLAY_SERVICE_ACCOUNT: ${{ secrets.PLAY_PUBLISHER_SA_JSON }} }
```

Decision rules (tune to your risk profile):

| Crash-free Δ vs baseline | Action |
|---|---|
| Worse by > 0.5 pp | Halt + Slack-alert release manager |
| Worse by 0.1 to 0.5 pp | Hold at current fraction, alert team |
| Within 0.1 pp | Double the fraction |
| Better than baseline | Double the fraction |

See `crash-rate-gating.md` for the metric source details.

---

## 6. Per-Country & Per-Device Staging

Play lets you stage by country:

```bash
# Promote to production at 5% globally, but 50% only in NZ (low-volume canary)
./gradlew :app:promoteArtifact \
  --promote-track=production \
  --user-fraction=0.05

# Then via Play Console UI: target country override for NZ to 50%
```

For per-device-class staging (e.g., "exclude Samsung Galaxy A series this release"), use Play's device catalog exclusion in Console. Useful when a known bug only affects certain chipsets.

---

## 7. Update Priority And In-App Updates

```kotlin
play {
    updatePriority.set(2)        // 0 = silent, 5 = critical
}
```

The priority is read by the In-App Updates API:

```kotlin
class InAppUpdateChecker @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val manager = AppUpdateManagerFactory.create(context)

    suspend fun check(): UpdateAction {
        val info = manager.appUpdateInfo.await()
        return when {
            info.updateAvailability() != UpdateAvailability.UPDATE_AVAILABLE -> UpdateAction.None
            info.updatePriority() >= 4 -> UpdateAction.Immediate(info)
            info.updatePriority() >= 2 -> UpdateAction.Flexible(info)
            else -> UpdateAction.None
        }
    }
}

sealed class UpdateAction {
    object None : UpdateAction()
    data class Flexible(val info: AppUpdateInfo) : UpdateAction()
    data class Immediate(val info: AppUpdateInfo) : UpdateAction()
}
```

| Priority | UX |
|---|---|
| 0-1 | Update silently next time Play decides |
| 2-3 | Flexible: background download + restart prompt |
| 4-5 | Immediate: blocking full-screen update dialog |

Reserve 4-5 for security-critical releases. Most go at 2-3.

---

## 8. Staged Rollout Diagram (Audit Trail)

Maintain a simple status log in CI artifacts:

```json
{
  "version": "2.0.0",
  "versionCode": 12340,
  "stages": [
    {"track": "internal", "promotedAt": "2026-06-15T10:00:00Z", "fraction": 1.0, "crashFree": 99.8},
    {"track": "alpha",    "promotedAt": "2026-06-16T10:00:00Z", "fraction": 1.0, "crashFree": 99.7},
    {"track": "beta",     "promotedAt": "2026-06-19T10:00:00Z", "fraction": 1.0, "crashFree": 99.6},
    {"track": "production","promotedAt": "2026-06-26T14:00:00Z", "fraction": 0.01, "crashFree": 99.5},
    {"track": "production","promotedAt": "2026-06-27T14:00:00Z", "fraction": 0.05, "crashFree": 99.5},
    {"track": "production","promotedAt": "2026-06-28T14:00:00Z", "fraction": 0.10, "crashFree": 99.5}
  ]
}
```

Stored as a build artifact + appended to a release-history file. Post-mortems reference this when reconstructing "what we knew and when."

---

## 9. Common Pitfalls

- **Going from 1% → 100% in one step.** Defeats the purpose.
- **Skipping the alpha/beta tracks.** Production is not where you find bugs.
- **No country-specific monitoring.** A bug only in India is invisible if your dashboard aggregates globally.
- **Halting without kill-switching the feature.** Users on the bad version remain affected.
- **Promoting on weekends.** No one is watching. Promote in business hours.
- **No environment protection on the promote workflow.** Anyone with `write` can ship to production.
- **Trusting Play's "% adopted" without independent measurement.** Play's number lags by hours; your Crashlytics by minutes.
- **Forgetting `releaseStatus = inProgress`.** Default in some Triple-T configs is `completed`, which bypasses staging.
- **Mixed-version mayhem on the backend.** A staged rollout means N versions live simultaneously. Your API must support all of them.
- **Forgetting to clean up halted releases in Play Console.** Sticky halts confuse the next release.

---

## 10. Further Reading

- [Triple-T Gradle Play Publisher](https://github.com/Triple-T/gradle-play-publisher) — promotion + rollout commands.
- [Play Developer API — Edits and Releases](https://developers.google.com/android-publisher/api-ref/rest/v3/edits.tracks) — official.
- [In-App Updates API](https://developer.android.com/guide/playcore/in-app-updates) — flexible vs immediate.
- [Android Vitals](https://developer.android.com/topic/performance/vitals) — Play Console's crash & ANR metrics.
- [Staged rollout in Play Console](https://support.google.com/googleplay/android-developer/answer/6346149) — Play UX walkthrough.

---

> **In short:** internal → alpha → beta → 1/5/10/25/50/100% production with 24h between stages. Automate promotion via Play Developer API; gate each step on crash-free rate. Halt fast; kill-switch in parallel. Audit every promotion.
