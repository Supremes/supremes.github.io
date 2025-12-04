---
title: Spring MVC
tags:
  - 面试
categories:
  - Spring
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/SpringMVC.webp
hidden: false
updated: 2025-12-04 21:04
abbrlink: 2d0b435f
date: 2025-12-04 20:51:26
sticky:
---
# SpringMVC 工作原理

## 引言

Spring MVC 框架作为 Java Web 应用程序开发中广泛采用的框架，以其分层和松耦合的架构而闻名。这种架构清晰地分离了表示层、持久层和控制层，使得开发人员能够独立地处理各个模块，并将其组合成专业的 Web 应用程序。遵循 MVC 标准开发的 Web 应用程序更易于扩展、更新和管理，因为松耦合的分层结构使得在特定层进行修改变得更加便捷 1。本报告旨在深入探讨 Spring MVC 框架内 HTTP 请求的完整生命周期，从客户端发起请求到最终响应返回，详细阐述其内部的工作原理。

## 理解模型-视图-控制器（MVC）模式

模型-视图-控制器（MVC）是一种广泛应用于软件工程中的架构模式，旨在分离应用程序的不同关注点，从而提高代码的可维护性和可重用性 3。在 MVC 模式中，应用程序被划分为三个核心组件：

- **模型（Model）：** 模型负责封装应用程序的数据和业务逻辑 2。它是应用程序的核心，管理着数据的存储、检索和处理 4。模型独立于用户界面，当模型中的数据发生变化时，它会通知视图进行更新 4。
- **视图（View）：** 视图负责呈现模型中的数据，并将其转化为用户可以理解的格式，例如 HTML、JSON 等 2。视图是被动组件，它从模型中获取数据并进行显示，不包含任何业务逻辑 4。
- **控制器（Controller）：** 控制器充当模型和视图之间的中介 2。它接收用户的输入（通常来自浏览器），并根据输入调用模型来执行相应的业务逻辑 4。处理完成后，控制器会选择合适的视图来显示模型中的数据 4。

Spring MVC 框架正是基于 MVC 设计模式构建的，它通过一个核心组件——DispatcherServlet（前端控制器）来管理整个请求处理流程 2。DispatcherServlet 接收所有传入的 HTTP 请求，并将其分发给适当的处理器进行处理，从而实现了 MVC 模式在 Web 应用程序中的应用 2。

## 核心调度器 DispatcherServlet

DispatcherServlet 在 Spring MVC 框架中扮演着前端控制器的关键角色，它负责拦截所有进入应用程序的 HTTP 请求 1。作为应用程序的唯一入口点，DispatcherServlet 并不直接处理请求，而是将请求的处理委派给其他组件，从而实现请求的统一管理和调度 5。

DispatcherServlet 的初始化和生命周期管理由 Web 服务器（如 Tomcat）负责。在基于 XML 的配置中，DispatcherServlet 通常在 `web.xml` 文件中声明和映射 1。对于基于 Java 的配置，则可以通过 `WebConfiguration` 类进行配置 1。为了确保在服务器启动时 DispatcherServlet 被初始化，通常会配置 `<load-on-startup>1</load-on-startup>` 5。DispatcherServlet 拥有自己的 `WebApplicationContext`，它是根应用程序上下文的子上下文，这种层级结构有助于清晰地分离 Web 相关的 Bean 和应用程序范围内的 Bean 5。通过在 `web.xml` 中将 DispatcherServlet 的 servlet 映射配置为 `"/"`，可以使得所有发往应用程序的请求都由该 DispatcherServlet 处理 1。

## 请求导航：请求处理流程

Spring MVC 框架处理 HTTP 请求的过程可以细分为以下几个关键步骤 1：

1. **客户端请求：** 用户在浏览器中输入 Web URL，发起对特定页面的请求 1。
2. **DispatcherServlet 拦截：** 所有的客户端请求首先被前端控制器 DispatcherServlet 拦截 1。这一步标志着 Spring MVC 框架开始介入请求的处理过程 1。
3. **HandlerMapping：** DispatcherServlet 使用 HandlerMapping 组件来查找与当前请求 URL 相匹配的控制器（Handler） 1。HandlerMapping 就像一个路由器，它根据请求的特征（如 URL）将请求导向负责处理它的特定控制器 1。
4. **控制器调用：** 一旦找到合适的控制器，DispatcherServlet 就将请求分发给该控制器进行处理 1。
5. **控制器处理：** 控制器接收到请求后，会执行相应的业务逻辑，与模型（负责业务逻辑和数据）进行交互，并准备好要展示给视图的数据 1。这是应用程序中处理特定请求的核心逻辑所在 1。
6. **ModelAndView 返回：** 控制器处理完请求后，通常会返回一个 ModelAndView 对象。该对象包含了模型数据（需要展示的数据）以及视图的逻辑名称 1。ModelAndView 对象充当了数据和视图展示方式的载体 1。
7. **视图解析：** DispatcherServlet 接收到 ModelAndView 对象后，会使用 ViewResolver 组件根据视图的逻辑名称来查找实际的视图实现（例如，一个 JSP 文件） 2。ViewResolver 的作用在于将抽象的视图名称与具体的视图技术连接起来，提供了框架的灵活性 4。
8. **视图渲染：** DispatcherServlet 将模型数据传递给解析得到的视图进行渲染 1。视图使用模型中的数据生成最终的 HTML 响应，该响应将被发送回客户端 1。
9. **响应返回客户端：** 最终，渲染后的视图作为 HTTP 响应返回给用户的浏览器，用户在浏览器中看到请求的结果 1。

**Spring MVC 请求处理流程**

| **步骤** | **涉及组件**      | **描述**                                             |
| -------- | ----------------- | ---------------------------------------------------- |
| 1        | 客户端            | 用户发起 HTTP 请求。                                 |
| 2        | DispatcherServlet | 拦截所有进入应用程序的请求。                         |
| 3        | HandlerMapping    | 确定处理该请求的控制器。                             |
| 4        | 控制器            | 接收并处理请求。                                     |
| 5        | 控制器            | 与模型交互，准备数据。                               |
| 6        | 控制器            | 返回包含模型数据和视图逻辑名称的 ModelAndView 对象。 |
| 7        | ViewResolver      | 将视图逻辑名称解析为实际的视图对象。                 |
| 8        | 视图              | 使用模型数据渲染响应。                               |
| 9        | DispatcherServlet | 将渲染后的响应返回给客户端。                         |

## 将请求映射到处理器：HandlerMapping 的作用

HandlerMapping 接口定义了将请求映射到处理器对象的契约 13。Spring MVC 提供了多种 HandlerMapping 接口的实现，大致可以分为继承自 `AbstractHandlerMethodMapping` 和 `AbstractUrlHandlerMapping` 的两类 16。

`RequestMappingHandlerMapping` 是最常用的实现，它将 `@Controller` 类中带有 `@RequestMapping` 注解的方法映射为请求处理器 13。在应用程序初始化阶段，`RequestMappingHandlerMapping` 会扫描带有 `@Controller` 和 `@RequestMapping` 注解的类，并根据这些注解构建请求映射 2。它使用 `RequestMappingInfo` 对象来表示映射关系，该对象封装了请求匹配的各种条件，如路径、请求头、参数、HTTP 方法和媒体类型 16。`getMappingForMethod` 方法负责根据处理器方法上的 `@RequestMapping` 注解创建 `RequestMappingInfo` 对象 16。`@RequestMapping` 注解提供了一种灵活且声明式的方式，可以根据多种条件将特定的 HTTP 请求映射到控制器方法 2。

`BeanNameUrlHandlerMapping` 是默认的 `HandlerMapping` 实现，它将 URL 路径映射到与 URL 路径同名的 Bean（Bean 的名称以 "/" 开头） 13。它支持直接名称匹配和使用 "*" 进行的模式匹配 13。这种方式提供了一种基于约定的映射方法，Bean 的名称直接对应于 URL 路径 13。

`SimpleUrlHandlerMapping` 允许通过 Spring 配置中的 `Properties` 对象或 `Map` 显式地配置 URL 到处理器的映射（处理器可以是 Bean 实例或 Bean 名称） 13。这种方式提供了一种更具声明性的方式在配置文件中定义映射规则，为复杂的路由场景提供了灵活性 13。

`@RequestMapping` 以及其他派生注解（如 `@GetMapping`、`@PostMapping` 等）简化了在控制器类中定义请求映射的过程 2。这些注解使得代码更易读和维护 2。

HandlerMapping 最终会返回一个 `HandlerExecutionChain` 对象，该对象包含了找到的处理器以及一个有序的拦截器列表 14。`HandlerExecutionChain` 允许在主要处理器执行前后执行拦截器，从而实现横切关注点的处理 14。可以使用 `order` 属性来设置不同 HandlerMapping 实现的优先级 13。

**常见的 HandlerMapping 实现**

| **HandlerMapping 实现**        | **描述**                                              | **主要注解/配置**                                            |
| ------------------------------ | ----------------------------------------------------- | ------------------------------------------------------------ |
| `RequestMappingHandlerMapping` | 将请求映射到带有 `@RequestMapping` 注解的控制器方法。 | `@Controller`, `@RequestMapping`, `@GetMapping`, `@PostMapping` 等。 |
| `BeanNameUrlHandlerMapping`    | 将 URL 映射到名称以 "/" 开头的同名 Bean。             | Bean 的名称作为 URL 路径。                                   |
| `SimpleUrlHandlerMapping`      | 通过配置显式地将 URL 映射到处理器 Bean 或 Bean 名称。 | Spring 配置文件中的属性或 Map。                              |

## 执行业务逻辑：控制器处理

DispatcherServlet 在确定了合适的控制器后，会将请求分发给该控制器进行处理 1。控制器中的方法会根据请求的 HTTP 方法（如 GET、POST 等）执行相应的业务逻辑 1。控制器通常会定义处理特定 HTTP 方法的方法，确保应用程序能够对不同类型的请求做出适当的响应 1。

在控制器方法执行过程中，Spring MVC 提供了灵活的参数解析和数据绑定机制 10。Spring MVC 允许使用任何对象作为命令或表单对象，而无需实现框架特定的接口 25。`@RequestParam` 注解用于将查询参数或表单数据映射到方法参数，尤其适用于基本数据类型 28。使用 `@RequestParam` 可以简化在控制器方法签名中直接访问请求参数的过程 28。数据绑定机制能够根据参数名称和类型自动将请求数据转换为 Java 对象 28。Spring 的数据绑定机制简化了将 HTTP 请求数据转换为可用的 Java 对象的过程，减少了样板代码 28。`@ModelAttribute` 注解可用于将请求参数绑定到方法参数或方法返回值，并将其作为命名的模型属性暴露给视图 21。`@ModelAttribute` 有助于实现双向数据绑定，方便表单数据与模型对象之间的映射 21。`DataBinder` 类支持构造器绑定和属性绑定，用于使用请求数据填充对象 27。较新版本的 Spring 中引入的构造器绑定提供了一种更安全的方式，通过调用构造函数并传入请求数据来绑定预期的参数 29。数据绑定过程中发生的类型不匹配会被视为验证错误，从而允许在应用程序层面进行处理 25。Spring 灵活的数据绑定能够优雅地处理常见的错误，使得开发者可以向用户提供有用的反馈 25。较新版本的 Spring 还支持直接在控制器方法参数上使用 `@Constraint` 注解进行方法验证，不再需要在类级别使用 `@Validated` 27。内置的方法验证简化了控制器方法中输入参数的验证过程，提高了代码的清晰度并减少了手动编写验证逻辑的需求 27。

## 传递数据和视图信息：ModelAndView

ModelAndView 对象是一个容器，它同时持有模型数据和要渲染的视图的名称 1。控制器在处理完请求后，通常会创建并返回 ModelAndView 对象 1。模型数据以键值对的形式存储在 Map 中，键是属性名称，值是要在视图中显示的数据 1。视图名称是一个逻辑标识符，ViewResolver 会将其解析为实际的视图技术 1。

控制器使用 ModelAndView 对象来同时返回模型数据和视图的逻辑名称 1。ModelAndView 对象可以通过构造函数传入视图名称，然后添加模型属性，也可以先创建一个空的 ModelAndView 对象，再分别设置模型属性和视图名称 17。它为控制器提供了一种便捷的方式来传递响应所需的数据以及指示应该使用哪个视图来呈现响应 1。

除了使用 ModelAndView，还有其他方式可以将模型数据传递给视图，例如将 `Model` 或 `ModelMap` 作为方法参数 17。`Model` 和 `ModelMap` 是用于向视图传递数据的接口/类，它们由 Spring 直接注入到控制器方法中 17。当使用 `Model` 或 `ModelMap` 时，控制器方法通常只返回视图的逻辑名称作为字符串 17。Spring 提供了多种向视图传递数据的方式，开发者可以根据控制器的需求和偏好选择最合适的方法 17。

## 解析视图：ViewResolver 的功能

ViewResolver 接口负责将控制器返回的视图逻辑名称映射到实际的 View 对象 2。它使得在浏览器中渲染模型数据成为可能，而无需将实现绑定到特定的视图技术 21。ViewResolver 接口定义了 `resolveViewName(String viewName, Locale locale)` 方法 23。

`InternalResourceViewResolver` 用于将视图名称解析为内部资源，如位于 `WEB-INF` 目录下的 JSP 文件 21。它通过配置前缀（例如 `/WEB-INF/views/`）和后缀（例如 `.jsp`）来定位视图文件 22。此解析器常用于使用 JSP 作为视图技术的传统 Java Web 应用程序 21。

`XmlViewResolver` 使用在 XML 文件中定义的视图 Bean 定义来解析视图名称 21。它允许配置具有特定类（例如 `JstlView`）和 URL 的视图 Bean 21。这种方式提供了一种配置驱动的视图解析方法，允许在同一应用程序中使用不同的视图技术 21。

`ResourceBundleViewResolver` 使用属性文件来解析视图名称，视图配置在属性文件中以键值对的形式定义 21。此解析器适用于以更外部化的方式管理视图配置，可能有助于国际化或特定于环境的设置 21。

还有其他常用的解析器，如用于 Velocity 模板的 `VelocityViewResolver` 和用于 FreeMarker 模板的 `FreeMarkerViewResolver` 7。Spring MVC 支持与各种流行的模板引擎集成，为开发者提供了广泛的视图层选择 7。

Spring MVC 支持配置多个视图解析器，并使用 `setOrder()` 方法设置它们的优先级 21。通过配置具有特定顺序的多个视图解析器，Spring 可以尝试不同的解析器，直到找到匹配的视图，从而允许在同一应用程序中基于视图名称模式使用不同的视图技术 21。

**常见的 ViewResolver 实现**

| **ViewResolver 实现**          | **描述**                                          | **典型配置**                                          |
| ------------------------------ | ------------------------------------------------- | ----------------------------------------------------- |
| `InternalResourceViewResolver` | 将视图名称解析为内部资源（如 JSP 文件）。         | 配置前缀（如 `/WEB-INF/views/`）和后缀（如 `.jsp`）。 |
| `XmlViewResolver`              | 使用在 XML 文件中定义的视图 Bean 来解析视图名称。 | 配置包含视图 Bean 定义的 XML 文件路径。               |
| `ResourceBundleViewResolver`   | 使用属性文件中的配置来解析视图名称。              | 配置属性文件的基本名称。                              |
| `VelocityViewResolver`         | 将视图名称解析为 Velocity 模板。                  | 配置 Velocity 模板的路径和后缀。                      |
| `FreeMarkerViewResolver`       | 将视图名称解析为 FreeMarker 模板。                | 配置 FreeMarker 模板的路径和后缀。                    |

## 渲染响应：视图组件

选定的视图负责渲染模型数据，生成最终的响应 1。视图接收模型数据（通过 `Model`、`ModelMap` 或 `ModelAndView` 添加的属性），并将其与视图模板合并 1。不同的视图技术（JSP、Thymeleaf、FreeMarker 等）有各自的语法和机制来访问模板中的模型数据 1。例如，在 JSP 中，通常使用表达式语言（EL），如 `${attributeName}` 17。渲染过程最终会生成 HTML（或其他内容类型），并作为响应发送回客户端的浏览器 1。

Spring MVC 支持多种视图技术及其集成 1。JSP（JavaServer Pages）是一种传统的视图技术，Spring MVC 对其提供了良好的支持 1。Thymeleaf 是一种现代的服务器端 Java 模板引擎，它提供了自然的模板 5。FreeMarker 和 Velocity 是其他可以与 Spring MVC 集成的模板引擎 7。此外，Spring MVC 还支持将视图渲染为 JSON 或 XML 格式，用于构建 RESTful API 4。Spring MVC 在视图层面的灵活性使其能够适应各种 Web 应用程序和 API 的构建需求 4。

## 拦截请求：使用 HandlerInterceptor

HandlerInterceptor 接口允许在请求到达处理器之前（`preHandle`）、处理器执行之后但在视图渲染之前（`postHandle`）、以及整个请求完成之后（`afterCompletion`）对请求进行拦截和处理 13。

- `preHandle(HttpServletRequest request, HttpServletResponse response, Object handler)` 方法在处理器执行之前被调用；返回 `true` 以继续处理，返回 `false` 则停止处理 19。此方法常用于执行身份验证、授权检查和日志记录等操作，这些操作需要在主要的请求处理逻辑之前完成 19。
- `postHandle(HttpServletRequest request, HttpServletResponse response, Object handler, ModelAndView modelAndView)` 方法在处理器成功执行之后但在视图渲染之前被调用；可以修改 ModelAndView 对象 19。这允许根据处理器执行的结果修改模型或视图，例如添加通用属性或更改视图名称 19。
- `afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex)` 方法在整个请求处理完成之后被调用，无论处理成功与否；常用于执行清理任务和记录日志 19。即使在请求处理过程中发生错误，此方法也能确保必要的清理操作或最终的日志记录语句得到执行 19。

HandlerInterceptor 的常见用例包括记录请求详细信息和响应时间 19、实现身份验证和授权检查以保护应用程序资源 19、通过记录请求开始和结束时间来执行性能监控 19 以及修改请求或响应头 19。

HandlerInterceptor 需要在 Spring MVC 框架中注册才能在请求处理生命周期中被调用 19。通常通过实现 `WebMvcConfigurer` 接口并覆盖 `addInterceptors` 方法来配置 HandlerInterceptor 19。

**HandlerInterceptor 方法**

| **方法名称**      | **调用时机**                   | **主要目的**                                                 | **返回值/参数**                                              |
| ----------------- | ------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------ |
| `preHandle`       | 在处理器执行之前               | 执行预处理，如身份验证、授权、日志记录等；可以决定是否继续处理请求。 | `boolean` (true 继续，false 停止)；`HttpServletRequest`, `HttpServletResponse`, `Object handler` |
| `postHandle`      | 在处理器执行之后，视图渲染之前 | 修改 ModelAndView 对象，添加额外的模型属性或修改视图名称。   | `void`；`HttpServletRequest`, `HttpServletResponse`, `Object handler`, `ModelAndView modelAndView` |
| `afterCompletion` | 在整个请求处理完成之后         | 执行清理任务，如释放资源、记录请求完成时间、处理异常等。     | `void`；`HttpServletRequest`, `HttpServletResponse`, `Object handler`, `Exception ex` (可选) |

## 结论

Spring MVC 框架的工作原理围绕着中央调度器 DispatcherServlet 展开，它与 HandlerMapping、Controller、ModelAndView、ViewResolver 和 View 等组件协同工作，共同处理客户端发起的 Web 请求。DispatcherServlet 接收所有请求，HandlerMapping 负责将请求映射到合适的控制器，控制器处理业务逻辑并返回包含模型数据和视图名称的 ModelAndView 对象，ViewResolver 将视图名称解析为实际的视图，最后视图使用模型数据渲染响应并返回给客户端。HandlerInterceptor 则提供了在请求处理的不同阶段进行拦截和处理的能力。

使用 Spring MVC 框架具有诸多优势。首先，MVC 模式实现了清晰的关注点分离 2。其次，组件之间的松耦合使得应用程序更易于维护和测试 1。框架提供了高度的灵活性和可扩展性，这得益于其可配置的组件和接口 1。Spring MVC 支持各种视图技术 2，并提供了强大的数据绑定和验证机制 25。通过 HandlerInterceptor，可以方便地实现面向切面的功能 19。此外，Spring MVC 还与 Spring 框架的其他功能（如依赖注入和 AOP）无缝集成 3，并有助于快速应用程序开发 2。这些特性使得 Spring MVC 成为构建健壮、可维护和可扩展的 Java Web 应用程序的首选框架之一。

# Spring MVC 面试题:

**什么是 Spring MVC 框架？**
   - **答案：** Spring MVC 是基于模型-视图-控制器（MVC）设计模式的 Web 框架，用于构建 Web 应用程序。

**Spring MVC 的工作原理是什么？**
   - **答案：** 客户端请求由前端控制器（DispatcherServlet）处理，然后通过处理器映射器（HandlerMapping）找到相应的控制器，控制器处理请求并返回模型和视图。

**Spring MVC 中的控制器是如何工作的？**
   - **答案：** 控制器接收并处理客户端请求，然后返回一个包含模型数据的逻辑视图名称。

**Spring MVC 的核心组件有哪些？**
   - **答案：** 包括 DispatcherServlet、Controller、HandlerMapping、ViewResolver 等。

**解释一下 Spring MVC 中的 DispatcherServlet。**
   - **答案：** DispatcherServlet 是 Spring MVC 的前端控制器，负责接收并分发客户端的请求。

**Spring MVC 中的 Model、View、Controller 是什么？**
   - **答案：** Model 用于封装数据，View 负责展示数据，Controller 处理用户请求并返回适当的模型和视图。

 **如何处理表单提交和参数绑定？**
   - **答案：** 使用@ModelAttribute 注解进行参数绑定，使用<form:form>标签处理表单提交。

**Spring MVC 中的拦截器是什么，有什么作用？**
   - **答案：** 拦截器用于在请求处理前或处理后执行一些额外的逻辑，例如身份验证、日志记录等。

**什么是 RESTful Web 服务，Spring MVC 如何支持 RESTful 风格？**
   - **答案：** RESTful 是一种 Web 服务设计风格，Spring MVC 通过注解（@RequestMapping）和 HTTP 方法来支持 RESTful 风格。

**Spring MVC 中的@ModelAttribute 和@SessionAttributes 有什么区别？**
    - **答案：** @ModelAttribute 用于绑定请求参数到模型中，@SessionAttributes 用于将模型中的属性暂时存储在会话中。