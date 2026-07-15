---
title: Redis 核心技术与实战
date: 2026-01-03
tags:
  - Redis
  - 数据库
  - 缓存
---
Redis 是一款高性能的键值数据库，广泛应用于缓存、消息队列、排行榜、分布式锁等场景。掌握 Redis 的核心原理和实战技巧是后端开发工程师的必备技能。

---

# 本站 Redis 导航

建议阅读顺序：基础数据类型 → 底层数据结构 → 持久化 → 缓存策略 → 集群架构 → 分布式锁 → 性能优化 → 应用场景。

- [[Redis数据类型与底层实现]]：String/Hash/List/Set/ZSet 五大类型，SDS/ziplist/skiplist/intset/dict 底层实现，编码转换规则
- [[Redis持久化机制]]：RDB 快照原理、AOF 日志机制、混合持久化策略、持久化配置调优
- [[Redis缓存策略]]：缓存穿透/击穿/雪崩解决方案、缓存更新策略（旁路/直写/异步刷新）、布隆过滤器实战
- [[Redis集群方案]]：主从复制原理、哨兵选举机制、Cluster 分片与槽位、一致性哈希、扩缩容流程
- [[Redis分布式锁]]：基于 SETNX 实现、Redisson 分布式锁、Redlock 算法、锁续期与看门狗机制
- [[Redis-性能优化]]：Pipeline 批量操作、大 key 与热 key 处理、内存淘汰策略、慢查询分析、Redis 多线程模型
- [[Redis应用场景实战]]：排行榜（ZSet）、消息队列（Stream）、限流（漏桶/令牌桶）、分布式 ID、地理位置、会话共享

下面是 Redis 知识体系的完整学习路径：

---

## Redis 学习大纲

### 第一阶段：数据类型与核心命令

1. **五大基础数据类型：**
   - **String (字符串)：**
     - 应用场景：缓存、计数器、分布式锁、Session 共享。
     - 核心命令：`SET`, `GET`, `INCR`, `DECR`, `SETEX`, `SETNX`。
     - 底层实现：SDS (Simple Dynamic String)，预分配空间、杜绝缓冲区溢出。
   - **Hash (哈希)：**
     - 应用场景：存储对象（如用户信息）。
     - 核心命令：`HSET`, `HGET`, `HMGET`, `HINCRBY`。
     - 底层实现：ziplist（元素少时）或 dict（元素多时）。
   - **List (列表)：**
     - 应用场景：消息队列、文章列表、最新消息。
     - 核心命令：`LPUSH`, `RPUSH`, `LPOP`, `RPOP`, `LRANGE`, `BLPOP`。
     - 底层实现：quicklist（双向链表 + ziplist 的混合体）。
   - **Set (集合)：**
     - 应用场景：标签系统、共同好友、去重。
     - 核心命令：`SADD`, `SMEMBERS`, `SINTER`, `SUNION`, `SISMEMBER`。
     - 底层实现：intset（整数集合）或 dict。
   - **ZSet (有序集合)：**
     - 应用场景：排行榜、延时队列、范围查询。
     - 核心命令：`ZADD`, `ZRANGE`, `ZREVRANGE`, `ZRANK`, `ZINCRBY`。
     - 底层实现：ziplist 或 skiplist + dict。

2. **三种特殊数据类型：**
   - **Bitmap (位图)：** 布隆过滤器、签到统计。
   - **HyperLogLog：** 基数统计（UV 统计）。
   - **Geospatial (地理位置)：** 附近的人、打车距离。
   - **Stream (流)：** 消息队列（Redis 5.0+）。

---

### 第二阶段：底层数据结构深入

1. **SDS (Simple Dynamic String)：**
   - 与 C 字符串的区别：`len` 记录长度、`free` 预分配空间、二进制安全。
   - 为什么 Redis 的 String 不用原生 C 字符串？避免溢出、减少内存分配次数。

2. **ziplist (压缩列表)：**
   - 紧凑型数据结构，节省内存。
   - 缺点：连锁更新（cascading update）性能问题。
   - 应用：Hash、List、ZSet 在元素少时使用。

3. **skiplist (跳表)：**
   - 有序数据结构，平均 O(log N) 复杂度。
   - ZSet 的核心实现（配合 dict 实现 O(1) 查找）。
   - 与红黑树对比：实现简单、范围查询友好。

4. **dict (字典/哈希表)：**
   - 渐进式 rehash：避免一次性 rehash 阻塞。
   - 链地址法解决哈希冲突。
   - 应用：Hash、Set、ZSet、Redis 全局键空间。

5. **intset (整数集合)：**
   - Set 在全是整数且数量少时使用。
   - 升级机制：从 int16 -> int32 -> int64。

6. **quicklist：**
   - List 的底层实现（Redis 3.2+）。
   - 双向链表 + ziplist 的混合体，平衡内存与性能。

---

### 第三阶段：持久化机制

1. **RDB (Redis Database Backup)：**
   - 全量快照，适合备份和恢复。
   - 触发方式：`SAVE`（阻塞）、`BGSAVE`（fork 子进程）、自动触发（配置 `save` 规则）。
   - 优点：恢复速度快、文件体积小。
   - 缺点：数据丢失风险（快照间隔内的数据会丢失）。

2. **AOF (Append Only File)：**
   - 增量日志，记录每条写命令。
   - 刷盘策略：`always`（每条命令）、`everysec`（每秒）、`no`（操作系统决定）。
   - AOF 重写（rewrite）：压缩日志文件，减少体积。
   - 优点：数据丢失少、可读性强。
   - 缺点：文件体积大、恢复速度慢。

3. **混合持久化（RDB + AOF）：**
   - Redis 4.0+ 默认策略。
   - AOF 重写时，先生成 RDB 快照，再追加增量命令。
   - 兼具两者优点：恢复快、数据丢失少。

---

### 第四阶段：缓存策略与高可用

1. **缓存更新策略：**
   - **Cache Aside（旁路缓存）：** 读穿透缓存、更新先删缓存再写 DB。
   - **Read/Write Through：** 缓存层自动同步 DB。
   - **Write Behind（异步刷新）：** 先写缓存，异步批量写 DB。

2. **缓存失效问题：**
   - **缓存穿透：** 查询不存在的数据。
     - 解决：布隆过滤器、缓存空对象。
   - **缓存击穿：** 热点 key 过期，瞬时流量打到 DB。
     - 解决：互斥锁（SETNX）、逻辑过期（永不过期 + 异步更新）。
   - **缓存雪崩：** 大量 key 同时过期。
     - 解决：随机过期时间、高可用架构、限流降级。

3. **内存淘汰策略：**
   - `noeviction`：内存满时拒绝写入。
   - `allkeys-lru`：所有 key 按 LRU 淘汰（推荐）。
   - `volatile-lru`：仅淘汰设置了过期时间的 key。
   - `allkeys-random`、`volatile-random`、`volatile-ttl`。

---

### 第五阶段：集群架构

1. **主从复制 (Replication)：**
   - 全量同步（RDB）+ 增量同步（命令传播）。
   - 读写分离：主节点写、从节点读。
   - 缺点：主节点宕机需手动切换。

2. **哨兵模式 (Sentinel)：**
   - 自动故障转移（Failover）。
   - 选举新的主节点（Raft 协议）。
   - 监控 + 通知 + 自动切换。

3. **Cluster (集群)：**
   - 数据分片：16384 个哈希槽（slot）。
   - 去中心化架构，无 Proxy 层。
   - 扩缩容：槽位迁移（`redis-cli --cluster reshard`）。
   - Gossip 协议：节点间通信。

---

### 第六阶段：分布式锁与事务

1. **分布式锁：**
   - 基础实现：`SETNX` + `EXPIRE`（需原子性：`SET key value NX EX seconds`）。
   - Redisson 分布式锁：自动续期（看门狗机制）。
   - Redlock 算法：Redis 作者提出的多节点锁方案（争议较大）。

2. **事务与 Lua 脚本：**
   - **MULTI/EXEC：** 事务不支持回滚，仅保证命令顺序执行。
   - **WATCH：** 乐观锁，监控 key 变化。
   - **Lua 脚本：** 原子性执行一组命令（推荐方式）。

3. **Pipeline（管道）：**
   - 批量发送命令，减少 RTT（Round-Trip Time）。
   - 非原子操作，与事务结合使用可保证原子性。

---

### 第七阶段：性能优化与监控

1. **性能调优：**
   - **大 key 问题：** 使用 `redis-cli --bigkeys` 分析，拆分大 key。
   - **热 key 问题：** 复制多份、使用本地缓存（Caffeine）。
   - **慢查询：** `SLOWLOG GET` 分析慢命令。
   - **Redis 多线程模型：** Redis 6.0+ 网络 I/O 多线程（命令执行仍单线程）。

2. **监控工具：**
   - `INFO` 命令：查看内存、连接、持久化等信息。
   - `MONITOR`：实时查看所有命令（生产慎用，性能影响大）。
   - Redis Exporter + Prometheus + Grafana：企业级监控方案。

---

### 第八阶段：应用场景实战

1. **排行榜：** ZSet 的 `ZADD` + `ZREVRANGE`。
2. **消息队列：** List 的 `BLPOP`/`BRPOP` 或 Stream（推荐）。
3. **限流：** 
   - 固定窗口：`INCR` + `EXPIRE`。
   - 滑动窗口：ZSet 时间戳。
   - 令牌桶/漏桶：Lua 脚本 + 原子操作。
4. **分布式 ID 生成：** `INCR` 单机递增、雪花算法。
5. **会话共享：** Spring Session + Redis。
6. **地理位置：** `GEOADD`、`GEORADIUS` 查找附近的人。
7. **布隆过滤器：** Redisson 实现、缓存穿透防护。

---

## 学习建议

1. **从实战出发：**
   - 先掌握常用命令和应用场景，再深入底层原理。
   - 通过 `redis-cli` 命令行实践每个数据类型。

2. **源码阅读路径：**
   - 先看数据结构源码（如 `sds.c`、`dict.c`）。
   - 再看持久化（`rdb.c`、`aof.c`）。
   - 最后看集群实现（`cluster.c`）。

3. **调试与压测：**
   - 使用 `redis-benchmark` 压测性能。
   - 通过 `INFO MEMORY` 分析内存使用。
   - 使用 Docker 搭建本地 Redis Cluster 环境。

4. **面试准备：**
   - 熟练掌握"三高"问题（穿透、击穿、雪崩）。
   - 理解持久化原理与选型（RDB vs AOF）。
   - 掌握分布式锁实现与坑点（锁过期、死锁）。

5. **持续学习：**
   - 关注 Redis 官方博客和社区动态。
   - 阅读《Redis 设计与实现》（黄健宏）。
   - 学习企业级架构（如阿里云 Redis、AWS ElastiCache）。

---

# 核心知识点速查

## 1. 数据类型与底层编码对应关系

| **类型**  | **底层编码（encoding）**            | **转换条件**                        |
| ------- | ------------------------------ | ------------------------------- |
| String  | int / embstr / raw             | 整数/短字符串（<44 字节）/长字符串           |
| Hash    | ziplist / hashtable            | 元素少且值小 → ziplist，否则 hashtable  |
| List    | quicklist（ziplist + linkedlist） | Redis 3.2+ 统一使用 quicklist       |
| Set     | intset / hashtable             | 全是整数且少 → intset，否则 hashtable    |
| ZSet    | ziplist / skiplist + hashtable | 元素少且值小 → ziplist，否则 skiplist+dict |

---

## 2. 持久化对比表

| **特性**   | **RDB**            | **AOF**            | **混合持久化（RDB+AOF）** |
| -------- | ------------------ | ------------------ | ------------------ |
| **文件大小** | 小（压缩二进制）           | 大（文本日志）            | 中等（前半部分 RDB，后半增量） |
| **恢复速度** | 快                  | 慢                  | 快（先加载 RDB）        |
| **数据丢失** | 多（快照间隔内数据会丢）       | 少（可配置每秒刷盘）         | 少                  |
| **性能影响** | fork 时有短暂阻塞        | 持续追加写，影响较小         | fork + 追加          |
| **适用场景** | 备份、冷数据、对丢失不敏感场景    | 金融、订单等高数据一致性场景     | 生产环境推荐（默认策略）       |

---

## 3. 主从复制 vs 哨兵 vs Cluster

| **架构**   | **优点**              | **缺点**            | **适用场景**   |
| -------- | ------------------- | ----------------- | ---------- |
| **主从复制** | 简单、读写分离             | 手动故障转移、写能力受限      | 小规模、读多写少   |
| **哨兵**   | 自动故障转移、高可用          | 写能力仍受限、运维复杂度提升    | 中等规模、需高可用  |
| **Cluster** | 数据分片、水平扩展、去中心化      | 配置复杂、不支持跨节点事务、运维成本高 | 大规模、高并发、需分片 |

---

## 4. 内存淘汰策略速查

| **策略**          | **淘汰范围**        | **淘汰算法**  | **推荐场景**       |
| --------------- | --------------- | --------- | -------------- |
| noeviction      | -               | -         | 不允许淘汰，写入报错     |
| **allkeys-lru** | **所有 key**      | **LRU**   | **通用场景（推荐）**   |
| volatile-lru    | 设置过期时间的 key     | LRU       | 部分数据需永久保留      |
| allkeys-random  | 所有 key          | 随机        | 测试环境           |
| volatile-random | 设置过期时间的 key     | 随机        | 不推荐            |
| volatile-ttl    | 设置过期时间的 key     | 优先淘汰 TTL 短 | Session、验证码等短期数据 |

---

# 面试题 / Checklist

- Redis 为什么快？单线程模型、IO 多路复用、内存操作、高效数据结构。
- String 的三种编码（int/embstr/raw）分别在什么场景下使用？
- skiplist 的平均时间复杂度是多少？为什么 ZSet 不用红黑树？
- 渐进式 rehash 如何避免阻塞？在 rehash 期间如何查询和插入数据？
- RDB 和 AOF 的区别？混合持久化如何工作？生产环境如何选择？
- 缓存穿透/击穿/雪崩的本质区别与解决方案？
- 布隆过滤器的原理与误判率如何权衡？
- 分布式锁的实现方式？如何解决锁过期问题（Redisson 看门狗）？
- Redis Cluster 的哈希槽（16384）分配原理？节点间如何通信（Gossip）？
- 大 key 和热 key 如何发现与处理？
- Redis 6.0 的多线程是指什么？为什么命令执行仍是单线程？
- Pipeline、事务（MULTI/EXEC）、Lua 脚本三者的区别与适用场景？
- 如何保证缓存与数据库的一致性？先删缓存还是先更新 DB？
- Redis 内存淘汰策略 allkeys-lru 和 volatile-lru 的区别？
- Stream 数据类型相比 List 做消息队列的优势是什么？

---

祝你学习顺利！Redis 是高并发系统的核心组件，掌握它将大大提升你的系统设计能力！🚀
