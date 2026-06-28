# Reified Types

## Overview

The `reified` keyword is Kotlin's magic trick for defeating "Type Erasure." It allows you to access the actual, concrete type of a Generic `<T>` at runtime inside a function. 

You can only use the `reified` keyword on generic parameters of an `inline` function.

## Why It Matters

As covered in [Generics](generics.md), the JVM erases generic types at compile time. At runtime, a `List<String>` is just a `List`. Because of this, you cannot perform reflection or type-checking on `T`.

```kotlin
// BAD: This will not compile.
fun <T> printType() {
    println(T::class.java) // ERROR: Cannot use 'T' as a reified type parameter. Use a class instead.
}
```

In Java, the only workaround is to force the caller to manually pass the `Class` object into the function:
`public <T> void printType(Class<T> clazz) { System.out.println(clazz); }`

This leads to incredibly ugly, verbose APIs: `gson.fromJson(jsonString, User.class)`.

Kotlin's `reified` keyword eliminates this boilerplate, allowing you to simply write: `gson.fromJson<User>(jsonString)`.

## Historical Context

Java architects chose Type Erasure in 2004 to maintain backward compatibility with old codebases. C# (which was created slightly later) chose to implement true Generics at the VM level, meaning C# does not have Type Erasure. Kotlin, being forced to run on the Java Virtual Machine, was stuck with Type Erasure. The `reified` keyword is a compiler hack specifically invented by JetBrains to provide C#-like generic capabilities on top of a JVM that inherently does not support them.

## First Principles

1.  **Reified means "Made Real":** A reified type parameter is not erased. It remains a real, queryable class at runtime.
2.  **Must be Inline:** The `reified` keyword absolutely requires the function to be marked `inline`. The magic does not work without it.
3.  **No Java Interop:** Because `reified` is a Kotlin compiler hack, Java code cannot call Kotlin functions that use `reified` types.

## Mental Model

Think of a bouncer at a club checking IDs.
- **Normal Generics (Type Erasure):** The club manager says, "Only VIPs (`<T>`) allowed." But the bouncer is blindfolded. When someone walks up, the bouncer cannot check their ID (`T::class`). The bouncer has to guess, which is illegal, so the compiler stops the manager from even giving the order.
- **Reified Generics:** The manager says, "Only VIPs allowed." Because it's an `inline` function, the manager *clones* the bouncer and sends a specific bouncer for every single VIP. One bouncer is specifically told, "Look for Alice's ID." Another is told, "Look for Bob's ID." They don't need to know what `<T>` is, because their instructions were hardcoded with the exact name before they started working.

## Internal Mechanics

How does Kotlin bypass the JVM's hard rule on Type Erasure? By cheating.

Using the rules of [Inline Functions](inline-functions.md), the compiler copies the body of the function and pastes it into the caller's code. Because the caller *knows* the exact type it is passing, the compiler simply replaces the generic `T` with the actual hardcoded class!

```kotlin
// The Reified Function
inline fun <reified T> isType(item: Any): Boolean {
    // We can use 'T' directly as a class!
    return item is T 
}

fun test() {
    val result = isType<String>(123)
}
```

If we decompile the `test()` function into Java, the magic is revealed:

```java
// Decompiled Java
public final void test() {
    Object item = 123;
    
    // The compiler pasted the inline function here, and replaced 'T' 
    // with 'String' because it saw we called isType<String>.
    // There are no Generics here at all! Type Erasure was bypassed entirely.
    boolean result = item instanceof String; 
}
```

## Bytecode Evidence

The decompiled Java says "instanceof String," but is that actually true in the bytecode, or is the decompiler reconstructing it from generics metadata? Run `javap -c -p`:

```
public final void test();
  Code:
     0: bipush        123
     2: invokestatic  #15 // Method java/lang/Integer.valueOf:(I)Ljava/lang/Integer;
     5: astore_1                                              // Any item = 123 (boxed)
     6: aload_1                                               // push item
     7: instanceof    #17 // class java/lang/String           // <-- HARDCODED String
    10: istore_2                                              // boolean result
    11: return
```

The constant pool entry at #17 reads:

```
#17 = Class              #18  // java/lang/String
#18 = Utf8               java/lang/String
```

There is no `T` anywhere. No `TypeToken<T>`, no `Class<T>` parameter, no `kotlin.reflect.KClass`. The class `java/lang/String` is hardcoded into the bytecode of `test()`. The compiler resolved `T = String` at compile time and emitted `instanceof java/lang/String` directly.

Now compile a second call site: `isType<Int>(123)`. You'll get a separate `test2()` method with:

```
     7: instanceof    #19 // class java/lang/Integer
```

Same `isType<>` source function, two different bytecode call sites, two different hardcoded class references. The "function" doesn't exist at runtime; only its specialised copies do.

**This is what makes `reified` impossible without `inline`.** A normal function compiles to one method body shared across all type parameters. The JVM can't preserve `T` for that single body — type erasure. With `inline`, there is no shared body; every call site gets its own bytecode with `T` already substituted. The JVM never has to "remember" `T` because the compiler already wrote it down.

## Production Example

**JSON Parsing and Intent Routing**

Reified types are used heavily in Android to clean up APIs that require `Class` objects.

**Before (Java-style):**
```kotlin
val intent = Intent(context, ProfileActivity::class.java)
startActivity(intent)

val user = gson.fromJson(json, User::class.java)
```

**After (Kotlin Reified style):**
```kotlin
// The extension function
inline fun <reified T : Activity> Context.startActivity() {
    startActivity(Intent(this, T::class.java))
}

// Usage: Clean and idiomatic
startActivity<ProfileActivity>()

val user: User = gson.fromJson(json) // T is inferred from the return type!
```

## Tradeoffs

**Advantages**
- **Beautiful APIs:** Eliminates the `Class<T>` boilerplate completely.
- **Type Inference:** The compiler can often infer `<T>` from the variable you are assigning the result to, meaning you don't even have to write `<T>` at the call site.

**Disadvantages**
- **Inline Bloat:** Because it *must* be an `inline` function, you suffer all the tradeoffs of inlining. If your reified function is 50 lines long and called 100 times, you just added 5,000 lines of bytecode to your APK.
- **No Java Calls:** If your Android project is a mix of Java and Kotlin, Java cannot use your beautiful reified extension functions. They are invisible to Java.

## Failure Modes

- **Reifying Massive Functions:**
  ```kotlin
  inline fun <reified T> parseNetworkResponse(json: String): T {
      // BAD: 50 lines of complex Gson parsing logic here.
      // Every time you call this, 50 lines of bytecode are duplicated.
  }
  ```
  *(Fix: The inline function should be a tiny 1-line wrapper that immediately delegates the heavy lifting to a normal, non-inline function, passing the `Class` object along).*
  ```kotlin
  // GOOD: Tiny inline wrapper
  inline fun <reified T> parse(json: String): T = parseReal(json, T::class.java)
  
  // GOOD: Massive logic safely hidden in a normal function
  fun <T> parseReal(json: String, clazz: Class<T>): T { /* 50 lines */ }
  ```
- **Confusing Reified with Reflection:** Thinking you need `reified` to use Kotlin Reflection on concrete objects. You don't. You only need `reified` if the type you want to reflect on is currently hidden behind a Generic `<T>`.

## Staff Engineer Thinking

When reviewing code, a Staff engineer looks for API ergonomics:

1.  **Kill the `Class<T>`:** If I see a Kotlin function signature `fun doWork(clazz: Class<*>)`, I will immediately ask for a refactor to `inline fun <reified T> doWork()`. We are writing Kotlin, not Java 6. We should use language features to make the call-sites as clean as possible for product engineers.
2.  **The Wrapper Rule:** I strictly enforce that `inline reified` functions are only used as tiny wrappers. They exist solely to extract `T::class.java` and pass it to a private, non-inline worker function. This prevents bytecode bloat while keeping the public API clean.
3.  **Java Interop:** If we are writing a core SDK that might be consumed by legacy Java code, I will enforce writing *both* versions. A standard `Class<T>` version for Java, and an `inline reified` extension function for Kotlin users.

## Common Misconceptions

- **"Reified types change how the JVM works."** No. The JVM is still enforcing Type Erasure. The `kotlinc` compiler is just copy/pasting your code and hardcoding the class names before the JVM ever sees it.
- **"I can reify a class-level generic."** False. You cannot write `class Container<reified T>`. You can only reify *functions*. If you instantiate a class, that class lives on the heap and must obey Type Erasure. Only function calls can be copy/pasted by the `inline` compiler directive.

## Probing Questions

1.  What is the specific limitation of JVM Generics (Type Erasure) that the `reified` keyword was invented to solve?
2.  Why is the `reified` keyword mathematically impossible to implement without also using the `inline` keyword?
3.  If you decompile a Kotlin function that uses `T::class.java` (where `T` is reified) back into Java, what does the Java code look like?
4.  Why can't Java code call a Kotlin function that uses a `reified` type parameter?
5.  Explain the architectural danger of putting 100 lines of complex logic inside an `inline fun <reified T>` function.
6.  How can the Kotlin compiler infer the type of a `reified T` without the developer explicitly writing `<User>` at the call site?
7.  Write a tiny `inline reified` wrapper function that delegates to a massive non-inline parsing function to prevent bytecode bloat.
8.  Why is it impossible to apply the `reified` keyword to the generic type parameter of a `class`?
9.  Describe an Android specific API (like Intents or SharedPreferences) that is drastically improved by creating a `reified` wrapper.
10. If C# does not use Type Erasure, does C# need a `reified` keyword? Why or why not?

## Further Reading

- [`generics.md`](generics.md) — The fundamental rules of Type Erasure.
- [`inline-functions.md`](inline-functions.md) — The copy/paste mechanism that makes reified types possible.
