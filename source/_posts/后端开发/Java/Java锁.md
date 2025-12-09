---
title: Java锁
tags:
  - 面试
categories:
  - 后端开发
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/Java%E9%94%81.webp
hidden: false
updated: 2025-12-09 22:24
abbrlink: 503970b4
date: 2025-12-08 20:29:33
sticky:
---
Java 中的锁机制经历了从重型到轻量，从单一到多元的发展历程。要深入理解它们，不能只背诵概念，必须结合 **JVM 内存模型 (JMM)**、**对象头 (Mark Word)** 以及 **AQS (AbstractQueuedSynchronizer)** 的底层原理。

以下是对 Java 各类锁的深度解析，涵盖 JVM 层面的锁优化、JUC 显式锁以及分布式环境下的锁策略。 

---
### 一、 宏观分类：锁的特性视角

在深入具体实现之前，我们需要建立一个清晰的分类体系。这些术语描述的是锁的**特性**或**设计思想**，而非具体的类。

| **锁分类**    | **描述**                     | **代表实现**                               | **适用场景**     |
| ---------- | -------------------------- | -------------------------------------- | ------------ |
| **乐观锁**    | 假设没有冲突，操作时检测数据是否被修改 (CAS)。 | `AtomicInteger`, 数据库版本号                | 读多写少，竞争不激烈   |
| **悲观锁**    | 假设总有冲突，操作前先锁定。             | `synchronized`, `ReentrantLock`        | 写多读少，竞争激烈    |
| **可重入锁**   | 允许同一个线程多次获取同一把锁，防止死锁。      | `synchronized`, `ReentrantLock`        | 递归调用，父子类方法调用 |
| **公平锁**    | 严格按照请求顺序获取锁 (FIFO)。        | `ReentrantLock(true)`                  | 需要防止线程饥饿     |
| **非公平锁**   | 允许插队，吞吐量更高，但可能导致饥饿。        | `synchronized`, `ReentrantLock(false)` | 追求高性能 (默认)   |
| **共享/独占锁** | 锁是只能被一个线程持有，还是可以被多个线程共享。   | `ReentrantReadWriteLock`               | 读写分离场景       |

---

### 二、什么是可重入？

在并发编程中，**可重入性** 是指：

> 如果一个线程已经持有了某个锁，当它试图再次获取这把**相同的锁**时，可以直接成功，而不会被自己阻塞。

```Java
class Counter {
    private int count = 0;

    // 1. 外部方法：加 1
    public synchronized void increment() {
        // 第一次获取锁 (Monitor Lock) 成功，计数器 = 1
        count++;
        System.out.println("Increment 第一次获取锁，count=" + count);
    }

    // 2. 内部方法：安全地加 2
    public synchronized void safeIncrement() {
        // 线程 T 第一次进入此方法，获取锁成功，计数器 = 1

        increment(); // 调用了另一个同步方法！
        // 线程 T 再次尝试获取锁，**如果不可重入，线程会死锁**。
        // 但因为是可重入的，线程 T **直接再次获取成功，计数器 = 2**。

        increment(); // 再次调用同步方法
        // 线程 T 第三次尝试获取锁，**再次获取成功，计数器 = 3**。
        
        System.out.println("SafeIncrement 最终释放锁，count=" + count);
        // 线程 T 退出方法，锁的重入计数器归零，锁被真正释放。
    }
}

// 假设线程 T 调用：
new Counter().safeIncrement();
```
- **非重入锁的简单实现：** 锁只检查 `isLocked` 状态，不关心是哪个线程锁定的。
- **重入锁的实现（如 `ReentrantLock`）：** 锁不仅检查 `isLocked` 状态，还会检查**当前持有锁的线程 ID** 是否是自己。如果是自己，则简单地增加一个重入计数器，而不是阻塞。
---

### 三、 JVM 内置锁：Synchronized (关键字)

在 Java 6 之前，`synchronized` 被称为“重量级锁”，因为它依赖于操作系统的 Mutex Lock，涉及用户态和内核态的切换，开销极大。但在 Java 6 之后，JVM 引入了**锁升级 (Lock Escalation)** 机制，使其性能大幅提升。

![Synchronized 原理](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/synchronized.webp)

#### 1. 锁升级过程

锁的状态保存在 [[JUC#2. 对象头 (Object Header) 与 Mark Word| 对象头（Object Header）]]  的 **Mark Word** 中。

- **偏向锁 (Biased Lock):**
    - **原理:** 假设只有一个线程在访问。当线程第一次访问同步块时，CAS 修改 Mark Word 记录线程 ID。后续该线程进入无需同步。
    - **现状:** 在 JDK 15+ 中，偏向锁默认已禁用（`UseBiasedLocking`），因为在现代高并发应用中，偏向锁撤销的开销往往大于收益。
- **轻量级锁 (Lightweight Lock):**
    - **原理:** 当有第二个线程竞争偏向锁时，升级为轻量级锁。线程在栈帧中创建 Lock Record，通过 CAS 尝试将 Mark Word 替换为指向 Lock Record 的指针。
    - **自旋 (Spin):** 如果 CAS 失败，线程不会立即阻塞，而是自旋（空循环）等待，期望持有锁的线程很快释放。
- **重量级锁 (Heavyweight Lock):**
    - **原理:** 自旋超过一定次数（自适应自旋）或竞争加剧，锁膨胀为重量级锁。此时 Mark Word 指向 **ObjectMonitor**，未获得锁的线程进入阻塞队列 (`EntryList`)，挂起并等待操作系统唤醒。

#### 2. 最佳实践

- **不要过早优化:** 现在的 `synchronized` 性能非常强劲，且语法简洁，不易出错（自动释放）。在非极高并发场景下，它是首选。

---

### 四、 JUC 显式锁：java.util.concurrent.locks

JUC 锁的核心基石是 **AQS (AbstractQueuedSynchronizer)**。AQS 使用一个 `volatile int state` 变量表示同步状态，并维护一个 FIFO 的双向队列（CLH 变体）来管理等待线程。

#### 1. ReentrantLock (可重入锁)

比 `synchronized` 更加灵活，提供了 ：
-  `tryLock()` (尝试获取，不等待)
- `lockInterruptibly()` (可中断) 等功能。

```Java
import java.util.concurrent.locks.ReentrantLock;
import java.util.concurrent.TimeUnit;

public class ReentrantLockDemo {
    // 默认是非公平锁，吞吐量通常高于公平锁
    private final ReentrantLock lock = new ReentrantLock();

    public void safeMethod() {
        try {
            // 尝试等待锁最多 500ms
            if (lock.tryLock(500, TimeUnit.MILLISECONDS)) {
                try {
                    // 临界区业务逻辑
                    processBusiness();
                } finally {
                    // 必须在 finally 块中释放锁，否则异常会导致死锁
                    lock.unlock();
                }
            } else {
                // 处理无法获取锁的情况（降级策略）
                handleFallback();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private void processBusiness() {}
    private void handleFallback() {}
}
```

#### 2. ReentrantReadWriteLock (读写锁)

适用于**读多写少**的场景。

- **读锁 (共享锁):** 多个线程可以同时持有读锁。
- **写锁 (独占锁):** 写锁被持有时，所有读锁和其他写锁都被阻塞。
- **锁降级:** 允许持有写锁的线程获取读锁，然后释放写锁，从而降级为读锁。
- **公平性与饥饿问题**:
>`ReentrantReadWriteLock` 默认是非公平的，它**可能会导致写饥饿（Writer Starvation）**
> 
>**写饥饿：** 当有大量的读线程持续请求读锁时，如果新的读请求不断插队，写线程可能会长时间无法获取写锁，导致写入操作长时间得不到执行。
> 
> 可以通过构造函数 `new ReentrantReadWriteLock(true)` 创建**公平锁**来缓解饥饿问题，但公平锁会引入额外的开销，降低整体吞吐量。因此，**在大多数高性能应用中，通常使用默认的非公平模式**。

```Java
import java.util.concurrent.locks.ReentrantReadWriteLock;
import java.util.concurrent.locks.Lock;

public class DataCache {
    private final ReentrantReadWriteLock rwLock = new ReentrantReadWriteLock();
    // 分别获取读锁和写锁
    private final Lock readLock = rwLock.readLock();
    private final Lock writeLock = rwLock.writeLock();
    
    private volatile Object data; // 共享数据

    // 读操作：允许多个线程并发访问
    public Object readData() {
        readLock.lock(); // 获取读锁
        try {
            System.out.println(Thread.currentThread().getName() + " 正在读取数据...");
            return data;
        } finally {
            readLock.unlock(); // 释放读锁
        }
    }

    // 写操作：排他性访问
    public void writeData(Object newData) {
        writeLock.lock(); // 获取写锁
        try {
            System.out.println(Thread.currentThread().getName() + " 正在写入数据...");
            this.data = newData;
        } finally {
            writeLock.unlock(); // 释放写锁
        }
    }
}
```

#### 3. StampedLock (JDK 8+ 高性能读写锁)

它是 `ReentrantReadWriteLock` 的加强版。引入了 **乐观读 (Optimistic Read)** 策略，在读操作期间不阻塞写操作，极大地提高了吞吐量。

**注意:** `StampedLock` **不可重入**，且不支持 `Condition`，使用稍复杂。

`StampedLock` 是 Java 8 在 `java.util.concurrent.locks` 包中引入的一种**新的、更高性能的锁机制**，旨在作为 `ReentrantReadWriteLock` 的替代品，尤其是在读操作远多于写操作的场景中。

它通过返回一个被称为 **“Stamp”（时间戳/标记）** 的整数值来管理锁状态，这个 Stamp 是锁状态的凭证。

##### 🎯 `StampedLock` 的三大模式

`StampedLock` 提供了三种模式，允许开发者在性能和安全性之间进行权衡：

|**模式**|**方法**|**特性**|
|---|---|---|
|1. **乐观读（Optimistic Read）**|`tryOptimisticRead()`|**非阻塞**。不获取锁，线程可以自由读取数据。它假设在读取期间，没有其他线程会写入数据。|
|2. **悲观读（Pessimistic Read）**|`readLock()`|**阻塞**。与 `ReentrantReadWriteLock` 的读锁类似，是共享锁。|
|3. **独占写（Exclusive Write）**|`writeLock()`|**阻塞**。与 `ReentrantReadWriteLock` 的写锁类似，是排他锁。|

---

##### 💡 核心机制：乐观读与验证

`StampedLock` 的高性能主要来源于其**乐观读**机制。

###### 1. 乐观读取 (`tryOptimisticRead()`)

1. **获取 Stamp：** 线程调用 `long stamp = lock.tryOptimisticRead();` 获取一个当前的锁状态 Stamp。
2. **读取数据：** 线程在不持有任何锁的情况下，直接读取共享变量。
3. **验证 Stamp：** 读取完成后，线程调用 `lock.validate(stamp)` 来验证 Stamp 是否有效。

- **如果验证成功 (`validate(stamp)` 返回 `true`)：** 表明在线程读取数据的整个过程中，没有其他线程获得写锁进行修改。读取的数据是有效的，操作完成。
- **如果验证失败 (`validate(stamp)` 返回 `false`)：** 表明在读取期间，有其他线程获取了写锁并可能修改了数据。此时，乐观读取失败，线程必须**退化（Fallback）**到悲观读取模式重新尝试。

###### 2. 悲观读 (`readLock()`)

如果乐观读取失败，或者操作本身需要更强的安全性保证，线程必须退化到悲观读模式：

1. 调用 `long stamp = lock.readLock();` 获取悲观读锁。
2. 在 `try...finally` 中执行读取操作。
3. 在 `finally` 中调用 `lock.unlockRead(stamp);` 释放读锁。

###### 3. 独占写 (`writeLock()`)

写操作是排他的，它会阻塞所有读锁和写锁。

1. 调用 `long stamp = lock.writeLock();` 获取写锁。
2. 在 `try...finally` 中执行写入操作。
3. 在 `finally` 中调用 `lock.unlockWrite(stamp);` 释放写锁。

---

##### 🆚 `StampedLock` 与 `ReentrantReadWriteLock` 的主要区别

|**特性**|**StampedLock**|**ReentrantReadWriteLock**|
|---|---|---|
|**读模式**|**三种**：乐观读、悲观读（悲观读可降级自写锁）|**一种**：悲观读|
|**写锁重入性**|**不可重入**。持有写锁的线程不能再次获取写锁。|**可重入**。持有写锁的线程可以再次获取写锁。|
|**性能**|**更高**。乐观读几乎没有同步开销，写锁优化了缓存一致性协议。|**较低**。读写都需要通过 AQS 队列机制。|
|**中断支持**|**支持**。提供了 `try...Lock()` 系列方法，如 `tryReadLock()` 和 `tryWriteLock()`。|**支持**。通过 `lockInterruptibly()` 实现。|

##### ⚠️ 注意事项

由于 `StampedLock` 引入了乐观读和不可重入的写锁，它在使用上比 `ReentrantReadWriteLock` 更复杂，需要注意以下几点：

1. **写锁不可重入：** 如果一个线程在持有写锁的情况下再次尝试获取写锁，它将**阻塞自身**，导致死锁。
2. **必须使用 Stamp：** 在释放锁（`unlockRead(stamp)` 或 `unlockWrite(stamp)`）时，**必须**传入获取锁时返回的 Stamp 值。
3. **乐观读的失败处理：** 如果乐观读验证失败，必须退化到悲观锁模式重新执行，否则可能读取到不一致的数据。

总而言之，`StampedLock` 通过乐观读提供了**极高的读取并发性**，是 Java 并发工具箱中针对读多写少场景的有力武器。

```Java
import java.util.concurrent.locks.StampedLock;

public class Point {
    private double x, y;
    private final StampedLock sl = new StampedLock();

    // 乐观读模式
    public double distanceFromOrigin() {
        long stamp = sl.tryOptimisticRead(); // 获得一个乐观读戳
        double currentX = x, currentY = y;   // 拷贝变量到本地堆栈

        // 检查在读取期间是否有写操作发生
        if (!sl.validate(stamp)) {
            // 如果校验失败（说明数据被修改过），升级为悲观读锁
            stamp = sl.readLock();
            try {
                currentX = x;
                currentY = y;
            } finally {
                sl.unlockRead(stamp);
            }
        }
        return Math.sqrt(currentX * currentX + currentY * currentY);
    }
}
```

---

### 五、分布式锁 (架构视角)

在微服务架构（Spring Cloud）中，JVM 内部的锁只能控制单个实例的并发。跨服务的资源互斥必须使用分布式锁。

#### 1. Redis 分布式锁 (Redisson)

这是 Spring 生态中最主流的方案。不要自己手写 `setnx`，因为很难处理好锁续期（WatchDog 机制）和原子性问题。

**Redisson 架构流:**

代码段

```
sequenceDiagram
    participant Client as Service A
    participant Redis as Redis Master
    participant Watchdog as Redisson Watchdog

    Client->>Redis: Try Lock (Lua Script)
    alt Lock Acquired
        Redis-->>Client: Success
        Client->>Watchdog: Start Watchdog (Renew Expiration)
        Watchdog->>Redis: Renew TTL every 10s
        Client->>Client: Execute Business Logic
        Client->>Redis: Unlock (Lua Script)
        Redis-->>Client: Unlocked
        Client->>Watchdog: Stop Watchdog
    else Lock Busy
        Redis-->>Client: Fail
        Client->>Client: Retry / Give up
    end
```

- **优点:** 性能极高，实现简单。
- **缺点:** 在 Redis 集群的主从切换（Failover）间隙，可能出现锁丢失（Redlock 算法虽然解决了这个问题，但争议较大且复杂，通常建议接受 CP 模型的 Zookeeper 或 强一致性数据库锁）。

#### 2. Zookeeper 分布式锁 (Curator)

- **原理:** 利用临时顺序节点（Ephemeral Sequential Nodes）。
- **优点:** CP 模型，强一致性，可靠性高于 Redis。
- **缺点:** 性能略逊于 Redis，频繁创建删除节点对 ZK 集群压力大。

---

### 六、专家建议：如何在 Spring 中选择锁？

作为架构师，我遵循以下决策树：

1. **单体应用 / 纯内存操作:**
    
    - 首选 `synchronized`（简单，JVM 优化好）。
    - 如果需要超时机制或非阻塞获取：用 `ReentrantLock`。
    - 如果是极端的读多写少（如缓存读取）：用 `StampedLock`。
        
2. **分布式环境 / 关键资源互斥:**
    
    - **高性能、容忍极低概率的锁失效:** 使用 **Redis (Redisson)**。这是 90% 互联网业务的选择。
    - **金融级强一致性:** 使用 **Zookeeper** 或 **数据库悲观锁** (`SELECT ... FOR UPDATE`，注意性能瓶颈)。
        
3. **避免死锁 (Deadlock):**
    
    - 始终按照固定的顺序获取锁。
    - 使用 `tryLock` 配合超时机制，永远不要无限等待。
    - 减小锁的粒度（只锁核心代码块，不要锁整个方法）。

>  下一步
> 
> 我可以为你演示 **"如何使用 Spring AOP + Redisson 自定义一个 `@DistributedLock` 注解"**，让你在业务代码中只需一行注解就能实现安全的分布式锁。你需要这个实战示例吗？
