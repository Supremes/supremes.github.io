---
title: MySQL 面试导航
date: 2026-08-09
tags:
  - MySQL
  - 数据库
  - 面试
---
MySQL 复习先抓高频场景，再回到原理与日志；系统表只在排障时查，不适合作为第一轮主线。

# 阅读顺序

## P0（先看，能直接应对面试）

1. [MySQL 高频场景与排查](./mysql-高频场景与排查.md)
   - 索引失效、EXPLAIN、MVCC / 锁、慢 SQL、主从复制、分页优化
2. [MySQL 核心原理笔记](./mysql核心原理笔记.md)
   - 架构、事务、B+ 树、MVCC、锁的底层逻辑

## P1（补强）

3. [MySQL 日志系统](./mysql-日志.md)
   - redo log、binlog、undo log、两阶段提交、崩溃恢复

## 参考资料（按需查）

4. [MySQL 系统表速查（参考）](./mysql-系统表速查.md)
   - INFORMATION_SCHEMA、performance_schema、sys、mysql

# 口述 Checklist

- 能先说清楚：慢 SQL 优先看慢日志和 `EXPLAIN`，不是一上来就“加索引”。
- 能解释联合索引最左前缀、范围条件后的列为什么容易失效。
- 能区分回表、覆盖索引、索引下推（ICP）。
- 能解释 `EXPLAIN` 里的 `type`、`rows`、`key`、`Extra`。
- 能说清 MVCC = `undo log + Read View`，普通 `SELECT` 是快照读。
- 能说清当前读会配合记录锁 / 间隙锁 / next-key lock。
- 能解释大分页为什么慢，以及为什么要改成 seek / 游标分页。
- 能说清主从复制链路：`binlog -> relay log -> replica apply`。
- 能指出异步复制的问题：复制延迟、主从切换丢数据窗口、读写一致性问题。
