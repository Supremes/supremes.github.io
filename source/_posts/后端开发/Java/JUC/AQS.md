---
title: AQS - AbstractQueuedSynchronizer
date: 2025-12-12 10:07:45
tags:
  - 面试
categories:
  - 后端开发
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/AQS.webp
sticky:
hidden: false
updated: 2025-12-12 10:30
---
这是一个非常好的课题。AQS (AbstractQueuedSynchronizer) 是 Java 并发包 (`java.util.concurrent`) 中许多同步组件（如 ReentrantLock, CountDownLatch, Semaphore）的基石。理解了它，就理解了 Java 并发的半壁江山。

我将生成两张 Excalidraw 风格的图片来辅助讲解：

1. **AQS 宏观内部结构图**：展示 State、持有线程以及 CLH 等待队列的整体关系。
2. **AQS 核心流程与状态转换图**：展示一个线程尝试获取锁失败后，如何进入队列、改变前驱节点状态以及最终被唤醒的动态过程。

### 图片生成

#### 图片 1：AQS 宏观内部结构图

这一张图展示了 AQS 是如何通过一个共享资源状态 (`state`) 和一个先进先出的等待队列 (CLH Queue) 来管理线程的。
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-Core-Theory.webp)

#### 图片 2：AQS 核心流程与状态转换图 (Acquire Flow)

这一张图聚焦于动态过程。当一个线程尝试去 "acquire"（获取锁）时，如果成功了会怎样，如果失败了，它在队列中会经历哪些关键状态的变迁。
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-TryAcquire.webp)

### 图文详解 AQS 原理

AQS 的全称是 AbstractQueuedSynchronizer（抽象队列同步器）。它的核心思想是：**如果被请求的共享资源空闲，则将当前请求资源的线程设置为有效的工作线程，并将共享资源设置为锁定状态；如果被请求的共享资源被占用，那么就需要一套线程阻塞等待以及被唤醒时锁分配的机制。**

AQS 使用一个 `int` 类型的成员变量 `state` 来表示同步状态，并使用一个 FIFO（先进先出）队列（即 CLH 队列）来完成资源获取线程的排队工作。

接下来，结合上面生成的两张 Excalidraw 图片进行详细解释。

#### 1. AQS 内部结构详解 (参考图片 1)

**核心组件：**

- **`volatile int state` (同步状态):**
    - 这是 AQS 的核心。它是一个共享资源
        ![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-Core-Theory.webp)

### 图文详解 AQS 原理

AQS 的全称是 AbstractQueuedSynchronizer（抽象队列同步器）。它的核心思想是：**如果被请求的共享资源空闲，则将当前请求资源的线程设置为有效的工作线程，并将共享资源设置为锁定状态；如果被请求的共享资源被占用，那么就需要一套线程阻塞等待以及被唤醒时锁分配的机制。**

AQS 使用一个 `int` 类型的成员变量 `state` 来表示同步状态，并使用一个 FIFO（先进先出）队列（即 CLH 队列）来完成资源获取线程的排队工作。

接下来，结合上面生成的两张 Excalidraw 图片进行详细解释。

#### 1. AQS 内部结构详解 (参考图片 1)

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

#### 2. 内部状态转换与流程详解 (参考图片 2)

这张图展示了一个线程（比如 Thread B）尝试去获取锁的动态过程，特别是失败后的处理逻辑。

**流程解析：**

1. **尝试获取 (Try Acquire):**
    
    - 线程 B 开始尝试获取锁。最直接的方式就是
		![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/AQS-TryAcquire.webp)

### 图文详解 AQS 原理

AQS 的全称是 AbstractQueuedSynchronizer（抽象队列同步器）。它的核心思想是：**如果被请求的共享资源空闲，则将当前请求资源的线程设置为有效的工作线程，并将共享资源设置为锁定状态；如果被请求的共享资源被占用，那么就需要一套线程阻塞等待以及被唤醒时锁分配的机制。**

AQS 使用一个 `int` 类型的成员变量 `state` 来表示同步状态，并使用一个 FIFO（先进先出）队列（即 CLH 队列）来完成资源获取线程的排队工作。

接下来，结合上面生成的两张 Excalidraw 图片进行详细解释。

#### 1. AQS 内部结构详解 (参考图片 1)

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

#### 2. 内部状态转换与流程详解 (参考图片 2)

这张图展示了一个线程（比如 Thread B）尝试去获取锁的动态过程，特别是失败后的处理逻辑。

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