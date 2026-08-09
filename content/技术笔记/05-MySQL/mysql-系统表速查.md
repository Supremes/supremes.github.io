---
title: MySQL 系统表与诊断视图速查
date: 2026-08-09
tags:
  - MySQL
  - 元数据
  - 参考资料
---
> 这是一份查表用参考，不建议作为首轮复习主线。面试主线请先看 [MySQL 面试导航](./mysql.md) 与 [MySQL 高频场景与排查](./mysql-高频场景与排查.md)。

# 一、先记四个系统库

| 系统库 | 作用 | 典型用途 |
| --- | --- | --- |
| `information_schema` | 元数据 | 查库、表、列、索引、约束、表大小 |
| `performance_schema` | 运行时性能数据 | 查慢 SQL、等待事件、锁等待、线程、I/O |
| `sys` | 对 `performance_schema` 的友好视图封装 | 快速看 Top SQL、表统计、锁等待 |
| `mysql` | 账户、权限、复制等系统信息 | 用户权限、复制元信息、系统配置 |

# 二、最常用的系统表

## 2.1 `information_schema`

### `TABLES`

查表引擎、行数估算、数据大小、索引大小。

```sql
SELECT
  table_schema,
  table_name,
  engine,
  table_rows,
  data_length,
  index_length
FROM information_schema.tables
WHERE table_schema = 'your_db';
```

### `COLUMNS`

查字段类型、是否可空、默认值、注释。

```sql
SELECT
  table_name,
  column_name,
  column_type,
  is_nullable,
  column_default,
  column_comment
FROM information_schema.columns
WHERE table_schema = 'your_db'
  AND table_name = 'your_table';
```

### `STATISTICS`

查索引列顺序、基数、是否唯一。

```sql
SELECT
  index_name,
  seq_in_index,
  column_name,
  non_unique,
  cardinality
FROM information_schema.statistics
WHERE table_schema = 'your_db'
  AND table_name = 'your_table'
ORDER BY index_name, seq_in_index;
```

### `TABLE_CONSTRAINTS` / `KEY_COLUMN_USAGE`

查主键、唯一约束、外键。

```sql
SELECT
  tc.constraint_name,
  tc.constraint_type,
  kcu.column_name,
  kcu.referenced_table_name,
  kcu.referenced_column_name
FROM information_schema.table_constraints tc
LEFT JOIN information_schema.key_column_usage kcu
  ON tc.constraint_schema = kcu.constraint_schema
 AND tc.table_name = kcu.table_name
 AND tc.constraint_name = kcu.constraint_name
WHERE tc.table_schema = 'your_db'
  AND tc.table_name = 'your_table';
```

## 2.2 `performance_schema`

### `events_statements_summary_by_digest`

聚合后的 SQL 模板统计，查 Top SQL 最常用。

```sql
SELECT
  digest_text,
  count_star,
  avg_timer_wait / 1000000000000 AS avg_seconds,
  sum_rows_examined,
  sum_rows_sent
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_timer_wait DESC
LIMIT 10;
```

### `data_locks` / `data_lock_waits`

MySQL 8 常用的锁排查入口。

```sql
SELECT *
FROM performance_schema.data_locks;

SELECT *
FROM performance_schema.data_lock_waits;
```

### `threads`

查线程、连接、后台任务。

```sql
SELECT thread_id, processlist_id, processlist_user, processlist_db, processlist_command
FROM performance_schema.threads;
```

## 2.3 `sys`

### `statement_analysis`

按可读方式看 SQL 聚合统计。

```sql
SELECT
  query,
  exec_count,
  avg_latency,
  rows_examined,
  rows_sent
FROM sys.statement_analysis
ORDER BY avg_latency DESC
LIMIT 10;
```

### `schema_table_statistics`

看表读写压力。

```sql
SELECT
  table_schema,
  table_name,
  rows_fetched,
  rows_inserted,
  rows_updated,
  rows_deleted
FROM sys.schema_table_statistics
WHERE table_schema = 'your_db'
ORDER BY rows_fetched DESC;
```

### `innodb_lock_waits`

快速看谁阻塞了谁。

```sql
SELECT *
FROM sys.innodb_lock_waits;
```

## 2.4 `mysql`

### `user`

查账户、认证插件、权限入口。

```sql
SELECT user, host, plugin, account_locked
FROM mysql.user;
```

### 常见复制相关表（视版本而定）

- `slave_master_info`
- `slave_relay_log_info`
- `slave_worker_info`

> 新版本术语通常用 replica，但很多系统表和命令仍保留旧命名。

# 三、排障时最常抄的几段 SQL

## 3.1 查单表大小

```sql
SELECT
  table_schema,
  table_name,
  ROUND((data_length + index_length) / 1024 / 1024, 2) AS size_mb
FROM information_schema.tables
WHERE table_schema = 'your_db'
ORDER BY size_mb DESC;
```

## 3.2 查某表索引是否合理

```sql
SELECT
  index_name,
  seq_in_index,
  column_name,
  cardinality,
  non_unique
FROM information_schema.statistics
WHERE table_schema = 'your_db'
  AND table_name = 'your_table'
ORDER BY index_name, seq_in_index;
```

## 3.3 查最慢 SQL 模板

```sql
SELECT
  digest_text,
  count_star,
  avg_timer_wait / 1000000000000 AS avg_seconds,
  sum_rows_examined
FROM performance_schema.events_statements_summary_by_digest
ORDER BY avg_timer_wait DESC
LIMIT 20;
```

## 3.4 查锁等待

```sql
SELECT *
FROM sys.innodb_lock_waits;
```

# 四、使用提醒

- `information_schema.tables.table_rows` 对 InnoDB 往往是估算值，不要当精确行数。
- `performance_schema` 适合做性能排查，但前提是相关采集已开启。
- `sys` 本质是视图，适合快速看结论；需要深挖时回到 `performance_schema`。
- 老资料里常见 `INNODB_LOCKS`、`INNODB_LOCK_WAITS`，MySQL 8 更建议看 `performance_schema.data_locks`。
