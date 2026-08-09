---
title: Dawn 项目学习笔记
updated: 2026-08-09 18:05
tags:
  - 项目复盘
  - Spring
  - Dawn
---
> **问题**：阅读 Dawn 项目源码时，需要把 AOP、拦截器、过滤器、指标埋点这些分散概念，映射回具体实现位置。  
> **决策**：围绕切点表达式、通知时机、Web 拦截链分层、Micrometer 指标类型做结构化整理。  
> **结果**：形成了一份可直接用于源码对照和项目讲解的阅读笔记。  
> **可追问**：AOP 与 Interceptor 怎么分工、`preHandle` 常做什么、指标为什么分 Counter / Gauge / Timer。

这份笔记保留项目阅读视角；如果只想看通用原理，可跳到 [04-Spring生态](../04-Spring生态/Spring生态总览.md)。

## 1. Spring AOP：切面编程怎么映射到项目代码

### `@Pointcut` 该怎么讲

- 标记 `@Pointcut` 的方法，返回值必须是 `void`，方法体为空。
- Pointcut 负责定义“拦哪里”，不负责定义“做什么”。
- 典型表达式：
  ```java
  execution(* com.dawn.controller..*.*(..))
  ```

| 位置 | 代码片段 | 含义 |
| --- | --- | --- |
| 指示符 | `execution(...)` | 监控方法执行 |
| 返回值 | 第一个 `*` | 任意返回值 |
| 包路径 | `com.dawn.controller..` | `controller` 包及其所有子包 |
| 类与方法 | `*.*` | 任意类的任意方法 |
| 参数 | `(..)` | 任意参数列表 |

### 核心通知怎么串

| 注解 | 执行时机 | 常见用途 |
| --- | --- | --- |
| `@Around` | 整个方法外层包裹 | 性能监控、事务、统一异常包装 |
| `@Before` | 目标方法前 | 参数校验、权限检查、入口日志 |
| `@AfterReturning` | 成功返回后 | 记录结果、缓存更新 |
| `@AfterThrowing` | 抛异常后 | 异常日志、告警 |
| `@After` | 无论成败都会执行 | 资源释放、上下文清理 |

可直接口述为：

```text
@Around 前半段
  -> @Before
    -> 目标方法
      -> 成功时 @AfterReturning
      -> 失败时 @AfterThrowing
  -> @After
@Around 后半段
```

## 2. Interceptor：项目里最常落点在请求前置处理

- 属于 Spring MVC 提供的 HTTP 请求拦截机制。
- 典型使用点：登录拦截、权限校验、限流、解析 Token、清理 `ThreadLocal`。
- 代码层面通过实现 `HandlerInterceptor` 接口完成。

| 方法名 | 执行时机 | 典型应用 |
| --- | --- | --- |
| `preHandle` | Controller 之前 | 登录拦截、权限校验、限流、Token 解析 |
| `postHandle` | Controller 之后、视图渲染之前 | 给 `Model` 补通用属性 |
| `afterCompletion` | 整个请求结束后 | 清理资源、记录完整耗时 |

补一句更贴近项目的面试说法：

- 前后端分离接口以 JSON 为主时，`postHandle` 的存在感会下降。
- 真正常用的往往是 `preHandle` 和 `afterCompletion`。

## 3. Interceptor 和 AOP 的分工

| 对比维度 | Interceptor | AOP |
| --- | --- | --- |
| 归属框架 | Spring MVC | Spring 核心容器 |
| 作用范围 | 仅限 Web 请求 | 任意 Spring Bean 方法 |
| 上下文信息 | 能直接拿到请求、响应、Handler | 更擅长拿方法、参数、注解、返回值 |
| 更适合处理什么 | Token、登录、请求级埋点 | 事务、审计、服务层日志、性能统计 |

经验口径：

- **和 HTTP 强相关** 的逻辑，优先考虑 Interceptor。
- **和业务方法强相关** 的横切逻辑，优先考虑 AOP。

## 4. Filter：比 Interceptor 更早的一层

- Filter 属于 Servlet 容器层，Spring 只是嵌在容器里。
- 它发生在请求进入 `DispatcherServlet` 之前。
- 适合做编码、跨域、安全入口、统一日志等更前置的事情。

| 对比维度 | Filter | Interceptor |
| --- | --- | --- |
| 所属规范 | Servlet 规范 | Spring MVC |
| 触发时机 | 到达 `DispatcherServlet` 之前 | 到达具体 Controller 之前 |
| 拦截范围 | 几乎所有请求 | 主要是 MVC 请求 |
| Spring Bean 注入 | 需要额外桥接或注册 | 天生受 Spring 管理 |

通用原理可继续看：[Filter、Interceptor 与 AOP](../04-Spring生态/Filter、Interceptor 与 AOP.md)。

## 5. Metrics：项目里如何讲观测性

- **Counter**：累计次数，只增不减，比如登录失败总数、异常总数。
- **Gauge**：瞬时状态，比如线程池活跃数、队列积压数。
- **Timer**：统计耗时与调用频率，适合接口或关键业务方法。

```java
import io.micrometer.core.annotation.Timed;

@Service
public class PaymentService {

    @Timed(value = "business.payment.process", description = "Time taken to process payment")
    public void processPayment() {
        // ...
    }
}
```

项目里讲指标时，别只说“接了 Grafana”，要能继续说：

1. 你埋了哪些业务指标；
2. 指标对应什么告警或容量判断；
3. 为什么这里用 Timer，不是 Counter。
