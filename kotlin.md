# Kotlin

## Purpose

The Kotlin language — from design choices to bytecode. Owns the canonical treatment of coroutines as a language feature; Android's coroutine application file links here.

## Why It Matters

Kotlin is the substrate for everything written in this repo's Android tree. Knowing it deeply — null safety, variance, inline functions, the memory model, JVM interop — is what separates engineers who write Android code from engineers who shape Android codebases.

## Learning Order

Language basics → type system depth (generics, variance) → metaprogramming (inline, reified) → coroutines → runtime (memory model, JVM interop, bytecode).

## Topics

- [Variables](kotlin/variables.md)
- [Null Safety](kotlin/null-safety.md)
- [Functions](kotlin/functions.md)
- [Extensions](kotlin/extensions.md)
- [Data Classes](kotlin/data-classes.md)
- [Sealed Classes](kotlin/sealed-classes.md)
- [Delegation](kotlin/delegation.md)
- [Inline Functions](kotlin/inline-functions.md)
- [Reified Types](kotlin/reified-types.md)
- [Generics](kotlin/generics.md)
- [Variance](kotlin/variance.md)
- [Coroutines](kotlin/coroutines.md) — canonical owner; [`android/coroutines.md`](android/coroutines.md) is the application file
- [Memory Model](kotlin/memory-model.md)
- [JVM Interop](kotlin/jvm-interop.md)
- [Bytecode](kotlin/bytecode.md)
