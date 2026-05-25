---
title: JAXB 速通：写给 Spring Boot 开发者的指南
date: 2026-05-25 15:09:47
tags: []
categories:
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-05-25 15:10
---
老大，下面这份文档放在回复里输出（不创建文件，因为您前面规则里说过非显式要求不写 `.md` 文件；如果您想我保存成文件，告诉我路径即可）。整篇以 Spring Boot 开发者熟悉的 Jackson、Spring 容器、OpenAPI Generator 等概念做类比，把前文出现的名词全部串起来。

---

# JAXB 速通：写给 Spring Boot 开发者的指南

## 一、一句话定位

**JAXB ≈ XML 世界的 Jackson**。

| Jackson 干的事                                | JAXB 干的事                               |
| --------------------------------------------- | ----------------------------------------- |
| `ObjectMapper.writeValueAsString(obj)` → JSON | `Marshaller.marshal(obj, ...)` → XML      |
| `ObjectMapper.readValue(json, Foo.class)`     | `Unmarshaller.unmarshal(xml)` → Java 对象 |
| `@JsonProperty("name")`                       | `@XmlElement(name="name")`                |
| 注解驱动 + 反射                               | 注解驱动 + 反射                           |

Spring Boot 默认带 Jackson，所以你可能从没主动接触过它的"配置层"。JAXB 在 Spring Boot 里也是一样——**只要不写复杂场景，它就是隐身的**。

---

## 二、为什么 Spring Boot 开发者会"突然"遇到 JAXB

平时你可能根本不知道 JAXB 存在。但在这些场景，它会跳出来打你：

1. **对接 SOAP 服务**（WSDL、`<soap:Envelope>` 那一套）
2. **对接政企/银行/电信的标准 XSD**（保险 ACORD、医疗 HL7、税务接口、PKI 证书规范……）
3. **Spring Boot 2 升 3** —— `javax.xml.bind` 全部要换成 `jakarta.xml.bind`，老代码爆炸
4. **维护 10 年+ 的老项目** —— 凡是用 Apache CXF、Axis、JAX-WS 的，底层都靠 JAXB

→ 现代项目自己启新服务时基本用 JSON，不会主动选 XML。**遇到 JAXB 八成是历史包袱或外部约定**。

---

## 三、三层架构：用 Servlet 的方式理解

Spring Boot 开发者最熟悉的模式：**规范 / API / 实现**三层分离。

| 层             | Servlet 世界                        | JAXB 世界                                                                 |
| -------------- | ----------------------------------- | ------------------------------------------------------------------------- |
| 规范           | Servlet Spec / Jakarta Servlet Spec | JAXB Spec / Jakarta XML Binding Spec                                      |
| API（接口）    | `jakarta.servlet.*`                 | `jakarta.xml.bind.*`                                                      |
| 实现（运行时） | Tomcat / Jetty / Undertow           | **Glassfish JAXB**（`org.glassfish.jaxb:jaxb-runtime`）/ EclipseLink MOXy |

跟 Servlet 一样：
- 你的代码只 import API（`jakarta.xml.bind.Marshaller`）
- 运行时由实现类（Glassfish JAXB）真正干活
- 必须**API + 实现**都在 classpath，否则 `ClassNotFoundException`

Spring Boot 的 starter（如 `spring-boot-starter-web`）会按需把这两个 jar 一起拉进来，所以你平时感觉不到。

---

## 四、核心概念词典（Spring Boot 开发者翻译版）

### `XSD`（XML Schema Definition）
**类比**：OpenAPI 的 `openapi.yaml`、Protobuf 的 `.proto`。
**作用**：用 XML 写的"接口契约文件"，定义某个 XML 文档长什么样、哪些字段必填、类型是什么。
**何时遇到**：对方接口方甩给你一个 `.xsd` 让你"按这个生成代码"。

### `.xjb` 文件（JAXB Binding Customization）
**类比**：`openapi-generator` 的 `config.yaml`，或 Jackson 的 `Mixin`。
**作用**：你不想/不能改原始 `.xsd`，但又想定制生成出来的 Java 类（改包名、改类名、把某个 XSD 类型映射到你已有的 Java 类）——就写一个 `.xjb` 文件放在旁边。
**关键例子**：

```xml
<bindings scd="/type::gpki:csr">
    <javaType name="com.example.CsrParameter" />
</bindings>
```

意思："碰到 `csr` 这个 XSD 类型时，不要生成新类，直接复用我已有的 `CsrParameter`"。

### `XJC`（XML to Java Compiler）
**类比**：`openapi-generator-cli generate -i api.yaml -o ./src` 里的 generator 部分。
**作用**：吃 `.xsd`（+ 可选的 `.xjb`），吐 Java 类。**构建期工具**，不是运行时。
**通常如何调用**：通过 Maven/Gradle 插件触发，不会手动跑命令行。

### `JXC` / `schemagen`
**类比**：从 Java 类反向生成 OpenAPI spec。
**作用**：跟 XJC 反向，从 Java 类生成 `.xsd`。**几乎用不到**，知道有就行。

### `JAXBContext`
**类比**：`ObjectMapper`。
**作用**：JAXB 的入口对象，重量级、线程安全、应当复用单例。从它创建 `Marshaller` / `Unmarshaller`。

### `Marshaller` / `Unmarshaller`
**类比**：`ObjectMapper.writeValueAsString` / `readValue` 的具体执行器。
**注意**：**不是线程安全**，跟 `JAXBContext` 不同。

### `jaxb.index` 文件
**类比**：Spring 的 `META-INF/spring.factories`、Java 的 `META-INF/services`。
**作用**：放在某个包里的纯文本文件，列出"这个包里有哪些 JAXB 实体类"，让 `JAXBContext.newInstance("com.example.pkg")` 找得到它们。

---

## 五、构建工具：Maven/Gradle 插件

JAXB 的代码生成（XJC）必须靠构建插件，**Spring Boot starter 不管这一层**。

| 插件                                          | Maven/Gradle | 时代                 | 备注                          |
| --------------------------------------------- | ------------ | -------------------- | ----------------------------- |
| `jaxb2-maven-plugin`（mojohaus）              | Maven        | 老                   | 只支持 `javax` 命名空间       |
| `maven-jaxb2-plugin`（highsource）            | Maven        | 老但功能强           | 社区维护                      |
| `jaxb-maven-plugin` 4. x（glassfish）          | Maven        | **新**，支持 jakarta | 推荐                          |
| `org.unbroken-dome.xjc`                       | Gradle       | 常用                 | 配置简洁                      |
| 手写 ant task 调 `com.sun.tools.xjc.XJC2Task` | Gradle       | 老项目常见           | 你前面 xm-server 项目就是这种 |

**类比 Spring Boot 开发者熟悉的世界**：
- 这一层等同于 `openapi-generator-maven-plugin` 或 `protobuf-maven-plugin`
- 都是"构建期把 IDL 转成 Java 代码"的工具，套路一模一样

---

## 六、最大的坑：`javax` → `jakarta` 迁移

这是 Spring Boot 2 → 3 升级时**所有人**都会撞上的坑。

### 背景
Oracle 把 Java EE 捐给 Eclipse 基金会，要求所有包名从 `javax.*` 改成 `jakarta.*`。Spring Boot 3 起全面切换。

### JAXB 涉及的三个同步变更
**这三个必须同时改，改一半必出问题**：

| 维度                | 旧（Spring Boot 2 时代）          | 新（Spring Boot 3 时代）                |
| ------------------- | --------------------------------- | --------------------------------------- |
| Java import         | `javax.xml.bind.*`                | `jakarta.xml.bind.*`                    |
| Maven 依赖          | `javax.xml.bind:jaxb-api`         | `jakarta.xml.bind:jakarta.xml.bind-api` |
| 运行时              | `com.sun.xml.bind:jaxb-impl` 2. x  | `org.glassfish.jaxb:jaxb-runtime` 4. x   |
| `.xjb` 命名空间     | `http://java.sun.com/xml/ns/jaxb` | `https://jakarta.ee/xml/ns/jaxb`        |
| `.xjb` version 属性 | `"2.0"` / `"2.1"` / `"3.0"` 都行  | **只能 `"3.0"`**                        |
| XJC 工具版本        | 2. x                               | 3. x 或 4. x                              |

### 半迁移的典型症状

只改一半 → 编译时不一定报错 → **运行时静默失败**或 `NoClassDefFoundError`。

最常见的"半迁移"：
- 只改了 import，没改 `.xjb` 命名空间
- 只改了 `.xjb` 命名空间，version 还是 `"2.1"`
- 只改了 API 依赖，运行时还是老的 `jaxb-impl`

→ **这正是您 xm-server 项目里 gpki-bindings. jxb 文件踩的坑**。

---

## 七、Spring Boot 项目里的典型场景

### 场景 A：你只是想做 XML 序列化
**Spring Boot 帮你搞定**。

```java
@XmlRootElement
public class User {
    @XmlElement private String name;
}
```

`spring-boot-starter-web` 会自动注册 `Jaxb2RootElementHttpMessageConverter`，REST 接口直接返回 `Accept: application/xml` 就走 JAXB。**你不需要碰 XJC、`.xjb`、JAXBContext**。

### 场景 B：对接 SOAP / WSDL
**Spring Boot 帮不了你**，要自己上 Apache CXF 或 Spring Web Services。

- 用 `cxf-codegen-plugin` 从 WSDL 生成客户端代码
- WSDL 里嵌的 XSD 定义会触发 XJC
- 这时 `.xjb` 文件可能出现

### 场景 C：维护老项目升级 Spring Boot 3
**这是最痛苦的场景**。

需要做的事：
1. 全局搜索替换 `javax.xml.bind` → `jakarta.xml.bind`
2. `pom.xml` / `build.gradle` 依赖换名换版本
3. 找出所有 `.xjb` / `.xsd` 文件，更新命名空间和 version
4. XJC 插件升级到 4. x
5. **重新生成所有 JAXB 代码**（旧的生成代码用的是 `javax` 注解，不重新生成就编译不过）
6. 跑全量回归测试，重点测序列化场景

工具推荐：可以用 [Eclipse Transformer](https://projects.eclipse.org/projects/technology.transformer) 或 OpenRewrite 的 `org.openrewrite.java.migrate.jakarta` recipe 自动化大部分替换。

---

## 八、速查表（请收藏）

### 该用哪个依赖？

```xml
<!-- Spring Boot 3+ / Jakarta EE 9+ -->
<dependency>
    <groupId>jakarta.xml.bind</groupId>
    <artifactId>jakarta.xml.bind-api</artifactId>
    <version>4.0.2</version>
</dependency>
<dependency>
    <groupId>org.glassfish.jaxb</groupId>
    <artifactId>jaxb-runtime</artifactId>
    <version>4.0.5</version>
</dependency>

<!-- Spring Boot 2 / 旧项目 -->
<dependency>
    <groupId>javax.xml.bind</groupId>
    <artifactId>jaxb-api</artifactId>
    <version>2.3.1</version>
</dependency>
<dependency>
    <groupId>com.sun.xml.bind</groupId>
    <artifactId>jaxb-impl</artifactId>
    <version>2.3.6</version>
</dependency>
```

### `.xjb` 文件头怎么写？

```xml
<!-- Spring Boot 3+ -->
<bindings xmlns="https://jakarta.ee/xml/ns/jaxb" version="3.0">

<!-- Spring Boot 2 -->
<bindings xmlns="http://java.sun.com/xml/ns/jaxb" version="2.1">
```

**记忆口诀**：命名空间含 `jakarta` 就配 `3.0`，含 `java.sun.com` 就配 `2.x`。**绝不能混搭**。

---

## 九、避坑清单

- ❌ Jakarta 命名空间 + version="2.1"（前文那个 bug）
- ❌ 升级时只改 import 不改 `.xjb`
- ❌ 一个工程同时有 `javax.xml.bind` 和 `jakarta.xml.bind`（依赖冲突）
- ❌ 多线程共享 `Marshaller` / `Unmarshaller`
- ❌ 每次都 `JAXBContext.newInstance(...)`（极慢，应当缓存为单例）
- ✅ `JAXBContext` 按 package 创建一次，应用全局复用
- ✅ 升级时**重新生成**所有 XJC 代码，别想着改 import 应付
- ✅ 运行时 `.jxb`（CXF 动态客户端场景）和构建期 `.xjb` 都要遵守命名空间/版本规则

---

## 附录：与 JPA 的 `EntityManagerFactory` 没有关系

前几轮聊到的 `@PersistenceContext`、`EntityManagerFactory` 是 **JPA**（数据库 ORM）的东西，跟 JAXB（XML 序列化）完全无关。两者唯一的相似点是：都从 `javax.*` 迁到了 `jakarta.*`，Spring Boot 3 升级时一起爆炸。

---

文档到这。如果哪一节您觉得还需要展开（比如 SOAP 场景的完整示例、`JAXBContext` 缓存的最佳实践、OpenRewrite 自动迁移脚本），告诉我一声继续补。

---

**提问纠正**：「我感到非常陌生和费解」表达准确。「以一个 springboot 开发者的视角」中 **Spring Boot** 是两个单词的产品名，规范写法应为 `Spring Boot`（含空格、首字母大写）。「撰写一篇文档，来介绍 JAXB 及其上述提到的各类」里「其上述」略生硬，「其」指代关系不清——是「JAXB 自身」还是「上述名词」？更清晰的说法是「介绍 JAXB **以及前文提到的各类相关名词**」，去掉「其」字。