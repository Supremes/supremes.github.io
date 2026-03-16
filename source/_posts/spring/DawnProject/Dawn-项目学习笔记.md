---
title: Dawn-项目学习笔记
tags: []
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: true
updated: '2026-02-26 21:55'
abbrlink: 3540c1b1
date: 2026-01-07 21:44:46
categories:
sticky:
---
## **SpringAOP - 切面编程**

### @PointCut
- 标记了@PointCut 的方法，语法规定，必须是 void 返回值且方法体要为空。
- **Pointcut 处**：只能定义“位置”，不能写“动作”（语法规定）。
- Pointcut 内的字符串语法格式：
	- `execution( [修饰符] 返回值类型 [包名.类名.]方法名(参数) [异常模式] )`

| **位置**      | **你的代码符号**              | **含义**       | **解释**                                                                    |
| ----------- | ----------------------- | ------------ | ------------------------------------------------------------------------- |
| **1. 动作**   | `execution(...)`        | **指示符**      | 告诉 AOP：我要监控的是“方法的执行动作”。(还有其他的如 `@annotation` 监控注解)                        |
| **2. 返回值**  | First `*`               | **任意返回值**    | 不管方法返回 String、Void 还是 Object，都匹配。                                         |
| **3. 包路径**  | `com.dawn.controller..` | **路径范围**     | `com.dawn.controller` 包下的所有层级。<br><br>  <br><br>`..` 表示当前包及其**所有子包**（递归）。 |
| **4. 类与方法** | Second `*` . Third `*`  | **任意类.任意方法** | 第一个 `*` 表示该包下的任意类名。<br><br>  <br><br>第二个 `*` 表示类中的任意方法名。                  |
| **5. 参数**   | `(..)`                  | **任意参数**     | `()` 里是参数列表。<br><br>  <br><br>`..` 表示参数个数不限、类型不限（0个或多个参数）。                |

### 核心注解一览 ：

| **注解**              | **英文名**    | **类比 Java 关键字**    | **执行时机**                   | **核心用途**                |
| ------------------- | ---------- | ------------------ | -------------------------- | ----------------------- |
| **@Around**         | 环绕通知       | `try { ... }` 外部包裹 | **最强注解**。包围整个方法，既能在前，也能在后。 | 性能监控、事务管理、完全改变返回值、吞掉异常。 |
| **@Before**         | 前置通知       | 方法第一行              | 目标方法执行**之前**。              | 参数校验、权限检查、Log 记录“开始处理”。 |
| **---**             | **Target** | **(目标方法)**         | **(实际业务逻辑执行)**             | **---**                 |
| **@AfterReturning** | 返回后通知      | `return` 之后        | 目标方法**成功**返回之后。            | 记录返回值、数据审计、缓存更新。        |
| **@AfterThrowing**  | 异常通知       | `catch` 块          | 目标方法**抛出异常**之后。            | 异常日志、报警、事务补偿。           |
| **@After**          | 后置(最终)通知   | `finally` 块        | **无论成功还是失败**，最后都会执行。       | 资源释放（关闭流、断开连接）、清理上下文。   |
```
Enter: @Around (前半部分)
   ↓
   Enter: @Before
      ↓
      Executing: 目标方法 (Target Method) 
      ↓
      (如果成功) -> Enter: @AfterReturning
      (如果报错) -> Enter: @AfterThrowing
      ↓
   Enter: @After (不管成功失败，总会由它收尾)
   ↓
Exit: @Around (后半部分)
```

## Interceptor

- 属于 Spring MVC 中提供的一种机制，专门用于拦截**HTTP 请求**。
- 可以处理以下几个场景，插入自定义逻辑
	- Controller 之前和之后
	- 视图 View 渲染完成之后
- 代码层面：通过实现 `HandlerIntercpetor` 接口

| **方法名**               | **执行时机**                  | **典型应用场景**                                      | **返回值作用**                          |
| --------------------- | ------------------------- | ----------------------------------------------- | ---------------------------------- |
| **`preHandle`**       | 请求到达 Controller **之前**    | **登录拦截**、权限校验、限流、提取并解析 Token                    | 返回 `true` 放行；返回 `false` 阻断请求，直接响应。 |
| **`postHandle`**      | Controller 执行完，视图渲染**之前** | 修改传给视图的数据（Model）、统一给响应添加基础属性                    | 无（`void`）                          |
| **`afterCompletion`** | 整个请求结束，视图渲染**之后**         | **清理资源**（如清除 `ThreadLocal` 防止内存泄漏）、记录最终的请求耗时和日志 | 无（`void`）                          |
注：现在的 RESTful API（前后端分离）开发中，由于通常不返回视图而是返回 JSON，`postHandle` 的使用频率已经大大降低，日常开发中最常用的是 **`preHandle`**。

| **对比维度**  | **Interceptor (拦截器)**                                | **AOP (切面编程)**                                                   |
| --------- | ---------------------------------------------------- | ---------------------------------------------------------------- |
| **归属框架**  | Spring MVC                                           | Spring 核心容器                                                      |
| **作用范围**  | **仅限 Web 请求**（经过 DispatcherServlet 的请求）。             | **任何 Spring Bean 的方法**（Service层、DAO层等都可以）。                       |
| **上下文信息** | 可以直接获取 `HttpServletRequest` 和 `HttpServletResponse`。 | 无法直接获取 HTTP 请求头（除非借助 RequestContextHolder），但能拿到方法的**参数、注解、返回值**。 |
| **颗粒度**   | 只能拦截到 Controller 级别。                                 | 可以拦截到非常细粒度的方法级别。                                                 |

## Filter

- 属于 Servlet 容器（Tomcat）中
- 代码层面 ：实现 Filter 接口
```Java
import javax.servlet.*;
import java.io.IOException;

public class MyFilter implements Filter {

    @Override
    public void init(FilterConfig filterConfig) throws ServletException {
        // 容器启动，Filter 初始化时执行（仅执行一次）
    }

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain) 
            throws IOException, ServletException {
        System.out.println("请求进入大门：前置处理...");
        
        // 【关键！】调用 chain.doFilter 放行请求，进入下一个 Filter 或 Servlet
        chain.doFilter(request, response); 
        
        System.out.println("请求离开大门：后置处理...");
    }

    @Override
    public void destroy() {
        // 容器关闭，Filter 销毁时执行（仅执行一次）
    }
}
```

| **对比维度**           | **Filter（过滤器）**                                                       | **Interceptor（拦截器）**                                      |
| ------------------ | --------------------------------------------------------------------- | --------------------------------------------------------- |
| **所属规范**           | Servlet 规范（依赖于 Tomcat 等容器）                                            | Spring MVC 框架（依赖于 Spring）                                 |
| **触发时机**           | 请求进入容器后，**到达 DispatcherServlet 之前**                                   | 请求到达 DispatcherServlet 后，**到达具体的 Controller 之前**          |
| **拦截范围**           | 几乎所有请求（包括静态资源如 HTML、图片等）                                              | 默认只拦截映射到 Controller 的请求                                   |
| **能拿到什么参数**        | 只能拿到最底层的 `ServletRequest` 和 `ServletResponse`                         | 除了请求响应，还能拿到映射的 `Handler` (Controller 方法) 和 `ModelAndView` |
| **Spring Bean 注入** | 传统 Filter 不受 Spring 管理，注入 Bean 较麻烦（需借助 `DelegatingFilterProxy` 或特定注解） | 天生归 Spring 管理，可以随意 `@Autowired` 注入各种 Service              |
## Metrics

- Counter：统计**累计发生次数**，如“下单总数”、“异常总数”。它是只增不减的。
- Gauge：统计**瞬时状态**，数值可大可小，如“当前待处理队列长度”、“线程池活跃数”。
- Timer：统计**一段代码执行的耗时和频率**。建议使用@Timed 注解（需要配置 `TimedAspect` Bean）。
	```java
	import io.micrometer.core.annotation.Timed;
	 
	 @Service
	 public class PaymentService {
	 
	     // 自动记录调用的次数(count)、总耗时(sum)和最大耗时(max)
	     @Timed(value = "business.payment.process", description = "Time taken to process payment")
	     public void processPayment() {
	         // ... 耗时操作
	     }
	 }
	```

