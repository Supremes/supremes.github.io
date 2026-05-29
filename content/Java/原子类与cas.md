---
title: 原子类与 CAS——ABA、LongAdder、字段更新器与 volatile 落地
date: 2025-12-26
tags:
  - 面试
  - JUC
---
很多人把“原子类”理解成“比锁快”。工程上更准确的说法是：
- 原子类 = **用 CAS 做无锁同步**
- 适用条件：冲突不高、临界区短、失败可重试

本篇补齐你大纲里提到但未落成正文的关键点：
- CAS 三步与 ABA
- `Atomic*` / `AtomicReference` 的选择
- `LongAdder` 为什么高并发更快
- 字段更新器（Updater）怎么用、限制是什么
- `volatile` 在这里到底解决什么（可见性 + 有序性）

---

## 1. CAS 是什么（Compare-And-Swap）

CAS 可以抽象成：
- 读出旧值 `expected`
- 计算新值 `newValue`
- 原子地：如果当前值仍等于 `expected`，则写入 `newValue`，否则失败

工程含义：
- **失败是常态**：高竞争下会频繁失败并自旋重试，CPU 会被烧掉

---

## 2. ABA 问题：什么时候是问题

ABA：
- 线程 1 读到值 A
- 线程 2 把 A 改成 B，又改回 A
- 线程 1 CAS 发现还是 A，于是认为“没变”，成功更新

什么时候会出事：
- 值“相同”但语义已经变了（典型：无锁栈/无锁链表的节点复用）

什么时候通常不是问题：
- 你关心的是“最终值”，而不是“期间是否发生变化”（很多计数/开关场景）

解决方案：
- `AtomicStampedReference`：加版本号 stamp
- `AtomicMarkableReference`：加 boolean mark（适合“是否删除/是否标记”的语义）

---

## 3. AtomicInteger/Long vs LongAdder：为什么高并发下 LongAdder 更快

`AtomicLong`：所有线程围绕一个热点变量 CAS
- 高冲突下：失败重试次数上升 → 吞吐下降

`LongAdder`：分散热点
- 内部维护 base + cells（分段计数）
- 冲突时把更新分摊到不同 cell，上层 `sum()` 汇总

工程取舍：
- `LongAdder` 适合：高并发统计（QPS、计数器）
- `AtomicLong` 适合：需要“每次读取都强一致”的场景（`get()` 立即就是精确值）

注意：
- `LongAdder.sum()` 不是一个“强一致快照”（汇总期间仍可能并发变化）

---

## 4. 字段更新器（AtomicFieldUpdater）：少对象、少分配

典型场景：
- 你有大量对象，每个对象一个计数/状态字段
- 如果为每个对象都创建 `AtomicInteger`，会产生大量额外对象
- 改用 updater：对对象的某个 volatile 字段做原子更新

示例：

```java
class Node {
    volatile int state;
}

AtomicIntegerFieldUpdater<Node> UPDATER =
        AtomicIntegerFieldUpdater.newUpdater(Node.class, "state");

Node n = new Node();
boolean ok = UPDATER.compareAndSet(n, 0, 1);
```

限制（必须记住）：
- 字段必须是 `volatile`
- 不能是 `static`
- 不能是 `final`
- 访问权限要允许 updater 反射访问（通常是 `public` 或同包可见）

---

## 5. volatile 在原子类里到底干了什么

常见误区：
- “volatile 保证原子性”——不对

更准确：
- volatile 保证 **可见性**：写入对其他线程尽快可见
- volatile 还提供一定的 **有序性**：禁止特定重排序（通过内存屏障语义）

在原子类里：
- CAS 提供“更新的原子性”
- volatile 提供“读写的可见性/有序性”

这也是为什么字段更新器要求字段是 volatile。

---

## 6. 经典落地：DCL 为什么一定要 volatile

双重检查锁（DCL）常见写法：

```java
class Singleton {
    private static volatile Singleton instance;

    public static Singleton getInstance() {
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

原因（直觉版）：
- `new Singleton()` 不是一个原子操作
- 可能发生“先把引用写出去、再初始化对象”的重排序
- 另一个线程看到 `instance != null` 时，拿到的是“半初始化对象”

volatile 用来禁止这种危险重排序，并保证初始化对读线程可见。

---

## 7. 总结：原子类选型建议

- 简单计数：低并发用 `AtomicLong`，高并发统计用 `LongAdder`
- 引用更新：`AtomicReference`，涉及 ABA 用 `AtomicStampedReference`
- 大量对象字段：用 `Atomic*FieldUpdater` 减少额外对象开销
- 冲突非常高/临界区复杂：不要硬上 CAS，自旋会烧 CPU；换锁或分段/队列化设计

---

## 面试题 / Checklist

- CAS 的三步语义是什么？为什么说“失败是常态”？
- ABA 什么时候是问题？`Stamped` 与 `Markable` 的适用差异？
- `LongAdder` 为什么在高并发计数更快？它的读语义有什么取舍？
- FieldUpdater 有哪些限制（volatile/static/final/可见性）？
- volatile 在原子类语境里解决什么问题？为什么不能替代 CAS/锁？
- DCL 为什么必须加 volatile？不加会出现什么问题？
