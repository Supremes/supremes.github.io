---
title: Golang
tags:
  - golang
categories:
  - 后端开发
abbrlink: 31482
date: 2025-11-29 08:59:30
cover: /imgs/cover/golang.png
---
# map

[map 的底层实现原理是什么 - 码农桃花源 (gitbook.io)](https://qcrao91.gitbook.io/go/map/map-de-di-ceng-shi-xian-yuan-li-shi-shi-mo)

## 底层数据结构

```
// A header for a Go map.
type hmap struct {
    // 元素个数，调用 len(map) 时，直接返回此值
    count     int
    flags     uint8
    // buckets 的对数 log_2
    B         uint8
    // overflow 的 bucket 近似数
    noverflow uint16
    // 计算 key 的哈希的时候会传入哈希函数
    hash0     uint32
    // 指向 buckets 数组，大小为 2^B
    // 如果元素个数为0，就为 nil
    buckets    unsafe.Pointer
    // 扩容的时候，buckets 长度会是 oldbuckets 的两倍
    oldbuckets unsafe.Pointer
    // 指示扩容进度，小于此地址的 buckets 迁移完成
    nevacuate  uintptr
    extra *mapextra // optional fields
}
```

- B：buckets数组的长度的对数，也就是说 buckets 数组的长度就是 2^B。bucket 里面存储了 key 和 value
- buckets是一个指针，最终指向bmap这个数据结构

```
type bmap struct {
    tophash [bucketCnt]uint8
}

// 但上述只是表面(src/runtime/hashmap.go)的结构，编译期间会给它加料，动态地创建一个新的结构：
type bmap struct {
    topbits  [8]uint8
    keys     [8]keytype
    values   [8]valuetype
    pad      uintptr
    overflow uintptr
}
```

- bmap：即常说的桶。

1. 桶里面最多**装8个key**，会根据 key 计算出来的 hash 值的高 8 位来决定 key 到底落入桶内的哪个位置
2. 如若有第九个key进来，会再创建一个bucket，通过overflow指针连接
3. bmap的内存模型，是key/key/.../value/value/...，这样可以减少额外的内存对齐所需要的空间

- map的创建：

1. map创建出来是一个指针，因此在作为函数参数传入时，内部的改动也会影响到map自身
2. slice是一个结构体，因此作为函数参数传入时，不会影响到数据自身，但是由于数据是指针，因此可以改变指向的数据

- map的遍历：是随机的  
    go中range遍历map，不是固定的从bucket0开始遍历，每次会随机一个bucket开始遍历，并且bucket内也是会随机一个cell遍历

## map扩容

为避免大量key落在一个桶中，退化成链表，导致查询效率变为O(n)，装载因子被提出，用来衡量该情况。

loadFactor := count / (2^B)

count : map中元素个数

B：2^B表示buckets数目

- 触发扩容的时机：在向map中插入元素时，符合下面两个条件，会触发扩容

1. 装载因子超出阈值6.5（元素塞满了bucket）
2. overflow的bucket过多：（元素没有塞满bucket了，bucket冗余空间过多）

当 B 小于 15，也就是 bucket 总数 2^B 小于 2^15 时，如果 overflow 的 bucket 数量超过 2^B；当 B >= 15，也就是 bucket 总数 2^B 大于等于 2^15，如果 overflow 的 bucket 数量超过 2^15

- 扩容的逻辑：“渐进式”扩容，原有的 key 并不会一次性搬迁完毕，每次最多只会搬迁 2 个 bucket。

1. 分配新的buckets
2. 搬迁到新的buckets，发生在插入、修改和删除时，会先检查oldbuckets是否为nil（nil则搬迁完成，不需要再搬迁了）

- 扩容后的容量：针对扩容触发的条件1和2，有两种策略

1. buckets数目翻倍：

要重新计算 key 的哈希，才能决定它到底落在哪个 bucket。

2. buckets数目相等：

从老的 buckets 搬迁到新的 buckets，由于 bucktes 数量不变，因此可以按序号来搬，比如原来在 0 号 bucktes，到新的地方后，仍然放在 0 号 buckets。

# context

## context作用

1. 在 一组 goroutine 之间传递共享的值
2. 取消goroutine
3. 防止goroutine泄露

4. 不要将 Context 塞到结构体里。直接将 Context 类型作为函数的第一参数，而且一般都命名为 ctx。
5. 不要向函数传入一个 nil 的 context，如果你实在不知道传什么，标准库给你准备好了一个 context：todo。
6. 不要把本应该作为函数参数的类型塞到 context 中，context 存储的应该是一些共同的数据。例如：登陆的 session、cookie 等。
7. 同一个 context 可能会被传递到多个 goroutine，别担心，context 是并发安全的。

- context 主要用来在 goroutine 之间传递上下文信息，包括：取消信号、超时时间、截止时间、k-v 等。
- 随着 context 包的引入，context 几乎成为了并发控制和超时控制的标准做法。

## context.Value

```
type valueCtx struct {
    Context
    key, val interface{}
}
```

1. key要求是可比较的
2. 属于一个树结构
3. 取值过程，是会向上查找的
4. 允许存在相同的key，向上查找会找到最后一个key相等的节点，即层数高的节点

# Goroutine

1. M必须拥有P才可执行G中的代码，P含有一个包含多个G的队列，P可以调度G交由M执行
2. 所有可执行go routine都放在队列中：

- 全局队列（GRQ）：存储全局可运行的goroutine（从系统调用中恢复的G）；
- 本地可运行队列（LRQ）：存储本地（分配到P的）可运行的goroutine

3. workingschedule：各个P中维护的G队列很可能是不均衡的；空闲的P会查询全局队列，若全局队列也空，则会从其他P中窃取G（一般每次取一半）。

## goroutine和线程的区别

1. 内存占用：goroutine默认栈为2KB，线程至少需要1MB
2. 创建和销毁：goroutine由go runtime管理，属于用户级别的，消耗小；线程是操作系统创建的，是内核级别的，消耗巨大
3. 切换：goroutine切换只需要保存三个寄存器，线程切换需要寄存器

## M:N模型（M个线程，N个goroutine）

1. go runtime负责管理goroutine，Runtime会在程序启动的时候，创建M个线程（CPU执行调度的单位），之后创建的N个goroutine都会依附在这M个线程上执行。
2. 同一时刻，一个线程只能跑一个goroutine，当goroutine发生阻塞时，runtime会把它调度走，让其他goroutine来执行，不让线程闲着

## 系统调用

### 同步调用

G1即将进入系统调用时，M1将释放P，让某个空闲的M2获取P并继续执行P队列中剩余的G（即M2接替M1的工作）；M2可能来源于M的缓存池，也可能是新建的。当G1系统调用完成后，根据M1能否获取到P，将对G1做不同的处理：

- 有空闲的P，则获取一个以继续执行G1；
- 无空闲P，将G1放入全局队列，等待被其他P调度；M1进入缓冲池睡眠

### 异步调用

1. M 不会被阻塞，G 的异步请求会被“代理人” network poller 接手，G 也会被绑定到 network poller
2. 等到系统调用结束，G 才会重新回到 P 上。
3. M 由于没被阻塞，它因此可以继续执行 LRQ 里的其他 G。

# GC

垃圾回收器主要分为两个半独立的组件：

- 赋值器(Mutator)：指代用户态的代码，修改对象之间的引用关系，也就是在对象图（对象之间引用关系的一个有向图）上进行操作。
- 回收期（Collector）：负责执行垃圾回收的代码

## 根对象

垃圾回收过程中最先检查的对象

1. 全局变量
2. 执行栈
3. 寄存器

## 常见GC算法

1. 追踪式

从根对象出发，根据对象之间的引用信息，一步步推进直到扫描完毕整个堆并确定需要保留的对象，从而回收所有可回收的对象。

2. 引用计数

每个对象自身包含一个被引用的计数器，当计数器归零时自动得到回收

## Go的GC算法

Go 的 GC 目前使用的是无分代（对象没有代际之分）、不整理（回收过程中不对对象进行移动与整理）、并发（与用户代码并发执行）的三色标记清扫算法。

三色标记法通常指标记清扫的垃圾回收，三色规定了三种不同的对象：

- **白色对象**（可能死亡）：未被回收器访问到的对象。在回收开始阶段，所有对象均为白色，当回收结束后，白色对象均不可达。
- **灰色对象**（波面）：已被回收器访问到的对象，但回收器需要对其中的一个或多个指针进行扫描，因为他们可能还指向白色对象。
- **黑色对象**（确定存活）：已被回收器访问到的对象，其中所有字段都已被扫描，黑色对象中任何一个指针都不可能直接指向白色对象。

### 回收过程：

1. 起初所有的对象都是白色的；
2. 从根对象出发扫描所有可达对象，标记为灰色，放入待处理队列；
3. 从待处理队列中取出灰色对象，将其引用的对象标记为灰色并放入待处理队列中，自身标记为黑色；
4. 重复步骤3，直到待处理队列为空，此时白色对象即为不可达的“垃圾”，回收白色对象；

### Go GC 需要 STW 的原因：

为了保证准确性、防止无止境的内存增长等问题而不可避免的需要停止赋值器进一步操作对象图以完成垃圾回收。

## GC监控

方式1：GODEBUG=gctrace=1

方式2：go tool trace 将统计来的信息以可视化的信息展现给用户  
方式3：debug.ReadGCStats 查看gc状态

方式4：runtime.ReadMemStats 对内存进行监控

## GC触发时机

1. **调用runtime.GC主动触发**，此调用阻塞式地等待当前 GC 运行完毕。
2. 被动触发：

- 使用系统监控，当超过两分钟没有产生任何 GC 时，强制触发 GC。
- 使用步调（Pacing）算法，其核心思想是控制内存增长的比例。

## GC内存分配速度超出标记清除的速度怎么办

当 GC 触发后，会首先进入并发标记的阶段。并发标记会设置一个标志，并在 mallocgc 调用时进行检查。当存在新的内存分配时，会暂停分配内存过快的那些 goroutine，并将其转去执行一些辅助标记（Mark Assist）的工作，从而达到放缓继续分配、辅助 GC 的标记工作的目的。

## GC调优

一般需要处理的两种情况：

1. 对停顿敏感：GC过程中造成的长时间停顿，即STW
2. 对资源消耗敏感：对于频繁分配内存的应用而言，频繁分配内存增加 GC 的工作量，原本可以充分利用 CPU 的应用不得不频繁地执行垃圾回收，影响用户代码对 CPU 的利用率，进而影响用户代码的执行效率。

- 减少并复用内存

例如使用 sync.Pool 来复用需要频繁创建临时对象，例如提前分配足够的内存来降低多余的拷贝。

- 调整 GOGC

GC 的触发原则是**由步调算法来**控制的，其关键在于估计下一次需要触发 GC 时，堆的大小。可想而知，如果我们在遇到海量请求的时，**为了避免 GC 频繁触发，是否可以通过将 GOGC 的值设置得更大**，让 GC 触发的时间变得更晚，从而减少其触发频率，进而增加用户代码对机器的使用率呢