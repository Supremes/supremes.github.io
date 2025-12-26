---
title: Redis-性能优化笔记
tags:
  - Redis
categories:
  - 数据库
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: true
updated: 2025-12-26 22:45
abbrlink: 7a7d46e0
date: 2025-12-07 22:39:19
sticky:
---
## 缓存失效

**缓存穿透**、**缓存击穿**和**缓存雪崩**是三个非常经典且容易混淆的高频面试题和生产事故场景。

它们的核心共同点是：**缓存失效或未命中，导致大量请求直接打到了数据库（DB），从而导致数据库压力骤增甚至宕机。**

为了帮助你区分，我将引入**缓存击穿**这个概念一起讲解，因为这三者通常是作为一套知识体系出现的。

---

### 1. 缓存穿透 (Cache Penetration)

核心定义： 查询一个根本不存在的数据。

因为缓存和数据库中都没有这个数据，所以缓存永远不会命中，请求每次都会穿过缓存直接打到数据库。

- **场景：** 恶意攻击（比如用 ID = -1 或超长随机字符串发起请求）。
- **比喻：** 就像有人去便利店买“原子弹”，货架（缓存）上没有，仓库（数据库）里也没有，但他一直问，店员就得一直跑仓库确认，累死店员。
- **后果：** 数据库短时间内承受大量无效请求，可能崩掉。

**解决方案：**

- **布隆过滤器 (Bloom Filter)：** 在请求到达缓存前，先用布隆过滤器判断数据是否存在。如果不包含，直接拦截。
- **缓存空对象：** 即使数据库查不到，也把这个空结果（null）写入缓存，并设置一个较短的过期时间。

---

### 2. 缓存击穿 (Cache Breakdown)

核心定义： 一个热点 Key 突然过期。

针对某一个被高并发访问的 Key（热点），在它失效的瞬间，海量请求同时到达。因为缓存刚过期，这些请求会同时“击穿”缓存，全部打到数据库上。

- **场景：** 微博热搜突发新闻、秒杀活动的商品详情页。
- **比喻：** 某款爆款手机（热点 Key）在货架上刚卖完（过期），还没来得及补货，几千个顾客瞬间涌入仓库去抢。
- **后果：** 数据库瞬间负载飙高，但通常只针对这一个数据点。

**解决方案：**

- **互斥锁 (Mutex Lock)：** 当缓存失效时，只允许一个线程去查数据库并回写缓存，其他线程等待。
- **逻辑过期：** 设置热点数据“永不过期”，但在 Value 内部包含一个逻辑过期时间。后台异步线程发现快过期时去更新它。

---

### 3. 缓存雪崩 (Cache Avalanche)

核心定义： 大量 Key 同时过期 或者 缓存服务器宕机。

不同于击穿（针对单个 Key），雪崩是指大面积的缓存失效。

- **场景：** 系统重启后加载缓存，设置了相同的过期时间；或者 Redis 挂了。
- **比喻：**
    
    1. **过期：** 雪崩就像便利店里所有商品在同一时间全部过期下架，所有顾客都只能去仓库拿货。
    2. **宕机：** 便利店塌了，顾客直接冲进了仓库。
        
- **后果：** 数据库流量激增，极其容易造成数据库宕机，甚至导致整个系统级联崩溃。

**解决方案：**

- **随机过期时间：** 在设置过期时间时，加上一个随机值（比如 1-5 分钟），避免集体失效。
- **高可用架构：** 使用 Redis Sentinel 或 Cluster 保证缓存服务不挂。
- **限流降级：** 当流量过大时，直接返回默认值或提示“系统繁忙”，保护数据库。

---

### 总结与区分表

为了让你一目了然，请看下表对比：

|**特性**|**缓存穿透 (Penetration)**|**缓存击穿 (Breakdown)**|**缓存雪崩 (Avalanche)**|
|---|---|---|---|
|**数据状态**|**数据根本不存在** (DB无，缓存无)|**数据存在**，但**热点Key**正好过期|**数据存在**，但**大量Key**同时过期或服务挂掉|
|**侧重点**|**“无中生有”**的恶意攻击|**“点”**的突破 (单点高并发)|**“面”**的崩塌 (大面积失效)|
|**核心对策**|布隆过滤器、缓存空值|互斥锁、逻辑过期|随机过期时间、高可用集群|

好的，为了让你更直观地理解，我将以企业级开发中最通用的 **Java (Spring Boot + RedisTemplate)** 为例，分别展示如何解决**缓存击穿**和**缓存穿透**。

---
### **Java (RedisTemplate)** 代码演示
#### 1. 解决缓存击穿 (Cache Breakdown)

场景： 热点 Key 失效，并发冲向数据库。

核心代码逻辑： 使用分布式锁（setnx），保证同一时刻只有一个线程去查 DB，其他线程等待或重试。

```Java
import org.springframework.data.redis.core.StringRedisTemplate;
import java.util.concurrent.TimeUnit;

public class CacheService {

    private StringRedisTemplate redisTemplate;

    // 模拟从数据库获取数据
    public String getData(String key) {
        // 1. 先查缓存
        String value = redisTemplate.opsForValue().get(key);
        if (value != null) {
            return value;
        }

        // 2. 缓存未命中，开始解决“击穿”问题
        // 定义锁的 key
        String lockKey = "lock:" + key;
        
        try {
            // 3. 尝试获取锁 (SETNX: Set If Not Exists)
            // 设置 10 秒过期是为了防止死锁（万一应用挂了，锁还能自动释放）
            Boolean isLocked = redisTemplate.opsForValue().setIfAbsent(lockKey, "1", 10, TimeUnit.SECONDS);

            if (Boolean.TRUE.equals(isLocked)) {
                // 4. 获取锁成功，去查数据库
                // 【双重检查 Double Check】：再查一次缓存，因为可能在上锁期间别人已经查完写回去了
                value = redisTemplate.opsForValue().get(key);
                if (value != null) {
                    return value;
                }

                // 真正查 DB
                value = getFromDB(key); 

                // 5. 写回缓存 (假设热点数据有效期 1 小时)
                redisTemplate.opsForValue().set(key, value, 1, TimeUnit.HOURS);
                return value;
            } else {
                // 6. 获取锁失败（说明有别人在查了）
                // 休眠一会，然后递归重试，或者返回空
                Thread.sleep(50);
                return getData(key); 
            }
        } catch (Exception e) {
            e.printStackTrace();
            return null;
        } finally {
            // 7. 释放锁
            // 注意：生产环境需要判断锁的值是否属于当前线程，推荐使用 Redisson
            redisTemplate.delete(lockKey);
        }
    }

    private String getFromDB(String key) {
        // 模拟 DB 查询
        return "data_from_db";
    }
}
```

> **注意：** 实际生产中，手动写 `setIfAbsent` 容易出现误删锁的问题（比如业务执行时间超过了锁的过期时间）。推荐直接使用 **Redisson** 框架，它封装了看门狗（Watch Dog）机制，能自动续期锁。

---

#### 2. 解决缓存穿透 (Cache Penetration)

场景： 查询 ID = -1，数据库和缓存都没有。

方案一：缓存空对象 (最简单)

```Java
public String getDataAvoidPenetration(String key) {
    // 1. 查缓存
    String value = redisTemplate.opsForValue().get(key);
    
    // 2. 如果缓存里有东西
    if (value != null) {
        // 如果缓存的是我们约定的"空占位符"（比如空字符串或特定标识），直接返回 null 或错误提示
        if ("".equals(value)) {
            return null; // 拦截住了
        }
        return value;
    }

    // 3. 查数据库
    value = getFromDB(key);

    if (value == null) {
        // 4. 关键点：DB 也没查到，往缓存里写一个空值（或特定字符串）
        // 必须设置一个较短的过期时间（例如 5 分钟），防止该 Key 长期占坑
        redisTemplate.opsForValue().set(key, "", 5, TimeUnit.MINUTES);
        return null;
    }

    // 5. DB 查到了，正常写缓存
    redisTemplate.opsForValue().set(key, value, 1, TimeUnit.HOURS);
    return value;
}
```

方案二：布隆过滤器 (Bloom Filter)

适用于数据量巨大且不想浪费缓存空间存空值的场景。通常配合 Redisson 使用。

```Java
import org.redisson.api.RBloomFilter;
import org.redisson.api.RedissonClient;

public class BloomFilterService {
    
    private RedissonClient redisson;

    // 初始化布隆过滤器 (通常在系统启动时预热)
    public void initBloomFilter() {
        RBloomFilter<String> bloomFilter = redisson.getBloomFilter("idList");
        // 初始化：预计插入 100万 数据，允许 0.03 的误判率
        bloomFilter.tryInit(1000000L, 0.03);
        
        // 把所有存在的 ID 加进去
        // bloomFilter.add("1001");
        // bloomFilter.add("1002");
    }

    public String getData(String key) {
        RBloomFilter<String> bloomFilter = redisson.getBloomFilter("idList");

        // 1. 先问布隆过滤器：这个 key 存在吗？
        // 如果布隆过滤器说 "不存在"，那肯定不存在，直接返回，别查 DB 了
        if (!bloomFilter.contains(key)) {
            return null; 
        }

        // 2. 如果布隆过滤器说 "可能存在" (有误判率)，再走正常的 缓存 -> DB 流程
        return searchCacheAndDB(key);
    }
}
```

---

#### 总结建议

1. **对于击穿（热点 Key）：** 只要并发高，**分布式锁 (Lock)** 是必须的。如果不想写复杂的锁逻辑，可以用 `Spring Cache` 的 `@Cacheable(sync=true)` 注解，它底层帮你做了一个简单的本地同步。
2. **对于穿透（不存在的数据）：**
    - **用户侧攻击：** 优先考虑**布隆过滤器**。
    - **常规容错：** **缓存空对象**代码最简单，也是最常用的“兜底”方案。

**既然提到了分布式锁的实现细节，** 你是否想了解一下 **Redisson 的“看门狗”机制**是如何自动给锁续期的？这是面试中经常紧接着问的高阶考点。

## Redisson 看门狗机制

这不仅是一个高频面试题，更是分布式锁在生产环境中必须解决的**核心痛点**。

### 1. 为什么要“看门狗” (Watch Dog)？

在刚才手动实现的 Redis 分布式锁代码中，我们面临一个**进退两难**的问题：

- 情况 A：过期时间设置太短
    
    假设你设置锁过期时间为 10 秒，但你的业务逻辑非常复杂，跑了 15 秒。
    
    - **后果：** 在第 10 秒时，Redis 自动把锁删了。第 11 秒，另一个线程进来了。此时**锁失效**，出现了并发问题。
- 情况 B：过期时间设置太长
    
    为了避免 A，你把过期时间设为 1 小时。
    
    - **后果：** 万一你的服务器刚拿到锁就宕机（断电）了，没有执行 `delete` 释放锁。
    - **结局：** 这个锁会在 Redis 里挂 1 小时，这 1 小时内谁都进不来，业务直接停摆。

**Redisson 的看门狗机制**就是为了解决这个问题：**它允许你只设置一个较短的过期时间（防宕机），但只要你的线程还在工作，它就自动帮你“续命”（防过期）。**

---

### 2. 看门狗的工作流程

Redisson 内部有一个后台线程（定时任务），我们俗称“看门狗”。它的工作逻辑如下：

1. **默认启动：** 当你调用 `lock.lock()` （不传时间参数）时，Redisson 会默认设置锁的过期时间（Lease Time）为 **30 秒**。
2. **定时检查：** 看门狗线程启动，每隔 **10 秒**（默认是过期时间的 1/3）就会去检查一下：“哎，那个持有锁的线程还在运行吗？”
3. **自动续期：**
    
    - **如果在：** 看门狗会执行一段 Lua 脚本，把 Redis 里的锁过期时间**重新重置**为 30 秒。
    - **如果不在（线程挂了/服务宕机）：** 看门狗线程也就没了（因为它在应用内存里），也就没人去续期。Redis 里的锁会在 30 秒倒计时结束后自动删除。

---

### 3. 代码对比：有狗 vs 没狗

这是面试官最喜欢问的细节：**并不是所有的 Redisson 锁都有看门狗！**

#### 场景一：激活看门狗 (推荐)

```Java
RLock lock = redisson.getLock("myLock");

// 方式 1：不传任何参数
// 默认过期时间 30s，每 10s 续期一次，直到业务跑完释放锁
lock.lock(); 

try {
    // 假设这里业务跑了 5 分钟
    // 没关系，看门狗会一直帮你续期，锁一直有效
    Thread.sleep(300000); 
} finally {
    lock.unlock(); // 解锁，看门狗线程销毁，停止续期
}
```

#### 场景二：看门狗失效 (手动指定时间)

```Java
RLock lock = redisson.getLock("myLock");

// 方式 2：显式指定 leaseTime (租约时间)
// 【注意】一旦传了这个时间（例如 10秒），看门狗机制就会失效！
// 如果 10秒 后业务还没跑完，锁会直接强制释放。
lock.lock(10, TimeUnit.SECONDS); 

try {
    // 业务跑了 15秒
    Thread.sleep(15000); 
    // 此时前 10秒 是安全的，后 5秒 锁已经没了，其他线程可以进来了！危险！
} finally {
    lock.unlock();
}
```

---

### 4. 核心原理总结 (面试作弊条)

如果你需要快速背诵核心点，记住这 3 个数字和 1 个机制：

1. **30 秒：** `lockWatchdogTimeout` 的默认配置，即锁的默认寿命。
2. **1/3 规则：** 看门狗会在过期时间过去了 1/3 时（即第 10 秒）由 `Netty` 的 `TimeTask` 进行续期。
3. **Lua 脚本：** 续期操作是原子的，通过 Lua 脚本完成。
4. **互斥性：** 如果服务宕机，看门狗线程随之死亡，无法续期，Redis 会在 30 秒后自动释放锁，避免死锁。

### 下一步

既然你已经掌握了 **“缓存三大难”** 和 **“分布式锁看门狗”**，这已经是中高级开发的水平了。

如果还要继续深挖 Redis，通常面试官会问：

“既然 Redisson 锁这么好，那如果 Redis 是主从架构（Master-Slave），主节点刚加完锁就挂了，锁还没同步到从节点，从节点升级为主，锁不就丢了吗？这怎么解决？”

你想了解这个极端的**“锁丢失”问题（Redlock 算法）**，还是想换个方向，聊聊 **Redis 为什么这么快（IO 多路复用）**？