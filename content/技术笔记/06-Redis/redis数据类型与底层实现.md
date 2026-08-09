---
title: Redis 数据类型与底层实现
date: 2026-08-09
tags:
  - Redis
  - 数据结构
---
这篇只保留面试最该会说的底层逻辑：数据类型、编码切换、核心结构，以及 ziplist / listpack 的版本差异。

# 一、先记版本差异

## 1.1 面试不要把 ziplist 当“现状”

| 类型 | 早期资料常见说法 | 现在更稳妥的说法 |
| --- | --- | --- |
| List | `ziplist` / `linkedlist` | Redis 3.2+ 主线是 `quicklist`；新版本 quicklist 节点内部更偏向 `listpack` |
| Hash | 小对象 `ziplist`，大对象 `hashtable` | 紧凑编码从 `ziplist` 逐步演进为 `listpack`，大对象仍是 `hashtable` |
| ZSet | 小对象 `ziplist`，大对象 `skiplist + dict` | 小对象回答成“早期 ziplist，新版 listpack”更稳妥；大对象仍是 `skiplist + dict` |
| Stream | - | Redis 5.0+，底层是 `radix tree + listpack` |

> 安全答法：**早期 ziplist，新版本 listpack；List 主线长期是 quicklist。**

# 二、五大核心数据类型对应什么底层结构

| 类型 | 典型场景 | 常见底层结构 |
| --- | --- | --- |
| String | 缓存、计数器、分布式锁 | `int` / `embstr` / `raw` |
| Hash | 用户对象、配置对象 | 紧凑编码（早期 `ziplist`，新版本 `listpack`）/ `hashtable` |
| List | 消息队列、最新列表 | `quicklist` |
| Set | 去重、标签 | `intset` / `hashtable` |
| ZSet | 排行榜、延时任务 | 紧凑编码（早期 `ziplist`，新版本 `listpack`）/ `skiplist + dict` |

# 三、最重要的底层结构

## 3.1 SDS：为什么 String 不直接用 C 字符串

SDS（Simple Dynamic String）比原生 C 字符串更适合服务端场景：

- **O(1) 取长度**
- **二进制安全**
- **减少内存重分配**
- **降低缓冲区溢出风险**

> 面试关键词：`len`、`free`、空间预分配、惰性释放。

## 3.2 dict：为什么 Hash / 全局键空间查得快

Redis 的哈希表核心是 `dict`：

- 链地址法解决冲突
- 扩容 / 缩容时采用**渐进式 rehash**
- rehash 期间查询可能同时查旧表和新表

这让 Redis 能在不长时间阻塞主线程的前提下完成扩缩容。

## 3.3 skiplist：为什么 ZSet 不用红黑树

ZSet 大对象常见组合是：

- `skiplist`：负责按 score 排序、做范围查询
- `dict`：负责按 member 快速查找

跳表相对红黑树的口述优势：

- 实现更简单
- 范围查询自然
- 并发修改时局部性更好

## 3.4 intset：为什么小整数集合省内存

当 Set 中：

- 元素都是整数
- 数量不大

Redis 会用 `intset`，比哈希表更省内存。  
一旦出现非整数或规模变大，就会转成 `hashtable`。

## 3.5 quicklist / listpack：List 为什么不再用纯链表

纯链表的问题是指针太多、内存碎片明显；纯紧凑结构又容易连锁更新。  
所以 Redis 选择了折中路线：

- 外层用 `quicklist`
- 单个节点内部用紧凑存储（早期更常见 `ziplist`，新版本更偏 `listpack`）

> 面试一句话：**quicklist 是“链表级别的插入删除能力 + 紧凑编码的省内存能力”的折中。**

# 四、编码切换怎么讲

## 4.1 String

| 编码 | 适用情况 |
| --- | --- |
| `int` | 值本身是整数 |
| `embstr` | 短字符串 |
| `raw` | 较长字符串 |

## 4.2 Hash / ZSet / List 的统一答法

- **小对象、短字段、元素少**：优先紧凑编码
- **字段多、元素多、更新频繁**：切到哈希表 / 跳表等更适合性能的结构

别死背某个固定阈值；阈值会随着版本和配置项命名演进。

## 4.3 什么时候切换会抖

编码转换通常是一次性操作，数据量大时可能出现明显耗时。  
所以大对象、高频变更对象需要重点关注。

# 五、如何观察编码

```bash
OBJECT ENCODING key
```

这个命令常用来验证：

- 某个 Set 还是不是 `intset`
- 某个 String 是 `embstr` 还是 `raw`
- 某个对象是否已经从紧凑编码切到了更重的结构

# 六、面试高频问法

## 6.1 为什么 Redis 快

- 内存访问快
- IO 多路复用
- 单线程执行命令，少锁竞争
- 数据结构针对业务场景做了优化

## 6.2 为什么 ZSet 同时用跳表和字典

- 跳表负责排序和范围查询
- 字典负责按 member O(1) 查找

## 6.3 渐进式 rehash 解决了什么

解决的是**大哈希表扩缩容时一次性搬迁导致的长时间阻塞**。

## 6.4 ziplist / listpack 怎么回答最稳

> 早期资料大量使用 ziplist；现在更建议回答为“紧凑编码从 ziplist 逐步演进到 listpack”，不要把 ziplist 说成当前通用现状。
