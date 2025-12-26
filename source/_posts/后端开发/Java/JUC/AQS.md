---
title: AQS - AbstractQueuedSynchronizer
date: 2025-12-12 10:07:45
tags:
  - 面试
  - JUC
categories:
  - 后端开发
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/AQS.webp
sticky:
hidden: false
updated: 2025-12-26 15:59
---
## AQS - Java 8

这是一个非常好的课题。AQS (AbstractQueuedSynchronizer) 是 Java 并发包 (`java.util.concurrent`) 中许多同步组件（如 ReentrantLock, CountDownLatch, Semaphore）的基石。理解了它，就理解了 Java 并发的半壁江山。

我将生成两张 Excalidraw 风格的图片来辅助讲解：

1. **AQS 宏观内部结构图**：展示 State、持有线程以及 CLH 等待队列的整体关系。
2. **AQS 核心流程与状态转换图**：展示一个线程尝试获取锁失败后，如何进入队列、改变前驱节点状态以及最终被唤醒的动态过程。

#### AQS 宏观内部结构图

这一张图展示了 AQS 是如何通过一个共享资源状态 (`state`) 和一个先进先出的等待队列 (CLH Queue) 来管理线程的。
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-Core-Theory.webp)

#### AQS 核心流程与状态转换图 (Acquire Flow)

这一张图聚焦于动态过程。当一个线程尝试去 "acquire"（获取锁）时，如果成功了会怎样，如果失败了，它在队列中会经历哪些关键状态的变迁。
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-TryAcquire.webp)

### 图文详解 AQS 原理

AQS 的全称是 AbstractQueuedSynchronizer（抽象队列同步器）。它的核心思想是：**如果被请求的共享资源空闲，则将当前请求资源的线程设置为有效的工作线程，并将共享资源设置为锁定状态；如果被请求的共享资源被占用，那么就需要一套线程阻塞等待以及被唤醒时锁分配的机制。**

AQS 使用一个 `int` 类型的成员变量 `state` 来表示同步状态，并使用一个 FIFO（先进先出）队列（即 CLH 队列）来完成资源获取线程的排队工作。

接下来，结合上面生成的两张 Excalidraw 图片进行详细解释。

#### 1. AQS 内部结构详解
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-Core-Theory.webp)

**核心组件：**

- **`volatile int state` (同步状态):**
    - 这是 AQS 的核心。它是一个共享资源，使用 `volatile` 修饰保证线程可见性。
    - 对于互斥锁（如 ReentrantLock），`state = 0` 表示锁是空闲的，`state > 0` 表示锁被占用（数值可能大于1，表示重入次数）。
    - AQS 通过 CAS (Compare-And-Swap) 原子操作来修改这个 `state` 值。
- **`exclusiveOwnerThread` (持有锁的线程):**
    - 在独占模式下，这个变量记录了当前哪个线程成功获取了同步状态。如图中所示，Thread A 成功将 `state` 改为 1，成为了 Owner 并正在运行。
- **CLH 队列 (Wait Queue):**
    - 这是一个双向链表队列。当线程尝试获取资源失败时，会被封装成一个 `Node` 节点加入到这个队列的尾部。
    - **Head (头节点):** AQS 维护一个 `head` 指针。需要注意的是，**队列的第一个节点（Head 指向的节点）通常是一个“哑节点”（Dummy Node），它不代表任何等待的线程**。真正的第一个等待线程是 Head 的后继节点（如图中的 Node 1 / Thread B）。当 Head 的后继节点获取到锁后，它会把自己设置为新的 Head，原有的 Dummy Head 会被 GC 回收。
    - **Tail (尾节点):** AQS 维护一个 `tail` 指针，始终指向队列的最后一个节点。新来的等待线程总是被添加到 tail 的后面。
- **Node (节点结构):**
    - 每个被阻塞的线程都会被封装成一个 `Node` 对象。
    - 它包含关键信息：封装的线程本身 (`thread`)、前驱和后继节点的引用 (`prev`, `next`)，以及一个非常重要的状态字段 `waitStatus`。

#### 2. 内部状态转换与流程详解 

这张图展示了一个线程（比如 Thread B）尝试去获取锁的动态过程，特别是失败后的处理逻辑。
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-TryAcquire.webp)

**流程解析：**

1. **尝试获取 (Try Acquire):**
    
    - 线程 B 开始尝试获取锁。最直接的方式就是执行 CAS 操作，试图将 `state` 从 0 修改为 1。

2. **成功 (Fast Path):**
    
    - 如果 CAS 成功，说明锁是空闲的。线程 B 将 `exclusiveOwnerThread` 设置为自己，然后开始运行。这是最快的路径。
        
3. **失败 (Slow Path) 与入队:**
    
    - 如果 CAS 失败（说明锁被 Thread A 占用了），线程 B 进入慢路径。
    - 它会被封装成一个 `Node` 节点，并使用 CAS 操作安全地加入到 CLH 队列的尾部（`tail` 指向它）。
        
4. **自旋与阻塞 (Spin Loop & Park):**
    
    - 线程 B 入队后，并不是立刻阻塞，而是进入一个自旋循环（Spin Loop Starts）。
    - **检查前驱:** 在循环中，它首先检查自己的前驱节点是不是 Head。如果是，说明它是队列中的第一个等待者，它有资格再次尝试 CAS 获取锁。如果获取成功，则退出循环并运行。
    - **准备阻塞:** 如果前驱不是 Head，或者再次尝试 CAS 失败，线程 B 就准备挂起（Park）自己以节省 CPU 资源。
    - **修改前驱状态 (关键):** 在阻塞之前，线程 B 必须告诉它的前驱节点："老哥，我准备睡了，你执行完后记得叫醒我"。这是通过将前驱节点的 `waitStatus` 修改为 `SIGNAL` (-1) 来实现的。
    - **阻塞 (Park):** 一旦前驱的 `waitStatus` 被成功设置为 `SIGNAL`，线程 B 就会调用 `LockSupport.park()` 将自己阻塞。
        
5. **唤醒 (Unpark & Retry):**
    
    - 当持有锁的线程（Thread A）释放锁时（调用 `unlock()` 或 `release()`），它会检查 Head 节点的后继节点的状态。如果后继节点的 `waitStatus` 是 `SIGNAL`，它就会调用 `LockSupport.unpark()` 唤醒该后继节点（Thread B）。
    - Thread B 被唤醒后，会回到自旋循环中（Unparked, Retry loop），再次尝试获取锁。

## AQS - Java 17

这是一个非常硬核且前沿的问题。很多开发者对 AQS 的理解还停留在 JDK 8 的经典设计上，而 JDK 17（基于 JDK 14 的重构 [JDK-8240818](https://www.google.com/search?q=https://bugs.openjdk.org/browse/JDK-8240818)）对 AQS 进行了**近十年来最大的手术**。

这次重构由 Doug Lea 亲自操刀，核心目的是：**简化代码逻辑**、**减少无谓的 CAS 操作**、以及**更友好的 GC**。

下面为你详细解析 Java 17 中 AQS 的设计变迁与核心逻辑。

---

### 1. 核心数据结构的改变：Node 状态

这是最直观的变化。正如你之前发现的，经典的 `SIGNAL` (-1) 和 `PROPAGATE` (-3) 消失了。

#### JDK 17 中的 Node 状态定义

```Java
abstract static class Node {
    volatile Node prev;       // 前驱节点
    volatile Node next;       // 后继节点
    Thread waiter;            // 绑定的线程
    volatile int status;      // 【关键变化】状态字段名由 waitStatus 变为 status

    // 方法和变量句柄 (VarHandle) ...

    // 状态常量
    static final int WAITING   = 1;          // 表示线程正在等待/挂起
    static final int CANCELLED = 0x80000000; // 负数，表示已取消
    static final int COND      = 2;          // 在条件队列中
}
```

#### 设计意图解读

1. **去除了 `SIGNAL`：**
    
    - **旧版逻辑：** 我（当前节点）要睡觉，必须修改**前驱节点**的状态为 `SIGNAL`。这导致了多余的内存屏障和 CAS 竞争（因为前驱节点可能正在被别人修改，或者正在释放）。
    - **新版逻辑：** 我要睡觉，我把**自己**的状态设为 `WAITING` 即可。我不再需要告诉前驱节点“请叫醒我”，因为前驱节点释放时，会有责任检查后继节点。
        
2. **去除了 `PROPAGATE`：**
    
    - **旧版逻辑：** 用于共享锁（Shared）的唤醒传播。
    - **新版逻辑：** 传播逻辑被内联到了 `acquireShared` 的代码流中，不再依赖节点状态位来传递信息。
        
3. **`CANCELLED` 变为负数：**
    
    - 利用二进制的高位（符号位）。判断节点是否取消，只需要 `status < 0`，比之前的 `== CANCELLED` 更快且逻辑更统一。

---

### 2. 核心流程重写：Acquire (加锁)

这是逻辑变动最大的地方。旧版的 `acquireQueued` 方法被移除（或者说逻辑被打散），取而代之的是更扁平化的循环。

我们来看 JDK 17 中 `acquire` 的伪代码逻辑重构：

```Java
// JDK 17 AQS acquire 方法逻辑简化版
final int acquire(Node node, int arg, boolean shared, ...) {
    Thread current = Thread.currentThread();
    byte p = 0; // 0: 初始, 1: 前驱是 head, 2: 需要 park
    int waitStatus = 0; // 局部变量缓存状态

    for (;;) {
        // 1. 尝试清理已被取消的前驱节点 (Clean Queue)
        if (node != null && node.prev != tail && node.prev.status < 0) {
            cleanQueue(); // 激进的清理策略
        }
        
        // 2. 如果前驱是 Head，尝试获取锁 (Spin/TryAcquire)
        if (p == 0 || (p == 1 && node.prev == head)) {
             if (tryAcquire(arg)) {
                 // 拿到锁了！设置 Head，返回
                 if (node != null) {
                     node.waiter = null;
                     head = node;
                 }
                 return 0;
             }
        }
        
        // 3. 准备入队 (Lazy Initialization)
        if (node == null) {
            node = new Node();
            node.waiter = current;
            continue; 
        }
        
        // 4. 设置自己的状态为 WAITING
        if (waitStatus == 0) {
            // 注意：这里只改自己，不像 JDK 8 去改前驱的 SIGNAL
            waitStatus = WAITING; 
            node.status = WAITING;
            continue;
        }
        
        // 5. 挂起线程 (Park)
        LockSupport.park(this);
        
        // 6. 醒来后的清理
        waitStatus = 0; // 清除等待状态
        if (Thread.interrupted()) return 1; // 处理中断
    }
}
```

#### 关键改进点：

1. **不再依赖前驱状态：** 线程只关心自己的 `status` 是否为 `WAITING`。
2. **减少 CAS：** 旧版入队往往需要多次 CAS（一次改前驱状态，一次入队），新版通过局部变量控制，尝试减少对共享内存的写入。
3. **惰性节点创建：** 注意代码中的 `if (node == null)`。如果第一次 `tryAcquire` 就成功了，甚至都不会创建 `Node` 对象！这在低竞争场景下极大减少了垃圾对象的产生。

---

### 3. 核心流程重写：Release (释放)

释放逻辑相对变化较小，但适配了新的状态定义。

```Java
public final boolean release(int arg) {
    if (tryRelease(arg)) {
        signalNext(head); // 唤醒后继
        return true;
    }
    return false;
}

private static void signalNext(Node h) {
    Node s;
    if (h != null && (s = h.next) != null && s.status != 0) {
        // 后继节点存在，且状态不是 0 (说明可能是 WAITING)
        s.getAndUnsetStatus(WAITING); // 清除 WAITING 状态
        LockSupport.unpark(s.waiter); // 唤醒
    } else {
        // 如果 next 指针失效或者状态不对，遍历链表寻找合法的后继
        // (这部分逻辑和 JDK 8 一样，从 tail 往回找)
        forkSignalNext(h); 
    }
}
```

逻辑解读：

释放锁的线程（Head）不需要检查自己是不是 SIGNAL。它假设只要后继节点存在，就尝试唤醒它。后继节点醒来后，会检查自己是否真的拿到了锁。

---

### 4. 总结：Java 17 AQS vs Java 8 AQS 对比表

|**特性**|**Java 8 (Classic)**|**Java 17 (Modern)**|**优势 (Java 17)**|
|---|---|---|---|
|**关键状态**|`SIGNAL (-1)`, `PROPAGATE (-3)`|`WAITING (1)`|语义更清晰，去除冗余状态|
|**挂起条件**|必须把前驱设为 `SIGNAL`|把自己设为 `WAITING`|减少对前驱节点的内存争用 (Cache Contention)|
|**Node 创建**|`addWaiter` 立即创建|循环中惰性创建 (`Lazy`)|**无竞争时零对象分配**，降低 GC 压力|
|**取消判断**|`waitStatus > 0`|`status < 0` (符号位)|位运算判断更高效|
|**底层工具**|`Unsafe` 类|`VarHandle`|更安全、标准化的内存访问 API|
|**代码结构**|嵌套深，逻辑分散 (`acquireQueued`)|扁平化循环，逻辑集中|可读性提升，更易维护|

### 你的理解修正

回到你之前的逻辑链条，在 Java 17 中是这样的：

1. **入队**：Node B 进来了。
2. **准备挂起**：Node B 发现抢不到锁。它**不需要**去看 Node A 的脸色（不需要改 A 为 SIGNAL）。
3. **设置状态**：Node B 把自己的 `status` 设为 `WAITING`。
4. **挂起**：Node B 睡觉。
5. **唤醒**：Node A (Head) 释放锁。它看了一眼 next (Node B)，发现 B 是 `WAITING` 或者是初始状态但非取消，直接 `unpark(B)`。

这种设计使得 AQS 在高并发下的吞吐量有了一定提升，同时也降低了代码的复杂度。

下一步：

既然已经聊到了 VarHandle 和底层重构，你是否对 JDK 9 引入的 VarHandle 相比 Unsafe 到底好在哪里感兴趣？它是 Java 17 AQS 实现的基础。

## 核心概念

### 同步队列和条件队列

理解AQS中的同步队列和条件队列，关键在于把握它们的分工与协作。简单来说，**同步队列是所有等待锁的线程的“大本营”，而条件队列则是等待某个特定条件成立的线程的“专用休息室”**。下面这个表格能帮你快速抓住它们的核心区别。

|特性维度|同步队列 (Sync Queue)|条件队列 (Condition Queue)|
|---|---|---|
|**主要目的**​|实现锁的互斥访问，解决“谁能进入临界区”的问题。|实现线程间协作，等待特定条件，解决“何时才能执行”的问题。|
|**队列数量**​|一个AQS实例只有一个同步队列。|一个AQS实例可以通过多个ConditionObject创建多个条件队列。|
|**数据结构**​|双向链表，通过`prev`和`next`连接节点。|单向链表，通过`nextWaiter`连接节点。|
|**线程状态**​|等待获取锁。节点`waitStatus`主要涉及`SIGNAL`, `CANCELLED`等。|等待条件满足。节点`waitStatus`为`CONDITION`。|
|**与锁的关系**​|获取锁失败时，线程加入此队列，此时**未持有锁**。|调用`await()`时，线程已持有锁，该方法会**释放当前锁**，然后线程才加入此队列。|

#### 🔄 工作原理与流程互动

光知道区别还不够，我们来看看它们具体是如何工作并相互配合的。

- **同步队列的工作流程**
    
    当线程尝试获取锁（如调用`lock.lock()`）失败时，AQS会将其包装成一个Node节点，**放入同步队列的尾部进行排队等待**。当前线程释放锁时，它会唤醒同步队列中头节点的后继节点（如果存在）。被唤醒的线程会尝试获取锁，成功则出队并继续执行。
    
- **条件队列的工作流程**
    
    当线程持有锁之后，发现某个业务条件（如队列已满）不满足，可以调用`condition.await()`方法。这时，当前线程会**被包装成Node节点并加入到对应的条件队列中**，同时**释放其持有的锁**，然后挂起。当其他线程使条件成立（如消费者从满的队列中取走一个元素）并调用`condition.signal()`或`signalAll()`时，会将**条件队列中的（一个或全部）节点转移到同步队列的尾部**，等待重新获取锁。这些线程在同步队列中成功获取锁后，会从之前`await()`的位置继续执行。

这个“节点从条件队列转移到同步队列”的过程，是两者协同工作的核心。这就好比线程从“专用休息室”（条件队列）被叫出来后，必须到“大门口”（同步队列）重新排队，才能再次进入工作区。

#### ⚖️ 核心区别与内在联系

基于以上内容，我们可以进一步概括：

- **核心区别**：两者最根本的不同在于职责。同步队列是**锁机制的核心**，管理的是一切等待获取锁的线程。条件队列是**线程间通信机制**，用于管理那些已经拿到锁，但因某个特定条件不满足而需要暂时放弃锁的线程。这也解释了为何一个锁可以有多个条件队列，因为等待的条件可以多种多样（如“非满”和“非空”）。
- **内在联系**：条件队列**依赖于同步队列**。一个线程要想使用条件队列的`await`或`signal`方法，**必须首先获得与该条件队列关联的锁**。条件队列中的线程被唤醒后，必须进入同步队列去重新竞争锁。它们共同构成了AQS中复杂的同步与协作机制。

#### 💡 实际应用与价值

理解这两者有助于你在实际编程中做出更佳选择。

- **`synchronized`的局限**：在`synchronized`内置锁的监视器（Monitor）模型中，相当于只有一个隐式的同步队列和一个隐式的等待集合（类似条件队列）。这意味着多个不同的等待条件（比如生产者和消费者）的线程都混在同一个等待集合中，当调用`notifyAll()`时，会唤醒所有等待线程，即使其中一部分线程的条件并未满足，这会带来不必要的性能开销。
- **`Lock`+ `Condition`的优势**：通过创建多个`Condition`对象（如`notFull`和`notEmpty`），可以实现**精准通知**。唤醒操作只针对等待特定条件的线程，大大减少了不必要的线程竞争和上下文切换，提升了程序效率。这种设计特别适用于实现资源池、阻塞队列等复杂的同步结构。

希望这些解释能帮助你清晰地理解同步队列和条件队列。如果你对某个特定同步器（如`ReentrantLock`或`ArrayBlockingQueue`）的内部细节感兴趣，我们可以继续深入探讨。

---

# 面试题 / Checklist

- AQS 的 `state` 表示什么？独占/共享模式下语义如何变化？
- AQS 等待队列（CLH 变体）里 head/tail、“哑节点”的意义是什么？
- 为什么 AQS 要用 `LockSupport.park/unpark` 而不是 `wait/notify`？
- `Condition.await()` 为什么必须先持有锁？await 期间发生了什么（释放锁、入条件队列、转同步队列）？
- 公平锁与非公平锁在 AQS 层面主要差别体现在哪里？
- 解释一次 acquire 失败后的典型流程：入队、自旋、park、unpark、重试。
- JDK 17 AQS 相对 JDK 8 的关键变化有哪些（status/WAITING、减少前驱争用、VarHandle）？