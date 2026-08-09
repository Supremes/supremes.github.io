---
title: Spring MVC
updated: 2026-08-09 18:05
tags:
  - Spring
  - 面试
  - MVC
---
## 一句话结论

Spring MVC 的核心就是 `DispatcherServlet` 统一接入请求，再把“找谁处理、怎么绑参数、怎么返回结果、怎么处理异常”拆成一串可扩展组件。

## 30 秒口述

浏览器请求先到 `DispatcherServlet`。它通过 `HandlerMapping` 找到目标处理器，再交给 `HandlerAdapter` 执行。执行过程中会做参数解析、数据绑定、校验、消息转换；执行完成后，再走返回值处理、视图解析或 JSON 序列化。如果中间抛异常，则交给 `HandlerExceptionResolver`。这套链路让 MVC 既统一又可扩展。

## 请求主链路

| 阶段 | 核心组件 | 你要会说什么 |
| --- | --- | --- |
| 请求入口 | `DispatcherServlet` | 前端控制器，统一调度所有 Web 请求 |
| 找处理器 | `HandlerMapping` | 根据路径、HTTP 方法、请求头等匹配 Controller 方法 |
| 执行处理器 | `HandlerAdapter` | 负责真正调用目标方法，不同处理器类型可配不同适配器 |
| 解析参数 | `HandlerMethodArgumentResolver` / `WebDataBinder` / `HttpMessageConverter` | 处理 `@RequestParam`、`@PathVariable`、`@RequestBody`、校验等 |
| 处理返回值 | `HandlerMethodReturnValueHandler` / `ViewResolver` / `HttpMessageConverter` | 返回视图名时走视图解析；返回对象时常直接转 JSON |
| 异常兜底 | `HandlerExceptionResolver` / `@ControllerAdvice` | 统一异常映射和响应格式 |

## 关键机制

### 1. DispatcherServlet 只负责调度

- 它是入口，不是业务处理器。
- 它最大的价值是把 Web 流程拆成多个策略接口，方便替换和扩展。

### 2. HandlerMapping 不只是“按 URL 找方法”

- `@RequestMapping` 不只匹配路径，也可以匹配 HTTP 方法、参数、请求头、`consumes`、`produces`。
- 实际返回的是 `HandlerExecutionChain`，除了处理器本身，还会带上拦截器链。

### 3. 参数解析是 MVC 面试高频点

- `@RequestParam`：更像从 query/form 里取值。
- `@PathVariable`：从路径模板里取值。
- `@RequestBody`：交给 `HttpMessageConverter` 反序列化。
- `@ModelAttribute`：更像把一组请求参数绑定成对象。
- 参数校验常和 `@Valid` / `@Validated` 连着问。

### 4. REST 接口和传统页面渲染不是同一条尾链

- **前后端分离**：更常见 `@ResponseBody` / `@RestController`，直接走消息转换器返回 JSON。
- **服务端渲染**：返回视图名，再交给 `ViewResolver` 找 JSP / Thymeleaf 模板。

### 5. 异常处理也是一条策略链

- `@ExceptionHandler` 适合处理局部异常。
- `@ControllerAdvice` 适合统一异常响应。
- 真正底层仍然是 `HandlerExceptionResolver` 在兜底。

## 常见追问 / 坑

- **`@RequestBody` 和 `@ModelAttribute` 区别**：前者主要依赖消息转换器读请求体，后者主要依赖数据绑定器按字段装配。
- **为什么返回对象能自动变 JSON**：因为 `@ResponseBody` 触发 `HttpMessageConverter`，常见实现是 Jackson。
- **拦截器和过滤器怎么选**：过滤器在 Servlet 容器层，拦截器在 Spring MVC 层；见 [Filter、Interceptor 与 AOP](./Filter、Interceptor 与 AOP.md)。
- **为什么说 `postHandle` 在前后端分离里存在感低**：因为很多接口直接返回 JSON，不走视图渲染。
- **静态资源一定走 Interceptor 吗**：不一定，要看映射链路和配置。

## 面试答题顺序建议

1. 先讲 `DispatcherServlet` 统一入口。
2. 再讲 `HandlerMapping + HandlerAdapter`。
3. 接着讲参数解析和返回值处理。
4. 最后补异常处理、拦截器和扩展点。

## 延伸阅读

- [Spring Security](./Spring Security.md)
- [Filter、Interceptor 与 AOP](./Filter、Interceptor 与 AOP.md)
