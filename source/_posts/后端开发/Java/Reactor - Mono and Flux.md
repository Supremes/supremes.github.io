---
title: Project Reactor Mono/Flux 响应式编程速查
tags:
  - java
  - reactor
  - spring
categories:
  - 后端开发
hidden: true
updated: 2026-04-22 23:48
---

# Project Reactor Mono/Flux 响应式编程速查

> 如果说 Java Stream API 是对**内存中已有集合**的声明式加工流水线，那 Project Reactor 则是对**时间轴上异步事件**的声明式编排引擎。两者外形相似（都是链式操作符），但驱动模型截然不同。

---

## 从 Stream API 说起

```java
// Java Stream：数据已在内存，同步拉取，调用 collect 立即执行
List<String> result = users.stream()
    .filter(u -> u.getAge() > 18)
    .map(User::getName)
    .collect(Collectors.toList());  // 终端操作，触发执行
```

Stream 的核心模型：**Pull（拉）**
调用终端操作时，框架逐条从数据源拉元素，经过中间操作管道，最终汇总结果。数据源必须在调用时已经存在。

---

## Mono / Flux 是什么？

Project Reactor 是 Reactive Streams 规范的实现，提供两种核心类型：

| 类型 | 含义 | 类比 |
|------|------|------|
| `Mono<T>` | **0 或 1 个**异步结果 | `CompletableFuture<T>` / `Optional<T>` |
| `Flux<T>` | **0 到 N 个**异步事件流 | `Stream<T>` 的异步版本 |

```java
// Mono：一次 HTTP 请求的单个响应
Mono<User> userMono = webClient.get().uri("/users/1").retrieve().bodyToMono(User.class);

// Flux：LLM 的逐 token 流式输出
Flux<ChatResponse> stream = chatClient.prompt().user("你好").stream().chatResponse();
```

关键：**定义管道 不等于 执行管道**。与 Stream 一样，Reactor 也是惰性的。只有触发订阅（subscribe）时，数据流才真正开始。

---

## 四个核心区别

### 1. 同步 vs 异步

```java
// Stream：同步阻塞，collect 返回时结果已在内存
List<String> names = list.stream().map(String::toUpperCase).collect(toList());

// Flux：异步非阻塞，subscribe 只是注册回调，不阻塞当前线程
flux.map(String::toUpperCase).subscribe(name -> System.out.println(name));
```

### 2. 数据来源

| | Java Stream | Reactor Flux |
|---|---|---|
| 数据何时存在 | 调用时已全部在内存 | 未来某时刻才逐个产生（网络、IO、定时器） |
| 驱动模式 | Pull（拉） | Push/Pull 混合 |

### 3. 终端操作 vs 订阅

```java
// Stream 终端操作 —— 触发同步执行
long count = stream.filter(...).count();

// Flux 订阅 —— 注册异步回调
flux.filter(...)
    .subscribe(
        item  -> System.out.println("收到: " + item),
        error -> System.err.println("出错: " + error),
        ()    -> System.out.println("完成")
    );
```

### 4. 背压（Backpressure）

Reactor 内置背压支持：下游消费者可以告诉上游我现在只能处理 N 个，防止内存溢出。Java Stream 没有此机制。

```java
flux.limitRate(10)  // 每次最多向上游请求 10 个元素
    .subscribe(...);
```

---

## 常用操作符速查

### 创建

```java
Flux.just("a", "b", "c")
Flux.fromIterable(list)
Flux.range(1, 5)                       // 1, 2, 3, 4, 5
Flux.empty()
Flux.error(new RuntimeException("oops"))
Mono.fromSupplier(() -> fetchFromDB())
Mono.fromFuture(completableFuture)
Flux.interval(Duration.ofSeconds(1))   // 每秒发一个递增 long
```

### 转换（中间操作）

```java
// map — 逐个同步变换（对应 Stream.map）
flux.map(s -> s.toUpperCase())

// flatMap — 每个元素展开为一个异步流，并发合并（无序）
flux.flatMap(id -> webClient.get().uri("/users/" + id).retrieve().bodyToMono(User.class))

// concatMap — 类似 flatMap 但保序，逐一等待
flux.concatMap(id -> fetchUser(id))

// filter / take / skip / distinct
flux.filter(u -> u.getAge() > 18)
flux.take(10)
flux.skip(5)
flux.takeWhile(chunk -> !isCancelled.getAsBoolean())
flux.distinct()

// zip — 将两个流拉链合并
Flux.zip(fluxA, fluxB, (a, b) -> a + "+" + b)

// merge — 并发合并多个流（不保序）
Flux.merge(flux1, flux2)
```

### 副作用（不改变流，仅观测）

```java
flux.doOnNext(item -> log.info("received: {}", item))
flux.doOnError(e -> log.error("error", e))
flux.doOnComplete(() -> log.info("stream completed"))
```

### 错误处理

```java
flux.onErrorReturn("默认值")
flux.onErrorResume(e -> fallbackFlux)
flux.retry(3)
flux.retryWhen(Retry.backoff(3, Duration.ofMillis(100)))
```

### 线程调度

```java
// subscribeOn — 指定订阅（数据生产）发生在哪个线程
mono.subscribeOn(Schedulers.boundedElastic())

// publishOn — 指定后续操作符在哪个线程执行
flux.publishOn(Schedulers.parallel())
```

### 终端操作（触发订阅）

```java
T result     = mono.block();
List<T> list = flux.collectList().block();
T last       = flux.blockLast();
flux.subscribe(onNext, onError, onComplete);
```

---

## dawn-ai 中的实战

dawn-ai（[GitHub](https://github.com/Supremes/dawn-ai)）是一个基于 Spring AI 的 ReAct Agent 项目。Spring AI 的 `ChatClient` 底层使用 Project Reactor，流式接口直接返回 `Flux<ChatResponse>`。

### 核心流水线

`AgentOrchestrator.streamChat()` 中：

```java
chatClient.prompt()
    .system(systemPrompt)
    .messages(history)
    .user(userMessage)
    .toolNames(toolRegistry.getNames())
    .stream()
    .chatResponse()               // 返回 Flux<ChatResponse>
    .contextCapture()             // 捕获 Reactor Context（用于跨算子传递上下文）
    .takeWhile(chunk -> !isCancelled.getAsBoolean())  // 客户端断开时提前终止
    .doOnNext(chunk -> {
        String reasoning = extractReasoning(chunk);
        if (reasoning != null) {
            sink.accept(ChatStreamEvent.thinking(...));
        }
        String delta = extractDelta(chunk);
        if (delta != null) {
            answer.append(delta);
            sink.accept(ChatStreamEvent.token(...));  // 推送给 SseEmitter
        }
    })
    .blockLast();                 // 在专用线程池中阻塞，等待流结束
```

| 操作符 | 职责 |
|--------|------|
| `.stream().chatResponse()` | 创建 `Flux<ChatResponse>`，LLM 每产出一个 token chunk 就发一个元素 |
| `.contextCapture()` | 把当前 Reactor Context 快照注入流，解决跨算子上下文传递问题 |
| `.takeWhile(...)` | 检查取消标志，客户端断连后优雅终止，不再消耗 LLM token |
| `.doOnNext(...)` | 纯副作用：解析 token/thinking 内容，转发给 SSE 下游 |
| `.blockLast()` | **终端操作**，触发整条流执行，阻塞直到流结束 |

### 架构选择：Spring MVC + Reactor，而非 WebFlux

dawn-ai 有意选择 **Spring MVC（Servlet）+ SseEmitter**，而非全响应式的 WebFlux。

这是一种**命令式与响应式的桥接模式**：
- Spring AI 返回的 `Flux` 用于处理 LLM 的流式 token
- `blockLast()` 将响应式流拉平回命令式代码，运行在专用线程池而非 Servlet 线程
- SSE 推送通过 `SseEmitter`（Spring MVC 原生支持），无需引入 WebFlux 依赖

### 真实踩坑：ThreadLocal 跨线程失效

`blockLast()` 背后，Reactor 会调度到自己的 Worker 线程执行，**不是**发起 `.stream()` 调用的那个线程。这导致基于 `ThreadLocal` 的上下文失效：

```
chatStreamExecutor 线程 A
  └─ StepCollector.init(maxSteps)      写入线程 A 的 ThreadLocal
  └─ chatClient.stream()...blockLast() 阻塞线程 A
        └─ Reactor Worker 线程 B（WebClient 回调）
              └─ KnowledgeSearchTool.apply()
                    └─ StepCollector.getAndIncreaseStepNumber()
                          └─ MAX_STEPS.get() 返回 null  线程 B 从未 init()
                          └─ NullPointerException
```

**根因**：`ThreadLocal` 只在同一线程可见，而 Reactor 内部回调运行在不同线程上。

**解法**：使用 `.contextCapture()` + `ThreadLocalAccessor`，或改用 `InheritableThreadLocal`，或将状态显式放入 Reactor Context 随流传递。

---

## Stream API vs Reactor 速查对比

| 维度 | Java Stream | Reactor Flux |
|------|-------------|--------------|
| 数据来源 | 内存中已有集合 | 异步事件（网络/IO/时间） |
| 执行时机 | 终端操作时同步执行 | 订阅后异步执行 |
| 线程模型 | 调用线程（或 ForkJoinPool 并行流） | 可配置（Schedulers） |
| 背压 | 不支持 | 内置支持 |
| 错误处理 | try-catch | `onErrorResume` / `onErrorReturn` / `retry` |
| 多值类型 | `Stream<T>` | `Flux<T>`（0-N）/ `Mono<T>`（0-1） |
| 终端操作 | `collect` / `forEach` / `reduce` | `subscribe` / `block` / `blockLast` |
| 惰性 | 中间操作惰性 | 订阅前不执行 |
| 调试 | 直接断点 | `.log()` / `.checkpoint()` |

---

## 常见操作符类比速查

| Java Stream | Reactor 等价 | 区别 |
|-------------|-------------|------|
| `filter` | `filter` | 无差异 |
| `map` | `map` | 均为同步变换 |
| `flatMap` | `flatMap` | Reactor flatMap **并发**展开；`concatMap` 保序 |
| `collect(toList())` | `collectList()` 返回 `Mono<List<T>>` | Reactor 返回异步包装 |
| `forEach` | `doOnNext` + `subscribe` | `doOnNext` 是中间操作，`subscribe` 触发执行 |
| `reduce` | `reduce` 返回 `Mono<T>` | — |
| `limit(n)` | `take(n)` | — |
| `skip(n)` | `skip(n)` | — |
| `peek` | `doOnNext` | — |
| `count()` | `count()` 返回 `Mono<Long>` | — |
| `anyMatch` | `any(predicate)` 返回 `Mono<Boolean>` | — |
| — | `blockLast()` | 阻塞等最后一个元素，Stream 无此概念 |
