---
updated: 2026-06-06 22:59
title: Spring Data Jpa
---
Spring Data Jpa 是一个 spring 中强大的 orm 库，这里介绍几个它提供的强大功能.

# 1. 方法名派生查询

Spring Data JPA 会解析方法名，按照约定生成对应的 JPQL/SQL 查询。比如，select 查询的规则是：
```
find + [条件] + [排序/分页]
```

- 简单查询用派生
	```java
	List<User> findByNameAndAge(String name, Integer age);
	```
- 复杂查询用@Query
	```java
	@Query("SELECT u FROM User u WHERE u.age BETWEEN :min AND :max AND u.name LIKE %:name%")
 	List<User> searchUsers(@Param("min") int min, @Param("max") int max, @Param("name") String name);
 
	```

- 动态条件用 Specification 或 QueryDSL
```
Page<User> findAll(Specification<User> spec, Pageable pageable);
```