---
title: "Redis 核心数据结构与应用场景"
date: "2026-05-12"
tags: "Redis,数据库,缓存"
summary: "Redis 不只是一个缓存，它是一个强大的内存数据结构服务器。理解它的核心数据结构，才能真正发挥它的威力。"
---

## 五种基础数据结构

### 1. String（字符串）

最简单的类型，但功能丰富：

```bash
# 基本操作
SET user:1:name "张三"
GET user:1:name

# 原子计数
INCR article:1:views
INCRBY user:1:points 10

# 设置过期时间
SET session:abc123 "user_data" EX 3600  # 1小时后过期
```

**应用场景：** 缓存、计数器、分布式锁、Session 存储

### 2. List（列表）

双向链表，支持两端操作：

```bash
# 消息队列
LPUSH queue:tasks "task1"
RPUSH queue:tasks "task2"
RPOP queue:tasks

# 最新列表（如最新动态）
LPUSH timeline:user1 "post:100"
LTRIM timeline:user1 0 49  # 只保留50条
```

**应用场景：** 消息队列、最新列表、时间线

### 3. Hash（哈希）

适合存储对象：

```bash
HSET user:1 name "张三" age 28 email "zhangsan@example.com"
HGET user:1 name
HGETALL user:1
HINCRBY user:1 age 1
```

**应用场景：** 用户信息、商品详情、配置存储

### 4. Set（集合）

无序、不重复：

```bash
# 共同关注
SADD follow:user1 "user2" "user3" "user4"
SADD follow:user2 "user1" "user3" "user5"
SINTER follow:user1 follow:user2  # 共同关注：user3

# 去重
SADD ip:blacklist "1.2.3.4"
SISMEMBER ip:blacklist "1.2.3.4"
```

**应用场景：** 标签、共同好友、去重、抽奖

### 5. Sorted Set（有序集合）

带分数的有序集合，最强大的类型之一：

```bash
# 排行榜
ZADD leaderboard 95 "player1"
ZADD leaderboard 87 "player2"
ZADD leaderboard 99 "player3"
ZREVRANGE leaderboard 0 9 WITHSCORES  # Top 10
ZRANK leaderboard "player1"  # 排名

# 延迟队列
ZADD delay_queue <timestamp> "task_data"
ZRANGEBYSCORE delay_queue 0 <current_time>
```

**应用场景：** 排行榜、延迟队列、范围查询、优先级队列

## 实战场景

### 分布式锁

```bash
# 加锁（原子操作）
SET lock:order:123 "holder_id" NX EX 30

# 释放锁（Lua 脚本保证原子性）
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
end
```

### 限流

```bash
# 滑动窗口限流
MULTI
ZADD rate:api:user1 <timestamp> <unique_id>
ZRANGEBYSCORE rate:api:user1 <timestamp - window> <timestamp>
ZREMRANGEBYSCORE rate:api:user1 0 <timestamp - window>
EXEC
```

## 性能优化

1. **使用 Pipeline** — 批量操作减少网络往返
2. **避免大 Key** — 单个 Key 的 value 不要超过 10KB
3. **合理设置过期时间** — 避免内存泄漏
4. **使用连接池** — 避免频繁建立连接

## 总结

Redis 的价值不仅在于「快」，更在于它提供的**丰富数据结构**。选择正确的数据结构，往往能让复杂的问题变得简单。

> 不要把 Redis 当成简单的 Key-Value 存储。它的数据结构才是真正的武器。
