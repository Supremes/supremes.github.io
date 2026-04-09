# Spring AI `TextSplitter` 与 `TokenTextSplitter` 实现剖析

按项目当前使用的 **Spring AI 1.1.4** 来看，`TextSplitter` 和 `TokenTextSplitter` 的关系可以从第一性原理理解成两层：

1. **`TextSplitter` 负责“文档级契约”**：它不是单纯切字符串，而是一个 `DocumentTransformer`，本质接口是 **`Function<List<Document>, List<Document>>`**。`apply()` 会把每个 `Document` 拆成多个 chunk，并统一处理这些事情：
   - 复制原始 `metadata`
   - 过滤掉 `null` key/value（因为 `Document` 不允许 metadata 含 null）
   - 补充 `parent_document_id`、`chunk_index`、`total_chunks`
   - 继承原始 `score`
   - 默认复制父文档的 `ContentFormatter`（`copyContentFormatter=true`）
   - **不会保留父文档 id 作为子 chunk id**；它用 `Document.builder()` 新建 chunk，chunk 自己会生成新 id，父子关系靠 metadata 关联

   所以 `TextSplitter` 解决的是：**切分后，文档血缘和可追踪性怎么保住**。

2. **`TokenTextSplitter` 负责“按 token 尺寸切”**：它继承 `TextSplitter`，真正只实现了一个抽象方法：`splitText(String text)`。也就是说，Spring AI 把“怎么切文本”与“切完后怎么重新组装成 Document”分开了。

## `TextSplitter` 的实现重点

源码骨架很简单，但设计很稳：

- `TextSplitter implements DocumentTransformer`
- `apply(List<Document>) -> doSplitDocuments(...)`
- 先把输入文档拆成几列数据：`text / metadata / formatter / score / originalId`
- 再调用 `createDocuments(...)`
- 在 `createDocuments(...)` 里对每个原文执行 `splitText(text)`，然后为每个 chunk 新建 `Document`

这说明它的抽象边界非常明确：

- **子类只负责切文本**
- **父类负责文档装配和元数据延续**

这是个很好的抽象，因为大多数自定义 splitter 真正变化的只是“边界规则”，不是 `Document` 生命周期。

## `TokenTextSplitter` 的实现重点

它的默认参数是：

- `chunkSize = 800`
- `minChunkSizeChars = 350`
- `minChunkLengthToEmbed = 5`
- `maxNumChunks = 10000`
- `keepSeparator = true`
- `punctuationMarks = ['.', '?', '!', '\n']`

内部依赖：

- `jtokkit`
- 固定 tokenizer：`EncodingType.CL100K_BASE`

这意味着它的 token 计算是**偏 OpenAI 体系**的，不是“对所有 embedding model 都精确一致”。

### 它的实际算法不是“先按标点切”，而是：

1. 整篇文本先 encode 成 token 列表
2. 每轮先硬取前 `chunkSize` 个 token
3. decode 回文本 `chunkText`
4. 如果原始剩余 token **超过** `chunkSize`，才尝试在这个 chunk 里向后回退到最后一个标点
5. 只有当这个标点位置 `> minChunkSizeChars` 时，才真正截断到标点
6. 把当前 chunk 加入结果
7. 再把这个 chunk 对应的 token 从总 token 流里移除，继续下一轮
8. 最后处理剩余 token

所以本质上它是：

**“token fixed window + punctuation backtracking”**，不是严格的语义切分器。

## 几个非常关键的实现细节

1. **小文本不会因为有标点被提前截断**  
   只有 `tokens.size() > chunkSize` 才启用“找最后一个标点回退”的逻辑。测试里专门覆盖了这一点。

2. **标点只是回退边界，不是主导边界**  
   如果 chunk 内找不到合适标点，或者标点位置太靠前（`<= minChunkSizeChars`），它就直接硬切 token。

3. **`minChunkSizeChars` 是字符阈值，不是 token 阈值**  
   这是实现里的一个混合策略：主窗口按 token，回退判定按字符长度。

4. **`keepSeparator` 不是“保留所有分隔符”**  
   它主要影响换行处理：`true` 时保留 chunk 原貌再 `trim()`；`false` 时把 `System.lineSeparator()` 替换为空格。它不是一个通用 separator policy。

5. **最后一个 chunk 的换行处理和前面不完全对称**  
   剩余 token 的收尾逻辑里直接 `replace(System.lineSeparator(), " ")`，这和前面 `keepSeparator` 的逻辑并不完全一致。

6. **`maxNumChunks` 不是绝对硬上限**  
   `while` 循环受 `num_chunks < maxNumChunks` 限制，但循环结束后如果还有剩余 token，还会再追加一个“尾块”。所以它更像“最多迭代这么多次”，不是严格的最终 chunk 总数上限。

7. **没有 overlap**  
   对当前项目特别重要：**Spring AI 1.1.4 这个 `TokenTextSplitter` 没有 overlap 参数**。项目 `RagService` 注释里写了“500 tokens, overlap=50”，但从实际 builder 调用看，**真实运行时并没有 overlap**。

## 结合当前项目 `RagService` 的真实含义

当前配置：

```java
splitter = TokenTextSplitter.builder()
    .withChunkSize(500)
    .withMinChunkSizeChars(350)
    .withMinChunkLengthToEmbed(5)
    .withMaxNumChunks(10000)
    .withKeepSeparator(true)
    .build();
```

实际效果是：

- 目标 chunk 大小约 `500 tokens`
- 尽量在 `.` `?` `!` `\n` 处回退收口
- 太短 chunk 不入库
- **无 overlap**
- 每个 chunk 会自动带上 `parent_document_id / chunk_index / total_chunks`

所以如果真实目标是 **提升 RAG 召回连续上下文**，目前最大限制不是参数调得不够细，而是：**这个实现本身没有 sliding overlap**。

## 自定义 `TextSplitter`，最少需要做什么

如果目标只是自定义“切分规则”，**最短路径**是：

1. **继承 `TextSplitter`**
2. **实现 `protected List<String> splitText(String text)`**
3. 返回切好的纯文本 chunk 列表

最小骨架：

```java
public class MyTextSplitter extends TextSplitter {
    @Override
    protected List<String> splitText(String text) {
        // 1. 空文本处理
        // 2. 自定义边界规则
        // 3. 过滤空 chunk
        // 4. 返回 chunks
    }
}
```

这时会自动继承到：

- `Document -> chunk Document` 的封装
- metadata 复制
- parent/child 关系字段
- score 继承
- formatter 复制

## 什么时候只继承 `TextSplitter` 不够

如果有下面这些诉求，**就不要只覆写 `splitText()`**，而要直接实现 `DocumentTransformer`，或者复制/改写 `TextSplitter`：

1. **想改 metadata 策略**  
   比如把 `section_title`、`heading_path`、`page_range` 写进每个 chunk。

2. **想控制 chunk id 生成规则**  
   比如希望 chunk id 可复现，而不是新随机 id。

3. **想做跨文档窗口切分**  
   比如 PDF 按页读进来后，想把 page N 尾部和 page N+1 头部拼成一个 chunk。

4. **想做 overlap / sliding window**  
   这不是当前 `TextSplitter` 帮你做的，你得自己实现 token 窗口推进逻辑。

5. **想做层级切分**  
   例如先按标题、再按段落、最后再按 token 上限回退。

一个关键现实点是：`TextSplitter` 里 `createDocuments(...)` 和 `doSplitDocuments(...)` 是 **private**，不是 protected。  
这意味着它更像“给你一个简单模板”，而不是“允许你半覆写流程”。你要改装配过程，就得自己接管整个 `apply()` 流程。

## 自定义 splitter 设计时真正要想清楚的 5 件事

1. **边界依据是什么**  
   token、字符、段落、标题、代码块、Markdown AST、句子，还是它们的组合。

2. **长度约束跟谁对齐**  
   应该优先对齐 embedding model 的 tokenizer，而不是拍脑袋按字符数。

3. **是否需要 overlap**  
   如果要提升问答时跨段上下文召回，overlap 往往比“更聪明的标点回退”更关键。

4. **是否要保留结构信息到 metadata**  
   例如 `section`, `subsection`, `page_number`, `source`, `heading_path`。这对检索后重排和答案溯源很有用。

5. **是否要求 chunk id 稳定**  
   如果要做增量重建索引、去重、幂等入库，稳定 id 很重要。

## 工程建议

如果真实目标是：

- **只是想按标题/段落/代码块切得更语义化**：继承 `TextSplitter` 就够了
- **想补 overlap**：不要基于现有 `TokenTextSplitter` 做小修小补，直接写一个自定义 token window splitter 更干净
- **想做 RAG 质量优化**：最值得做的是  
  **“结构边界切分 + token 上限回退 + overlap + 结构化 metadata”**

这条路线比单纯调 `chunkSize/minChunkSizeChars` 更有效。
