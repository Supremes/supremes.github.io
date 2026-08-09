---
title: Java基础高频考点
date: 2026-08-09
tags:
  - 面试
  - Java
---
# Java 基础高频考点

> 目标：每个主题先给一句话结论，再给 30 秒口述，最后补最容易被追问的坑。

## 先背这 7 句

- `String` 不可变，频繁拼接优先 `StringBuilder`。
- `==` 比较地址，`equals()` 比较逻辑相等；重写 `equals()` 必须同时重写 `hashCode()`。
- Java 泛型是**编译期约束 + 运行期擦除**。
- checked exception 强迫你显式处理，unchecked exception 更多是编程错误。
- 反射解决“运行期拿类、字段、方法”的问题；注解只是元数据，生效靠框架解析。
- BIO 面向流、通常一连接一线程；NIO 面向 `Buffer` / `Channel` / `Selector`。
- Java 原生序列化能用但不适合跨服务协议，线上更常见是 JSON / Protobuf。

## String

### 一句话结论

`String` 的核心价值是**不可变**，因此天然适合做常量、缓存 key、配置值。

### 30 秒口述

`String` 是 final 类，内部存储不对外暴露，可保证对象创建后内容不变，所以线程安全、可缓存 hash、适合放进字符串常量池。频繁拼接不要反复 `+`，因为会产生很多中间对象；循环里优先用 `StringBuilder`。

### 关键追问 / 坑

- `String` 常量拼接会在编译期折叠，变量拼接才会走运行期对象创建。
- `intern()` 是把字符串放进常量池 / 复用池中引用，别把它讲成“任何场景都提速”。
- `StringBuilder` 线程不安全，`StringBuffer` 线程安全但一般不默认选。

## equals() / hashCode()

### 一句话结论

只要对象会作为 `HashMap` key 或 `HashSet` 元素，就必须同时考虑 `equals()` 和 `hashCode()`。

### 30 秒口述

`equals()` 决定“逻辑上是不是同一个对象”，`hashCode()` 决定它先进哪个桶。规则是：如果两个对象 `equals()` 为 true，它们的 `hashCode()` 必须相同；反过来 `hashCode()` 相同，不代表 `equals()` 一定相同。只重写一个不重写另一个，哈希容器就会出错。

### 关键追问 / 坑

- `==` 比的是引用地址，除非是基本类型，否则不要混着说。
- 作为 key 的字段最好保持**不可变**，否则放进 `HashMap` 后可能再也取不出来。
- `Objects.equals()` / `Objects.hash()` 只是辅助工具，不是底层原理。

## 泛型

### 一句话结论

泛型的目的不是炫技，而是把类型错误尽量前移到**编译期**。

### 30 秒口述

Java 泛型主要用于类型约束和减少强转，底层实现是类型擦除：运行期不会真的存在 `List<String>` 和 `List<Integer>` 两套不同类。因为擦除存在，所以你不能直接 `new T()`，也不能创建 `new List<String>[10]`。面试高频还有 PECS：`? extends T` 适合读，`? super T` 适合写。

### 关键追问 / 坑

- `List<Object>` 不是 `List<String>` 的父类型，泛型默认**不协变**。
- `<?>` 表示“某种未知类型”，能读成 `Object`，但基本不能安全写入。
- 框架里想保留泛型信息，通常要借助 `TypeReference`、`ParameterizedType` 之类的手段。

## 异常

### 一句话结论

异常体系的重点不是背类图，而是知道**谁该处理、在哪一层处理**。

### 30 秒口述

Java 异常分 checked 和 unchecked。checked exception 要么捕获要么声明抛出，适合 IO 这类调用方可恢复问题；`RuntimeException` 通常代表编程错误或非法状态。工程上应遵循“底层尽量带上下文抛出，上层统一转换/记录”，不要到处 `catch (Exception)` 然后吞掉。

### 关键追问 / 坑

- `finally` 适合清理资源，但不要在 `finally` 里 `return`，会吞掉原异常。
- 资源关闭优先 `try-with-resources`，比手写 `finally` 更稳。
- 自定义业务异常时，先想清楚是要调用方恢复，还是只是表达非法状态。

## 反射 / 注解

### 一句话结论

反射给了框架运行期操作类结构的能力，注解负责声明意图，二者组合成 Spring / JPA 这类框架的基础。

### 30 秒口述

反射可以在运行时拿到类、构造器、字段、方法并调用，带来了灵活性，也带来了性能损耗和封装破坏风险，所以框架通常会做缓存。注解本身只是元数据，真正有意义的是“谁来读它”。面试里常被追问注解生命周期：`SOURCE`、`CLASS`、`RUNTIME`，只有 `RUNTIME` 才能通过反射读取。

### 关键追问 / 坑

- 反射“慢”不是不能用，而是不要在热点路径里反复无缓存调用。
- 动态代理是反射常见延伸：JDK 动态代理基于接口，CGLIB 基于继承。
- `setAccessible(true)` 能破封装，但也要注意安全和模块系统限制。

## IO / NIO

### 一句话结论

BIO 适合简单顺序读写，NIO 适合高并发连接和更细粒度的缓冲区控制。

### 30 秒口述

传统 IO 以 `InputStream` / `OutputStream`、`Reader` / `Writer` 为核心，通常是阻塞式；NIO 的核心是 `Buffer`、`Channel`、`Selector`，可以用少量线程管理大量连接。别把 NIO 讲成“永远更快”，它是模型更复杂、适合高并发网络编程，不是所有文件读写都该上 NIO。

### 关键追问 / 坑

- 字节流处理二进制，字符流处理文本编码。
- `ByteBuffer` 经典动作：`put -> flip -> get -> clear/compact`。
- 追问到零拷贝时，可提 `FileChannel.transferTo/transferFrom`。

## 序列化

### 一句话结论

序列化的本质是**把对象状态变成可传输 / 可存储格式**，而不是 Java 面向对象的“魔法”。

### 30 秒口述

Java 原生序列化靠 `Serializable`，会把对象图按协议写出；`serialVersionUID` 用来控制版本兼容；`transient` 字段不会被序列化。但在现代服务里，Java 原生序列化通常不作为 RPC 首选，因为性能、兼容性和安全性都不够理想，更常见是 JSON、Protobuf、Avro 这类显式协议。

### 关键追问 / 坑

- 不显式写 `serialVersionUID`，类结构变化后可能反序列化失败。
- 敏感字段要用 `transient` 或改走显式 DTO。
- 不要反序列化不可信数据，Java 原生反序列化有安全风险。

## 面试 Checklist

- 能用 30 秒讲清 `String` 为什么不可变，以及 `+` 和 `StringBuilder` 的取舍。
- 能讲清 `equals()` / `hashCode()` 的契约和哈希容器后果。
- 能解释泛型擦除、PECS、为什么不能 `new T()`。
- 能说明 checked / unchecked exception 的分工和 `try-with-resources`。
- 能说清反射、注解、动态代理在框架中的角色。
- 能区分 BIO / NIO，并说明什么场景才值得上 `Selector`。
- 能说明为什么线上更少直接用 Java 原生序列化。
