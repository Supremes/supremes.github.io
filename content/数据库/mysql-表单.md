---
title: MySQL - 表单
date: 2025-12-10
tags:
  - MySQL
  - database
---
# MySQL 表单概述

MySQL 提供了多种系统预定义的数据库和表单，用于存储元数据、管理权限、记录性能信息等。这些系统表单是 MySQL 数据库管理系统的核心组成部分。

---

# INFORMATION_SCHEMA

`INFORMATION_SCHEMA` 是 MySQL 和 PostgreSQL 中用于定义数据库元数据的标准数据库。它提供了对数据库结构信息的只读访问。

## 常用表单

### 1. SCHEMATA
存储所有数据库（schema）的信息。

```sql
SELECT * FROM INFORMATION_SCHEMA.SCHEMATA;
```

**主要字段：**
- `CATALOG_NAME`: 目录名称
- `SCHEMA_NAME`: 数据库名称
- `DEFAULT_CHARACTER_SET_NAME`: 默认字符集
- `DEFAULT_COLLATION_NAME`: 默认排序规则

### 2. TABLES
存储所有表的元数据信息。

```sql
SELECT TABLE_NAME, TABLE_TYPE, ENGINE, TABLE_ROWS 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_SCHEMA = 'your_database';
```

**主要字段：**
- `TABLE_CATALOG`: 目录名
- `TABLE_SCHEMA`: 数据库名
- `TABLE_NAME`: 表名
- `TABLE_TYPE`: 表类型（BASE TABLE, VIEW, SYSTEM VIEW）
- `ENGINE`: 存储引擎（InnoDB, MyISAM 等）
- `VERSION`: 表版本
- `ROW_FORMAT`: 行格式
- `TABLE_ROWS`: 表中的行数（估计值）
- `AVG_ROW_LENGTH`: 平均行长度
- `DATA_LENGTH`: 数据文件大小
- `INDEX_LENGTH`: 索引文件大小
- `AUTO_INCREMENT`: 自增值
- `CREATE_TIME`: 创建时间
- `UPDATE_TIME`: 更新时间
- `TABLE_COLLATION`: 表的排序规则

### 3. COLUMNS
存储所有列的详细信息。

```sql
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_KEY 
FROM INFORMATION_SCHEMA.COLUMNS 
WHERE TABLE_SCHEMA = 'your_database' 
  AND TABLE_NAME = 'your_table';
```

**主要字段：**
- `TABLE_SCHEMA`: 数据库名
- `TABLE_NAME`: 表名
- `COLUMN_NAME`: 列名
- `ORDINAL_POSITION`: 列的位置
- `COLUMN_DEFAULT`: 默认值
- `IS_NULLABLE`: 是否可为 NULL
- `DATA_TYPE`: 数据类型
- `CHARACTER_MAXIMUM_LENGTH`: 字符最大长度
- `NUMERIC_PRECISION`: 数字精度
- `NUMERIC_SCALE`: 数字小数位数
- `COLUMN_TYPE`: 完整的列类型
- `COLUMN_KEY`: 键类型（PRI, UNI, MUL）
- `EXTRA`: 额外信息（auto_increment 等）
- `COLUMN_COMMENT`: 列注释

### 4. STATISTICS
存储表索引的统计信息。

```sql
SELECT INDEX_NAME, COLUMN_NAME, SEQ_IN_INDEX, NON_UNIQUE 
FROM INFORMATION_SCHEMA.STATISTICS 
WHERE TABLE_SCHEMA = 'your_database' 
  AND TABLE_NAME = 'your_table';
```

**主要字段：**
- `TABLE_SCHEMA`: 数据库名
- `TABLE_NAME`: 表名
- `NON_UNIQUE`: 是否非唯一索引（0=唯一，1=非唯一）
- `INDEX_SCHEMA`: 索引所在数据库
- `INDEX_NAME`: 索引名称
- `SEQ_IN_INDEX`: 列在索引中的顺序
- `COLUMN_NAME`: 列名
- `COLLATION`: 排序方式（A=升序，D=降序）
- `CARDINALITY`: 基数（唯一值的估计数量）
- `INDEX_TYPE`: 索引类型（BTREE, HASH 等）

### 5. TABLE_CONSTRAINTS
存储表的约束信息。

```sql
SELECT CONSTRAINT_NAME, CONSTRAINT_TYPE 
FROM INFORMATION_SCHEMA.TABLE_CONSTRAINTS 
WHERE TABLE_SCHEMA = 'your_database';
```

**约束类型：**
- `PRIMARY KEY`: 主键约束
- `FOREIGN KEY`: 外键约束
- `UNIQUE`: 唯一约束
- `CHECK`: 检查约束（MySQL 8.0.16+）

### 6. KEY_COLUMN_USAGE
存储键列的使用信息。

```sql
SELECT CONSTRAINT_NAME, COLUMN_NAME, REFERENCED_TABLE_NAME, REFERENCED_COLUMN_NAME 
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
WHERE TABLE_SCHEMA = 'your_database' 
  AND TABLE_NAME = 'your_table';
```

### 7. REFERENTIAL_CONSTRAINTS
存储外键引用约束的信息。

```sql
SELECT CONSTRAINT_NAME, UNIQUE_CONSTRAINT_NAME, UPDATE_RULE, DELETE_RULE 
FROM INFORMATION_SCHEMA.REFERENTIAL_CONSTRAINTS 
WHERE CONSTRAINT_SCHEMA = 'your_database';
```

### 8. VIEWS
存储所有视图的定义信息。

```sql
SELECT TABLE_NAME, VIEW_DEFINITION, CHECK_OPTION, IS_UPDATABLE 
FROM INFORMATION_SCHEMA.VIEWS 
WHERE TABLE_SCHEMA = 'your_database';
```

### 9. TRIGGERS
存储触发器的信息。

```sql
SELECT TRIGGER_NAME, EVENT_MANIPULATION, EVENT_OBJECT_TABLE, ACTION_TIMING 
FROM INFORMATION_SCHEMA.TRIGGERS 
WHERE TRIGGER_SCHEMA = 'your_database';
```

**主要字段：**
- `TRIGGER_NAME`: 触发器名称
- `EVENT_MANIPULATION`: 触发事件（INSERT, UPDATE, DELETE）
- `EVENT_OBJECT_TABLE`: 触发器所在的表
- `ACTION_TIMING`: 触发时机（BEFORE, AFTER）
- `ACTION_STATEMENT`: 触发器执行的 SQL 语句

### 10. ROUTINES
存储存储过程和函数的信息。

```sql
SELECT ROUTINE_NAME, ROUTINE_TYPE, DTD_IDENTIFIER 
FROM INFORMATION_SCHEMA.ROUTINES 
WHERE ROUTINE_SCHEMA = 'your_database';
```

**主要字段：**
- `ROUTINE_NAME`: 过程/函数名称
- `ROUTINE_TYPE`: 类型（PROCEDURE, FUNCTION）
- `DTD_IDENTIFIER`: 返回值类型（函数）
- `ROUTINE_DEFINITION`: 过程/函数的定义

### 11. PARTITIONS
存储分区表的信息。

```sql
SELECT TABLE_NAME, PARTITION_NAME, PARTITION_METHOD, PARTITION_EXPRESSION 
FROM INFORMATION_SCHEMA.PARTITIONS 
WHERE TABLE_SCHEMA = 'your_database';
```

### 12. PROCESSLIST
显示当前正在执行的线程信息。

```sql
SELECT ID, USER, HOST, DB, COMMAND, TIME, STATE, INFO 
FROM INFORMATION_SCHEMA.PROCESSLIST;
```

### 13. CHARACTER_SETS
列出所有可用的字符集。

```sql
SELECT CHARACTER_SET_NAME, DEFAULT_COLLATE_NAME, DESCRIPTION 
FROM INFORMATION_SCHEMA.CHARACTER_SETS;
```

### 14. COLLATIONS
列出所有可用的排序规则。

```sql
SELECT COLLATION_NAME, CHARACTER_SET_NAME, IS_DEFAULT 
FROM INFORMATION_SCHEMA.COLLATIONS;
```

### 15. ENGINES
列出所有可用的存储引擎。

```sql
SELECT ENGINE, SUPPORT, COMMENT, TRANSACTIONS, XA, SAVEPOINTS 
FROM INFORMATION_SCHEMA.ENGINES;
```

**支持状态：**
- `YES`: 支持并已启用
- `DEFAULT`: 默认引擎
- `NO`: 不支持
- `DISABLED`: 已编译但未启用

---

# mysql 系统数据库

`mysql` 数据库是 MySQL 服务器的核心系统数据库，存储了用户账户、权限、插件、时区等重要信息。

## 主要表单

### 1. user
存储用户账户、权限和认证信息。

```sql
SELECT User, Host, authentication_string 
FROM mysql.user;
```

**主要字段：**
- `Host`: 主机名或 IP
- `User`: 用户名
- `authentication_string`: 加密后的密码
- `plugin`: 认证插件
- 各种权限字段：`Select_priv`, `Insert_priv`, `Update_priv`, `Delete_priv` 等

### 2. db
存储数据库级别的权限。

```sql
SELECT Host, Db, User, Select_priv, Insert_priv 
FROM mysql.db;
```

### 3. tables_priv
存储表级别的权限。

```sql
SELECT Host, Db, User, Table_name, Table_priv 
FROM mysql.tables_priv;
```

### 4. columns_priv
存储列级别的权限。

```sql
SELECT Host, Db, User, Table_name, Column_name, Column_priv 
FROM mysql.columns_priv;
```

### 5. procs_priv
存储存储过程和函数的权限。

```sql
SELECT Host, Db, User, Routine_name, Routine_type, Proc_priv 
FROM mysql.procs_priv;
```

### 6. proxies_priv
存储代理用户的权限。

```sql
SELECT Host, User, Proxied_host, Proxied_user 
FROM mysql.proxies_priv;
```

### 7. time_zone 相关表
用于存储时区信息：
- `time_zone`: 时区定义
- `time_zone_name`: 时区名称
- `time_zone_transition`: 时区转换规则
- `time_zone_transition_type`: 时区转换类型

### 8. plugin
存储服务器插件信息。

```sql
SELECT name, dl 
FROM mysql.plugin;
```

### 9. servers
存储 FEDERATED 存储引擎使用的服务器连接信息。

### 10. help 相关表
用于存储 MySQL 帮助文档：
- `help_topic`: 帮助主题
- `help_category`: 帮助分类
- `help_relation`: 帮助关系
- `help_keyword`: 帮助关键字

---

# performance_schema

`performance_schema` 是 MySQL 的性能监控数据库，提供了运行时性能数据的低级别访问。

## 主要表单类别

### 1. 当前事件表
记录当前正在执行的事件。

```sql
-- 当前等待事件
SELECT * FROM performance_schema.events_waits_current;

-- 当前语句事件
SELECT * FROM performance_schema.events_statements_current;

-- 当前阶段事件
SELECT * FROM performance_schema.events_stages_current;

-- 当前事务事件
SELECT * FROM performance_schema.events_transactions_current;
```

### 2. 历史事件表
记录最近完成的事件。

```sql
-- 等待事件历史
SELECT * FROM performance_schema.events_waits_history;

-- 语句事件历史
SELECT * FROM performance_schema.events_statements_history;

-- 阶段事件历史
SELECT * FROM performance_schema.events_stages_history;
```

### 3. 汇总表
提供各种维度的性能统计汇总。

```sql
-- 按账户汇总的语句统计
SELECT * FROM performance_schema.events_statements_summary_by_account_by_event_name;

-- 按主机汇总的语句统计
SELECT * FROM performance_schema.events_statements_summary_by_host_by_event_name;

-- 按用户汇总的语句统计
SELECT * FROM performance_schema.events_statements_summary_by_user_by_event_name;

-- 按线程汇总的语句统计
SELECT * FROM performance_schema.events_statements_summary_by_thread_by_event_name;

-- 全局语句统计
SELECT * FROM performance_schema.events_statements_summary_global_by_event_name;
```

### 4. 连接和会话表

```sql
-- 当前连接
SELECT * FROM performance_schema.threads;

-- 账户信息
SELECT * FROM performance_schema.accounts;

-- 主机信息
SELECT * FROM performance_schema.hosts;

-- 用户信息
SELECT * FROM performance_schema.users;

-- 会话连接属性
SELECT * FROM performance_schema.session_connect_attrs;
```

### 5. 锁相关表

```sql
-- 数据锁等待
SELECT * FROM performance_schema.data_lock_waits;

-- 数据锁
SELECT * FROM performance_schema.data_locks;

-- 元数据锁
SELECT * FROM performance_schema.metadata_locks;

-- 表锁等待
SELECT * FROM performance_schema.table_handles;
```

### 6. 文件 I/O 表

```sql
-- 文件实例
SELECT * FROM performance_schema.file_instances;

-- 按文件汇总的 I/O 统计
SELECT * FROM performance_schema.file_summary_by_instance;

-- 按事件名汇总的 I/O 统计
SELECT * FROM performance_schema.file_summary_by_event_name;
```

### 7. 表和索引 I/O 表

```sql
-- 表 I/O 等待统计
SELECT * FROM performance_schema.table_io_waits_summary_by_table;

-- 表锁等待统计
SELECT * FROM performance_schema.table_lock_waits_summary_by_table;

-- 索引 I/O 统计
SELECT * FROM performance_schema.table_io_waits_summary_by_index_usage;
```

### 8. 内存使用表

```sql
-- 按线程汇总的内存使用
SELECT * FROM performance_schema.memory_summary_by_thread_by_event_name;

-- 按账户汇总的内存使用
SELECT * FROM performance_schema.memory_summary_by_account_by_event_name;

-- 全局内存使用
SELECT * FROM performance_schema.memory_summary_global_by_event_name;
```

### 9. 复制相关表

```sql
-- 复制连接配置
SELECT * FROM performance_schema.replication_connection_configuration;

-- 复制连接状态
SELECT * FROM performance_schema.replication_connection_status;

-- 复制应用器配置
SELECT * FROM performance_schema.replication_applier_configuration;

-- 复制应用器状态
SELECT * FROM performance_schema.replication_applier_status;
```

### 10. 准备语句表

```sql
-- 准备语句实例
SELECT * FROM performance_schema.prepared_statements_instances;
```

### 11. 设置和配置表

```sql
-- 全局变量
SELECT * FROM performance_schema.global_variables;

-- 会话变量
SELECT * FROM performance_schema.session_variables;

-- 全局状态
SELECT * FROM performance_schema.global_status;

-- 会话状态
SELECT * FROM performance_schema.session_status;

-- 设置表
SELECT * FROM performance_schema.setup_actors;
SELECT * FROM performance_schema.setup_consumers;
SELECT * FROM performance_schema.setup_instruments;
SELECT * FROM performance_schema.setup_objects;
SELECT * FROM performance_schema.setup_threads;
```

---

# sys 数据库

`sys` 数据库是基于 `performance_schema` 和 `INFORMATION_SCHEMA` 构建的视图集合，提供了更易读的性能和诊断信息。

## 常用视图

### 1. 会话和连接

```sql
-- 当前会话
SELECT * FROM sys.session;

-- 按用户分组的会话
SELECT * FROM sys.user_summary;

-- 按主机分组的会话
SELECT * FROM sys.host_summary;

-- 当前进程列表
SELECT * FROM sys.processlist;
```

### 2. 语句分析

```sql
-- 执行最慢的语句
SELECT * FROM sys.statements_with_runtimes_in_95th_percentile;

-- 执行次数最多的语句
SELECT * FROM sys.statement_analysis;

-- 全表扫描的语句
SELECT * FROM sys.statements_with_full_table_scans;

-- 产生临时表的语句
SELECT * FROM sys.statements_with_temp_tables;

-- 按错误排序的语句
SELECT * FROM sys.statements_with_errors_or_warnings;
```

### 3. 表和索引

```sql
-- 未使用的索引
SELECT * FROM sys.schema_unused_indexes;

-- 冗余索引
SELECT * FROM sys.schema_redundant_indexes;

-- 表统计信息
SELECT * FROM sys.schema_table_statistics;

-- 按 I/O 排序的表
SELECT * FROM sys.schema_tables_with_full_table_scans;

-- 自增使用情况
SELECT * FROM sys.schema_auto_increment_columns;
```

### 4. I/O 分析

```sql
-- 按文件排序的 I/O
SELECT * FROM sys.io_global_by_file_by_bytes;

-- 按表排序的 I/O
SELECT * FROM sys.io_global_by_file_by_latency;

-- 等待时间最长的 I/O
SELECT * FROM sys.io_by_thread_by_latency;
```

### 5. 锁分析

```sql
-- 等待的元数据锁
SELECT * FROM sys.schema_table_lock_waits;

-- InnoDB 锁等待
SELECT * FROM sys.innodb_lock_waits;
```

### 6. 内存使用

```sql
-- 全局内存使用
SELECT * FROM sys.memory_global_total;

-- 按线程的内存使用
SELECT * FROM sys.memory_by_thread_by_current_bytes;

-- 按用户的内存使用
SELECT * FROM sys.memory_by_user_by_current_bytes;

-- 按主机的内存使用
SELECT * FROM sys.memory_by_host_by_current_bytes;
```

### 7. 数据库对象

```sql
-- 存储过程
SELECT * FROM sys.schema_object_overview;
```

---

# 关键字和保留字

MySQL 中有许多保留字，不能直接用作表名、列名等标识符，除非使用反引号 `` ` `` 包围。

## 常见保留字

### DDL 相关
- `CREATE`, `ALTER`, `DROP`, `TRUNCATE`, `RENAME`
- `TABLE`, `DATABASE`, `SCHEMA`, `INDEX`, `VIEW`, `TRIGGER`, `PROCEDURE`, `FUNCTION`
- `ADD`, `MODIFY`, `CHANGE`, `COLUMN`
- `PRIMARY`, `FOREIGN`, `UNIQUE`, `KEY`, `CONSTRAINT`
- `REFERENCES`, `CHECK`, `DEFAULT`

### DML 相关
- `SELECT`, `INSERT`, `UPDATE`, `DELETE`
- `FROM`, `WHERE`, `JOIN`, `ON`, `USING`
- `GROUP`, `HAVING`, `ORDER`, `LIMIT`, `OFFSET`
- `AS`, `DISTINCT`, `ALL`
- `VALUES`, `SET`

### 数据类型
- `INT`, `INTEGER`, `BIGINT`, `SMALLINT`, `TINYINT`
- `DECIMAL`, `NUMERIC`, `FLOAT`, `DOUBLE`, `REAL`
- `CHAR`, `VARCHAR`, `TEXT`, `BLOB`
- `DATE`, `TIME`, `DATETIME`, `TIMESTAMP`, `YEAR`
- `BOOLEAN`, `BOOL`
- `JSON`, `ENUM`, `SET`

### 逻辑和比较
- `AND`, `OR`, `NOT`, `XOR`
- `IN`, `NOT IN`, `EXISTS`, `NOT EXISTS`
- `BETWEEN`, `LIKE`, `REGEXP`, `RLIKE`
- `IS`, `NULL`, `TRUE`, `FALSE`
- `CASE`, `WHEN`, `THEN`, `ELSE`, `END`

### 连接类型
- `INNER`, `LEFT`, `RIGHT`, `OUTER`, `CROSS`
- `NATURAL`, `STRAIGHT_JOIN`

### 函数和聚合
- `COUNT`, `SUM`, `AVG`, `MAX`, `MIN`
- `CONCAT`, `SUBSTRING`, `LENGTH`
- `NOW`, `CURDATE`, `CURTIME`
- `CAST`, `CONVERT`

### 约束和修饰符
- `NOT NULL`, `AUTO_INCREMENT`
- `UNSIGNED`, `ZEROFILL`
- `BINARY`, `CHARACTER SET`, `COLLATE`
- `COMMENT`

### 事务相关
- `BEGIN`, `START`, `COMMIT`, `ROLLBACK`, `SAVEPOINT`
- `TRANSACTION`, `ISOLATION`, `LEVEL`
- `READ`, `WRITE`, `ONLY`
- `LOCK`, `UNLOCK`, `TABLES`

### 权限相关
- `GRANT`, `REVOKE`, `DENY`
- `USAGE`, `ALL`, `PRIVILEGES`
- `IDENTIFIED`, `BY`, `PASSWORD`
- `WITH`, `OPTION`

### 其他重要关键字
- `USE`, `SHOW`, `DESCRIBE`, `DESC`, `EXPLAIN`
- `IF`, `ELSEIF`, `LOOP`, `WHILE`, `REPEAT`
- `DECLARE`, `CURSOR`, `FETCH`, `OPEN`, `CLOSE`
- `TEMPORARY`, `GLOBAL`, `SESSION`, `LOCAL`
- `PARTITION`, `SUBPARTITION`
- `ENGINE`, `CHARSET`, `COLLATION`

## 使用保留字作为标识符

如果必须使用保留字作为标识符，需要用反引号包围：

```sql
-- 错误：order 是保留字
CREATE TABLE order (
    id INT PRIMARY KEY
);

-- 正确：使用反引号
CREATE TABLE `order` (
    id INT PRIMARY KEY,
    `select` VARCHAR(50),  -- select 也是保留字
    `from` VARCHAR(50)     -- from 也是保留字
);
```

---

# 实用查询示例

## 查看数据库大小

```sql
SELECT 
    table_schema AS '数据库',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS '大小(MB)'
FROM information_schema.tables
GROUP BY table_schema;
```

## 查看表大小

```sql
SELECT 
    table_name AS '表名',
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS '大小(MB)',
    table_rows AS '行数'
FROM information_schema.tables
WHERE table_schema = 'your_database'
ORDER BY (data_length + index_length) DESC;
```

## 查找没有主键的表

```sql
SELECT t.table_schema, t.table_name
FROM information_schema.tables t
LEFT JOIN information_schema.table_constraints tc
    ON t.table_schema = tc.table_schema
    AND t.table_name = tc.table_name
    AND tc.constraint_type = 'PRIMARY KEY'
WHERE t.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
    AND t.table_type = 'BASE TABLE'
    AND tc.constraint_name IS NULL;
```

## 查找重复索引

```sql
SELECT 
    a.table_schema AS '数据库',
    a.table_name AS '表名',
    a.index_name AS '索引1',
    b.index_name AS '索引2',
    GROUP_CONCAT(a.column_name ORDER BY a.seq_in_index) AS '列'
FROM information_schema.statistics a
JOIN information_schema.statistics b
    ON a.table_schema = b.table_schema
    AND a.table_name = b.table_name
    AND a.column_name = b.column_name
    AND a.seq_in_index = b.seq_in_index
    AND a.index_name < b.index_name
WHERE a.table_schema NOT IN ('information_schema', 'mysql', 'performance_schema', 'sys')
GROUP BY a.table_schema, a.table_name, a.index_name, b.index_name
HAVING COUNT(*) = (
    SELECT COUNT(*) 
    FROM information_schema.statistics 
    WHERE table_schema = a.table_schema 
        AND table_name = a.table_name 
        AND index_name = a.index_name
);
```

## 查看当前正在执行的查询

```sql
SELECT 
    id,
    user,
    host,
    db,
    command,
    time,
    state,
    info
FROM information_schema.processlist
WHERE command != 'Sleep'
ORDER BY time DESC;
```

## 查看表的外键关系

```sql
SELECT 
    tc.constraint_name AS '约束名',
    tc.table_name AS '表名',
    kcu.column_name AS '列名',
    rc.referenced_table_name AS '引用表',
    kcu.referenced_column_name AS '引用列',
    rc.update_rule AS '更新规则',
    rc.delete_rule AS '删除规则'
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.referential_constraints rc
    ON tc.constraint_name = rc.constraint_name
    AND tc.table_schema = rc.constraint_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'your_database';
```

---

# 最佳实践

1. **避免使用保留字**：尽量不要使用 MySQL 保留字作为表名、列名等标识符
2. **定期检查表结构**：使用 `INFORMATION_SCHEMA` 定期审查数据库结构
3. **监控性能**：利用 `performance_schema` 和 `sys` 数据库监控查询性能
4. **权限管理**：通过 `mysql` 数据库中的权限表管理用户权限
5. **索引优化**：定期检查未使用和重复的索引
6. **命名规范**：使用有意义的、一致的命名规范，避免混淆

---

# 参考资料

- [MySQL 官方文档 - INFORMATION_SCHEMA](https://dev.mysql.com/doc/refman/8.0/en/information-schema.html)
- [MySQL 官方文档 - performance_schema](https://dev.mysql.com/doc/refman/8.0/en/performance-schema.html)
- [MySQL 官方文档 - sys Schema](https://dev.mysql.com/doc/refman/8.0/en/sys-schema.html)
- [MySQL 保留字列表](https://dev.mysql.com/doc/refman/8.0/en/keywords.html)