---
title: KafkaNotes
date: 2025-11-27 21:11:20
tags:
    - Kafka
categories:
    - 学习笔记
    - 消息队列
description:
cover: /imgs/KafkaNotes封面.png
---

![img](https://cdn.nlark.com/yuque/0/2024/png/26265874/1729754130306-a1a3af15-9b76-490d-b9af-0224ad74ff97.png)

![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729754903829-7e18bd78-ced4-496f-8a6b-52fe21c941a1.jpeg)

**

**

**leader replica: for client to read and write**

**follower replica: sync latest data with leader replica**

**

**

**kafka broker 持久化消费日志:**

- **使用顺序I/O追加写消费日志**
- **Log segment: 将日志按照Log segment进行分段，然后定时去更新删除Log segment来腾出空间**



# 背景

kafka早期版本由scala编写，编译成class文件，跑在JVM上，后面由Java编写。

# 术语

- 消息：Record。Kafka是消息引擎嘛，这里的消息就是指Kafka处理的主要对象。
- 主题：Topic。主题是承载消息的逻辑容器，在实际使用中多用来区分具体的业务。
- 分区：Partition。一个有序不变的消息序列。每个主题下可以有多个分区。
- 消息位移：Offset。表示分区中每条消息的位置信息，是一个单调递增且不变的值。
- 副本：Replica。Kafka中同一条消息能够被拷贝到多个地方以提供数据冗余，这些地方就是所谓的副本。副本还分为领导者副本和追随者副本，各自有不同的角色划分。副本是在分区层级下的，即每个分区可配置多个副本实现高可用。
- 生产者：Producer。向主题发布新消息的应用程序。
- 消费者：Consumer。从主题订阅新消息的应用程序。
- 消费者位移：Consumer Offset。表征消费者消费进度，每个消费者都有自己的消费者位移。
- 消费者组：Consumer Group。多个消费者实例共同组成的一个组，同时消费多个分区以实现高吞吐。
- 重平衡：Rebalance。消费者组内某个消费者实例挂掉后，其他消费者实例自动重新分配订阅主题分区的过程。Rebalance是Kafka消费者端实现高可用的重要手段。
- **刷盘**：刷盘是指将内存中的数据持久化到磁盘的过程。Kafka 的数据存储在磁盘上的日志文件（Log File）中，消息先被写入到内存缓冲区，然后根据一定的策略将这些消息从内存刷写到磁盘，以保证数据的持久性，即使在服务器重启等情况下数据也不会丢失。
- replication-factor：副本因子。例如，一个主题分区有 3 个副本，意味着除了主副本（Leader Replica）外，还有 2 个从副本（Follower Replica）存储相同的数据。
- Purgatory：是一个用于处理延迟操作的内部机制。它主要用于处理那些不能立即完成，需要等待一些条件满足后才能完成的操作，比如事务（Transaction）相关的操作。





# 部署

![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729760833135-4703b8dc-570c-4d7b-a938-e9ffad214cce.jpeg)

## 集群参数设置

![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729822843114-90d3b692-99ef-4fba-9859-27aebf9ec514.jpeg)

![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729824751683-671327c5-2f28-44eb-98ed-793f21f57d84.jpeg)

### Broker参数

- Log.dirs: 建议各个目录挂在到不同的磁盘csv格式，**提升读写性能和实现故障转移**

/home/dir1, /home/dir2

- Log.dir：单个路径，补充上述参数所用
- listeners：告诉外部连接者（客户端或其他broker）使用什么协议连接
- advertised.listeners：和listeners相比多了个advertised。Advertised的含义表示宣称的、公布的，就是说这组监听器是Broker用于对外发布的。

**监听器**

协议可以是标准协议或自定义协议，如：

 controller://localhost:9992

若使用了自定义协议（如：controller），还需要指定以下参数：

- listener.security.protocol.map：告诉协议底层使用了哪种安全协议 - listener.security.protocol.map=CONTROLLER:PLAINTEXT

**Topic管理**

- auto.create.topics.enable：是否允许自动创建Topic。建议默认设置为false，避免线上环境出现未知问题
- unclean.leader.election.enable：是否允许Unclean Leader选举。建议默认设置为false
- auto.leader.rebalance.enable：是否允许定期进行Leader选举。建议默认设置为false，不然线上会出现定期换leader副本的情况

**数据管理**

- log.retention.{hours|minutes|ms}：这是个“三兄弟”，都是控制一条消息数据被保存多长时间。从优先级上来说ms设置最高、minutes次之、hours最低。
- log.retention.bytes：这是指定Broker为消息保存的总磁盘容量大小。
- message.max.bytes：控制Broker能够接收的最大消息大小。

### Topic参数

同时设置broker参数和topic参数，以topic参数为准。

- `retention.ms`：规定了该Topic消息被保存的时长。默认是7天，即该Topic只保存最近7天的消息。一旦设置了这个值，它会覆盖掉Broker端的全局参数值。
- `retention.bytes`：规定了要为该Topic预留多大的磁盘空间。和全局参数作用相似，这个值通常在多租户的Kafka集群中会有用武之地。当前默认值是-1，表示可以无限使用磁盘空间。
- `max.message.bytes`。它决定了Kafka Broker能够正常接收该Topic的最大消息大小。



### JVM 参数

JVM参数：在启动时设置

- KAFKA_HEAP_OPTS：堆大小参数：默认为1GB，建议设置成6GB，业界公认的值，毕竟broker在和客户端交互时，会创建大量的ByteBuffer实例
- KAFKA_JVM_PERFORMANCE_OPTS：垃圾回收期参数- GC参数

## 分区策略

决定生产者将消息发送到哪个分区的算法，kafka提供了默认的分区策略，也支持自定义分区算法。

自定义分区策略，需要配置生产者端的参数 - partitioner.class : 参数为实现类的full qualified name

实现org.apache.kafka.clients.producer.Partitioner 接口

### 轮询策略

轮询策略有非常优秀的负载均衡表现，它总是能保证消息最大限度地被平均分配到所有分区上，故默认情况下它是最合理的分区策略，也是我们最常用的分区策略之一。![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729826033997-732b5a79-f512-494e-876a-48bdab887675.jpeg)

### 随机策略

![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729826080044-8819f9a6-ca2e-4505-bab7-7aaee08842ff.jpeg)

### **按消息键保序策略**

Key-ordering 策略。同一个Key的所有消息都进入到相同的分区里面，由于每个分区下的消息处理都是有顺序的，故这个策略被称为按消息键保序策略，如下图所示。

![img](https://cdn.nlark.com/yuque/0/2024/jpeg/26265874/1729826566637-bfda281e-26a3-4ffa-b7e0-8cc8a4d14c81.jpeg)

```java
List<PartitionInfo> partitions = cluster.partitionsForTopic(topic);
return Math.abs(key.hashCode()) % partitions.size();
```

## Kafka控制器

Kafka集群运行过程中，只能有一台Broker充当控制器的角色。

### 主要职责

负责管理和协调集群中的各类工作，比如分区的分配，副本的管理，主题的创建和删除等

1. 1. 分区分配：主副本的分布，例如topic有两个分区，分区1的leader副本放置到broker1，从副本放置到broker2；分区2的leader副本放置到broker2，从副本放置到broker1。

![img](https://cdn.nlark.com/yuque/0/2024/png/26265874/1731847546326-2db13fcb-42d0-4871-bcb3-5fd03497be70.png)

1. 1. leader副本选举：若leader副本所在broker节点宕机，控制器会启动副本选举过程
   2. 主题创建和删除：接受来自脚本或API的请求
   3. 集群监控和协调：与节点之间的心跳机制，来检测节点是否存活，若节点长时间无心跳，则认为出现问题，便会重新分配该节点上的分区和副本

### 控制器如何被选出来的

Broker在启动时，会尝试去ZooKeeper中创建/controller节点。Kafka当前选举控制器的规则是：第一个成功创建/controller节点的Broker会被指定为控制器。

### 控制节点宕机了怎么办

Failover机制：Zookeeper通过watch机制，来检测当前的控制器所在节点是否存活，若出现问题，便会删除该控制器，存活的broker会重新竞选新的控制器。



## 消息交付可靠性保障

所谓的消息交付可靠性保障，是指Kafka对Producer和Consumer要处理的消息提供什么样的承诺。常见的承诺有以下三种：

- **最多一次（at most once）：消息可能会丢失，但绝不会被重复发送。**
- **至少一次（at least once）：消息不会丢失，但有可能被重复发送。**
- **精确一次（exactly once）：消息不会丢失，也不会被重复发送。**

目前，Kafka默认提供的交付可靠性保障是第二种，即至少一次。

Kafka通过幂等性和事务性来实现精确一次的交付可靠性保障。

# 问题

## 1. 为什么Kafka不像MySQL那样允许追随者副本对外提供读服务？

1. **一致性模型差异**

- - **Kafka**：Kafka遵循的是一种分布式的、基于日志的消息传递模型。消息是顺序写入分区（Partition）的日志文件中的，消费者从分区的主副本（Leader Replica）读取消息是按照顺序进行的。如果允许追随者副本（Follower Replica）对外提供读服务，由于网络延迟、副本同步等因素，不同副本之间的数据可能存在微小的差异。在高吞吐量的消息流场景下，确保消息顺序的一致性和数据的实时性是非常重要的。
  - **MySQL**：MySQL主要用于事务处理和数据存储，它采用了ACID（原子性、一致性、隔离性、持久性）原则来保证数据的一致性。在主从复制（Master - Slave）模式下，从库（Slave）会通过二进制日志（Binlog）来同步主库（Master）的数据。从库在应用完主库的事务日志后，数据在一定程度上可以认为是与主库一致的，因此可以提供读服务。

1. **数据更新机制**

- - **Kafka**：Kafka的消息更新主要是生产者向主副本写入新消息。主副本负责管理消息的写入顺序和偏移量（Offset）等元数据。追随者副本通过从主副本拉取消息来进行同步。这个过程中，如果允许追随者副本同时对外提供读服务，当追随者副本还没有完全同步最新的消息时，就可能出现消费者读取到不一致的数据。
  - **MySQL**：MySQL的主从复制是基于事务日志的同步。主库在执行事务并写入数据的同时，会记录二进制日志。从库会不断地从主库获取并应用这些日志来更新自己的数据。一旦从库应用完相应的日志，其数据状态在逻辑上与主库是一致的，所以可以提供读服务。

1. **Kafka的设计目标**

- - Kafka主要是为了高效地处理大规模的实时消息流。它的重点是确保消息的快速写入和顺序读取。如果允许追随者副本提供读服务，可能会引入额外的复杂性，如读取的负载均衡、数据一致性的验证等。
  - 相比之下，MySQL的设计目标包括支持复杂的事务处理和多种查询操作。允许从库提供读服务可以分担主库的负载，提高系统的整体性能，特别是在读写比例较高的应用场景中。

1. **故障恢复和数据同步的复杂性**

- - **Kafka**：在Kafka中，当主副本出现故障时，会从追随者副本中选举出一个新的主副本。如果追随者副本同时在提供读服务，那么在故障恢复过程中，需要考虑如何处理正在进行的读操作，以及如何保证新主副本的数据一致性。这会增加系统的复杂性和潜在的风险。
  - **MySQL**：MySQL在主从复制模式下，从库的故障恢复相对来说比较简单。从库可以重新从主库获取二进制日志来同步数据。而且在正常运行时，主从之间的数据同步机制比较成熟，能够保证从库在提供读服务时的数据质量。

## 2. Kafka如何保证消息顺序性

1. 分区有序：Kafka的每个topic有多个分区，每个分区内的消息是有序的（按顺序追加写）。如需全局有序，需要把消息发布到指定单个分区中。
2. 同步发送：配置消息发送确认模式acks=all，保证消息被写入到ISR（In-Sync Replicas）之后，才会被认为消息发送成功。牺牲了吞吐量，保证了消息持久性和顺序性。

1. 1. acks参数：

1. 1. 1. acks = 0， 最不可靠的设置项，不会等待集群的确认，生产者会立即认为消息发送成功
      2. acks = 1，等待分区的主副本（Leader Replica）的确认（成功接受并写入消息）。相对可靠，可能主副本成功接收消息后，还没来得及将消息同步到其他副本（Follower Replica）就发生故障，那么消息可能会丢失。
      3. acks = all， 等待所有同步副本 - ISR 的确认。最可靠。

1. 消息偏移量（offsets）：kafka中的每个消息都有唯一的偏移量，其在分区内是连续递增的。消费者维护该偏移量来记录消费进度，并按照偏移量来消费，保证消费顺序。

## 3. Kafka中的消息如何存储

消息是以优化后的日志格式存储在磁盘上，主题由多个分区组成，分区是一个有序的，不可变的消息序列，使用Log Segments进行管理。

- 每个分区由多个Log Segments组成
- 每个Log Segment包含一个.log文件用于存储消息数据，以及一个可选的.index文件用于快速查找消息

- - log文件存储消息内容
  - index文件存储索引，方便快速查找消息





# 参考

## 参数设置

`auto.create.topics.enable`参数我建议最好设置成false，即不允许自动创建Topic。在我们的线上环境里面有很多名字稀奇古怪的Topic，我想大概都是因为该参数被设置成了true的缘故。

你可能有这样的经历，要为名为test的Topic发送事件，但是不小心拼写错误了，把test写成了tst，之后启动了生产者程序。恭喜你，一个名为tst的Topic就被自动创建了。

所以我一直相信好的运维应该防止这种情形的发生，特别是对于那些大公司而言，每个部门被分配的Topic应该由运维严格把控，决不能允许自行创建任何Topic。

第二个参数`unclean.leader.election.enable`是关闭Unclean Leader选举的。何谓Unclean？还记得Kafka有多个副本这件事吗？每个分区都有多个副本来提供高可用。在这些副本中只能有一个副本对外提供服务，即所谓的Leader副本。

那么问题来了，这些副本都有资格竞争Leader吗？显然不是，只有保存数据比较多的那些副本才有资格竞选，那些落后进度太多的副本没资格做这件事。

好了，现在出现这种情况了：假设那些保存数据比较多的副本都挂了怎么办？我们还要不要进行Leader选举了？此时这个参数就派上用场了。

如果设置成false，那么就坚持之前的原则，坚决不能让那些落后太多的副本竞选Leader。这样做的后果是这个分区就不可用了，因为没有Leader了。反之如果是true，那么Kafka允许你从那些“跑得慢”的副本中选一个出来当Leader。这样做的后果是数据有可能就丢失了，因为这些副本保存的数据本来就不全，当了Leader之后它本人就变得膨胀了，认为自己的数据才是权威的。

这个参数在最新版的Kafka中默认就是false，本来不需要我特意提的，但是比较搞笑的是社区对这个参数的默认值来来回回改了好几版了，鉴于我不知道你用的是哪个版本的Kafka，所以建议你还是显式地把它设置成false吧。

第三个参数`auto.leader.rebalance.enable`的影响貌似没什么人提，但其实对生产环境影响非常大。设置它的值为true表示允许Kafka定期地对一些Topic分区进行Leader重选举，当然这个重选举不是无脑进行的，它要满足一定的条件才会发生。严格来说它与上一个参数中Leader选举的最大不同在于，它不是选Leader，而是换Leader！比如Leader A一直表现得很好，但若`auto.leader.rebalance.enable=true`，那么有可能一段时间后Leader A就要被强行卸任换成Leader B。

你要知道换一次Leader代价很高的，原本向A发送请求的所有客户端都要切换成向B发送请求，而且这种换Leader本质上没有任何性能收益，因此我建议你在生产环境中把这个参数设置成false。
