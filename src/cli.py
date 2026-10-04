"""命令行交互入口。

用法：
  python -m src.cli                 # 进入交互模式
  python -m src.cli --query "审查 demo.py"   # 单次查询
  python -m src.cli --mock          # 强制演示模式
  python -m src.cli --reset         # 清空历史记忆
"""
import argparse
from .agent import CodeAgent
from . import llm as llm_mod

BANNER = """========================================================
  代码助手 Agent (Code Agent) - 命令行模式
  输入你的问题，例如：
    - 审查 samples/demo.py 并指出潜在 Bug
    - 解释 utils.py 的核心逻辑
    - 为 app.py 生成单元测试
  命令：exit/quit 退出 | reset 清空记忆
========================================================
"""


def main():
    parser = argparse.ArgumentParser(description="Code Agent 命令行")
    parser.add_argument("--query", help="直接执行单次查询（非交互模式）")
    parser.add_argument("--workdir", default=".", help="项目工作目录")
    parser.add_argument("--reset", action="store_true", help="启动时清空历史记忆")
    parser.add_argument("--mock", action="store_true", help="强制使用演示模式")
    args = parser.parse_args()

    llm = llm_mod.LLMClient(mock=True if args.mock else None)
    agent = CodeAgent(llm=llm, workdir=args.workdir)
    if args.reset:
        agent.memory.reset()

    if args.query:
        answer, log = agent.run(args.query)
        print("\n".join(f"  • {line}" for line in log))
        print("\n--- Agent 回答 ---\n")
        print(answer)
        return

    print(BANNER)
    while True:
        try:
            q = input("你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not q:
            continue
        if q.lower() in ("exit", "quit", "q"):
            print("再见！")
            break
        if q.lower() == "reset":
            agent.memory.reset()
            print("记忆已清空。")
            continue
        answer, log = agent.run(q)
        print()
        for line in log:
            print("  •", line)
        print("\n--- Agent 回答 ---\n")
        print(answer)
        print()


if __name__ == "__main__":
    main()
