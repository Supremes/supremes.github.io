---
title: 全局唯一 ID 生成方案
date: 2026-08-06
tags:
  - 分布式系统
  - 唯一ID
  - 雪花算法
summary: "从分库分表的现实约束出发，横向对比 UUID、数据库自增、号段模式、Redis INCR、雪花算法与 ULID，深挖 Snowflake 的时钟回拨问题与工业级实现（美团 Leaf、百度 uid-generator），并给出选型决策树。"
---

单机时代主键交给 `AUTO_INCREMENT` 就够了。一旦分库分表、多机房部署，数据库自增就从「免费午餐」变成了「冲突源头」——这才是全局唯一 ID 这个课题存在的原因。

---

# 一、什么时候真的需要它

不要为了「分布式」而分布式。只有下面这些场景才值得引入独立的 ID 生成器：

| 场景 | 为什么单库自增不够 |
| --- | --- |
| **分库分表** | 每个物理库各自维护自增序列，跨库主键必然重复 |
| **数据迁移 / 合并** | 两套库合并时主键撞车，只能全量重映射 |
| **多机房 / 单元化** | 跨机房无法共享一个自增序列 |
| **链路追踪 traceId** | 需要在服务间传递，且不能依赖任何存储 |
| **对外暴露的业务单号** | 订单号、支付流水号，既要唯一又不能被猜出总量 |

---

# 二、评价一个 ID 方案的四个维度

这四条是后面所有对比的标尺，也是面试时的答题框架。

**1. 全局唯一（硬性）**
任何情况下不可重复，包括时钟回拨、节点重启、机器 ID 冲突这些异常路径。

**2. 趋势递增（性能相关）**
InnoDB 主键索引是聚簇索引 B+ 树。**有序插入**只会在最右侧的叶子节点追加；**随机插入**（如 UUID v4）会命中随机页面，导致：

- 频繁的**页分裂**，B+ 树结构反复调整
- 页填充率下降，索引膨胀（同样数据量占用更多页）
- Buffer Pool 命中率暴跌，随机 IO 上升

这是 UUID v4 做主键最致命的问题，量级上来后写入性能可以差出数倍。

**3. 高可用（可用性）**
ID 生成器是**写链路上的强依赖**——它挂了，所有插入操作全挂。所以必须能容忍下游（DB / ZK / Redis）短时不可用。

**4. 信息安全（业务相关）**
连续自增的订单号会泄漏经营数据：竞对每天下单两次，两个单号相减就是你的日单量（经典的「德军坦克问题」）。对外单号必须**不可枚举**。

> [!warning] 趋势递增 与 信息安全 天然冲突
> 一个要求可预测有序，一个要求不可预测。工程上的解法是**内外分离**：内部主键用趋势递增的 Snowflake，对外单号另生成一套带随机因子的编号，两者建映射。

---

# 三、方案横评

## 3.1 UUID

```java
String id = UUID.randomUUID().toString();
// "8f14e45f-ceea-467a-9575-9a0d1f43a0dc"
```

**UUID v4**：128 位，其中 122 位随机。本地生成、零依赖、性能极高。

**致命缺陷**：

- **完全无序** → B+ 树页分裂（见 2.2）
- **36 个字符**，作为主键会被所有二级索引冗余存储一份，索引体积膨胀明显
- 可读性差，不能作为业务单号

> [!tip] UUID v7：值得关注的新选项
> RFC 9562（2024 年发布，取代 RFC 4122）正式引入 **UUID v7**：高 48 位是 Unix 毫秒时间戳，剩余为随机位。**既保留 UUID 的零依赖，又具备时间有序性**，解决了 v4 的页分裂问题。
>
> Java 标准库尚未内置 v7，可用 `com.github.f4b6a3:uuid-creator` 或 JDK 之外的实现。新项目如果不想自建发号器，UUID v7 是比 v4 好得多的默认选择。

**适用**：临时标识、幂等 key、文件名、traceId。**不建议**作为大表主键（v4）。

---

## 3.2 数据库自增 + 步长

多个 DB 实例设置不同起点、相同步长，天然错开：

```sql
-- 实例 1
set @@auto_increment_offset    = 1;
set @@auto_increment_increment = 4;   -- 生成 1, 5, 9, 13 ...

-- 实例 2
set @@auto_increment_offset    = 2;
set @@auto_increment_increment = 4;   -- 生成 2, 6, 10, 14 ...
```

**优点**：实现成本几乎为零，ID 短、单调递增。

**缺点**：

- **扩容是灾难**：步长写死为 4，想加到第 5 台机器就得重算全局步长，几乎无法在线完成
- 每取一个 ID 就是一次 DB 写操作，QPS 上限被数据库锁死
- 强依赖 DB 可用性

**适用**：机器数量固定、并发不高的中小系统。

---

## 3.3 号段模式（Leaf-segment）

数据库自增的问题在于**每次都要访问 DB**。号段模式的核心思路是：**一次批发一段，在内存里零售。**

表结构：

```sql
CREATE TABLE leaf_alloc (
  biz_tag     VARCHAR(128) NOT NULL COMMENT '业务标识，实现隔离',
  max_id      BIGINT       NOT NULL COMMENT '当前已分配的最大 ID',
  step        INT          NOT NULL COMMENT '号段长度',
  update_time TIMESTAMP    NOT NULL,
  PRIMARY KEY (biz_tag)
);
```

取号段的 SQL 在一个事务内完成：

```sql
UPDATE leaf_alloc SET max_id = max_id + step WHERE biz_tag = 'order';
SELECT max_id, step FROM leaf_alloc WHERE biz_tag = 'order';
```

拿到 `(max_id - step, max_id]` 这一段后，进程内用 `AtomicLong` 自增分发。**DB 访问频率被降低了 step 倍。**

### 双 Buffer 优化

朴素实现有个毛刺：号段耗尽的那一刻，所有请求都会阻塞等待一次 DB IO。Leaf 的做法是**准备两个 buffer**：

```
current buffer  ████████████░░░░░░░░  消耗到 10% 时
                     ↓ 触发异步线程预加载
next buffer     ████████████████████  提前就绪

current 耗尽 → 无缝切换到 next → 再异步准备新的 next
```

关键点：**在当前号段消耗到 10% 时，就异步把下一个号段拉回来**，让取号永远不阻塞在 IO 上。

**优点**：

- DB 压力极低，性能好
- **DB 短时宕机不影响服务**——内存里还有整个号段可用（这是相对 Redis INCR 的核心优势）
- ID 单调递增，可通过 `biz_tag` 做业务隔离

**缺点**：

- ID 号段连续 → **可被枚举**，不适合直接做对外单号
- 服务重启会浪费当前号段剩余部分（ID 不连续，但这通常无所谓）
- 仍然依赖 DB（只是弱依赖）

**适用**：绝大多数内部业务主键。**这是性价比最高的方案。**

---

## 3.4 Redis INCR

```java
public Long generateId() {
    return redisTemplate.opsForValue().increment("global:id");
}
```

`INCR` 是原子操作，单机可达 10 万 QPS。

**缺点**：

- **引入新的强依赖**：Redis 挂了，ID 生成直接不可用
- **主从异步复制存在丢号风险**：主节点 `INCR` 后未来得及同步就宕机，从节点晋升后会**重复发放**已用过的 ID
- 需要考虑持久化策略（AOF `everysec` 仍有最多 1 秒的数据丢失窗口）

**改进**：同样可以用号段思路——每次 `INCRBY 1000` 批发一段到本地，既降低 Redis 压力，也缓解丢号影响。

**适用**：系统里已经重度依赖 Redis、且能接受上述风险时的轻量方案。详见 [Redis 应用场景实战](../06-Redis/redis应用场景实战.md) 第四章。

---

## 3.5 雪花算法（Snowflake）

Twitter 开源方案，**纯本地生成，不依赖任何外部存储**，是目前最主流的分布式 ID 算法。

### 位分配

```
 0  |  0000000000 0000000000 0000000000 0000000000 0  | 0000000000 |  000000000000
 ↑                          ↑                              ↑              ↑
符号位(1)              时间戳差值(41)                  机器ID(10)      序列号(12)
恒为0                  毫秒级，约 69 年                 1024 个节点    单毫秒 4096 个
```

| 段 | 位数 | 容量 | 说明 |
| --- | --- | --- | --- |
| 符号位 | 1 | — | 恒为 0，保证 ID 为正数 |
| 时间戳 | 41 | 2^41 ms ≈ **69 年** | 存的是**与自定义纪元的差值**，不是绝对时间戳 |
| 机器 ID | 10 | **1024** 个节点 | 常拆成 5 位 datacenterId + 5 位 workerId |
| 序列号 | 12 | **4096 个/ms** | 同毫秒内递增，用尽则自旋等待下一毫秒 |

理论吞吐：**409.6 万 ID/秒/节点**。

> [!note] 纪元（epoch）必须自定义
> 41 位只有 69 年寿命。如果用 1970-01-01 做起点，2039 年就溢出了。**务必把 epoch 设为项目上线日期**，这样能用到 2095 年。

### 核心实现

```java
public class SnowflakeIdGenerator {

    private final long epoch = 1735689600000L;  // 自定义纪元：2025-01-01
    private final long workerIdBits   = 10L;
    private final long sequenceBits   = 12L;
    private final long maxWorkerId    = ~(-1L << workerIdBits);   // 1023
    private final long sequenceMask   = ~(-1L << sequenceBits);   // 4095

    private final long workerIdShift  = sequenceBits;             // 12
    private final long timestampShift = sequenceBits + workerIdBits; // 22

    private final long workerId;
    private long sequence      = 0L;
    private long lastTimestamp = -1L;

    public SnowflakeIdGenerator(long workerId) {
        if (workerId < 0 || workerId > maxWorkerId) {
            throw new IllegalArgumentException("workerId 超出范围: " + workerId);
        }
        this.workerId = workerId;
    }

    public synchronized long nextId() {
        long timestamp = System.currentTimeMillis();

        // 时钟回拨检测
        if (timestamp < lastTimestamp) {
            long offset = lastTimestamp - timestamp;
            if (offset <= 5) {
                // 小幅回拨：等待时钟追上
                try {
                    wait(offset << 1);
                    timestamp = System.currentTimeMillis();
                    if (timestamp < lastTimestamp) {
                        throw new IllegalStateException("时钟回拨，拒绝生成 ID");
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    throw new IllegalStateException(e);
                }
            } else {
                // 大幅回拨：直接失败，绝不生成可能重复的 ID
                throw new IllegalStateException("时钟回拨 " + offset + "ms，拒绝生成 ID");
            }
        }

        if (timestamp == lastTimestamp) {
            sequence = (sequence + 1) & sequenceMask;
            if (sequence == 0) {
                // 当前毫秒序列号用尽，自旋到下一毫秒
                timestamp = tilNextMillis(lastTimestamp);
            }
        } else {
            sequence = 0L;
        }

        lastTimestamp = timestamp;

        return ((timestamp - epoch) << timestampShift)
             | (workerId << workerIdShift)
             | sequence;
    }

    private long tilNextMillis(long lastTimestamp) {
        long timestamp = System.currentTimeMillis();
        while (timestamp <= lastTimestamp) {
            timestamp = System.currentTimeMillis();
        }
        return timestamp;
    }
}
```

快速接入可直接用 Hutool：

```java
@Bean
public Snowflake snowflake() {
    return IdUtil.getSnowflake(workerId, datacenterId);
}
```

---

## 3.6 ULID / NanoID

| 方案 | 结构 | 长度 | 特点 |
| --- | --- | --- | --- |
| **ULID** | 48 位毫秒时间戳 + 80 位随机 | 26 字符（Crockford Base32） | **字典序 = 时间序**，无需中心化协调，URL 安全 |
| **NanoID** | 纯随机 | 默认 21 字符 | 比 UUID 更短、URL 安全，**完全无序** |
| **MongoDB ObjectId** | 4 字节秒级时间戳 + 5 字节随机 + 3 字节计数器 | 24 位 hex | 时间有序，MongoDB 默认主键 |

ULID 和 UUID v7 解决的是同一个问题（有序 + 无依赖），差别主要在编码格式和生态支持。**如果不想维护 workerId 分配机制，ULID / UUID v7 是 Snowflake 的轻量替代品**——代价是失去了 ID 中携带机器信息的可追溯性。

---

# 四、Snowflake 的两个工程难点

Snowflake 算法本身十行代码就能写完，真正的难点全在这两处。

## 4.1 时钟回拨

**成因**：NTP 校时向后调整、虚拟机快照恢复、闰秒处理、运维手动改时间。

一旦时钟回拨，同一个 `(时间戳, workerId, sequence)` 组合就可能重复出现——**直接产生重复 ID**。

三种应对策略：

| 策略 | 做法 | 适用 |
| --- | --- | --- |
| **等待** | 回拨幅度小（如 < 5ms）时阻塞等待时钟追平 | 最常用，覆盖 NTP 微调 |
| **拒绝** | 回拨幅度大时抛异常，让上游重试或摘除节点 | 保证正确性优先，**绝不能静默生成** |
| **借用未来时间** | 维护一个逻辑时钟，回拨时继续用上次时间戳 + 序列号 | 百度 uid-generator 思路 |

> [!danger] 绝对不要「忽略回拨继续生成」
> 重复主键会引发插入失败、数据覆盖甚至资损。**宁可短暂不可用，也不能生成重复 ID。**

**Leaf-snowflake 的做法**：节点启动时把当前时间写入 ZooKeeper 持久节点；每次启动先与 ZK 上记录的时间戳、以及其他节点的平均时间做比对，**发现本机时钟异常则直接拒绝启动**，从源头堵住问题。

## 4.2 workerId 如何分配

1024 个槽位，必须保证**任意时刻不重复**。

| 方式 | 说明 | 风险 |
| --- | --- | --- |
| **配置文件写死** | 每台机器手工配 | 扩容易出错，容器化环境不可行 |
| **ZooKeeper 顺序节点** | 启动时注册获取自增编号（Leaf 方案） | 引入 ZK 依赖，需处理节点复用 |
| **Redis INCR** | 启动时 `INCR` 取号 | 重启会不断消耗号段，需回收机制 |
| **数据库分配表** | 按 IP/hostname 查表取固定 ID | 简单可靠，推荐 |
| **K8s StatefulSet 序号** | 从 Pod 名 `app-3` 中解析出 `3` | 云原生环境的最优解，天然稳定唯一 |
| **IP / MAC 哈希** | 取 IP 后两段做位运算 | **有哈希冲突风险**，不推荐用于生产 |

> [!warning] 容器化环境的坑
> Deployment 部署的 Pod IP 会漂移，用 IP 派生 workerId 极易冲突。**有状态发号需求请用 StatefulSet，或走 ZK / DB 集中分配。**

---

# 五、工业级实现参考

## 5.1 美团 Leaf

同时提供两种模式，可按业务选择：

- **Leaf-segment**：号段模式 + 双 Buffer（见 3.3），主打稳定、可容忍 DB 抖动
- **Leaf-snowflake**：Snowflake + ZooKeeper 管理 workerId 和时钟校验

## 5.2 百度 uid-generator

在 Snowflake 基础上做了两处关键改造：

**① 重新分配位数**（默认）：

```
1 位符号 + 28 位时间戳（秒级） + 22 位 workerId + 13 位序列号
```

时间戳降到**秒级**、workerId 扩到 **22 位（400 万）**——因为它的 workerId 是**每次启动从 DB 取一个新的**，用完即弃，所以需要海量槽位。

**② RingBuffer 预生成**：

`CachedUidGenerator` 用环形数组**提前把 ID 生产好缓存起来**，消费时直接取。这带来两个收益：

- 消除运行时的时钟依赖，**天然规避时钟回拨**（用的是逻辑递增的秒数）
- 通过缓存行填充（padding）解决**伪共享**问题，并发性能极高

## 5.3 ShardingSphere

分库分表中间件内置 `SNOWFLAKE` 主键生成器，配置即用：

```yaml
rules:
  - !SHARDING
    tables:
      t_order:
        keyGenerateStrategy:
          column: order_id
          keyGeneratorName: snowflake
    keyGenerators:
      snowflake:
        type: SNOWFLAKE
```

---

# 六、选型决策

## 6.1 对比总表

| 方案 | 唯一性 | 有序性 | 性能 | 外部依赖 | 可枚举 | 长度 |
| --- | --- | --- | --- | --- | --- | --- |
| UUID v4 | ✅ | ❌ 完全无序 | 极高 | 无 | 否 | 36 字符 |
| UUID v7 / ULID | ✅ | ✅ 趋势递增 | 极高 | 无 | 否 | 36 / 26 字符 |
| DB 自增 + 步长 | ✅ | ✅ 严格递增 | 低 | 强依赖 DB | **是** | 短 |
| 号段模式 | ✅ | ✅ 趋势递增 | 高 | 弱依赖 DB | **是** | 短 |
| Redis INCR | ⚠️ 主从有丢号风险 | ✅ 严格递增 | 高 | 强依赖 Redis | **是** | 短 |
| Snowflake | ✅ | ✅ 趋势递增 | 极高 | 无（需分配 workerId） | 否 | 19 位数字 |

## 6.2 决策树

```
需要全局唯一 ID
│
├─ 是否作为数据库主键？
│  │
│  ├─ 否（traceId / 幂等 key / 文件名）
│  │  └──→ UUID v4 或 NanoID，足够了
│  │
│  └─ 是
│     │
│     ├─ 能接受引入基础设施吗？
│     │  ├─ 不能（小团队 / Serverless）
│     │  │  └──→ UUID v7 或 ULID（有序、零依赖）
│     │  │
│     │  └─ 能
│     │     ├─ 有稳定的 workerId 来源（K8s StatefulSet / ZK / DB）？
│     │     │  └──→ Snowflake ⭐ 性能最优
│     │     │
│     │     └─ 没有，但有 MySQL
│     │        └──→ 号段模式（Leaf-segment）⭐ 最稳
│
└─ 是对外暴露的业务单号（订单号 / 流水号）？
   └──→ 内部主键用 Snowflake / 号段
        对外单号 = 业务前缀 + 日期 + 随机串，另建映射
        （绝不能直接暴露连续递增的内部 ID）
```

## 6.3 一句话结论

- **有 K8s / ZK，追求极致性能** → Snowflake
- **只有 MySQL，追求稳定** → 号段模式（Leaf-segment）
- **不想维护任何发号服务** → UUID v7 / ULID
- **对外单号** → 一定要加随机因子，与内部主键解耦

---

# 七、高频面试题

**Q：为什么 UUID 不适合做 MySQL 主键？**
InnoDB 主键是聚簇索引，UUID v4 无序会导致随机位置插入 → 页分裂、页填充率低、Buffer Pool 命中率下降；且 36 字符会被所有二级索引冗余存储，索引膨胀。

**Q：Snowflake 的 41 位时间戳能用多久？为什么？**
2^41 毫秒 ≈ 69.7 年。前提是存**与自定义纪元的差值**——如果用 1970 做起点，2039 年就会溢出。

**Q：时钟回拨怎么处理？**
小幅回拨（毫秒级）阻塞等待时钟追平；大幅回拨直接抛异常拒绝服务并告警。绝不能忽略回拨继续生成。工程上还可以像 Leaf 那样启动时用 ZK 校验时钟，或像 uid-generator 那样用逻辑时钟彻底规避。

**Q：号段模式相比 Redis INCR 好在哪？**
号段模式把一整段 ID 缓存在内存里，**DB 短时宕机不影响发号**；Redis INCR 是强依赖，且主从异步复制在故障切换时可能重复发号。

**Q：双 Buffer 解决了什么问题？**
朴素号段模式在号段耗尽瞬间会阻塞等待 DB IO，产生请求毛刺。双 Buffer 在当前号段消耗到 10% 时异步预加载下一段，让取号永不阻塞在 IO 上。

**Q：订单号可以直接用自增 ID 吗？**
不可以。连续递增会泄漏业务量（下两单相减即得日单量）。对外单号必须引入随机因子，与内部主键解耦。

---

# 相关阅读

- [分库分表速查](./分库分表速查.md)：本文的上游话题，为什么会需要全局 ID
- [Redis 分布式锁实战](../06-Redis/redis分布式锁.md)：分布式系统的另一块基石
- [Redis 应用场景实战](../06-Redis/redis应用场景实战.md)：Redis 视角下的 ID 生成实现
- [MySQL 核心原理笔记](../05-MySQL/mysql核心原理笔记.md)：InnoDB 聚簇索引与页分裂
