---
title: Maven 命令速查表
tags:
  - maven
  - java
---
# Maven 命令速查表

> 基于日常开发高频场景整理，覆盖构建、依赖分析、插件使用等核心操作。

---

## 项目构建

```bash
# 清理 + 编译 + 打包（跳过测试）
mvn clean package -DskipTests

# 清理 + 编译 + 打包 + 安装到本地仓库
mvn clean install

# 只编译，不打包
mvn compile

# 编译测试代码（不运行）
mvn test-compile

# 运行测试
mvn test

# 打包（jar/war）
mvn package

# 部署到远程仓库
mvn deploy
```

### 跳过测试的两种方式

```bash
# 跳过测试执行，但仍编译测试代码
mvn package -DskipTests

# 跳过测试编译和执行（更彻底）
mvn package -Dmaven.test.skip=true
```

---

## 依赖分析

```bash
# 查看完整依赖树
mvn dependency:tree

# 过滤特定 groupId 的依赖（追溯某个包怎么引入的）
mvn dependency:tree -Dincludes=io.projectreactor

# 支持 groupId:artifactId 精确过滤
mvn dependency:tree -Dincludes=com.fasterxml.jackson.core:jackson-databind

# 显示详细信息（包含被省略的重复依赖）
mvn dependency:tree -Dverbose

# 输出到文件
mvn dependency:tree -DoutputFile=deps.txt

# 分析未使用和缺失的依赖
mvn dependency:analyze

# 查看依赖列表（扁平视图）
mvn dependency:list

# 将所有依赖复制到 target/dependency 目录
mvn dependency:copy-dependencies
```

### 多模块项目依赖分析

```bash
# 只分析指定子模块
mvn dependency:tree -pl <module-name>

# 组合过滤
mvn dependency:tree -pl <module-name> -Dincludes=io.projectreactor
```

> `-pl` 仅适用于多模块项目（父 POM 包含 `<modules>` 声明）。单模块项目不需要此参数。

---

## 插件与帮助

```bash
# 查看有效 POM（合并父 POM 继承 + profile 后的最终结果）
mvn help:effective-pom

# 查看有效 settings.xml
mvn help:effective-settings

# 查看某个插件的详细用法
mvn help:describe -Dplugin=compiler
mvn help:describe -Dplugin=surefire -Ddetail

# 查看当前激活的 profile
mvn help:active-profiles

# 评估表达式（调试 POM 变量）
mvn help:evaluate -Dexpression=project.version -q -DforceStdout
```

---

## Profile 管理

```bash
# 激活指定 profile
mvn package -P dev

# 激活多个 profile
mvn package -P dev,docker

# 查看所有可用 profile
mvn help:all-profiles
```

---

## 版本与属性

```bash
# 查看项目版本
mvn help:evaluate -Dexpression=project.version -q -DforceStdout

# 查看 Java 编译版本
mvn help:evaluate -Dexpression=maven.compiler.source -q -DforceStdout

# 批量更新子模块版本号（多模块项目）
mvn versions:set -DnewVersion=2.0.0

# 检查依赖是否有新版本
mvn versions:display-dependency-updates

# 检查插件是否有新版本
mvn versions:display-plugin-updates
```

---

## Spring Boot 项目

```bash
# 启动应用
mvn spring-boot:run

# 指定 profile 启动
mvn spring-boot:run -Dspring-boot.run.profiles=dev

# 构建可执行 jar
mvn clean package spring-boot:repackage
```

---

## Maven Wrapper（mvnw）

项目自带的 Maven 版本管理，不依赖全局安装：

```bash
# 生成 wrapper 文件
mvn wrapper:wrapper

# 指定 Maven 版本
mvn wrapper:wrapper -Dmaven=3.9.6

# 使用 wrapper 构建（替代 mvn）
./mvnw clean package
```

---

## 常用组合技

```bash
# 快速构建，跳过测试和 Javadoc
mvn clean package -DskipTests -Dmaven.javadoc.skip=true

# 离线模式（不下载任何东西）
mvn package -o

# 强制更新 SNAPSHOT 依赖
mvn package -U

# 只构建当前模块，不构建依赖模块
mvn package -pl <module> -am

# 并行构建（多模块项目加速）
mvn package -T 4     # 4 个线程
mvn package -T 1C    # 每个 CPU 核心 1 个线程

# 调试模式（输出详细日志）
mvn package -X
```

---

## 参数速查

| 参数 | 作用 |
|------|------|
| `-pl <module>` | 指定构建的子模块 |
| `-am` | 同时构建所依赖的模块 |
| `-amd` | 同时构建依赖于该模块的模块 |
| `-rf <module>` | 从指定模块开始继续构建（构建失败后恢复） |
| `-DskipTests` | 跳过测试执行 |
| `-Dmaven.test.skip=true` | 跳过测试编译和执行 |
| `-U` | 强制更新 SNAPSHOT |
| `-o` | 离线模式 |
| `-X` | 调试输出 |
| `-q` | 静默模式，只输出错误 |
| `-T <n>` | 并行构建线程数 |
| `-P <profile>` | 激活 profile |
| `-f <pom>` | 指定 POM 文件路径 |

---

## 本地仓库管理

```bash
# 本地仓库位置（默认）
~/.m2/repository

# 清理本地仓库中某个依赖的缓存
rm -rf ~/.m2/repository/com/example/some-artifact

# 将本地 jar 安装到本地仓库
mvn install:install-file \
  -Dfile=lib/custom.jar \
  -DgroupId=com.example \
  -DartifactId=custom \
  -Dversion=1.0.0 \
  -Dpackaging=jar
```
