---
title: APNS
date: 2025-11-29 07:57:54
tags:
  - APNS
categories:
  - 网络安全
cover: /imgs/APNS.png
---
**APNS**、**iPhone**（设备）和 **后台服务器（Server）** 三者之间的关系和数据流。

以下是APNS的时序图，展示了设备、APNS和服务器之间的交互流程：

{% mermaid %}
sequenceDiagram
    participant I as iPhone (设备)
    participant A as APNS
    participant S as Server (后台服务器)

    autonumber
    
    %% 设备注册推送并获取设备令牌
    I->>A: 注册推送通知 (registerForRemoteNotifications)
    A-->>I: 返回设备令牌 (Device Token)
    I->>S: 发送设备令牌给后台服务器 (via HTTPS)

    %% 设备与 APNS 建立长连接
    I->>A: 建立 TCP 长连接 (端口 5223/443)
    Note right of A: 长连接维持，设备主动发起

    %% 推送通知流程
    S->>A: 发送推送请求 (HTTP/2, 携带 Device Token)
    Note right of S: 短连接，按需发起
    A->>I: 通过长连接推送通知给设备
    Note right of I: 系统处理通知 (显示/角标等)

    %% 断网后重连
    I--xA: 网络断开，长连接中断
    I->>A: 网络恢复，主动重连 (携带 Device Token)
    Note right of A: APNS 更新连接状态

    %% 再次推送
    S->>A: 发送新的推送请求
    A->>I: 通过新连接推送通知
{% endmermaid %}

> 可以在 [https://mermaid.live](https://mermaid.live) 在线编辑和渲染Mermaid图表

![[APNS.png]]

[[MySQL]]