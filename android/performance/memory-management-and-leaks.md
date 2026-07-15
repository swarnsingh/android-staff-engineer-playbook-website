# Memory Management and Leaks

## Overview

In the Java/Kotlin ecosystem, memory management is handled by the Garbage Collector (GC). You do not manually `malloc()` or `free()` memory like you do in C/C++. 

However, a Staff Android Engineer knows that the GC is not magic. It relies on **Reachability**. If an object in memory is no longer needed, but is still "reachable" via a chain of references leading back to a GC Root (like the Main Thread or a Static variable), the Garbage Collector is strictly forbidden from destroying it.

This is a **Memory Leak**. On Android, leaking an `Activity` or a `Fragment` is an architectural disaster that will rapidly exhaust the app's memory budget, causing the OS to violently crash the app with an `OutOfMemoryError` (OOM).

## Why It Matters

Android devices have vastly different RAM capacities. A flagship device has 12GB of RAM. A budget device in an emerging market might have 2GB of RAM. The Android OS places a hard "Heap Limit" on every single application (e.g., your app might only be allowed to use 256MB of RAM total).

If you leak a complex `Activity` (which holds a `Window`, a massive `View` hierarchy, and multiple high-resolution `Bitmaps`), you might lose 40MB of your 256MB budget instantly. If the user opens and closes that Activity 6 times, your app hits the 256MB limit and crashes. 

An app with memory leaks is a ticking time bomb.

## Historical Context

- **Dalvik (Pre-Android 5.0):** The original Android runtime. Its Garbage Collector was famously slow and "Stop-The-World" (it froze the entire app to clean up memory), leading to massive [Jank](jank.md) during fast allocations.
- **ART (Android RunTime):** Introduced to replace Dalvik. ART has a vastly superior Concurrent Garbage Collector. It cleans up memory in the background without freezing the UI. However, ART cannot clean up what it cannot reach.
- **LeakCanary (2015):** Square released an open-source library that revolutionized Android memory debugging. It automatically detects leaked Activities/Fragments and dumps the heap, drawing a trace of exactly what is preventing the GC from deleting the object.

## First Principles

1.  **The Heap:** The pool of RAM where all your objects live.
2.  **GC Roots:** The "anchors" of the app. These are things the OS knows are currently active: The Main Thread, active Coroutines, `static` variables, and JNI (C++) references.
3.  **Reachability:** If the GC can draw a continuous line from a GC Root to an Object, the Object is reachable and cannot be deleted.
4.  **The Memory Leak:** An object that is conceptually useless to the user, but is still technically reachable from a GC Root.

## Mental Model

Think of memory management as a **Rock Climber (The Object) and a Rope (The Reference)**.
- The top of the cliff is the GC Root (The Main Thread).
- The rock climber wants to go home (be Garbage Collected).
- As long as the climber is tied to the rope, the Safety Crew (Garbage Collector) refuses to let them fall/leave.
- A **Memory Leak** is when the climber finishes their climb, takes off their harness, but someone tied the rope around their ankle. They are permanently stuck to the cliff face until the rope is cut.

## Internal Mechanics

### How an Activity Leaks

An `Activity` is massive. It holds a reference to the `Context`, which holds the `Window`, which holds the View hierarchy.

```kotlin
// THE DISASTER: Leaking an Activity via a Background Thread
class ProfileActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // We start a background thread that runs for 10 minutes
        thread {
            Thread.sleep(10 * 60 * 1000) // Simulating a massive download
            
            // This inner lambda holds an IMPLICIT reference to 'this' (ProfileActivity)
            // so it can call updateUi().
            runOnUiThread { updateUi() }
        }
    }
}
```

1. The user opens `ProfileActivity`. The Thread starts.
2. The user presses the Back button. The `ProfileActivity` is destroyed. The user wants their RAM back.
3. The GC runs. It looks at `ProfileActivity`. It wants to delete it.
4. The GC sees the Background Thread is still running (it is a GC Root).
5. The Thread holds a reference to the Lambda.
6. The Lambda holds an implicit reference to `ProfileActivity`.
7. The GC says: *"ProfileActivity is reachable. I cannot delete it."*
8. The Activity, and its 40MB of Bitmaps, are permanently trapped in RAM for the next 10 minutes.

### The Staff Fix (Cancellation)

The solution is [Structured Concurrency](../architecture/structured-concurrency.md). You must cut the rope when the Activity dies.

```kotlin
class ProfileActivity : AppCompatActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        // lifecycleScope is automatically CANCELLED when the Activity dies.
        // It cuts the rope!
        lifecycleScope.launch {
            delay(10 * 60 * 1000) 
            updateUi() 
        }
    }
}
```

## Production Example

**The Static / Companion Object Leak**

A very common pattern in legacy codebases is keeping global caches using `static` variables (or `companion object` in Kotlin). 

```kotlin
// BAD
class UserCache {
    companion object {
        private val listeners = mutableListOf<Listener>()
        
        fun register(listener: Listener) {
            listeners.add(listener)
        }
    }
}

class DashboardFragment : Fragment(), Listener {
    override fun onViewCreated() {
        UserCache.register(this) // The Fragment hands a rope to the Static Root
    }
    // We FORGOT to unregister in onDestroyView!
}
```

A `companion object` lives forever (it is a GC Root). If the Fragment registers itself but forgets to unregister, the `companion object` holds the `Fragment` in memory forever. If the user opens and closes the Fragment 50 times, there will be 50 dead Fragments trapped in the `listeners` list, resulting in an OOM crash.

*(Fix: Always `unregister` in `onDestroyView`, or vastly prefer using [Dependency Injection](../data-and-di/dependency-injection.md) or `WeakReference` instead of static singletons).*

## Tradeoffs

**Strong vs Weak References**

If you absolutely must hold a reference to an object, but you do not want to prevent it from being Garbage Collected, you can use a `WeakReference`.

```kotlin
class Cache {
    // If the GC needs RAM, it is allowed to delete the Context 
    // even if this Cache still holds a WeakReference to it!
    private var contextRef: WeakReference<Context>? = null
}
```

- **Tradeoff:** Weak References are often a "band-aid" for terrible architectural design. A Staff Engineer relies on tight, predictable lifecycles (`viewModelScope`, Jetpack components) rather than littering `WeakReference` throughout the codebase. If you need a `Context` outliving its scope, you should likely be injecting the Application Context via Hilt.

## Failure Modes

- **The Inner Class Trap:**
  In Kotlin, `inner class` (unlike standard nested classes) holds a permanent, hidden reference to the outer class. If you pass an instance of an `inner class` to a Singleton (like a network manager), you instantly leak the outer class.
  *(Fix: Avoid `inner class` unless absolutely necessary).*
- **The Context Cast:**
  Passing an `Activity` context into a repository constructor because the repository needs to access SharedPreferences or a database. The repository outlives the Activity, leaking the Activity.
  *(Fix: When a Singleton or Repository requires a `Context`, always pass `context.applicationContext`).*
- **Unregistered BroadcastReceivers:**
  If an Activity calls `registerReceiver()` but crashes or finishes without calling `unregisterReceiver()`, the Android OS system service holds a hard reference to your receiver, leaking your Activity.

## Staff Engineer Thinking

When attacking an `OutOfMemoryError` spike in production, a Staff engineer focuses on the Heap:

1.  **LeakCanary is Mandatory:** I enforce that `LeakCanary` is installed in the `debug` build variant of all company apps. If QA or a developer triggers a leak during testing, LeakCanary throws a giant notification with the exact stack trace. It catches 95% of leaks before they merge.
2.  **Heap Dumps (.hprof):** When an OOM occurs in production, Crashlytics doesn't tell you *what* leaked, it just tells you that you ran out of memory. I pull an `.hprof` heap dump from a testing device and load it into Android Studio's Memory Profiler (or Eclipse MAT) to analyze the "Dominator Tree." This tells me exactly which object is holding 40% of the RAM.
3.  **Bitmaps:** While leaking an Activity is bad, leaking a `Bitmap` is fatal. Bitmaps are massive, uncompressed pixel grids in memory. If a backend sends a 4000x4000 pixel avatar image, and we load it into memory without down-sampling it via `Glide` or `Coil`, the app will OOM instantly, even without a "leak."

## Common Misconceptions

- **"Kotlin doesn't have memory leaks because it has a Garbage Collector."** The GC only deletes *unreachable* objects. A memory leak in Java/Kotlin is a logic error where you keep a reference to an object you no longer need. The GC works perfectly; your code is at fault.
- **"System.gc() fixes memory leaks."** Calling `System.gc()` is a suggestion to the JVM. It does not force it. More importantly, if an object is reachable (a leak), `System.gc()` will *never* delete it. It only deletes unreachable objects.

## Probing Questions

1.  Explain the concept of "Reachability" and how it determines whether the Android Garbage Collector can destroy an object.
2.  Why is an `Activity` the most dangerous object to leak in the Android ecosystem? What does it hold in memory?
3.  Describe how an active, running background Thread acts as a GC Root and causes memory leaks.
4.  If a Singleton class requires access to `SharedPreferences`, why is it a critical error to pass it an `Activity` context? What should you pass instead?
5.  Explain the architectural flaw of using a Kotlin `companion object` to hold a list of callback listeners registered by Fragments.
6.  How does the `lifecycleScope` in Kotlin Coroutines natively solve the problem of leaking background tasks when an Activity is destroyed?
7.  What is a `WeakReference`, and how does its behavior differ from a standard (Strong) reference during a Garbage Collection cycle?
8.  Why does an `inner class` in Kotlin pose a significantly higher risk of causing a memory leak than a standard nested class?
9.  Describe the tool `LeakCanary`. How does it help teams prevent `OutOfMemoryError` crashes before releasing to production?
10. If an app crashes with an `OutOfMemoryError`, but `LeakCanary` reports zero leaked Activities, what other common memory structure is likely responsible for the crash? (Hint: Think about images).

## Further Reading

- [`jank.md`](jank.md) — How Garbage Collection events (caused by bad memory management) pause the Main Thread and drop frames.
- [`process-death-and-state-restoration.md`](../architecture/process-death-and-state-restoration.md) — How the OS brutally kills apps that consume too much RAM.
- [Android Developers: Memory Management](https://developer.android.com/topic/performance/memory)
