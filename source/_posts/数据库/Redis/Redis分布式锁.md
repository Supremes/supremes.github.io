---
title: Redis 分布式锁实战
tags:
  - Redis
  - 分布式锁
  - Redisson
categories:
  - 数据库
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
hidden: true
updated: 2026-01-03 15:00
abbrlink: 3abc81c7
date: 2026-01-03 15:00:00
---

分布式锁是分布式系统中的核心组件。本文深入解析基于 Redis 的分布式锁实现，从基础方案到 Redisson 工程实践。

---

# 一、为什么需要分布式锁？

## 1.1 单机锁的局限性

**场景：** 电商秒杀，10 个商品，100 个用户同时抢购。

**单机环境（使用 synchronized）：**
```java
private int stock = 10;

public synchronized void deductStock() {
    if (stock > 0) {
        stock--;
        System.out.println("扣减成功，剩余：" + stock);
    }
}
```

**问题：** 在分布式环境下（多个服务实例），`synchronized` 只能锁住当前 JVM，无法跨服务实例生效。

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│ 实例 A   │  │ 实例 B   │  │ 实例 C   │
│ stock=10│  │ stock=10│  │ stock=10│
└─────────┘  └─────────┘  └─────────┘
     ↓            ↓            ↓
    超卖！（可能扣减到 -5）
```

---

## 1.2 分布式锁的核心特性

| **特性**     | **说明**                   | **实现手段**          |
| ---------- | ------------------------ | ----------------- |
| **互斥性**    | 同一时刻只有一个客户端能持有锁          | SETNX（SET if Not eXists） |
| **超时释放**   | 避免死锁（客户端宕机时锁能自动释放）       | 设置过期时间（EXPIRE）     |
| **可重入性**   | 同一线程可多次获取同一把锁            | 记录持有线程（ThreadLocal） |
| **高可用**    | 锁服务不能是单点（Redis 主从/集群）    | Sentinel/Cluster  |
| **阻塞/非阻塞** | 支持阻塞等待或立即返回              | BLPOP / 自旋重试       |

---

# 二、基础实现：SETNX + EXPIRE

## 2.1 第一版：基础版（存在死锁风险）

```java
public boolean tryLock(String key, String value) {
    // 尝试获取锁
    Boolean success = redisTemplate.opsForValue().setIfAbsent(key, value);
    if (Boolean.TRUE.equals(success)) {
        // 设置过期时间（防止死锁）
        redisTemplate.expire(key, 30, TimeUnit.SECONDS);
        return true;
    }
    return false;
}

public void unlock(String key) {
    redisTemplate.delete(key);
}
```

**问题：**
1. **非原子操作：** `SETNX` 和 `EXPIRE` 不是原子操作。如果设置锁后，进程崩溃，锁永远不会过期（死锁）。
2. **误删他人的锁：** 线程 A 的锁过期后被释放，线程 B 获取了锁，线程 A 执行 `unlock()` 时会删除线程 B 的锁。

---

## 2.2 第二版：原子性 + 防误删

```java
public boolean tryLock(String key, String value, long timeout, TimeUnit unit) {
    // SET key value NX EX timeout（原子操作）
    return Boolean.TRUE.equals(
        redisTemplate.opsForValue()
            .setIfAbsent(key, value, timeout, unit)
    );
}

public void unlock(String key, String value) {
    // Lua 脚本：判断锁的 value 是否匹配，再删除（原子操作）
    String script = 
        "if redis.call('get', KEYS[1]) == ARGV[1] then " +
        "    return redis.call('del', KEYS[1]) " +
        "else " +
        "    return 0 " +
        "end";
    
    redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList(key),
        value
    );
}
```

**改进：**
1. **原子性：** 使用 `SET key value NX EX timeout` 一条命令完成加锁 + 设置过期时间。
2. **防误删：** 通过 Lua 脚本判断 value 是否匹配，只删除自己的锁。

---

## 2.3 第三版：可重入锁

**问题：** 同一线程多次获取锁时会被阻塞。

**解决：** 使用 Hash 结构记录锁的持有次数。

```java
// Hash 结构：lock:{lockName} -> {threadId: count}
public boolean tryLock(String lockName) {
    String key = "lock:" + lockName;
    String threadId = Thread.currentThread().getId() + "";
    
    // Lua 脚本实现可重入
    String script = 
        "if (redis.call('exists', KEYS[1]) == 0) then " +
        "    redis.call('hincrby', KEYS[1], ARGV[1], 1); " +
        "    redis.call('expire', KEYS[1], ARGV[2]); " +
        "    return 1; " +
        "end; " +
        "if (redis.call('hexists', KEYS[1], ARGV[1]) == 1) then " +
        "    redis.call('hincrby', KEYS[1], ARGV[1], 1); " +
        "    redis.call('expire', KEYS[1], ARGV[2]); " +
        "    return 1; " +
        "end; " +
        "return 0;";
    
    Long result = redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList(key),
        threadId, "30"
    );
    
    return result != null && result == 1;
}

public void unlock(String lockName) {
    String key = "lock:" + lockName;
    String threadId = Thread.currentThread().getId() + "";
    
    String script = 
        "if (redis.call('hexists', KEYS[1], ARGV[1]) == 0) then " +
        "    return nil; " +
        "end; " +
        "local count = redis.call('hincrby', KEYS[1], ARGV[1], -1); " +
        "if (count > 0) then " +
        "    return 0; " +
        "else " +
        "    redis.call('del', KEYS[1]); " +
        "    return 1; " +
        "end;";
    
    redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList(key),
        threadId
    );
}
```

---

# 三、Redisson 分布式锁（生产级方案）

## 3.1 Redisson 简介

**Redisson** 是 Redis 官方推荐的 Java 客户端，提供了开箱即用的分布式锁实现。

**核心特性：**
- **可重入锁**（RLock）
- **自动续期**（看门狗机制）
- **红锁**（Redlock）
- **公平锁**、**读写锁**、**信号量**

---

## 3.2 基础用法

### Maven 依赖

```xml
<dependency>
    <groupId>org.redisson</groupId>
    <artifactId>redisson-spring-boot-starter</artifactId>
    <version>3.23.5</version>
</dependency>
```

### 配置 Redisson

```java
@Configuration
public class RedissonConfig {
    @Bean
    public RedissonClient redissonClient() {
        Config config = new Config();
        config.useSingleServer()
            .setAddress("redis://127.0.0.1:6379")
            .setPassword("mypassword")
            .setDatabase(0);
        return Redisson.create(config);
    }
}
```

---

## 3.3 可重入锁（RLock）

```java
@Autowired
private RedissonClient redisson;

public void deductStock() {
    String lockKey = "lock:stock:1001";
    RLock lock = redisson.getLock(lockKey);
    
    try {
        // 尝试加锁（最多等待 10 秒，锁自动过期时间 30 秒）
        boolean success = lock.tryLock(10, 30, TimeUnit.SECONDS);
        if (!success) {
            throw new RuntimeException("获取锁失败");
        }
        
        // 业务逻辑
        int stock = getStock();
        if (stock > 0) {
            deduct();
        }
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    } finally {
        // 释放锁
        if (lock.isHeldByCurrentThread()) {
            lock.unlock();
        }
    }
}
```

---

## 3.4 看门狗机制（自动续期）

### 问题：锁过期时间如何设置？

- **太短：** 业务未执行完，锁就过期了（被其他线程抢占）。
- **太长：** 客户端宕机后，锁长时间占用（影响性能）。

### 看门狗机制

**原理：** Redisson 启动一个后台线程，每隔 10 秒（`lockWatchdogTimeout / 3`）为持有锁的线程续期。

**默认配置：**
```java
config.setLockWatchdogTimeout(30000); // 30 秒
```

**示例：**
```java
RLock lock = redisson.getLock("lock:order");

// 不指定过期时间，自动开启看门狗
lock.lock();

try {
    // 执行耗时业务（如 2 分钟）
    Thread.sleep(120000);
} finally {
    lock.unlock();
}
```

**注意：** 如果手动指定了过期时间，看门狗不会启动。

---

## 3.5 公平锁（FairLock）

**原理：** 先到先得，按请求顺序获取锁（FIFO）。

```java
RLock fairLock = redisson.getFairLock("lock:fair");
fairLock.lock();

try {
    // 业务逻辑
} finally {
    fairLock.unlock();
}
```

---

## 3.6 读写锁（ReadWriteLock）

**场景：** 读多写少（如配置中心）。

```java
RReadWriteLock rwLock = redisson.getReadWriteLock("lock:config");

// 读锁（共享锁）
RLock readLock = rwLock.readLock();
readLock.lock();
try {
    // 读取配置
} finally {
    readLock.unlock();
}

// 写锁（独占锁）
RLock writeLock = rwLock.writeLock();
writeLock.lock();
try {
    // 更新配置
} finally {
    writeLock.unlock();
}
```

---

## 3.7 信号量（Semaphore）

**场景：** 限制并发数（如停车场车位）。

```java
RSemaphore semaphore = redisson.getSemaphore("lock:parking");

// 设置总车位数
semaphore.trySetPermits(10);

// 获取车位（阻塞）
semaphore.acquire();

try {
    // 停车
} finally {
    // 释放车位
    semaphore.release();
}
```

---

# 四、Redlock 算法（多节点锁）

## 4.1 为什么需要 Redlock？

**问题：** 单机 Redis 宕机，锁全部失效。主从复制也存在数据丢失风险（异步复制）。

**Redlock：** Redis 作者提出的多节点分布式锁算法（争议较大）。

---

## 4.2 Redlock 原理

**架构：** 至少 5 个独立的 Redis 主节点（无主从关系）。

**加锁流程：**
```
1. 客户端向 5 个节点依次发送加锁请求（SET key value NX EX timeout）
   │
2. 记录加锁开始时间（startTime）
   │
3. 如果 >= 3 个节点（N/2+1）加锁成功，且总耗时 < 锁过期时间，则加锁成功
   │
4. 否则，向所有节点发送解锁请求（释放资源）
```

---

## 4.3 Redisson 实现

```java
@Bean
public RedissonClient redissonClient1() {
    Config config = new Config();
    config.useSingleServer().setAddress("redis://127.0.0.1:6379");
    return Redisson.create(config);
}

@Bean
public RedissonClient redissonClient2() {
    Config config = new Config();
    config.useSingleServer().setAddress("redis://127.0.0.1:6380");
    return Redisson.create(config);
}

@Bean
public RedissonClient redissonClient3() {
    Config config = new Config();
    config.useSingleServer().setAddress("redis://127.0.0.1:6381");
    return Redisson.create(config);
}

// 使用红锁
public void useRedlock() {
    RLock lock1 = redissonClient1.getLock("lock:redlock");
    RLock lock2 = redissonClient2.getLock("lock:redlock");
    RLock lock3 = redissonClient3.getLock("lock:redlock");
    
    RedissonRedLock redLock = new RedissonRedLock(lock1, lock2, lock3);
    
    try {
        boolean success = redLock.tryLock(10, 30, TimeUnit.SECONDS);
        if (success) {
            // 业务逻辑
        }
    } catch (InterruptedException e) {
        Thread.currentThread().interrupt();
    } finally {
        redLock.unlock();
    }
}
```

---

## 4.4 Redlock 的争议

**Martin Kleppmann（分布式专家）的批评：**
1. **时钟漂移问题：** 依赖系统时钟，NTP 不同步会导致锁失效。
2. **GC 暂停问题：** 客户端 GC 暂停可能导致锁过期。
3. **网络分区问题：** 少数派节点可能依然持有锁。

**Redis 作者（antirez）的回应：**
- Redlock 适用于对一致性要求不高的场景（如限流、防重复提交）。
- 强一致性场景应使用 Zookeeper 或 etcd。

---

# 五、分布式锁的常见问题

## 5.1 锁超时问题

**场景：** 业务执行时间 > 锁过期时间，锁被自动释放。

**解决方案：**
1. **看门狗机制**（Redisson 自带）。
2. **设置合理的超时时间**（根据业务平均耗时 + 缓冲）。

---

## 5.2 锁重入问题

**场景：** 同一线程多次获取锁（如递归调用）。

**解决方案：** 使用 Redisson 的 `RLock`（支持重入）。

---

## 5.3 死锁问题

**场景：** 客户端宕机，锁永远不释放。

**解决方案：** 设置过期时间（`EX` 参数）。

---

## 5.4 主从复制导致的锁丢失

**场景：**
```
1. 客户端 A 向主节点加锁成功
2. 主节点宕机（数据未同步到从节点）
3. 从节点晋升为主节点
4. 客户端 B 向新主节点加锁成功（重复加锁）
```

**解决方案：**
- 使用 **Redlock**（多节点独立加锁）。
- 使用 **Zookeeper**（强一致性）。

---

# 六、分布式锁对比

| **方案**              | **优点**                   | **缺点**                | **推荐场景**      |
| ------------------- | ------------------------ | --------------------- | ------------- |
| **Redis（Redisson）** | 性能高、实现简单                 | 非强一致性（主从复制可能丢失锁）      | 高并发、对一致性要求不高  |
| **Zookeeper**       | 强一致性（CP）、临时节点自动删除        | 性能较低、运维复杂             | 对一致性要求高（如选举）  |
| **etcd**            | 强一致性（Raft）、支持租约（TTL）      | 学习成本高                 | 云原生场景（K8s）    |
| **数据库锁**            | 实现简单（SELECT FOR UPDATE） | 性能差、死锁风险高             | 低并发、无 Redis 环境 |

---

# 七、最佳实践

1. **使用 Redisson**：避免重复造轮子，功能完善且经过生产验证。
2. **设置合理的超时时间**：过期时间 = 业务平均耗时 × 2。
3. **开启看门狗**：不手动指定过期时间，让 Redisson 自动续期。
4. **锁的粒度要小**：避免锁住整个业务流程，只锁住竞态资源。
5. **监控锁的持有时间**：通过日志或 APM 工具监控，发现异常。
6. **避免在锁内执行 RPC 调用**：减少锁持有时间。
7. **强一致性场景用 Zookeeper**：金融、订单等关键业务。

---

# 八、面试高频问题

1. **Redis 分布式锁的基础实现？**
   - `SET key value NX EX timeout` + Lua 脚本释放锁。

2. **如何防止锁被误删？**
   - 在锁的 value 中存储唯一标识（如 UUID），释放时判断是否匹配。

3. **Redisson 的看门狗机制是什么？**
   - 后台线程每隔 10 秒为持有锁的线程续期，避免锁过期。

4. **Redlock 算法的原理？**
   - 向多个独立 Redis 节点加锁，超过半数成功则加锁成功。

5. **Redis 分布式锁的缺点？**
   - 主从复制异步，可能导致锁丢失；非强一致性。

6. **Redis 分布式锁 vs Zookeeper 分布式锁？**
   - Redis 性能高但非强一致；Zookeeper 强一致但性能较低。

7. **如何保证锁的可重入性？**
   - 使用 Hash 结构记录持有线程和重入次数。

---

通过合理的分布式锁设计，可以保证分布式系统的数据一致性与业务正确性！🚀
