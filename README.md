# Code Agent · 代码助手 Agent

> 课程作业 Homework 1：搭建一个简单的代码助手 Agent，掌握 Agent 开发的基础能力
> （LLM 调用、Prompt 设计、工具集成、Agent 循环）。

本项目是一个**可运行的代码助手 Agent**，能够：

- 🔍 **代码审查**：分析代码质量、发现潜在 Bug、给出改进建议
- 📖 **代码解释**：解释代码逻辑、生成说明
- 🧪 **测试生成**：为目标源文件生成单元测试骨架
- 🛠️ **重构建议**：分析代码坏味道、给出重构方向
- 🌐 **技术检索**：检索公开技术资料

---

## 一、环境要求

- Python 3.9+（**无需安装任何第三方依赖**，核心实现仅用标准库）
- 可选：配置任意 OpenAI 兼容接口的 LLM（OpenAI / 通义千问 / DeepSeek / 本地 Ollama 等）

## 二、快速开始

```bash
# 1. 进入项目目录
cd code-agent

# 2.（可选）配置 LLM —— 复制示例并填入你的 Key
cp .env.example .env
#   编辑 .env：设置 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL、MOCK_MODE=0

# 3. 命令行交互模式（默认演示模式，无需 Key 即可跑通）
python -m src.cli

# 3'. 单次查询
python -m src.cli --query "审查 samples/demo.py 并指出潜在 Bug"

# 4. Web 界面（默认 http://localhost:8000）
python -m src.web
```

> 程序启动时会自动加载项目根目录的 `.env` 文件（无需手动 export）。
> 未配置 `LLM_API_KEY`（或 `MOCK_MODE=1`）时，自动进入 **Mock 演示模式**，
> 仍会完整走通「输入 → 推理 → 工具调用 → 输出」的 Agent 循环，便于无 Key 演示与评分。

## 三、两种交互方式

### 1. 命令行（CLI）

```
你 > 审查 samples/demo.py 并指出潜在 Bug
  • 第 1 步：调用工具 read_file({'path': 'samples/demo.py'})
  • 第 2 步：推理并给出最终回答

--- Agent 回答 ---
...（基于文件内容的具体分析与建议）...
```

命令：`exit/quit` 退出，`reset` 清空记忆。

### 2. Web 界面

启动后浏览器打开 `http://localhost:8000`，在对话框中输入需求即可，
界面会实时显示 Agent 的推理步骤（🔧 工具调用日志）与最终回答。

## 四、配置说明（.env）

| 变量 | 说明 | 示例 |
|------|------|------|
| `LLM_BASE_URL` | OpenAI 兼容接口地址 | `https://api.openai.com/v1` |
| `LLM_API_KEY` | 服务商 API Key | `sk-...` |
| `LLM_MODEL` | 模型名 | `gpt-4o-mini` / `qwen-plus` / `deepseek-chat` |
| `MOCK_MODE` | `1` 演示模式 / `0` 真实调用 | `1` |
| `WEB_PORT` | Web 服务端口 | `8000` |

**通义千问示例**：`LLM_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1`、`LLM_MODEL=qwen-plus`
**DeepSeek 示例**：`LLM_BASE_URL=https://api.deepseek.com/v1`、`LLM_MODEL=deepseek-chat`

## 五、目录结构

```
code-agent/
├── run.py              # 便捷启动入口（cli / web）
├── requirements.txt    # 依赖说明（核心零依赖）
├── .env.example        # 配置模板
├── src/
│   ├── __init__.py
│   ├── llm.py          # LLM 客户端（真实调用 + Mock + 重试）
│   ├── memory.py       # 对话记忆（内存 + JSON 持久化）
│   ├── tools.py        # 工具集（read_file/list_directory/run_command/search_web/generate_unit_test）
│   ├── agent.py        # Agent 核心循环（ReAct 风格）
│   ├── cli.py          # 命令行交互
│   └── web.py          # 标准库 Web 界面
├── samples/
│   └── demo.py         # 示例目标文件（含常见代码问题，供演示）
└── memory.json         # 运行后自动生成（对话历史，--reset 可清空）
```

## 六、内置工具

| 工具 | 用途 | 安全限制 |
|------|------|----------|
| `read_file` | 读取源文件内容 | 超长截断（8000 字符） |
| `list_directory` | 列出目录 | — |
| `run_command` | 执行 shell 命令（如跑测试） | 仅白名单命令前缀，超时 30s |
| `search_web` | 技术资料检索 | 演示模式返回内置示例 |
| `generate_unit_test` | 生成单元测试骨架 | 演示模式返回模板 |

## 七、提交说明（对应作业要求）

- **代码**：本仓库（可推送到 GitHub/Gitee）
- **文档**：`README.md`（本文件）+ `Design.md`（设计文档）
- **演示视频**：可选，建议录制 1 分钟以内，展示「输入需求 → 工具调用 → 回答」全流程
- **打包**：将上述内容打包为「学号姓名」压缩包（如 `2412190222孟雨航.rar`），提交至 `001Homework1`，截止 **2026-10-07 24:00**
