---
title: "Linux 服务自启动配置指南：systemd 与其他方案"
date: "2026-05-28"
tags: "Linux,systemd,运维,DevOps,服务管理,自启动"
summary: "系统整理 Linux 下服务自启动的主流方案，重点讲解 systemd 的配置与实战，同时对比 cron、Supervisor、Docker 等替代方案。"
---

## 为什么需要自启动？

服务器重启后，应用不会自动跑起来。手动一个个启动？不现实。

自启动解决的核心问题：

- 服务器重启后服务自动恢复
- 进程崩溃后自动拉起
- 统一管理多个服务的生命周期
- 减少人工干预，提高可用性

## 方案总览

| 方案 | 适用场景 | 复杂度 | 崩溃重启 | 日志管理 |
|------|---------|--------|---------|---------|
| **systemd** | 系统级服务（首选） | 中 | ✅ | ✅ journald |
| **cron @reboot** | 简单脚本 | 低 | ❌ | ❌ |
| **Supervisor** | 多进程管理 | 中 | ✅ | ✅ |
| **pm2** | Node.js 应用 | 低 | ✅ | ✅ |
| **Docker** | 容器化部署 | 中高 | ✅ | ✅ |
| **nohup + &** | 临时测试 | 低 | ❌ | 基础 |

---

## 方案一：systemd（推荐）

### 什么是 systemd？

systemd 是现代 Linux 发行版（Ubuntu 16+、CentOS 7+、Debian 8+）的默认初始化系统。它负责：

- 系统启动时按顺序拉起服务
- 监控进程状态，崩溃自动重启
- 集中管理日志（journald）
- 处理服务依赖关系

### 核心概念

```
systemd 架构：

┌─────────────────────────────────┐
│           systemd               │
│  ┌───────┐ ┌───────┐ ┌───────┐ │
│  │ .service│ │ .timer │ │ .socket│ │
│  └───────┘ └───────┘ └───────┘ │
│       ↓         ↓         ↓     │
│  ┌─────────────────────────────┐│
│  │      cgroup 资源控制         ││
│  └─────────────────────────────┘│
└─────────────────────────────────┘
```

最常用的是 **.service** 单元，管理一个后台服务。

### 配置文件位置

| 路径 | 作用 | 优先级 |
|------|------|--------|
| `/etc/systemd/system/` | 用户自定义服务 | **最高** |
| `/usr/lib/systemd/system/` | 软件包安装的服务 | 中 |
| `/lib/systemd/system/` | 系统内置服务 | 最低 |

> 建议：自定义服务统一放 `/etc/systemd/system/`，不会被系统更新覆盖。

### 服务文件详解

创建一个服务文件：

```bash
sudo vim /etc/systemd/system/myapp.service
```

完整模板：

```ini
[Unit]
# 服务描述
Description=我的应用

# 依赖关系：在网络就绪后启动
After=network.target

# 可选：要求某个服务先启动（不存在则本服务不启动）
# Requires=postgresql.service

# 可选：弱依赖（建议先启动，但不强制）
# Wants=redis.service

[Service]
# 服务类型
# simple  — 前台运行（默认，最常用）
# forking — 后台运行（需配合 PIDFile）
# oneshot — 执行一次就退出（配合 RemainAfterExit=yes）
# notify  — 类似 simple，但服务会主动通知 systemd 就绪状态
Type=simple

# 工作目录
WorkingDirectory=/opt/myapp

# 启动命令（必须用绝对路径）
ExecStart=/usr/bin/python3 app.py

# 可选：停止前执行的命令
# ExecStop=/usr/bin/python3 shutdown.py

# 可选：重载配置的命令
# ExecReload=/bin/kill -HUP $MAINPID

# 环境变量
Environment=NODE_ENV=production
Environment=PORT=8080

# 或从文件加载环境变量
# EnvironmentFile=/opt/myapp/.env

# 重启策略
# always        — 总是重启
# on-failure    — 非正常退出时重启（推荐）
# on-abnormal   — 信号超时/看门狗超时时重启
# no            — 不重启（默认）
Restart=on-failure

# 重启间隔（秒）
RestartSec=3

# 最大重启次数（0=无限，默认无限）
# StartLimitIntervalSec=60
# StartLimitBurst=5

# 运行用户（不设置则 root）
User=root
Group=root

# 资源限制
# LimitNOFILE=65536      # 文件描述符上限
# LimitNPROC=4096        # 进程数上限
# MemoryMax=512M         # 内存上限（cgroup v2）

# 标准输出/错误重定向到 journald
StandardOutput=journal
StandardError=journal

[Install]
# 多用户模式下启用（相当于开机自启）
WantedBy=multi-user.target
```

### 实战示例

#### 示例 1：Python Flask 应用

```ini
[Unit]
Description=知识库网站
After=network.target

[Service]
Type=simple
WorkingDirectory=/root/knowledge-base
ExecStart=/usr/bin/python3 app.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 示例 2：Node.js 应用

```ini
[Unit]
Description=Node.js API 服务
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/api-server
ExecStart=/usr/bin/node server.js
Restart=on-failure
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3000

[Install]
WantedBy=multi-user.target
```

#### 示例 3：uvicorn（Python ASGI）

```ini
[Unit]
Description=ASGI 应用
After=network.target

[Service]
Type=simple
WorkingDirectory=/root
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 5800
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
```

#### 示例 4：带虚拟环境的 Python 应用

```ini
[Unit]
Description=Python 虚拟环境应用
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/myproject
ExecStart=/opt/myproject/venv/bin/python app.py
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

> 注意：虚拟环境场景下，ExecStart 直接指向 venv 里的 python，不需要先 activate。

### 常用命令

```bash
# 重载配置文件（修改 .service 后必须执行）
sudo systemctl daemon-reload

# 启动/停止/重启
sudo systemctl start myapp
sudo systemctl stop myapp
sudo systemctl restart myapp

# 查看状态
sudo systemctl status myapp

# 开机自启
sudo systemctl enable myapp

# 取消开机自启
sudo systemctl disable myapp

# 启用 + 立即启动（一步到位）
sudo systemctl enable --now myapp

# 查看所有已启用的服务
systemctl list-unit-files --state=enabled

# 查看所有运行中的服务
systemctl list-units --type=service --state=running
```

### 日志管理

```bash
# 查看服务日志
sudo journalctl -u myapp

# 实时跟踪
sudo journalctl -u myapp -f

# 最近 50 行
sudo journalctl -u myapp -n 50

# 查看今天的日志
sudo journalctl -u myapp --since today

# 查看指定时间范围
sudo journalctl -u myapp --since "2026-05-28 10:00" --until "2026-05-28 12:00"

# 只看错误
sudo journalctl -u myapp -p err

# 日志占用的磁盘空间
journalctl --disk-usage

# 清理 7 天前的日志
sudo journalctl --vacuum-time=7d
```

### 依赖管理

多个服务之间有依赖关系时：

```ini
# 服务 B 依赖服务 A
[Unit]
Description=服务 B
After=service-a.service
Requires=service-a.service
```

**依赖类型对比：**

| 指令 | 含义 | A 不存在时 |
|------|------|-----------|
| `Requires` | 强依赖 | B 不启动 |
| `Wants` | 弱依赖 | B 正常启动 |
| `After` | 启动顺序 | 不影响启动 |
| `Before` | 启动顺序（反向） | 不影响启动 |
| `BindsTo` | 绑定（A 停 B 也停） | B 不启动 |
| `Conflicts` | 互斥 | — |

### 定时任务：Timer 单元

systemd 也能替代 cron 做定时任务：

```ini
# /etc/systemd/system/backup.timer
[Unit]
Description=每日备份

[Timer]
# 每天凌晨 2 点执行
OnCalendar=*-*-* 02:00:00
# 如果错过了（比如关机），开机后立即补执行
Persistent=true

[Install]
WantedBy=timers.target
```

```ini
# /etc/systemd/system/backup.service
[Unit]
Description=执行备份

[Service]
Type=oneshot
ExecStart=/opt/scripts/backup.sh
```

```bash
# 启用定时器
sudo systemctl enable --now backup.timer

# 查看所有定时器
systemctl list-timers --all
```

---

## 方案二：cron @reboot

最简单的自启动方式，适合一次性脚本。

```bash
# 编辑 crontab
crontab -e

# 添加一行（@reboot = 开机时执行一次）
@reboot /usr/bin/python3 /opt/myapp/app.py >> /var/log/myapp.log 2>&1
```

**优点：**
- 配置简单，一行搞定
- 所有 Linux 都支持

**缺点：**
- 没有崩溃重启
- 没有日志管理
- 没有依赖管理
- 执行时机不确定（可能网络还没就绪）

**适用场景：** 临时脚本、开机挂载、简单的一次性任务。

---

## 方案三：Supervisor

Supervisor 是 Python 写的进程管理工具，适合管理多个进程。

### 安装

```bash
pip install supervisor
# 或
apt install supervisor
```

### 配置

```ini
# /etc/supervisor/conf.d/myapp.conf
[program:myapp]
command=/usr/bin/python3 /opt/myapp/app.py
directory=/opt/myapp
user=root
autostart=true
autorestart=true
startsecs=10
startretries=3
redirect_stderr=true
stdout_logfile=/var/log/myapp.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
environment=ENV="production"
```

### 常用命令

```bash
# 重载配置
supervisorctl reread
supervisorctl update

# 操作
supervisorctl start myapp
supervisorctl stop myapp
supervisorctl restart myapp
supervisorctl status
```

**与 systemd 的关系：** Supervisor 本身通常由 systemd 管理。现代更推荐直接用 systemd。

---

## 方案四：pm2（Node.js 专属）

Node.js 生态最流行的进程管理器。

### 安装

```bash
npm install -g pm2
```

### 基本使用

```bash
# 启动应用
pm2 start app.js --name myapp

# 带参数启动
pm2 start server.js --name api -- -p 3000

# 查看状态
pm2 status

# 查看日志
pm2 logs myapp

# 重启/停止
pm2 restart myapp
pm2 stop myapp

# 删除
pm2 delete myapp
```

### 生成开机自启脚本

```bash
# 生成启动脚本
pm2 startup

# 保存当前进程列表
pm2 save
```

`pm2 startup` 会输出一条命令让你执行，它实际上是创建了一个 systemd 服务。

**适用场景：** 纯 Node.js 项目，不想手写 systemd 配置。

---

## 方案五：Docker + restart policy

容器化部署天然支持自启动。

### Docker 直接运行

```bash
# --restart=always 开机自启 + 崩溃重启
docker run -d \
  --name myapp \
  --restart=always \
  -p 8080:8080 \
  myapp:latest
```

**重启策略：**

| 策略 | 含义 |
|------|------|
| `no` | 不重启（默认） |
| `on-failure` | 非零退出码时重启 |
| `on-failure:5` | 最多重试 5 次 |
| `always` | 总是重启（推荐） |
| `unless-stopped` | 类似 always，但手动停止后不自动恢复 |

### Docker Compose

```yaml
version: '3.8'
services:
  web:
    image: myapp:latest
    ports:
      - "8080:8080"
    restart: always
  redis:
    image: redis:7
    restart: always
```

```bash
# 启动
docker compose up -d

# Docker daemon 本身也需要自启
sudo systemctl enable docker
```

---

## 方案对比与选择建议

### 决策树

```
你的应用是什么类型？
│
├─ Python / Go / 通用应用
│   └─ 推荐：systemd ✅
│
├─ Node.js 项目
│   ├─ 快速上手 → pm2
│   └─ 生产环境 → systemd
│
├─ 多个进程需要统一管理
│   ├─ 不用容器 → Supervisor 或 systemd slice
│   └─ 用容器 → Docker Compose
│
└─ 临时脚本 / 一次性任务
    └─ cron @reboot
```

### 生产环境推荐组合

```
┌─────────────────────────────────┐
│         systemd                 │  ← 系统级服务管理
│  ┌──────────┐ ┌──────────────┐ │
│  │ 应用服务  │ │ Docker daemon │ │  ← 容器由 Docker 管理
│  └──────────┘ └──────────────┘ │
│         ↓                       │
│  ┌──────────────────────────────┐│
│  │   journald 日志收集          ││  ← 统一日志
│  └──────────────────────────────┘│
│  ┌──────────────────────────────┐│
│  │   timer 定时任务             ││  ← 替代 cron
│  └──────────────────────────────┘│
└─────────────────────────────────┘
```

---

## 常见问题排查

### 服务启动失败

```bash
# 第一步：看状态
systemctl status myapp

# 第二步：看详细日志
journalctl -u myapp -n 50 --no-pager

# 第三步：手动执行命令看报错
cd /opt/myapp && /usr/bin/python3 app.py
```

### 修改配置后不生效

```bash
# 必须先重载
sudo systemctl daemon-reload
# 再重启
sudo systemctl restart myapp
```

### 权限问题

```bash
# 确认文件权限
ls -la /opt/myapp/

# 如果用非 root 用户运行
sudo chown -R myuser:myuser /opt/myapp
# 在 .service 中设置
# User=myuser
# Group=myuser
```

### 端口被占用

```bash
# 查看谁占了端口
sudo ss -tlnp | grep :8080
# 或
sudo lsof -i :8080
```

### 环境变量不生效

```bash
# 不要在 .service 里用 source ~/.bashrc
# 用 Environment 或 EnvironmentFile

# 方式一：直接写
Environment=PATH=/usr/local/bin:/usr/bin

# 方式二：从文件加载
EnvironmentFile=/opt/myapp/.env
```

---

## 总结

| 场景 | 推荐方案 |
|------|---------|
| 生产环境单个服务 | **systemd** |
| Node.js 快速上手 | pm2 |
| 多进程统一管理 | Supervisor 或 Docker Compose |
| 临时脚本 | cron @reboot |
| 容器化部署 | Docker + restart policy |

**一句话建议：** 除非有特殊理由，直接用 systemd。它是 Linux 的标准，稳定、功能全面、文档丰富。
