"""便捷启动入口。

用法：
  python run.py cli           # 命令行交互
  python run.py web           # Web 界面（默认 8000 端口）
  python run.py web --port 9000 --mock
  python run.py --query "..." # 直接单次查询（默认 cli 模式）
也可直接使用：python -m src.cli / python -m src.web
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src import cli, web


def main():
    argv = sys.argv[1:]
    mode = argv[0] if argv and argv[0] in ("cli", "web") else "cli"
    if mode == "web":
        sys.argv = [sys.argv[0]] + argv[1:]
        web.main()
    else:
        if argv and argv[0] == "cli":
            argv = argv[1:]
        sys.argv = [sys.argv[0]] + argv
        cli.main()


if __name__ == "__main__":
    main()
