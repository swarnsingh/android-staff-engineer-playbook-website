# Kotlin

## Purpose

The Kotlin language — from design choices to bytecode. Owns the canonical treatment of coroutines as a language feature; Android's coroutine application file links here.

## Why It Matters

Kotlin is the substrate for everything written in this repo's Android tree. Knowing it deeply — null safety, variance, inline functions, the memory model, JVM interop — is what separates engineers who write Android code from engineers who shape Android codebases.

## What This Folder Helps You Do

- Write Kotlin APIs that are null-safe, type-safe, binary-conscious, coroutine-friendly, and pleasant for other engineers to consume.
- Understand what the compiler generates: data-class methods, inline functions, reified type access, suspend state machines, bytecode, and Java interop surfaces.
- Reason about runtime behavior: heap allocation, captured continuations, cancellation, Flow backpressure, dispatcher boundaries, and test-time virtual time.
- Review Android and KMP code with Staff-level judgment: where abstractions leak, where variance matters, where public APIs become compatibility promises, and where coroutine misuse becomes a production incident.

## Learning Order

Language basics -> type system depth -> API design and metaprogramming -> coroutines and Flow -> runtime/JVM behavior -> version and KMP updates.

## Organization Note

The `kotlin/` folder is physically flat to preserve existing links, but this index groups the files by learning domain. If the repo later chooses a filesystem restructure, these sections are the intended subfolder boundaries.

## Topics

### Language Core

- [Variables](kotlin/variables.md)
- [Null Safety](kotlin/null-safety.md)
- [Functions](kotlin/functions.md)
- [Extensions](kotlin/extensions.md)
- [Data Classes](kotlin/data-classes.md)
- [Sealed Classes](kotlin/sealed-classes.md)
- [Delegation](kotlin/delegation.md)

### Type System and API Design

- [Generics](kotlin/generics.md)
- [Variance](kotlin/variance.md)

### Compiler Features and Metaprogramming

- [Inline Functions](kotlin/inline-functions.md)
- [Reified Types](kotlin/reified-types.md)

### Coroutines and Flow

- [Coroutines](kotlin/coroutines.md) — canonical owner; platform application lives in [`android/concurrency/coroutines-under-the-hood.md`](android/concurrency/coroutines-under-the-hood.md)
- [Channels and Select](kotlin/channels-and-select.md)
- [Flow Operators and Backpressure](kotlin/flow-operators-and-backpressure.md)
- [callbackFlow and Bridging Callbacks](kotlin/callbackflow-and-bridging-callbacks.md)
- [Coroutines Debugging and Profiling](kotlin/coroutines-debugging-and-profiling.md)
- [Test Dispatchers and Virtual Time](kotlin/test-dispatchers-virtual-time.md)

### Runtime and JVM Interop

- [Memory Model](kotlin/memory-model.md)
- [JVM Interop](kotlin/jvm-interop.md)
- [Bytecode](kotlin/bytecode.md)

### Version Updates

- [Kotlin 2.4 Update for Android and KMP](kotlin/kotlin-2-4-update.md)
