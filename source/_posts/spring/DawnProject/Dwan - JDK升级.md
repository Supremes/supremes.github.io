---
title: Dwan - JDK升级
tags: []
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: true
updated: '2026-02-06 23:06'
abbrlink: '51292416'
date: 2026-01-31 09:35:26
categories:
sticky:
---
将项目中使用的 JDK 从 1.8 升级到 17，springboot 从 2 升级到 3，做出了如下变更：
- 包名变化：javax  -> jakara
- maven 依赖库
	- 替换升级为日志添加traceid spanid 的库：spring-cloud-starter-sleuth 移除，使用micrometer-tracing-bridge-brave
	- loki-appender
	- mybatisplus
	- mysql-connector
	- jjwt
- Spring security 配置类写法变化：
	继承 `WebSecurityConfigurerAdapter` => 使用 `SecurityFilterChain` Bean