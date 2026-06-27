# Generics

## Overview

Generics allow you to write code that operates on *types as parameters*. Just as a function can take a `String` or an `Int` as an argument, a Generic class or function can take the *concept* of a `String` or `Int` as an argument. 

Generics are the foundation of reusable architectures. Without them, you would have to write a separate `StringList` class, an `IntList` class, and a `UserList` class. With generics, you write a single `List<T>` class, and the compiler enforces the type safety for you.

## Why It Matters

Before Generics existed (Java 1.4 and earlier), collections held raw `Object` references. You could put a `String` and a `Dog` into the exact same `ArrayList`. When you pulled an item out, you had to cast it: `(Dog) list.get(0)`. If you accidentally cast the `String` to a `Dog`, the app crashed at runtime with a `ClassCastException`.

Generics shifted this risk from Run Time to Compile Time. If you declare a `List<Dog>`, the compiler physically prevents you from putting a `String` into it. This mathematical guarantee is required to build safe, scalable SDKs.

## Historical Context

When Java 5 introduced Generics in 2004, they had a massive problem: Backward Compatibility. They could not break the millions of existing Java 1.4 programs that used raw `ArrayList`s. 

To solve this, Java introduced **Type Erasure**. The compiler enforces the generic types while compiling, but then it *erases* the types before generating the bytecode. At runtime in the JVM, a `List<String>` and a `List<Dog>` are the exact same thing: a raw `List` holding `Object`s. Kotlin runs on the JVM, so it inherited this exact same limitation. Understanding Type Erasure is the key to understanding all advanced Kotlin generics.

## First Principles

1.  **The Type Parameter (`<T>`):** The placeholder. It says "I don't know what type this is yet, but whatever it is, I will enforce it consistently across this class."
2.  **Type Erasure:** Generics do not exist at runtime on the JVM. They are a compile-time hallucination.
3.  **Upper Bounds:** You can restrict a generic. `<T : Animal>` means "T can be anything, as long as it is an Animal or a subclass of Animal."

## Mental Model

Think of a generic class like a Tupperware container factory.
- **The Blueprint (The Class):** The factory makes containers of a specific size, but it doesn't care what you put in them. `class Container<T>(val item: T)`
- **The Label (The Compiler):** When you buy the container, you stick a label on it: "Flour Only" (`Container<Flour>`). The Kitchen Manager (the Compiler) reads the label. If you try to put Sugar in the Flour container, the Manager stops you.
- **Type Erasure (At Runtime):** Once the containers are in the pantry with the lights off, the labels disappear. A container holding Flour looks identical to a container holding Sugar.

## Internal Mechanics

### 1. Type Erasure in Action

```kotlin
val stringList = listOf("A", "B")
val intList = listOf(1, 2)

// At compile time, the compiler knows stringList is List<String>.
// But look at what happens at runtime if we check the class:

println(stringList::class.java) // Prints: class java.util.Arrays$ArrayList
println(intList::class.java)    // Prints: class java.util.Arrays$ArrayList

// They are identical. The <String> and <Int> have been erased.
```

Because of Type Erasure, you **cannot** perform `is` checks on generic types at runtime:

```kotlin
fun checkType(list: Any) {
    // COMPILER ERROR: Cannot check for instance of erased type: List<String>
    if (list is List<String>) { ... } 
}
```
*Why?* Because at runtime, the JVM has no idea if the list holds Strings or Ints. It only knows it's a `List`.

### 2. The Star Projection (`*`)

If you want to check if something is a List, but you acknowledge that you cannot know what is *inside* the List due to Type Erasure, you use the Star Projection.

```kotlin
fun checkTypeSafely(list: Any) {
    // Valid! Checks if it is a List of literally anything.
    if (list is List<*>) {
        println("It's a list with ${list.size} items!")
        
        // But because of the *, you cannot safely read elements as specific types:
        val item = list[0] // Type is 'Any?', not 'String'.
    }
}
```

## Architecture

```mermaid
graph TD
    subgraph Compile Time
        Code[val list = List<String>] --> Compiler[Kotlinc Compiler]
        Compiler -->|Enforces Types| Check[Refuses list.add(1)]
    end
    
    subgraph Run Time (JVM)
        Compiler -->|Generates Bytecode| Bytecode
        Bytecode --> JVM[JVM Execution]
        JVM -->|Types Erased| Raw[Raw List holds Objects]
        Raw -->|Auto-Casts| Get[String s = (String) list.get(0)]
    end
```

## Production Example

**Generic Network Responses**

Generics are heavily used to create uniform wrappers around API responses.

```kotlin
// The Generic Wrapper
// T can be anything (User, Product, Order)
sealed class ApiResponse<T> {
    data class Success<T>(val data: T) : ApiResponse<T>()
    data class Error<T>(val exception: Exception) : ApiResponse<T>()
}

// Usage in Repository
suspend fun fetchUser(): ApiResponse<User> {
    return try {
        val user = api.getUser()
        ApiResponse.Success(user)
    } catch (e: Exception) {
        ApiResponse.Error(e)
    }
}
```

## Tradeoffs

**Advantages**
- **Type Safety:** Eliminates `ClassCastException`.
- **DRY (Don't Repeat Yourself):** A single `Result<T>` class can handle every single network request in the entire application.

**Disadvantages**
- **Complexity:** Generics get incredibly confusing when combined with Inheritance (this leads to [Variance](variance.md), which is notoriously difficult).
- **Runtime Blindness:** Type Erasure makes reflection and dynamic type checking very painful. (Though Kotlin solves some of this with [Reified Types](reified-types.md)).

## Failure Modes

- **The Generic Shadowing Trap:**
  ```kotlin
  class Processor<T> {
      // BAD: The <T> in the function signature SHADOWS the <T> of the class.
      // This function's T is completely unrelated to the class's T!
      fun <T> process(item: T) { }
  }
  ```
  *(Fix: Remove the `<T>` from the function signature if you want to use the class's type parameter).*
- **The Unchecked Cast Warning:**
  ```kotlin
  val genericList: List<*> = listOf(1, 2, 3)
  // The compiler warns you: "Unchecked cast: List<*> to List<String>"
  val stringList = genericList as List<String> 
  
  // It compiles, but it will crash at runtime when you try to read it!
  val s: String = stringList[0] // ClassCastException: Integer cannot be cast to String
  ```
  *(Fix: Never ignore unchecked cast warnings. The compiler is telling you it cannot guarantee safety because of Type Erasure).*

## Staff Engineer Thinking

When reviewing generic architecture, a Staff engineer focuses on boundaries and constraints:

1.  **Do we need Upper Bounds?** If I see `class JsonParser<T>`, I immediately ask if `T` can be literally anything, including `null`. If `T` shouldn't be nullable, it must be `class JsonParser<T : Any>`. If `T` must implement an interface, it must be `class JsonParser<T : Serializable>`. Unbounded generics are often too permissive.
2.  **Is this overly generic?** Junior developers often suffer from "Genericitis"—trying to make every single class generic "just in case." Generics reduce readability. If a class is only ever going to process `String`s, hardcode it to `String`. I enforce the Rule of Three: don't make it generic until you have three distinct use cases.
3.  **Are we relying on Runtime Type Information (RTTI)?** If a generic class tries to do `T::class.java` to instantiate an object using reflection, I know the developer doesn't understand Type Erasure. The bytecode won't compile. I will direct them to use `inline` functions with `reified` types.

## Common Misconceptions

- **"Generics make the app larger or slower."** False. Because of Type Erasure, there is no runtime overhead. A `List<String>` and a `List<Int>` share the exact same bytecode implementation in memory. (Note: C++ Templates work differently and *do* bloat the binary; JVM Generics do not).
- **"If `Dog` is a subclass of `Animal`, then `List<Dog>` is a subclass of `List<Animal>`."** This is the most dangerous misconception in Kotlin. It is completely FALSE. This concept is called Invariance, and it requires a dedicated file to explain: [Variance](variance.md).

## Probing Questions

1.  What is "Type Erasure," and why was it introduced into the JVM?
2.  Why does `if (myList is List<String>)` fail to compile in Kotlin?
3.  What is the purpose of the Star Projection (`*`) in Kotlin generics?
4.  Explain the difference between `<T>` (unbounded) and `<T : Any>` (bounded) in a generic class definition.
5.  If Generics are erased at runtime, how does the JVM know to throw a `ClassCastException` if you put the wrong object into a raw list? (Hint: The compiler inserts automatic casts).
6.  Describe a scenario where a developer might accidentally "Shadow" a generic type parameter.
7.  Why are generic wrapper classes (like `Result<T>` or `Resource<T>`) so ubiquitous in Android repository layers?
8.  If you need to know the actual `Class` of `T` at runtime (e.g., to pass it to a JSON deserializer), why do standard generics fail, and what Kotlin feature must you use instead?
9.  Why is ignoring an "Unchecked Cast" compiler warning considered a severe architectural risk?
10. If `List<String>` and `List<Int>` compile to the exact same bytecode, how does the IDE provide auto-complete for `.length` on the String list, but not the Int list?

## Further Reading

- [`variance.md`](variance.md) — Why `List<Dog>` is not a `List<Animal>`, and how to fix it with `in` and `out`.
- [`reified-types.md`](reified-types.md) — How to magically bypass Type Erasure at runtime.
- [Oracle Java Docs: Type Erasure](https://docs.oracle.com/javase/tutorial/java/generics/erasure.html)
