# Release Engineering: Crash-Rate Gating (Automated Rollback)

> Automated checks that read crash + ANR metrics during a staged rollout and decide: promote, hold, or halt. The release manager isn't supposed to babysit Crashlytics at 3 AM.

---

## 1. The Metrics That Matter

| Metric | Source | Target |
|---|---|---|
| **Crash-free users** | Firebase Crashlytics / Android Vitals | > 99.5% |
| **Crash-free sessions** | Firebase Crashlytics | > 99.7% |
| **ANR rate** | Android Vitals | < 0.47% (Play's threshold) |
| **User-perceived ANR** | Android Vitals | < 0.20% |
| **Slow cold start rate** | Android Vitals | < 5% |
| **Slow rendering rate** | Android Vitals | < 5% |

"Crash-free users" is the gold standard: of all users who interacted with this version today, what fraction did NOT experience a crash? Above 99.5% is healthy. Below 99% is "do not promote." Below 98% is "halt the rollout immediately."

Always compare against a **baseline** (previous version) over the same time window. A 99.6% crash-free rate is great unless the previous version was 99.9%.

---

## 2. Reading Android Vitals (Play Developer API)

```python
# scripts/vitals_crashrate.py
from google.oauth2 import service_account
from googleapiclient.discovery import build
import argparse, sys, json
from datetime import datetime, timedelta

SCOPES = ['https://www.googleapis.com/auth/playdeveloperreporting']
PACKAGE = 'com.example.app'

def crash_free_users(version_code: int, hours: int) -> float:
    creds = service_account.Credentials.from_service_account_file(
        os.environ['PLAY_VITALS_SA'], scopes=SCOPES,
    )
    service = build('playdeveloperreporting', 'v1beta1', credentials=creds)

    now = datetime.utcnow()
    start = now - timedelta(hours=hours)

    body = {
        "timelineSpec": {
            "aggregationPeriod": "HOURLY",
            "startTime": {"year": start.year, "month": start.month, "day": start.day,
                          "hours": start.hour, "minutes": 0},
            "endTime":   {"year": now.year,   "month": now.month,   "day": now.day,
                          "hours": now.hour,   "minutes": 0},
        },
        "metrics": ["distinctUsers", "crashRate"],
        "filter": f'versionCode = {version_code}',
        "dimensions": ["versionCode"],
    }

    resp = service.vitals().crashrate().query(
        name=f"apps/{PACKAGE}/crashRateMetricSet",
        body=body,
    ).execute()

    rows = resp.get('rows', [])
    total_users = sum(int(r['metrics'][0]['decimalValue']['value']) for r in rows)
    crashed = sum(int(r['metrics'][1]['decimalValue']['value']) for r in rows)
    return 1.0 - (crashed / total_users) if total_users else 1.0

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--version-code', type=int, required=True)
    parser.add_argument('--hours', type=int, default=24)
    args = parser.parse_args()

    rate = crash_free_users(args.version_code, args.hours)
    print(json.dumps({"crashFreeUsers": rate, "versionCode": args.version_code, "hours": args.hours}))
```

```bash
python scripts/vitals_crashrate.py --version-code 12340 --hours 24
# {"crashFreeUsers": 0.9962, "versionCode": 12340, "hours": 24}
```

The Vitals API is the same Play Console reads; trust it.

---

## 3. Reading Firebase Crashlytics

Crashlytics doesn't expose a streaming API; you BigQuery-export and read from there:

```sql
-- BigQuery dataset: firebase_crashlytics.<package_name>_ANDROID
WITH window_users AS (
  SELECT
    COUNT(DISTINCT installation_uuid) AS users,
    COUNTIF(crashed) AS crashed_users,
  FROM `proj.firebase_crashlytics.com_example_app_ANDROID`
  WHERE event_timestamp BETWEEN
        TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR) AND CURRENT_TIMESTAMP()
    AND app_display_version = '2.0.0'
)
SELECT
  1 - (SAFE_DIVIDE(crashed_users, users)) AS crash_free_rate,
  users
FROM window_users;
```

```python
# scripts/crashlytics_bq.py
from google.cloud import bigquery
import sys, json

def crash_free_rate(version_name: str, hours: int) -> dict:
    client = bigquery.Client()
    query = f"""
        WITH window_users AS (
          SELECT
            COUNT(DISTINCT installation_uuid) AS users,
            COUNTIF(crashed) AS crashed_users
          FROM `proj.firebase_crashlytics.com_example_app_ANDROID`
          WHERE event_timestamp BETWEEN
                TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {hours} HOUR) AND CURRENT_TIMESTAMP()
            AND app_display_version = '{version_name}'
        )
        SELECT 1 - SAFE_DIVIDE(crashed_users, users) AS rate, users
        FROM window_users
    """
    row = list(client.query(query).result())[0]
    return {"crashFreeRate": float(row.rate), "users": int(row.users)}
```

Crashlytics gives richer per-issue breakdowns; Vitals is more authoritative for promote/halt decisions because it's the same source Play uses.

---

## 4. The Auto-Halt Workflow

```yaml
# .github/workflows/crash-gate.yml
on:
  schedule:
    - cron: '*/30 * * * *'   # every 30 min during a rollout
  workflow_dispatch:

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install google-api-python-client google-auth google-cloud-bigquery

      - name: Get current release status
        id: status
        run: |
          python scripts/play_status.py > status.json
          echo "version_code=$(jq -r .versionCode status.json)" >> $GITHUB_OUTPUT
          echo "fraction=$(jq -r .userFraction status.json)" >> $GITHUB_OUTPUT
        env: { PLAY_SERVICE_ACCOUNT: ${{ secrets.PLAY_PUBLISHER_SA_JSON }} }

      - name: Read crash-free rate (Vitals)
        id: crash
        run: |
          python scripts/vitals_crashrate.py \
            --version-code "${{ steps.status.outputs.version_code }}" \
            --hours 6 > vitals.json
          echo "rate=$(jq -r .crashFreeUsers vitals.json)" >> $GITHUB_OUTPUT
        env: { PLAY_VITALS_SA: ${{ secrets.PLAY_VITALS_SA_JSON }} }

      - name: Read baseline rate (previous version)
        id: baseline
        run: |
          prev=$(python scripts/previous_version.py "${{ steps.status.outputs.version_code }}")
          python scripts/vitals_crashrate.py --version-code "$prev" --hours 168 > baseline.json
          echo "rate=$(jq -r .crashFreeUsers baseline.json)" >> $GITHUB_OUTPUT
        env: { PLAY_VITALS_SA: ${{ secrets.PLAY_VITALS_SA_JSON }} }

      - name: Decision
        id: decide
        env:
          NOW: ${{ steps.crash.outputs.rate }}
          BASE: ${{ steps.baseline.outputs.rate }}
        run: |
          delta=$(python -c "print($BASE - $NOW)")
          echo "delta=$delta" >> $GITHUB_OUTPUT
          if (( $(python -c "print(int($NOW < 0.98))") )); then
            echo "action=halt-critical" >> $GITHUB_OUTPUT
          elif (( $(python -c "print(int($delta > 0.005))") )); then
            echo "action=halt-regression" >> $GITHUB_OUTPUT
          elif (( $(python -c "print(int($delta > 0.001))") )); then
            echo "action=hold" >> $GITHUB_OUTPUT
          else
            echo "action=promote-eligible" >> $GITHUB_OUTPUT
          fi

      - name: Apply
        run: |
          case "${{ steps.decide.outputs.action }}" in
            halt-critical)
              python scripts/halt.py production
              python scripts/slack_alert.py "🚨 HALTED v${{ steps.status.outputs.version_code }} — crash-free $NOW below 98%"
              ;;
            halt-regression)
              python scripts/halt.py production
              python scripts/slack_alert.py "⚠️ HALTED v${{ steps.status.outputs.version_code }} — crash regression $(printf %.2f%% "$(echo "${{steps.decide.outputs.delta}} * 100" | bc)") vs baseline"
              ;;
            hold)
              python scripts/slack_alert.py "⏸ HOLDING v${{ steps.status.outputs.version_code }} — minor regression; re-evaluating"
              ;;
            promote-eligible)
              # Only auto-promote on weekdays during business hours.
              dow=$(date -u +%u); hr=$(date -u +%H)
              if [ "$dow" -lt 6 ] && [ "$hr" -ge 14 ] && [ "$hr" -lt 22 ]; then
                next=$(python -c "print(min(1.0, ${{ steps.status.outputs.fraction }} * 2))")
                python scripts/promote.py production "$next"
                python scripts/slack_alert.py "✅ Promoted to $next"
              fi
              ;;
          esac
        env:
          PLAY_SERVICE_ACCOUNT: ${{ secrets.PLAY_PUBLISHER_SA_JSON }}
          SLACK_WEBHOOK: ${{ secrets.RELEASE_SLACK_WEBHOOK }}
          NOW: ${{ steps.crash.outputs.rate }}
```

Decision rules tuned to the org's risk profile. The thresholds (0.001, 0.005, 0.98) are starting points; calibrate on historical data.

---

## 5. Per-Cohort Crash Rates

A single global rate hides cohort regressions:

```python
# scripts/cohort_breakdown.py
COHORTS = [
    ("emerging_market_lowend",  "country IN ('IN','BR','ID') AND ram_mb < 4000"),
    ("flagship",                "country NOT IN ('IN','BR','ID') AND ram_mb >= 6000"),
    ("samsung_a_series",        "device_model LIKE 'SM-A%'"),
    ("oem_xiaomi",              "device_manufacturer = 'Xiaomi'"),
]

for name, filter_clause in COHORTS:
    rate = crash_free_with_filter(version_name, filter_clause)
    print(f"{name:30s}: {rate * 100:.2f}%")
```

If global is fine but `samsung_a_series` is at 96%, you've found a vendor-specific bug. Halt or kill-switch the offending feature on that cohort only.

---

## 6. Slack-Driven Manual Override

Auto-halt errs on caution. Sometimes a regression is acceptable (e.g., new feature has slightly worse baseline because it does more). Manual override pattern:

```python
# scripts/slack_promote_handler.py (Slack slash command)
# /release promote 0.10
def handle(user, command):
    if user not in RELENG_TEAM:
        return "Sorry, only releng can run this."
    if "promote" in command:
        fraction = float(command.split()[1])
        promote_production(fraction)
        return f"Promoted to {fraction}. Watching crash-free rate."
    if "halt" in command:
        halt_production()
        return "Halted. Run `/release resume` to undo."
```

Manual paths are audited (Slack channel + GitHub Actions log + Play Console history). No silent overrides.

---

## 7. Time Windows And Sample Size

A 6-hour window at 1% rollout might only have 5K active users. Crash-free rate is noisy at that scale. Rules:

| Rollout % | Min sample for decision | Window |
|---|---|---|
| 1% | 10K users | 12h |
| 5% | 50K users | 6h |
| 10% | 100K users | 4h |
| 25%+ | 250K users | 2h |

Don't promote prematurely just because the crash-free rate looks good with 200 users.

```python
def is_sample_sufficient(rollout_fraction: float, users_observed: int) -> bool:
    required = max(10_000, 1_000_000 * rollout_fraction)
    return users_observed >= required
```

---

## 8. ANR-Specific Gates

ANRs (Application Not Responding) have their own threshold:

```python
def anr_rate(version_code: int, hours: int) -> float:
    # via Vitals anrRateMetricSet, same shape as crashRateMetricSet
    ...
```

Play's "bad behavior threshold" is 0.47% ANR rate (1 in 200 sessions). Above that, Play deprioritizes the app in Search and may eventually remove it. Gate at 0.30% to give margin.

User-perceived ANRs (those that happened while the user was actually interacting) are stricter — gate at 0.20%.

---

## 9. Common Pitfalls

- **Comparing to no baseline.** "99.6% is fine" — if previous was 99.95%, you've regressed.
- **Auto-promoting outside business hours.** If something breaks on auto-promote at 3 AM Sunday, no human is responding for hours.
- **Tiny sample sizes.** 100 users isn't enough to estimate a 99.5% crash-free rate.
- **Only looking at global rate.** Cohort regressions hide.
- **Halting without alerting.** Silent halts confuse the next release manager.
- **Decision rules in code, not in a docs runbook.** When CI halts at 3 AM, on-call needs to read why.
- **Ignoring slow-rendering / slow-start rates.** They're soft failures that erode trust over time.
- **Trusting Crashlytics for the gate.** Vitals is the source Play uses; align with it.
- **No "cooldown" after a halt.** Halt + resume in 5 minutes hides whether the fix worked.
- **Manual overrides without audit.** Someone presses resume and forgets to monitor.

---

## 10. Further Reading

- [Play Developer Reporting API](https://developers.google.com/play/developer/reporting) — Vitals access.
- [Android Vitals — Crash rate & ANR](https://developer.android.com/topic/performance/vitals) — what Play measures.
- [Firebase Crashlytics BigQuery export](https://firebase.google.com/docs/crashlytics/bigquery-export) — historical cohort queries.
- [Play "bad behavior threshold"](https://support.google.com/googleplay/android-developer/answer/9859174) — the 0.47% ANR cutoff.
- [Site Reliability Engineering (SRE) ch. 33 — Lessons learned from other incidents](https://sre.google/sre-book/lessons-learned/) — incident discipline transferable to releases.

---

> **In short:** Vitals as the source of truth; compare against baseline; per-cohort breakdown; auto-halt with Slack alert; auto-promote only in business hours; sample-size minimums; ANR < 0.30% target. Don't make humans babysit dashboards.
