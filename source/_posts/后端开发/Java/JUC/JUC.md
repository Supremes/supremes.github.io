---
title: JUC并发编程
tags:
  - 面试
  - JUC
categories:
  - 后端开发
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/JUC.webp
hidden: false
updated: 2025-12-26 15:58
abbrlink: eb9166f8
date: 2025-12-04 21:00:06
sticky: "9"
---
JUC 包是 Java 并发编程的基石，包含了线程池、锁、原子操作、并发集合等核心组件。

---

# 本站 JUC 导航

建议阅读顺序：基础（JMM/中断/等待唤醒）→ AQS/锁 → 同步器/容器队列 → 线程池与调参 → CompletableFuture 工程化。

- [[线程与中断]]：interrupt 语义、阻塞点表现、优雅取消模板
- [[等待与唤醒机制]]：wait/notify、Condition、LockSupport 对照
- [[原子类与CAS]]：CAS/ABA、LongAdder、FieldUpdater、volatile 落地与常见坑
- [[AQS]]：AQS 原理与 JDK 17 重构要点
- [[Java锁]]：synchronized 锁升级、显式锁、读写锁、StampedLock、分布式锁视角
- [[同步器]]：CountDownLatch / CyclicBarrier / Semaphore / Phaser / Exchanger 选型与坑
- [[并发容器与队列]]：CopyOnWrite、SkipList、BlockingQueue 家族、弱一致迭代
- [[线程池]]：ThreadPoolExecutor 核心流程与关键组件
- [[线程池调参]]：参数联动、背压/拒绝策略、排障 checklist
- [[CompletableFuture工程实践]]：执行器隔离、超时、异常治理、上下文传播

下面是JUC 源码学习的大纲，并提供了一些学习建议：

------

### JUC 源码学习大纲

**第一阶段：基础知识回顾与工具准备**

1. **并发基础理论：**
   - **可见性、原子性、有序性：** 深入理解这三大特性及其在并发中的重要性。
   - **JMM (Java Memory Model)：** 了解 Java 内存模型如何保证并发的正确性。
   - **Happens-Before 原则：** 理解它如何定义操作之间的顺序。
   - **锁的原理：** 了解悲观锁、乐观锁，以及自旋锁等概念。
   - **AQS (AbstractQueuedSynchronizer) 概述：** 对 AQS 有一个初步的认识，它是 JUC 许多高级同步器的基石。
   - **CAS (Compare-And-Swap) 原理：** 理解其三步操作和 ABA 问题。
2. **Lombok 与 `@SneakyThrows`：**
   - Lombok 在 JUC 源码中不常用，但如果你在其他项目中大量使用 Lombok，可以了解其原理。
   - `@SneakyThrows`：理解其作用、优缺点及何时使用。
3. **工具准备：**
   - **IntelliJ IDEA：** 最推荐的 IDE，其源码导航和调试功能非常强大。
   - **JAD 或 JD-GUI：** 反编译工具，用于查看字节码（如果需要）。
   - **VisualVM 或 JProfiler：** 性能分析工具，用于观察线程状态、锁竞争等（可选）。
   - **画图工具：** 如 draw. Io, XMind, Excalidraw 等，用于绘制类图、状态转换图。

**第二阶段：核心原子操作与 CAS 深入**

1. `java.util.concurrent.atomic` 包：
   - `AtomicInteger`：
     - **源码分析：** 关注其核心方法 `compareAndSet()`。
     - **底层机制：** 了解它如何利用 `Unsafe` 类的 CAS 操作（`compareAndSwapInt`）。
     - **`volatile` 关键字：** 理解它在这里的作用（保证可见性）。
   - `AtomicLong` / `AtomicBoolean` / `AtomicReference`：
     - 与 `AtomicInteger` 类似，重点理解 `AtomicReference` 如何实现对象引用的原子更新。
   - `AtomicStampedReference` / `AtomicMarkableReference`：
     - **源码分析：** 重点理解它们如何通过版本号（或标记）解决 CAS 的 ABA 问题。
     - **使用场景：** 何时需要考虑 ABA 问题。
   - `AtomicIntegerFieldUpdater` / `AtomicLongFieldUpdater` / `AtomicReferenceFieldUpdater`：
     - **源码分析：** 了解其工作原理（通过反射实现对指定对象的特定字段的原子更新）。
     - **使用限制：** 为什么字段必须是 `volatile` 且不能是 `static` 或 `final`。
   - `LongAdder` / `DoubleAdder` / `LongAccumulator` / `DoubleAccumulator` (Java 8+):
     - **源码分析：** 理解它们如何通过分段（cells）技术，将热点 CAS 竞争分散，提高高并发下的性能。
     - **与 `AtomicLong` 的对比：** 性能优势和适用场景。

**第三阶段：锁的实现基石 - AQS (AbstractQueuedSynchronizer)**

1. **AQS 核心原理：**

   - **内部状态（`state`）：** 如何通过 `volatile int state` 表示同步状态。
   - **FIFO 双向队列：** 理解等待线程如何封装成 `Node` 节点，并排队等待锁。
   - 独占模式与共享模式：
     - 独占模式：

        如 

       ```
       ReentrantLock
       ```

       。

       - `acquire()` / `release()`：如何获取和释放锁。
       - `tryAcquire()` / `tryRelease()`：尝试获取/释放，由子类实现。
     - 共享模式：

        如 

       ```
       Semaphore
       ```

       、

       ```
       CountDownLatch
       ```

       。

       - `acquireShared()` / `releaseShared()`：如何获取和释放共享锁。
       - `tryAcquireShared()` / `tryReleaseShared()`：尝试获取/释放，由子类实现。
   - 条件变量 (`ConditionObject`)：
     - 理解 AQS 内部的条件队列，以及 `await()` / `signal()` / `signalAll()` 的实现。

2. **AQS 典型实现类：**

   - `ReentrantLock`：
     - **源码分析：** 重点看 `Sync` 抽象类 (`NonfairSync` 和 `FairSync`) 的实现。
     - **公平锁与非公平锁：** 它们的区别和实现方式（AQS `tryAcquire` 的差异）。
     - **可重入性：** 如何通过 `state` 计数和当前持有线程来管理。
   - `Semaphore` (信号量)：
     - **源码分析：** 理解它如何基于 AQS 的共享模式实现许可证计数。
     - **`acquire()` / `release()`：** 它们如何与 AQS 的 `acquireShared` / `releaseShared` 交互。
   - `CountDownLatch` (倒计时门闩)：
     - **源码分析：** 理解其 `count` 如何基于 AQS 的共享模式实现计数和等待。
     - **`await()` / `countDown()`：** 它们如何与 AQS 的 `acquireShared` / `releaseShared` 交互。
   - `CyclicBarrier` (循环屏障)：
     - **源码分析：** 它的实现相对复杂，结合了 ReentrantLock 和 Condition。
     - **与 `CountDownLatch` 的区别：** 可重用性和等待所有线程到达。
   - `ReentrantReadWriteLock` (读写锁)：
     - **源码分析：** 核心是 `Sync` 类，如何利用一个 `state` 变量同时表示读锁和写锁（高 16 位和低 16 位）。
     - **读写分离：** 读锁共享，写锁独占的实现细节。
     - **锁降级：** 什么是锁降级，如何实现。

**第四阶段：线程池 (Executor 框架)**

1. **`Executor` 接口层级：**
   - `Executor` -> `ExecutorService` -> `AbstractExecutorService` -> `ThreadPoolExecutor`。
   - **`Callable` 和 `Future`：** 回顾它们与 `ExecutorService` 的关系。
2. **`ThreadPoolExecutor`：**
   - **源码分析：** JUC 中最复杂的类之一。
   - **核心参数：** `corePoolSize`, `maximumPoolSize`, `keepAliveTime`, `TimeUnit`, `workQueue`, `ThreadFactory`, `RejectedExecutionHandler`。深入理解每个参数的作用。
   - **线程池状态：** `RUNNING`, `SHUTDOWN`, `STOP`, `TIDYING`, `TERMINATED`。理解它们的转换。
   - 任务提交流程 (`execute()` 方法)：
     - 如何根据核心线程数、阻塞队列、最大线程数来决定任务的处理方式（直接执行、入队、新建线程）。
   - 工作线程 (`Worker` 类)：
     - 如何复用线程，如何从队列中获取任务。
     - 线程池的生命周期管理。
   - **拒绝策略 (`RejectedExecutionHandler`)：** 理解四种默认策略和自定义策略。
   - **常用的工厂方法 (`Executors`)：** 理解 `newFixedThreadPool`, `newSingleThreadExecutor`, `newCachedThreadPool`, `newScheduledThreadPool` 的底层实现。

**第五阶段：并发集合**

1. **`ConcurrentHashMap`：**
   - **源码分析：** Java 7 (分段锁) 和 Java 8 (CAS + synchronized + 数组 + 链表/红黑树) 的实现差异。重点关注 Java 8。
   - Java 8 实现：
     - **`Node` 数组 + 链表/红黑树：** 数据结构。
     - **`volatile` + CAS：** 如何保证读写可见性和原子性。
     - **`synchronized`：** 内部何时使用 `synchronized` (如 `put` 时的链表/红黑树操作，`resize` 时的扩容)。
     - **扩容机制 (`transfer()` / `helpTransfer()`):** 多线程下的扩容如何实现。
   - **与 `Hashtable` 和 `Collections.synchronizedMap` 的对比。**
2. **`ConcurrentLinkedQueue` (非阻塞队列)：**
   - **源码分析：** 重点理解其非阻塞的入队 (`offer()`) 和出队 (`poll()`) 操作如何基于 CAS 实现。
   - **`head` 和 `tail` 指针：** 如何维护。
   - **使用场景：** 为什么它比基于锁的队列在高并发下性能更好。
3. **`BlockingQueue` 接口：**
   - **理解其阻塞特性：** `put()` 和 `take()` 方法。
   - 典型实现类：
     - **`ArrayBlockingQueue`：** 基于数组，有界，ReentrantLock + Condition 实现。
     - **`LinkedBlockingQueue`：** 基于链表，可选有界，两个 ReentrantLock + 两个 Condition 实现。
     - **`SynchronousQueue`：** 不存储元素的队列，直接将生产者和消费者配对。
     - **`PriorityBlockingQueue`：** 支持优先级的无界阻塞队列。
     - **`DelayQueue`：** 延迟队列。

**第六阶段：CompletableFuture (Java 8)**

1. `CompletionStage` 接口：
   - **理解其设计思想：** 异步计算阶段，链式调用，非阻塞回调。
   - **核心方法分类：** 转换、组合、异常处理等。
2. `CompletableFuture`：
   - **源码分析：** 理解它如何作为 `Future` 和 `CompletionStage` 的实现。
   - **异步工厂方法：** `supplyAsync()`, `runAsync()`, `completedFuture()`, `failedFuture()`。
   - **回调方法：** `thenApply()`, `thenAccept()`, `thenRun()`, `whenComplete()`。
   - **组合方法：** `thenCompose()`, `thenCombine()`, `allOf()`, `anyOf()`。
   - **异常处理：** `exceptionally()`, `handle()`。
   - **执行器 (Executor)：** 理解其异步方法如何使用默认线程池或指定线程池。
   - **内部 `Completion` 链：** 理解其回调如何通过内部 `Completion` 链表实现任务的级联执行。

------

### 学习建议

1. **从宏观到微观：**
   - 首先理解整个 JUC 模块的架构和每个组件的职责。
   - 然后选择一个模块（如 `atomic` 包）深入，接着是 `AQS`，再到其实现类。
   - 不要一开始就钻入细节，否则容易迷失。
2. **带着问题去阅读：**
   - 这个类解决了什么问题？
   - 它是如何保证线程安全的？
   - 它是如何利用 CAS 或锁的？
   - 它的核心数据结构是什么？
   - 它的关键方法是如何实现的？
   - 是否存在性能瓶颈，以及如何优化？
3. **调试是最好的老师：**
   - 不要只看代码，要多使用 IntelliJ IDEA 的调试器。
   - 设置断点，单步执行，观察变量（特别是 `state` 值、队列结构）的变化，这对于理解 AQS 等复杂机制至关重要。
4. **画图辅助理解：**
   - 对于复杂的类（如 AQS、ConcurrentHashMap、ThreadPoolExecutor），尝试绘制它们的内部数据结构图（队列、数组、Node）和状态转换图。
   - UML 类图功能在 IntelliJ IDEA Ultimate 中非常有用。
5. **对照官方文档和相关博客：**
   - Java Doc 是最好的参考资料，它描述了每个类和方法的行为。
   - 网上有很多优秀的 JUC 源码分析文章和视频，可以作为补充材料，但要带着批判性思维去阅读，以官方源码为准。
6. **逐步实践：**
   - 阅读完一个模块后，尝试编写一些简单的示例代码来验证你的理解。
   - 尝试重现一些并发问题，然后观察 JUC 组件如何解决它们。
7. **循序渐进，持之以恒：**
   - JUC 源码内容庞大且复杂，不要期望一口吃成胖子。
   - 每天投入一定的时间，坚持下去，你会逐渐掌握其中的奥秘。

祝你学习顺利！这是一个非常有价值的挑战！

---
# 并发基本原理
## 1. JVM 内存模型 (JMM - Java Memory Model)

JMM 是一种**抽象的概念**（并不是物理存在的内存划分，不要与“堆/栈/方法区”混淆）。它定义了 JVM 如何与计算机内存（RAM）进行交互，主要用于屏蔽不同硬件和操作系统的内存访问差异。

### 核心架构：主内存与工作内存

JMM 规定了所有的变量都存储在 **主内存 (Main Memory)** 中。每条线程还有自己的 **工作内存 (Working Memory)**（可类比为 CPU 缓存或寄存器）。

1. **主内存 (Main Memory):** 所有线程共享，存储实例对象、静态变量等。
2. **工作内存 (Working Memory):** 线程私有。线程在操作变量时，必须先将变量从主内存**拷贝**到自己的工作内存中，进行读取、赋值等操作后，再**写回**主内存。

### JMM 解决的三大并发问题

JMM 的主要目的就是为了解决多线程环境下的以下三个问题：

- **原子性 (Atomicity):** 一个操作是不可中断的。
    - _保障手段: _ `synchronized`, Lock, CAS (Compare-And-Swap).
- **可见性 (Visibility):** 当一个线程修改了共享变量，其他线程能立即看到。
    - _保障手段: _ `volatile`, `synchronized`, `final`.
- **有序性 (Ordering):** 程序执行的顺序按照代码的先后顺序执行（禁止指令重排序）。
    - _保障手段: _ `volatile` (通过内存屏障), `synchronized`.

### Happens-Before 原则

这是 JMM 最核心的概念。如果操作 A "Happens-Before" 操作 B，那么 A 的结果对 B 可见，且 A 的执行顺序在 B 之前。这是判断数据是否存在竞争的依据。

## 2. 对象头 (Object Header) 与 Mark Word

Java 对象在堆内存中的布局分为三块：**对象头 (Header)**、**实例数据 (Instance Data)** 和 **对齐填充 (Padding)**。

**Mark Word** 是对象头中最关键的部分。

![Java Object](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/JavaObject.webp)

### Mark Word 的作用

Mark Word 是一个非固定的数据结构，用于存储对象自身的**运行时数据**。为了在极小的空间内存储更多的信息，它会根据对象的状态复用存储空间。

**它主要存储：**

- **哈希码 (HashCode):** 对象的标识。
- **GC 分代年龄:** 对象经历了多少次 GC。
- **锁状态标志:** 记录锁的类型（偏向锁、轻量级锁、重量级锁）。
- **线程持有的锁:** 指向锁记录或 monitor 的指针。

### Mark Word 的状态流转（锁升级）

在 64 位 JVM 中，Mark Word 的最后 2 位（或 3 位）通常用于标识锁的状态。随着竞争的加剧，锁会从“无锁”状态逐渐升级，且**不可逆**（一般情况）。

| **锁状态**                | **存储内容 (Mark Word)**               | **含义**              | **适用场景**         |
| ---------------------- | ---------------------------------- | ------------------- | ---------------- |
| **无锁 (Normal)**        | HashCode + 分代年龄 + 001              | 对象未被锁定。             | 单线程访问。           |
| **偏向锁 (Biased)**       | **线程 ID** + Epoch + 分代年龄 + 101      | 锁偏向于第一个获得它的线程。      | 只有一个线程反复进入同步块。   |
| **轻量级锁 (Lightweight)** | 指向栈中**Lock Record**的指针 + 00        | 线程通过 CAS 尝试获取锁。     | 线程交替执行，无长时间阻塞。   |
| **重量级锁 (Heavyweight)** | 指向互斥量 **(ObjectMonitor)** 的指针 + 10 | 锁膨胀，未获取锁的线程被阻塞 (挂起)。 | 高并发，竞争激烈，持有锁时间长。 |
| **GC 标记**              | 空 + 11                             | 对象被 GC 标记为待回收。      | 垃圾回收。            |
### Monitor

Java 虚拟机 (HotSpot) 中，每个对象（Object）在内存头部（Mark Word）中都关联着一个 Monitor 对象。Monitor 内部主要包含三个区域，对应线程的不同状态：
![Synchronized 原理](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/synchronized.webp)
- **Entry Set (锁池)**
    - **状态**：`BLOCKED`
    - **功能**：存放所有**争抢锁失败**的线程。当一个线程尝试获取锁但锁已被占用时，会被封装成 ObjectWaiter 对象放入此队列阻塞等待。
- **The Owner (持有者)**
    - **状态**：`RUNNABLE` (持有锁运行中)
    - **功能**：表示**当前获取到锁**的线程。Monitor 中的 `_owner` 指针指向该线程。同一时刻，Monitor 中只能有一个 Owner。
- **Wait Set (等待池)**
    - **状态**：`WAITING` / `TIMED_WAITING`
    - **功能**：存放**主动放弃锁**的线程。当 Owner 线程调用 `wait()` 方法时，会释放锁并进入此区域，等待被 `notify()` 或 `notifyAll()` 唤醒。

---

## 3. 深度连接：JMM 与 Mark Word 的关系

这两者通过 **`synchronized` (同步锁)** 紧密联系在一起。

1. **JMM 的需求:** JMM 规定了多线程访问共享资源时必须保证原子性和可见性。`synchronized` 是实现这一目标的关键字。
2. **Mark Word 的实现:** 当 JVM 执行 `synchronized(obj)` 时，它需要一个地方来记录“谁锁住了这个对象”以及“锁的状态”。**Mark Word 就是这个记录本。**

### 锁升级过程 (示例)

1. **偏向锁阶段:** 线程 A 访问同步块。JVM 检查 Mark Word，发现是无锁，于是将 **线程 A 的 ID** 写入 Mark Word。以后线程 A 再次进入，无需同步，直接放行。
2. **轻量级锁阶段:** 线程 B 来了，发现 Mark Word 里存的是线程 A。产生竞争。JVM 撤销偏向锁，升级为轻量级锁。线程 A 和 B 在自己的栈帧中创建 **Lock Record**，并尝试用 **CAS** 将 Mark Word 更新为指向自己 Lock Record 的指针。
3. **重量级锁阶段:** 线程 B 自旋（CAS）多次失败，或者线程 C 又来了。CAS 竞争太激烈。锁膨胀为重量级锁。Mark Word 修改为指向堆中 **ObjectMonitor** 对象的指针。线程 B 和 C 进入操作系统的阻塞队列（Wait Set），通过操作系统内核互斥量（Mutex）来调度，性能开销最大。

### 总结对比

|**特性**|**JMM (Java 内存模型)**|**Mark Word (对象头)**|
|---|---|---|
|**本质**|**规范/协议**|**数据结构/存储单元**|
|**作用域**|整个 JVM 运行时的并发规则。|单个 Java 对象在堆中的头部。|
|**解决问题**|可见性、原子性、有序性。|存储 HashCode、GC 年龄、锁状态。|
|**关键点**|主内存、工作内存、volatile、Happens-Before。|偏向锁、轻量级锁、重量级锁、CAS。|
|**联系**|JMM 定义的并发规则，底层往往依赖 Mark Word 中的锁标记来实现（特别是 `synchronized`）。||

## 4. AQS (AbstractQueuedSynchronizer) 概述

对 AQS 有一个初步的认识，它是 JUC 许多高级同步器的基石。
## 5. CAS (Compare-And-Swap) 原理

理解其三步操作和 ABA 问题。

---

# CompletableFuture - 异步编程首选

- 支持链式调用
- 支持非阻塞回调

# Atomic 包

提供了一系列原子操作的类，在高并发环境下实现无锁（Lock-free）的线程安全操作。

### `atomic` 包的核心思想：CAS (Compare-And-Swap)

`atomic` 包中的所有原子操作类都是基于 **CAS（Compare-And-Swap）** 这种硬件指令实现的。

**CAS 操作包含三个操作数：**

1. **V (Value)**：要更新的变量的内存位置。
2. **A (Expected)**：期望的旧值。
3. **B (New)**：要设置的新值。

**CAS 的操作逻辑：** 如果内存位置 V 的值等于期望的旧值 A，那么就将 V 的值更新为新值 B。否则，不做任何操作。无论更新成功还是失败，CAS 操作都会返回 V 的当前值（或者布尔值表示是否成功）。

**CAS 的缺点 (ABA 问题)：** 如果一个值从 A 变成了 B，然后又变回了 A。当执行 CAS 操作时，发现当前值是 A，就会成功更新。但实际上，这个值已经被其他线程修改过了。

### **ABA 问题解决方案**：

- 使用 `AtomicMarkableReference`: 带版本号的原子引用。它不仅比较引用是否相同，还会比较版本号是否相同。这可以有效解决 ABA 问题。

  ```java
      private static class Pair<T> {
          final T reference;
          final boolean mark;
  
          private Pair(T reference, boolean mark) {
              this.reference = reference;
              this.mark = mark;
          }
  
          static <T> Pair<T> of(T reference, boolean mark) {
              return new Pair(reference, mark);
          }
      }
  ```

- 使用 `AtomicStampedReference`: 引入 int 类型 stamp 变量，记录值的标记状态，适合更加复杂的场景

  ```java
  private static class Pair<T> {
          final T reference;
          final int stamp;
  
          private Pair(T reference, int stamp) {
              this.reference = reference;
              this.stamp = stamp;
          }
  
          static <T> Pair<T> of(T reference, int stamp) {
              return new Pair(reference, stamp);
          }
      }
  ```

### 累加器（Accumulators）和加法器（Adders）

解决在大量线程更新同一个 `AtomicLong` 或 `AtomicInteger` 时，CAS 操作冲突严重导致性能下降的问题（热点问题）。

- **`LongAdder`**: 专为高并发的 `long` 型计数设计。
- **`DoubleAdder`**: 专为高并发的 `double` 型计数设计。
- **`LongAccumulator`**: 泛化的 `LongAdder`，可以执行任意的二元操作，而不仅仅是加法。
- **`DoubleAccumulator`**: 泛化的 `DoubleAdder`。

---
# AQS

## 队列

AQS 设计中涉及两种队列：

1. 同步队列：核心部分，管理尝试获取锁但失败的线程。
2. 条件队列：与条件变量相关，支持 locks. Condition 接口的操作 -  await 和 signal 方法

### 同步队列

同步队列中每个节点代表一个等待锁的线程，按照 FIFO 的原则排列组织。

| 状态值        | 常量名      | 数值 | 应用场景                                    |
| ------------- | ----------- | ---- | ------------------------------------------- |
| 等待唤醒      | `SIGNAL`    | -1   | 独占锁/共享锁的同步队列，确保后继节点被唤醒 |
| 取消竞争      | `CANCELLED` | 1    | 线程因超时或中断放弃锁竞争                  |
| 条件等待      | `CONDITION` | -2   | 条件队列（如 `Condition.await()`）           |
| 传播释放      | `PROPAGATE` | -3   | 共享模式下传递释放信号（如 `Semaphore`）     |
| 初始化/未使用 | 默认状态    | 0    | 节点刚加入队列时的初始状态                  |

### 条件队列

**Await 方法**

> 调用 Await 方法会释放当前线程持有的锁，并将该线程加入到条件队列中等待被唤醒

1. **必须先持有锁**：调用 `await()` 前，线程必须已经成功获取了锁（即处于同步状态中），否则会抛出异常。
2. **释放锁**：在进入等待之前，线程会**完全释放它所持有的锁**（注意是全部的重入次数）。
3. **构造节点并插入条件队列**：线程会被封装成一个节点（Node），添加到对应的 **条件队列** 中。
4. **阻塞自己**：线程进入等待状态，直到被其他线程通过 `signal()` 或 `signalAll()` 唤醒。
5. **重新竞争锁**：当被唤醒后，线程需要重新去尝试获取锁（此时进入同步队列），只有成功获取锁之后才能从 `await()` 返回。

**Signal 方法**

> 调用 signal 方法，将一个等待在条件队列上线程加入到同步队列，让其准备参与锁的竞争

- `signal()` 会从条件队列中取出一个等待的节点（通常是头节点），将其**转移到同步队列中**。
- 转移完成后，如果同步队列中前驱节点的状态为 `SIGNAL`，那么这个刚转移过来的节点可能会被唤醒（具体由 AQS 调度决定）。
- 只有当这个线程重新获取到锁之后，它才会从 `await()` 返回继续执行。
---
# JUC 包中核心组件

以下是 JUC 包中核心组件的中文解析：

---

### 1. 原子类 (`java.util.concurrent.atomic`)

这些类提供了对单个变量进行**线程安全**操作的能力，而无需使用重量级的 `synchronized` 关键字。它们主要依赖于硬件级别的 **CAS (Compare-And-Swap/比较并交换)** 算法来实现高性能。

- **常见类：** `AtomicInteger`, `AtomicLong`, `AtomicReference`, `LongAdder` (高并发下性能优于 AtomicLong)。

### 2. 锁机制 (`java.util.concurrent.locks`)

提供了比 Java 内置的 `synchronized` 更加灵活的锁和等待机制。

- **`ReentrantLock` (可重入锁)：** 一种互斥锁，功能类似 `synchronized`，但功能更强大（支持公平锁/非公平锁、可中断、可超时）。
- **`ReentrantReadWriteLock` (读写锁)：** 允许多个读线程同时访问，但写线程独占。适合“读多写少”的场景。
- **`Condition`：** 配合 Lock 使用，类似于 `Object` 的 `wait/notify`，可以实现更精细的线程等待与唤醒控制。

### 3. 并发容器 (Concurrent Collections)

为多线程环境优化的集合类，解决了标准集合（如 `HashMap`, `ArrayList`）线程不安全的问题，性能优于使用 `Collections.synchronizedMap`。

- **`ConcurrentHashMap`：** 并发编程中最常用的 Map。早期版本使用分段锁，JDK 8 之后改为 CAS + `synchronized`，性能极高。
	![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/ConcurrentHashMap.webp)
- **`CopyOnWriteArrayList`：** 写入时复制。读操作无锁，写操作时复制新数组。适合“读多写极少”的场景。
- **`BlockingQueue` (阻塞队列)：** 线程池的核心组件。当队列空时取元素会阻塞，满时存元素会阻塞（如 `ArrayBlockingQueue`, `LinkedBlockingQueue`）。

### 4. 线程池 / 执行器框架 (`java.util.concurrent.Executor`)

将任务的提交与执行解耦。在生产环境中，我们极少手动 `new Thread()`，而是使用线程池来管理线程生命周期，复用线程以降低开销。

- [[线程池#ThreadPoolExecutor | ThreadPoolExecutor]]： 线程池的核心实现类，包含核心线程数、最大线程数、拒绝策略等参数。
	![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/ThreadPoolExecutor.webp)
- **`Executors`：** 创建线程池的工厂类（如 `newFixedThreadPool`），但通常建议手动创建 `ThreadPoolExecutor` 以避免 OOM 风险。
- **`Future` & `Callable`：** 相比 `Runnable`，它们允许线程有返回值并能抛出异常。

### 5. 同步工具类 (Synchronizers)

用于协调多个线程之间的同步控制。

- **`CountDownLatch` (倒计时器)：** 让一个或多个线程等待其他线程完成一组操作后再执行（一次性使用）。
- **`CyclicBarrier` (循环栅栏)：** 让一组线程到达一个屏障（同步点）时被阻塞，直到最后一个线程到达屏障，大家才继续运行（可循环使用）。
- **`Semaphore` (信号量)：** 控制同时访问特定资源的线程数量，常用于限流。

---

# 面试题 / Checklist

- 解释 JMM 的三大特性，以及各自常用保障手段。
- Happens-Before 常见规则有哪些？用它如何判断“可见性是否成立”。
- `volatile` 解决什么问题？为什么不能保证复合操作原子性？
- `synchronized` 与 `ReentrantLock` 的核心差异点（可中断、可超时、公平性、Condition）。
- AQS 的 `state` + 队列模型在独占/共享模式下分别如何工作。
- `ThreadPoolExecutor.execute()` 的“三级缓冲”路径与拒绝策略的工程取舍。
- 阻塞队列的选型：有界 vs 无界、`SynchronousQueue` 的语义。
- `CompletableFuture` 默认 commonPool 的风险点与工程规避方案。

