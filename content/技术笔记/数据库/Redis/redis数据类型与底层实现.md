---
title: Redis 数据类型与底层实现
date: 2026-01-03
tags:
  - Redis
  - 数据结构
---
Redis 的高性能离不开其精心设计的底层数据结构。理解数据类型与底层实现的对应关系，是掌握 Redis 性能优化和故障排查的关键。

---

# 一、Redis 数据类型概览

Redis 支持多种数据类型，每种类型针对不同的应用场景设计：

| **数据类型**             | **底层编码**                         | **典型应用场景**               |
| -------------------- | -------------------------------- | ------------------------ |
| **String (字符串)**     | int / embstr / raw               | 缓存、计数器、分布式锁、Session 共享  |
| **Hash (哈希)**        | ziplist / hashtable              | 存储对象（用户信息、商品详情）          |
| **List (列表)**        | quicklist                        | 消息队列、文章列表、最新消息           |
| **Set (集合)**         | intset / hashtable               | 标签系统、共同好友、去重             |
| **ZSet (有序集合)**      | ziplist / skiplist + hashtable   | 排行榜、延时队列、范围查询            |
| **Bitmap (位图)**      | String 的 bit 操作                  | 签到统计、布隆过滤器               |
| **HyperLogLog**      | 基于概率算法                           | UV 统计、基数计数               |
| **Geospatial (地理位置)** | ZSet（经纬度编码为 score）               | 附近的人、打车距离                |
| **Stream (流)**       | Radix Tree + Listpack            | 消息队列（Redis 5.0+，推荐替代 List） |

---

# 二、底层数据结构详解

## 2.1 SDS (Simple Dynamic String) - 简单动态字符串

### 为什么不用 C 字符串？

Redis 是用 C 语言编写的，但没有使用原生的 C 字符串（以 `\0` 结尾的字符数组），而是自己实现了 SDS。

**C 字符串的缺陷：**
1. **获取长度需要 O(n) 时间**（需遍历到 `\0`）。
2. **无法存储二进制数据**（`\0` 会被误认为结尾）。
3. **容易缓冲区溢出**（strcat 等函数不检查空间）。
4. **频繁内存分配**（每次修改都可能 realloc）。

### SDS 的结构

```c
struct sdshdr {
    int len;       // 已使用字节数（不包括 '\0'）
    int free;      // 未使用字节数
    char buf[];    // 实际存储数据（柔性数组）
};
```

### SDS 的优势

| **特性**     | **C 字符串**    | **SDS**         |
| ---------- | ------------ | --------------- |
| 获取长度复杂度    | O(n)         | **O(1)**（直接读 len） |
| 二进制安全      | ❌（遇到 `\0` 截断） | ✅（len 明确记录长度）    |
| 缓冲区溢出      | ⚠️ 需手动检查      | ✅（自动检查并扩容）      |
| 内存重分配次数    | 修改 N 次需 N 次分配  | **空间预分配** + 惰性释放  |
| 兼容 C 字符串函数 | ✅            | ✅（末尾保留 `\0`）    |

### 内存优化策略

1. **空间预分配：**
   - 当 SDS 扩容时，如果新长度 < 1MB，预分配双倍空间（`len = free`）。
   - 如果新长度 >= 1MB，额外预分配 1MB。

2. **惰性释放：**
   - 缩短字符串时，不立即回收内存，而是增加 `free` 计数，等待复用。

---

## 2.2 ziplist (压缩列表) - 紧凑型数据结构

### 设计目标

**牺牲一定的时间复杂度，换取极致的内存节省。**

ziplist 将所有元素紧密排列在一块连续的内存中，没有额外的指针开销（如链表节点的 prev/next 指针）。

### 结构布局

```
<zlbytes> <zltail> <zllen> <entry1> <entry2> ... <zlend>
```

| **字段**     | **说明**                     |
| ---------- | -------------------------- |
| `zlbytes`  | 整个 ziplist 占用的字节数          |
| `zltail`   | 尾节点的偏移量（用于快速访问尾部）          |
| `zllen`    | 节点数量（当数量 >= 65535 时需遍历统计） |
| `entry`    | 实际存储的节点                    |
| `zlend`    | 结束标志（固定为 `0xFF`）           |

### entry 节点结构

```
<prevlen> <encoding> <data>
```

- **prevlen：** 前一个节点的长度（用于从后向前遍历）。
- **encoding：** 记录 data 的类型和长度（整数或字符串）。
- **data：** 实际数据。

### 连锁更新问题（Cascading Update）

**场景：** 插入一个新节点，导致后续节点的 `prevlen` 字段需要扩展（从 1 字节变为 5 字节），进而引发连锁反应。

**最坏情况：** 所有节点都需要重新分配内存，时间复杂度退化为 O(n²)。

**Redis 的应对：** 限制 ziplist 的使用场景（元素少、值小），超过阈值自动转换为其他编码。

---

## 2.3 skiplist (跳表) - 有序集合的核心

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/redis_skiplist.webp)

Note: skiplist 每一层是一个标准的、有序的双向链表（Redis 中为了支持倒序遍历是双向的，图中简化为单向箭头）。
### 为什么不用红黑树？

| **对比项**  | **跳表**                 | **红黑树**          |
| -------- | ---------------------- | ---------------- |
| 平均时间复杂度  | O(log n)               | O(log n)         |
| 实现难度     | **简单**（概率性插入索引层）       | 复杂（旋转、变色）        |
| 范围查询     | **优秀**（沿着底层链表顺序遍历）     | 中序遍历（需递归）        |
| 内存占用     | 额外索引层（期望 1.33 倍）       | 额外颜色标记           |
| 并发性能     | **更友好**（局部修改，无全局旋转）    | 红黑树旋转涉及多个节点      |

### 跳表的结构

```c
typedef struct zskiplistNode {
    sds ele;                      // 存储的成员（member）
    double score;                 // 分数（用于排序）
    struct zskiplistNode *backward; // 后退指针（用于从后向前遍历）
    struct zskiplistLevel {
        struct zskiplistNode *forward; // 前进指针
        unsigned long span;            // 跨度（用于计算排名）
    } level[];                         // 层级数组（柔性数组）
} zskiplistNode;

typedef struct zskiplist {
    struct zskiplistNode *header, *tail; // 头尾节点
    unsigned long length;                // 节点数量
    int level;                           // 当前最大层数
} zskiplist;
```

### 层级生成算法（概率性晋升）

新插入的节点有 1/4 的概率晋升到上一层索引（期望最大层数为 log₄n）。

```c
int randomLevel() {
    int level = 1;
    while (random() < 0.25 && level < MAX_LEVEL) {
        level++;
    }
    return level;
}
```

---

## 2.4 dict (字典) - 哈希表的实现

### 结构设计

```c
typedef struct dictht {
    dictEntry **table;      // 哈希表数组
    unsigned long size;     // 哈希表大小（2 的幂次）
    unsigned long sizemask; // size - 1（用于哈希值取模）
    unsigned long used;     // 已使用节点数
} dictht;

typedef struct dict {
    dictType *type;  // 类型特定函数（哈希、比较、析构）
    void *privdata;  // 私有数据
    dictht ht[2];    // 两个哈希表（用于渐进式 rehash）
    long rehashidx;  // rehash 的当前索引（-1 表示未进行 rehash）
} dict;
```

### 渐进式 rehash（核心机制）

**为什么需要渐进式？**
- 如果字典有百万级键值对，一次性 rehash 会导致服务长时间阻塞。

**渐进式 rehash 的步骤：**

1. **为 ht[1] 分配空间**（大小为 ht[0].used * 2 的第一个 2ⁿ）。
2. **将 rehashidx 设置为 0**，表示 rehash 开始。
3. **在每次增删改查操作时**：
   - 顺带将 ht[0] 在 `rehashidx` 索引上的所有键值对迁移到 ht[1]。
   - `rehashidx++`。
4. **rehash 完成后**：
   - 释放 ht[0]，将 ht[1] 设置为 ht[0]，重置 ht[1] 为空表。
   - `rehashidx = -1`。

**在 rehash 期间的操作策略：**
- **查询：** 先查 ht[0]，未找到再查 ht[1]。
- **插入：** 直接插入 ht[1]（确保 ht[0] 只减不增）。
- **删除：** 同时在 ht[0] 和 ht[1] 中查找并删除。

---

## 2.5 intset (整数集合) - 极致节省内存

### 设计目标

当 Set 中全是整数且数量不多时，使用 intset 替代 dict，节省内存。

### 结构

```c
typedef struct intset {
    uint32_t encoding; // 编码类型：INTSET_ENC_INT16 / INT32 / INT64
    uint32_t length;   // 元素数量
    int8_t contents[]; // 实际存储数组（柔性数组）
} intset;
```

### 编码升级机制

**场景：** 向 int16 编码的 intset 插入一个 int32 的值。

**升级步骤：**
1. 根据新元素类型，扩展底层数组。
2. 将现有元素转换为新类型。
3. 插入新元素。

**注意：** intset 不支持降级（即使删除大整数，编码也不会回退）。

---

## 2.6 quicklist - List 的混合实现

### 为什么引入 quicklist？

- **ziplist：** 内存紧凑，但连锁更新影响性能。
- **linkedlist：** 插入删除快，但每个节点都有 prev/next 指针（内存浪费）。

**quicklist = linkedlist + ziplist：**
- 用双向链表连接多个 ziplist 节点。
- 每个 ziplist 节点存储一定数量的元素。

### 结构

```c
typedef struct quicklistNode {
    struct quicklistNode *prev;
    struct quicklistNode *next;
    unsigned char *zl;        // 指向 ziplist
    unsigned int sz;          // ziplist 的字节数
    unsigned int count : 16;  // ziplist 中的元素数量
    // ... 其他字段
} quicklistNode;

typedef struct quicklist {
    quicklistNode *head;
    quicklistNode *tail;
    unsigned long count;      // 总元素数量
    unsigned long len;        // quicklistNode 的数量
    // ... 其他字段
} quicklist;
```

### 优势

- **平衡内存与性能**：既不像纯 ziplist 那样容易连锁更新，也不像纯链表那样浪费内存。
- **配置项 `list-max-ziplist-size`**：控制每个 ziplist 节点的最大元素数。

---

# 三、数据类型与编码转换规则

## 3.1 String 的三种编码

| **编码**    | **条件**                      | **示例**                          |
| --------- | --------------------------- | ------------------------------- |
| `int`     | 值是整数，且在 long 范围内            | `SET counter 100`               |
| `embstr`  | 字符串长度 <= 44 字节（Redis 3.2+） | `SET name "Alice"`              |
| `raw`     | 字符串长度 > 44 字节               | `SET desc "very long text..."` |

**embstr vs raw：**
- **embstr：** redisObject 和 SDS 在一块连续内存中（一次内存分配）。
- **raw：** redisObject 和 SDS 分开存储（两次内存分配）。

---

## 3.2 Hash 的编码转换

| **编码**        | **条件**                                           |
| ------------- | ------------------------------------------------ |
| `ziplist`     | 1. 所有键值对的键和值长度 < 64 字节 <br> 2. 键值对数量 < 512     |
| `hashtable`   | 超过上述任一条件                                         |

**配置项：**
```
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
```

---

## 3.3 List 的编码

| **版本**         | **编码**                      |
| -------------- | --------------------------- |
| Redis < 3.2    | `ziplist` 或 `linkedlist`    |
| Redis >= 3.2   | **统一使用 `quicklist`**       |

---

## 3.4 Set 的编码转换

| **编码**        | **条件**                              |
| ------------- | ----------------------------------- |
| `intset`      | 1. 所有元素都是整数 <br> 2. 元素数量 <= 512   |
| `hashtable`   | 超过上述任一条件                            |

**配置项：**
```
set-max-intset-entries 512
```

---

## 3.5 ZSet 的编码转换

| **编码**                    | **条件**                                           |
| ------------------------- | ------------------------------------------------ |
| `ziplist`                 | 1. 所有元素的 member 长度 < 64 字节 <br> 2. 元素数量 < 128  |
| `skiplist` + `hashtable`  | 超过上述任一条件                                         |

**为什么 ZSet 同时使用 skiplist 和 dict？**
- **skiplist：** 支持按 score 范围查询（`ZRANGE`）。
- **dict：** 支持 O(1) 查找 member（`ZSCORE`）。

**配置项：**
```
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
```

---

# 四、特殊数据类型原理

## 4.1 Bitmap (位图)

**本质：** 基于 String 类型的 bit 操作。

**核心命令：**
```bash
SETBIT key offset value   # 设置指定位
GETBIT key offset         # 获取指定位
BITCOUNT key              # 统计为 1 的位数
BITOP operation destkey key1 key2  # 位运算（AND/OR/XOR/NOT）
```

**应用场景：**
- **签到统计：** 用户 ID 为 offset，签到为 1。
- **布隆过滤器：** 判断元素是否可能存在。

---

## 4.2 HyperLogLog

**本质：** 基于概率算法的基数计数（去重计数）。

**优势：** 只需 12KB 内存，误差率约 0.81%，适合大数据场景。

**核心命令：**
```bash
PFADD key element1 element2  # 添加元素
PFCOUNT key                 # 统计基数
PFMERGE destkey key1 key2   # 合并多个 HyperLogLog
```

**应用场景：** UV 统计、独立 IP 统计。

---

## 4.3 Geospatial (地理位置)

**本质：** 基于 ZSet 实现，将经纬度编码为 52 位的 geohash 作为 score。

**核心命令：**
```bash
GEOADD key longitude latitude member  # 添加地理位置
GEORADIUS key longitude latitude radius [unit]  # 查找范围内的元素
GEODIST key member1 member2 [unit]    # 计算两点距离
```

**应用场景：** 附近的人、打车距离、外卖配送。

---

## 4.4 Stream (流)

**本质：** 专为消息队列设计的数据结构（Redis 5.0+）。

**相比 List 的优势：**
- 支持消费者组（Consumer Group）。
- 支持 ACK 确认机制。
- 支持消息持久化和回溯。

**核心命令：**
```bash
XADD stream * field1 value1  # 添加消息
XREAD STREAMS stream 0       # 读取消息
XGROUP CREATE stream group 0 # 创建消费者组
XREADGROUP GROUP group consumer STREAMS stream >  # 消费组读取
```

---

# 五、编码查看与性能影响

## 查看对象编码

```bash
OBJECT ENCODING key
```

**示例：**
```bash
127.0.0.1:6379> SET name "Alice"
OK
127.0.0.1:6379> OBJECT ENCODING name
"embstr"

127.0.0.1:6379> SADD myset 1 2 3
(integer) 3
127.0.0.1:6379> OBJECT ENCODING myset
"intset"
```

## 编码转换的性能影响

- **ziplist → hashtable：** 一次性转换，O(n) 时间复杂度。
- **intset → hashtable：** 需要重建哈希表，可能短暂阻塞。

**建议：**
- 对于频繁变动的数据，提前设置为高效编码（如直接用 hashtable）。
- 监控 `INFO MEMORY` 中的内存占用，避免过度使用紧凑编码导致频繁转换。

---

# 六、总结与最佳实践

## 核心原则

1. **小数据用紧凑编码**（ziplist/intset）：节省内存。
2. **大数据用高效编码**（hashtable/skiplist）：提升性能。
3. **合理配置转换阈值**：根据业务场景调整 `hash-max-ziplist-entries` 等参数。

## 性能优化建议

- **避免大 key：** 单个 Hash/List/Set/ZSet 元素过多会导致阻塞。
- **使用 Pipeline：** 批量操作减少网络 RTT。
- **监控编码转换：** `SLOWLOG` 记录慢查询，定位编码转换导致的性能问题。

## 面试高频问题

- SDS 相比 C 字符串有哪些优势？
- ziplist 的连锁更新问题是什么？如何避免？
- 为什么 ZSet 同时使用 skiplist 和 dict？
- 渐进式 rehash 如何保证在 rehash 期间的查询正确性？
- quicklist 相比 ziplist 和 linkedlist 的优势是什么？

---

通过深入理解 Redis 的底层数据结构，你将能够更好地进行性能优化和故障排查！🚀
