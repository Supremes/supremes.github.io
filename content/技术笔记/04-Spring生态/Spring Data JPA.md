---
title: Spring Data JPA
updated: 2026-08-09 18:05
tags:
  - Spring
  - 面试
  - JPA
---
## 一句话结论

Spring Data JPA 不是替代 JPA，而是在 `EntityManager` 之上提供 Repository 抽象，把大量样板 CRUD 和查询模板收敛掉。

## 30 秒口述

JPA 负责 ORM 规范，Hibernate 常是具体实现；Spring Data JPA 再往上包一层 Repository，让你通过接口声明就能拿到增删改查、分页和排序能力。简单查询可以靠方法名派生，复杂查询用 `@Query`，动态条件常配 `Specification` 或 QueryDSL。

## 关键机制

### 1. 三种常见查询方式

- **方法名派生**：适合简单条件查询。
  ```java
  List<User> findByNameAndAge(String name, Integer age);
  ```
- **`@Query`**：适合复杂 JPQL / 原生 SQL。
  ```java
  @Query("SELECT u FROM User u WHERE u.age BETWEEN :min AND :max AND u.name LIKE %:name%")
  List<User> searchUsers(@Param("min") int min, @Param("max") int max, @Param("name") String name);
  ```
- **`Specification` / QueryDSL**：适合动态拼条件。
  ```java
  Page<User> findAll(Specification<User> spec, Pageable pageable);
  ```

### 2. Repository 的价值

- 降低模板代码量。
- 自带分页、排序、审计等常用能力。
- 和 Spring 事务体系天然集成。

### 3. JPA 不是“写 SQL 越少越高级”

- 复杂查询依然要关注生成的 SQL。
- 面试里主动提 `N+1`、懒加载、分页性能，往往比只背注解更加分。

## 常见追问 / 坑

- **`save()` 是插入还是更新**：取决于实体状态和主键情况，不是看到 `save` 就等于 insert。
- **N+1 问题**：关联对象逐条懒加载时很常见，要结合抓取策略、`join fetch`、批量查询一起治理。
- **`LazyInitializationException`**：脱离持久化上下文后再访问懒加载字段容易出现。
- **分页和排序要不要下推到数据库**：要，别先全量查出来再在内存里切页。
- **大批量写入**：注意 `flush` / `clear` 节奏，不要让持久化上下文无限膨胀。

## 面试答题顺序建议

1. 先讲“JPA 是规范，Spring Data JPA 是 Repository 抽象”。
2. 再讲三种查询方式。
3. 最后补 `N+1`、懒加载、分页这些实战坑。

## 延伸阅读

- [Spring AOP 与声明式事务](./Spring AOP 与声明式事务.md)
