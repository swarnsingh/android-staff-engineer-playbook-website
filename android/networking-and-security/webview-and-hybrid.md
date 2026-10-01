# WebView & Hybrid Architecture

## Overview

Many large Android apps embed web content somewhere: help centers, promotional pages, 3-D Secure payment challenges, embedded checkout, legal documents, and hybrid features that iterate faster than releases. **WebView** is one way to render these surfaces. Native OAuth authorization requests belong in an external user agent such as a browser or Custom Tab, as required by [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252).

WebView sits at an awkward intersection: it is simultaneously a UI widget, a browser with your app's permissions, and a bridge between two trust domains (your native code and whatever the web content does). Treating it as "just a view that shows URLs" is how apps ship cross-site-scripting-shaped holes into production.

## Why It Matters

- **It's a browser inside your security boundary.** Content rendered in a WebView executes JavaScript inside your app's process. A JavaScript bridge exposed to the wrong page hands that page a native API surface with your app's identity and permissions.
- **Payment challenges may flow through it.** A 3-DS challenge may require WebView cookie and redirect handling; mistakes can break checkout or expose sensitive data. Native OAuth authorization uses an external browser context and returns to the app through a registered redirect URI.
- **It's the fastest hybrid escape hatch** — and the easiest to over-use. Staff engineers need a principled answer for *which* surfaces belong in web content and which never should.
- **It ships separately from your app.** WebView updates through Play as its own package; the engine version under your feature changes without your release train's involvement.

## First Principles

1.  **Two trust domains, one process.** Native code is trusted; loaded web content is not (even "your own" pages can be compromised, MITM'd on old devices, or redirected). Every WebView design decision is about policing that boundary.
2.  **The URL decides the trust.** What the WebView is *currently showing* determines what capabilities it should have. Navigation is therefore a security event, not just a UX event.
3.  **Bridges are API surface.** Anything exposed via a JavaScript bridge is a public API callable by whatever wins control of the page.
4.  **The engine is a dependency you don't pin.** Behavior varies by installed WebView version and OEM; feature-detect via `androidx.webkit` rather than assuming.

## Mental Model

A WebView is a **guest worker inside your office building**.

- They do real work you don't want to staff natively (content pages, fast-changing flows).
- They wear your badge: network calls, cookies, and anything you bridge to them happen with your app's identity.
- The rooms they can open are exactly the rooms you badge them into — that's the JavaScript bridge and the settings you enable.
- You verify *who they are* at the door (URL allowlisting on every navigation), not once at hiring time (initial `loadUrl`).

Security reviews of WebView code are access-control reviews of that badge.

## Internal Mechanics

### What loads and runs where

- Since Android 5.0, WebView is an updatable APK (Play-delivered); since Android 8.0, page rendering runs in a **separate sandboxed renderer process**, so a renderer compromise or crash doesn't automatically own your app process — but your bridges and cookies remain in *your* process, so the boundary you control is still the interesting one.
- `WebSettings` gate the risk surface: `javaScriptEnabled` (off by default — leave off for static content), file access flags (the legacy `file://` access settings are deprecated; don't resurrect them), mixed-content mode.

### The JavaScript bridge, safely

The official guidance is blunt: **don't use `addJavascriptInterface()` unless you wrote all of the HTML and JavaScript in the WebView.** The injected object is visible in **every frame, including iframes** — a malicious iframe in an otherwise-trusted page can call your bridge.

```kotlin
// Only for fully-controlled content, and audit every method:
class Bridge(private val onEvent: (String) -> Unit) {
    @JavascriptInterface        // required; only annotated methods are exposed
    fun postEvent(json: String) = onEvent(json)   // treat as untrusted input: validate, no reflection
}
webView.addJavascriptInterface(Bridge(::handle), "NativeBridge")
```

The modern alternative for anything beyond fully-owned content is **message-channel messaging** — `WebViewCompat.addWebMessageListener` / `postWebMessage` from `androidx.webkit` — which lets you scope the channel to **explicit trusted origins** instead of exposing an object to every frame:

```kotlin
if (WebViewFeature.isFeatureSupported(WebViewFeature.WEB_MESSAGE_LISTENER)) {
    WebViewCompat.addWebMessageListener(
        webView, "checkoutBridge",
        setOf("https://checkout.example.com"),      // origin allowlist — never "*"
    ) { _, message, sourceOrigin, isMainFrame, replyProxy ->
        if (!isMainFrame) return@addWebMessageListener
        handleCheckoutMessage(message.data, replyProxy)
    }
}
```

### Loading your own assets

Never serve app-bundled content via `file://`. Use **`WebViewAssetLoader`**, which serves local assets over an `https://` virtual domain — same-origin policy works, and the deprecated file-access settings stay off.

### Navigation policing

```kotlin
override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
    // Subframes CAN trigger this callback (official docs: "may be called for
    // subframes and with non-HTTP(S) schemes"). Never let an iframe cause
    // native side effects — block it instead of routing it.
    if (!request.isForMainFrame) return true                 // cancel subframe navigations off-allowlist

    val url = request.url
    return when {
        url.host in allowedHosts -> false                    // let the WebView load it
        url.scheme in setOf("http", "https") -> {
            customTabs.launch(url); true                     // kick unknown web out to a browser context
        }
        url.scheme in allowedAppSchemes -> {
            deepLinkRouter.handle(url); true                 // only allowlisted app schemes reach the router
        }
        else -> true                                         // unknown scheme: cancel, log, do nothing
    }
}
```

Allowlist, don't blocklist — and gate every native side effect on `request.isForMainFrame`, or an iframe inside an otherwise-trusted page can launch Custom Tabs or drive your deep-link router. Also know the callback's limits: it is **not called for POST requests**, and resource loads/XHR go through `shouldInterceptRequest` instead — the bridge-origin scoping above is what actually protects the bridge.

## Architecture: Where Hybrid Belongs

| Surface | Verdict | Why |
|---|---|---|
| Help center, legal, blog content | WebView (or Custom Tabs) | High churn, low interactivity, no bridge needed |
| 3-DS / PSD2 payment challenge | WebView, isolated | Bank-controlled content; needs cookies + redirect capture; no bridge |
| OAuth authorization in native apps | **External browser or Custom Tab, not WebView** | [RFC 8252](https://www.rfc-editor.org/rfc/rfc8252) requires an external user agent; it keeps credentials and browser session state outside the app's WebView |
| Checkout / high-iteration commerce flows | Hybrid with message-channel bridge | Iteration speed matters; scope the bridge per-origin |
| Core navigation, feeds, camera/media surfaces | Native | Perf, gestures, offline, a11y — WebView tax too high |
| Anything needing native capability exposure | Native or SDUI first | Every bridged capability is permanent API surface ([`../../mobile-system-design/server-driven-ui.md`](../../mobile-system-design/server-driven-ui.md) is often the better dynamism tool) |

## Production Example

**The 3-DS challenge that ate checkout.**

A payments team embeds their PSP's 3-DS challenge in a WebView. Three incidents over one year:

1. **Cookie loss:** the challenge relies on a session cookie set on a prior redirect; the app used a fresh WebView per screen, so `CookieManager` state was there but third-party cookie defaults differed across WebView versions → intermittent challenge loops on a subset of devices. Fix: pin the whole flow to one WebView instance, explicitly configure cookie acceptance for the PSP's domains, and assert the cookie before loading.
2. **Redirect capture:** success returns via a `https://merchant.example/3ds-complete?...` redirect. The team parsed it in `onPageFinished` (fires for iframes and intermediate pages too) and double-processed results. Fix: intercept in `shouldOverrideUrlLoading` on exact host+path match, finish the WebView, hand the token to native code.
3. **The debug hole:** `setWebContentsDebuggingEnabled(true)` shipped in a release build "temporarily" for a support investigation — remote-debuggable checkout WebViews in production. Fix: tie it to `BuildConfig.DEBUG` and add a release-build lint check.

The pattern across all three: WebView flows fail at the *edges* (cookies, redirects, settings), not in the middle — so the edges are what you test and lint.

## Tradeoffs

- **Iteration speed vs capability tax:** web content deploys same-day but pays for it in gesture fidelity, startup cost (~100ms+ first-WebView-in-process init), memory (a renderer process), and a11y that must be correct in *two* stacks (TalkBack ↔ page semantics).
- **WebView vs Custom Tabs:** Custom Tabs gives you the user's real browser (their sessions, their password manager, Safe Browsing UI) and takes away your bridge and your chrome. Default to Custom Tabs for third-party content; reserve WebView for content you need to *integrate*, not just display.
- **One shared WebView vs per-feature instances:** sharing amortizes init cost but couples cookie/session state across features; per-flow instances isolate state but re-pay startup. Payment challenges can use a dedicated instance; OAuth authorization runs in an external user agent.

## Failure Modes

- **Bridge exposed to hostile content:** a redirect or compromised page reaches a screen whose `addJavascriptInterface` bridge is still attached → every `@JavascriptInterface` method is now attacker-callable. *(Fix: origin-scoped `WebMessageListener`, or tear down bridges on navigation away from trusted hosts.)*
- **Deprecated file-access flags re-enabled** to "make local content work" → any XSS becomes local-file exfiltration. *(Fix: `WebViewAssetLoader`.)*
- **TLS errors swallowed:** overriding `onReceivedSslError` with `proceed()` to silence a staging-cert complaint ships MITM acceptance to production. Play flags this pattern in review. *(Fix: never call `proceed()` on real errors; use debug-only network security config for staging.)*
- **`evaluateJavascript` with concatenated input:** native → JS injection, the mirror image of the bridge problem. *(Fix: pass data via `postWebMessage`/JSON-encoded single argument.)*
- **Memory/renderer churn on low-end devices:** multiple live WebViews on 2GB devices trigger renderer kills that present as blank white views. *(Fix: cap live instances; handle `onRenderProcessGone` by rebuilding the view — returning `true` keeps your app alive.)*

## Staff Engineer Thinking

1.  **Treat the bridge like a public SDK.** Versioned, documented, reviewed like any API; every method assumes hostile input; removal follows a deprecation policy because web content ships on its own cadence.
2.  **Make the trust boundary auditable.** One place in the codebase constructs WebViews (a factory that applies settings, clients, and lint-enforced defaults). "Find every WebView configuration" should be a one-file read, not a grep expedition.
3.  **Decide hybrid surfaces with a rubric, not per-feature debate:** iteration rate, interactivity depth, offline need, a11y complexity, capability needs. Publish the rubric; revisit yearly.
4.  **Own the version matrix.** WebView version distribution is part of your crash triage — pull it into observability dimensions so "blank checkout on Android 10" correlates with engine versions, not just app versions.

## Common Misconceptions

- **"It's our own page, so the bridge is safe."** Your page today; an open redirect, subdomain takeover, or compromised CDN tomorrow. Origin-scope the bridge anyway.
- **"`shouldOverrideUrlLoading` sees all navigation."** It doesn't — POST requests never reach it, and XHR/resource loads go through `shouldInterceptRequest`. Meanwhile it *can* fire for subframes, so unguarded handlers turn iframes into native-side-effect triggers. Treat it as UX routing with an `isForMainFrame` gate, not a security boundary.
- **"WebView is dying; everything is native/Compose now."** Payment challenges (3-DS), embedded commerce, and content surfaces still create WebView use cases. The skill is to contain its trust boundary and route OAuth authorization through an external user agent.
- **"Custom Tabs and WebView are interchangeable."** They differ in exactly the dimension that matters: whose session state and whose security UI the user gets.

## Probing Questions

1.  Walk through the trust boundary of a WebView with a JavaScript bridge. What exactly can a malicious iframe do, and which API changes the answer?
2.  Why must app-bundled content load through `WebViewAssetLoader` instead of `file://`, and what attack does that close?
3.  Design the WebView setup for a 3-DS payment challenge: instance strategy, cookie handling, redirect capture, and the settings you'd lint against.
4.  When do you choose Custom Tabs over WebView, and what do you lose in each direction?
5.  A blank white view appears intermittently on low-end devices. Walk through the renderer-process explanation and the recovery path.
6.  How would you structure a hybrid-surface rubric for a 40-team app, and how do you keep teams from routing around it?

## Answer Key

1. **Walk through the trust boundary of a WebView with a JavaScript bridge. What exactly can a malicious iframe do, and which API changes the answer?**
   A malicious iframe can execute arbitrary JS that calls native methods exposed via the bridge, effectively wielding app-level permissions. Using `addJavascriptInterface()` exposes the bridge to all frames. Switching to `WebViewCompat.addWebMessageListener` restricts access to specific trusted origins.
2. **Why must app-bundled content load through `WebViewAssetLoader` instead of `file://`, and what attack does that close?**
   Loading via `file://` requires enabling legacy file access flags, which can be exploited by XSS to read arbitrary local files from the device. `WebViewAssetLoader` creates an HTTPS virtual domain, respecting standard Same-Origin policies while safely serving local files.
3. **Design the WebView setup for a 3-DS payment challenge: instance strategy, cookie handling, redirect capture, and the settings you'd lint against.**
   Use a dedicated WebView instance for the flow to isolate state. Explicitly configure `CookieManager` to accept third-party cookies for the PSP domain. Capture redirects carefully via `shouldOverrideUrlLoading` (ensuring `isForMainFrame`). Lint against `setWebContentsDebuggingEnabled` in release and `onReceivedSslError.proceed()`.
4. **When do you choose Custom Tabs over WebView, and what do you lose in each direction?**
   Choose Custom Tabs for OAuth or third-party web content to utilize the browser's cookies and password manager safely. You lose UI customizability and the ability to bridge JS to native. Choose WebView when deep native integration and customized UI are strictly required.
5. **A blank white view appears intermittently on low-end devices. Walk through the renderer-process explanation and the recovery path.**
   On low-memory devices, Android may kill the separate WebView renderer process to reclaim RAM, leaving the native WebView empty. Recover by overriding `onRenderProcessGone()`, returning `true` to keep the app alive, and rebuilding or reloading the WebView.
6. **How would you structure a hybrid-surface rubric for a 40-team app, and how do you keep teams from routing around it?**
   Define clear guidelines based on interaction depth, offline requirements, capability access, and iteration speed. Implement CI lint checks and centralize WebView creation in a single, well-reviewed factory class so teams physically cannot instantiate rogue WebViews.

## Further Reading

- [WebView — native bridges risk](https://developer.android.com/privacy-and-security/risks/insecure-webview-native-bridges) — official guidance on `addJavascriptInterface` and message listeners.
- [WebView — unsafe file inclusion](https://developer.android.com/privacy-and-security/risks/webview-unsafe-file-inclusion) — why the file-access flags are deprecated; `WebViewAssetLoader`.
- [Build web apps in WebView](https://developer.android.com/develop/ui/views/layout/webapps/webview) — platform documentation.
- [OAuth 2.0 for Native Apps (RFC 8252)](https://www.rfc-editor.org/rfc/rfc8252) — external user-agent requirement for authorization requests.
- [`WebViewAssetLoader`](https://developer.android.com/reference/androidx/webkit/WebViewAssetLoader) / [`WebViewCompat.WebMessageListener`](https://developer.android.com/reference/androidx/webkit/WebViewCompat.WebMessageListener) — the two androidx.webkit APIs this file leans on.
- [`security-and-keystore.md`](security-and-keystore.md) — the broader app trust model this plugs into.
- [`../../mobile-system-design/payment-flow.md`](../../mobile-system-design/payment-flow.md) — where the 3-DS flow fits in checkout.
- [`../../security/certificate-pinning.md`](../../security/certificate-pinning.md) — why `onReceivedSslError.proceed()` is never the fix.
