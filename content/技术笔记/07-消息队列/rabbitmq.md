---
title: RabbitMQ 核心原理与面试重点
date: 2026-08-09
tags:
  - RabbitMQ
  - 消息队列
  - 面试
---
RabbitMQ 的强项不是“吞吐第一”，而是业务消息治理：路由灵活、ACK 明确、重试 / 死信容易落地。

# 一、RabbitMQ 适合什么场景

典型场景：

- 订单事件分发
- 通知、短信、邮件
- 任务异步化
- 需要复杂路由的业务消息

如果需求是：

- 超高吞吐日志流
- 超长时间海量积压
- 大规模事件回放

Kafka 通常更合适。

# 二、核心模型

| 概念 | 作用 |
| --- | --- |
| Producer | 生产消息 |
| Exchange | 路由消息 |
| Queue | 承载消息 |
| Binding | 绑定 Exchange 与 Queue |
| Consumer | 消费消息 |

## 2.1 一句话流程

Producer 发到 Exchange，Exchange 根据规则路由到 Queue，Consumer 从 Queue 拉取并 ACK。

# 三、Exchange 类型

| 类型 | 适合场景 |
| --- | --- |
| Direct | 精准路由 |
| Topic | 按模式匹配路由，最常见 |
| Fanout | 广播 |
| Headers | 按 header 路由，面试知道即可 |

> 真正常被问的是 Direct / Topic / Fanout，尤其 Topic。

# 四、RabbitMQ 怎么保证可靠性

## 4.1 生产者确认

开启 `publisher confirm`，确认消息是否真正到达 Broker。

## 4.2 Broker 持久化

至少要同时满足：

- Queue durable
- Message persistent

否则 Broker 重启后消息可能丢。

## 4.3 消费者确认

- 业务成功后再 ACK
- 不要收到消息立刻 auto-ack

## 4.4 新项目队列类型建议

> 新项目更建议优先 **Quorum Queue**，不要再把经典镜像队列当默认答案。

原因：

- 数据安全性更稳
- 故障恢复更清晰
- 更符合现在的官方主线

# 五、重试、死信、延迟

## 5.1 为什么 RabbitMQ 适合做业务消息

因为这条治理链路比较顺：

1. 消费失败
2. 判断能否重试
3. 临时失败走延迟重试
4. 永久失败进死信队列

## 5.2 死信队列（DLQ）

常见触发：

- 被拒绝且不重回队列
- TTL 到期
- 队列达到最大长度

## 5.3 延迟重试常见做法

- TTL + Dead Letter Exchange
- delayed message plugin

> 面试里核心不是背插件，而是说明：**重试要退避，死信要隔离，不能无限原地重试。**

# 六、顺序、并发与积压

## 6.1 顺序

- 单队列天然 FIFO
- 但多消费者并发、失败重回队列都会破坏业务完成顺序

严格保序时常见做法：

- 一个业务 key 落一个串行消费通道
- 控制并发和 `prefetch`

## 6.2 `prefetch`

它控制消费者一次预取多少条消息。

- 太大：单消费者囤积太多未 ACK 消息
- 太小：吞吐上不去

## 6.3 积压治理

| 问题 | 处理思路 |
| --- | --- |
| 消费慢 | 增消费者、拆慢逻辑、异步化 |
| 单队列过热 | 拆队列、按业务键路由 |
| 重试风暴 | 限重试次数、退避、死信隔离 |

# 七、RabbitMQ 的优点和边界

## 7.1 优点

- 路由灵活
- ACK / Confirm 语义直观
- 重试 / 死信治理容易讲清楚
- 很适合订单、通知、任务类业务消息

## 7.2 边界

- 吞吐通常不如 Kafka
- 长时间超大规模积压不是它的强项
- 做事件流回放不如 Kafka 顺手

# 八、面试 Checklist

- 能说清 Exchange / Queue / Binding 的关系。
- 能说清 RabbitMQ 可靠性三件套：Confirm、持久化、手动 ACK。
- 能说清为什么要死信队列，以及为什么不能无限重试。
- 能说清顺序只在单队列层面天然成立。
- 能主动补一句：**新项目优先考虑 Quorum Queue。**
