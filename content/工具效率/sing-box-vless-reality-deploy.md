---
title: sing-box
tags: []
---
# sing-box + VLESS Reality 部署指南

> 无需域名、无需证书，抗检测能力强，部署最简方案。

## 前置条件

- 一台境外 VPS（Debian/Ubuntu）
- 本地能通过 SSH 连接到 VPS
- 443 端口未被占用

## 1. 安装 sing-box

VPS 可能无法直接从 GitHub 下载 releases 文件，通过本地中转：

```bash
# 本地下载（版本号按需替换）
curl -sL -o /tmp/sing-box.tar.gz \
  https://github.com/SagerNet/sing-box/releases/download/v1.13.13/sing-box-1.13.13-linux-amd64.tar.gz

# 上传到 VPS
scp /tmp/sing-box.tar.gz vps:/tmp/

# VPS 上安装
ssh vps "cd /tmp && tar xzf sing-box.tar.gz && \
  cp sing-box-*/sing-box /usr/local/bin/ && \
  chmod +x /usr/local/bin/sing-box"

# 验证
ssh vps "sing-box version"
```

> 最新版本查看：https://github.com/SagerNet/sing-box/releases

## 2. 生成密钥

在 VPS 上执行：

```bash
# Reality 密钥对
sing-box generate reality-keypair
# 输出：
# PrivateKey: xxxx  ← 服务端用
# PublicKey:  xxxx  ← 客户端用

# 用户 UUID
sing-box generate uuid

# Short ID
openssl rand -hex 8
```

**记录以上三组值，后续配置要用。**

## 3. 写入配置

```bash
mkdir -p /etc/sing-box
cat > /etc/sing-box/config.json << 'EOF'
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "vless",
      "tag": "vless-in",
      "listen": "::",
      "listen_port": 443,
      "users": [
        {
          "uuid": "<替换为生成的 UUID>",
          "flow": "xtls-rprx-vision"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "www.apple.com",
        "reality": {
          "enabled": true,
          "handshake": {
            "server": "www.apple.com",
            "server_port": 443
          },
          "private_key": "<替换为 PrivateKey>",
          "short_id": ["<替换为 Short ID>"]
        }
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ]
}
EOF
```

### 关于 SNI 目标站点

`server_name` 和 `handshake.server` 需要是同一个支持 TLS 1.3 和 H2 的大站，推荐：

- `www.apple.com`
- `www.microsoft.com`
- `www.samsung.com`

验证目标站是否可用：

```bash
curl -sI --tlsv1.3 https://www.apple.com | head -1
# 应返回 HTTP/2 200
```

### 验证配置

```bash
sing-box check -c /etc/sing-box/config.json
```

## 4. 设置 systemd 服务

```bash
cat > /etc/systemd/system/sing-box.service << 'EOF'
[Unit]
Description=sing-box service
Documentation=https://sing-box.sagernet.org
After=network.target nss-lookup.target

[Service]
ExecStart=/usr/local/bin/sing-box run -c /etc/sing-box/config.json
Restart=on-failure
RestartSec=10
LimitNOFILE=infinity

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable sing-box
systemctl start sing-box
```

### 常用管理命令

```bash
systemctl status sing-box    # 查看状态
systemctl restart sing-box   # 重启
systemctl stop sing-box      # 停止
journalctl -u sing-box -f    # 查看实时日志
```

## 5. 客户端连接

### 连接参数

| 参数 | 值 |
|------|-----|
| 协议 | VLESS |
| 地址 | VPS 的 IP |
| 端口 | 443 |
| UUID | 第 2 步生成的 UUID |
| 流控 | xtls-rprx-vision |
| 安全 | Reality |
| SNI | www.apple.com（与服务端一致） |
| 公钥 | 第 2 步生成的 PublicKey |
| Short ID | 第 2 步生成的值 |
| 指纹 | chrome |

### 分享链接格式

```
vless://<UUID>@<IP>:443?encryption=none&flow=xtls-rprx-vision&security=reality&sni=www.apple.com&fp=chrome&pbk=<PublicKey>&sid=<ShortID>&type=tcp#节点名称
```

可直接导入 v2rayN / Shadowrocket / NekoBox / Clash Verge 等客户端。

### 推荐客户端

| 平台 | 客户端 |
|------|--------|
| iOS | Shadowrocket（付费）/ Stash |
| Android | NekoBox / v2rayNG |
| macOS | Clash Verge Rev / NekoRay |
| Windows | v2rayN / Clash Verge Rev |

## 6. 故障排查

```bash
# 检查服务是否运行
systemctl status sing-box

# 检查 443 端口是否监听
ss -tlnp | grep 443

# 查看错误日志
journalctl -u sing-box --no-pager -n 50

# 检查防火墙是否放行
iptables -L -n | grep 443
```

## 7. 升级 sing-box

```bash
# 本地下载新版本
curl -sL -o /tmp/sing-box.tar.gz \
  https://github.com/SagerNet/sing-box/releases/download/v新版本号/sing-box-新版本号-linux-amd64.tar.gz

# 上传并替换
scp /tmp/sing-box.tar.gz vps:/tmp/
ssh vps "cd /tmp && tar xzf sing-box.tar.gz && \
  cp sing-box-*/sing-box /usr/local/bin/ && \
  systemctl restart sing-box"
```
