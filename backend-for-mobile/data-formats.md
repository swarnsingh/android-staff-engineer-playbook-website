# Data Formats (JSON, Protobuf, FlatBuffers)

## Overview

A Junior Engineer assumes that `JSON` is the only way applications communicate over the internet, and that `Gson` or `Moshi` are just magic black boxes that turn text into Kotlin objects.

A Staff Engineer understands that translating data from a network transport format into physical RAM (Heap Allocation) is one of the most CPU-intensive and Garbage Collection (GC) heavy operations a mobile device performs. If you are rendering a high-speed 60fps graph, waiting 300ms for a massive JSON string to parse will destroy the user experience.

Choosing the correct Data Format—whether it's human-readable JSON, strictly typed Protocol Buffers (Protobuf), or zero-copy FlatBuffers—is a fundamental architectural decision that dictates battery life, payload size, and rendering speed.

## Why It Matters

Imagine an app downloading a list of 10,000 products.
- **JSON:** The network downloads a 5MB text string. The CPU reads the string character by character. Every time it sees a `"name": "Laptop"`, the Android OS allocates a new `String` object in memory. It allocates 10,000 `Product` objects, 10,000 `String` objects, and 10,000 `Double` objects. The Garbage Collector panics, freezes the Main Thread for 200ms, and the app stutters.
- **Protobuf:** The network downloads a 1MB binary file. The parser reads binary tags and instantly constructs the Kotlin objects. It is 5x faster, but still requires allocating 10,000 objects in RAM.
- **FlatBuffers:** The network downloads a 1MB binary file. *There is no parser.* The app simply maps the binary file directly into RAM. To get the first product's name, the app reads a memory offset pointer. **Zero objects are allocated.** The parsing time is literally 0 milliseconds.

## Historical Context

- **XML (Pre-2010):** Extensible Markup Language. Massive, verbose, and incredibly slow to parse (DOM vs SAX parsing wars).
- **JSON (2010-Present):** JavaScript Object Notation. Won the war because it was natively supported by Web Browsers. It is human-readable, schema-less, and easy to debug. But it is fundamentally inefficient for machines to read.
- **Protocol Buffers / Protobuf (2008+):** Invented by Google for internal microservice communication. A binary format requiring a strict `.proto` schema file.
- **FlatBuffers (2014+):** Invented by Google for Game Developers. A memory-mapped binary format that requires zero parsing or allocation.

## First Principles

1.  **Serialization/Deserialization (SerDes):** The act of converting an in-memory object (Kotlin) into a format that can be sent over a wire (JSON/Binary), and vice versa.
2.  **Schema:** A strict contract defining exactly what the data looks like (e.g., "Field 1 is an Int32"). JSON has no mandatory schema. Protobuf requires one.
3.  **Zero-Copy / Memory Mapping:** A technique where the raw binary data downloaded from the network is used directly by the application, completely skipping the Deserialization step.
4.  **Forward/Backward Compatibility:** The ability for an old Android App (v1) to successfully read data sent by a new Server (v2), and vice versa, without crashing.

## The Formats

### 1. JSON (JavaScript Object Notation)
- **Mechanics:** Text-based key-value pairs.
- **Pros:** Human readable (you can read it in Charles Proxy or Logcat). Universally supported by every language. No schema setup required.
- **Cons:** Massive payload size (the keys like `"user_id"` are repeated thousands of times in an array). Very slow to parse. Not strictly typed (the server can accidentally send a String `"123"` instead of an Int `123`, crashing the app).

### 2. Protocol Buffers (gRPC / Protobuf)
- **Mechanics:** Binary format based on a strict `.proto` contract.
```protobuf
message User {
  int32 id = 1;
  string name = 2;
}
```
- **Pros:** Tiny payloads (Keys are reduced to a single byte integer tag like `1` or `2`). Blazingly fast parsing. Strongly typed (the compiler generates Kotlin data classes for you). Excellent backward compatibility rules.
- **Cons:** Binary data cannot be read by humans without a decoder. Requires sharing the `.proto` files between the Android repo and the Backend repo.

### 3. FlatBuffers
- **Mechanics:** Binary format structured exactly how C++ structs are laid out in memory.
- **Pros:** **Zero-Copy Parsing.** The parsing time is literally 0ms. It uses practically zero RAM because it doesn't create intermediate Kotlin objects.
- **Cons:** The API is incredibly hostile to write (you have to build objects backward using a Builder). It is mostly reserved for High-Frequency Trading apps, AAA 3D Games (Unity/Unreal), or massive ML data sets.

## Internal Mechanics

### How JSON Parsing Kills Battery (Reflection vs Codegen)

In the old days of Android, libraries like `Gson` used **Reflection**.
To parse `{"name": "John"}`, `Gson` would use Java Reflection to inspect the Kotlin class at runtime, find a field named `name`, force it to be accessible, and inject the string. Reflection is phenomenally slow.

Modern libraries (like `Moshi` with KSP, or `kotlinx.serialization`) use **Code Generation**.
During the Gradle build, they generate hardcoded Kotlin classes that act like massive `switch` statements. When the parser reads the string `"name"`, it jumps straight to `user.name = value`. This is 10x faster than Reflection.

### The JSON Parser Decision: Moshi vs `kotlinx.serialization`
If you are forced to use JSON, you must choose a parser.
- **Gson:** Deprecated by the community. Relies entirely on slow, unsafe Java Reflection. Do not use for new projects.
- **Moshi (Codegen):** Developed by Square. Highly reliable, fast, and generates Kotlin parsers via KSP at compile time. Excellent if you are using Retrofit in a pure Android (non-KMP) app.
- **kotlinx.serialization:** Developed by JetBrains. The modern standard. It is the only option that works perfectly across Kotlin Multiplatform (Android, iOS, Wasm). It is incredibly strict (will crash if backend sends `null` for a non-nullable field).

*Staff Rule:* If you use JSON, you MUST use a code-generating parser (`kotlinx.serialization` or Moshi Codegen). If you use `Gson` in a modern app, you are committing architectural malpractice.

## Architecture

```mermaid
graph TD
    subgraph JSON Payload (5MB Text)
        J1[{"id": 1, "name": "A"}] -->|Network| J2[Parse JSON String]
        J2 -->|Allocate Strings/Ints| J3[Kotlin Objects]
    end
    
    subgraph Protobuf Payload (1MB Binary)
        P1[01 01 02 41] -->|Network| P2[Parse Binary Tags]
        P2 -->|Allocate Strings/Ints| P3[Kotlin Objects]
    end
    
    subgraph FlatBuffers Payload (1MB Binary)
        F1[Memory Aligned Binary] -->|Network| F2[Memory Map ByteBuffer]
        F2 -.->|Zero Allocation| F3[Direct Pointer Reads]
    end
```

## Production Example

**Migrating to `kotlinx.serialization`**

If a team is migrating from `Gson` to `kotlinx.serialization` for performance, a Staff Engineer must handle the **Default Value Trap**.

```kotlin
@Serializable
data class User(
    val id: Int,
    val name: String,
    val isPremium: Boolean = false // Default value
)
```

If the Backend sends `{"id": 1, "name": "John"}`, `Gson` (using unsafe reflection) would sometimes initialize `isPremium` to `false` (JVM default), or worse, leave it null and crash later.
`kotlinx.serialization` respects Kotlin's default arguments perfectly. However, if the backend sends `{"id": 1, "name": "John", "isPremium": null}`, `kotlinx.serialization` will violently crash with a `SerializationException`. It refuses to put a `null` into a non-nullable field. 

This strictness prevents million-dollar bugs, but requires the Backend to actually respect the API contract.

## Tradeoffs

**Strictness vs Resilience**

- **JSON (Loose):** The backend can add 50 new fields to the JSON response. The Android app ignores them and keeps working. The backend can change the order of the fields. The app keeps working.
- **Protobuf (Strict):** If a backend developer deletes a field (e.g., changes `int32 id = 1` to `string user_id = 1`) without bumping the version, every Android app in the world will instantly fail to parse the binary payload. Protobuf relies on integer Tags (`1`, `2`). You can never reuse a tag, and you can never change a tag's type.

*Staff Decision:* Protobuf's strictness is actually a massive advantage. Because the `.proto` file is the contract, you can write CI/CD rules that fail the Backend's Pull Request if they break backward compatibility. JSON's looseness allows backend devs to silently break contracts.

## Failure Modes

- **The Massive JSON Main Thread Freeze:**
  A developer makes a network request using Coroutines `Dispatchers.IO`, downloads the JSON, and then accidentally passes the massive JSON string to the UI layer where `Moshi.fromJson()` is called on the Main Thread. The UI freezes for 300ms.
  *(Fix: Deserialization is a CPU-bound mathematical operation. It MUST be executed on `Dispatchers.Default` or `Dispatchers.IO` before the resulting Kotlin object is handed to the UI).*
- **Enum Evolution Crashes:**
  The Android app expects `enum class Status { ACTIVE, INACTIVE }`. The backend adds `PENDING` and sends it. The Android JSON parser throws an `IllegalArgumentException` because it doesn't know what `PENDING` is, crashing the app.
  *(Fix: Mobile API contracts must use `@Json(name = "UNKNOWN")` fallback mechanisms for Enums, or avoid Enums entirely and use Strings for network boundaries, to allow for safe forward-evolution of the API).*

## Staff Engineer Thinking

When reviewing data transport formats, a Staff engineer focuses on the bottleneck.

1.  **JSON is fine for 95% of use cases.** I don't migrate a Login API to Protobuf to save 5 milliseconds. I migrate the `Live Market Feed` API to Protobuf to save 500 milliseconds and prevent the phone from overheating. Premature optimization is the root of all evil.
2.  **Network vs CPU:** Sometimes the network is fast, but the CPU is slow. If we are downloading a massive 50MB map dataset, even Protobuf parsing will freeze the app. This is the only time I authorize **FlatBuffers**. We download the binary file, map it to disk via `MappedByteBuffer`, and the UI reads pointers directly off the disk without ever allocating a Kotlin object in RAM.
3.  **ProGuard / R8 Rules:** JSON parsers are notoriously fragile when minified. If R8 obfuscates `data class User(val firstName: String)` to `data class a(val b: String)`, the JSON parser will look for a JSON key called `"b"` and fail. I aggressively audit `@Keep` annotations and R8 rules to ensure our Data Transfer Objects (DTOs) are never obfuscated.

## Common Misconceptions

- **"JSON is smaller because it compresses well with GZIP."** GZIP is fantastic at compressing repeated JSON keys over the network. However, once the payload arrives at the phone, the OS must decompress it back into the massive, uncompressed JSON String in RAM before parsing it. Protobuf is tiny *in RAM*.
- **"Protobuf is a network protocol."** False. Protobuf is purely a Data Serialization format (like JSON). You can send Protobuf over HTTP/1.1, HTTP/2, WebSockets, or save it to a local disk. gRPC is the network protocol that usually carries Protobuf.

## Probing Questions

1.  Explain the fundamental difference between how a CPU processes a JSON payload versus a Protocol Buffer (Protobuf) payload.
2.  Why is Java Reflection incredibly dangerous for battery life and performance when parsing massive JSON arrays in Android?
3.  Describe the concept of "Zero-Copy" parsing in FlatBuffers. How does it eliminate Garbage Collection (GC) thrashing?
4.  If a backend developer renames a JSON key from `"user_id"` to `"userId"`, what happens to the Android app? How does Protobuf's integer tag system solve this?
5.  Why must an Android Engineer ensure that JSON deserialization (e.g., `Gson.fromJson()`) never executes on the Main (UI) Thread?
6.  Explain the "Enum Evolution Crash" and how a Staff Engineer designs Kotlin Data Classes to safely ignore new Enum values sent by the backend.
7.  How do Code-Generating JSON parsers (like `Moshi` Codegen or `kotlinx.serialization`) avoid the performance penalties of Reflection?
8.  Why is it an architectural requirement to configure R8 (ProGuard) rules to prevent obfuscation of Kotlin Data Transfer Objects (DTOs)?
9.  If an application downloads a 50MB statistical dataset, why might a Staff Engineer choose FlatBuffers over Protobuf?
10. Does compressing a JSON payload with GZIP reduce the memory footprint required to parse the JSON string on the Android device? Why or why not?

## Further Reading

- [`transport-protocols.md`](transport-protocols.md) — How Protobufs are usually transmitted over gRPC and HTTP/2.
- [`app-size-and-r8.md`](../android/performance/app-size-and-r8.md) — How the R8 shrinker breaks JSON parsing if `@Keep` rules are missing.
- [`jank.md`](../android/performance/jank.md) — The dropped frames caused by heavy JSON Reflection parsing on the Main Thread.
