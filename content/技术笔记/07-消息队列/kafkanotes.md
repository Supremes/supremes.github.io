---
title: Kafka 核心原理与面试重点
date: 2026-08-09
tags:
  - Kafka
  - 消息队列
  - 面试
---
Kafka 的核心不是“会配参数”，而是理解它为什么能扛高吞吐、顺序和可靠性边界在哪里、为什么 Rebalance 会出事。

# 一、Kafka 适合解决什么问题

Kafka 更像**分布式提交日志**：

- 高吞吐事件流
- 日志采集
- 埋点数据
- 订单 / 用户行为事件总线
- 流式计算前置缓冲层

如果你要的是：

- 复杂路由
- 细粒度重试 / 死信
- 低门槛业务队列治理

RabbitMQ 往往更顺手。

# 二、核心模型

| 概念 | 作用 |
| --- | --- |
| Topic | 逻辑主题 |
| Partition | 顺序与并行的基本单位 |
| Offset | 分区内位点 |
| Leader Replica | 对外读写的主副本 |
| Follower Replica | 同步 Leader 数据 |
| ISR | 与 Leader 保持同步的副本集合 |
| Consumer Group | 共享消费进度的一组消费者 |

## 2.1 关于控制器要补的新说法

老资料常把 Kafka 和 ZooKeeper 强绑定。  
更稳妥的说法是：

> **新版本主流是 KRaft 模式**，控制器元数据管理已经不再默认依赖 ZooKeeper。

# 三、Kafka 为什么快

## 3.1 顺序追加写

消息按日志追加，磁盘和页缓存都更友好。

## 3.2 批量

- Producer 批量发送
- Broker 批量刷盘
- Consumer 批量拉取

## 3.3 Page Cache

大量读写命中操作系统页缓存，减少真实磁盘 I/O。

## 3.4 Zero Copy

Broker 转发文件数据时尽量减少内核态 / 用户态复制。

> 面试一句话：**Kafka 不是“磁盘慢所以不行”，而是把磁盘当成顺序日志设备来用。**

# 四、可靠性主线

## 4.1 生产者侧

### `acks`

| 配置 | 含义 |
| --- | --- |
| `0` | 发送即返回，可能丢 |
| `1` | Leader 收到即返回 |
| `all` | ISR 全部确认才返回 |

### 幂等生产者

`enable.idempotence=true`

作用：

- 减少因重试导致的重复写入
- 适合同一 Producer 会话内的幂等保障

## 4.2 Broker 侧

高频要点：

- 副本因子不要太低
- `min.insync.replicas` 不能随便设 1
- `unclean.leader.election.enable=false`

## 4.3 消费者侧

- 业务成功后再提交 offset
- 追求 at-least-once 时，重复消费要靠业务幂等

# 五、顺序与并行

## 5.1 Kafka 只能保证分区内顺序

如果你要“同一订单的消息有序”，做法是：

- 用订单号作为 key
- 同 key 落同一 partition

## 5.2 想提吞吐就会牺牲什么

- 分区越多，并行能力越强
- 但顺序只在单分区内成立
- 增加分区还会影响已有 key 的路由分布

# 六、Consumer Group 与 Rebalance

## 6.1 为什么会 Rebalance

- 新消费者加入
- 消费者掉线
- 分区数变化
- 处理太慢导致超时

## 6.2 为什么 Rebalance 可怕

- 暂时停顿
- 吞吐抖动
- offset 提交不当时容易重复消费

## 6.3 怎么减轻

- `poll` 线程别做超长阻塞
- 业务处理与 offset 提交顺序要一致
- 降低无意义扩缩容和频繁重启
- 使用更平滑的分配策略

# 七、积压与 lag

## 7.1 先看 lag，不要只看 Topic 总量

真正要看的是：

- 每个 partition 的 lag
- 是不是只有某几个 partition 特别热

## 7.2 常见治理

| 问题 | 处理思路 |
| --- | --- |
| 消费逻辑太重 | 异步化、批处理、拆慢 RPC |
| 热点分区 | 调整 key 设计 |
| 并行度不够 | 增消费者或分区，但要评估顺序影响 |
| 下游扛不住 | 限流、隔离、降级 |

# 八、Kafka 高频配置只记这些

| 配置 | 作用 |
| --- | --- |
| `acks=all` | 提升生产确认可靠性 |
| `enable.idempotence=true` | 降低重复写入 |
| `min.insync.replicas` | 约束最少同步副本数 |
| `max.poll.interval.ms` | 控制消费处理超时窗口 |
| `session.timeout.ms` | 控制心跳超时 |

# 九、面试 Checklist

- 能说清 Kafka 为什么快：顺序写、批量、页缓存、零拷贝。
- 能说清顺序只在 partition 内成立。
- 能说清 Rebalance 的触发、影响、缓解手段。
- 能说清 `acks=all`、ISR、`min.insync.replicas` 的关系。
- 能主动补一句：**现在主流是 KRaft，不要把 ZooKeeper 当默认前提。**
