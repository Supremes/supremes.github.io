---
title: Redis 缓存策略与一致性方案
date: 2026-01-03
tags:
  - Redis
  - 缓存
  - 一致性
---
Redis 作为缓存层，需要解决缓存穿透、击穿、雪崩三大经典问题，同时保证缓存与数据库的数据一致性。本文深入解析各种缓存策略与工程实践。

---

# 一、缓存失效三连问

## 1.1 缓存穿透 (Cache Penetration)

### 定义

**查询一个根本不存在的数据**，缓存和数据库都没有，导致每次请求都打到数据库。

### 场景

- **恶意攻击：** 用随机 ID（如 `id=-1` 或超长字符串）发起大量请求。
- **业务漏洞：** 前端未校验参数，直接穿透到后端。

### 危害

- 数据库承受大量无效查询，可能崩溃。
- 缓存层形同虚设。

---

### 解决方案

#### 方案 1：缓存空对象

**原理：** 即使数据库查不到，也将空结果（null）写入缓存，设置较短的过期时间。

**代码示例（Java + RedisTemplate）：**
```java
public User getUserById(Long id) {
    String cacheKey = "user:" + id;
    
    // 1. 查询缓存
    User user = redisTemplate.opsForValue().get(cacheKey);
    if (user != null) {
        return user; // 缓存命中
    }
    
    // 2. 查询数据库
    user = userMapper.selectById(id);
    
    // 3. 写入缓存（即使为 null）
    if (user != null) {
        redisTemplate.opsForValue().set(cacheKey, user, 30, TimeUnit.MINUTES);
    } else {
        // 缓存空对象，5 分钟过期
        redisTemplate.opsForValue().set(cacheKey, new User(), 5, TimeUnit.MINUTES);
    }
    
    return user;
}
```

**优点：**
- 实现简单。

**缺点：**
- 占用缓存空间（大量不存在的 key）。
- 需设置合理的过期时间（太长浪费内存，太短可能仍打到 DB）。

---

#### 方案 2：布隆过滤器（推荐）

**原理：** 在请求到达缓存前，先用布隆过滤器判断数据是否可能存在。

**布隆过滤器特性：**
- **判断存在：** 可能误判（实际不存在但判断存在）。
- **判断不存在：** 100% 准确（一定不存在）。

**架构流程：**
```
客户端请求
   ↓
布隆过滤器（判断 key 是否存在）
   ├─ 不存在 → 直接返回 null（拦截恶意请求）
   └─ 可能存在 → 查询缓存 → 查询数据库
```

**代码示例（Java + Redisson）：**
```java
@Autowired
private RedissonClient redisson;

// 初始化布隆过滤器
@PostConstruct
public void initBloomFilter() {
    RBloomFilter<Long> bloomFilter = redisson.getBloomFilter("user:bloom");
    // 预期元素数量 100 万，误判率 0.01
    bloomFilter.tryInit(1000000L, 0.01);
    
    // 将所有用户 ID 加入布隆过滤器
    List<Long> userIds = userMapper.selectAllIds();
    userIds.forEach(bloomFilter::add);
}

public User getUserById(Long id) {
    RBloomFilter<Long> bloomFilter = redisson.getBloomFilter("user:bloom");
    
    // 1. 布隆过滤器判断
    if (!bloomFilter.contains(id)) {
        return null; // 一定不存在，直接返回
    }
    
    // 2. 查询缓存
    String cacheKey = "user:" + id;
    User user = redisTemplate.opsForValue().get(cacheKey);
    if (user != null) {
        return user;
    }
    
    // 3. 查询数据库
    user = userMapper.selectById(id);
    if (user != null) {
        redisTemplate.opsForValue().set(cacheKey, user, 30, TimeUnit.MINUTES);
    }
    
    return user;
}
```

**优点：**
- 高效拦截恶意请求（内存占用极小，100 万元素仅需 1.2MB）。

**缺点：**
- 需预热（将所有有效 key 加入过滤器）。
- 新增数据时需同步更新布隆过滤器。

---

#### 方案 3：接口限流与参数校验

**原理：** 在网关层拦截恶意请求。

**措施：**
- **参数校验：** 前端 + 后端双重校验（如 ID 范围、格式）。
- **限流：** 使用令牌桶或漏桶算法（如 Guava RateLimiter、Sentinel）。
- **黑名单：** 将恶意 IP 加入黑名单。

---

## 1.2 缓存击穿 (Cache Breakdown)

### 定义

**一个热点 key 突然过期**，瞬间大量并发请求同时打到数据库。

### 场景

- 微博热搜突发新闻。
- 秒杀活动的商品详情页。

### 危害

- 数据库瞬时压力飙升。
- 可能引发连锁反应（数据库慢查询 → 连接池耗尽）。

---

### 解决方案

#### 方案 1：互斥锁（Mutex Lock）

**原理：** 当缓存失效时，只允许一个线程去查数据库并回写缓存，其他线程等待或重试。

**代码示例（Java + RedisTemplate）：**
```java
public User getUserById(Long id) {
    String cacheKey = "user:" + id;
    String lockKey = "lock:user:" + id;
    
    // 1. 查询缓存
    User user = redisTemplate.opsForValue().get(cacheKey);
    if (user != null) {
        return user;
    }
    
    // 2. 尝试获取分布式锁（SETNX）
    Boolean locked = redisTemplate.opsForValue()
        .setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);
    
    if (Boolean.TRUE.equals(locked)) {
        try {
            // 双重检查：再次查询缓存（避免其他线程已回写）
            user = redisTemplate.opsForValue().get(cacheKey);
            if (user != null) {
                return user;
            }
            
            // 3. 查询数据库
            user = userMapper.selectById(id);
            
            // 4. 回写缓存
            if (user != null) {
                redisTemplate.opsForValue().set(cacheKey, user, 30, TimeUnit.MINUTES);
            }
            
            return user;
        } finally {
            // 5. 释放锁
            redisTemplate.delete(lockKey);
        }
    } else {
        // 未获取到锁，等待 50ms 后重试
        try {
            Thread.sleep(50);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        return getUserById(id); // 递归重试
    }
}
```

**优点：**
- 保证只有一个线程查询数据库。

**缺点：**
- 其他线程需等待或重试（体验稍差）。
- 需保证锁的超时时间 > 数据库查询时间。

---

#### 方案 2：逻辑过期（推荐）

**原理：** 热点数据**永不过期**，但在 value 内部记录逻辑过期时间。后台异步线程检测并更新数据。

**数据结构：**
```java
@Data
public class CacheData<T> {
    private T data;
    private LocalDateTime expireTime; // 逻辑过期时间
}
```

**代码示例：**
```java
private static final ExecutorService CACHE_REBUILD_EXECUTOR = 
    Executors.newFixedThreadPool(10);

public User getUserById(Long id) {
    String cacheKey = "user:" + id;
    
    // 1. 查询缓存
    CacheData<User> cacheData = redisTemplate.opsForValue().get(cacheKey);
    
    // 2. 缓存不存在（首次访问）
    if (cacheData == null) {
        return rebuildCache(id);
    }
    
    // 3. 判断逻辑过期
    if (LocalDateTime.now().isAfter(cacheData.getExpireTime())) {
        // 逻辑过期，异步重建缓存
        String lockKey = "lock:user:" + id;
        Boolean locked = redisTemplate.opsForValue()
            .setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);
        
        if (Boolean.TRUE.equals(locked)) {
            CACHE_REBUILD_EXECUTOR.submit(() -> {
                try {
                    rebuildCache(id);
                } finally {
                    redisTemplate.delete(lockKey);
                }
            });
        }
    }
    
    // 4. 返回旧数据（用户无感知）
    return cacheData.getData();
}

private User rebuildCache(Long id) {
    User user = userMapper.selectById(id);
    if (user != null) {
        CacheData<User> cacheData = new CacheData<>();
        cacheData.setData(user);
        cacheData.setExpireTime(LocalDateTime.now().plusMinutes(30));
        redisTemplate.opsForValue().set("user:" + id, cacheData);
    }
    return user;
}
```

**优点：**
- 用户无感知（始终返回数据，即使是旧数据）。
- 无阻塞（异步更新）。

**缺点：**
- 可能短暂返回过期数据（秒级不一致）。

---

## 1.3 缓存雪崩 (Cache Avalanche)

### 定义

**大量 key 同时过期** 或 **缓存服务宕机**，导致请求全部打到数据库。

### 场景

- 系统重启后批量加载缓存，设置了相同的过期时间。
- Redis 服务器宕机。

### 危害

- 数据库瞬时流量激增，可能引发连锁崩溃。

---

### 解决方案

#### 方案 1：随机过期时间

**原理：** 在设置过期时间时，加上一个随机值（如 1-5 分钟）。

**代码示例：**
```java
// 基础过期时间 30 分钟 + 随机 0-300 秒
int expireTime = 30 * 60 + ThreadLocalRandom.current().nextInt(0, 300);
redisTemplate.opsForValue().set(cacheKey, user, expireTime, TimeUnit.SECONDS);
```

---

#### 方案 2：高可用架构

**措施：**
- **主从 + 哨兵：** 自动故障转移。
- **Redis Cluster：** 数据分片，单节点宕机影响有限。
- **多级缓存：** 本地缓存（Caffeine）+ Redis。

---

#### 方案 3：限流降级

**原理：** 当流量过大时，直接返回默认值或提示"系统繁忙"。

**代码示例（Sentinel）：**
```java
@SentinelResource(value = "getUserById", 
    blockHandler = "handleBlock", 
    fallback = "handleFallback")
public User getUserById(Long id) {
    // 正常业务逻辑
}

// 限流降级处理
public User handleBlock(Long id, BlockException ex) {
    return new User(); // 返回默认对象
}
```

---

## 1.4 三者对比总结

| **问题**   | **本质**              | **核心对策**               |
| -------- | ------------------- | ---------------------- |
| **缓存穿透** | **数据根本不存在**（恶意攻击）   | 布隆过滤器、缓存空对象            |
| **缓存击穿** | **热点 key 过期**（点的突破） | 互斥锁、逻辑过期               |
| **缓存雪崩** | **大量 key 同时过期**（面的崩塌） | 随机过期时间、高可用架构、限流降级      |

---

# 二、缓存更新策略

## 2.1 三种经典模式

### Cache Aside（旁路缓存，最常用）

**读流程：**
```
1. 查询缓存
   ├─ 命中 → 返回
   └─ 未命中 → 查数据库 → 写入缓存 → 返回
```

**写流程：**
```
1. 先删除缓存
2. 再更新数据库
```

**为什么先删缓存？**
- **避免数据不一致：** 如果先更新 DB，再删缓存，删缓存失败会导致脏数据。

**代码示例：**
```java
public void updateUser(User user) {
    String cacheKey = "user:" + user.getId();
    
    // 1. 删除缓存
    redisTemplate.delete(cacheKey);
    
    // 2. 更新数据库
    userMapper.updateById(user);
}
```

---

### Read/Write Through（读写穿透）

**原理：** 缓存层自动同步数据库，应用层只与缓存交互。

**适用场景：** 需要缓存中间件支持（如 Guava Cache + CacheLoader）。

---

### Write Behind（异步刷新）

**原理：** 先写缓存，异步批量写数据库。

**优点：** 写性能极高（如游戏排行榜）。

**缺点：** 可能丢失数据（缓存宕机）。

---

## 2.2 缓存一致性问题

### 问题：先删缓存 vs 先更新数据库？

| **策略**        | **流程**          | **问题**                    | **推荐**  |
| ------------- | --------------- | ------------------------- | ------- |
| **先删缓存，再更新 DB** | 1. 删缓存 → 2. 更新 DB | 线程 A 删缓存，线程 B 读到旧数据并写入缓存   | **✅ 推荐** |
| 先更新 DB，再删缓存   | 1. 更新 DB → 2. 删缓存 | 删缓存失败，缓存一直是旧数据（脏数据）       | ❌ 不推荐   |

### 最佳实践：延迟双删

**原理：** 先删缓存 → 更新 DB → 延迟 N 秒 → 再删一次缓存。

**代码示例：**
```java
public void updateUser(User user) {
    String cacheKey = "user:" + user.getId();
    
    // 1. 删除缓存
    redisTemplate.delete(cacheKey);
    
    // 2. 更新数据库
    userMapper.updateById(user);
    
    // 3. 延迟 1 秒后再删一次缓存
    new Thread(() -> {
        try {
            Thread.sleep(1000);
            redisTemplate.delete(cacheKey);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }).start();
}
```

---

## 2.3 强一致性方案：分布式锁 + 版本号

**原理：** 使用分布式锁保证读写操作的原子性。

**代码示例（Redisson）：**
```java
public User getUserById(Long id) {
    String cacheKey = "user:" + id;
    String lockKey = "lock:user:" + id;
    
    RLock lock = redisson.getLock(lockKey);
    lock.lock();
    
    try {
        // 查询缓存
        User user = redisTemplate.opsForValue().get(cacheKey);
        if (user != null) {
            return user;
        }
        
        // 查询数据库
        user = userMapper.selectById(id);
        if (user != null) {
            redisTemplate.opsForValue().set(cacheKey, user, 30, TimeUnit.MINUTES);
        }
        
        return user;
    } finally {
        lock.unlock();
    }
}
```

---

# 三、缓存预热与淘汰

## 3.1 缓存预热

**场景：** 系统启动时，提前将热点数据加载到缓存。

**实现方式：**
1. 启动时查询数据库，批量写入 Redis。
2. 使用定时任务（如每天凌晨）刷新热点数据。

**代码示例：**
```java
@PostConstruct
public void warmUpCache() {
    List<User> hotUsers = userMapper.selectHotUsers();
    hotUsers.forEach(user -> {
        String cacheKey = "user:" + user.getId();
        redisTemplate.opsForValue().set(cacheKey, user, 30, TimeUnit.MINUTES);
    });
}
```

---

## 3.2 内存淘汰策略

**配置：**
```bash
# redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
```

**常用策略：**
| **策略**          | **淘汰范围**        | **推荐场景**       |
| --------------- | --------------- | -------------- |
| **allkeys-lru** | **所有 key**      | **通用场景（推荐）**   |
| volatile-lru    | 设置过期时间的 key     | 部分数据需永久保留      |
| allkeys-random  | 所有 key          | 测试环境           |
| volatile-ttl    | 优先淘汰 TTL 短的 key | Session、验证码等短期数据 |

---

# 四、面试高频问题

1. **缓存穿透、击穿、雪崩的区别？**
   - 穿透：数据不存在（恶意）；击穿：热点 key 过期（点）；雪崩：大量 key 过期（面）。

2. **布隆过滤器的误判率如何权衡？**
   - 误判率越低，占用内存越大。通常设置 0.01（1%）即可。

3. **为什么先删缓存，再更新数据库？**
   - 避免删缓存失败导致的长期脏数据。

4. **如何保证缓存与数据库的强一致性？**
   - 使用分布式锁 + 延迟双删，或放弃缓存（直接查 DB）。

5. **Redis 内存淘汰策略如何选择？**
   - 通用场景推荐 `allkeys-lru`。

6. **缓存击穿的逻辑过期方案为什么优于互斥锁？**
   - 逻辑过期无阻塞，用户体验更好（返回旧数据 vs 等待）。

---

通过合理的缓存策略，可以在高并发场景下保证系统的稳定性与一致性！🚀
