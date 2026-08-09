---
title: Filter、Interceptor 与 AOP
updated: 2026-08-09 18:05
tags:
  - Spring
  - 面试
  - Web
---
## 一句话结论

Filter 属于 Servlet 容器层，Interceptor 属于 Spring MVC 层，AOP 属于 Spring Bean 方法层；三者都能“拦”，但拦截位置和适用问题完全不同。

## 30 秒口述

如果需求发生在 HTTP 请求刚进系统时，比如编码、跨域、统一日志、认证前置处理，优先想 Filter；如果需求紧贴 Controller 调用，比如登录校验、限流、埋点、`ThreadLocal` 清理，优先想 Interceptor；如果需求根本不是 Web 专属，而是所有 Bean 方法都要增强，比如事务、审计、重试、统一监控，优先想 AOP。

## 三者对比

| 维度 | Filter | Interceptor | AOP |
| --- | --- | --- | --- |
| 所属层级 | Servlet 容器 | Spring MVC | Spring 容器 |
| 触发时机 | 请求到 `DispatcherServlet` 之前 | Controller 前后 | Bean 方法调用前后 |
| 拦截范围 | 几乎所有 Web 请求 | 主要是映射到 MVC 的请求 | 任何被 Spring 管理的 Bean 方法 |
| 能拿到什么 | `ServletRequest` / `ServletResponse` | 请求、响应、`Handler`、`ModelAndView` | 方法、参数、注解、返回值、异常 |
| 是否天然依赖 Spring | 否 | 是 | 是 |
| 典型用途 | 编码、CORS、安全入口、统一日志 | 登录校验、限流、埋点、上下文清理 | 事务、审计、监控、重试、权限 |

## 关键机制

### Filter：容器维度的第一道入口

- 由 Servlet 规范定义，和 Tomcat / Jetty 这类容器紧密相关。
- Spring Security 之所以强，就是因为它建立在 Filter 链上。
- 需要把普通 Filter 交给 Spring 管理时，常会用到 `DelegatingFilterProxy` 或注册 Bean 的方式。

### Interceptor：MVC 请求链的增强点

- 常见三个方法：`preHandle`、`postHandle`、`afterCompletion`。
- `preHandle` 最常用，适合做登录校验、限流、TraceId 注入。
- `afterCompletion` 常用于清理 `ThreadLocal`，防止内存泄漏。

### AOP：业务横切逻辑的统一切入点

- 它不关心是不是 Web 请求，只关心某个 Bean 方法有没有命中切点。
- 事务就是最典型的 AOP 应用之一。
- 如果业务需要拿请求头，也不是不能做，但通常说明这个问题更适合放在 Web 层。

## 选型口诀

- **先问是不是 HTTP 问题**：不是，就优先想 AOP。
- **是 HTTP 问题，再问要不要比 MVC 更早介入**：要，就用 Filter。
- **只和 Controller 链路强相关**：优先用 Interceptor。

## 常见追问 / 坑

- **Filter 能替代 Interceptor 吗**：能做一部分事，但拿不到 `Handler`、`ModelAndView` 这类 MVC 上下文。
- **Interceptor 能替代 Security 吗**：不适合。安全一般要更早介入，且往往依赖完整 Filter 链。
- **AOP 能不能做所有权限校验**：技术上能做一部分，但 Web 身份认证、Token 解析更适合放 Filter / Interceptor。
- **为什么 `postHandle` 用得少**：前后端分离下很多接口直接返回 JSON，不走视图渲染。

## 延伸阅读

- [Spring MVC](./Spring MVC.md)
- [Spring Security](./Spring Security.md)
- [Spring AOP 与声明式事务](./Spring AOP 与声明式事务.md)
