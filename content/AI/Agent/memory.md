---
updated: 2026-09-14 17:57
---

Claude Code:
- 持久化：项目级别的记忆管理机制，在 project 目录下，创建 memory 目录，包含索引文件 Memory. md 和多个 topic 文件
- 写入：LLM 驱动的记忆写入机制，在系统提示词中添加语义，让 LLM 自身判断是否需要添加更新记忆文件
- 读取：将 memory. md 索引文件的内容（限制读取的最大内容），加入到提示词中；按需读取 topic. md

compact 上下文压缩策略：不动提示词开头固化的数据(System Prompt, tools, claude.md , memory. md, env...) 

除此之外，优化上下文压缩策略，可以极大程度上避免关键信息丢失的问题：
1. 写进 claude. md 内，这个不会被压缩
2. 写进文件内，压缩后知道去哪里重读
3. precompact hook：设计该类 hook，追加自定义压缩指令，影响压缩后的摘要写法

Dawn
- 持久化：
	- 上下文：Redis，有限条目 10 条 Q&A
	- 记忆：vector DB - postgresql pgvector 插件
- 写入：redis 中的条目塞满了，把更早的条目 pop 出来到 pending key 上，pending key 满了再作为输入，嵌入到向量数据库中
- 读取：pgvector 中拉取用户画像，和系统提示词一起拼接组成提示词