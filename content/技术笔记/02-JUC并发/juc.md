---
title: JUC 并发总览
date: 2025-12-04
updated: 2026-08-09
tags:
  - 面试
  - JUC
---
# JUC 并发总览

> 这篇只做导航和 Checklist，不再重复专项正文。并发里的 JMM 统一收口到 [JMM 与 volatile](./JMM与volatile.md)。

## 面试主线

建议按这个顺序复习：
1. [JMM 与 volatile](./JMM与volatile.md)：先分清可见性、原子性、有序性。
2. [线程与中断](./线程与中断.md)：讲清协作式取消。
3. [等待与唤醒机制](./等待与唤醒机制.md)：讲清 `wait/notify`、`Condition`、`LockSupport`。
4. [原子类与 CAS](./原子类与cas.md)：讲清 CAS、ABA、`LongAdder`。
5. [AQS](./aqs.md) + [Java锁](./java锁.md)：讲清锁的公共底座和常见实现。
6. [同步器](./同步器.md) + [并发容器与队列](./并发容器与队列.md)：讲清协作模型和容器选型。
7. [线程池](./线程池.md) + [线程池调参](./线程池调参.md)：讲清生产落地。
8. [CompletableFuture 工程实践](./completablefuture工程实践.md)：讲清异步编排。

## 场景 → 入口

| 你在回答什么题 | 直接跳转 |
| --- | --- |
| `volatile`、happens-before、DCL | [JMM 与 volatile](./JMM与volatile.md) |
| `interrupt()`、优雅停线程 | [线程与中断](./线程与中断.md) |
| `wait` / `notify` / `park` 区别 | [等待与唤醒机制](./等待与唤醒机制.md) |
| CAS、ABA、`LongAdder` | [原子类与 CAS](./原子类与cas.md) |
| `synchronized`、`ReentrantLock`、读写锁 | [Java锁](./java锁.md) |
| AQS 如何支撑锁和同步器 | [AQS](./aqs.md) |
| `CountDownLatch`、`Semaphore`、`CyclicBarrier` | [同步器](./同步器.md) |
| `ConcurrentHashMap`、阻塞队列 | [并发容器与队列](./并发容器与队列.md) |
| 线程池参数、拒绝策略、背压 | [线程池](./线程池.md)、[线程池调参](./线程池调参.md) |
| `CompletableFuture` 组合、超时、异常治理 | [CompletableFuture 工程实践](./completablefuture工程实践.md) |

## 复习 Checklist

- [ ] 能说清 JMM 不是 JVM 运行时数据区。
- [ ] 能解释 `interrupt()` 为什么不是“强杀线程”。
- [ ] 能比较 `wait/notify`、`Condition`、`LockSupport`。
- [ ] 能说清 CAS 的收益、ABA 的风险、`LongAdder` 的适用场景。
- [ ] 能讲清 `synchronized` 和 `ReentrantLock` 的取舍。
- [ ] 能解释 AQS 的 `state`、队列、独占 / 共享模式。
- [ ] 能区分 `CountDownLatch`、`CyclicBarrier`、`Semaphore` 的场景。
- [ ] 能说明 `ConcurrentHashMap` 为什么不允许 `null`。
- [ ] 能背出线程池核心参数和常见拒绝策略。
- [ ] 能说明 `CompletableFuture` 为什么不要默认依赖公共线程池。
