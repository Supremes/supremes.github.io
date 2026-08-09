---
title: JMM 与 volatile
date: 2026-08-09
tags:
  - 面试
  - JUC
---
# JMM 与 volatile

> 并发里的 JMM 统一放在这里；JVM 运行时数据区请看 [JVM](../03-JVM/JVM.md)。

## 一句话结论

JMM 不是讲堆、栈、方法区怎么分，而是讲**线程之间如何安全地看见共享变量**。

## 30 秒口述

JMM 规定共享变量存在主内存，线程会把变量拷贝到自己的工作内存后再操作。多线程问题主要就三类：可见性、原子性、有序性。`volatile` 解决的是可见性和部分有序性，`synchronized` / `Lock` / CAS 解决的是更完整的同步问题。判断线程间结果是否“应该看得见”，核心标准是 **happens-before**。

## 1. JMM 到底解决什么

- **可见性**：线程 A 改了值，线程 B 什么时候能看到。
- **有序性**：编译器和 CPU 可不可以为了性能重排指令。
- **原子性**：一组操作能不能被其他线程“看到一半”。

最容易犯的错是把 JMM 和 JVM 运行时数据区混为一谈：  
- JVM 运行时数据区回答“对象放哪、栈帧放哪”。  
- JMM 回答“线程之间如何读写共享变量”。

## 2. happens-before 必背规则

- 程序次序规则：同一线程内，前面的操作先行发生于后面的操作。
- `volatile` 规则：对一个 `volatile` 变量的写，先行发生于后续对它的读。
- 管程锁规则：一次 `unlock` 先行发生于后续对同一把锁的 `lock`。
- 线程启动规则：`Thread.start()` 先行发生于线程内动作。
- 线程终止规则：线程内所有动作先行发生于其他线程感知它结束（`join()` / `isAlive()` 返回 false）。
- 传递性：如果 A happens-before B，B happens-before C，那么 A happens-before C。

面试里不用背定义原文，但要知道：**这套规则决定了“看见”是否合法**。

## 3. volatile 到底保证什么

### 一句话结论

`volatile` 保证**可见性**和**禁止关键重排序**，但**不保证复合操作原子性**。

### 30 秒口述

线程写 `volatile` 变量时，会把修改尽快刷新到主内存；其他线程读这个变量时，会强制从主内存重新读取。JMM 还会在它周围建立内存屏障，约束部分重排序。所以 `volatile` 很适合做状态开关、配置刷新、DCL 单例里的实例引用，但 `count++` 这类读改写复合操作仍然不安全。

### 关键追问 / 坑

- `volatile` 不能替代锁：`count++` 仍然会丢数据。
- 它更适合**一个线程写、多线程读**或状态发布类场景。
- 只要涉及多个共享变量的一致性，通常就要上锁或上更高层并发原语。

## 4. DCL 为什么一定要加 volatile

```java
class Singleton {
    private static volatile Singleton instance;

    static Singleton getInstance() {
        if (instance == null) {
            synchronized (Singleton.class) {
                if (instance == null) {
                    instance = new Singleton();
                }
            }
        }
        return instance;
    }
}
```

原因不是“让它更快”，而是防止：
1. 分配对象内存
2. 把引用赋给 `instance`
3. 执行构造初始化

如果 2 和 3 被重排，别的线程可能看到一个**非空但未初始化完成**的对象。

## 5. 高频坑

- 看到“内存模型”先问清：是 **JMM** 还是 **JVM 运行时数据区**。
- `volatile` 适合状态位，不适合事务性更新。
- `final` 字段也有发布语义，但别把它和 `volatile` 混成一回事。
- “可见”不等于“安全”，你可能只是更快地看到了错误结果。

## 面试 Checklist

- 能区分 JMM 和 JVM 运行时数据区。
- 能解释可见性 / 原子性 / 有序性分别是什么意思。
- 能说出 3~5 条常见 happens-before 规则。
- 能讲清 `volatile` 能保证什么、不能保证什么。
- 能解释 DCL 为什么必须加 `volatile`。
