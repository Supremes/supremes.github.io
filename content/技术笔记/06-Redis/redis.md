---
title: Redis 面试导航
date: 2026-08-09
tags:
  - Redis
  - 缓存
  - 面试
---
Redis 复习最怕“每篇都像总纲”。这里把入口收敛成一条主线：先缓存与锁，再高可用与底层，最后看专项资料。

# 阅读顺序

## P0（先看）

1. [Redis 缓存策略与一致性方案](./redis缓存策略.md)
   - 穿透 / 击穿 / 雪崩、双删、逻辑过期、缓存一致性
2. [Redis 分布式锁实战](./redis分布式锁.md)
   - `SET NX EX` + Lua、Redisson、主从失锁、Redlock 争议、Zookeeper 对比
3. [Redis 集群方案](./redis集群方案.md)
   - 主从、哨兵、Cluster、槽位、故障转移
4. [Redis 数据类型与底层实现](./redis数据类型与底层实现.md)
   - String / Hash / List / Set / ZSet、SDS、dict、skiplist、版本差异

## P1（补强）

5. [Redis 持久化机制](./redis持久化机制.md)
   - RDB、AOF、混合持久化、fork / COW
6. [Redis 性能优化与排障](./redis-性能优化.md)
   - bigkey / hotkey、慢命令、内存、持久化抖动、排障主线
7. [Redis 应用场景实战](./redis应用场景实战.md)
   - 排行榜、限流、分布式 ID、Session、GEO、延时任务

## 参考资料

8. [Redis 速记补充（参考）](./redis-核心原理笔记.md)
   - 渐进式 rehash、Hash Tag、事务边界、bigkey / hotkey 口述补充

# 口述 Checklist

- 能说清 Redis 为什么快：内存、IO 多路复用、单线程执行命令避免锁竞争、数据结构高效。
- 能区分缓存穿透 / 击穿 / 雪崩，并给出不同处理方案。
- 能说清分布式锁的最小正确实现：`SET key value NX EX` + Lua 校验 value 再删。
- 能解释主从、哨兵、Cluster 的适用边界。
- 能说明“早期 ziplist，新版本 listpack / quicklist”的版本差异，别把 ziplist 当成通用现状。
- 能解释 bigkey / hotkey 为什么危险，以及怎么发现和处理。
