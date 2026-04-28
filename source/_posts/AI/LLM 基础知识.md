---
title: LLM 基础知识
tags: []
categories:
  - AI
hidden: false
updated: '2026-03-25 22:54'
abbrlink: b4688e1e
date: 2026-03-16 23:25:16
cover:
sticky:
---
## Transformer

> [!info]
> 在 2007 年由 Google 提出的神经网络架构，基于 Self-Attention 来构建。

- Transformer 本质上是一个**高并发、无状态、基于权重路由**的特征聚合引擎
- Transformer 的核心机制是 self-attention
- LLM 是 Transformer 架构在海量数据和巨大参数量下的工程实现

### Self-Attention

> [!info]
> Self-Attention是所有现代大模型的“灵魂”。它的核心作用是让模型在处理一个词时，能够**同时观察到句子中其他所有的词**，并判断哪些词对理解当前词最重要。

- **联系点：** 它解决了长距离依赖问题。比如在句子“猫太胖了，因为它吃得太多”中，Self-Attention 能让模型明确知道“它”指代的是“猫”。
- **数学逻辑：** 它通过计算 Query ($Q$)、Key ($K$) 和 Value ($V$) 的点积来分配权重。公式表达为：   $$\text{Attention}(Q, K, V) = \text{softmax}\left(\frac{QK^T}{\sqrt{d_k}}\right)V$$
在 Java 中，我们从 Map 中找数据时，通过给定的 key，来找到对应的 value，这属于**硬匹配 (Hard Attention)**, 具备 100%的确定性。
但在自然语言的世界中，词与词之间是模糊关联的。Self-Attention 的核心是，将 Map 的概念升级为了**软性检索 (Soft Attention)**.

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/Self-Attention.webp)

这个图表全面展示了自注意力机制（Self-Attention Mechanism），也称为缩放点积注意力（Scaled Dot-Product Attention）的完整工作流程，这是 Transformer 模型的核心组成部分。

#### 主要组件和阶段：

1. **输入嵌入 X（Input Embedding X）**：
    
    - 这是初始的输入序列，包含多个标记（Tokens）。
    - 每个标记（如 Token 1, Token 2）都被转换为向量表示。
        
2. **查询（Q）、键（K）、值（V）路径（Query, Key, Value Paths）**：
    
    - **查询（Q）**：蓝色。表示当前标记正在“寻找”什么。
    - **键（K）**：绿色。表示标记的“身份”或它能提供什么。
    - **值（V）**：橙色。表示标记的“实际内容”。
    - 输入 X 通过三个独立的线性变换（Projection Matrices）生成这三个矩阵：Q, K, V。
        
3. **注意分数（Attention Scores）**：
    
    - 通过计算 **查询（Q）** 和 **键的转置（K^T）** 的点积（MatMul）来生成。这反映了序列中每对标记之间的相关性或重要性。
        
4. **缩放（Scaling）**：
    
    - 将注意分数除以一个缩放因子（d_k 的平方根，即键向量维度的平方根），以防止分数过大。
        
5. **Softmax**：
    
    - 对缩放后的分数应用 Softmax 函数，将其转换为概率分布（Attention Weights）。这些权重表示在生成当前标记的输出时，应该对序列中其他每个标记给予多少“注意力”。
        
6. **加权求和（Weighted Sum of Values）**：
    
    - 最后，将 **注意力权重（Attention Weights）** 与 **值（V）** 矩阵进行点积（MatMul）。
    - 这会产生每个标记的 contextualized embedding，它是整个序列中相关信息的加权组合。
        
7. **自注意力输出 Z（Attention Output Z）**：
    
    - 这是最终的输出序列，每个标记的表示都融入了整个序列的上下文信息。

## Token

> [!info]
> 大模型计算资源的**计费单元**和**内存分配单元**
## Context Window

> [!info]
>  
>  大模型在一次交互中，能够处理的最大 Token 数量。

### 组件

Context Window includes:
- User Prompt
- System Prompt
- Tool Definitions (System Tools, MCP metadata, Skill metadata)
- Tool Output
- Conversation history (短期记忆)
- RAG 检索的向量文档（长期记忆)
- Response

### Context Window 是 Agent 设计的核心约束

在构建 Agent 系统时，Context Window 就是你的**物理瓶颈**，类似于单台服务器的物理内存。它从以下四个维度死死卡住了 Agent 的工程化上限：

#### 记忆OOM
Context window 的容量有限，而一个成熟的 agent，需要短期记忆（**对话上下文**）+长期记忆（**RAG 检索的向量文档**），若一味的往里塞，很容易爆表 OOM。因此还需要为 agent 设计记忆机制，例如保留 System prompt，对历史对话进行**滑动窗口截断 - 类似 FIFO**, 或者用一个小模型对历史对话进行压缩，摘要。

#### 计算复杂度带来的接口超时
Transformer 架构底层的自注意力机制，其计算复杂度相对于 Token 的数量，是平方级别的增长。若 token 越多，耗时就越长。

#### 中间迷失 Lost in the Middle

大模型对于长文的内容理解，会出现**只记住开头和结尾，忽略中间**的情况，这边是中间迷失。

>  工程映射：在 RAG 架构中，做好 Document Chunking 和 Re-ranking，只把最核心的 Top-k 喂给大模型，只给重点，减少噪声信息。

#### 工具调用（Tool Calling / ReAct）的“常量池”开销

Agent 具有可调用外部工具的能力，但是每个 tool 需要提供 metadata（函数描述，参数声明等信息），光是工具描述，便要占用 context window 不少的内容，这样留给实际业务的空间也不多了。

## Prompt Engineering

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/prompt-engineering-arch.webp)

### 上下文设计

#### 1. Zero-shot (零样本)：裸调底层 JDK 原生方法

**概念：** 不给模型提供任何示例，直接抛出任务指令，完全依赖模型在预训练阶段（Pre-training）吸收的世界知识来直接作答。

> **⚙️ 跨界类比 (Analogy Binding)：**
> 
> Zero-shot 就像是你直接调用了 JDK 底层的 `Math.random()` 或者不带任何自定义配置的 `new ObjectMapper()`。你没有给它注入任何自定义的 `Serializer`，你指望它依靠“出厂设置”就能完美理解你那极其复杂的嵌套 DTO。

- **工程化痛点：** 确定性极差。对于通识性问题（比如“写一段冒泡排序”），Zero-shot 表现很好。但对于带有强业务 Domain 属性的格式化提取（比如“从这段案情描述中提取原告、被告并输出特定的 JSON 结构”），Zero-shot 极易出现我们上一节提到的幻觉或格式错误。

#### 2. Few-shot (少样本)：基于 In-context Learning 的 Mock 注入

**概念：** 在 Prompt 中提供少量的（通常 1~5 个）“输入-输出”示例（Demonstrations），然后再给出实际的问题。模型会通过“上下文学习（In-context Learning）”瞬间捕捉到示例中的模式（Pattern），并应用到新问题上。

> **⚙️ 跨界类比 (Analogy Binding)：**
> 
> Few-shot 的本质就是 **TDD (测试驱动开发)** 与 **Mock 数据注入**。
> 
> 你不仅定义了接口（Instruction），你还提供了一组 `@ParameterizedTest` 的测试用例。大模型在阅读这些用例时，就像 Spring 容器在启动时动态解析 `@Bean` 的依赖关系一样，它会在其 Transformer 的注意力机制中，动态建立起你期望的映射规则（Mapping Logic）。

- **工程化视角：**
    - **规范输出结构：** 这是约束大模型输出特定 JSON/XML 格式最有效的手段。
    - **Token 成本：** 引入 Few-shot 会显著增加 Context Window 的消耗。你的示例越长，你的 API 调用成本和耗时就越高。

### 推理范式
#### 1. Chain-of-Thought, CoT (思维链)：开启 DEBUG 级别的堆栈追踪

**概念：** 强制要求大模型在给出最终答案之前，必须一步一步地写出中间的推理过程（例如加上一句经典的 “Let's think step by step”）。

> **⚙️ 跨界类比 (Analogy Binding)：**
> 
> 对于复杂的数学题或逻辑推理，如果你让大模型直接输出答案，就好比你让 JVM 在 $O(1)$ 的时间复杂度内算出一个极其复杂的哈希碰撞结果——大概率会算错。
> 
> **CoT 的本质，就是迫使大模型将 $O(1)$ 的隐式计算，展开为 $O(N)$ 的显式状态转移。** 它等同于你在 Java 代码中开启了 `DEBUG` 级别的日志打印，或者记录了详细的线程 `Stack Trace`。每输出一个中间步骤的 Token，大模型就相当于把当前的状态暂存到了上下文（内存）中，供下一步推导使用。

- **工程化视角：**
    - **Time-to-Compute 换 Accuracy：** CoT 是一种典型的“以算力换准确率”的架构设计。
    - **延迟灾难 (Latency Disaster)：** 在生产环境中，让模型输出长篇大论的思考过程会导致整体响应时间（Total Response Time）急剧飙升。用户可能要等 10 秒才能看到最终的结论。

#### 2. ToT (Tree of Thoughts / 思维树)：大模型的“分支预测与回溯”

**概念：** 允许大模型在每一步推理时，生成多个不同的“分支（Thoughts）”，系统会评估这些分支的质量，保留高分分支继续向下展开，舍弃低分分支（剪枝）。如果发现此路不通，可以回溯（Backtrack）到上一个节点重新选择。

- **⚙️ 跨界类比：** * 在算法层面，这就是经典的 **DFS/BFS（深度/广度优先搜索）结合启发式剪枝**（比如走迷宫或八皇后问题）。
    - 在架构层面，这就像是数据库引擎在执行复杂 SQL 时生成的**执行计划树（Execution Plan Tree）**，优化器会评估多条路径的 Cost，选择代价最小的路径。
- **工程化痛点：** 极度昂贵！一次 ToT 推理可能需要对大模型发起数十次相互依赖的 API 调用。你的并发连接池、Token 计费将面临巨大压力。

#### 3. GoT (Graph of Thoughts / 思维图)：大模型的“并发协同与流处理”

**概念：** 现实世界的思考不仅是树状的，还会产生交叉和融合。GoT 允许不同的思维节点进行合并（Synergy）、循环（Loop）和精炼。节点 A 和节点 B 的局部结论，可以汇聚成节点 C 的输入。

- **⚙️ 跨界类比：**
    - 这不就是我们后端最熟悉的 **DAG (Directed Acyclic Graph，有向无环图) 任务调度框架**吗？（如 Apache Airflow 或 DolphinScheduler）。
    - 或者在 Java 中，这就是基于 `CompletableFuture` 的复杂任务编排：`CompletableFuture.allOf(taskA, taskB).thenApply(...)`。你可以让 Agent 派生出多个并行的子任务去分析客诉的不同维度，最后用一个 Reduce 节点将结论合并。

---

### 输出约束

在 Prompt Engineering 中，结构化输出是将 LLM响应接入工程系统的关键技术，核心目标是让模型输出可被程序直接消费的格式：
- JSON Mode — 最简单，强制输出合法 JSON，但只保语法、不保字段完整，需配合Pydantic等做二次校验
- Function Calling — 通过定义工具Schema，让模型解析意图并填充参数，代码再执行实际逻辑，是构建 Agent 的基础
- Structured Outputs — OpenAI 最新方案，`json_schema + strict: true`
  提供最强约束，字段类型和必填项均由 Schema 保证
- Schema 设计是核心 — description 影响模型理解，enum 限制取值可有效减少幻觉，required只标真正必填字段
- 选型原则 — 简单提取用 JSON Mode，多工具/多步骤用 Function Calling，强类型系统对接用Structured Outputs
## 智能体范式

- ReAct：执行thought -> action -> observe 动态循环，模拟人类解决问题的方式，方便地利用外部的工具，直至 LLM 认为任务结束。
- Plan - and - Solve: 先规划后执行，擅长解决需要多部推理的场景，将复杂的场景逐步拆解成清晰的步骤进行执行
- Reflection（自我反思和迭代）：引入 **执行 -> 反思 -> 优化**的迭代循环，显著提升解决方案的质量。

![img](https://raw.githubusercontent.com/datawhalechina/Hello-Agents/main/docs/images/4-figures/4-4.png)

### 对比

ReAct：摸着石头过河，思考和行动是高度交织、步步紧扣的。
Plan - and - Solve: 思考与行动是解耦的，前期进行思考，输出 plan，随后进入纯 Solve 模式，按部就班完成每一步
Reflection: 不是指导行动的第一范式，强调在执行之后，加入一次回顾性思考，找到错误并修正，并发起一轮新的行动

### Reflection 机制如何与 Plan-and-Solve、ReAct 协作？

在实际的智能体系统中，**Reflection 并不是一个孤立存在的执行范式，而是一个建立在 ReAct 或 Plan-and-Solve 基础之上的高阶“元控制”回路。** 它们之间的协作关系完美地体现在 Reflection 的“三步走”工作流中：

#### 1. 执行阶段 (Execution)：ReAct / Plan-and-Solve 负责“打草稿”

Reflection 机制发挥作用的前提是必须有一个“初稿”。这个初稿正是由 ReAct 或 Plan-and-Solve 跑完一轮后生成的初步解决方案或行动轨迹。

- **与 ReAct 协作：** 智能体先通过 ReAct 循环不断调用工具尝试解决问题。例如，智能体试图写一段爬虫代码，通过 ReAct 调用测试工具后发现报错，将这段含有缺陷的行动与报错轨迹保留下来。
- **与 Plan-and-Solve 协作：** 智能体通过 Planner 制定计划，并由 Executor 逐步推导得出一个初步答案（比如一道复杂数学题的解题过程及答案）。

#### 2. 反思阶段 (Reflection)：针对执行结果进行“内部评审”

ReAct 和 Plan-and-Solve 都是**一次性**的任务执行链路——一旦输出了最终答案（即使是错的），工作流就结束了。并且，ReAct 极度依赖外部工具的反馈（Observation），如果工具返回无用信息，ReAct 就容易陷入死循环。

而 Reflection 机制此时作为“评审员”介入协作：

- 它脱离了单纯对外部工具的依赖，调用模型从**内部逻辑维度**审查 ReAct 或 Plan-and-Solve 刚刚产出的“初稿轨迹”。
- 它会专门检查是否存在事实性错误、逻辑不连贯、关键约束遗漏，或者方案是否过于低效（例如发现 Plan-and-Solve 生成的 Python 代码时间复杂度是 $O(n^2)$），然后生成结构化的“反馈意见（Feedback）”。

#### 3. 优化阶段 (Refinement)：带着反馈重新触发执行

最后，Reflection 机制将原始任务、前两者的执行初稿，以及刚刚生成的评审反馈融合在一起，构建成全新的上下文（利用文章中提到的 `Memory` 模块管理）。

- 智能体带着这些极具针对性的反馈，**再次触发** ReAct 去寻找新工具，或者要求 Plan-and-Solve 重新规划一套更优的执行路径，生成“修订版”。
- 这个过程会多次迭代，直到反思阶段找不出新问题为止。

**总结来说：**

如果把解决复杂问题比作写一篇文章，**Plan-and-Solve** 是在列大纲并按章节起草，**ReAct** 是在边查资料边撰写内容。而 **Reflection** 则是写完后的“校对和审稿机制”。Reflection 将原本单向执行的 ReAct 和 Plan-and-Solve 包裹进了一个持续迭代优化的循环中，显著提升了智能体处理复杂任务的成功率和结果质量。



![[LLM 基础知识.png]]


![[LLM 基础知识2.png]]

![[LLM 基础知识3.png]]