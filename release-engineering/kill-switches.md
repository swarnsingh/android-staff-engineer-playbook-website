# Release Engineering: Kill Switches

## The Prompt

*"Your team just shipped a massive new Video Call feature to 100% of your Android users. Two hours later, you discover a critical bug in the Video Call SDK that causes the phone's microphone to overheat and crash the OS. You cannot un-publish the app. You cannot wait 2 days for a Hotfix review. How do you stop users from using the feature instantly?"*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Instantly disable a broken feature for 100% of active users.
- Hide the entry points to the feature in the UI.
- Fail gracefully if the user is already inside the feature.

### Non-Functional Requirements (NFRs)
- **Latency (Priority 0):** The kill switch must propagate globally in seconds or minutes, not days.
- **Resilience:** The Kill Switch infrastructure itself must never crash. It must be highly available and isolated from the core application backend.

## 2. High-Level Architecture (The Remote Config Paradigm)

A Junior engineer says "We'll just turn off the Video Call backend server." This causes the Android app to make network requests, time out, show ugly error dialogs, and potentially crash if it doesn't handle HTTP 500s correctly.
A Staff engineer uses a **Client-Side Kill Switch** driven by Remote Config.

```mermaid
graph TD
    subgraph Mobile App (Android)
        Config[(Remote Config Cache)]
        Engine[Kill Switch Engine]
        UI[App UI]
        Feature[Video Call Module]
    end
    
    subgraph Incident Response
        SRE[SRE / Release Manager] -->|Panic Button| Dashboard[Config Dashboard]
        Dashboard --> CDN[(Global Edge CDN)]
    end
    
    CDN -.->|Push / Short TTL Pull| Config
    UI -->|1. Check `is_video_killed`| Engine
    Engine -->|Returns True| UI
    UI -->|2. Hide Button| Feature
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Granularity of the Kill Switch
*Interviewer:* "Do you have one giant Kill Switch for the entire app?"

**Staff Answer:**
"No, a global kill switch is only for catastrophic API failures (Force Update/Maintenance Mode). For features, we use **Granular Kill Switches**.
Every major feature (Video Calls, Payments, Chat, Search) has its own dedicated boolean in the Remote Config payload:
```json
{
  "kill_video_calls": true,
  "kill_payments": false,
  "kill_chat": false
}
```
If the Video Call SDK is melting phones, we only flip `kill_video_calls` to `true`. The rest of the application functions perfectly, preserving 90% of the company's revenue."

### Flow 2: UI Degradation (Hiding the Entry Points)
*Interviewer:* "The Kill Switch is flipped to `true`. What exactly happens on the user's screen?"

**Staff Answer:**
"The UI must degrade gracefully. We do not show an error dialog. We remove the feature from existence.
1. The 'Start Video Call' button (`FloatingActionButton`) is wrapped in a check:
   `if (KillSwitch.isKilled("video_calls")) { fab.visibility = View.GONE }`
2. If the user is *already* inside the Video Call screen when the payload arrives (via a silent push or background sync), the app immediately terminates the call, pops the fragment off the back-stack, and shows a non-intrusive Snackbar: 'Video Calls are temporarily disabled for maintenance.'
This requires strictly wrapping every entry point to a major feature in the Kill Switch evaluation."

### Flow 3: Propagation Strategy (Pull vs Push)
*Interviewer:* "How does the Android app actually receive the 'true' signal instantly? If your config cache is set to 12 hours, the phone won't check for updates until tomorrow."

**Staff Answer:**
"We combine **Short TTL Polling** with **Silent Push Notifications**.
1. **Pull (Standard):** We configure the Remote Config SDK with a relatively short TTL (Time-To-Live), such as 1 hour. This guarantees a baseline recovery.
2. **Push (Instant):** When an SRE flips the panic button on the dashboard, the backend broadcasts a **Silent Push Notification** (FCM Data Payload) to all active devices.
3. The Silent Push wakes up the `FirebaseMessagingService`.
4. The service reads the payload: `{"action": "invalidate_config"}`.
5. The service immediately invalidates the 1-hour cache and forces the Remote Config SDK to fetch the newest JSON from the CDN. The UI is updated instantly."

## 4. Failure Modes & Bottlenecks

### Bottleneck: The Kill Switch Breaks the App
*Interviewer:* "You flip the `kill_payments` switch. The entire app crashes on startup. Why?"

**Staff Answer:**
"The Kill Switch path was never tested.
When a feature is built, engineers test the 'Happy Path' (Payments enabled). If they never test the 'Sad Path' (Payments disabled), they might leave a `null` reference or a broken dependency injection graph when the feature is forcibly removed from the UI.
**The Fix:** Automated UI Tests (Espresso/UIAutomator) must run nightly on CI with **every single kill switch flipped to true**. The app must prove it can boot and navigate safely when degraded."

### Bottleneck: The Infinite Retry Storm
*Interviewer:* "You kill the Video Call feature. But there's a background `WorkManager` job that is trying to upload a missed Video Call log. It keeps failing, retrying, and draining the battery."

**Staff Answer:**
"The Kill Switch must penetrate to the Background Layer, not just the UI layer.
1. When `kill_video_calls` is flipped, the `KillSwitchEngine` must broadcast an internal event (e.g., Kotlin `SharedFlow`).
2. All background jobs related to Video Calls must subscribe to this event.
3. If they detect the kill switch is active, they must instantly `cancelAllWork()` or return `Result.failure()` to clear themselves from the OS scheduling queue. They must not infinitely retry."

## 5. Staff Engineer Thinking: Technical Debt of Kill Switches

A Junior engineer leaves Kill Switches in the code forever. A Staff Engineer knows that Kill Switches, like Feature Flags, are Technical Debt.

However, unlike Feature Flags (which expire after 30 days when a rollout hits 100%), **Kill Switches are permanent infrastructure**.

If you build a Payment Gateway, you keep the `kill_payments` switch in the code forever. A 3rd-party API like Stripe can go down at any time, 5 years from now. You must always have the ability to turn it off. The cost is that the UI must forever support the `View.GONE` state for that button.

## 6. Probing Questions (For Practice)

1.  Explain why turning off the backend server is a dangerous and poor alternative to using a Client-Side Kill Switch.
2.  Describe the concept of "Granularity" in Kill Switches. Why should a major app have 10-20 kill switches instead of just one?
3.  Walk through the "Graceful Degradation" of the UI. What happens to entry points, and what happens if the user is already inside the feature?
4.  How does a Silent Push Notification (FCM) solve the latency problem of a Remote Config cache that is set to expire in 12 hours?
5.  Why is it critical to run automated CI tests with all Kill Switches flipped to `true`? What type of bug does this prevent?
6.  Explain how a Kill Switch must interact with Android's `WorkManager`. Why is hiding the UI button not enough?
7.  Differentiate between the lifespan of a Feature Flag and a Kill Switch. Why are Kill Switches considered permanent infrastructure?
8.  If the CDN hosting the Kill Switch JSON goes down completely, what should the Android app's default behavior be (Fail Open vs Fail Closed)?
9.  Describe the architectural pattern required to ensure a developer remembers to wrap a new button in a Kill Switch check before merging their PR.
10. How do you handle deep links or App Links that point directly to a feature that is currently disabled by a Kill Switch?

## Further Reading

- [`feature-flags-and-remote-config.md`](../mobile-system-design/feature-flags-and-remote-config.md) — The underlying infrastructure that powers Kill Switches.
- [`push-notifications.md`](../mobile-system-design/push-notifications.md) — How Silent Pushes wake the app to invalidate the config cache.
- [`staged-rollouts.md`](staged-rollouts.md) — Why Kill Switches are necessary because Hotfixes take 2 days.
