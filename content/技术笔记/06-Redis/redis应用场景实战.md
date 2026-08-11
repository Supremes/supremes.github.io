---
title: Redis 应用场景实战
date: 2026-01-03
tags:
  - Redis
  - 应用场景
  - 实战
---
Redis 的高性能和丰富的数据类型使其在各种业务场景中大放异彩。本文汇总 Redis 在实际项目中的经典应用场景与最佳实践。

---

# 一、排行榜（Leaderboard）

## 1.1 场景描述

**典型应用：** 游戏积分榜、文章点赞榜、销售排行榜、直播热度榜。

**核心需求：**
- 实时更新排名。
- 高并发读写（如百万用户同时刷新排行榜）。
- 支持范围查询（如 Top 100）。

---

## 1.2 技术方案：ZSet（有序集合）

**数据结构：**
```bash
ZADD leaderboard:2025 100 "user:1001"
ZADD leaderboard:2025 200 "user:1002"
ZADD leaderboard:2025 150 "user:1003"
```

**常用操作：**

### 更新分数（增加积分）
```bash
ZINCRBY leaderboard:2025 10 "user:1001"
```

### 查询 Top N（降序）
```bash
ZREVRANGE leaderboard:2025 0 99 WITHSCORES
# 返回前 100 名及其分数
```

### 查询用户排名
```bash
ZREVRANK leaderboard:2025 "user:1001"
# 返回排名（0 表示第一名）
```

### 查询用户分数
```bash
ZSCORE leaderboard:2025 "user:1001"
```

### 查询分数区间的用户
```bash
ZRANGEBYSCORE leaderboard:2025 100 200 WITHSCORES
```

---

## 1.3 Java 实现示例

```java
@Service
public class LeaderboardService {
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    private static final String LEADERBOARD_KEY = "leaderboard:2025";
    
    // 增加积分
    public void addScore(String userId, double score) {
        redisTemplate.opsForZSet().incrementScore(LEADERBOARD_KEY, userId, score);
    }
    
    // 获取 Top N
    public List<LeaderboardVO> getTopN(int topN) {
        Set<ZSetOperations.TypedTuple<String>> result = 
            redisTemplate.opsForZSet()
                .reverseRangeWithScores(LEADERBOARD_KEY, 0, topN - 1);
        
        return result.stream()
            .map(tuple -> new LeaderboardVO(
                tuple.getValue(),
                tuple.getScore(),
                getRank(tuple.getValue()) + 1 // 排名从 1 开始
            ))
            .collect(Collectors.toList());
    }
    
    // 获取用户排名
    public Long getRank(String userId) {
        return redisTemplate.opsForZSet()
            .reverseRank(LEADERBOARD_KEY, userId);
    }
    
    // 获取用户分数
    public Double getScore(String userId) {
        return redisTemplate.opsForZSet()
            .score(LEADERBOARD_KEY, userId);
    }
}
```

---

## 1.4 性能优化

### 定时快照

**问题：** 实时排行榜压力大（如百万用户频繁查询）。

**优化：** 每分钟生成一次快照，用户查询快照版本。

```bash
# 定时任务（每分钟执行）
ZUNIONSTORE leaderboard:snapshot 1 leaderboard:2025
EXPIRE leaderboard:snapshot 120
```

---

# 二、消息队列（Message Queue）

> 这一节只讨论 **Redis 作为轻量队列** 的适用边界；如果是业务主消息链路、可靠性治理、重试 / 死信 / 积压处理，主线请看 [消息可靠性主线与选型](../07-消息队列/消息可靠性与选型.md)。

## 2.1 方案对比

| **方案**           | **数据结构** | **优点**         | **缺点**               | **推荐场景**   |
| ---------------- | -------- | -------------- | -------------------- | ---------- |
| **List + BLPOP** | List     | 实现简单           | 无 ACK 机制、无消费者组       | 简单任务队列     |
| **Stream**       | Stream   | 支持消费者组、ACK 确认  | 功能仍弱于专业 MQ           | **轻量可靠队列** |
| **Pub/Sub**      | -        | 多播、实时性高        | 不持久化、消费者离线消息丢失       | 实时通知、聊天室   |

---

## 2.2 方案 1：List + BLPOP（简单队列）

### 生产者
```bash
LPUSH queue:task "task1"
LPUSH queue:task "task2"
```

### 消费者（阻塞等待）
```bash
BRPOP queue:task 0  # 0 表示永久阻塞
```

### Java 实现
```java
// 生产者
public void sendTask(String task) {
    redisTemplate.opsForList().leftPush("queue:task", task);
}

// 消费者
public String consumeTask() {
    return redisTemplate.opsForList()
        .rightPop("queue:task", 0, TimeUnit.SECONDS);
}
```

**缺点：**
- 无 ACK 机制：消费者崩溃，消息丢失。
- 无消费者组：多消费者会重复消费。

---

## 2.3 方案 2：Stream（推荐）

### 生产者
```bash
XADD stream:order * order_id 1001 user_id 2001 amount 99.99
```

### 创建消费者组
```bash
XGROUP CREATE stream:order group1 0
```

### 消费者读取消息
```bash
XREADGROUP GROUP group1 consumer1 COUNT 10 STREAMS stream:order >
```

### ACK 确认
```bash
XACK stream:order group1 <message_id>
```

### Java 实现（Spring Data Redis）
```java
@Service
public class StreamMessageService {
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    // 生产者
    public void sendOrder(Order order) {
        Map<String, String> fields = Map.of(
            "order_id", order.getId().toString(),
            "user_id", order.getUserId().toString(),
            "amount", order.getAmount().toString()
        );
        
        redisTemplate.opsForStream()
            .add(StreamRecords.newRecord()
                .ofMap(fields)
                .withStreamKey("stream:order"));
    }
    
    // 消费者
    @Scheduled(fixedDelay = 1000)
    public void consumeOrder() {
        List<MapRecord<String, Object, Object>> records = 
            redisTemplate.opsForStream()
                .read(Consumer.from("group1", "consumer1"),
                      StreamReadOptions.empty().count(10),
                      StreamOffset.create("stream:order", ReadOffset.lastConsumed()));
        
        records.forEach(record -> {
            // 处理消息
            System.out.println("Received: " + record.getValue());
            
            // ACK 确认
            redisTemplate.opsForStream()
                .acknowledge("stream:order", "group1", record.getId());
        });
    }
}
```

---

# 三、限流（Rate Limiting）

## 3.1 方案对比

| **方案**      | **实现**                | **优点**     | **缺点**       | **推荐场景**   |
| ----------- | --------------------- | ---------- | ------------ | ---------- |
| **固定窗口**    | INCR + EXPIRE         | 实现简单       | 窗口边界流量突刺     | 简单限流       |
| **滑动窗口**    | ZSet（时间戳）            | 精确限流       | 占用内存多        | 精确限流（如 API） |
| **令牌桶/漏桶**  | Lua 脚本 + 时间戳         | 平滑限流       | 实现复杂         | 高并发场景      |

---

## 3.2 方案 1：固定窗口（INCR）

### 原理
```
每秒允许 100 次请求
┌─────────┬─────────┬─────────┐
│ 第 1 秒  │ 第 2 秒  │ 第 3 秒  │
│  100    │   0     │   0     │
└─────────┴─────────┴─────────┘
```

### 实现
```java
public boolean allowRequest(String userId) {
    String key = "ratelimit:" + userId + ":" + System.currentTimeMillis() / 1000;
    Long count = redisTemplate.opsForValue().increment(key);
    
    if (count == 1) {
        redisTemplate.expire(key, 1, TimeUnit.SECONDS);
    }
    
    return count <= 100; // 每秒最多 100 次
}
```

**缺点：** 窗口边界流量突刺（如第 1 秒末 50 次 + 第 2 秒初 50 次 = 100 次，但 1 秒内实际 100 次）。

---

## 3.3 方案 2：滑动窗口（ZSet）

### 原理
```
用时间戳作为 score，滑动窗口内的请求数不超过限制
```

### Lua 脚本
```lua
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

-- 删除窗口外的请求
redis.call('ZREMRANGEBYSCORE', key, 0, now - window * 1000)

-- 统计窗口内的请求数
local count = redis.call('ZCARD', key)

if count < limit then
    redis.call('ZADD', key, now, now)
    redis.call('EXPIRE', key, window)
    return 1
else
    return 0
end
```

### Java 实现
```java
public boolean allowRequest(String userId) {
    String key = "ratelimit:sliding:" + userId;
    long now = System.currentTimeMillis();
    int limit = 100; // 100 次
    int window = 60;  // 60 秒
    
    String script = "..."; // Lua 脚本
    Long result = redisTemplate.execute(
        new DefaultRedisScript<>(script, Long.class),
        Collections.singletonList(key),
        String.valueOf(limit),
        String.valueOf(window),
        String.valueOf(now)
    );
    
    return result != null && result == 1;
}
```

---

## 3.4 方案 3：令牌桶（推荐）

### 原理
```
每秒生成 N 个令牌，请求时消耗令牌，桶满时丢弃令牌
```

### Lua 脚本
```lua
local key = KEYS[1]
local capacity = tonumber(ARGV[1])    -- 桶容量
local rate = tonumber(ARGV[2])        -- 生成速率（令牌/秒）
local requested = tonumber(ARGV[3])   -- 请求令牌数
local now = tonumber(ARGV[4])

local tokens_key = key .. ":tokens"
local timestamp_key = key .. ":timestamp"

local last_tokens = tonumber(redis.call('GET', tokens_key) or capacity)
local last_time = tonumber(redis.call('GET', timestamp_key) or now)

-- 计算新增令牌
local delta = math.max(0, now - last_time)
local new_tokens = math.min(capacity, last_tokens + delta * rate / 1000)

if new_tokens >= requested then
    redis.call('SET', tokens_key, new_tokens - requested)
    redis.call('SET', timestamp_key, now)
    redis.call('EXPIRE', tokens_key, 60)
    redis.call('EXPIRE', timestamp_key, 60)
    return 1
else
    return 0
end
```

---

# 四、分布式 ID 生成

## 4.1 方案 1：INCR（简单自增 ID）

```java
public Long generateId() {
    return redisTemplate.opsForValue().increment("global:id");
}
```

**优点：** 简单、高性能（单机 10 万 QPS）。

**缺点：**
- 单调递增，容易被爬虫（如订单 ID）。
- 单机瓶颈。

---

## 4.2 方案 2：雪花算法（Snowflake）

**结构：**
```
64 位 = 1 位符号 + 41 位时间戳 + 10 位机器 ID + 12 位序列号
```

**Java 实现（Hutool）：**
```java
@Bean
public Snowflake snowflake() {
    return new Snowflake(1, 1); // workerId=1, datacenterId=1
}

public long generateId() {
    return snowflake.nextId();
}
```

**优点：**
- 趋势递增（按时间排序）。
- 高性能（单机百万 QPS）。

**缺点：**
- 依赖系统时钟（时钟回拨会重复）。

> 这一节只覆盖 **Redis 视角** 的两种实现；完整的方案横评（UUID v7、号段模式、ULID）、时钟回拨的三种应对策略、workerId 分配方式以及选型决策树，见 [全局唯一 ID 生成方案](../10-系统设计与场景题/全局唯一ID生成方案.md)。

---

# 五、会话共享（Session）

## 5.1 场景描述

**问题：** 单体应用扩展为分布式集群后，Session 无法共享。

```
用户请求 → Nginx 负载均衡
              ├─ 服务器 A（Session A）
              ├─ 服务器 B（Session B）
              └─ 服务器 C（Session C）
```

---

## 5.2 解决方案：Spring Session + Redis

### Maven 依赖
```xml
<dependency>
    <groupId>org.springframework.session</groupId>
    <artifactId>spring-session-data-redis</artifactId>
</dependency>
```

### 配置
```yaml
spring:
  session:
    store-type: redis
    timeout: 30m
```

### 使用（无需修改代码）
```java
@GetMapping("/login")
public String login(HttpSession session) {
    session.setAttribute("userId", 1001);
    return "success";
}

@GetMapping("/getUser")
public Object getUser(HttpSession session) {
    return session.getAttribute("userId");
}
```

**原理：** Spring Session 拦截 HttpSession 操作，自动存储到 Redis。

---

# 六、地理位置（GEO）

## 6.1 场景描述

**典型应用：** 附近的人、附近的餐厅、打车距离计算。

---

## 6.2 核心命令

### 添加地理位置
```bash
GEOADD locations 116.397128 39.916527 "beijing"
GEOADD locations 121.473701 31.230416 "shanghai"
```

### 查找附近的位置
```bash
GEORADIUS locations 116.40 39.92 100 km WITHDIST WITHCOORD
```

### 计算两点距离
```bash
GEODIST locations "beijing" "shanghai" km
```

---

## 6.3 Java 实现
```java
@Service
public class LocationService {
    @Autowired
    private StringRedisTemplate redisTemplate;
    
    // 添加用户位置
    public void addUserLocation(String userId, double longitude, double latitude) {
        redisTemplate.opsForGeo()
            .add("user:locations", new Point(longitude, latitude), userId);
    }
    
    // 查找附近的用户（5 公里内）
    public List<String> getNearbyUsers(double longitude, double latitude) {
        Circle circle = new Circle(new Point(longitude, latitude), 
                                   new Distance(5, Metrics.KILOMETERS));
        
        GeoResults<RedisGeoCommands.GeoLocation<String>> results = 
            redisTemplate.opsForGeo()
                .radius("user:locations", circle);
        
        return results.getContent().stream()
            .map(result -> result.getContent().getName())
            .collect(Collectors.toList());
    }
}
```

---

# 七、布隆过滤器（Bloom Filter）

## 7.1 场景描述

**典型应用：** 缓存穿透防护、垃圾邮件过滤、爬虫去重。

---

## 7.2 Redisson 实现

```java
@Autowired
private RedissonClient redisson;

@PostConstruct
public void initBloomFilter() {
    RBloomFilter<String> bloomFilter = redisson.getBloomFilter("email:filter");
    // 预期 100 万元素，误判率 0.01
    bloomFilter.tryInit(1000000L, 0.01);
    
    // 添加已注册邮箱
    bloomFilter.add("alice@example.com");
    bloomFilter.add("bob@example.com");
}

public boolean isEmailRegistered(String email) {
    RBloomFilter<String> bloomFilter = redisson.getBloomFilter("email:filter");
    return bloomFilter.contains(email);
}
```

---

# 八、延时队列（Delayed Queue）

## 8.1 场景描述

**典型应用：** 订单超时取消、优惠券过期提醒、定时任务。

---

## 8.2 实现方案：ZSet（时间戳作为 score）

### 添加延时任务
```java
public void addDelayedTask(String taskId, long delaySeconds) {
    long executeTime = System.currentTimeMillis() + delaySeconds * 1000;
    redisTemplate.opsForZSet().add("delayed:tasks", taskId, executeTime);
}
```

### 消费延时任务
```java
@Scheduled(fixedDelay = 1000)
public void consumeDelayedTasks() {
    long now = System.currentTimeMillis();
    
    Set<String> tasks = redisTemplate.opsForZSet()
        .rangeByScore("delayed:tasks", 0, now);
    
    tasks.forEach(taskId -> {
        // 执行任务
        System.out.println("Execute: " + taskId);
        
        // 删除任务
        redisTemplate.opsForZSet().remove("delayed:tasks", taskId);
    });
}
```

---

# 九、总结与选型

| **场景**     | **Redis 数据类型** | **关键命令**                     | **典型应用**     |
| ---------- | -------------- | ---------------------------- | ------------ |
| **排行榜**    | ZSet           | ZADD、ZREVRANGE、ZRANK        | 游戏积分榜、热度榜    |
| **消息队列**   | Stream / List  | XADD、XREADGROUP、BLPOP       | 轻量任务队列、短链路异步 |
| **限流**     | String / ZSet  | INCR、Lua 脚本                 | API 限流、防刷    |
| **分布式 ID** | String         | INCR、雪花算法                   | 订单号、用户 ID    |
| **会话共享**   | Hash / String  | Spring Session               | 分布式 Web 应用   |
| **地理位置**   | Geo            | GEOADD、GEORADIUS、GEODIST    | 附近的人、打车距离    |
| **布隆过滤器**  | Bitmap         | SETBIT、GETBIT（Redisson 封装）   | 缓存穿透防护、去重    |
| **延时队列**   | ZSet           | ZADD、ZRANGEBYSCORE           | 订单超时、定时任务    |

---

通过灵活运用 Redis 的数据类型与命令，可以高效解决各种业务场景的技术难题！🚀
