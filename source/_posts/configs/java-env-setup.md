---
updated: '2026-03-20 17:10'
title: java env setup
hidden: true
abbrlink: f1fa76fa
---
# Java & Maven 编译环境维护指南

> 基于实际踩坑整理，适用于 macOS + 多 JDK 共存场景。

---

## 核心概念：三层版本控制

```
全局 (Global)   ~/.jenv/version          ← jenv global <version>
项目 (Local)    <project>/.java-version  ← jenv local <version>
当前 (Shell)    当前 terminal session    ← jenv shell <version>

优先级：Shell > Local > Global
```

Maven 读取 Java 版本的路径：
```
JAVA_HOME 环境变量 → (jenv export 插件同步) → jenv 当前版本
```

**关键结论：`java` 命令和 `mvn` 使用的 Java 版本，是两个独立的机制，必须都配好才能一致。**

---

## 一次性环境搭建

### 1. 安装 jenv

```bash
brew install jenv
```

在 `~/.zshrc` 末尾加入（顺序不能错）：

```zsh
export PATH="$HOME/.jenv/bin:$PATH"
eval "$(jenv init -)"
```

然后启用两个关键插件：

```bash
jenv enable-plugin export   # 让 jenv 切版本时同步更新 JAVA_HOME
jenv enable-plugin maven    # 让 mvn 跟随 jenv 版本（可选但推荐）
```

重新加载：

```bash
source ~/.zshrc
```

### 2. 注册已安装的 JDK

jenv **不会自动扫描**系统 JDK，每个都要手动注册：

```bash
# 查看系统中已安装的 JDK
/usr/libexec/java_home -V

# 逐个注册
jenv add /Library/Java/JavaVirtualMachines/jdk1.8.0_333.jdk/Contents/Home
jenv add /Users/junkangd/Library/Java/JavaVirtualMachines/corretto-17.0.9/Contents/Home
jenv add /usr/local/Cellar/openjdk/24.0.1/libexec/openjdk.jdk/Contents/Home

# 确认注册结果
jenv versions
```

### 3. 设置全局默认版本

```bash
jenv global 17
```

### 4. 验证 java 和 mvn 一致

```bash
java -version    # 应该是 17
mvn --version    # Java version 也应该是 17
```

如果 `mvn` 显示的 Java 版本与 `java -version` 不一致，说明 `export` 插件没生效，重新执行：

```bash
jenv enable-plugin export
source ~/.zshrc
```

---

## 项目级版本锁定

在项目根目录执行：

```bash
cd /path/to/your-project
jenv local 17      # 生成 .java-version 文件，内容为 "17"
```

效果：进入该目录后，`java` 和 `mvn` 自动切换到 17，离开后恢复全局版本。

**是否提交 `.java-version` 到 git？**

| 场景 | 建议 |
|---|---|
| 团队统一使用 jenv | `git add .java-version`，锁定版本，避免环境差异 |
| 团队工具不统一 | 加入 `.gitignore`，作为个人本地配置 |

本项目选择加入 git，确保所有开发者在项目目录内自动使用 Java 17：

```bash
git add .java-version
git commit -m "chore: lock project Java version to 17 via jenv"
```

---

## 常见问题排查

### 问题 1：`jenv global 1.8` 执行后版本没变

**排查步骤**：

```bash
# 1. 检查当前目录是否有 .java-version（Local 优先级更高）
cat .java-version

# 2. 检查 1.8 是否已注册
jenv versions | grep 1.8

# 3. 确认 jenv 诊断
jenv doctor
```

**常见原因**：
- 当前目录存在 `.java-version`，Local 覆盖了 Global
- `1.8` 版本未通过 `jenv add` 注册

---

### 问题 2：`java -version` 是 17，但 `mvn --version` 显示 Java 8 或 24

**根因**：`JAVA_HOME` 环境变量没有跟随 jenv 切换。

```bash
echo $JAVA_HOME    # 查看当前 JAVA_HOME 指向哪里
```

**修复**：

```bash
jenv enable-plugin export
source ~/.zshrc
```

---

### 问题 3：`mvn` 报 `invalid flag: --release`

**根因**：Maven 用了 Java 8，而 `--release` 参数是 Java 9+ 才支持的编译器参数。

**快速验证**：

```bash
mvn --version | grep "Java version"
```

**修复**：确保 `JAVA_HOME` 指向 Java 11+，参考问题 2。

---

### 问题 4：新开 terminal 版本恢复默认

**根因**：`~/.zshrc` 里没有 jenv 初始化代码，或者初始化代码放在了 `~/.bashrc` 里（但用的是 zsh）。

**检查**：

```bash
grep -n "jenv" ~/.zshrc
```

确保以下三行在 `~/.zshrc` 里：

```zsh
export PATH="$HOME/.jenv/bin:$PATH"
eval "$(jenv init -)"
```

---

## 版本切换速查

```bash
# 查看所有已注册版本
jenv versions

# 全局切换（对所有目录生效，.java-version 除外）
jenv global 17

# 项目切换（生成/修改 .java-version）
jenv local 17

# 临时切换（仅当前 shell session）
jenv shell 17

# 查看当前生效版本及来源
jenv version
# 输出示例: 17 (set by /path/to/project/.java-version)
```

---

## 本项目的 `mvnw` 备用方案

项目根目录提供了 `mvnw` 脚本，**不依赖 jenv 或 JAVA_HOME 配置**，直接通过 `/usr/libexec/java_home -v 17` 定位 Java 17：

```bash
./mvnw clean package        # 始终使用 Java 17 构建
./mvnw test                 # 运行测试
./mvnw spring-boot:run      # 启动应用
```

当 jenv 环境出问题时，`./mvnw` 是最可靠的兜底方案。

---

## 环境健康检查清单

每次遇到奇怪的编译问题，先跑这几条：

```bash
jenv doctor              # jenv 自检
jenv version             # 当前生效版本及来源
echo $JAVA_HOME          # JAVA_HOME 指向
java -version            # java 命令版本
mvn --version            # mvn 用的 Java 版本
```

**正常状态**：`java -version`、`mvn --version` 中的 Java 版本、`$JAVA_HOME` 路径三者一致。
