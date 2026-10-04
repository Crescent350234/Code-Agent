"""Agent 可调用的工具集合。

每个工具包含：
- OpenAI 格式的 JSON Schema 描述（TOOLS_SPEC），供 LLM 进行 function calling；
- run_tool() 中的实际执行逻辑。

工具清单：
- read_file          读取源文件内容（代码审查/解释用）
- list_directory     列出目录，定位代码文件
- run_command        在项目目录内执行安全白名单命令（如运行测试）
- search_web         检索技术资料（演示模式返回内置示例）
- generate_unit_test 为目标源文件生成单元测试骨架
"""
import os
import subprocess

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取指定路径的源代码或文本文件内容，用于代码审查、解释与重构分析。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件相对或绝对路径"}
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "列出目录下的文件与子目录，帮助定位代码文件。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目录路径，默认当前目录"}
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "在项目目录内执行一条 shell 命令（如运行测试、代码格式化）。出于安全限制，仅允许白名单命令并禁止危险操作。",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "要执行的命令字符串"}
                },
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "检索公开技术资料或官方文档（演示模式下返回内置示例链接）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "检索关键词"}
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "generate_unit_test",
            "description": "为一个给定的源代码文件生成单元测试骨架（演示模式返回模板）。",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "目标源代码文件路径"}
                },
                "required": ["path"],
            },
        },
    },
]

# 命令白名单：仅允许这些命令开头，避免任意代码执行风险
_ALLOWED_CMD = ("python", "python3", "pytest", "pip", "ls", "dir", "cat",
                "echo", "node", "npm", "git")


def _safe_path(path):
    return os.path.abspath(path)


def run_tool(name, arguments, workdir="."):
    """执行指定工具，返回字符串结果。所有异常被捕获并返回错误信息。"""
    try:
        if name == "read_file":
            p = _safe_path(arguments.get("path", ""))
            if not os.path.isfile(p):
                return f"[错误] 文件不存在: {p}"
            with open(p, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if len(content) > 8000:  # 防止上下文过长
                content = content[:8000] + "\n... (内容过长已截断) ..."
            return content

        elif name == "list_directory":
            d = arguments.get("path") or workdir
            d = _safe_path(d)
            if not os.path.isdir(d):
                return f"[错误] 目录不存在: {d}"
            items = sorted(os.listdir(d))
            return "\n".join(items)

        elif name == "run_command":
            cmd = arguments.get("command", "")
            if not cmd.strip():
                return "[错误] 命令为空"
            head = cmd.strip().split()[0].lower()
            if head not in _ALLOWED_CMD:
                return (f"[拒绝] 出于安全考虑，不允许执行命令: {head}；"
                        f"允许前缀: {', '.join(_ALLOWED_CMD)}")
            try:
                res = subprocess.run(cmd, shell=True, cwd=workdir,
                                     capture_output=True, text=True, timeout=30)
                out = (res.stdout or "") + (res.stderr or "")
                return out[:4000] if out else "[命令执行完成，无输出]"
            except subprocess.TimeoutExpired:
                return "[错误] 命令执行超时（>30s）"

        elif name == "search_web":
            q = arguments.get("query", "")
            return (f"[演示检索结果] 关于「{q}」的参考资料：\n"
                    "- https://docs.python.org/3/  (Python 官方文档)\n"
                    "- https://peps.python.org/  (Python 增强提案)\n"
                    "- https://stackoverflow.com/  (技术问答社区)\n"
                    "（配置真实 LLM 与检索 API 后可返回实时结果）")

        elif name == "generate_unit_test":
            p = arguments.get("path", "")
            base = os.path.basename(p)
            mod = os.path.splitext(base)[0] or "module"
            return (
                f"# 为 {base} 生成的单元测试骨架（演示）\n"
                f"import unittest\n"
                f"# from {mod} import *\n\n"
                f"class Test{mod.capitalize()}(unittest.TestCase):\n"
                f"    def test_example(self):\n"
                f"        # TODO: 补充针对 {mod} 的真实断言\n"
                f"        self.assertTrue(True)\n\n"
                f"if __name__ == '__main__':\n"
                f"    unittest.main()\n"
            )

        else:
            return f"[错误] 未知工具: {name}"
    except Exception as e:
        return f"[工具执行异常] {e}"
