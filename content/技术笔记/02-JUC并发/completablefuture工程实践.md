---
title: CompletableFuture 工程实践——执行器、超时、异常治理与上下文传播
date: 2025-12-26
tags:
  - 面试
  - JUC
---
# CompletableFuture 工程实践

这篇只写工程落地：你在生产里用 `CompletableFuture` 90% 会踩的坑，基本都跟下面四件事有关：
- **用谁的线程池跑**（默认 commonPool 很容易出事故）
- **超时怎么做**（单个阶段超时 vs 整条链路超时）
- **异常怎么收敛**（避免“异常被吞/链路静默失败”）
- **上下文怎么传**（ThreadLocal/MDC/租户信息在线程池中会丢）

---

## 1. 第一原则：不要迷信默认线程池（commonPool）

`CompletableFuture.supplyAsync/runAsync` 不传 executor 时，通常使用 `ForkJoinPool.commonPool()`。

风险点：
- commonPool 是**全局共享**：你服务里任何模块都可能占用它。
- 你在异步阶段里做了**阻塞 IO**（RPC/DB/HTTP/锁等待），会把 commonPool 的工作线程卡住。
- 卡住的结果不是“慢一点”，而是：
  - 异步链条堆积
  - 触发更多超时与重试
  - 最终雪崩

工程建议：
- 业务异步：**一律用“专用线程池”**（独立隔离、可监控、可调参）。
- commonPool：只留给 `parallelStream` 或非常确定的 CPU 计算型任务。

---

## 2. 推荐的执行器：独立线程池 + 可观测

```java
public final class BizExecutors {

    public static final ThreadPoolExecutor CF_POOL = new ThreadPoolExecutor(
            32,
            64,
            60L,
            TimeUnit.SECONDS,
            new ArrayBlockingQueue<>(1000),
            r -> {
                Thread t = new Thread(r);
                t.setName("cf-biz-" + t.getId());
                t.setDaemon(false);
                return t;
            },
            new ThreadPoolExecutor.CallerRunsPolicy()
    );

    private BizExecutors() {}
}
```

建议你至少做到：
- 线程命名（排障必需）
- 有界队列（避免 OOM）
- 明确拒绝策略（背压/降级）

---

## 3. 链路编排：thenCompose vs thenCombine（必须讲清）

- `thenCompose`：**串行依赖**（上一步结果决定下一步）
- `thenCombine`：**并行合并**（两个 independent 结果合并）

```java
CompletableFuture<User> fUser = CompletableFuture.supplyAsync(() -> loadUser(uid), BizExecutors.CF_POOL);
CompletableFuture<List<Order>> fOrders = CompletableFuture.supplyAsync(() -> loadOrders(uid), BizExecutors.CF_POOL);

CompletableFuture<UserProfile> profile = fUser.thenCombine(fOrders,
        (user, orders) -> new UserProfile(user, orders));
```

易错点：
- 把“依赖关系”写错会导致：本该串行的并行跑、或本该并行的串行跑（性能/一致性都出问题）。

---

## 4. 超时：分两类（阶段超时 vs 整体超时）

### 4.1 JDK 9+：orTimeout / completeOnTimeout

```java
CompletableFuture<String> f = CompletableFuture
        .supplyAsync(this::callRpc, BizExecutors.CF_POOL)
        .orTimeout(200, TimeUnit.MILLISECONDS);
```

- `orTimeout`：超时后以 `TimeoutException` 结束。
- `completeOnTimeout(value, ...)`：超时后返回一个兜底值。

### 4.2 JDK 8 兼容思路（工程常见）
如果你需要兼容 JDK 8，常用方案是：
- 额外准备一个 `ScheduledExecutorService`，在超时点 `completeExceptionally`。

---

## 5. 异常治理：不要让异常“静默”

### 5.1 exceptionally / handle / whenComplete 怎么选
- `exceptionally(fn)`：只处理异常，返回兜底值
- `handle((v, ex) -> ...)`：不管成功失败都会走，适合“统一收敛”
- `whenComplete((v, ex) -> ...)`：只做副作用（打日志/埋点），不改结果

工程推荐写法：
- **链路末端统一收敛**（一处处理）
- `whenComplete` 做埋点
- `handle` 或 `exceptionally` 做兜底/转译

```java
return profile
    .whenComplete((v, ex) -> {
        if (ex != null) {
            // 记录链路异常
        }
    })
    .exceptionally(ex -> fallbackProfile(uid));
```

### 5.2 join vs get
- `get()`：受检异常，调用方必须处理
- `join()`：抛 `CompletionException`（运行时异常包装）

工程里常见做法：
- 对外 API 层：用 `get(timeout)` 或整体超时控制，返回明确错误码
- 内部聚合：用 `join()` 但要统一 unwrap

---

## 6. 取消（cancel）与“停得下来”

`CompletableFuture.cancel(true)` **不保证**真正停掉正在运行的任务：
- 如果任务线程不检查中断、或卡在不可中断阻塞点，取消只是把 future 标记为取消。

工程建议：
- 任务代码要支持取消：
  - 长循环里检查 `Thread.currentThread().isInterrupted()`
  - 阻塞点选择可中断 API（如 `lockInterruptibly` / `BlockingQueue.take` 等）

---

## 7. 经典死锁模式：同池相互等待（非常高频）

错误模式：
- 在 `CF_POOL` 里跑任务 A
- A 内部 `join()` 等待另一个也提交到 `CF_POOL` 的任务 B
- 当池满/队列堆积时，可能出现 **线程都在等别人、但没人有线程可运行**

规避：
- 依赖链尽量用非阻塞编排（thenCompose/thenCombine），不要在池内 `join()`
- 或者：为“会互相等待”的环节拆分不同线程池

---

## 8. 上下文传播：ThreadLocal/MDC 在线程池里会丢

现实：
- ThreadLocal 绑定在线程上；异步切线程后，ThreadLocal 自然不存在。

最稳妥的工程解法（不引入额外库的情况下）：
- 提交任务前 capture
- 任务执行前 set
- finally remove/restore

```java
public static Runnable wrapWithThreadLocal(Runnable task) {
    Map<String, String> ctx = Context.capture(); // 你自己实现：把 ThreadLocal 里的内容拷贝出来
    return () -> {
        Map<String, String> old = Context.apply(ctx);
        try {
            task.run();
        } finally {
            Context.restore(old);
        }
    };
}
```

如果你项目里用日志 MDC：
- 同样的思路 capture/apply/restore
- 否则会出现日志丢 traceId、甚至串号

---

## 9. 推荐的“生产模板”

目标：
- 所有异步阶段都跑在专用 executor
- 有超时
- 有异常收敛
- 有埋点

```java
public CompletableFuture<UserProfile> getProfile(long uid) {
    CompletableFuture<User> fUser = CompletableFuture
            .supplyAsync(() -> loadUser(uid), BizExecutors.CF_POOL)
            .orTimeout(200, TimeUnit.MILLISECONDS);

    CompletableFuture<List<Order>> fOrders = CompletableFuture
            .supplyAsync(() -> loadOrders(uid), BizExecutors.CF_POOL)
            .orTimeout(300, TimeUnit.MILLISECONDS);

    return fUser.thenCombine(fOrders, UserProfile::new)
            .whenComplete((v, ex) -> {
                // metrics + log
            })
            .exceptionally(ex -> fallbackProfile(uid));
}
```

---

## 10. 小结

- `CompletableFuture` 的工程难点不在 API，而在 **线程池隔离、超时、异常治理、上下文传播**。
- 如果你把这四件事写成团队模板/组件，生产稳定性会明显提升。

---

## 面试题 / Checklist

- 为什么默认 `ForkJoinPool.commonPool()` 容易出事故？哪些任务类型最危险？
- `thenCompose` vs `thenCombine` 的语义差异？分别适合什么场景？
- `exceptionally` / `handle` / `whenComplete` 如何选择？异常如何统一收敛？
- `join()` 与 `get()` 的异常模型差异是什么？如何 unwrap `CompletionException`？
- `cancel(true)` 为什么不保证真正停掉任务？任务代码如何配合中断？
- 解释“同池互等”死锁模式，并给出规避策略。
- ThreadLocal/MDC 在异步链路中如何做 capture/apply/restore？
