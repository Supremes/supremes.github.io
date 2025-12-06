---
title: Java
tags:
  - 面试
categories:
  - 后端开发
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/JAVA8.webp
hidden: false
updated: 2025-12-06 10:42
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

## Java 17 新特性
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