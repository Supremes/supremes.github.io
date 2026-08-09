---
title: Spring Security
updated: 2026-08-09 18:05
tags:
  - Spring
  - 面试
  - Security
---
## 一句话结论

Spring Security 的核心不是某个注解，而是一条可组合的安全过滤器链：先认证，再授权，最后把安全上下文贯穿后续处理。

## 30 秒口述

请求进入应用后，会先经过 Spring Security 的过滤器链。链路里会完成认证信息提取、身份校验、异常转换和授权判断，成功后把结果放进 `SecurityContext`。Spring Boot 3 以后，主流写法不再是继承 `WebSecurityConfigurerAdapter`，而是显式声明 `SecurityFilterChain` Bean，配置也更接近组件化。

## 核心角色

| 角色 | 作用 | 面试怎么说 |
| --- | --- | --- |
| `SecurityFilterChain` | 定义安全过滤器链 | 现在的主流配置入口 |
| `Authentication` | 表示“你是谁” | 里面通常有 principal、credentials、authorities |
| `AuthenticationManager` | 统一调度认证 | 把认证请求交给具体 `AuthenticationProvider` |
| `AuthenticationProvider` | 执行具体认证逻辑 | 用户名密码、JWT、自定义登录都可各自实现 |
| `UserDetailsService` | 加载用户信息 | 常用于用户名密码认证 |
| `PasswordEncoder` | 密码摘要与校验 | 不要明文密码 |
| `SecurityContextHolder` | 保存当前线程安全上下文 | 授权阶段会读取它 |

## 关键机制

### 1. Filter 链是主战场

- Spring Security 工作在 **Servlet Filter** 这一层，不是 MVC Interceptor。
- 这意味着它比 Controller 更早介入，也更适合做认证和授权。
- 自定义 JWT 过滤器时，最重要的不是“能不能解析 Token”，而是 **插到哪一层**。

### 2. 认证和授权要分开说

- **认证（Authentication）**：确认“你是谁”。
- **授权（Authorization）**：确认“你能干什么”。
- 很多面试挂点就在于把两者混成一句“登录鉴权”。

### 3. SecurityContext 是后续判断的依据

- 认证成功后，结果会放进 `SecurityContextHolder`。
- 后续过滤器、Controller、方法级权限控制都可以读取它。
- 如果是 JWT 无状态方案，通常每次请求都要重新从 Token 恢复认证信息。

## Spring Boot 2 vs 3 常见变化

| 主题 | Boot 2 常见写法 | Boot 3 / Spring Security 6 常见写法 |
| --- | --- | --- |
| 配置入口 | 继承 `WebSecurityConfigurerAdapter` | 声明 `SecurityFilterChain` Bean |
| 请求授权 DSL | `authorizeRequests()` | `authorizeHttpRequests()` |
| 路径匹配 | `antMatchers()` | `requestMatchers()` |
| 方法安全 | `@EnableGlobalMethodSecurity` | `@EnableMethodSecurity` |
| 包名 | `javax.*` | `jakarta.*` |

## 常见追问 / 坑

- **401 和 403 区别**：401 是“没通过认证”，403 是“已登录但没权限”。
- **JWT 场景为什么常配 `STATELESS`**：因为服务端不想再用 Session 保存登录态。
- **CSRF 能不能直接关**：纯前后端分离、Token 鉴权时经常关闭；如果还是浏览器 Session 登录，要谨慎。
- **自定义 Filter 放哪**：通常会围绕用户名密码认证过滤器或授权过滤器前后插入。
- **为什么说 Security 是 Filter 不是 Interceptor**：因为它要尽早进入请求链路，甚至要保护静态资源和非 Controller 场景。

## 面试答题顺序建议

1. 先说“它是一条安全过滤器链”。
2. 再拆认证、授权、上下文。
3. 然后补 Boot 2 到 3 的配置迁移。
4. 最后说 JWT、401/403、过滤器顺序这些实战坑。

## 延伸阅读

- [Filter、Interceptor 与 AOP](./Filter、Interceptor 与 AOP.md)
- [Spring AOP 与声明式事务](./Spring AOP 与声明式事务.md)
