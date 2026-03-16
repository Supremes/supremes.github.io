---
title: MySQL
tags:
  - MySQL
categories:
  - 面试
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/covers/MySQL%E5%AF%BC%E8%88%AA.webp
sticky:
hidden: false
updated: 2025-12-28 22:03
abbrlink: c24675b4
date: 2025-12-28 21:48:34
---
# 本站 MySQL 导航

建议阅读顺序：架构 → 日志系统 → 事务隔离/MVCC → 索引 → 锁 → 系统表速查。

- [[MySQL核心原理笔记#MySQL 架构 | 架构与执行流程]]：连接器/分析器/优化器/执行器
- [[MySQL-日志]]：redo/bin/undo、WAL、刷盘与崩溃恢复
- [[MySQL核心原理笔记#事务隔离|事务隔离与 MVCC]]：隔离级别、脏读/不可重复读/幻读、快照读/当前读
- [[MySQL核心原理笔记#索引|索引]]：B+树、回表/覆盖、联合索引、最左前缀、索引下推
- [[MySQL核心原理笔记#锁|锁]]：全局锁/表锁/行锁、死锁检测、MDL
- [[MySQL - 表单]]：INFORMATION_SCHEMA 等系统表速查