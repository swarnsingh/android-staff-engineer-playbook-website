# Release Engineering: Kill Switches

> A server-controlled flag that disables a specific feature within minutes of flipping it. Built on top of `feature-flags-and-remote-config.md`'s infrastructure but with operational discipline: who flips, how fast, what's audited.

---

## 1. When To Use A Kill Switch

| Scenario | Kill Switch? |
|---|---|
| New feature has a critical bug on Samsung Galaxy A | Yes |
| Server backend overloaded by new feature traffic | Yes |
| Regulatory request to disable a feature in one country | Yes |
| Security vulnerability in a specific code path | Yes |
| New feature has lower engagement than expected | No — A/B test |
| Need to change a UI string | No — server config |
| Wallet UI is slow on low-end devices | Yes (gated kill switch) |

The rule: kill switches are emergency brakes. Use them sparingly so they retain operational authority.

---

## 2. The Kill-Switch Flag Pattern

```kotlin
object Flags {
    // Kill switches are boolean. Default is `true` (feature enabled).
    // Server flipping to `false` disables.
    val killVideoCalls = BooleanFlag(
        key = "kill_video_calls",
        default = true,                       // ← default-enabled; flip = disable
        applyPolicy = ApplyPolicy.LIVE,        // ← live, not next-session
        owners = listOf("video-calls@example.com"),
    )

    val killBackgroundSync = BooleanFlag(
        key = "kill_background_sync",
        default = true,
        applyPolicy = ApplyPolicy.LIVE,
        owners = listOf("sync@example.com"),
    )
}
```

```kotlin
@Composable
fun VideoCallButton(...) {
    val enabled by remember { derivedStateOf { Flags.killVideoCalls() } }
    if (!enabled) return     // feature gone; no entry point
    Button(onClick = startVideoCall) { Text("Video Call") }
}
```

The naming convention is `kill_<feature>`. Server flipping to `false` means "kill the feature." Default `true` because if the flag service is down, you ship the feature (otherwise you'd accidentally kill on flag-fetch failure).

---

## 3. Live Apply Policy

Most flags use "next session" apply policy (see `mobile-system-design/feature-flags-and-remote-config.md`). Kill switches are the exception: they MUST take effect now, not at next launch.

```kotlin
class FlagsRepository @Inject constructor(...) {

    private val flagSet = MutableStateFlow(FlagSet.EMPTY)

    suspend fun refresh() {
        val response = api.fetchFlags(context.snapshot())
        store.write(FlagsSnapshot(response.flags, response.evaluatedAt))

        val newSet = evaluator.evaluate(FlagsSnapshot(response.flags, response.evaluatedAt))

        if (hasLiveFlagChange(flagSet.value, newSet)) {
            flagSet.value = newSet       // immediate
        } else {
            pendingSnapshot.value = newSet  // wait for next session
        }
    }

    private fun hasLiveFlagChange(old: FlagSet, new: FlagSet): Boolean {
        return old.entries.any { (key, oldValue) ->
            val newValue = new.entries[key]
            val policy = flagDefinitions[key]?.applyPolicy
            policy == ApplyPolicy.LIVE && oldValue != newValue
        }
    }
}
```

A kill switch flip triggers an immediate UI update via the StateFlow; any composable observing the flag re-runs.

---

## 4. Propagation Latency

How fast does a kill switch travel?

| Step | Typical latency |
|---|---|
| Engineer flips flag in dashboard | 0s |
| Flag service caches invalidated | 5-30s |
| Next client polling fetch | 0-300s (poll interval) |
| FCM "refresh flags" push (optional) | 2-10s |
| Client refresh + UI update | < 1s |
| **Total without FCM**: | up to 5 minutes |
| **Total with FCM push**: | < 15 seconds |

For true incident response, ship the FCM push path. Server flips the flag, then fires a `data` push to all devices:

```json
{ "type": "flags.refresh", "reason": "kill_video_calls" }
```

```kotlin
class FlagRefreshFcmService : FirebaseMessagingService() {
    @Inject lateinit var flagsRepository: FlagsRepository

    override fun onMessageReceived(message: RemoteMessage) {
        if (message.data["type"] == "flags.refresh") {
            CoroutineScope(Dispatchers.IO).launch {
                flagsRepository.refresh()
            }
        }
    }
}
```

FCM data messages bypass the app's normal polling cadence. Even backgrounded devices wake to apply the flip (subject to OEM kill caveats; see `mobile-system-design/push-notifications.md`).

---

## 5. Who Can Flip (Authorization)

The same dashboard that flips experiments shouldn't flip kill switches with the same authority. Distinct paths:

```yaml
# flags.config.yaml
flags:
  kill_video_calls:
    default: true
    apply_policy: LIVE
    owners: ["video-calls@example.com"]
    required_approvers: ["releng@example.com"]   # second sign-off
    audit_required: true                          # log every flip
    rollback_window: 24h                          # auto-revert if no human reapplies
```

A flag flip:
1. Engineer submits a flip request in the dashboard.
2. Dashboard requires a reason ("Sev-1 incident #4242").
3. A second signer (releng on-call or feature owner) approves.
4. Flag changes server-side, audit log records (who, when, why, approvers).
5. Optional FCM push fires.
6. Auto-revert if no one re-applies the flip within the rollback window.

The auto-revert is the most important rule: a kill switch that nobody re-validates becomes a forgotten dead feature.

---

## 6. Granular Kill Switches

Instead of one binary, use a gated kill switch for partial outages:

```kotlin
val killVideoCalls = VariantFlag(
    key = "kill_video_calls",
    default = "enabled",
    variants = listOf("enabled", "disabled_for_samsung_a", "disabled_for_low_ram", "disabled_globally"),
)

@Composable
fun VideoCallButton(...) {
    val mode = Flags.killVideoCalls()
    val show = when (mode) {
        "disabled_globally" -> false
        "disabled_for_samsung_a" -> !DeviceInfo.isSamsungA()
        "disabled_for_low_ram" -> DeviceInfo.totalRamMb > 4000
        else -> true
    }
    if (!show) return
    Button(onClick = startVideoCall) { Text("Video Call") }
}
```

The cohort-specific kill is far less disruptive than a global kill. Always reach for cohort-specific first.

---

## 7. Server-Side Kill For Backend Features

Some features have a server-side counterpart you need to kill simultaneously (e.g., a new endpoint that's overloading a service):

```kotlin
// Server BFF
fun handleVideoCallStart(...): Response {
    if (configService.killVideoCallsActive()) {
        return Response(status = 503, body = "Feature temporarily unavailable")
    }
    return startVideoCall(...)
}
```

```kotlin
// Client handles the 503 gracefully
suspend fun startVideoCall(): Result<...> {
    return runCatching { api.startVideoCall(...) }
        .onFailure { e ->
            if (e is HttpException && e.code() == 503) {
                analytics.log("video_call_unavailable_server_side")
                showSnack("Video calling is temporarily unavailable. Please try again later.")
            }
        }
}
```

Server + client kill together. Client kill hides the entry point; server kill rejects any race-condition calls. Defense in depth.

### API compatibility behavior

An API kill switch must return a response shape every supported client can parse. Do not invent a new error payload during an incident.

| Situation | Server behavior | Client expectation |
|---|---|---|
| Optional feature disabled | Return a typed business error such as `FEATURE_TEMPORARILY_UNAVAILABLE` | Hide entry point or show retryable unavailable state |
| Expensive endpoint overload | Return cached/stale response, smaller page size, or `Retry-After` | Back off; do not spin retries |
| New response shape is broken | Downgrade by capability to the previous shape | Old and current clients parse successfully |
| Security issue | Fail closed with force-update or blocked action | User cannot continue the risky flow |

Default-enabled flags are right for most client UI kill switches, because a flag-fetch outage should not remove features accidentally. Server/API kill switches need a per-risk default. For overload protection, fail open can take the backend down; for non-critical UI, fail closed can create a user outage. Document the default in the flag definition, not in tribal memory.

---

## 8. Kill Switches During A Bad Release

In a mobile incident, a kill switch is often faster than a hotfix and more useful than a Play halt. Use it to protect users who already updated.

| Release failure | Kill-switch response |
|---|---|
| New checkout UI crashes | Hide new checkout entry point and route to legacy checkout |
| Feed response shape breaks old parser | Server downgrades response by capability |
| Heavy animation causes jank on low-end devices | Disable animation for device-tier cohort |
| Backend dependency overloads | Return cached/stale state or disable the expensive feature |
| Security-sensitive path is unsafe | Block the action and force update if needed |

Every kill switch used during release response needs an expiry owner. If the switch remains off after the incident, it becomes a silent fork of the product.

---

## 9. Local Override For Engineering

```kotlin
class FlagsOverridesStore @Inject constructor(
    @ApplicationContext private val context: Context,
) {
    private val prefs = context.getSharedPreferences("flag_overrides", Context.MODE_PRIVATE)

    fun set(key: String, value: String) {
        check(BuildConfig.DEBUG) { "overrides only allowed in debug builds" }
        prefs.edit().putString(key, value).apply()
    }

    fun get(key: String): String? = if (BuildConfig.DEBUG) prefs.getString(key, null) else null
}
```

`FlagSet.get()` checks the override store first; in release builds, the override returns `null` and is ignored. Engineers can simulate kill switches locally without server flips. Production users cannot.

---

## 10. Telemetry

Every kill-switch evaluation logs:

```kotlin
analytics.log("flag_evaluated", mapOf(
    "flag" to flagKey,
    "value" to evaluatedValue,
    "isLiveApply" to (policy == ApplyPolicy.LIVE),
    "source" to source,  // "remote", "default", "override"
))
```

Server-side telemetry monitors:
- **Kill switch flip frequency.** A flag flipped > 5x in a month signals an unstable feature.
- **Auto-revert events.** A flag that auto-reverted without resolution is an incident.
- **Time from flag flip to deactivation rate plateau.** Did the kill actually take effect?

---

## 11. Common Pitfalls

- **Kill switch default = `false`.** A flag-fetch failure now silently kills the feature for all users. Always default `true`.
- **No FCM push for live flags.** A 5-minute propagation is too slow for incident response.
- **Flipping experiments and kill switches through the same path.** Different stakes, different approvals.
- **No auto-revert.** Kill switches become "abandoned switches" no one knows about.
- **Forgetting client-side kill = no server protection.** A racing client still calls the endpoint. Server-side kill too.
- **Kill switch around a feature that's deep in code.** If kill = compile-time `#if`, the user must update. If kill = runtime check, the user gets it instantly. Always runtime.
- **No audit log.** "Who killed video calls last night?" answerable in 30 seconds, not 3 hours.
- **Engineer-only kill authority.** Releng / on-call needs to be able to kill features they didn't write at 3 AM.
- **Killing without a path to re-enable.** Once killed, the rollout to re-enable should be staged: 1% → 10% → 100% to confirm the fix.
- **No expiry owner after an incident.** A disabled feature can become permanent by accident unless someone owns the re-enable plan.
- **No documented kill-switch list.** "What kill switches do we have?" — a release runbook should answer this in seconds.

---

## 12. Testing

```kotlin
@Test
fun killSwitch_disabled_hidesFeature() = runTest {
    val flagsRepo = FakeFlagsRepository().apply { set("kill_video_calls", "false") }
    composeRule.setContent { VideoCallButton(repo = flagsRepo) }
    composeRule.onNodeWithText("Video Call").assertDoesNotExist()
}

@Test
fun killSwitch_flagFetchFails_defaultsToEnabled() = runTest {
    val flagsRepo = FailingFlagsRepository()
    composeRule.setContent { VideoCallButton(repo = flagsRepo) }
    composeRule.onNodeWithText("Video Call").assertExists()
}
```

End-to-end: flip a kill switch in the staging flag service; assert the production-build staging APK hides the feature within the propagation window.

---

## 13. Further Reading

- [Martin Fowler — Feature Toggles taxonomy](https://martinfowler.com/articles/feature-toggles.html) — categorization: release, ops, experiment, permission.
- [GrowthBook](https://www.growthbook.io/) — open-source flag platform with kill-switch path.
- [LaunchDarkly — Kill switches](https://launchdarkly.com/blog/) — vendor patterns.
- [feature-flags-and-remote-config.md](../mobile-system-design/feature-flags-and-remote-config.md) — the underlying flag architecture.
- [push-notifications.md](../mobile-system-design/push-notifications.md) — FCM-driven flag refresh.

---

> **In short:** kill switches default-enabled, live-apply policy, FCM-driven refresh for < 15s propagation, gated approval, audit + auto-revert, server + client kill in tandem, cohort-specific where possible. Build them before you need them.
