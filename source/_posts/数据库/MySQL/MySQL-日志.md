---
title: MySQL 日志系统
tags: []
categories:
  - 数据库
  - MySQL
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/MySQL_Log.webp
hidden: false
abbrlink: 356a30bc
date: 2025-12-02 17:26:11
sticky:
---
# Redo Log
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/MySQL_RedoLog.webp)

这张图被一条中间的虚线分为左右两部分，代表了计算机系统中两种截然不同的存储介质属性。

## 1. 左侧区域：IN-MEMORY (内存区域) - Volatile (易失性)

- **特点：**
    - **速度极快：** CPU 对内存的读写速度远远高于磁盘。为了高性能，数据库必须尽可能在内存中处理数据。
    - **易失性 (Volatile)：** 这是最大的弱点。一旦断电、系统崩溃或进程被强制终止，内存中的所有数据瞬间消失。图中的气泡对话框形象地说明了这一点：“Fast access, but data lost on power failure.”（访问快，但断电丢数据）。
        
- **关键组件：**
    - **BUFFER POOL (缓冲池)：**
        - 这是 InnoDB 在内存中最大的保留区域。它缓存了从磁盘读取的数据页 (Data Pages)。
        - 当我们要修改数据时，不是直接去改磁盘文件，而是先在 Buffer Pool 中找到对应的数据页进行修改。
        - **Dirty Page (脏页)：** 图中高亮的橙色方块。当一个数据页在内存中被修改了，但还没有写回到磁盘的数据文件中时，它就和磁盘上的版本不一致了，我们称之为“脏页”。
    - **LOG BUFFER (日志缓冲)：**
        - 这是一个相对较小的内存区域，专门用来暂存即将写入磁盘的 Redo Log 记录。
        - 每当 Buffer Pool 中的数据发生修改，InnoDB 就会生成一条对应的、非常紧凑的日志记录（比如：“第10号数据页偏移量500的位置，值从A改成了B”），先暂存在这里。
            
## 2. 右侧区域：ON-DISK (磁盘区域) - Persistent (持久性)

- **特点：**
    
    - **速度慢：** 相比内存，磁盘 I/O 是非常昂贵的操作，速度很慢。
        
    - **持久性 (Persistent)：** 优点是数据安全。写入磁盘后，即使断电，数据也不会丢失。
        
- **关键组件：**
    
    - **REDO LOG FILES (重做日志文件)：**
        
        - 这是保证数据安全的核心。它们是物理磁盘上的文件（通常命名为 `ib_logfile0`, `ib_logfile1` 等）。
            
        - 特点是**顺序写入 (Sequential Write)**。就像写日记一样，一直往文件末尾追加内容。对于机械硬盘来说，顺序写的速度远快于随机写。
            
    - **DATA FILES (数据文件)：**
        
        - 这是表数据最终的归宿（通常是 `.ibd` 文件）。
            
        - 写入这些文件通常是**随机写入 (Random Write)**，因为不同的数据页分布在文件的不同位置。
            

---

## 流程详解：正常事务操作 (Normal Operation)

这个流程的目标是：**既要利用内存的高速，又要保证数据的安全。**

**步骤 1. UPDATE/INSERT Data (事务开始)**

- 客户端发起一个更新请求。
    
- InnoDB 首先在 **Buffer Pool** 中查找需要修改的数据页。如果不在，就先从磁盘读入。
    
- 在内存中直接修改该数据页。此时，该页变成了 **Dirty Page (脏页)**。
    

**步骤 2. COMMIT Transaction (提交事务)**

- 客户端修改完数据后，发起 `COMMIT` 命令，告诉数据库：“我完成了，请把这些修改永久保存。”
    
- 此时，关于这次修改的日志记录已经被放入了 **Log Buffer** 中等待。
    

**步骤 3. WAL: WRITE-AHEAD LOGGING (预写式日志) —— 最关键的一步！**

- **这是跨越“易失”和“持久”边界的关键动作。**
    
- 在事务被认为是“提交成功”之前，InnoDB 必须遵循 WAL 原则：**日志先行**。
    
- 系统会将 Log Buffer 中的日志记录，强制写入到磁盘上的 **Redo Log Files** 中，并执行 `fsync()` 操作（确保数据真的落到物理磁盘介质上，而不是停留在操作系统的文件缓存里）。
    
- **图中文字强调：** “Must reach disk BEFORE transaction is confirmed.”（在确认事务之前，日志必须到达磁盘）。
    
- _注：一旦这一步完成，哪怕数据文件还没更新，事务也被认为是安全的了。图里虽然没画步骤4，但此时数据库会向客户端返回“Commit OK”。_
    

**步骤 5. ASYNC CHECKPOINT (异步检查点/刷脏页)**

- 这是一个后台的、异步的过程，**不影响客户端的响应速度**。
    
- Buffer Pool 中的“脏页”不能永远待在内存里，内存有限，且不安全。
    
- InnoDB 的后台线程会选择合适的时机（比如系统空闲时，或 Redo Log 快写满时），慢慢地将这些脏页刷新到磁盘上的 **Data Files** 中。我们将这个过程称为“刷脏”或 Checkpoint。
    
- 图中虚线箭头和文字 "Lazy write of data pages"（数据的延迟写入）准确地描述了这个过程。
    

---

## 流程详解：崩溃恢复 (Crash Recovery Process)

这个流程的目标是：**当发生意外时，把还没来得及写入数据文件的修改找回来。**

**场景假设：** 假设在上面的流程中，**步骤 3 刚刚完成**（Redo Log 已经落盘），但是**步骤 5 还没有发生**（脏页还在内存里，没写到数据文件），突然机房断电了。

**后果：** 内存中的 Dirty Page 瞬间消失。磁盘上的 Data Files 里存的还是旧数据。

**恢复过程 (图的底部区域)：**

1. **SYSTEM CRASH / POWER OUTAGE (系统崩溃/断电)**。
    
2. **RESTART (重启)**：MySQL 服务器重新启动。
    
3. **Read from Last Checkpoint (从上次检查点读取)**：
    
    - InnoDB 启动时会检查状态，发现上次是非正常关闭。
        
    - 它会去读取磁盘上的 **REDO LOG FILES**。它需要找到一个“检查点 (Checkpoint)”，这个点之前的数据保证都已经写入数据文件了。
        
4. **REPLAY LOGS (重放日志)**：
    
    - InnoDB 从检查点开始，往后读取所有的 Redo Log 记录。
        
    - 它按照日志记录的内容，在内存的 **Buffer Pool** 中重新执行一遍修改操作。
        
5. **Restore Dirty Pages to Memory (恢复脏页到内存)**：
    
    - 通过重放日志，崩溃前那一刻内存中的 **Dirty Page** 就被完美还原了。
        
    - 此时，数据库恢复到了崩溃前的一致状态，可以对外提供服务了。随后，后台线程会再次尝试执行步骤 5，把这些恢复出来的脏页写入数据文件。
        

## 总结

这张图完美地展示了 MySQL InnoDB 的设计哲学：

- 利用 **内存 (Buffer Pool)** 来保证**高性能**（读写都在内存）。
    
- 利用 **Redo Log (WAL机制)** 来保证**持久性**（关键时刻利用顺序写快速落盘日志）。
    
- 利用 **异步刷脏 (Checkpoint)** 来平衡性能和数据最终的一致性。

# Bin Log
- Server 层也有自己的日志，称为 binlog（归档日志）。
- binlog 是可以追加写入的。“追加写”是指 binlog 文件写到一定大小后会切换到下一个，并不会覆盖以前的日志。
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/MySQL_BinLog.webp)
## 工作流程图详解

这张图片直观地展示了 **MySQL Binlog (Binary Log，二进制日志)** 的工作原理，以及它是如何支撑 **主从复制 (Replication)** 的。

我们可以把这张图的流程拆解为三个主要部分：**主库（Master）的记录**、**数据的传输**、**从库（Slave/Replica）的重放**。

以下是详细的步骤解释：

### 1. 主库端 (Master Server)：记录变更

这是流程的起点，对应图中左侧或上方的部分。

- 写入操作 (Write Operations):
    
    当客户端应用（Client Application）向数据库发送 修改数据 的请求（如 INSERT, UPDATE, DELETE）时，这些操作首先在主库的存储引擎中执行。
    
    - _注意：`SELECT` 等读取操作不会被记录，因为它们不改变数据。_
        
- 写入 Binlog 文件 (Binary Log File):
    
    在数据被提交（Commit）到底层存储之前（或同时），MySQL 会将这次数据变更的详细信息顺序写入到磁盘上的 Binlog 文件 中。
    
    - **Binlog 的内容：** 它可以记录具体的 SQL 语句（Statement 格式），也可以记录行数据的变化（Row 格式），或者两者的混合（Mixed 格式）。
        

### 2. 复制与传输过程：三个关键线程

这是连接主库和从库的核心机制，也是图中的核心逻辑。为了把数据同步过去，MySQL 使用了三个专门的线程：

#### A. Binlog Dump Thread (主库端)

- 当从库连接到主库并请求同步时，主库会创建一个 **Binlog Dump 线程**。
    
- 它的任务是读取主库的 Binlog 文件，并将内容通过网络发送给从库。
    

#### B. I/O Thread (从库端)

- 从库启动后，会创建一个 **I/O 线程**。
    
- 它的任务是“搬运工”：它连接到主库，接收 Dump 线程发来的 Binlog 数据块。
    
- **关键点：** I/O 线程收到数据后，**不会直接写入从库的数据库**，而是将其写入到从库磁盘上的一个临时中转文件，叫做 **Relay Log (中继日志)**。
    

#### C. SQL Thread (从库端)

- 这是从库的第二个关键线程。
    
- 它的任务是“执行者”：它实时检测 Relay Log 中有没有新内容。
    
- 一旦发现新内容，它就读取这些日志，并将其解析为具体的数据库操作，然后在从库的数据库中**重新执行 (Replay)** 一遍。
    

### 3. 从库端 (Replica Server)：最终一致性

对应图中右侧或下方的部分。

- Relay Log (中继日志):
    
    这是一个缓冲地带。它的存在使得“获取日志”和“执行日志”解耦了。即使从库执行 SQL 比较慢（SQL Thread 阻塞），I/O 线程依然可以快速地把主库的日志拉取回来存在本地，保证数据不丢失。
    
- 数据同步完成:
    
    当 SQL 线程执行完 Relay Log 中的操作后，从库的数据状态就和主库保持了一致。
    

---

### 总结：这张图告诉了我们什么？

1. **异步复制 (Asynchronous):** 主库写完 Binlog 就可以告诉客户端“成功了”，它不需要等从库确认。从库是后来慢慢追上来的。
    
2. **解耦:** 通过 Binlog 和 Relay Log，主库和从库的压力被隔离开了。
    
3. **核心用途:**
    
    - **主从复制:** 实现读写分离（主库写，从库读）或高可用热备。
        
    - **数据恢复:** 如果数据库误删了，可以通过重放 Binlog 把数据恢复到误删前的任意时刻（Point-in-Time Recovery）。
        

你可以把这个过程想象成：

主库是演讲者（执行写操作），它把演讲内容录在磁带（Binlog）里。从库派了一个快递员（I/O 线程）把磁带复刻一份拿回家（Relay Log），然后从库自己在家里放磁带（SQL 线程），跟着录音再做一遍动作。

**需要我为您解释 Binlog 的三种格式（Statement, Row, Mixed）的区别吗？这对性能和数据一致性有很大影响。**

# Undo Log
如果说 **Redo Log** 是“发生意外时的救命稻草”，**Bin Log** 是“传给别人的操作手册”，那么 **Undo Log** 就是**“后悔药”**（或者说是电脑上的 `Ctrl+Z`）。

它是 MySQL 保证事务 **原子性 (Atomicity)** 和实现 **MVCC (多版本并发控制)** 的核心组件。

以下是 Undo Log 的详细解析及其与另外两个日志的区别。

---

## 1. 什么是 Undo Log？

Undo Log（回滚日志）记录的是数据的**逻辑变化**，但它的记录方式是**“反着来的”**。

- **记录原理：** 只要你修改数据，MySQL 就会在 Undo Log 里记录一条**相反**的操作，以便随时回滚。
    
    - 你执行 `INSERT`，它记录 `DELETE`。
        
    - 你执行 `DELETE`，它记录 `INSERT`。
        
    - 你执行 `UPDATE` 把 `age` 从 10 改为 20，它记录 `UPDATE age = 10`。
        

#### **它的两大核心作用：**

1. **事务回滚 (Rollback)：**
    
    - 当事务执行到一半，用户手动输入 `ROLLBACK`，或者程序发生错误（如唯一索引冲突），MySQL 就利用 Undo Log 将数据恢复到事务开始前的样子。
        
2. **MVCC (多版本并发控制)：**
    
    - 当一个事务正在修改某行数据（还没提交），另一个事务来读取这行数据时，为了不加锁且不读到脏数据，MySQL 会利用 Undo Log 构建一个**“历史版本快照”**，让读取者看到修改之前的数据。
        

---

## 2. Undo Log 的工作流程图解

假设我们执行一个事务：`UPDATE user SET age = 20 WHERE id = 1;` (原 age = 10)

#### **Step 1: 准备回滚数据**

在真正修改内存中的数据之前，InnoDB 会先生成一条 Undo Log：

> “如果要把 id=1 的数据回滚，请执行 `UPDATE user SET age = 10 WHERE id = 1;`”

#### **Step 2: 修改内存 & 写 Redo Log**

执行修改，内存中的 age 变为 20。同时写入 Redo Log（记录物理修改）。

#### **Step 3: 此时如果有别的事务来查 (MVCC)**

事务还没提交。此时事务 B 来查 id=1。

InnoDB 发现这行数据被锁定了（或处于活跃事务中），它不会阻塞，而是顺着回滚指针 (Rollback Pointer) 找到 Undo Log 里的记录。

- **结果：** 事务 B 读到了 `age = 10`。
    
- **意义：** 读写互不阻塞，高并发性能的关键。
    

#### **Step 4: 事务提交 (Commit) 或 回滚 (Rollback)**

- **如果提交：** Undo Log 不会立即删除（因为可能还有长事务需要看旧版本），而是放入“待清理列表 (History List)”，由 Purge 线程后续清理。
    
- **如果回滚：** 立即执行 Undo Log 里的反向操作，将 age 变回 10。
    

---

## 3. 一个刁钻的问题：Undo Log 本身需要持久化吗？

**需要。**

这听起来有点绕：Undo Log 是用来修数据的，那谁来修 Undo Log 呢？

答案是 Redo Log。

- Undo Log 在 MySQL 中也被视为“数据”的一种（存在于系统表空间或 undo 表空间中）。
    
- 当你写 Undo Log 时，这个写入操作本身也会产生对应的 Redo Log。
    
- **场景：** 假设事务执行了一半，MySQL 崩溃了。
    
    1. 重启后，Redo Log 会先恢复数据，**同时也恢复了 Undo Log**。
        
    2. 数据库发现有一个事务处于“未提交”状态。
        
    3. 利用刚刚恢复出来的 Undo Log，对该事务进行回滚 (Rollback)。
        
    4. 数据库恢复一致性。
        

---

## 总结

- **Redo Log** 让你**向前走**（掉电了也能继续往前走完）。
    
- **Undo Log** 让你**向后退**（做错了可以退回到原点）。
    
- **Bin Log** 让你**克隆**（把你的经历完整复制给另一个库）。
    

三者配合：

1. 事务开启。
    
2. 写 **Undo Log** (为了能退回来)。
    
3. 执行内存修改。
    
4. 写 **Redo Log** (为了防断电)。
    
5. 提交时写 **Bin Log** (为了给从库)。
    
6. 事务结束。
    
# 区别
| **特性**    | **Redo Log (重做日志)**                               | **Bin Log (归档日志)**                 | **Undo Log (回滚日志)**                                     |
| --------- | ------------------------------------------------- | ---------------------------------- | ------------------------------------------------------- |
| **核心关键词** | **“恢复”**                                          | **“复制”**                           | **“撤销”**                                                |
| **比喻**    | 记账本的草稿 (防止断电忘事)                                   | 完整的账单明细 (给别人看)                     | **橡皮擦 / Ctrl+Z**                                        |
| **侧重点**   | 物理偏向 (页修改)                                        | 逻辑偏向 (SQL语义)                       | **逻辑反向** (逆操作)                                          |
| **主要作用**  | 崩溃恢复 (Crash Safe)<br><br>  <br><br>保证 **D** (持久性) | 主从复制、数据恢复<br><br>  <br><br>保证数据一致性 | 事务回滚、MVCC<br><br>  <br><br>保证 **A** (原子性) 和 **I** (隔离性) |
| **写入时机**  | 事务进行中不断写                                          | 事务提交时一次性写                          | 事务开始前/修改前写                                              |
| **释放时机**  | 落盘后覆盖 (循环写)                                       | 不删除 (追加写)                          | 事务提交后，若无 MVCC 需求则标记删除 (Purge)                           |

# 问题
## 为什么需要“两阶段提交” (2 PC)?
![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/MySQL_2PC.webp)

### 背景问题：数据一致性
如果 MySQL 没有两阶段提交，Redo Log 和 Bin Log 的写入顺序是独立的。假设我们执行一条 `UPDATE` 语句：

1. **先写 Redo Log，再写 Bin Log：**
    - 如果 Redo Log 写完，Bin Log 还没写完时系统宕机。
    - _恢复后：_ 主库通过 Redo Log 恢复了数据（A=1）；但 Bin Log 没记录，从库同步时数据仍是旧的（A=0）。**主从不一致。**
        
2. **先写 Bin Log，再写 Redo Log：**
    - 如果 Bin Log 写完，Redo Log 没写完时系统宕机。
    - _恢复后：_ 主库因 Redo Log 缺失，事务回滚（A=0）；但 Bin Log 已经有了记录，从库会同步这条更新（A=1）。**主从不一致。**
        

### 目的
**两阶段提交是为了让 Redo Log 和 Bin Log 在逻辑上保持一致**。要么同时成功，要么同时失败。

---

### 两阶段提交流程详解

假设执行语句：`UPDATE user SET age = age + 1 WHERE id = 1;`

#### **流程图解**
代码段

{%mermaid%}
sequenceDiagram
    participant Client as 客户端
    participant Executor as 执行器 (Server层)
    participant InnoDB as InnoDB 引擎
    participant DiskRedo as Redo Log (磁盘)
    participant DiskBin as Bin Log (磁盘)

    Client->>Executor: 发起 Update 语句
    Executor->>InnoDB: 查找 ID=1 的行
    InnoDB-->>Executor: 返回行数据 (若不在内存则从磁盘读)
    
    Note over Executor: 1. 执行更新操作
    Executor->>InnoDB: 写入新行数据 (内存更新)

    Note over InnoDB, DiskRedo: 2. Prepare 阶段 (准备)
    InnoDB->>DiskRedo: 写入 Redo Log (状态: PREPARE)
    
    Note over Executor, DiskBin: 3. 写 Binlog 阶段
    Executor->>DiskBin: 写入 Bin Log
    
    Note over InnoDB, DiskRedo: 4. Commit 阶段 (提交)
    Executor->>InnoDB: 提交事务 (调用引擎接口)
    InnoDB->>DiskRedo: Redo Log 标记为 (状态: COMMIT)
    
    Executor-->>Client: 返回成功
{%endmermaid%}

#### **详细步骤解析**

1. **执行阶段：**
    
    - InnoDB 将内存中的数据更新（此时数据在内存中是脏页）。
        
2. **Prepare 阶段 (第一阶段)：**
    
    - InnoDB 将本次事务的变更写入 Redo Log，并将 Redo Log 的记录状态标记为 `PREPARE`。
        
    - 此时，事务并未真正完成，但数据变更已经持久化到了 Redo Log 中。
        
3. **写 Bin Log 阶段：**
    
    - MySQL Server 层将事务的逻辑操作写入 Bin Log 文件，并确保写入磁盘（依赖 `sync_binlog` 参数）。
        
4. **Commit 阶段 (第二阶段)：**
    
    - Server 层调用引擎的提交接口。
        
    - InnoDB 收到通知后，将 Redo Log 中刚才那条记录的状态由 `PREPARE` 修改为 `COMMIT`。
        
    - 至此，事务彻底完成。
        

---

### 崩溃恢复逻辑：它是如何保证一致性的？

如果在上述流程的任意时刻发生宕机（Crash），MySQL 重启后会检查 Redo Log 中的状态：

- **情况 A：Redo Log 是完整的 `COMMIT` 状态**
    
    - **处理：** 直接根据 Redo Log 提交事务，恢复数据。
        
    - **结果：** 事务成功。
        
- **情况 B：Redo Log 是 `PREPARE` 状态，且 Bin Log 完整**
    
    - _场景：_ 步骤 3 完成了（Bin Log 写了），但步骤 4 还没来得及改状态。
        
    - **处理：** MySQL 扫描 Bin Log，发现该事务的 XID（事务 ID）在 Bin Log 中存在且完整。引擎将 Redo Log 状态补齐为 Commit，提交事务。
        
    - **结果：** 事务成功（因为 Bin Log 已经有了，为了主从一致，主库必须提交）。
        
- **情况 C：Redo Log 是 `PREPARE` 状态，但 Bin Log 不完整/缺失**
    
    - _场景：_ 步骤 2 完成了，但在写 Bin Log 时宕机。
        
    - **处理：** 扫描 Bin Log 发现没有对应的 XID。引擎回滚（Rollback）该事务。
        
    - **结果：** 事务失败（主库回滚，从库也没收到 Bin Log，达成一致）。
        

---

### 总结
- **Redo Log** 救主库（物理恢复），**Bin Log** 救从库（逻辑同步）。
- **两阶段提交** 就像是一个“握手协议”：
    - 先让 Redo Log 做好准备（Prepare）。
    - 再写 Bin Log（关键点）。
    - 最后确认 Redo Log（Commit）。
        
- **判决标准：** 只要 **Bin Log 写成功了**，这个事务就算成功，Redo Log 即使是 Prepare 状态也会被强制提交；否则就回滚。
