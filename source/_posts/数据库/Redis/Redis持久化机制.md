---
title: Redis 持久化机制
tags:
  - Redis
  - 持久化
categories:
  - 数据库
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
hidden: true
updated: 2026-01-03 15:00
abbrlink: 79b4769c
date: 2026-01-03 15:00:00
---

Redis 作为内存数据库，持久化机制是保障数据安全的关键。本文深入解析 RDB、AOF 和混合持久化的原理与最佳实践。

---

# 一、为什么需要持久化？

Redis 数据存储在内存中，如果服务器宕机或重启，数据会全部丢失。持久化机制将内存数据保存到磁盘，实现数据恢复。

**持久化的核心权衡：**
- **数据安全性 vs 性能**：持久化频率越高，数据越安全，但性能开销越大。
- **恢复速度 vs 文件大小**：压缩格式恢复快但可读性差，文本格式便于调试但体积大。

---

# 二、RDB (Redis Database Backup) - 快照持久化

## 2.1 核心原理

**RDB 是全量快照**：在某个时间点，将内存中的所有数据生成一个二进制文件（`dump.rdb`）。

### 触发方式

#### 1. 手动触发

| **命令**     | **阻塞行为**          | **应用场景**          |
| ---------- | ----------------- | ----------------- |
| `SAVE`     | **阻塞主进程**，直到快照完成  | 调试环境（生产环境禁用）      |
| `BGSAVE`   | **非阻塞**，fork 子进程执行 | 生产环境推荐（自动触发也用此方式） |

#### 2. 自动触发

通过配置 `save` 规则：

```bash
# redis.conf
save 900 1      # 900 秒内至少 1 次修改
save 300 10     # 300 秒内至少 10 次修改
save 60 10000   # 60 秒内至少 10000 次修改
```

**任意一条规则满足即触发 BGSAVE。**

#### 3. 其他触发场景

- **主从复制**：主节点执行 `BGSAVE` 生成 RDB 发送给从节点。
- **执行 SHUTDOWN**：Redis 会先执行 `SAVE` 保存数据。
- **执行 FLUSHALL**：清空所有数据后生成一个空的 RDB 文件。

---

## 2.2 BGSAVE 工作流程

```
1. Redis 主进程 fork 出子进程（子进程继承父进程的内存快照）
   │
   ├─ 子进程写入临时 RDB 文件（dump-temp-xxx.rdb）
   │
   ├─ 主进程继续处理客户端请求（COW 机制保证数据一致性）
   │
   └─ 子进程完成后，原子性替换旧 RDB 文件
```

### Copy-On-Write (COW) 机制

**问题：** 子进程执行 BGSAVE 时，主进程可能修改数据，如何保证快照一致性？

**解决：** fork 时，子进程和父进程共享内存页（只读）。当主进程修改数据时，操作系统会复制被修改的内存页（写时复制），子进程仍持有旧数据。

**优势：** 无需完整复制内存，节省时间和空间。

**风险：** 如果修改量大，可能导致内存使用翻倍（最坏情况）。

---

## 2.3 RDB 文件格式

RDB 是二进制格式，结构如下：

```
[REDIS] [版本号] [数据库号] [键值对1] [键值对2] ... [EOF] [校验和]
```

**优势：**
- **体积小**：经过 LZF 压缩算法压缩。
- **恢复快**：直接加载到内存，比 AOF 快 10 倍以上。

**劣势：**
- **数据丢失风险**：两次快照之间的数据会丢失。
- **不可读**：无法手动编辑或排查问题。

---

## 2.4 RDB 配置详解

```bash
# RDB 文件名
dbfilename dump.rdb

# RDB 文件存储目录
dir /var/lib/redis/

# 自动触发规则（可配置多条）
save 900 1
save 300 10
save 60 10000

# BGSAVE 失败时，停止写入（保护数据）
stop-writes-on-bgsave-error yes

# 是否压缩 RDB 文件（推荐开启）
rdbcompression yes

# 是否校验 RDB 文件（推荐开启，但会影响 10% 性能）
rdbchecksum yes
```

---

## 2.5 RDB 的优缺点

| **优点**              | **缺点**                   |
| ------------------- | ------------------------ |
| 文件体积小（压缩后）          | 数据丢失风险高（快照间隔内的数据会丢）      |
| 恢复速度快（直接加载到内存）      | fork 子进程有短暂阻塞（毫秒级）       |
| 适合冷备份和灾难恢复          | 不适合实时性要求高的场景（如金融交易）      |
| 对性能影响小（子进程异步执行）     | 大数据量时 fork 和 COW 可能导致内存翻倍 |

---

# 三、AOF (Append Only File) - 增量日志

## 3.1 核心原理

**AOF 记录每条写命令**：将客户端的写操作（SET、DEL 等）追加到日志文件（`appendonly.aof`）。

### 工作流程

```
客户端请求
   ↓
Redis 主进程执行命令
   ↓
将命令追加到 AOF 缓冲区
   ↓
根据刷盘策略写入磁盘
```

---

## 3.2 刷盘策略（appendfsync）

| **策略**         | **刷盘时机**         | **数据安全性**  | **性能**  | **推荐场景**   |
| -------------- | ---------------- | ---------- | ------- | ---------- |
| `always`       | 每条命令立即刷盘         | ★★★★★（几乎不丢） | ★（最慢）   | 金融、支付系统    |
| **`everysec`** | **每秒刷盘一次（默认）**   | ★★★★（最多丢 1 秒） | ★★★★（推荐） | **通用场景（推荐）** |
| `no`           | 由操作系统决定（通常 30 秒） | ★★（可能丢数分钟）  | ★★★★★（最快） | 可丢失数据的场景   |

**配置方式：**
```bash
# redis.conf
appendonly yes
appendfsync everysec
```

---

## 3.3 AOF 重写（Rewrite）

### 为什么需要重写？

AOF 文件会不断增大（每条写命令都追加），导致：
1. 文件体积膨胀（可能达到几十 GB）。
2. Redis 启动时加载 AOF 文件耗时过长。

### 重写原理

**核心思想：** 生成一个新的 AOF 文件，只保留当前数据的最少命令集。

**示例：**
```bash
# 原 AOF 文件
SET key1 100
SET key1 200
SET key1 300
INCR key1

# 重写后 AOF 文件
SET key1 301
```

### 重写触发方式

#### 1. 手动触发
```bash
BGREWRITEAOF
```

#### 2. 自动触发
```bash
# redis.conf
auto-aof-rewrite-percentage 100  # AOF 文件增长 100% 时触发
auto-aof-rewrite-min-size 64mb   # AOF 文件至少达到 64MB 才触发
```

**计算公式：**
```
触发条件 = (当前 AOF 大小 - 上次重写后 AOF 大小) / 上次重写后 AOF 大小 >= 100%
         && 当前 AOF 大小 >= 64MB
```

---

## 3.4 AOF 重写流程（BGREWRITEAOF）

```
1. Redis 主进程 fork 子进程
   │
   ├─ 子进程遍历内存数据，生成新 AOF 文件（appendonly-temp-xxx.aof）
   │
   ├─ 主进程继续处理请求，新命令同时写入：
   │   ├─ 旧 AOF 文件（保证不丢失）
   │   └─ AOF 重写缓冲区（rewrite buffer）
   │
   ├─ 子进程完成后，主进程将 AOF 重写缓冲区的命令追加到新 AOF 文件
   │
   └─ 原子性替换旧 AOF 文件
```

**关键点：**
- **AOF 重写缓冲区**：避免重写期间的新命令丢失。
- **阻塞时间**：仅在最后替换文件时有短暂阻塞（毫秒级）。

---

## 3.5 AOF 文件格式

AOF 是文本格式，使用 **RESP 协议**（Redis Serialization Protocol）。

**示例：**
```bash
*3           # 3 个参数
$3           # 第一个参数长度为 3
SET
$4
key1
$5
value
```

**优势：**
- **可读性强**：可以用文本编辑器查看和修改。
- **可排查**：出现问题可手动删除错误命令。

**劣势：**
- **体积大**：同样数据的 AOF 文件比 RDB 大 5-10 倍。

---

## 3.6 AOF 损坏修复

**场景：** Redis 异常宕机，AOF 文件可能损坏（最后一条命令不完整）。

**修复工具：**
```bash
redis-check-aof --fix appendonly.aof
```

**原理：** 删除文件末尾的不完整命令，保留有效部分。

---

## 3.7 AOF 配置详解

```bash
# 启用 AOF
appendonly yes

# AOF 文件名
appendfilename "appendonly.aof"

# 刷盘策略
appendfsync everysec

# 重写期间是否暂停刷盘（避免磁盘 I/O 冲突）
no-appendfsync-on-rewrite no

# 自动重写触发条件
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# AOF 重写时是否使用 RDB-preamble 格式（混合持久化）
aof-use-rdb-preamble yes
```

---

## 3.8 AOF 的优缺点

| **优点**              | **缺点**              |
| ------------------- | ------------------- |
| 数据丢失少（最多丢 1 秒）      | 文件体积大（比 RDB 大 5-10 倍） |
| 可读性强，便于排查问题         | 恢复速度慢（需重放所有命令）      |
| 支持自动重写，压缩文件大小       | 重写时可能短暂阻塞           |
| 适合实时性要求高的场景（如金融交易） | 对磁盘 I/O 要求高          |

---

# 四、混合持久化（RDB + AOF）

## 4.1 设计背景

| **问题**         | **RDB**  | **AOF**  | **混合持久化**  |
| -------------- | -------- | -------- | ---------- |
| 数据丢失风险         | 高        | 低        | **低**      |
| 恢复速度           | 快        | 慢        | **快**      |
| 文件体积           | 小        | 大        | **中等**     |

**Redis 4.0+ 引入混合持久化**，兼具两者优点。

---

## 4.2 工作原理

**在 AOF 重写时：**
1. 前半部分：生成 **RDB 格式的快照**（压缩二进制）。
2. 后半部分：追加重写期间的 **增量命令**（AOF 格式）。

**AOF 文件结构：**
```
[RDB 二进制数据] + [AOF 增量命令]
```

---

## 4.3 启用混合持久化

```bash
# redis.conf
appendonly yes
aof-use-rdb-preamble yes  # 开启混合持久化（默认 yes）
```

**验证：**
```bash
$ head -c 5 appendonly.aof
REDIS  # 如果看到 "REDIS" 标识，说明前半部分是 RDB 格式
```

---

## 4.4 恢复流程

1. Redis 启动时检测到 AOF 文件。
2. 先加载 RDB 部分（快速恢复大部分数据）。
3. 再重放 AOF 增量命令（补齐重写期间的新数据）。

**恢复速度：** 比纯 AOF 快 **5-10 倍**。

---

# 五、持久化策略选择

## 5.1 对比总结

| **场景**            | **推荐方案**           | **理由**                  |
| ----------------- | ------------------ | ----------------------- |
| **通用生产环境**        | **混合持久化（RDB+AOF）** | **平衡性能与数据安全（默认推荐）**     |
| 数据可丢失（如缓存）        | 仅 RDB 或关闭持久化       | 性能最优，数据来源于数据库           |
| 金融/交易系统（不可丢数据）   | AOF (always)       | 数据安全性优先                 |
| 大数据量 + 频繁写入      | 混合持久化 + SSD 磁盘     | 避免磁盘 I/O 瓶颈             |
| 备份与灾难恢复           | RDB                | 文件小，便于跨机房传输             |

---

## 5.2 配置建议

### 通用生产环境（推荐）

```bash
# 同时启用 RDB 和 AOF
save 900 1
save 300 10
save 60 10000

appendonly yes
appendfsync everysec
aof-use-rdb-preamble yes

# 避免重写时阻塞
no-appendfsync-on-rewrite yes
```

### 高可用场景（金融/支付）

```bash
# 关闭 RDB，仅用 AOF
save ""

appendonly yes
appendfsync always  # 每条命令立即刷盘（性能下降 50%）
aof-use-rdb-preamble yes
```

### 纯缓存场景

```bash
# 关闭所有持久化
save ""
appendonly no
```

---

# 六、持久化监控与调优

## 6.1 监控指标

```bash
INFO persistence
```

**关键指标：**
```
# RDB
rdb_last_save_time         # 最后一次 RDB 时间
rdb_changes_since_last_save # 距上次 RDB 的修改次数
rdb_current_bgsave_time_sec # 当前 BGSAVE 耗时

# AOF
aof_enabled                 # 是否启用 AOF
aof_current_size            # 当前 AOF 文件大小
aof_base_size               # 上次重写后的 AOF 大小
aof_pending_rewrite         # 是否有待执行的重写任务
```

---

## 6.2 性能优化建议

### 1. 减少 fork 阻塞

**问题：** 大数据量时，fork 子进程可能阻塞 100ms+。

**优化：**
- 控制 Redis 实例内存（建议 < 20GB）。
- 使用 **Transparent Huge Pages (THP)**：
  ```bash
  echo never > /sys/kernel/mm/transparent_hugepage/enabled
  ```

### 2. 避免内存翻倍

**问题：** COW 机制可能导致内存使用翻倍。

**优化：**
- 避免在高峰期执行 BGSAVE/BGREWRITEAOF。
- 使用 Redis Cluster 分散数据。

### 3. 磁盘 I/O 优化

**问题：** AOF 频繁刷盘影响性能。

**优化：**
- 使用 SSD 磁盘（IOPS 提升 10 倍）。
- 启用 `no-appendfsync-on-rewrite yes`（重写期间暂停刷盘）。

---

## 6.3 故障排查

### 问题 1：Redis 启动失败，提示 "Bad file format"

**原因：** RDB/AOF 文件损坏。

**解决：**
```bash
# 检查并修复 AOF
redis-check-aof --fix appendonly.aof

# 检查 RDB
redis-check-rdb dump.rdb
```

### 问题 2：持久化耗时过长

**排查：**
```bash
INFO persistence
SLOWLOG GET 10  # 查看慢日志
```

**优化：**
- 减少 `save` 规则频率。
- 提升 `auto-aof-rewrite-min-size` 阈值。

---

# 七、面试高频问题

1. **RDB 和 AOF 的区别？生产环境如何选择？**
   - RDB 快但可能丢数据，AOF 安全但体积大，推荐混合持久化。

2. **BGSAVE 的 fork 过程会阻塞主进程吗？**
   - fork 时有短暂阻塞（毫秒级），之后主进程继续处理请求。

3. **AOF 重写期间新命令如何保证不丢失？**
   - 新命令同时写入旧 AOF 和 AOF 重写缓冲区。

4. **混合持久化如何工作？**
   - AOF 重写时前半部分生成 RDB 快照，后半部分追加增量命令。

5. **如何避免持久化导致的内存翻倍？**
   - 控制单实例内存 < 20GB，避免高峰期执行持久化。

6. **Redis 宕机后如何恢复数据？**
   - 优先加载 AOF（数据更全），AOF 不存在则加载 RDB。

7. **appendfsync 的三种策略如何选择？**
   - `always`（金融）、`everysec`（通用）、`no`（可丢失数据）。

---

通过合理配置持久化策略，可以在性能与数据安全之间取得最佳平衡！🚀
