---
title: Linux 与 Docker 面试速查
date: 2026-08-09
tags:
  - Linux
  - Docker
  - systemd
---
# Linux 与 Docker 面试速查

## 1. Linux 面试最常问什么

### 进程排查

| 问题 | 常用命令 | 你要看什么 |
| --- | --- | --- |
| CPU 高 | `top` / `ps` | 哪个进程、哪个线程、持续多久 |
| 内存高 | `top` / `free -h` / `pmap` | RSS、缓存、是否泄漏 |
| 端口被占用 | `ss -tlnp` / `lsof -i` | 谁在监听 |
| 磁盘满了 | `df -h` / `du -sh` | 分区满还是目录满 |
| 日志排查 | `tail -f` / `journalctl` | 错误时间点、重启前后 |

### 权限

- `rwx` 分别对应读 / 写 / 执行
- 文件看内容要 `r`
- 目录想进入要 `x`
- 目录想列出文件名要 `r`

### kill 与 kill -9

- `kill` 默认发 `SIGTERM`，给进程清理机会
- `kill -9` 是强杀，兜底时再用

## 2. systemd 只背这几个命令

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now myapp
sudo systemctl status myapp
sudo journalctl -u myapp -n 50 --no-pager
sudo systemctl restart myapp
```

如果需要完整配置模板和替代方案，看：

- [systemd 与其他自启动方案长参考](./linux-systemd-autostart-guide.md)

## 3. Docker 面试最短答案

### Docker 是什么

Docker 是**应用打包、分发、部署**的工具。容器底层主要依赖：

- **namespace**：做隔离
- **cgroup**：做资源限制
- **rootfs / 镜像层**：做文件系统视图

### 镜像 vs 容器

- **镜像**：只读模板
- **容器**：镜像启动后的运行实例

### 常见高频点

| 题目 | 最短回答 |
| --- | --- |
| 为什么容器启动快 | 共享宿主机内核，不像虚拟机那样完整虚拟一套 OS |
| 为什么容器隔离弱于虚拟机 | 容器共享内核，虚拟机连内核都隔开了 |
| 多容器怎么通信 | 自定义 bridge 网络、service name、端口映射 |
| 数据怎么持久化 | volume 或 bind mount |
| 多服务怎么一起跑 | `docker compose` |
| 重启后怎么自启 | `--restart=always` 或 `unless-stopped` |

### 面试里的常见取舍

- **优点**：部署快、环境一致、易回滚、资源利用率高
- **缺点**：隔离不如虚拟机、网络和存储会多一层复杂度

## 4. 一句话串起来

Linux 更偏排障与运维常识；Docker 更偏交付与隔离。  
对 Java 后端来说，面试官通常想听到的是：**你能不能把服务跑起来、查出来、稳住。**
