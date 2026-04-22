---
title: Server-Sent Events
date: 2026-04-22 00:27:12
tags: []
categories:
  - AI
cover: https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg
sticky:
hidden: false
updated: 2026-04-22 17:56
---
SSE 实现方案：
1. Spring WebMVC (阻塞模型，基于 Servlet API) + SseEmitter
		a. 线程模型：**Thread-per-request（一请求一线程）**
2. Spring Webflux（异步模型，基于 Reactive Streams）：底层使用 Projcet Reactor, 核心对象是 `Mono` 和  `Flux`
		a. **线程模型**：**Event Loop（事件循环）**。默认服务器通常是 **Netty**。它使用极少数的线程（通常等于 CPU 核心数）来处理海量请求。当遇到 I/O 操作时，线程不等待，而是注册一个回调后立即去处理其他事件, 利用虚拟网卡+DMA 技术来实现。

 利用 Project Reactor 库提供的流式接口 Flux 来构造响应式数据流, 这里总结在代码中使用到的几个操作符:
 