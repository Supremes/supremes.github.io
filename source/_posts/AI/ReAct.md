---
title: ReAct
tags: []
categories:
  - AI
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: false
updated: '2026-03-16 14:30'
abbrlink: e0e90631
date: 2026-03-16 14:30:06
sticky:
---
ReAct 框架:
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

**色彩编码：** 不同的颜色被用于区分流程的不同阶段和组件，如蓝色代表输入，绿色代表智能体内部和最终输出，黄色代表推理（THOUGHT），橙色代表外部行动（ACTION），红色代表外部观察（OBSERVATION），有助于您区分这些概念。

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/ReAct-Diagram.webp)

### 1. 摘要

这张图表是一个完整的 Excalidraw 风格架构图，旨在介绍 ReAct（Reasoning and Acting，推理与行动）提示范式。它直观地展示了 LLM 智能体如何将自身的内部推理（思维）与外部工具（行动）结合起来，以解决复杂的任务，并在此过程中不断迭代、减少幻觉、提高结果的准确性和可解释性。

### 2. 核心组件与阶段

图表包含四个主要区域：

- **‘OVERVIEW: REACT VS. OTHERS’ (左上)**：对比了三种主要的提示方法（标准提示、思维链 CoT、ReAct）。它强调了 ReAct 的关键优势：通过外部接地（External Grounding）实现的动态推理和基于事实的结果。
- **‘THE CORE ReAct LOOP’ (中部)**：这是核心部分，展示了一个多步迭代的循环。
    - **'[USER INPUT]' (红色)**：用户输入问题，标志着流程的开始。
    - **'[THOUGHT (REASONING)]' (黄色 thought bubble)**：LLM 进行内部推理，将任务分解，制定计划。
    - **'[ACTION (ACTING)]' (蓝色 rectangular box)**：基于推理，智能体生成具体的工具请求（例如：搜索查询或计算指令）。
    - **'[EXTERNAL ENVIRONMENT / TOOLS]' (灰色云)**：系统执行工具（如 Google 搜索、计算器、Python 解释器），并将结果作为“观察”返回。
    - **'[OBSERVATION (FEEDBACK)]' (绿色 speech bubble)**：LLM 接收外部反馈，将其添加到上下文，并更新内部状态。
    - 这个循环（Thought -> Action -> Observation）会重复进行（由中间的箭头和“... (Repeat N times)”表示），直到任务完成。
    - **'[FINAL ANSWER]' (紫色 star)**：在最后一步 Thought 中，智能体决定任务已完成，并生成最终答案。
- **‘COMPONENTS & INTERACTIONS’ (右上)**：清晰地划分了系统架构。
    - **'[LLM AGENT (BRAIN)]' (黄色)**：负责 Thought 的生成、Action 的规划和 Observation 的解析。
    - **'[TOOLS (EXTERNAL)]' (蓝色)**：智能体可以访问的外部服务（如 APIs、搜索）。
    - **'[SYSTEM / ENVIRONMENT]' (绿色)**：负责工具的执行、错误处理和观察结果的格式化。箭头显示了从智能体发送请求和从环境接收观察的流程。
- **‘END-TO-END WORKFLOW EXAMPLE’ (底部)**：一个详细的、分步的示例。
    - 通过查询“What is the sum of populations of New York City and Los Angeles in 2024?”（2024年纽约市和洛杉矶的人口之和是多少？），这个时间轴式的工作流展示了智能体如何经历 4 次完整的 Thought-Action-Observation 循环。它清晰地追踪了每次迭代中：
        - `Iteration N: [Thought] ... -> [Action] ... -> [Observation] ...`
    - 直到 `[Final Step]` 的 `[Final Answer]` 给出计算结果“12.1 million”。

### 3. 流程/逻辑解释

ReAct 的核心逻辑是：

1. **推理与行动交替**：LLM 智能体不只是生成一个静态的思维链，而是交替地进行内部推理和外部行动。
2. **动态规划**：智能体不会预先制定一个完美的、固定的计划。相反，它的计划是动态的。每次“观察”都会提供新的信息，从而更新智能体对任务状态的理解，并指导其下一步的推理和行动。
3. **接地与可解释性**：每一个“行动”都将推理过程“接地”到外部现实中（例如，获取实时数据或进行精确计算），从而显著减少了 Hallucination（幻觉）。同时，整个流程（Thought -> Action -> Observation）是完全透明的，这使得智能体的决策过程非常容易理解和调试。

### 4. 颜色编码说明

图表使用了一套有意义且一致的颜色 palette，以帮助视觉理解：

- **红色**：用于标记“User Input”（用户输入）和“Query”（查询），表示流程的起始边界。
- **黄色/橙色**：用于标记所有“Thought”（推理/思维）阶段、 thought bubble 风格和“LLM Agent (Brain)”，表示智能体的内部操作和规划。
- **蓝色**：用于标记所有“Action”（行动/工具请求）阶段、 tool belt/tool icons 和“Tools (External)”，表示智能体对外部世界的交互。
- **绿色**：用于标记所有“Observation”（观察/反馈）阶段、 document icon 和“System / Environment”，表示从外部世界获得的结果。
- **紫色/星形**：用于标记“Final Answer”（最终答案），表示任务完成和最终输出。
- **灰色**：用于连接箭头、一般结构框和流程中的中性元素（如“External Environment / Tools”云）。

通过这种一致的颜色编码，用户只需看一眼就能分辨出哪个部分是智能体的推理、哪个部分是外部行动、以及哪个部分是反馈。