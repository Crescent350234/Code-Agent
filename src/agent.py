"""Agent 核心：实现 输入 → 推理 → 工具调用 → 输出 的循环（ReAct 风格）。

设计要点：
- 系统提示词定义 Agent 角色与可用工具；
- 每轮调用 LLM，若返回 tool_calls 则执行工具并将结果回填上下文，继续推理；
- 若无 tool_calls 则返回最终答案；
- 通过 Memory 实现多轮上下文记忆；
- LLM 调用具备重试与异常兜底（见 llm.py）。
"""
import json
from . import llm as llm_mod
from . import tools as tools_mod
from .memory import Memory

SYSTEM_PROMPT = """你是一个专业的「代码助手 Agent」，能够帮助开发者进行代码审查、\
代码解释、代码生成、单元测试生成与重构建议。

你可以调用如下工具来完成任务：
- read_file: 读取文件内容
- list_directory: 列出目录
- run_command: 在项目内执行安全命令（如运行测试）
- search_web: 检索技术资料
- generate_unit_test: 生成单元测试骨架

工作准则：
1. 先理解用户意图，必要时调用工具获取上下文（例如先 read_file 再分析）。
2. 一次只做必要的工具调用，调用后必须基于真实返回结果给出结论。
3. 给出具体、可执行的建议，避免空泛套话。
4. 使用中文回复。
若信息不足，主动向用户追问以澄清需求。
"""


class CodeAgent:
    def __init__(self, llm=None, memory_path="memory.json", workdir="."):
        self.llm = llm or llm_mod.LLMClient()
        self.memory = Memory(path=memory_path)
        self.workdir = workdir
        self.tools = tools_mod.TOOLS_SPEC
        self.max_steps = 6  # 单轮对话最大推理步数，防止无限循环

    def _build_messages(self, user_input):
        msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        msgs += self.memory.get_messages()
        msgs.append({"role": "user", "content": user_input})
        return msgs

    def run(self, user_input):
        """执行一次用户请求，返回 (最终回答文本, 步骤日志列表)。"""
        messages = self._build_messages(user_input)
        self.memory.add("user", content=user_input)
        steps_log = []

        for step in range(self.max_steps):
            try:
                resp = self.llm.chat(messages, tools=self.tools)
            except Exception as e:
                return f"[Agent 错误] LLM 调用失败: {e}", steps_log

            content = resp.get("content") or ""
            tool_calls = resp.get("tool_calls")

            # 构造并保存助手消息
            assistant_msg = {"role": "assistant", "content": content}
            if tool_calls:
                assistant_msg["tool_calls"] = [
                    {
                        "id": tc["id"],
                        "type": "function",
                        "function": {
                            "name": tc["name"],
                            "arguments": json.dumps(tc["arguments"], ensure_ascii=False),
                        },
                    }
                    for tc in tool_calls
                ]
            messages.append(assistant_msg)
            self.memory.add("assistant", content=content or "",
                            tool_calls=assistant_msg.get("tool_calls"))

            # 无工具调用 → 本轮结束，返回最终答案
            if not tool_calls:
                steps_log.append(f"第 {step + 1} 步：推理并给出最终回答")
                return content, steps_log

            # 执行工具并回填结果
            for tc in tool_calls:
                args = tc.get("arguments", {})
                result = tools_mod.run_tool(tc["name"], args, workdir=self.workdir)
                tool_msg = {
                    "role": "tool",
                    "tool_call_id": tc.get("id"),
                    "name": tc["name"],
                    "content": str(result),
                }
                messages.append(tool_msg)
                self.memory.add("tool", content=str(result),
                                name=tc["name"], tool_call_id=tc.get("id"))
                steps_log.append(f"第 {step + 1} 步：调用工具 {tc['name']}({args})")

        final = "（已达到最大推理步数，请简化任务或拆分为更小的问题。）"
        self.memory.add("assistant", content=final)
        return final, steps_log
