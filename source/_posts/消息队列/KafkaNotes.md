---
title: Kafka 深度学习笔记
tags:
  - Kafka
  - 分布式系统
categories:
  - 消息队列
description: 深入学习 Apache Kafka 的核心概念、架构设计、部署配置和生产环境最佳实践
cover: /imgs/KafkaNotes封面.png
abbrlink: 1562
date: 2025-11-27 21:11:20
updated: 2025-11-27 22:35:00
---

## 📖 简介

Apache Kafka 是一个分布式流处理平台,最初由 LinkedIn 开发。早期版本使用 Scala 编写并运行在 JVM 上,后续版本逐渐迁移至 Java 实现。

## 🔑 核心概念

### 副本机制

- **Leader Replica（主副本）**
  - 负责处理所有客户端的读写请求
  - 维护消息的写入顺序和偏移量等元数据
  
- **Follower Replica（从副本）**
  - 从 Leader 同步最新数据
  - 提供数据冗余和高可用保障
  - 不对外提供读写服务

### 持久化机制

Kafka 使用高效的日志存储机制来持久化消息：

- **顺序 I/O 追加写入**
  - 消息以追加方式顺序写入日志文件
  - 充分利用磁盘顺序读写的高性能特性
  
- **Log Segment 分段管理**
  - 将日志按照 Log Segment 进行分段
  - 定时清理过期的 Segment 来释放磁盘空间

---

## 📚 核心术语

| 术语 | 英文 | 说明 |
|-----|------|------|
| **消息** | Record | Kafka 处理的主要对象 |
| **主题** | Topic | 承载消息的逻辑容器，用于区分不同的业务 |
| **分区** | Partition | 一个有序不变的消息序列，每个主题可以有多个分区 |
| **消息位移** | Offset | 分区中每条消息的位置信息，单调递增且不变 |
| **副本** | Replica | 消息的多个拷贝，分为 Leader 和 Follower 副本 |
| **生产者** | Producer | 向主题发布新消息的应用程序 |
| **消费者** | Consumer | 从主题订阅消息的应用程序 |
| **消费者位移** | Consumer Offset | 表征消费者消费进度 |
| **消费者组** | Consumer Group | 多个消费者实例组成的组，同时消费多个分区以实现高吞吐 |
| **重平衡** | Rebalance | 消费者组内某个实例挂掉后，其他实例自动重新分配订阅分区的过程 |

### 高级概念

- **刷盘（Flush）**
  - 将内存中的数据持久化到磁盘的过程
  - 消息先写入内存缓冲区，再根据策略刷写到磁盘
  - 保证数据持久性，即使服务器重启也不会丢失

- **副本因子（Replication Factor）**
  - 定义每个分区有多少个副本
  - 例如副本因子为 3，意味着 1 个 Leader + 2 个 Follower

- **Purgatory（炼狱）**
  - 用于处理延迟操作的内部机制
  - 处理不能立即完成，需要等待条件满足的操作
  - 例如事务相关操作

---

## 🚀 部署配置

### Broker 参数配置

#### 存储配置

**`log.dirs`**（推荐）
```properties
log.dirs=/home/kafka/data1,/home/kafka/data2,/home/kafka/data3
```
- 建议将各个目录挂载到不同的物理磁盘
- **优势**：提升读写性能 + 实现故障转移

**`log.dir`**
- 单个路径配置，补充 `log.dirs` 使用

#### 网络配置

**`listeners`**
- 告诉外部连接者使用什么协议连接
- 格式：`<protocol>://<host>:<port>`
- 示例：`PLAINTEXT://localhost:9092`

**`advertised.listeners`**
- Broker 对外发布的监听器地址
- 客户端实际连接的地址

**自定义协议配置**
```properties
listeners=CONTROLLER://localhost:9992
listener.security.protocol.map=CONTROLLER:PLAINTEXT
```

#### Topic 管理

| 参数 | 推荐值 | 说明 |
|-----|--------|------|
| `auto.create.topics.enable` | **false** | 禁止自动创建 Topic，避免线上未知问题 |
| `unclean.leader.election.enable` | **false** | 禁止不干净的 Leader 选举，防止数据丢失 |
| `auto.leader.rebalance.enable` | **false** | 禁止定期 Leader 选举，避免频繁切换 |

#### 数据管理

**消息保留时间**
```properties
log.retention.hours=168    # 7天
log.retention.minutes=10080
log.retention.ms=604800000  # 优先级最高
```

**消息大小限制**
```properties
message.max.bytes=1048576   # 1MB
log.retention.bytes=-1      # 无限制
```

### Topic 级别参数

Topic 参数优先级高于 Broker 全局参数：

```properties
# 消息保留时间
retention.ms=604800000  # 7天

# 磁盘空间配额
retention.bytes=-1      # 无限制

# 最大消息大小
max.message.bytes=1048576
```

### JVM 参数调优

```bash
# 堆内存配置（推荐 6GB）
export KAFKA_HEAP_OPTS="-Xms6g -Xmx6g"

# GC 配置
export KAFKA_JVM_PERFORMANCE_OPTS="-XX:+UseG1GC -XX:MaxGCPauseMillis=20"
```

---

## 🎯 分区策略

决定生产者将消息发送到哪个分区的算法。

### 自定义分区策略

```java
// 实现 Partitioner 接口
public class CustomPartitioner implements org.apache.kafka.clients.producer.Partitioner {
    @Override
    public int partition(String topic, Object key, byte[] keyBytes, 
                        Object value, byte[] valueBytes, Cluster cluster) {
        // 自定义分区逻辑
    }
}
```

配置参数：
```properties
partitioner.class=com.example.CustomPartitioner
```

### 内置分区策略

#### 1. 轮询策略（Round-Robin）

**特点**：
- Kafka 默认策略
- 消息均匀分配到所有分区
- 最佳负载均衡表现

**适用场景**：
- 无需保证消息顺序
- 追求负载均衡

#### 2. 随机策略（Random）

**特点**：
- 随机选择分区
- 理论上也能实现负载均衡
- 但效果不如轮询策略

#### 3. 按键保序策略（Key-Ordering）

**特点**：
- 相同 Key 的消息进入同一分区
- 保证相同 Key 的消息顺序

**实现**：
```java
List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
return Math.abs(key.hashCode()) % partitions.size();
```

**适用场景**：
- 需要保证相同 Key 的消息顺序
- 例如：同一用户的操作日志

---

## 🎮 Kafka 控制器

### 角色定位

Kafka 集群中只能有**一台 Broker** 充当控制器（Controller）角色。

### 主要职责

#### 1. 分区分配

控制器负责决定每个分区的副本分布：

```
示例：Topic 有 2 个分区，副本因子为 2
- 分区1: Leader→Broker1, Follower→Broker2
- 分区2: Leader→Broker2, Follower→Broker1
```

#### 2. Leader 副本选举

- 当 Leader 副本所在 Broker 宕机时
- 控制器从 ISR（In-Sync Replicas）中选举新的 Leader

#### 3. 主题管理

- 接受来自管理工具或 API 的请求
- 处理主题的创建和删除操作

#### 4. 集群监控与协调

- 通过心跳机制检测 Broker 存活状态
- 节点失联时重新分配分区和副本

### 控制器选举

**选举机制**：
1. Broker 启动时尝试在 ZooKeeper 中创建 `/controller` 节点
2. 第一个成功创建节点的 Broker 成为控制器
3. 其他 Broker 通过 Watch 机制监控控制器状态

**Failover 机制**：
- ZooKeeper 检测到控制器节点失效
- 删除 `/controller` 节点
- 存活的 Broker 重新竞选新的控制器

---

## 🔒 消息交付可靠性

Kafka 提供三种消息交付可靠性保障：

### 1. 最多一次（At Most Once）

- **特征**：消息可能丢失，但绝不重复
- **场景**：日志收集等对数据完整性要求不高的场景

### 2. 至少一次（At Least Once）

- **特征**：消息不会丢失，但可能重复
- **默认**：Kafka 默认提供此级别保障
- **场景**：大多数业务场景

### 3. 精确一次（Exactly Once）

- **特征**：消息不丢失也不重复
- **实现**：通过幂等性 + 事务机制
- **场景**：金融交易等对数据准确性要求极高的场景

---

## ❓ 常见问题

### Q1: 为什么 Kafka 不允许从副本读取数据？

与 MySQL 主从复制不同，Kafka 的从副本不对外提供读服务。原因如下：

#### 1. 一致性模型差异

**Kafka**：
- 基于日志的消息传递模型
- 强调消息顺序和实时性
- 从副本可能存在同步延迟，导致数据不一致

**MySQL**：
- ACID 事务模型
- 从库应用完 Binlog 后数据一致
- 可以安全地提供读服务

#### 2. 设计目标不同

**Kafka**：
- 专注于高吞吐量的消息写入和顺序读取
- 允许从副本读取会增加复杂性

**MySQL**：
- 支持复杂查询和事务处理
- 读写分离可以分担主库压力

#### 3. 故障恢复复杂性

**Kafka**：
- 从副本提供读服务时，故障切换更复杂
- 需要处理正在进行的读操作

**MySQL**：
- 从库故障恢复相对简单
- 重新同步 Binlog 即可

### Q2: Kafka 如何保证消息顺序性？

#### 1. 分区有序

- 每个分区内的消息严格有序
- 全局有序需要使用单分区（牺牲并发性）

#### 2. 同步发送

配置 `acks=all` 保证消息持久性：

| acks 值 | 说明 | 可靠性 | 性能 |
|---------|------|--------|------|
| **0** | 不等待确认，立即返回 | ❌ 最低 | ✅ 最高 |
| **1** | 等待 Leader 确认 | ⚠️ 中等 | ⚠️ 中等 |
| **all** | 等待所有 ISR 确认 | ✅ 最高 | ❌ 最低 |

#### 3. 消息偏移量

- 每个消息有唯一的 Offset
- 消费者按 Offset 顺序消费
- 保证消费顺序与生产顺序一致

### Q3: Kafka 消息如何存储？

#### 存储结构

```
Topic
└── Partition
    └── Log Segment
        ├── .log    # 消息数据
        └── .index  # 索引文件
```

#### 存储特性

- **格式**：优化的日志格式
- **不可变**：消息一旦写入不可修改
- **顺序追加**：新消息追加到日志末尾
- **分段管理**：Log Segment 便于管理和清理

---

## 💡 生产环境最佳实践

### 关键参数配置

#### auto.create.topics.enable = false

**理由**：
- 避免因拼写错误自动创建 Topic
- 例如：`test` 误写为 `tst`，会自动创建 `tst` Topic
- 大公司应由运维统一管理 Topic

#### unclean.leader.election.enable = false

**场景**：所有高质量副本都挂掉了，怎么办？

**选择**：
- `false`：坚持原则，分区不可用（保证数据完整性）
- `true`：降级服务，允许落后副本成为 Leader（可能丢数据）

**推荐**：生产环境设置为 `false`

#### auto.leader.rebalance.enable = false

**问题**：定期换 Leader 的代价很高
- 所有客户端需要切换连接
- 没有实质性能收益
- 可能影响服务稳定性

**推荐**：生产环境设置为 `false`

---

## 📚 参考资料

- [Apache Kafka 官方文档](https://kafka.apache.org/documentation/)
- [Kafka: The Definitive Guide](https://www.confluent.io/resources/kafka-the-definitive-guide/)
- [Kafka 核心技术与实战](https://time.geekbang.org/column/intro/100029201)
