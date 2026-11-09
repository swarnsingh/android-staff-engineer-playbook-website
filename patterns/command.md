# Command Pattern

> The Command pattern encapsulates a request as an object, thereby letting you parameterize clients with different requests, queue or log requests, and support undoable operations. In modern Android, the Command pattern is the architectural bedrock of offline-first applications and background processing. A Staff engineer recognizes that **WorkManager** is simply a durable, SQLite-backed Command Bus. By encapsulating network calls or database writes as Commands, you can retain execution intent across ordinary process death, subject to scheduler constraints, payload access, cancellation and application lifetime. Persistence does not guarantee eventual success.

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
**Staff Insight:** If this state needs to survive process death (e.g., the user leaves the photo editor and returns), persist serializable command data/deltas, not objects holding Views. Use saved state only for small reconstructible UI state; use durable storage for user work, and reconstruct executors with current owners/dependencies.

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
// Fragment: WorkerFactory injects the API and durable operation store.
class UploadImageWorker(
    appContext: Context,
    workerParams: WorkerParameters,
    private val api: ImageUploadApi,
    private val uploads: UploadOperations,
) : CoroutineWorker(appContext, workerParams) {
    override suspend fun doWork(): Result {
        val id = inputData.getString("UPLOAD_ID") ?: return Result.failure()
        val operation = uploads.load(id) ?: return Result.failure()
        operation.terminalResult?.let { return it }
        suspend fun fail(reason: String): Result {
            uploads.markFailed(id, reason)
            return Result.failure()
        }
        val fileId = inputData.getString("FILE_ID") ?: return fail("Missing image")
        if (fileId != operation.fileId) return fail("Missing or mismatched image")
        if (runAttemptCount >= 4) return fail("Retry budget exhausted")
        if (!uploads.retryIsDue(id)) return Result.retry()
        val response = try {
            api.uploadImage(fileId, operation.idempotencyKey)
        } catch (cancelled: CancellationException) {
            throw cancelled
        } catch (failure: HttpException) {
            if (!retryableUploadStatus(failure.code())) return fail("HTTP ${failure.code()}")
            uploads.deferRetry(id, failure.response()?.headers()?.get("Retry-After"))
            return Result.retry()
        } catch (failure: IOException) {
            return Result.retry()
        }
        uploads.markSucceeded(id, response.url)
        return Result.success(workDataOf("SERVER_URL" to response.url))
    }
}
```

This uses the endpoint-specific `retryableUploadStatus` policy and durable `UploadOperations` contract in [Retry](retry.md#2-durable-retries-the-command-layer-workmanager): terminal failures are saved, cancellation is rethrown, and a persisted `Retry-After` gate prevents early requests. These are app-owned interfaces; they must be implemented and injected, not mistaken for SDK methods.

### Issuing the Command

```kotlin
class ProfileViewModel(
    private val workManager: WorkManager,
    private val images: PrivateImageStore,
    private val uploads: UploadOperations,
) : ViewModel() {
    // Called by a UI-owned coroutine; the caller renders copy/save/enqueue failures.
    // selectionId belongs to the saved draft and is reused on repeated taps/re-entry.
    suspend fun onProfilePictureSelected(selectionId: String, uri: Uri): String {
        val fileId = images.copyOnceToPrivateStorage(selectionId, uri)
        val operation = uploads.getOrCreate(selectionId, fileId)
        if (operation.terminalResult != null) return operation.id
        val uploadCommand = OneTimeWorkRequestBuilder<UploadImageWorker>()
            .setInputData(workDataOf("UPLOAD_ID" to operation.id, "FILE_ID" to operation.fileId))
            .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
            .setBackoffCriteria(BackoffPolicy.EXPONENTIAL, 10, TimeUnit.SECONDS)
            .build()
        workManager.enqueueUniqueWork("upload:${operation.id}", ExistingWorkPolicy.KEEP, uploadCommand)
            .await()
        return operation.id
    }
}
```

`PrivateImageStore.copyOnceToPrivateStorage` is an app-owned, main-safe copy operation: copy the selected URI while its grant is valid into non-cache app storage, publish the file atomically, and reuse that file for the same selection ID. `getOrCreate` atomically inserts an account-scoped operation with a stable key, or returns the existing row for that saved selection. Both commits precede enqueue. Keep the file until the operation is resolved; handle copy failures/orphan cleanup explicitly. This fragment requires those implementations, not just `uri.toString()`.

`KEEP` prevents concurrent unfinished work with the same name; it is not remote deduplication and does not block reenqueuing after completion. The saved terminal result and server key cover those cases. A recovery scan schedules committed pending rows if the process dies after saving but before enqueue; after an unknown remote outcome, reconcile or retry only within the server's deduplication contract. WorkManager can resume eligible work after ordinary process death, but force-stop, uninstall, changed permissions and scheduling restrictions can prevent execution.

---

## 3. The Offline-First Action Queue

For many fine-grained actions, use one durable outbox and coalesce drain scheduling. An in-memory channel may wake a consumer, but must not be the only source of pending work.

```kotlin
// Fragment: app-owned interfaces, with explicit durable contracts below.
sealed interface OfflineAction {
    data class LikePost(val postId: String) : OfflineAction
    data class SubmitComment(val postId: String, val text: String) : OfflineAction
}

class ActionQueue(
    private val api: SessionBoundActionApi,
    private val store: ActionStore,
    private val scheduler: ActionDrainScheduler,
) {
    suspend fun enqueue(action: OfflineAction) {
        // One DB transaction: apply pending UI state + insert serialized action/key.
        store.recordPending(api.accountId, UUID.randomUUID().toString(), action)
        scheduler.enqueueDrain(api.accountId)
    }

    // A lifecycle-owned coroutine or CoroutineWorker invokes this suspending API.
    suspend fun drainOne(): Boolean {
        val pending = store.claimNext(api.accountId) ?: return false
        api.execute(pending.action, pending.idempotencyKey)
        store.acknowledgeAndReconcile(pending.id)
        return true
    }
}
```

`recordPending` returns only after local state and intent commit atomically. `claimNext` is account-scoped, ordered where required, and uses a recoverable lease so process death cannot strand in-flight rows. The captured API/session must not silently switch to another account. A restart/reconciliation path scans persisted pending/expired-lease rows and enqueues drains, covering a crash after commit but before scheduling.

The worker owns bounded retry/backoff and classifies transient failure, permanent rejection and cancellation. Failed/cancelled calls retain recoverable intent; a permanent rejection updates that operation's status and reconciles its optimistic effect without undoing newer edits. A stable key works only with server-side deduplication. This fragment specifies the storage/scheduling contracts; it is not a complete Room/Worker implementation. There is no construction-time hidden launch or unbounded in-memory command buffer.

## 4. Failure Modes & Tradeoffs

| Failure Mode | Cause | Prevention / Solution |
|---|---|---|
| **Command Bloat** | Storing massive payloads (e.g., entire Bitmaps or 10MB JSON strings) directly inside the Command object (or WorkManager `Data`). | Commands should only store **references** (URIs, Database IDs). The Command executor fetches the heavy data when it runs. |
| **Out of Order Execution** | The user goes offline, renames a folder to "A", then renames it to "B". The Commands execute out of order when connectivity returns, resulting in "A". | Persist aggregate/sequence identity and serialize required operations. WorkManager chains impose prerequisite-success order; a Channel preserves its queued receive order, not global business order across concurrent producers, retries or process death. |
| **Process Death Memory Loss** | Implementing an Undo/Redo stack purely in memory. If the app is backgrounded and killed by the OS, the user loses their work. | Use small saved-state reconstruction hints or persist command data to disk according to the required durability. Ensure Commands don't hold references to non-serializable objects (like `View` or `Activity`). |
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
*Fix:* Commands should manipulate data or emit state. The UI observes the state. A delayed/durable command should not retain a View or Activity. A short-lived UI-only undo command can reference its view only while scoped to that view; persist model-level deltas for recovery.

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

1. **WorkManager Internals:** The maximum serialized size is 10,240 bytes (defined by `Data.MAX_DATA_BYTES`), including serialization overhead. If exceeded, WorkManager throws an `IllegalStateException`.
2. **Idempotency:** The backend must recognize duplicate commands via a unique idempotency key (like a UUID sent in the command) and return the cached success response rather than processing the action twice.
3. **Command Chaining:** Worker B and Worker C are marked as FAILED and do not run. WorkManager stops the chain on the first failure.
4. **Undo/Redo State:** The Command should only store the delta (the specific pixels changed) or a reference to a snapshot, rather than full copies of the image, minimizing memory overhead.
5. **Optimistic UI:** The Command issues a rollback action to the local ActionQueue or database, which removes the optimistic state, triggering a Flow emission that updates the UI to its previous state.

## Further Reading

- [`../android/concurrency/workmanager.md`](../android/concurrency/workmanager.md) — Deep dive into Android's persistent Command Bus.
- [`../distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — Why Commands must be idempotent when retried over mobile networks.
- [`../reference-architectures/offline-first-app.md`](../reference-architectures/offline-first-app.md) — Architecting the full data layer around offline command queues.
- [`saga.md`](saga.md) — Chaining multiple commands together across microservices.
- [WorkManager persistence and scheduling scope](https://developer.android.com/develop/background-work/background-tasks/persistent)
- [WorkManager Data serialized-size limit](https://developer.android.com/reference/androidx/work/Data#MAX_DATA_BYTES)
- [WorkManager prerequisite and failure semantics](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/chain-work)
- [Saved state versus durable storage](https://developer.android.com/topic/libraries/architecture/saving-states)
- [Android offline-first durable write queues](https://developer.android.com/topic/architecture/data-layer/offline-first)
- [Coroutine cancellation](https://kotlinlang.org/docs/cancellation-and-timeouts.html)
- [Unique work and KEEP conflict policy](https://developer.android.com/develop/background-work/background-tasks/persistent/how-to/manage-work)
- [App-specific file ownership and retention](https://developer.android.com/training/data-storage/app-specific)
- [WorkManager Operation.await suspension](https://raw.githubusercontent.com/androidx/androidx/androidx-main/work/work-runtime/src/main/java/androidx/work/Operation.kt)
