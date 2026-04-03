---
title: '第18章：安全防护模式 / Guardrails & Safety Patterns'
tags:
  - Agentic Design Patterns
categories:
  - AI
cover: 'https://cdn.jsdelivr.net/gh/Supremes/blog-images@master/imgs/cover.jpg'
hidden: true
updated: '2026-03-23 23:30'
date: '2026-03-23 23:30'
sticky:
---

# 第18章：安全防护模式 / Guardrails & Safety Patterns

**来源 URL**: https://adp.xindoo.xyz/chapters/Chapter%2018_%20Guardrails_Safety%20Patterns/  
**整理日期**: 2026-03-23

---

## 核心概念

Guardrails（防护栏），也称为安全模式，是确保 AI 智能体**安全、符合道德规范并按预期运行**的关键机制。它们作为保护层，引导智能体的行为和输出，防止有害、有偏见、无关或其他不良响应。

**防护栏的核心目的不是限制智能体能力，而是引导其行为**——确保运行稳健、可靠且有益。

防护栏实施阶段：
- 输入验证/清理（过滤恶意内容）
- 输出过滤/后处理（分析毒性或偏见）
- 行为约束（提示词级别指令）
- 工具使用限制（约束智能体能力）
- 外部审核 API
- 人机协同监督（Human-in-the-Loop）

---

## 解决什么问题

没有防护栏，AI 系统可能：

- 生成有害、仇恨、虚假或不道德的内容
- 被"越狱"攻击绕过安全限制
- 在医疗、法律、金融等敏感领域给出危险建议
- 产生不可预测的涌现行为，造成现实损害
- 在关键决策中缺乏人工监督而失控
- 引发法律和声誉风险

---

## 工作原理/关键机制

```
用户输入
    ↓
[输入防护层]
├── 输入验证/清理：检测恶意提示词、越狱尝试
├── 内容审核 API：筛选仇恨言论、危险内容
└── Schema 验证（Pydantic）：结构化输入合规检查
    ↓
[主智能体处理]
    ↓
[输出防护层]
├── 输出过滤：检测毒性、偏见、事实错误
├── 行为约束提示词：系统提示词内嵌安全指令
├── 工具使用限制：约束可调用工具范围
└── 回调验证（before_tool_callback）：工具执行前验证参数
    ↓
[人机协同] ← 关键决策或触发警报时介入
    ↓
最终响应
```

**防护栏提示词示例（输入过滤器）**：
```
decision: "safe" | "unsafe"
reasoning: "决策解释"
```
LLM 充当安全评估者，对输入按以下准则评估：
1. 越狱尝试（忽略指令、重置角色等）
2. 有害内容生成（仇恨言论、危险活动、性内容）
3. 离题讨论（政治、宗教、个人生活）
4. 品牌诋毁或竞争对手讨论

---

## 应用场景

1. **客户服务聊天机器人**：防止生成冒犯性语言、不正确建议（医疗/法律）或离题响应；检测有毒用户输入并拒绝或升级到人工

2. **内容生成系统**：确保生成的文章、营销文案符合准则、法律要求和道德标准；后处理过滤器标记并删除有问题短语

3. **教育导师/助手**：防止提供不正确答案、推广偏见观点或进行不当对话；内容过滤 + 课程合规

4. **法律研究助手**：防止智能体提供明确法律建议，引导用户咨询持证律师

5. **招聘和 HR 工具**：过滤歧视性语言，确保候选人筛选公平性

6. **社交媒体内容审核**：自动识别仇恨言论、虚假信息、暴力内容

7. **科学研究助手**：防止伪造数据或得出缺乏支持的结论

---

## 框架实现

### CrewAI 实现

```python
# 1. 定义 Pydantic 验证模型
class PolicyEvaluation(BaseModel):
    compliance_status: str  # "compliant" | "non-compliant"
    evaluation_summary: str
    triggered_policies: List[str]

# 2. 创建策略执行智能体
policy_enforcer_agent = Agent(
    role="AI 内容策略执行者",
    llm=gemini_flash,  # 使用快速低成本模型作为防护层
    verbose=False,
    allow_delegation=False,
)

# 3. 任务绑定防护栏验证
evaluate_input_task = Task(
    description=f"{SAFETY_GUARDRAIL_PROMPT}\n\n待审查输入: {user_input}",
    guardrail=validate_policy_evaluation,
    output_pydantic=PolicyEvaluation,
    agent=policy_enforcer_agent,
)
```

### Google ADK（工具调用前验证回调）

```python
def validate_tool_params(tool, args, tool_context):
    expected_user_id = tool_context.state.get("session_user_id")
    actual_user_id = args.get("user_id_param")
    if actual_user_id != expected_user_id:
        return {"status": "error", "error_message": "用户 ID 验证失败，工具调用被阻止"}
    return None  # 允许执行

root_agent = Agent(
    model='gemini-2.0-flash-exp',
    before_tool_callback=validate_tool_params,
    tools=[...]
)
```

### Vertex AI 最佳实践

- 使用计算密集度较低的模型（如 Gemini Flash Lite）作为额外保障层
- 采用隔离的代码执行环境
- 在安全网络边界内限制智能体（VPC Service Controls）
- 在 UI 中显示前清理所有模型生成内容（防 XSS）

---

## 注意事项或权衡

| 权衡点 | 说明 |
|--------|------|
| 误报率 | 过于严格的防护栏会阻止合法请求，影响用户体验 |
| 额外延迟 | 防护层增加处理时间，特别是当使用多层防护时 |
| 额外成本 | 每次请求都经过额外 LLM 评估会增加 token 消耗 |
| 持续维护 | 攻击手法不断演变，防护栏需要持续更新 |
| 过度限制 | 防护栏不应成为智能体能力的枷锁，需精细平衡 |
| 分层复杂性 | 多层防护的调试和故障排查难度较高 |

**最佳工程实践**：
- 模块化设计（输入/输出/行为各层分离）
- 结构化日志记录所有操作（可观测性）
- 最小权限原则（智能体只能访问任务所需资源）
- 检查点和回滚机制（出错时可恢复到已验证状态）

---

## 一句话总结

> 防护栏通过在输入验证、输出过滤、行为约束和人机协同多个层面构建分层防御，确保 AI 智能体在自主运行时保持安全、可预测和符合道德规范，是负责任 AI 开发的核心承诺。
