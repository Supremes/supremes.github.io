---
title: 深挖 · Agent 运行机制（Q5-9）
date: 2026-08-21
tags: [interview, agent, tool-use, react, agent-loop]
---

> 速答版见 [[00-面试速答总览]]。这五题是整套题里区分度最高的部分 —— **答得出消息结构和 `stop_reason`，就说明是实现过 Agent 而不只是用过。**

---

# Q5 · 一次 Agent 请求从用户输入到最终回答的完整链路是什么？

## 一张图先立住骨架

```
   用户输入
      │
      ▼
 ┌─────────────┐
 │ 1. 入口层    │  鉴权、限流、会话路由
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │ 2. 上下文组装 │  system + tools + 历史 + 检索 + 当前输入
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │ 3. 预算检查   │  token 计数 → 超了就压缩/裁剪/compaction
 └──────┬──────┘
        ▼
 ┌─────────────┐
 │ 4. 调用 LLM  │◄─────────────────┐
 └──────┬──────┘                  │
        ▼                         │
   看 stop_reason                  │
    ├── end_turn ──────► 出答案     │
    └── tool_use                   │
            │                      │
            ▼                      │
     ┌─────────────┐               │
     │ 5. 执行工具  │  校验→gate→跑  │
     └──────┬──────┘               │
            ▼                      │
     ┌─────────────┐               │
     │ 6. 结果回灌  │───────────────┘
     └─────────────┘
```

## 逐段展开

### 1. 入口层

前端 → 网关 → Agent 服务。这层做鉴权（见 [[05-网络与鉴权]]）、限流、会话路由。输入可能是文本、图片、文件 —— 多模态输入要在这一层做格式转换和大小校验。

### 2. 上下文组装（context assembly）

这是整条链路里**最能体现工程水平**的一步。要往上下文里放的东西按顺序是：

| 顺序 | 内容 | 为什么是这个位置 |
|---|---|---|
| 1 | 工具定义 `tools` | 最稳定，放最前面利于 prompt cache |
| 2 | `system` prompt | 次稳定 |
| 3 | 历史消息 | 逐轮追加，前缀稳定 |
| 4 | 检索到的知识 | 每次都变 |
| 5 | 当前输入 | 最易变，放最后 |

**排序原则是缓存**：prompt cache 是**前缀匹配**的，改动任何位置会让它后面的全部失效。所以稳定的放前面、易变的放后面。这条在 [[03-Coding-Agent-实践]] 的 Context Engineering 一节会展开。

### 3. 预算检查

调之前先数 token（用官方的 count_tokens 接口，别用第三方 tokenizer 猜）。超了有三种处理：

- **裁剪**：丢掉最老的消息 —— 简单但会丢关键信息
- **压缩 / compaction**：把早期对话摘要成一段 —— 保留信息密度
- **context editing**：只清理旧的 tool_result 和 thinking 块，保留对话结构

### 4. 调用 LLM

请求体的关键字段：`model`、`messages`、`tools`、`tool_choice`、`max_tokens`、thinking / effort 配置。

**这里必须强调一句：API 是无状态的。** 服务端不记得上一轮，每次请求都要把完整历史重新发一遍。所谓"对话记忆"完全是客户端在维护 `messages` 数组。

### 5-6. 工具执行与回灌

见下面的 Q7，这是重点。

### 流式输出

模型是逐 token 生成的，所以用 SSE 把 delta 实时推给前端（为什么是 SSE 不是 WebSocket，见 [[05-网络与鉴权]] Q18）。

注意一个体验细节：**工具执行期间没有 token 产出**，前端会显示"卡住"。所以要把「正在调用 XX 工具」也作为事件推出去。

### 收尾

- **Trace 落库**：一次完整运行是一个 Trace，每次 LLM 往返是一个 Turn（见 [[04-Agent-工程化评测]]）
- **计费**：累加各轮的 input / output / cache token
- **指标上报**：总延迟、TTFT、迭代轮数、工具调用次数与失败率

## 面试答题模板

> 从输入进来先做上下文组装 —— system、工具定义、历史、检索结果按缓存友好的顺序拼起来，数一遍 token 看要不要压缩。
> 然后调模型，**关键是看返回的 `stop_reason`**：`end_turn` 就出答案，`tool_use` 就去执行工具。
> 工具执行完把**完整的 assistant content 连同 `tool_result` 一起追加回 messages 数组**，再调一次模型 —— 因为 API 是无状态的，每轮都要重发全量历史。
> 这个循环转到 `end_turn`，或者撞到工程侧的熔断条件为止。
> 全程用 SSE 流式推给前端，最后落 trace、算 token 成本、报指标。

---

# Q6 · 大模型如何判断是否需要调用工具？

## 先破除一个误解

很多人以为模型内部有个"判断器"在决定要不要调工具。**没有。**

实际机制是：
1. 你传的 `tools` 数组会被**渲染成文本，拼进 prompt 的最前面**
2. 模型在训练时见过大量 tool-use 格式的数据
3. 于是"输出一个结构化的 `tool_use` 块"对它来说就是一种**合法的续写方式**
4. 它照常做 next-token prediction，只不过这次预测出来的是工具调用

**本质上和"预测下一个词"是同一件事。** 说清这点，比背一堆参数有用。

推论：既然工具定义在 prompt 最前面，那**中途增删工具会让整个 prompt cache 失效** —— 这是很多人踩过的坑，成本会突然翻好几倍。

## 影响判断的因素，按杠杆大小排

### 1. description 的质量（最大杠杆）

**要写「什么时候调用」，不只写「做什么」。**

```json
// 差 —— 只说了功能
{ "name": "get_weather", "description": "获取天气" }

// 好 —— 说了触发条件
{
  "name": "get_weather",
  "description": "获取指定城市的实时天气。当用户询问当前天气、气温、是否下雨，或者询问需要依赖天气判断的事情（比如要不要带伞、适不适合户外活动）时调用。不要用于历史天气或天气预报查询。"
}
```

后者不仅提高了该调时的命中率，**还通过一句「不要用于...」降低了误调用**。

### 2. input_schema 的清晰度

每个字段都要写 `description`，固定取值用 `enum`，真正必填的才放进 `required`。schema 模糊 → 参数幻觉。

需要强保证时开 `strict: true`（要求 `additionalProperties: false`），API 层面保证参数一定符合 schema。

### 3. tool_choice 参数

| 值 | 行为 | 用在哪 |
|---|---|---|
| `{"type": "auto"}` | 模型自己决定（默认） | 常规对话 |
| `{"type": "any"}` | 必须调至少一个工具 | 确定这轮就是要执行动作 |
| `{"type": "tool", "name": "x"}` | 强制调指定工具 | 结构化抽取、固定第一步 |
| `{"type": "none"}` | 禁止调工具 | 最后一轮只要总结 |

另外可以加 `disable_parallel_tool_use: true` 强制一轮最多一个工具。

### 4. 工具数量

工具太多会稀释注意力，模型选错的概率上升。两个解法：

- **tool search**：把工具标成 `defer_loading`，模型先搜索再加载需要的 schema。好处是**追加而非替换**，不破坏 prompt cache。
- **拆 agent**：不同职责的工具给不同的 subagent。

## 三种典型 failure mode

| 现象 | 根因 | 怎么修 |
|---|---|---|
| **该调不调** | description 没写触发条件 | 在 description 里写明"当用户...时调用" |
| **不该调乱调** | description 太宽泛，或工具间语义重叠 | 加否定条件；合并或重命名重叠的工具 |
| **参数幻觉** | schema 字段缺描述 | 补 description + `enum`；开 `strict: true` |

调这三个问题的顺序：**先改 description，再改 schema，最后才考虑改 system prompt。** 因为 description 离决策点最近。

---

# Q7 · Function Call 和 Tool Result 如何重新进入模型上下文？

## 一句话机制

**作为普通消息追加到 `messages` 数组里，下一轮整个重发。** 没有魔法，没有服务端状态。

## 完整的消息序列（Anthropic 格式）

```jsonc
[
  // 第 1 轮：用户提问
  { "role": "user", "content": "北京现在天气怎么样？" },

  // 模型返回 —— 注意 content 是数组，可能同时有 text 和 tool_use
  { "role": "assistant", "content": [
      { "type": "text", "text": "我查一下北京的天气。" },
      { "type": "tool_use",
        "id":   "toolu_01A09q90qw90lq917835lq9",   // ← 这个 id 是配对的钥匙
        "name": "get_weather",
        "input": { "location": "Beijing", "unit": "celsius" } }
  ]},

  // 你执行完工具，把结果作为 user 消息发回去
  { "role": "user", "content": [
      { "type": "tool_result",
        "tool_use_id": "toolu_01A09q90qw90lq917835lq9",  // ← 必须完全匹配
        "content": "晴，26°C，湿度 45%" }
  ]},

  // 模型拿到结果后给出最终回答
  { "role": "assistant", "content": [
      { "type": "text", "text": "北京现在是晴天，26 度，湿度 45%，挺舒服的。" }
  ]}
]
```

## 五个必须说对的细节

### 1. 必须回填完整的 `response.content`，不能只取 text

这是最高频的 bug：

```python
# ❌ 错 —— 只提取了文本，tool_use 块丢了
text = next(b.text for b in response.content if b.type == "text")
messages.append({"role": "assistant", "content": text})
# 下一轮发 tool_result 时，API 找不到对应的 tool_use → 400

# ✅ 对 —— 整块原样回填
messages.append({"role": "assistant", "content": response.content})
```

**记法：assistant 那条永远是原样回填，不做任何加工。** thinking 块、compaction 块也是同理 —— 加工了就出错。

### 2. tool_result 放在 `role: "user"` 里

这是 Anthropic 的设计。**对比 OpenAI 格式**（面试常问这个差异）：

| | Anthropic | OpenAI |
|---|---|---|
| 模型请求调用 | assistant 消息里的 `tool_use` 块 | assistant 消息的 `tool_calls` 字段 |
| 参数格式 | `input` 是**已解析的对象** | `arguments` 是**JSON 字符串**，要自己 parse |
| 结果回传 | user 消息里的 `tool_result` 块 | 独立的 `role: "tool"` 消息 |
| 配对字段 | `tool_use_id` | `tool_call_id` |
| 多个结果 | **全部塞进一条 user 消息** | 每个结果一条 tool 消息 |

### 3. 并行调用：所有结果必须在同一条消息里

一条 assistant 消息里可以有**多个** `tool_use` 块（模型判断这几个调用互不依赖）。

```jsonc
// ✅ 对 —— 三个结果放进同一条 user 消息
{ "role": "user", "content": [
    { "type": "tool_result", "tool_use_id": "toolu_A", "content": "..." },
    { "type": "tool_result", "tool_use_id": "toolu_B", "content": "..." },
    { "type": "tool_result", "tool_use_id": "toolu_C", "content": "..." }
]}
```

> [!warning] 拆开发的后果
> 把三个结果拆成三条 user 消息，API 不一定报错，但**你等于在示范「工具结果是一个一个回来的」**。模型会学到这个模式，之后就不再做并行调用了 —— 性能白白掉一大截，而且很难排查。

### 4. 失败也必须回，不能丢

```jsonc
{ "type": "tool_result",
  "tool_use_id": "toolu_01A",
  "content": "ConnectionTimeout: 连接 weather-api 超时（5s）",
  "is_error": true }
```

给出**信息量足够的错误文本**，模型能据此换个方式重试或者向用户说明。静默丢弃会让模型一直等一个永远不来的结果。

### 5. thinking 块要原样带回

开了 extended thinking 时，assistant content 里会有 `thinking` 块。**同一个模型继续对话时必须原样回传**，否则推理链断裂。换模型时对方会静默忽略，不用手动删。

## 为什么是这个设计

有人会问：为什么不让服务端记住工具调用状态？

因为**无状态是水平扩展的前提**。每个请求自包含，任何一台机器都能处理任何一个请求，不需要粘性会话、不需要共享存储。

代价是每轮都要重传全量历史 —— 这就是 prompt cache 存在的意义：**重传的是同一段前缀，缓存命中后成本降到十分之一**。

> 这个「无状态 + 自包含」的权衡，和 [[05-网络与鉴权]] 里 JWT vs Session 的权衡是**同一个思想**。面试时能把这两处串起来说，加分很多。

---

# Q8 · Agent Loop 在什么条件下继续执行，又在什么条件下结束？

## 分两层答：模型侧信号 + 工程侧熔断

只答第一层是不完整的。**光靠模型自己收敛不安全** —— 它可能反复调同一个工具、可能陷入自我怀疑循环、可能一路烧钱。

## 第一层：`stop_reason` 全枚举

| 值 | 含义 | 怎么处理 |
|---|---|---|
| `tool_use` | 模型要调工具 | **继续** —— 执行工具，回灌结果 |
| `pause_turn` | 服务端工具（web search 等）达到内部迭代上限 | **继续** —— 把当前 assistant 响应原样带上重发即可续跑，**不要额外加一条"请继续"的 user 消息** |
| `end_turn` | 正常说完了 | 结束，返回答案 |
| `max_tokens` | 撞到输出上限被**截断** | ⚠️ 提高 `max_tokens` 重试，或做续写。**绝不能当成正常结束** |
| `stop_sequence` | 命中自定义停止序列 | 按业务处理 |
| `refusal` | 安全拒绝 | 看 `stop_details.category`，走降级或提示用户 |

> [!danger] 最容易翻车的一条
> 只写 `while stop_reason == "tool_use"` 就循环、否则返回。
> `max_tokens` 会被当成正常结束 —— **用户拿到半截答案，系统还认为一切正常**，日志里干干净净什么都查不到。
> 正确做法是 `stop_reason` 每个分支都显式处理，`default` 分支要告警。

## 第二层：工程侧熔断（必须有）

| 熔断条件 | 典型阈值 | 防的是什么 |
|---|---|---|
| 最大迭代轮数 | 10-50 | 无限循环 |
| Token / 成本预算 | 按场景定 | 烧钱 |
| Wall-clock 超时 | 5-30 分钟 | 卡死 |
| 用户中断 | — | 用户改主意了 |
| 连续工具失败 | 3 次 | 下游挂了还在硬刚 |
| **重复调用检测** | 同样的 (tool, input) 出现 2-3 次 | 模型陷入死循环 |

**重复调用检测**是实践中最有用也最常被漏掉的一条。做法：对 `(tool_name, 规范化后的 input)` 做 hash，同一个 hash 短时间内重复出现就打断，并往上下文里注入一条提示："你已经用相同参数调用过这个工具，结果是 X，请换个思路。"

## 更聪明的做法：task budget

比硬性熔断更优雅的是给模型一个**它自己能看到的预算**。

硬性 `max_tokens` 是模型感知不到的墙 —— 撞上了就是硬截断。task budget 则是把「你还剩多少额度」告诉模型，让它**自己规划节奏、提前收尾**，而不是话说到一半被砍。

两者不冲突，通常一起用：task budget 让它优雅收敛，硬熔断兜最坏情况。

## 参考实现

```python
MAX_ITER = 25

def agent_loop(messages, tools):
    for i in range(MAX_ITER):
        resp = client.messages.create(model=MODEL, messages=messages,
                                      tools=tools, max_tokens=16000)
        messages.append({"role": "assistant", "content": resp.content})

        match resp.stop_reason:
            case "tool_use":
                results = execute_tools(resp.content)          # 全部执行
                messages.append({"role": "user", "content": results})  # 一条消息装全部
                continue
            case "pause_turn":
                continue                                        # 原样重发即可续跑
            case "end_turn":
                return extract_text(resp)
            case "max_tokens":
                raise OutputTruncated("输出被截断，需要提高 max_tokens 或续写")
            case "refusal":
                return handle_refusal(resp.stop_details)
            case other:
                raise UnexpectedStopReason(other)               # 显式炸，别静默
    raise MaxIterationsExceeded(MAX_ITER)                       # 熔断
```

---

# Q9 · ReAct 是什么？

## 定义

**ReAct = Reasoning + Acting**（Yao et al., 2022）。核心是让模型**交替**产出推理和行动，而不是只做其中一个：

```
Thought:      我需要知道北京现在的天气
Action:       get_weather("Beijing")
Observation:  晴，26°C
Thought:      拿到了，可以回答了
Final Answer: 北京现在晴天 26 度
```

Thought → Action → Observation 循环，直到给出 Final Answer。

## 它解决了什么（讲清楚这个才算懂）

对比两个极端：

| 方案 | 问题 |
|---|---|
| **只有 Reasoning**（纯 CoT） | 推理链条再漂亮也接触不到外部世界。问"今天股价多少"必然瞎编 —— 它只能从参数里捞，捞不到就幻觉 |
| **只有 Acting**（直接调工具） | 没有推理环节，模型不做规划。工具乱调、调完不知道下一步、错了不会纠 |

**ReAct 的价值在于两者互相纠正**：
- 推理指导下一步该调什么工具（不乱调）
- 观察到的真实结果修正推理（不幻觉）

这个"互相纠正"是 ReAct 论文的核心贡献，不是"能调工具"本身。

## 早期实现：纯 prompt 工程

在原生 tool use 出现之前，ReAct 全靠文本模板硬撑：

```text
你可以使用以下工具：
get_weather(city) - 查询天气

请严格按以下格式回答：
Thought: <你的推理>
Action: <工具名>(<参数>)
Observation: <这里会被填入结果>
... 可以重复多轮 ...
Final Answer: <最终答案>
```

然后设 `stop_sequence = "Observation:"` 让模型停下，用**正则解析** `Action:` 那行，执行完把结果拼成 `Observation: xxx` 追加回去继续。

这套方案脆在哪：
- 模型少写个冒号、换个格式，正则就崩
- 参数是自由文本，得自己 parse，类型全靠猜
- 没法做并行调用
- 格式说明本身占大量 token
- 模型可能自己幻觉出 `Observation:` 一整段（因为它见过这个格式）

## 现在：原生 tool use 就是 ReAct 的工程化

| ReAct 概念 | 现代 API 对应 |
|---|---|
| Thought | `thinking` 块（extended thinking） |
| Action | `tool_use` 块（结构化，`input` 已经是对象） |
| Observation | `tool_result` 块 |
| 循环控制 | `stop_reason == "tool_use"` |
| Final Answer | `stop_reason == "end_turn"` 时的 `text` 块 |

**所以现代 API 的 tool use 循环，本身就是 ReAct。** 只不过：
- 结构化 block 取代了正则解析 → 不会因为格式抖动崩掉
- 支持并行 Action → 一轮能干多件事
- Thought 被模型训练内化了 → 不用在 prompt 里教格式

## 面试标准答法

> ReAct 是 2022 年提出的一个 agent 范式，让模型交替产出「思考 → 行动 → 观察」并循环。
> 它解决的是纯 CoT 只能在脑子里推、碰不到外部世界，和纯工具调用没有规划两个极端 —— **两者互相纠正**：推理决定调什么工具，工具结果修正推理。
> 早期是纯 prompt 工程，靠文本模板 + stop sequence + 正则解析，很脆。
> **现在原生 tool use 就是 ReAct 的工程化实现** —— `thinking` 块对应 Thought，`tool_use` 对应 Action，`tool_result` 对应 Observation，循环由 `stop_reason` 驱动。
> 所以现在不太会有人专门"实现一个 ReAct"，它已经是 Agent Loop 的默认形态了。

> [!tip] 加分点
> 主动指出「现在还手写 ReAct 文本模板是在开倒车」，说明你知道技术演进而不是在背 2023 年的教程。

---

## 相关

- [[00-面试速答总览]] · [[03-Coding-Agent-实践]] · [[04-Agent-工程化评测]] · [[05-网络与鉴权]]
