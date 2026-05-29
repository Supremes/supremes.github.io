---
title: "Docker 容器化实战指南"
date: "2026-05-10"
tags: "Docker,容器化,DevOps"
summary: "从零开始掌握 Docker 的核心概念和实战技巧，让你的应用部署变得简单可靠。"
---

## 为什么用 Docker？

传统部署的痛点：

- 「在我电脑上能跑啊」— 环境不一致
- 部署一个应用需要装一堆依赖
- 多个应用之间互相干扰
- 扩容和迁移困难

Docker 的解决方案：**把应用和它的运行环境打包在一起**。

## 核心概念

### 镜像（Image）

镜像是一个只读的模板，包含运行应用所需的一切：

```
┌─────────────────────┐
│      应用代码        │
├─────────────────────┤
│    依赖库/运行时     │
├─────────────────────┤
│      基础系统        │
└─────────────────────┘
```

### 容器（Container）

容器是镜像的运行实例。一个镜像可以创建多个容器，就像一个类可以创建多个对象。

### Dockerfile

描述如何构建镜像的「配方」：

```dockerfile
# 基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 复制依赖文件
COPY requirements.txt .
RUN pip install -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "app.py"]
```

## 实战技巧

### 1. 多阶段构建

减小镜像体积：

```dockerfile
# 构建阶段
FROM node:18 AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# 运行阶段
FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
```

### 2. 使用 .dockerignore

```
node_modules
.git
.env
*.md
```

### 3. 合理利用缓存

把变化频率低的层放在前面：

```dockerfile
# ✅ 好的顺序：依赖变化少，代码变化多
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .

# ❌ 不好的顺序：每次代码变化都要重新装依赖
COPY . .
RUN pip install -r requirements.txt
```

## Docker Compose

管理多容器应用：

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - db
      - redis
  
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: myapp
    volumes:
      - pgdata:/var/lib/postgresql/data
  
  redis:
    image: redis:7-alpine

volumes:
  pgdata:
```

## 常用命令

```bash
# 构建镜像
docker build -t myapp:1.0 .

# 运行容器
docker run -d -p 8000:8000 --name myapp myapp:1.0

# 查看运行中的容器
docker ps

# 查看日志
docker logs -f myapp

# 进入容器
docker exec -it myapp bash

# 清理未使用的资源
docker system prune -a
```

## 安全最佳实践

1. **不要用 root 用户运行应用**
2. **使用官方基础镜像**
3. **定期更新镜像**修复安全漏洞
4. **不要在镜像中存储敏感信息**，用环境变量或 secrets 管理
5. **扫描镜像漏洞**：`docker scout cves <image>`

## 总结

Docker 让部署变得可重复、可预测。掌握它的核心概念和最佳实践，能极大地提升开发和运维效率。

> 记住：Docker 不是万能的，但它解决了一个非常实际的问题——「环境一致性」。
