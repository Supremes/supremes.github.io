---
title: Spring 核心面试主线
updated: 2026-08-09 18:05
tags:
  - Spring
  - 面试
---
这篇只做一件事：把 Spring 面试里最容易散掉的主线，压缩成可口述、可展开、可追问的版本。

## 1. IoC / DI

- **一句话结论**：IoC 是“对象交给容器管理”，DI 是“容器把依赖装配进去”，DI 只是 IoC 的实现方式之一。
- **30 秒口述**：Spring 的本质不是一堆注解，而是一个容器。业务对象不自己 `new` 依赖，而是先把类描述成 `BeanDefinition`，再由容器统一创建、注入、初始化和销毁。这样对象关系集中管理，解耦和扩展都更容易。
- **关键机制**：
  - `BeanFactory` / `ApplicationContext` 是容器核心，前者偏底层，后者在此基础上补了事件、国际化、资源加载等能力。
  - Spring 先解析配置或注解，生成 `BeanDefinition`，再按依赖关系创建 Bean。
  - `@Autowired` 默认按类型找，冲突时再看 `@Primary`、`@Qualifier`、参数名。
  - 构造器注入最稳，因为依赖在创建时就完整，字段注入最省事但最不利于测试和不可变设计。
- **常见追问 / 坑**：
  - IoC 和 DI 不是同义词，DI 只是实现 IoC 的一种手段。
  - `singleton` 只代表容器里单例，不代表线程安全。
  - 面试里最好优先回答“构造器注入优于字段注入”。

## 2. Bean 创建与生命周期

- **一句话结论**：Bean 生命周期不是“new 完就能用”，而是“定义 -> 实例化 -> 依赖注入 -> 初始化 -> 代理增强 -> 销毁”。
- **30 秒口述**：Spring 先把 Bean 的定义收集起来，真正需要时再实例化。实例化后会做属性填充、执行 `Aware` 回调、`BeanPostProcessor` 前后置处理、初始化方法，最后才把完整 Bean 放进容器。关闭容器时再执行销毁逻辑。
- **关键机制**：
  - 常见初始化链路：实例化 -> 属性填充 -> `BeanNameAware` / `BeanFactoryAware` 等 -> `postProcessBeforeInitialization` -> `@PostConstruct` / `InitializingBean` / `initMethod` -> `postProcessAfterInitialization`。
  - AOP 代理通常出现在 `BeanPostProcessor` 阶段，所以“放进容器里的 Bean”可能已经不是原始对象。
  - 销毁阶段常见入口：`@PreDestroy`、`DisposableBean`、`destroyMethod`。
- **常见追问 / 坑**：
  - `BeanFactoryPostProcessor` 改的是 **Bean 定义**，`BeanPostProcessor` 改的是 **Bean 实例**。
  - `@PostConstruct` 不是构造器；构造器解决“能不能造出来”，`@PostConstruct` 解决“造完后怎么初始化”。

## 3. 三级缓存与循环依赖边界

- **一句话结论**：Spring 的三级缓存只为了解决“单例 Bean 的属性/Setter 循环依赖”，不是万能循环依赖解法。
- **30 秒口述**：Spring 创建单例 Bean 时，实例化和初始化是分开的。为了让 A 还没完全初始化时，B 也能先拿到 A 的早期引用，Spring 放了三级缓存：成品池、半成品池、对象工厂池。这样可以提前暴露引用，必要时还可以提前暴露代理对象。
- **关键机制**：
  - `singletonObjects`：一级缓存，放完全初始化后的单例。
  - `earlySingletonObjects`：二级缓存，放提前暴露的早期对象。
  - `singletonFactories`：三级缓存，放“如何生成早期引用”的工厂，AOP 场景下可借此返回代理。
  - 三级缓存存在的核心价值不是“多一层”，而是 **延迟决定是否要把早期对象包装成代理**。
- **常见追问 / 坑**：
  - **构造器循环依赖**解决不了，因为对象都还没实例化完，没法提前暴露引用。
  - **Prototype Bean** 默认也解决不了，因为 Spring 不缓存它。
  - 自定义多个代理增强器时，如果早期暴露和最终对象不一致，容易引出循环依赖异常或“注入的不是最终代理”问题。

## 4. AOP 代理

- **一句话结论**：Spring AOP 的默认思路不是改源码，而是给 Bean 套一层代理，在代理里织入横切逻辑。
- **30 秒口述**：AOP 最常见的用途是事务、日志、权限和监控。外部调用先进入代理对象，代理按切点命中通知链，再调用目标方法。Spring 常见代理方式有 JDK 动态代理和 CGLIB，本质都是“代理拦截”，不是字节码静态织入。
- **关键机制**：
  - 有接口时可用 JDK 动态代理；类代理多见 CGLIB。Spring Boot 里通常默认更偏向类代理。
  - 切点决定“拦谁”，通知决定“做什么”，代理决定“何时插进去”。
  - 事务本质上就是一个 AOP 拦截器：方法前开启事务，方法后决定提交还是回滚。
- **常见追问 / 坑**：
  - **自调用失效**：`this.xxx()` 绕过代理，AOP 和事务都会失效。
  - **final 类 / final 方法**会限制基于继承的代理增强。
  - Spring AOP 只拦 Spring 容器管理的 Bean，自己 `new` 的对象不生效。

> 深挖可继续看：[Spring AOP 与声明式事务](./Spring AOP 与声明式事务.md)。

## 5. 声明式事务：传播、隔离与失效场景

- **一句话结论**：`@Transactional` 不是语法糖，本质是事务拦截器围绕方法执行，在传播行为和隔离级别上做决策。
- **30 秒口述**：方法进入事务代理后，Spring 会通过 `TransactionInterceptor` 找到合适的 `PlatformTransactionManager`。如果当前线程已有事务，就按传播行为决定加入还是新开；如果没有，就决定是否创建。隔离级别最终落在数据库；提交和回滚也由事务管理器统一处理。
- **关键机制**：
  - 常用传播行为：`REQUIRED`（默认，能加入就加入）、`REQUIRES_NEW`（挂起旧事务，开新事务）、`NESTED`（基于保存点做子事务）。
  - 常用隔离级别：`READ_COMMITTED` 解决脏读，`REPEATABLE_READ` 进一步避免不可重复读；幻读能否完全避免还要看数据库实现。
  - 默认只对 `RuntimeException` 和 `Error` 回滚，受检异常通常要显式加 `rollbackFor`。
- **常见追问 / 坑**：
  - **失效场景高频清单**：自调用、非 Spring Bean、异常被吃掉、受检异常没配回滚、异步/新线程丢失上下文、选错事务管理器。
  - `readOnly = true` 主要是提示优化，不等于数据库层面绝对禁止写。
  - `REQUIRES_NEW` 会额外占连接，高并发下容易把连接池打满。

## 6. Spring Boot 自动配置

- **一句话结论**：自动配置不是“Spring 猜中了你的心思”，而是“按条件批量注册默认 Bean，用户 Bean 优先级更高”。
- **30 秒口述**：`@SpringBootApplication` 里包含 `@EnableAutoConfiguration`。启动时，Spring Boot 会从 starter 提供的自动配置清单里导入配置类，再用 `@ConditionalOnClass`、`@ConditionalOnMissingBean`、`@ConditionalOnProperty` 等条件判断是否生效。满足条件就给你一套默认 Bean，不满足就跳过。
- **关键机制**：
  - Spring Boot 3 常看 `META-INF/spring/org.springframework.boot.autoconfigure.AutoConfiguration.imports`；老版本常见 `spring.factories`。
  - starter 解决“依赖打包”，auto-configuration 解决“默认装配”。
  - `@ConfigurationProperties` 负责把配置文件稳定地绑定到对象上。
- **常见追问 / 坑**：
  - 想关掉某个自动配置，可用 `exclude` 或配置项控制。
  - 自己声明同类型 Bean，往往就会覆盖默认 Bean，这是“可接管”的核心。
  - 排查自动配置是否命中，最直接看条件报告（Condition Evaluation Report）。

## 7. 常见扩展点

- **一句话结论**：Spring 最强的地方不是内置功能多，而是几乎每个阶段都留了扩展点。
- **30 秒口述**：如果要在容器启动前改 Bean 定义，用 `BeanFactoryPostProcessor`；要在 Bean 初始化前后增强，用 `BeanPostProcessor`；要扩展 Web 参数解析，用 `HandlerMethodArgumentResolver`；要扩展 MVC 配置，用 `WebMvcConfigurer`；要做业务解耦，可以走事件机制。
- **关键机制**：
  - **容器启动期**：`ImportSelector`、`Condition`、`BeanDefinitionRegistryPostProcessor`。
  - **Bean 生命周期**：`BeanPostProcessor`、`InstantiationAwareBeanPostProcessor`、各种 `Aware`。
  - **Web 层**：`HandlerInterceptor`、`Filter`、`Converter`、`Formatter`、`HandlerMethodArgumentResolver`、`ResponseBodyAdvice`。
  - **业务协作**：`ApplicationEventPublisher`、`@EventListener`、`ApplicationRunner` / `CommandLineRunner`。
- **常见追问 / 坑**：
  - 别把所有需求都塞进 AOP，参数解析、统一响应、请求拦截各有更合适的扩展位。
  - `@EventListener` 只是解耦调用，不天然等于“可靠异步消息”。

## 速记串法

如果面试官让你“整体讲讲 Spring”，可以按这条线答：

1. **容器**：IoC / DI 管对象和依赖。
2. **生命周期**：Bean 不是 `new` 完就结束，中间会经过初始化和代理增强。
3. **代理**：AOP 用代理织入日志、事务、权限。
4. **事务**：声明式事务本质是 AOP 拦截器。
5. **自动配置**：Spring Boot 用条件装配把一堆默认能力组起来。
6. **扩展点**：Spring 强在“可被接管”，不是“只能照着用”。
