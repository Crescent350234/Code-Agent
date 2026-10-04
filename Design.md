# Design.md · 代码助手 Agent 设计文档

## 1. 项目目标

依据 Homework 1 要求，构建一个**简单的代码助手 Agent**，作为 Agent 开发的入门实践，
覆盖以下基础能力：

- LLM 调用（兼容 OpenAI Chat Completions 接口）
- Prompt 设计（系统提示词定义角色与工具使用规范）
- 工具集成（文件读取、目录列举、命令执行、检索、测试生成）
- Agent 循环（输入 → 推理 → 工具调用 → 输出）
- 上下文记忆、错误处理与重试

## 2. 技术选型

| 维度 | 选择 | 理由 |
|------|------|------|
| 语言 | Python 3.9+ | 生态成熟、适合 AI/Agent 开发 |
| 依赖 | **零第三方依赖**（仅标准库） | 降低环境配置成本，开箱即运行，便于评分演示 |
| LLM 接入 | OpenAI 兼容 HTTP 接口（urllib 实现） | 一套代码适配 OpenAI / 通义千问 / DeepSeek / Ollama |
| Agent 范式 | ReAct（推理 + 行动） | 业界主流、直观体现「Agent 设计模式」 |
| Web | 标准库 `http.server` | 无需额外安装即可提供交互界面 |
| 记忆 | 内存 + JSON 文件持久化 | 实现多轮上下文记忆，可重置 |

> 说明：作业允许「Agent 框架（LangChain/AutoGen/CrewAI/Dify）或 LLM 原生 API」二选一。
> 本项目选择 **LLM 原生 API + 自研轻量 Agent 循环**，更直观地体现 Agent 架构原理，
> 且零依赖、可审计、易扩展。

## 3. 系统架构

```
┌──────────────────────────────────────────────────────────┐
│                        用户 (CLI / Web)                    │
└───────────────┬──────────────────────────┬────────────────┘
                │ 输入需求                  │ 查看回答 + 步骤日志
                ▼                          ▲
        ┌──────────────────────────────────────────┐
        │               CodeAgent (agent.py)        │
        │   Agent 循环 (ReAct):                      │
        │   1. 组装 messages (system + 记忆 + user)   │
        │   2. 调用 LLM 推理                          │
        │   3. 若有 tool_calls → 执行工具 → 回填结果   │
        │   4. 若无 tool_calls → 输出最终答案          │
        │   5. 循环至多 max_steps 步                   │
        └───────┬───────────────────────┬────────────┘
                │                        │
        ┌───────▼────────┐       ┌───────▼────────┐
        │  LLMClient     │       │   Memory       │
        │ (llm.py)       │       │ (memory.py)    │
        │ 真实调用/Mock  │       │ 上下文记忆持久化 │
        │ 重试机制       │       └────────────────┘
        └───────┬────────┘
                │ function calling
        ┌───────▼────────────────────────────────┐
        │            Tools (tools.py)             │
        │  read_file / list_directory /           │
        │  run_command / search_web /             │
        │  generate_unit_test                     │
        └─────────────────────────────────────────┘
```

## 4. Agent 循环伪代码

```text
function run(user_input):
    messages = [system_prompt] + memory.history + [user_input]
    memory.add(user_input)

    for step in range(max_steps):
        resp = llm.chat(messages, tools)          # 推理
        messages.append(assistant_msg(resp))      # 记录助手消息
        if resp has no tool_calls:
            return resp.content                    # 输出最终答案

        for each tool_call in resp.tool_calls:     # 行动
            result = execute_tool(tool_call)       # 调用工具
            messages.append(tool_result(result))   # 回填上下文
            memory.add(tool_result)

    return "达到最大步数，请拆分任务"
```

核心设计点：

- **工具调用闭环**：LLM 通过 function calling 决定调用哪个工具；工具结果以 `role=tool`
  消息回填，使 LLM 能基于**真实返回**继续推理，而非凭空生成。
- **上下文记忆**：`Memory` 保存完整多轮对话（含工具调用链），支持连续追问与上下文延续；
  提供 `reset` 清空。
- **错误与重试**：`LLMClient.chat()` 内置指数退避重试；工具执行异常被捕获为字符串结果返回，
  避免单点失败导致整个 Agent 崩溃。

## 5. Prompt 设计

系统提示词（`agent.py` 中 `SYSTEM_PROMPT`）明确：

1. 角色定位：专业代码助手，覆盖审查 / 解释 / 生成 / 测试 / 重构五类能力；
2. 工具清单与适用场景；
3. 工作准则：先理解意图、必要时调用工具、基于真实结果作答、给出可执行建议、中文回复、信息不足时追问。

通过将工具描述以 JSON Schema 形式随请求下发，LLM 可自主选择并正确传参。

## 6. 工具设计

每个工具同时提供「OpenAI 格式的函数描述」与「执行实现」：

- `read_file`：读取源码，超长截断，避免上下文溢出；
- `list_directory`：定位代码文件；
- `run_command`：仅允许白名单命令前缀（python/pytest/node 等），超时 30s，**默认禁止危险操作**；
- `search_web`：检索技术资料（演示模式返回内置示例）；
- `generate_unit_test`：为目标文件生成测试骨架。

工具集以列表形式组织，新增工具只需在 `TOOLS_SPEC` 注册描述并在 `run_tool` 实现分支，
Agent 主循环无需改动 —— 体现良好的**可扩展性**。

## 7. 对应评审标准

| 评审维度 | 权重 | 本项目的体现 |
|----------|------|--------------|
| 功能完整性 | 40% | 五类代码助手能力 + 5 个工具；边界处理（文件不存在/命令超时/异常捕获） |
| Agent 架构 | 30% | 清晰的 ReAct 循环、工具调用闭环、记忆机制、可扩展工具注册 |
| 代码质量 | 20% | 模块化拆分、类型清晰、错误处理、零依赖可维护 |
| 文档 | 10% | `README.md`（使用说明）+ 本 `Design.md`（设计文档） |

## 8. 运行与演示建议

1. **无 Key 演示**：直接 `python -m src.cli --mock` 或 `python -m src.web --mock`，
   可见完整 Agent 循环（工具调用日志 + 回答）。
2. **真实效果**：在 `.env` 配置 Key 后将 `MOCK_MODE` 设为 `0`，Agent 由真实大模型动态分析代码。
3. **演示视频脚本**：打开 Web 界面 → 输入「审查 samples/demo.py」→ 展示工具调用步骤与最终建议 → 结束（控制在 1 分钟内）。
