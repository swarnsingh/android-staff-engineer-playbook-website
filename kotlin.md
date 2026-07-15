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

The `kotlin/` folder is organized by learning domain. Each subfolder keeps a focused slice of the language: core syntax, type-system design, compiler features, coroutine/Flow mechanics, runtime/JVM behavior, and version-specific updates.

## Topics

### Language Core

- [Variables](kotlin/language-core/variables.md)
- [Null Safety](kotlin/language-core/null-safety.md)
- [Functions](kotlin/language-core/functions.md)
- [Extensions](kotlin/language-core/extensions.md)
- [Data Classes](kotlin/language-core/data-classes.md)
- [Value Classes](kotlin/language-core/value-classes.md)
- [Sealed Classes](kotlin/language-core/sealed-classes.md)
- [Delegation](kotlin/language-core/delegation.md)

### Type System and API Design

- [Generics](kotlin/type-system/generics.md)
- [Variance](kotlin/type-system/variance.md)

### Compiler Features and Metaprogramming

- [Inline Functions](kotlin/compiler-features/inline-functions.md)
- [Reified Types](kotlin/compiler-features/reified-types.md)

### Coroutines and Flow

- [Coroutines](kotlin/coroutines-and-flow/coroutines.md) — canonical owner; platform application lives in [`android/concurrency/coroutines-under-the-hood.md`](android/concurrency/coroutines-under-the-hood.md)
- [Channels and Select](kotlin/coroutines-and-flow/channels-and-select.md)
- [Flow Operators and Backpressure](kotlin/coroutines-and-flow/flow-operators-and-backpressure.md)
- [callbackFlow and Bridging Callbacks](kotlin/coroutines-and-flow/callbackflow-and-bridging-callbacks.md)
- [Coroutines Debugging and Profiling](kotlin/coroutines-and-flow/coroutines-debugging-and-profiling.md)
- [Test Dispatchers and Virtual Time](kotlin/coroutines-and-flow/test-dispatchers-virtual-time.md)

### Runtime and JVM Interop

- [Memory Model](kotlin/runtime-and-jvm/memory-model.md)
- [JVM Interop](kotlin/runtime-and-jvm/jvm-interop.md)
- [Bytecode](kotlin/runtime-and-jvm/bytecode.md)

### Version Updates

- [Kotlin 2.4 Update for Android and KMP](kotlin/version-updates/kotlin-2-4-update.md)
