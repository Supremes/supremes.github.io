---
title: Dawn 项目 JDK 17 与 Spring Boot 3 升级记录
updated: 2026-08-09 18:05
tags:
  - 项目复盘
  - 升级
  - Dawn
---
> **问题**：项目原先基于 JDK 1.8 和 Spring Boot 2，技术栈偏旧，难以继续承接更现代的 Spring 与 Java 能力。  
> **决策**：升级到 JDK 17 和 Spring Boot 3，并同步处理包名迁移、依赖替换和 Security 配置方式变化。  
> **结果**：形成了一份明确的升级改动清单，可直接用于解释兼容性成本和迁移重点。  
> **可追问**：`javax` 到 `jakarta` 影响了什么、为什么要替换 Sleuth、SecurityFilterChain 和旧写法差在哪。

## 升级目标

- JDK：`1.8 -> 17`
- Spring Boot：`2.x -> 3.x`

## 关键兼容性变化

### 1. 包名迁移

- `javax.* -> jakarta.*`

这往往不是简单全局替换，涉及：

- Servlet API
- Validation API
- JPA / ORM 相关注解
- 依赖库自身是否已适配 Jakarta 生态

### 2. 依赖替换与升级

文中已明确提到的调整包括：

- `spring-cloud-starter-sleuth` 移除，改用 `micrometer-tracing-bridge-brave`
- `loki-appender`
- `mybatisplus`
- `mysql-connector`
- `jjwt`

这里最值得在面试里展开的是：

- **为什么移除 Sleuth**：Boot 3 主流 tracing 方案已转向 Micrometer Tracing。
- **为什么依赖升级要成组看**：JDK、Boot、Spring Security、数据库驱动往往一起受版本矩阵约束。

### 3. Spring Security 配置方式变化

旧写法：

- 继承 `WebSecurityConfigurerAdapter`

新写法：

- 显式声明 `SecurityFilterChain` Bean

## 升级时最该讲清楚的点

1. **不是只改 JDK 版本号**：核心框架、依赖和 API 命名空间都会一起变。
2. **不是所有报错都来自业务代码**：很多时候是三方依赖没跟上 Jakarta。
3. **Security 改动最容易被追问**：因为它既有 API 变化，也牵涉认证链路理解。

## 一段可直接复述的项目表达

这个项目从 JDK 8 升到 17、Spring Boot 2 升到 3 时，最核心的工作不是“编译通过”，而是梳理 Jakarta 命名空间迁移、链路追踪方案替换，以及 Spring Security 从 `WebSecurityConfigurerAdapter` 迁到 `SecurityFilterChain` 的配置重构。真正难点在于版本兼容矩阵和依赖联动，而不是某一个 API 的机械替换。

## 相关文档

- [DawnBlog 架构审计与演进建议书](./DawnBlog 架构审计与演进建议书.md)
- [Dawn 项目改造建议与行动路线图](./Dawn 项目改造建议与行动路线图.md)
