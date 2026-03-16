---
title: KV Cache
tags: []
categories:
  - AI
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: false
updated: '2026-03-16 15:01'
abbrlink: 10d86b97
date: 2026-03-16 14:39:31
sticky:
---

> [!Important]
> - Query, Key, Value
> - self-attention: 自注意力机制

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/KV-Cache.webp)

本图表详细解释了大型语言模型（LLM）推理过程中的 **KV-Cache（Key-Value Cache，键值缓存）** 机制。该机制是提高 LLM 生成速度的核心技术，它通过避免重复计算来加速 token 的生成。

### 图表结构与流程

图表分为四个主要部分，从宏观到微观展示了 KV-Cache 的全貌：

1. **LLM 推理概览 (LLM Inference Overview)**：
    
    - 展示了 LLM 生成文本的基本过程。输入提示（Prompt）后，模型会逐个生成 token。生成一个 token 后，它会与之前的输入一起再次输入模型，以生成下一个 token。这是一个循环过程。
        
2. **对比：无与有 KV-Cache (Comparison: Without vs. With KV-Cache)**：
    
    - **无 KV-Cache（左侧红色区域）**：在生成第 3 个 token 时，模型必须重新计算**所有**先前 token（Token 1 和 Token 2）的自注意力矩阵（Q, K, V）。图中使用红色虚线和文本强调了这种“重新计算”导致的低效和高延迟（Latency: O(N^2)）。
    - **有 KV-Cache（右侧绿色区域）**：在生成第 3 个 token 时，模型只需要计算**当前新 token** 的 Q, K, V。然后，它会直接从 [KV-Cache 存储器] 中“**读取**”之前所有 token 的 K 和 V 矩阵，将它们与新 token 的 K, V 拼接。这样就极大地减少了计算量，实现了低延迟（Latency: O(N)）。
        
3. **KV-Cache 的详细机制 (The KV-Cache Mechanism in Attention)**：
    
    - 这一部分是核心，详细说明了缓存的运作。
    - **阶段 1：预填充 (Prefill - Prompt Processing)**：当模型第一次处理完整的 Prompt 时，它会计算所有输入 token 的 Q, K, V 矩阵。所有计算出的 K 矩阵（**蓝色**）和 V 矩阵（**绿色**）都被**存储**到 [KV-Cache] 中。
    - **阶段 2：解码 (Decode - Token Generation)**：当生成新的 token 时：
        - 模型仅计算新 token 的 Q_new, K_new, V_new。
        - 在**注意力步骤**中，新 token 的 `Query` (Q_new) 会关注从缓存中读取的**所有旧的 K、V 矩阵**（K_cache, V_cache）以及自己的 K_new, V_new。图中的“拼接”操作形象地展示了这一点。
            
4. **KV-Cache 总结表 (KV-Cache Summary)**：
    
    - 图表右下角的表格清晰地对比了有无 KV-Cache 的关键指标：
        - **每个 Token 的计算量**：O(1)（有）vs O(N)（无），N 为 Token 数。
        - **KV 存储**：N 个 Token（有）vs 无（无）。
        - **速度**：快（有）vs 慢（无）。
        - **内存使用**：高（有）vs 低（无）。

### 总结

总而言之，KV-Cache 是一种**空间换时间**的策略。它利用内存存储了先前计算过的 Key 和 Value 矩阵，从而在推理的每一步解码过程中，只需计算一个新 token 的值。这种设计显著降低了计算量，是使 LLM（如 ChatGPT）能够实时生成文本的关键技术。

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/kv-cache-qkv.webp)

本图表详细解释了在大型语言模型 (LLM) 推理过程中，**Key-Value Cache (KV-Cache)** 机制是如何利用和存储 Query (Q)、Key (K) 和 Value (V) 向量，从而实现高效生成的。

### 图表结构与流程

图表分为三个主要部分，从对比的角度展示了 KV-Cache 的全貌：

1. **无 KV-Cache 的 LLM 推理（慢速） (LLM INFERENCE WITHOUT KV-CACHE (SLOW))**：
    
    - 展示了在生成多个 token 时，模型必须为每一个新 token 重新计算**所有**先前 token 的 K 和 V 矩阵。
    - 例如，在生成第 3 个 token (T3) 时，模型必须再次计算 (Prompt, T1, T2) 的 K 和 V。这种“重新计算”随着生成序列的变长，计算量会呈二次方增长 (Quadratic Cost)，从而导致延迟非常高。红色文本强调了这一点：**SLOW & INEFFICIENT**。
        
2. **有 KV-Cache 的 LLM 推理（快速） (LLM INFERENCE WITH KV-CACHE (FAST))**：
    
    - 展示了核心优化机制。模型会“记住”先前 token 的计算结果，将其存储在 **KV-Cache** 中。
    - **步骤 1 (T1 生成)**：模型计算 Q1, K1, V1。然后，它会将 $K_1, V_1$ **存储**在 [KV-Cache] 存储器中（图中使用数据库图标表示）。
    - **步骤 2 (T2 生成)**：当生成新的 T2 时，模型**只计算新 token** (T2) 的 Q2, K2, V2。然后，它从 [KV-Cache] 中直接**读取**之前存储的 $K_1, V_1$。
    - 在自注意力机制中，Q2 只会关注新计算的 K2 和 V2，以及从缓存中读取的 $K_1, V_1$，而无需重新计算 T1 的 K、V。这种方法实现了线性计算成本 (Linear Cost)。绿色文本强调了这一点：**FAST & EFFICIENT**。
        
3. **KV-Cache 自注意力机制的详细内部原理 (INSIDE THE SELF-ATTENTION BLOCK WITH KV-CACHE)**：
    
    - 这一部分是核心，详细说明了缓存的运作。
    - **输入**：新的输入 token (Ti) 和来自 KV-Cache 的先前 K、V ($K_{1 \dots i-1}, V_{1 \dots i-1}$)。
    - **模型计算**：从 Ti 派生出 $Q_i, K_i, V_i$。
    - **缓存更新 (UPDATE KV-CACHE)**：将新计算出的 $K_i, V_i$ **追加 (Append)** 到缓存中。
    - **注意力计算 (ATTENTION COMPUTATION)**：图中使用手绘的 Softmax 图标展示了注意力操作。
        - Q_i (Query) 与**所有** K 向量的点积：Attention 权重 = $\text{Softmax}(Q_i \cdot K_{\text{all}}^T / \sqrt{d})$。
        - 权重乘以**所有** V 向量：最终 Output Vector = 权重 $\cdot V_{\text{all}}$。
        - 图表中明确指出 $K_{\text{all}}$ 是缓存 $K_{1 \dots i-1}$ 和新 $K_i$ 的拼接，同样的，$V_{\text{all}}$ 也是拼接。

### 总结

总而言之，KV-Cache 是一种将先前 token 的 K 和 V **矩阵存储在内存中**的优化技术。这样，在推理的每一步解码过程中，只需计算一个新 token 的值，极大地降低了计算量，从而加速了 LLM 的生成速度。

![img](https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/articles/Kv-cache-llm.webp)

# Q K V

可以把 **KV-cache** 里的 **Q / K / V** 理解成注意力机制里的三种“角色”：

- **Q（Query）**：当前 token 想“查什么”
- **K（Key）**：每个历史 token 提供的“索引/标签”
- **V（Value）**：每个历史 token 真正携带的“内容”

---

## 1. 先从类比理解

想象你在图书馆找资料：

- **Q**：你手里的检索需求  
  > “我要找和‘法国首都’相关的信息”
- **K**：每本书的目录卡/标签  
  > “地理”“欧洲”“法国”……
- **V**：书里真正的内容  
  > “巴黎是法国首都”

流程就是：

1. 用 **Q** 去和所有 **K** 做匹配
2. 看哪些 **K** 最相关
3. 把这些相关位置对应的 **V** 加权取出来

这就是 attention 的核心。

---

## 2. 在 Transformer 里它们怎么来的

对每个 token 的隐藏状态 \(x\)，模型会通过三组不同的线性变换得到：

\[
Q = xW_Q,\quad K = xW_K,\quad V = xW_V
\]

所以：

- **Q**：表示“这个位置现在要关注什么”
- **K**：表示“这个位置能被怎样检索到”
- **V**：表示“这个位置要贡献什么信息”

注意力分数一般是：

\[
\text{Attention}(Q, K, V) = \text{softmax}\left (\frac{QK^T}{\sqrt{d_k}}\right) V
\]

含义：

- \(QK^T\)：算相似度
- softmax：变成权重
- 再乘 \(V\)：把内容按权重聚合

---

## 3. 为什么推理时只缓存 K 和 V，不缓存 Q？

这是 **KV-cache** 最关键的问题。

在自回归生成里，模型是一个 token 一个 token 往后生成：

- 第 1 步生成第 1 个新 token
- 第 2 步生成第 2 个新 token
- ……

当生成当前位置时：

- 当前 token 的 **Q** 只用于“这一次查询”
- 历史 token 的 **K / V** 会被后续所有步骤反复使用

所以：

- **Q**：每一步都重新算，没必要缓存
- **K / V**：历史不变，后面一直要用，缓存起来最划算

因此叫 **KV-cache**，而不是 QKV-cache。

---

## 4. 一个更直观的生成过程

假设上下文是：

> “The capital of France is”

现在模型要预测下一个词。

### 已有历史 token
每个历史 token 都已经生成了自己的：

- \(K_1, V_1\)
- \(K_2, V_2\)
- ...
- \(K_t, V_t\)

这些会被存进 cache。

### 当前步骤
模型对当前位置算出当前的 **Q_t**

然后：

1. 用 \(Q_t\) 和历史所有 \(K_1... K_t\) 做匹配
2. 得到注意力权重
3. 对应加权汇总 \(V_1... V_t\)
4. 得到当前上下文表示
5. 预测下一个 token，例如 `Paris`

生成完这个新 token 后，再为它计算自己的 **K, V**，追加到 cache 里，供下一步使用。

---

## 5. 为什么 KV-cache 能加速

如果没有 cache，每生成一个新 token，都要对之前所有 token 重新计算 K 和 V。

例如已经有 1000 个 token：

- 生成第 1001 个 token 时
- 如果不缓存，要把前面 1000 个 token 又过一遍，重新算 K/V
- 很浪费

有了 KV-cache：

- 前面 1000 个 token 的 K/V 已经算好了
- 这一步只需要算新 token 的 Q，以及新 token 的 K/V
- 再拿 Q 去跟缓存里的 K 做 attention

所以它主要节���的是 **重复计算**。

---

## 6. 但为什么它会占显存？

因为你要把每一层、每个 head、每个历史位置的 K/V 都存下来。

缓存大小大致和这些因素成正比：

- batch size
- 序列长度
- 层数
- attention heads
- hidden dimension
- 数据类型（fp 16 / bf 16 / fp 8 等）

所以常见现象是：

- **KV-cache 提升速度**
- **但会增加显存占用**

这也是长上下文推理很吃显存的重要原因之一。

---

## 7. Q / K / V 的“本质理解”

可以这么记：

- **Q = 我现在想找什么**
- **K = 你这里能提供什么索引**
- **V = 你这里真正提供什么内容**

注意力不是“把所有历史都平均看一遍”，而是：

> 当前 token 拿着自己的 Q，去历史 token 的 K 里检索，然后把对应的 V 取回来。

---

## 8. 一个常见误区

### 误区：K 和 V 是“固定语义”
不完全对。

虽然可以直观理解成：

- K 像标签
- V 像内容

但它们本质上都是模型学出来的向量投影，不一定能严格对应自然语言中的“标签”和“正文”。这只是帮助理解的比喻。

### 误区：Q 不重要，因为不缓存
也不对。

**Q 非常重要**，只是它的生命周期很短：

- 只服务当前这一步的注意力计算
- 用完就没必要留了

---

## 9. 一句话总结

**在 KV-cache 中：Q 是当前查询，K 是历史位置的可匹配索引，V 是历史位置承载的��息；推理时缓存 K/V 是因为它们会被反复复用，而 Q 每一步都要重新生成。**

如果你愿意，我还可以继续给你讲：
1. **prefill 和 decode 阶段里 KV-cache 的区别**
2. **为什么 attention 复杂度会从重复计算中受益**
3. **从代码实现角度看 KV-cache tensor shape 是什么样的**