---
title: Java8
date: 2025-12-04 21:06:42
tags:
  - 面试
categories:
  - 后端开发
  - 面试
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/JAVA8.webp
sticky:
hidden: false
updated: 2025-12-04 22:11
---
# Lambda 表达式、Method Reference - 方法引用

```java
private static void testLambda() {
    List<String> names = Arrays.asList("name", "sex", "hobby");

    // with method reference -- static method
    names.forEach(System.out::println);
    names.forEach(name -> System.out.println(name));

    // with method reference -- instance method
    names.sort(String::compareTo);
    names.sort((a, b) -> a.compareTo(b));

    // with method reference -- constructor method
    Supplier<Map<String, String>> mm = () -> new HashMap<>();
    Supplier<Map<String, String>> supplier = HashMap::new;
}
```

# Supplier

`Supplier` 接口的应用场景通常涉及需要延迟计算、动态生成值、或者在需要提供某种默认值的情况。以下是一些可能的应用场景：

1. **延迟计算：**

   ```Java
   Supplier<Double> randomSupplier = Math::random;
   // 这里并不会立即生成随机数，而是在调用get()时才生成
   double randomValue = randomSupplier.get();
   ```

2. **提供默认值：**

   ```Java
   Supplier<String> defaultStringSupplier = () -> "Default Value";
   String value = getValueFromSomeSource(); // 某个方法获取值
   String result = (value != null) ? value : defaultStringSupplier.get();
   ```

3. **动态生成对象：**

   ```Java
   Supplier<List<String>> listSupplier = ArrayList::new;
   List<String> list = listSupplier.get();
   ```

4. **懒加载：**

   ```Java
   class LazyInitializedObject {
       private Supplier<ExpensiveObject> expensiveObjectSupplier = 
           () -> {
               ExpensiveObject obj = new ExpensiveObject();
               // 进行一些初始化或者其他操作
               return obj;
           };
   
       public ExpensiveObject getExpensiveObject() {
           return expensiveObjectSupplier.get();
       }
   }
   ```

这些例子都展示了如何使用 `Supplier` 接口来提供一种方法，使得某些值或操作的计算被推迟，直到真正需要这些值的时候再进行计算。这种延迟计算的特性可以提高性能，尤其是在处理昂贵或者资源密集型的操作时。

# Stream API

Stream API 引入了一种新的抽象，用于对集合进行流式操作。它提供了一种声明性的方式来操作数据，支持类似 SQL 的查询语言，使得代码更为清晰和简洁。Stream 操作可以分为中间操作和终端操作。

中间操作可以是链式的，形成一条流水线，例如过滤、映射、排序等：

```Java
List<String> filteredNames = names.stream()
                                  .filter(name -> name.startsWith("A"))
                                  .map(String::toUpperCase)
                                  .collect(Collectors.toList());
```

终端操作会触发流水线的执行，例如收集、计数、聚合等：

```Java
long count = names.stream().count();
```

Stream API 使得我们能够以一种更函数式的方式来处理数据，从而提高代码的可读性和可维护性。

Lambda 表达式和 Stream API 通常一起使用，以实现更简洁、高效的集合操作。它们是 Java 向函数式编程的转变迈出的重要一步，为开发者提供了更多灵活性和表达力。

# Others

1. **默认方法（Default Methods）：**

   - 接口中可以包含默认方法，允许在接口中提供具体实现，而不影响实现该接口的现有类。这为接口的演进提供了更大的灵活性。

   ```Java
   interface MyInterface {
       default void myMethod() {
           System.out.println("Default implementation");
       }
   }
   ```

2. **函数式接口：**

   - 函数式接口是只包含一个抽象方法的接口。Java 8 通过 `@FunctionalInterface` 注解来支持函数式接口的定义，以便更好地支持 Lambda 表达式。

```Java
   @FunctionalInterface
   interface MyFunctionalInterface {
       void myMethod();
   }
   ```

3. **新的日期和时间 API：**

   - `java.time` 包提供了全新的日期和时间 API，支持更方便的日期和时间操作，解决了旧的 `java.util.Date` 和 `java.util.Calendar` 类的问题。

   ```Java
   LocalDate date = LocalDate.now();
   LocalTime time = LocalTime.now();
   ```

4. **CompletableFuture：**

   - `CompletableFuture` 是一个支持异步编程的工具，可以轻松处理异步操作和构建异步应用程序。

   ```java
   CompletableFuture<String> future = CompletableFuture.supplyAsync(() -> "Hello")
                                                      .thenApply(s -> s + " World");
   ```

5. **方法引用（Method References）：**

   - 方法引用是一种简化 Lambda 表达式的语法，它提供了一种直接引用已有方法（静态方法、实例方法或构造方法）的方式。

   ```Java
   list.forEach(System.out::println);
   ```

这些特性使得 Java 8 在代码编写、集合操作、并发编程等方面变得更加强大和灵活。学习这些特性可以提高代码的效率、可读性，并使代码更具现代化。