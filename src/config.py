"""轻量 .env 加载器（零依赖）。

始终相对项目根目录（src/ 的上一级）寻找 .env 文件，无论从哪个目录启动程序，
都能正确加载配置；将 KEY=VALUE 行注入 os.environ（不覆盖已存在的环境变量）。
这样用户只需编辑 .env 即可切换 LLM 服务商 / 模式，无需手动 export 环境变量。
"""
import os

# 项目根目录 = src/ 的上一级
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_dotenv(path=None):
    if path is None:
        path = os.path.join(_PROJECT_ROOT, ".env")
    if not os.path.exists(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception:
        pass


load_dotenv()
