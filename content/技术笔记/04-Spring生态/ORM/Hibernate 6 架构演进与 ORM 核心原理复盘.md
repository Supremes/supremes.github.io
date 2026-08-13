---
title: Hibernate 6 架构演进与 ORM 核心原理复盘
date: 2026-08-13
updated: 2026-08-13
tags:
  - Hibernate
  - ORM
  - JPA
  - Java
---
#### 一、核心架构：Hibernate 6 的 SQM 引擎

**背景**：Hibernate 6 引入了 **SQM (Semantic Query Model，语义查询模型)**，彻底重构了查询管道。

1. **新旧对比**：
    - **Hibernate 5**：`Criteria API -> 生成 JPQL 字符串 -> 解析 JPQL -> SQL`（效率低，逻辑绕）。
    - **Hibernate 6**：`Criteria API -> 直接构建 SQM 树 -> SQL`（效率高，统一模型）。
    
2. **SQM 的作用**：它是 Hibernate 内部的“通用语”，位于 HQL/JPQL 和 SQL 之间。它是**数据库无关的**（只认实体名和属性名，不认表名和列名）。
    
3. **解析流程**：
    
    - **JPQL/HQL**：通过 **Antlr4**​ 解析成语法树（AST），再转换为 SQM。
        
    - **Criteria API**：直接实例化 SQM 节点（`SqmRoot`, `SqmPredicate` 等），不再生成中间字符串。
        
    

#### 二、查询 API 的演进与选择

**核心结论**：`EntityManager` + JPA Criteria 是标准，`unwrap(Session.class)` 仅用于获取 Hibernate 扩展能力。

1. **`CriteriaBuilder` (JPQL/Criteria API)**：
    
    - **是什么**：面向对象的查询构建工厂，解决 SQL 字符串拼接的脆弱性和 SQL 注入问题。
        
    - **Hibernate 6 现状**：旧的 `org.hibernate.Criteria` 已被彻底删除。现在的 `HibernateCriteriaBuilder` 直接构建 SQM。
        
    - **代码建议**：
        
        ```
        // 推荐：纯 JPA 标准写法
        CriteriaBuilder cb = entityManager.getCriteriaBuilder();
        // 仅在需要 Hibernate 特有功能（如 ilike, createCountQuery）时 unwrap
        HibernateCriteriaBuilder hcb = entityManager.unwrap(Session.class).getCriteriaBuilder();
        ```
        
    
2. **JPQL vs HQL**：
    
    - **JPQL**：标准规范。`EntityManager.createQuery(...)` 传入的字符串叫 JPQL。
        
    - **HQL**：Hibernate 方言。`Session.createQuery(...)` 传入的字符串叫 HQL。
        
    - **现状**：两者语法 90% 重叠，Hibernate 6 对 HQL 校验更严格（如 `UPDATE` 语句不再支持 `FROM` 关键字）。
        
    
3. **MyBatis/MyBatis-Plus 的对应实现**：
    
    - **组件**：`Wrapper` (`LambdaQueryWrapper`)。
        
    - **原理**：**SQL 片段拼接**（而非 AST 解析）。通过 `ExpressionParser` 将 Lambda 表达式解析为字段名，再用 `StringBuilder` 拼接 SQL。
        
    - **对比**：Hibernate 像“编译器”，严谨但重；MP 像“高级编辑器”，灵活但需手动防错。
        
    

#### 三、 Hibernate 5 升级到 6 的破坏性变更清单

**重点**：这是一次涉及 Jakarta EE 迁移和内部引擎替换的大版本升级。

1. **包名切换（必须改）**：`javax.persistence.*` -> `jakarta.persistence.*`。
    
2. **API 删除（必须改）**：旧的 `org.hibernate.Criteria`、`Restrictions`、`Projections` 全部删除，强制迁移至 JPA Criteria。
    
3. **类型映射（必须改）**：废弃 `@Type(type = "json")`，改为类型安全的 `@JdbcTypeCode(SqlTypes.JSON)`。
    
4. **序列命名（高危）**：默认从 `hibernate_sequence` 改为 `<实体名>_SEQ`。建议配置 `hibernate.id.db_structure_naming_strategy=legacy` 过渡，或新建序列。
    
5. **行为变化（静默坑）**：
    
    - `DISTINCT` 语义变化：Fetch 时自动去重，且 `HINT_PASS_DISTINCT_THROUGH` 被移除。
        
    - 隐式 JOIN 返回值变化：无显式 SELECT 的 JOIN 查询，H6 只返回 FROM 根对象。
        
    - 时区存储：默认策略改变，建议显式配置 `hibernate.jdbc.time_zone=UTC`。
        
    

#### 四、 N+1 问题深度剖析

**本质**：关联数据的加载时机失控。

1. **Hibernate (高发区)**：
    
    - **原因**：`@OneToMany` 默认 `FetchType.LAZY`。当你遍历主表结果（1 次查询）并访问关联属性的 Getter 时，触发 N 次关联查询。
        
    - **解决**：
        
        - **JPQL/HQL**：使用 `JOIN FETCH` (`select a from Author a join fetch a.books`)。
            
        - **Spring Data JPA**：使用 `@EntityGraph(attributePaths = {"books"})`。
            
        - **全局优化**：使用 `@BatchSize(size = 100)` 缓解（将 N 次查询合并为几次 In 查询）。
            
        
    
2. **MyBatis (极低概率)**：
    
    - **原因**：仅在使用 `<collection select="...">`（嵌套 Select）且开启延迟加载时才会发生。
        
    - **解决**：使用 **嵌套 ResultMap + JOIN 查询**（官方推荐），一次查询搞定。
        
    

#### 五、关键概念速查表

|概念|归属|核心作用|备注|
|---|---|---|---|
|**JPA**​|规范|定义 ORM 标准接口 (`EntityManager`, `@Entity`)|类似 JDBC|
|**Hibernate**​|实现|JPA 规范的 ORM 实现引擎|类似 MySQL Connector|
|**Spring ORM**​|整合|管理 ORM Session 生命周期，统一事务|不抹平 API 差异|
|**Spring Data JPA**​|抽象|基于 Repository 模式，自动生成 DAO 实现|简化 CRUD|
|**SQM**​|Hibernate 6|内部统一的语义查询模型|取代旧解析器|
|**AST**​|编译原理|抽象语法树，Antlr4 解析 JPQL 的产物|生成 SQM 的原料|

---

**文档结尾建议添加**：

> **复盘人注**：本次对话重点澄清了 Hibernate 6 中 `unwrap` 的真实用途（获取扩展而非逃避 JPA）以及 SQM 的核心地位。在选型时，若追求强类型与领域模型完整性，选 Hibernate；若追求 SQL 灵活性与可控性，选 MyBatis/MP。

---

**纠正语法/提问方式：**

1. 提问“沉淀到腾讯文档里”——在开发语境下，建议表述为“**整理成 Markdown 文档并同步到腾讯文档**”或“**沉淀为技术 Wiki**”，更符合研发协作习惯。
    
2. 回顾全篇，你的提问质量很高，但在技术名词大小写上偶有疏漏（如 `criteriabuilder` -> `CriteriaBuilder`，`mybatis plus` -> `MyBatis-Plus`），保持大小写规范有助于提升文档的专业度。
    

**后续建议：**

这份文档可以作为你团队的**ORM 规范基础**。如果你需要，下一步我可以帮你把其中的“Hibernate 5 升级 6”部分拆解为一份**迁移检查清单（Checklist）**，方便你在做实际项目升级时逐条打钩确认。需要吗？