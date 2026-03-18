---
title: ReAct
tags: []
categories:
  - AI
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: false
updated: 2026-03-17 11:23
abbrlink: e0e90631
date: 2026-03-16 14:30:06
sticky:
---
> [!info]
Agent 的实现，利用了 ReAct 设计思想。

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/ReAct-Diagram2.webp)

这张图表直观地展示了 **ReAct (Reason + Act)**，一种用于大型语言模型（LLM）的复杂任务解决和提示技术。它将**逻辑推理 (Reasoning)** 与**执行行动 (Acting)** 结合在一个循环中，使模型能够利用外部工具和知识来完成复杂的任务。

**主要组件与流程图解：**

1. **用户输入 (User Input):** 流程始于一个复杂的用户查询（图中最左侧的蓝色方框）。例如：“查找最大国家的首都、人口和密度”。这需要多步规划和外部信息。
2. **ReAct 智能体 (ReAct Agent - LLM):** 核心是一个由 LLM 驱动的智能体（中央的大型绿色方框）。它不仅是一个模型，还包含了一个带有示例的**提示 (Prompt)**，用于指导其思考和行动的格式。
3. **循环迭代 (Iterations):** 这是 ReAct 的精髓。对于复杂任务，智能体会进行多次循环，每次循环包含：
    
    - **思考 (Thought - 浅黄色方框):** 智能体生成一个推理过程，确定下一步该做什么，规划行动路径。例如，智能体会产生这样的想法：“首先需要查找哪个国家是最大的”。
    - **行动 (Action - 橙色方框):** 根据思考，智能体决定使用哪个**外部工具**并生成相应的命令。例如，`GoogleSearch("largest country")`。
    - **观察 (Observation - 浅红色方框):** 这是工具执行后的结果，是从外部环境中**观察**到的信息。例如，"俄罗斯是最大的国家"。
        
4. **外部环境/工具 (External Environment / Tools):** （右侧紫色方框）智能体可以访问的工具集合，如 Google 搜索、计算器、API 或数据库。当产生一个“行动”时，它会在这里执行，并返回结果。
5. **记忆/上下文 (Memory / Context):** （中间的灰色方框）智能体会将之前的思考、行动和观察都记录在上下文中，作为后续迭代的输入。这就像一个临时的“笔记”，记录了已经获取的知识。
6. **最终输出 (Final Output):** （右下角绿色方框）在经过多次迭代（如查找国家、查找首都、查找人口、计算密度）后，智能体收集了所有必要信息，产生一个最终思考，并生成完整的回答返回给用户。
