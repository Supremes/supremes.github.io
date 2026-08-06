---
updated: 2026-08-03 20:17
featured: "true"
---
# JVM

- 内存区域
- 类加载机制
- 垃圾回收
- 调优与排查

## 1. JVM 内存模型

通常指 JVM 运行时数据区，与 JMM（Java 内存模型）不同。

- JVM 内存模型（JVM 运行时数据区）：关注 JVM 运行时把内存划分成哪些区域。
- Java 内存模型（**Java Memory Model，JMM**）：描述多线程如何读写共享变量，以及可见性、有序性和原子性规则。

```
JVM 进程
├── 线程共享
│   ├── 堆（Heap）
│   ├── 方法区（Method Area）
│   │   └── HotSpot 中主要由 Metaspace 实现
│   └── 运行时常量池（Runtime Constant Pool）
│
└── 线程私有
    ├── 程序计数器（Program Counter Register）
    ├── Java 虚拟机栈（JVM Stack）
    │   └── 栈帧（Stack Frame）
    └── 本地方法栈（Native Method Stack）
```

![JVM 内存模型：运行时数据区](./jvm-memory-model.svg)


## 2. 垃圾回收

### 垃圾回收算法 

![](https://picx.zhimg.com/v2-6fcb5510cd270ae70f85513459e53dce_r.jpg?source=2c26e567)

| **维度**       | **Serial**              | **CMS**                 | **G1**                   | **ZGC**                 |
| ------------ | ----------------------- | ----------------------- | ------------------------ | ----------------------- |
| **内存结构**     | 连续分代（Eden/S0/S1/Old）    | 连续分代（Eden/S0/S1/Old）    | 逻辑分代，物理 Region 分块        | 逻辑分代/不分代，基于 Region 分页   |
| **核心算法**     | 复制算法（Young）/ 标记-整理（Old） | 复制算法（Young）/ 标记-清除（Old） | 标记-整理（Region 间移动复制）      | 标记-整理（基于染色指针与并发转移）      |
| **STW 停顿时间** | 几十毫秒至数秒（随内存变大而线性增长）     | 几十到几百毫秒                 | 可预测，通常在 100~200ms 内      | **< 1ms**（且不随堆大小线性增加）   |
| **推荐内存大小**   | < 100MB                 | 1GB ~ 6GB               | 4GB ~ 64GB               | 16GB ~ 16TB+            |
| **主要屏障**     | 无                       | 写屏障 (Write Barrier)     | 写屏障 (SATB Write Barrier) | **读屏障** (Read Barrier)  |
| **JDK 状态**   | 依然可用（适合客户端微型应用）         | JDK 9 废弃，JDK 14 正式移除    | JDK 9 起为**默认收集器**        | JDK 15 生产可用，JDK 21 支持分代 |
**Serial：**
- 优势：简单高效，开销低，内存占用小
- 劣势：回收时需要STW（暂停所有用户线程），堆内存增大后，遇到回收后，停顿时间无法承受
- 使用场景：单 CPU 环境、微服务客户端容器或内存 < 100MB 的边缘设备

**CMS：**
- 优势：垃圾收集线程与用户线程并行，大幅降低STW时间
- 劣势：使用标记-清除垃圾回收算法，会产生大量内存碎片，容易产生full gc
- 使用场景：JDK8及之前，对响应时间敏感、内存低的web应用

**G1：**
- 优势：将堆拆分为上千个等大的 Region，按回收价值优先（Garbage-First）回收。
- 劣势：memory footprint较高，占用堆内存10-20个点
- 使用场景：JDK9及之后的默认垃圾回收算法


**ZGC:**
- 优势：依靠染色指针和读屏障实现并发标记和转移，将STW时间控制在1ms以内，效率极高
- 局限：ZGC 依靠**读屏障**和**染色指针**实现超低延迟，但读屏障带来了 3%~5% 的 CPU 吞吐量开销，且需要更多的物理内存（通常建议堆大小 > 16GB）来缓解并发垃圾产生的分配速率压力。
- 使用场景：对延迟极度敏感（金融交易、实时推荐）、大内存服务服务

## 3. 类加载机制

Java17里有三层类加载器：
- 启动类加载器
- 平台类加载器
- 应用类加载器

![img](./JVM-双亲委派机制.png)

> [!important]
> **双亲委派**: 收到一个类加载请求，自己先不加载，先扔给父加载器。父加载器也一样，继续往上扔，直到最顶层的启动类加载器。如果父加载器加载不了（在自己负责的路径下找不到这个类），再一层层退回来，由子加载器尝试加载。

- 安全：你自己写一个 `java.lang.String` 类，因为双亲委派，最终会由启动类加载器去加载JDK自带的String，你的冒牌货永远不会被加载。这就保证了核心API不会被篡改。
- 避免重复加载： 父加载器已经加载过的类，子加载器不会再加载一次。

> 特例：优先加载子类
> - SPI机制
> - 热部署


## JVM调优

-  [为什么那么多带gc的语言,只有jvm需要调优?](https://www.zhihu.com/question/602234735/answer/2066500567258731942)

![[Pasted image 20260806220739.png]]

### 几种常用实战场景 

这三个场景是线上最高频的"急诊"，每个都有一套标准定位流程。把这三套流程刻进肌肉记忆，线上告警来了才不慌。
#### CPU 使用率飙升

> [!important]
> 监控告警某台机器 CPU 接近 100%，服务响应变慢。定位的核心思路是：**找到是哪个线程在狂占 CPU，再看它在执行什么代码。**

**方案1：**
1. 找出 cpu 占用最高的进程：top -> 比如 `9527`
2. 找出进程内 cpu 占用最高的线程: top -Hp `9527` -> 比如 `9550`
3. 线程 TID 转成16进制: printf "%x\n" `9550` -> 254e
4. 在线程栈中搜这个16进制线程 ID，定位到具体代码栈: jstack `9257` | grep `254e` -A 30 

**方案2：**
- 安装 Arthas，调用命令 `thread -n 3`, 列出 CPU 占用率最高的前三线程栈

> **特殊情况**：若发现占用 CPU 的是 GC 线程，则说明问题是 GC 太频繁，查询 GC 日志，八成是内存出了问题

#### 内存泄露 - OOM

> [!important]
> 服务运行一段时间后越来越慢，最终抛 `java.lang.OutOfMemoryError: Java heap space`；GC 日志里老年代**只涨不降**、Full GC 越来越频繁却压不下去。


1. 拿到堆快照:
	- 依靠预设值的 JVM 参数 `-XX:+HeapDumpOnOutOfMemoryError`，在 OOM 时自动生成 dump
	- 在内存高位手动 dump: `jmap - dump:format=b, file=heap.hprof 9527`
2. 使用MAT打开heap.hprof 分析：
	- 看Leak Suspects报告
	- 看Dominator Tree，找出内存占用最大的对象
	- 对可疑对象右键，path to GC Roots，看它被谁一直引用

常见OOM场景：
- 静态集合只加不删：static Map/List这种
- 缓存没有淘汰策略
- 资源未关闭：连接、流、监听器未及时关闭
#### 死锁

> [!important]
> 某个功能不工作了，但是CPU并不高。这属于死锁的典型特征

死锁定位很简单，`jstack` 命令会直接帮你揪出来这个问题线程
```
jstack 9527 # 输出的末尾会有类似这样一段（jstack 自动检测并报告）： 
# Found one Java-level deadlock: 
# ============================= 
# "Thread-A": # waiting to lock monitor ... (a com.example.OrderLock), 
# which is held by "Thread-B" 
# "Thread-B": # waiting to lock monitor ... (a com.example.StockLock), 
# which is held by "Thread-A"

```

`jstack` 会明确说明：哪几个线程死锁了、各自持有哪把锁，又在等待哪把锁

或者使用 `Arthas` 提供的 `thread -b` 命令，直接输出死锁信息

# 概念科普

- JIT：JIT（Just-In-Time）就是 JVM 在运行时把**热点代码**编译成对应平台的**本地机器码**，之后直接执行机器码，从而显著提高执行速度和效率。
- 主流 JVM 实现 - HotSpot，其他还包括 OpenJ9、GraalVM 等


# 常用 Java 命令行工具

以下工具通常位于 `$JAVA_HOME/bin`，命令中的 `<pid>` 表示 Java 进程 ID。

## jps：查看 Java 进程

列出当前用户可访问的 JVM 进程及其启动信息。

```bash
jps -l       # 显示主类全限定名或 JAR 路径
jps -lv      # 同时显示 JVM 启动参数
```
## jstat：采样 JVM 统计数据

持续观察 GC、堆容量、类加载和 JIT 编译等指标，适合快速判断 GC 是否频繁。

```bash
jstat -gcutil <pid> 1000 10  # 每秒采样一次，共 10 次
jstat -gccapacity <pid>      # 查看各代容量
```


## jcmd：综合诊断

向运行中的 JVM 发送诊断命令。功能覆盖线程、堆、GC 和 JFR，现代 JDK 中应优先使用。

```bash
jcmd <pid> help                    # 查看支持的命令
jcmd <pid> VM.flags                # 查看 JVM 参数
jcmd <pid> GC.heap_info            # 查看堆信息
```

## jinfo：查看 JVM 配置

查看系统属性和 JVM 参数，也可调整部分支持动态修改的参数。

```bash
jinfo -flags <pid>                 # 查看 JVM 参数
jinfo -sysprops <pid>              # 查看系统属性
jinfo -flag <参数名> <pid>         # 查看指定参数
```


## jstack：生成线程快照

输出线程栈、锁和死锁信息。排查死锁或 CPU 飙高时，应间隔数秒连续采集多份快照进行对比。

```bash
jstack -l <pid> > /tmp/threads.txt
```

## jmap：生成堆快照

查看对象统计或导出 Heap Dump，用于分析内存泄漏和大对象。`live` 选项可能触发 Full GC。

```bash
jmap -histo:live <pid>                         # 统计存活对象
jmap -dump:live,format=b,file=/tmp/heap.hprof <pid>
```

## jhat：分析 Heap Dump

启动本地 Web 服务分析 `.hprof` 文件。仅适用于 JDK 8，JDK 9 起已移除，实际排障通常使用 Eclipse MAT。

```bash
jhat -J-Xmx2g /tmp/heap.hprof  # 默认访问 http://localhost:7000
```

 
## JFR / jfr：持续采样与故障记录

JFR 记录 CPU、GC、锁、线程和 I/O 等事件；`jfr` 命令用于读取记录文件，适合生产环境持续诊断（JDK 11+）。

```bash
jcmd <pid> JFR.start settings=profile duration=60s filename=/tmp/app.jfr
jfr summary /tmp/app.jfr
jfr print --events jdk.CPULoad,jdk.GarbageCollection /tmp/app.jfr
```



# JMM

> [!important]
> 描述多线程如何读写共享变量，以及可见性、有序性和原子性规则。

## JMM 的核心抽象结构

> [!note]
> JMM 规定所有变量必须存储在主内存中，每个线程都有自己的工作内存

- 线程不能直接读取主内存的变量
- 线程必须将主内存中的变量，复制一份副本，到自己的工作内存
- 线程在工作内存中对变量进行修改后，必须在合适的时机回写到主内存
## JMM 解决了三大并发问题

- 可见性: 线程修改了共享值，其他线程是否能立即看到。使用 `volatile` 关键字
- 有序性：编译器和 CPU 为了性能优化，对指令进行了重排。为了避免多线程下出现不可预料的问题，使用 `volatile` 关键字，禁止指令重排
- 原子性：一个或多个操作，在 CPU 执行中，要么全部完成或全部不完成。使用 `synchronized` `ReetrantLock` `Atomic` 等来解决
