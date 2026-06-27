# Command Pattern

## Overview

The Command pattern turns a request into a stand-alone object that contains all information about the request. This transformation lets you pass requests as method arguments, delay or queue a request's execution, and support undoable operations. In modern Android, it is the foundational pattern for implementing offline queues, undo stacks, and reliable background processing.

## Why It Exists

Normally, if the UI wants to save a document, it calls `document.save()`. The request is executed immediately. But what if the user is offline? What if you want to support "Undo"? What if you want to schedule the save for 3:00 AM? 

You cannot queue or delay a raw method invocation. By turning the invocation into a data object (`SaveDocumentCommand`), you separate the *intent* to do work from the *execution* of the work.

## Historical Context

One of the original GoF behavioral patterns. Historically implemented using strict class hierarchies (e.g., `Command` interface, `ConcreteCommand` classes, an `Invoker`, and a `Receiver`). In modern Kotlin, functional programming features (like higher-order functions and lambdas) can replace simple commands, but robust, serializable commands for offline architectures still heavily rely on data classes and the classic pattern structure.

## First Principles

1.  **Reification of Intent:** Make a verb (an action) into a noun (an object).
2.  **Decoupling Invoker and Receiver:** The UI (Invoker) creates the command. It does not know how the Receiver (e.g., the Database) will execute it.
3.  **Serializability:** If a command is an object, it can be serialized to disk. This is the cornerstone of offline-first design.

## Mental Model

Think of ordering food at a restaurant. You don't walk into the kitchen and cook the steak yourself (direct execution). You don't even talk to the chef. You tell the waiter what you want. The waiter writes your order on a piece of paper (The Command Object). This piece of paper is placed on a spindle (The Queue). The chef (The Receiver) takes the paper when they are ready and cooks the meal. The paper decouples you from the kitchen, allows orders to be queued, and provides a record of what was requested.

## Internal Mechanics

### 1. The Classic Offline-Queue Command

This is how modern offline-first apps operate. The Command is a data structure.

```kotlin
// 1. The Command (Reified Intent)
// Must be serializable so it can survive process death
@Serializable
sealed class SyncCommand {
    data class LikePost(val postId: String, val timestamp: Long) : SyncCommand()
    data class UpdateProfile(val newName: String) : SyncCommand()
}

// 2. The Invoker (UI / Repository)
class PostRepository(private val db: Database) {
    fun likePost(postId: String) {
        val command = SyncCommand.LikePost(postId, System.currentTimeMillis())
        // We don't execute it. We queue it.
        db.commandQueueDao().insert(command)
        
        // Optimistically update UI
        db.postDao().incrementLikes(postId) 
    }
}

// 3. The Receiver / Executor (Background Sync Engine)
class SyncEngine(
    private val api: RemoteApi,
    private val queueDao: CommandQueueDao
) {
    suspend fun executePendingCommands() {
        val commands = queueDao.getPending()
        commands.forEach { command ->
            when (command) {
                is SyncCommand.LikePost -> api.sendLike(command.postId)
                is SyncCommand.UpdateProfile -> api.updateName(command.newName)
            }
            queueDao.markComplete(command)
        }
    }
}
```

### 2. The Undoable Command (Editor pattern)

If a command knows how to execute itself, it can also know how to *un-execute* itself.

```kotlin
interface Command {
    fun execute()
    fun undo()
}

class ChangeTextCommand(
    private val editor: TextEditor,
    private val newText: String
) : Command {
    private var previousText: String = ""

    override fun execute() {
        previousText = editor.getText() // Save state before changing
        editor.setText(newText)
    }

    override fun undo() {
        editor.setText(previousText) // Restore state
    }
}

class CommandManager {
    private val history = Stack<Command>()

    fun execute(command: Command) {
        command.execute()
        history.push(command)
    }

    fun undo() {
        if (history.isNotEmpty()) {
            history.pop().undo()
        }
    }
}
```

## Architecture

```mermaid
flowchart LR
    Client[Client / UI] -->|creates| Command[Command Object]
    Client -->|passes to| Invoker[Invoker / Queue]
    Invoker -->|calls execute() on| Command
    Command -->|modifies state of| Receiver[Receiver / Database]
    
    classDef core fill:#d4edda,stroke:#28a745,stroke-width:2px;
    classDef cmd fill:#fff3cd,stroke:#ffc107,stroke-width:2px;
    
    class Client,Receiver core;
    class Command,Invoker cmd;
```

## Production Example

**WorkManager** is Android's ultimate implementation of the Command pattern.

When you create a `OneTimeWorkRequest`, you are creating a Command object. You don't execute the work. You hand the request to `WorkManager.enqueue()`. WorkManager writes the command to a local SQLite database (so it survives device reboots). Later, when battery and network conditions are met, WorkManager (the Invoker) instantiates your `Worker` class (the Receiver) and tells it to `doWork()`.

```kotlin
// The Command Definition
val uploadWorkRequest = OneTimeWorkRequestBuilder<UploadWorker>()
    // Constraints are meta-data attached to the Command
    .setConstraints(Constraints.Builder().setRequiredNetworkType(NetworkType.CONNECTED).build())
    // Input data is the payload of the Command
    .setInputData(workDataOf("IMAGE_URI" to "file://image.jpg"))
    .build()

// The Invoker queuing the command
WorkManager.getInstance(context).enqueue(uploadWorkRequest)
```

## Tradeoffs

**Advantages**
- **Offline Reliability:** By queuing serializable commands, apps work seamlessly offline and sync when reconnected.
- **Undo/Redo:** Trivial to implement if commands track their previous state.
- **Decoupling:** The UI doesn't need to know the heavy dependencies required to actually execute the network request.

**Disadvantages**
- **Over-engineering:** Using the Command pattern for simple, synchronous UI actions (like navigating to a new screen) adds massive, useless boilerplate.
- **State Stale-ness:** If a command sits in an offline queue for 3 days, executing it later might overwrite newer data on the server. (Requires Idempotency and Conflict Resolution strategies).
- **Asynchronous Complexity:** Because execution is deferred, the UI cannot simply `catch` an exception if the command fails. Error handling becomes an asynchronous architectural problem.

## Failure Modes

- **Un-serializable Commands:** If a Command holds a reference to a `Context`, a `View`, or a large Bitmap, it cannot be safely serialized to disk or passed across process boundaries. Commands should hold primitive IDs (like `userId` or `filePath`), not the objects themselves.
- **The Fat Command:** A command that contains 500 lines of complex business logic. The Command should just be a data transport layer or a thin orchestrator. The actual business logic belongs in the Receiver (the Domain or Data layer).
- **Ignoring Idempotency:** If the network drops while the app is executing a command, the app won't know if the server received it. The Invoker will retry the command. If the server isn't idempotent, you'll end up with duplicate purchases or likes. See [`distributed-systems/idempotency.md`](../distributed-systems/idempotency.md).

## Staff Engineer Thinking

When reviewing architectures relying on queues and commands, a Staff engineer asks:

1.  **What happens when the queue gets stuck?** If a `SyncProfileCommand` consistently crashes the background worker due to a bad payload, does it block the entire queue? There must be a mechanism to quarantine "poison pill" commands.
2.  **Is the order guaranteed?** If I queue `UpdateName("John")` then `UpdateName("Johnny")`, does the executor guarantee they hit the server in that exact order?
3.  **How is the user notified of failure?** If I "like" a post offline, the UI shows a red heart. Three hours later, the command fails permanently because the post was deleted. How does the UI reconcile this?

## Common Misconceptions

- **"Lambdas replaced the Command pattern."** Partially. For simple UI callbacks (`button.onClick = { doSomething() }`), lambdas are perfect. However, you cannot easily serialize a lambda to a SQLite database, nor can you easily inspect a lambda's internal properties. For offline queues, the explicit Command Object pattern is still mandatory.
- **"Commands are just Events."** The difference is intent. An **Event** says "Something happened" (`UserLoggedInEvent`). A **Command** says "Do this thing" (`SyncUserDataCommand`).

## Probing Questions

1.  How does the Command pattern enable offline-first application architectures?
2.  What is the "Poison Pill" problem in command queues, and how do you handle it?
3.  Why is it critical that offline commands use primitive data types (like String IDs) rather than object references?
4.  Explain how Android's `WorkManager` implements the Command pattern.
5.  How would you design a text editor with infinite Undo/Redo capabilities using the Command pattern?
6.  If a user queues an `UpdateEmailCommand`, and immediately queues a `DeleteAccountCommand`, how should the executor handle this?
7.  What is the relationship between the Command pattern and Idempotency?
8.  How does the Command pattern relate to the concept of Unidirectional Data Flow (MVI/Redux)? (Hint: Actions/Intents are often Commands).
9.  If execution is deferred, how do you handle validation? Should the command be validated when it's created, or when it's executed?
10. Describe a scenario where using the Command pattern would be considered an anti-pattern.

## Further Reading

- [`../reference-architectures/offline-first-app.md`](../reference-architectures/offline-first-app.md) — The ultimate application of the Command pattern (the Outbox queue).
- [`../distributed-systems/idempotency.md`](../distributed-systems/idempotency.md) — Mandatory reading if you are sending commands across a network boundary.
- Refactoring Guru: [Command Pattern](https://refactoring.guru/design-patterns/command)
