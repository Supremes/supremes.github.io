---
title: VPS 服务迁移指南
date: 2026-05-30
category: 运维
tags: [迁移, VPS, 运维, 部署]
description: 从旧 VPS 迁移所有服务到新机器的完整指南，涵盖四大 Web 服务、Hermes Agent、飞书/微信网关等。
---

# VPS 服务迁移指南

## 一、服务总览

当前服务器运行以下服务（Ubuntu 22.04 LTS）：

| 服务 | 端口 | 路径 | 技术栈 | systemd 服务名 |
|------|------|------|--------|----------------|
| 知识库网站 | 8080 | `/root/knowledge-base/` | Flask + Markdown | `knowledge-base.service` |
| LeetCode 追踪器 | 8081 | `/root/leetcode-tracker/` | Flask + SQLite | `leetcode-tracker.service` |
| 金融估值面板 | 8082 | `/root/market-dashboard/` | Flask + yfinance | `market-dashboard.service` |
| 文件服务器 | 5800 | `/root/file-server/` | FastAPI + Uvicorn | `fileserver.service` |
| Hermes Gateway | — | `/usr/local/lib/hermes-agent/` | Python (user service) | `hermes-gateway.service`（systemd user） |
| Hermes Web UI | 3000 | `/usr/lib/node_modules/hermes-web-ui/` | Node.js | 无 systemd，需手动管理 |

## 二、迁移前准备

### 2.1 新服务器要求

- **操作系统**：Ubuntu 22.04 LTS
- **Python**：3.10+（系统自带即可）
- **Node.js**：v22+（Hermes Web UI 需要）
- **内存**：建议 2GB+
- **磁盘**：建议 20GB+（当前 `/root/` 约 2.6GB）

### 2.2 需要从旧服务器导出的数据

```
# 1. 四个 Web 服务目录
/root/knowledge-base/       # 92MB（含 Git 仓库）
/root/leetcode-tracker/     # 272KB（含 SQLite 数据库）
/root/market-dashboard/     # 1.3MB（含缓存数据）
/root/file-server/          # 128KB

# 2. Hermes Agent 配置和数据
/root/.hermes/              # 146MB（配置、技能、会话、记忆）

# 3. SSH 密钥（Git 推送需要）
/root/.ssh/id_ed25519
/root/.ssh/id_ed25519.pub
/root/.ssh/id_ed25519_supremes
/root/.ssh/id_ed25519_supremes.pub
/root/.ssh/config

# 4. Git 全局配置
/root/.gitconfig
```

## 三、逐步迁移

### 3.1 在旧服务器打包数据

```bash
# 打包所有服务数据（排除缓存和临时文件）
cd /root
tar czf /tmp/vps-migration.tar.gz \
  knowledge-base/ \
  leetcode-tracker/ \
  market-dashboard/ \
  file-server/ \
  .hermes/ \
  .ssh/ \
  .gitconfig \
  --exclude='__pycache__' \
  --exclude='*.pyc' \
  --exclude='node_modules' \
  --exclude='.hermes/sessions/request_dump_*'

# 查看包大小
ls -lh /tmp/vps-migration.tar.gz
```

### 3.2 传输到新服务器

```bash
# 方法一：SCP（推荐）
scp /tmp/vps-migration.tar.gz root@<新服务器IP>:/root/

# 方法二：如果两台机器都能访问同一存储
# 可以用 rclone、rsync 等
```

### 3.3 在新服务器解压

```bash
cd /root
tar xzf /tmp/vps-migration.tar.gz
```

### 3.4 安装系统依赖

```bash
# 更新系统
apt-get update && apt-get upgrade -y

# Python 相关
apt-get install -y python3 python3-pip python3-venv

# 安装各服务的 Python 依赖
/usr/bin/python3 -m pip install flask markdown pygments fastapi uvicorn yfinance requests

# Node.js（用于 Hermes Web UI）
curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
apt-get install -y nodejs
```

### 3.5 安装 Hermes Agent

```bash
# 克隆 Hermes Agent
git clone https://github.com/NousResearch/hermes-agent.git /usr/local/lib/hermes-agent
cd /usr/local/lib/hermes-agent

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -e .

# 创建 hermes 命令链接
cat > /usr/local/bin/hermes << 'EOF'
#!/bin/bash
source /usr/local/lib/hermes-agent/venv/bin/activate
exec python -m hermes_cli.main "$EOF"
EOF
chmod +x /usr/local/bin/hermes

# 安装 Hermes Web UI
npm install -g hermes-web-ui
```

### 3.6 恢复 SSH 密钥和 Git 配置

```bash
# 确保 SSH 密钥权限正确
chmod 700 /root/.ssh
chmod 600 /root/.ssh/id_ed25519 /root/.ssh/id_ed25519_supremes
chmod 644 /root/.ssh/id_ed25519.pub /root/.ssh/id_ed25519_supremes.pub

# 测试 GitHub 连接
ssh -T git@github-supremes
# 应该看到：Hi Supremes! You've successfully authenticated...
```

## 四、配置 Systemd 服务

### 4.1 Web 服务（系统级）

创建 `/etc/systemd/system/knowledge-base.service`：

```ini
[Unit]
Description=Knowledge Base Website (知识库网站)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/knowledge-base
ExecStart=/usr/bin/python3 /root/knowledge-base/app.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/leetcode-tracker.service`：

```ini
[Unit]
Description=LeetCode Progress Tracker (LeetCode 进度追踪器)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/leetcode-tracker
ExecStart=/usr/bin/python3 /root/leetcode-tracker/app.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/market-dashboard.service`：

```ini
[Unit]
Description=Market Valuation Dashboard (美股估值仪表盘)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/market-dashboard
ExecStart=/usr/bin/python3 /root/market-dashboard/app.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

创建 `/etc/systemd/system/fileserver.service`：

```ini
[Unit]
Description=Hermes File Server (文件服务器)
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/file-server
ExecStart=/usr/bin/python3 /root/file-server/main.py
Restart=always
RestartSec=10
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
```

启用并启动所有服务：

```bash
systemctl daemon-reload
systemctl enable knowledge-base leetcode-tracker market-dashboard fileserver
systemctl start knowledge-base leetcode-tracker market-dashboard fileserver

# 验证服务状态
systemctl status knowledge-base leetcode-tracker market-dashboard fileserver
```

### 4.2 Hermes Gateway（用户级 systemd）

```bash
# 确保 systemd user 服务目录存在
mkdir -p /root/.config/systemd/user/

# 服务文件已在 /root/.config/systemd/user/hermes-gateway.service 中
# 如果没有，创建它：

cat > /root/.config/systemd/user/hermes-gateway.service << 'EOF'
[Unit]
Description=Hermes Agent Gateway - Messaging Platform Integration
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=simple
ExecStart=/usr/local/lib/hermes-agent/venv/bin/python -m hermes_cli.main gateway run --replace
WorkingDirectory=/usr/local/lib/hermes-agent
Environment="PATH=/usr/local/lib/hermes-agent/venv/bin:/usr/local/lib/hermes-agent/node_modules/.bin:/usr/bin:/root/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
Environment="VIRTUAL_ENV=/usr/local/lib/hermes-agent/venv"
Environment="HERMES_HOME=/root/.hermes"
Restart=always
RestartSec=5
RestartMaxDelaySec=300
RestartSteps=5
RestartForceExitStatus=75
KillMode=mixed
KillSignal=SIGTERM
ExecReload=/bin/kill -USR1 $MAINPID
TimeoutStopSec=210
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
EOF

# 启用 lingering（允许 user service 在用户未登录时运行）
loginctl enable-linger root

# 启动 gateway
systemctl --user daemon-reload
systemctl --user enable hermes-gateway
systemctl --user start hermes-gateway

# 验证
systemctl --user status hermes-gateway
```

### 4.3 Hermes Web UI

Hermes Web UI 通过 npm 全局安装，需要手动启动或创建 systemd 服务：

```bash
# 启动 Web UI（端口 3000）
hermes-web-ui &

# 或者创建 systemd user service：
cat > /root/.config/systemd/user/hermes-web-ui.service << 'EOF'
[Unit]
Description=Hermes Web UI
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/node /usr/lib/node_modules/hermes-web-ui/dist/server/index.js
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
EOF

systemctl --user daemon-reload
systemctl --user enable hermes-web-ui
systemctl --user start hermes-web-ui
```

## 五、Hermes Agent 配置

### 5.1 恢复配置文件

迁移后 `/root/.hermes/` 目录已包含所有配置，但需要检查：

```bash
# 检查配置文件
cat /root/.hermes/config.yaml

# 检查环境变量（包含 API 密钥）
cat /root/.hermes/.env
```

### 5.2 关键环境变量

`.env` 文件中包含以下重要配置（迁移后需要更新）：

| 变量名 | 说明 | 是否需要更新 |
|--------|------|-------------|
| `WEIXIN_TOKEN` | 微信接入 Token | 可能需要 |
| `WEIXIN_BASE_URL` | 微信回调地址 | **需要更新为新服务器 IP/域名** |
| `WEIXIN_CDN_BASE_URL` | 微信 CDN 地址 | **需要更新** |
| `FEISHU_APP_ID` | 飞书应用 ID | 不需要 |
| `FEISHU_APP_SECRET` | 飞书应用密钥 | 不需要 |
| `XIAOMI_BASE_URL` | 小米模型 API 地址 | 不需要 |

### 5.3 Hermes 更新

```bash
cd /usr/local/lib/hermes-agent
git pull origin main
source venv/bin/activate
pip install -e .
hermes --version
```

## 六、知识库 Git 仓库

知识库使用 Git 管理，远程仓库指向 GitHub：

```
origin  git@github-supremes:Supremes/supremes.github.io.git
```

迁移后需要：

1. **SSH 密钥**：已在 3.6 步骤恢复
2. **Git remote**：解压后自动保留，无需重新配置
3. **验证**：
   ```bash
   cd /root/knowledge-base
   git remote -v
   git pull origin main  # 测试拉取
   ```

## 七、数据备份清单

迁移前务必确认以下数据已备份：

| 数据 | 路径 | 重要性 | 说明 |
|------|------|--------|------|
| 知识库源文件 | `/root/knowledge-base/content/` | ⭐⭐⭐ | 所有 Markdown 文章 |
| 知识库模板 | `/root/knowledge-base/templates/` | ⭐⭐⭐ | HTML 模板 |
| 知识库静态资源 | `/root/knowledge-base/static/` | ⭐⭐ | CSS/JS/图片 |
| LeetCode 数据库 | `/root/leetcode-tracker/leetcode.db` | ⭐⭐⭐ | SQLite，刷题记录 |
| 金融面板缓存 | `/root/market-dashboard/data/` | ⭐ | 可重新获取 |
| 文件服务器文件 | `/root/file-server/wwwroot/` | ⭐⭐ | 用户上传的文件 |
| Hermes 配置 | `/root/.hermes/config.yaml` | ⭐⭐⭐ | Agent 配置 |
| Hermes 环境变量 | `/root/.hermes/.env` | ⭐⭐⭐ | API 密钥等 |
| Hermes 技能库 | `/root/.hermes/skills/` | ⭐⭐ | 自定义技能 |
| Hermes 记忆 | `/root/.hermes/memories/` | ⭐⭐ | 跨会话记忆 |
| SSH 密钥 | `/root/.ssh/` | ⭐⭐⭐ | Git 推送必需 |
| Systemd 服务 | `/etc/systemd/system/*.service` | ⭐⭐ | 4 个 Web 服务 |
| Systemd User 服务 | `/root/.config/systemd/user/` | ⭐⭐ | Hermes Gateway |

## 八、迁移后验证清单

完成迁移后，逐项验证：

```bash
# 1. 检查所有服务状态
systemctl status knowledge-base leetcode-tracker market-dashboard fileserver
systemctl --user status hermes-gateway hermes-web-ui

# 2. 测试各服务 HTTP 响应
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080  # 知识库
curl -s -o /dev/null -w "%{http_code}" http://localhost:8081  # LeetCode
curl -s -o /dev/null -w "%{http_code}" http://localhost:8082  # 金融面板
curl -s -o /dev/null -w "%{http_code}" http://localhost:5800  # 文件服务器
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000  # Web UI
curl -s -o /dev/null -w "%{http_code}" http://localhost:4000  # Gateway

# 3. 测试 Hermes CLI
hermes --version

# 4. 测试 Git 连接
cd /root/knowledge-base && git fetch origin

# 5. 测试知识库热加载
echo "---
title: 测试文章
date: 2026-05-30
category: 测试
---
# 测试" > /root/knowledge-base/content/测试/test.md
# 访问网站确认文章出现，然后删除测试文件
rm -rf /root/knowledge-base/content/测试/

# 6. 测试外部访问（替换为新服务器 IP）
curl -s -o /dev/null -w "%{http_code}" http://<新IP>:8080
```

## 九、常见问题

### Q: Hermes Gateway 启动失败？

```bash
# 查看日志
journalctl --user -u hermes-gateway -n 50

# 常见原因：.env 中的 API 密钥过期、网络不通
```

### Q: 知识库 Git 推送失败？

```bash
# 测试 SSH 连接
ssh -T git@github-supremes

# 如果失败，检查 SSH 密钥权限
chmod 600 /root/.ssh/id_ed25519
```

### Q: 金融面板数据为空？

```bash
# yfinance 需要联网获取数据，首次访问会自动拉取
# 如果超时，检查网络连通性
curl -s https://query1.finance.yahoo.com/ > /dev/null && echo "OK" || echo "FAIL"
```

### Q: 端口被占用？

```bash
# 查看端口占用
lsof -i :8080
lsof -i :8081
lsof -i :8082
lsof -i :5800
lsof -i :3000
lsof -i :4000

# 杀掉占用进程
kill -9 <PID>
```

### Q: 如何更新 Hermes Agent？

```bash
cd /usr/local/lib/hermes-agent
git pull origin main
source venv/bin/activate
pip install -e .
systemctl --user restart hermes-gateway
```

## 十、回滚方案

如果新服务器出现问题，旧服务器的数据仍在：

1. 旧服务器的 systemd 服务保持不变
2. 只需重新启动旧服务器上的服务：
   ```bash
   systemctl start knowledge-base leetcode-tracker market-dashboard fileserver
   systemctl --user start hermes-gateway
   ```
3. DNS/端口映射切回旧服务器即可

---

> 📝 **最后更新**：2026-05-30
> 
> **当前服务器环境**：Ubuntu 22.04 LTS / Python 3.10.12 / Node.js v22.22.2 / Hermes Agent v0.14.0
