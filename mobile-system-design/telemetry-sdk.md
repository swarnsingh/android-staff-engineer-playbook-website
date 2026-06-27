# Platform Design: Telemetry SDK (Crash & Performance)

## The Prompt

*"Design a Telemetry SDK (like Crashlytics or New Relic) that will be embedded into thousands of third-party Android apps. It must capture unhandled exceptions, ANRs (Application Not Responding), and network performance. It must run silently in the background, consume near-zero battery, and never cause the host application to crash."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- **Crash Reporting:** Intercept unhandled exceptions (Java/Kotlin) and Native crashes (C++).
- **ANR Detection:** Detect when the Main Thread is blocked for > 5 seconds.
- **Network Interception:** Automatically track HTTP request latency and status codes.

### Non-Functional Requirements (NFRs)
- **Safety (Priority 0):** The SDK code MUST NOT throw exceptions that crash the host app. If the Telemetry SDK crashes, you destroy the customer's business.
- **Battery/Network:** Do not fire an HTTP request for every single event. Batch and compress.
- **Initialization:** Must initialize instantly (< 5ms) without the host developer writing complex setup code.

## 2. High-Level Architecture (The Silent Observer)

A Junior engineer designs an SDK that forces the host developer to call `Telemetry.logEvent()` everywhere.
A Staff engineer designs an **Auto-Instrumenting SDK** that hooks into the Android OS lifecycle silently.

```mermaid
graph TD
    subgraph Host Application (Android)
        App[Host Code]
        
        subgraph Telemetry SDK
            CrashHook[UncaughtExceptionHandler]
            ANRHook[Choreographer/Watchdog]
            NetHook[OkHttp Interceptor]
            
            Buffer[(Disk Buffer - SQLite)]
            Sender[Transmission Engine]
        end
    end
    
    App -- Crashes --> CrashHook
    CrashHook -->|Synchronous Write| Buffer
    
    App -- Blocked Main Thread --> ANRHook
    ANRHook -->|Stack Trace| Buffer
    
    App -- HTTP Request --> NetHook
    NetHook -->|Metrics| Buffer
    
    Sender -->|Batched GZIP Upload| Backend[Ingestion Gateway]
```

## 3. The Core Flows (Deep Dive)

### Flow 1: Intercepting Crashes (The Final Will & Testament)
*Interviewer:* "The host app throws a `NullPointerException`. The OS is about to terminate the process and erase all memory. How does your SDK catch it and save the stack trace?"

**Staff Answer:**
"I must replace the JVM's default crash handler.
1. During SDK initialization, I call `Thread.setDefaultUncaughtExceptionHandler(myCustomHandler)`.
2. When the NPE occurs, the JVM pauses the crash and calls my handler.
3. **CRITICAL:** I have milliseconds before the OS forcefully kills the process. I cannot make a network request. I cannot allocate massive amounts of memory (if it's an OOM crash). I must write the StackTrace synchronously to a flat file on disk (or a pre-allocated memory-mapped file).
4. Finally, I *must* call the original `UncaughtExceptionHandler` that I replaced, so the OS can finish the crash process normally (showing the 'App has stopped' dialog). If I don't, the app freezes in a zombie state."

### Flow 2: ANR Detection (The Watchdog Thread)
*Interviewer:* "The Main Thread is blocked in an infinite `while` loop. The app is completely frozen. How does your SDK detect this?"

**Staff Answer:**
"I cannot rely on the Main Thread to report its own death. I must spawn a background **Watchdog Thread**.
1. The Watchdog Thread wakes up every 5 seconds.
2. It posts a simple `Runnable` to the Main Thread's `Looper`. The `Runnable` just increments a counter.
3. The Watchdog goes to sleep for 5 seconds.
4. When it wakes up, it checks the counter. If the counter did *not* increment, it means the Main Thread was too blocked to execute the tiny `Runnable`. We have an ANR!
5. The Watchdog Thread immediately calls `Looper.getMainLooper().thread.stackTrace` to grab the frozen thread's stack trace and writes it to disk."

### Flow 3: Auto-Instrumentation (Bytecode Manipulation)
*Interviewer:* "You want to track every HTTP request made by `OkHttp` or `Retrofit`. But you cannot force the host developer to manually add your Interceptor to their `OkHttpClient.Builder()`. How do you inject it automatically?"

**Staff Answer:**
"This requires a **Gradle Plugin** performing Bytecode Manipulation (via ASM or Transform API).
1. When the host developer compiles their app, my Gradle Plugin intercepts the `.class` files before they are converted to `.dex`.
2. The plugin searches the bytecode for `new OkHttpClient.Builder()`.
3. It rewrites the bytecode on the fly to inject `.addInterceptor(new TelemetryInterceptor())`.
4. At runtime, the app behaves as if the developer typed the code themselves. This provides zero-touch integration."

## 4. Failure Modes & Bottlenecks

### Bottleneck: The Transmission Storm (Battery Drain)
*Interviewer:* "Your SDK records 5,000 UI click events, 20 network requests, and 3 handled exceptions in a 10-minute session. Do you send 5,023 HTTP POST requests to your backend?"

**Staff Answer:**
"Absolutely not. That would destroy the battery and saturate the network.
1.  **Disk Buffering:** Every event is serialized (preferably to Protobuf) and written to SQLite or a flat file.
2.  **Batching:** We only upload when the buffer reaches a size threshold (e.g., 50KB), or when the app is backgrounded (`onStop`).
3.  **Compression:** The batched payload MUST be compressed using GZIP before transmission. Text logs achieve 80-90% compression ratios, drastically saving cellular data."

### Bottleneck: The Infinite Recursion Crash
*Interviewer:* "Your Telemetry SDK's network upload code throws an `IOException`. Your SDK catches its own exception and tries to log it. The logging code throws an exception, which logs it again. The app crashes with a `StackOverflowError`."

**Staff Answer:**
"This is the most dangerous bug in a Telemetry SDK. The SDK must have a strict **Internal Boundary**.
1. All SDK code must be wrapped in global `try-catch (Throwable t)` blocks.
2. If an exception occurs *inside* the SDK namespace (e.g., `com.telemetry.*`), we increment a silent counter and immediately abort the logging attempt. We **never** route SDK-internal exceptions back through the public event pipeline."

## 5. Staff Engineer Thinking: SDK Integration Friction

A Staff Engineer understands that developers hate integrating SDKs. If it takes more than 1 line of code, they won't use it.

- **The Old Way:** The developer adds `Telemetry.initialize(context, "API_KEY")` in their `Application.onCreate()`. This slows down app startup.
- **The Modern Way (ContentProvider):** I will declare an empty `ContentProvider` in my SDK's `AndroidManifest.xml`. The Android OS automatically initializes all `ContentProviders` *before* it calls `Application.onCreate()`. My `ContentProvider` extracts the API Key from the manifest metadata and initializes the SDK completely silently. The developer literally only has to add `implementation 'com.telemetry:sdk'` to their `build.gradle`, and the SDK works instantly. (Note: Jetpack App Startup does exactly this under the hood).

## 6. Probing Questions (For Practice)

1.  Explain why a Telemetry SDK must never throw an unhandled exception back to the host application, and how you ensure a strict internal boundary.
2.  Walk through the precise mechanism of replacing the JVM's `UncaughtExceptionHandler`. Why must you execute your logic in milliseconds before the OS terminates the process?
3.  Describe the "Watchdog Thread" architecture for detecting ANRs (Application Not Responding). Why must the detection logic live on a background thread?
4.  How does a Gradle Plugin use Bytecode Manipulation (ASM) to auto-instrument network calls without requiring the host developer to modify their code?
5.  Why is it an architectural failure to send a network request for every individual telemetry event? Detail the Batching and GZIP compression strategy.
6.  Explain the "Infinite Recursion Crash" inside a logging SDK and the mathematical safeguard required to prevent a `StackOverflowError`.
7.  Describe how an empty `ContentProvider` allows an SDK to initialize automatically without the host developer writing `Telemetry.init()` in their Application class.
8.  If the host application throws a fatal `OutOfMemoryError` (OOM), why might your Crash Hook fail to write the stack trace to a SQLite database, and how do you mitigate this?
9.  Explain why a Telemetry SDK must permanently store its collected data on Disk (SQLite/Files) rather than holding it in a RAM buffer before batch uploading.
10. If the user is on an unreliable cellular network and the batched payload upload fails, how does the SDK ensure those logs are not lost while preventing duplicate uploads?

## Further Reading

- [`anrs.md`](../android/performance/anrs.md) — The deep dive into what actually blocks the Main Thread.
- [`app-startup.md`](app-startup.md) — How the `ContentProvider` trick impacts cold start times.
- [`gradle-and-build-systems.md`](../android/os-internals/gradle-and-build-systems.md) — The fundamentals of Bytecode Manipulation via Gradle.
