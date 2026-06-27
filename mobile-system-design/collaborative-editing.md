# System Design: Collaborative Editing (Google Docs / Figma)

## The Prompt

*"Design the collaborative editing engine for a mobile app like Google Docs or Figma. Two users, Alice and Bob, are editing the exact same paragraph simultaneously on their phones. Alice deletes a word while Bob inserts a word. Both are occasionally losing cell service. The system must merge their edits perfectly without locking the document or showing error dialogs."*

## 1. Requirements & Clarification (RADIO Framework)

### Functional Requirements
- Real-time text/canvas editing.
- Multiple cursors visible to all users.
- Offline support (users can type while in a tunnel, edits sync when reconnected).

### Non-Functional Requirements (NFRs)
- **Data Integrity (Priority 0):** Absolute Convergence. When the network dust settles, Alice's phone, Bob's phone, and the Backend must all reflect the *exact same document state*.
- **Latency:** Typing must reflect locally in 0ms (no waiting for the server). Edits should reflect on other clients in < 50ms.
- **Locking:** Zero pessimistic locks. You cannot "lock" a paragraph while Alice types, because Bob needs to type simultaneously.

## 2. High-Level Architecture (The Synchronization Math)

The Junior answer is: "Alice sends the whole document to the server. The server saves it." This fails instantly because Bob's simultaneous save will overwrite Alice's completely.

A Staff engineer knows there are only two mathematical ways to solve this: **Operational Transformation (OT)** or **Conflict-Free Replicated Data Types (CRDTs)**.

```mermaid
graph TD
    Alice[Alice Android App] <-->|WebSocket| SyncServer[Sync Gateway]
    Bob[Bob Android App] <-->|WebSocket| SyncServer
    
    subgraph CRDT Engine (Local)
        AliceUI[UI] -->|Type 'X'| AliceLocal[Local CRDT Graph]
        AliceLocal -->|Emit Math Delta| Alice
    end
    
    subgraph CRDT Engine (Local)
        BobUI[UI] -->|Type 'Y'| BobLocal[Local CRDT Graph]
        BobLocal -->|Emit Math Delta| Bob
    end
    
    SyncServer -->|Broadcast Deltas| RedisPubSub[Redis Pub/Sub]
    SyncServer -->|Persist Document| Cassandra[(Document DB)]
```

## 3. Operational Transformation (OT) vs CRDTs

### The OT Approach (The Google Docs Way)
OT sends operations: `Insert 'A' at Index 5`. 
If Alice inserts at Index 5, and Bob deletes Index 3 simultaneously, Alice's operation is now mathematically wrong (she needs to insert at Index 4, because everything shifted left).
The Central Server must catch both operations, transform the math, and send the corrected operations back to the clients.
**Pros:** Smaller payloads. 
**Cons:** Requires a heavy, centralized server. Incredibly difficult to build.

### The CRDT Approach (The Modern/Figma Way)
CRDTs assign a globally unique, mathematically sortable ID to *every single character* (or pixel).
Instead of saying `Insert 'A' at Index 5`, Alice's app says: `Insert 'A' between ID-4 and ID-6`. 
Because the IDs are immutable and relative to each other, it doesn't matter what Bob does. If Bob deletes `ID-3`, Alice's instruction is still perfectly valid. The math merges seamlessly without a central server needing to transform anything.
**Pros:** Peer-to-peer capability, perfect offline support, math always converges.
**Cons:** Massive memory footprint (storing a UUID for every single character is heavy).

*Staff Decision:* For modern mobile systems, we will use **CRDTs** (e.g., using a library like Yjs or Automerge). It offloads the transformation logic to the client, simplifying the backend to a dumb message broker.

## 4. The Core Flows (Deep Dive)

### Flow 1: Handling Offline (The DAG)
*Interviewer:* "Alice enters a subway tunnel for 10 minutes. She types 5 paragraphs. Bob deletes the paragraph she is editing. Alice exits the tunnel and connects to the WebSocket. What happens?"

**Staff Answer:**
"With a CRDT, the document is mathematically represented as a **Directed Acyclic Graph (DAG)** of operations.
1. While offline, Alice's Android app records her 5 paragraphs as a chain of local operations in Room/SQLite.
2. When she reconnects, her app sends the entire chain of operations to the server.
3. The server forwards it to Bob.
4. Bob's local CRDT engine receives Alice's insertions. Because Bob *deleted* the parent node of Alice's text, the CRDT engine mathematically determines that Alice's new text is attached to a deleted node.
5. The engine (depending on the exact algorithm) either drops Alice's text or resurrects the paragraph. The critical part is that Alice's phone and Bob's phone run the exact same deterministic math, guaranteeing they both converge on the identical final state without throwing merge errors."

### Flow 2: The Memory Problem (Tombstones)
*Interviewer:* "Bob types 1,000 words. He deletes 1,000 words. He types 1,000 words. He does this for a year. The document is only 1,000 words long, but the app uses 1GB of RAM and crashes. Why?"

**Staff Answer:**
"This is the fundamental flaw of CRDTs: **Tombstones**.
When you delete a character in a CRDT, you cannot actually remove it from memory. You must mark it as deleted (a Tombstone), because Alice's offline phone might reconnect in a month and try to insert a letter next to the character Bob deleted today. If the character doesn't exist, the math breaks.
**The Fix:** We must implement **Garbage Collection (Compaction)**. The central server must periodically establish a 'Snapshot' epoch. Once the server confirms that *all* active clients have received the updates up to Epoch 100, the server compresses the DAG, deletes the tombstones, and ships a fresh baseline state to the clients, freeing the RAM."

### Flow 3: Real-Time Cursors (Ephemeral State)
*Interviewer:* "You want to show Bob's cursor moving across Alice's screen. If you send a CRDT operation for every pixel the cursor moves, you will overwhelm the database and the network."

**Staff Answer:**
"Cursor movements are **Ephemeral State**. They do not belong in the CRDT or the Document Database.
1. When Bob touches the screen, his app sends a lightweight UDP or WebSocket message: `{"type": "cursor", "user": "Bob", "index": 45}`.
2. The Sync Server receives this and immediately broadcasts it to all other active WebSockets viewing the document.
3. It is *never* written to disk. If the packet drops, it doesn't matter, the next movement will overwrite it. This keeps the document database purely focused on persistent text changes."

## 5. Failure Modes & Bottlenecks

### Bottleneck: Large Document Loading
A junior developer pulls down the entire CRDT operation history (100,000 operations) over the network when the user opens the app. The phone takes 15 seconds to calculate the final text.
*(Fix: The backend must provide a calculated **Snapshot**. The Android app downloads the final string + the current active CRDT tree, rather than replaying 5 years of history).*

### Bottleneck: The WebSocket Reconnection Storm
If Google Docs has 1 million active users and the central server cluster restarts, 1 million Android apps will attempt to reconnect simultaneously.
*(Fix: Exponential Backoff with Jitter must be hardcoded into the Android WebSocket client to smear the reconnections across a 60-second window).*

## 6. Staff Engineer Thinking: CRDT vs OT

In a real interview, you must acknowledge the trade-off you are making.
- "I am choosing CRDTs because they are inherently decentralized and handle long-offline periods beautifully. However, I acknowledge that text-editing CRDTs have a memory overhead of roughly 100x the size of the raw text. For a 10KB text document, the CRDT will consume 1MB of RAM. On modern Android devices, this is perfectly acceptable, but I must implement aggressive Garbage Collection epochs to prevent long-lived documents from growing unbounded."

## 7. Probing Questions (For Practice)

1.  Explain why "Last-Write-Wins" (LWW) is a catastrophic failure for a collaborative text editing application.
2.  Describe the fundamental difference between Operational Transformation (OT) and Conflict-Free Replicated Data Types (CRDTs).
3.  How does assigning a globally unique, mathematically sortable ID to every character solve the synchronization problem without a central transformation server?
4.  Walk through the "Tombstone" problem in CRDTs. Why can you never truly delete a character from the graph until a Garbage Collection epoch occurs?
5.  Explain why Cursor movements and "User is typing..." indicators must be treated as Ephemeral State and kept out of the main document database.
6.  Describe the "Snapshot" optimization. Why must a mobile app avoid downloading the entire history of CRDT operations when opening a document?
7.  If a user goes completely offline for a week, makes thousands of edits to a document, and then reconnects, explain why a CRDT guarantees convergence when they sync with the server.
8.  Why is a persistent connection (WebSocket) mandatory for collaborative editing, and why would standard HTTP Polling destroy the user experience?
9.  Explain the concept of Exponential Backoff with Jitter in the context of a mass WebSocket disconnection event.
10. Justify the memory overhead tradeoff when choosing a CRDT over Operational Transformation for a mobile application.

## Further Reading

- [`crdts.md`](../distributed-systems/crdts.md) — The deep mathematical computer science behind CRDTs.
- [`offline-sync.md`](offline-sync.md) — How basic offline sync works (and why CRDTs are required for text).
- [`chat-messaging.md`](chat-messaging.md) — Deep dive into persistent WebSocket architectures.
