---
title: Java Stream API 常用方法速查
tags:
  - java
  - stream
categories:
  - Java
hidden: true
updated: '2026-04-09 14:54'
abbrlink: 39c40f71
---

# Java Stream API 常用方法速查

> Java 8 引入的声明式集合处理工具。核心思想：**用链式操作替代 for 循环**。

---

## 基础概念

```java
List<String> names = Arrays.asList("Alice", "Bob", "Charlie");

names.stream()              // 1. 创建流（数据源）
    .filter(s -> s.length() > 3)  // 2. 中间操作（惰性，可链式叠加）
    .map(String::toUpperCase)     // 2. 中间操作
    .collect(Collectors.toList()); // 3. 终端操作（触发执行，返回结果）
```

| 概念   | 说明                                  |
| ---- | ----------------------------------- |
| 中间操作 | 返回新 Stream，可继续链式调用。**惰性**，不调终端操作不执行 |
| 终端操作 | 触发整条链执行，返回最终结果。一个 Stream 只能有一个终端操作  |
| 惰性求值 | 中间操作只是声明"要做什么"，直到终端操作才真正执行          |

---

## 创建流

```java
// 从集合
List<String> list = Arrays.asList("a", "b", "c");
Stream<String> s1 = list.stream();

// 从数组
String[] arr = {"a", "b", "c"};
Stream<String> s2 = Arrays.stream(arr);

// 直接指定元素
Stream<String> s3 = Stream.of("a", "b", "c");

// 空流
Stream<String> s4 = Stream.empty();

// 无限流（配合 limit 使用）
Stream<Integer> s5 = Stream.iterate(0, n -> n + 2);  // 0, 2, 4, 6, ...
Stream<Double> s6 = Stream.generate(Math::random);    // 随机数流

// 数值范围
IntStream.range(1, 5);       // 1, 2, 3, 4（不含 5）
IntStream.rangeClosed(1, 5); // 1, 2, 3, 4, 5（含 5）
```

---

## 中间操作

### filter — 筛选

保留满足条件的元素。

```java
List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5, 6);

nums.stream()
    .filter(n -> n > 3)
    .collect(Collectors.toList());
// [4, 5, 6]

// 多条件组合
nums.stream()
    .filter(n -> n > 2 && n < 6)
    .collect(Collectors.toList());
// [3, 4, 5]
```

### map — 逐个变换

对每个元素应用函数，返回变换后的新流。

```java
List<String> names = Arrays.asList("alice", "bob", "charlie");

// 转大写
names.stream()
    .map(String::toUpperCase)
    .collect(Collectors.toList());
// ["ALICE", "BOB", "CHARLIE"]

// 取长度
names.stream()
    .map(String::length)
    .collect(Collectors.toList());
// [5, 3, 7]

// 对象取字段
users.stream()
    .map(User::getName)
    .collect(Collectors.toList());
```

### flatMap — 拍平嵌套

每个元素映射为一个流，然后合并成一个流。解决 `Stream<Stream<T>>` 嵌套问题。

```java
// 场景：每个用户有多个订单
List<User> users = ...;

// map 得到嵌套结构 Stream<List<Order>>
users.stream().map(User::getOrders);
// [[订单1, 订单2], [订单3], [订单4, 订单5]]

// flatMap 拍平为 Stream<Order>
users.stream()
    .flatMap(u -> u.getOrders().stream())
    .collect(Collectors.toList());
// [订单1, 订单2, 订单3, 订单4, 订单5]

// 字符串拆分拍平
List<String> lines = Arrays.asList("hello world", "foo bar");
lines.stream()
    .flatMap(line -> Arrays.stream(line.split(" ")))
    .collect(Collectors.toList());
// ["hello", "world", "foo", "bar"]
```

### sorted — 排序

```java
List<Integer> nums = Arrays.asList(3, 1, 4, 1, 5);

// 自然排序（升序）
nums.stream().sorted().collect(Collectors.toList());
// [1, 1, 3, 4, 5]

// 降序
nums.stream()
    .sorted(Comparator.reverseOrder())
    .collect(Collectors.toList());
// [5, 4, 3, 1, 1]

// 按对象字段排序
users.stream()
    .sorted(Comparator.comparing(User::getAge))           // 按年龄升序
    .sorted(Comparator.comparing(User::getAge).reversed()) // 按年龄降序
    .collect(Collectors.toList());
```

### distinct — 去重

```java
Arrays.asList(1, 1, 2, 2, 3).stream()
    .distinct()
    .collect(Collectors.toList());
// [1, 2, 3]
```

### limit / skip — 截取

```java
Stream.of(1, 2, 3, 4, 5)
    .skip(2)    // 跳过前 2 个
    .limit(2)   // 只取 2 个
    .collect(Collectors.toList());
// [3, 4]
```

### peek — 查看（调试用）

不改变流，只是"偷看"每个元素，常用于调试。

```java
nums.stream()
    .filter(n -> n > 2)
    .peek(n -> System.out.println("过滤后: " + n))
    .map(n -> n * 10)
    .peek(n -> System.out.println("变换后: " + n))
    .collect(Collectors.toList());
```

---

## 终端操作

### collect — 收集结果

最常用的终端操作，把流转成集合或其他数据结构。

```java
// 转 List
stream.collect(Collectors.toList());

// 转 Set（自动去重）
stream.collect(Collectors.toSet());

// 转 Map
users.stream().collect(Collectors.toMap(
    User::getId,      // key
    User::getName      // value
));

// 用逗号拼接字符串
names.stream().collect(Collectors.joining(", "));
// "Alice, Bob, Charlie"

// 按条件分组
users.stream().collect(Collectors.groupingBy(User::getDepartment));
// {IT=[user1, user2], HR=[user3]}

// 按条件分区（true/false 两组）
users.stream().collect(Collectors.partitioningBy(u -> u.getAge() > 30));
// {true=[user1], false=[user2, user3]}
```

### forEach — 逐个消费

```java
names.stream().forEach(System.out::println);

// 注意：forEach 没有返回值，不能继续链式调用
```

### reduce — 聚合成单个值

```java
List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5);

// 求和
nums.stream().reduce(0, Integer::sum);        // 15

// 求最大值
nums.stream().reduce(Integer::max);           // Optional[5]

// 字符串拼接
names.stream().reduce("", (a, b) -> a + b);  // "AliceBobCharlie"
```

**reduce 执行过程**：

```
reduce(0, Integer::sum)

  初始值: 0
  第1步: 0 + 1 = 1
  第2步: 1 + 2 = 3
  第3步: 3 + 3 = 6
  第4步: 6 + 4 = 10
  第5步: 10 + 5 = 15
```

### count / min / max — 聚合统计

```java
long count = nums.stream().filter(n -> n > 3).count();  // 2

Optional<Integer> max = nums.stream().max(Integer::compareTo);  // Optional[5]
Optional<Integer> min = nums.stream().min(Integer::compareTo);  // Optional[1]
```

### anyMatch / allMatch / noneMatch — 条件判断

```java
List<Integer> nums = Arrays.asList(1, 2, 3, 4, 5);

nums.stream().anyMatch(n -> n > 4);   // true（存在 > 4 的）
nums.stream().allMatch(n -> n > 0);   // true（全部 > 0）
nums.stream().noneMatch(n -> n > 10); // true（没有 > 10 的）
```

### findFirst / findAny — 取元素

```java
Optional<String> first = names.stream()
    .filter(s -> s.startsWith("A"))
    .findFirst();  // Optional["Alice"]

// findAny 在并行流中可能返回任意匹配的元素，性能更好
Optional<String> any = names.parallelStream()
    .filter(s -> s.length() > 3)
    .findAny();
```

### toArray — 转数组

```java
String[] arr = names.stream()
    .filter(s -> s.length() > 3)
    .toArray(String[]::new);
```

---

## 数值流（避免装箱开销）

处理基本类型时，用专用流避免 `int ↔ Integer` 的自动装箱。

```java
// IntStream / LongStream / DoubleStream
int sum = IntStream.rangeClosed(1, 100).sum();  // 5050

// 对象流 → 数值流
double avg = users.stream()
    .mapToInt(User::getAge)
    .average()
    .orElse(0);

// 数值流特有方法
IntStream.of(1, 2, 3, 4, 5).sum();           // 15
IntStream.of(1, 2, 3, 4, 5).average();       // OptionalDouble[3.0]
IntStream.of(1, 2, 3, 4, 5).summaryStatistics();
// IntSummaryStatistics{count=5, sum=15, min=1, average=3.0, max=5}
```

---

## 并行流

```java
// 串行流
list.stream().map(...).collect(...);

// 并行流（自动多线程处理）
list.parallelStream().map(...).collect(...);

// 串行转并行
list.stream().parallel().map(...).collect(...);
```

**注意事项**：
- 数据量小（< 1万）时并行流反而更慢（线程调度开销）
- 操作必须是**无状态**的，不能依赖共享变量
- `ArrayList` 并行性能好（随机访问），`LinkedList` 差（顺序访问）

---

## 实战组合示例

### 1. 统计词频

```java
String text = "hello world hello java world hello";

Map<String, Long> wordCount = Arrays.stream(text.split(" "))
    .collect(Collectors.groupingBy(
        w -> w,
        Collectors.counting()
    ));
// {hello=3, world=2, java=1}
```

### 2. 取每个部门薪资最高的员工

```java
Map<String, Optional<Employee>> topByDept = employees.stream()
    .collect(Collectors.groupingBy(
        Employee::getDepartment,
        Collectors.maxBy(Comparator.comparing(Employee::getSalary))
    ));
```

### 3. 嵌套对象提取 + 去重

```java
// 取所有订单中不重复的商品名
List<String> productNames = orders.stream()
    .flatMap(order -> order.getItems().stream())
    .map(Item::getProductName)
    .distinct()
    .sorted()
    .collect(Collectors.toList());
```

### 4. 分页查询

```java
List<User> page = users.stream()
    .sorted(Comparator.comparing(User::getCreatedAt).reversed())
    .skip((pageNum - 1) * pageSize)
    .limit(pageSize)
    .collect(Collectors.toList());
```

### 5. CSV 行解析

```java
List<String[]> rows = Files.lines(Path.of("data.csv"))
    .skip(1)                           // 跳过表头
    .map(line -> line.split(","))       // 每行按逗号拆分
    .filter(cols -> cols.length >= 3)   // 过滤无效行
    .collect(Collectors.toList());
```

---

## 速查表

| 操作 | 类型 | 签名 | 用途 |
|------|------|------|------|
| `filter` | 中间 | `Stream<T> → Stream<T>` | 筛选 |
| `map` | 中间 | `Stream<T> → Stream<R>` | 逐个变换 |
| `flatMap` | 中间 | `Stream<T> → Stream<R>` | 拍平嵌套 |
| `sorted` | 中间 | `Stream<T> → Stream<T>` | 排序 |
| `distinct` | 中间 | `Stream<T> → Stream<T>` | 去重 |
| `limit` | 中间 | `Stream<T> → Stream<T>` | 取前 N 个 |
| `skip` | 中间 | `Stream<T> → Stream<T>` | 跳过前 N 个 |
| `peek` | 中间 | `Stream<T> → Stream<T>` | 调试查看 |
| `collect` | 终端 | `Stream<T> → R` | 收集为集合 |
| `forEach` | 终端 | `Stream<T> → void` | 逐个消费 |
| `reduce` | 终端 | `Stream<T> → T` | 聚合成单值 |
| `count` | 终端 | `Stream<T> → long` | 计数 |
| `min/max` | 终端 | `Stream<T> → Optional<T>` | 最小/最大 |
| `anyMatch` | 终端 | `Stream<T> → boolean` | 存在匹配 |
| `allMatch` | 终端 | `Stream<T> → boolean` | 全部匹配 |
| `findFirst` | 终端 | `Stream<T> → Optional<T>` | 取第一个 |
| `toArray` | 终端 | `Stream<T> → T[]` | 转数组 |
