# Command Pattern

> The Command pattern encapsulates a request as an object, thereby letting you parameterize clients with different requests, queue or log requests, and support undoable operations. In modern Android, the Command pattern is the architectural bedrock of offline-first applications and background processing. A Staff engineer recognizes that **WorkManager** is simply a durable, SQLite-backed Command Bus. By encapsulating network calls or database writes as Commands, you can ensure execution across process death, poor network conditions, and complex state changes.

---

## Overview

In traditional object-oriented programming, if the UI wants to save a user's profile, it calls `repository.saveProfile(user)`. This executes immediately. 

If you use the Command pattern, the UI creates a `SaveProfileCommand(user)` object and hands it to an Invoker (a queue or bus). The Invoker decides *when* and *how* to execute it.

This separation of "what to do" from "when to do it" is critical on mobile devices where network connectivity is intermittent and the OS aggressively kills background processes.

---

## 1. The Classic Implementation: Undo/Redo in Android

The most traditional use case for the Command pattern is an Undo/Redo stack, commonly used in photo editors or note-taking apps.

```kotlin
// 1. The Command Interface
interface Command {
    fun execute()
    fun undo()
}

// 2. A Concrete Command
class DrawStrokeCommand(
    private val canvasView: CanvasView,
    private val stroke: Stroke
) : Command {
    
    override fun execute() {
        canvasView.addStroke(stroke)
    }

    override fun undo() {
        canvasView.removeStroke(stroke)
    }
}

// 3. The Invoker (The Command Manager)
class CommandManager {
    private val history = Stack<Command>()
    private val redoStack = Stack<Command>()

    fun executeCommand(command: Command) {
        command.execute()
        history.push(command)
        redoStack.clear() // New actions invalidate the redo history
    }

    fun undo() {
        if (history.isNotEmpty()) {
            val command = history.pop()
            command.undo()
            redoStack.push(command)
        }
    }

    fun redo() {
        if (redoStack.isNotEmpty()) {
            val command = redoStack.pop()
            command.execute()
            history.push(command)
        }
    }
}
```
**Staff Insight:** If this state needs to survive process death (e.g., the user leaves the photo editor and returns), the `Command` objects must be serializable (e.g., to JSON) and saved in `SavedStateHandle` or Room.

---

## 2. Core Android Example: WorkManager as a Command Bus

Android's **WorkManager** is the ultimate, OS-integrated Command pattern. 
- The `Worker` is the Command implementation.
- The `Data` input is the Command payload.
- The `WorkManager` enqueue system is the Invoker.
- Room (inside WorkManager) is the durable Command Queue.

### Encapsulating a Request
Instead of making an API call directly, we encapsulate the intent to upload an image into a `Worker`.

```kotlin
// The Command Implementation
class UploadImageWorker(
    appContext: Context,
    workerParams: WorkerParameters
) : CoroutineWorker(appContext, workerParams) {

    override suspend fun doWork(): Result {
        // The Payload
        val imageUri = inputData.getString("IMAGE_URI") ?: return Result.failure()
        
        return try {
            val response = api.uploadImage(imageUri)
            Result.success(workDataOf("SERVER_URL" to response.url))
        } catch (e: IOException) {
            // Network failure? WorkManager will automatically retry this Command later!
            Result.retry()
        } catch (e: Exception) {
            Result.failure()
        }
    }
}
```

### Issuing the Command
The UI layer simply creates the Command (the `WorkRequest`) and hands it to the Invoker (`WorkManager`).

```kotlin
class ProfileViewModel(private val workManager: WorkManager) : ViewModel() {
    
    fun onProfilePictureSelected(uri: Uri) {
        // 1. Parameterize the request
        val inputData = workDataOf("IMAGE_URI" to uri.toString())
        
        // 2. Create the Command object
        val uploadCommand = OneTimeWorkRequestBuilder<UploadImageWorker>()
            .setInputData(inputData)
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .build()
            
        // 3. Queue the request
        workManager.enqueue(uploadCommand)
    }
}
```
Because this Command is written to SQLite by WorkManager, even if the user immediately swipes the app away and kills the process, the image will upload the next time the OS detects network connectivity.

---

## 3. The Offline-First Action Queue

For highly interactive apps (like Twitter or Slack), you cannot use WorkManager for every single "Like" or "Upvote" button press—it is too heavy and has a minimum latency overhead.

Instead, Staff engineers build an in-memory or Room-backed **Action Queue** using Coroutines and Channels. This is a custom Command Invoker.

```kotlin
// The Command Definition
sealed interface OfflineAction {
    data class LikePost(val postId: String) : OfflineAction
    data class SubmitComment(val postId: String, val text: String) : OfflineAction
}

// The Invoker (Application Scoped)
@Singleton
class ActionQueue @Inject constructor(
    private val api: SocialApi,
    private val database: ActionDatabase,
    @ApplicationScope private val scope: CoroutineScope
) {
    // A channel to buffer commands
    private val commandChannel = Channel<OfflineAction>(Channel.UNLIMITED)

    init {
        // The worker loop
        scope.launch {
            for (action in commandChannel) {
                processAction(action)
            }
        }
    }

    // UI calls this. It returns instantly.
    fun enqueue(action: OfflineAction) {
        scope.launch {
            database.saveAction(action) // Persist to disk for crash resilience
            commandChannel.send(action) // Push to in-memory queue
        }
    }

    private suspend fun processAction(action: OfflineAction) {
        try {
            when (action) {
                is OfflineAction.LikePost -> api.likePost(action.postId)
                is OfflineAction.SubmitComment -> api.submitComment(action.postId, action.text)
            }
            database.deleteAction(action) // Remove from disk on success
        } catch (e: IOException) {
            // Network is down. Push it back to the channel after a delay
            delay(5000)
            commandChannel.send(action)
        }
    }
}
```
This pattern allows the UI to update optimistically ("Like" turns red immediately) while the background Command Queue ensures eventual consistency with the server.

---

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **Command Bloat** | Storing massive payloads (e.g., entire Bitmaps or 10MB JSON strings) directly inside the Command object (or WorkManager `Data`). | Commands should only store **references** (URIs, Database IDs). The Command executor fetches the heavy data when it runs. |
| **Out of Order Execution** | The user goes offline, renames a folder to "A", then renames it to "B". The Commands execute out of order when connectivity returns, resulting in "A". | Use sequential queues (Channels) or WorkManager Chaining (`beginWith().then()`) to enforce strict FIFO execution of related commands. |
| **Process Death Memory Loss** | Implementing an Undo/Redo stack purely in memory. If the app is backgrounded and killed by the OS, the user loses their work. | Serialize the Command stack to `SavedStateHandle` or disk. Ensure Commands don't hold references to non-serializable objects (like `View` or `Activity`). |
| **Zombie Commands** | A Command to delete a post is queued offline. Before it executes, the user deletes their account. The Command executes later, crashing on the backend. | Commands must validate system state *at execution time*, not at creation time. |

---

## 5. Common Pitfalls

### Pitfall 1: Leaking UI References in Commands
```kotlin
// BAD
class ShowSnackbarCommand(private val view: View, private val message: String) : Command {
    override fun execute() { Snackbar.make(view, message, Snackbar.LENGTH_SHORT).show() }
}
```
If this Command is put in a delayed queue, it holds a strong reference to `View`. If the Activity rotates, the `View` leaks.
*Fix:* Commands should manipulate data or emit state. The UI observes the state. Commands should never hold Android UI toolkit references.

### Pitfall 2: Bypassing the Single Source of Truth
If a `SubmitCommentCommand` updates the network, and then the Command itself updates the UI via a callback, you fracture your state.
*Fix:* The Command should only update the remote server and the local database (Room). The UI should observe the Room database (via `Flow`). The Command has no UI callbacks.

---

## Probing Questions

1.  **WorkManager Internals:** WorkManager serializes your `Data` object into a SQLite database. What is the maximum size (in bytes) of a `Data` payload in WorkManager, and what exception is thrown if you exceed it? 
2.  **Idempotency:** If the network drops *after* the server processes a `LikePostCommand` but *before* the Android device receives the HTTP 200 OK, WorkManager will retry the Command. How must the backend API be designed to handle this duplicate command safely?
3.  **Command Chaining:** In WorkManager, you can chain commands: `A -> B -> C`. If Worker A fails and returns `Result.failure()`, what is the state of Worker B and Worker C? Do they run?
4.  **Undo/Redo State:** In a complex app like a photo editor, storing a new `Command` object for every single pixel change will exhaust device memory. How do you combine the Command pattern with the Memento pattern to manage memory in a deep undo stack?
5.  **Optimistic UI:** When you use an Offline Action Queue, you update the UI immediately (Optimistic Update). If the `Command` permanently fails (e.g., HTTP 403 Forbidden), how does the Command notify the UI to roll back the optimistic state?

## Answer Key

1. **WorkManager Internals:** The maximum size is 10KB (defined by `Data.MAX_DATA_BYTES`). If exceeded, WorkManager throws an `IllegalStateException`.
2. **Idempotency:** The backend must recognize duplicate commands via a unique idempotency key (like a UUID sent in the command) and return the cached success response rather than processing the action twice.
3. **Command Chaining:** Worker B and Worker C are marked as FAILED and do not run. WorkManager stops the chain on the first failure.
4. **Undo/Redo State:** The Command should only store the delta (the specific pixels changed) or a reference to a snapshot, rather than full copies of the image, minimizing memory overhead.
5. **Optimistic UI:** The Command issues a rollback action to the local ActionQueue or database, which removes the optimistic state, triggering a Flow emission that updates the UI to its previous state.

## Further Reading

- [`../android/concurrency/workmanager.md`](../android/concurrency/workmanager.md) — Deep dive into Android's persistent Command Bus.
- [`../distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — Why Commands must be idempotent when retried over mobile networks.
- [`../reference-architectures/offline-first-app.md`](../reference-architectures/offline-first-app.md) — Architecting the full data layer around offline command queues.
- [`saga.md`](saga.md) — Chaining multiple commands together across microservices.
