---
title: Spring 过滤器
tags:
  - 面试
categories:
  - Spring
cover: >-
  https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/Spring%E8%BF%87%E6%BB%A4%E5%99%A8.webp
hidden: false
updated: '2025-12-03 22:43'
abbrlink: fed01c2
date: 2025-12-03 22:37:18
sticky:
---
## Filter 和 Interceptor

### Filter 过滤器
- Servlet 容器维度的，拦截 Servlet 的请求。
- 通过 `Filter` 接口实现的

Servlet 容器： Tomcat、Jetty。遵循 Java Servlet 规范，通常包括 HTTP 服务器，处理 web 请求和响应。
### Interceptor 拦截器

- Spring 容器维度的，对 Spring MVC 的请求进行拦截。
- 通过实现 `HandlerInterceptor` 接口实现的，并通过 Spring 的配置进行注册。

#### PS：

Spring 框架嵌入到 Servlet 容器中，利用 spring 容器管理应用程序中的其他组件:

- **Spring Beans：** 在 Spring 框架中，你可以定义和配置各种 Bean，包括业务逻辑组件、数据访问组件、服务等。这些 Bean 的生命周期、依赖关系等都由 Spring 容器管理。
- **Service 层和业务逻辑：** 你可以使用 Spring 来管理业务逻辑层的组件，使其成为 Spring 容器管理的 Bean。这些业务逻辑组件通常包括服务层的实现，处理业务逻辑、事务管理等。
- **数据访问组件：** Spring 框架提供了对数据访问的支持，包括整合 Hibernate、MyBatis 等持久化框架。你可以将数据访问组件配置为 Spring Bean，并由 Spring 容器进行管理。
- **事务管理：** Spring 容器可以管理应用程序中的事务，确保事务的一致性和隔离性。通过将事务管理配置为 Spring Bean，可以轻松地进行声明性事务管理。
- **AOP（面向切面编程）：** Spring 框架提供 AOP 的支持，你可以将切面配置为 Spring Bean，以实现横切关注点的模块化管理。
- **配置信息：** Spring 容器可以管理应用程序的配置信息，通过将配置文件解析为 Spring Bean，实现配置的集中化管理。