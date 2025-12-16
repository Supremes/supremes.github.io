---
title: Java新特性简介
tags:
  - 面试
categories:
  - 后端开发
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/JAVA8.webp
hidden: false
updated: 2025-12-16 11:24
abbrlink: 5363d109
date: 2025-12-04 21:06:42
sticky:
---
# Java 8 新特性
## Lambda 表达式
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

#### 语法格式 
Lamda 的基本语法有三步构成
```Java
(参数列表) -> {方法体}
```

- 参数列表：`可省略类型`，编译器会自动推断
- 右侧：Lamda 体，若只有一行代码，可以省略 `花括号{}和 return 关键字`

### 函数式接口 - Functional Interface
Lambda 表达式不能凭空存在，它必须依附于**函数式接口**。
>  - Lambda 表达式**必须**依托于一个**确定的接口**（JDK 自带的如 `Runnable`, `Predicate` 或者你自定义的接口）。
>  - 这个接口充当了 Lambda 的“身份证明”。没有这个接口，Java 编译器就不知道如何存储和调用这段代码。

- **定义**：只包含**一个抽象方法**的接口。
- **注解**：通常使用 `@FunctionalInterface` 标记（非强制，但推荐）。
- **常见接口**：`Runnable`, `Comparator`, 以及 Java 8 新增的 `java.util.function` 包下的 `Predicate`, `Consumer`, `Function`, `Supplier`。

#### 四种系统预定义函数式接口 - [示例代码](https://github.com/Supremes/blog_demo_application/blob/master/src/main/java/org/dododo/StreamDemo.java)
#####  1. Consumer (消费者)
> **口诀：只吃不吐（有去无回）**

- **作用**：接收一个参数，进行处理，**不返回任何值**。
- **抽象方法**：`void accept(T t)`
- **适用场景**：打印日志、写入数据库、发送消息等“副作用”操作。
```Java
// 定义：接收一个 String，把它打印出来（没有返回值）
Consumer<String> printer = s -> System.out.println("Processing: " + s);

// 调用：
printer.accept("Hello World"); 
// 输出: Processing: Hello World
```
##### 2. Supplier (供给者)

> **口诀：无中生有（只吐不吃）**

- **作用**：不接收任何参数，**返回一个结果**。
- **抽象方法**：`T get()`
- **适用场景**：生成随机数、获取当前时间、懒加载对象、工厂模式。

**代码示例：**
```Java
// 定义：不接受参数，返回一个随机整数
Supplier<Integer> randomizer = () -> (int)(Math.random() * 100);

// 调用：
Integer num = randomizer.get();
System.out.println(num);
```

---

##### 3. Function (函数/转换者)

> **口诀：有去有回（加工处理）**

- **作用**：接收一个参数，经过处理后，**返回一个结果**。这是最经典的数学函数概念 $y = f(x)$。
- **抽象方法**：`R apply(T t)` (T 是输入类型，R 是输出类型)
- **适用场景**：类型转换（String 转 Integer）、对象提取（User 对象转 UserID）、数据处理。

**代码示例：**

```Java
// 定义：接收一个 String，返回它的长度 Integer
// Function<输入类型, 输出类型>
Function<String, Integer> lengthMapper = s -> s.length();

// 调用：
int len = lengthMapper.apply("Java8");
System.out.println(len); // 输出: 5
```

---

##### 4. Predicate (断言/裁判)

> **口诀：非黑即白（真假判断）**

- **作用**：接收一个参数，**返回一个布尔值 (boolean)**。
- **抽象方法**：`boolean test(T t)`
- **适用场景**：数据过滤（filter）、条件判断、权限检查。

**代码示例：**

```Java
// 定义：接收一个 String，判断它的长度是否大于 5
Predicate<String> isLongText = s -> s.length() > 5;

// 调用：
System.out.println(isLongText.test("Java"));   // false
System.out.println(isLongText.test("Java8_Lambda")); // true
```

---

##### 总结对比表 (Cheat Sheet)
针对 `Consumer`, `Function`, `Predicate` 提供了 "Bi" (Binary，二元) 版本：
1. **BiConsumer<T, U>**：接收两个参数，无返回值。
    - _比如：把 Key 和 Value 放入 Map。_
2. **BiFunction<T, U, R>**：接收两个参数 (T, U)，返回一个结果 (R)。
    - _比如：两个整数相加 `(a, b) -> a + b`。_
3. **BiPredicate<T, U>**：接收两个参数，返回 boolean。
    - _比如：判断两个字符串是否相等。_
_(注：Supplier 不需要 Bi 版本，因为它本身就不接受参数)_

| **接口名**            | **输入参数** | **返回值** | **方法名**     | **核心逻辑** | **典型应用**           |
| ------------------ | -------- | ------- | ----------- | -------- | ------------------ |
| **Consumer<T>**    | T        | void    | `accept(t)` | **消费**数据 | `forEach` 打印、保存    |
| **Supplier<T>**    | 无        | T       | `get()`     | **提供**数据 | `generate` 生成、工厂方法 |
| **Function<T, R>** | T        | R       | `apply(t)`  | **转换**数据 | `map` 转换、提取字段      |
| **Predicate<T>**   | T        | boolean | `test(t)`   | **判断**数据 | `filter` 过滤、验证     |
## Method Reference - 方法引用

>  方法引用是 Lambda 表达式的**语法糖**（Syntactic Sugar）。如果你的 Lambda 表达式仅仅是**调用一个已经存在的方法**，那么你可以直接使用方法引用来替代 Lambda。

#### 语法格式
```Java
类名或对象名::方法名
```

#### 例子
```Java
// Lamba
Function<String, Integer> func = input -> Integer.parseInt(input)

// 方法引用
Function<String, Integer> ref = Integer::parseInt;
```

- **Lambda** 是为了让我们可以把函数当作参数传递，摆脱繁琐的匿名内部类。
- **方法引用** 是在 Lambda 的基础上，如果逻辑只是“调用一个已有的方法”，则进一步简化代码。

## Supplier

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

## Stream API

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

## Others

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

# Java 17 新特性
### 1. 文本块 (Text Blocks)

> **解决痛点**：在 Java 代码中拼接 JSON、SQL 或 HTML 字符串简直是噩梦（需要大量的 `+` 号和转义字符 `\"`）。

- **Java 13/15 引入**
- 使用三个双引号 `"""` 包裹。

**Java 8 写法：**

Java

```
String json = "{\n" +
              "  \"name\": \"Java\",\n" +
              "  \"age\": 17\n" +
              "}";
```

**Java 17 写法：**

Java

```
String json = """
              {
                "name": "Java",
                "age": 17
              }
              """;
// 所见即所得，自动处理缩进，无需手动转义引号
```

---
### 2. Record 类 (Records)

> **解决痛点**：为了写一个简单的 DTO (数据传输对象)，需要写构造器、Getter、`equals()`、`hashCode()`、`toString()`，或者依赖 Lombok。

- **Java 14/16 引入**
- **Record** 是一种特殊的类，它是**不可变 (Immutable)** 的，专门用于承载数据。

**Java 8 写法 (需要 Lombok 或手动写一大堆)：**

Java

```
public class Point {
    private final int x;
    private final int y;

    public Point(int x, int y) { 
        this.x = x; 
        this.y = y; 
    }
    // 还要写 getter, equals, hashCode, toString...
}
```

**Java 17 写法：**

Java

```
// 一行代码搞定！
// 自动生成：构造器、x() 和 y() 访问方法（注意不叫 getX）、equals、hashCode、toString
public record Point(int x, int y) {}
```

|**特性**|**Lombok @Data**|**Java 17 Record**|
|---|---|---|
|**本质**|代码生成工具 (Annotation Processor)|Java 语言特性 (Class 的变体)|
|**可变性**|**Mutable** (有 Setters)|**Immutable** (无 Setters, 全 final)|
|**继承**|可以继承/被继承|**不可继承** (隐式 final)|
|**访问器命名**|`getName()`|`name()`|
|**无参构造器**|默认有 (或通过 `@NoArgsConstructor`)|**默认无** (只有全参构造器)|
|**框架支持**|100% 支持 (JavaBean 规范)|需要较新框架支持 (Jackson 2.12+, Spring 5.3+)|
|**最佳用途**|**JPA Entity (实体类)**|**DTO, VO, Config, Map Key**|
---

### 3. Switch 表达式 (Switch Expressions)

> **解决痛点**：旧的 switch 语法繁琐，容易漏写 `break` 导致 bug，且不能直接作为返回值赋值给变量。

- **Java 12/14 引入**
- 支持 `->` 箭头语法，无需 `break`。

**Java 8 写法：**

Java

```
String day = "MONDAY";
int num;
switch (day) {
    case "MONDAY":
    case "FRIDAY":
    case "SUNDAY":
        num = 6;
        break;
    case "TUESDAY":
        num = 7;
        break;
    default:
        num = 0;
}
```

**Java 17 写法：**

Java

```
// 直接返回值，逻辑清晰，无 break
int num = switch (day) {
    case "MONDAY", "FRIDAY", "SUNDAY" -> 6;
    case "TUESDAY" -> 7;
    default -> 0;
};
```

---

### 4. instanceof 模式匹配 (Pattern Matching for instanceof)

> **解决痛点**：每次判断完 `instanceof`，还得强制类型转换一次，非常啰嗦。

- **Java 14/16 引入**

**Java 8 写法：**

Java

```
Object obj = "Hello";
if (obj instanceof String) {
    String s = (String) obj; // 必须强转
    System.out.println(s.length());
}
```

**Java 17 写法：**

Java

```
Object obj = "Hello";
// 如果是 String，直接转为变量 s，大括号内直接用
if (obj instanceof String s) {
    System.out.println(s.length());
}
```

---

### 其他重要更新 (一句话带过)

1. **var 关键字 (Java 10)**：局部变量类型推断。
    
    - `var list = new ArrayList<String>();` （编译器自动推断 list 是 ArrayList 类型）。
        
2. **密封类 Sealed Classes (Java 15/17)**：
    
    - 允许你控制**谁可以继承我**。
    - `public sealed class Shape permits Circle, Square {}`
    - 这对于编写严谨的领域模型或框架非常有用。
        
3. **更有用的 NullPointerException (Java 14)**：
    
    - 以前只报 NPE，不告诉你是哪个对象空了。
    - 现在会提示：`Cannot invoke "String.length()" because "name" is null`。
        
4. **Stream.toList() (Java 16)**：
    
    - 以前：`.collect(Collectors.toList())`
    - 现在：`.toList()` (注意：这个返回的是不可变 List)。

---

### 总结：为什么要升 Java 17？

|**特性**|**影响**|
|---|---|
|**Record**|**干掉 DTO 样板代码**，甚至可能不再需要 Lombok 的 `@Data`。|
|**Text Blocks**|**SQL/JSON 拼接神器**，代码可读性提升 10 倍。|
|**Switch 表达式**|逻辑更紧凑，减少 Bug。|
|**性能**|G1 垃圾回收器优化，以及 **ZGC** (低延迟 GC) 的成熟，应用吞吐量更高。|
|**Spring Boot 3**|**强制要求** Java 17+。|

# Java 21 新特性

Java 17 是目前许多企业应用的基准版本（LTS，长期支持版），但在它之后，Java 保持了每六个月发布一次的节奏。

目前最重要的里程碑是 **Java 21 (LTS)**。对于大多数开发者来说，从 17 升级的下一站就是 21。Java 22 和 23 则是后续的特性版本。

以下是 Java 17 之后的主要核心变化，按**重要性**和**功能领域**分类介绍：

---

### 1. 核心变革：Project Loom (并发能力的飞跃)

这是自 Java 5 引入 `java.util.concurrent` 以来最大的并发模型变革。

#### **虚拟线程 (Virtual Threads)** - _Java 21 正式发布_

这是 Spring Boot 3.2+ 性能起飞的关键。

- **痛点：** 以前的 Java 线程（Platform Thread）直接映射到操作系统的内核线程，创建成本高，数量受限（通常几千个）。
- **变革：** 虚拟线程由 JVM 管理，极其轻量级，可以轻松创建**数百万个**。
- **场景：** 高并发、I/O 密集型任务（如 Web 服务器处理大量请求）。
- **代码示例：**
 ```Java
    // 以前：使用线程池限制数量
    // 现在：可以直接为每个任务创建一个虚拟线程
    try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
        IntStream.range(0, 10_000).forEach(i -> {
            executor.submit(() -> {
                Thread.sleep(Duration.ofSeconds(1));
                return i;
            });
        });
    }
 ```

#### **结构化并发 (Structured Concurrency)** - _Preview 阶段_

旨在简化多线程编程，将相关的一组任务视为单个工作单元，从而简化错误处理和取消操作。

---

### 2. 语法糖与开发体验：Project Amber (让代码更简洁)

这一系列更新旨在减少样板代码，让 Java 写起来更像现代语言（如 Kotlin 或 Scala）。

#### **模式匹配增强 (Pattern Matching)** - _Java 21 正式发布_

`switch` 语句现在极其强大，支持类型匹配和守卫条件。

- **代码示例：**
    ```Java
    static String formatter(Object obj) {
        return switch (obj) {
            case Integer i -> String.format("int %d", i);
            case Long l    -> String.format("long %d", l);
            case Double d  -> String.format("double %f", d);
            case String s  -> String.format("String %s", s);
            case null      -> "It's null"; // 直接处理 null
            default        -> obj.toString();
        };
    }
    ```

#### **记录模式 (Record Patterns)** - _Java 21 正式发布_

可以直接在 `instanceof` 或 `switch` 中拆解 Record 对象。

- **代码示例：**
    
    ```Java
    record Point(int x, int y) {}
    
    void printSum(Object obj) {
        // 直接解构 Point 为 x 和 y
        if (obj instanceof Point(int x, int y)) {
            System.out.println(x + y);
        }
    }
    ```

#### **未命名变量与模式 (Unnamed Variables)** - _Java 22 正式发布_

使用下划线 `_` 表示你不关心的变量（类似 Go 或 Python）。

- **场景：** 异常捕获、Lambda 参数、循环变量。
- **代码示例：**
    ```Java
    try {
        int number = Integer.parseInt(string);
    } catch (NumberFormatException _) { // 我不关心异常变量 e，直接用 _
        System.out.println("Not a number");
    }
    ```

---

### 3. API 库的改进

#### **序列化集合 (Sequenced Collections)** - _Java 21 正式发布_

终于统一了 List、Deque、Set 的访问顺序 API。以前获取“最后一个元素”在不同集合中写法都不一样，现在统一了。

- **新接口：** `SequencedCollection`, `SequencedSet`, `SequencedMap`
- **新方法：**
    - `getFirst()` / `getLast()`
    - `addFirst()` / `addLast()`
    - `removeFirst()` / `removeLast()`
    - `reversed()` (返回反转视图)

#### **简单的 Web 服务器 (Simple Web Server)** - _Java 18 正式发布_

类似于 Python 的 `python -m http.server`。

- **命令：** `jwebserver`
- **用途：** 快速搭建静态文件服务，用于测试或原型开发。

---

### 4. 性能与底层设施

#### **分代 ZGC (Generational ZGC)** - _Java 21 正式发布_

ZGC 是低延迟垃圾收集器。分代 ZGC 将堆分为年轻代和老年代，显著减少了 CPU 消耗。

- **特点：** 即使是 TB 级的堆内存，暂停时间也能控制在 1ms 左右。

#### **默认 UTF-8** - _Java 18 正式发布_

所有操作系统上的默认字符集统一为 UTF-8。这解决了 Windows 上中文乱码的许多历史遗留问题。

---

### 总结：你应该关注哪个版本？

| **版本**         | **状态**  | **关键点**                    | **建议**                                 |     |
| -------------- | ------- | -------------------------- | -------------------------------------- | --- |
| **Java 17**    | LTS     | 当前主流                       | 也就是你现在的基准。                             |     |
| **Java 21**    | **LTS** | **虚拟线程、ZGC、模式匹配**          | **强烈建议升级的目标版本。** Spring Boot 3.x 完美支持。 |     |
| **Java 22/23** | Non-LTS | `super()`前置语句、Markdown文档注释 | 尝鲜版本，生产环境通常跳过。                         |     |

下一步建议：

考虑到您对 Spring Security 和 OAuth 的关注，升级到 Java 21 配合 Spring Boot 3.2+ 可以利用虚拟线程大幅提升高并发下的身份验证处理能力（因为 Auth 请求通常涉及大量 I/O 等待）。

您想看一段 **Spring Boot 3 中启用虚拟线程** 的配置示例吗？

# VarHandle

这不仅是一个 API 的替换，更是 Java **内存模型（JMM）** 和 **底层生态** 的一次重大升级。

`sun.misc.Unsafe` 长期以来被称为 Java 的“后门”或“黑魔法”，而 `java.lang.invoke.VarHandle`（JDK 9 引入，JDK 17 中被 AQS 全面采用）则是官方为了终结这个混乱时代而推出的**标准化、安全且性能更强的**替代方案。

以下从 **安全性**、**易用性** 和 **性能（内存屏障控制）** 三个维度详细解析为什么 `VarHandle` 优于 `Unsafe`。

---

### 1. 身份与合法性：从“黑户”到“正规军”

#### 💀 `sun.misc.Unsafe`：危险的“黑户”

- **非标准 API：** 它属于 `sun.misc` 包，意味着它不是 Java 标准库的一部分（Not Java SE API）。Oracle 随时可能在未通知的情况下修改或删除它（虽然因为用的人太多，一直不敢删）。
- **破坏封装：** 它可以随意修改 `private` 字段，甚至直接操作堆外内存。如果不小心写错了地址（Offset），会导致 JVM 直接崩溃（Segmentation Fault），没有任何报错提示。
- **使用繁琐：** 你必须先通过反射获取 `Unsafe` 实例（因为它不让普通代码调用），然后手动计算字段在内存中的**偏移量（Offset）**。

Java

```
// Unsafe 的典型用法（JDK 8 AQS 风格）
private static final Unsafe unsafe = Unsafe.getUnsafe();
private static final long stateOffset;

static {
    try {
        // 必须手动计算偏移量，非常底层
        stateOffset = unsafe.objectFieldOffset(Node.class.getDeclaredField("waitStatus"));
    } catch (Exception ex) { throw new Error(ex); }
}

// 调用时传入对象、偏移量、期望值、新值
unsafe.compareAndSwapInt(node, stateOffset, 0, 1);
```

#### 🛡️ `VarHandle`：持证上岗的“特种兵”

- **标准 API：** 位于 `java.lang.invoke` 包，是官方支持的标准。
- **类型安全：** 它持有变量的引用（引用变量本身，而非内存地址）。由于它知道变量的类型，编译器和 JVM 可以进行类型检查，避免将 `int` 误写入 `long` 字段。
- **封装性：** 它的创建依赖于 `MethodHandles.Lookup`，这意味着如果你的类没有权限访问某个私有字段，你也无法为该字段创建 `VarHandle`。

Java

```
// VarHandle 的典型用法（JDK 17 AQS 风格）
private static final VarHandle STATUS;

static {
    try {
        MethodHandles.Lookup l = MethodHandles.lookup();
        // 直接通过类和字段名获取，清晰明了
        STATUS = l.findVarHandle(Node.class, "status", int.class);
    } catch (Exception ex) { throw new Error(ex); }
}

// 调用时像方法一样自然
STATUS.compareAndSet(node, 0, 1);
```

---

### 2. 性能核心：精细化的内存屏障 (Memory Fences)

这是 `VarHandle` 最硬核的优势，也是 Doug Lea 在 AQS 中引入它的主要动力。

背景：

Unsafe 的 CAS 操作（如 compareAndSwapInt）和 volatile 读写，在底层对应的是最强级别的内存屏障（Full Fence / StoreLoad Barrier）。

这就像：每次过马路都强制把整条街封锁，虽然安全，但效率低。

VarHandle 的改进：

引入了类似 C++11 原子操作的精细化访问模式。它允许开发者根据需要选择“更弱”但够用的内存屏障，从而在 ARM 等弱内存模型架构上获得显著的性能提升。

`VarHandle` 提供了 3 层访问模式：

1. **Plain (普通读写)：**
    
    - 等同于普通变量读写，无内存屏障，不保证可见性。
    - API: `get`, `set`
        
2. **Opaque (不透明)：**
    
    - 比 Plain 强，保证程序顺序，但不保证跨线程的立即可见性（禁止编译器乱序优化，但允许 CPU 缓存延迟）。
    - API: `getOpaque`, `setOpaque`
        
3. **Acquire/Release (获取/释放)：**
    
    - **Acquire (读)：** 保证读之后的代码不会重排序到读之前。
    - **Release (写)：** 保证写之前的代码不会重排序到写之后。
    - 这正是 lock/unlock 的语义，比 `volatile` 的开销小。
    - API: `getAcquire`, `setRelease`
        
4. **Volatile (全屏障)：**
    
    - 最强级别，等同于 `Unsafe` 的旧行为。
    - API: `getVolatile`, `setVolatile`

在 AQS 中的应用场景：

在 JDK 17 的 AQS 源码中，你会发现大量使用了 setRelease 而不是 compareAndSet（CAS）。

- **场景：** 释放锁时，修改 `state` 变量。
- **JDK 8 (Unsafe):** 只能用 `volatile` 写，强行刷缓存，开销大。
- **JDK 17 (VarHandle):** 使用 `STATE.setRelease(this, 0)`。这告诉 CPU：“我只要求之前的操作对后续可见即可，不需要加全屏障”。这在 x86 上区别不大，但在 **ARM 架构（也就是现在的 Mac M1/M2/M3 和大量服务器）** 上，指令开销大幅降低。

---

### 3. JVM 优化与未来维护

#### JIT 编译器的“亲儿子”

- **Unsafe：** JVM 只能把 `Unsafe` 的方法作为“固有方法（Intrinsics）”硬编码在编译器里。每当 CPU 架构更新，JVM 开发者就要痛苦地去维护这些汇编代码。
- **VarHandle：** 设计之初就考虑了 JIT 友好性。它的签名是多态的（Polymorphic Signature），JVM 可以在运行时像内联普通方法一样极其高效地内联 `VarHandle` 的操作，甚至将其优化为单条 CPU 指令。

#### Project Valhalla 的铺垫

Java 正在进行大规模的值类型（Value Types）改革（Project Valhalla）。`Unsafe` 是基于对象头和偏移量的，它无法很好地支持未来的值类型（因为值类型可能没有对象头，或者被扁平化在数组中）。`VarHandle` 是为未来设计的，能够无缝兼容值类型。

---

### 总结对比

|**特性**|**Unsafe (JDK 8)**|**VarHandle (JDK 17+)**|**胜出者**|
|---|---|---|---|
|**API 类型**|内部私有 (`sun.misc`)|标准公开 (`java.lang.invoke`)|✅ VarHandle|
|**内存定位**|裸指针/偏移量 (Offset)|类型化引用 (Typed Reference)|✅ VarHandle|
|**类型检查**|无 (写错就 Crash)|有 (运行时/编译期检查)|✅ VarHandle|
|**内存屏障**|仅支持 Volatile (重)|支持 Opaque/Acquire/Release (细粒度)|✅ VarHandle|
|**ARM 性能**|较低 (过度屏障)|**极高** (按需屏障)|✅ VarHandle|
|**学习曲线**|陡峭 (黑魔法)|中等 (需要理解内存模型)|平手|

### 结论

Java 17 中的 AQS 抛弃 `Unsafe` 拥抱 `VarHandle`，不是简单的语法糖替换，而是为了：

1. **更强的安全性**（不再怕写错 Offset 炸 JVM）。
2. **更细粒度的并发控制**（在 ARM 架构服务器日益普及的今天，这一点对性能至关重要）。
3. **拥抱未来**（为 Java 后续的版本演进扫清障碍）。

作为开发者，给你的建议是：

虽然你在业务代码中很少直接写 Unsafe 或 VarHandle，但理解这一点能让你在面试中脱颖而出：“我知道 Java 17 性能提升的一个底层原因是在并发包中引入了 VarHandle，利用更轻量级的内存屏障（Acquire/Release）优化了在 ARM 架构下的锁性能。”