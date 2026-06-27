# The Memory Model (Stack vs. Heap)

## Overview

Understanding the Kotlin memory model requires understanding the underlying Java Virtual Machine (JVM). The JVM divides memory into two primary areas: the **Stack** and the **Heap**. 

A Staff engineer must know exactly where their Kotlin code is allocating memory, because allocating memory in the wrong place (the Heap) causes the Garbage Collector (GC) to run, which drops UI frames and causes the app to stutter (Jank).

## Why It Matters

Every object you create requires memory. 
- Memory allocated on the **Stack** is "free." It takes nanoseconds, requires zero cleanup, and is completely invisible to the Garbage Collector.
- Memory allocated on the **Heap** is expensive. It takes longer to find space, and eventually, the JVM must stop the entire app (Stop-The-World) to clean it up.

If you write a `for` loop that iterates 10,000 times to draw pixels on a screen, and you accidentally allocate an object on the Heap inside that loop, you will trigger a GC pause. The screen will freeze. Understanding how Kotlin compiles to JVM bytecode is the only way to avoid this.

## Historical Context

In C and C++, developers had to manually allocate memory to the heap using `malloc()` and manually clean it up using `free()`. Forgetting to call `free()` caused memory leaks. The JVM was invented to solve this by managing the Heap automatically via Garbage Collection. However, automatic GC is not magic; it requires massive CPU resources to track "dead" objects. Modern Android development (like Jetpack Compose) emphasizes minimizing Heap allocations to keep the GC completely silent.

## First Principles

1.  **The Stack (Fast & Temporary):** Used for function execution. It holds primitive values (`Int`, `Double`, `Boolean`) and *references* (memory addresses) to objects. When a function finishes, its Stack is instantly destroyed.
2.  **The Heap (Slow & Permanent):** Used for storing actual Objects (`User`, `String`, `List`). It persists across function calls until the Garbage Collector decides no Stack references point to it anymore.
3.  **Kotlin's Illusion:** Kotlin hides the difference between Primitives and Objects in syntax. Everything *looks* like an Object (`Int`, `Double`), but the compiler secretly optimizes them to JVM primitives on the Stack whenever mathematically possible.

## Mental Model

Think of a bustling Restaurant.
- **The Stack (A Waiter's Notepad):** The waiter writes down an order quickly. It's cheap, fast, and completely temporary. As soon as the order is given to the kitchen (the function returns), the waiter throws the paper away. Zero cleanup required.
- **The Heap (The Kitchen Pantry):** The kitchen stores massive amounts of ingredients. When an order comes in, they have to search the pantry (allocation) and take ingredients out. Every hour, the kitchen has to stop cooking entirely to sweep the floors and throw away rotten food (Garbage Collection). 
- **The Reference:** The waiter's notepad doesn't contain a physical steak. It contains a *reference* (a word) pointing to the steak in the pantry.

## Internal Mechanics

How does Kotlin map its elegant syntax to the ruthless reality of the JVM Stack and Heap?

### 1. Primitives vs Wrappers

```kotlin
fun calculate() {
    // Looks like an object. The compiler optimizes it to a JVM primitive 'int'.
    // Stored entirely on the STACK. Zero GC cost.
    val age: Int = 30 
    
    // Looks almost identical. But it's Nullable.
    // The JVM cannot store 'null' in a primitive 'int'. 
    // The compiler is forced to "Box" it into a java.lang.Integer OBJECT.
    // Stored on the HEAP. Causes GC pressure.
    val nullAge: Int? = 30 
}
```

This is why `List<Int>` is dangerous in performance-critical code. A `List` can only hold Objects (Generics undergo Type Erasure). Every single `Int` in that list is Boxed into an object on the Heap. *(Use `IntArray` instead, which holds raw primitives contiguous in memory).*

### 2. Escape Analysis

The JVM has an incredibly advanced Just-In-Time (JIT) compiler. It performs "Escape Analysis."

```kotlin
fun processUser() {
    // We create a User object. Normally, Objects go on the Heap.
    val user = User("Alice") 
    
    // We only use it inside this function. We don't return it. 
    // It does not "Escape" the function.
    println(user.name)
}
```
If the JIT compiler can mathematically prove that the `User` object never leaves the function (it doesn't escape), it will magically "Scalar Replace" the object. It will break the `User` object apart and store its inner fields directly on the **Stack**, completely bypassing the Heap and the Garbage Collector.

### 3. Lambdas and the Heap

As discussed in [Inline Functions](inline-functions.md), Lambdas are anonymous objects.

```kotlin
fun doMath(action: () -> Unit) { ... }

fun test() {
    var counter = 0
    // We pass a Lambda. This allocates a Function0 Object on the HEAP.
    // AND it captures the 'counter' variable, forcing 'counter' onto the Heap too!
    doMath { counter++ } 
}
```
If `doMath` is marked `inline`, the Lambda is never allocated, and `counter` remains safely on the Stack.

## Architecture

```mermaid
graph TD
    subgraph The JVM Memory Space
        subgraph Thread 1 Stack
            F1[Function execution]
            P1[Primitive: int = 5]
            Ref1[Reference: mem_addr_0x1]
            Ref2[Reference: mem_addr_0x2]
        end
        
        subgraph The Heap (Garbage Collected)
            Obj1[0x1: String 'Alice']
            Obj2[0x2: User Object]
            Obj3[0x3: Dead Object] -.->|Swept by GC| Trash
        end
    end
    
    Ref1 --> Obj1
    Ref2 --> Obj2
```

## Production Example

**Jetpack Compose & Value Classes**

In Jetpack Compose, the color of a pixel is represented by a `Color` class. The screen draws at 60 Frames Per Second. If `Color` was a normal class, changing the color of the screen would allocate 60 Objects per second on the Heap. The UI would stutter immediately.

Kotlin solved this with `value class`.

```kotlin
// A Value Class tells the compiler to erase the object wrapper at runtime!
@JvmInline
value class Color(val value: ULong)

fun draw(color: Color) { ... }
```
At compile time, `Color` is a strongly-typed class. At runtime, the JVM literally strips the class away and passes the raw `ULong` primitive on the Stack. Zero Heap allocations. 60 FPS achieved.

## Tradeoffs

**Advantages of Stack Allocation**
- Blistering fast access (L1 CPU Cache).
- Zero Garbage Collection overhead.

**Disadvantages of Stack Allocation**
- Tiny capacity (usually 1MB per thread). If you try to put too much on the Stack (e.g., Infinite Recursion), you get a `StackOverflowError`.
- No sharing. The Stack is private to the Thread. You cannot share Stack memory between two threads.

## Failure Modes

- **The Boxing Loop:**
  ```kotlin
  var sum: Long? = 0L // BAD: Nullable Long forces Boxing.
  for (i in 1..10_000) {
      // Every iteration creates a brand new java.lang.Long OBJECT on the Heap!
      // This allocates 10,000 Objects and triggers a massive GC pause.
      sum = sum?.plus(i) 
  }
  ```
  *(Fix: Use non-nullable primitives `var sum: Long = 0L` in loops).*
- **Leaking the Context (Android):**
  If a long-running background thread holds a reference to an `Activity`, the `Activity` object is on the Heap. Even if the user destroys the screen, the GC cannot clean up the `Activity` because the thread's Stack still holds a valid reference to it. This is a Memory Leak. The app will eventually run out of Heap space and throw an `OutOfMemoryError` (OOM).

## Staff Engineer Thinking

When reviewing performance-critical code (Custom Views, Compose Modifiers, Physics Engines), a Staff engineer becomes a Memory Auditor:

1.  **Hunt for allocations in `onDraw`.** I will reject any PR that uses the `new` keyword (or Kotlin constructor calls) inside an `onDraw` loop. All `Paint`, `Path`, and `Rect` objects must be pre-allocated on the Heap during initialization and simply reused/mutated during the loop.
2.  **Primitive Arrays vs Collections.** If we are processing 100,000 audio samples, I forbid the use of `List<Float>`. It must be a `FloatArray`. The overhead of 100,000 Object Headers on the Heap will destroy the cache locality and choke the CPU.
3.  **Value Classes for Domain Types.** I push teams to use `value class UserId(val id: String)` instead of passing raw Strings everywhere. It provides massive compile-time safety (preventing you from accidentally passing a `Password` string to a `UserId` function) with literally zero memory overhead at runtime.

## Common Misconceptions

- **"Kotlin `Int` is an Object because I can call `.toString()` on it."** False. It is an illusion provided by the compiler. If it can be a JVM primitive on the Stack, the compiler makes it one. The compiler only boxes it into an Object on the Heap if you make it nullable (`Int?`) or put it in a Generic (`List<Int>`).
- **"The Garbage Collector is fast, I don't need to worry about the Heap."** The modern ART GC is incredibly fast, but it is not magic. "Stop-The-World" pauses still exist. If you allocate garbage faster than the GC can clean it up, the GC is forced into a desperate, blocking sweep, skipping frames and causing Jank.

## Probing Questions

1.  What is the fundamental difference in lifecycle and cleanup between the JVM Stack and the JVM Heap?
2.  Why does adding a `?` to a primitive type (e.g., `Int?`) force the JVM to allocate memory on the Heap instead of the Stack?
3.  Explain why `IntArray` is vastly more memory-efficient than `List<Int>` when dealing with thousands of numbers.
4.  What is "Escape Analysis," and how does the JIT compiler use it to optimize object allocation?
5.  Why is allocating a new object inside a drawing loop (like `onDraw` or a Compose layout phase) considered a catastrophic performance anti-pattern in Android?
6.  How does a `value class` provide the compile-time safety of a strong type without the runtime memory overhead of a Heap object?
7.  Explain the relationship between the `inline` keyword and reducing Garbage Collection pressure caused by Lambdas.
8.  What is a `StackOverflowError`, and what specific programming mistake typically causes it?
9.  Describe how a Memory Leak occurs when the Stack interacts with the Heap (e.g., an Android `Activity` leak).
10. If the JVM Stack is so much faster than the Heap, why don't we just allocate all objects on the Stack?

## Further Reading

- [`inline-functions.md`](inline-functions.md) — The tool used to prevent Lambdas from hitting the Heap.
- [Android Developers: Manage your app's memory](https://developer.android.com/topic/performance/memory)
